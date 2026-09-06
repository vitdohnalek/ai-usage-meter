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
