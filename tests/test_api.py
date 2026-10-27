import pytest

from waybar_pokemon import api
from waybar_pokemon.config import Config
from waybar_pokemon.pokemon import berries, names, pokedex

GERMAN = Config(names_language="de")


def test_spawn_by_name_in_the_configured_language(sprites):
    resident = api.spawn(GERMAN, "pantimos", shiny=True)
    assert (resident.uid, resident.species.id, resident.shiny, resident.name) == (1, 122, True, "Pantimos")
    assert api.residents(Config()) == [api.Resident(1, resident.species, True, "Mr. Mime")]


def test_random_spawns_from_the_generations(sprites):
    assert api.spawn(Config(random_generations=(9,))).species.id == 906
    assert api.spawn(Config(random_generations=(9,)), generations=(6,)).species.id == 669  # argument wins
    with pytest.raises(pokedex.NoCandidates):
        api.spawn(Config(), generations=(4,))


def test_spawn_needs_the_sprite():
    with pytest.raises(OSError):  # not cached, and no network
        api.spawn(Config(), "pikachu")
    assert api.residents(Config()) == []


def test_full(sprites):
    for _ in range(api.MAX_RESIDENTS):
        api.spawn(Config(), "mew")
    with pytest.raises(api.Full):
        api.spawn(Config(), "mew")


def test_despawn(sprites):
    for query in ("mew", "mewtwo", "mew", "pikachu"):
        api.spawn(GERMAN, query)
    assert api.despawn(GERMAN, "mew").uid == 3  # the newest Mew, not Mewtwo
    assert api.despawn(GERMAN, "mewt").name == "Mewtu"
    assert api.despawn(GERMAN, "1").uid == 1
    with pytest.raises(api.NotInHabitat):
        api.despawn(GERMAN, "bisasam")
    assert api.despawn(GERMAN).name == "Pikachu"  # the newest
    with pytest.raises(api.Empty):
        api.despawn(GERMAN)


def test_despawn_all(sprites):
    api.spawn(Config(), "mew")
    api.spawn(Config(), "pikachu")
    assert [r.name for r in api.despawn_all(Config())] == ["Mew", "Pikachu"]
    with pytest.raises(api.Empty):
        api.despawn_all(Config())


def test_drop_berry(sprites):
    assert api.drop_berry(GERMAN, "sinel") == api.DroppedBerry("oran", "Sinelbeere")
    assert berries.take_requests() == ["oran"]
    with pytest.raises(names.NotFound) as error:
        api.drop_berry(GERMAN, "xyz")
    assert error.value.kind == "berry"


def test_names():
    assert api.pokemon_names(GERMAN)[:2] == ["Bisasam", "Pikachu"]
    assert "Sinelbeere" in api.berry_names(GERMAN)
