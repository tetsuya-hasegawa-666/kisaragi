# execution order patterns

## 目的

- `skill-planner` が specialist skill の実行順を決める時の既定 pattern を持つ。

## pattern 1: script 変更 + 文書同期

1. 文脈固定
2. 設計 / 参照整理
3. code / docs 編集
4. test / probe
5. evidence / closeout

推奨 skill:
- `phase-task-orchestrator`
- `design-first-script-builder`
- `reference-rewire-operator`
- `documentation-watchkeeper`

## pattern 2: script 変更 + 依存棚卸し

1. 文脈固定
2. 依存棚卸し
3. 必要なら参照切替
4. code / docs 編集
5. probe / unittest
6. evidence / closeout

## pattern 3: external compute

1. 文脈固定
2. runbook / input contract 確認
3. output tree / persistent storage 確認
4. 実行
5. final output 保存
6. cleanup 判断

## pattern 4: BDD / TDD / gate 更新

1. 文脈固定
2. story / behavior 整理
3. TDD task 化
4. gate 状態更新
5. handover / closeout
