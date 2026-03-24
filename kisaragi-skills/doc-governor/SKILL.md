---
name: doc-governor
description: version 付き spec 群の文書整合を保つ。文書 file を更新するとき、旧版を old_files へ移すとき、file 間参照を点検するとき、命名規則や version 規則を適用するときに使う。
---

# Doc Governor

## 適用境界

- version 付き spec 群、archive 移動、固定 layer の current docs、相互参照の整合確認に使う。
- root、docs、develop、agent file をまたぐ全体 topology 再設計を主目的にするときの第一選択にはしない。
- 会話起点で同一 turn 中に起きる documentation drift 確認を主目的にするときの第一選択にはしない。

文書構造の信頼性を保つために使う。

## Workflow
1. `docs/index.md` を読み、`docs/artifact/`、`docs/process/`、`docs/observability/`、`docs/metrics/`、`docs/reference/` の current source-of-truth file を特定する。
2. 文書を差し替えるときは、場当たり的な新規 file を増やさず、固定 layer の文書へ現役内容を集約する。
3. current source-of-truth file にある相互参照を更新する。
4. 置き換えられた文書が `docs/archive/legacy_docs/` 配下へ移されていることを確認する。
5. 移動理由が分かるように `docs/index.md` と必要な archive 対応表を更新する。

## 点検項目
- `docs/index.md` が実際の current 構造と一致している。
- current docs から archive 済み legacy path への古い参照が残っていない。
- 現役内容が archive に重複せず、固定 layer 文書に存在している。
- archive 移動後も履歴と移行経緯を追跡できる。
