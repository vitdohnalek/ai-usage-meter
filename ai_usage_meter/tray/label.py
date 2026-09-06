"""What the AppIndicator shows, as pure functions over the display state.
GNOME tray labels are plain text, so bold becomes a ``!`` marker and the
90 percent flip becomes an icon swap."""
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from ..core import countdown
from ..core.clamp import clamped_int
from ..core.display import SEPARATOR, UNKNOWN, MeterDisplay, WindowDisplay
from ..core.line import CONTEXT_GLYPH
from ..core.sessions import SessionRecord

ICON_DIR = Path(__file__).resolve().parent.parent / "assets"
NORMAL_ICON = "ai-usage-meter-symbolic"
ALARM_ICON = "ai-usage-meter-alarm"
BOLD_MARKER = "!"
BAR_CELLS = 10
BAR_FULL = "▰"
BAR_EMPTY = "▱"
LABEL_GUIDE = "100%! · 100%! · 100%!"


def _number(window: WindowDisplay) -> str:
    return window.percent_text + (BOLD_MARKER if window.is_bold else "")


def label_text(display: MeterDisplay, show_numbers: bool = True) -> str:
    """Empty when the user hides the numbers: an empty label makes the
    appindicator extension drop the text widget, leaving the icon alone."""
    if not show_numbers:
        return ""
    return SEPARATOR.join(_number(w) for w in display.windows)


def label_guide(show_numbers: bool) -> str:
    """The widest label the panel should reserve room for."""
    return LABEL_GUIDE if show_numbers else ""


def icon_name(display: MeterDisplay) -> str:
    return ALARM_ICON if display.is_flipped else NORMAL_ICON


def bar_text(fraction: float) -> str:
    filled = int(min(1.0, max(0.0, fraction)) * BAR_CELLS + 0.5)
    return BAR_FULL * filled + BAR_EMPTY * (BAR_CELLS - filled)


def menu_rows(display: MeterDisplay) -> List[Tuple[str, str]]:
    return [(w.row_text, bar_text(w.fraction)) for w in display.windows]


def session_header(records: List[SessionRecord]) -> str:
    return f"Sessions ({len(records)})"


def _session_context(record: SessionRecord) -> str:
    """Percentage only; the token count stays in the terminal line so the
    dropdown reads at a glance."""
    percent = clamped_int(record.context_used_percentage) if record.context_used_percentage is not None else None
    return f"{CONTEXT_GLYPH} {UNKNOWN if percent is None else f'{percent}%'}"


def _session_cache(record: SessionRecord, now: datetime) -> str:
    if record.cache_warm is None:
        return ""
    remaining = countdown.text(record.cache_expires_at, now) if record.cache_warm and record.cache_expires_at else None
    if remaining:
        return f"{SEPARATOR}cache {remaining}"
    if record.cache_warm and record.cache_expires_at is None:
        return f"{SEPARATOR}cache warm"
    return f"{SEPARATOR}cache cold"


def session_rows(records: List[SessionRecord], now: datetime) -> List[str]:
    """One inert row per live session, alphabetical: name, context, cache.
    The cache countdown runs on the tray's clock, so it ticks between hook
    runs."""
    ordered = sorted(records, key=lambda r: (r.name.lower(), r.session_id))
    return [f"{r.name}  {_session_context(r)}{_session_cache(r, now)}" for r in ordered]
