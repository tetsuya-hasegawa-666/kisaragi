# AGENTS.md

<order>

## 大前提

- 文章の行に<order>と</order>が配置されている場合、その間にある文章は、adminによる指示です。この内容は最優先で事項なので必ず守りなさい。また、この領域の内容はcodexによる書き換えは禁止とします。書き換えが必要な場合はユーザーの了解を必ず得てください。

- このシステムを使う目的は、機械設計者から転身したソフトウェアエンジニアであるadminが、codexという非常に優れたシニアソフトウェア＆UXエンジニアをパートナーとして、人にとって有益なソフトウェアをいち早く開発し社会実装することを目的としている。

- このシステムを運用する人（指示者、命令者）のことで、"admin"と表現します。
- すべての文書は、人が読みやすい構成および文章構造であること。
- すべての文書は、文字数当たりの情報量が最大になる構成及び文章構造であること。
- 次のアクションの提案がある場合は、箇条書きで50字以内のこと。

- この配下の文書やデータの配置ルールは、この文書の案内に必ず従うこととする。
- 識別子、command、path、API 名、service 名、英字略語は必要に応じてそのまま使うものとする。
- 全ての文書における記録用途および人やAIプロンプト向けの説明に用いる言語は日本語とすること。
- ただし、ファイル名は半角英数字に加え、各プログラムで混乱が起きにくい半角記号のみとすること。
- 文字化けを避けるため 日本語文書を取り扱うときは、UTF-8 に適した入力方法および出力方法を必ず用いること。
- 語彙は、日本人のソフトウェアエンジニアが日本語で専門会話するときの水準にそろえるものとする。

- 一般的に使われる `README.md` や `index.md` は利用は禁止。どうしても必要な場合は、トップディレクトリの`AGENTS.md`か、その配下にある各ディレクトリの`agents.md`の冒頭に説明を付加して運用すること。


## 読み順（入口）

- 読み順は、 kisaragi/ 直下を基準として、取り扱う文書の階層までにある、すべての1.`AGENTS.md`、2.`agents.md`を把握して、それらのルールに従って、該当文書の把握・編集を行うこと。

## 共有制御ファイルの読み方

- 最上位 shared control file は AGENTS.md とする。
- 各 directory の agents.md は、その配下全体に効く directory rule とする。
- shared control file と個別 file が衝突した場合は、上位 shared control file を優先する。

## kisaragi/ ディレクトリ構造と役割

- `kisaragi/`の最上位運用正本である、AGENTS.mdが保管される
- workspace 管理に必要な最小ファイルの追加に限って、<order>記載規則の例外として許容する。
- 最上位のディレクトリ
- kisaragi/のディレクトリ構造は下記

```text
kisaragi/
  kisaragi-db/
  kisaragi-ruling/
  kisaragi-skills/
  kisaragi-tree/
  AGENTS.md

```


## kisaragi-db/ ディレクトリ構造と役割

- プロジェクトの方針、構想、経過、成果物などプロジェクトで発生するデータはすべてこのディレクトリの中に保管すること。
- 配下のディレクトリは、prj-<project名> （接頭にprj-がある）ディレクトリ以外は、接頭に"--"を持つ。
- 接頭に"--"を持つディレクトリは、その親のディレクトリで取り扱う情報を細分化した1要素である。
- 接頭に"--"を持つディレクトリの新規作成や削除については、ユーザーの了解がない限り禁止とする。（ユーザーは柔軟に対応するので、追加や削除の提案はしてください）
- 接頭に"--"を持つディレクトリ直下には、agents.md を置いてもよく、かつagents.md以外のファイルを置くことを禁止する。
- 接頭に"--"を持つディレクトリ内に prj-<project名> （接頭にprj-がある）のディレクトリがある場合、そのディレクトリと並列に、接頭に"--"を持つディレクトリが存在してはいけない。
- prj-<project名> （接頭にprj-がある） の直下には、agents.md を置くのは禁止する。
- ただし、--exsams/配下については、その性質上、codexによる自由な書き換えを許容する。

- kisaragi-db/のディレクトリ構造は下記
```text
kisaragi-db/
  --devs/
  --exsams/
  agents.md

```


## kisaragi-skills/ ディレクトリ構造と役割

- kisaragi/全体で利用するskillsを集合管理する。
- ディレクトリ構造は下記
```text
kisaragi-skills/
  ...
  agents.md

```


## kisaragi-tree/ ディレクトリ構造と役割

- `kisaragi-tree/` 配下は junction によって構成し、実データの copy は持たないものとする。
- `kisaragi-tree/` で直接編集せず、更新は常に `kisaragi-db/` の正本側で行うものとする。
- `kisaragi-tree/` は ディレクトリにデータが追加削除されるたびに、自動更新されるように tree sync 実行物を更新して、閲覧UIが対応すること。
- `sandbox/kisaragi-tree/` は `kisaragi-db/` の正本を project 単位で見やすく束ねる tree layer とする。

```text
kisaragi-tree/
  ...
  agents.md

```


## --devs/ ディレクトリ構造と役割

- `--devs` は、計画、状態、証跡、test 出力、test code、product 実装物および証跡を置くこと。
- testlogsには、トレースとして有益な、記録、要約などの情報やmanifest等のみを配置し、それ以外は--exsamsを利用すること。

- --devs/のディレクトリ構造は下記
```text
--devs
  --evidence/
  --plans/
  --products/
  --project-truth/
  --state/
  --testcode/
  --testlogs/
  agents.md

```


## --exsams/ ディレクトリ構造と役割

- --exsams は、開発中のテストによる生成物はすべてここに置くこと。
- ディレクトリの内部は、prj-<project名> ディレクトリが配置され、その中に各プロジェクトからの生成物を置くこと。
- --exsams/配下については、その性質上、codexによる自由な書き換えを許容する。
</order>


## 更新規則・同期規則

- 共通 rule を追加する場合は、まずこの文書の末尾に更新情報を記載する。
- 更新情報は、日時、文書名、と変更内容がわかる標題をつけ、背景・目的・対処方法・対応内容・更新結果と、新旧の文書を表で記録。

## 実装原則

- terminal behavior は BDD で定義し、user や operator から見える振る舞いで記述するものとする。
- 自動検証できる変更は TDD を基本とし、fail する test を先に置いてから実装するものとする。
- green 後の refactor は、既存の visible behavior を壊さない範囲で行うものとする。
- MVC を採る project では、View は表示と入力、Controller は状態遷移と orchestration、Model は contract と record structure を担当するものとする。
- 完了した挙動は、必ず docs、plan、evidence のいずれかに trace を残すものとする。

## 開発計画の立案 規則

- terminal behavior は BDD を起点に確認するものとする。
- 到達段階は `MRL`、実行単位は `mRL` で管理するものとする。
- release 計画は `--devs/--plans/prj-<project>/` に置くものとする。
- `MRL` または `mRL` が `pass` になったら、`--devs/--evidence/prj-<project>/` 内の`mrl-ux-valid.md` に記録するものとする。
- UX 検証成果は `--devs/--evidence/prj-<project>/`内の`mrl-ux-valid.md` に集約するものとする。

### plan 文書の標準 3 点セット

- `prj-remote-pwsh` の `bdd-release-compass.md`、`tdd-test-matrix.md`、`mrl-record.md` を、`--devs/--plans/prj-<project>/` に置く release planning 文書の参照型とする。
- `bdd-release-compass.md` は、少なくとも「文書の目的文」「ノーススター」「提供方針」「コアストーリー」「terminal behaviors」「受け入れ基準」「MRL 対応表」を持つものとする。
- `bdd-release-compass.md` の `terminal behaviors` は `B1` 形式の識別子を持ち、user または operator から観測可能な振る舞いとして記述するものとする。
- `bdd-release-compass.md` の `受け入れ基準` は、各 behavior に対して観点と判定可能な基準を表で持つものとする。
- `tdd-test-matrix.md` は、少なくとも「文書の目的文」「TDD タスク表」「実行方針」「現在の見立て」を持つものとする。
- `tdd-test-matrix.md` のタスク表は `task_id`、`behavior_id`、`test_target`、`criterion`、`status`、`evidence` を列として持ち、1 task 1 責務を守るものとする。
- `tdd-test-matrix.md` の `behavior_id` は対応する `bdd-release-compass.md` の `terminal behavior` を参照し、`criterion` は自動検証または明確な確認条件として書くものとする。
- `mrl-record.md` は、gate closeout の記録を集約する文書とし、「文書の目的文」「記録ルール」「Entries」を持つものとする。
- `mrl-record.md` の各 entry は、少なくとも `record date`、`target MRL`、`target mRL`、`gate change`、`issue`、`cause`、`resolution`、`recurrence prevention`、`remaining work`、`evidence path` を持つものとする。
- 既存 project が `market_release_lines.md` や `micro_release_lines.md` を持つ場合でも、BDD と TDD の正本対応は上記 2 文書で管理し、closeout 記録が必要になった時点で `mrl-record.md` を追加または移行するものとする。

## Git Branch Rule

- branch 運用の authoritative section は `ブランチ規則` とする。
- この節は `ブランチ規則` の参照とし、重複する branch / push 本文は持たないものとする。

## 文字コードと調査 command

- 調査、棚卸し、検索、内容確認に使う command は、UTF-8 入出力を前提に実行するものとする。
- PowerShell では、必要に応じて `$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)` を先に設定するものとする。
- Python を使って文書調査を行う場合も、UTF-8 を明示して file を読むものとする。
- 文字化けが疑われる出力は、そのまま判断せず UTF-8 前提で再取得するものとする。

## commit and push hygiene

- build output、generated file、cache、device dump、screen capture、tmp、`__pycache__`、`.pytest_cache`、`*.egg-info` などの生成物は commit / push しないものとする。
- stage は原則として明示 path で行い、生成物の誤 stage を避けるものとする。

## Guard

- project から移した内部情報は、根拠なく削減しないものとする。
- 構造や rule を変えるときは、対応する正本と pointer の両方を確認するものとする。
- user の明示指示がない限り、未整理データや未解決項目を消さないものとする。
- 迷いがある場合は `kisaragi-ruling/` を確認し、`issue-note.md` が実在する時だけ補助メモとして参照または更新すること。

# 協調規則

## 役割
### AI
- 調査、仮説生成、設計提案、実装支援、文書更新、影響確認を行う。
- 正本文書を変更する前に、既存文脈を読む。
- 意思決定ログへ昇格すべき重要判断を抽出する。

### 人間
- 価値判断、優先順位付け、不可逆な選択、最終承認を担う。
- 実運用上のリスク許容度と現実検証の境界を決める。

## 協調規則
- AI は新しい運用規則をチャットだけに残してはならない。
- 人間承認事項は `kisaragi-db/--devs/--state/current_state.md` に記録する。
- 短命な推論はオブザーバビリティ層に置き、持続する真実はアーティファクト層またはプロセス層へ置く。
- AI は投機的拡張よりも、現在制約下で実行可能な前進を優先する。
- AI は人間の実験負荷を、常時使える大量リソースではなく、限られた相談対象として扱う。
- 人間へ取得や手動検証を依頼する時は、受諾または拒否しても全体計画が崩れない程度に小さく保つ。

## 並行作業規則
- 各インスタンスは、共有制御ファイルを編集する前に `current_state.md` で所有権を宣言する。
- 重要変更は 履歴用文書のいずれかによって追跡できなければならない。
- 文書更新は、対応する変更と同じタスクの中で完了させる。
- 共有制御ファイルの階層は、最上位を `AGENTS.md`、directory 単位を各階層の `agents.md`、state 共有を `kisaragi-db/--devs/--state/decision_log.md` と `kisaragi-db/--devs/--state/current_state.md` とする。

## ブランチ規則
- 人間向け基準ブランチは `dev`とする。
- Codex 向け基準ブランチは `codex/dev`とする。
- Codex の通常 push 先は `codex/dev` とする。
- 人間向け `dev` へ反映した内容は、Codex の判断で `codex/dev` にも反映してよい。
- Codex は必要時のみ `codex/<topic>` 形式の補助ブランチへ push する。
- 人間から `push` の指示を受けた場合は、明示例外がない限り `dev` へ反映する。
- remote `dev` は人間向け基準 branch として維持し、再構成時は既存 `dev` を空にした後で基準内容を反映する。
- `git add`、`git commit`、`git push`、file 移動、削除、rename など、前段の結果に依存する command は必ず直列に実行するものとする。
- `git commit` と `git push` は並列実行しないものとし、commit 完了と commit hash を確認してから push するものとする。
- push 後は `git status` で working tree が空であることを確認するものとする。

## 期待効果
- AI の自律性を明示境界内に保つ。
- 不可逆意思決定に対する人間責任を保つ。
- 複数セッションまたは複数インスタンス作業での文書ドリフトを減らす。


# 意思決定方針

## 原則
- 可逆な意思決定は、現在承認済みの方向性の範囲内で AI が提案し、進めてよい。
- 不可逆な意思決定には、人間の明示承認が必要である。
- 重要な意思決定は、後から再構成するのではなく、決まった時点で記録する。

## 可逆な意思決定
- 文言整理。
- 局所的リファクタリング。
- テスト追加。
- プロジェクト価値、ガバナンス、運用境界を変えない明確化。

## 不可逆な意思決定
- 大きなアーキテクチャ転換。
- プロジェクト目的または成功条件の変更。
- 文書構造または正本方針の変更。
- 安全主張、精度目標、現場導入前提に対する強いコミット。
- データ保持方針の変更。

## ゲート規則
- 承認依頼には、文脈、選択肢、採用案、予想される帰結を含める。
- 承認待ち事項は `kisaragi-db/--devs/--state/current_state.md` に列挙する。


# 文書規則

## 中核規則
- 文書体系は最小かつ安定に保つ。
- 新しい永続文書を増やすより、固定された正本文書を更新することを優先する。
- 重要な意思決定は `kisaragi-db\--devs\--state\decision_log.md` に置く。
- 人間確認事項と次アクションは `kisaragi-db\--devs\--state\current_state.md` に置く。
- 長文の一時推論は、要約せずにそのまま恒久アーティファクトへ昇格させない。
- 人が読む運用手順は、必要になった時点で `kisaragi-db\--devs\--evidence\ux_check_manual.md` に集約する。
- 非テキスト資産のデータインベントリ規則は、実装コードやチャットだけに残さず、正本文書へ反映する。
- アクティブタスクに必要な文書更新は、プロジェクト上の真実が変わった同じタスク単位で完了させる。
- skills の唯一の正本は `kisaragi-skills/` とする。

## レイヤ分離
- プロダクト上の真実はアーティファクト層に置く。
- 作業方法と承認規則はプロセス層に置く。
- 短命な痕跡はオブザーバビリティ層に置く。
- 集約指標はメトリクス層に置く。
- 外部技術メモはリファレンス層に置く。

## 共有制御ファイル
- 共有制御ファイルの最上位は `AGENTS.md` とする。
- directory 単位の共有制御ファイルは、各階層の `agents.md` とする。
- state 共有制御ファイルは `kisaragi-db/--devs/--state/decision_log.md` と `kisaragi-db/--devs/--state/current_state.md` とする。
- `agents.md` は配下全体に効く directory rule を持ち、個別 file はその rule に従うものとする。
- shared control file と個別 file が衝突した場合は shared control file を優先し、個別 file を修正する。
- 可能な限り追記優先の文書として扱う。
- 大きな構造変更には人間承認が必要である。

## 整合性確認
- 更新後は、欠落、矛盾、古い参照、重複記述、所有権衝突を確認する。
- 上位文書と下位文書が衝突した場合は、下位文書を修正する。
- 上位文書同士が衝突した場合は停止し、`人間確認待ち` に記録する。

## 記述規則
- このリポジトリの本文は日本語を既定とする。
- 固有名詞、API 名、ファイル名、コマンド名、固定技術用語、その他非日本語でないと意味を損なう記法のみ英語または原文を許可する。
- 一文一意を基本とし、数値目標を書く場合は単位を含める。

## 文字コードとコマンド規則
- プロジェクトのテキストファイルは UTF-8 を使うこと。
- PowerShell でテキストを読む時は、可能な限り UTF-8 を意識した読み方を使う。
- 端末上の文字化けを、ファイル自体の真実として再読込なしに信じない。
- ソースファイル内の文字化けが確認されたら、そのまま持ち越さず速やかに修正する。
- あいまいな既定文字コードでファイルを書き換えるコマンドは避ける。

## 自律タスク継続規則
- 現在の計画作業を終えたら、停止前に短いレビューを行う。
  - 完了したタスクを振り返る
  - プロジェクト全体の矛盾や進捗ギャップを確認する
  - 次に着手すべき高優先タスクを選ぶ
- 意思決定ゲート、依存不足、明示停止がない限り、自動的に高優先タスクを最大 3 件まで続行する。


# 研究方法

## 研究ループ
1. 問題
2. 仮説
3. 設計
4. 評価
5. 意思決定

## 運用規則
- 問題は `problem_and_assumptions.md` との差分として記述する。
- 仮説は採用されるまでは短命な作業痕跡にとどめる。
- 採用された設計変更は `MRL文書` に反映し、重要なら `decision_log.md` にも記録する。
- 評価では、ローカル推論、実行可能検証、現実世界で必要な検証を区別する。
- 可逆な意思決定と不可逆な意思決定は分けて扱う。

## 実行ループ
- 一度作業が始まったら、計画上作業できるところを見つけて作業を継続し、小計画の機械的に止まってはいけない。
- ユーザーが `再開してください` と言った場合は、ゼロから再計画するのではなく、現在の正本と実装状態から再開する要求として扱う。
- セッション最初のプロンプト時と、前のプロンプトから 3 時間以上空いた時は、作業開始前に現在の正本群を再読込する。
- 最小再読込対象は `AGENTS.md`、アーティファクト層、プロセス層である。
- 矛盾が見つかった場合は、継続前に `kisaragi-db/--devs/--state/current_state.md` と必要に応じて `kisaragi-db/--devs/--state/decision_log.md` を更新する。
- 実際の検証ステップへ近づく最短実行経路を優先する。

- 作業単位を終える前に短いタスクレビューと全体クイックレビューを行い、ブロックされていなければ次の高優先タスク 1 件から 3 件へ進む。
- クイックレビューでは、矛盾、文書更新漏れ、古い前提、未完了テスト、追従不足を拾う。

## 人間支援実験規則
- AI は人間のデータ収集能力を無制限と仮定してはならない。
- 新しい取得依頼の前に、目的、予想時間、成功条件、未実施時の代替を含む境界付き依頼を提示する。
- 人間に依頼する実験単位は、一度に小さな依頼 1 件を既定とする。

## 文字コード安定規則
- 文字表示が崩れて見えたら、それをプロジェクト上の真実と扱う前に UTF-8 を意識してファイルを再確認する。
- コマンドと編集方法は UTF-8 の安定性を保つものを優先する。
- ソースファイル内で確認された文字化けは、そのタスクの中で修正する。

## 自律アーキテクト既定
- 構想整理や実装計画では、自律継続は現在のプロジェクト範囲内に限って許可する。
- 新しいアイデアが出ただけで新規恒久文書を作らず、まず既存の正本文書を更新する。
- 新しい文書カテゴリが必要に見える場合は停止し、人間承認を求める。

## 期待効果
- 曖昧な構想から不安定な実装へ飛ぶことを防ぐ。
- 人間とAIを同じ研究ループの中に保つ。
- セッションをまたいだ継続性を確保する。


# Windows 運用マニュアル

## 目的
- 実行可能な入口が存在する時に、このリポジトリ向けの簡潔で人が読める運用手引きを提供する。
- Windows 前提の再現可能な操作について、このマニュアルを単一の正本とする。

## 現在状態
- 現時点のこのリポジトリは、文書の足場に加えて試験実装も含む状態になっている。
- ただし、運用者向けに固定した標準 `.cmd` 群、テスト実行順、コンソール起動手順はまだ十分に整理されていない。

## 規則
- 実装が再現可能な Windows ベース運用を追加したら、チャットへ散在させずに標準手順をここへ記録する。

## 予定セクション
- 環境セットアップ
- テスト実行
- ローカルアプリ起動
- レビューと可視化確認
- データ取込またはリプレイ手順

## tree sync 実行
- `kisaragi-tree/` の同期は `kisaragi-tree/tree-sync.cmd` または `kisaragi-tree/tree-sync.ps1` を使う。
- PowerShell から実行する場合は `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\kisaragi-tree\tree-sync.ps1` を用いる。
- 実行後は `kisaragi-tree/prj-<project>/` 配下に category ごとの junction が生成または更新されることを確認する。
- `kisaragi-tree/` 配下に実データ copy を追加してはならない。

## tree sync 実行物の再生成
- 配布用実行物は `kisaragi-tree/kisaragi-tree-sync.exe` とする。
- 再生成時は `kisaragi-tree/tree-sync.ps1` と `kisaragi-tree/tree-sync-build.sed` を正本として扱う。
- Windows 標準の IExpress を用いて `tree-sync-build.sed` を読み込み、`kisaragi-tree-sync.exe` を再生成する。
- 再生成後は `tree-sync.ps1` を直接実行して同期結果を確認し、その後に `kisaragi-tree-sync.exe` でも起動確認する。
