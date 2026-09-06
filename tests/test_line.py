import unittest

from ai_usage_meter.core import line
from ai_usage_meter.core.display import SEPARATOR
from ai_usage_meter.core.payload import StatuslinePayload
from tests.fixtures import NO_RATE_LIMITS_JSON, ONLY_FIVE_HOUR_JSON, SAMPLE_PAYLOAD_JSON


class StatuslineLineTests(unittest.TestCase):
    def test_renders_model_effort_and_context(self):
        payload = StatuslinePayload.decode(SAMPLE_PAYLOAD_JSON)
        self.assertEqual(line.render(payload), "Fable 5.1 · high · ⛁ 12%")

    def test_omits_effort_when_absent(self):
        payload = StatuslinePayload.decode(NO_RATE_LIMITS_JSON)
        self.assertEqual(line.render(payload), "Fable 5.1 · ⛁ 3%")

    def test_renders_any_effort_word(self):
        payload = StatuslinePayload.decode(b'{"model":{"display_name":"Opus 4.8"},"effort":{"level":"medium"}}')
        self.assertEqual(line.render(payload), "Opus 4.8 · medium · ⛁ --")

    def test_rounds_fractional_percentages(self):
        payload = StatuslinePayload.decode(ONLY_FIVE_HOUR_JSON)
        self.assertEqual(line.render(payload), "Opus 4.8 · ⛁ 41%")

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
