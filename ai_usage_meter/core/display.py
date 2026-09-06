"""Everything the tray renders, computed once per refresh so the GTK layer
stays free of rules."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from . import countdown
from .snapshot import Snapshot, UsageWindow

BOLD_THRESHOLD = 75
FLIP_THRESHOLD = 90
UNKNOWN = "--"
SEPARATOR = " · "
MODEL_FALLBACK_NAME = "Model"


@dataclass
class WindowDisplay:
    percent: Optional[int]
    is_bold: bool
    percent_text: str
    row_text: str
    fraction: float


@dataclass
class MeterDisplay:
    NO_SNAPSHOT_TEXT = "No snapshot yet"

    five_hour: WindowDisplay
    seven_day: WindowDisplay
    model: Optional[WindowDisplay]
    is_flipped: bool
    age_text: str

    @property
    def windows(self) -> List[WindowDisplay]:
        """The rows to render, in order; the model row only once known."""
        return [w for w in (self.five_hour, self.seven_day, self.model) if w is not None]


def _window(name: str, window: Optional[UsageWindow], now: datetime) -> WindowDisplay:
    if window is None:
        return WindowDisplay(None, False, UNKNOWN, f"{name}  {UNKNOWN}", 0)
    remaining = countdown.text(window.resets_at, now)
    if remaining is None:
        return WindowDisplay(0, False, "0%", f"{name}  0%{SEPARATOR}reset", 0)
    percent = window.used_percentage
    return WindowDisplay(
        percent=percent,
        is_bold=percent >= BOLD_THRESHOLD,
        percent_text=f"{percent}%",
        row_text=f"{name}  {percent}%{SEPARATOR}resets in {remaining}",
        fraction=min(1.0, max(0.0, percent / 100)),
    )


def make(snapshot: Optional[Snapshot], now: datetime) -> MeterDisplay:
    usage = snapshot.claude if snapshot else None
    five_hour = _window("5-hour", usage.five_hour if usage else None, now)
    seven_day = _window("7-day", usage.seven_day if usage else None, now)
    model_window = usage.seven_day_model if usage else None
    model = (_window(model_window.model or MODEL_FALLBACK_NAME, model_window, now)
             if model_window is not None else None)
    display = MeterDisplay(five_hour, seven_day, model, False, "")
    display.is_flipped = any((w.percent or 0) >= FLIP_THRESHOLD for w in display.windows)
    display.age_text = (f"Updated {countdown.age(usage.captured_at, now)}{SEPARATOR}{usage.source}"
                        if usage else MeterDisplay.NO_SNAPSHOT_TEXT)
    return display
