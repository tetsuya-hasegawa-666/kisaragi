---
name: task-intent-normalizer
description: prompt の意図を実装、同期、調査、確認、計画などの実務型へ正規化する child skill。複数意図が混在する task を planner が扱いやすい形へ整える時に使う。
---

# Task Intent Normalizer

曖昧な prompt を、実行順を決めやすい task intent 群へ正規化する child skill とする。

## Input

- `task_summary`
- `selected_skills`
- `marks_detected`

## Output

- `normalized_intents`
- `primary_intent`
- `secondary_intents`

## Guard Rails

- skill の追加削除をしない。
- user の主目的を補助論点に落とさない。
- 単一 task を不必要に分割しない。

## Coordination

- `skill-planner` から必要時にだけ参照される。
- `task-scope-splitter` と `close-condition-definer` の前段材料を返す。
