---
name: authoritative-doc-guard
description: script、notebook、test、runbook、skill、shared rule 文書を編集する前後に、どの正本文書を先に読むべきか、どの正本文書へ事後反映が必要かを点検する。`AGENTS.md`、`project-truth.md`、`hi-ai-unified-blueprint.md` を shared / project の正本として扱い、sharedlogs を正本と誤認しないようにしたい時に使う。
---

# Authoritative Doc Guard

編集 task の前後で「どの正本を見るべきか」「どの正本更新が残っているか」を落とさないための skill とする。

## Workflow

1. 対象 path 群を集める。
   明示 path があればそれを使い、無ければ `git diff --name-only` などの変更候補を使う。
2. `scripts/check_authoritative_docs.py` を実行する。
3. 出力された `must_read_before` を先に確認する。
4. code / docs 編集後に同じ script を再実行し、`should_review_after` と `likely_update_targets` を確認する。
5. `sharedlogs_*` が出ても、それを正本扱いせず、対応する `AGENTS.md`、`project-truth.md`、`hi-ai-unified-blueprint.md`、必要なら admin / evidence 文書へ反映する。

## Guard Rails

- `sharedlogs_*` を authoritative doc として扱わない。
- shared rule 変更候補があるのに `AGENTS.md` を見ずに閉じない。
- project 配下の script / runbook / test を触ったのに `project-truth.md` と `HAUB` の両方を確認せずに閉じない。
- `HAUB` 更新後は `big-open` の有無を確認し、response で必要な明示を落とさない。

## Script

- `scripts/check_authoritative_docs.py`
  - 入力 path 群から shared / project 正本を推定する
  - `must_read_before`
  - `should_review_after`
  - `likely_update_targets`
  - `notes`
  を JSON で返す

## Typical Use

```powershell
python kisaragi-skills/authoritative-doc-guard/scripts/check_authoritative_docs.py `
  --workspace-root C:\Users\tetsuya\kisaragi `
  --path C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\colab\da3_increpose_sources\cells\08_09.py
```

## Close Condition

- 編集前に `must_read_before` を確認した
- 編集後に `should_review_after` を確認した
- `likely_update_targets` に残った正本文書の更新要否を判断した
