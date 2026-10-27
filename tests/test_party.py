import json

from waybar_pokemon import paths
from waybar_pokemon.pokemon import party


def test_editing_saves():
    with party.editing() as members:
        members.append(party.Member(party.next_uid(members), 25, False))
        members.append(party.Member(party.next_uid(members), 1, True))
    assert [(m.uid, m.species_id, m.shiny) for m in party.load()] == [(1, 25, False), (2, 1, True)]


def test_empty_or_broken_file():
    assert party.load() == []
    paths.PARTY_FILE.parent.mkdir(parents=True)
    paths.PARTY_FILE.write_text("{not json")
    assert party.load() == []


def test_older_files_with_names_still_load():
    paths.PARTY_FILE.parent.mkdir(parents=True)
    paths.PARTY_FILE.write_text(json.dumps([{"uid": 3, "species_id": 122, "name": "Mr Mime", "shiny": False}]))
    assert party.load() == [party.Member(3, 122, False)]
