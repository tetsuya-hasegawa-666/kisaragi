---
name: skill-distributor
description: 開発 prompt を受け取った直後に prompt 全体を必ず review し、skill を使うかどうか、使うなら何を使うか、admin mark をどう解釈するかを最初に決める最上位入口 skill。必要 skill の最終集合を確定して `skill-planner` へ handoff し、skill 不要判断もこの skill が持つ。
---

# Skill Distributor

prompt を受けた最初の段階で、「今回 skill を使うべきか」「使うなら何を使うべきか」を決め、その最終 skill 集合を確定するための最上位入口 skill とする。

## Trigger Ownership

- 開発 prompt の trigger ownership はこの skill が単独で持つ。
- 他 skill は自分で発火判断を持たない。
- admin mark `//s`、`//d`、`//c`、`//m` などの解釈もこの skill が持つ。

## Core Workflow

1. prompt 全体を review し、依頼を 1 行で要約する。
2. prompt に未処理指示、制約、明示条件、mark が無いかを確認する。
3. `references/skill-trigger-matrix.md` と `references/admin-mark-table.md` を必ず読み、既定 route、mark 補正、skill 化候補を確認する。
4. 依頼を次の観点で分類する。
   - 複数 task か
   - script / notebook / runbook 編集を含むか
   - 設計変更や参照切替を含むか
   - 文書同期が必要か
   - BDD / TDD / gate 更新が主題か
   - `Colab` / remote compute を含むか
   - 外部調査が必要か
   - shared rule と project rule の境界監査が必要か
   - shared worklog rotate / template 強制 / tree sync 定型化の検討が必要か
5. admin mark を解釈し、追加強制が必要かを決める。
6. skill を使わなくてよいかを判定する。
7. skill が必要なら、必要 skill を最小集合で選び、その最終 skill 集合を確定する。
8. 既存 skill で不足する場合は、reference に記載された新規 skill 候補を検討対象として明示する。
9. 最低限の文脈読込対象と handoff 条件を決める。
10. 確定済み skill 集合を `skill-planner` へ handoff する。

## Child Skills

- `rule-snapshot-reader`
- `authoritative-doc-scope-resolver`
- `rule-diff-clarifier`

必要時だけ上記 child skill を参照し、rule 確定と文書範囲切り出しを補助させる。

## Decision Outputs

- `use_skills`: `yes` / `no`
- `no_skill_reason`
- `selected_skills`
- `why`
- `marks_detected`
- `minimum_authoritative_docs`
- `planner_required`

## Default Routing Heuristics

- 複数 task を含む開発依頼:
  `skill-planner`
- その上で必要時に `phase-task-orchestrator`
- script / notebook / runbook の新規作成や大改修:
  `design-first-script-builder`
- path / contract / output / docs_id の切替:
  `reference-rewire-operator`
- 文書 drift や文書 topology の同期:
  `documentation-watchkeeper`
- BDD / TDD / gate / handover:
  `delivery-planning-keeper`
- `Colab` / remote notebook / remote GPU job:
  `external-compute-output-keeper`
- frontier research / 外部技術調査:
  `frontier-research-curator`
- branch / Docker / FastAPI runtime:
  `runtime-operator`

## Output Format

最低限、次の 3 点を返す。

- `use_skills`
- `no_skill_reason`
- `selected_skills`
- `why`
- `planner_required`

短い形でよい。例:

```text
use_skills: yes
no_skill_reason:
selected_skills:
- skill-planner
- reference-rewire-operator
- documentation-watchkeeper

planner_required: yes

why:
- 複数 task 依頼で実行順管理が必要
- path / contract 切替を含む
- 正本文書同期が必要
```

skill 不要判断の時の例:

```text
use_skills: no
no_skill_reason:
- code / docs 編集を伴わず、通常応答の方が軽い
selected_skills:

planner_required: no

why:
- 現状確認のみで specialist skill を起動する必要がない
```

## Guard Rails

- `skill-distributor` と `skill-planner` の役割の違いを理解し、実運用で混同させない。
  役割は、`skill-distributor` は review と最終選定、`skill-planner` は実行順と管理の担当である。
- 既に出力された履歴やデータの現状表示には、文脈が求めない限り skill を使用しない。
- skill は必要十分に選択することが基本。
- skill は最小限の数を目指すものとする。
- skill を選択したときには、なぜ 必要か / 不要か を必ず明示する。
- 選ばなかった skill も、迷ったなら短く理由を書く。
- `skill-planner` が後から skill を増減できる前提で書かない。

## Coordination

- 各project で codex に prompt が渡されたときの既定入口はこの skill とする。
- skill が必要な時は、確定済み skill 集合を `skill-planner` へ handoff する。
- skill 不要判断の時は、その理由を明示したうえで通常 task へ進む。
- この skill 自体は code を編集しない。prompt review、最終 skill 集合の確定、skill 要否判断、必要となった skill の handoff が責務である。

## When To Read References

- prompt review のたびに `references/skill-trigger-matrix.md` と `references/admin-mark-table.md` を必ず読む。
- `agents_skillification_review.md` に対応する skill 化候補の検討も `references/skill-trigger-matrix.md` から行う。
- prompt review 補助が必要な時は `scripts/review_prompt_checklist.py` を使ってよい。
