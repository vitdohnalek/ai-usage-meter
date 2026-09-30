# Decision: on a WSL host the tray runs on Windows and reads the snapshot over the share

## What was decided
A WSL install gets a tray on the Windows side: `ai_usage_meter/wintray`,
run as `pythonw -m ai_usage_meter.wintray.app` under the Windows Python
with pystray and Pillow. Every 30 seconds it reads `snapshot.json` and
`sessions/*.json` through `\\wsl.localhost\<distro>\...`, feeds them to the
same `core/display.py` and `tray/label.py` rules the Linux tray uses, and
shows:

- three notification-area icons, one per window, each with its percentage
  drawn in, kept in the order 5-hour, 7-day, per-model week (Windows
  orders icons by when they are added, so the tray adds them rightmost
  first and again whenever the set changes); a stripe under the number
  shows the level in the owner's bands: green to 20, blue to 50, orange to
  75, red to 90, purple above, grey when unknown; the model icon appears
  once that window is known;
- one dropdown, opened by a click on any icon: the Linux rows and bars,
  the sessions section, the age row.

It is a reader. It never writes the snapshot, never runs the usage probe,
and asks `wsl.exe -l --running -q` before each read so that it never
opens the share of a stopped distro; while the distro is stopped it shows
a local copy of the last snapshot (`%LOCALAPPDATA%\ai-usage-meter`),
marked "WSL stopped". Session liveness uses the distro's `/proc` through
the same share; when that is unreadable the tray lists by age and deletes
no session file. `make install-wintray` (from WSL) runs
`packaging/install-wintray.ps1`, which copies the package to
`%LOCALAPPDATA%`, writes the snapshot path to
`%APPDATA%\ai-usage-meter\wintray.json` and adds a Startup shortcut.

## Why
In WSL the terminal line was the only meter, visible only inside an open
session; the owner wanted the always-visible numbers the Ubuntu top bar
gives. The snapshot already sat on the Linux filesystem for this reader
([snapshot path](2026-09-06_snapshot-in-xdg-state-home.md)).

## Evidence
- On the owner's host (Windows 11 build 26200, Python 3.14, distro
  Ubuntu-24.04) the snapshot and `/proc/1/stat` both read through
  `\\wsl.localhost`; a read of the snapshot plus two session files took
  about 300 ms; `wsl.exe -l --running -q` answered in about 100 ms.
  [log 2026-09-30]
- After `make install-wintray` the process ran, logged no error, wrote the
  local copy, and Windows registered its icon with the tooltip
  `5-hour  3% · resets in 1h 49m`. [log 2026-09-30]
- `tests/test_wintray_view.py`, `test_wintray_source.py` and
  `test_wintray_render.py` pin the icon and menu rules, the distro gate,
  the cache fallback, the age-only session listing and the drawing.
- The owner chose three icons over one worst-number icon or a floating
  strip, and Python with pip over a dependency-free PowerShell script;
  after seeing the first version asked for the fixed order and for the
  stripe to show the level in five bands instead of naming the window.
  A capture of the tray corner showed `4`, `14`, `1` in that order.
  [log 2026-09-30]

## Alternatives considered
- One icon with the highest number: fewer slots, but hides which window is
  close. Rejected by the owner.
- A floating always-on-top text strip: closest to the GNOME label, no
  packages, but it fights the Windows 11 taskbar.
- A PowerShell `NotifyIcon` script: nothing to install, but the display
  rules would be rewritten untested in a second language.
- Running the GTK tray under WSLg: an AppIndicator has no place to go in
  the Windows notification area.
- Probing from Windows through `wsl.exe` on a timer: it would start the
  distro and keep the VM up; the hook already probes while a session is
  open ([detached probe](2026-09-30_hook-starts-the-probe-detached.md)).
- Importing `core/store.py` for the read: it imports `fcntl`, which
  Windows lacks; the tray decodes the file with `core/snapshot.py` alone.

## Consequences
- The numbers move only while a Claude Code session is open in WSL.
- Windows keys the taskbar-visibility choice by executable, so the three
  icons show as "Python" in the taskbar settings and start in the
  overflow.
- The click-opens-menu behaviour overrides pystray's private `_on_notify`;
  a pystray release that renames it brings back right-click only.
- pystray and Pillow are the repo's first pip dependencies; they live in
  the Windows user site only, the Linux side stays stdlib plus system GI.

Related: [Linux port](2026-09-06_linux-port-python-appindicator.md),
[session files](2026-09-06_session-files-beside-the-snapshot.md),
[runbook](../entities/runbooks/install_and_wire.md),
[gaps](../synthesis/gaps_and_leads.md)

**Last updated**: 2026-09-30
