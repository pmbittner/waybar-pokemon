import random

from PIL import Image

from waybar_pokemon import engine
from waybar_pokemon.pokemon.heart import DURATION, Heart
from waybar_pokemon.pokemon.sparkle import DURATION as DURATION_OF_TWINKLE
from waybar_pokemon.pokemon.sparkle import PERIOD, Sparkle

STAGE = engine.Stage(40, 30, random.Random(1))


def walker() -> engine.Walker:
    image = Image.new("RGBA", (20, 20), (0, 0, 255, 255))
    return engine.Walker(engine.Sprite(image, image), x=10.0, direction=1, state="idle")


def test_blend_keeps_what_is_below_and_cuts_off_outside():
    frame = Image.new("RGBA", (4, 4), (0, 0, 255, 255))
    engine.blend(frame, Image.new("RGBA", (4, 4), (255, 0, 0, 128)), 2, -2)
    assert frame.getpixel((3, 0))[3] == 255  # still opaque below a half-transparent pixel
    assert frame.getpixel((3, 0))[0] > 100  # and reddish
    assert frame.getpixel((0, 3)) == (0, 0, 255, 255)  # untouched


def test_fading_effects_do_not_punch_holes_into_what_is_below():
    frame = Image.new("RGBA", (40, 30), (0, 0, 255, 255))  # e.g. a sprite
    Heart(clock=DURATION * 0.9).draw(frame, walker(), STAGE)  # nearly faded
    Sparkle(clock=DURATION_OF_TWINKLE / 2).draw(frame, walker(), STAGE)
    assert {frame.getpixel((x, y))[3] for x in range(40) for y in range(30)} == {255}
    assert frame.tobytes() != Image.new("RGBA", (40, 30), (0, 0, 255, 255)).tobytes()  # both drew


def test_finished_effects_are_dropped():
    w = walker()
    w.effects += [Heart(), Sparkle()]
    for _ in range(round(DURATION / 0.1) + 1):
        w.update(0.1, STAGE)
    assert [type(e) for e in w.effects] == [Sparkle]


def test_the_sparkle_twinkles_now_and_then():
    sparkle = Sparkle()
    sizes = []
    for _ in range(round(2 * PERIOD / 0.05)):
        sparkle.update(0.05, STAGE)
        sizes.append(sparkle.size)
    assert set(sizes) == {0, 1, 2}
    assert sizes.count(0) > len(sizes) / 2  # mostly off
