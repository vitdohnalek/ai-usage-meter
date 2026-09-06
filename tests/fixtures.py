"""Shared fixtures, ported from Tests/MeterCoreTests/Fixtures.swift."""
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
