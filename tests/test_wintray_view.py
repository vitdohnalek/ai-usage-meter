import unittest
from datetime import timedelta

from ai_usage_meter.core.display import make
from ai_usage_meter.core.sessions import SessionRecord
from ai_usage_meter.wintray import view
from tests.fixtures import CAPTURED as NOW, FIVE_RESET
from tests.test_label import display


def session(name, percent=61):
    return SessionRecord(session_id=name, name=name, project_dir=None, model=None,
                         context_used_percentage=percent, context_tokens=None, context_window_size=None,
                         cache_warm=None, cache_expires_at=None, updated_at=NOW)


class IconSpecTests(unittest.TestCase):
    def test_one_icon_per_window_in_order(self):
        specs = view.icon_specs(display(21, 4, model=5))
        self.assertEqual([s.key for s in specs], [view.FIVE_HOUR, view.SEVEN_DAY, view.MODEL])
        self.assertEqual([s.text for s in specs], ["21", "4", "5"])
        self.assertEqual([s.level for s in specs], [view.BLUE, view.GREEN, view.GREEN])

    def test_model_icon_only_once_the_window_is_known(self):
        self.assertEqual([s.key for s in view.icon_specs(display(21, 4))], [view.FIVE_HOUR, view.SEVEN_DAY])

    def test_level_bands(self):
        bands = {0: view.GREEN, 20: view.GREEN, 21: view.BLUE, 50: view.BLUE, 51: view.ORANGE,
                 75: view.ORANGE, 76: view.RED, 90: view.RED, 91: view.PURPLE, 100: view.PURPLE,
                 250: view.PURPLE}
        for percent, level in bands.items():
            self.assertEqual(view.level_of(percent), level, percent)
        self.assertEqual(view.level_of(None), view.UNKNOWN_LEVEL)

    def test_each_window_gets_its_own_level(self):
        specs = view.icon_specs(display(20, 76, model=100))
        self.assertEqual([s.level for s in specs], [view.GREEN, view.RED, view.PURPLE])
        self.assertEqual(specs[2].text, "100")

    def test_unknown_window_and_missing_snapshot(self):
        specs = view.icon_specs(display(42, None))
        self.assertEqual((specs[1].text, specs[1].level), ("--", view.UNKNOWN_LEVEL))
        self.assertEqual([s.text for s in view.icon_specs(make(None, NOW))], ["--", "--"])

    def test_reset_window_shows_zero(self):
        spec = view.icon_specs(display(95, 40, now=FIVE_RESET + timedelta(seconds=60)))[0]
        self.assertEqual((spec.text, spec.level), ("0", view.GREEN))

    def test_tooltip_is_the_menu_row_and_fits_the_windows_limit(self):
        specs = view.icon_specs(display(21, 4, model=5))
        self.assertTrue(specs[0].tooltip.startswith("5-hour  21% · resets in "), specs[0].tooltip)
        self.assertTrue(specs[2].tooltip.startswith("Fable  5%"), specs[2].tooltip)
        self.assertTrue(all(len(s.tooltip) <= view.TOOLTIP_MAX for s in specs))

    def test_stale_tooltip_says_so(self):
        spec = view.icon_specs(display(21, 4), live=False)[0]
        self.assertTrue(spec.tooltip.endswith(view.STALE_TEXT), spec.tooltip)


class MenuLineTests(unittest.TestCase):
    def test_rows_bars_and_age(self):
        lines = view.menu_lines(display(21, 4, model=5), [], NOW)
        self.assertTrue(lines[0].startswith("5-hour  21%"))
        self.assertEqual(lines[1], "▰▰▱▱▱▱▱▱▱▱")
        self.assertTrue(lines[4].startswith("Fable  5%"))
        self.assertEqual(lines[6:], [view.SEPARATOR_LINE, "Updated 2 min ago · statusline"])

    def test_sessions_section_appears_only_with_sessions(self):
        self.assertNotIn("Sessions (0)", view.menu_lines(display(21, 4), [], NOW))
        lines = view.menu_lines(display(21, 4), [session("zeta"), session("alpha", 12)], NOW)
        start = lines.index("Sessions (2)")
        self.assertEqual(lines[start - 1], view.SEPARATOR_LINE)
        self.assertEqual(lines[start + 1:start + 3], ["alpha  ⛁ 12%", "zeta  ⛁ 61%"])

    def test_sessions_are_capped(self):
        many = [session(f"s{i:02d}") for i in range(view.SESSION_SLOTS + 3)]
        lines = view.menu_lines(display(21, 4), many, NOW)
        self.assertEqual(sum(1 for line in lines if line and line.startswith("s")), view.SESSION_SLOTS)

    def test_stale_state_is_named_in_the_age_row(self):
        lines = view.menu_lines(display(21, 4), [], NOW, live=False)
        self.assertEqual(lines[-1], "Updated 2 min ago · statusline · " + view.STALE_TEXT)
        self.assertEqual(view.menu_lines(make(None, NOW), [], NOW, live=False)[-1],
                         "No snapshot yet · " + view.STALE_TEXT)

    def test_ampersand_is_escaped_for_win32_menus(self):
        self.assertEqual(view.menu_text("R&D  ⛁ 61%"), "R&&D  ⛁ 61%")
        self.assertEqual(view.menu_text("plain"), "plain")
