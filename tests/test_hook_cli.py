"""End-to-end: the real hook script, as Claude Code would invoke it."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.fixtures import SAMPLE_PAYLOAD_JSON

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "ai_usage_meter" / "hook.py"


class HookCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ai-usage-meter-cli-")
        self.addCleanup(self.tmp.cleanup)
        self.env = {**os.environ, "XDG_STATE_HOME": self.tmp.name, "PYTHONPATH": str(REPO)}

    def run_hook(self, stdin: bytes):
        return subprocess.run([sys.executable, str(HOOK)], input=stdin, env=self.env,
                              capture_output=True, timeout=10)

    def test_prints_one_line_writes_snapshot_exits_zero_and_stays_silent(self):
        result = self.run_hook(SAMPLE_PAYLOAD_JSON)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, b"")
        self.assertEqual(result.stdout.decode("utf-8"), "Fable 5.1 · high · ⛁ 12%\n")
        path = Path(self.tmp.name) / "ai-usage-meter" / "snapshot.json"
        document = json.loads(path.read_text())
        self.assertEqual(document["schema_version"], 1)
        self.assertEqual(document["providers"]["claude"]["five_hour"]["used_percentage"], 21)
        self.assertEqual(document["providers"]["claude"]["five_hour"]["resets_at"], "2026-09-05T14:10:00Z")

    def test_garbage_still_prints_a_line_and_exits_zero(self):
        result = self.run_hook(b"\xff\xfe not json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, b"")
        self.assertEqual(result.stdout.decode("utf-8"), "Claude · ⛁ --\n")

    def test_lock_and_store_are_shared_across_runs(self):
        self.run_hook(SAMPLE_PAYLOAD_JSON)
        stale = b'{"rate_limits":{"five_hour":{"used_percentage":12,"resets_at":1788617400}}}'
        self.run_hook(stale)
        path = Path(self.tmp.name) / "ai-usage-meter" / "snapshot.json"
        document = json.loads(path.read_text())
        self.assertEqual(document["providers"]["claude"]["five_hour"]["used_percentage"], 21)
