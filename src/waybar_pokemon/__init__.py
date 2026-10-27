"""Little Pokémon walking around in a waybar module."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("waybar-pokemon")  # from pyproject.toml
except PackageNotFoundError:  # not installed
    __version__ = "unknown"
