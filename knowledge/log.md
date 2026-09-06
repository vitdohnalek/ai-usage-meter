# Knowledge Wiki Log
<!-- Append-only. Records all INGEST, QUERY, LINT operations. -->
<!-- Format: ## [YYYY-MM-DD] operation | description -->

## [2026-09-05] INIT | Wiki scaffolded during the founding grill session
- Scaffold created by hand from ~/.claude/templates/knowledge (tooling flavor)
- Seed source: docs/2026-09-05_usage-data-sources.md

## [2026-09-05] ingest | Usage data-source fact report
- source: docs/2026-09-05_usage-data-sources.md
- pages touched: decisions/2026-09-05_data-source-statusline-snapshot.md, decisions/2026-09-05_host-native-swift-menubarextra.md, synthesis/gaps_and_leads.md, index.md
- notes: two real quota sources exist (official statusline JSON, undocumented OAuth endpoint); only the first is credential-free

## [2026-09-05] ingest | Founding grill rounds one and two
- source: grill session answers (Daniel), assets/claude.svg
- pages touched: decisions/2026-09-05_snapshot-contract.md, decisions/2026-09-05_hook-is-a-swift-target.md, decisions/2026-09-05_app-refresh-and-display-rules.md, index.md, synthesis/gaps_and_leads.md
- notes: all frontier questions settled; one parked item (statusline probe) awaits go-ahead

## [2026-09-05] ingest | Statusline probe capture
- source: docs/2026-09-05_statusline-probe.md
- pages touched: decisions/2026-09-05_snapshot-merge-rule.md (new), decisions/2026-09-05_snapshot-contract.md, synthesis/gaps_and_leads.md, sources/source_registry.md, index.md
- notes: rate_limits confirmed on 2.1.261; resets_at is epoch seconds; every running session renders concurrently with its own stale value, so the hook merges per window (max within a window, later reset wins); grill closed

## [2026-09-05] ingest | v1 implementation on feature/v1-meter
- source: docs/superpowers/plans/2026-09-05-v1-meter.md and the resulting commits
- pages touched: decisions/2026-09-05_glyph-embedded-svg-string.md (new), entities/runbooks/install_and_wire.md (new), decisions/2026-09-05_app-refresh-and-display-rules.md, decisions/2026-09-05_data-source-statusline-snapshot.md, index.md
- notes: three-target SwiftPM package, 51 MeterCore tests, make install wiring; display rules revised the same day after Daniel's first look (75 bold, 90 flip, pill bars); two toolchain traps recorded in the runbook (stale private interfaces moved aside; CLT swift-testing wired through make test); seven_day confirmed as the all-models weekly row

## [2026-09-05] ingest | Tasks 15 and 16, terminal line
- source: the plan `docs/superpowers/plans/2026-09-05-v1-meter.md` Tasks 15 and 16
- pages touched: decisions/2026-09-05_hook-is-a-swift-target.md, entities/runbooks/install_and_wire.md, README.md
- notes: line format now `<model> · <effort> · U+26C1 <n>%`, 5h/7d dropped; test count 54 plus the fix-wave additions, 70 total from `make test`

## [2026-09-05] ingest | Probe 2, per-model weekly window
- source: docs/2026-09-05_statusline-probe-2.md (S3)
- pages touched: sources/source_registry.md, synthesis/gaps_and_leads.md, decisions/2026-09-05_data-source-statusline-snapshot.md, index.md (Now block)
- notes: Fable weekly row is usage-API only; statusline emits five_hour, seven_day, spend_limit; third meter deferred with a named trigger

## [2026-09-05] lint
- contradictions: none
- stale claims: none (superseded design bullets were folded on 2026-09-05; remaining mentions of the 70/90 outline design live in History sections only)
- orphan pages: none
- missing cross-refs: WIKI_SCHEMA.md and sources/source_registry.md carry no outbound link (utility pages; warning only)
- now-block: fresh (all five lines dated 2026-09-05, no later log entry contradicts them)
- claude-md: compliant (50 lines, static Now-block pointer, no mutable state)

## [2026-09-05] ingest | PR audit round 1
- source: six-agent audit verdicts (session), commits c822f0b and b7cc5be
- pages touched: decisions/2026-09-05_pr-1_audit.md (new), synthesis/gaps_and_leads.md, index.md (Now block, catalog), WIKI_SCHEMA.md
- notes: all six approve; HIGH freshness bug fixed; 72 tests

## [2026-09-05] ingest | Release v0.1.0
- source: PR #1 (devel, merge 27bc05d), PR #2 (main, merge 3d3c9e6), tag v0.1.0
- pages touched: index.md (Now block)
- notes: first release; no code change since the audit

## [2026-09-06] ingest | Linux port MVP (fork vitdohnalek/ai-usage-meter)
- source: docs/superpowers/specs/2026-09-06-linux-port-design.md; host probe of Ubuntu 24.04 / GNOME 46; architect recon of upstream v0.1.0
- pages touched: decisions/2026-09-06_linux-port-python-appindicator.md (new), decisions/2026-09-06_snapshot-in-xdg-state-home.md (new), decisions/2026-09-06_tray-label-marker-and-icon-swap.md (new), entities/runbooks/install_and_wire.md (rewritten for Linux), index.md (Now block, catalog)
- notes: Swift tree replaced by ai_usage_meter/ (Python, 87 unittest cases); hook and tray installed and wired on the host; WSL = hook only for now

## [2026-09-06] ingest | Fable weekly window as a third meter
- source: docs/2026-09-06_statusline-probe-3.md (S4); bundle read of Claude Code 2.1.263; three live get_usage probes
- pages touched: decisions/2026-09-06_fable-window-via-get-usage.md (new), decisions/2026-09-05_data-source-statusline-snapshot.md (amended), synthesis/gaps_and_leads.md (lead closed, one added), entities/runbooks/install_and_wire.md, sources/source_registry.md (S4), index.md (Now block, catalog)
- notes: snapshot gains optional seven_day_model {used_percentage, resets_at, model}; tray probes every 5 min off the GTK thread; hook unchanged; 108 tests

## [2026-09-06] lint | fork cleanup of upstream wording
- contradictions: none
- stale claims: README, CLAUDE.md, code docstrings and the GitHub description still called the project a macOS tool; fixed to describe the Linux port, with a credits section for upstream
- orphan pages: none; four upstream-only decision pages (Swift host, Swift hook target, SVG glyph string, PR-1 audit) moved to decisions/upstream/ with a banner; the upstream Swift implementation plan under docs/superpowers/plans/ removed
- missing cross-refs: links to the moved pages updated in index, decisions, runbook

## [2026-09-06] ingest | Top-bar numbers toggle
- source: user report (numbers missing from the panel while the dropdown had them); D-Bus check showed XAyatanaLabel still exported; gnome-shell-extension-appindicator indicatorStatusIcon.js _updateLabel read
- pages touched: decisions/2026-09-06_tray-label-marker-and-icon-swap.md (amended), entities/runbooks/install_and_wire.md (check, trap 5), synthesis/gaps_and_leads.md (lead), index.md (Now block)
- notes: tray/prefs.py stores {"show_numbers"} under $XDG_CONFIG_HOME/ai-usage-meter/tray.json; Gtk.CheckMenuItem in the dropdown; empty label when off; 115 tests

## [2026-09-06] ingest | Terminal line: limits, cache countdown, colour
- source: statusline docs field table (S1, re-read 2026-09-06: prompt_cache block, exceeds_200k_tokens, ANSI support)
- pages touched: decisions/2026-09-06_terminal-line-segments.md (new), entities/runbooks/install_and_wire.md (check), index.md (catalog, Now block)
- notes: payload gains PromptCache and exceeds_200k; line.render(payload, now, color); hook.py decides colour from NO_COLOR; 120 tests

## [2026-09-06] ingest | Terminal line: per-model week from the snapshot
- source: user request; snapshot already carries seven_day_model from the tray probe
- pages touched: decisions/2026-09-06_terminal-line-segments.md (amended), entities/runbooks/install_and_wire.md, index.md (catalog)
- notes: hook_runner reads the stored seven_day_model after the merge and passes it to line.render(model_window=); 122 tests

## [2026-09-06] ingest | statusLine snippet ships refreshInterval 60
- source: user feedback (the cache countdown must tick by default)
- pages touched: decisions/2026-09-06_terminal-line-segments.md (amended), entities/runbooks/install_and_wire.md
- notes: Makefile snippet target prints "refreshInterval": 60; applied to the host settings.json with a backup
