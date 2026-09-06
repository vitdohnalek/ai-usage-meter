"""Reads and writes the snapshot file. Writes go to a temporary file in the
same directory followed by ``os.replace`` (``rename(2)``), so a reader never
sees a partial document."""
import fcntl
import os
import time
import uuid
from pathlib import Path
from typing import Callable, Optional, TypeVar

from .snapshot import Snapshot, decode, encode

DIRECTORY_NAME = "ai-usage-meter"
FILE_NAME = "snapshot.json"
LOCK_FILE_NAME = "snapshot.lock"
LOCK_RETRY_INTERVAL = 0.005
LOCK_TIMEOUT = 0.25

T = TypeVar("T")


def default_path() -> Path:
    """``$XDG_STATE_HOME/ai-usage-meter/snapshot.json``: mutable runtime state,
    always on the Linux filesystem so a future WSL reader can reach it."""
    base = os.environ.get("XDG_STATE_HOME")
    root = Path(base) if base else Path(os.path.expanduser("~")) / ".local" / "state"
    return root / DIRECTORY_NAME / FILE_NAME


class SnapshotStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    @classmethod
    def default(cls) -> "SnapshotStore":
        return cls(default_path())

    def read(self) -> Optional[Snapshot]:
        """``None`` when the file is missing or unreadable as a snapshot."""
        try:
            return decode(self.path.read_bytes())
        except (OSError, ValueError):
            return None

    def write(self, snapshot: Snapshot) -> None:
        data = encode(snapshot)
        directory = self.path.parent
        directory.mkdir(parents=True, exist_ok=True)
        temporary = directory / f".{FILE_NAME}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
        try:
            with open(temporary, "wb") as handle:
                handle.write(data)
            os.replace(temporary, self.path)
        except BaseException:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise

    def with_exclusive_lock(self, body: Callable[[], T]) -> T:
        """Serialize read-merge-write cycles across processes.

        Bounded, not blocking: polls a non-blocking ``flock`` up to
        ``LOCK_TIMEOUT``. The hook runs inside Claude Code's render loop and
        must never stall, so once the bound expires ``body`` runs anyway. That
        is safe: ``write`` is atomic and the merge is monotone, so a lost
        update is repaired by the next invocation.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path.parent / LOCK_FILE_NAME, os.O_CREAT | os.O_RDWR | os.O_CLOEXEC, 0o644)
        acquired = False
        try:
            deadline = time.monotonic() + LOCK_TIMEOUT
            while True:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        break
                    time.sleep(LOCK_RETRY_INTERVAL)
            return body()
        finally:
            if acquired:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)
