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
  - rationale: `trajectreview` で契約固定済み項目を一括 `pass` 扱いしてしまい、着手中と完了済みの境界が曖昧になったため
  - consequence: 以後の closeout は、実装、検証、残作業の確認を経て `pass` を付与する
- 2026-03-25
  - project: `shared`
  - decision: project 個別の `current_state`、BDD、TDD は `b2t-plans-result.md` 1 file に統合して管理する
  - rationale: `bdd-release-compass.md`、`tdd-test-matrix.md`、project 個別 `current_state.md` の重複が強く、同期漏れが起きやすいため
  - consequence: 以後の project 計画更新は `b2t-plans-result.md` を最優先で更新し、個別 `current_state.md` は原則作らない
- 2026-03-25
  - project: `prj-kisaragi_0002`
  - decision: `trajectreview` は UI mock のまま止めず、`iSensorium` session folder 抽出を app 内へ統合して `MRL-5` として closeout する
  - rationale: `InputPackaging` は既存 parser 契約だけでは実利用に届かず、現場では app から raw と派生出力を取得できることが再開優先事項になったため
  - consequence: `MRL-5` では legacy alias intake、`isensorium/` と `trajectreview/` の bundle 分離、quality 数値表示付き UI を実装対象に追加する
- 2026-03-25
  - project: `prj-kisaragi_0002`
  - decision: `iSensorium` の `Xperia 5 III` 収録仕様は `sandbox` 参照のままにせず、`project-truth/isensorium_xperia5iii_intake_spec.md` に吸収する
  - rationale: `trajectreview` の intake 条件が外部 workspace 依存のままだと、再開時に必要権限、recording mode、時刻整列、sample count の基準が失われるため
  - consequence: 以後の `InputPackaging` 判断は `prj-kisaragi_0002` 配下の正本だけで追跡でき、`Xperia 5 III` の準備条件も `sandbox` を開かずに確認できる
- 2026-03-25
  - project: `prj-kisaragi_0002`
  - decision: `iSensorium` 本体一式の参照実体は `project-truth` へ直置きせず、verified mirror として `--products` / `--testcode` に保持し、`project-truth` から pointer する
  - rationale: `project-truth` は恒久 truth と参照規則の正本であり、source code 一式を直置きすると役割が混濁する一方、実装追跡には code mirror 自体が必要だったため
  - consequence: 以後 `iSensorium` 参照本体は mirror path を使い、truth 側では役割、参照先、確認結果だけを正本として維持する
- 2026-03-25
  - project: `prj-kisaragi_0002`
  - decision: `kisaragi` 側 mirror は比較用 app として `applicationId = com.kisaragi.isensorium`、表示名 `kisaragi-iSensorium` で install する
  - rationale: 本来の `iSensorium` を端末から消さずに、同じ `Xperia 5 III` 上で挙動比較したい要求があるため
  - consequence: 以後の比較検証は source app と `kisaragi-iSensorium` を同居させて実施できる
- 2026-03-25
  - project: `prj-kisaragi_0002`
  - decision: `MRL-6` では `InputPackaging` の抽象 `SessionPackage` を concrete artifact の `session_package.json` と `space_handoff_manifest.json` へ落とし、`video.mp4` を raw bundle に保持する
  - rationale: 抽出後の bundle を後段へ渡すには、主カメラ動画と stage-2 gate を同じ export 単位へ含める必要があるため
  - consequence: `SpaceReconstruction` は `trajectreview/` 配下の handoff artifact だけで着手可否を判定できる
