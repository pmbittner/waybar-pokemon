import pytest

from waybar_pokemon.pokemon import names


@pytest.mark.parametrize(
    "text, normalized",
    [
        ("Mr. Mime", "mrmime"),
        ("Flabébé", "flabebe"),
        ("Typ:Null", "typnull"),
        ("Nidoran♀", "nidoran♀"),
        ("Großes Ding", "grossesding"),
        ("ピカチュウ", "ピカチュウ"),
        ("ガルーラ", "ガルーラ"),  # Japanese marks stay
    ],
)
def test_normalize(text, normalized):
    assert names.normalize(text) == normalized


CANDIDATES = [("mew", ["Mew"]), ("mewtwo", ["Mewtwo", "Mewtu"]), ("pikachu", ["Pikachu"])]


def test_exact_name_wins_over_longer_ones():
    assert names.match("mew", CANDIDATES, str) == "mew"


def test_unique_beginning():
    assert names.match("pika", CANDIDATES, str) == "pikachu"
    assert names.match("mewt", CANDIDATES, str) == "mewtwo"


def test_any_of_the_names():
    assert names.match("MEWTU", CANDIDATES, str) == "mewtwo"


def test_ambiguous_and_unknown():
    with pytest.raises(names.NotFound) as error:
        names.match("me", CANDIDATES, str)
    assert error.value.count == 2 and error.value.matches == ["mew", "mewtwo"]
    with pytest.raises(names.NotFound) as error:
        names.match("xyz", CANDIDATES, str)
    assert error.value.count == 0


def test_species_names_fall_back_to_english():
    assert names.species(122, "de", fallback="?") == "Pantimos"
    assert names.species(122, "fr", fallback="?") == "Mr. Mime"  # no French in the test tables
    assert names.species(9999, "de", fallback="?") == "?"
