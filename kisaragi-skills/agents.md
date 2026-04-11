# agents.md

## kisaragi-skills の構成

- この directory は skill 正本 directory とする。
- skill 実体は役割が近いものを統合して配置するものとする。
- 同名 skill は 1 つだけを正本として置くものとする。
- 役割が近い skill は、観点を失わない範囲で既存 skill へ吸収してよい。


## 収録 skill

- `design-first-script-builder`
- `documentation-watchkeeper`
- `delivery-planning-keeper`
- `external-compute-output-keeper`
- `frontier-research-curator`
- `phase-task-orchestrator`
- `reference-rewire-operator`
- `runtime-operator`
- `runtime-structure-dependency-mapper`
- `script-doc-sync-enforcer`
- `skill-distributor`
- `skill-planner`


## 役割境界

- `skill-distributor` を開発 prompt の最上位入口とし、prompt 全体 review、skill 要否判断、mark 解釈、および今回使う最終 skill 集合の確定までを担うものとする。skill 不要判断もこの skill が行う。
- `skill-planner` を `skill-distributor` の直下に置き、確定済み skill 集合の実行順、phase 配置、handoff、完了条件、検証順、closeout 順を管理する orchestration skill とする。skill の追加削除は行わない。
- `phase-task-orchestrator` は開発入口ではなく、`skill-planner` から呼ばれる phase 構成 specialist とし、authoritative doc check、phase header、完了条件、closeout ひな形を提供するものとする。
- `design-first-script-builder` は、設計審査票、責務分離、関数一覧表、docs ID 対応、validation / error handling 契約を先に固定してから script や notebook を書く観点を扱うものとする。
- `documentation-watchkeeper` は docs drift、文書 topology、version 整合、encoding 健全性をまとめて扱うものとする。
- `delivery-planning-keeper` は BDD、TDD、release gate、handover をまとめて扱うものとする。
- `external-compute-output-keeper` は `Colab`、remote notebook、remote GPU job の final output を永続 visible storage へ固定し、cleanup 対象を分離する観点を扱うものとする。
- `runtime-operator` は branch 同期、Docker 安定化、FastAPI 実装運用をまとめて扱うものとする。
- `frontier-research-curator` は外部研究調査を扱うものとする。
- `script-doc-sync-enforcer` は script / notebook / runbook の変更と、関連正本文書更新、test、記録反映を同一 task で閉じる specialist とする。
- `runtime-structure-dependency-mapper` は import、path、artifact、directory の依存棚卸しと runtime 契約確認を扱う specialist とする。
- 発火条件の ownership は `skill-distributor` が持ち、他 skill は自分で発火判断を持たず、受入前提、処理責務、完了条件、失敗条件に集中するものとする。
- `design-first-script-builder`、`reference-rewire-operator`、`documentation-watchkeeper`、`delivery-planning-keeper` は `skill-planner` または `phase-task-orchestrator` の各 phase で併用する専門 skill とする。
- `reference-rewire-operator` は、設計変更で path、ID、helper 所有、contract、generated output 名などの参照先を切り替える時の棚卸し、切替順、grep 検査、文書同期、下流確認を扱うものとする。
