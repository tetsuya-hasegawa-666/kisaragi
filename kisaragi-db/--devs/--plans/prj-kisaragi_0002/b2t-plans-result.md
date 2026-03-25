# B2T-Plans-Result

## 文書の役割

この文書は `prj-kisaragi_0002` の `current_state`、BDD、TDD を 1 つに統合した正本とする。

## current_state

### 役割

- `prj-kisaragi_0002` は、主空間再構成と経路レビューを 4 段階一括処理で扱う project とする
- `Next Action + Thin Status` を中核 UX とし、`SessionPackage`、`SpacePackage`、`TrajectoryPackage`、`ReviewArtifact` の契約で進める

### 現在の重点

- 現行計画の `MRL` / `mRL` と `T1` から `T16` は、contract 実装、test、routing 実行で `pass` になった
- 4 分担作業のための段階間インターフェースと追加出力を正本文書へ明示した
- Kotlin controller と Python parser により、受理、gate、空間品質、人物経路、同時刻ハイライト、成果物境界の契約を固定した
- `GNSS` は任意入力とし、既定は `GNSS` なしでも成立する設計を維持する

### 阻害要因の境界

- `COLMAP` と `3DGS` の実行基盤は未選定である
- 人物 path の視覚再拘束に使う実データ条件が未確定である
- `ReviewArtifact` の最終 viewer 実装先は Android 固定ではない

### 次の確認

1. parser と controller の契約評価を実データ読込へ接続する
2. `3DGS` と viewer の実成果物を `ReviewArtifact` 契約へ接続する
3. 同時刻ハイライトを実データから自動生成する

### 作業所有権

- Codex が `project-truth.md`、`b2t-plans-result.md`、`mrl-record.md` の再開基線整備と `MRL` 継続作業を担当する

## BDD

### 目的文

この章は `prj-kisaragi_0002` の提供価値、`Purpose Story`、`System Behaviors`、`MRL` / `mRL` の対応を定義する。

### 目指す姿

- `trajectreview` は、1 台のスマホカメラとその `IMU` による連続動画、および `IMU` 付き機器を持つ人がその動画へ頻繁に映り込む状況で、最も効果を発揮する
- 連続動画と `IMU` のデータ、および動画なしの `IMU` 付きスマホを携帯する人のデータを入力するだけで、現場の `3DGS`、撮影主体の経路、映り込む人の経路を同じ `3DGS` 空間上へ表示できる
- 経路は時系列情報を持ち、同じ時刻の位置関係をハイライトできる

### 提供方針

- 最適条件は 1 台の主カメラ動画と、映り込む人の `IMU` データである
- `GNSS` は任意入力とし、なくても主 `ARCore` 空間を基準に成立させる
- `Timeline` を統合キーとして、主カメラ path と人物 path を同時刻で束ねる
- まず受理、診断、実行可否を固め、その後に空間、経路、閲覧を分離実装する
- 閲覧成果物は `3DGS` の操作、経路表示、同時刻ハイライトを一体で扱う

### Purpose Story

- `s1`: 利用者は、主カメラ動画と主カメラ `IMU`、および人物側 `IMU` の入力がそろっているかを受理時点で把握できる
- `s2`: 利用者は、主カメラ動画に人物が十分映り込んでいるか、不足入力や品質低下とあわせて診断で読める
- `s3`: 利用者は、主空間再構成と人物経路再構成に必要な条件を満たした時だけ `処理を開始` を受け取れる
- `s4`: 利用者は、実行中に今どの段階を処理しているかだけを見ればよい
- `s5`: 利用者は、主空間再構成が成立しない時に `3DGS` 生成へ進まず修正へ戻れる
- `s6`: 利用者は、1 台の主カメラ動画から作られた `3DGS` と主カメラ経路を確認できる
- `s7`: 利用者は、人物側 `IMU` と映り込みを使って人物経路が主空間へ重ねられた結果を確認できる
- `s8`: 利用者は、見失い区間と再拘束の不確実性を理由付きで把握できる
- `s9`: 利用者は、`3DGS` 上で主カメラ経路と人物経路を同時刻比較できる
- `s10`: 利用者は、同じ時刻の位置関係をハイライトし、注視すべき区間を絞り込める
- `s11`: 利用者は、生成済み `ReviewArtifact` を viewer で操作し、空間と経路をレビューできる
- `s12`: 運用者は、4 分担の境界と出力契約だけで実装と運用を継続できる

### System Behaviors

- `b1`: 受理時に、主カメラ動画、主カメラ `IMU`、人物側 `IMU`、任意 `poses` / `gnss` の充足状況を `SessionPackage` へ要約する
- `b2`: `Diagnose` は、人物映り込みの十分性、不足入力、品質低下、修正理由を `Thin Status` で返す
- `b3`: 実行可否 gate は、主カメラ動画、主カメラ `IMU`、人物側 `IMU`、空間再構成前提、経路再構成前提の readiness を満たした時だけ `処理を開始` を返す
- `b4`: 実行 phase は、`Next Action` を常に `完了を待つ` 1 件に保ち、現在段階を別 line で返す
- `b5`: `COLMAP.status != READY_FOR_DENSIFICATION` のとき、`3DGS` を開始せず `入力条件を見直す` を返す
- `b6`: `SpacePackage` は、1 台の主カメラ動画から得た主空間基準、主カメラ path、空間品質を返す
- `b7`: `TrajectoryPackage` は、主カメラ path、人物 path、不確実性、再拘束点を同じ `Timeline` 上で返す
- `b8`: 人物 path の relink は visual match confidence、time gap、anchor proximity、`BT` 主体維持で判定し、不成立時は不確実性を上げる
- `b9`: `Verify` は空間品質と経路品質を同時に返し、`Interpret` は同時刻ハイライト候補と `attention point` を返す
- `b10`: `Assembly` は `3DGS` 操作用情報、経路、同時刻ハイライト情報を束ねた `ReviewArtifact` を唯一生成する
- `b11`: parser は `bt.jsonl` / `poses.jsonl` と `ble_scan.jsonl` / `arcore_pose.jsonl` の両方を受理する
- `b12`: `trajectreview` の docs、build、test、生成物経路は `prj-kisaragi_0002` 配下で完結し、要約と生の生成物を分離する
- `b13`: `InputPackaging` は `iSensorium` 生出力に加えて、`input_readiness.json`、`sensor_quality.json`、`frame_pose_index.csv`、`member_identity_map.json` を分担インターフェースとして出力する
- `b14`: 4 分担の各段階は、前段の出力契約だけを読めば次段へ着手できる

### 受け入れ基準

| s-id | b-id | 観点 | 受け入れ基準 |
| --- | --- | --- | --- |
| `s1` | `b1`,`b11`,`b13` | 受理契約 | 主カメラ動画、主カメラ `IMU`、人物側 `IMU`、任意 `poses` / `gnss`、追加出力の有無が 1 つの要約として読める |
| `s2` | `b2` | diagnose UX | 人物映り込みの十分性、不足入力、品質低下、修正理由が `Thin Status` で読める |
| `s3` | `b3` | 実行可否 gate | readiness 未達時は `処理を開始` を返さず、修正 action を返す |
| `s4` | `b4` | 実行 UX | `Next Action` は常に 1 件で、現在段階は補足 line に分離される |
| `s5` | `b5` | パイプライン安全性 | 主空間再構成 failure 時に `3DGS` を開始しない |
| `s6` | `b6` | 主空間確認 | 主空間基準、主カメラ path、空間品質が読める |
| `s7` | `b7`,`b8` | 人物経路確認 | 人物 path が主空間へ重ねられ、不確実区間と再拘束点が識別できる |
| `s8` | `b8` | 不確実性 | 再拘束失敗時に不確実性 mode と理由が更新される |
| `s9` | `b7`,`b9` | 同時刻比較 | 主カメラ経路と人物経路が同じ時刻軸で比較できる |
| `s10` | `b9` | ハイライト | 同じ時刻の位置関係と `attention point` に時間範囲と理由が入る |
| `s11` | `b10` | 閲覧成果物 | `ReviewArtifact` に `3DGS` 操作、経路表示、同時刻ハイライトが含まれる |
| `s12` | `b12`,`b13`,`b14` | 独立運用 | docs / build / test が project 内で完結し、段階間契約だけで分担着手できる |

### `MRL` 対応表

| MRL | mRL | 目的 | 関連 s-id | 関連 b-id | 現在 gate |
| --- | --- | --- | --- | --- | --- |
| `MRL-1` | `-` | 受理と診断の基礎線を成立させる | `s1`,`s2`,`s3` | `b1`,`b2`,`b3`,`b11`,`b13`,`b14` | `pass` |
| `MRL-1` | `mRL-1.1` | 主入力の受理契約 | `s1` | `b1`,`b11`,`b13` | `pass` |
| `MRL-1` | `mRL-1.2` | 人物映り込みを含む診断基線 | `s2` | `b2` | `pass` |
| `MRL-1` | `mRL-1.3` | 実行可否 gate | `s3` | `b3` | `pass` |
| `MRL-1` | `mRL-1.4` | 分担インターフェース固定 | `s1`,`s12` | `b13`,`b14` | `pass` |
| `MRL-2` | `-` | 主空間再構成の基礎線を成立させる | `s4`,`s5`,`s6` | `b4`,`b5`,`b6` | `pass` |
| `MRL-2` | `mRL-2.1` | 主カメラ path と空間基準固定 | `s4`,`s6` | `b4`,`b6` | `pass` |
| `MRL-2` | `mRL-2.2` | `COLMAP` から `3DGS` への安全 gate | `s5` | `b5` | `pass` |
| `MRL-2` | `mRL-2.3` | 空間品質要約 | `s6` | `b6` | `pass` |
| `MRL-3` | `-` | 人物経路再構成と同時刻比較の基礎線を成立させる | `s7`,`s8`,`s9`,`s10` | `b7`,`b8`,`b9` | `pass` |
| `MRL-3` | `mRL-3.1` | 人物経路の主空間登録 | `s7`,`s9` | `b7` | `pass` |
| `MRL-3` | `mRL-3.2` | relink と不確実性 | `s7`,`s8` | `b8` | `pass` |
| `MRL-3` | `mRL-3.3` | 同時刻ハイライトと `attention point` | `s9`,`s10` | `b9` | `pass` |
| `MRL-4` | `-` | 閲覧成果物と運用硬化を成立させる | `s11`,`s12` | `b10`,`b12`,`b13`,`b14` | `pass` |
| `MRL-4` | `mRL-4.1` | `ReviewArtifact` と viewer 境界 | `s11` | `b10` | `pass` |
| `MRL-4` | `mRL-4.2` | 独立 project 境界 | `s12` | `b12`,`b14` | `pass` |
| `MRL-4` | `mRL-4.3` | 生成物 routing hygiene | `s12` | `b12`,`b13` | `pass` |

## TDD

### 目的文

この章は `prj-kisaragi_0002` の BDD `System Behaviors` を、1 task 1 責務で実装と検証へ落とす。

### TDD タスク

| task_id | behavior_id | test_target | criterion | status | evidence |
| --- | --- | --- | --- | --- | --- |
| `T1` | `b11` | Python session parser alias compatibility | `bt.jsonl` / `poses.jsonl` と `ble_scan.jsonl` / `arcore_pose.jsonl` の両方を 1 parser で読める | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py` |
| `T2` | `b1` | `SessionPackage` intake summary | 主カメラ動画、主カメラ `IMU`、人物側 `IMU`、任意入力、時刻基準、品質状態を 1 summary に落とせる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py` |
| `T3` | `b2` | `Thin Status` diagnose formatter | 人物映り込みの十分性、不足入力、品質、理由を `phase`、`pipeline`、`data_health`、`quality`、`issues` で返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T4` | `b3` | execute readiness gate | 主カメラ動画、主カメラ `IMU`、人物側 `IMU`、空間再構成前提、経路前提がそろわない限り `処理を開始` を返さない | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T5` | `b4` | run phase single-action UX | run phase の `Next Action` が常に 1 件で、現在段階を別 line に出せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T6` | `b5` | `COLMAP` to `3DGS` safety gate | `COLMAP.status != READY_FOR_DENSIFICATION` のとき `3DGS` を開始しない | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T7` | `b6` | `SpacePackage` coordinate contract | 主カメラ path と主空間基準を返し、`GNSS` がない時に主 `ARCore` local 空間を唯一基準として返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T8` | `b7` | `TrajectoryPackage` timeline registration | 主カメラ path、人物 path、不確実性、再拘束点を同じ時刻軸で返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T9` | `b8` | relink uncertainty classifier | visual match confidence、time gap、anchor proximity、`BT` 維持情報で不確実性を決める | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T10` | `b9` | verify quality summary | `space` と `trajectory` の quality、同時刻比較の弱点、weak area を同時に返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T11` | `b9` | interpret attention point synthesis | `attention point` と同時刻ハイライトに時間範囲、理由、不確実区間情報を持たせる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T12` | `b10` | `ReviewArtifact` boundary contract | `Assembly` だけが `3DGS` 操作、経路表示、同時刻ハイライトを含む `ReviewArtifact` を生成する | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T13` | `b12` | independent project boundary scan | `prj-kisaragi_0002` products と docs が外部 project の shared 参照なしで継続できる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_project_contracts.py` |
| `T14` | `b12` | output routing hygiene | Android build cache と raw test report が `--exsams`、summary が `--testlogs` に分離される | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/scripts/run_android_unit_tests.ps1` |
| `T15` | `b13` | `InputPackaging` interface manifest | `iSensorium` 生出力に加え、受理判定、品質、frame-pose 対応、主体対応表が JSON と CSV の契約で出力される | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py` |
| `T16` | `b14` | stage handoff contract | 4 分担の各段階で入力、出力、受け渡し条件が文書と実装の両方で読める | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_project_contracts.py` |

### 実行方針

- `MRL-1` では `T1`、`T2`、`T3`、`T4` を優先し、入口と実行可否 gate を固めた
- `MRL-1` では `T15` と `T16` も先に固め、分担作業の手戻りを防いだ
- `MRL-2` では `T5`、`T6`、`T7` を使って主空間基準と安全 gate を固めた
- `MRL-3` では `T8` から `T11` で人物経路、relink、不確実性、同時刻ハイライト、`attention point` を固めた
- `MRL-4` では `T12` から `T14` で成果物境界と運用 hygiene を固めた

### 現在の見立て

- `T1` から `T16` は、契約実装、project 境界 scan、output routing 実行で `pass` になった
- Python unittest、Android unit test、PowerShell script 実行により、入口契約から成果物 routing までの計画範囲を固定した
- 次の主作業は、pass した contract を実データ pipeline と viewer の実利用へ拡張することになる
