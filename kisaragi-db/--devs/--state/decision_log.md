# decision_log

## 共有制御

- この文書は project 横断の shared decision だけを保持する。
- project 固有の decision は、各 project の正本計画書または truth に吸収する。`prj-kisaragi_0002` は [b2t-plans-result.md](/Users/tetsuya/kisaragi/kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/b2t-plans-result.md) と [project-truth.md](/Users/tetsuya/kisaragi/kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/project-truth.md) を正本とする。

## entries

- 2026-03-28
  - project: `shared`
  - decision: `--tgpce-map/` は承認済み project の `truth`、`goal`、`plan`、`current`、`evidence-map` を集約する統合文書置き場とする
  - rationale: project 固有の truth、plan、evidence、current が category ごとに分散すると、再開時の把握と文書境界の理解に余計な往復が発生するため
  - consequence: `prj-kisaragi_0002` を pilot とし、project 固有文書は `--tgpce-map/prj-kisaragi_0002/` に集約する
- 2026-03-28
  - project: `shared`
  - decision: shared `current_state.md` と `decision_log.md` は project 固有記録を恒常的に保持しない
  - rationale: project 固有記録を shared state に置くと、`b2t` と二重管理になり、current と decision の責務境界が崩れるため
  - consequence: `prj-kisaragi_0002` の current / decision は `b2t-plans-result.md` と `project-truth.md` に吸収し、shared state は横断事項だけに圧縮する
