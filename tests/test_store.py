import fcntl
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from ai_usage_meter.core.snapshot import ProviderUsage, Snapshot, UsageWindow
from ai_usage_meter.core.store import LOCK_TIMEOUT, SnapshotStore, default_path
from tests.fixtures import CAPTURED, FIVE_RESET


def sample():
    return Snapshot(schema_version=1, providers={
        "claude": ProviderUsage(UsageWindow(21, FIVE_RESET), None, CAPTURED, "statusline")
    })


class SnapshotStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ai-usage-meter-tests-")
        self.addCleanup(self.tmp.cleanup)
        self.store = SnapshotStore(Path(self.tmp.name) / "nested" / "snapshot.json")

    def test_read_returns_none_when_missing(self):
        self.assertIsNone(self.store.read())

    def test_write_creates_directories_and_reads_back(self):
        self.store.write(sample())
        self.assertEqual(self.store.read(), sample())

    def test_write_leaves_no_temporary_file_behind(self):
        self.store.write(sample())
        self.assertEqual(os.listdir(self.store.path.parent), ["snapshot.json"])

    def test_overwrite_replaces_content(self):
        self.store.write(sample())
        second = sample()
        second.claude.five_hour.used_percentage = 99
        self.store.write(second)
        self.assertEqual(self.store.read().claude.five_hour.used_percentage, 99)

    def test_read_returns_none_on_garbage(self):
        self.store.path.parent.mkdir(parents=True)
        self.store.path.write_text("{not json")
        self.assertIsNone(self.store.read())

    def test_default_path_follows_xdg_state_home(self):
        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": "/x/state"}):
            self.assertEqual(default_path(), Path("/x/state/ai-usage-meter/snapshot.json"))
        with mock.patch.dict(os.environ, {"HOME": "/home/u"}, clear=True):
            self.assertEqual(default_path(), Path("/home/u/.local/state/ai-usage-meter/snapshot.json"))

    def test_exclusive_lock_runs_the_body_and_returns_its_value(self):
        self.assertEqual(self.store.with_exclusive_lock(lambda: 42), 42)
        self.assertTrue((self.store.path.parent / "snapshot.lock").exists())

    def test_exclusive_lock_releases_when_body_raises(self):
        with self.assertRaises(RuntimeError):
            self.store.with_exclusive_lock(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        start = time.monotonic()
        self.store.with_exclusive_lock(lambda: None)
        self.assertLess(time.monotonic() - start, LOCK_TIMEOUT)

    def test_exclusive_lock_gives_up_after_the_bound_and_runs_anyway(self):
        self.store.path.parent.mkdir(parents=True)
        external = os.open(self.store.path.parent / "snapshot.lock", os.O_CREAT | os.O_RDWR, 0o644)
        fcntl.flock(external, fcntl.LOCK_EX)
        self.addCleanup(os.close, external)
        ran = []
        start = time.monotonic()
        self.store.with_exclusive_lock(lambda: ran.append(True))
        elapsed = time.monotonic() - start
        self.assertTrue(ran)
        self.assertGreaterEqual(elapsed, LOCK_TIMEOUT)
        self.assertLess(elapsed, 1)

    def test_exclusive_lock_serializes_writers(self):
        count = [0]
        count_lock = threading.Lock()

        def bump(index):
            def body():
                current = self.store.read()
                value = current.claude.five_hour.used_percentage if current else 0
                nxt = Snapshot(schema_version=1, providers={})
                nxt.claude = ProviderUsage(UsageWindow(value + 1, FIVE_RESET), None, CAPTURED, f"test-{index}")
                self.store.write(nxt)
                with count_lock:
                    count[0] += 1
            self.store.with_exclusive_lock(body)

        threads = [threading.Thread(target=bump, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(count[0], 20)
        self.assertEqual(self.store.read().claude.five_hour.used_percentage, 20)
