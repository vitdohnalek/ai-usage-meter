import json
import tempfile
import unittest
from pathlib import Path

from ai_usage_meter.core.hook_runner import run as run_hook
from ai_usage_meter.core.store import SnapshotStore
from ai_usage_meter.wintray import source
from tests.fixtures import CAPTURED, SAMPLE_PAYLOAD_JSON

UNC = r"\\wsl.localhost\Ubuntu-24.04\home\donv\.local\state\ai-usage-meter\snapshot.json"


class PathTests(unittest.TestCase):
    def test_distro_is_read_from_either_unc_spelling(self):
        self.assertEqual(source.distro_of(UNC), "Ubuntu-24.04")
        self.assertEqual(source.distro_of(r"\\wsl$\Debian\home\x\snapshot.json"), "Debian")
        self.assertEqual(source.distro_of(r"\\WSL.LOCALHOST\Debian\home\x\snapshot.json"), "Debian")
        self.assertEqual(source.distro_of("//wsl.localhost/Debian/home/x/snapshot.json"), "Debian")

    def test_other_paths_have_no_distro(self):
        for path in (r"C:\Users\donv\snapshot.json", "/home/donv/snapshot.json", r"\\server\share\x", ""):
            self.assertIsNone(source.distro_of(path), path)

    def test_proc_root_sits_beside_the_distro_root(self):
        self.assertEqual(source.proc_root(UNC), r"\\wsl.localhost\Ubuntu-24.04\proc")
        self.assertEqual(source.proc_root(r"\\wsl$\Debian\home\x\snapshot.json"), r"\\wsl$\Debian\proc")
        self.assertIsNone(source.proc_root(r"C:\Users\donv\snapshot.json"))

    def test_running_list_is_utf16_with_crlf(self):
        output = "Ubuntu-24.04\r\nDebian\r\n".encode("utf-16-le")
        self.assertEqual(source.parse_running(output), ["Ubuntu-24.04", "Debian"])
        self.assertEqual(source.parse_running(b"\xff\xfe" + "Debian\r\n".encode("utf-16-le")), ["Debian"])
        self.assertEqual(source.parse_running(b""), [])
        self.assertEqual(source.parse_running(b"\xff"), [])

    def test_running_list_is_utf8_when_wsl_utf8_is_set(self):
        self.assertEqual(source.parse_running(b"Ubuntu-24.04\r\nDebian\r\n"), ["Ubuntu-24.04", "Debian"])
        self.assertEqual(source.parse_running(b"\xff\xfe\xfd"), [])


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ai-usage-meter-wintray-")
        self.addCleanup(self.tmp.cleanup)
        self.config = Path(self.tmp.name) / "wintray.json"

    def test_env_wins_over_the_config_file(self):
        self.config.write_text(json.dumps({"snapshot_path": "from-file"}))
        self.assertEqual(source.configured_path({source.PATH_ENV: "from-env"}, self.config), "from-env")
        self.assertEqual(source.configured_path({}, self.config), "from-file")

    def test_missing_or_broken_config_yields_none(self):
        self.assertIsNone(source.configured_path({}, self.config))
        for content in ("{not json", "[]", json.dumps({"snapshot_path": 3}), json.dumps({"snapshot_path": ""})):
            self.config.write_text(content)
            self.assertIsNone(source.configured_path({}, self.config), content)


class SnapshotSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ai-usage-meter-wintray-")
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.path = root / "state" / "snapshot.json"
        self.cache = root / "cache" / "snapshot.json"
        run_hook(SAMPLE_PAYLOAD_JSON, SnapshotStore(self.path), CAPTURED)
        self.running = ["Ubuntu-24.04"]
        self.calls = []

    def make(self, distro="Ubuntu-24.04"):
        def list_running():
            self.calls.append(1)
            return self.running
        return source.SnapshotSource(self.path, cache_path=self.cache, distro=distro, list_running=list_running)

    def test_reads_the_snapshot_while_the_distro_runs(self):
        reading = self.make().read()
        self.assertTrue(reading.live)
        self.assertEqual(reading.snapshot.claude.five_hour.used_percentage, 21)
        self.assertEqual(self.cache.read_bytes(), self.path.read_bytes())

    def test_stopped_distro_is_never_touched_and_the_cache_answers(self):
        snapshots = self.make()
        snapshots.read()
        self.running = []
        self.path.unlink()  # a read now would fail; the point is that none happens
        reading = snapshots.read()
        self.assertFalse(reading.live)
        self.assertEqual(reading.snapshot.claude.five_hour.used_percentage, 21)

    def test_stopped_distro_without_a_cache_gives_nothing(self):
        self.running = []
        reading = self.make().read()
        self.assertEqual((reading.snapshot, reading.live), (None, False))
        self.assertFalse(self.cache.exists())

    def test_distro_names_compare_case_insensitively(self):
        self.running = ["ubuntu-24.04"]
        self.assertTrue(self.make().read().live)

    def test_failing_distro_query_counts_as_stopped(self):
        def boom():
            raise OSError("no wsl.exe")
        snapshots = source.SnapshotSource(self.path, cache_path=self.cache, distro="Ubuntu-24.04", list_running=boom)
        self.assertFalse(snapshots.read().live)

    def test_plain_path_needs_no_distro_check(self):
        reading = self.make(distro=None).read()
        self.assertTrue(reading.live)
        self.assertEqual(self.calls, [])

    def test_unreadable_snapshot_falls_back_to_the_cache_but_stays_live(self):
        snapshots = self.make()
        snapshots.read()
        self.path.write_bytes(b"{half a docu")
        reading = snapshots.read()
        self.assertTrue(reading.live)
        self.assertEqual(reading.snapshot.claude.five_hour.used_percentage, 21)
        self.assertNotEqual(self.cache.read_bytes(), self.path.read_bytes())

    def test_missing_snapshot_and_no_cache(self):
        self.path.unlink()
        reading = self.make().read()
        self.assertEqual((reading.snapshot, reading.live), (None, True))

    def test_cached_is_the_last_good_snapshot_without_touching_the_path(self):
        snapshots = self.make()
        self.assertIsNone(snapshots.cached())
        snapshots.read()
        self.path.unlink()
        self.assertEqual(snapshots.cached().claude.five_hour.used_percentage, 21)

    def test_unwritable_cache_does_not_break_the_read(self):
        snapshots = source.SnapshotSource(self.path, cache_path=Path("/proc/nope/snapshot.json"),
                                          distro=None, list_running=lambda: [])
        self.assertEqual(snapshots.read().snapshot.claude.five_hour.used_percentage, 21)


class LiveSessionTests(unittest.TestCase):
    """The Windows tray sees the distro's /proc through the share; when it
    cannot, no session file may be deleted on that account."""

    def setUp(self):
        from datetime import timedelta
        from ai_usage_meter.core import sessions
        from tests.test_sessions import fake_proc
        self.tmp = tempfile.TemporaryDirectory(prefix="ai-usage-meter-wintray-")
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.proc = root / "proc"
        fake_proc(self.proc, 1, "systemd", 0, 1)
        fake_proc(self.proc, 500, "claude", 1, 77)
        self.store = sessions.SessionStore(root / "sessions")

        def record(session_id, owner, age):
            return sessions.SessionRecord(
                session_id=session_id, name=session_id, project_dir=None, model=None,
                context_used_percentage=None, context_tokens=None, context_window_size=None,
                cache_warm=None, cache_expires_at=None, updated_at=CAPTURED - timedelta(seconds=age),
                owner_pid=owner[0] if owner else None, owner_start=owner[1] if owner else None)
        self.store.write(record("running", (500, 77), age=900))
        self.store.write(record("exited", (600, 88), age=10))
        self.store.write(record("ownerless-fresh", None, age=10))

    def names(self, proc):
        return sorted(r.session_id for r in source.live_sessions(self.store, CAPTURED, proc))

    def test_readable_proc_lists_by_process_and_prunes_the_gone(self):
        self.assertEqual(self.names(self.proc), ["ownerless-fresh", "running"])
        self.assertEqual(sorted(r.session_id for r in self.store.read_all()), ["ownerless-fresh", "running"])

    def test_unreadable_proc_lists_by_age_and_deletes_nothing(self):
        for proc in (Path(self.tmp.name) / "nowhere", None):
            self.assertEqual(self.names(proc), ["exited", "ownerless-fresh"], proc)
            self.assertEqual(len(self.store.read_all()), 3)

    def test_missing_session_directory_is_empty(self):
        from ai_usage_meter.core import sessions
        empty = sessions.SessionStore(Path(self.tmp.name) / "none")
        self.assertEqual(source.live_sessions(empty, CAPTURED, self.proc), [])
