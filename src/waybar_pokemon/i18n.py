"""Texts of the user interface (notifications, menus, messages of the
commands) in the supported languages.

The names of Pokémon and berries come from the games instead, in their own
language setting (see pokemon/names.py). Command line help and the
daemon's log stay in English.

To add a language, copy the English texts and translate them.
"""

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "wild": "A wild {name} appeared!",
        "wild_shiny": "✨ A shiny {name} appeared! ✨",
        "returned_one": "{names} returned to its Poké Ball.",
        "returned_many": "{names} returned to their Poké Balls.",
        "berry_fell": "A {berry} fell from the sky!",
        "full": "The habitat is full ({max} Pokémon). Despawn one first.",
        "nobody": "No Pokémon to despawn.",
        "not_in_habitat": "No '{query}' in the habitat.",
        "no_pokemon": "'{query}' matches no Pokémon.",
        "many_pokemon": "'{query}' matches {count} Pokémon: {matches}",
        "no_berry": "'{query}' matches no berry.",
        "many_berries": "'{query}' matches {count} berries: {matches}",
        "no_generation": "No Pokémon in generation {generations}.",
        "offline": "{error} (no internet? See cache_all_sprites in the README.)",
        "random": "Random",
        "random_from": "Random (generation {generations})",
        "everyone": "Everyone",
        "progress": "{done}/{total} files",
        "failed": "{failed} files could not be downloaded.",
    },
    "de": {
        "wild": "Ein wildes {name} erscheint!",
        "wild_shiny": "✨ Ein schillerndes {name} erscheint! ✨",
        "returned_one": "{names}, komm zurück!",
        "returned_many": "{names}, kommt zurück!",
        "berry_fell": "Eine {berry} fällt vom Himmel!",
        "full": "Das Habitat ist voll ({max} Pokémon). Schicke erst eines zurück.",
        "nobody": "Kein Pokémon zum Zurückschicken.",
        "not_in_habitat": "Kein „{query}“ im Habitat.",
        "no_pokemon": "„{query}“ passt auf kein Pokémon.",
        "many_pokemon": "„{query}“ passt auf {count} Pokémon: {matches}",
        "no_berry": "„{query}“ passt auf keine Beere.",
        "many_berries": "„{query}“ passt auf {count} Beeren: {matches}",
        "no_generation": "Keine Pokémon in Generation {generations}.",
        "offline": "{error} (kein Internet? Siehe cache_all_sprites in der README.)",
        "random": "Zufällig",
        "random_from": "Zufällig (Generation {generations})",
        "everyone": "Alle",
        "progress": "{done}/{total} Dateien",
        "failed": "{failed} Dateien konnten nicht heruntergeladen werden.",
    },
}

LANGUAGES = tuple(MESSAGES)

_language = "en"


def set_language(language: str) -> None:
    global _language
    if language not in MESSAGES:
        raise ValueError(f"Unknown language '{language}' (available: {', '.join(LANGUAGES)})")
    _language = language


def text(key: str, **fields: object) -> str:
    """The text in the current language, falling back to English."""
    template = MESSAGES[_language].get(key) or MESSAGES["en"][key]
    return template.format(**fields)
