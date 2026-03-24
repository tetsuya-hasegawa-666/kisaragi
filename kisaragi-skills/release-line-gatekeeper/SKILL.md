---
name: release-line-gatekeeper
description: release-line の readiness と gate status（RL1-RL4）を評価する。system が次の release line へ進める状態か判断するときに使う。
---

# Release Line Gatekeeper

gate ごとに release readiness を評価するために使う。

## Workflow
1. release-line 定義を読む。
2. 各 line に必要な evidence を確認する。
3. 理由付きで pass / fail / blocked を付ける。
4. blocker を解消するための最小 action を報告する。

## 出力形式
- RL status table
- blocking item
- 次 action
