# agents.md

## kisaragi-skills の構成

- この directory は skill 正本 directory とする。
- skill 実体は役割が近いものを統合して配置するものとする。
- 同名 skill は 1 つだけを正本として置くものとする。
- 役割が近い skill は、観点を失わない範囲で既存 skill へ吸収してよい。


## 収録 skill

- `documentation-watchkeeper`
- `delivery-planning-keeper`
- `external-compute-output-keeper`
- `frontier-research-curator`
- `runtime-operator`


## 役割境界

- `documentation-watchkeeper` は docs drift、文書 topology、version 整合、encoding 健全性をまとめて扱うものとする。
- `delivery-planning-keeper` は BDD、TDD、release gate、handover をまとめて扱うものとする。
- `external-compute-output-keeper` は `Colab`、remote notebook、remote GPU job の final output を永続 visible storage へ固定し、cleanup 対象を分離する観点を扱うものとする。
- `runtime-operator` は branch 同期、Docker 安定化、FastAPI 実装運用をまとめて扱うものとする。
- `frontier-research-curator` は外部研究調査を扱うものとする。
