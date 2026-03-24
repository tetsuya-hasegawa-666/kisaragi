# Recorded_Release_Line

この文書は、active plan set の closeout 記録を残す。

## ルール

- `MRL` または `mRL` が `pass` になったら 1 entry を追加する
- entry には issue、cause、resolution、recurrence prevention、remaining work、evidence path を含める
- hands-on 結果は `../../hands-on_results/2026-03-20-001/` と対で管理する

## Entries

- record date: 2026-03-20
  target MRL: none
  target mRL: none
  gate change: initialized
  issue: remote recovery project の文書基線が未作成だった
  cause: `remote-pwsh` project 自体が新規だった
  resolution: project skeleton、BDD、TDD、MRL/mRL を作成した
  recurrence prevention: 以後は `kisaragi-db/--devs/` と `AGENTS.md` を source-of-truth として追加更新する
  remaining work: 実装と live validation は未着手
  evidence path: `../test_field/remote-pwsh-test/`
- record date: 2026-03-20
  target MRL: `MRL-1`
  target mRL: `mRL-1.1`
  gate change: `pass`
  issue: mobile / Windows の事前準備一覧と採用 app が未確定だった
  cause: iPhone / Android の client と既存 remote software 競合条件が未確定だった
  resolution: `Termius` 統一、`Moshi` 競合なし、個人 PC 前提を `ux_check_manual.md` に反映した
  recurrence prevention: app 選定と host 制約は `additional_info.md` に集約してから次の mRL に進む
  remaining work: live install と host config 適用
  evidence path: `../additional_info.md`
- record date: 2026-03-20
  target MRL: `MRL-1`
  target mRL: `mRL-1.2`
  gate change: `pass`
  issue: 主系統と副系統で共有する recovery contract が未定義だった
  cause: `doctor`、`resume`、evidence 仕様が文書で固定されていなかった
  resolution: `kisaragi-db/--devs/--project-truth/prj-remote-pwsh/recovery_contract.md` を新設し、command surface と evidence layout を固定した
  recurrence prevention: contract 変更は `recovery_contract.md` を先に更新する
  remaining work: `Synceller` 実 runtime command の接続
  evidence path: `kisaragi-db/--devs/--project-truth/prj-remote-pwsh/recovery_contract.md`
- record date: 2026-03-20
  target MRL: `MRL-1`
  target mRL: `mRL-1.3`
  gate change: `pass`
  issue: BDD / TDD と current state が新しい前提に追随していなかった
  cause: client 決定、用語統一、runbook 入口が文書へ反映されていなかった
  resolution: BDD、TDD、change protocol、current state、docs index を更新した
  recurrence prevention: project truth 変更時は `documentation-watchkeeper` 手順で関連文書を同時更新する
  remaining work: shell 到達の live validation
  evidence path: `kisaragi-db/--devs/--state/prj-remote-pwsh/current_state.md`
- record date: 2026-03-20
  target MRL: `MRL-1`
  target mRL: none
  gate change: `pass`
  issue: Recovery Contract Baseline を実装へ接続する入口がなかった
  cause: docs 基線のみで、contract と script skeleton が未作成だった
  resolution: `MRL-1` を pass とし、`MRL-2` 開始に必要な runbook と script 入口を作成した
  recurrence prevention: `MRL` closeout 時は `UX_MRL-<number>.md` と evidence を同時に残す
  remaining work: `mRL-2.2` の default shell 固定と live validation
  evidence path: `../../hands-on_results/2026-03-20-001/UX_MRL-1.md`
- record date: 2026-03-20
  target MRL: `MRL-2`
  target mRL: `mRL-2.1`
  gate change: `pass`
  issue: mobile から Windows への private path 設計が runbook 化されていなかった
  cause: `Termius` 前提の host profile と Tailscale reachability 手順が未記載だった
  resolution: `ux_check_manual.md` に接続 profile と reachability を記載した
  recurrence prevention: 主系統の到達条件は runbook を正本にする
  remaining work: host への config 適用と実接続確認
  evidence path: `kisaragi-db/--devs/--evidence/prj-remote-pwsh/ux_check_manual.md`
- record date: 2026-03-20
  target MRL: `MRL-2`
  target mRL: `mRL-2.3`
  gate change: `pass`
  issue: iPhone / Android の接続 profile が OS ごとに分散していた
  cause: SSH client を統一する前提が文書に固定されていなかった
  resolution: `Termius` 統一前提の profile を runbook に固定した
  recurrence prevention: mobile client の採用決定は `additional_info.md` と runbook の両方で管理する
  remaining work: `Termius` 実 profile での live validation
  evidence path: `kisaragi-db/--devs/--evidence/prj-remote-pwsh/ux_check_manual.md`
- record date: 2026-03-20
  target MRL: `MRL-3`
  target mRL: `mRL-3.1`
  gate change: `pass`
  issue: `remote-pwsh` の diagnosis wrapper が `synceller` 実 runtime に未接続だった
  cause: `doctor` は placeholder 実装のみで、既存 `synceller` script を再利用していなかった
  resolution: `remote-pwsh/infra/scripts/RemoteRecovery.Common.ps1` から `synceller/infra/scripts/doctor.ps1` を呼ぶ adapter を追加した
  recurrence prevention: 既存 project に同名運用 script がある場合は wrapper から再利用する
  remaining work: `resume` の live execution と smartphone 導線確認
  evidence path: `../../../test_field/remote-pwsh-test/logs/20260320-153627-rr-20260320-153627-doctor.json`
- record date: 2026-03-20
  target MRL: `MRL-3`
  target mRL: `mRL-3.3`
  gate change: `pass`
  issue: recovery contract の evidence layout は文書化されていたが、実 file 出力が未実装だった
  cause: wrapper script が JSON / Markdown の出力を持っていなかった
  resolution: `doctor`、`resume`、`recheck`、`summary` の evidence を `test_field/remote-pwsh-test/` に出力するようにした
  recurrence prevention: contract 変更時は evidence layout と script 出力を同時に更新する
  remaining work: `/codex status` capture を evidence に含める
  evidence path: `../../../test_field/remote-pwsh-test/artifacts/20260320-153627-rr-20260320-153627-summary.json`
- record date: 2026-03-20
  target MRL: none
  target mRL: none
  gate change: rule added
  issue: `remote-pwsh` から project 外の data を変更する境界が明文化されていなかった
  cause: wrapper 実装を進める中で、外部 project 参照と変更の境界が文書に固定されていなかった
  resolution: project 外の変更は user 確認がある場合のみ許可するルールを `AGENTS.md` に追加した
  recurrence prevention: `remote-pwsh` 外を変更する前に user 確認の有無を確認し、未確認なら停止する
  remaining work: 既存 wrapper で外部参照のみ行う範囲を維持する
  evidence path: `AGENTS.md`
- record date: 2026-03-20
  target MRL: `MRL-2`
  target mRL: `mRL-2.2`
  gate change: `pass`
  issue: smartphone から Windows `PowerShell` に入る live validation が未完だった
  cause: `OpenSSH DefaultShell` と SSH 認証の host 側確認が終わっていなかった
  resolution: `Termius` から Windows に接続し、remote shell 上で `Invoke-RemoteDoctor.ps1` を実行できることを確認した
  recurrence prevention: SSH 導線の初回確認では network / auth / shell を分けて切り分ける
  remaining work: GUI fallback の接続検証
  evidence path: `kisaragi-db/--devs/--evidence/prj-remote-pwsh/ux_check_manual.md`
- record date: 2026-03-20
  target MRL: `MRL-2`
  target mRL: none
  gate change: `pass`
  issue: Primary Mobile Shell Path の実地確認が未完だった
  cause: docs と script 骨格はあったが、smartphone 導線の実接続が未確認だった
  resolution: `Termius` 接続、`doctor` 実行、`resume` 実行まで smartphone から通した
  recurrence prevention: MRL closeout 前に live path の最小操作を 1 回通す
  remaining work: GUI fallback と運用判断 runbook
  evidence path: `../../../test_field/remote-pwsh-test/logs/20260320-183435-rr-20260320-183435-resume.json`
- record date: 2026-03-20
  target MRL: `MRL-3`
  target mRL: `mRL-3.2`
  gate change: `pass`
  issue: recovery wrapper の live execution が未確認だった
  cause: `resume` は wrapper から `synceller` 実 runtime を呼べるだけで、実行証跡がなかった
  resolution: smartphone から `Invoke-RemoteResume.ps1` を実行し、全 target が completed になることを確認した
  recurrence prevention: wrapper を active 扱いにする間は live execution を 1 回残す
  remaining work: GUI fallback と capture 運用の固定
  evidence path: `../../../test_field/remote-pwsh-test/logs/20260320-183435-rr-20260320-183435-resume.json`
- record date: 2026-03-20
  target MRL: `MRL-3`
  target mRL: none
  gate change: `pass`
  issue: Recovery Command Path の end-to-end 確認が未完だった
  cause: `resume` 実行後の `doctor` healthy と `/codex status` 再疎通が未確認だった
  resolution: `doctor` healthy、`Invoke-RemoteRecover.ps1 -WhatIf` の summary ready、smartphone の `/codex status` 応答を確認した
  recurrence prevention: 今後は `doctor -> resume -> doctor -> /codex status` を 1 セットで closeout する
  remaining work: Slack capture の定型保存と GUI fallback
  evidence path: `../../../test_field/remote-pwsh-test/artifacts/20260320-183559-rr-20260320-183559-summary.json`
- record date: 2026-03-20
  target MRL: `MRL-3`
  target mRL: none
  gate change: `pass`
  issue: Recovery Command Path 全体の closeout 記録が current gate に反映されていなかった
  cause: MRL-3 の各 mRL を pass にした後、MRL gate 更新が未反映だった
  resolution: `MRL-3` を pass とし、`MRL-4` と `MRL-5` の docs work を active に更新した
  recurrence prevention: 全 mRL pass 時に必ず MRL gate も更新する
  remaining work: GUI fallback と long-idle recovery の live validation
  evidence path: `../../../test_field/remote-pwsh-test/artifacts/20260320-183559-rr-20260320-183559-summary.json`
- record date: 2026-03-20
  target MRL: `MRL-5`
  target mRL: `mRL-5.1`
  gate change: `pass`
  issue: 主系統優先と手動介入条件の判断基準が会話内に散っていた
  cause: operator がどの時点で GUI fallback や手動介入に切り替えるかを 1 枚で参照できなかった
  resolution: `ux_check_manual.md` に主系統継続と GUI fallback の分岐条件を追加した
  recurrence prevention: 新しい障害分岐が出たら decision matrix を先に更新する
  remaining work: long-idle recovery の live 確認
  evidence path: `kisaragi-db/--devs/--evidence/prj-remote-pwsh/ux_check_manual.md`
- record date: 2026-03-20
  target MRL: none
  target mRL: none
  gate change: manual improved
  issue: `Termius` 初回設定で `Hostname`、password、`Use Telnet` の意味が不明確だった
  cause: runbook が概念説明寄りで、端末別の一意手順と FAQ が不足していた
  resolution: `ux_check_manual.md` に実設定マニュアルを追記した
  recurrence prevention: mobile app 設定で聞き返しが発生した場合は runbook に FAQ を即時追加する
  remaining work: GUI fallback 側でも同じ粒度の初回設定マニュアルを整える
  evidence path: `kisaragi-db/--devs/--evidence/prj-remote-pwsh/ux_check_manual.md`
- record date: 2026-03-21
  target MRL: none
  target mRL: none
  gate change: vision added
  issue: remote-pwsh の将来 UX と multi-session 活用像が既存 BDD の外にあり、文書化されていなかった
  cause: recovery 専用の設計に集中しており、平常時の継続利用や fail-safe / fool-proof 拡張が別文書化されていなかった
  resolution: `kisaragi-db/--devs/--project-truth/prj-remote-pwsh/remote-pwsh_add-vision.md` を追加し、story ベースで拡張 UX、かたい設計、guided UX を提案した
  recurrence prevention: 新しい応用活用や UX 提案は artifact の追加 vision 文書で先に受ける
  remaining work: 提案のうち lock 設計と multi-session ルールを正本へ昇格させる判断
  evidence path: `kisaragi-db/--devs/--project-truth/prj-remote-pwsh/remote-pwsh_add-vision.md`
- record date: 2026-03-21
  target MRL: `MRL-6`
  target mRL: `mRL-6.1`
  gate change: `pass`
  issue: GUI fallback で command 手入力が前提だと操作性が落ちる
  cause: launcher icon を使う設計が runbook と release map に存在しなかった
  resolution: `gui_launcher_runbook.md` を追加し、launcher spec を正本化した
  recurrence prevention: GUI 操作を前提にする UX は launcher 化の可否を先に判断する
  remaining work: live desktop 配置の実地確認
  evidence path: `kisaragi-db/--devs/--evidence/prj-remote-pwsh/ux_check_manual.md`
- record date: 2026-03-21
  target MRL: `MRL-4`
  target mRL: `mRL-4.1`
  gate change: `pass`
  issue: smartphone から `RustDesk` で Windows GUI に入る live validation が未完だった
  cause: GUI fallback は runbook 化のみで実機確認がなかった
  resolution: smartphone の `RustDesk` から Windows に接続し、GUI 上で recovery script を実行した
  recurrence prevention: GUI fallback は runbook と live path を対で確認する
  remaining work: `/codex status` capture の定型保存
  evidence path: `../../../test_field/remote-pwsh-test/logs/20260321-052408-rr-20260321-052408-doctor.json`
- record date: 2026-03-21
  target MRL: `MRL-4`
  target mRL: `mRL-4.2`
  gate change: `pass`
  issue: GUI fallback から主系統と同じ recovery script を起動できるか未確認だった
  cause: launcher / PowerShell 入口のどちらでも実地証跡がなかった
  resolution: GUI 上の `PowerShell` で `Invoke-RemoteResume.ps1` と `Invoke-RemoteRecover.ps1 -WhatIf` を実行し、summary ready を確認した
  recurrence prevention: GUI fallback closeout では `doctor -> resume -> doctor -> recover preview` を 1 セットで残す
  remaining work: `/codex status` capture の定型保存
  evidence path: `../../../test_field/remote-pwsh-test/artifacts/20260321-052408-rr-20260321-052408-summary.json`
- record date: 2026-03-21
  target MRL: `MRL-4`
  target mRL: none
  gate change: `pass`
  issue: Secondary GUI Fallback 全体の closeout が未反映だった
  cause: mRL-4.1 と mRL-4.2 の pass 後に MRL gate 更新が未実施だった
  resolution: `MRL-4` を pass に更新した
  recurrence prevention: 各 mRL pass 後に MRL gate を即時更新する
  remaining work: `MRL-5.2` の capture 運用
  evidence path: `../../../test_field/remote-pwsh-test/artifacts/20260321-052408-rr-20260321-052408-summary.json`
- record date: 2026-03-21
  target MRL: `MRL-5`
  target mRL: `mRL-5.2`
  gate change: `pass`
  issue: `/codex status` の smartphone capture を closeout evidence に含める運用が未確認だった
  cause: Slack 応答確認は実施済みだったが、capture を closeout 記録に反映していなかった
  resolution: smartphone の `Slack` から `/codex status` 応答 capture を確認し、post-recovery check を closeout した
  recurrence prevention: 今後は `/codex status` の応答 capture を MRL-5 closeout 条件に含める
  remaining work: capture の file 保存自動化が必要なら別 task 化する
  evidence path: `user-confirmed smartphone Slack capture at 2026-03-21 05:28 JST`
- record date: 2026-03-21
  target MRL: `MRL-5`
  target mRL: none
  gate change: `pass`
  issue: Remote Recovery Operations 全体の closeout が未反映だった
  cause: `mRL-5.1` pass 後に `mRL-5.2` の live capture が未完だった
  resolution: `mRL-5.2` を pass とし、`MRL-5` を pass に更新した
  recurrence prevention: operations 系 gate は decision matrix と live capture の両方がそろってから閉じる
  remaining work: add vision の拡張提案を別計画へ昇格させるか判断する
  evidence path: `kisaragi-db/--devs/--evidence/prj-remote-pwsh/ux_check_manual.md`
- record date: 2026-03-21
  target MRL: `MRL-7`
  target mRL: `mRL-7.1`
  gate change: `pass`
  issue: `resume` の二重実行防止が運用ルール依存だった
  cause: wrapper script に排他制御がなかった
  resolution: atomic file create を使う global lock を `RemoteRecovery.Common.ps1` に追加した
  recurrence prevention: action 系 command は lock を前提に設計する
  remaining work: multi-session policy と capture 保存導線の live closeout
  evidence path: `lock error observed at 2026-03-21 05:41 JST`
- record date: 2026-03-21
  target MRL: `MRL-7`
  target mRL: `mRL-7.2`
  gate change: `pass`
  issue: guided recovery UX が未実装で、operator が次の判断を script に委ねられなかった
  cause: wrapper は個別 command のみで guided flow がなかった
  resolution: `Invoke-GuidedRecover.ps1` を追加し、guided flow と summary ready を返すようにした
  recurrence prevention: operator 向け導線には guided command を先に用意する
  remaining work: screenshot capture の live 取り込み
  evidence path: `../../../test_field/remote-pwsh-test/artifacts/20260321-054028-rr-20260321-054028-summary.json`
- record date: 2026-03-21
  target MRL: `MRL-7`
  target mRL: `mRL-7.3`
  gate change: `pass`
  issue: smartphone screenshot を evidence 配下へ保存する導線が live 未確認だった
  cause: probe file での確認に留まり、実画像 file の取り込みが未実施だった
  resolution: `Save-SlackCapture.ps1` で smartphone の Slack screenshot を `captures/` 配下へ保存できることを確認した
  recurrence prevention: capture 保存導線は probe file だけでなく実画像 file で 1 回確認する
  remaining work: add vision の拡張項目を別計画へ昇格させるか判断する
  evidence path: `../../../test_field/remote-pwsh-test/captures/20260321-084541-rr-20260321-084541-slack-status.png`
- record date: 2026-03-21
  target MRL: `MRL-7`
  target mRL: none
  gate change: `pass`
  issue: Safe Guided Operations 全体の closeout が未反映だった
  cause: capture 保存導線の live 確認待ちだった
  resolution: `MRL-7` を pass に更新した
  recurrence prevention: lock / guided / capture の 3 点がそろってから guided operations を closeout する
  remaining work: add vision の次期計画化
  evidence path: `../../../test_field/remote-pwsh-test/captures/20260321-084541-rr-20260321-084541-slack-status.png`
