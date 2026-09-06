# Runbook: install and wire the meter (Linux)

## Steps
1. `make test` must pass (unittest, no packages needed).
2. `make install` copies the package to `~/.local/share/ai-usage-meter`,
   writes the `ai-usage-meter-hook` and `ai-usage-meter-tray` shims to
   `~/.local/bin`, writes `~/.config/autostart/ai-usage-meter.desktop`,
   restarts the tray, and prints the settings snippet. `make install-hook`
   installs only the hook (WSL, no GNOME).
3. Paste the printed `statusLine` object into `~/.claude/settings.json`
   by hand; it carries `"refreshInterval": 60` so the cache countdown ticks
   while idle. The installer never edits that file by
   [decision](../../decisions/upstream/2026-09-05_hook-is-a-swift-target.md).
4. Send one prompt in any Claude Code session. Every running session picks
   the new statusline up immediately and the snapshot appears within the
   same second; the tray updates on its next 30-second tick.
5. Within a few seconds of the tray starting, the probe adds
   `seven_day_model` (the Fable week) to the snapshot; it re-asks every
   5 minutes. If the third number never appears, check that `claude` is on
   the tray's PATH or set `AI_USAGE_METER_CLAUDE=/path/to/claude` in the
   autostart environment.

## Checks
- `cat ~/.local/state/ai-usage-meter/snapshot.json` shows
  `providers.claude` with three windows and ISO-8601 dates; `source` is
  `statusline` or `usage` depending on the last writer.
- The terminal status bar shows `<model> · <effort> · ⛁ <n>% (<tokens>) ·
  5h <n>% · wk <n>%` (plus `Fable <n>%` once the tray's probe has written
  the snapshot, and `cache <countdown>` once a turn has run); the tray
  follows within 30 seconds.
- `pgrep -af ai-usage-meter-tray` shows one process; the autostart file
  exists.
- The 7-day number equals the `/usage` row "Current week (all models)";
  the third number equals "Current week (Fable)".
- `ls ~/.local/state/ai-usage-meter/sessions/` shows one JSON file per
  session that rendered lately; the dropdown's "Sessions (n)" section
  lists them with context and cache countdown; a session drops out on the
  tray tick after its `claude` process exits (each file carries
  `owner_pid`/`owner_start`; without them, three minutes after the last
  render).
- The dropdown's "Show numbers in top bar" item is ticked and
  `~/.config/ai-usage-meter/tray.json` holds `{"show_numbers": true}` after
  the first toggle.
- One-off probe by hand:
  `python3 -c 'from ai_usage_meter.core import usage_probe; print(usage_probe.capture("/tmp/x"))'`
  from the repo root prints a `ProviderUsage` with `seven_day_model` set.

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
4. Never add `--bare` to the probe: it disables OAuth and `get_usage`
   answers `rate_limits_available: false`.
5. If the icon shows but the numbers do not, the GNOME appindicator
   extension has dropped its text widget although the item still exports
   the label (check with `busctl --user get-property <bus name>
   /org/ayatana/NotificationItem/ai_usage_meter org.kde.StatusNotifierItem
   XAyatanaLabel`). Untick and re-tick "Show numbers in top bar": the empty
   label makes the extension destroy the widget, the next one rebuilds it.

Related: [snapshot path](../../decisions/2026-09-06_snapshot-in-xdg-state-home.md)

**Last updated**: 2026-09-06
