---
name: test-and-evidence-recorder
description: task で要求された test 実行と、既存 evidence 正本への反映を同時に閉じる child skill。結果が log にしか残らない状態を避けたい時に使う。
---

# Test And Evidence Recorder

test 実行結果を既存 evidence 面へ昇格させる child skill とする。

## Input

- `required_tests`
- `required_evidence`
- `working_files`

## Output

- `test_execution_summary`
- `evidence_update_targets`
- `recorded_results`

## Guard Rails

- log だけで close しない。
- 新しい evidence file を勝手に増やさない。
- test 未実行を実行済みとして記録しない。

## Coordination

- `script-doc-sync-enforcer` と `evidence-destination-resolver` を補助する。
