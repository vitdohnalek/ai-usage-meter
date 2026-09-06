import math
import unittest

from ai_usage_meter.core.clamp import clamped_int


class ClampTests(unittest.TestCase):
    def test_rounds_within_range(self):
        self.assertEqual(clamped_int(42.4), 42)
        self.assertEqual(clamped_int(42.5), 43)

    def test_clamps_below_lower_bound(self):
        self.assertEqual(clamped_int(-5), 0)

    def test_clamps_above_upper_bound(self):
        self.assertEqual(clamped_int(1_500), 1_000)

    def test_non_finite_becomes_none(self):
        self.assertIsNone(clamped_int(math.inf))
        self.assertIsNone(clamped_int(-math.inf))
        self.assertIsNone(clamped_int(math.nan))

    def test_huge_finite_value_clamps(self):
        self.assertEqual(clamped_int(1e300), 1_000)
        self.assertEqual(clamped_int(-1e300), 0)

    def test_honors_a_custom_range(self):
        self.assertEqual(clamped_int(1e300, 0, 1_000_000_000_000), 1_000_000_000_000)
        self.assertEqual(clamped_int(5, 10, 20), 10)

    def test_non_numbers_become_none(self):
        self.assertIsNone(clamped_int("12"))
        self.assertIsNone(clamped_int(None))
        self.assertIsNone(clamped_int(True))
