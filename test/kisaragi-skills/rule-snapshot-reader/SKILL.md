---
name: rule-snapshot-reader
description: 共有 rule と project rule の現時点の有効面を短く確定する child skill。`AGENTS.md`、上位 `agents.md`、`project-truth-core.md`、`HAUB` などを読んで、今回の task に効く rule snapshot を作る時に使う。
---

# Rule Snapshot Reader

shared rule と project rule の最新有効面を、その task に必要な最小範囲だけで確定する child skill とする。

## Input

- `task_summary`
- `project_code`
- `candidate_authoritative_docs`

## Output

- `current_rule_snapshot`
- `rule_priority`
- `open_rule_questions`

## Guard Rails

- 新しい rule を決めない。
- project 固有 truth と shared governance を混同しない。
- 既存文書の要約に徹し、編集判断は親 skill へ返す。

## Coordination

- `skill-invoker` から必要時にだけ参照される。
- `authoritative-doc-scope-resolver` と `rule-diff-clarifier` の前段材料を返す。


