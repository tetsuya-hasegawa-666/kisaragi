# decision_log

## 共有制御

- この文書は project 横断の shared decision log 正本とする。

## entries

- 2026-03-25
  - project: `shared`
  - decision: project 固有 directory 名は `prj-kisaragi_****` 形式を正本とし、`project-name` ではなく immutable な `project-code` を使う
  - rationale: project 名は将来変更され得る一方、directory、生成物、log、識別 path は変更しない code で安定化した方が全 workspace の整合を保ちやすいため
  - consequence: `prj-kisaragi_0001` と `prj-kisaragi_0002` を project directory 正本として運用し、参照先も code 基準へ更新する
- 2026-03-25
  - project: `prj-kisaragi_0002`
  - decision: `reviework_process.md` と `reviework_UX_condept.md` の内容を、外部参照ではなく `prj-kisaragi_0002` の正本文書へ吸収した
  - rationale: 再開計画が外部一時文書に依存したままだと、削除後に `MRL` / `mRL` と実装着手の根拠が失われるため
  - consequence: 以後の再開判断は `project-truth.md`、`b2t-plans-result.md`、`mrl-record.md` を正本として行う
- 2026-03-25
  - project: `shared`
  - decision: 全 project の `b2t-plans-result.md` の BDD 章で `Purpose Story` を `s1` 形式、`System Behaviors` を `b1` 形式とし、受け入れ基準と `MRL` 対応表へ `s-id` と `b-id` を必須記載とする
  - rationale: `コアストーリー`、`user stories`、`terminal behaviors` の表記ゆれを止め、BDD 計画の参照粒度を全 project で統一するため
  - consequence: 以後の `b2t-plans-result.md` は `prj-kisaragi_0002` を見本として記述し、TDD の `behavior_id` も `b1` 形式へ合わせる
- 2026-03-25
  - project: `shared`
  - decision: `MRL` 作業中は、部分 blocker があっても他に進められる task を継続し、他に何もできない状態になるまで止まらない
  - rationale: blocker 1 件で停止すると、並行して close できる `mRL`、test、文書整合の消化が遅れるため
  - consequence: 今後の `MRL` 作業は、blocker の切り分けと並行して進められる task を先に潰す
- 2026-03-25
  - project: `shared`
  - decision: `MRL`、`mRL`、TDD task の状態語は、`planned` を未着手、`active` を着手中、`pass` を `active` 後に完了した状態として扱う
  - rationale: `reviework` で契約固定済み項目を一括 `pass` 扱いしてしまい、着手中と完了済みの境界が曖昧になったため
  - consequence: 以後の closeout は、実装、検証、残作業の確認を経て `pass` を付与する
- 2026-03-25
  - project: `shared`
  - decision: project 個別の `current_state`、BDD、TDD は `b2t-plans-result.md` 1 file に統合して管理する
  - rationale: `bdd-release-compass.md`、`tdd-test-matrix.md`、project 個別 `current_state.md` の重複が強く、同期漏れが起きやすいため
  - consequence: 以後の project 計画更新は `b2t-plans-result.md` を最優先で更新し、個別 `current_state.md` は原則作らない
