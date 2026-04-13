---
name: doc-target-resolver
description: code / notebook / runbook 変更から、同 task で更新すべき正本文書と補助文書を特定する child skill。文書更新漏れを避けたい時に使う。
---

# Doc Target Resolver

変更対象から、更新すべき文書群を洗い出す child skill とする。

## Input

- `working_files`
- `must_read_docs`
- `likely_write_docs`

## Output

- `doc_update_targets`
- `doc_sync_rationale`

## Guard Rails

- 正本と補助文書の優先順位を崩さない。
- 変更理由のない文書を広げすぎない。
- 逆に関連文書を取りこぼさない。

## Coordination

- `script-doc-sync-enforcer` と `documentation-watchkeeper` を補助する。
