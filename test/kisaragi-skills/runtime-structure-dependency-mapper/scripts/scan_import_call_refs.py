from __future__ import annotations

import re
from pathlib import Path


IMPORT_RE = re.compile(r"^\s*(from\s+\S+\s+import|import\s+\S+)", re.MULTILINE)


def scan_file(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    imports = IMPORT_RE.findall(text)
    return {"path": path, "imports": imports}


if __name__ == "__main__":
    print(scan_file(__file__))
