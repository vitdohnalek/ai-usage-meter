# Design: Linux port of ai-usage-meter (Ubuntu / GNOME, WSL-ready)

Date: 2026-09-06. Fork of DanielZucha/ai-usage-meter at vitdohnalek/ai-usage-meter.
Approved in conversation section by section; built directly as an MVP by the
user's instruction ("build it, then polish").

## Goal

The same meter as upstream, on Ubuntu 24.04 / GNOME 46 (Wayland): Claude
Code's statusline hook writes a snapshot, a tray app shows the Claude glyph
with the 5-hour and 7-day utilization, and the terminal line shows model,
effort and context. No credential is ever read. The fork is Linux-only; the
Swift tree is removed and README points to upstream for macOS.

## Decisions (with the alternatives set aside)

- **Runtime: Python 3.12 + PyGObject.** Already present with the
  AppIndicator3 binding; core logic headless-testable. Set aside: GNOME Shell
  extension (not testable, GNOME-version coupled), Node (needs a native tray
  library), Swift on Linux (no toolchain, no SwiftUI).
- **Tray host: StatusNotifierItem via AppIndicator3** served by the enabled
  ubuntu-appindicators extension. Wayland has no other tray protocol.
- **Tray label: icon + text label, icon carries the alarm.** GNOME labels
  cannot be bold, so a window at >= 75 gets a trailing `!`; at >= 90 the icon
  swaps to the inverted alarm variant. Set aside: one wide rendered PNG
  (may be squashed to a square by the extension), numbers only.
- **Topology: 30 s poll timer, mirror of the Mac app.** The file is the sole
  source of truth so a future Windows-side WSL reader works the same way.
  Set aside: GFileMonitor (needs directory watch + debounce + reconciling
  poll, integration-only tests), hook push over DBus/socket (new failure
  surface inside the never-block hook).
- **Packaging: plain package + Makefile copy, no pip.** The tray needs the
  system-owned PyGObject typelibs, so a venv or zipapp cannot host it;
  Ubuntu's externally-managed marker makes pip machine-dependent. Package
  copied to `~/.local/share/ai-usage-meter`, two shims in `~/.local/bin`.
- **Launch at login: XDG autostart `.desktop`.** Set aside: systemd --user
  unit (crash restart and journal, one extra session assumption); can be
  added later.
- **Snapshot path: `${XDG_STATE_HOME:-~/.local/state}/ai-usage-meter/snapshot.json`.**
  Mutable runtime state per XDG; on ext4 so the atomic rename and flock the
  store relies on hold, and reachable from Windows via `\\wsl$`.
- **Tests: standard-library unittest.** pytest is not installed and
  `make test` must need nothing.
- **Hook replaces the user's existing `statusline-command.sh`** (agreed);
  the installer still only prints the settings snippet.
- **WSL: hook only, this pass.** `make install-hook` installs the hook
  without the tray. A Windows-side tray reading the snapshot across
  `\\wsl$` is a later spec.

## Layout

    ai_usage_meter/
      core/       clamp, snapshot, payload, merge, store, countdown, display,
                  line, hook_runner        (stdlib only; one-to-one with MeterCore)
      hook.py     statusline entrypoint: stdin -> HookRunner -> one line, exit 0
      tray/       label.py (pure: label text, icon name, bar text, rows)
                  app.py   (Gtk.Application + AppIndicator3, 30 s timer)
      assets/     ai-usage-meter-symbolic.svg, ai-usage-meter-alarm.svg
    tests/        unittest modules mirroring the Swift suites + hook CLI test
    packaging/    autostart .desktop template
    Makefile      test / install / install-hook / install-tray / uninstall / snippet

## Contracts carried over unchanged

- Statusline line `<model> · <effort> · ⛁ <n>%`; effort omitted when absent,
  `--` when unknown, fallback model `Claude`, CR/LF flattened.
- Snapshot JSON byte-compatible with upstream: `schema_version` 1,
  provider-keyed, ISO-8601 dates, absent windows absent, sorted pretty keys.
- Merge: same window keeps max, later reset replaces, earlier discarded;
  hollow `rate_limits` leaves the snapshot alone.
- Clamp 0...1000 for percentages; non-finite -> unknown.
- Display: bold at >= 75, flip at >= 90, reset windows show 0 % derived from
  wall time, age buckets, "No snapshot yet".
- Store: temp file + `os.replace`, bounded non-blocking `flock` (0.25 s,
  then run anyway).

## Behaviour that differs from upstream, on purpose

- Dropdown is a text-only `Gtk.Menu` (the tray protocol transports text
  only): rows `5-hour  21% · resets in 2h 21m` plus a ten-cell bar
  `▰▰▱▱▱▱▱▱▱▱`; age line; Quit. Rows are inert.
- Bold becomes a `!` marker in the label; flip becomes an icon swap.
- A `resets_at` outside the range a `datetime` can hold drops that window
  instead of rendering a clamped countdown.

## Testing

`make test` runs `python3 -m unittest discover -s tests`. Each core module
has a test module porting the Swift cases; `tests/test_hook_cli.py` runs the
real hook script via subprocess with a temporary `XDG_STATE_HOME`. Tray
label logic is tested; GTK wiring is not, matching upstream.

## Out of scope

Windows-side WSL tray, threshold notifications, second provider, systemd
unit, per-model weekly window.
