from __future__ import annotations

import json
import re
import sys
from pathlib import Path


CANDIDATE_ENCODINGS = [
    "utf-8",
    "utf-8-sig",
    "utf-16",
    "utf-16-le",
    "utf-16-be",
    "cp932",
    "shift_jis",
]

ENCODING_PRIORITY = {
    "utf-8": 0,
    "utf-8-sig": 1,
    "utf-16": 2,
    "utf-16-le": 3,
    "utf-16-be": 4,
    "cp932": 5,
    "shift_jis": 6,
}

MOJIBAKE_PATTERNS = [
    "�",
    "縺",
    "繧",
    "蜿",
    "逶",
    "髫",
    "ﾂ",
    "Ã",
    "ï»¿",
]


def text_score(text: str) -> int:
    score = 0
    for marker in MOJIBAKE_PATTERNS:
        score += text.count(marker) * 10
    score += len(re.findall(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", text)) * 20
    if not text.strip():
        score += 100
    if re.search(r"[ぁ-んァ-ヶ一-龠]", text):
        score -= 5
    if re.search(r"[A-Za-z0-9]", text):
        score -= 2
    return score


def detect(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    has_utf16_bom = raw.startswith((b"\xff\xfe", b"\xfe\xff"))
    null_ratio = raw.count(b"\x00") / max(len(raw), 1)
    candidates: list[dict[str, object]] = []
    for encoding in CANDIDATE_ENCODINGS:
        if encoding.startswith("utf-16") and not has_utf16_bom and null_ratio < 0.05:
            continue
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        score = text_score(text)
        candidates.append(
            {
                "encoding": encoding,
                "score": score,
                "suspicious": score >= 20,
                "preview": text[:120],
            }
        )

    if not candidates:
        return {
            "path": str(path),
            "encoding": None,
            "suspicious": True,
            "recoverable": False,
            "reason": "No supported encoding decoded successfully.",
        }

    best = sorted(
        candidates,
        key=lambda item: (item["score"], ENCODING_PRIORITY.get(str(item["encoding"]), 99)),
    )[0]
    return {
        "path": str(path),
        "encoding": best["encoding"],
        "suspicious": best["suspicious"],
        "recoverable": True,
        "score": best["score"],
        "preview": best["preview"],
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: check_markdown_encoding.py <path> [<path> ...]", file=sys.stderr)
        return 2

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    results = [detect(Path(arg)) for arg in sys.argv[1:]]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
