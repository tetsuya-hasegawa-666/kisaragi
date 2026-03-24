# delete-tmp

この文書は、`kisaragi/` を新規 workspace としてクリーン化する前に、`AGENTS.md` 内の競合・重複、実ディレクトリで起きている競合、運用規則上 `kisaragi/` 全体をそのまま push できない理由を列挙するための作業棚卸しである。

## 0. 現在の実構造の確認結果

### 0-1. `kisaragi/` 直下の実在 directory

- `.git/`
- `kisaragi-db/`
- `kisaragi-ruling/`
- `kisaragi-skills/`
- `kisaragi-tree/`

### 0-2. `kisaragi-db/` 直下の実在 directory

- `--devs/`
- `--exsams/`

### 0-3. `kisaragi-db/--devs/` 直下の実在 directory

- `--evidence/`
- `--plans/`
- `--products/`
- `--project-truth/`
- `--state/`
- `--testcode/`
- `--testlogs/`

### 0-4. `kisaragi-db/--exsams/` 直下の実在 directory

- `prj-codev-viewer/`
- `prj-remote-pwsh/`
- `prj-reviework/`

## 1. `AGENTS.md` 内部で競合していること

### 1-1. branch 規則が二重化し、内容も競合している

- `Git Branch Rule` は運用 branch を `codex/dev` と `user/dev` としている。
- `ブランチ規則` は人間向け基準 branch を `dev`、Codex 通常 push 先を `codex/dev` としている。
- `push` 指示時の反映先が `user/dev` なのか `dev` なのか一意に決まらない。

### 1-2. test 生成物の置き場が競合している

- `--devs` の説明では、`test 出力` を `--devs` 配下に置くとしている。
- `--exsams` の説明では、`開発中のテストによる生成物はすべてここに置く` としている。
- test log、report、artifact、screen capture の正置場が `--devs/--testlogs` なのか `--exsams` なのか一意に決まらない。

### 1-3. `current_state.md` の置き場が競合している

- `<order>` の directory structure では `--devs/--state/` の下に project ごとの state を置く形になっている。
- 協調規則と文書規則では `devs/state/current_state.md` を共有制御ファイル、記録先としている。
- project 単位の `current_state.md` と共有 1 枚の `current_state.md` のどちらを正本にするかが未確定である。

### 1-4. `decision_log.md` の置き場が競合している

- 文書規則では、重要な意思決定は `kisaragi-db\--devs\--evidence\decision_log.md` に置くとしている。
- 共有制御ファイルの節では `devs/state/decision_log.md` を共有制御ファイルとしている。
- `decision_log.md` の authoritative path が 2 つ存在する。

### 1-5. `kisaragi-db/` の標準構造が競合している

- `<order>` では `kisaragi-db/` の構造を `--devs/`、`--exsams/`、`agents.md` としている。
- `kisaragi-db/agents.md` では `--devs/`、`--docs/`、`--skills/`、`--exsams/`、`agents.md` としている。
- `--docs/` と `--skills/` を標準構造に含めるのかが未確定である。

### 1-6. `kisaragi-tree` 更新対象名が project 名と競合している

- `<order>` では `kisaragi-tree` の自動更新対象として `prj-codev-view` を挙げている。
- 実際の project 名は `prj-codev-viewer` である。
- 自動更新対象の project 名が一致していない。

## 2. `AGENTS.md` 内部で重複していること

### 2-1. UTF-8 / 文字化け対策が複数節に分散している

- `<order>` の大前提
- `文字コードと調査 command`
- `文字コードとコマンド規則`
- `文字コード安定規則`

上記がほぼ同じ趣旨を繰り返しているため、修正時の追従漏れが起きやすい。

### 2-2. branch / push 規則が複数節に分散している

- `Git Branch Rule`
- `ブランチ規則`
- `commit and push hygiene`

内容の重複だけでなく一部競合もあるため、後続の運用判断を不安定にしている。

### 2-3. `current_state.md` / `decision_log.md` 記録規則が複数節に分散している

- 協調規則
- 並行作業規則
- ゲート規則
- 文書規則
- 実行ループ

記録先 path と用途が 1 か所に集約されていない。

## 3. 実ディレクトリで起きている競合

### 3-1. top directory が `<order>` 記載の構造と一致していない

- 実ディレクトリには `.git`、`.gitignore`、`delete-tmp.md` が存在する。
- `<order>` の top structure にはこれらが記載されていない。

### 3-2. `kisaragi-db/` 実体が `<order>` 記載と一致していない

- 実ディレクトリの `kisaragi-db/` は `--devs/`、`--exsams/`、`agents.md` で構成されている。
- 過去記述の一部には `--docs/` を含む想定が残っていた。
- 実体と旧記述がずれていたため、参照先の判断を誤る余地があった。

### 3-3. `kisaragi-db/agents.md` が要求する `--skills/` が実在しない

- `kisaragi-db/agents.md` は `kisaragi-db/--skills/` を含む構造を示している。
- 実ディレクトリには `kisaragi-db/--skills/` がない。

### 3-4. `kisaragi-tree/` が junction になっていない

- `<order>` では `kisaragi-tree/` は junction によって構成するとしている。
- 実ディレクトリ上の `kisaragi-tree/` は通常 directory として見えている。

### 3-5. `kisaragi-tree/agents.md` が存在しない

- `<order>` では `kisaragi-tree/` の構造に `agents.md` が含まれている。
- 現状の `rg --files -g "AGENTS.md" -g "agents.md"` では `kisaragi-tree/agents.md` が見つからない。

### 3-6. 実運用の test 生成物が `--devs/--testlogs/` に滞留している

- `prj-remote-pwsh` の `artifacts/`、`logs/`、`reports/`、`captures/`
- `prj-reviework` の `artifacts/testDebugUnitTest/binary/`、`logs/`、`reports/`
- `prj-codev-viewer` の `logs/`、`reports/`

これらは `--devs` に置くのか `--exsams` に逃がすのかが `AGENTS.md` 上で未整理である。

### 3-7. 新規コピー分と既存文書の混在が起きている

- `kisaragi-db/--devs/--project-truth/agents.md` も既に存在する。
- `project-truth` の正本位置に関する旧提案や旧記述が残っている。
- 現在の実構造では `project-truth` は `kisaragi-db/--devs/--project-truth/` に存在するため、旧 `--docs` 前提の記述は除去対象である。

## 4. `kisaragi/` 全体がそのまま push できない理由

### 4-1. working tree が dirty である

- `AGENTS.md` が未 commit である。
- `kisaragi-db/--devs/--plans/prj-reviework/bdd-release-compass.md` が未 commit である。
- `kisaragi-db/--devs/--plans/prj-reviework/tdd-test-matrix.md` が未 commit である。
- `kisaragi-db/--devs/--state/prj-codev-viewer/current_state.md` が未 commit である。
- `kisaragi-db/--devs/--state/prj-remote-pwsh/current_state.md` が未 commit である。
- `kisaragi-db/--devs/--state/prj-reviework/current_state.md` が未 commit である。

### 4-2. 未追跡 file / directory が存在する

- `delete-tmp.md`
- `kisaragi-db/--devs/--plans/prj-codev-viewer/bdd-release-compass.md`
- `kisaragi-db/--devs/--plans/prj-codev-viewer/tdd-test-matrix.md`
- `kisaragi-db/--devs/--plans/prj-remote-pwsh/mrl-record.md`
- `kisaragi-db/--devs/--state/current_state.md`
- `kisaragi-db/--devs/--state/decision_log.md`
- 各階層に新規配置した `agents.md`
- `kisaragi-tree/` 配下の tree sync 実行物と設定 file

このままでは push しても workspace 全体は再現されない。

### 4-3. branch 運用規則が衝突していて push 先を一意に決められない

- 現在の local branch は `codex/dev` のみである。
- remote branch は `codex/dev` と `user/dev` のみで、`dev` は存在しない。
- 一方で `AGENTS.md` には `push` 指示時の反映先として `dev` を要求する規則がある。
- 規則どおりに push すべき branch が確定していない。

### 4-4. 既に追跡済みの生成物が `commit and push hygiene` に反している

- `kisaragi-db/--devs/--testlogs/prj-codev-viewer/logs/npm-build.log`
- `kisaragi-db/--devs/--testlogs/prj-codev-viewer/logs/npm-test.log`
- `kisaragi-db/--devs/--testlogs/prj-remote-pwsh/captures/20260321-084541-rr-20260321-084541-slack-status.png`
- `kisaragi-db/--devs/--testlogs/prj-reviework/artifacts/testDebugUnitTest/binary/output.bin`
- `kisaragi-db/--devs/--testlogs/prj-reviework/reports/testDebugUnitTest/html/index.html`

`commit and push hygiene` は build output、generated file、cache、device dump、screen capture、tmp などを commit / push しないとしているため、規則準拠の状態ではない。

### 4-5. `kisaragi-tree/` が想定構造を満たしていない

- junction 化されていない。
- `agents.md` がない。
- `prj-codev-view` / `prj-codev-viewer` 名称も不一致である。

tree layer を含めて `kisaragi/` 全体を正本準拠で push する条件を満たしていない。

### 4-6. `kisaragi-db` 配下の標準構造が確定していない

- root `AGENTS.md` の `<order>` は `--devs` と `--exsams` を標準としている。
- 下位文書や旧棚卸しには `--docs` と `--skills` を含む想定が残っていた。
- 実ディレクトリは `--docs` も `--skills` も持たない。

標準構造の合意がないまま push すると、何を正本とみなすかが揺れる。

## 5. 今回の削除・移動候補として先に確認すべきもの

- `AGENTS.md` の branch 規則を `codex/dev` / `user/dev` / `dev` のどれに統一するか
- test 生成物の正置場を `--devs/--testlogs` と `--exsams` のどちらへ統一するか
- `current_state.md` と `decision_log.md` の authoritative path を 1 本化するか
- `kisaragi-db/--docs/` を正式採用するか、別階層へ寄せるか
- `kisaragi-tree/` を junction に作り直すか
- 既に追跡済みの generated file を index から外すか

## 6. 整合に向けた提案

### 6-1. branch 規則の統一提案

- 提案: 人間向け基準 branch を `dev`、Codex 通常 branch を `codex/dev` に統一し、`user/dev` 規則は廃止する。
- 理由: 現在の `AGENTS.md` では `dev` と `user/dev` が競合しており、運用判断が二重化している。
- 反映案:
  - `Git Branch Rule` を削除または `ブランチ規則` に統合する。
  - remote に `dev` を作成する。
  - `user/dev` は移行完了後に廃止候補とする。

### 6-2. `kisaragi-db` 標準構造の統一提案

- 提案: 現在の実構造どおり、`kisaragi-db/` の標準構造を `--devs/`、`--exsams/`、`agents.md` に統一し、`--docs/` と `--skills/` は採用しない。
- 理由: 実際に存在する `kisaragi-db/` 直下 directory は `--devs/` と `--exsams/` の 2 つである。`--skills/` は存在せず、skills は top-level の `kisaragi-skills/` に集約される。
- 反映案:
  - `kisaragi-db/agents.md` の構造説明を実構造へ合わせる。
  - `--docs/` を前提にした旧記述を削除する。
  - `kisaragi-skills/` を skills の唯一の正本として明記する。

### 6-3. `project-truth` の正本位置の統一提案

- 提案: 現在の実構造に合わせ、`project-truth` は `kisaragi-db/--devs/--project-truth/` を正本とする。
- 理由: 現時点の実ディレクトリに `--docs/` は存在せず、push 前 clean 化では実構造との一致を優先すべきである。
- 反映案:
  - `--docs/` 前提の旧記述を棚卸し対象として除去する。
  - `kisaragi-db/--devs/--project-truth/agents.md` を参照型の初期配置として維持する。

### 6-4. `current_state.md` と `decision_log.md` の path 統一提案

- 提案: shared control file は `kisaragi-db/--devs/--state/current_state.md` と `kisaragi-db/--devs/--state/decision_log.md` に統一し、project 個別 state は `kisaragi-db/--devs/--state/prj-<project>/current_state.md` とする。
- 理由: `--state/` の下に shared と per-project の両方を置けば、directory 役割と path 規則を両立できる。
- 反映案:
  - `AGENTS.md` の `devs/state/current_state.md` 表記を絶対 path ベースにそろえる。
  - `decision_log.md` の置き場を `--evidence` と `--state` のどちらか 1 つへ統一する。
  - 推奨は shared control file として扱いやすい `--state/decision_log.md` である。

### 6-5. test 生成物の正置場統一提案

- 提案: 開発中に都度再生成される実ファイルは `--exsams/`、記録として残す要約結果のみ `--devs/--testlogs/` に残す。
- 理由: `<order>` の `--exsams` 定義と `commit and push hygiene` を両立しやすい。
- 反映案:
  - `--devs/--testlogs/` には summary、manifest、`.gitkeep` だけを残す。
  - binary、HTML report、screen capture、raw JSON log は `--exsams/prj-<project>/` に移す。
  - `.gitignore` をこの方針に合わせて補強する。

### 6-6. 既追跡生成物の整理提案

- 提案: 既に追跡済みの generated file は index から外し、必要なら summary 文書だけ残す。
- 理由: 現行の tracked artifact は `commit and push hygiene` と矛盾している。
- 反映案:
  - `git rm --cached` 対象候補を project ごとに一覧化する。
  - 置換要約として `verification-summary.md`、`mrl-ux-valid.md`、必要最小限の manifest を残す。

### 6-7. `kisaragi-tree` の再整備提案

- 提案: `kisaragi-tree/` は一度空にして、junction 前提で作り直す。
- 理由: 現在は通常 directory で、`agents.md` も欠けており、`prj-codev-view` 名義も不一致である。
- 反映案:
  - target project 名を `prj-codev-viewer` に統一する。
  - `kisaragi-tree/agents.md` を追加する。
  - junction 作成手順を Windows 運用マニュアルへ記載する。

### 6-8. top directory の許容物整理提案

- 提案: top directory は `AGENTS.md`、`.git`、`.gitignore`、`delete-tmp.md` のような workspace 管理に必要な最小ファイルを許容物として明記する。
- 理由: 現実の Git workspace 運用では `.git` と `.gitignore` を排除できない。
- 反映案:
  - `<order>` の top structure は主要論理構造だけを示すと注記する。
  - 実運用補助 file の許容条件を 1 行で追加する。

### 6-9. `AGENTS.md` の重複節圧縮提案

- 提案: 次の 3 系統は 1 節へ統合する。
  - branch / push 規則
  - UTF-8 / 文字コード規則
  - state / decision 記録規則
- 理由: 現状は同趣旨の規則が複数箇所に分散し、修正時の差分追跡が難しい。
- 反映案:
  - 先に authoritative section を 1 つ決める。
  - 他節は参照だけ残して重複本文を削る。

### 6-10. clean 化の実行順提案

- 提案: 整理作業は次の順で進める。
1. `AGENTS.md` の path / branch / layer 規則を確定する
2. `kisaragi-db` 構造を確定する
3. `project-truth` と state / decision の正本位置を移す
4. generated file を `--exsams` へ退避し index から外す
5. `kisaragi-tree` を junction で再作成する
6. branch 整備後に commit / push する

- 理由: 規則確定前に file 移動を始めると、同じ文書を複数回動かすことになるためである。

## 7. 6-10 に対する実行結果、未実行項目、修正提案

### 7-1. 実行できたこと

- `origin/user/dev` を基準に remote `dev` を新設し、人間向け基準 branch を `dev` として運用可能な状態にした。
- `AGENTS.md` の非 `<order>` 節で、`ブランチ規則` を authoritative section とする整理を反映した。
- `kisaragi-skills/` を skills の唯一の正本とする記述を追加した。
- `kisaragi-db/`、`--devs/`、`--exsams/`、`kisaragi-ruling/`、`kisaragi-tree/` と、`--devs` 配下の各 `--` directory に `agents.md` を初期配置した。
- `kisaragi-db/--devs/--state/current_state.md` と `kisaragi-db/--devs/--state/decision_log.md` を shared control file として新設した。
- `AGENTS.md` の非 `<order>` 節で、shared control file の階層に `agents.md` を追加し、shared と per-file の優先関係を明記した。
- 再生成可能な raw test 生成物を `kisaragi-db/--exsams/` へ移し、`.gitignore` を補強した。
- `kisaragi-tree/` の top に tree 同期用の `tree-sync.ps1`、`tree-sync.cmd`、`kisaragi-tree-sync.exe` を配置し、PowerShell 実行で同期できることを確認した。

### 7-2. この指示だけでは完了していないこと

- remote `dev` の「既存データを最初にすべて削除」は、remote 側に `dev` 自体が存在しなかったため、実質的には空 branch の新設で代替された。
- `user/dev` の廃止まではまだ実施していない。現在は `origin/user/dev` が残っている。
- 「競合している相手のデータ名を変更して回避する」処理は、今回の push 対象でまだ実行していない。実際に merge 競合または path 競合が出た時点で、相手側名の退避 rename 方針を個別適用する必要がある。
- `kisaragi-tree/` は同期実行物を整えたが、directory 自体を junction そのものへ置換したわけではない。現在は通常 directory の下に project ごとの junction を張る構成である。
- `AGENTS.md` の `<order>` 内部に残る `--devs` と `--exsams` の test 出力規則の二重性は、`<order>` を Codex が書き換えられないため、本文側の整合だけでは完全解消していない。

### 7-3. 現在の `AGENTS.md` で文章規則上、修正提案が望ましい箇所

- `<order>` 内の `--devs` 説明にある `test 出力` は、`--exsams` の「開発中のテストによる生成物はすべてここ」と競合するため、`--devs` 側を「要約・記録・manifest」に限定する文言へ寄せたい。
- `<order>` 内の `kisaragi-tree/` 説明は「`kisaragi-tree/` 自体が junction」と読めるが、今回実装したのは tree 配下 project directory の junction 構成である。実装方針に合わせるなら「tree 配下を junction で構成する」と書く方が正確である。
- `Guard` の `../issue-note.md` は現在の workspace 実構造に存在確認が要る。正本が未配置なら参照規則だけ残すと把握漏れの温床になる。
- `Windows 運用マニュアル` は tree sync 実行物の起動方法を追記対象とするのが望ましい。
- `共有制御ファイル` と `各 directory の agents.md` の関係は本文側で最小限追記済みだが、`<order>` 側にも同じ整理があると読み始め時点で迷いが減る。

### 7-4. push 前に残っている実務上の抜け漏れ

- 現在の working tree は dirty のままであり、未追跡 file と tracked deletion が多数ある。
- `--devs/--testlogs/` から移した tracked 生成物は、commit 時に delete として整理する必要がある。
- `kisaragi-tree-sync.exe` は実行確認済みだが、配布運用するなら再生成手順を `Windows 運用マニュアル` に残すのが安全である。
- `dev` へ push する前に、`codex/dev` 側へも同じ整理をどう反映するかを決める必要がある。
