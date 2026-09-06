# ai-usage-meter (Linux)

A tray meter for Claude Code's 5-hour, 7-day, and per-model weekly
(Fable) rate-limit utilization on Ubuntu / GNOME, forked from
[DanielZucha/ai-usage-meter](https://github.com/DanielZucha/ai-usage-meter)
(the macOS original). It never touches a credential: Claude Code's own
statusline hook writes a small snapshot file, the tray asks Claude Code
itself for the per-model window, and the tray reads that file.

## How it works

1. Claude Code runs `ai-usage-meter-hook` as its statusline command after
   every API response, passing the documented statusline JSON on stdin.
2. The hook merges the `rate_limits` block into
   `~/.local/state/ai-usage-meter/snapshot.json` (or `$XDG_STATE_HOME`)
   and prints one line back to the terminal: `Fable 5.1 · high · ⛁ 12%`
   (effort omitted when Claude Code does not send one; the cylinder is the
   U+26C1 symbol /context uses for the context window).
3. Every 5 minutes the tray runs a throwaway `claude -p` process and sends
   it the SDK control request `get_usage`; Claude Code answers with the
   per-model weekly bucket that `/usage` shows as "Current week (Fable)"
   and the tray merges it into the same snapshot as `seven_day_model`.
   Claude Code talks to Anthropic with its own credential; the tray never
   sees one. The call takes about 1.3 s, runs no hooks, and leaves no
   transcript.
4. The tray app re-reads the snapshot every 30 seconds and shows the Claude
   glyph with `21% · 4% · 5%` (5-hour, 7-day, Fable week; the third number
   appears once the first probe has answered). A number at 75 percent or
   more gets a `!` (`78%! · 4% · 5%`); at 90 percent the glyph swaps to a
   red-on-white alarm icon. Clicking the item opens a menu with one row per
   window, a ten-cell bar, the countdown to reset, the snapshot age, and
   Quit. Windows that have reset show 0 percent until the next update.

The snapshot format is a superset of the macOS original: the extra
`seven_day_model` key is ignored by readers that do not know it.

Environment knobs for the tray: `AI_USAGE_METER_CLAUDE` (path to the
`claude` binary when it is not on PATH) and `AI_USAGE_METER_MODEL` (pick a
bucket by its display name when the account has several; default is the
first one).

## Requirements

Ubuntu 24.04 (or any GNOME on Wayland/X11) with:

- `python3` (3.10+), standard library only for the hook
- for the tray: `python3-gi`, `gir1.2-gtk-3.0`, `gir1.2-appindicator3-0.1`,
  and the `gnome-shell-extension-appindicator` extension enabled (Ubuntu
  ships it enabled)

`make install-tray` checks these and tells you what to install.

## Install

    make test
    make install

`make install` copies the package to `~/.local/share/ai-usage-meter`,
writes `ai-usage-meter-hook` and `ai-usage-meter-tray` to `~/.local/bin`,
adds an autostart entry, launches the tray, and prints the `statusLine`
snippet for `~/.claude/settings.json`. Paste that snippet yourself; the
installer never edits that file.

    make install-hook     hook only (WSL, servers, non-GNOME desktops)
    make install-tray     tray only
    make uninstall        remove everything except the snapshot

## WSL

Inside WSL run `make install-hook`: the terminal line and the snapshot work
unchanged. There is no Linux tray in WSL; the snapshot stays on the Linux
filesystem so a future Windows-side tray can read it at
`\\wsl$\<distro>\home\<user>\.local\state\ai-usage-meter\snapshot.json`.
That Windows tray is not built yet.

## Layout

    ai_usage_meter/core    schema, parsing, merge, storage, formatting (tested)
    ai_usage_meter/hook.py the statusline entrypoint
    ai_usage_meter/tray    label rules (tested) and the AppIndicator shell
    ai_usage_meter/assets  tray icons
    tests/                 unittest suite: make test
    packaging/             autostart .desktop template
    knowledge/             project wiki: decisions, runbooks, log
