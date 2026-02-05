import re
import pandas as pd
from resubmit.__bookkeeping import create_jobs_dataframe, ensure_unique_combinations


def test_create_jobs_basic():
    params = {"a": [1, 2], "b": [10]}
    df = create_jobs_dataframe(params)
    assert len(df) == 2
    assert set(df.columns) == {"a", "b"}


def test_create_jobs_callable():
    params = {"a": [1, 2], "b__callable": lambda df: df["a"] * 10}
    df = create_jobs_dataframe(params)
    assert list(df["b"]) == [10, 20]


def test_create_jobs_transform():
    params = {
        "a": [1, 2],
        "b__callable": lambda df: df["a"] * 10,
        "d_transform": lambda df: pd.DataFrame({"a": df["a"], "c": df["a"] + df["b"]}),
    }
    df = create_jobs_dataframe(params)
    assert "b" not in df.columns
    assert list(df["c"]) == [11, 22]


def test_error_in_create_jobs_transform():
    def raise_error():
        raise NotImplementedError("Test")

    params = {
        "a": [1, 2],
        "b__callable": lambda df: df["a"] * 10,
        "d_transform": lambda df: raise_error(),
    }
    try:
        df = create_jobs_dataframe(params)
    except NotImplementedError as e:
        assert "Test" in e.args[0] and "Error at key 'd'" in e.args[0]


def test_error_in_create_jobs_callable():
    def raise_error():
        raise NotImplementedError("Test")

    params = {
        "a": [1, 2],
        "b__callable": lambda df: raise_error(),
        "d_transform": lambda df: df,
    }
    try:
        df = create_jobs_dataframe(params)
    except NotImplementedError as e:
        assert "Test" in e.args[0] and "Error at key 'b'" in e.args[0]


def test_error_in_create_jobs_static_items():

    params = {
        "a": [1, 2],
        "s": 1,
        "b__callable": lambda df: df["a"] * 10,
    }
    try:
        df = create_jobs_dataframe(params)
    except TypeError as e:
        assert f"'s' = 1 is not iterable" in e.args[0]


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
