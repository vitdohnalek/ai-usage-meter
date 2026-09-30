"""What the Windows tray shows, as pure functions over the display state.
The notification area has no text labels, so each window gets its own icon
with the number drawn into it, coloured by how full the window is; the
icons keep a fixed order, so position says which window is which. The
dropdown reuses the Linux tray's rows."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from ..core.display import SEPARATOR, MeterDisplay, WindowDisplay
from ..core.sessions import SessionRecord
from ..tray import label

FIVE_HOUR = "five_hour"
SEVEN_DAY = "seven_day"
MODEL = "model"
GREEN = "green"
BLUE = "blue"
ORANGE = "orange"
RED = "red"
PURPLE = "purple"
UNKNOWN_LEVEL = "unknown"
LEVELS = (GREEN, BLUE, ORANGE, RED, PURPLE, UNKNOWN_LEVEL)
# The owner's bands, finer than the Linux tray's two thresholds: each colour
# holds up to and including its bound, purple above the last.
BANDS = ((20, GREEN), (50, BLUE), (75, ORANGE), (90, RED))
UNKNOWN_TEXT = "--"
STALE_TEXT = "WSL stopped"
TOOLTIP_MAX = 127        # NOTIFYICONDATA.szTip holds 128 characters with the terminator
SESSION_SLOTS = 8
SEPARATOR_LINE = None


@dataclass(frozen=True)
class IconSpec:
    key: str
    text: str
    level: str
    tooltip: str


def level_of(percent: Optional[int]) -> str:
    if percent is None:
        return UNKNOWN_LEVEL
    return next((level for bound, level in BANDS if percent <= bound), PURPLE)


def _spec(key: str, window: WindowDisplay, live: bool) -> IconSpec:
    text = UNKNOWN_TEXT if window.percent is None else str(window.percent)
    tooltip = window.row_text if live else f"{window.row_text}{SEPARATOR}{STALE_TEXT}"
    return IconSpec(key, text, level_of(window.percent), tooltip[:TOOLTIP_MAX])


def icon_specs(display: MeterDisplay, live: bool = True) -> List[IconSpec]:
    """One icon per window, in the order of the Linux label; the model icon
    only once that window is known. ``live`` is False while the numbers come
    from the local copy because the distro is not running."""
    specs = [_spec(FIVE_HOUR, display.five_hour, live), _spec(SEVEN_DAY, display.seven_day, live)]
    if display.model is not None:
        specs.append(_spec(MODEL, display.model, live))
    return specs


def menu_lines(display: MeterDisplay, sessions: List[SessionRecord], now: datetime,
               live: bool = True) -> List[Optional[str]]:
    """The dropdown, top to bottom; ``SEPARATOR_LINE`` marks a divider."""
    lines: List[Optional[str]] = []
    for row, bar in label.menu_rows(display):
        lines += [row, bar]
    rows = label.session_rows(sessions, now)[:SESSION_SLOTS]
    if rows:
        lines += [SEPARATOR_LINE, label.session_header(sessions), *rows]
    age = display.age_text if live else f"{display.age_text}{SEPARATOR}{STALE_TEXT}"
    return lines + [SEPARATOR_LINE, age]


def menu_text(line: str) -> str:
    """Win32 menus read ``&`` as a mnemonic prefix; doubled, it is literal."""
    return line.replace("&", "&&")
