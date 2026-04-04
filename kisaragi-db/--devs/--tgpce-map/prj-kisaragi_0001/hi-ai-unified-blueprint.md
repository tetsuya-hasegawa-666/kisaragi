# hi-ai-unified-blueprint (HAUB)

## current_state

### 疑問点不整合一覧

| id | 論点 | 影響 | 現在の扱い | admin 状態 | 関連文書 |
| --- | --- | --- | --- | --- | --- |
| `ISS-001` | headless browser automation を再導入するか | local smoke check の自動化粒度 | 現在は static preview smoke check で代替する | `no judge` | `admin-mrl-test-method.md`, `admin-mrl-test-evidence.md` |

### 現在の重点

- `MRL-1` から `MRL-4` は `pass`
- main focus は launcher、dual-pane、read-only boundary の維持である
- `market_release_lines.md` と `micro_release_lines.md` は参考情報として残す

## BDD

### 目的文

- `prj-kisaragi_0001` の user value、`Purpose Story`、`System Behaviors`、受け入れ基準、`MRL` 対応をまとめる。

### ノーススター

- operator は launcher から `db-view` と `prj-view` を開き、dual-pane の read-only viewer で比較、読解、Explorer handoff を迷わず進められる。

### 提供方針

- live source は read-only first を維持する
- dual-pane の左右独立状態を崩さない
- file explorer と reader を同一画面で扱う
- in-app editing を持ち込まない

### Purpose Story

- `s1`: operator は launcher mode で `db-view` と `prj-view` を basis 単位で切り替えられる
- `s2`: operator は左右 pane を独立状態のまま保って比較できる
- `s3`: operator は compact tree と automatic search で対象文書へ素早く到達できる
- `s4`: operator は Markdown と plain text 系 file を viewer 内で安全に読める
- `s5`: operator は configured roots 外の path を handoff できず、read-only 境界が守られる
- `s6`: operator は unsupported binary file を UI に持ち込まずに済む
- `s7`: operator は responsive 時も左右 split を維持したまま比較を続けられる
- `s8`: operator は必要時だけ Explorer handoff で外部編集系 tool へ移れる
- `s9`: operator は `npm run dashboard` と launcher icon を入口に `direview` を起動できる

### System Behaviors

- `b1`: viewer は source profile の文書を収集し、launcher mode では `db-view` と `prj-view` を返す
- `b2`: left pane と right pane は profile、search、expand state、selection を独立して保持する
- `b3`: document workspace は profile tab、compact expandable tree、sticky trail を表示できる
- `b4`: search は submit button なしで自動実行され、partial-match の結果 branch を展開する
- `b5`: Markdown file を選択すると reading layout で本文を読める
- `b6`: supported text file を選択すると plain text として読める
- `b7`: Explorer handoff は configured roots 内だけを reveal target として解決し、外側 path は拒否する
- `b8`: code target と consultation 導線は read-only policy note と phase gate を保つ
- `b9`: dashboard は `npm run dashboard` と launcher icon を entry にし、page title を `direview` に固定する

### 受け入れ基準

| s-id | b-id | 観点 | 受け入れ基準 |
| --- | --- | --- | --- |
| `s1` | `b1` | source profile | launcher mode で `db-view` と `prj-view` が読める |
| `s2` | `b2` | dual-pane state | 左右 pane の状態が互いを上書きしない |
| `s3` | `b3`,`b4` | navigation UI | profile tab、compact tree、sticky trail、automatic search が同一 workspace で成立する |
| `s4` | `b5`,`b6` | reader | Markdown と plain text が適切に表示される |
| `s5` | `b7`,`b8` | safety boundary | configured roots 外 path は拒否され、編集機能を持ち込まない |
| `s9` | `b9` | launch contract | `npm run dashboard` と launcher icon で起動し、page title が `direview` になる |

### MRL 対応表

| MRL | mRL | 目的 | 関連 s-id | 関連 b-id | 現在 gate |
| --- | --- | --- | --- | --- | --- |
| `MRL-1` | `mRL-1.1` | source profile manifest contract | `s1`,`s2` | `b1`,`b2` | `pass` |
| `MRL-1` | `mRL-1.2` | shell switch and read-only reset | `s2`,`s5` | `b2`,`b8` | `pass` |
| `MRL-1` | `mRL-1.3` | documentation and state alignment | `s1`,`s5` | `b1`,`b8` | `pass` |
| `MRL-2` | `mRL-2.1` | compare lane selection model | `s2`,`s3` | `b2`,`b3` | `pass` |
| `MRL-2` | `mRL-2.2` | side-by-side preview contract | `s4` | `b5`,`b6` | `pass` |
| `MRL-2` | `mRL-2.3` | cross-profile comparison evidence | `s3`,`s7` | `b3`,`b4` | `pass` |
| `MRL-3` | `mRL-3.1` | reveal target resolution | `s5`,`s8` | `b7` | `pass` |
| `MRL-3` | `mRL-3.2` | right click Explorer handoff | `s5`,`s8` | `b7`,`b8` | `pass` |
| `MRL-3` | `mRL-3.3` | no-edit UX close | `s5` | `b8` | `pass` |
| `MRL-4` | `mRL-4.1` | launch method candidates | `s9` | `b9` | `pass` |
| `MRL-4` | `mRL-4.2` | global UI composition direction | `s3`,`s4`,`s7` | `b3`,`b5`,`b6` | `pass` |
| `MRL-4` | `mRL-4.3` | implementation-start close | `s9` | `b9` | `pass` |

## TDD

### 目的文

- `System Behaviors` を固定する test target、criterion、evidence を管理する。

### TDD タスク

| task_id | behavior_id | test_target | criterion | status | evidence |
| --- | --- | --- | --- | --- | --- |
| `T1` | `b1` | liveProjectSnapshot multi-profile scan | 複数 source profile の文書を収集できる | `pass` | `--devs/--testcode/prj-kisaragi_0001/tests/shared-core/liveProjectSnapshot.test.ts` |
| `T2` | `b1` | profile metadata attachment | 収集結果に profile metadata が付与される | `pass` | `--devs/--testcode/prj-kisaragi_0001/tests/shared-core/liveProjectSnapshot.test.ts` |
| `T2a` | `b1` | launcher db/prj manifest scan | launcher mode の `db-view` と `prj-view` から文書を収集できる | `pass` | `--devs/--testcode/prj-kisaragi_0001/tests/shared-core/liveProjectSnapshot.test.ts` |
| `T3` | `b7` | reveal target inside roots | configured roots 内 path を reveal target として解決できる | `pass` | `--devs/--testcode/prj-kisaragi_0001/tests/shared-core/liveProjectSnapshot.test.ts` |
| `T4` | `b7` | reveal target outside roots rejection | configured roots 外 path を reveal target として拒否する | `pass` | `--devs/--testcode/prj-kisaragi_0001/tests/shared-core/liveProjectSnapshot.test.ts` |
| `T5` | `b2` | dual-pane independent state | 2 pane が独立表示される | `pass` | `--devs/--testcode/prj-kisaragi_0001/tests/shared-core/dashboardController.test.ts` |
| `T6` | `b1` | default basis selection | default が `prj-view` になる | `pass` | `--devs/--testcode/prj-kisaragi_0001/tests/document-workspace/documentWorkspaceController.test.ts` |
| `T7` | `b3` | active profile tree build | active profile だけの nested tree を構成できる | `pass` | `--devs/--testcode/prj-kisaragi_0001/tests/document-workspace/documentWorkspaceController.test.ts` |
| `T8` | `b3` | compact tree and profile tabs view | profile tab と compact tree を表示できる | `pass` | `--devs/--testcode/prj-kisaragi_0001/tests/document-workspace/documentWorkspaceView.test.ts` |
| `T9` | `b3` | sticky trail persistence | sticky trail を維持できる | `pass` | `--devs/--testcode/prj-kisaragi_0001/tests/document-workspace/documentWorkspaceView.test.ts` |
| `T10` | `b5` | Markdown reading layout | Markdown file 選択時に reading layout を表示できる | `pass` | `--devs/--testcode/prj-kisaragi_0001/tests/document-workspace/documentWorkspaceView.test.ts` |
| `T11` | `b6` | plain text reader | non-Markdown file を plain text で表示できる | `pass` | `--devs/--testcode/prj-kisaragi_0001/tests/document-workspace/documentWorkspaceView.test.ts` |
| `T12` | `b8` | read-only code target contract | read-only target と policy note を返せる | `pass` | `--devs/--testcode/prj-kisaragi_0001/tests/code-workspace/codeWorkspaceController.test.ts` |
| `T13` | `b8` | phase-gated consultation response | code consultation が phase gate の内側に保たれる | `pass` | `--devs/--testcode/prj-kisaragi_0001/tests/code-workspace/codeWorkspaceController.test.ts` |
| `T14` | `b9` | launch and build baseline | `npm test` と `npm run build` が継続して通る | `pass` | `--devs/--testlogs/prj-kisaragi_0001/reports/verification-summary.md` |
| `T15` | `b1` | manifest path env override | launcher が指定した manifest path を優先できる | `pass` | `--devs/--testcode/prj-kisaragi_0001/tests/shared-core/liveProjectSnapshot.test.ts` |

