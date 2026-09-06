"""What the AppIndicator shows, as pure functions over the display state.
GNOME tray labels are plain text, so bold becomes a ``!`` marker and the
90 percent flip becomes an icon swap."""
from pathlib import Path
from typing import List, Tuple

from ..core.display import SEPARATOR, MeterDisplay, WindowDisplay

ICON_DIR = Path(__file__).resolve().parent.parent / "assets"
NORMAL_ICON = "ai-usage-meter-symbolic"
ALARM_ICON = "ai-usage-meter-alarm"
BOLD_MARKER = "!"
BAR_CELLS = 10
BAR_FULL = "▰"
BAR_EMPTY = "▱"


def _number(window: WindowDisplay) -> str:
    return window.percent_text + (BOLD_MARKER if window.is_bold else "")


def label_text(display: MeterDisplay) -> str:
    return _number(display.five_hour) + SEPARATOR + _number(display.seven_day)


def icon_name(display: MeterDisplay) -> str:
    return ALARM_ICON if display.is_flipped else NORMAL_ICON


def bar_text(fraction: float) -> str:
    filled = int(min(1.0, max(0.0, fraction)) * BAR_CELLS + 0.5)
    return BAR_FULL * filled + BAR_EMPTY * (BAR_CELLS - filled)


def menu_rows(display: MeterDisplay) -> List[Tuple[str, str]]:
    return [(w.row_text, bar_text(w.fraction)) for w in (display.five_hour, display.seven_day)]
