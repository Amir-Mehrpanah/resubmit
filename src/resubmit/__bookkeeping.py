import re
from typing import Any, Dict, List, Tuple, Union, Optional, Iterable
import pandas as pd
from itertools import product
import logging


def _is_regex_spec(val: Any) -> bool:
    """Return True if val looks like a regex specifier.

    Accepted forms:
    - compiled `re.Pattern`
    - tuple (`re.Pattern`, exclude: bool)
    - dict with keys `pattern` (re.Pattern) and optional `exclude` (bool)
    - string starting with 're:' (e.g. 're:^foo.*') meaning include matches
    - string starting with '!re:' meaning exclude matches
    """
    if hasattr(val, "search") and callable(val.search):
        return True
    if isinstance(val, tuple) and len(val) >= 1 and hasattr(val[0], "search"):
        return True
    if isinstance(val, dict) and "pattern" in val:
        return True
    if isinstance(val, str) and (val.startswith("re:") or val.startswith("!re:")):
        return True
    return False


def _normalize_regex_spec(val: Any) -> Tuple[re.Pattern, bool]:
    """Return (compiled_pattern, exclude_flag) for a given regex spec.

    Raises ValueError for unsupported types.
    """
    if hasattr(val, "search") and callable(val.search):
        return val, False
    if isinstance(val, tuple) and len(val) >= 1:
        pat = val[0]
        exclude = bool(val[1]) if len(val) > 1 else False
        return pat, exclude
    if isinstance(val, dict):
        pat = val["pattern"]
        exclude = bool(val.get("exclude", False))
        return pat, exclude
    if isinstance(val, str):
        if val.startswith("!re:"):
            return re.compile(val[4:]), True
        elif val.startswith("re:"):
            return re.compile(val[3:]), False
    raise ValueError(f"Unsupported regex spec: {val!r}")


def ensure_unique_combinations(
    df: pd.DataFrame, cols: Union[str, List[str]], raise_on_conflict: bool = True
) -> Tuple[bool, Optional[pd.DataFrame]]:
    """Check that combinations of columns `cols` are unique across `df`.

    Returns (is_unique, duplicates_df) where `duplicates_df` is None when unique.
    If `raise_on_conflict` is True, raises `ValueError` when duplicates are found.
    """
    if isinstance(cols, str):
        cols = [cols]
    # Stringify to avoid dtype mismatch effects
    key_series = df[cols].astype(str).agg("||".join, axis=1)
    nunique = key_series.nunique()
    if nunique == len(df):
        return True, None

    duplicates = df[key_series.duplicated(keep=False)]
    if raise_on_conflict:
        raise ValueError(
            f"Found {len(duplicates)} rows with non-unique combinations for cols={cols}."
        )
    return False, duplicates


def create_jobs_dataframe(params: Dict[str, Any]) -> pd.DataFrame:
    """Create a job DataFrame from a parameter map.

    Rules:
    - For parameters whose values are iterable (lists, tuples), we build the Cartesian
      product across all such parameters.
    - If a parameter value is callable, it is evaluated AFTER the initial DataFrame
      is created; the callable is called as `col_values = fn(df)` and the result is
      used as the column values (must be same length as `df`).
    - If a parameter value is a regex spec (see `_is_regex_spec`), it is applied LAST
      as a filter on the generated DataFrame. Regex specs can be used to include or
      exclude rows based on the stringified value of that column.

    Returns a filtered DataFrame with the applied callables and regex filters.
    """
    # Separate static values (used for product), callables and regex specs
    static_items = {}
    callables: Dict[str, Any] = {}
    regex_specs: Dict[str, Any] = {}
    unique_items: Dict[str, Any] = {}

    for k, v in params.items():
        # support explicit regex keys like 'name__regex' or 'name_regex' to filter 'name'
        if k.endswith("__regex") or k.endswith("_regex"):
            if k.endswith("__regex"):
                base = k[: -len("__regex")]
            else:
                base = k[: -len("_regex")]
            regex_specs[base] = v
        elif k.endswith("__callable") or k.endswith("_callable"):
            if k.endswith("__callable"):
                base = k[: -len("__callable")]
            else:
                base = k[: -len("_callable")]
            callables[base] = v
        elif k.endswith("__unique") or k.endswith("_unique"):
            if k.endswith("__unique"):
                base = k[: -len("__unique")]
            else:
                base = k[: -len("_unique")]
            unique_items[base] = v
            continue
        elif callable(v):
            callables[k] = v
        elif _is_regex_spec(v):
            # treat a regex spec provided under the same key as a filter for that column
            regex_specs[k] = v
        else:
            static_items[k] = v

    # If there are no static items, start from single-row DataFrame so callables
    # can still compute columns.
    if len(static_items) == 0:
        df = pd.DataFrame([{}])
    else:
        df = pd.DataFrame(
            list(product(*static_items.values())), columns=static_items.keys()
        )

    # Apply callables (they must accept the dataframe and return a list-like)
    for k, fn in callables.items():
        vals = fn(df)
        if len(vals) != len(df):
            raise ValueError(
                f"Callable for param {k!r} returned length {len(vals)} != {len(df)}"
            )
        df[k] = vals

    # Apply regex specs last as filters
    if len(regex_specs) > 0:
        mask = pd.Series([True] * len(df), index=df.index)
        for k, spec in regex_specs.items():
            pat, exclude = _normalize_regex_spec(spec)
            col_str = df[k].astype(str)
            matches = col_str.apply(lambda s: bool(pat.search(s)))
            if exclude:
                mask = mask & ~matches
            else:
                mask = mask & matches
        df = df[mask].reset_index(drop=True)

    # apply unique constraints
    for k, unique_val in unique_items.items():
        is_unique, duplicates = ensure_unique_combinations(
            df,
            k,
            raise_on_conflict=unique_val,
        )
        if not is_unique:
            logging.warning(f"Non-unique values found for column {k!r}:\n{duplicates}")

    return df


def submit_jobs(
    jobs_args: dict[Iterable],
    func: Any,
    *,
    timeout_min: int,
    cpus_per_task: int = 16,
    mem_gb: int = 64,
    num_gpus: int = 1,
    folder: str = "logs/%j",
    block: bool = False,
    prompt: bool = True,
    local_run: bool = False,
    slurm_additional_parameters: Dict | None = None,
) -> Any:
    """
    Submit jobs described by `jobs_args` where each entry is a dict of kwargs for `func`.
    A dataframe is created from cartesian product of parameter lists, with support for callables and regex filtering.
    1. use `__unique' postfix in keys to enforce uniqueness.
    2. use `__callable' postfix in keys to define callables for column values.
    3. use `__regex' postfix in keys to define regex filters for columns.

    Args:
        jobs_args: dict of lists of job parameters.
        func: Function to be submitted for each job.
        timeout_min: Job timeout in minutes.
        cpus_per_task: Number of CPUs per task.
        mem_gb: Memory in GB.
        num_gpus: Number of GPUs.
        folder: Folder for logs.
        block: Whether to block until jobs complete.
        prompt: Whether to prompt for confirmation before submission.
        local_run: If True, runs the function locally instead of submitting.
        slurm_additional_parameters: Additional Slurm parameters as a dict. If not provided, defaults to {"gpus": num_gpus}.
    Returns:
        The result of `submit_jobs` from `.__submit`.
    """

    jobs_df = create_jobs_dataframe(jobs_args)
    records = jobs_df.to_dict(orient="records")
    from .__submit import submit_jobs as _submit_jobs

    return _submit_jobs(
        records,
        func,
        timeout_min=timeout_min,
        cpus_per_task=cpus_per_task,
        mem_gb=mem_gb,
        num_gpus=num_gpus,
        folder=folder,
        block=block,
        prompt=prompt,
        local_run=local_run,
        slurm_additional_parameters=slurm_additional_parameters,
    )
