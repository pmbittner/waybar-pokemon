from waybar_pokemon import i18n


def test_every_language_has_every_text():
    for language, messages in i18n.MESSAGES.items():
        assert set(messages) == set(i18n.MESSAGES["en"]), language


def test_texts():
    i18n.set_language("de")
    try:
        assert i18n.text("wild", name="Pantimos") == "Ein wildes Pantimos erscheint!"
    finally:
        i18n.set_language("en")
    assert i18n.text("wild", name="Pantimos") == "A wild Pantimos appeared!"
