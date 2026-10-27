"""Settings: an explicit, validated type, filled from the config file.

The daemon, the commands and anyone using the library interface (api.py)
pass a Config around; nothing reads settings from elsewhere.
"""

import json
from dataclasses import dataclass, field, fields
from pathlib import Path

from . import i18n, paths
from .pokemon import names


@dataclass(frozen=True)
class Config:
    width: int = 240  # size of the habitat in pixels; waybar's "size" must match
    height: int = 30
    fps: int = 10  # frames per second; waybar's "interval" should be 1 / fps
    frame: str = ""  # path of the rendered frame; empty means the default
    # Download the sprites of all Pokémon (normal and shiny) in the
    # background, so any Pokémon can be spawned without internet. Otherwise a
    # sprite is downloaded when its Pokémon is spawned for the first time.
    cache_all_sprites: bool = False
    # Generations that random spawns pick from, e.g. (1, 2, 3, 4). Empty
    # means all. Spawning a Pokémon by name is not restricted.
    random_generations: tuple[int, ...] = field(default_factory=tuple)
    # How often a wild berry falls from the sky while there are Pokémon, on
    # average. 0 turns it off.
    wild_berries_per_hour: float = 1.0
    # Language of the Pokémon and berry names, as in the games, e.g. "de".
    names_language: str = "en"
    # Language of everything else: notifications, menus, messages.
    ui_language: str = "en"

    def __post_init__(self) -> None:
        def check(condition: bool, message: str) -> None:
            if not condition:
                raise ValueError(message)

        for f in fields(self):
            value = getattr(self, f.name)
            if f.type is float:
                check(_is_number(value), f"{f.name} must be a number")
                object.__setattr__(self, f.name, float(value))  # e.g. 1 from JSON
            elif f.type is int:
                check(_is_number(value) and isinstance(value, int), f"{f.name} must be a whole number")
            elif f.type in (bool, str):
                check(isinstance(value, f.type), f"{f.name} must be {'true or false' if f.type is bool else 'a text'}")
            else:  # random_generations
                check(isinstance(value, tuple) and all(_is_number(g) and isinstance(g, int) for g in value), f"{f.name} must be a list of whole numbers")
        check(self.width > 0 and self.height > 0, "width and height must be positive")
        check(self.fps > 0, "fps must be positive")
        check(self.wild_berries_per_hour >= 0, "wild_berries_per_hour must not be negative")
        check(self.names_language in names.LANGUAGES, f"unknown names_language '{self.names_language}' (available: {', '.join(names.LANGUAGES)})")
        check(self.ui_language in i18n.LANGUAGES, f"unknown ui_language '{self.ui_language}' (available: {', '.join(i18n.LANGUAGES)})")

    @property
    def frame_path(self) -> Path:
        return Path(self.frame) if self.frame else paths.default_frame_path()


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def load(path: Path = paths.CONFIG_FILE) -> Config:
    """Reads the config file, a JSON object with any of Config's fields.
    Without the file, the defaults. ValueError if it is invalid."""
    if not path.exists():
        return Config()
    try:
        values = json.loads(path.read_text())
        if not isinstance(values, dict):
            raise ValueError("expected a JSON object")
        known = {f.name for f in fields(Config)}
        for key in values:
            if key not in known:
                raise ValueError(f"unknown setting '{key}'")
        if isinstance(values.get("random_generations"), list):
            values["random_generations"] = tuple(values["random_generations"])
        return Config(**values)
    except ValueError as error:
        raise ValueError(f"{path}: {error}") from None


def parse_generations(text: str) -> tuple[int, ...]:
    """Parses generations like "1-4" or "1,3,5-6" (as pokemon-colorscripts)."""
    generations: list[int] = []
    for part in text.split(","):
        first, _, last = part.strip().partition("-")
        generations.extend(range(int(first), int(last or first) + 1))
    return tuple(generations)
