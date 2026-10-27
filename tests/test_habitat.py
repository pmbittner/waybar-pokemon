"""The race for the berries."""

import random

from PIL import Image

from waybar_pokemon import engine
from waybar_pokemon.pokemon import party
from waybar_pokemon.pokemon.berry import Berry
from waybar_pokemon.pokemon.habitat import Habitat


def habitat_with(*species_ids: int) -> Habitat:
    for species_id in species_ids:
        party.add(species_id, False)
    habitat = Habitat(engine.Stage(240, 30, random.Random(3)), wild_berries_per_hour=0)
    habitat.sync()
    return habitat


def place(habitat: Habitat, uid: int, x: float):
    pokemon = habitat.pokemon[uid]
    pokemon.x, pokemon.y = x, 0.0
    pokemon.stop(habitat.stage)
    return pokemon


def lay_berry(habitat: Habitat, x: float) -> Berry:
    berry = Berry(Image.new("RGBA", (10, 10), "blue"), x=x, y=0.0)
    habitat.berries.append(berry)
    return berry


def run(habitat: Habitat, seconds: float, until=lambda: False) -> None:
    for _ in range(round(seconds * 10)):
        habitat.sync()
        habitat.update(0.1)
        if until():
            return


def test_the_closest_one_in_sight_wins(sprites):
    habitat = habitat_with(25, 1, 150)
    near, far, away = place(habitat, 1, 60), place(habitat, 2, 20), place(habitat, 3, 220)
    berry = lay_berry(habitat, 100)  # centers: berry 105, near 70, far 30, away 230

    run(habitat, 1)
    assert far.racing_for is berry or far.state == "eat" or near.state == "eat"
    run(habitat, 5, until=lambda: near.state == "eat")
    assert near.state == "eat"
    assert far.racing_for is None and far.state != "eat"
    assert away.racing_for is None

    run(habitat, 5, until=lambda: near.heart is not None)
    assert habitat.berries == []  # gone with the last bite
    assert near.heart is not None and near.state != "eat"  # happy


def test_a_berry_nobody_sees_stays():
    habitat = habitat_with()
    berry = lay_berry(habitat, 100)
    run(habitat, 3)
    assert habitat.berries == [berry] and berry.bites == 0


def test_a_despawned_eater_leaves_the_berry_to_the_others(sprites):
    habitat = habitat_with(25, 1)
    eater, other = place(habitat, 1, 80), place(habitat, 2, 0)  # other out of sight
    berry = lay_berry(habitat, 100)
    run(habitat, 3, until=lambda: eater.state == "eat")
    assert eater.state == "eat"

    party.remove(lambda members: [m for m in members if m.uid == 1])
    place(habitat, 2, 60)  # comes into sight
    run(habitat, 10, until=lambda: other.state == "eat")
    assert other.state == "eat" and berry in habitat.berries
