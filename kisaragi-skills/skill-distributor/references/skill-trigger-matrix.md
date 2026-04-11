# skill trigger matrix

## 目的

- `skill-distributor` が prompt review 後に、必要 skill 候補を過不足なく選ぶための基準表とする。
- trigger ownership は `skill-distributor` が持ち、この表はその判断根拠の軽量 reference とする。

## 基本方針

- まず `skill を使わない` 選択肢を残したまま review する。
- 複数条件に当てはまる時は、最小 skill 集合を優先する。
- specialist skill の発火条件はここで判断し、各 specialist 側へ持ち込まない。

## trigger matrix

| prompt 条件 | 選定候補 | 備考 |
| --- | --- | --- |
| 複数 task が混在する | `skill-planner` | phase 要否は planner が判断 |
| `script` / `notebook` / `runbook` を新規作成または大改修する | `design-first-script-builder` | 設計駆動が必要な時 |
| path / contract / output / docs_id を切り替える | `reference-rewire-operator` | old/new 対応と probe を伴いやすい |
| code 変更に文書更新が伴う | `documentation-watchkeeper` | docs drift close |
| BDD / TDD / gate / handover を扱う | `delivery-planning-keeper` | plan / gate 系 |
| `Colab` / remote notebook / remote GPU job を扱う | `external-compute-output-keeper` | 出力保全 |
| branch / Docker / FastAPI runtime を安定化する | `runtime-operator` | runtime 系 |
| 外部技術調査や reference note 更新を行う | `frontier-research-curator` | 調査系 |
| project task で文脈固定が必要 | `skill-planner` と必要時 `phase-task-orchestrator` | planner が specialist を束ねる |

## mark 補正

| mark | 追加作用 |
| --- | --- |
| `//s` | code と文書と記録の同期を planner に要求する |
| `//d` | 依存 / path / artifact / directory の棚卸し担当を planner に要求する |
| `//c` | admin 確認待ち論点を plan に残す |
| `//m` | 対応処理を省略不可にする |

## skill 不要判断の例

- 単純な説明だけで code / docs 編集が無い
- 現状確認だけで編集や実行を伴わない
- skill を使うより通常応答の方が明らかに軽い

## 注意

- `skill-planner` は execution order owner であり、選定 owner ではない。
- 迷った時は skill を増やしすぎず、`skill-planner` と specialist 1 本から始める。
