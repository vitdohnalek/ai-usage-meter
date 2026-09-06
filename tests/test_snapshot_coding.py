import json
import unittest

from ai_usage_meter.core.snapshot import (
    CLAUDE_PROVIDER_ID, CURRENT_SCHEMA_VERSION, ModelWindow, ProviderUsage, Snapshot, UsageWindow,
    decode, encode,
)
from tests.fixtures import CAPTURED, FIVE_RESET, MODEL_RESET, SEVEN_RESET


def sample():
    return Snapshot(
        schema_version=CURRENT_SCHEMA_VERSION,
        providers={
            CLAUDE_PROVIDER_ID: ProviderUsage(
                five_hour=UsageWindow(used_percentage=21, resets_at=FIVE_RESET),
                seven_day=UsageWindow(used_percentage=4, resets_at=SEVEN_RESET),
                captured_at=CAPTURED,
                source="statusline",
            )
        },
    )


class SnapshotCodingTests(unittest.TestCase):
    def test_round_trips_through_json(self):
        self.assertEqual(decode(encode(sample())), sample())

    def test_uses_snake_case_keys_and_iso8601_dates(self):
        text = encode(sample()).decode("utf-8")
        for key in ["schema_version", "providers", "five_hour", "seven_day",
                    "used_percentage", "resets_at", "captured_at", "source"]:
            self.assertIn(f'"{key}"', text)
        self.assertNotIn("schemaVersion", text)
        self.assertIn("2026-09-05T14:10:00Z", text)
        self.assertIn("2026-09-05T11:48:12Z", text)
        self.assertNotIn("1788617400", text)

    def test_output_is_pretty_and_sorted(self):
        text = encode(sample()).decode("utf-8")
        self.assertIn("\n", text)
        parsed = json.loads(text)
        self.assertEqual(list(parsed.keys()), sorted(parsed.keys()))

    def test_absent_window_is_absent_not_zero(self):
        snapshot = sample()
        snapshot.claude.seven_day = None
        text = encode(snapshot).decode("utf-8")
        self.assertNotIn("seven_day", text)
        decoded = decode(text.encode("utf-8"))
        self.assertIsNone(decoded.claude.seven_day)
        self.assertEqual(decoded.claude.five_hour.used_percentage, 21)

    def test_claude_accessor_reads_and_writes_the_provider_map(self):
        snapshot = Snapshot(schema_version=1, providers={})
        self.assertIsNone(snapshot.claude)
        snapshot.claude = sample().claude
        self.assertEqual(sorted(snapshot.providers), ["claude"])

    def test_decode_rejects_garbage_and_wrong_shapes(self):
        for bad in [b"{not json", b"[]", b'{"schema_version":1}',
                    b'{"schema_version":1,"providers":{"claude":{"captured_at":"x","source":"s"}}}']:
            with self.assertRaises(ValueError):
                decode(bad)

    def test_model_window_round_trips_and_is_optional(self):
        snapshot = sample()
        self.assertIsNone(decode(encode(snapshot)).claude.seven_day_model)
        snapshot.claude.seven_day_model = ModelWindow(5, MODEL_RESET, "Fable")
        text = encode(snapshot).decode("utf-8")
        self.assertIn('"seven_day_model": {', text)
        self.assertIn('"model": "Fable"', text)
        self.assertIn("2026-09-06T18:59:59Z", text)
        decoded = decode(text.encode("utf-8"))
        self.assertEqual(decoded.claude.seven_day_model.model, "Fable")
        self.assertEqual(decoded.claude.seven_day_model.used_percentage, 5)
        self.assertEqual(decoded.claude.seven_day_model.resets_at, MODEL_RESET.replace(microsecond=0))

    def test_model_window_with_bad_label_is_rejected(self):
        bad = b'{"schema_version":1,"providers":{"claude":{"captured_at":"2026-09-05T11:48:12Z","source":"s",' \
              b'"seven_day_model":{"used_percentage":5,"resets_at":"2026-09-06T18:59:59Z","model":7}}}}'
        with self.assertRaises(ValueError):
            decode(bad)
