# decision_log

## 共有制御

- この文書は project 横断の shared decision log 正本とする。

## entries

- 2026-03-25
  - project: `prj-reviework`
  - decision: `reviework_process.md` と `reviework_UX_condept.md` の内容を、外部参照ではなく `prj-reviework` の正本文書へ吸収した
  - rationale: 再開計画が外部一時文書に依存したままだと、削除後に `MRL` / `mRL` と実装着手の根拠が失われるため
  - consequence: 以後の再開判断は `project-truth.md`、`bdd-release-compass.md`、`tdd-test-matrix.md`、`mrl-record.md` を正本として行う
- 2026-03-25
  - project: `shared`
  - decision: 全 project の `bdd-release-compass.md` で `Purpose Story` を `s1` 形式、`System Behaviors` を `b1` 形式とし、受け入れ基準と `MRL` 対応表へ `s-id` と `b-id` を必須記載とする
  - rationale: `コアストーリー`、`user stories`、`terminal behaviors` の表記ゆれを止め、BDD 計画の参照粒度を全 project で統一するため
  - consequence: 以後の `bdd-release-compass.md` は `prj-reviework` を見本として記述し、TDD の `behavior_id` も `b1` 形式へ合わせる
- 2026-03-25
  - project: `shared`
  - decision: `MRL` 作業中は、部分 blocker があっても他に進められる task を継続し、他に何もできない状態になるまで止まらない
  - rationale: blocker 1 件で停止すると、並行して close できる `mRL`、test、文書整合の消化が遅れるため
  - consequence: 今後の `MRL` 作業は、blocker の切り分けと並行して進められる task を先に潰す
