"""End-to-end: the real hook script, as Claude Code would invoke it."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from tests.fixtures import SAMPLE_PAYLOAD_JSON, USAGE_RESPONSE_JSONL
from tests.test_usage_probe import FAKE_CLAUDE

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "ai_usage_meter" / "hook.py"


class HookCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ai-usage-meter-cli-")
        self.addCleanup(self.tmp.cleanup)
        self.env = {**os.environ, "XDG_STATE_HOME": self.tmp.name, "PYTHONPATH": str(REPO), "NO_COLOR": "1",
                    "AI_USAGE_METER_NO_PROBE": "1"}

    def run_hook(self, stdin: bytes):
        return subprocess.run([sys.executable, str(HOOK)], input=stdin, env=self.env,
                              capture_output=True, timeout=10)

    def test_prints_one_line_writes_snapshot_exits_zero_and_stays_silent(self):
        result = self.run_hook(SAMPLE_PAYLOAD_JSON)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, b"")
        self.assertEqual(result.stdout.decode("utf-8"), "Fable 5.1 · high · ⛁ 12% (119k/1M) · 5h 21% · wk 4%\n")
        path = Path(self.tmp.name) / "ai-usage-meter" / "snapshot.json"
        document = json.loads(path.read_text())
        self.assertEqual(document["schema_version"], 1)
        self.assertEqual(document["providers"]["claude"]["five_hour"]["used_percentage"], 21)
        self.assertEqual(document["providers"]["claude"]["five_hour"]["resets_at"], "2026-09-05T14:10:00Z")

    def test_colours_unless_no_color_is_set(self):
        del self.env["NO_COLOR"]
        result = self.run_hook(SAMPLE_PAYLOAD_JSON)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, b"")
        self.assertIn(b"\x1b[32m12%\x1b[0m", result.stdout)
        self.assertTrue(result.stdout.endswith(b"wk 4%\n"))

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

    def test_no_probe_env_keeps_the_hook_from_spawning_one(self):
        self.run_hook(SAMPLE_PAYLOAD_JSON)
        self.assertFalse((Path(self.tmp.name) / "ai-usage-meter" / "probe.stamp").exists())

    def test_hook_spawns_a_probe_that_adds_the_model_week(self):
        """No tray anywhere: the hook's detached probe is the only writer of
        ``seven_day_model``, and the next render shows it."""
        root = Path(self.tmp.name)
        claude = root / "claude"
        claude.write_text(FAKE_CLAUDE)
        claude.chmod(0o755)
        (root / "output.jsonl").write_bytes(USAGE_RESPONSE_JSONL)
        del self.env["AI_USAGE_METER_NO_PROBE"]
        self.env.update({"AI_USAGE_METER_CLAUDE": str(claude), "CLAUDECODE": "1", "SLEEP": "3",
                         "PYTHONDEVMODE": "1",  # surfaces ResourceWarning on stderr
                         "FAKE_OUTPUT": str(root / "output.jsonl"), "FAKE_CWD_OUT": str(root / "cwd.txt")})
        started = time.monotonic()
        first = self.run_hook(SAMPLE_PAYLOAD_JSON)
        self.assertLess(time.monotonic() - started, 2.5, "the hook waited for the probe")
        self.assertEqual(first.stderr, b"")
        self.assertEqual(first.stdout.decode("utf-8"), "Fable 5.1 · high · ⛁ 12% (119k/1M) · 5h 21% · wk 4%\n")
        path = root / "ai-usage-meter" / "snapshot.json"
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if "seven_day_model" in json.loads(path.read_text())["providers"]["claude"]:
                break
            time.sleep(0.05)
        document = json.loads(path.read_text())
        self.assertEqual(document["providers"]["claude"]["seven_day_model"]["model"], "Fable")
        self.assertEqual(document["providers"]["claude"]["five_hour"]["used_percentage"], 21)
        second = self.run_hook(SAMPLE_PAYLOAD_JSON)
        self.assertEqual(second.stderr, b"")
        self.assertTrue(second.stdout.decode("utf-8").startswith(
            "Fable 5.1 · high · ⛁ 12% (119k/1M) · 5h 21% · wk 4% · Fable "), second.stdout)
