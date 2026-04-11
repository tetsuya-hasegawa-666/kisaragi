---
name: skill-planner
description: `skill-distributor` が確定した skill 集合と前提情報を受け取り、実行順、phase、handoff、完了条件、検証順、closeout 順を決める orchestration skill。複数 skill をどの順番で実行させるかと、実際の実行管理を担う。skill の追加削除は行わない。
---

# Skill Planner

`skill-distributor` の次段で動き、確定済み skill 群を実行可能な計画へ落とす orchestration skill とする。

## Trigger Ownership

- この skill 自身は発火判断を持たない。
- `skill-distributor` から `selected_skills`、`no_skill_reason`、mark 解釈、最低限の文脈情報が渡された時だけ起動する。

## Core Workflow

1. `skill-distributor` から受け取った確定済み skill 集合と理由を確認する。
2. task を、`single-step`、`multi-step`、`multi-phase` のいずれかへ分類する。
3. 実行順を決める。
   - 文脈固定
   - 設計 / 参照整理
   - code / docs 編集
   - probe / test / check
   - evidence / closeout
4. 必要時だけ `phase-task-orchestrator` を呼び、phase header と phase 完了条件を固定する。
5. 各 skill へ handoff する入力と expected result を固定する。
6. 下位 skill の結果を見て、次に進めるか、前段へ戻すか、close 不可にするかを決める。
7. task 全体の close 条件を満たしたら closeout へ進める。

## Input

- `selected_skills`
- `why`
- `no_skill_reason`
- `admin_marks`
- `minimum_authoritative_docs`
- `task_summary`

## Output

- `execution_order`
- `phase_layout`
- `handoff_packet`
- `close_conditions`
- `fallback_path`

## Guard Rails

- 自分で skill 選定をやり直さない。skill 要否判断と最終選定は `skill-distributor` の ownership とする。
- 実行順を決めずに下位 skill を並列乱発しない。
- `Phase 1` と `Phase 4` を必要時に落とさない。
- 下位 skill の expected result を固定せずに handoff しない。
- close 条件を持たずに task を終えない。
- 確定済み skill 集合を planner の都合で増減しない。

## Coordination

- 複数 skill が選ばれた時の既定 orchestrator はこの skill とする。
- phase が必要な時は `phase-task-orchestrator` を呼ぶ。
- code / docs 同期が必要な時は `script-doc-sync-enforcer` または `documentation-watchkeeper` を前後に置く。
- 計算環境依存がある時は `runtime-structure-dependency-mapper` または `reference-rewire-operator` を適切な順に置く。

## References

- `references/execution-order-patterns.md`
- `references/phase-selection-rule.md`
- `references/handoff-packet-template.md`
- `scripts/build_execution_plan.py`
