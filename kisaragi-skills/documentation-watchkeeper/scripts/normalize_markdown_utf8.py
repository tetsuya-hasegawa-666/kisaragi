from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from check_markdown_encoding import detect  # noqa: E402


def normalize(path: Path) -> int:
    result = detect(path)
    if not result.get("recoverable"):
        print(f"[normalize] unrecoverable: {path}", file=sys.stderr)
        return 1

    encoding = result["encoding"]
    if encoding is None:
        print(f"[normalize] no encoding detected: {path}", file=sys.stderr)
        return 1

    text = path.read_bytes().decode(str(encoding))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[normalize] wrote UTF-8: {path}")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: normalize_markdown_utf8.py <path> [<path> ...]", file=sys.stderr)
        return 2

    exit_code = 0
    for arg in sys.argv[1:]:
        exit_code = max(exit_code, normalize(Path(arg)))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
