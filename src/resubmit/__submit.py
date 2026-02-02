"""Core submission utilities wrapping submitit."""

from typing import Any, Callable, Iterable, List, Optional, Dict


def _submit_jobs(
    jobs_args: Iterable[dict],
    func: Callable[[List[dict]], Any],
    *,
    timeout_min: int,
    cpus_per_task: int,
    mem_gb: int,
    num_gpus: int,
    folder: str,
    block: bool,
    prompt: bool,
    local_run: bool,
    debug: bool = False,
    job_name: Optional[str] = "resubmit",
    slurm_additional_parameters: Optional[Dict] = None,
):
    """Submit jobs described by `jobs_args` where each entry is a dict of kwargs for `func`.

    Args:
        jobs_args: Iterable of dicts of job parameters.
        func: Function to be submitted for each job.
        timeout_min: Job timeout in minutes.
        cpus_per_task: Number of CPUs per task.
        mem_gb: Memory in GB.
        num_gpus: Number of GPUs.
        folder: Folder for logs.
        block: Whether to block until jobs complete.
        prompt: Whether to prompt for confirmation before submission.
        local_run: If True, runs the function locally instead of submitting.
        debug: If True, runs only the first job in the queue for debugging.
        job_name: Name of the job.
        slurm_additional_parameters: Additional Slurm parameters as a dict. If not provided,
    
    - If `local_run` is True, the function is called directly on the local machine: `func(jobs_args[0])`.
    - Otherwise, submits via submitit.AutoExecutor and returns job objects or, if `block` is True, waits and returns results.

    Optional Slurm settings `constraint` and `reservation` can be provided via explicit
    parameters (they take precedence) or by passing `slurm_additional_parameters`.
    If not provided, they are omitted so the code is not tied to cluster-specific
    defaults.
    """
    jobs_list = list(jobs_args) if not isinstance(jobs_args, list) else jobs_args

    if debug:
        print("Debug mode: only running the first job locally")
        return func([jobs_list[0]])

    if len(jobs_list) == 0:
        print("No jobs to run exiting")
        return

    if local_run:
        print("Running the jobs locally (local_run=True)")
        return func(jobs_list)

    if prompt:
        print("Do you want to continue? [y/n]", flush=True)
        if input() != "y":
            print("Aborted")
            return

    import submitit

    print("submitting jobs")
    executor = submitit.AutoExecutor(folder=folder)

    print("Slurm additional parameters:", slurm_additional_parameters)

    executor.update_parameters(
        name=job_name,
        timeout_min=timeout_min,
        cpus_per_task=cpus_per_task,
        gpus_per_node=num_gpus,
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
