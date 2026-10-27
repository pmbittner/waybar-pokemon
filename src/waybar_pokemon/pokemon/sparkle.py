"""The sign of a shiny Pokémon: a little star twinkling on its sprite."""

import random
from dataclasses import dataclass

from PIL import Image

from ..engine import Stage, Walker, blend

PERIOD = 2.0  # seconds from one twinkle to the next
DURATION = 0.5  # seconds a twinkle lasts


def star(size: int) -> Image.Image:
    """A four-pointed star with rays of the given length, fading outwards."""
    image = Image.new("RGBA", (2 * size + 1, 2 * size + 1))
    image.putpixel((size, size), (255, 255, 255, 255))
    for distance in range(1, size + 1):
        for dx, dy in ((distance, 0), (-distance, 0), (0, distance), (0, -distance)):
            image.putpixel((size + dx, size + dy), (255, 240, 150, 255 - 70 * distance))
    return image


STARS = {size: star(size) for size in (1, 2)}


@dataclass
class Sparkle:
    clock: float = 0.0  # seconds into the current period
    spot: tuple[float, float] = (0.5, 0.25)  # on the sprite, relative to its size
    done: bool = False  # it never ends

    @classmethod
    def start(cls, rng: random.Random) -> "Sparkle":
        """Starts at a random moment, so shiny Pokémon don't twinkle in sync."""
        return cls(clock=rng.uniform(0, PERIOD))

    def update(self, dt: float, stage: Stage) -> None:
        self.clock += dt
        if self.clock >= PERIOD:
            self.clock %= PERIOD
            # A new spot every time, in the upper half of the sprite.
            self.spot = (stage.rng.random(), stage.rng.random() / 2)

    @property
    def size(self) -> int:
        """Length of the star's rays: growing, full, shrinking, then gone."""
        if self.clock >= DURATION:
            return 0
        return 2 if 0.3 * DURATION <= self.clock <= 0.7 * DURATION else 1

    def draw(self, frame: Image.Image, walker: Walker, stage: Stage) -> None:
        size = self.size
        if not size or walker.state == "drop":  # not while in the air
            return
        left, top, width, height = walker.box(stage)
        x = left + int(self.spot[0] * width)
        y = top + int(self.spot[1] * height)
        blend(frame, STARS[size], x - size, y - size)
