"""Debug helpers (attach remote debugger when running via Submitit)."""


from typing import Optional

def maybe_attach_debugger(port: Optional[int]) -> None:
    """Attach debugpy to the current job when `port` is provided (> 0).

    Safe no-op if `port` is None or <= 0. Raises informative errors if debugpy is missing.
    """
    if port is None or port <= 0:
        return

    try:
        import submitit
        import debugpy
    except Exception as exc:  # pragma: no cover - environmental dependency
        raise RuntimeError(
            "debugging requires 'submitit' and 'debugpy' packages installed on the compute node"
        ) from exc

    job_env = submitit.JobEnvironment()
    print(f"Debugger is running on node {job_env.hostname} port {port}")
    debugpy.listen((job_env.hostname, port))
    print("Waiting for debugger attach")
    debugpy.wait_for_client()
