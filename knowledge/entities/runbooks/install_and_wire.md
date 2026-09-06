# Runbook: install and wire the meter (Linux)

## Steps
1. `make test` must pass (unittest, no packages needed).
2. `make install` copies the package to `~/.local/share/ai-usage-meter`,
   writes the `ai-usage-meter-hook` and `ai-usage-meter-tray` shims to
   `~/.local/bin`, writes `~/.config/autostart/ai-usage-meter.desktop`,
   restarts the tray, and prints the settings snippet. `make install-hook`
   installs only the hook (WSL, no GNOME).
3. Paste the printed `statusLine` object into `~/.claude/settings.json`
   by hand. The installer never edits that file by
   [decision](../../decisions/2026-09-05_hook-is-a-swift-target.md).
4. Send one prompt in any Claude Code session. Every running session picks
   the new statusline up immediately and the snapshot appears within the
   same second; the tray updates on its next 30-second tick.

## Checks
- `cat ~/.local/state/ai-usage-meter/snapshot.json` shows
  `providers.claude` with two windows and ISO-8601 dates.
- The terminal status bar shows `<model> · <effort> · ⛁ <n>%`; the tray
  follows within 30 seconds.
- `pgrep -af ai-usage-meter-tray` shows one process; the autostart file
  exists.
- The 7-day number equals the `/usage` row "Current week (all models)", not
  the per-model row.

## Undo
- `make uninstall`, then remove the `statusLine` entry from settings.json.

## Toolchain traps
1. `make install-tray` fails fast with an apt hint when PyGObject or the
   AppIndicator3 typelib is missing. On Ubuntu 24.04 the package is
   `gir1.2-appindicator3-0.1` (the non-Ayatana one); the Ayatana typelib
   `gir1.2-ayatanaappindicator3-0.1` is a different namespace and is not
   what `tray/app.py` imports.
2. The tray icon is invisible if the appindicator GNOME extension is
   disabled: `gnome-extensions enable ubuntu-appindicators@ubuntu.com`.
3. Never run the tray under a venv: `gi` comes from the system dpkg
   packages only.

Related: [snapshot path](../../decisions/2026-09-06_snapshot-in-xdg-state-home.md)

**Last updated**: 2026-09-06
