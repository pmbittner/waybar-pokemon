"""Downloads into the cache."""

import urllib.request
from pathlib import Path

from ..files import write_atomic


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "waybar-pokemon"})
    with urllib.request.urlopen(request, timeout=30) as response:
        write_atomic(destination, response.read())
