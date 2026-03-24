# AGENTS.md

<order>

## 目的

- 機械設計者から転身したソフトウェアエンジニアが、codexという非常に優れたシニアソフトウェア＆UXエンジニアをパートナーとして、人にとって有益なソフトウェアをいち早く開発し社会実装することを目的とする。
</order>

<order>

## 大前提

- 文章の上行に<order>、下行に</order>があり、その間にある文章は、admin（ユーザー）による指示です。
- 最優先で必ず守りなさい。また、codexによる書き換えは禁止とします。

- この配下の文書やデータの配置ルールは、この文書の案内に必ず従うこととする。
- 識別子、command、path、API 名、service 名、英字略語は必要に応じてそのまま使うものとする。
- 全ての文書における記録用途および人やAIプロンプト向けの説明に用いる言語は日本語とすること。
- ただし、ファイル名は半角英数字に加え、各プログラムで混乱が起きにくい半角記号のみとすること。
- 文字化けを避けるため 日本語文書を取り扱うときは、UTF-8 に適した入力方法および出力方法を必ず用いること。
- 語彙は、日本人のソフトウェアエンジニアが日本語で専門会話するときの水準にそろえるものとする。

- 一般的に使われる `README.md` や `index.md` は利用は禁止。どうしても必要な場合は、1.`AGENTS.md`、2.`agents.md`の冒頭に説明を付加して利用すること。
</order>

<order>

## 読み順（入口）

- 読み順は、 kisaragi/ 直下を基準として、取り扱う文書の階層までにある、すべての1.`AGENTS.md`、2.`agents.md`を把握して、それらのルールに従って、該当文書の把握・編集を行うこと。

</order>

<order>

## kisaragi/ ディレクトリ構造と役割

- `kisaragi/`の最上位運用正本である、AGENTS.mdが保管される
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
</order>

<order>

## kisaragi-db/ ディレクトリ構造と役割

- プロジェクトの方針、構想、経過、成果物などプロジェクトで発生するデータはすべてこのディレクトリの中に保管すること。
- 配下のディレクトリは、prj-<project名> （接頭にprj-がある）ディレクトリ以外は、接頭に"--"を持つ。
- 接頭に"--"を持つディレクトリは、その親のディレクトリで取り扱う情報を細分化した1要素である。
- 接頭に"--"を持つディレクトリの新規作成や削除については、ユーザーの了解がない限り禁止とする。（ユーザーは柔軟に対応するので、追加や削除の提案はしてください）
- 接頭に"--"を持つディレクトリ直下には、agents.md を置いてもよく、かつagents.md以外のファイルを置くことを禁止する。
- 接頭に"--"を持つディレクトリ内に prj-<project名> （接頭にprj-がある）のディレクトリがある場合、そのディレクトリと並列に、接頭に"--"を持つディレクトリが存在してはいけない。
- prj-<project名> （接頭にprj-がある） の直下には、agents.md を置くのは禁止する。

- kisaragi-db/のディレクトリ構造は下記
```text
kisaragi-db/
  --devs/
  --exsams/
  agents.md

```
</order>


<order>

## kisaragi-skills/ ディレクトリ構造と役割

- kisaragi/全体で利用するskillsを集合管理する。
- ディレクトリ構造は下記
```text
kisaragi-skills/
  ...
  agents.md

```
</order>

<order>

## kisaragi-tree/ ディレクトリ構造と役割

- `kisaragi-tree/` は junction によって構成し、実データの copy は持たないものとする。
- `kisaragi-tree/` で直接編集せず、更新は常に `kisaragi-db/` の正本側で行うものとする。
- `kisaragi-tree/` は ディレクトリにデータが追加削除されるたびに、自動更新されるように`prj-codev-view`を更新して、閲覧UIが対応すること。
- `sandbox/kisaragi-tree/` は `kisaragi-db/` の正本を project 単位で見やすく束ねる tree layer とする。

```text
kisaragi-tree/
  ...
  agents.md

```
</order>


<order>

## --devs/ ディレクトリ構造と役割

- `--devs` は、計画、状態、証跡、test 出力、test code、product 実装物および証跡を置くこと。

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
</order>


<order>

## --exsams/ ディレクトリ構造と役割

- --exsams は、開発中のテストによる生成物はすべてここに置くこと。
- ディレクトリの内部は、prj-<project名> ディレクトリが配置され、その中に各プロジェクトからの生成物を置くこと。
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

## Git Branch Rule

- 運用 branch は `codex/dev` と `user/dev` とする。
- Codex は自己判断で `codex/dev` へ push してよいものとする。
- `user/dev` は user の明示指示がある場合のみ push してよいものとする。
- user の明示指示がある場合、Codex は `codex/dev` と `user/dev` の両方へ push するものとする。
- `git add`、`git commit`、`git push`、file 移動、削除、rename など、前段の結果に依存する command は必ず直列に実行するものとする。
- `git commit` と `git push` は並列実行しないものとし、commit 完了と commit hash を確認してから push するものとする。
- push 後は `git status` で working tree が空であることを確認するものとする。

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
- 迷いがある場合は `../issue-note.md` と `../kisaragi-ruling/` を確認し、必要に応じて記載すること。
