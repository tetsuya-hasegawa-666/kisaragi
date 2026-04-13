---
name: path-contract-scanner
description: code と文書に現れる path read / write 契約を棚卸しする child skill。canonical path、legacy alias、read/write 境界を確認したい時に使う。
---

# Path Contract Scanner

path 契約を read / write / alias / final output の観点で整理する child skill とする。

## Input

- `working_files`
- `project_code`
- `must_read_docs`

## Output

- `path_contracts`
- `path_aliases`
- `path_risks`

## Guard Rails

- 参照 path と生成 path を混同しない。
- legacy alias を canonical path と取り違えない。
- 外部 compute の一時 path を永続 path と誤認しない。

## Coordination

- `runtime-structure-dependency-mapper` と `external-compute-output-keeper` を補助する。
