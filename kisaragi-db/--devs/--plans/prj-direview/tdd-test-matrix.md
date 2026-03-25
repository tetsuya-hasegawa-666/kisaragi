# TDD テストマトリクス

この文書は、`prj-direview` の BDD terminal behavior に対する TDD 計画を管理する。

## TDD タスク

| task_id | behavior_id | test_target | criterion | status | evidence |
| --- | --- | --- | --- | --- | --- |
| `T1` | `B1` | liveProjectSnapshot multi-profile scan | 複数 source profile の文書を収集できる | pass | `--devs/--testcode/prj-direview/tests/shared-core/liveProjectSnapshot.test.ts` |
| `T2` | `B1` | profile metadata attachment | 収集結果に profile metadata が付与される | pass | `--devs/--testcode/prj-direview/tests/shared-core/liveProjectSnapshot.test.ts` |
| `T2a` | `B1` | launcher db/prj manifest scan | launcher mode の `db-view` と `prj-view` から文書を収集できる | pass | `--devs/--testcode/prj-direview/tests/shared-core/liveProjectSnapshot.test.ts` |
| `T3` | `B7` | reveal target inside roots | configured roots 内 path を reveal target として解決できる | pass | `--devs/--testcode/prj-direview/tests/shared-core/liveProjectSnapshot.test.ts` |
| `T4` | `B7` | reveal target outside roots rejection | configured roots 外 path を reveal target として拒否する | pass | `--devs/--testcode/prj-direview/tests/shared-core/liveProjectSnapshot.test.ts` |
| `T5` | `B2` | dual-pane independent state | 2 pane が独立表示され、left pane profile switch が成立する | pass | `--devs/--testcode/prj-direview/tests/shared-core/dashboardController.test.ts` |
| `T6` | `B1` | default basis selection | available profiles が返り、default が `codev-view` になる | pass | `--devs/--testcode/prj-direview/tests/document-workspace/documentWorkspaceController.test.ts` |
| `T7` | `B3` | active profile tree build | active profile だけの nested tree を構成できる | pass | `--devs/--testcode/prj-direview/tests/document-workspace/documentWorkspaceController.test.ts` |
| `T8` | `B3` | compact tree and profile tabs view | profile tab と compact expandable tree を表示できる | pass | `--devs/--testcode/prj-direview/tests/document-workspace/documentWorkspaceView.test.ts` |
| `T9` | `B3` | sticky trail persistence | `prj-direview` を sticky trail で可視に保てる | pass | `--devs/--testcode/prj-direview/tests/document-workspace/documentWorkspaceView.test.ts` |
| `T10` | `B5` | Markdown reading layout | Markdown file 選択時に reading layout を表示できる | pass | `--devs/--testcode/prj-direview/tests/document-workspace/documentWorkspaceView.test.ts` |
| `T11` | `B6` | plain text reader | non-Markdown file を plain text で表示できる | pass | `--devs/--testcode/prj-direview/tests/document-workspace/documentWorkspaceView.test.ts` |
| `T12` | `B8` | read-only code target contract | read-only target と policy note を返せる | pass | `--devs/--testcode/prj-direview/tests/code-workspace/codeWorkspaceController.test.ts` |
| `T13` | `B8` | phase-gated consultation response | code consultation が phase gate の内側に保たれる | pass | `--devs/--testcode/prj-direview/tests/code-workspace/codeWorkspaceController.test.ts` |
| `T14` | `B9` | launch and build baseline | `npm test` と `npm run build` が継続して通る | pass | `--devs/--testlogs/prj-direview/reports/verification-summary.md` |
| `T15` | `B9` | manifest path env override | launcher が指定した manifest path を優先できる | pass | `--devs/--testcode/prj-direview/tests/shared-core/liveProjectSnapshot.test.ts` |

## 実行方針

- 1 task 1 責務で進める
- `MRL-25` は `T1` から `T7` で source profile と dual-pane 基線を固める
- launcher の `db-view` / `prj-view` mode は `T2a` と `T15` で固定する
- `MRL-26` は `T8` から `T11` で比較閲覧 UX を固める
- `MRL-27` は `T3`、`T4`、`T12`、`T13` で handoff と read-only 境界を固定する
- `MRL-28` は `T14` で launch と build の継続性を確認する

## 現在の見立て

- `T1` から `T13` は Vitest で固定済みである
- `T14` は `npm test` と `npm run build` の verification summary で pass と扱える
- BDD 文書化は今回整備したが、closeout 記録は今後 `mrl-record.md` へ移行可能である
