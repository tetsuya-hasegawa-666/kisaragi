# project-truth

この文書は `prj-kisaragi_0002` の恒久的な真実を保持する正本とする。

## 目的

`trajectreview` は、1 台のスマホカメラとその `IMU` による連続動画、および動画へ頻繁に映り込む人物が持つ `IMU` 付き機器の記録を単一セッションとして受理し、主空間の再構成、主カメラ経路と人物経路の再構成、閲覧成果物の組立までを一貫して扱い、レビュー判断を迷わず進められる作業空間を提供する。

## ノーススター

- 利用者は常に次に取るべき行動を 1 件だけ受け取れる
- 利用者は `Thin Status` で処理段階、品質低下、阻害理由を薄く常時把握できる
- 利用者は主空間、主カメラ経路、人物経路を同じ `Timeline` で見比べ、同時刻ハイライトと `attention point` からレビュー判断へ進める
- 運用者は外部 project や一時文書に依存せず、`prj-kisaragi_0002` 配下だけで計画、実装、検証を継続できる

## 完成判定の原則

- `trajectreview` の完成判定は `本来機能が app 内で実行できること` を基準とする
- `UX 確認`、`contract 固定`、`build / install`、`local sample`、`stub 読込` は価値のある中間成果だが、完成そのものではない
- `pass` を付ける時は、対象 app が本来の入出力を扱い、後段が消費する実生成物を出し、主要 blocker が残っていないことを要件とする

## 現在の到達認識

- `trajectreview-correcting` は `現場記録 -> 最新 session 再読込 -> data-check -> correction guidance` を 1 app 内で実行できる
- `trajectreview-correcting` は `現場記録 -> data-check -> 同一ネットワーク上の対象 PC 選択 -> wireless PC transfer` を 1 app 内で閉じる方針を採る
- `trajectreview-correcting` は `Depth Anything v3 MetricLarge` 後段のために、同一 `ARCore` frame から pose、frame timestamp、image intrinsics、texture intrinsics、lens distortion を 1 record として残す
- `frozen_camerax_arcore` route では録画安定性を優先し、記録中の `ARCore` 収集を停止する
- `trajectreview-modeling` は `local sample before colab` と request 生成を持つが、実 `DA3Metric-Large` / point-cloud projection / trajectory reconstruction は未実装である
- `trajectreview-modeling` は preflight として `experiment_manifest.json`、`da3_input_manifest.json`、`benchmark_summary.json`、`selected_route.json`、Colab notebook / import helper を生成できる
- Colab notebook は `session_root` と `result_root` を最小入力とし、`session_package.json`、`selected_route.json`、`colab_job_request.json` から `session_id`、`route_id`、`sampling profile`、`intrinsics mode` を自動解決する
- `trajectreview-modeling` は単一 route 固定で始めず、`DA3Metric-Large` の sampling / intrinsics handling を比較し、暫定採用 route を後から既定化する方針を採る
- `trajectreview-reviewing` は summary / stub 読込を持つが、実 `ReviewArtifact` viewer と操作系は未実装である
- 統合 app は workflow 境界の理解には使えるが、現時点では本来機能を end-to-end で閉じていない

## 対象シナリオ

- 主空間収録主体は `ARCore` 連携スマホカメラを持ち、連続動画と `IMU` を記録して主空間の基準となる
- 人物主体は動画なしの携行スマートフォンを持ち、`IMU` と必要に応じて `BT` を中心に時系列追跡される
- 人物は主カメラ動画へ頻繁に映り込み、人物経路の再拘束に使える
- `GNSS` は任意入力とし、ない場合でも成立する設計を既定とする
- `GNSS` がない場合は主 `ARCore` 空間を唯一の基準座標とする

## 提供価値

- 現場らしく見える `3DGS` 空間をレビュー起点として読める
- 主カメラ経路と人物経路を同時刻で比較できる
- 同じ時刻の位置関係をハイライトできる
- 品質低下や再構成失敗の理由を短く把握できる
- 不確実区間を隠さず、誤読しにくい形でレビューできる

## UX 原則

- `Next Action` は常に 1 件だけ提示する
- `Thin Status` は `phase`、`pipeline`、`data_health`、`quality`、`issues` の 5 項目を基本とする
- 利用者に探索を強要せず、レビューすべき `attention point` と同時刻ハイライトを時間範囲と理由付きで提示する
- 正常時は薄く、異常時だけ強調する
- `Timeline` を統合キーとして、space、trajectory、同時刻ハイライト、`attention point`、summary を束ねる

## UX フェーズ

### Intake

- 目的: 入力セッション folder から主カメラ動画と `IMU`、人物側 `IMU` を抽出し、単一セッションとして受理する
- 主表示: `入力セッションを選択`
- 状態表示: 選択元、抽出先、frame 数、必須入力の充足、欠落有無、時刻整列指標

### Diagnose

- 目的: 実行可否と入力品質を判定する
- 主表示: `処理を開始` または修正 action
- 状態表示: data health、人物映り込みの十分性、主要 issue、修正理由

### Run

- 目的: 一括処理 pipeline を進行させる
- 主表示: `完了を待つ`
- 状態表示: 現在段階、進行状況、blocking issue

### Verify

- 目的: 空間品質と経路品質の成立を確認する
- 主表示: 結果を確認
- 状態表示: 空間品質、経路品質、同時刻比較の弱点

### Interpret

- 目的: レビューと改善判断を行う
- 主表示: この区間を見る
- 状態表示: `attention point`、同時刻ハイライト、不確実区間、危険候補

## 4 段階処理構造

- app 構成は、`trajectreview-correcting`、`trajectreview-modeling`、`trajectreview-reviewing`、統合 app の 4 実行入口を許容する
- 上記 4 app は、複数人分担や手戻り時の原因分析速度を上げるための作業境界であり、実際の開発主体が admin と Codex の 2 名であることと矛盾しない

### 第 1 段階: `InputPackaging`

- 責務: 取得元 app data から主カメラ動画、主カメラ `IMU`、人物側 `IMU` を抽出し、単一セッション入力へ正規化する
- 主な処理: session folder 選択、raw file 抽出、frame 抽出、`ARCore` pose 整理、`IMU` 整理、`BT` 整理、時刻整列、品質フラグ付与
- 出力: `SessionPackage`

### 第 2 段階: `SpaceReconstruction`

- 責務: 主空間の基準座標と再構成成果物を作る
- 主な処理: frame 選別、`DA3Metric-Large` 入力生成、metric depth 推定、`ARCore pose` による world projection、空間品質集約
- 出力: `SpacePackage`

### 第 3 段階: `TrajectoryReconstruction`

- 責務: 主カメラ経路と人物経路を主空間へ登録する
- 主な処理: 主カメラ経路生成、人物 path 推定、`BT` による主体維持、視覚再拘束、見失い区間橋渡し、不確実性付与
- 出力: `TrajectoryPackage`

### 第 4 段階: `AssemblyAndViewer`

- 責務: 閲覧可能な成果物を組み立て、viewer で読む
- 主な処理: timeline 生成、主体表示定義、同時刻ハイライト定義、`attention point` 統合、閲覧 manifest 生成
- 出力: `ReviewArtifact`

## app 構成

### `trajectreview-correcting`

- 対象段階: `InputPackaging`
- 主責務: 現場記録、取得条件設定、source session 保存、入力補正の起点作成
- 完成基準:
  - `trajectreview-correcting` 自体が camera / IMU / GNSS / BLE / ARCore 記録画面を持ち、source session を端末内へ保存する
  - `保存先を選択` により、利用者が同期先 folder を app 内で明示的に選べる
  - 同じ app 内で session を intake し、`session_package.json`、`sensor_quality.json`、`space_handoff_manifest.json` まで生成する
  - `ARCore` pose record には `frameTimestampNs`、`imageFocalLength`、`imagePrincipalPoint`、`imageDimensions`、`textureFocalLength`、`texturePrincipalPoint`、`textureDimensions`、`lensDistortion` を含める
  - `camera_calibration_summary.json` に calibration 対応率を出し、`DA3 MetricLarge` 前段の入力可否を判断できる
  - `data-check` が readiness、quality、blocker、recommended correction を返す
  - `data-check` を 1 回以上通した後にだけ `PC 転送` を有効化し、同一ネットワーク上の対象 PC を app 内で選択できる
  - 利用者が `現場撮影データ保存を開始` から wireless PC transfer 完了まで、別 app へ移らず進められる

### `trajectreview-modeling`

- 対象段階: `SpaceReconstruction`、`TrajectoryReconstruction`
- 主責務: model 入力確認、実行 gate、進行把握、再構成 blocker 確認
- 完成基準:
  - `session_package.json`、`sensor_quality.json`、`space_handoff_manifest.json`、`camera_calibration_summary.json` を入力として、`DA3Metric-Large` の前処理入力、`Colab` upload 対象、job request を route 単位で生成する
  - `DA3Metric-Large` による metric depth 推定と `ARCore pose` / intrinsics による world projection を実行し、主要 quality 指標と failure reason を route 単位で記録する
  - 複数の sampling / intrinsics route を比較し、`benchmark_summary.json` と `selected_route.json` により暫定採用 route を固定する
  - remote 実行結果を受理し、`SpacePackage`、`TrajectoryPackage`、`space_quality.json`、`trajectory_quality.json`、`attention_seed.json` を更新する
  - `local sample before colab` は preflight 用補助 route とし、完成判定の代替に使わない

## modeling route 方針

- `DA3Metric-Large` を first target の metric depth 基盤とする
- 最初から最終 route を固定せず、少なくとも `5fps`、`10fps`、`per-frame intrinsics` を比較候補として扱う
- depth route は quality、runtime、resource usage、failure rate を比較して暫定採用 route を決める
- route 比較は同一 session、同一 export contract、同一評価指標で行う
- 暫定採用 route と research route は `selected_route.json` で分離し、既定 route の変更履歴を追えるようにする

### `trajectreview-reviewing`

- 対象段階: `AssemblyAndViewer`
- 主責務: verify、review、same-time highlight、`attention point` 確認
- 完成基準:
  - `ReviewArtifact` 実体を読み、viewer、timeline、same-time highlight、`attention point` jump を提供する
  - summary / stub 読込だけでなく、後段成果物そのものを利用者が操作できる

### 統合 app

- 対象段階: 全段階
- 主責務: correcting、modeling、reviewing の全 workflow を 1 つの視点で束ねる
- 完成基準:
  - correcting、modeling、reviewing の本来機能を 1 app から順につなげられる
  - workflow 全体の現在地と blocker を示しつつ、各段階の実生成物へ到達できる

## 分担インターフェース

### 分担 1: `InputPackaging`

- 担当: 現場記録、source session 生成、取得元入力の抽出、受理、整形、時刻整列、入力診断
- 次段へ渡すもの:
  - `SessionPackage`
  - `input_readiness.json`
  - `sensor_quality.json`
  - `frame_pose_index.csv`
  - `camera_calibration_summary.json`
  - `member_identity_map.json`
  - `session_package.json`
  - `space_handoff_manifest.json`
- 受け渡し条件:
  - `trajectreview-correcting` で source session が保存済みである
  - 主カメラ動画、主カメラ `IMU`、人物側 `IMU` の充足が判定済みである
  - 主体、端末、時刻基準の対応が追える
  - 取得元 raw と `trajectreview` 派生出力が分離されている
  - app 内で抽出元と抽出先が追える

### 分担 2: `SpaceReconstruction`

- 担当: 主空間再構成、空間基準固定、`COLMAP` / `3DGS` 連携
- 前段から受け取るもの:
  - `SessionPackage`
  - `session_package.json`
  - `space_handoff_manifest.json`
  - `input_readiness.json`
  - `sensor_quality.json`
  - `frame_pose_index.csv`
  - `camera_calibration_summary.json`
- 次段へ渡すもの:
  - `SpacePackage`
  - `space_quality.json`
  - `coverage_report.json`
  - `main_camera_path.csv`
  - `trajectreview/modeling/experiment_manifest.json`
  - `trajectreview/modeling/da3_input_manifest.json`
  - `trajectreview/modeling/benchmark_summary.json`
  - `trajectreview/modeling/selected_route.json`
  - `trajectreview/modeling/local_model_summary.json`
  - `trajectreview/modeling/colab_job_request.json`
  - `trajectreview/modeling/review_artifact_stub.json`
- 受け渡し条件:
  - 主空間基準が一意に決まっている
  - `ARCore pose` と intrinsics が `DA3Metric-Large` 入力として成立している
  - 比較対象 route の quality、runtime、resource usage、failure reason が同一指標で記録されている
  - 暫定採用 route と research route が分離されている
  - `Colab` account 未取得時も local sample 実行で logic 検証済みである

### 分担 3: `TrajectoryReconstruction`

- 担当: 人物経路再構成、再拘束、不確実性付与
- 前段から受け取るもの:
  - `SessionPackage`
  - `SpacePackage`
  - `member_identity_map.json`
  - `main_camera_path.csv`
  - `space_quality.json`
- 次段へ渡すもの:
  - `TrajectoryPackage`
  - `trajectory_quality.json`
  - `relink_events.json`
  - `attention_seed.json`
- 受け渡し条件:
  - 主カメラ path と人物 path が主空間座標系に載っている
  - 不確実区間と再拘束点が識別できる

### 分担 4: `AssemblyAndViewer`

- 担当: 閲覧成果物組立、timeline 統合、viewer 表示
- 前段から受け取るもの:
  - `SpacePackage`
  - `TrajectoryPackage`
  - `space_quality.json`
  - `trajectory_quality.json`
  - `attention_seed.json`
- 最終出力:
  - `ReviewArtifact`
  - `viewer_manifest.json`
  - `timeline.json`
  - `attention_points.json`
  - `same_time_highlights.json`
- 受け渡し条件:
  - 閲覧時に必要な quality、`attention point`、同時刻ハイライトが欠落なく束ねられている
  - `Viewer` は read-only で扱える

## パッケージ契約

### `SessionPackage`

- 目的: 後段が迷わず扱える単一入力単位
- 必須要素: `session_id`、`timebase`、`frames`、`arcore_pose`、`imu`、`bt`、`quality`
- 任意要素: `gnss`
- 契約:
  - 全 record が共通単調時刻軸で比較できる
  - `frame_id` と `image_path` が一意である
  - 主体と端末の対応が追える
  - 取得元 raw だけでなく、`trajectreview` 派生の受理判定、品質、対応表を同梱または併設参照できる

### `SpacePackage`

- 目的: 主空間の唯一基準と再構成成果物を渡す
- 必須要素: `coordinate_system`、`valid_frames`、`rejected_frames`、`camera_path`、`colmap`、`gs_model`、`quality`
- 契約:
  - `GNSS` がない場合は `ARCore` local 空間を唯一基準とする
  - `camera_path` は `timestamp_ns` を持つ
  - 主カメラ path と空間品質の報告を含む

### `TrajectoryPackage`

- 目的: 主空間座標系上に登録された主カメラ経路と人物経路を渡す
- 必須要素: `machine_trajectory`、`worker_trajectories`、`uncertainty`、`anchors`、`relinks`、`timeline`
- 契約:
  - すべての path は `SpacePackage.coordinate_system` に従う
  - 各人物 path は `member_id` と一意対応する
  - 見失い区間は不確実性 mode で識別できる

### `ReviewArtifact`

- 目的: 開けばレビューを開始できる完成成果物
- 必須要素: `viewer_manifest`、`timeline`、`ui_config`、`space_assets`、`trajectory_assets`、`entrypoint`
- 契約:
  - `Assembly` だけが生成する
  - `Viewer` は閲覧専用で消費する
  - 時刻スライダは `TrajectoryPackage.timeline` と一致する
  - 同時刻ハイライト情報を含む

## `iSensorium` 由来出力と追加出力

- `Xperia 5 III` の設定条件、recording mode、raw output、時刻整列、sample count の詳細は `isensorium_xperia5iii_intake_spec.md` を正本とする
- `iSensorium` source code、Python parser、script、gradle wrapper の verified 参照実体は `--products/prj-kisaragi_0002/reference_isensorium_verified_20260325/` に置き、確認結果は `--evidence/prj-kisaragi_0002/isensorium_verified_reference_snapshot.md` を正本とする

### `iSensorium` 由来の入力正本

- `session_manifest.json` または `manifest.json`
- `video_frame_timestamps.csv` または `frames.csv`
- `imu.csv`
- `gnss.csv`
- `bt.jsonl` または `ble_scan.jsonl` または `bt_events.csv` または `bt.csv`
- `poses.jsonl` または `arcore_pose.jsonl`
- legacy alias として `bt_events.csv`、`arcore_pose.csv` も受理対象に含める

### `trajectreview` で追加生成する出力

- `input_readiness.json`: 必須入力、任意入力、次 action 判定
- `sensor_quality.json`: stream ごとの品質低下と診断理由、時刻整列 delta、completeness score、pose coverage ratio
- `frame_pose_index.csv`: frame と pose の対応表
- `camera_calibration_summary.json`: `ARCore` frame timestamp、camera intrinsics、texture intrinsics、lens distortion の収集要約
- `member_identity_map.json`: 端末、主体、`BT` の対応表
- `session_package.json`: 後段へ渡すための正規化済み `SessionPackage` 実体
- `space_handoff_manifest.json`: `SpaceReconstruction` 着手可否、blocker、利用 artifact の要約
- `modeling/local_model_summary.json`: `Colab` 前の軽量 local sample model 結果
- `modeling/experiment_manifest.json`: route ごとの frame sampling、intrinsics mode、depth projection、resource 制約、出力先の定義
- `modeling/da3_input_manifest.json`: `DA3Metric-Large` に渡す画像入力、`ARCore` pose、intrinsics 指定
- `modeling/depth_estimation_report.json`: metric depth 推定の主要指標と failure reason
- `modeling/benchmark_summary.json`: sampling / intrinsics route ごとの比較結果
- `modeling/selected_route.json`: 暫定採用 route、research route、不採用理由、再評価条件
- `modeling/colab_job_request.json`: `Colab` remote 実行へ渡す request
- `modeling/review_artifact_stub.json`: reviewing app と統合 app が読む review 用 stub
- `modeling/modeling_handoff_manifest.json`: reviewing 着手可否と blocker の要約
- `space_quality.json`: 主空間品質と coverage の要約
- `trajectory_quality.json`: 経路品質と不確実区間の要約
- `attention_seed.json`: `attention point` 候補の種
- `same_time_highlights.json`: 同じ時刻の位置関係を強調表示するための候補

## 抽出 bundle layout

- `InputPackaging` の app 抽出結果は `session_id/isensorium/` と `session_id/trajectreview/` に分離する
- `isensorium/` には source 側の raw file を保持する
- `trajectreview/` には readiness、quality、frame-pose 対応、identity map、`session_package.json`、`space_handoff_manifest.json` を保持する
- app UI は抽出元、抽出先、`ready_for_diagnose`、`ready_for_space_reconstruction`、欠落入力、主要数値を表示できる
- app は session folder 直下だけでなく、manifest を持つ 1 段下の child directory も抽出対象として受理する
- `trajectreview-correcting` の wireless PC transfer は、同一 `Wi-Fi` 上の PC を UDP bootstrap で検出し、Android 側では `multicast lock` と同一 subnet への追加 probe を使って候補探索し、PC 側 bootstrap は `Tailscale` や仮想 NIC よりも `Wi-Fi` の `192.168.*` address を優先して返す
- `trajectreview-correcting` の `data-check` は記録停止後に自動実行し、新しい記録開始時には成功回数を `0` に戻す
- `poseCoverageRatio` は `pose数 / frame数` ではなく、session 長と `arCoreIntervalMs` から見積もった期待 pose sample 数に対する達成率で扱う
- `trajectreview-correcting` は app 内の作業用 session を保持しつつ、user が選んだ保存先へ停止後と `data-check` 後に session 一式を同期する
- `trajectreview-correcting` の `ARCore` 記録は `Session.update()` で得た同一 frame の pose、frame timestamp、image intrinsics、texture intrinsics、lens distortion を 1 record として `arcore_pose.jsonl` へ保存する
- PC 側 companion script は `correcting/scripts/pc-transfer-bootstrap.ps1` と `correcting/scripts/pc-transfer-receiver.ps1` を正本とし、`receiver` は idle 後に自動終了する
- PC 側既定保存先は `kisaragi-db/--exsams/prj-kisaragi_0002/pc-transfer-inbox/` とする

## `GNSS` なし前提の成立条件

- 主 `ARCore` 空間が唯一基準として安定している
- `ARCore` tracking quality を入力時点から厳格に記録する
- 人物の主体維持を `BT` で支える
- 人物が再び見えた時に視覚再拘束できる
- 見失い区間は橋渡ししても、不確実性を必ず残す
- `GNSS` がない場合は絶対位置合わせを捨て、主空間への再拘束を正しさの基準にする

## 責務境界

- `InputPackaging`: sensor 統合、時刻整列、品質フラグ、`SessionPackage` 生成
- `Preprocess`: frame 選別、再構成可否の前処理、診断用 summary
- `COLMAP`: valid frame set 確定、camera pose 推定、densification readiness 判定
- `3DGS`: scene representation 生成
- `Trajectory`: 人物 path 推定、再拘束、主体対応、不確実性付与
- `Assembly`: `SpacePackage`、`TrajectoryPackage`、`Timeline` を統合し `ReviewArtifact` を生成
- `Viewer`: 生成済み成果物を読む閲覧面

## 非目標

- Android app 内で重い再構成を完結させること
- `COLMAP` や `3DGS` engine 本体をこの project 内で内製すること
- `GNSS` 前提の地図表示や地理参照を既定 UX にすること
- 外部一時文書を正本のまま残し続けること

## 成功条件

- 利用者が迷わない
- 状態と理由が分かる
- 主カメラ経路と人物経路を同時刻で比較できる
- 不確実性を含めてレビューできる
- `attention point` と同時刻ハイライトから次の判断へ進める
- 外部参照が消えても `prj-kisaragi_0002` の正本文書だけで再開できる
