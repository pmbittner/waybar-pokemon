"""Berries: their names, and the requests to drop one.

The berry command adds a request to a small file; the daemon takes the
requests and drops the berries. Unlike the party, berries are not kept
across restarts.
"""

import random

from .. import paths
from ..files import locked
from . import names

# The berries with icons in PokéSprite (see sprites.py), by PokeAPI's
# identifiers without "-berry".
NAMES = (
    "aguav", "apicot", "aspear", "babiri", "belue", "bluk", "charti", "cheri", "chesto", "chilan",
    "chople", "coba", "colbur", "cornn", "custap", "durin", "enigma", "figy", "ganlon",
    "golden-nanab", "golden-pinap", "golden-razz", "grepa", "haban", "hondew", "iapapa", "jaboca",
    "kasib", "kebia", "kee", "kelpsy", "lansat", "leppa", "liechi", "lum", "mago", "magost",
    "maranga", "micle", "nanab", "nomel", "occa", "oran", "pamtre", "passho", "payapa", "pecha",
    "persim", "petaya", "pinap", "pomeg", "qualot", "rabuta", "rawst", "razz", "rindo", "roseli",
    "rowap", "salac", "shuca", "silver-nanab", "silver-pinap", "silver-razz", "sitrus", "spelon",
    "starf", "tamato", "tanga", "wacan", "watmel", "wepear", "wiki", "yache",
)


def display_name(name: str, language: str) -> str:
    """The name in a language of the games, e.g. "Sinelbeere" for "oran" in "de"."""
    return names.item(f"{name}-berry", language, fallback=name.replace("-", " ").title() + " Berry")


def find(query: str, language: str) -> str:
    """A berry by its name in the given language or in English, or a unique
    beginning of it, e.g. "sit" or "Oran Berry". Raises names.NotFound
    otherwise."""
    candidates = ((n, [display_name(n, language), display_name(n, "en"), n]) for n in NAMES)
    return names.match(query, candidates, lambda n: display_name(n, language), kind="berry")


def random_name(rng: random.Random | None = None) -> str:
    return (rng or random).choice(NAMES)


def request(name: str) -> None:
    """Asks the daemon to drop a berry."""
    with locked(paths.BERRY_LOCK), paths.BERRY_REQUESTS.open("a") as file:
        file.write(name + "\n")


def take_requests() -> list[str]:
    """The berries to drop since the last call (for the daemon)."""
    if not paths.BERRY_REQUESTS.exists():  # the usual case, without locking
        return []
    with locked(paths.BERRY_LOCK):
        try:
            lines = paths.BERRY_REQUESTS.read_text().split()
            paths.BERRY_REQUESTS.unlink()
        except FileNotFoundError:
            return []
    return [line for line in lines if line in NAMES]
