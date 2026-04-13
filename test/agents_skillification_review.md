# AGENTS skillification review

## 判定記号

| 記号 | 意味 |
| --- | --- |
| `K` | `AGENTS.md` に shared rule として残す |
| `E` | 既存 skill へ移せる |
| `N` | 新規 skill 化候補 |
| `P` | project 固有 skill / project 文書へ寄せる |
| `D` | refresh 設計上は `AGENTS.md` から外す |

## 章別判定

| 章 | 主内容 | 判定 | skill / 先 | 吸収先 | 理由 |
| --- | --- | --- | --- | --- | --- |
| `前提事項` | 最上位 control、読込順、日本語 / UTF-8 前提 | `K` | - | - | shared governance そのもの |
| `project名称のルール` | project code / naming | `K` | - | - | naming governance |
| `ディレクトリ構造と保管内容` | top 構造、shared directory rule | `K` | - | - | shared structure rule |
| `更新規則` | `AGENTS.md` と `AGENTSmd-RH.md` 同時更新 | `E` | `documentation-watchkeeper` | `AGENTSmd-RH.md` | 実行監視は skill 化しやすい |
| `skill dispatch DA表` | 全 prompt は `skill-distributor` を通す | `K` | `skill-distributor` | `skill-trigger-matrix.md` に詳細 | 入口 ownership だけ残す |
| ``AGENTS.md` と project 文書の境界` | shared / project の境界定義 | `K+E+N+P+D` | 下表 | 下表 | 境界 rule と仕分け処理を分離できる |
| `共有 directory 統制` | `--` directory の新設抑止 | `K` | - | - | shared directory governance |
| `workspace 外 access 制限` | workspace 外は `READ` のみ | `K` | - | - | safety rule |
| `実装原則` | BDD / TDD / gate 意味 | `K+E` | `delivery-planning-keeper` / `test-and-evidence-recorder` | project plan / evidence | 原則は shared、運用は skill 化 |
| `開発計画` | `MRL` / `INITL` / gate state | `K+E+P` | `delivery-planning-keeper` / project 文書 | project 文書群 | 状態語は shared、内容運用は project |
| `plan 文書の標準 2 点セット` | table schema、current_state schema | `K+E+P` | `delivery-planning-keeper` / project 文書 | project 文書群 | schema は shared、実体は project |
| `ブランチ規則` | `dev` / `codex/dev` / push hygiene | `K+E` | `runtime-operator` / `branch-sync-operator` | branch 実務 skill | 実行手順は skill 化しやすい |
| `文字コードと commit / push hygiene` | UTF-8、stage hygiene | `K+E` | `runtime-operator` / `doc-governor` | hygiene check skill | 実務チェックは skill 化可 |
| `Guard` | 削減禁止、pointer 両確認 | `K` | - | - | guard rail |
| `協調規則` | AI / 人間役割、prompt 処理原則 | `K+E` | `skill-distributor` / `skill-planner` / `phase-task-orchestrator` | 各 parent skill | ownership は shared、route は skill |
| `並行作業` | 影響文書洗い出し、同 task 更新 | `E` | `documentation-watchkeeper` / `script-doc-sync-enforcer` | doc sync skill | 同期処理は既存 skill 向き |
| `意思決定方針` | reversible / irreversible / approval | `K` | - | - | approval policy |
| `文書規則` | 正本語、worklog、役割境界、共有制御 | `K+E+N+P+D` | 下表 | 下表 | 文書運用 rule と仕分け処理が混在 |
| `test refresh addendum` | refresh 専用 rule | `D` | refresh proposal 側 | `kisaragi_upper_document_lightweighting_proposal.md` と project refresh 文書 | 本番 `AGENTS.md` には不要 |
| `skill 直指示しづらい論点` | gap list | `D` | review 文書 | `skill-direct-gap-list.md` | `AGENTS.md` 本体には不要 |
| `記述と整合` | 日本語、一文一意、整合確認 | `K+E` | `doc-governor` / `documentation-watchkeeper` | doc review skill | 原則は shared、検査は skill 化可 |
| `研究方法` | 再読込、30min rule、問題探索ループ | `K+E` | `skill-distributor` / `skill-planner` / 新規 audit skill | parent skill / future audit skill | stance は shared、再読込運用は skill 化余地あり |
| `Windows 運用マニュアル` | tree sync 手順 | `K+E` | `runtime-operator` / 新規 `tree-sync-operator` | `tree-sync-operator` または `kisaragi-tree/agents.md` | 正本手順は残し、実行確認は skill 化可 |

## ``AGENTS.md` と project 文書の境界` の細分

| rule | 判定 | skill / 先 | 吸収先 | 理由 |
| --- | --- | --- | --- | --- |
| `AGENTS.md` は project 横断 rule だけを持つ | `K` | - | - | 最上位原則 |
| project の目的、UX、artifact、route は project 側 | `K` | - | - | 境界原則 |
| `AGENTS.md` に project path / code を書く時は例示に限る | `E` | 新規 `shared-rule-scope-guard` | `shared-rule-scope-guard` rule | 文書 lint 化しやすい |
| 特定 project の現時点判断や URL を `AGENTS.md` に固定しない | `N` | 新規 `shared-rule-scope-guard` | `shared-rule-scope-guard` | project 固有漏れ検知の guard に向く |
| 変動内容は shared へ一般化できるものだけ残す | `E` | `documentation-watchkeeper` | `documentation-watchkeeper` workflow | 既存 skill で docs drift として扱える |
| project truth に shared rule が混入したら分離する | `N` | 新規 `shared-project-boundary-splitter` | `shared-project-boundary-splitter` | 双方向の分離支援が必要 |
| `--tgpce-map/` project は truth / goal / plan / current / evidence-map を同 directory へ集約可 | `P` | project 構造 rule / project skill | project `agents.md` / `project-truth-core.md` / `realtime-compass-and-status.md` | project 文書設計に近い |
| shared governance / directory / branch / hygiene は `AGENTS.md` に残す | `K` | - | - | 最上位正本 rule |
| refresh canonical set 定義 | `D` | proposal / project 文書 | `kisaragi_upper_document_lightweighting_proposal.md` と `refresh-file-map.md` と対象 project 文書 | refresh 設計変更であり shared rule ではない |
| `HAUB` 非同一視 | `D` | proposal / review 文書 | `kisaragi_upper_document_lightweighting_proposal.md` と `agents_skillification_review.md` | 名称移行の設計メモであり shared rule ではない |

## `文書規則` の細分

| rule 群 | 判定 | skill / 先 | 吸収先 | 理由 |
| --- | --- | --- | --- | --- |
| `正本` 語の使用範囲 | `K` | - | - | shared wording rule |
| 永続文書を増やしすぎない | `K` | - | - | shared doc philosophy |
| 重要変更を上位文書へ反映 | `E` | `documentation-watchkeeper` | `documentation-watchkeeper` workflow | 既存 skill で同期管理可 |
| inventory / non-text evidence の agents 記載 | `E` | `doc-governor` | `doc-governor` workflow | directory rule 追従チェック可 |
| `current_state` / `MRL` / blocker 同時更新 | `E+P` | `delivery-planning-keeper` / project skill | project `realtime-compass-and-status.md` | project 実務への近さが強い |
| shared worklog の header / 読み順 / append-only | `E` | `log-promotable-facts-extractor` + 新規 `worklog-rotator` | `collaborative-worklog_<thema>.md` rule と将来 `worklog-rotator` | 一部既存、一部不足 |
| shared worklog を永続 evidence にしない | `K` | - | - | shared evidence rule |
| `# admin` template 運用 | `N` | 新規 `worklog-template-enforcer` | `worklog-template-enforcer` | 定型強制に向く |
| 文書の役割境界そのもの | `K` | - | - | shared doc architecture |
| admin evidence / Codex closeout を compass へ統合する refresh 変更 | `D` | proposal / project 文書 | `kisaragi_upper_document_lightweighting_proposal.md` と対象 project `realtime-compass-and-status.md` | 設計変更メモ |

## 優先度の高い新規 skill 候補

| skill 名案 | 役割 |
| --- | --- |
| `shared-rule-scope-guard` | `AGENTS.md` に project 固有情報が混入していないか検査する |
| `shared-project-boundary-splitter` | shared rule と project truth の混在を分離候補として出す |
| `worklog-rotator` | `shared worklog` の 50k ring buffer rotate を実施する |
| `worklog-template-enforcer` | `# admin` / `# codex` template と append-only rule を検査する |
| `tree-sync-operator` | `kisaragi-tree` の sync / exe 再生成 / 確認を定型化する |

## 結論

- `AGENTS.md` に残すべき中心は `shared governance / safety / wording / ownership`。
- `route 選定`、`文書同期`、`gate 更新`、`worklog 昇格`、`branch / runtime 実務` は既存 skill へかなり落とせる。
- `shared と project の境界検査`、`worklog rotate`、`template 強制` は新規 skill 化余地が大きい。
- refresh 固有の canonical set や名称移行メモは、本来的には `AGENTS.md` ではなく proposal / review / project 文書へ寄せるべき。
