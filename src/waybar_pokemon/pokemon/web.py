"""Downloads into the cache."""

import os
import threading
import urllib.request
from pathlib import Path


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "waybar-pokemon"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
    # A unique temporary name, as the daemon may download in the background.
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.{threading.get_ident()}.part")
    temporary.write_bytes(data)
    temporary.replace(destination)
