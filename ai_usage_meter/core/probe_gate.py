"""Who may run the usage probe, and when. Where no tray runs (WSL, servers)
the hook is the only process left to start one, and every open session
runs the hook once a minute. A stamp file beside the snapshot holds the
time of the last probe start; a prober claims the next one under a
non-blocking ``flock`` on that file, so one probe starts per interval no
matter how many hooks render at once."""
import fcntl
import os
from datetime import datetime
from pathlib import Path

STAMP_FILE_NAME = "probe.stamp"
# The tray probes every 300 s and stamps each start; the hook waits a minute
# longer, so it stays quiet for as long as a tray is doing the work.
HOOK_SECONDS = 360


def stamp_path(snapshot_path) -> Path:
    return Path(snapshot_path).parent / STAMP_FILE_NAME


def claim(snapshot_path, now: datetime, interval: float = HOOK_SECONDS) -> bool:
    """True when no probe started within ``interval`` seconds; the stamp then
    moves to ``now``. Never raises and never waits: a busy or unwritable
    stamp is a refusal."""
    path = stamp_path(snapshot_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_CLOEXEC, 0o644)
    except OSError:
        return False
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        last = _read(descriptor)
        # A stamp ahead of the clock (the clock was set back) must not
        # silence the probe until the clock catches up.
        if last is not None and 0 <= (now - last).total_seconds() < interval:
            return False
        os.ftruncate(descriptor, 0)
        os.pwrite(descriptor, now.isoformat().encode("ascii"), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False
    finally:
        os.close(descriptor)


def stamp(snapshot_path, now: datetime) -> None:
    """Record a probe start unconditionally (the tray, on its own timer)."""
    claim(snapshot_path, now, interval=0)


def _read(descriptor: int):
    try:
        return datetime.fromisoformat(os.pread(descriptor, 64, 0).decode("ascii").strip())
    except ValueError:
        return None
