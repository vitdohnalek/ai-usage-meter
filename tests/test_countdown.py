import unittest
from datetime import timedelta

from ai_usage_meter.core import countdown
from tests.fixtures import CAPTURED as NOW


class CountdownTests(unittest.TestCase):
    def test_days_and_hours(self):
        until = NOW + timedelta(days=4, hours=6, minutes=59)
        self.assertEqual(countdown.text(until, NOW), "4d 06h")

    def test_hours_and_minutes(self):
        self.assertEqual(countdown.text(NOW + timedelta(hours=1, minutes=2), NOW), "1h 02m")

    def test_minutes_only(self):
        self.assertEqual(countdown.text(NOW + timedelta(minutes=42), NOW), "42m")

    def test_under_a_minute(self):
        self.assertEqual(countdown.text(NOW + timedelta(seconds=30), NOW), "under 1m")

    def test_none_once_reset(self):
        self.assertIsNone(countdown.text(NOW, NOW))
        self.assertIsNone(countdown.text(NOW - timedelta(seconds=1), NOW))

    def test_age_buckets(self):
        self.assertEqual(countdown.age(NOW - timedelta(seconds=10), NOW), "just now")
        self.assertEqual(countdown.age(NOW - timedelta(minutes=3), NOW), "3 min ago")
        self.assertEqual(countdown.age(NOW - timedelta(hours=2), NOW), "2 h ago")
        self.assertEqual(countdown.age(NOW - timedelta(days=3), NOW), "3 d ago")

    def test_huge_reset_distance_does_not_crash(self):
        self.assertIsNotNone(countdown.text_for_seconds(1e300))

    def test_non_finite_reset_distance_returns_none(self):
        self.assertIsNone(countdown.text_for_seconds(float("inf")))
        self.assertIsNone(countdown.text_for_seconds(float("nan")))

    def test_huge_age_does_not_crash(self):
        self.assertEqual(countdown.age_for_seconds(1e300), "11574074 d ago")
        self.assertEqual(countdown.age_for_seconds(float("nan")), "just now")
