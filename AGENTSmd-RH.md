# AGENTS.md 更新履歴

## 目的

- この文書は `AGENTS.md` の更新履歴正本とする。

## 記録規則

- `AGENTS.md` を更新したら、この文書へ履歴を追加する。
- 更新履歴は新しい日付を上に置く。
- 各履歴は日時、文書名、標題、背景、目的、対処方法、対応内容、更新結果、新旧比較を持つ。

## 更新履歴

### 2026-03-25 AGENTS.md project-name 対応表の No.2 更新

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: `prj-kisaragi_0002` の project-name を `prj-trajectreview` へ更新
- 背景: `project-code` は維持したまま、No.2 の project-name を現在の機能表現へ合わせて更新する指示が出た。
- 目的: immutable な `project-code` と可変な `project-name` の対応表を最新化し、関連文書と表示名の整合を保つ。
- 対処方法: `AGENTS.md` の対応表を更新し、`prj-kisaragi_0002` 配下の正本文書、README、表示名、Gradle project 名を `trajectreview` 基準へ同期した。
- 対応内容: `project-truth.md`、`b2t-plans-result.md`、`resume-startup-plan.md`、`mrl-record.md`、`README.md`、`strings.xml`、`settings.gradle.kts` などの人向け名称を更新した。
- 更新結果: `prj-kisaragi_0002` は directory 名を維持したまま、project-name と表示名を `prj-trajectreview` / `trajectreview` として扱う。
- 新旧比較:
  - 旧: No.2 は `prj-kisaragi_0002 : prj-reviework` だった。
  - 新: No.2 は `prj-kisaragi_0002 : prj-trajectreview` となり、関連表示も同期した。

### 2026-03-25 AGENTS.md 更新履歴を `AGENTSmd-RH.md` へ分離

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: 更新履歴正本の外部化
- 背景: `AGENTS.md` 本体が運用 rule と履歴を同時に抱えて肥大化し、rule の読み取り効率が落ちていた。
- 目的: 運用 rule の本文と更新履歴を分離し、`AGENTS.md` は rule、`AGENTSmd-RH.md` は履歴正本として扱えるようにする。
- 対処方法: `AGENTS.md` に `AGENTSmd-RH.md` を参照する rule を明記し、既存履歴をこの文書へ移した。
- 対応内容: `AGENTS.md` 末尾の更新履歴本文を削除し、`AGENTSmd-RH.md` 参照だけを残したうえで、既存全 entry をこの文書に統合した。
- 更新結果: 今後の `AGENTS.md` 履歴追加は、この文書に対して実施する。
- 新旧比較:
  - 旧: `AGENTS.md` 本体末尾に更新履歴本文を直接持っていた。
  - 新: `AGENTS.md` は履歴参照のみを持ち、更新履歴正本は `AGENTSmd-RH.md` に集約した。

### 2026-03-25 AGENTS.md project code を directory 正本へ適用

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: `prj-kisaragi_****` 形式の project directory 正本化
- 背景: project 名は将来変更され得るため、project 固有 directory と生成物の命名を immutable な `project-code` へ寄せたい要求が出た。
- 目的: `kisaragi/` 配下の project 固有 path と data 名を `project-code` 基準で安定化し、名称変更による参照破綻を防ぐ。
- 対処方法: `prj-<project-name>` と書いていた構造 rule を `prj-kisaragi_****` へ置換し、計画、evidence、raw artifact の path rule も code 基準へ統一した。
- 対応内容: `kisaragi-db/` 配下の project directory rule、`--exsams/` rule、計画書と evidence path rule、tree sync の確認 path を `prj-kisaragi_****` に更新した。
- 更新結果: 今後の project 固有 directory、生成物、識別 path は `project-name` ではなく `project-code` を使う。
- 新旧比較:
  - 旧: `prj-direview` や `prj-reviework` のように project 名を directory 名へ使っていた。
  - 新: `prj-kisaragi_0001`、`prj-kisaragi_0002` のように immutable な `project-code` を directory 名へ使う。

### 2026-03-25 AGENTS.md MRL 状態語の意味固定

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: `planned`、`active`、`pass` の意味固定
- 背景: `reviework` の `MRL` 更新時に、計画済み項目を一括で `pass` 扱いしてしまい、着手中と完了済みの区別が曖昧になった。
- 目的: `MRL`、`mRL`、TDD task の状態語を全 project で同じ意味で使い、過大な closeout を防ぐ。
- 対処方法: 開発計画節へ `planned`、`active`、`pass` の定義を追記した。
- 対応内容: `planned` を未着手、`active` を着手中、`pass` を `active` 後に完了した gate として固定した。
- 更新結果: 今後は `MRL` / `mRL` の進捗を、計画、着手中、完了で誤解なく管理できる。
- 新旧比較:
  - 旧: `planned` と `pass` の境界が明文化されていなかった。
  - 新: `planned`、`active`、`pass` の意味を shared rule として固定した。

### 2026-03-25 AGENTS.md resume-startup-plan の役割明確化

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: `resume-startup-plan.md` の用途固定
- 背景: `reviework` の補助計画書を残す理由が file 名だけでは伝わらず、通常計画書との違いが分かりにくかった。
- 目的: 中断後の再開時に現在地と立ち上げ順を短く掴むための補助文書であることを shared rule として明確にする。
- 対処方法: 開発計画節へ `resume-startup-plan.md` の役割を追記した。
- 対応内容: 正本を置き換えず、再開導線と初動確認項目を補助する文書として位置付けた。
- 更新結果: 今後は、補助計画を残す理由と使いどころを file 名と shared rule の両方から理解できる。
- 新旧比較:
  - 旧: 補助計画書を残す理由が文書構造上は明確でなかった。
  - 新: `resume-startup-plan.md` は再開時の現在地把握と立ち上げ順確認のための補助文書だと明示した。

### 2026-03-25 AGENTS.md B2T 統合正本への移行

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: `b2t-plans-result.md` への統合
- 背景: `bdd-release-compass.md`、`tdd-test-matrix.md`、project 個別 `current_state.md` の重複が強く、同じ project 真実を複数 file で同期する負荷が高かった。
- 目的: `current_state`、BDD、TDD を 1 つの正本へ統合し、計画と結果の同期漏れを減らす。
- 対処方法: 開発計画節と標準文書構成を `b2t-plans-result.md` 基準へ更新した。
- 対応内容: `b2t-plans-result.md` に `current_state` 章、BDD 章、TDD 章を必須化し、project 個別 `current_state.md` は原則統合管理に切り替えた。
- 更新結果: 今後は project ごとに `b2t-plans-result.md` と `mrl-record.md` を中心に運用する。
- 新旧比較:
  - 旧: `bdd-release-compass.md`、`tdd-test-matrix.md`、`prj-<project>/current_state.md` を別々に管理していた。
  - 新: `b2t-plans-result.md` 1 file に `current_state`、BDD、TDD を統合して管理する。

### 2026-03-25 AGENTS.md BDD 記法の識別子統一

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: `Purpose Story` と `System Behaviors` の識別子統一
- 背景: BDD 記法内で `コアストーリー` と `user stories`、`terminal behaviors` の呼び方が混在し、参照粒度が揺れていた。
- 目的: BDD 計画の読み方を全 project で統一し、`MRL`、受け入れ基準、TDD から同じ識別子で追えるようにする。
- 対処方法: BDD 章の必須構成を `Purpose Story`、`System Behaviors` に改め、`s-id` と `b-id` を受け入れ基準と `MRL` 対応表へ必須化した。
- 対応内容: `Purpose Story` を `s1` 形式、`System Behaviors` を `b1` 形式とし、`prj-reviework` の `b2t-plans-result.md` を記法見本に指定した。
- 更新結果: 今後の BDD 計画は、story、behavior、受け入れ基準、`MRL` を同じ識別子体系で横断参照できる。
- 新旧比較:
  - 旧: `コアストーリー`、`user stories`、`terminal behaviors` の呼称と識別子が project ごとに揺れ得た。
  - 新: `Purpose Story` は `s1`、`System Behaviors` は `b1`、受け入れ基準と `MRL` 対応表は `s-id` と `b-id` 必須で統一した。

### 2026-03-25 AGENTS.md 計画正本と MRL 参考位置付けの明確化

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: plan 正本と参考情報の役割整理
- 背景: `prj-direview` の rename と UI 修正を先行実装した後、計画正本を project ごとに先に固定し、`MRL` と `mRL` は参考情報として扱う運用を全 project 共通で固定したい要求が出た。
- 目的: BDD/TDD 計画をどの project でも先に作ること、何を残すか、`MRL` と `mRL` をどう位置付けるかを shared control file に明文化する。
- 対処方法: 開発計画節へ必須作成 rule、計画正本 role、`market_release_lines.md` と `micro_release_lines.md` の参考 role を追記した。
- 対応内容: 実装前の plan 作成義務、検証方法と小 milestone の明示、`MRL` と `mRL` の参考情報化、closeout は `mrl-record.md` へ寄せる rule を追加した。
- 更新結果: 今後は project ごとに `b2t-plans-result.md` を正本計画として残し、`MRL` / `mRL` は補助的な release-line 参照として扱う運用を共通化した。
- 新旧比較:
  - 旧: `MRL` / `mRL` と計画正本の役割分担が明文化されていなかった。
  - 新: `b2t-plans-result.md` が正本、`MRL` / `mRL` は参考、closeout は `mrl-record.md` へ集約する方針を明示した。
