# hi-ai-unified-blueprint (HAUB)

## current_state

### 疑問点不整合一覧

| id | 論点 | 影響 | 現在の扱い | admin 状態 | 関連文書 |
| --- | --- | --- | --- | --- | --- |
| `ISS-001` | add vision の lock / guided UX / multi-session を次期計画へ昇格するか | 次期 MRL の範囲 | 現在は参考文書に保持し、採用時に別計画化する | `small-open` | `project-truth.md`, `remote-pwsh_add-vision.md` |

### 現在の重点

- `MRL-1` から `MRL-7` は `pass`
- main focus は主系統と副系統の運用維持、launcher 導線、capture 保存導線の継続性である
- add vision は参考情報として保持し、即時の正本には昇格しない

## BDD

### 目的文

- `prj-kisaragi_0003` の remote recovery UX、`Purpose Story`、`System Behaviors`、`MRL` 対応をまとめる。

### ノーススター

- operator は smartphone から Windows PC を遠隔監視操作し、`Synceller` と `Slack` の接続異常を復旧して Codex 開発継続に戻れる。

### 提供方針

- shared recovery contract を先に固める
- 生命線である主系統を優先する
- 副系統は主系統の contract 完了後に並行化してよい

### Purpose Story

- `s1`: operator は iPhone または Android から Windows PC に private path で到達できる
- `s2`: operator は smartphone から Windows `PowerShell` を使える
- `s3`: operator は `Synceller` と周辺依存の状態を remote で診断できる
- `s4`: operator は remote から復旧 command を実行できる
- `s5`: operator は主系統が使えない場合に副系統へ切り替えられる
- `s6`: operator は復旧後に Slack から Codex 開発継続へ戻れる
- `s7`: operator は GUI fallback で launcher icon から recovery action を起動できる
- `s8`: operator は複数 session を安全に使い分けられる
- `s9`: operator は guided command と capture 保存導線で closeout を迷わない

### System Behaviors

- `b1`: operator は iPhone または Android から Windows へ private path で到達できる
- `b2`: 主系統では mobile から `PowerShell` shell を直接開ける
- `b3`: 主系統の 1 command で `doctor` 相当の状態診断を返せる
- `b4`: 主系統の 1 command で `resume` を安全順序で実行できる
- `b5`: 主系統の実行結果は evidence path と次の判断を返せる
- `b6`: 副系統では GUI から同じ recovery script を実行できる
- `b7`: operator は主系統と副系統の切替条件を判断できる
- `b8`: 復旧後、Slack の `/codex status` で再疎通確認できる
- `b9`: GUI fallback では launcher icon から `doctor` / `resume` / `recover preview` を起動できる

### 受け入れ基準

| s-id | b-id | 観点 | 受け入れ基準 |
| --- | --- | --- | --- |
| `s1` | `b1` | reachability | iPhone と Android の両方に到達手順と認証前提が定義されている |
| `s2` | `b2` | shell entry | smartphone から Windows `PowerShell` を既定 shell として開ける |
| `s3` | `b3` | diagnosis | 診断 command が `Slack`、`Docker`、`PostgreSQL`、`Synceller`、`app-server` の状態を返す |
| `s4` | `b4`,`b5` | recovery | 復旧 command が安全順序で動き、evidence path と次の判断を返す |
| `s5`,`s7` | `b6`,`b7`,`b9` | fallback | GUI fallback と launcher icon から同じ recovery contract を使える |
| `s6`,`s9` | `b8` | closeout | `/codex status` 確認と capture 保存導線が UX と evidence に含まれる |

### MRL 対応表

| MRL | mRL | 目的 | 関連 s-id | 関連 b-id | 現在 gate |
| --- | --- | --- | --- | --- | --- |
| `MRL-1` | `mRL-1.1` | 環境インベントリ | `s1`,`s3` | `b1`,`b3` | `pass` |
| `MRL-1` | `mRL-1.2` | 共通復旧契約 | `s3`,`s4` | `b3`,`b4`,`b5` | `pass` |
| `MRL-1` | `mRL-1.3` | BDD / TDD 基準 | `s1` から `s9` | `b1` から `b9` | `pass` |
| `MRL-2` | `mRL-2.1` | Tailscale 到達性 | `s1` | `b1` | `pass` |
| `MRL-2` | `mRL-2.2` | OpenSSH PowerShell 入口 | `s2` | `b2` | `pass` |
| `MRL-2` | `mRL-2.3` | モバイル接続 profile | `s1`,`s2` | `b1`,`b2` | `pass` |
| `MRL-3` | `mRL-3.1` | 診断ラッパー | `s3` | `b3` | `pass` |
| `MRL-3` | `mRL-3.2` | 復旧ラッパー | `s4` | `b4` | `pass` |
| `MRL-3` | `mRL-3.3` | 証跡出力 | `s4`,`s9` | `b5` | `pass` |
| `MRL-4` | `mRL-4.1` | RustDesk 到達性 | `s5` | `b6` | `pass` |
| `MRL-4` | `mRL-4.2` | 共通 script 呼び出し | `s5` | `b6` | `pass` |
| `MRL-5` | `mRL-5.1` | 判断マトリクス | `s5` | `b7` | `pass` |
| `MRL-5` | `mRL-5.2` | 長時間待機後の復旧 UX | `s6` | `b8` | `pass` |
| `MRL-6` | `mRL-6.1` | launcher 仕様 | `s7` | `b9` | `pass` |
| `MRL-6` | `mRL-6.2` | launcher script 群 | `s7` | `b9` | `pass` |
| `MRL-6` | `mRL-6.3` | デスクトップショートカット配置 | `s7` | `b9` | `pass` |
| `MRL-7` | `mRL-7.1` | resume lock | `s8`,`s9` | `b4` | `pass` |
| `MRL-7` | `mRL-7.2` | guided recovery UX | `s9` | `b5` | `pass` |
| `MRL-7` | `mRL-7.3` | capture と multi-session 方針 | `s8`,`s9` | `b8` | `pass` |

## TDD

### 目的文

- `System Behaviors` を固定する test target と evidence を管理する。

### TDD タスク

| task_id | behavior_id | test_target | criterion | status | evidence |
| --- | --- | --- | --- | --- | --- |
| `T1` | `b1` | mobile 到達要件表 | iPhone / Android / Windows の事前準備が 1 枚で読める | `pass` | `kisaragi-db/--devs/--testlogs/prj-kisaragi_0003/reports/` |
| `T2` | `b2` | SSH shell runbook | smartphone から Windows `PowerShell` を既定 shell で開く手順が定義されている | `pass` | `kisaragi-db/--devs/--testlogs/prj-kisaragi_0003/reports/20260320-153627-rr-20260320-153627-summary.md` |
| `T3` | `b3` | diagnosis wrapper | `Slack`、`Docker`、`PostgreSQL`、`Synceller`、`app-server` の状態を 1 command で返せる | `pass` | `kisaragi-db/--exsams/prj-kisaragi_0003/logs/20260320-153627-rr-20260320-153627-doctor.json` |
| `T4` | `b4` | recovery wrapper | `doctor -> recover -> recheck` が安全順序で実行される | `pass` | `kisaragi-db/--exsams/prj-kisaragi_0003/logs/20260320-183435-rr-20260320-183435-resume.json` |
| `T5` | `b5` | summary formatter | evidence path、失敗理由、次の判断を summary に含める | `pass` | `kisaragi-db/--exsams/prj-kisaragi_0003/artifacts/20260320-153627-rr-20260320-153627-summary.json` |
| `T6` | `b6` | GUI fallback runbook | `RustDesk` から同じ recovery script を起動できる | `pass` | `kisaragi-db/--exsams/prj-kisaragi_0003/artifacts/20260321-052408-rr-20260321-052408-summary.json` |
| `T7` | `b7` | decision matrix | 主系統優先と副系統移行条件が明文化されている | `pass` | `admin-mrl-test-method.md` |
| `T8` | `b8` | post-recovery check | 復旧後に `/codex status` を確認する手順が evidence に含まれる | `pass` | `user-confirmed smartphone Slack capture at 2026-03-21 05:28 JST` |
| `T9` | `b2` | Termius setup manual | 初回設定で `Hostname`、password、`Use Telnet` で迷わない | `pass` | `admin-mrl-test-method.md` |
| `T10` | `b9` | GUI launcher spec | GUI launcher の役割と起動対象が固定されている | `pass` | `admin-mrl-test-method.md` |
| `T11` | `b9` | GUI launcher scripts | desktop 配置用 launcher script が用意されている | `pass` | `kisaragi-db/--devs/--products/prj-kisaragi_0003/apps/` |
| `T12` | `b4` | resume lock | `resume` の二重実行が lock で防止される | `pass` | `lock error observed at 2026-03-21 05:41 JST` |
| `T13` | `b5` | guided recovery | guided command が次の判断を含めて返す | `pass` | `kisaragi-db/--exsams/prj-kisaragi_0003/artifacts/20260321-054028-rr-20260321-054028-summary.json` |
| `T14` | `b8` | capture save flow | Slack capture を evidence 配下に保存する導線がある | `pass` | `kisaragi-db/--exsams/prj-kisaragi_0003/captures/20260321-084541-rr-20260321-084541-slack-status.png` |
| `T15` | `b4` | multi-session policy | 複数 session の役割分離が文書化されている | `pass` | `admin-mrl-test-method.md` |

