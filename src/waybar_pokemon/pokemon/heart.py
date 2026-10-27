"""A little heart that rises and fades above a Pokémon, after a meal."""

from dataclasses import dataclass

from PIL import Image

from ..engine import Stage, Walker, blend

DURATION = 1.2  # seconds
RISE = 4  # pixels
SHAPE = (
    ".XX.XX.",
    "XXXXXXX",
    "XXXXXXX",
    ".XXXXX.",
    "..XXX..",
    "...X...",
)
HEART = Image.new("RGBA", (len(SHAPE[0]), len(SHAPE)))
for _y, _row in enumerate(SHAPE):
    for _x, _cell in enumerate(_row):
        if _cell == "X":
            HEART.putpixel((_x, _y), (255, 110, 150, 255))


@dataclass
class Heart:
    clock: float = 0.0

    @property
    def done(self) -> bool:
        return self.clock >= DURATION

    def update(self, dt: float, stage: Stage) -> None:
        self.clock += dt

    def draw(self, frame: Image.Image, walker: Walker, stage: Stage) -> None:
        """Above the front of the sprite, fading out at the end."""
        if self.done:
            return
        left, top, width, _ = walker.box(stage)
        progress = self.clock / DURATION
        x = left + (width - HEART.width if walker.direction > 0 else 0)
        y = max(0, top - HEART.height + 2 - round(RISE * progress))
        image = HEART
        if progress > 0.6:
            opacity = (1 - progress) / 0.4
            image = HEART.copy()
            image.putalpha(HEART.getchannel("A").point(lambda a: round(a * opacity)))
        blend(frame, image, x, y)
