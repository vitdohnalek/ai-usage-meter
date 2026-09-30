# Gaps and leads

## Open
- `schema_version` is written but never inspected on read, and there is no
  migration hook; becomes a P3 debt issue at the first `currentSchemaVersion`
  bump.

## Closed
- 2026-09-05: whether `rate_limits` arrives at all. Yes; see
  [the merge rule](../decisions/2026-09-05_snapshot-merge-rule.md) for
  the cross-session wrinkle the probe exposed.

## Leads
- Notifications at thresholds were deferred, not rejected. Trigger: a
  limit surprises Daniel in use.
- A second provider (Codex) would be an additional writer into the same
  provider-keyed snapshot. Nothing in version one should assume one provider.
- Exact-multiple countdown boundaries are untested (e.g. remaining time
  landing precisely on a day, hour, or minute mark). No trigger yet.
- No test exercises the lock being released when `body` throws inside
  `SnapshotStore.withExclusiveLock`. No trigger yet.
- The Quit menu item's keyboard shortcut (`q`) has no visible affordance in
  the dropdown. No trigger yet.
- Closed 2026-09-06: the Fable per-model weekly window is still not in the
  statusline payload on 2.1.263 ([S4:F1]) but the tray now reads it through
  the `get_usage` control request ([S4:F3],
  [decision](../decisions/2026-09-06_fable-window-via-get-usage.md)).
  Remaining lead: if a later Claude Code forwards it into the statusline
  `rate_limits` block, drop the probe and let the hook write it.
- The probe spawns `claude -p` every 5 minutes from the tray, or every 6
  or so from the hook where no tray runs (1.3 s each, 2.3 s measured in WSL
  on 2026-09-30). Trigger: if Anthropic ever rate-limits `get_usage` or the
  SDK control channel changes shape, the third number silently stops
  updating and its reset countdown runs out to 0 percent; watch `source` in
  the snapshot.
- A `resets_at` unit change upstream (seconds to milliseconds or ISO) would
  render a clamped huge countdown or drop the window silently. Trigger:
  Claude Code changes the unit; then reject values outside now-1d..now+60d.
- The GNOME appindicator extension once stopped rendering the label while
  the item still exported `XAyatanaLabel` (2026-09-06, GNOME 46, extension
  for shell 45/46). Its `_updateLabel` re-adds a dropped widget only on the
  next label change, so a toggle off/on repairs it (runbook trap 5). Trigger
  for a real fix: it recurs at login; then try a one-shot empty-then-set
  label two seconds after activation.
- A failed hook-started probe is silent by design and is not retried
  before the 6-minute gate reopens; nothing records why it failed. Trigger:
  the Fable segment goes missing on a hook-only install; then have
  `probe.py` leave its last outcome beside the stamp.
- Unverified on the Windows tray, because checking means stopping the
  distro the work ran in: (a) that the 30-second reads through
  `\\wsl.localhost` do not keep an otherwise idle distro alive, and (b)
  that a stopped distro really is left alone and the "WSL stopped" copy
  shows. Check: close every WSL terminal, wait two minutes, run
  `wsl -l --running` in PowerShell. If the distro never stops, read less
  often or only while a session file is fresh.
- Windows tray, still unconfirmed: that a left click opens the dropdown
  (it rides on pystray's private `_on_notify`), and that the icon order
  survives a reboot (Windows may remember positions; the order was right
  on two launches on 2026-09-30).
- Windows tray: a read that outlasts 15 s falls back to the local copy and
  the menu then says "WSL stopped" although the share is merely slow; the
  log has the true cause. Trigger: it shows up in use; then give the
  reading its own stale reason.

Related: [data-source decision](../decisions/2026-09-05_data-source-statusline-snapshot.md)

**Last updated**: 2026-09-30
