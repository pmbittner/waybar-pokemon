"""The library interface: everything the commands do, without a command line.

Each function takes the settings explicitly and returns data. Failures are
exceptions: the ones below, names.NotFound (no or several matches for a
name), pokedex.NoCandidates (no Pokémon in the generations) and OSError
(downloads). Texts for people are up to the caller, see cli.py and
i18n.py. The daemon (daemon.py) shows the results.
"""

from dataclasses import dataclass
from typing import Callable, Collection

from .config import Config
from .pokemon import berries, names, party, pokedex, sprites


class Empty(LookupError):
    """There is no Pokémon in the habitat."""


class NotInHabitat(LookupError):
    def __init__(self, query: str) -> None:
        super().__init__(f"No '{query}' in the habitat")
        self.query = query


Full = party.Full
MAX_RESIDENTS = party.MAX_SIZE


@dataclass(frozen=True)
class Resident:
    """A Pokémon in the habitat."""

    uid: int  # to despawn it
    species: pokedex.Species
    shiny: bool
    name: str  # in the configured language


@dataclass(frozen=True)
class DroppedBerry:
    identifier: str  # e.g. "oran"
    name: str  # in the configured language


def _resident(member: party.Member, config: Config) -> Resident:
    species = pokedex.get(member.species_id)
    return Resident(member.uid, species, member.shiny, species.name(config.names_language))


def residents(config: Config) -> list[Resident]:
    """The Pokémon in the habitat, oldest first."""
    return [_resident(m, config) for m in party.load()]


def spawn(config: Config, query: str | None = None, *, shiny: bool = False, generations: Collection[int] | None = None) -> Resident:
    """Sends out the Pokémon with the given name or number, or a random one
    (from the generations, else those of the settings). It is shiny if
    asked for, else with the games' chance."""
    if query:
        species = pokedex.find(query, config.names_language)
    else:
        species = pokedex.random_species(config.random_generations if generations is None else generations)
    shiny = shiny or pokedex.roll_shiny()
    sprites.pokemon(species.id, shiny)  # download now, so errors show here
    return _resident(party.add(species.id, shiny), config)


def despawn(config: Config, query: str | None = None) -> Resident:
    """Returns the Pokémon with the given uid or name (the newest of that
    name), or the newest one without a query."""

    def choose(members: list[party.Member]) -> list[party.Member]:
        if not members:
            raise Empty()
        if query is None:
            return [members[-1]]
        if query.strip().isdigit():
            matching = [m for m in members if m.uid == int(query)]
        else:
            candidates = [(m, _names(m, config)) for m in members]
            matching = names.match_all(query, candidates)
        if not matching:
            raise NotInHabitat(query)
        return [matching[-1]]

    (member,) = party.remove(choose)
    return _resident(member, config)


def despawn_all(config: Config) -> list[Resident]:
    def choose(members: list[party.Member]) -> list[party.Member]:
        if not members:
            raise Empty()
        return members

    return [_resident(m, config) for m in party.remove(choose)]


def _names(member: party.Member, config: Config) -> list[str]:
    species = pokedex.get(member.species_id)
    return [species.name(config.names_language), species.name("en"), species.identifier]


def drop_berry(config: Config, query: str | None = None) -> DroppedBerry:
    """Asks the daemon to drop the berry with the given name, or a random one."""
    identifier = berries.find(query, config.names_language) if query else berries.random_name()
    sprites.berry(identifier)  # download now, so errors show here
    berries.request(identifier)
    return DroppedBerry(identifier, berries.display_name(identifier, config.names_language))


def pokemon_names(config: Config) -> list[str]:
    """All Pokémon, by Pokédex number, in the configured language."""
    return [s.name(config.names_language) for s in pokedex.all_species()]


def berry_names(config: Config) -> list[str]:
    return [berries.display_name(n, config.names_language) for n in berries.NAMES]


def download(progress: Callable[[int, int], None] | None = None) -> int:
    """Downloads all data and sprites that are not cached yet, for using it
    without internet. Returns the number of files that failed."""
    return sprites.download_all(progress)
