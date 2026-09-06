"""One small JSON file per open Claude Code session, written by the hook
on every render and listed by the tray. Each session is its own file, so
no lock is needed: the write is a temp file plus ``os.replace``.
Sessions that stop updating fall out of the live list; their files are
pruned after a day."""
import hashlib
import os
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import json

from .payload import StatuslinePayload
from .snapshot import format_date, parse_date

DIRECTORY_NAME = "sessions"
LIVE_SECONDS = 180      # three statusline refreshes; a closed session goes quiet within one
PRUNE_SECONDS = 86_400
SHORT_ID = 8
_SAFE = re.compile(r"[^A-Za-z0-9_-]")


@dataclass(frozen=True)
class SessionRecord:
    session_id: str
    name: str
    project_dir: Optional[str]
    model: Optional[str]
    context_used_percentage: Optional[float]
    context_tokens: Optional[float]
    context_window_size: Optional[float]
    cache_warm: Optional[bool]
    cache_expires_at: Optional[datetime]
    updated_at: datetime


def display_name(session_name: Optional[str], project_dir: Optional[str], session_id: str) -> str:
    """The session's own name, else its directory's basename, else the
    first eight characters of its id."""
    if session_name and session_name.strip():
        return session_name.strip()
    if project_dir:
        base = os.path.basename(project_dir.rstrip("/"))
        return base or project_dir
    return session_id[:SHORT_ID]


def from_payload(payload: Optional[StatuslinePayload], now: datetime) -> Optional[SessionRecord]:
    if payload is None or not payload.session_id:
        return None
    cache = payload.prompt_cache
    expires = None
    if cache is not None and cache.expires_at is not None:
        try:
            expires = datetime.fromtimestamp(cache.expires_at, tz=now.tzinfo)
        except (OverflowError, ValueError, OSError):
            expires = None
    return SessionRecord(
        session_id=payload.session_id,
        name=display_name(payload.session_name, payload.project_dir, payload.session_id),
        project_dir=payload.project_dir,
        model=payload.model_display_name,
        context_used_percentage=payload.context_used_percentage,
        context_tokens=payload.context_tokens,
        context_window_size=payload.context_window_size,
        cache_warm=cache.warm if cache is not None else None,
        cache_expires_at=expires,
        updated_at=now,
    )


def encode(record: SessionRecord) -> bytes:
    document = asdict(record)
    document["cache_expires_at"] = format_date(record.cache_expires_at) if record.cache_expires_at else None
    document["updated_at"] = format_date(record.updated_at)
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _optional_number(value) -> Optional[float]:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _optional_string(value) -> Optional[str]:
    return value if isinstance(value, str) else None


def decode(data: bytes) -> SessionRecord:
    """Raise ``ValueError`` unless ``session_id`` and ``updated_at`` are
    usable; every other field degrades to ``None`` on its own."""
    try:
        document = json.loads(data)
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError(str(error)) from error
    if not isinstance(document, dict):
        raise ValueError("session record is not an object")
    session_id = document.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("session_id missing")
    updated_at = parse_date(document.get("updated_at"))
    expires_raw = document.get("cache_expires_at")
    try:
        expires = parse_date(expires_raw) if isinstance(expires_raw, str) else None
    except ValueError:
        expires = None
    project_dir = _optional_string(document.get("project_dir"))
    name = _optional_string(document.get("name")) or display_name(None, project_dir, session_id)
    warm = document.get("cache_warm")
    return SessionRecord(
        session_id=session_id,
        name=name,
        project_dir=project_dir,
        model=_optional_string(document.get("model")),
        context_used_percentage=_optional_number(document.get("context_used_percentage")),
        context_tokens=_optional_number(document.get("context_tokens")),
        context_window_size=_optional_number(document.get("context_window_size")),
        cache_warm=warm if isinstance(warm, bool) else None,
        cache_expires_at=expires,
        updated_at=updated_at,
    )


def file_name(session_id: str) -> str:
    """Safe on any filesystem: the id with odd characters replaced, plus a
    short hash so two ids that sanitize alike never share a file."""
    digest = hashlib.sha1(session_id.encode("utf-8")).hexdigest()[:SHORT_ID]
    return f"{_SAFE.sub('_', session_id)[:64]}-{digest}.json"


class SessionStore:
    def __init__(self, directory: Path):
        self.directory = Path(directory)

    @classmethod
    def for_snapshot(cls, snapshot_path: Path) -> "SessionStore":
        return cls(Path(snapshot_path).parent / DIRECTORY_NAME)

    def write(self, record: SessionRecord) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.directory / file_name(record.session_id)
        temporary = self.directory / f".{target.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
        try:
            temporary.write_bytes(encode(record))
            os.replace(temporary, target)
        except BaseException:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise

    def read_all(self) -> List[SessionRecord]:
        records = []
        try:
            entries = list(self.directory.iterdir())
        except OSError:
            return records
        for entry in entries:
            if entry.suffix != ".json" or entry.name.startswith("."):
                continue
            try:
                records.append(decode(entry.read_bytes()))
            except (OSError, ValueError):
                continue
        return records

    def live(self, now: datetime, max_age_seconds: float = LIVE_SECONDS) -> List[SessionRecord]:
        """Sessions whose hook ran within ``max_age_seconds``; a record
        stamped in the future counts as live (clock skew, not a ghost)."""
        return [r for r in self.read_all() if (now - r.updated_at).total_seconds() <= max_age_seconds]

    def prune(self, now: datetime, older_than_seconds: float = PRUNE_SECONDS) -> None:
        for entry in list(self.directory.iterdir()) if self.directory.is_dir() else []:
            if entry.suffix != ".json":
                continue
            try:
                record = decode(entry.read_bytes())
            except (OSError, ValueError):
                continue
            if (now - record.updated_at).total_seconds() > older_than_seconds:
                try:
                    entry.unlink()
                except OSError:
                    pass
