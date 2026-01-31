"""Small helpers for SLURM parameter construction."""


from typing import Optional

def make_default_slurm_params(gpus: int = 1, constraint: str = "thin", reservation: str = "safe", account: Optional[str] = None) -> dict:
    params = {"constraint": constraint, "reservation": reservation, "gpus": gpus}
    if account is not None:
        params["account"] = account
    return params
