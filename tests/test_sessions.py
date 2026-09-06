import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ai_usage_meter.core import sessions
from ai_usage_meter.core.payload import StatuslinePayload
from tests.fixtures import CAPTURED as NOW, SAMPLE_PAYLOAD_JSON

CACHE_AT = datetime(2026, 9, 5, 12, 31, 12, tzinfo=timezone.utc)  # 1788611472
NAMED_JSON = (b'{"session_id":"abc-123","session_name":"harness work","cwd":"/x",'
              b' "workspace":{"project_dir":"/home/v/harness"},"model":{"display_name":"Opus 4.8"},'
              b' "context_window":{"used_percentage":61,"total_input_tokens":610000,"context_window_size":1000000},'
              b' "prompt_cache":{"warm":true,"caching_observed":true,"expires_at":1788611472}}')


class RecordTests(unittest.TestCase):
    def test_from_the_real_capture_names_by_directory(self):
        record = sessions.from_payload(StatuslinePayload.decode(SAMPLE_PAYLOAD_JSON), NOW)
        self.assertEqual(record.session_id, "f9d550b8-b03e-47b2-aa24-76d4af4f8a26")
        self.assertEqual(record.name, "ai-usage-meter")
        self.assertEqual(record.project_dir, "/home/vitek/Desktop/cartagenum/ai-usage-meter")
        self.assertEqual(record.model, "Fable 5.1")
        self.assertEqual(record.context_used_percentage, 12)
        self.assertEqual(record.context_tokens, 118695)
        self.assertEqual(record.context_window_size, 1_000_000)
        self.assertIsNone(record.cache_warm)
        self.assertIsNone(record.cache_expires_at)
        self.assertEqual(record.updated_at, NOW)

    def test_session_name_and_project_dir_win_over_cwd(self):
        record = sessions.from_payload(StatuslinePayload.decode(NAMED_JSON), NOW)
        self.assertEqual(record.name, "harness work")
        self.assertEqual(record.project_dir, "/home/v/harness")
        self.assertTrue(record.cache_warm)
        self.assertEqual(record.cache_expires_at, CACHE_AT)

    def test_no_session_id_means_no_record_and_fallbacks(self):
        self.assertIsNone(sessions.from_payload(StatuslinePayload.decode(b"{}"), NOW))
        self.assertIsNone(sessions.from_payload(None, NOW))
        record = sessions.from_payload(StatuslinePayload.decode(b'{"session_id":"deadbeef-1234"}'), NOW)
        self.assertEqual(record.name, "deadbeef")
        record = sessions.from_payload(StatuslinePayload.decode(b'{"session_id":"s","cwd":"/"}'), NOW)
        self.assertEqual(record.name, "/")

    def test_round_trip_and_tolerant_decode(self):
        record = sessions.from_payload(StatuslinePayload.decode(NAMED_JSON), NOW)
        self.assertEqual(sessions.decode(sessions.encode(record)), record)
        document = json.loads(sessions.encode(record))
        self.assertEqual(document["cache_expires_at"], "2026-09-05T12:31:12Z")
        self.assertEqual(document["updated_at"], "2026-09-05T11:48:12Z")
        for bad in (b"{", b"[]", b'{"session_id":"x"}', b'{"session_id":3,"updated_at":"2026-09-05T11:48:12Z"}',
                    b'{"session_id":"x","updated_at":"never"}'):
            with self.assertRaises(ValueError, msg=bad):
                sessions.decode(bad)
        minimal = sessions.decode(b'{"session_id":"x","updated_at":"2026-09-05T11:48:12Z","context_used_percentage":"?"}')
        self.assertEqual(minimal.name, "x")
        self.assertIsNone(minimal.context_used_percentage)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = sessions.SessionStore(Path(self.tmp.name) / "sessions")

    def record(self, session_id, at, name="n"):
        return sessions.SessionRecord(session_id=session_id, name=name, project_dir="/p", model="M",
                                      context_used_percentage=1, context_tokens=None, context_window_size=None,
                                      cache_warm=None, cache_expires_at=None, updated_at=at)

    def test_default_directory_sits_next_to_the_snapshot(self):
        self.assertEqual(sessions.SessionStore.for_snapshot(Path("/s/ai-usage-meter/snapshot.json")).directory,
                         Path("/s/ai-usage-meter/sessions"))

    def test_write_is_one_file_per_session_named_safely(self):
        self.store.write(self.record("../evil/../id 1", NOW))
        self.store.write(self.record("../evil/../id 1", NOW + timedelta(seconds=60)))
        self.store.write(self.record("second", NOW))
        names = sorted(os.listdir(self.store.directory))
        self.assertEqual(len(names), 2)
        for name in names:
            self.assertTrue(name.endswith(".json") and "/" not in name and ".." not in name, name)
        self.assertEqual(self.store.read_all()[0].updated_at, NOW + timedelta(seconds=60))

    def test_live_keeps_recent_sessions_and_skips_junk(self):
        self.store.write(self.record("fresh", NOW - timedelta(seconds=170)))
        self.store.write(self.record("stale", NOW - timedelta(seconds=190)))
        self.store.write(self.record("future", NOW + timedelta(seconds=30)))
        (self.store.directory / "junk.json").write_text("{")
        (self.store.directory / "notes.txt").write_text("x")
        self.assertEqual(sorted(r.session_id for r in self.store.live(NOW)), ["fresh", "future"])
        self.assertEqual(self.store.live(NOW, max_age_seconds=10), [r for r in self.store.live(NOW) if r.session_id == "future"])

    def test_prune_removes_old_files_only(self):
        self.store.write(self.record("old", NOW - timedelta(days=2)))
        self.store.write(self.record("new", NOW))
        (self.store.directory / "junk.json").write_text("{")
        self.store.prune(NOW)
        self.assertEqual(sorted(os.listdir(self.store.directory)), ["junk.json", sessions.file_name("new")])

    def test_missing_directory_reads_empty_and_prunes_quietly(self):
        self.assertEqual(self.store.live(NOW), [])
        self.store.prune(NOW)


if __name__ == "__main__":
    unittest.main()


def fake_proc(root: Path, pid: int, comm: str, ppid: int, start: int) -> None:
    (root / str(pid)).mkdir(parents=True, exist_ok=True)
    tail = " ".join(["0"] * 30)
    (root / str(pid) / "stat").write_text(f"{pid} ({comm}) S {ppid} 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 {start} {tail}\n")


class OwnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.proc = Path(self.tmp.name) / "proc"
        fake_proc(self.proc, 1, "systemd", 0, 1)
        fake_proc(self.proc, 4166, "gnome-terminal-", 1, 10)
        fake_proc(self.proc, 102456, "claude", 4166, 75177828)
        fake_proc(self.proc, 119439, "bash", 102456, 75900000)
        fake_proc(self.proc, 119451, "python3", 119439, 75900100)

    def test_walks_up_to_the_claude_process(self):
        self.assertEqual(sessions.find_owner(119451, proc=self.proc), (102456, 75177828))
        self.assertEqual(sessions.find_owner(119439, proc=self.proc), (102456, 75177828))

    def test_no_claude_ancestor_or_missing_proc_means_unknown(self):
        self.assertIsNone(sessions.find_owner(4166, proc=self.proc))
        self.assertIsNone(sessions.find_owner(424242, proc=self.proc))
        self.assertIsNone(sessions.find_owner(119451, proc=Path(self.tmp.name) / "nowhere"))

    def test_owner_alive_needs_same_pid_and_start_time(self):
        self.assertTrue(sessions.owner_alive(102456, 75177828, proc=self.proc))
        self.assertFalse(sessions.owner_alive(102456, 1, proc=self.proc))  # pid reused
        self.assertFalse(sessions.owner_alive(999999, 75177828, proc=self.proc))

    def test_from_payload_records_the_owner(self):
        record = sessions.from_payload(StatuslinePayload.decode(SAMPLE_PAYLOAD_JSON), NOW, owner=(102456, 75177828))
        self.assertEqual((record.owner_pid, record.owner_start), (102456, 75177828))
        self.assertEqual(sessions.decode(sessions.encode(record)), record)
        self.assertIsNone(sessions.decode(b'{"session_id":"x","updated_at":"2026-09-05T11:48:12Z","owner_pid":"7"}').owner_pid)

    def test_live_drops_a_session_whose_process_is_gone_at_once(self):
        store = sessions.SessionStore(Path(self.tmp.name) / "sessions")
        def record(session_id, owner, age=0):
            return sessions.SessionRecord(session_id, session_id, "/p", None, 1, None, None, None, None,
                                          NOW - timedelta(seconds=age), owner_pid=owner and owner[0],
                                          owner_start=owner and owner[1])
        store.write(record("running", (102456, 75177828)))
        store.write(record("running-but-quiet", (102456, 75177828), age=3600))
        store.write(record("closed", (777, 5)))
        store.write(record("reused-pid", (102456, 5)))
        store.write(record("unknown-owner-fresh", None, age=100))
        store.write(record("unknown-owner-stale", None, age=200))
        live = sorted(r.session_id for r in store.live(NOW, proc=self.proc))
        self.assertEqual(live, ["running", "running-but-quiet", "unknown-owner-fresh"])
        store.prune(NOW, proc=self.proc)
        self.assertEqual(sorted(r.session_id for r in store.read_all()),
                         ["running", "running-but-quiet", "unknown-owner-fresh", "unknown-owner-stale"])
