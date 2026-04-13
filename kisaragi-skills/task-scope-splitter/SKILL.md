---
name: task-scope-splitter
description: 1 prompt に複数 task が混在する時に、順序付きの task 単位へ分割する child skill。未完了指示を落とさずに planner の phase へ載せたい時に使う。
---

# Task Scope Splitter

複数指示を、取りこぼしなく順序付き task 群へ分ける child skill とする。

## Input

- `task_summary`
- `normalized_intents`
- `selected_skills`

## Output

- `task_units`
- `deferred_items`
- `phase_candidates`

## Guard Rails

- 指示を理由説明なしに捨てない。
- phase と task unit を混同しない。
- 依存関係を無視して parallel 前提にしない。

## Coordination

- `skill-planner` から必要時にだけ参照される。
- `phase-task-orchestrator` の材料として使う。
