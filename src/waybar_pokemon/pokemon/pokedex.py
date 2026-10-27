"""Pokémon species and sprites, downloaded on first use and cached.

Species come from PokeAPI's species table, their names in all languages
from names.py. Sprites are the small box icons
of the games (68 x 56, normal and shiny) from the PokéSprite project: the
classic icons of generation 7 where there is one (Pokémon up to generation
7), else the icons of generation 8. For Pokémon without any icon there (the
newest ones), PokeAPI's larger front sprites are used instead. Everything is
fetched from GitHub.
"""

import csv
import random
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from functools import cache, partial
from pathlib import Path
from typing import Callable, Collection

from .. import paths
from . import names
from .web import download

SPECIES_URL = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/pokemon_species.csv"
ICON_URL = "https://raw.githubusercontent.com/msikma/pokesprite/master/pokemon-{icon_set}/{variant}/{name}.png"
ICON_SETS = ("gen7x", "gen8")  # tried in this order
SPRITE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{variant}{id}.png"

# The chance of a shiny Pokémon in the games since generation 6.
SHINY_ODDS = 4096


@dataclass(frozen=True)
class Species:
    id: int
    identifier: str  # e.g. "mr-mime"
    generation: int

    def name(self, language: str) -> str:
        """The name in a language of the games, e.g. "Pantimos" in "de"."""
        return names.species(self.id, language, fallback=self.identifier.replace("-", " ").title())


class NoCandidates(LookupError):
    def __init__(self, generations: Collection[int]) -> None:
        super().__init__(f"No Pokémon in generations {sorted(generations)}")
        self.generations = sorted(generations)


@cache
def all_species() -> list[Species]:
    """All species, ordered by Pokédex number (read once per process)."""
    if not paths.SPECIES_FILE.exists():
        download(SPECIES_URL, paths.SPECIES_FILE)
    with paths.SPECIES_FILE.open(newline="") as file:
        rows = csv.DictReader(file)
        species = [Species(int(row["id"]), row["identifier"], int(row["generation_id"])) for row in rows]
    return sorted(species, key=lambda s: s.id)


def get(species_id: int) -> Species:
    return next(s for s in all_species() if s.id == species_id)


def find(query: str, language: str) -> Species:
    """Looks up a species by Pokédex number or name, in the given language
    or in English. A unique beginning of a name is enough, e.g. "pika".
    Raises names.NotFound otherwise.
    """
    species = all_species()
    if query.strip().isdigit():
        matches = [s for s in species if s.id == int(query)]
        if len(matches) != 1:
            raise names.NotFound(query, 0, [])
        return matches[0]
    candidates = ((s, [s.name(language), s.name("en"), s.identifier]) for s in species)
    return names.match(query, candidates, lambda s: s.name(language))


def random_species(generations: Collection[int] = ()) -> Species:
    """A random species, only from the given generations if any are given."""
    candidates = [s for s in all_species() if not generations or s.generation in generations]
    if not candidates:
        raise NoCandidates(generations)
    return random.choice(candidates)


def roll_shiny() -> bool:
    return random.randrange(SHINY_ODDS) == 0


def sprite_path(species_id: int, shiny: bool) -> Path:
    """The cached sprite (box icon, or front sprite as fallback), downloaded if missing."""
    # One directory per choice of icons, so changing ICON_SETS downloads
    # the new icons instead of reusing the cached ones.
    path = paths.SPRITE_DIR / "+".join(ICON_SETS) / f"{species_id}{'-shiny' if shiny else ''}.png"
    if path.exists():
        return path
    name = get(species_id).identifier
    variant = "shiny" if shiny else "regular"
    urls = [ICON_URL.format(icon_set=icon_set, variant=variant, name=name) for icon_set in ICON_SETS]
    urls.append(SPRITE_URL.format(variant="shiny/" if shiny else "", id=species_id))
    for url in urls[:-1]:
        try:
            download(url, path)
            return path
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
    download(urls[-1], path)
    return path


def download_all(progress: Callable[[int, int], None] | None = None) -> int:
    """Downloads the names, and the sprites of all species (normal and
    shiny) and of all berries that are not cached yet. Returns the number
    of sprites that could not be downloaded.
    """
    from . import berries  # (berries uses this module)

    names.download_all()
    jobs: list[Callable[[], Path]] = [partial(sprite_path, s.id, shiny) for s in all_species() for shiny in (False, True)]
    jobs += [partial(berries.sprite_path, name) for name in berries.NAMES]
    failed = 0
    # A few downloads at a time; one by one takes several minutes.
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(job) for job in jobs]
        for done, future in enumerate(as_completed(futures), start=1):
            if isinstance(future.exception(), OSError):
                failed += 1
            if progress:
                progress(done, len(jobs))
    return failed
