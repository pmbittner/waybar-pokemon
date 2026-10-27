"""The race for the berries.

When a berry has landed, every Pokémon that is free (standing or walking
around) and sees it runs to it. The first one there claims and eats it;
the others give up. A berry nobody sees stays until someone comes into
sight. A Pokémon that leaves while eating leaves the rest of the berry to
the others.

Who claimed a berry is only known by the Pokémon itself (Pokemon.meal), so
there is nothing to clean up when it leaves.
"""

from typing import Iterable

from ..engine import Stage
from .berry import Berry
from .creature import Pokemon

SIGHT = 80  # pixels: how far a Pokémon sees a berry (center to center)


def feed(pokemon: Iterable[Pokemon], berries: list[Berry], stage: Stage) -> list[Berry]:
    """Runs one step of the race after the update; returns the berries
    that are left."""
    pokemon = list(pokemon)
    berries = [b for b in berries if not b.eaten]
    for berry in berries:
        if not berry.landed or any(p.meal is berry for p in pokemon):
            continue
        racers = [p for p in pokemon if p.racing_for is berry]
        arrived = [p for p in racers if p.arrived]
        if arrived:
            winner = min(arrived, key=lambda p: abs(p.center - berry.center))
            winner.eat(berry)
            for loser in racers:
                if loser is not winner:
                    loser.give_up(stage)
        else:
            for p in pokemon:
                if p.available and abs(p.center - berry.center) <= SIGHT:
                    p.race_to(berry, stage)
    for p in pokemon:
        if p.racing_for is not None and p.racing_for not in berries:
            p.give_up(stage)  # it is gone
    return berries
