import pytest

from waybar_pokemon.pokemon import berries, names


def test_names_in_languages():
    assert berries.display_name("oran", "de") == "Sinelbeere"
    assert berries.display_name("oran", "en") == "Oran Berry"
    assert berries.display_name("cheri", "de") == "Cheri Berry"  # not in the test tables


@pytest.mark.parametrize("query, name", [("sinel", "oran"), ("Oran Berry", "oran"), ("tsitru", "sitrus"), ("pecha", "pecha")])
def test_find(query, name):
    assert berries.find(query, "de") == name


def test_find_fails():
    with pytest.raises(names.NotFound):
        berries.find("beere", "de")


def test_requests_are_taken_once():
    assert berries.take_requests() == []
    berries.request("oran")
    berries.request("sitrus")
    assert berries.take_requests() == ["oran", "sitrus"]
    assert berries.take_requests() == []
