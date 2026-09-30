import fcntl
import os
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from ai_usage_meter.core import probe_gate
from tests.fixtures import CAPTURED


class ProbeGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ai-usage-meter-gate-tests-")
        self.addCleanup(self.tmp.cleanup)
        self.snapshot = Path(self.tmp.name) / "state" / "snapshot.json"

    def test_first_claim_wins_and_creates_the_stamp(self):
        self.assertTrue(probe_gate.claim(self.snapshot, CAPTURED))
        self.assertTrue(probe_gate.stamp_path(self.snapshot).exists())
        self.assertEqual(probe_gate.stamp_path(self.snapshot).parent, self.snapshot.parent)

    def test_claim_is_refused_until_the_interval_has_passed(self):
        probe_gate.claim(self.snapshot, CAPTURED)
        almost = CAPTURED + timedelta(seconds=probe_gate.HOOK_SECONDS - 1)
        self.assertFalse(probe_gate.claim(self.snapshot, almost))
        due = CAPTURED + timedelta(seconds=probe_gate.HOOK_SECONDS)
        self.assertTrue(probe_gate.claim(self.snapshot, due))
        self.assertFalse(probe_gate.claim(self.snapshot, due + timedelta(seconds=1)))

    def test_refused_claim_does_not_move_the_stamp(self):
        probe_gate.claim(self.snapshot, CAPTURED)
        probe_gate.claim(self.snapshot, CAPTURED + timedelta(seconds=200))
        self.assertTrue(probe_gate.claim(self.snapshot, CAPTURED + timedelta(seconds=probe_gate.HOOK_SECONDS)))

    def test_stamp_from_another_prober_defers_the_claim(self):
        probe_gate.stamp(self.snapshot, CAPTURED)
        self.assertFalse(probe_gate.claim(self.snapshot, CAPTURED + timedelta(seconds=300)))
        probe_gate.stamp(self.snapshot, CAPTURED + timedelta(seconds=300))
        self.assertFalse(probe_gate.claim(self.snapshot, CAPTURED + timedelta(seconds=600)))

    def test_unreadable_stamp_counts_as_due(self):
        self.snapshot.parent.mkdir(parents=True)
        for content in (b"", b"not a date", b"\xff\xfe"):
            probe_gate.stamp_path(self.snapshot).write_bytes(content)
            self.assertTrue(probe_gate.claim(self.snapshot, CAPTURED), content)

    def test_stamp_from_the_future_counts_as_due(self):
        probe_gate.stamp(self.snapshot, CAPTURED + timedelta(days=1))
        self.assertTrue(probe_gate.claim(self.snapshot, CAPTURED))

    def test_claim_is_refused_while_another_process_holds_the_stamp(self):
        self.snapshot.parent.mkdir(parents=True)
        descriptor = os.open(probe_gate.stamp_path(self.snapshot), os.O_CREAT | os.O_RDWR, 0o644)
        self.addCleanup(os.close, descriptor)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        self.assertFalse(probe_gate.claim(self.snapshot, CAPTURED))
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        self.assertTrue(probe_gate.claim(self.snapshot, CAPTURED))

    def test_unwritable_directory_refuses_without_raising(self):
        snapshot = Path("/proc/ai-usage-meter-cannot-write/snapshot.json")
        self.assertFalse(probe_gate.claim(snapshot, CAPTURED))
        probe_gate.stamp(snapshot, CAPTURED)
