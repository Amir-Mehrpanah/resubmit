"""resubmit: small helpers around submitit for reproducible cluster submissions."""

from .submit import submit_jobs
from .debug import maybe_attach_debugger
from .slurm import make_default_slurm_params

__all__ = ["submit_jobs", "maybe_attach_debugger", "make_default_slurm_params"]
