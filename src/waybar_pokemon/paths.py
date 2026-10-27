"""Where waybar-pokemon keeps its files."""

import os
from pathlib import Path


def _xdg_dir(variable: str, fallback: str) -> Path:
    return Path(os.environ.get(variable) or Path.home() / fallback)


# Downloaded data: PokeAPI's tables and the sprites.
CACHE_DIR = _xdg_dir("XDG_CACHE_HOME", ".cache") / "waybar-pokemon"
SPRITE_DIR = CACHE_DIR / "sprites"

# The current party, kept across restarts; berries to drop, until the
# daemon takes them; and the locks.
STATE_DIR = _xdg_dir("XDG_STATE_HOME", ".local/state") / "waybar-pokemon"
PARTY_FILE = STATE_DIR / "party.json"
PARTY_LOCK = STATE_DIR / "party.lock"
BERRY_REQUESTS = STATE_DIR / "berries"
BERRY_LOCK = STATE_DIR / "berries.lock"
DAEMON_LOCK = STATE_DIR / "daemon.lock"  # held by the running daemon

# Optional settings for the daemon (see config.py).
CONFIG_FILE = _xdg_dir("XDG_CONFIG_HOME", ".config") / "waybar-pokemon" / "config.json"


def default_frame_path() -> Path:
    """The rendered frame that waybar shows.

    It is rewritten several times per second, so it lives in /dev/shm
    (memory) instead of on disk. The path must be known in advance for
    waybar's config, so it only depends on the user name.
    """
    user = os.environ.get("USER") or str(os.getuid())
    return Path("/dev/shm") / f"waybar-pokemon-{user}" / "frame.png"
