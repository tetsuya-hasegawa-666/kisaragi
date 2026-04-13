---
name: drive-input-bootstrap-checker
description: external compute task で Drive mount から input 解決までの bootstrap を確認する child skill。Drive 入力候補の発見、選択、handoff 契約を固定したい時に使う。
---

# Drive Input Bootstrap Checker

`Drive mount -> input 解決` を固定して外部 compute の初動を安定化する child skill とする。

## Input

- `task_summary`
- `project_code`
- `must_read_docs`

## Output

- `drive_mount_requirements`
- `input_resolution_steps`
- `selected_input_contract`

## Guard Rails

- Drive mount 前提を黙って飛ばさない。
- hardcode path を canonical route とみなさない。
- input 発見と input 採用を混同しない。

## Coordination

- `external-compute-output-keeper` を補助する。
