import unittest

from ai_usage_meter.core.payload import StatuslinePayload
from ai_usage_meter.core.snapshot import UsageWindow
from tests.fixtures import (
    CAPTURED, FIVE_RESET, NO_RATE_LIMITS_JSON, ONLY_FIVE_HOUR_JSON, SAMPLE_PAYLOAD_JSON,
)


class StatuslinePayloadTests(unittest.TestCase):
    def test_decodes_the_real_capture(self):
        payload = StatuslinePayload.decode(SAMPLE_PAYLOAD_JSON)
        self.assertEqual(payload.model_display_name, "Fable 5.1")
        self.assertEqual(payload.effort_level, "high")
        self.assertEqual(payload.context_used_percentage, 12)
        self.assertEqual(payload.rate_limits.five_hour.used_percentage, 21)
        self.assertEqual(payload.rate_limits.five_hour.resets_at, 1_788_617_400)
        self.assertEqual(payload.rate_limits.seven_day.used_percentage, 4)

    def test_tolerates_missing_rate_limits(self):
        payload = StatuslinePayload.decode(NO_RATE_LIMITS_JSON)
        self.assertIsNone(payload.rate_limits)
        self.assertIsNone(payload.provider_usage(CAPTURED))

    def test_tolerates_an_empty_object(self):
        payload = StatuslinePayload.decode(b"{}")
        self.assertIsNone(payload.model_display_name)
        self.assertIsNone(payload.context_used_percentage)
        self.assertIsNone(payload.rate_limits)

    def test_rejects_non_json_and_non_objects(self):
        for bad in [b"not json", b"", b"[1,2]", b'"str"']:
            with self.assertRaises(ValueError):
                StatuslinePayload.decode(bad)

    def test_converts_to_provider_usage_with_epoch_dates_and_rounding(self):
        payload = StatuslinePayload.decode(ONLY_FIVE_HOUR_JSON)
        usage = payload.provider_usage(CAPTURED)
        self.assertEqual(usage.five_hour, UsageWindow(55, FIVE_RESET))
        self.assertIsNone(usage.seven_day)
        self.assertEqual(usage.captured_at, CAPTURED)
        self.assertEqual(usage.source, "statusline")

    def test_drops_a_window_missing_either_field(self):
        data = b'{"rate_limits":{"five_hour":{"used_percentage":10},"seven_day":{"used_percentage":4,"resets_at":1789160400}}}'
        usage = StatuslinePayload.decode(data).provider_usage(CAPTURED)
        self.assertIsNone(usage.five_hour)
        self.assertEqual(usage.seven_day.used_percentage, 4)

    def test_rate_limits_with_no_usable_window_is_no_usage(self):
        data = b'{"rate_limits":{"five_hour":{"used_percentage":10},"seven_day":{"resets_at":1789160400}}}'
        self.assertIsNone(StatuslinePayload.decode(data).provider_usage(CAPTURED))

    def test_huge_percentage_is_clamped_not_trapped(self):
        data = b'{"rate_limits":{"five_hour":{"used_percentage":1e300,"resets_at":1788617400}}}'
        usage = StatuslinePayload.decode(data).provider_usage(CAPTURED)
        self.assertEqual(usage.five_hour.used_percentage, 1_000)

    def test_bogus_reset_epoch_drops_that_window_only(self):
        data = b'{"rate_limits":{"five_hour":{"used_percentage":10,"resets_at":1e300},"seven_day":{"used_percentage":4,"resets_at":1789160400}}}'
        usage = StatuslinePayload.decode(data).provider_usage(CAPTURED)
        self.assertIsNone(usage.five_hour)
        self.assertEqual(usage.seven_day.used_percentage, 4)

    def test_numeric_effort_level_does_not_block_rate_limits_decoding(self):
        data = b'{"effort":{"level":3},"rate_limits":{"five_hour":{"used_percentage":21,"resets_at":1788617400}}}'
        payload = StatuslinePayload.decode(data)
        self.assertIsNone(payload.effort_level)
        self.assertEqual(payload.rate_limits.five_hour.used_percentage, 21)

    def test_wrong_typed_blocks_decode_independently(self):
        data = b'{"model":"Fable","context_window":[],"rate_limits":{"five_hour":"x","seven_day":{"used_percentage":4,"resets_at":1789160400}}}'
        payload = StatuslinePayload.decode(data)
        self.assertIsNone(payload.model_display_name)
        self.assertIsNone(payload.context_used_percentage)
        self.assertIsNone(payload.rate_limits.five_hour)
        self.assertEqual(payload.rate_limits.seven_day.used_percentage, 4)
