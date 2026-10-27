import json
import sys

import pytest

from waybar_pokemon import cli, i18n, paths


def run(monkeypatch, *arguments: str) -> None:
    monkeypatch.setattr(sys, "argv", ["waybar-pokemon", *arguments])
    cli.main()


@pytest.fixture(autouse=True)
def english_afterwards():
    yield
    i18n.set_language("en")


def configure(**values) -> None:
    paths.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    paths.CONFIG_FILE.write_text(json.dumps(values))


def test_spawn_list_despawn(monkeypatch, capsys, sprites):
    configure(names_language="de")
    run(monkeypatch, "spawn", "mr mime", "--shiny")
    run(monkeypatch, "list")
    assert capsys.readouterr().out == "Pantimos ✨\n1: Pantimos ✨\n"
    run(monkeypatch, "despawn", "pan")
    run(monkeypatch, "list")
    assert capsys.readouterr().out == ""


def test_errors_in_the_interface_language(monkeypatch, capsys):
    configure(ui_language="de")
    with pytest.raises(SystemExit):
        run(monkeypatch, "spawn", "xyz")
    assert capsys.readouterr().err == "waybar-pokemon: „xyz“ passt auf kein Pokémon.\n"
    with pytest.raises(SystemExit):
        run(monkeypatch, "berry", "xyz")
    assert "keine Beere" in capsys.readouterr().err


def test_invalid_config(monkeypatch, capsys):
    configure(fps=0)
    with pytest.raises(SystemExit) as exit:
        run(monkeypatch, "list")
    assert "fps must be positive" in str(exit.value)
