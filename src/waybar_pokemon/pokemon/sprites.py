"""Sprites of Pokémon and berries, downloaded on first use and cached.

Pokémon: the small box icons of the games (68 x 56, normal and shiny) from
the PokéSprite project; the classic icons of generation 7 where there is
one (Pokémon up to generation 7), else the icons of generation 8. For
Pokémon without any icon there (the newest ones), PokeAPI's larger front
sprites are used instead.

Berries: the bag icons of the games (32 x 32), also from PokéSprite.
"""

import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from pathlib import Path
from typing import Callable

from .. import paths
from . import berries, data, pokedex
from .web import download

POKESPRITE = "https://raw.githubusercontent.com/msikma/pokesprite/master"
ICON_URL = POKESPRITE + "/pokemon-{icon_set}/{variant}/{name}.png"
ICON_SETS = ("gen7x", "gen8")  # tried in this order
FRONT_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{variant}{id}.png"
BERRY_URL = POKESPRITE + "/items/berry/{name}.png"


def pokemon(species_id: int, shiny: bool) -> Path:
    """The cached sprite of a Pokémon (an icon, or its front sprite as
    fallback), downloaded if missing."""
    # One directory per choice of icons, so changing ICON_SETS downloads
    # the new icons instead of reusing the cached ones.
    path = paths.SPRITE_DIR / "+".join(ICON_SETS) / f"{species_id}{'-shiny' if shiny else ''}.png"
    if path.exists():
        return path
    name = pokedex.get(species_id).identifier
    variant = "shiny" if shiny else "regular"
    urls = [ICON_URL.format(icon_set=icon_set, variant=variant, name=name) for icon_set in ICON_SETS]
    urls.append(FRONT_URL.format(variant="shiny/" if shiny else "", id=species_id))
    for url in urls[:-1]:
        try:
            download(url, path)
            return path
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
    download(urls[-1], path)
    return path


def berry(name: str) -> Path:
    """The cached sprite of a berry, downloaded if missing."""
    path = paths.SPRITE_DIR / "berries" / f"{name}.png"
    if not path.exists():
        download(BERRY_URL.format(name=name), path)
    return path


def download_all(progress: Callable[[int, int], None] | None = None) -> int:
    """Downloads the data tables, and the sprites of all Pokémon (normal
    and shiny) and berries that are not cached yet. Returns the number of
    sprites that could not be downloaded.
    """
    data.download_all()
    jobs: list[Callable[[], Path]] = [partial(pokemon, s.id, shiny) for s in pokedex.all_species() for shiny in (False, True)]
    jobs += [partial(berry, name) for name in berries.NAMES]
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
