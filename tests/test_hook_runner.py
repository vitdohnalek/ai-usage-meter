import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from ai_usage_meter.core.hook_runner import run
from ai_usage_meter.core.snapshot import UsageWindow
from ai_usage_meter.core.store import SnapshotStore
from tests.fixtures import (
    CAPTURED, FIVE_RESET, NO_RATE_LIMITS_JSON, SAMPLE_PAYLOAD_JSON, SEVEN_RESET,
)


class HookRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ai-usage-meter-hook-tests-")
        self.addCleanup(self.tmp.cleanup)
        self.store = SnapshotStore(Path(self.tmp.name) / "snapshot.json")

    def test_writes_snapshot_and_returns_line(self):
        self.assertEqual(run(SAMPLE_PAYLOAD_JSON, self.store, CAPTURED), "Fable 5.1 · high · ⛁ 12% (119k/1M) · 5h 21% · wk 4%")
        snapshot = self.store.read()
        self.assertEqual(snapshot.claude.five_hour, UsageWindow(21, FIVE_RESET))
        self.assertEqual(snapshot.claude.seven_day, UsageWindow(4, SEVEN_RESET))
        self.assertEqual(snapshot.claude.captured_at, CAPTURED)

    def test_stale_session_does_not_lower_the_snapshot(self):
        run(SAMPLE_PAYLOAD_JSON, self.store, CAPTURED)
        stale = b'{"rate_limits":{"five_hour":{"used_percentage":12,"resets_at":1788617400},"seven_day":{"used_percentage":2,"resets_at":1789160400}}}'
        run(stale, self.store, CAPTURED + timedelta(seconds=5))
        snapshot = self.store.read()
        self.assertEqual(snapshot.claude.five_hour.used_percentage, 21)
        self.assertEqual(snapshot.claude.seven_day.used_percentage, 4)

    def test_payload_without_rate_limits_leaves_snapshot_untouched(self):
        run(SAMPLE_PAYLOAD_JSON, self.store, CAPTURED)
        before = self.store.read()
        self.assertEqual(run(NO_RATE_LIMITS_JSON, self.store, CAPTURED + timedelta(seconds=5)), "Fable 5.1 · ⛁ 3%")
        self.assertEqual(self.store.read(), before)

    def test_rate_limits_with_no_usable_window_leaves_snapshot_untouched(self):
        run(SAMPLE_PAYLOAD_JSON, self.store, CAPTURED)
        before = self.store.read()
        hollow = b'{"model":{"display_name":"Fable 5.1"},"rate_limits":{"five_hour":{"used_percentage":50},"seven_day":{"resets_at":1789160400}}}'
        self.assertEqual(run(hollow, self.store, CAPTURED + timedelta(seconds=5)), "Fable 5.1 · ⛁ -- · 5h 50%")
        self.assertEqual(self.store.read(), before)

    def test_garbage_input_still_returns_a_line_and_writes_nothing(self):
        self.assertEqual(run(b"garbage", self.store, CAPTURED), "Claude · ⛁ --")
        self.assertIsNone(self.store.read())

    def test_empty_input_still_returns_a_line(self):
        self.assertEqual(run(b"", self.store, CAPTURED), "Claude · ⛁ --")

    def test_unwritable_store_does_not_raise_or_change_the_line(self):
        store = SnapshotStore(Path("/proc/ai-usage-meter-cannot-write/snapshot.json"))
        self.assertEqual(run(SAMPLE_PAYLOAD_JSON, store, CAPTURED), "Fable 5.1 · high · ⛁ 12% (119k/1M) · 5h 21% · wk 4%")

    def test_huge_context_percentage_returns_a_line(self):
        self.assertEqual(run(b'{"context_window":{"used_percentage":1e300}}', self.store, CAPTURED), "Claude · ⛁ 1000%")

    def test_numeric_effort_level_still_writes_the_snapshot(self):
        data = b'{"effort":{"level":3},"rate_limits":{"five_hour":{"used_percentage":21,"resets_at":1788617400},"seven_day":{"used_percentage":4,"resets_at":1789160400}}}'
        self.assertEqual(run(data, self.store, CAPTURED), "Claude · ⛁ -- · 5h 21% · wk 4%")
        self.assertEqual(self.store.read().claude.five_hour, UsageWindow(21, FIVE_RESET))
