# Decision: tray label is icon + text; `!` marks 75, icon swap marks 90

## What was decided
The indicator shows the Claude glyph as its icon and `21% · 4%` as its
text label. A window at or above 75 percent gets a trailing `!`
(`78%! · 4%`). At or above 90 percent the icon swaps from
`ai-usage-meter-symbolic` to `ai-usage-meter-alarm` (red glyph on a white
rounded square). The dropdown is a plain `Gtk.Menu`: two inert rows
(`5-hour  42% · resets in 2h 21m` over a ten-cell `▰▰▰▰▱▱▱▱▱▱` bar), the
age line, Quit.

## Why
AppIndicator labels are plain text (no Pango markup, no bold), and the
StatusNotifierItem menu protocol transports labels and icons only, so
pill-bar widgets cannot appear in the dropdown. The display rules
(`core/display.py`) are unchanged; only their rendering degrades.

## Evidence
- `tests/test_label.py` pins the marker, icon choice and bar text.
- [app-refresh-and-display-rules](2026-09-05_app-refresh-and-display-rules.md)
  for the thresholds themselves.

## Alternatives considered
- One wide rendered PNG as the whole label (exact Mac look): the
  appindicator extension may scale wide icons to a square; needs a spike.
  Deferred to polish.
- Numbers only, thresholds shown in the dropdown alone: loses the
  at-a-glance warning the tool exists for.

**Last updated**: 2026-09-06
