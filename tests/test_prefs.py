import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ai_usage_meter.tray import prefs


class PrefsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "nested" / "tray.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_defaults_show_numbers(self):
        self.assertTrue(prefs.Prefs().show_numbers)
        self.assertEqual(prefs.load(self.path), prefs.Prefs(show_numbers=True))

    def test_round_trip_creates_directory_and_leaves_no_temp_file(self):
        prefs.save(prefs.Prefs(show_numbers=False), self.path)
        self.assertEqual(prefs.load(self.path), prefs.Prefs(show_numbers=False))
        self.assertEqual(os.listdir(self.path.parent), ["tray.json"])
        self.assertEqual(json.loads(self.path.read_text()), {"show_numbers": False})

    def test_corrupt_or_wrong_typed_file_falls_back_to_defaults(self):
        self.path.parent.mkdir(parents=True)
        for body in ("{", "[]", '{"show_numbers": "no"}', '{"show_numbers": 0}', '{"other": 1}'):
            self.path.write_text(body)
            self.assertEqual(prefs.load(self.path), prefs.Prefs(), body)

    def test_default_path_follows_xdg_config_home(self):
        with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": "/cfg"}):
            self.assertEqual(prefs.default_path(), Path("/cfg/ai-usage-meter/tray.json"))
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.dict(os.environ, {"HOME": "/home/x"}):
                self.assertEqual(prefs.default_path(), Path("/home/x/.config/ai-usage-meter/tray.json"))


if __name__ == "__main__":
    unittest.main()
