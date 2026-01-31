"""resubmit: small helpers around submitit for reproducible cluster submissions."""

from .__debug import maybe_attach_debugger
from .__bookkeeping import submit_jobs

__all__ = ["submit_jobs", "maybe_attach_debugger"]
