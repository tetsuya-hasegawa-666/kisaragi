---
name: runtime-bootstrap-scope-resolver
description: fresh runtime から再現する最小 bootstrap 範囲を決める child skill。trial 往復ではなく clean bootstrap runbook に昇格させるべき範囲を切る時に使う。
---

# Runtime Bootstrap Scope Resolver

bootstrap 手順のうち、何を canonical runbook へ昇格させるかを決める child skill とする。

## Input

- `task_summary`
- `working_files`
- `must_read_docs`

## Output

- `bootstrap_scope`
- `runbook_promotion_targets`
- `do_not_leave_only_in_log`

## Guard Rails

- shared log を bootstrap 正本の代わりにしない。
- partial recovery 手順を無制限に積み増さない。
- evidence と runbook を混同しない。

## Coordination

- `external-compute-output-keeper` と `script-doc-sync-enforcer` を補助する。
