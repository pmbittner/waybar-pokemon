"""Effects: little extras that follow a walker and are drawn on top of it,
e.g. a sparkle or a heart."""

from typing import TYPE_CHECKING, Protocol

from PIL import Image

from .scene import Stage

if TYPE_CHECKING:
    from .walker import Walker


class Effect(Protocol):
    @property
    def done(self) -> bool:
        """Finished, so the walker drops it."""

    def update(self, dt: float, stage: Stage) -> None: ...

    def draw(self, frame: Image.Image, walker: "Walker", stage: Stage) -> None:
        """Draws the effect for the walker (see Walker.box), without
        changing its state."""
