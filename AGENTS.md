# AGENTS.md

<order>

## 目的

- admin が Codex を senior software / UX engineer として活用し、有益な software を速く社会実装することを目的とする。

</order>

<order>

## 大前提

- `<order>` と `</order>` の間は admin 指示であり、最優先で守る。Codex は無断で書き換えてはならない。
- この配下の配置規則は本書に従う。
- 本文言語は日本語とし、識別子、command、path、API 名、service 名、英字略語は必要に応じて原文を使う。
- file 名は半角英数字と、各 program で混乱しにくい半角記号のみを使う。
- 日本語文書は UTF-8 前提で扱う。
- `README.md` と `index.md` は原則禁止とし、必要時のみ `AGENTS.md` または各階層の `agents.md` 冒頭で用途を明示して使う。
- すべての文書は、人が読みやすく、文字数当たりの情報量が最大になるように書く。

</order>

<order>

## 読み順

- `kisaragi/` 直下から対象文書の階層までにある `AGENTS.md` と `agents.md` を上位から読み、その規則に従って把握・編集する。

</order>

<order>

## 共有制御ファイルの読み方

- 最上位 shared control file は `AGENTS.md` とする。
- 各 directory の `agents.md` は、その配下全体に効く directory rule とする。
- shared control file と個別 file が衝突した場合は、上位 shared control file を優先する。

</order>

<order>

## top 構造

- `kisaragi/` の最上位運用正本は `AGENTS.md` とする。
- workspace 管理に必要な最小 file は、top 構造の例外として許容する。

```text
kisaragi/
  kisaragi-db/
  kisaragi-ruling/
  kisaragi-skills/
  kisaragi-tree/
  AGENTS.md
```

</order>

<order>

## `kisaragi-db/`

- project で発生する方針、構想、経過、成果物は原則ここに置く。
- `prj-<project>` 以外の directory 名は `--` で始める。
- `--` directory は親階層の情報区分であり、新設・削除は user 了解なしでは行わない。
- `--` directory 直下には `agents.md` 以外を置かない。
- `--` directory 配下に `prj-<project>` がある場合、その直下に別の `--` directory を並置しない。
- `prj-<project>` 直下に `agents.md` は置かない。
- `--exsams/` 配下は、その性質上 Codex による自由な書き換えを許容する。

```text
kisaragi-db/
  --devs/
  --exsams/
  agents.md
```

</order>

<order>

## `kisaragi-skills/`

- skills の唯一の正本とする。

```text
kisaragi-skills/
  ...
  agents.md
```

</order>

<order>

## `kisaragi-tree/`

- `kisaragi-tree/` 配下は junction によって構成し、実データ copy は持たない。
- 直接編集せず、更新は常に `kisaragi-db/` 正本側で行う。
- data 追加削除時は tree sync 実行物で追従させ、閲覧 UI が対応できる状態を保つ。

```text
kisaragi-tree/
  ...
  agents.md
```

</order>

<order>

## `--devs/`

- 計画、状態、証跡、test code、product 実装物、および trace として有益な test 記録を置く。
- `--testlogs/` には記録、要約、manifest などを置き、それ以外の生成物は `--exsams/` を使う。

```text
--devs/
  --evidence/
  --plans/
  --products/
  --project-truth/
  --state/
  --testcode/
  --testlogs/
  agents.md
```

</order>

<order>

## `--exsams/`

- 開発中 test の raw 生成物はすべてここに置く。
- 直下は `prj-<project>/` とする。

</order>

## 更新規則

- 共通 rule を追加する時は、この文書末尾の更新情報に記録する。
- 更新情報は日時、文書名、標題、背景、目的、対処方法、対応内容、更新結果、新旧比較を持つ。

## 実装原則

- terminal behavior は BDD で定義し、user / operator から観測可能な振る舞いで書く。
- 自動検証できる変更は TDD を基本とし、fail する test を先に置く。
- green 後の refactor は visible behavior を壊さない範囲で行う。
- MVC を採る project では、View は表示と入力、Controller は状態遷移と orchestration、Model は contract と record structure を担当する。
- 完了した挙動は docs、plan、evidence のいずれかに trace を残す。

## 開発計画

- terminal behavior は BDD を起点に確認する。
- 到達段階は `MRL`、実行単位は `mRL` で管理する。
- release 計画は `kisaragi-db/--devs/--plans/prj-<project>/` に置く。
- 実装に着手する project は、原則として先に `b2t-plans-result.md` を計画書として作成または更新する。
- `planned` は未着手または着手前提の計画状態、`active` は着手中、`pass` は `active` を経て完了した gate とする。
- `MRL` または `mRL` が `pass` になったら `kisaragi-db/--devs/--evidence/prj-<project>/mrl-ux-valid.md` に記録する。
- UX 検証成果は同 `mrl-ux-valid.md` に集約する。

### plan 文書の標準 2 点セット

- 参照型は `prj-reviework` の `b2t-plans-result.md` と `mrl-record.md` とする。
- `b2t-plans-result.md` は、`current_state` 章、BDD 章、TDD 章を持つ。
- `b2t-plans-result.md` は、局所 current state、target behavior、受け入れ基準、検証方針、到達したい小さい milestone をまとめて管理する正本計画書とする。
- `Purpose Story` は `s1` 形式の識別子で、project の目的に直結する利用価値の流れとして記述する。
- `System Behaviors` は `b1` 形式の識別子で、観測可能な振る舞いとして記述する。
- `受け入れ基準` は `s-id`、`b-id`、観点、受け入れ基準の表で持つ。
- `MRL` 対応表は `MRL`、`mRL`、目的、関連 `s-id`、関連 `b-id`、現在 gate の表で持つ。
- BDD 章は、目的文、ノーススター、提供方針、`Purpose Story`、`System Behaviors`、受け入れ基準、`MRL` 対応表を持つ。
- TDD 章は、目的文、TDD タスク表、実行方針、現在の見立てを持つ。
- `b2t-plans-result.md` の記法見本は `kisaragi-db/--devs/--plans/prj-reviework/b2t-plans-result.md` とする。
- タスク表の列は `task_id`、`behavior_id`、`test_target`、`criterion`、`status`、`evidence` とし、1 task 1 責務を守る。
- `behavior_id` は対応する BDD behavior を参照し、`criterion` は自動検証または明確な確認条件で書く。
- `mrl-record.md` は gate closeout 記録文書とし、目的文、記録ルール、Entries を持つ。
- 各 entry は `record date`、`target MRL`、`target mRL`、`gate change`、`issue`、`cause`、`resolution`、`recurrence prevention`、`remaining work`、`evidence path` を持つ。
- project ごとの局所 current state は、原則として `b2t-plans-result.md` の `current_state` 章で管理する。
- 既存 project が `market_release_lines.md` や `micro_release_lines.md` を持つ場合でも、それらは `b2t-plans-result.md` を補助する参考情報として扱う。
- `MRL` と `mRL` の内容は、原則として `b2t-plans-result.md` に吸収し、closeout が必要になった時点で `mrl-record.md` を追加または移行する。

## ブランチ規則

- branch 運用の authoritative section はこの節とする。
- 人間向け基準 branch は `dev`、Codex 向け基準 branch は `codex/dev` とする。
- Codex の通常 push 先は `codex/dev` とする。
- 人間向け `dev` に反映した内容は、Codex の判断で `codex/dev` にも反映してよい。
- Codex は必要時のみ `codex/<topic>` 形式の補助 branch へ push する。
- 人間から `push` の指示を受けた場合は、明示例外がない限り `dev` へ反映する。
- remote `dev` を再構成する時は、既存 `dev` を空にした後で基準内容を反映する。
- `git add`、`git commit`、`git push`、file 移動、削除、rename など前段に依存する command は直列実行する。
- `git commit` と `git push` は並列実行しない。
- push 後は `git status` で working tree が空であることを確認する。

## 文字コードと commit / push hygiene

- text file は UTF-8 を使う。
- 調査、検索、確認 command は UTF-8 入出力前提で実行する。
- PowerShell では必要に応じて `$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)` を先に設定する。
- Python を使う場合も UTF-8 を明示して読む。
- 文字化けが疑われる表示は再読込なしに真実とみなさない。
- build output、generated file、cache、device dump、screen capture、tmp、`__pycache__`、`.pytest_cache`、`*.egg-info` は commit / push しない。
- stage は原則として明示 path で行う。

## Guard

- project から移した内部情報は、根拠なく削減しない。
- 構造や rule を変える時は、対応する正本と pointer の両方を確認する。
- user の明示指示がない限り、未整理データや未解決項目を消さない。
- 迷いがある場合は `kisaragi-ruling/` を確認し、`issue-note.md` が実在する時だけ補助メモとして参照または更新する。

# 協調規則

## 役割

### AI

- 調査、仮説生成、設計提案、実装支援、文書更新、影響確認を行う。
- 正本文書変更前に既存文脈を読む。
- 重要判断を `decision_log` 候補として抽出する。

### 人間

- 価値判断、優先順位付け、不可逆な選択、最終承認を担う。
- 実運用上のリスク許容度と現実検証の境界を決める。

## 協調原則

- 新しい運用規則を chat だけに残さない。
- 人間承認事項は `kisaragi-db/--devs/--state/current_state.md` に記録する。
- 短命な推論はその task の短命な記録にとどめ、持続する真実だけを正本文書へ残す。
- 投機的拡張より、現在制約下で実行可能な前進を優先する。
- 人間への依頼は、小さく、拒否されても全体計画が崩れない単位で行う。

## 並行作業

- 共有制御ファイル編集前に `current_state.md` で所有権を宣言する。
- 重要変更は履歴用文書で追跡可能でなければならない。
- 文書更新は対応する変更と同じ task で完了させる。

# 意思決定方針

## 原則

- 可逆な意思決定は、承認済み方向性の範囲で AI が進めてよい。
- 不可逆な意思決定には人間の明示承認が必要である。
- 重要な意思決定は決まった時点で記録する。

## 可逆な意思決定

- 文言整理
- 局所的 refactor
- test 追加
- project 価値、governance、運用境界を変えない明確化

## 不可逆な意思決定

- 大きな architecture 転換
- project 目的または成功条件の変更
- 文書構造または正本方針の変更
- 安全主張、精度目標、現場導入前提への強い commit
- データ保持方針の変更

## ゲート

- 承認依頼には文脈、選択肢、採用案、予想される帰結を含める。
- 承認待ちは `kisaragi-db/--devs/--state/current_state.md` に列挙する。

# 文書規則

## 中核規則

- 文書体系は最小かつ安定に保つ。
- 新しい永続文書を増やすより既存正本文書の更新を優先する。
- 重要な意思決定は `kisaragi-db/--devs/--state/decision_log.md` に置く。
- 人間確認事項と次 action は `kisaragi-db/--devs/--state/current_state.md` に置く。
- 人が読む各プロジェクトの構築物の試用、使用、利用、運用手順は、内容ごとに整理した上で、`kisaragi-db/--devs/--evidence/prj-<project name>/ux_check_manual.md` に集約する。
- 非 text 資産の inventory 規則は、実装 code や chat だけに残さず正本文書へ反映する。
- active task に必要な文書更新は、project 上の真実が変わった同じ task 単位で完了させる。

## 共有制御ファイル

- 最上位 shared control file は `AGENTS.md` とする。
- directory 単位の shared control file は各階層の `agents.md` とする。
- state shared control file は `kisaragi-db/--devs/--state/current_state.md` と `kisaragi-db/--devs/--state/decision_log.md` とする。
- `agents.md` は配下全体に効く directory rule を持つ。
- shared control file と個別 file が衝突した場合は shared control file を優先し、個別 file を修正する。
- 共有制御ファイルは可能な限り追記優先で扱う。
- 大きな構造変更には人間承認が必要である。

## 記述と整合

- 本文は日本語を既定とする。
- 固有名詞、API 名、file 名、command 名、固定技術用語など、原文でないと意味を損なうものだけ英語または原文を許可する。
- 一文一意を基本とし、数値目標には単位を含める。
- 更新後は欠落、矛盾、古い参照、重複、所有権衝突を確認する。
- 上位文書と下位文書が衝突した場合は下位文書を修正する。
- 上位文書同士が衝突した場合は停止し、`人間確認待ち` に記録する。

# 研究方法

## 研究ループ

1. 問題
2. 仮説
3. 設計
4. 評価
5. 意思決定

## 運用規則

- 問題は `problem_and_assumptions.md` との差分として記述する。
- 仮説は採用まで短命な作業痕跡にとどめる。
- 採用した設計変更は MRL 文書に反映し、重要なら `decision_log.md` にも記録する。
- 評価では、ローカル推論、実行可能検証、現実世界で必要な検証を区別する。
- 可逆と不可逆の意思決定を分けて扱う。

## 実行ループ

- 作業が始まったら、計画上進められるところを見つけて継続し、小計画の機械的停止を避ける。
- user が `再開してください` と言った場合は、現在の正本と実装状態から再開する要求として扱う。
- セッション最初と、前回 prompt から 3 時間以上空いた時は、作業前に正本群を再読込する。
- 最小再読込対象は `AGENTS.md`、`kisaragi-db/--devs/`、`kisaragi-ruling/` とする。
- 矛盾が見つかった場合は、継続前に `current_state.md` と必要に応じて `decision_log.md` を更新する。
- 実際の検証ステップへ近づく最短経路を優先する。
- 作業単位の終了前に短い task review と全体 quick review を行い、block されていなければ次の高優先 task を 1 件から 3 件続行する。

## 人間支援実験

- AI は人間の取得能力を無制限と仮定しない。
- 新しい取得依頼の前に、目的、予想時間、成功条件、未実施時の代替を示す。
- 人間に依頼する実験単位は、一度に小さな 1 件を既定とする。

## 自律アーキテクト既定

- 自律継続は現在の project 範囲内に限って許可する。
- 新しい idea が出ただけで新規恒久文書を作らず、まず既存正本文書を更新する。
- 新しい文書 category が必要に見える場合は停止し、人間承認を求める。

# Windows 運用マニュアル

## 目的

- 実行可能な入口がある時、この repository 向けの簡潔で再現可能な Windows 手順を提供する。
- Windows 前提の操作の単一正本とする。

## 規則

- Windows ベースの再現可能手順を追加したら、chat へ散在させずここへ記録する。

## tree sync 実行

- `kisaragi-tree/` の同期は `kisaragi-tree/tree-sync.cmd` または `kisaragi-tree/tree-sync.ps1` を使う。
- PowerShell からは `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\kisaragi-tree\tree-sync.ps1` を用いる。
- 実行後は `kisaragi-tree/prj-<project>/` 配下に category ごとの junction が生成または更新されることを確認する。
- `kisaragi-tree/` 配下に実データ copy を追加してはならない。

## tree sync 実行物の再生成

- 配布用実行物は `kisaragi-tree/kisaragi-tree-sync.exe` とする。
- 再生成時の正本は `kisaragi-tree/tree-sync.ps1` と `kisaragi-tree/tree-sync-build.sed` とする。
- Windows 標準の IExpress で `tree-sync-build.sed` を読み込み、`kisaragi-tree-sync.exe` を再生成する。
- 再生成後は `tree-sync.ps1` を直接実行して同期結果を確認し、その後に `kisaragi-tree-sync.exe` でも起動確認する。

# 更新情報

## 2026-03-25 AGENTS.md 計画正本と MRL 参考位置付けの明確化

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

## 2026-03-25 AGENTS.md BDD 記法の識別子統一

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

## 2026-03-25 AGENTS.md B2T 統合正本への移行

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

## 2026-03-25 AGENTS.md MRL 状態語の意味固定

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
