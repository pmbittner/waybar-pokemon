"""A Pokémon on the stage: a walker that races for berries and eats them.
Its effects (e.g. the sparkle of a shiny one) are set by the habitat."""

from dataclasses import dataclass

from PIL import Image

from ..engine import Stage, Walker
from .berry import BITES, Berry
from .heart import Heart

RACE_SPEED = 30.0  # pixels per second, faster than walking
BITE = 0.6  # seconds per bite: two chews
CHEW = BITE / 4  # squashed for this long, twice per bite
SQUASH = 2  # pixels
JOY = 60.0  # speed of the happy jump after a meal, pixels per second


@dataclass(eq=False)
class Pokemon(Walker):
    racing_for: Berry | None = None
    meal: Berry | None = None
    meal_clock: float = 0.0

    # Commands (from the habitat)

    def race_to(self, berry: Berry, stage: Stage) -> None:
        """Runs to the berry, so that the front of the sprite touches it."""
        self.racing_for = berry
        width = self.sprite.width
        if self.center < berry.center:
            target = berry.x - width + 2
        else:
            target = berry.x + berry.image.width - 2
        self.go_to(min(max(target, 0), max(0, stage.width - width)), RACE_SPEED)

    def give_up(self, stage: Stage) -> None:
        self.racing_for = None
        self.stop(stage)

    def eat(self, berry: Berry) -> None:
        self.racing_for, self.meal, self.meal_clock = None, berry, 0.0
        self.state = "eat"
        self.direction = 1 if berry.center > self.center else -1

    # Update

    def move(self, dt: float, stage: Stage) -> None:
        if self.state == "eat":
            self.meal_clock += dt
            self._munch()
        else:
            super().move(dt, stage)

    def _munch(self) -> None:
        """A bite at the start of every BITE seconds; then a happy jump."""
        assert self.meal is not None
        while self.meal.bites < min(BITES, int(self.meal_clock / BITE) + 1):
            self.meal.bite()
        if self.meal_clock >= BITES * BITE:
            self.meal = None
            self.effects.append(Heart())
            self.jump(JOY)

    @property
    def chewing(self) -> bool:
        """Squashed: in the first and third quarter of every bite."""
        return self.state == "eat" and int(self.meal_clock / CHEW) % 2 == 0

    # Draw

    @property
    def image(self) -> Image.Image:
        image = super().image
        if self.chewing and image.height > 2 * SQUASH:
            image = image.resize((image.width, image.height - SQUASH), Image.Resampling.NEAREST)
        return image
