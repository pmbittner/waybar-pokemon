"""Test setup: every test runs in its own empty home with small copies of
PokeAPI's tables and without network access."""

import csv
import os
import shutil
import tempfile
import urllib.request
from pathlib import Path

import pytest
from PIL import Image

# Before waybar_pokemon is imported, as its paths are computed on import.
ROOT = Path(tempfile.mkdtemp(prefix="waybar-pokemon-tests-"))
os.environ.update(
    XDG_CACHE_HOME=str(ROOT / "cache"),
    XDG_STATE_HOME=str(ROOT / "state"),
    XDG_CONFIG_HOME=str(ROOT / "config"),
    USER="test",
)

from waybar_pokemon import paths  # noqa: E402
from waybar_pokemon.pokemon import names, pokedex  # noqa: E402

# id, identifier, generation, English name, German name
SPECIES = [
    (1, "bulbasaur", 1, "Bulbasaur", "Bisasam"),
    (25, "pikachu", 1, "Pikachu", "Pikachu"),
    (29, "nidoran-f", 1, "Nidoran♀", "Nidoran♀"),
    (32, "nidoran-m", 1, "Nidoran♂", "Nidoran♂"),
    (122, "mr-mime", 1, "Mr. Mime", "Pantimos"),
    (150, "mewtwo", 1, "Mewtwo", "Mewtu"),
    (151, "mew", 1, "Mew", "Mew"),
    (669, "flabebe", 6, "Flabébé", "Flabébé"),
    (906, "sprigatito", 9, "Sprigatito", "Felori"),
]
# item id, identifier, English name, German name
ITEMS = [
    (132, "oran-berry", "Oran Berry", "Sinelbeere"),
    (135, "sitrus-berry", "Sitrus Berry", "Tsitrubeere"),
]


def _write(path: Path, header: list[str], rows: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)


def write_tables(cache: Path) -> None:
    en, de = names.LANGUAGES["en"], names.LANGUAGES["de"]
    _write(cache / "species.csv", ["id", "identifier", "generation_id"], [(i, s, g) for i, s, g, _, _ in SPECIES])
    _write(
        cache / "pokemon_species_names.csv",
        ["pokemon_species_id", "local_language_id", "name", "genus"],
        [(i, en, e, "") for i, _, _, e, _ in SPECIES] + [(i, de, d, "") for i, _, _, _, d in SPECIES],
    )
    _write(cache / "items.csv", ["id", "identifier"], [(i, s) for i, s, _, _ in ITEMS])
    _write(
        cache / "item_names.csv",
        ["item_id", "local_language_id", "name"],
        [(i, en, e) for i, _, e, _ in ITEMS] + [(i, de, d) for i, _, _, d in ITEMS],
    )


def clear_caches() -> None:
    pokedex.all_species.cache_clear()
    names._species_names.cache_clear()
    names._item_names.cache_clear()


def fake_sprite(path: Path, size: tuple[int, int] = (20, 20)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", size, (200, 80, 80, 255)).save(path)
    return path


@pytest.fixture(autouse=True)
def home(monkeypatch):
    """A fresh home with the tables, and no network."""
    shutil.rmtree(ROOT, ignore_errors=True)
    write_tables(paths.CACHE_DIR)
    clear_caches()

    def offline(*args, **kwargs):
        raise OSError("no network in tests")

    monkeypatch.setattr(urllib.request, "urlopen", offline)
    yield ROOT
    clear_caches()


@pytest.fixture
def sprites():
    """Creates cached sprites for all species and berries of the tables."""
    from waybar_pokemon.pokemon import berries

    for species_id, *_ in SPECIES:
        for shiny in (False, True):
            name = f"{species_id}{'-shiny' if shiny else ''}.png"
            fake_sprite(paths.SPRITE_DIR / "+".join(pokedex.ICON_SETS) / name)
    for name in berries.NAMES:
        fake_sprite(paths.SPRITE_DIR / "berries" / f"{name}.png", (10, 10))
