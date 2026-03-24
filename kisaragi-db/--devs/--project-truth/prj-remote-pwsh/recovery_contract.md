# Shared Recovery Contract

## 目的

この文書は、主系統の shell recovery と副系統の GUI fallback が共通で使う recovery contract を定義する。

## 適用範囲

- 主系統: `Tailscale + OpenSSH Server + PowerShell + Termius`
- 副系統: `Tailscale + RustDesk`
- 実行場所: Windows 上の `--process/--products/prj-remote-pwsh/scripts/`

## 固定方針

- operator 向け command 名は `doctor`、`resume`、`recheck`、`summary` とする
- `recover` は経路全体を指す概念名としてのみ使う
- 主系統と副系統は同じ PowerShell script 群を呼ぶ
- すべての実行は `--process/--testlogs/prj-remote-pwsh/` に evidence を残す
- wrapper は `Slack`、`Docker`、`PostgreSQL`、`Synceller`、`app-server` を最低監視対象とする

## 実行順序

1. `doctor`
2. 必要時のみ `resume`
3. `recheck`
4. `summary`

`resume` 単体実行は許容するが、script 内では直前の `doctor` 結果がない場合に警告を返す。

## Command Surface

### `doctor`

- 役割: 監視対象の状態診断
- 入力:
  - `-SessionId`
  - `-EvidenceRoot`
  - `-Format` `json|table`
- 出力:
  - component ごとの status
  - degraded / down の一覧
  - 手動介入要否
  - evidence path

### `resume`

- 役割: 安全順序の復旧操作
- 入力:
  - `-SessionId`
  - `-EvidenceRoot`
  - `-WhatIf`
  - `-ResumeTarget`
- 出力:
  - 実行した復旧 step
  - 各 step の成功可否
  - 失敗理由
  - evidence path

### `recheck`

- 役割: `resume` 後の再診断
- 入力:
  - `-SessionId`
  - `-EvidenceRoot`
  - `-Format` `json|table`
- 出力:
  - `doctor` と同形式
  - 復旧前後差分

### `summary`

- 役割: operator 判断用の最終要約
- 入力:
  - `-SessionId`
  - `-EvidenceRoot`
- 出力:
  - overall status
  - 次の判断
  - manual intervention 要否
  - `/codex status` 再確認要否
  - evidence path 一覧

## Status Model

component status は次の 4 値に正規化する。

- `healthy`
- `degraded`
- `down`
- `unknown`

overall status は次の 3 値に正規化する。

- `ready`
- `needs_resume`
- `needs_manual_intervention`

## Safety Rules

- `resume` は対象 component ごとの手順を固定順序で実行する
- `resume` は global lock を取り、二重実行を拒否する
- `PostgreSQL` と `Docker` を巻き込む操作は `-WhatIf` で事前確認できるようにする
- destructive 操作は contract 外に置き、初期 contract には含めない
- 実 command 未接続の段階では dry-run と placeholder を返してもよい

## Evidence Layout

`--process/--testlogs/prj-remote-pwsh/` 配下に次を残す。

- `logs/<timestamp>-<session-id>-doctor.json`
- `logs/<timestamp>-<session-id>-resume.json`
- `logs/<timestamp>-<session-id>-recheck.json`
- `artifacts/<timestamp>-<session-id>-summary.json`
- `reports/<timestamp>-<session-id>-summary.md`

`timestamp` は `yyyyMMdd-HHmmss` とする。

## Session Rules

- 1 回の remote recovery 操作につき 1 つの `SessionId` を使う
- `SessionId` 未指定時は script 側で `rr-<timestamp>` を採番する
- 同一 session の evidence は追記ではなく別 file で残す
- action 系 command の lock owner は `SessionId` と hostname を残す

## 初期実装の範囲

- status 収集は PowerShell function に抽象化する
- `doctor` は `--process/--products/prj-synceller/scripts/doctor.ps1` を呼ぶ adapter を持ってよい
- 実 service command が未確定の component は placeholder 実装でよい
- evidence 出力と summary 形式を先に固定し、その後に本物の診断 command を差し替える
