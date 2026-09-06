# Source Registry
<!-- One row per immutable input under docs/. -->

| id | path | type | added | summary |
|----|------|------|-------|---------|
| S1 | docs/2026-09-05_usage-data-sources.md | fact report | 2026-09-05 | Local and web facts on how Claude usage is exposed (upstream, written on macOS) |
| S2 | docs/2026-09-05_statusline-probe.md | capture report | 2026-09-05 | Live statusline payloads from six sessions; findings F1-F6 plus a sample payload || S3 | docs/2026-09-05_statusline-probe-2.md | capture report | 2026-09-05 | Per-model weekly window is absent from the statusline payload; builder emits five_hour, seven_day, spend_limit only |
| S4 | docs/2026-09-06_statusline-probe-3.md | capture report | 2026-09-06 | 2.1.263 statusline still lacks the per-model window; the `get_usage` SDK control request returns it as `model_scoped`; flags that keep the probe side-effect free |

**Last updated**: 2026-09-06
