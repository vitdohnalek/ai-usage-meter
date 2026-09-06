"""The one line the hook prints back to Claude Code's status bar:
``Fable 5.1 · high · ⛁ 12% (119k/1M) · 5h 21% · wk 4% · Fable 5% · cache 43m``.
The per-model window is not in the payload; it comes from the snapshot the
tray's probe maintains, so it is absent where no tray runs."""
import math
from datetime import datetime, timezone
from typing import Optional

from . import countdown
from .clamp import clamped_int
from .display import BOLD_THRESHOLD, FLIP_THRESHOLD, MODEL_FALLBACK_NAME, SEPARATOR, UNKNOWN
from .payload import StatuslinePayload
from .snapshot import ModelWindow

FALLBACK_MODEL = "Claude"
CONTEXT_GLYPH = "⛁"  # the stacked-cylinder symbol /context uses
CONTEXT_YELLOW = 50
CONTEXT_RED = 75
FIVE_HOUR_TAG = "5h"
SEVEN_DAY_TAG = "wk"
CACHE_TAG = "cache"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"


def _paint(text: str, code: Optional[str], color: bool) -> str:
    return f"{code}{text}{RESET}" if color and code else text


def _percent(value: Optional[float]) -> Optional[int]:
    return clamped_int(value) if value is not None else None


def _percent_text(percent: Optional[int]) -> str:
    return UNKNOWN if percent is None else f"{percent}%"


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


def _tokens(payload: StatuslinePayload) -> Optional[str]:
    """``(119k/1M)``, ``(119k)`` when the size is unknown, ``None`` otherwise."""
    used = compact_tokens(payload.context_tokens)
    if used is None:
        return None
    size = compact_tokens(payload.context_window_size)
    return f"({used}/{size})" if size else f"({used})"


def _context(payload: Optional[StatuslinePayload], color: bool) -> str:
    """Percentage green under 50, yellow under 75, red from 75; the token
    count turns red once Claude Code flags the 200k long-context boundary."""
    percent = _percent(payload.context_used_percentage) if payload else None
    code = None
    if percent is not None:
        code = RED if percent >= CONTEXT_RED else YELLOW if percent >= CONTEXT_YELLOW else GREEN
    text = _paint(_percent_text(percent), code, color)
    tokens = _tokens(payload) if payload else None
    if tokens:
        text += " " + _paint(tokens, RED if payload.exceeds_200k else None, color)
    return f"{CONTEXT_GLYPH} {text}"


def _limit_text(tag: str, percent: int, color: bool) -> str:
    """One rate-limit segment, coloured at the tray's own thresholds."""
    code = RED if percent >= FLIP_THRESHOLD else YELLOW if percent >= BOLD_THRESHOLD else None
    return f"{tag} {_paint(_percent_text(percent), code, color)}"


def _limit(tag: str, window, color: bool) -> Optional[str]:
    percent = _percent(window.used_percentage) if window else None
    return None if percent is None else _limit_text(tag, percent, color)


def _model_limit(window: Optional[ModelWindow], now: datetime, color: bool) -> Optional[str]:
    """The stored per-model week, named after its label; 0 once its reset
    has passed and no fresher probe has landed, as the tray shows it."""
    if window is None:
        return None
    percent = window.used_percentage if countdown.text(window.resets_at, now) else 0
    return _limit_text(window.model or MODEL_FALLBACK_NAME, percent, color)


def _limits(payload: Optional[StatuslinePayload], color: bool) -> list:
    limits = payload.rate_limits if payload else None
    if limits is None:
        return []
    segments = [_limit(FIVE_HOUR_TAG, limits.five_hour, color), _limit(SEVEN_DAY_TAG, limits.seven_day, color)]
    return [s for s in segments if s]


def _cache(payload: Optional[StatuslinePayload], now: datetime, color: bool) -> Optional[str]:
    """``cache 43m`` while the prefix is warm and its expiry is known,
    ``cache warm`` without an expiry, ``cache cold`` otherwise; nothing when
    Claude Code has not seen caching at all."""
    cache = payload.prompt_cache if payload else None
    if cache is None or not cache.observed or cache.warm is None:
        return None
    remaining = None
    if cache.warm and cache.expires_at is not None:
        try:
            remaining = countdown.text(datetime.fromtimestamp(cache.expires_at, tz=timezone.utc), now)
        except (OverflowError, ValueError, OSError):
            remaining = None
    if remaining:
        return f"{CACHE_TAG} {remaining}"
    if cache.warm and cache.expires_at is None:
        return f"{CACHE_TAG} warm"
    return _paint(f"{CACHE_TAG} cold", YELLOW, color)


def render(payload: Optional[StatuslinePayload], now: Optional[datetime] = None, color: bool = False,
           model_window: Optional[ModelWindow] = None) -> str:
    now = now or datetime.now(timezone.utc)
    model = (payload.model_display_name if payload else None) or FALLBACK_MODEL
    effort = payload.effort_level if payload else None
    segments = [model] + ([effort] if effort else []) + [_context(payload, color)] + _limits(payload, color)
    for extra in (_model_limit(model_window, now, color), _cache(payload, now, color)):
        if extra:
            segments.append(extra)
    return SEPARATOR.join(segments).replace("\r", " ").replace("\n", " ")
