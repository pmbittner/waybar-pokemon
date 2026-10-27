"""PokeAPI's data tables (CSV files from GitHub), downloaded on first use
and cached."""

import csv
from pathlib import Path
from typing import Iterator

from .. import paths
from .web import download

URL = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/{table}.csv"
TABLES = ("pokemon_species", "pokemon_species_names", "items", "item_names")


def path(table: str) -> Path:
    """The cached table, downloaded if missing."""
    path = paths.CACHE_DIR / f"{table}.csv"
    if not path.exists():
        download(URL.format(table=table), path)
    return path


def rows(table: str) -> Iterator[dict[str, str]]:
    with path(table).open(newline="", encoding="utf-8") as file:
        yield from csv.DictReader(file)


def download_all() -> None:
    """Downloads the tables that are not cached yet."""
    for table in TABLES:
        path(table)
