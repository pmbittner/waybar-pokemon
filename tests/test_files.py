import pytest

from waybar_pokemon import daemon, files, paths
from waybar_pokemon.config import Config


def test_write_atomic(tmp_path):
    path = tmp_path / "deep" / "file.json"
    files.write_atomic(path, b"one")
    files.write_atomic(path, b"two")
    assert path.read_bytes() == b"two"
    assert [p.name for p in path.parent.iterdir()] == ["file.json"]  # no leftovers


def test_lock_without_waiting(tmp_path):
    with files.locked(tmp_path / "lock"):
        with pytest.raises(BlockingIOError):
            with files.locked(tmp_path / "lock", wait=False):
                pass
    with files.locked(tmp_path / "lock", wait=False):  # free again
        pass


def test_only_one_daemon():
    with files.locked(paths.DAEMON_LOCK):  # as if a daemon were running
        with pytest.raises(SystemExit) as exit:
            daemon.run(Config())
    assert "already running" in str(exit.value)
