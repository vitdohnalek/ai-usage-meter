"""The one line the hook prints back to Claude Code's status bar."""
import math
from typing import Optional

from .clamp import clamped_int
from .display import SEPARATOR, UNKNOWN
from .payload import StatuslinePayload

FALLBACK_MODEL = "Claude"
CONTEXT_GLYPH = "⛁"  # the stacked-cylinder symbol /context uses


def _percent(value: Optional[float]) -> str:
    clamped = clamped_int(value) if value is not None else None
    return UNKNOWN if clamped is None else f"{clamped}%"


def compact_tokens(value: Optional[float]) -> Optional[str]:
    """``118695`` -> ``119k``, ``1000000`` -> ``1M``, ``1250000`` -> ``1.25M``."""
    if value is None or not math.isfinite(value) or value < 0:
        return None
    if value < 1_000:
        return str(int(value))
    if value < 1_000_000:
        return f"{value / 1_000:.0f}k"
    text = f"{value / 1_000_000:.2f}".rstrip("0").rstrip(".")
    return f"{text}M"


def _tokens(payload: Optional[StatuslinePayload]) -> str:
    """`` (119k/1M)``, `` (119k)`` when the size is unknown, empty otherwise."""
    used = compact_tokens(payload.context_tokens) if payload else None
    if used is None:
        return ""
    size = compact_tokens(payload.context_window_size)
    return f" ({used}/{size})" if size else f" ({used})"


def render(payload: Optional[StatuslinePayload]) -> str:
    model = (payload.model_display_name if payload else None) or FALLBACK_MODEL
    effort = payload.effort_level if payload else None
    context = _percent(payload.context_used_percentage if payload else None) + _tokens(payload)
    segments = [model] + ([effort] if effort else []) + [f"{CONTEXT_GLYPH} {context}"]
    return SEPARATOR.join(segments).replace("\r", " ").replace("\n", " ")
