# Decision: snapshot lives in `$XDG_STATE_HOME/ai-usage-meter/snapshot.json`

## What was decided
The snapshot path on Linux is `${XDG_STATE_HOME:-~/.local/state}/ai-usage-meter/snapshot.json`.
The document format is unchanged and byte-compatible with upstream.

## Why
XDG_STATE_HOME is the home for mutable runtime state that persists between
runs but is not user data; `~/.cache` would invite deletion and lose
in-window tracking. The path is always on the Linux filesystem (ext4), so
the store's atomic `rename(2)` and `flock` keep their semantics, and a
future Windows-side WSL reader can reach it through
`\\wsl$\<distro>\home\<user>\.local\state\ai-usage-meter\snapshot.json`.
Writing to `/mnt/c` instead would surrender both guarantees.

## Evidence
- Store contract: [snapshot-contract](2026-09-05_snapshot-contract.md),
  amended in the path clause only.
- `tests/test_store.py::test_default_path_follows_xdg_state_home`.

## Alternatives considered
- `~/.local/share` (XDG_DATA_HOME): closest to the Mac's Application
  Support, but semantically "data", not state.
- `~/.cache`: safe-to-delete by convention; wrong for a value the merge rule
  depends on.
- `/mnt/c/...` for WSL: DrvFs degrades rename atomicity and flock.

Amends: [snapshot-contract](2026-09-05_snapshot-contract.md).

**Last updated**: 2026-09-06
