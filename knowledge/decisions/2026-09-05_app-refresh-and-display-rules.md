# Decision: app refresh cadence and display rules

## What was decided
- Refresh: a 30-second timer re-reads the snapshot and recomputes the
  countdown. No file-system watcher.
- Bar: `assets/claude.svg` (single path, 24x24 viewBox, currentColor),
  always filled, then the 5-hour and 7-day percentages, for example
  `42% · 18%`. The label is drawn as one `NSImage`: a template image in
  the normal state, an opaque-color image in the flipped state, since a
  template cannot carry its own background.
- Dropdown: a window-style panel (`menuBarExtraStyle(.window)`), one row
  per window with the row text over a pill bar filled to the utilization,
  then the age line with source and Quit. Nothing per-session (context,
  cost stay in the terminal statusline); a native menu cannot host the bars.
- Thresholds, monochrome only: at 75 percent the affected number turns
  bold; at 90 percent the whole label flips, a white background at half
  alpha with the glyph and the numbers in black. No color at any level,
  no notifications.
- Reset: once `resets_at` passes with no newer snapshot, that window shows
  zero. Absence before the first turn of a session leaves the previous
  snapshot standing. No snapshot at all shows the glyph with two dashes.
- Both the meter and the Claude desktop app keep their asterisk; no
  variant glyph.

## Why
A half-minute lag is invisible on a menu-bar number and the timer is
needed for the countdown anyway. Daniel asked for a clear, modern,
minimalist look; a weight change and a fill are the alerts that idiom
allows. Utilization only changes when quota is consumed, so a stale
snapshot plus a local countdown is correct while idle.

First look on 2026-09-05: Daniel asked for the star always filled with a
wider gap, bold at 75 rather than 70, the flipped label instead of a fill
change at 90, and pill bars in the dropdown. The outline-versus-filled
signal read as an unfilled icon rather than a state.

## Evidence
- Statusline windows drop after `resets_at`. [S1]
- Menu-bar icons must be template images to follow light and dark bars. [S1]
- Daniel's menu bar screenshot, 2026-09-05: all icons monochrome template
  style, Claude desktop asterisk already present.

## Alternatives considered
- File-system watch: instant, about 20 more lines, rejected as unneeded.
- Color at thresholds (system red at 95 percent): rejected for the
  minimalist constraint.
- macOS notifications: deferred; add only if a limit surprises Daniel in use.
- Per-model 7-day rows: impossible, only the undocumented endpoint has them.

Related: [snapshot contract](2026-09-05_snapshot-contract.md),
[host decision](upstream/2026-09-05_host-native-swift-menubarextra.md)

## History
- 2026-09-05: thresholds 70/90 with outline-to-filled glyph superseded the
  same day by 75 bold / 90 flip, always-filled glyph, window-style dropdown
  with pill bars, after the first installed build.

**Last updated**: 2026-09-05
