import urllib.error

import pytest

from waybar_pokemon.pokemon import sprites


@pytest.fixture
def downloads(monkeypatch):
    """Records the URLs; only the ones in `available` exist."""
    tried: list[str] = []
    available: set[str] = set()

    def download(url, path):
        tried.append(url)
        if url not in available:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"png")

    monkeypatch.setattr(sprites, "download", download)
    return tried, available


def test_icons_first_then_the_front_sprite(downloads):
    tried, available = downloads
    available.add(sprites.FRONT_URL.format(variant="shiny/", id=906))
    path = sprites.pokemon(906, shiny=True)
    assert path.read_bytes() == b"png"
    assert [url.split("/")[-3] for url in tried[:2]] == ["pokemon-gen7x", "pokemon-gen8"]
    assert tried[-1].endswith("/shiny/906.png")

    tried.clear()
    assert sprites.pokemon(906, shiny=True) == path  # cached now
    assert tried == []


def test_other_errors_are_not_hidden(downloads, monkeypatch):
    def broken(url, path):
        raise urllib.error.HTTPError(url, 500, "Server Error", None, None)

    monkeypatch.setattr(sprites, "download", broken)
    with pytest.raises(urllib.error.HTTPError):
        sprites.pokemon(25, shiny=False)


def test_berries(downloads):
    tried, available = downloads
    available.add(sprites.BERRY_URL.format(name="oran"))
    assert sprites.berry("oran").name == "oran.png"
