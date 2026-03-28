# admin-mrl-test-evidence

## MRL-1

## 到達点

`MRL-1 Recovery Contract Baseline` は pass。
operator は、主系統と副系統がどの contract を共有するか、どの script を入口にするか、どこへ evidence を残すかを文書と script 骨格の両方で追える。

## 現時点で触れる価値

1. `kisaragi-db/--devs/--project-truth/prj-kisaragi_0003/recovery_contract.md` を見れば、`doctor -> resume -> recheck -> summary` の contract と evidence 仕様が 1 枚で読める
2. `kisaragi-db/--devs/--evidence/prj-kisaragi_0003/admin-mrl-test-method.md` を見れば、`Termius` から Windows `PowerShell` に入るための運用手順を追える
3. `scripts/Invoke-RemoteRecover.ps1 -WhatIf` を実行すると、summary は `kisaragi-db/--devs/--testlogs/prj-kisaragi_0003/` に、raw evidence は `kisaragi-db/--exsams/prj-kisaragi_0003/` に残る

## 残タスク

- GUI fallback の live 導線を確認する
- 主系統と副系統の切替判断を runbook 化する
- `resume` 後の `/codex status` 再疎通確認を evidence に入れる

## Evidence

- `kisaragi-db/--devs/--project-truth/prj-kisaragi_0003/recovery_contract.md`
- `kisaragi-db/--devs/--evidence/prj-kisaragi_0003/admin-mrl-test-method.md`
- `kisaragi-db/--exsams/prj-kisaragi_0003/artifacts/20260320-153627-rr-20260320-153627-summary.json`

## MRL-3

## 到達点

`MRL-3 Recovery Command Path` は pass。
operator は smartphone の `Termius` から `doctor`、`resume`、`recheck` を通し、最後に smartphone の `Slack` で `/codex status` を確認できる。

## 現時点で触れる価値

1. `Invoke-RemoteResume.ps1` から `C:/Users/tetsuya/sandbox/codev-db/--process/--products/prj-synceller/scripts/resume.ps1` を呼び、live recovery を実行できる
2. `Invoke-RemoteDoctor.ps1` は `Slack`、`Docker`、`PostgreSQL`、`Synceller`、`app-server` を healthy で返せる
3. `Invoke-RemoteRecover.ps1 -WhatIf` は ready summary と evidence path を返し、次の確認が `/codex status` であることを明示できる

## 残タスク

- `/codex status` の capture を `kisaragi-db/--exsams/prj-kisaragi_0003/captures/` に定型保存する
- GUI fallback の reachability と共通 script 起動を確認する
- 主系統優先と手動介入の decision matrix を runbook 化する

## Evidence

- `kisaragi-db/--exsams/prj-kisaragi_0003/logs/20260320-183435-rr-20260320-183435-resume.json`
- `kisaragi-db/--exsams/prj-kisaragi_0003/logs/20260320-183559-rr-20260320-183559-doctor.json`
- `kisaragi-db/--exsams/prj-kisaragi_0003/artifacts/20260320-183559-rr-20260320-183559-summary.json`

## MRL-4

## 到達点

`MRL-4 Secondary GUI Fallback` は pass。
operator は smartphone の `RustDesk` から Windows GUI に入り、GUI 上の `PowerShell` で主系統と同じ recovery script を実行できる。

## 現時点で触れる価値

1. SSH が使えなくても `RustDesk` から同じ recovery contract を使える
2. GUI 上で `doctor`、`resume`、`recover preview` を順に実行できる
3. summary が `ready` を返し、次の行動が `/codex status` だと分かる

## 残タスク

- `/codex status` の capture を `captures/` に定型保存する
- GUI launcher の live desktop 配置を必要なら確認する
- long-idle recovery の closeout を残す

## Evidence

- `kisaragi-db/--exsams/prj-kisaragi_0003/logs/20260321-052306-rr-20260321-052306-resume.json`
- `kisaragi-db/--exsams/prj-kisaragi_0003/artifacts/20260321-052408-rr-20260321-052408-summary.json`

## MRL-5

## 到達点

`MRL-5` は文書基線まで前進した。
operator は主系統継続、副系統移行、手動介入の判断を `decision_matrix.md` で追える。

## 現時点で触れる価値

1. `kisaragi-db/--devs/--evidence/prj-kisaragi_0003/admin-mrl-test-method.md` を見れば、SSH 継続と GUI fallback の切替判断を含む運用手順が追える
2. 同文書を見れば、`Termius` 初回設定で詰まりやすい点を回避できる
3. 同文書を見れば、`RustDesk` で同じ recovery script を呼ぶ手順が分かる

## 残タスク

- `RustDesk` の live 接続確認
- GUI 上で same script invocation を実行した evidence
- long-idle recovery と `/codex status` capture の定型保存

## Evidence

- `kisaragi-db/--devs/--evidence/prj-kisaragi_0003/admin-mrl-test-method.md`
- `kisaragi-db/--devs/--evidence/prj-kisaragi_0003/admin-mrl-test-method.md`
- `kisaragi-db/--devs/--evidence/prj-kisaragi_0003/admin-mrl-test-method.md`

## MRL-5-closeout

## 到達点

`MRL-5 Remote Recovery Operations` は pass。
operator は smartphone の `Termius` または `RustDesk` から recovery を実行し、最後に smartphone の `Slack` で `/codex status` を確認できる。

## 現時点で触れる価値

1. 主系統と副系統の両方で recovery path を通せる
2. `doctor`、`resume`、`recover preview`、`/codex status` を end-to-end で確認できる
3. decision matrix に沿って、主系統継続、GUI fallback、手動介入を判断できる

## 残タスク

- add vision の lock / guided UX / multi-session を正本へ昇格させるか判断する
- GUI launcher の live desktop 配置を必要なら確認する
- `/codex status` capture の file 保存自動化を必要なら追加する

## Evidence

- `kisaragi-db/--exsams/prj-kisaragi_0003/artifacts/20260321-052408-rr-20260321-052408-summary.json`
- `user-confirmed smartphone Slack capture at 2026-03-21 05:28 JST`

## MRL-7

## 到達点

`MRL-7 Safe Guided Operations` は pass。
operator は `resume` の二重実行を lock で避けつつ、guided command と screenshot capture 保存導線を使って closeout できる。

## 現時点で触れる価値

1. `Invoke-GuidedRecover.ps1` が guided flow と次の判断を返す
2. `resume` は lock により二重実行を拒否できる
3. smartphone の `/codex status` screenshot を `captures/` に evidence として保存できる

## 残タスク

- add vision の multi-session / guided UX を次期 plan として昇格させるか判断する
- launcher の live desktop 配置を必要なら確認する

## Evidence

- `kisaragi-db/--exsams/prj-kisaragi_0003/artifacts/20260321-054028-rr-20260321-054028-summary.json`
- `kisaragi-db/--exsams/prj-kisaragi_0003/captures/20260321-084541-rr-20260321-084541-slack-status.png`
