---
name: runtime-structure-dependency-mapper
description: `import/呼び出し関係`、`path read/write`、`artifact producer/consumer`、`directory structure` を棚卸しし、計算環境依存の崩れを検知する specialist skill。発火判断は持たず、`skill-distributor` と `skill-planner` から依存整理担当として割り当てられた時だけ動く。
---

# Runtime Structure Dependency Mapper

実行時の path ずれ、read/write 不整合、artifact handoff 破綻、directory 構造の崩れを task 中に減らす specialist skill とする。

## Trigger Ownership

- この skill 自身は発火判断を持たない。
- `skill-distributor` が依存棚卸し対象を検知し、`skill-planner` が runtime / structure 依存整理担当として割り当てた時だけ動く。

## 受入前提

- 対象差分または変更対象一覧が handoff 済みであること
- 対象 project code または path が handoff 済みであること
- design contract または inventory の候補が渡されていること

## Core Workflow

1. 変更対象から dependency scan scope を確定する。
2. `project-truth.md`、`HAUB`、design contract、inventory、対象 directory の `agents.md` を読む。
3. `import/呼び出し関係` を棚卸しする。
4. `path read/write` を棚卸しする。
5. `artifact producer/consumer` を棚卸しする。
6. `directory structure` の変更有無を棚卸しする。
7. handoff matrix、probe、unittest がある時は関連更新と実行対象を確定する。
8. 不一致一覧を出し、必要な設計契約更新や probe 実行へ handoff する。

## 必須 READ

- 対象 project の `project-truth.md`
- 対象 project の `hi-ai-unified-blueprint.md`
- 対象 design contract
- 対象 inventory
- 対象 directory の `agents.md`

## 条件付き READ

- handoff matrix や probe がある時:
  - handoff matrix
  - contract probe
  - 関連 unittest
- external runtime を含む時:
  - bootstrap runbook
  - input / output contract 文書

## 必須 WRITE

- 依存変更があった code / notebook / runbook
- 依存変更を反映すべき design contract
- 依存変更を反映すべき inventory
- handoff matrix や probe がある時はその関連更新

## 完了条件

- `import/呼び出し関係` の影響が棚卸し済み
- `path read/write` の変更が管理面へ反映済み
- `artifact producer/consumer` の変更が inventory と関連文書へ反映済み
- `directory structure` 変更が `agents.md` や関連文書と矛盾していない
- 関連 probe / unittest の実行要否が確定している

## 失敗条件

- 依存棚卸しが途中で止まる
- handoff 契約と source の不一致を検知したのにそのまま先へ進む
- probe が必要なのに未実行のまま close しようとする

## Coordination

- 棚卸し範囲の定義には `references/dependency-scan-scope.md` を使う。
- runtime 契約確認には `references/runtime-contract-checklist.md` を使う。
- 補助 scan には `scripts/scan_path_artifact_refs.py` と `scripts/scan_import_call_refs.py` を使ってよい。
