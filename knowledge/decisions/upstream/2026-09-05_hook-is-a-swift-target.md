# Decision: the statusline hook is a second executable target in the package

> Inherited from the upstream project this port started from. It describes
> the original implementation, not this repository; kept for the reasoning
> behind the shared contracts. See [the port decision](../2026-09-06_linux-port-python-appindicator.md).

## What was decided
The SwiftPM package has three targets: a library with the snapshot model,
parsing, formatting, and threshold rules; the menu-bar app; and a hook
executable that Claude Code invokes as its statusline command. The hook
reads the statusline JSON from stdin, writes the snapshot, and prints one
line: `<model> · <effort> · ⛁ <n>%`. It never blocks and never writes to
stderr; on any failure it prints whatever it can and exits zero.
`make install` copies the binary to `~/.local/bin` and prints the
settings.json snippet; it does not edit settings.json.

## Why
One language, one test suite, one definition of the schema. A compiled
hook starts in about 10 ms, which matters because it runs after every
turn inside Claude Code's render loop.

## Evidence
- No statusline exists today, so there is nothing to preserve. [S1]
- Python and jq are available but would split the schema across
  languages. [S1]

## Alternatives considered
- Python stdlib script: fine on speed, but a second language and a second
  copy of the schema.
- bash plus jq: fragile quoting, jq lives in an Anaconda prefix that may
  not be on PATH in the render loop.

Related: [snapshot contract](../2026-09-05_snapshot-contract.md)

## History
- 2026-09-05: added the optional effort word (`payload.effort.level`)
  between the model and the context segment, requested after first use.
  Omitted, not dashed, when the payload carries no effort block, since it
  is a session property rather than a meter. Same day: removed the 5h and
  7d segments from the printed line, since the menu bar already shows
  both rate-limit windows; the hook still merges `rate_limits` into the
  snapshot exactly as before, only the printed line got shorter.
- 2026-09-05: ctx replaced by U+26C1, the /context cylinder, at Daniel's
  request; he confirmed the glyph by eye against U+26C3.

**Last updated**: 2026-09-05
