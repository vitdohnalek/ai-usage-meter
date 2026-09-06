# Decision: the session overview is one file per session, not a snapshot key

## What was decided
On every render the hook writes `sessions/<safe id>-<hash>.json` next to
the snapshot: session id, name (the session's own name, else the project
directory's basename), model, context percentage and tokens, prompt-cache
warmth and expiry, and `updated_at`. The tray lists the files updated
within the last three minutes as inert dropdown rows
(`cartagenum  ⛁ 61% (610k/1M) · cache 12m`) under a `Sessions (n)`
header, hides the section when there are none, and deletes files older
than a day. The snapshot contract is untouched.

## Why
The user wants to see every open session's context and remaining cache
time from the tray. Each Claude Code session runs its own hook, so a
per-session file has exactly one writer and needs no lock, and the
`refreshInterval` of 60 s already in the settings snippet makes "updated
in the last three minutes" a sound liveness test: a closed session goes
quiet within one interval. Putting sessions into the snapshot would have
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
- Detecting liveness by process: the hook has no parent pid it can trust
  and the tray must not scan processes; time since last render is enough.

Related: [terminal line](2026-09-06_terminal-line-segments.md),
[snapshot contract](2026-09-05_snapshot-contract.md)

**Last updated**: 2026-09-06
