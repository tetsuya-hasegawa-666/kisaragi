# kisaragi pilot skill spec

## 文書の目的

- `kisaragi/` における skill 構成の pilot として、最初に整備する 3 skill を具体化する。
- 対象は `project-context-enforcer`、`script-doc-sync-enforcer`、`runtime-structure-dependency-mapper` とする。
- 本文は skill の責務表として、目的、入力、必須 `READ`、必須 `WRITE`、起動条件、下位 skill、強制する完了条件、失敗時の扱いを固定する。

## 共通前提

- 正本は文書であり、skill は文書を置き換えない。
- skill は、正本文書の閲覧と更新を疎かにしないための強制器として使う。
- project task の `READ` 下限は、常に `project-truth.md` と `HAUB` とする。
- project task の `WRITE` は、`READ` した正本と、その変更内容に関連する文書まで同一 task で到達する。
- 記録先は新設せず、既存の `codex-mrl-test-evidence.md`、`admin-mrl-test-evidence.md`、`--testlogs/`、関連運用文書を使う。
- skill の可視化 rule は skill 側で独自定義せず、`AGENTS.md` と `project-truth.md` と `HAUB` の rule に従う。
- 開発 prompt の trigger ownership は `skill-distributor` が単独で持つ。
- `skill-distributor` は prompt 全体を必ず review し、skill 要否判断、mark 解釈、および今回使う最終 skill 集合の確定を集中して行う。
- `skill-planner` は、`skill-distributor` の出力を受けて、確定済み skill 集合の発火、実行順、phase、handoff、完了条件、検証順を管理する。skill の追加削除は行わない。
- 他 skill は自分で発火判断を持たず、受入前提、処理責務、完了条件、失敗条件だけを持つ。

## pilot skill 一覧

| skill | 主目的 | 位置づけ |
| --- | --- | --- |
| `project-context-enforcer` | task 着手時に project 文脈を強制読込し、必要 skill 群を起動する | 常時入口 |
| `script-doc-sync-enforcer` | script 変更と正本文書更新、test、記録を同一 task で閉じる | 変更監視と同期 |
| `runtime-structure-dependency-mapper` | code / runtime / path / artifact / directory の依存を棚卸しし、崩れを検知する | 計算環境依存整理 |

## skill 1. `project-context-enforcer`

### 目的

- project task 着手時に、最低限必要な project 文脈を必ず固定する。
- task 内容から必要な下位 skill を選び、検知だけで止まらず起動まで行う。
- `project-truth.md` と `HAUB` を読まずに局所修正へ入る流れを禁止する。

### 入力

- task prompt
- 対象 path または対象 project code
- task 種別
  - `script_edit`
  - `notebook_edit`
  - `runbook_edit`
  - `doc_edit`
  - `external_compute`
  - `mixed_dev_task`

### 必須 READ

- `AGENTS.md`
- 対象 project の `project-truth.md`
- 対象 project の `hi-ai-unified-blueprint.md`

### 条件付き READ

- task が script / notebook / runbook 編集を含む時:
  - 対象 directory の `agents.md`
  - 対象 design contract
  - 対象 inventory
- task が external compute を含む時:
  - 対象 runbook
  - 対象 bootstrap / contract 文書
- task が shared rule を触る時:
  - `AGENTSmd-RH.md`

### 必須 WRITE

- 直接編集は必須ではない
- ただし、起動した下位 skill に対して、必要な正本文書更新対象を明示的に handoff すること

### 受入前提

- この skill 自身は発火判断を持たない
- `skill-distributor` が project task と判断し、`skill-planner` が入口文脈固定担当として割り当てた時だけ動く
- 少なくとも対象 project の path または project code が渡されていること

### 呼び出す下位 skill

- 常時候補
  - `skill-distributor`
  - `phase-task-orchestrator`
- task 内容に応じて起動
  - `script-doc-sync-enforcer`
  - `runtime-structure-dependency-mapper`
  - `documentation-watchkeeper`
  - `design-first-script-builder`
  - `reference-rewire-operator`
  - `external-compute-output-keeper`

### 強制する完了条件

- task 開始前に `project-truth.md` と `HAUB` を読んだ状態が確定している
- task 種別に応じた下位 skill が選定済みである
- 下位 skill に、読むべき文書と更新対象文書が handoff 済みである
- 「読まないまま編集開始」が起きていない

### 失敗時の扱い

- `project-truth.md` または `HAUB` を特定できない時は task を止める
- 対象 project 不明時は path から推定し、それでも不明なら user 確認へ戻す
- 下位 skill を決められない時は、`phase-task-orchestrator` と `documentation-watchkeeper` を最低構成として起動する

## skill 2. `script-doc-sync-enforcer`

### 目的

- `script`、`notebook`、`runbook` の変更を、関連する正本文書更新、test 実行、記録反映まで含めて 1 task で完結させる。
- 「code だけ直って、記録や文書が sharedlog にしか残らない」状態を禁止する。

### 入力

- 変更対象 file 群
- 対象 project code
- task の変更要約
- 変更理由

### 必須 READ

- 対象 project の `project-truth.md`
- 対象 project の `hi-ai-unified-blueprint.md`
- 対象 directory の `agents.md`
- 対象 design contract
- 対象 inventory

### 条件付き READ

- shared rule 変更を含む時:
  - `AGENTS.md`
  - `AGENTSmd-RH.md`
- test / evidence 反映先の確認が必要な時:
  - `codex-mrl-test-evidence.md`
  - `admin-mrl-test-evidence.md`
  - `admin-mrl-test-method.md`

### 必須 WRITE

- 変更した code / notebook / runbook 本体
- `project-truth.md` または `HAUB` の関連箇所
- 変更内容に関連する design contract または inventory
- test 実行結果の反映先
  - `codex-mrl-test-evidence.md`
  - `--testlogs/` 要約
  - 関連する補助文書

### 条件付き WRITE

- shared rule に波及した時:
  - `AGENTS.md`
  - `AGENTSmd-RH.md`
- admin 手順に影響する時:
  - `admin-mrl-test-method.md`

### 受入前提

- この skill 自身は発火判断を持たない
- `skill-distributor` が `script` / `notebook` / `runbook` 変更を検知し、`skill-planner` が同期担当として割り当てた時だけ動く
- 変更対象 file 群と対象 project が handoff 済みであること

### 呼び出す下位 skill

- `documentation-watchkeeper`
- `design-first-script-builder`
- `reference-rewire-operator`
- `runtime-structure-dependency-mapper`
- `delivery-planning-keeper`

### 強制する完了条件

- code 変更だけで task を閉じない
- `project-truth.md` と `HAUB` の関連箇所が更新済み、または「更新不要」を明示済み
- 関連 design contract / inventory が同期済み
- test が実行済み
- test 結果が既存の正しい記録先へ反映済み
- sharedlog にしか残っていない重要変更が無い

### 失敗時の扱い

- 更新対象文書が特定できない時は、まず `HAUB` と design contract を基準に棚卸ししてから続行する
- test 実行に失敗した時は、失敗を記録先へ反映したうえで task を close 不可とする
- evidence 反映先が曖昧な時は、新設せず既存構造から最も近い正本を選び、その理由を残す

## skill 3. `runtime-structure-dependency-mapper`

### 目的

- 計算環境に関わる依存を、code 変更に合わせて整理しきる。
- `import/呼び出し関係`、`path read/write`、`artifact producer/consumer`、`directory structure` の崩れを task 中に検知する。
- 実行時に発火する path ずれ、read/write 不整合、handoff 破綻を事前に減らす。

### 入力

- 対象 script / notebook / runbook
- 対象 directory
- 変更差分または変更対象一覧

### 必須 READ

- 対象 project の `project-truth.md`
- 対象 project の `hi-ai-unified-blueprint.md`
- 対象 design contract
- 対象 inventory
- 対象 directory の `agents.md`

### 条件付き READ

- handoff matrix や probe がある時:
  - handoff matrix
  - contract probe
  - 関連 unittest
- external runtime を含む時:
  - bootstrap runbook
  - input / output contract 文書

### 必須 WRITE

- 依存変更があった code / notebook / runbook
- 依存変更を反映すべき design contract
- 依存変更を反映すべき inventory
- handoff matrix や probe が存在する場合は、その関連更新

### 受入前提

- この skill 自身は発火判断を持たない
- `skill-distributor` が依存棚卸し対象を検知し、`skill-planner` が runtime / structure 依存整理担当として割り当てた時だけ動く
- 対象差分または変更対象一覧が handoff 済みであること

### 呼び出す下位 skill

- `reference-rewire-operator`
- `design-first-script-builder`
- `documentation-watchkeeper`
- contract probe 実行 skill
- unittest 実行 skill

### 強制する完了条件

- `import/呼び出し関係` の影響が棚卸し済み
- `path read/write` の変更が design contract または handoff 管理面へ反映済み
- `artifact producer/consumer` の変更が inventory と関連文書へ反映済み
- directory 構造変更が `agents.md` または関連文書と矛盾していない
- 関連 probe / unittest が実行済み

### 失敗時の扱い

- 依存棚卸しが途中で止まった時は code 変更だけで close しない
- probe があるのに未実行なら close 不可とする
- handoff 契約と source の不一致を検知した時は、まず不一致一覧を出し、そのまま後続編集へ進まない

## 3 skill の関係

### 実行順

1. `project-context-enforcer`
2. `script-doc-sync-enforcer`
3. `runtime-structure-dependency-mapper`

### 役割分担

- `project-context-enforcer` は入口であり、文脈読込と下位 skill 起動を担当する
- `script-doc-sync-enforcer` は code と文書と test と記録の同期完了を担当する
- `runtime-structure-dependency-mapper` は計算環境依存の棚卸しと崩れ検知を担当する

## この 3 skill の直下に置きたい補助 skill

| 補助 skill | 役割 |
| --- | --- |
| `doc-target-resolver` | 変更に関連する正本文書を特定する |
| `test-and-evidence-recorder` | test 実行と既存記録先への反映を行う |
| `artifact-handoff-probe-runner` | handoff matrix、probe、unittest を実行する |
| `drive-input-bootstrap-checker` | `Drive mount` から `input解決` までを固定確認する |

## 次段で決めるべき事項

1. 各 pilot skill を `kisaragi-skills/` のどの粒度で実装するか
2. 既存 skill を改修するか、新設するか
3. `doc-target-resolver` と `test-and-evidence-recorder` を補助 skill として先に作るか
4. `prj-kisaragi_0002` でこの 3 skill を試す最初の task を何にするか

## admin 明示指示のマーキング案

### 目的

- admin が prompt で毎回長い説明を書かなくても、短い mark で「この指示は明示的に強い」と示せるようにする。
- skill 側は、この mark を検知した時だけ追加の強制動作や確認動作を発火する。
- 継続困難な重い書式は避け、短い token を先頭または行頭に置くだけで使えるようにする。

### 基本方針

- mark は短く、目で見て即分かることを優先する。
- 自然文に 1 行足すだけで使えるようにする。
- mark が無い時は通常 rule で進める。
- mark がある時だけ、対応する skill が強制動作を追加する。
- mark は「書かないと動かない必須記法」ではなく、普段使わなくても周辺 skill が通常運転で動く前提にする。
- mark は、必要な時だけ追加の強制度を与える補助トリガーとして定義する。

### 推奨する最小 mark

| mark | 意味 | skill への作用 |
| --- | --- | --- |
| `//m` | この task で必ず実施 | 対応処理を省略不可にする |
| `//c` | この点は admin が確認したい | 自動完了せず、確認対象として残す |
| `//s` | code と文書と記録を同 task でそろえる | `script-doc-sync-enforcer` を必須起動 |
| `//d` | 依存、path、artifact、directory を棚卸しする | `runtime-structure-dependency-mapper` を必須起動 |
| `//x` | 文脈固定を強める | `project-context-enforcer` に追加読込を要求 |
| `//l` | 今回は log だけ残せばよい | 正本昇格を保留候補として扱う |
| `//p` | log に残さず正本へ昇格する | 関連文書更新を省略不可にする |
| `//g` | shared rule 変更を含む | `AGENTS.md` と `AGENTSmd-RH.md` の確認を必須化 |

### 最初に採用する運用案

- 初期は「あまり使わないが、一応定義しておく」前提とする。
- mark は常用必須にしない。
- 普段は自然文で指示し、強制度を追加したい時だけ mark を使う。
- 普段使わなくても、文書読込、関連文書更新、test、記録反映は既定動作として走るように周辺 skill を固める。
- まずは 4 つだけを実用候補として扱う。
  - `//s`
  - `//d`
  - `//c`
  - `//m`
- 他の mark は予備定義として置き、必要が出るまで積極運用しない。

### mark の書き方

#### 1 行先頭で書く

```text
//s runbook source を直す時は、関連する HAUB と inventory も同 task で更新する
```

#### 箇条書きにも付けられる

```text
- //m test を実行して既存の記録先へ反映する
- //d path read/write と artifact handoff を棚卸しする
- //c canonical route を変える場合だけ admin 確認に回す
```

#### 複数 mark の併用

```text
//s //d #8-9 を直す。path 契約、handoff、HAUB、test まで同時に閉じる
```

### skill 側の解釈 rule 案

#### `project-context-enforcer`

- `//x` または `//m` がある時は、通常より広い関連文書を読む
- `//c` がある時は、その論点を admin 確認待ちとして task header に残す

#### `script-doc-sync-enforcer`

- `//s` または `//m` がある時は、関連文書更新、test、記録反映を省略不可にする
- `//p` がある時は、sharedlog のみで閉じない

#### `runtime-structure-dependency-mapper`

- `//d` または `//m` がある時は、import、path、artifact、directory の棚卸しを必須にする

### admin にとって軽い運用形

- 基本は自然文で指示する
- 強くしたい行だけに mark を付ける
- すべての文に mark を付ける運用にはしない

### 推奨する使い方

#### 軽い例

```text
//s この修正は code だけで閉じず、HAUB と記録までそろえてください
```

#### 依存確認を強制したい例

```text
//d この変更は path と artifact の依存を必ず棚卸ししてください
```

#### admin が見る点を残す例

```text
//c canonical route を変える時だけ、採用前に判断材料を出してください
```

### この案の利点

- admin は短い mark を付けるだけでよい
- Codex は自然文から意図を推測するだけでなく、明示 token を検知できる
- skill の発火条件を prompt 上で追加指定できる
- 長い運用文を書かなくても、強制度を上げられる
- mark を使わない通常 prompt でも運用できるため、継続性を落としにくい

### この案の注意点

- mark が増えすぎると継続できない
- 初期は 4 種程度に絞る
- 常用前提にしない
- mark が無いからといって正本更新を怠ってよいわけではない
- 正本優先の原則は、mark の有無より上位に置く

### 当面の採用候補

1. `//s`
2. `//d`
3. `//c`
4. `//m`

### 次に決めるべきこと

1. この 4 mark を正式採用するか
2. mark の表記を `//x` 系で固定するか
3. mark 検知をどの skill に組み込むか
4. `AGENTS.md` に shared rule として入れるか、まず `pilot` 運用に留めるか
