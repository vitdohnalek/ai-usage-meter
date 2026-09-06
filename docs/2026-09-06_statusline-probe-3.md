# Statusline probe 3 -- the per-model weekly window on 2.1.263

Run 2026-09-06 on Claude Code 2.1.263 (Max plan, Ubuntu 24.04) when the
fork's owner asked for the Fable weekly usage as a third meter. The bundle
was read directly (`strings`/byte search over the binary); three live
`get_usage` probes were run. Facts only.

## Findings

- F1. The statusline builder in 2.1.263 still emits only `five_hour`,
  `seven_day`, and (gateway only) `spend_limit`. Same as probe 2 on 2.1.261.
- F2. The client does hold the per-model bucket: the unified rate-limit
  header store has a `seven_day_overage_included` window, labelled
  "Fable limit" in the limit messages, and `/usage` renders it from the
  `limits[]` array of the usage endpoint. Neither reaches the statusline.
- F3. The SDK control channel exposes it. Sending
  `{"type":"control_request","request_id":"x","request":{"subtype":"get_usage","skip_behaviors":true}}`
  on stdin to `claude -p --input-format stream-json --output-format
  stream-json --verbose` returns one `control_response` line whose
  `response.rate_limits.model_scoped` is
  `[{"display_name":"Fable","utilization":5,"resets_at":"2026-09-06T18:59:59.988722+00:00"}]`.
  Claude Code makes the usage-endpoint call itself with its own OAuth
  credential; the caller never sees a token.
- F4. `--bare` skips OAuth entirely, so `get_usage` answers
  `rate_limits_available: false`. Not usable.
- F5. `--setting-sources project --no-session-persistence
  --strict-mcp-config` with an empty cwd runs no hooks, loads no MCP
  servers, and leaves no transcript; the response is the only stdout line.
  Wall time 1.3 s (1.75 s with hooks). The nested-session guard is avoided
  by unsetting `CLAUDECODE`.
- F6. `resets_at` in this payload is ISO-8601 with microseconds and a
  `+00:00` offset, not epoch seconds like the statusline. The Fable window
  reset (2026-09-06T19:00Z) differs from the all-models 7-day reset
  (2026-09-11T21:00Z) reported by the statusline.

## Consequence

A third meter is reachable without touching credentials or the endpoint
directly, at the cost of spawning one `claude -p` every few minutes from
the tray. The hook stays statusline-only.
