import pytest
from resubmit import submit_jobs, maybe_attach_debugger


def dummy_func(jobs):
    # return a list of strings to show behavior
    return [f"ok-{j['id']}" for j in jobs]


def test_submit_local_run():
    jobs = [{"id": 1}, {"id": 2}]
    res = submit_jobs(jobs, dummy_func, timeout_min=1, local_run=True)
    assert res == ["ok-1", "ok-2"]


def test_maybe_attach_debugger_noop():
    # should not raise when port is None or 0
    maybe_attach_debugger(None)
    maybe_attach_debugger(0)
