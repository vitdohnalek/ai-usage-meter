#!/usr/bin/env python3
"""The Windows tray app: one notification-area icon per usage window, each
with its number drawn into it and a stripe coloured by its level, re-read from the WSL snapshot every 30
seconds. A click on any of them opens the same dropdown. Read-only: it
never probes and never writes inside the distro, except to prune session
files of processes that are gone. Run with ``pythonw -m
ai_usage_meter.wintray.app``; needs pystray and Pillow."""
import concurrent.futures
import ctypes
import logging
import logging.handlers
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pystray  # noqa: E402

from ai_usage_meter.core import display as display_rules  # noqa: E402
from ai_usage_meter.core.sessions import SessionStore  # noqa: E402
from ai_usage_meter.wintray import render, source, view  # noqa: E402

REFRESH_SECONDS = 30
IO_SECONDS = 15       # patience with the WSL share per refresh
START_SECONDS = 60    # all three icons must be up by then
QUIT_SECONDS = 6      # grace for pystray's threads after Quit
MUTEX_NAME = "Local\\AiUsageMeterWintray"
ERROR_ALREADY_EXISTS = 183
WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
LOG_FILE_NAME = "wintray.log"
KEYS = (view.FIVE_HOUR, view.SEVEN_DAY, view.MODEL)
PLACEHOLDER = view.IconSpec(view.FIVE_HOUR, view.UNKNOWN_TEXT, view.UNKNOWN_LEVEL, "AI usage")
QUIT_TEXT = "Quit AI Usage Meter"

log = logging.getLogger("ai_usage_meter.wintray")


class ClickIcon(pystray.Icon):
    """pystray opens the menu on a right click only; here any click does.
    ``menu_open`` is true while the popup is on screen, so the refresh
    thread can leave that menu alone."""
    menu_open = False
    built_lines = None

    def _on_notify(self, wparam, lparam):
        self.menu_open = True
        try:
            super()._on_notify(wparam, WM_RBUTTONUP if lparam == WM_LBUTTONUP else lparam)
        finally:
            self.menu_open = False


class MeterTray:
    def __init__(self, snapshots: source.SnapshotSource):
        self.snapshots = snapshots
        self.sessions = SessionStore.for_snapshot(snapshots.path)
        self.proc = source.proc_root(snapshots.path)
        self.lines = [display_rules.MeterDisplay.NO_SNAPSHOT_TEXT]
        self.shown = {}
        self.visible = []
        self.ready = set()
        self.lock = threading.Lock()
        self.stopping = threading.Event()
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.pending = None
        self.icons = {key: self._icon(key) for key in KEYS}

    def _icon(self, key):
        return ClickIcon(f"ai-usage-meter-{key}", icon=render.draw(PLACEHOLDER), title=PLACEHOLDER.tooltip,
                         menu=pystray.Menu(self._menu_items))

    def _menu_items(self):
        for line in self.lines:
            if line is view.SEPARATOR_LINE:
                yield pystray.Menu.SEPARATOR
            else:
                yield pystray.MenuItem(view.menu_text(line), None, enabled=False)
        yield pystray.Menu.SEPARATOR
        yield pystray.MenuItem(QUIT_TEXT, self.quit)

    def run(self):
        for key in KEYS[1:]:
            self.icons[key].run_detached(setup=lambda _, key=key: self._on_ready(key))
        threading.Thread(target=self._loop, daemon=True).start()
        _exit_later(START_SECONDS, 1, lambda: len(self.ready) < len(KEYS), "an icon did not start")
        self.icons[KEYS[0]].run(setup=lambda _, key=KEYS[0]: self._on_ready(key))

    def _on_ready(self, key):
        with self.lock:
            self.ready.add(key)
        self.refresh()

    def _loop(self):
        while not self.stopping.wait(REFRESH_SECONDS):
            self.refresh()

    def refresh(self):
        with self.lock:
            try:
                self._refresh()
            except Exception:
                log.exception("refresh failed")

    def _gather(self, now):
        """Everything read through the share, on the worker thread."""
        reading = self.snapshots.read()
        live = []
        if reading.live:
            try:
                live = source.live_sessions(self.sessions, now, self.proc)
            except Exception:
                log.exception("session listing failed")
        return reading, live

    def _gathered(self, now):
        """A share that stops answering must not freeze the tray: past the
        deadline the local copy answers, and the stuck read is picked up on
        a later tick instead of being started again."""
        if self.pending is None:
            self.pending = self.pool.submit(self._gather, now)
        try:
            result = self.pending.result(timeout=IO_SECONDS)
        except concurrent.futures.TimeoutError:
            log.warning("the WSL share did not answer within %s s", IO_SECONDS)
            return source.Reading(self.snapshots.cached(), False), []
        except Exception:
            self.pending = None
            raise
        self.pending = None
        return result

    def _refresh(self):
        now = datetime.now(timezone.utc)
        reading, live = self._gathered(now)
        state = display_rules.make(reading.snapshot, now)
        self.lines = view.menu_lines(state, live, now, live=reading.live)
        if len(self.ready) < len(KEYS):
            return
        specs = view.icon_specs(state, live=reading.live)
        for spec in specs:
            try:
                self._apply(self.icons[spec.key], spec)
            except Exception:
                log.exception("updating the %s icon failed", spec.key)
        self._arrange([spec.key for spec in specs])

    def _apply(self, icon, spec):
        """Redraw only what changed: every new picture costs a temporary
        .ico file on pystray's side, and rebuilding a menu destroys the old
        one, which must not happen while it is open."""
        shown = self.shown.get(spec.key)
        if shown is None or (shown.text, shown.level) != (spec.text, spec.level):
            icon.icon = render.draw(spec)
        if shown is None or shown.tooltip != spec.tooltip:
            icon.title = spec.tooltip
        self.shown[spec.key] = spec
        if icon.built_lines != self.lines and not icon.menu_open:
            icon.update_menu()
            icon.built_lines = self.lines

    def _arrange(self, keys):
        """Keep the icons in reading order, 5-hour leftmost. Windows places
        an icon by the moment it is added, each new one to the left of the
        last, so whenever the set changes all are removed and added again,
        rightmost first."""
        if keys == self.visible:
            return
        for key in self.visible:
            self.icons[key].visible = False
        for key in reversed(keys):
            self.icons[key].visible = True
        self.visible = keys

    def quit(self, *_):
        self.stopping.set()
        _exit_later(QUIT_SECONDS, 0)
        for icon in self.icons.values():
            threading.Thread(target=icon.stop, daemon=True).start()


def _exit_later(seconds, code, condition=lambda: True, reason=None):
    """pystray keeps non-daemon threads that never end when an icon fails
    to start or a read is stuck; a process left behind that way would hold
    the single-instance mutex until logoff. So leave the hard way."""
    def leave():
        if condition():
            if reason:
                log.error("%s; exiting", reason)
            logging.shutdown()
            os._exit(code)
    timer = threading.Timer(seconds, leave)
    timer.daemon = True
    timer.start()


def _log_thread_failure(args):
    log.error("thread %s failed", args.thread.name if args.thread else "?",
              exc_info=(args.exc_type, args.exc_value, args.exc_traceback))


def already_running() -> bool:
    """Holds a named mutex for the life of the process; a second instance
    finds it taken."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    already_running.handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    return ctypes.get_last_error() == ERROR_ALREADY_EXISTS


def configure_logging() -> None:
    """``pythonw`` has no console, so failures go to a small file beside
    the cached snapshot."""
    directory = source.default_cache_path().parent
    directory.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(directory / LOG_FILE_NAME, maxBytes=200_000, backupCount=1,
                                                   encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])


def main() -> int:
    configure_logging()
    threading.excepthook = _log_thread_failure
    try:
        if already_running():
            log.info("another instance is running; exiting")
            return 0
        path = source.configured_path(os.environ, source.default_config_path())
        if path is None:
            log.error("no snapshot path: set %s or run the installer", source.PATH_ENV)
            return 1
        log.info("reading %s", path)
        MeterTray(source.SnapshotSource(path, cache_path=source.default_cache_path())).run()
        return 0
    except Exception:
        log.exception("tray stopped")
        return 1


if __name__ == "__main__":
    sys.exit(main())
