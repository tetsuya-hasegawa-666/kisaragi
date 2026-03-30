---
name: runtime-operator
description: branch 同期、Docker 安定化、FastAPI 実装運用をまとめて扱う。repository runtime と service runtime の両方を安定状態へそろえるときに使う。
---

# Runtime Operator

runtime を、`git branch / container / app server` をまたいで安定化するための skill とする。

## 吸収した観点

- `branch-sync-operator` の branch head 同期と hash 確認
- `docker-stability-operator` の daemon / compose / health 診断
- `fastapi` の CLI、entrypoint、実装規約

## Workflow

1. 対象 runtime が branch、Docker、FastAPI のどれに依存するかを特定する。
2. branch が関係する時は remote head と hash を確認する。
3. Docker が関係する時は daemon、compose、health、port、volume を先に診断する。
4. FastAPI が関係する時は entrypoint、CLI、parameter style、app 構成を確認する。
5. 安定状態へ収束させた後、再利用できる起動経路と残リスクを記録する。

## 安全規則

- 明示指示なしで破壊的 branch 同期を行わない。
- Docker 障害を実装作業の後ろへ送らない。
- FastAPI は、可能なら `pyproject.toml` entrypoint と `Annotated` style を優先する。

## 参照

- `scripts/show_hashes.py`
- `references/fastapi/`
