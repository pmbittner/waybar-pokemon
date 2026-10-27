"""Files shared by the commands and the daemon: locks and atomic writes."""

import fcntl
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def locked(path: Path, wait: bool = True) -> Iterator[None]:
    """Holds the lock file at path. Without waiting, BlockingIOError if
    someone else holds it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | (0 if wait else fcntl.LOCK_NB))
        yield


def write_atomic(path: Path, data: bytes) -> None:
    """Replaces the file at once, so a reader never sees half of it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Unique per process and thread, as downloads run in parallel.
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.part")
    temporary.write_bytes(data)
    temporary.replace(path)
