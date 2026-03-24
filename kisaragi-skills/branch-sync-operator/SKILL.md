---
name: branch-sync-operator
description: main / dev / stg branch を明示的な確認と報告付きで安全に同期する。branch の乖離を解消し、整列させる必要があるときに使う。
---

# Branch Sync Operator

branch head を制御された手順で同期するときに使う。

## Workflow
1. 現在の remote head を fetch して確認する。
2. strategy を決める。
   - merge
   - force-with-lease（明示指示がある場合のみ）
3. 同期を実行する。
4. すべての branch hash を確認する。
5. 結果の commit ID を正確に報告する。

## 安全規則
- 明示指示なしで破壊的同期を行わない。
- before / after の commit hash を必ず示す。
- conflict が出たら中断し、明確に報告する。
