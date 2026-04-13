# agents.md
- 概案名: `Skill Structure Ledger`

## kisaragi-skills の構成

- この directory は skill 正本 directory とする。
- `1 skill = 1 directory` を原則とする。
- skill 群の親子関係は filesystem の入れ子ではなく、`agents.md` と各 `SKILL.md` の責務記述で表す。
- 同名 skill は 1 つだけを正本として置くものとする。
- 役割が近い skill は、観点を失わない範囲で既存 skill へ吸収してよい。
- `skill-distributor` と `skill-planner` を主線とし、それ以外は原則として child skill または specialist skill として配置する。


## 収録 skill

- `authoritative-doc-scope-resolver`
- `artifact-handoff-mapper`
- `close-condition-definer`
- `design-first-script-builder`
- `documentation-watchkeeper`
- `doc-target-resolver`
- `drive-input-bootstrap-checker`
- `delivery-planning-keeper`
- `evidence-destination-resolver`
- `external-compute-output-keeper`
- `frontier-research-curator`
- `log-promotable-facts-extractor`
- `path-contract-scanner`
- `phase-task-orchestrator`
- `reference-rewire-operator`
- `rule-diff-clarifier`
- `rule-snapshot-reader`
- `runtime-operator`
- `runtime-bootstrap-scope-resolver`
- `runtime-structure-dependency-mapper`
- `script-doc-sync-enforcer`
- `skill-distributor`
- `skill-planner`
- `task-intent-normalizer`
- `task-scope-splitter`
- `test-and-evidence-recorder`


## 役割境界 DA表

| family | parent | child | specialist | ownership / 用途 |
| --- | --- | --- | --- | --- |
| intake | `skill-distributor` | `rule-snapshot-reader` / `authoritative-doc-scope-resolver` / `rule-diff-clarifier` | - | trigger ownership。prompt 全体 review、skill 要否判断、mark 解釈、最終 skill 集合確定 |
| planning | `skill-planner` | `task-intent-normalizer` / `task-scope-splitter` / `close-condition-definer` | `phase-task-orchestrator` | execution ownership。実行順、phase、handoff、完了条件、closeout 管理。skill 追加削除はしない |
| script / docs | `skill-planner` | `doc-target-resolver` / `test-and-evidence-recorder` | `script-doc-sync-enforcer` / `documentation-watchkeeper` / `design-first-script-builder` / `reference-rewire-operator` | script / notebook / runbook 編集、文書同期、参照切替、test / evidence 反映 |
| runtime / structure | `skill-planner` | `artifact-handoff-mapper` / `path-contract-scanner` | `runtime-structure-dependency-mapper` | import、path、artifact、directory 契約の棚卸しと runtime 契約確認 |
| external compute | `skill-planner` | `drive-input-bootstrap-checker` / `runtime-bootstrap-scope-resolver` | `external-compute-output-keeper` | `Colab` / remote notebook / remote GPU job の bootstrap と persistent output 固定 |
| planning / gate | `skill-planner` | - | `delivery-planning-keeper` | BDD、TDD、release gate、handover |
| runtime ops | `skill-planner` | - | `runtime-operator` | branch、Docker、FastAPI runtime 安定化 |
| research | `skill-planner` | - | `frontier-research-curator` | frontier research 収集、比較、reference 更新 |
| closeout / evidence | `skill-planner` | `evidence-destination-resolver` / `log-promotable-facts-extractor` | - | 記録先確定、shared worklog からの durable fact 昇格 |

- 発火条件の ownership は `skill-distributor` が持ち、他 skill は自分で発火判断を持たない。
- `design-first-script-builder`、`reference-rewire-operator`、`documentation-watchkeeper`、`delivery-planning-keeper` は `skill-planner` または `phase-task-orchestrator` の各 phase で併用する。

## test refresh addendum

- この `test/kisaragi-skills/` は refresh 版 workspace における skill 正本とする。
- parent / child / specialist の family map は本書の役割境界と各 `SKILL.md` に従って全面有効とする。
- trigger ownership は `skill-distributor` が持ち、execution ownership は `skill-planner` が持つ。
- decision ownership は parent skill または対応する正本文書が持ち、child skill は補助情報だけを返す。
- record ownership は truth / plan / evidence / method / worklog の各正本文書が持ち、skill は更新補助を担う。
- canonical の detail 判定は skill が勝手に増やさず、対応する project 文書の必須 canonical 要素定義に従う。

