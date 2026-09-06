import unittest

from ai_usage_meter.core import line
from ai_usage_meter.core.display import SEPARATOR
from ai_usage_meter.core.payload import StatuslinePayload
from datetime import timedelta

from tests.fixtures import (
    CACHE_PAYLOAD_JSON, CAPTURED, NO_RATE_LIMITS_JSON, ONLY_FIVE_HOUR_JSON, SAMPLE_PAYLOAD_JSON,
)


class StatuslineLineTests(unittest.TestCase):
    def test_renders_model_effort_and_context(self):
        payload = StatuslinePayload.decode(SAMPLE_PAYLOAD_JSON)
        self.assertEqual(line.render(payload), "Fable 5.1 · high · ⛁ 12% (119k/1M) · 5h 21% · wk 4%")

    def test_omits_effort_when_absent(self):
        payload = StatuslinePayload.decode(NO_RATE_LIMITS_JSON)
        self.assertEqual(line.render(payload), "Fable 5.1 · ⛁ 3%")

    def test_renders_any_effort_word(self):
        payload = StatuslinePayload.decode(b'{"model":{"display_name":"Opus 4.8"},"effort":{"level":"medium"}}')
        self.assertEqual(line.render(payload), "Opus 4.8 · medium · ⛁ --")

    def test_rounds_fractional_percentages(self):
        payload = StatuslinePayload.decode(ONLY_FIVE_HOUR_JSON)
        self.assertEqual(line.render(payload), "Opus 4.8 · ⛁ 41% · 5h 55%")

    def test_falls_back_to_claude_when_nothing_is_known(self):
        self.assertEqual(line.render(None), "Claude · ⛁ --")

    def test_context_glyph_is_u26c1(self):
        self.assertEqual(line.CONTEXT_GLYPH, "⛁")
        self.assertEqual(line.SEPARATOR, SEPARATOR)

    def test_huge_context_percentage_does_not_crash(self):
        payload = StatuslinePayload.decode(b'{"context_window":{"used_percentage":1e300}}')
        self.assertEqual(line.render(payload), "Claude · ⛁ 1000%")

    def test_empty_display_name_falls_back(self):
        payload = StatuslinePayload.decode(b'{"model":{"display_name":""},"context_window":{"used_percentage":5}}')
        self.assertEqual(line.render(payload), "Claude · ⛁ 5%")

    def test_newlines_in_model_or_effort_are_flattened(self):
        payload = StatuslinePayload.decode(b'{"model":{"display_name":"Fable\\n5.1"},"effort":{"level":"hi\\rgh"}}')
        rendered = line.render(payload)
        self.assertNotIn("\n", rendered)
        self.assertNotIn("\r", rendered)
        self.assertEqual(rendered, "Fable 5.1 · hi gh · ⛁ --")

    def test_token_count_formats(self):
        for value, text in [(0, "0"), (512, "512"), (999, "999"), (1000, "1k"), (118695, "119k"),
                            (199_500, "200k"), (999_499, "999k"), (1_000_000, "1M"), (1_250_000, "1.25M"),
                            (None, None), (-5, None), (float("inf"), None)]:
            self.assertEqual(line.compact_tokens(value), text, value)

    def test_tokens_without_size_and_size_without_tokens(self):
        payload = StatuslinePayload.decode(b'{"context_window":{"used_percentage":12,"total_input_tokens":118695}}')
        self.assertEqual(line.render(payload), "Claude · ⛁ 12% (119k)")
        payload = StatuslinePayload.decode(b'{"context_window":{"used_percentage":12,"context_window_size":200000}}')
        self.assertEqual(line.render(payload), "Claude · ⛁ 12%")
        payload = StatuslinePayload.decode(b'{"context_window":{"total_input_tokens":"lots","context_window_size":true}}')
        self.assertEqual(line.render(payload), "Claude · ⛁ --")

    def test_rate_limit_segments_follow_the_windows_present(self):
        payload = StatuslinePayload.decode(b'{"rate_limits":{"seven_day":{"used_percentage":4.4}}}')
        self.assertEqual(line.render(payload), "Claude · ⛁ -- · wk 4%")
        payload = StatuslinePayload.decode(b'{"rate_limits":{"five_hour":{"resets_at":1},"seven_day":"x"}}')
        self.assertEqual(line.render(payload), "Claude · ⛁ --")

    def test_cache_segment(self):
        now = CAPTURED
        payload = StatuslinePayload.decode(CACHE_PAYLOAD_JSON)
        self.assertEqual(line.render(payload, now),
                         "Fable 5.1 · ⛁ 23% (230k/1M) · 5h 78% · wk 91% · cache 43m")
        self.assertEqual(line.render(payload, now + timedelta(hours=2)).split(SEPARATOR)[-1], "cache cold")
        cold = StatuslinePayload.decode(b'{"prompt_cache":{"warm":false,"caching_observed":true,"expires_at":null}}')
        self.assertEqual(line.render(cold, now), "Claude · ⛁ -- · cache cold")
        warm_no_expiry = StatuslinePayload.decode(b'{"prompt_cache":{"warm":true,"caching_observed":true}}')
        self.assertEqual(line.render(warm_no_expiry, now), "Claude · ⛁ -- · cache warm")
        for absent in (b'{"prompt_cache":{"warm":true,"caching_observed":false}}', b'{"prompt_cache":[]}',
                       b'{"prompt_cache":{"warm":"yes","caching_observed":true}}'):
            self.assertEqual(line.render(StatuslinePayload.decode(absent), now), "Claude · ⛁ --", absent)

    def test_colours_context_by_threshold_and_limits_by_tray_thresholds(self):
        G, Y, R, X = line.GREEN, line.YELLOW, line.RED, line.RESET
        def ctx(pct):
            return line.render(StatuslinePayload.decode(b'{"context_window":{"used_percentage":%d}}' % pct), color=True)
        self.assertEqual(ctx(49), f"Claude · ⛁ {G}49%{X}")
        self.assertEqual(ctx(50), f"Claude · ⛁ {Y}50%{X}")
        self.assertEqual(ctx(75), f"Claude · ⛁ {R}75%{X}")
        self.assertEqual(line.render(StatuslinePayload.decode(b"{}"), color=True), "Claude · ⛁ --")
        payload = StatuslinePayload.decode(CACHE_PAYLOAD_JSON)
        self.assertEqual(line.render(payload, CAPTURED, color=True),
                         f"Fable 5.1 · ⛁ {G}23%{X} {R}(230k/1M){X} · 5h {Y}78%{X} · wk {R}91%{X} · cache 43m")
        payload = StatuslinePayload.decode(SAMPLE_PAYLOAD_JSON)
        self.assertEqual(line.render(payload, color=True),
                         f"Fable 5.1 · high · ⛁ {G}12%{X} (119k/1M) · 5h 21% · wk 4%")
        cold = StatuslinePayload.decode(b'{"prompt_cache":{"warm":false,"caching_observed":true}}')
        self.assertEqual(line.render(cold, color=True), f"Claude · ⛁ -- · {Y}cache cold{X}")
