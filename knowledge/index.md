# ai-usage-meter knowledge index
<!-- Master catalog. Updated on every INGEST. Read at session start. -->
<!-- Generated 2026-09-05 during the founding grill session -->

## Now
- Phase: Linux port on main (108 tests, Python + AppIndicator) with a third meter, the Fable weekly window, fed by a `get_usage` probe from the tray (as of 2026-09-06)
- Active: first real-world use of the three-number tray; watch whether the `!` marker and alarm icon read well on the GNOME top bar and whether the probe keeps answering (as of 2026-09-06)
- Next: polish pass (hook cold start ~120 ms, icon rendering check, optional systemd unit, probe interval tuning) (as of 2026-09-06)
- Deferred: Windows-side WSL tray reading the snapshot over \wsl$; threshold notifications; Codex as a second provider (as of 2026-09-06)
- Known: decision pages dated 2026-09-05 were inherited from upstream; the ones that only described its implementation live under decisions/upstream/ (as of 2026-09-06)

## Sources
- [source_registry.md](sources/source_registry.md) -- registry of immutable inputs (S1-S4)

## Entities

### Components
### Integrations
### Data formats
### Runbooks
- [install_and_wire.md](entities/runbooks/install_and_wire.md) -- Linux: make install / install-hook, paste the snippet, verify, undo, toolchain traps

## Synthesis
- [gaps_and_leads.md](synthesis/gaps_and_leads.md) -- open questions and leads

## Decisions
- [2026-09-06_fable-window-via-get-usage.md](decisions/2026-09-06_fable-window-via-get-usage.md) -- third meter: the tray asks a throwaway `claude -p` for `get_usage` every 5 min and stores `seven_day_model`; amends the data-source decision's out-of-scope clause
- [2026-09-06_linux-port-python-appindicator.md](decisions/2026-09-06_linux-port-python-appindicator.md) -- Linux-only port in Python + PyGObject, AppIndicator tray, 30 s poll; supersedes the upstream host decisions
- [2026-09-06_snapshot-in-xdg-state-home.md](decisions/2026-09-06_snapshot-in-xdg-state-home.md) -- snapshot at $XDG_STATE_HOME/ai-usage-meter, on ext4 for a future WSL reader; amends the snapshot contract's path clause
- [2026-09-06_tray-label-marker-and-icon-swap.md](decisions/2026-09-06_tray-label-marker-and-icon-swap.md) -- icon + text label; `!` at 75, alarm icon at 90, text-only dropdown with block bars
- [2026-09-05_data-source-statusline-snapshot.md](decisions/2026-09-05_data-source-statusline-snapshot.md) -- read usage from the official statusline JSON via a snapshot file; never touch credentials
- [2026-09-05_snapshot-contract.md](decisions/2026-09-05_snapshot-contract.md) -- provider-keyed snapshot, atomic rename, absence preserved (path clause amended for Linux)
- [2026-09-05_app-refresh-and-display-rules.md](decisions/2026-09-05_app-refresh-and-display-rules.md) -- 30 s timer, filled glyph plus two numbers, bold at 75, label flips at 90, zero after reset, window-style dropdown with pill bars
- [2026-09-05_snapshot-merge-rule.md](decisions/2026-09-05_snapshot-merge-rule.md) -- every session writes; same window keeps the max, later reset replaces, epoch converted to ISO

### Inherited from upstream (implementation no longer applies)
- [2026-09-05_host-native-swift-menubarextra.md](decisions/upstream/2026-09-05_host-native-swift-menubarextra.md) -- native SwiftPM app with MenuBarExtra, no third-party runtime
- [2026-09-05_hook-is-a-swift-target.md](decisions/upstream/2026-09-05_hook-is-a-swift-target.md) -- hook is a compiled target sharing the model; prints one terminal line; installer never edits settings.json
- [2026-09-05_glyph-embedded-svg-string.md](decisions/upstream/2026-09-05_glyph-embedded-svg-string.md) -- glyph travels as a Swift string constant, byte-identical to assets/claude.svg; no resource bundle
- [2026-09-05_pr-1_audit.md](decisions/upstream/2026-09-05_pr-1_audit.md) -- v1 merges as audited; hollow rate_limits no longer refreshes captured_at; low notes recorded, not ticketed

**Last updated**: 2026-09-06
