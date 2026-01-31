import pytest
from resubmit import maybe_attach_debugger
from resubmit.__submit import _submit_jobs


def dummy_func(jobs):
    # return a list of strings to show behavior
    return [f"ok-{j['id']}" for j in jobs]


def test_submit_local_run():
    jobs = [{"id": 1}, {"id": 2}]
    res = _submit_jobs(
        jobs,
        dummy_func,
        timeout_min=1,
        local_run=True,
        num_gpus=0,
        cpus_per_task=1,
        mem_gb=8,
        folder="dummy/%j",
        block=False,
        prompt=False,
    )
    assert res == ["ok-1", "ok-2"]


def test_maybe_attach_debugger_noop():
    # should not raise when port is None or 0
    maybe_attach_debugger(None)
    maybe_attach_debugger(0)


def test_slurm_parameters_optional(monkeypatch):
    events = {}

    class DummyExecutor:
        def __init__(self, folder):
            events["folder"] = folder

        def update_parameters(self, **kwargs):
            # capture the parameters passed to the executor
            events["update"] = kwargs

        def map_array(self, func, jobs_list):
            return []

    class DummyModule:
        AutoExecutor = DummyExecutor

    import sys

    monkeypatch.setitem(sys.modules, "submitit", DummyModule)

    jobs = [{"id": 1}]
    # default: no constraint/reservation keys
    _submit_jobs(
        jobs,
        dummy_func,
        timeout_min=1,
        local_run=False,
        num_gpus=2,
        prompt=False,
        cpus_per_task=4,
        mem_gb=16,
        folder="logs/%j",
        block=False,
    )
    slurm = events["update"]["slurm_additional_parameters"]
    assert slurm["gpus"] == 2
    assert "constraint" not in slurm
    assert "reservation" not in slurm


def test_slurm_parameters_settable(monkeypatch):
    events = {}

    class DummyExecutor:
        def __init__(self, folder):
            events["folder"] = folder

        def update_parameters(self, **kwargs):
            events["update"] = kwargs

        def map_array(self, func, jobs_list):
            return []

    class DummyModule:
        AutoExecutor = DummyExecutor

    import sys

    monkeypatch.setitem(sys.modules, "submitit", DummyModule)

    jobs = [{"id": 1}]
    _submit_jobs(
        jobs,
        dummy_func,
        timeout_min=1,
        local_run=False,
        prompt=False,
        slurm_additional_parameters={
            "constraint": "thin",
            "reservation": "safe",
        },
        cpus_per_task=4,
        mem_gb=16,
        folder="logs/%j",
        block=False,
        num_gpus=1,
    )
    slurm = events["update"]["slurm_additional_parameters"]
    assert slurm["constraint"] == "thin"
    assert slurm["reservation"] == "safe"

