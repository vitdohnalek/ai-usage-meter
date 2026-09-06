"""Shared fixtures: real statusline and get_usage payloads, trimmed."""
from datetime import datetime, timezone

FIVE_RESET = datetime.fromtimestamp(1_788_617_400, tz=timezone.utc)
SEVEN_RESET = datetime.fromtimestamp(1_789_160_400, tz=timezone.utc)
CAPTURED = datetime.fromtimestamp(1_788_608_892, tz=timezone.utc)

SAMPLE_PAYLOAD_JSON = b"""
{"session_id":"f9d550b8-b03e-47b2-aa24-76d4af4f8a26",
 "cwd":"/home/vitek/Desktop/cartagenum/ai-usage-meter",
 "model":{"id":"claude-fable-5-1","display_name":"Fable 5.1"},
 "version":"2.1.263",
 "effort":{"level":"high"},
 "cost":{"total_cost_usd":8.343004900000002,"total_duration_ms":4110311},
 "context_window":{"total_input_tokens":118695,"context_window_size":1000000,
   "used_percentage":12,"remaining_percentage":88},
 "exceeds_200k_tokens":false,
 "rate_limits":{"five_hour":{"used_percentage":21,"resets_at":1788617400},
                "seven_day":{"used_percentage":4,"resets_at":1789160400}}}
"""

NO_RATE_LIMITS_JSON = b"""
{"model":{"id":"claude-fable-5-1","display_name":"Fable 5.1"},
 "context_window":{"used_percentage":3}}
"""

ONLY_FIVE_HOUR_JSON = b"""
{"model":{"display_name":"Opus 4.8"},
 "context_window":{"used_percentage":40.6},
 "rate_limits":{"five_hour":{"used_percentage":55.4,"resets_at":1788617400}}}
"""

MODEL_RESET = datetime(2026, 9, 6, 18, 59, 59, 988722, tzinfo=timezone.utc)

# What ``claude -p --output-format stream-json`` prints for a ``get_usage``
# control request on 2.1.263, trimmed to the fields that matter plus noise.
USAGE_RESPONSE_JSONL = b"""not json at all
{"type":"system","subtype":"init","session_id":"fd861edf"}
{"type":"control_response","response":{"subtype":"success","request_id":"ai-usage-meter","response":{"session":{"total_cost_usd":0},"subscription_type":"max","rate_limits_available":true,"rate_limits":{"five_hour":{"utilization":24,"resets_at":"2026-09-06T17:59:59.689325+00:00"},"seven_day":{"utilization":3,"resets_at":"2026-09-06T18:59:59.689371+00:00"},"model_scoped":[{"display_name":"Fable","utilization":5.4,"resets_at":"2026-09-06T18:59:59.988722+00:00"},{"display_name":"Opus","utilization":61,"resets_at":"2026-09-06T18:59:59.988722+00:00"}]},"behaviors":null}}}
"""

USAGE_ERROR_JSONL = b"""{"type":"control_response","response":{"subtype":"error","request_id":"ai-usage-meter","error":"boom"}}
"""

USAGE_NO_MODEL_JSONL = b"""{"type":"control_response","response":{"subtype":"success","request_id":"ai-usage-meter","response":{"rate_limits_available":false,"rate_limits":null}}}
"""

# A payload with the prompt-cache block (2.1.251+) and the 200k flag set.
CACHE_PAYLOAD_JSON = b"""
{"model":{"display_name":"Fable 5.1"},
 "context_window":{"used_percentage":23,"total_input_tokens":230100,"context_window_size":1000000},
 "exceeds_200k_tokens":true,
 "rate_limits":{"five_hour":{"used_percentage":78,"resets_at":1788617400},
                "seven_day":{"used_percentage":91,"resets_at":1789160400}},
 "prompt_cache":{"warm":true,"caching_observed":true,"ttl":"1h","expires_at":1788611472}}
"""
