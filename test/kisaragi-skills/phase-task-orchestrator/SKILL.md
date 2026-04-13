---
name: phase-task-orchestrator
description: `skill-planner` から呼ばれた時に、複数 task 開発依頼を phase 構成へ分解し、authoritative context、設計確定、実装、文書同期、検証、closeout を崩さず進める phase specialist。発火判断は持たず、phase 化と完了条件固定だけを担当する。
---

# Phase Task Orchestrator

長い依頼を 1 塊で処理せず、phase ごとの checkpoint を先に固定してから進めるための skill とする。

## Trigger Ownership

- この skill 自身は発火判断を持たない。
- `skill-planner` が multi-phase 管理が必要と判断した時だけ呼ばれる。

## Core Workflow

1. 依頼全体を 1 行で言い換える。
2. `scripts/check_authoritative_docs.py` を使い、事前に読むべき authoritative doc と事後に見直すべき文書候補を洗う。
3. authoritative context を固定する。
   - shared rule
   - project truth / plan
   - 関連 contract / inventory / manual
   - 正本扱いしない worklog / evidence
4. task header を作る。
   少なくとも `Goal`、`Authoritative`、`Working files`、`Do not treat as truth`、`Close condition` を置く。
5. phase を切る。
   既定は次の 5 phase とする。
   - `Phase 1`: authoritative context 確定
   - `Phase 2`: 設計確定と参照面棚卸し
   - `Phase 3`: code / docs 編集
   - `Phase 4`: probe / test / link check
   - `Phase 5`: evidence / closeout
6. 各 phase の完了条件を書く。
   phase 完了条件が無いまま次へ進まない。
7. phase ごとに未解決と非対象を書く。
   今回やらないことを明示し、暗黙の期待を減らす。
8. 実編集に入る前に、先に `Phase 1` と `Phase 2` を commentary で宣言する。
9. 長い task では、phase 完了ごとに「何が確定したか」「次の phase は何か」を短く再宣言する。

## Default Phase Template

```text
Task Header
- Goal:
- Authoritative:
- Working files:
- Do not treat as truth:
- Close condition:

Phase 1: authoritative context 確定
- 完了条件:

Phase 2: 設計確定と参照面棚卸し
- 完了条件:

Phase 3: code / docs 編集
- 完了条件:

Phase 4: probe / test / link check
- 完了条件:

Phase 5: evidence / closeout
- 完了条件:
```

## Typical Use

- 1 回の依頼に design、implementation、docs、verification、push が混ざる時
- admin が「全部まとめてやってほしい」と依頼する時
- notebook / runbook / contract / test が同時に動く時
- 設計変更で参照切替が入り、文書同期まで同 task で閉じたい時
- 中断再開が多く、今どの段階かを毎回再固定したい時

## Guard Rails

- `Phase 1` を飛ばして編集を始めない。
- `Phase 2` の設計確定前に rename や大きい refactor を始めない。
- `Phase 3` で code だけ直して文書同期を別 task へ逃がさない。
- `Phase 4` を省略して「たぶん大丈夫」で閉じない。
- `Phase 5` で evidence path や close 条件を書かずに終えない。
- 1 phase の中で複数の大論点を増殖させない。
- `sharedlogs_*` を authoritative doc と誤認しない。

## Coordination With Other Skills

- `skill-planner` から呼ばれる phase specialist とする。
- 設計変更や関数責務整理がある時は `design-first-script-builder` を `Phase 2` から併用する。
- path / contract / output 名の切替がある時は `reference-rewire-operator` を `Phase 2` から併用する。
- 文書 drift を閉じる時は `documentation-watchkeeper` を `Phase 3` 以降で使う。
- BDD / TDD / gate 更新が主題の時は `delivery-planning-keeper` を `Phase 2` または `Phase 5` で併用する。

## Minimum Deliverables

- task header
- authoritative doc check 結果
- phase 一覧
- phase ごとの完了条件
- 非対象または未解決
- 最終検証結果

## When To Read References

- prompt ひな形が必要な時は `references/phase-task-template.md` を読む。
- phase の粒度や省略条件で迷う時だけ読み直せばよい。

## Script

- `scripts/check_authoritative_docs.py`
  - 編集前の `must_read_before`
  - 編集後の `should_review_after`
  - `likely_update_targets`
  を機械的に洗い出す
