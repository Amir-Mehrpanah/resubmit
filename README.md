# resubmit

Small utility library to simplify job submission with Submitit on SLURM clusters.

Quick usage:

- Install locally for development:

```bash
pip install -e .[debug]
```

- Use in your project:

```python
from resubmit import submit_jobs, maybe_attach_debugger

# attach remote debugger if requested
maybe_attach_debugger(args.get("port", None))

# submit jobs (list of dicts)
submit_jobs(jobs_list, my_entrypoint, timeout_min=60, block=True)
```

## API

### submit_jobs(...) 🔧

Submit multiple jobs to a Slurm cluster using Submitit.

Signature (short):

`submit_jobs(jobs_args: Iterable[dict], func: Callable[[List[dict]], Any], *, timeout_min: int, cpus_per_task: int = 16, mem_gb: int = 64, num_gpus: int = 1, account: Optional[str] = None, folder: str = "logs/%j", block: bool = False, prompt: bool = True, local_run: bool = False, slurm_additional_parameters: Optional[Dict] = None, constraint: Optional[str] = None, reservation: Optional[str] = None)`

- `jobs_args`: iterable of per-job kwargs (each item is passed to `func`).
- `func`: entrypoint called for each job (should accept a list or single job dict depending on your usage).
- `timeout_min`, `cpus_per_task`, `mem_gb`, `num_gpus`: common Slurm resources.
- `account`: optional Slurm account name.
- `folder`: logs folder for Submitit files (supports `%j` for job id).
- `block`: if True, waits for all jobs and returns results.
- `prompt`: if True, asks for confirmation interactively; set to `False` for CI or tests.
- `local_run`: run the jobs locally without Submitit (useful for debugging).
- `slurm_additional_parameters`: pass any extra Slurm key/value pairs to Submitit.
- `constraint` / `reservation`: cluster-specific options kept out of defaults — provide them explicitly if you need them (they take precedence over values in `slurm_additional_parameters`).

Example:

```python
submit_jobs(
    jobs_list,
    my_entrypoint,
    timeout_min=60,
    num_gpus=2,
    prompt=False,
    constraint="gpu",
)
```

### maybe_attach_debugger(port: Optional[int]) 🐞

Attach `debugpy` to the job when `port` is provided (> 0). Safe no-op if `port` is `None` or `<= 0`.

- If `debugpy` (and `submitit`) are not available on the node, a `RuntimeError` is raised with an explanatory message.

Example:

```python
# attach remote debugger only when a port is provided (e.g., from CLI args)
maybe_attach_debugger(args.get("port"))
```

---

Tips:
- Use `prompt=False` when calling `submit_jobs` from scripts or CI to avoid interactive prompts.
- Tests demonstrate non-interactive behavior (`prompt=False`) and optional `constraint`/`reservation` handling.
