"""Ensure a background scheduler starts in exactly one process.

Gunicorn runs GUNICORN_WORKERS (default 4) separate processes, each
importing app.py fresh -- so any scheduler start call placed at module
level (needed so it actually runs at all; see the app.py comment on why
it can't live inside `if __name__ == "__main__":`) would otherwise fire
once per worker, quadruple-sending every push notification and funnel
snapshot.

A simple non-blocking flock on a fixed path, shared by all workers in the
same container, gives exactly one winner. The lock is held for the life
of the winning process (fd never closed) so it naturally releases if that
worker restarts.
"""

import fcntl
import logging
import os

logger = logging.getLogger(__name__)

_LOCK_DIR = os.getenv("SCHEDULER_LOCK_DIR", "/tmp")
_held_fds = []  # keep file descriptors alive for the process lifetime


def acquire(name: str) -> bool:
    """Try to become the single owner of the named scheduler. Returns True
    if this process should start the scheduler, False if another worker
    already holds it."""
    lock_path = os.path.join(_LOCK_DIR, f"gq_scheduler_{name}.lock")
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _held_fds.append(fd)
        return True
    except (OSError, BlockingIOError):
        logger.info(f"[scheduler-lock] {name}: another worker already holds it")
        return False
