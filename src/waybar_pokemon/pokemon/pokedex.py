"""Pokémon species: Pokédex number, generation and names (from PokeAPI's
tables), lookup, random choice and the shiny chance."""

import random
from dataclasses import dataclass
from functools import cache
from typing import Collection

from . import data, names

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
    rows = data.rows("pokemon_species")
    return sorted((Species(int(r["id"]), r["identifier"], int(r["generation_id"])) for r in rows), key=lambda s: s.id)


@cache
def _by_id() -> dict[int, Species]:
    return {s.id: s for s in all_species()}


def get(species_id: int) -> Species:
    """The species with the given Pokédex number (KeyError if unknown)."""
    return _by_id()[species_id]


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
