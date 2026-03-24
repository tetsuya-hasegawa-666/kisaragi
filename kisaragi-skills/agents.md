# agents.md

## kisaragi-skills の構成

- この directory は skill 集約層とする。
- skill 実体は skill 名 directory ごとに独立して配置するものとする。
- 同名 skill は 1 つだけを正本として置くものとする。
- 役割が近い skill がある場合は、kisaragi-skills の中の agents.md で境界を明示するものとする。


## 収録 skill

- `bdd-story-builder`
- `branch-sync-operator`
- `doc-governor`
- `docker-stability-operator`
- `document-topology-keeper`
- `documentation-watchkeeper`
- `encoding-integrity-keeper`
- `fastapi`
- `frontier-research-curator`
- `release-line-gatekeeper`
- `session-handover-writer`
- `tdd-testflow-manager`


## 役割境界

- `document-topology-keeper` は文書 topology、authoritative / pointer、重複削減を扱うものとする。
- `doc-governor` は versioned spec set の current / archive 整合を扱うものとする。
- `documentation-watchkeeper` は会話や実装変更による docs drift の検知と同一 turn での追従を扱うものとする。
- `encoding-integrity-keeper` は text / markdown の encoding 健全性だけを扱うものとする。