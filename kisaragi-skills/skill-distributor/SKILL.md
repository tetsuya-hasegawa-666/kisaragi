---
name: skill-distributor
description: 開発 prompt を受け取った直後に、今回使うべき最小 skill 群と適用順を先に決めたい時に使う。複数 task、設計変更、文書同期、external compute、BDD/TDD、外部調査などが混ざる依頼で、どの skill を必須起動にするかを Codex が先に提案し、その後の作業を安定させたい時に発動する。
---

# Skill Distributor

prompt を受けた最初の段階で、「今回どの skill を使うべきか」を決めるための入口 skill とする。

## Core Workflow

1. 依頼を 1 行で要約する。
2. 依頼を次の観点で分類する。
   - 複数 task か
   - script / notebook / runbook 編集を含むか
   - 設計変更や参照切替を含むか
   - 文書同期が必要か
   - BDD / TDD / gate 更新が主題か
   - `Colab` / remote compute を含むか
   - 外部調査が必要か
3. 必要 skill を最小集合で選ぶ。
4. skill の適用順を決める。
5. 先頭 commentary で、今回使う skill と順序を 1 回明示する。
6. 選んだ skill に handoff して実作業へ入る。

## Default Routing

- 複数 task を含む開発依頼:
  `phase-task-orchestrator`
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

- `selected_skills`
- `why`
- `order`

短い形でよい。例:

```text
selected_skills:
- phase-task-orchestrator
- reference-rewire-operator
- documentation-watchkeeper

order:
1. phase-task-orchestrator
2. reference-rewire-operator
3. documentation-watchkeeper

why:
- 複数 task 依頼で phase 固定が必要
- path / contract 切替を含む
- 正本文書同期が必要
```

## Guard Rails

- skill を多く積みすぎない。
- 入口 skill が不要な局所 task では、専門 skill だけを選んでよい。
- `phase-task-orchestrator` と `skill-distributor` の役割を混同しない。
  `skill-distributor` は選定、`phase-task-orchestrator` は進行管理を担当する。
- skill 名だけ挙げて順序を書かずに終わらない。
- 選ばなかった skill も、迷ったなら短く理由を書く。

## Coordination

- 開発 prompt の既定入口はこの skill とする。
- この skill が `phase-task-orchestrator` を選んだ時は、その後の phase header 固定まで含めて handoff する。
- この skill 自体は code を編集しない。選定と handoff が責務である。

## When To Read References

- routing ルールに迷う時だけ `references/skill-routing-matrix.md` を読む。
