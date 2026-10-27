"""Drawing helpers."""

from PIL import Image


def blend(frame: Image.Image, image: Image.Image, x: int, y: int) -> None:
    """Draws an RGBA image onto the frame at (x, y), blending
    semi-transparent pixels with what is already there. Parts outside the
    frame are cut off."""
    left, top = max(0, x), max(0, y)
    right, bottom = min(frame.width, x + image.width), min(frame.height, y + image.height)
    if left >= right or top >= bottom:
        return
    part = image.crop((left - x, top - y, right - x, bottom - y))
    frame.alpha_composite(part, (left, top))
