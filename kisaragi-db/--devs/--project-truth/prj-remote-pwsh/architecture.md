# Architecture

## 構成

remote-pwsh は次の 4 要素で構成する。

1. Mobile Client
2. Secure Transport
3. Windows Control
4. Recovery Workflow

## Mobile Client

- iPhone / Android ともに SSH client は `Termius` で統一する
- GUI fallback では iPhone / Android ともに `RustDesk` を使う

## Secure Transport

- 主系統は `Tailscale` 上の SSH 到達を使う
- 副系統は `Tailscale` 上の `RustDesk` 到達を使う
- 公開ポート開放を前提にしない

## Windows Control

- Windows では `OpenSSH Server` を常駐させる
- 遠隔 shell の既定は `PowerShell` とする
- 復旧 command は `scripts/` に集約する
- GUI fallback では launcher icon または shortcut から同じ復旧 command を起動できる

## Recovery Workflow

- `doctor` を先に実行する
- `resume` を必要時のみ実行する
- `recheck` と `summary` を必ず返す
- 要約は `kisaragi-db/--devs/--testlogs/prj-remote-pwsh/` に、raw 生成物は `kisaragi-db/--exsams/prj-remote-pwsh/` に記録する
- `Synceller` の運用判断につながる summary を返す
- contract は `kisaragi-db/--devs/--project-truth/prj-remote-pwsh/recovery_contract.md` を正本とする

## 主系統と副系統

### 主系統

- `Tailscale + OpenSSH Server + PowerShell + Termius`
- もっとも少ない帯域と操作数で復旧できる
- `Synceller` と `Slack` の接続異常時に最初に使う

### 副系統

- `Tailscale + RustDesk`
- shell に入れない、あるいは GUI 操作が必要なときだけ使う
- 主系統の補助導線であり、常用経路にはしない

## 開発順序

- 共有 contract は先に 1 回だけ定義する
- その後は主系統を先に集中実装する
- 副系統は主系統の recovery contract が固まった後で並行化できる
- `OpenSSH Server` と `PowerShell` の既定 shell runbook を主系統実装の入口にする

## 理由

- 生命線として必要なのは GUI ではなく shell 到達である
- 主系統だけで大半の障害は扱える
- 副系統を先に作ると、復旧 command の contract が曖昧なまま GUI 操作に逃げやすい
