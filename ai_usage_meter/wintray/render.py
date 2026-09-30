"""Draws one tray icon: the number on a dark plate, with a stripe
underneath in the colour of its level. Needs Pillow."""
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont

from . import view

SIZE = 64
RADIUS = 12
STRIPE = 12
MARGIN = 3
FONTS = ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf")
FONT_SIZES = range(58, 9, -2)
PLATE = (30, 34, 42, 255)
INK = (255, 255, 255, 255)
UNKNOWN_INK = (150, 156, 168, 255)
STRIPE_COLOR = {
    view.GREEN: (50, 200, 130, 255),
    view.BLUE: (70, 150, 255, 255),
    view.ORANGE: (245, 160, 40, 255),
    view.RED: (230, 55, 55, 255),
    view.PURPLE: (190, 110, 255, 255),
    view.UNKNOWN_LEVEL: (110, 116, 128, 255),
}


def _font(name: str, size: int):
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return None


def _fitted(draw, text: str, fonts: Sequence[str], width: int, height: int):
    """The largest bold face that fits; Pillow's built-in one when none of
    the named fonts is installed."""
    name = next((n for n in fonts if _font(n, 12) is not None), None)
    for size in FONT_SIZES:
        font = _font(name, size) if name else ImageFont.load_default(size)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        if right - left <= width and bottom - top <= height:
            return font
    return font


def draw(spec: view.IconSpec, fonts: Sequence[str] = FONTS) -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas = ImageDraw.Draw(image)
    stripe = STRIPE_COLOR.get(spec.level, STRIPE_COLOR[view.UNKNOWN_LEVEL])
    canvas.rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), RADIUS, fill=stripe)
    canvas.rounded_rectangle((0, 0, SIZE - 1, SIZE - 1 - STRIPE), RADIUS, fill=PLATE)
    canvas.rectangle((0, SIZE - STRIPE - RADIUS, SIZE - 1, SIZE - 1 - STRIPE), fill=PLATE)
    area = SIZE - STRIPE
    font = _fitted(canvas, spec.text, fonts, SIZE - 2 * MARGIN, area - 2 * MARGIN)
    ink = UNKNOWN_INK if spec.level == view.UNKNOWN_LEVEL else INK
    canvas.text((SIZE / 2, area / 2), spec.text, font=font, fill=ink, anchor="mm")
    return image
