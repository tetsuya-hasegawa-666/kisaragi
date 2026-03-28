# remote-pwsh 製品 README

## 目的

この directory は `remote-pwsh` の運用 product を置くものとする。実行 script は `scripts/`、GUI fallback と desktop launcher は `apps/` に分けて管理するものとする。

## 構成

- `scripts/`
  - `Invoke-RemoteDoctor.ps1`
  - `Invoke-RemoteResume.ps1`
  - `Invoke-RemoteRecover.ps1`
  - `Invoke-GuidedRecover.ps1`
  - `RemoteRecovery.Common.ps1`
  - `Save-SlackCapture.ps1`
  - `Set-OpenSshPowerShellDefault.ps1`
  - `Test-OpenSshPowerShellEntry.ps1`
- `apps/`
  - `Deploy-DesktopShortcuts.ps1`
  - `OpenEvidenceFolder.cmd`
  - `RemoteDoctor.cmd`
  - `RemoteRecoverPreview.cmd`
  - `RemoteResume.cmd`

## 現在の見方

- `doctor` は `synceller` 側の `doctor.ps1` を呼ぶ wrapper として使うものとする。
- `resume` / `recover` は remote recovery contract 用の wrapper として使うものとする。
- `Invoke-GuidedRecover.ps1` は次の調査手順を案内する guided flow として使うものとする。
- `Save-SlackCapture.ps1` は `kisaragi-db/--exsams/prj-kisaragi_0003/captures/` へ残す capture の補助として使うものとする。
- `apps/` は GUI fallback と desktop launcher の入口として扱うものとする。

## 使用例

```powershell
pwsh -File .\scripts\Invoke-RemoteDoctor.ps1 -Format Table
pwsh -File .\scripts\Invoke-RemoteResume.ps1 -WhatIf
pwsh -File .\scripts\Invoke-RemoteRecover.ps1 -WhatIf
pwsh -File .\scripts\Set-OpenSshPowerShellDefault.ps1 -WhatIf
pwsh -File .\scripts\Test-OpenSshPowerShellEntry.ps1
```

## 以下をpwshで実行すると起動用アイコンがデスクトップに配置される

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0003\apps\Deploy-DesktopShortcuts.ps1
```

## スマホから Windows PC に入って使う場合の前提

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0003\scripts\Set-OpenSshPowerShellDefault.ps1
powershell -ExecutionPolicy Bypass -File C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0003\scripts\Test-OpenSshPowerShellEntry.ps1
```
