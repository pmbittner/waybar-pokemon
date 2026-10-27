import random

import pytest

from waybar_pokemon.pokemon import names, pokedex


@pytest.mark.parametrize(
    "query, language, species_id",
    [
        ("pantimos", "de", 122),
        ("mr mime", "de", 122),  # English works in every language
        ("Mr. Mime", "en", 122),
        ("flabebe", "en", 669),
        ("felo", "de", 906),
        ("25", "en", 25),
        ("Nidoran♀", "en", 29),
    ],
)
def test_find(query, language, species_id):
    assert pokedex.find(query, language).id == species_id


@pytest.mark.parametrize("query", ["nidoran", "xyz", "9999"])
def test_find_fails(query):
    with pytest.raises(names.NotFound):
        pokedex.find(query, "en")


def test_names_in_languages():
    mime = pokedex.find("122", "en")
    assert (mime.name("en"), mime.name("de")) == ("Mr. Mime", "Pantimos")


def test_random_species_from_generations():
    random.seed(1)
    assert all(pokedex.random_species([1]).generation == 1 for _ in range(50))
    assert pokedex.random_species([9]).id == 906
    with pytest.raises(pokedex.NoCandidates):
        pokedex.random_species([4])
