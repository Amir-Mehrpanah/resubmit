"""Core submission utilities wrapping submitit."""

from typing import Callable, Iterable, Optional, Dict, Union

from .__debug import maybe_attach_debugger


def _submit_jobs(
    jobs_args: Iterable[dict],
    func: Callable,
    *,
    timeout_min: int,
    cpus_per_task: int,
    mem_gb: int,
    num_gpus: int,
    folder: str,
    block: bool,
    prompt: Union[bool, str],
    local_run: bool,
    debug_port: bool = False,
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
        prompt: Whether to prompt for confirmation before submission. if boolean it only prompts whether it should continue if str, it prints values from jobs for the prompted key.
        debug_port: If `debug_port > 0`, attaches a debugger and waits for debugger to attach. if `debug_port >= 0` runs only the first job in the queue.
        job_name: Name of the job.
        slurm_additional_parameters: Additional Slurm parameters as a dict. If not provided,

    - If `local_run` is True, the function is called directly on the local machine: `func(jobs_args[0])`.
    - Otherwise, submits via submitit.AutoExecutor and returns job objects or, if `block` is True, waits and returns results.
    - If you want to see a list of jobs before running, provide a key named `resubmit_prompt` in jobs_args. It will be printed before the prompt.

    Optional Slurm settings `constraint` and `reservation` can be provided via explicit
    parameters (they take precedence) or by passing `slurm_additional_parameters`.
    If not provided, they are omitted so the code is not tied to cluster-specific
    defaults.
    """
    jobs_list = list(jobs_args) if not isinstance(jobs_args, list) else jobs_args

    if len(jobs_list) == 0:
        print("No jobs to run exiting")
        return

    if debug_port is not None and debug_port >= 0:
        print("Debug mode: only running the first job.")
        jobs_list = [jobs_list[0]]

    if prompt:
        if isinstance(prompt, str):
            for job in jobs_list:
                print(job[prompt])
        print("Do you want to continue? [y/n]", flush=True)
        if input() != "y":
            print("Aborted")
            return

    if local_run:
        print("Running the jobs locally (local_run=True)")
        return [func(job) for job in jobs_list]

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
    if debug_port is not None and debug_port > 0:

        def wrapper(args):
            maybe_attach_debugger(debug_port)
            return func(args)

        jobs = executor.map_array(wrapper, jobs_list)
    else:
        jobs = executor.map_array(func, jobs_list)
    print("Jobs submitted")

    if block:
        print("Waiting for job to finish")
        results = [job.result() for job in jobs]
        print("All jobs finished")
        return results

    return jobs
