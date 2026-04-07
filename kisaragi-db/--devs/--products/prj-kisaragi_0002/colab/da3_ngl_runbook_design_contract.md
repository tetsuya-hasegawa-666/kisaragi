# da3_ngl_runbook design contract

この文書は `da3_ngl_runbook.md` / `da3_ngl_runbook.ipynb` を source 正本から再構築する時の authoring 契約とする。

## 目的

- `da3_runbook_sources/` を canonical source とし、notebook 上の code cell と markdown cell の両方を管理対象にする。
- 各 markdown cell は対応する `#No`、その直前の `#No`、その直後の `#No` を先頭に持ち、複数 pattern は `#9-1..#9-5` のような最短表現で示す。
- `#6 Shared Helpers` を camera trajectory / pose / intrinsics / anchor basis の唯一の共通契約面とし、`#7`、`#9`、`#14` が同じ参照面で動くようにする。

## source 正本

| item | path | role |
| --- | --- | --- |
| code manifest | `da3_runbook_sources/cell_manifest.json` | code cell token と source file の対応 |
| markdown manifest | `da3_runbook_sources/markdown_manifest.json` | markdown cell の順序、対応 token、前後参照 |
| code source | `da3_runbook_sources/cells/*.py` | 各 code cell の正本 |
| markdown source | `da3_runbook_sources/markdown/*.md` | 各 markdown cell の正本 |
| sync utility | `da3_runbook_sources/sync_da3_runbook_sources.py` | source 正本から pair を再構築する |
| inventory utility | `da3_runbook_sources/build_inventory.py` | code / markdown inventory を生成する |

## markdown cell rule

- markdown source file は先頭 3 行を必須とする。
- 1 行目は `#No: ...`
- 2 行目は `前: ...`
- 3 行目は `次: ...`
- 複数連番は `#4-1..#4-2` のように最短表現で書く。
- markdown 本文は、その直後の code cell 群の実働内容と出力契約に合わせる。

## 再構築 rule

- `sync_da3_runbook_sources.py` は markdown cell と code cell を source 正本から順に組み立て、`.md` と `.ipynb` を同時更新する。
- notebook companion を直接編集した時は、その内容を `da3_runbook_sources/` 側へ戻すか、再度 source 正本に寄せて同期し直す。
- inventory 更新時は `build_inventory.py` を再実行し、`da3_ngl_runbook_source_inventory.md` を同じ task で更新する。
