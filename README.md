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
