---
name: design-first-script-builder
description: script、notebook、runbook を設計駆動で新規作成または再構成する。責務分離、stage 分割、設計審査票、関数 / クラス一覧表、docs ID 対応、validation / error handling 契約を先に固定してから実装したい時に使う。対象 project が `HAUB` などの handoff 対照表や contract probe を持つ時は、その対照表を設計契約へ取り込み、編集後に probe / test まで回す task で使う。
---

# Design First Script Builder

script や notebook を「あとから継ぎ足す」形ではなく、「設計契約を先に固定してから実装する」流れへ戻す skill とする。

## Trigger Ownership

- この skill 自身は発火判断を持たない。
- `skill-distributor` と `skill-planner` が、設計駆動の script / notebook / runbook 作業だと判断した時だけ呼ばれる。

## Workflow

1. 対象 script の目的、入出力、制約、既存の詰まり方を短く整理する。
2. `references/design-review-sheet.md` の列に沿って設計審査票を作る。
3. stage / pipeline を分割し、各 stage の責務境界と input / output を決める。
4. `references/function-inventory-template.md` に沿って関数 / クラス一覧表を作り、全要素へ `docs_id` を振る。
5. pure function、I/O layer、orchestration layer、validation layer を分ける。
6. 実装前に、例外条件、recoverable / fatal、検証条件、影響範囲を明示する。
7. 対象 project が `HAUB` などの handoff 対照表を持つ時は、producer / consumer / artifact path を先に照合し、必要な row を code 編集前に決める。
8. その後にだけ code を書く。code は docs 契約から逸脱しないように保つ。
9. 変更後は `references/review-checklist.md` で責務逸脱、暗黙状態、docs 不整合、validation 抜け、handoff 対照表の不足を点検する。
10. contract probe や source test を持つ project では、同じ task で必ず実行し、pass を確認してから close する。

## 必須成果物

- 設計審査票
- stage / pipeline 責務表
- 関数 / クラス一覧表
- docs ID 対応表
- validation / error handling 契約
- 実装後レビュー結果

## 固定ルール

- 1関数1責務を守る。
- 読込、推定、保存を 1 関数へ混在させない。
- 暗黙状態、無名 tuple/list 返却、`dict` 乱用を避ける。
- 座標系、単位、向き、index 意味を型名か列名へ出す。
- validation は estimate / transform の直後に置く。
- error は `何が壊れたか` と `どの前提で壊れたか` を含める。
- docs は長文説明ではなく、責務契約、入出力、検証、失敗条件に限定する。
- docs ID 対応表を更新せずに code だけ変えない。
- `HAUB` handoff 対照表や path contract probe を持つ project では、それらを更新せずに script だけ変えない。

## 推奨運用

- notebook は orchestration 面に寄せ、重い helper や wrapper 生成 code は source file へ逃がす。
- pair 文書を持つ runbook は、設計契約書と source-sync 手段を同じ task で更新する。
- 拡張時は stage を追加し、既存 stage の責務を増やし過ぎない。
- 修正時は既存の docs_id を起点に局所変更で閉じる。
- script edit 中に artifact handoff が変わるなら、`HAUB` の対照表 row と probe / test を同じ task で更新する。

## 参照

- `references/design-review-sheet.md`
- `references/function-inventory-template.md`
- `references/review-checklist.md`
- `scripts/render_design_packet.py`
