import unittest
from datetime import timedelta

from ai_usage_meter.core import merge
from ai_usage_meter.core.snapshot import (
    CURRENT_SCHEMA_VERSION, ProviderUsage, Snapshot, UsageWindow,
)
from tests.fixtures import CAPTURED, FIVE_RESET, SEVEN_RESET

RESET = FIVE_RESET
LATER_RESET = FIVE_RESET + timedelta(hours=5)


class SnapshotMergeTests(unittest.TestCase):
    def test_later_reset_replaces_outright(self):
        existing = UsageWindow(80, RESET)
        incoming = UsageWindow(3, LATER_RESET)
        self.assertEqual(merge.merge_window(existing, incoming), incoming)

    def test_same_reset_keeps_the_maximum(self):
        high = UsageWindow(21, RESET)
        low = UsageWindow(12, RESET)
        self.assertEqual(merge.merge_window(high, low), high)
        self.assertEqual(merge.merge_window(low, high), high)

    def test_earlier_reset_is_discarded_as_stale(self):
        existing = UsageWindow(3, LATER_RESET)
        stale = UsageWindow(90, RESET)
        self.assertEqual(merge.merge_window(existing, stale), existing)

    def test_absent_incoming_keeps_existing(self):
        existing = UsageWindow(40, RESET)
        self.assertEqual(merge.merge_window(existing, None), existing)

    def test_absent_existing_takes_incoming(self):
        incoming = UsageWindow(40, RESET)
        self.assertEqual(merge.merge_window(None, incoming), incoming)
        self.assertIsNone(merge.merge_window(None, None))

    def test_provider_merge_stamps_incoming_capture_time(self):
        existing = ProviderUsage(UsageWindow(21, RESET), UsageWindow(4, SEVEN_RESET), CAPTURED, "statusline")
        later = CAPTURED + timedelta(seconds=60)
        incoming = ProviderUsage(UsageWindow(12, RESET), None, later, "statusline")
        merged = merge.merge_provider(existing, incoming)
        self.assertEqual(merged.five_hour.used_percentage, 21)
        self.assertEqual(merged.seven_day.used_percentage, 4)
        self.assertEqual(merged.captured_at, later)

    def test_snapshot_merge_creates_the_document_when_missing(self):
        incoming = ProviderUsage(UsageWindow(21, RESET), None, CAPTURED, "statusline")
        merged = merge.merge_snapshot(None, "claude", incoming)
        self.assertEqual(merged.schema_version, CURRENT_SCHEMA_VERSION)
        self.assertEqual(merged.claude, incoming)

    def test_snapshot_merge_leaves_other_providers_alone(self):
        codex = ProviderUsage(None, None, CAPTURED, "other")
        snapshot = Snapshot(schema_version=1, providers={"codex": codex})
        incoming = ProviderUsage(UsageWindow(1, RESET), None, CAPTURED, "statusline")
        merged = merge.merge_snapshot(snapshot, "claude", incoming)
        self.assertEqual(merged.providers["codex"], codex)
        self.assertEqual(merged.claude, incoming)
        self.assertNotIn("claude", snapshot.providers, "merge must not mutate its input")
