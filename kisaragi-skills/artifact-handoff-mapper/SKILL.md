---
name: artifact-handoff-mapper
description: producer / consumer の artifact handoff を整理する child skill。生成物名、保存先、再解釈面、下流消費先のずれを確認したい時に使う。
---

# Artifact Handoff Mapper

artifact 契約の producer / consumer 関係を可視化する child skill とする。

## Input

- `working_files`
- `project_code`
- `must_read_docs`

## Output

- `artifact_handoff_map`
- `producer_consumer_gaps`

## Guard Rails

- file path と artifact 名を混同しない。
- runtime 上の tmp 出力を canonical artifact と誤認しない。
- manifest 面と実体面の責務を混ぜない。

## Coordination

- `runtime-structure-dependency-mapper` と `reference-rewire-operator` を補助する。
