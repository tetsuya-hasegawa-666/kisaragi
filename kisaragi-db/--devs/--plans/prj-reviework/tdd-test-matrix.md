# TDD テストマトリクス

## 目的文

この文書は `prj-reviework` の BDD `System Behaviors` を、1 task 1 責務で実装と検証へ落とす正本計画書とする。

## TDD タスク

| task_id | behavior_id | test_target | criterion | status | evidence |
| --- | --- | --- | --- | --- | --- |
| `T1` | `b11` | Python session parser alias compatibility | `bt.jsonl` / `poses.jsonl` と `ble_scan.jsonl` / `arcore_pose.jsonl` の両方を 1 parser で読める | pass | `kisaragi-db/--devs/--testlogs/prj-reviework/reports/python-unittest-summary.md` |
| `T2` | `b1` | `SessionPackage` intake summary | 主カメラ動画、主カメラ `IMU`、人物側 `IMU`、任意入力、時刻基準、品質状態を 1 summary に落とせる | planned | `none yet` |
| `T3` | `b2` | `Thin Status` diagnose formatter | 人物映り込みの十分性、不足入力、品質、理由を `phase`、`pipeline`、`data_health`、`quality`、`issues` で返せる | in_progress | `kisaragi-db/--devs/--products/prj-reviework/app/src/main/java/com/reviework/app/ReviewScreenController.kt` |
| `T4` | `b3` | execute readiness gate | 主カメラ動画、主カメラ `IMU`、人物側 `IMU`、空間再構成前提、経路前提がそろわない限り `処理を開始` を返さない | planned | `none yet` |
| `T5` | `b4` | run phase single-action UX | run phase の `Next Action` が常に 1 件で、現在段階を別 line に出せる | pass | `kisaragi-db/--exsams/prj-reviework/reports/testDebugUnitTest/junit/TEST-com.reviework.app.ReviewScreenControllerTest.xml` |
| `T6` | `b5` | `COLMAP` to `3DGS` safety gate | `COLMAP.status != READY_FOR_DENSIFICATION` のとき `3DGS` を開始しない | planned | `none yet` |
| `T7` | `b6` | `SpacePackage` coordinate contract | 主カメラ path と主空間基準を返し、`GNSS` がない時に主 `ARCore` local 空間を唯一基準として返せる | planned | `none yet` |
| `T8` | `b7` | `TrajectoryPackage` timeline registration | 主カメラ path、人物 path、不確実性、再拘束点を同じ時刻軸で返せる | planned | `none yet` |
| `T9` | `b8` | relink uncertainty classifier | visual match confidence、time gap、anchor proximity、`BT` 維持情報で不確実性を決める | planned | `none yet` |
| `T10` | `b9` | verify quality summary | `space` と `trajectory` の quality、同時刻比較の弱点、weak area を同時に返せる | planned | `none yet` |
| `T11` | `b9` | interpret attention point synthesis | `attention point` と同時刻ハイライトに時間範囲、理由、不確実区間情報を持たせる | in_progress | `kisaragi-db/--exsams/prj-reviework/reports/testDebugUnitTest/junit/TEST-com.reviework.app.ReviewScreenControllerTest.xml` |
| `T12` | `b10` | `ReviewArtifact` boundary contract | `Assembly` だけが `3DGS` 操作、経路表示、同時刻ハイライトを含む `ReviewArtifact` を生成する | planned | `none yet` |
| `T13` | `b12` | independent project boundary scan | `prj-reviework` products と docs が外部 project の shared 参照なしで継続できる | planned | `none yet` |
| `T14` | `b12` | output routing hygiene | Android build cache と raw test report が `--exsams`、summary が `--testlogs` に分離される | pass | `kisaragi-db/--devs/--products/prj-reviework/scripts/run_android_unit_tests.ps1` |
| `T15` | `b13` | `InputPackaging` interface manifest | `iSensorium` 生出力に加え、受理判定、品質、frame-pose 対応、主体対応表が JSON と CSV の契約で出力される | in_progress | `kisaragi-db/--devs/--testcode/prj-reviework/test_session_parser.py` |
| `T16` | `b14` | stage handoff contract | 4 分担の各段階で入力、出力、受け渡し条件が文書と実装の両方で読める | planned | `none yet` |

## 実行方針

- `MRL-1` では `T1`、`T2`、`T3`、`T4` を優先し、入口と実行可否 gate を固める
- `MRL-1` では `T15` と `T16` も先に固め、分担作業の手戻りを防ぐ
- `MRL-2` では `T5`、`T6`、`T7` を使って主空間基準と安全 gate を固める
- `MRL-3` では `T8` から `T11` で人物経路、relink、不確実性、同時刻ハイライト、`attention point` を固める
- `MRL-4` では `T12` から `T14` で成果物境界と運用 hygiene を固める
- fail する test を先に置き、green 後に view / controller の整理を行う

## 現在の見立て

- `T1` は Python unittest で pass している
- `T3` は表示面の骨格があるが、人物映り込みの十分性を含む diagnose 計算本体は未完である
- `T5` は Kotlin unit test で pass している
- `T11` は demo 表示までは見えているが、実データ由来の `attention point` と同時刻ハイライト生成は未実装である
- `T14` は PowerShell script と出力先の分離で pass している
- `T15` は Python parser に分担用インターフェース出力を追加し、direct unittest で通過したが、要約証跡の更新は未実施である
- `MRL-1` を閉じるには `T2`、`T4`、`T15`、`T16` の自動検証または文書化証跡が必要である
