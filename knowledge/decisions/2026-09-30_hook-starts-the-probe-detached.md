# Decision: where no tray runs, the hook starts the usage probe detached

## What was decided
When a statusline payload carries rate limits and no usage probe has
started in the last 360 seconds, the hook starts `ai_usage_meter/probe.py`
as a detached process (own session, no stdio) and prints its line without
waiting. `probe.py` runs the same `get_usage` request the tray runs
(`usage_probe.refresh`) and merges `seven_day_model` into the snapshot
under the shared lock; the next render shows the segment. The gate is
`probe.stamp` beside the snapshot: it holds the start time of the last
probe and is claimed under a non-blocking `flock`, so any number of
sessions rendering at once start one probe (`core/probe_gate.py`). The
tray stamps each of its own probe starts, and its 300-second timer is
shorter than the hook's 360, so a hook beside a running tray never
probes. `AI_USAGE_METER_NO_PROBE` in the hook's environment turns the
hook's probing off.

## Why
In WSL there is no tray, so nothing wrote `seven_day_model` and the
terminal line, the only meter there, lacked the Fable week. The hook is
the only process that runs on a hook-only install.

## Evidence
- On the owner's WSL host the snapshot held `five_hour` and `seven_day`
  only, while `usage_probe.capture` run by hand returned
  `ModelWindow(1, 2026-10-04T15:59:59Z, 'Fable')` in 2.3 s: the probe
  works there, nothing was starting it. [log 2026-09-30]
- After `make install-hook` the running session's own statusline wrote
  `probe.stamp` and, within the same minute, `seven_day_model` into the
  snapshot; the installed hook then printed `... · 5h 2% · Fable 1%`.
  [log 2026-09-30]
- The hook takes about 60 ms with or without a claim;
  `tests/test_hook_cli.py` proves the real hook returns before a slow
  probe answers and that the following render carries the segment;
  `tests/test_probe_gate.py` pins the gate (interval, busy stamp, garbage,
  clock set back, unwritable directory).
- The probe's `claude -p` loads no user settings
  (`--setting-sources project`), so it runs no statusline hook and cannot
  start another probe. [S4:F4]

## Alternatives considered
- Run the probe inline in the hook: still rejected, it would hold the
  render loop for one to two seconds
  ([Fable-window decision](2026-09-06_fable-window-via-get-usage.md)).
- A systemd user timer or cron entry for `probe.py`: works, but WSL
  distros often run without systemd, it probes while no session is open,
  and it is a second thing to install and remove.
- Decide by looking for a tray process instead of a stamp: couples the
  hook to the tray's process name and says nothing about whether that tray
  is actually probing.
- Use the snapshot's `captured_at` as the freshness signal: every
  statusline write overwrites it, so it does not say when the last probe
  ran.
- The same 300 seconds for both probers: their ticks would race and a
  tray host would probe twice every so often.

## Consequences
- A hook-only install spawns `claude -p` about every 6 minutes while at
  least one session is rendering, and never while none is.
- The stamp moves before the probe runs, so a failing probe is retried
  only after the interval, and silently
  ([gaps](../synthesis/gaps_and_leads.md)).
- The state directory gains `probe.stamp`; readers of the snapshot are
  unaffected.

Related: [Fable-window decision](2026-09-06_fable-window-via-get-usage.md),
[terminal line](2026-09-06_terminal-line-segments.md),
[runbook](../entities/runbooks/install_and_wire.md)

**Last updated**: 2026-09-30
