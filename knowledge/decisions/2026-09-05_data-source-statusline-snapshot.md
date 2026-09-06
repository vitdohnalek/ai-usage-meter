# Decision: usage comes from the statusline JSON via a snapshot file

## What was decided
A Claude Code statusline hook receives the official statusline stdin JSON
after every API response and writes its `rate_limits` block (5-hour and
7-day utilization with reset times) to a local snapshot file. The menu-bar
app reads only that file. Version one never reads the Keychain and never
calls the undocumented `api/oauth/usage` endpoint. The snapshot is keyed by
provider so a second service can be added additively.

## Why
Daniel's reason for building his own meter was not wanting personal
credentials inside someone else's unmaintained code. The statusline path is
documented by Anthropic, needs no credential, and refreshes after every
Claude Code turn. Claude Code on this Mac is nearly all of his usage; the
occasional claude.ai chat is already included in the server-reported
percentage and appears at the next turn.

## Evidence
- Statusline docs list `rate_limits.five_hour` and `rate_limits.seven_day`
  with `used_percentage` and `resets_at` for Pro/Max subscribers. [S1]
- The endpoint is undocumented, 429s without a spoofed User-Agent, and
  external token refresh can break Claude Code's own credential. [S1]
- Utilization only changes when quota is consumed, so a stale snapshot plus
  a local countdown to `resets_at` renders correctly while idle. [S1]
- Verified 2026-09-05 after wiring: the statusline's seven_day (10 percent)
  matched /usage "Current week (all models)" (10 percent), not the
  per-model row (14 percent). [S2]
- Per-model weekly windows (the /usage "Current week (Fable)" row) are not
  in the statusline payload on 2.1.261; the only source is the usage API,
  so a third meter is out of scope until Claude Code forwards them. [S3:F1][S3:F3]
  Amended 2026-09-06: the tray now gets that window from Claude Code's own
  `get_usage` control request, still without touching a credential; see
  [the Fable-window decision](2026-09-06_fable-window-via-get-usage.md). [S4:F3]

## Alternatives considered
- Endpoint polling (what public tools do): exact even between turns, but
  requires reading the OAuth token and depends on an undocumented surface.
  Rejected for version one; kept as a possible fallback writer if staleness
  ever matters.
- Hybrid (statusline primary, endpoint fallback): rejected as unnecessary
  once Daniel confirmed Claude Code is nearly all of his usage.
- Transcript parsing (ccusage style): cannot report quota at all. Rejected.

Related: [host decision](upstream/2026-09-05_host-native-swift-menubarextra.md),
[gaps](../synthesis/gaps_and_leads.md)

**Last updated**: 2026-09-06
