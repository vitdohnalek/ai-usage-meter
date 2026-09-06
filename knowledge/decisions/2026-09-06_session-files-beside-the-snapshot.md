# Decision: the session overview is one file per session, not a snapshot key

## What was decided
On every render the hook writes `sessions/<safe id>-<hash>.json` next to
the snapshot: session id, name (the session's own name, else the project
directory's basename), model, context percentage and tokens, prompt-cache
warmth and expiry, `updated_at`, and the pid and start time of the
`claude` process found by walking up the hook's parent chain in `/proc`.
The tray lists a session while that process still exists (same pid, same
start time, so a reused pid does not count) as inert dropdown rows
(`cartagenum  ⛁ 61% · cache 12m`; the token count stays in the
terminal line) under a `Sessions (n)`
header, hides the section when there are none, and deletes the files of
gone processes and anything older than a day. When the hook finds no
`claude` ancestor, the session is live for three minutes after its last
render. The snapshot contract is untouched.

## Why
The user wants to see every open session's context and remaining cache
time from the tray, and closed sessions must vanish at once: the first
version used "rendered in the last three minutes" and the user saw closed
sessions linger (2026-09-06). Each Claude Code session runs its own hook,
so a per-session file has exactly one writer and needs no lock, and the
hook's parent chain (`python3 -> bash -> claude`) names the process whose
lifetime is the session's. Putting sessions into the snapshot would have
grown the provider-keyed contract with unrelated, high-churn data and put
every hook run through the flock.

## Evidence
- Statusline payload fields `session_id`, `session_name`,
  `workspace.project_dir`, `cwd`, `prompt_cache.*` [S1].
- `tests/test_sessions.py` (records, store, liveness, pruning, unsafe ids),
  `tests/test_label.py::test_session_rows`, `tests/test_hook_runner.py`.

## Alternatives considered
- A `sessions` key inside the snapshot: rejected, see above.
- Reading Claude Code's own session files under `~/.claude/projects/`:
  rejected, that tree is transcripts and private state, and the meter
  never reads Claude Code's files.
- Time since last render as the only liveness test: kept as the fallback
  only; with a 60 s refresh it cannot drop a closed session in under about
  three minutes without flickering live ones.
- Scanning all processes from the tray: rejected; the tray only stats the
  one pid each file names, and matches its start time against pid reuse.

Related: [terminal line](2026-09-06_terminal-line-segments.md),
[snapshot contract](2026-09-05_snapshot-contract.md)

**Last updated**: 2026-09-06
