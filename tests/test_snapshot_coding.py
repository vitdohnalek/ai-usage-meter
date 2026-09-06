import json
import unittest

from ai_usage_meter.core.snapshot import (
    CLAUDE_PROVIDER_ID, CURRENT_SCHEMA_VERSION, ProviderUsage, Snapshot, UsageWindow,
    decode, encode,
)
from tests.fixtures import CAPTURED, FIVE_RESET, SEVEN_RESET


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
