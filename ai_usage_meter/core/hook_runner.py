"""Everything the hook does, minus stdin and stdout, so it can be tested.
Never raises: the hook runs inside Claude Code's render loop and a failure
must cost nothing but a missing update."""
from datetime import datetime, timezone
from typing import Callable, Optional

from . import line, merge, probe_gate, sessions
from .payload import StatuslinePayload
from .snapshot import CLAUDE_PROVIDER_ID
from .store import SnapshotStore


def run(data: bytes, store: SnapshotStore, now: Optional[datetime] = None, color: bool = False,
        request_probe: Optional[Callable[[], None]] = None) -> str:
    """``request_probe`` must start a usage probe without waiting for it; it
    is called when the payload carries rate limits and no probe, the tray's
    included, has started within ``probe_gate.HOOK_SECONDS``."""
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
    record = sessions.from_payload(payload, now, owner=sessions.find_owner())
    if record is not None:
        try:
            sessions.SessionStore.for_snapshot(store.path).write(record)
        except Exception:
            pass
    if request_probe is not None and incoming is not None:
        try:
            if probe_gate.claim(store.path, now):
                request_probe()
        except Exception:
            pass
    return line.render(payload, now, color, model_window=_stored_model_window(store))


def _stored_model_window(store: SnapshotStore):
    """The per-model week a probe last wrote, if any; the hook never waits
    for one."""
    try:
        snapshot = store.read()
        usage = snapshot.claude if snapshot else None
        return usage.seven_day_model if usage else None
    except Exception:
        return None
