"""The one line the hook prints back to Claude Code's status bar."""
from typing import Optional

from .clamp import clamped_int
from .display import SEPARATOR, UNKNOWN
from .payload import StatuslinePayload

FALLBACK_MODEL = "Claude"
CONTEXT_GLYPH = "⛁"  # the stacked-cylinder symbol /context uses


def _percent(value: Optional[float]) -> str:
    clamped = clamped_int(value) if value is not None else None
    return UNKNOWN if clamped is None else f"{clamped}%"


def render(payload: Optional[StatuslinePayload]) -> str:
    model = (payload.model_display_name if payload else None) or FALLBACK_MODEL
    effort = payload.effort_level if payload else None
    context = _percent(payload.context_used_percentage if payload else None)
    segments = [model] + ([effort] if effort else []) + [f"{CONTEXT_GLYPH} {context}"]
    return SEPARATOR.join(segments).replace("\r", " ").replace("\n", " ")
