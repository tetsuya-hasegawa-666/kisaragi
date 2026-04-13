from __future__ import annotations

import argparse
from pathlib import Path


DESIGN_REVIEW_SHEET = """| 項目 | 内容 |
| --- | --- |
| 目的 |  |
| 物理前提 |  |
| 不定性 |  |
| 入力 |  |
| 出力 |  |
| 分離単位 |  |
| 検証 |  |
| 失敗 |  |
| 影響範囲 |  |
"""

FUNCTION_INVENTORY = """| name | kind | purpose | inputs | outputs | validation | errors | docs_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
"""


def build_packet(target_name: str) -> str:
    return f"""# {target_name} Design Packet

## 設計審査票

{DESIGN_REVIEW_SHEET}

## Stage 責務表

| stage_id | purpose | inputs | outputs | docs_id |
| --- | --- | --- | --- | --- |

## 関数 / クラス一覧表

{FUNCTION_INVENTORY}

## 変更時レビュー

- docs ID 対応表を先に更新したか
- 責務境界を越える変更がないか
- validation と error context を保てているか
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("target_name")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    content = build_packet(args.target_name)
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content)


if __name__ == "__main__":
    main()
