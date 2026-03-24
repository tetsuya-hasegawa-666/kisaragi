# TDD テストマトリクス

この文書は、`prj-reviework` の BDD terminal behavior に対する TDD 計画を管理する。

## TDD タスク

| task_id | behavior_id | test_target | criterion | status | evidence |
| --- | --- | --- | --- | --- | --- |
| `T1` | `B10` | Python session parser alias compatibility | `bt.jsonl` / `poses.jsonl` と legacy alias の両方を 1 parser で読める | pass | `--process/--testlogs/prj-reviework/reports/python-unittest-summary.md` |
| `T2` | `B1` | SessionPackage intake summary | required / optional input の充足状況を summary に落とせる | planned | `none yet` |
| `T3` | `B2` | Thin Status diagnose formatter | `phase`、`pipeline`、`data_health`、`quality`、`issues` の 5 カテゴリで理由を返せる | in_progress | `--process/--products/prj-reviework/app/src/main/java/com/reviework/app/ReviewScreenController.kt` |
| `T4` | `B3` | execute readiness gate | readiness 未達時は `処理を開始` を返さず、修正 action を返す | planned | `none yet` |
| `T5` | `B4` | run phase single-action UX | run phase の `Next Action` が常に 1 件で、current step を別 line に出せる | pass | `--process/--testlogs/prj-reviework/reports/testDebugUnitTest/junit/TEST-com.reviework.app.ReviewScreenControllerTest.xml` |
| `T6` | `B5` | COLMAP to 3DGS safety gate | `COLMAP.status != READY_FOR_DENSIFICATION` のとき `3DGS` を開始しない | planned | `none yet` |
| `T7` | `B6` | verify quality projection | `space` と `trajectory` の quality と weak area を同時に返せる | planned | `none yet` |
| `T8` | `B7` | attention point synthesis | attention point に時間範囲と理由を持たせる | in_progress | `--process/--testlogs/prj-reviework/reports/testDebugUnitTest/junit/TEST-com.reviework.app.ReviewScreenControllerTest.xml` |
| `T9` | `B8` | relink uncertainty classifier | visual match confidence、time gap、anchor proximity の 3 条件で uncertainty を決める | planned | `none yet` |
| `T10` | `B9` | ReviewArtifact boundary contract | `Assembly` だけが `ReviewArtifact` を生成し、viewer は read-only で消費する | planned | `none yet` |
| `T11` | `B11` | independent copy boundary scan | `prj-reviework` products が `prj-isensorium` の shared 参照を持たない | pass | `codev-ruling/copy-plans-results/prj-reviework/copy-plans-results.md` |
| `T12` | `B12` | output routing scripts | Android build cache と test report が `--trial-data` と `--testlogs` に分離される | pass | `--process/--products/prj-reviework/scripts/run_android_unit_tests.ps1` |

## 実行方針

- 1 task 1 責務で進める
- `MRL-1` は `T1`、`T2`、`T3`、`T4` を優先する
- `MRL-2` は `T5`、`T6` で run gate を閉じる
- `MRL-3` は `T7` から `T10` で verify / interpret / artifact を固める
- `MRL-4` は `T11`、`T12` で独立運用と証跡分離を維持する

## 現在の見立て

- `T1` は Python unittest で pass
- `T5` は Kotlin unit test で pass
- `T3` は `Thin Status` の表示責務までは見えているが、diagnose 計算本体は継続実装が必要である
- `T8` は attention point の demo 表示までは通っているが、実データ由来の synthesis は未実装
- `T11` は copy plan と products 構造上は pass だが、継続的な boundary scan は今後も必要
- `T12` は PowerShell script と test 出力先で pass
