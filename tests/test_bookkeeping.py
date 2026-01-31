import re
import pandas as pd
from resubmit.__bookkeeping import create_jobs_dataframe, ensure_unique_combinations


def test_create_jobs_basic():
    params = {"a": [1, 2], "b": [10]}
    df = create_jobs_dataframe(params)
    assert len(df) == 2
    assert set(df.columns) == {"a", "b"}


def test_create_jobs_callable():
    params = {"a": [1, 2], "b": lambda df: df["a"] * 10}
    df = create_jobs_dataframe(params)
    assert list(df["b"]) == [10, 20]


def test_create_jobs_regex_include():
    params = {"name": ["apple", "banana", "apricot"], "name__regex": re.compile(r"^a")}
    df = create_jobs_dataframe(params)
    assert set(df["name"]) == {"apple", "apricot"}


def test_create_jobs_regex_exclude():
    params = {"name": ["apple", "banana", "apricot"], "name_regex": "!re:^a"}
    df = create_jobs_dataframe(params)
    assert set(df["name"]) == {"banana"}


def test_ensure_unique_combinations_raises():
    df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
    try:
        ensure_unique_combinations(df, ["a", "b"], raise_on_conflict=True)
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_ensure_unique_combinations_ok():
    df = pd.DataFrame({"a": [1, 2, 3], "b": [3, 4, 5]})
    ok, dup = ensure_unique_combinations(df, ["a", "b"], raise_on_conflict=False)
    assert ok
    assert dup is None
