import pytest
from resubmit import maybe_attach_debugger
from resubmit.__submit import _submit_jobs
from resubmit.__bookkeeping import submit_jobs


def dummy_func(job):
    print(job)
    # return a list of strings to show behavior
    return f"ok-{job['id']}"


def test_submit_local_run():
    jobs = {"id": [1,2], "xd": [4]}
    res = submit_jobs(
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

def test_submit_with_port_number_remote_run(monkeypatch):
    events = {}

    class DummyExecutor:
        def __init__(self, folder):
            events["folder"] = folder

        def update_parameters(self, **kwargs):
            # capture the parameters passed to the executor
            events["update"] = kwargs

        def map_array(self, func, jobs_list):
            print("my map array is called")
            return [func(j) for j in jobs_list]

    class DummyModule:
        AutoExecutor = DummyExecutor

    import sys

    monkeypatch.setitem(sys.modules, "submitit", DummyModule)

    jobs = {"id": [1,2], "xd": [5,6]}
    res = submit_jobs(
        jobs,
        dummy_func,
        timeout_min=1,
        local_run=False,
        num_gpus=0,
        cpus_per_task=1,
        mem_gb=8,
        folder="dummy/%j",
        debug_port=0,
        block=False,
        prompt=False,
    )
    assert res == ["ok-1"]

def test_maybe_attach_debugger_noop():
    # should not raise when port is None or 0
    maybe_attach_debugger(None)
    maybe_attach_debugger(0)


def test_runs_only_the_first_job_in_debug_mode_local_run():
    jobs = {"id": [1, 2, 3], "xd": [2, 3, 4]}

    res = submit_jobs(
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
        debug_port=0,
    )
    # only the first job should be run in debug mode
    assert res == ["ok-1"]


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
        slurm_additional_parameters={},
    )
    slurm = events["update"]["slurm_additional_parameters"]

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
