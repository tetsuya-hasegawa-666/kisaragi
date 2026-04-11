# doc target resolution rule

## 目的

- `script-doc-sync-enforcer` が、変更に関連する正本文書を過不足なく特定するための最小 rule とする。

## 基本 rule

- `READ` 下限は常に `project-truth.md` と `HAUB`
- `WRITE` は、`READ` した正本と、その変更内容に関連する文書

## resolution order

1. 変更対象 file の project を確定する
2. `project-truth.md` と `HAUB` を必須候補に置く
3. 対象 directory の `agents.md` を確認する
4. design contract / inventory の有無を確認する
5. shared rule 変更時だけ `AGENTS.md` と `AGENTSmd-RH.md` を追加する
6. admin 手順や evidence に影響する時だけ admin 系文書を追加する

## 典型追加先

| 変更内容 | 追加候補 |
| --- | --- |
| source-managed runbook 変更 | design contract、source inventory |
| path / contract 変更 | design contract、inventory、handoff 管理面 |
| gate / evidence 変更 | `codex-mrl-test-evidence.md`、`--testlogs/` |
| admin 操作変更 | `admin-mrl-test-method.md` |
| shared rule 変更 | `AGENTS.md`、`AGENTSmd-RH.md` |
