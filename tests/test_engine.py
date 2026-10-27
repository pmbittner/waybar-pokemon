import random

from PIL import Image

from waybar_pokemon import engine


def stage() -> engine.Stage:
    return engine.Stage(100, 30, random.Random(1))


def sprite() -> engine.Sprite:
    return engine.Sprite(Image.new("RGBA", (10, 10), "red"), Image.new("RGBA", (10, 10), "blue"))


def test_png_file_is_only_written_when_the_picture_changes(tmp_path):
    output = engine.PngFile(tmp_path / "frame.png")
    frame = Image.new("RGBA", (10, 10))
    output.present(frame)
    first = output.path.stat().st_mtime_ns
    output.path.unlink()
    output.present(frame.copy())
    assert not output.path.exists()  # same picture: not written again
    frame.putpixel((0, 0), (255, 0, 0, 255))
    output.present(frame)
    assert output.path.exists() and first


def test_walker_drops_onto_the_ground():
    s = stage()
    walker = engine.Walker.drop_in(sprite(), s)
    assert walker.y < 0
    for _ in range(20):
        walker.update(0.1, s)
    assert walker.y == 0 and walker.state in ("idle", "walk")


def test_walker_goes_to_a_place():
    s = stage()
    walker = engine.Walker(sprite(), x=10.0, direction=-1, state="idle")
    walker.go_to(50.0, speed=20.0)
    assert walker.direction == 1
    for _ in range(25):
        walker.update(0.1, s)
    assert walker.arrived and walker.x == 50.0
