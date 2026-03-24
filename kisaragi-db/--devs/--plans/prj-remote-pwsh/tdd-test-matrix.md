# TDD テストマトリクス

この文書は、BDD terminal behavior に対する TDD 計画を管理する。

## TDD タスク

| task_id | behavior_id | test_target | criterion | status | evidence |
| --- | --- | --- | --- | --- | --- |
| `T1` | `B1` | mobile 到達要件表 | iPhone / Android / Windows の事前準備が 1 枚で読める | pass | `--process/--testlogs/prj-remote-pwsh/reports/` |
| `T2` | `B2` | SSH shell runbook | smartphone から Windows `PowerShell` を既定 shell で開く手順が定義されている | pass | `--process/--testlogs/prj-remote-pwsh/reports/20260320-153627-rr-20260320-153627-summary.md` |
| `T3` | `B3` | diagnosis wrapper | `Slack`、`Docker`、`PostgreSQL`、`Synceller`、`app-server` の状態を 1 command で返せる | pass | `--process/--testlogs/prj-remote-pwsh/logs/20260320-153627-rr-20260320-153627-doctor.json` |
| `T4` | `B4` | recovery wrapper | `doctor -> recover -> recheck` が安全順序で実行される | pass | `--process/--testlogs/prj-remote-pwsh/logs/20260320-183435-rr-20260320-183435-resume.json` |
| `T5` | `B5` | summary formatter | evidence path、失敗理由、次の判断を summary に含める | pass | `--process/--testlogs/prj-remote-pwsh/artifacts/20260320-153627-rr-20260320-153627-summary.json` |
| `T6` | `B6` | GUI fallback runbook | `RustDesk` から同じ recovery script を起動できる | pass | `--process/--testlogs/prj-remote-pwsh/artifacts/20260321-052408-rr-20260321-052408-summary.json` |
| `T7` | `B7` | decision matrix | 主系統優先と副系統移行条件が明文化されている | pass | `../../docs/process/decision_matrix.md` |
| `T8` | `B8` | post-recovery check | 復旧後に `/codex status` を確認する手順が evidence に含まれる | pass | `user-confirmed smartphone Slack capture at 2026-03-21 05:28 JST` |
| `T9` | `B2` | Termius setup manual | 初回設定で `Hostname`、password、`Use Telnet` で迷わない | pass | `../../docs/process/ssh_shell_runbook.md` |
| `T10` | `B9` | GUI launcher spec | GUI launcher の役割と起動対象が固定されている | pass | `../../docs/process/gui_launcher_runbook.md` |
| `T11` | `B9` | GUI launcher scripts | desktop 配置用 launcher script が用意されている | pass | `--process/--products/prj-remote-pwsh/apps/` |
| `T12` | `B4` | resume lock | `resume` の二重実行が lock で防止される | pass | `lock error observed at 2026-03-21 05:41 JST` |
| `T13` | `B5` | guided recovery | guided command が次の判断を含めて返す | pass | `--process/--testlogs/prj-remote-pwsh/artifacts/20260321-054028-rr-20260321-054028-summary.json` |
| `T14` | `B8` | capture save flow | Slack capture を evidence 配下に保存する導線がある | pass | `--process/--testlogs/prj-remote-pwsh/captures/20260321-084541-rr-20260321-084541-slack-status.png` |
| `T15` | `B4` | multi-session policy | 複数 session の役割分離が文書化されている | pass | `../../docs/process/multi_session_policy.md` |

## 実行方針

- 1 task 1 責務で進める
- `MRL-1` では `T1` から `T2` を先に固める
- `MRL-2` と `MRL-3` で shell 経路と recovery command の task を進める
- `MRL-4` は `T6` を中心に副系統を追加する

## 現在の見立て

- `T1` は `additional_info.md` の事前準備一覧と client 決定で pass 相当
- `T2` は `docs/process/ssh_shell_runbook.md` を正本にして具体化する
- `T3` は `--process/--products/prj-synceller/scripts/doctor.ps1` adapter 経由で pass
- `T4` は smartphone 導線で live execution 済み
- `T6` は GUI fallback の live validation まで完了
