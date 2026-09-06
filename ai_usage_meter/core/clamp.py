"""Double-to-int without surprises: round half away from zero, clamp, None for non-numbers."""
import math
from typing import Optional


def clamped_int(value, low: int = 0, high: int = 1_000) -> Optional[int]:
    """Round half away from zero and clamp to ``[low, high]``.

    Non-numbers, booleans and non-finite values become ``None``. Untrusted
    JSON can carry ``1e300``; the clamped result (``1000%``) is itself the
    visible tell that the input was bad, matching the upstream tradeoff.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    rounded = math.floor(abs(number) + 0.5) * (1 if number >= 0 else -1)
    return int(min(max(rounded, low), high))
