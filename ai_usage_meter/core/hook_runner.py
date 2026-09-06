"""Everything the hook does, minus stdin and stdout, so it can be tested.
Never raises: the hook runs inside Claude Code's render loop and a failure
must cost nothing but a missing update."""
from datetime import datetime, timezone
from typing import Optional

from . import line, merge, sessions
from .payload import StatuslinePayload
from .snapshot import CLAUDE_PROVIDER_ID
from .store import SnapshotStore


def run(data: bytes, store: SnapshotStore, now: Optional[datetime] = None, color: bool = False) -> str:
    now = now or datetime.now(timezone.utc)
    try:
        payload = StatuslinePayload.decode(data)
    except ValueError:
        payload = None
    incoming = payload.provider_usage(now) if payload else None
    if incoming is not None:
        try:
            store.with_exclusive_lock(
                lambda: store.write(merge.merge_snapshot(store.read(), CLAUDE_PROVIDER_ID, incoming))
            )
        except Exception:
            pass
    record = sessions.from_payload(payload, now)
    if record is not None:
        try:
            sessions.SessionStore.for_snapshot(store.path).write(record)
        except Exception:
            pass
    return line.render(payload, now, color, model_window=_stored_model_window(store))


def _stored_model_window(store: SnapshotStore):
    """The per-model week the tray's probe last wrote, if any; the hook
    never asks for it itself."""
    try:
        snapshot = store.read()
        usage = snapshot.claude if snapshot else None
        return usage.seven_day_model if usage else None
    except Exception:
        return None
