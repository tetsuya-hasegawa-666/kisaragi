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
- `reference-rewire-operator`
- `runtime-operator`


## 役割境界

- `design-first-script-builder` は、設計審査票、責務分離、関数一覧表、docs ID 対応、validation / error handling 契約を先に固定してから script や notebook を書く観点を扱うものとする。
- `documentation-watchkeeper` は docs drift、文書 topology、version 整合、encoding 健全性をまとめて扱うものとする。
- `delivery-planning-keeper` は BDD、TDD、release gate、handover をまとめて扱うものとする。
- `external-compute-output-keeper` は `Colab`、remote notebook、remote GPU job の final output を永続 visible storage へ固定し、cleanup 対象を分離する観点を扱うものとする。
- `runtime-operator` は branch 同期、Docker 安定化、FastAPI 実装運用をまとめて扱うものとする。
- `frontier-research-curator` は外部研究調査を扱うものとする。
- `reference-rewire-operator` は、設計変更で path、ID、helper 所有、contract、generated output 名などの参照先を切り替える時の棚卸し、切替順、grep 検査、文書同期、下流確認を扱うものとする。
