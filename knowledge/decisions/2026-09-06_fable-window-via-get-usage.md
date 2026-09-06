# Decision: the per-model weekly window comes from a `get_usage` control request

## What was decided
The tray asks a throwaway `claude -p` process (stream-json in and out,
`--setting-sources project --no-session-persistence --strict-mcp-config`,
cwd = the snapshot directory, `CLAUDECODE` unset) for the SDK control
request `get_usage` every 5 minutes, takes the first entry of
`rate_limits.model_scoped` (or the one named by `AI_USAGE_METER_MODEL`),
and merges it into the snapshot as `providers.claude.seven_day_model`
with `used_percentage`, `resets_at`, and the server-supplied `model` label.
The hook is unchanged. The tray label shows it as a third number
(`24% · 3% · 5%`), the menu as a third row named after the model.

## Why
The fork's owner wants the Fable weekly bucket next to the two existing
numbers. Probe 3 showed it still absent from the statusline on 2.1.263 but
present in the answer to `get_usage`, which Claude Code fulfils with its
own credential. This keeps the no-credential rule of the
[data-source decision](2026-09-05_data-source-statusline-snapshot.md) while
lifting its "out of scope" clause for the third meter.

## Evidence
- The bundle's statusline builder emits five_hour, seven_day, spend_limit
  only. [S4:F1]
- `get_usage` returns `model_scoped` with the Fable bucket; `--bare` breaks
  it; setting-sources=project skips hooks and leaves nothing behind; 1.3 s
  per call. [S4:F3][S4:F4][S4:F5]
- Live check 2026-09-06 after install: snapshot carries
  `seven_day_model: {model: Fable, used_percentage: 6, resets_at: 2026-09-06T19:00:00Z}`
  and a following statusline write kept it (merge test
  `test_statusline_write_keeps_the_model_window`).

## Alternatives considered
- Wait for Claude Code to forward the window into the statusline: no sign of
  it in 2.1.263; the lead in gaps_and_leads is closed instead.
- Call `api/oauth/usage` ourselves with the OAuth token from
  `~/.claude/.credentials.json`: exact and cheap, but reads a credential
  and depends on the undocumented endpoint. Rejected, as before.
- Run the probe from the hook: 1.3 s inside Claude Code's render loop is
  unacceptable; the hook must stay under ~150 ms. Rejected.
- Keep a long-lived `claude -p` process and re-send the request: saves
  startup time but holds a session open forever. Rejected for the MVP.

## Consequences
- The snapshot schema gains an optional key; schema_version stays 1 because
  readers that ignore unknown keys (ours, and upstream's Swift decoder)
  still work.
- `source` in the snapshot now alternates between `statusline` and `usage`
  depending on the last writer; the age row shows whichever wrote last.
- `AI_USAGE_METER_CLAUDE` overrides the `claude` binary path when it is not
  on the tray's PATH (autostart sessions may lack `~/.local/bin`; the
  fallback tries it explicitly).

Related: [data-source decision](2026-09-05_data-source-statusline-snapshot.md),
[label decision](2026-09-06_tray-label-marker-and-icon-swap.md),
[gaps](../synthesis/gaps_and_leads.md)

**Last updated**: 2026-09-06
