import unittest
from datetime import timedelta

from ai_usage_meter.core.display import make
from ai_usage_meter.core.snapshot import ModelWindow, ProviderUsage, Snapshot, UsageWindow
from ai_usage_meter.tray import label
from tests.fixtures import CAPTURED as NOW, FIVE_RESET, MODEL_RESET, SEVEN_RESET


def display(five, seven, now=NOW, model=None):
    snapshot = Snapshot(schema_version=1, providers={"claude": ProviderUsage(
        five_hour=UsageWindow(five, FIVE_RESET) if five is not None else None,
        seven_day=UsageWindow(seven, SEVEN_RESET) if seven is not None else None,
        captured_at=NOW - timedelta(seconds=120), source="statusline",
        seven_day_model=ModelWindow(model, MODEL_RESET, "Fable") if model is not None else None)})
    return make(snapshot, now)


class LabelTests(unittest.TestCase):
    def test_plain_label_and_normal_icon(self):
        d = display(21, 4)
        self.assertEqual(label.label_text(d), "21% · 4%")
        self.assertEqual(label.icon_name(d), label.NORMAL_ICON)

    def test_seventy_five_marks_only_the_affected_number(self):
        self.assertEqual(label.label_text(display(78, 4)), "78%! · 4%")
        self.assertEqual(label.label_text(display(10, 75)), "10% · 75%!")

    def test_ninety_swaps_to_the_alarm_icon(self):
        d = display(12, 90)
        self.assertEqual(label.icon_name(d), label.ALARM_ICON)
        self.assertEqual(label.label_text(d), "12% · 90%!")

    def test_unknown_and_reset_windows(self):
        self.assertEqual(label.label_text(display(42, None)), "42% · --")
        self.assertEqual(label.label_text(display(95, 40, now=FIVE_RESET + timedelta(seconds=60))), "0% · 40%")
        self.assertEqual(label.label_text(make(None, NOW)), "-- · --")

    def test_bar_text_has_ten_cells(self):
        self.assertEqual(label.bar_text(0), "▱▱▱▱▱▱▱▱▱▱")
        self.assertEqual(label.bar_text(0.42), "▰▰▰▰▱▱▱▱▱▱")
        self.assertEqual(label.bar_text(1), "▰▰▰▰▰▰▰▰▰▰")
        self.assertEqual(label.bar_text(0.04), "▱▱▱▱▱▱▱▱▱▱")
        self.assertEqual(label.bar_text(0.05), "▰▱▱▱▱▱▱▱▱▱")

    def test_menu_rows(self):
        rows = label.menu_rows(display(42, 18))
        self.assertEqual(rows, [
            ("5-hour  42% · resets in 2h 21m", "▰▰▰▰▱▱▱▱▱▱"),
            ("7-day  18% · resets in 6d 09h", "▰▰▱▱▱▱▱▱▱▱"),
        ])

    def test_icons_exist_as_files(self):
        for name in (label.NORMAL_ICON, label.ALARM_ICON):
            self.assertTrue((label.ICON_DIR / f"{name}.svg").is_file(), name)

    def test_model_window_is_the_third_number(self):
        self.assertEqual(label.label_text(display(21, 4, model=5)), "21% · 4% · 5%")
        self.assertEqual(label.label_text(display(21, 4, model=91)), "21% · 4% · 91%!")
        self.assertEqual(label.icon_name(display(21, 4, model=91)), label.ALARM_ICON)
        rows = label.menu_rows(display(42, 18, model=5))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[2], ("Fable  5% · resets in 1d 07h", "▰▱▱▱▱▱▱▱▱▱"))
