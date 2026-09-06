# Decision: the terminal line carries limits, cache state and colour

## What was decided
The statusline hook prints
`Fable 5.1 · high · ⛁ 12% (119k/1M) · 5h 21% · wk 4% · cache 43m`.
Three segments were added to the model, effort and context that were
already there:

- `5h <n>%` and `wk <n>%`, the same two rate-limit windows the tray shows,
  each present only when the payload carries it.
- `Fable <n>%`, the per-model week, read from the snapshot the tray's
  probe maintains (`seven_day_model`), never fetched by the hook itself;
  0 once its reset has passed, as the tray shows it; absent where no tray
  runs (WSL, servers).
- `cache <countdown>` from `prompt_cache.expires_at` while
  `prompt_cache.warm` is true; `cache warm` when the expiry is unknown;
  `cache cold` otherwise; nothing when `caching_observed` is false or the
  block is missing (Claude Code before 2.1.251, or providers that do not
  report cache tokens).
- ANSI colour: the context percentage is green under 50, yellow under 75,
  red from 75; the token count turns red when `exceeds_200k_tokens` is
  true; the limits use the tray's own thresholds (yellow at 75, red at
  90); `cache cold` is yellow. `NO_COLOR` in the hook's environment turns
  colour off. The decision is made in `hook.py`, the shell, so
  `hook_runner.run` and `line.render` stay pure and default to plain text.

## Why
In WSL or over SSH there is no tray, so the terminal line is the only
meter; the limits cost nothing because the hook already parses them. The
cache countdown answers the one question the percentages cannot: whether
replying now is cheaper than replying after a break. Colour is the only
emphasis a one-line status bar has.

## Evidence
- Field list and ANSI support: the statusline docs ([S1]); the
  `prompt_cache` block is documented as 2.1.251+ and computed client-side.
- `tests/test_line.py` pins every segment and colour; `tests/test_hook_cli.py`
  proves the real hook honours `NO_COLOR`.

## Alternatives considered
- Colouring the tray thresholds into the context percentage too (75 and
  90): rejected, a context window at 75 percent is already the point where
  compaction looms, so the terminal scale is tighter than the quota scale.
- A `>200k` text marker: rejected in favour of the red token count, which
  says the same without widening the line.
- Ticking the countdown from the hook: impossible, the hook runs only when
  Claude Code re-renders; documented `refreshInterval` instead.

Related: [tray label](2026-09-06_tray-label-marker-and-icon-swap.md),
[data source](2026-09-05_data-source-statusline-snapshot.md)

**Last updated**: 2026-09-06
