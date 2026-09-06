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
- The probe spawns `claude -p` every 5 minutes (1.3 s each). Trigger: if
  Anthropic ever rate-limits `get_usage` or the SDK control channel changes
  shape, the third number silently stops updating and its reset countdown
  runs out to 0 percent; watch `source` in the snapshot.
- A `resets_at` unit change upstream (seconds to milliseconds or ISO) would
  render a clamped huge countdown or drop the window silently. Trigger:
  Claude Code changes the unit; then reject values outside now-1d..now+60d.
- The GNOME appindicator extension once stopped rendering the label while
  the item still exported `XAyatanaLabel` (2026-09-06, GNOME 46, extension
  for shell 45/46). Its `_updateLabel` re-adds a dropped widget only on the
  next label change, so a toggle off/on repairs it (runbook trap 5). Trigger
  for a real fix: it recurs at login; then try a one-shot empty-then-set
  label two seconds after activation.

Related: [data-source decision](../decisions/2026-09-05_data-source-statusline-snapshot.md)

**Last updated**: 2026-09-06
