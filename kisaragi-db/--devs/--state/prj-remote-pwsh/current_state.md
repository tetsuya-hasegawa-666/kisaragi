# 現在状態

- active plan set: `2026-03-20-001`
- active main release line: `done`
- active micro release line: `done`

## 決定済み

- `remote-pwsh` は `Synceller` 障害時の別系統 recovery project とする
- 主系統は `Tailscale + OpenSSH Server + PowerShell + Termius` とする
- 副系統は `Tailscale + RustDesk` とする
- 実装順序は、共有 recovery contract を先に定義し、その後は主系統を優先する
- iPhone / Android の SSH client は `Termius` に統一する
- operator 向け command 名は `doctor` / `resume` / `recheck` / `summary` とする
- `recover` は復旧経路全体の概念名として扱う
- Windows 側の既存 remote software 競合は `Moshi` 試験利用のみで、撤去可能と確認済み
- `remote-pwsh` から project 外の data を変更する場合は、先に user 確認を取る
- smartphone の `Termius` から Windows `PowerShell` へ接続できる
- `Invoke-RemoteResume.ps1` は `--process/--products/prj-synceller/scripts/resume.ps1` を呼び出して live 実行できる
- 復旧後に smartphone の `Slack` から `/codex status` を確認できる
- 拡張 UX 提案は `docs/artifact/remote-pwsh_add-vision.md` で管理する
- GUI fallback では launcher icon から recovery script を起動する拡張を許容する
- smartphone の `RustDesk` から Windows GUI に接続し、GUI 上の `PowerShell` で同じ recovery script を live 実行できる
- 拡張実装では `resume` lock、guided recovery、capture 保存導線を先に追加する

## 現在の blocker

- 現時点で active blocker はない

## 次の確認

- add vision の lock / guided UX / multi-session を次の計画へ昇格させるか判断する
- launcher の live desktop 配置を必要なら追加確認する

## 2026-03-24 作業所有権

- Codex が `AGENTS.md` への計画文書基準追記と、3 project の BDD / TDD plan 整合化を担当する

## 2026-03-22 sandbox 移行状況
- `prj-synceller` 側の script 正本 path は `codev-db/--process/--products/prj-synceller/scripts/` とする。
- test evidence path は `codev-db/--process/--testlogs/prj-remote-pwsh/` とする。
- 移行後に次の確認が通っている。
  - `Invoke-RemoteDoctor.ps1 -Format Table`
  - `Invoke-RemoteRecover.ps1 -WhatIf`
  - `prj-synceller` 側の `Invoke-OutOfBandDoctor.ps1 -Format Table`
- 移行判断と補足記録は `C:\Users\tetsuya\sandbox\codev-ruling\copy-plans-results\prj-remote-pwsh\copy-plans-results.md` を参照する。
