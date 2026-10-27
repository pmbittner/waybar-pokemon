"""Names of Pokémon and berries in the languages of the games, and looking
them up by what the user typed.

The names come from PokeAPI's tables (data.py).
A name missing in a language falls back to English.
"""

import unicodedata
from functools import cache
from typing import Callable, Hashable, Iterable, TypeVar

from . import data

# The languages with names, by PokeAPI's identifiers and ids.
LANGUAGES = {
    "en": 9, "de": 6, "fr": 5, "it": 8, "es": 7, "es-419": 14,
    "ja": 11, "ja-hrkt": 1, "ja-roma": 2, "ko": 3, "zh-hans": 12, "zh-hant": 4,
}

K = TypeVar("K", bound=Hashable)


class NotFound(LookupError):
    """No match or more than one; matches holds up to five names of them,
    kind says what was looked for ("pokemon" or "berry")."""

    def __init__(self, query: str, count: int, matches: list[str], kind: str = "pokemon") -> None:
        super().__init__(f"'{query}' matches {count} {kind}" + (f": {', '.join(matches)}" if matches else ""))
        self.query, self.count, self.matches, self.kind = query, count, matches, kind


@cache
def _species_names(language: str) -> dict[int, str]:
    language_id = str(LANGUAGES[language])
    return {int(r["pokemon_species_id"]): r["name"] for r in data.rows("pokemon_species_names") if r["local_language_id"] == language_id}


@cache
def _item_names(language: str) -> dict[str, str]:
    """By the item's identifier, e.g. "oran-berry"."""
    identifiers = {r["id"]: r["identifier"] for r in data.rows("items")}
    language_id = str(LANGUAGES[language])
    return {identifiers[r["item_id"]]: r["name"] for r in data.rows("item_names") if r["local_language_id"] == language_id and r["item_id"] in identifiers}


def species(species_id: int, language: str, fallback: str) -> str:
    return _species_names(language).get(species_id) or _species_names("en").get(species_id) or fallback


def item(identifier: str, language: str, fallback: str) -> str:
    return _item_names(language).get(identifier) or _item_names("en").get(identifier) or fallback


def normalize(text: str) -> str:
    """For comparing names: case, accents, spaces and punctuation do not
    matter ("mr mime" finds "Mr. Mime", "flabebe" finds "Flabébé")."""
    characters: list[str] = []
    for character in unicodedata.normalize("NFKD", text.casefold()):
        # Drop accents of Latin letters only; e.g. Japanese marks stay.
        if unicodedata.combining(character) and characters and characters[-1].isascii():
            continue
        characters.append(character)
    text = unicodedata.normalize("NFC", "".join(characters))
    return "".join(c for c in text if c.isalnum() or c in "♀♂")


def match_all(query: str, candidates: Iterable[tuple[K, list[str]]]) -> list[K]:
    """The candidates with a name that is the query, or else the ones whose
    name begins with it. Candidates are (key, names) pairs."""
    key = normalize(query)
    normalized = [(k, [normalize(n) for n in names]) for k, names in candidates]
    matches = [k for k, names in normalized if key in names]
    if not matches and key:
        matches = [k for k, names in normalized if any(n.startswith(key) for n in names)]
    return matches


def match(query: str, candidates: Iterable[tuple[K, list[str]]], show: Callable[[K], str], kind: str = "pokemon") -> K:
    """The one candidate that match_all finds; NotFound otherwise. show
    names a candidate in the error."""
    matches = match_all(query, candidates)
    if len(matches) != 1:
        raise NotFound(query, len(matches), [show(k) for k in matches[:5]], kind)
    return matches[0]
