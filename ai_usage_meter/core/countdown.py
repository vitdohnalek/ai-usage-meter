"""Human-readable durations for the dropdown. Kept coarse on purpose: the
app refreshes every 30 seconds, so seconds would only jitter."""
import math
from datetime import datetime
from typing import Optional

from .clamp import clamped_int

SECONDS_MAX = 1_000_000_000_000


def text_for_seconds(remaining_seconds: float) -> Optional[str]:
    """``None`` once the reset has passed (or the input is not finite)."""
    if not isinstance(remaining_seconds, (int, float)) or not math.isfinite(remaining_seconds):
        return None
    remaining = clamped_int(math.ceil(remaining_seconds), 0, SECONDS_MAX)
    if not remaining:
        return None
    minutes = remaining // 60
    hours = minutes // 60
    days = hours // 24
    if days >= 1:
        return f"{days}d {hours % 24:02d}h"
    if hours >= 1:
        return f"{hours}h {minutes % 60:02d}m"
    if minutes >= 1:
        return f"{minutes}m"
    return "under 1m"


def age_for_seconds(elapsed_seconds: float) -> str:
    seconds = clamped_int(elapsed_seconds, 0, SECONDS_MAX) or 0
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60} min ago"
    if seconds < 86_400:
        return f"{seconds // 3600} h ago"
    return f"{seconds // 86_400} d ago"


def text(until: datetime, now: datetime) -> Optional[str]:
    return text_for_seconds((until - now).total_seconds())


def age(since: datetime, now: datetime) -> str:
    return age_for_seconds((now - since).total_seconds())
