"""Where the Windows tray gets the snapshot: the file the hook writes inside
WSL, reached through ``\\\\wsl.localhost\\<distro>\\...``. Opening that share
can start a stopped distro, so the distro is asked for first and left
alone when it is not running; a local copy of the last good snapshot
answers instead."""
import json
import os
import re
import subprocess
import uuid
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Mapping, Optional

from ..core import sessions
from ..core.snapshot import Snapshot, decode

PATH_ENV = "AI_USAGE_METER_SNAPSHOT"
DIRECTORY_NAME = "ai-usage-meter"
CONFIG_FILE_NAME = "wintray.json"
CACHE_FILE_NAME = "snapshot.json"
WSL_TIMEOUT_SECONDS = 10
AUTO = object()
_UNC = re.compile(r"^(\\\\(?:wsl\.localhost|wsl\$)\\([^\\]+))\\", re.IGNORECASE)


def _match(path):
    return _UNC.match(str(path).replace("/", "\\"))


def distro_of(path) -> Optional[str]:
    """The distro a WSL share path points into; ``None`` for any other path."""
    match = _match(path)
    return match.group(2) if match else None


def proc_root(path) -> Optional[str]:
    """The distro's ``/proc`` as seen from Windows, for session liveness."""
    match = _match(path)
    return match.group(1) + "\\proc" if match else None


def parse_running(output: bytes) -> List[str]:
    """``wsl.exe -l --running -q`` prints UTF-16 with CRLF line ends, or
    UTF-8 when ``WSL_UTF8`` is set in the user's environment."""
    try:
        text = output.decode("utf-16-le" if b"\x00" in output else "utf-8")
    except UnicodeDecodeError:
        return []
    return [line.strip() for line in text.lstrip("﻿").splitlines() if line.strip()]


def running_distros() -> List[str]:
    """Asks the WSL service; does not start anything. Empty on any failure,
    which includes "no running distributions" (a non-zero exit)."""
    completed = subprocess.run(
        ["wsl.exe", "-l", "--running", "-q"], capture_output=True, timeout=WSL_TIMEOUT_SECONDS,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return parse_running(completed.stdout) if completed.returncode == 0 else []


def default_config_path() -> Path:
    return Path(os.environ.get("APPDATA") or os.path.expanduser("~")) / DIRECTORY_NAME / CONFIG_FILE_NAME


def default_cache_path() -> Path:
    return Path(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")) / DIRECTORY_NAME / CACHE_FILE_NAME


def configured_path(environ: Mapping[str, str], config_file) -> Optional[str]:
    """``AI_USAGE_METER_SNAPSHOT``, else ``snapshot_path`` in the config the
    installer wrote; ``None`` when neither names a path."""
    explicit = environ.get(PATH_ENV)
    if explicit:
        return explicit
    try:
        document = json.loads(Path(config_file).read_bytes())
    except (OSError, ValueError):
        return None
    path = document.get("snapshot_path") if isinstance(document, dict) else None
    return path if isinstance(path, str) and path else None


@dataclass(frozen=True)
class Reading:
    snapshot: Optional[Snapshot]
    live: bool  # False: the distro is not running, the snapshot is the local copy


class SnapshotSource:
    def __init__(self, path, cache_path=None, distro=AUTO,
                 list_running: Callable[[], List[str]] = running_distros):
        self.path = Path(path)
        self.cache_path = Path(cache_path) if cache_path else None
        self.distro = distro_of(path) if distro is AUTO else distro
        self.list_running = list_running
        self._cached_bytes = None

    def is_live(self) -> bool:
        if self.distro is None:
            return True
        try:
            return self.distro.lower() in (name.lower() for name in self.list_running())
        except Exception:
            return False

    def read(self) -> Reading:
        if not self.is_live():
            return Reading(self.cached(), False)
        try:
            data = self.path.read_bytes()
            snapshot = decode(data)
        except (OSError, ValueError):
            return Reading(self.cached(), True)
        self._remember(data)
        return Reading(snapshot, True)

    def cached(self) -> Optional[Snapshot]:
        """The local copy of the last good snapshot; never touches the share."""
        if self.cache_path is None:
            return None
        try:
            return decode(self.cache_path.read_bytes())
        except (OSError, ValueError):
            return None

    def _remember(self, data: bytes) -> None:
        if self.cache_path is None or data == self._cached_bytes:
            return
        temporary = self.cache_path.parent / f".{self.cache_path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_bytes(data)
            os.replace(temporary, self.cache_path)
            self._cached_bytes = data
        except OSError:
            try:
                os.unlink(temporary)
            except OSError:
                pass


def live_sessions(store: sessions.SessionStore, now: datetime, proc) -> List[sessions.SessionRecord]:
    """With a readable ``proc``: prune and list by process, as the Linux
    tray does. Without one: list by age alone and delete nothing, because
    every process would look gone."""
    if proc is not None and sessions.proc_readable(Path(proc)):
        store.prune(now, proc=Path(proc))
        return store.live(now, proc=Path(proc))
    ownerless = (replace(record, owner_pid=None, owner_start=None) for record in store.read_all())
    return [record for record in ownerless if sessions.is_live(record, now)]
