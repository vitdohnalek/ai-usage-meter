# Decision: the hook merges, it does not overwrite

## What was decided
The hook reads the existing snapshot before writing. For each window of
the incoming provider payload it compares `resets_at` with the stored
window: a later `resets_at` replaces the stored window outright; the same
`resets_at` keeps the larger `used_percentage`; an earlier `resets_at` is
discarded as stale. The incoming `resets_at` (epoch seconds) is converted
to ISO-8601 on write. Session-scoped fields (model, context, cost) never
enter the snapshot; they describe one session and belong only on the
terminal line the hook prints.

## Why
Every running Claude Code session invokes the statusline command, and each
one reports the rate limits as of its own last API response. Idle sessions
therefore report stale, lower numbers alongside the live one, sometimes in
the same second. A last-writer-wins snapshot would flicker between stale
and fresh values. Within one window `used_percentage` only rises, so the
maximum across sessions is the true value; a new `resets_at` marks a new
window and legitimately restarts from a low number.

## Evidence
- Six sessions rendered concurrently at 11:43:08 with five-hour values of
  9, 9, 12, 18, 20 and 21 percent for the same `resets_at`. [S2:F3][S2:F4]
- `resets_at` is epoch seconds in the payload. [S2:F2]
- The statusline fires several times per turn, so the merge must stay a
  single small read plus one atomic write. [S2:F5]
- Concurrent invocations interleave their read-merge-write, so the cycle
  runs under an `flock(2)` on a sibling lock file; without it two writers
  in the same second can drop the higher value. [S2:F3]

## Alternatives considered
- Last writer wins: rejected, produces visible flicker between sessions.
- Trust only the session with the newest `captured_at`: rejected, the
  newest render is often an idle session reacting to a settings or
  focus event, not the session that just spent quota.
- Ignore payloads without a change in `cost.total_cost_usd`: rejected,
  cost is per session and cannot tell a fresh cross-session value apart
  from a stale one.

Related: [snapshot contract](2026-09-05_snapshot-contract.md),
[hook target](upstream/2026-09-05_hook-is-a-swift-target.md)

**Last updated**: 2026-09-05
