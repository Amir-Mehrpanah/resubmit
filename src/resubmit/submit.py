"""Core submission utilities wrapping submitit."""
from typing import Any, Callable, Iterable, List, Optional, Dict


def submit_jobs(
    jobs_args: Iterable[dict],
    func: Callable[[List[dict]], Any],
    *,
    timeout_min: int,
    cpus_per_task: int = 16,
    mem_gb: int = 64,
    num_gpus: int = 1,
    account: Optional[str] = None,
    folder: str = "logs/%j",
    block: bool = False,
    prompt: bool = True,
    local_run: bool = False,
    slurm_additional_parameters: Optional[Dict] = None,
):
    """Submit jobs described by `jobs_args` where each entry is a dict of kwargs for `func`.

    - If `local_run` is True, the function is called directly: `func(jobs_args)`.
    - Otherwise, submits via submitit.AutoExecutor and returns job objects or, if `block` is True, waits and returns results.
    """
    jobs_list = list(jobs_args) if not isinstance(jobs_args, list) else jobs_args

    if len(jobs_list) == 0:
        print("No jobs to run exiting")
        return

    if local_run:
        print("Running locally (local_run=True)")
        return func(jobs_list)

    if prompt:
        print("Do you want to continue? [y/n]", flush=True)
        if input() != "y":
            print("Aborted")
            return

    import submitit
    print("submitting jobs")
    executor = submitit.AutoExecutor(folder=folder)

    # default slurm params
    if slurm_additional_parameters is None:
        slurm_additional_parameters = {
            "constraint": "thin",
            "reservation": "safe",
            "gpus": num_gpus,
        }
    else:
        slurm_additional_parameters = dict(slurm_additional_parameters)
        slurm_additional_parameters.setdefault("gpus", num_gpus)

    if account is not None:
        slurm_additional_parameters["account"] = account

    print("Slurm additional parameters:", slurm_additional_parameters)

    executor.update_parameters(
        timeout_min=timeout_min,
        cpus_per_task=cpus_per_task,
        mem_gb=mem_gb,
        slurm_additional_parameters=slurm_additional_parameters,
    )

    jobs = executor.map_array(func, jobs_list)
    print("Job submitted")

    if block:
        print("Waiting for job to finish")
        results = [job.result() for job in jobs]
        print("All jobs finished")
        return results

    return jobs
