---
name: close-condition-definer
description: 今回の task を何で閉じるかを、成果物、文書更新、test、evidence の観点で固定する child skill。close 条件を曖昧にしたくない時に使う。
---

# Close Condition Definer

task の終わり方を、完成条件ではなく実行可能な close 条件として短く固定する child skill とする。

## Input

- `task_units`
- `selected_skills`
- `likely_write_docs`

## Output

- `close_conditions`
- `required_tests`
- `required_evidence`
- `cannot_close_if`

## Guard Rails

- test と evidence を省略前提にしない。
- `warning` と `blocker` を混同しない。
- 文書同期が必要な task を code 変更だけで閉じない。

## Coordination

- `skill-planner` から必要時にだけ参照される。
- `phase-task-orchestrator` の close 条件欄へ反映する。
