"""Tray preferences: one small JSON file under ``$XDG_CONFIG_HOME``.
Anything unreadable or oddly typed falls back to the defaults, so a broken
file can never keep the tray from starting."""
import json
import os
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

DIRECTORY_NAME = "ai-usage-meter"
FILE_NAME = "tray.json"


@dataclass(frozen=True)
class Prefs:
    show_numbers: bool = True


def default_path() -> Path:
    """``$XDG_CONFIG_HOME/ai-usage-meter/tray.json``: a user choice, so it
    lives in config, unlike the snapshot in state."""
    base = os.environ.get("XDG_CONFIG_HOME")
    root = Path(base) if base else Path(os.path.expanduser("~")) / ".config"
    return root / DIRECTORY_NAME / FILE_NAME


def decode(data: bytes) -> Prefs:
    try:
        document = json.loads(data)
    except ValueError:
        return Prefs()
    if not isinstance(document, dict):
        return Prefs()
    show_numbers = document.get("show_numbers", True)
    if not isinstance(show_numbers, bool):
        show_numbers = True
    return Prefs(show_numbers=show_numbers)


def encode(prefs: Prefs) -> bytes:
    return (json.dumps(asdict(prefs), indent=2, sort_keys=True) + "\n").encode("utf-8")


def load(path: Path) -> Prefs:
    try:
        return decode(Path(path).read_bytes())
    except OSError:
        return Prefs()


def save(prefs: Prefs, path: Path) -> None:
    """Temp file plus ``os.replace`` so a crash mid-write leaves the old file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{FILE_NAME}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    try:
        temporary.write_bytes(encode(prefs))
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
