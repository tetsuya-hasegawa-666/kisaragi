# skill trigger matrix

## 目的

- `skill-distributor` が prompt review 後に、必要 skill 候補を過不足なく選ぶための基準表とする。
- trigger ownership は `skill-distributor` が持ち、この表はその判断根拠の軽量 reference とする。

## 基本方針

- まず `skill を使わない` 選択肢を残したまま review する。
- 複数条件に当てはまる時は、最小 skill 集合を優先する。
- specialist skill の発火条件はここで判断し、各 specialist 側へ持ち込まない。

## trigger matrix

| 案件 | `skill-distributor` | `skill-planner` | 既定 child / specialist | 終点 |
| --- | --- | --- | --- | --- |
| codex への prompt すべて | ◎ | ○ | `rule-snapshot-reader` / `authoritative-doc-scope-resolver` / `rule-diff-clarifier` | skill 要否と最終集合確定 |
| 複数 task のとき | ◎ | ◎ | `task-intent-normalizer` / `task-scope-splitter` / `close-condition-definer` / `phase-task-orchestrator` | phase 固定 |
| code 編集 ipynb 含む / runbook 編集 | ◎ | ◎ | `design-first-script-builder` / `reference-rewire-operator` / `script-doc-sync-enforcer` | code / docs / test / evidence 同 task close |
| 文書同期作業のとき | ◎ | ○ | `documentation-watchkeeper` / `doc-target-resolver` | 正本整合 |
| path / artifact / directory 契約変更 | ◎ | ◎ | `runtime-structure-dependency-mapper` / `artifact-handoff-mapper` / `path-contract-scanner` | 依存棚卸し完了 |
| BDD / TDD / gate 更新 | ◎ | ◎ | `delivery-planning-keeper` / `test-and-evidence-recorder` | plan と gate 更新 |
| external compute / Colab | ◎ | ◎ | `external-compute-output-keeper` / `drive-input-bootstrap-checker` / `runtime-bootstrap-scope-resolver` | bootstrap / persistent output 固定 |
| runtime / branch / Docker / FastAPI | ◎ | ◎ | `runtime-operator` | runtime 安定化 |
| shared worklog 昇格 / reset | ◎ | ○ | `log-promotable-facts-extractor` / `evidence-destination-resolver` | 正本昇格後 reset 可否確定 |
| frontier 調査 | ◎ | ○ | `frontier-research-curator` | reference 更新 |

- 記号は `◎=必須`、`○=条件付き` とする。

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

## skillification candidate check

| 条件 | 既存 route | 追加検討 |
| --- | --- | --- |
| `AGENTS.md` に project 固有 path / code / URL / 現時点判断が混入していそう | `documentation-watchkeeper` | 新規 `shared-rule-scope-guard` |
| shared rule と project truth の混在を分離したい | `documentation-watchkeeper` | 新規 `shared-project-boundary-splitter` |
| `shared worklog` が 50k 上限へ近い / rotate 判断が必要 | `log-promotable-facts-extractor` | 新規 `worklog-rotator` |
| `# admin` / `# codex` template と append-only を強制したい | `log-promotable-facts-extractor` | 新規 `worklog-template-enforcer` |
| `kisaragi-tree` の sync / exe 再生成 / 確認を定型化したい | `runtime-operator` | 新規 `tree-sync-operator` |

- 上記条件に当てはまる時は、`skill-distributor` は既存 skill だけで閉じるか、新規 skill 候補が必要かを必ず short note で明示する。
- 新規 skill 候補が必要でも、その場で自動新設はせず、まず候補名と不足理由を handoff または review 文書へ残す。
