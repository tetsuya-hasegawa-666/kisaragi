---
name: authoritative-doc-scope-resolver
description: 今回の task で実質的な管理対象になる正本文書と関連文書の範囲を決める child skill。対象 path、project code、task 要旨から `must_read_docs` と `likely_write_docs` を切り出す時に使う。
---

# Authoritative Doc Scope Resolver

今回の task がどの正本文書を読むべきか、どの文書まで整合更新の対象に含めるべきかを確定する child skill とする。

## Input

- `task_summary`
- `project_code`
- `working_files`
- `current_rule_snapshot`

## Output

- `must_read_docs`
- `likely_write_docs`
- `do_not_treat_as_truth`

## Guard Rails

- 文書の優先順位を勝手に入れ替えない。
- `sharedlogs` や raw artifact を正本扱いしない。
- `READ` 必須と `WRITE` 候補を混同しない。

## Coordination

- `skill-invoker` から必要時にだけ参照される。
- `script-doc-sync-enforcer` と `documentation-watchkeeper` の事前条件を固める。
