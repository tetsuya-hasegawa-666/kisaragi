---
name: docker-stability-operator
description: Docker ベースの project 環境を安定化する。Codex が Docker や compose の問題を診断するとき、壊れた runtime state を復旧するとき、project script 経由で起動経路を標準化するとき、または service を再利用可能な安定状態へ戻すときに使う。Docker 依存作業の前に使い、Docker 問題を実装の後ろへ送らない。
---

# Docker Stability Operator

Docker に依存する task では、問題がまだ出ていなくてもこの skill を使う。

## コアルール

次の task が Docker を必要とするなら、先に Docker を診断する。
Docker daemon、compose、service health の問題を無関係な実装作業の後ろへ送らない。

## 使う場面

- Docker 依存の実装や検証の前
- Docker Engine や Docker daemon の状態が不明なとき
- `docker compose` が失敗するとき
- service が unhealthy なとき
- runtime state が壊れている可能性があるとき
- Docker 起動の摩擦が繰り返し発生しているとき

## 手順

1. 対象 project を確認し、`infra/docker/`、`infra/scripts/`、project の Docker 方針を読む。
2. 先に診断する。
   - Docker Engine / Docker daemon
   - `docker compose`
   - `.env`
   - ports
   - mounts と volumes
   - service health
3. 障害を分類する。
   - host 障害
   - 設定障害
   - runtime 障害
   - state 障害
4. 次の順で復旧する。
   - 通常起動を再試行する
   - 失敗した service を再作成する
   - 影響 image を再 build する
   - project runtime state を reset する
   - project 側で解消できない host blocker のみ escalation する
5. stack を安定状態へ収束させる。
   - 必要 service が起動している
   - 必要 service が healthy である
   - 同じ script 経路で project を再起動できる
6. 診断結果、実施内容、最終状態、残リスクを記録する。

## 安定状態の条件

1 回 command が通っただけで Docker を usable と判断しない。
安定状態とは次を満たす状態を指す。

- Docker daemon に到達できる
- `docker compose config` が通る
- project の標準起動経路が通る
- 必要 service が healthy である
- 次の task でも同じ起動経路を再利用できる

## Project 慣例

- Docker file は `infra/docker/`
- runtime script は `infra/scripts/`
- 標準 script は次である
  - `doctor.ps1`
  - `up.ps1`
  - `down.ps1`
  - `reset.ps1`
  - `wait-healthy.ps1`

## 運用ルール

- 破壊的復旧の前に診断する
- 生の compose command より project script を優先する
- 可能なら影響 service だけを再 build する
- volume reset は runtime state 破損が疑われるときだけ行う
- Docker 依存作業では、Docker 不安定そのものが現在 task である
- 安定状態に到達したか、残っている host blocker が何かを明示して終える

## 参照

failure class と steady-state criteria は `references/recovery-patterns.md` を読む。
