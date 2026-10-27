"""The Pokémon currently out in the habitat, stored in a JSON file.

The commands add and remove members; the daemon watches the file and shows
its members. A lock file keeps concurrent commands from losing changes.
"""

import fcntl
import json
from contextlib import contextmanager
from dataclasses import asdict, dataclass, fields
from typing import Callable, Iterator

from .. import paths

MAX_SIZE = 10  # more would not fit into a small habitat


class Full(Exception):
    def __init__(self) -> None:
        super().__init__(f"The party is full ({MAX_SIZE} Pokémon)")


@dataclass(frozen=True)
class Member:
    uid: int  # unique within the party, to tell apart two of the same species
    species_id: int
    shiny: bool


def load() -> list[Member]:
    try:
        data = json.loads(paths.PARTY_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    known = {f.name for f in fields(Member)}  # older files also have a name
    return [Member(**{k: v for k, v in member.items() if k in known}) for member in data]


def _save(members: list[Member]) -> None:
    temporary = paths.PARTY_FILE.with_suffix(".json.part")
    temporary.write_text(json.dumps([asdict(m) for m in members], indent=2))
    temporary.replace(paths.PARTY_FILE)


@contextmanager
def editing() -> Iterator[list[Member]]:
    """Yields the party as a list to change; saves it afterwards."""
    paths.STATE_DIR.mkdir(parents=True, exist_ok=True)
    with (paths.STATE_DIR / "party.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        members = load()
        yield members
        _save(members)


def add(species_id: int, shiny: bool) -> Member:
    """Adds a new member; Full if there is no room."""
    with editing() as members:
        if len(members) >= MAX_SIZE:
            raise Full()
        member = Member(max((m.uid for m in members), default=0) + 1, species_id, shiny)
        members.append(member)
    return member


def remove(choose: Callable[[list[Member]], list[Member]]) -> list[Member]:
    """Removes the members that choose picks from the party (in one locked
    step, so the choice is made from the current party). Errors from
    choose leave the party unchanged."""
    with editing() as members:
        leaving = choose(list(members))
        members[:] = [m for m in members if m not in leaving]
    return leaving
