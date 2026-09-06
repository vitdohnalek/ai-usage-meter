import os
import stat
import tempfile
import unittest
from pathlib import Path

from ai_usage_meter.core import usage_probe
from ai_usage_meter.core.snapshot import ModelWindow
from tests.fixtures import (
    CAPTURED, MODEL_RESET, USAGE_ERROR_JSONL, USAGE_NO_MODEL_JSONL, USAGE_RESPONSE_JSONL,
)

FAKE_CLAUDE = """#!/usr/bin/env python3
import json, os, sys, time
if os.environ.get("SLEEP"):
    time.sleep(float(os.environ["SLEEP"]))
request = json.loads(sys.stdin.readline())
assert request["request"]["subtype"] == "get_usage", request
assert "--no-session-persistence" in sys.argv, sys.argv
assert "CLAUDECODE" not in os.environ, "nested-session guard would fire"
open(os.environ["FAKE_CWD_OUT"], "w").write(os.getcwd())
sys.stdout.buffer.write(open(os.environ["FAKE_OUTPUT"], "rb").read())
"""


class ParseTests(unittest.TestCase):
    def test_first_model_bucket_wins_by_default(self):
        window = usage_probe.parse(USAGE_RESPONSE_JSONL)
        self.assertEqual(window, ModelWindow(5, MODEL_RESET, "Fable"))

    def test_utilization_is_rounded_to_an_int(self):
        self.assertEqual(usage_probe.parse(USAGE_RESPONSE_JSONL).used_percentage, 5)

    def test_named_model_is_picked(self):
        self.assertEqual(usage_probe.parse(USAGE_RESPONSE_JSONL, model="Opus").used_percentage, 61)
        self.assertIsNone(usage_probe.parse(USAGE_RESPONSE_JSONL, model="Sonnet"))

    def test_error_or_empty_responses_yield_nothing(self):
        self.assertIsNone(usage_probe.parse(USAGE_ERROR_JSONL))
        self.assertIsNone(usage_probe.parse(USAGE_NO_MODEL_JSONL))
        self.assertIsNone(usage_probe.parse(b""))
        self.assertIsNone(usage_probe.parse(b"{not json"))

    def test_bucket_without_reset_is_skipped(self):
        text = USAGE_RESPONSE_JSONL.replace(b'"resets_at":"2026-09-06T18:59:59.988722+00:00"}', b'"resets_at":null}', 1)
        self.assertEqual(usage_probe.parse(text).model, "Opus")

    def test_request_is_one_line_of_json(self):
        data = usage_probe.request()
        self.assertTrue(data.endswith(b"\n"))
        self.assertNotIn(b"\n", data[:-1])
        self.assertIn(b'"get_usage"', data)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.script = root / "claude"
        self.script.write_text(FAKE_CLAUDE)
        self.script.chmod(self.script.stat().st_mode | stat.S_IXUSR)
        self.output = root / "output.jsonl"
        self.output.write_bytes(USAGE_RESPONSE_JSONL)
        self.cwd_out = root / "cwd.txt"
        self.cwd = root / "state"
        self.env = {
            **os.environ, "CLAUDECODE": "1",
            "FAKE_OUTPUT": str(self.output), "FAKE_CWD_OUT": str(self.cwd_out),
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_capture_returns_only_the_model_window(self):
        usage = usage_probe.capture(self.cwd, claude=str(self.script), now=CAPTURED, environ=self.env)
        self.assertEqual(usage.seven_day_model, ModelWindow(5, MODEL_RESET, "Fable"))
        self.assertIsNone(usage.five_hour)
        self.assertIsNone(usage.seven_day)
        self.assertEqual(usage.captured_at, CAPTURED)
        self.assertEqual(usage.source, usage_probe.SOURCE)

    def test_capture_runs_in_the_given_directory_and_creates_it(self):
        usage_probe.capture(self.cwd, claude=str(self.script), environ=self.env)
        self.assertEqual(Path(self.cwd_out.read_text()).resolve(), self.cwd.resolve())

    def test_model_env_narrows_the_pick(self):
        env = {**self.env, usage_probe.MODEL_ENV: "Opus"}
        usage = usage_probe.capture(self.cwd, claude=str(self.script), environ=env)
        self.assertEqual(usage.seven_day_model.model, "Opus")

    def test_timeout_yields_none(self):
        env = {**self.env, "SLEEP": "5"}
        self.assertIsNone(usage_probe.capture(self.cwd, claude=str(self.script), timeout=0.3, environ=env))

    def test_missing_binary_yields_none(self):
        self.assertIsNone(usage_probe.capture(self.cwd, claude=str(Path(self.tmp.name) / "nope"), environ=self.env))

    def test_find_claude_prefers_the_env_override_then_path(self):
        self.assertEqual(usage_probe.find_claude({usage_probe.BINARY_ENV: "/x/claude"}), "/x/claude")
        self.assertEqual(usage_probe.find_claude({"PATH": self.tmp.name}), str(self.script))
