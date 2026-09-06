import unittest
from datetime import timedelta

from ai_usage_meter.core.display import SEPARATOR, MeterDisplay, make
from ai_usage_meter.core.snapshot import ProviderUsage, Snapshot, UsageWindow
from tests.fixtures import CAPTURED as NOW, FIVE_RESET, SEVEN_RESET


def snapshot(five, seven, captured_ago=120):
    return Snapshot(schema_version=1, providers={
        "claude": ProviderUsage(
            five_hour=UsageWindow(five, FIVE_RESET) if five is not None else None,
            seven_day=UsageWindow(seven, SEVEN_RESET) if seven is not None else None,
            captured_at=NOW - timedelta(seconds=captured_ago),
            source="statusline",
        )
    })


class DisplayStateTests(unittest.TestCase):
    def test_normal_state_is_plain(self):
        display = make(snapshot(42, 18), NOW)
        self.assertEqual(display.five_hour.percent_text, "42%")
        self.assertEqual(display.seven_day.percent_text, "18%")
        self.assertFalse(display.five_hour.is_bold)
        self.assertFalse(display.seven_day.is_bold)
        self.assertFalse(display.is_flipped)
        self.assertEqual(display.five_hour.fraction, 0.42)
        self.assertEqual(display.seven_day.fraction, 0.18)
        self.assertEqual(display.five_hour.row_text, "5-hour  42% · resets in 2h 21m")
        self.assertEqual(display.seven_day.row_text, "7-day  18% · resets in 6d 09h")
        self.assertEqual(display.age_text, "Updated 2 min ago · statusline")

    def test_seventy_five_bolds_only_the_affected_number(self):
        display = make(snapshot(75, 74), NOW)
        self.assertTrue(display.five_hour.is_bold)
        self.assertFalse(display.seven_day.is_bold)
        self.assertFalse(display.is_flipped)

    def test_ninety_flips_the_label(self):
        display = make(snapshot(12, 90), NOW)
        self.assertTrue(display.is_flipped)
        self.assertTrue(display.seven_day.is_bold)
        self.assertFalse(make(snapshot(89, 89), NOW).is_flipped)

    def test_passed_reset_shows_zero(self):
        after = FIVE_RESET + timedelta(seconds=60)
        display = make(snapshot(95, 40), after)
        self.assertEqual(display.five_hour.percent, 0)
        self.assertEqual(display.five_hour.percent_text, "0%")
        self.assertFalse(display.five_hour.is_bold)
        self.assertEqual(display.five_hour.fraction, 0)
        self.assertEqual(display.five_hour.row_text, "5-hour  0% · reset")
        self.assertFalse(display.is_flipped)
        self.assertEqual(display.seven_day.percent, 40)

    def test_absent_window_shows_dashes(self):
        display = make(snapshot(42, None), NOW)
        self.assertEqual(display.five_hour.percent_text, "42%")
        self.assertEqual(display.seven_day.percent_text, "--")
        self.assertIsNone(display.seven_day.percent)
        self.assertEqual(display.seven_day.fraction, 0)
        self.assertEqual(display.seven_day.row_text, "7-day  --")

    def test_fraction_is_clamped_to_one(self):
        display = make(snapshot(130, 18), NOW)
        self.assertEqual(display.five_hour.fraction, 1)
        self.assertTrue(display.is_flipped)

    def test_no_snapshot_shows_dashes_and_no_age(self):
        display = make(None, NOW)
        self.assertEqual(display.five_hour.percent_text, "--")
        self.assertEqual(display.seven_day.percent_text, "--")
        self.assertFalse(display.is_flipped)
        self.assertEqual(display.age_text, MeterDisplay.NO_SNAPSHOT_TEXT)
        self.assertEqual(display.age_text, "No snapshot yet")

    def test_separator_is_the_single_source_of_truth(self):
        self.assertEqual(SEPARATOR, " · ")
