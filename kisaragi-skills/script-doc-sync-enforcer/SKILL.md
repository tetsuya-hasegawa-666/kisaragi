---
name: script-doc-sync-enforcer
description: `script`、`notebook`、`runbook` の変更を、関連する正本文書更新、test 実行、記録反映まで同一 task で閉じる specialist skill。発火判断は持たず、`skill-distributor` と `skill-planner` から同期担当として割り当てられた時だけ動く。
---

# Script Doc Sync Enforcer

code 変更だけが先行し、正本文書更新、test、記録反映が sharedlog に取り残される状態を防ぐ specialist skill とする。

## Trigger Ownership

- この skill 自身は発火判断を持たない。
- `skill-distributor` が code / notebook / runbook 変更と文書同期が必要だと判断し、`skill-planner` が同期担当として割り当てた時だけ動く。

## 受入前提

- 対象 project code または対象 path が handoff 済みであること
- 変更対象 file 群が handoff 済みであること
- `project-truth.md` と `HAUB` を読むべき task であることが確定していること

## Core Workflow

1. 変更対象 file 群を確認する。
2. `project-truth.md`、`HAUB`、対象 directory の `agents.md`、design contract、inventory を読む。
3. 変更内容に関連する正本文書候補を特定する。
4. code / notebook / runbook の変更と同じ task で、関連する正本文書、design contract、inventory を更新する。
5. test 実行対象を確定する。
6. test を実行し、結果を既存の記録先へ反映する。
7. sharedlog にしか残っていない持続価値がないかを確認する。
8. close 条件を満たしているか確認する。

## 必須 READ

- 対象 project の `project-truth.md`
- 対象 project の `hi-ai-unified-blueprint.md`
- 対象 directory の `agents.md`
- 対象 design contract
- 対象 inventory

## 条件付き READ

- shared rule 変更を含む時:
  - `AGENTS.md`
  - `AGENTSmd-RH.md`
- 手順や記録先を確認する時:
  - `codex-mrl-test-evidence.md`
  - `admin-mrl-test-evidence.md`
  - `admin-mrl-test-method.md`

## 必須 WRITE

- 変更した code / notebook / runbook 本体
- `project-truth.md` または `HAUB` の関連箇所
- 関連 design contract または inventory
- test 結果の既存記録先

## 条件付き WRITE

- shared rule に波及した時:
  - `AGENTS.md`
  - `AGENTSmd-RH.md`
- admin 手順に影響する時:
  - `admin-mrl-test-method.md`

## 完了条件

- code 変更だけで task を閉じていない
- 関連正本文書が更新済み、または更新不要が明示済み
- design contract / inventory が同期済み
- test が実行済み
- test 結果が既存記録先へ反映済み
- sharedlog にしか残っていない重要変更が無い

## 失敗条件

- 更新対象文書を特定できない
- test を未実行のまま close しようとする
- 記録先が未確定のまま close しようとする

## Coordination

- 正本文書候補の特定には `references/doc-target-resolution-rule.md` を使う。
- 記録先の判断には `references/evidence-routing-rule.md` を使う。
- 必要なら `scripts/check_doc_sync_targets.py` と `scripts/check_evidence_targets.py` を補助的に使う。
