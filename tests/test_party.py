import json

from waybar_pokemon import paths
from waybar_pokemon.pokemon import party


import pytest


def test_add_and_remove():
    party.add(25, False)
    party.add(1, True)
    assert [(m.uid, m.species_id, m.shiny) for m in party.load()] == [(1, 25, False), (2, 1, True)]
    assert party.remove(lambda members: members[:1]) == [party.Member(1, 25, False)]
    assert party.add(150, False).uid == 3  # uids are not reused while others are out


def test_full():
    for _ in range(party.MAX_SIZE):
        party.add(25, False)
    with pytest.raises(party.Full):
        party.add(25, False)


def test_a_failing_choice_changes_nothing():
    party.add(25, False)

    def choose(members):
        raise LookupError("no")

    with pytest.raises(LookupError):
        party.remove(choose)
    assert len(party.load()) == 1


def test_empty_or_broken_file():
    assert party.load() == []
    paths.PARTY_FILE.parent.mkdir(parents=True)
    paths.PARTY_FILE.write_text("{not json")
    assert party.load() == []


def test_older_files_with_names_still_load():
    paths.PARTY_FILE.parent.mkdir(parents=True)
    paths.PARTY_FILE.write_text(json.dumps([{"uid": 3, "species_id": 122, "name": "Mr Mime", "shiny": False}]))
    assert party.load() == [party.Member(3, 122, False)]
