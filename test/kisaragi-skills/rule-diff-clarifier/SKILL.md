---
name: rule-diff-clarifier
description: prompt で求められた rule と、現行の shared / project rule との差分を明示する child skill。新規 rule、例外、明確化だけを切り分けたい時に使う。
---

# Rule Diff Clarifier

prompt が現行 rule の追認なのか、差分なのか、例外なのかを短く分解する child skill とする。

## Input

- `task_summary`
- `current_rule_snapshot`
- `marks_detected`

## Output

- `requested_rule_delta`
- `needs_shared_rule_change`
- `needs_project_rule_change`
- `temporary_exception_candidate`

## Guard Rails

- 差分の存在を確認せずに rule 変更前提で進めない。
- shared 変更と project 固有変更を混同しない。
- 例外運用を恒久 rule として扱わない。

## Coordination

- `skill-invoker` から必要時にだけ参照される。
- `AGENTS.md` 変更か project 文書変更かの切り分け材料を返す。


