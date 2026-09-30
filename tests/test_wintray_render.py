import importlib.util
import unittest

from ai_usage_meter.wintray import view

HAS_PILLOW = importlib.util.find_spec("PIL") is not None


def spec(key=view.FIVE_HOUR, text="21", level=view.BLUE):
    return view.IconSpec(key, text, level, "tip")


@unittest.skipUnless(HAS_PILLOW, "Pillow is a Windows-tray dependency only")
class RenderTests(unittest.TestCase):
    def setUp(self):
        from ai_usage_meter.wintray import render
        self.render = render

    def test_image_is_square_rgba_and_not_blank(self):
        image = self.render.draw(spec())
        self.assertEqual((image.mode, image.size), ("RGBA", (self.render.SIZE, self.render.SIZE)))
        self.assertGreater(len(image.getcolors(maxcolors=100_000)), 1)

    def test_text_and_level_change_the_picture_and_the_window_does_not(self):
        base = self.render.draw(spec()).tobytes()
        self.assertNotEqual(base, self.render.draw(spec(text="22")).tobytes())
        pictures = {self.render.draw(spec(level=level)).tobytes() for level in view.LEVELS}
        self.assertEqual(len(pictures), len(view.LEVELS))
        self.assertEqual(base, self.render.draw(spec(key=view.SEVEN_DAY)).tobytes())

    def test_every_level_has_a_colour(self):
        self.assertEqual(set(self.render.STRIPE_COLOR), set(view.LEVELS))

    def test_widest_and_unknown_texts_render(self):
        for text in ("100", "--", "0"):
            self.assertEqual(self.render.draw(spec(text=text)).size, (self.render.SIZE, self.render.SIZE))

    def test_missing_font_falls_back(self):
        image = self.render.draw(spec(), fonts=("no-such-font.ttf",))
        self.assertGreater(len(image.getcolors(maxcolors=100_000)), 1)
