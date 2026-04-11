from __future__ import annotations

import re
from pathlib import Path


PATH_TOKENS = ("path", "dir", "root", "manifest", "artifact", "output", "input")


def scan_file(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    hits = [line.strip() for line in text.splitlines() if any(token in line.lower() for token in PATH_TOKENS)]
    return {"path": path, "hits": hits[:50]}


if __name__ == "__main__":
    print(scan_file(__file__))
