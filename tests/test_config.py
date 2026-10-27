import json

import pytest

from waybar_pokemon import config, paths


def write_config(values: dict) -> None:
    paths.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    paths.CONFIG_FILE.write_text(json.dumps(values))


def test_defaults_without_a_file():
    settings = config.load()
    assert (settings.width, settings.height, settings.fps) == (240, 30, 10)
    assert settings.names_language == settings.ui_language == "en"


def test_values_from_the_file():
    write_config({"names_language": "de", "random_generations": [1, 2], "cache_all_sprites": True, "wild_berries_per_hour": 2})
    settings = config.load()
    assert settings.names_language == "de"
    assert settings.random_generations == (1, 2)
    assert settings.cache_all_sprites is True
    assert settings.wild_berries_per_hour == 2.0


@pytest.mark.parametrize(
    "values",
    [
        {"colour": "red"},  # unknown setting
        {"cache_all_sprites": "yes"},
        {"names_language": "klingon"},
        {"ui_language": "fr"},  # no texts in French yet
        {"fps": 0},
        {"width": -1},
        {"wild_berries_per_hour": -1},
        {"wild_berries_per_hour": "often"},
        {"random_generations": ["one"]},
        {"height": 2.5},
    ],
)
def test_invalid_settings(values):
    write_config(values)
    with pytest.raises(ValueError):
        config.load()


def test_the_type_is_valid_without_a_file_too():
    with pytest.raises(ValueError):
        config.Config(names_language="klingon")
    assert config.Config(wild_berries_per_hour=2).wild_berries_per_hour == 2.0


@pytest.mark.parametrize(
    "text, generations",
    [("1-4", (1, 2, 3, 4)), ("1,3,5-6", (1, 3, 5, 6)), ("9", (9,)), (" 2 - 3 ", (2, 3))],
)
def test_parse_generations(text, generations):
    assert config.parse_generations(text) == generations
