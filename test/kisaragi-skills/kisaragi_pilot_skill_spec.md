# kisaragi pilot skill spec

## 文書の目的

- refresh 主線の pilot として、最初に具体化する core skill を定義する。
- 対象は `receipt-manager`、`skill-invoker`、`response-manager` とする。
- `skill-planner` は既存実装を流用する前提で、pilot 文書では新規 3 skill の責務を先に固定する。

## 共通前提

- 正本は文書であり、skill は文書を置き換えない。
- project task の `READ` 下限は、常に project truth 正本と統合計画書とする。
- `receipt-manager -> skill-invoker -> skill-planner -> response-manager` の順序は固定する。
- specialist skill は自分で発火判断を持たず、`skill-invoker` と `skill-planner` の handoff を前提とする。

## pilot skill 一覧

| skill | 主目的 | 位置づけ |
| --- | --- | --- |
| `receipt-manager` | prompt 全体の解釈を固定する | 常時入口前段 |
| `skill-invoker` | 必要 skill 集合と読込下限を確定する | 常時統合入口 |
| `response-manager` | 最終応答を整形する | 常時出口後段 |

## skill 1. `receipt-manager`

### 目的

- prompt を部分読取せず全件 review する。
- 明示要求、暗黙要求、制約、禁止事項、期待形式を抽出する。
- 実行に入る前の解釈精度を固定する。

### 入力

- `prompt_full`
- 継続文脈
- admin mark

### 出力

- `explicit_requests`
- `implicit_requests`
- `constraints`
- `expected_output`
- `task_type`
- `interpretation`
- `handoff_to: skill-invoker`

### 非責務

- skill 選定
- 実行順設計
- 文書や code の直接編集
- admin 向け最終応答の整形

## skill 2. `skill-invoker`

### 目的

- `receipt-manager` の解釈結果から、必要 skill 集合を確定する。
- `read_set_minimum` と `deferred_skills` と `blocked_skills` を分離する。
- trigger ownership を一箇所に集約する。

### 入力

- `receipt-manager` の出力
- 現在文脈
- 管理下の skill registry

### 出力

- `selected_skills`
- `deferred_skills`
- `blocked_skills`
- `read_set_minimum`
- `decision_log`
- `handoff_to: skill-planner`

### 非責務

- 実行順設計
- 応答整形
- 正本文書直接編集

## skill 3. `response-manager`

### 目的

- `skill-planner` と specialist skill の結果を admin 向けに整形する。
- 粒度、表現、箇条書き、要約順を整える。
- 未実施事項を実施済みに見せない。

### 入力

- `receipt-manager` の解釈結果
- `skill-planner` の実行結果
- specialist skill の結果

### 出力

- admin 向け応答本文
- 残件
- 必要時の確認依頼

### 非責務

- skill 選定や再選定
- 事実改変
- 直接編集

## `skill-planner` との関係

- `skill-planner` は既存の orchestration owner として維持する。
- `skill-planner` は `skill-invoker` が確定した集合だけを扱う。
- `skill-planner` は skill 集合の追加削除を行わない。

## 次段で決めること

1. 現行単一入口をどの段階で `receipt-manager` と `skill-invoker` へ分解するか。
2. `response-manager` を独立 skill として実装するか、応答整形 helper から始めるか。
3. `read_set_minimum` の schema をどこに置くか。
4. 既存 specialist skill の handoff packet を新主線にどう合わせるか。
