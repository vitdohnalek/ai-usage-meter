import unittest
from datetime import timedelta

from ai_usage_meter.core import merge
from ai_usage_meter.core.snapshot import (
    CURRENT_SCHEMA_VERSION, ModelWindow, ProviderUsage, Snapshot, UsageWindow,
)
from tests.fixtures import CAPTURED, FIVE_RESET, MODEL_RESET, SEVEN_RESET

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

    def test_probe_write_keeps_the_statusline_windows(self):
        existing = ProviderUsage(UsageWindow(21, RESET), UsageWindow(4, SEVEN_RESET), CAPTURED, "statusline")
        probe = ProviderUsage(None, None, CAPTURED + timedelta(seconds=30), "usage",
                              seven_day_model=ModelWindow(5, MODEL_RESET, "Fable"))
        merged = merge.merge_provider(existing, probe)
        self.assertEqual(merged.five_hour.used_percentage, 21)
        self.assertEqual(merged.seven_day.used_percentage, 4)
        self.assertEqual(merged.seven_day_model, probe.seven_day_model)
        self.assertEqual(merged.source, "usage")

    def test_statusline_write_keeps_the_model_window(self):
        existing = ProviderUsage(None, None, CAPTURED, "usage", seven_day_model=ModelWindow(5, MODEL_RESET, "Fable"))
        hook = ProviderUsage(UsageWindow(30, RESET), None, CAPTURED + timedelta(seconds=30), "statusline")
        merged = merge.merge_provider(existing, hook)
        self.assertEqual(merged.seven_day_model.model, "Fable")
        self.assertEqual(merged.five_hour.used_percentage, 30)

    def test_model_window_follows_the_window_rules(self):
        old = ModelWindow(80, MODEL_RESET, "Fable")
        newer = ModelWindow(2, MODEL_RESET + timedelta(days=7), "Fable")
        self.assertEqual(merge.merge_window(old, newer), newer)
        self.assertEqual(merge.merge_window(old, ModelWindow(50, MODEL_RESET, "Fable")), old)
