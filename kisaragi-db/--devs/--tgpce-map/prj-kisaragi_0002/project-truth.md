# project-truth

この文書は `prj-kisaragi_0002` の恒久的な真実を保持する正本とする。Concept of truth.

## 目的

`trajectreview` は、1 台のスマホカメラとその `IMU` による連続動画、および動画へ頻繁に映り込む人物が持つ `IMU` 付き機器の記録を単一セッションとして受理し、主空間の再構成、主カメラ経路と人物経路の再構成、閲覧成果物の組立までを一貫して扱い、レビュー判断を迷わず進められる作業空間を提供する。

- 利用者は常に次に取るべき行動を 1 件だけ受け取れる。
- 利用者は `Thin Status` で処理段階、品質低下、阻害理由を薄く常時把握できる。
- 利用者は主空間、主カメラ経路、人物経路を同じ `Timeline` で見比べ、同時刻ハイライトと `attention point` からレビュー判断へ進める。
- 運営者は外部 project や一時文書に依存せず、`prj-kisaragi_0002` 配下だけで計画、実装、検証を継続できる。
- 主空間収録主体は `ARCore` 連携スマホカメラを持ち、連続動画と `IMU` を記録して主空間の基準となる。
- 人物主体は動画なしの携行スマートフォンを持ち、`IMU` と必要に応じて `BT` を中心に時系列追跡される。
- 人物は主カメラ動画へ頻繁に映り込み、人物経路の再拘束に使える。
- `GNSS` は任意入力とし、ない場合でも成立する設計を既定とする。
- `GNSS` がない場合は主 `ARCore` 空間を唯一の基準座標とする。
- 現場らしく見える `3DGS` 空間、主カメラ経路、人物経路、同時刻ハイライト、不確実区間を同じ review 文脈で扱えることを提供価値とする。

## 完成判定

- `trajectreview` の完成判定は `本来機能が app 内で実行できること` を基準とする。
- `UX 確認`、`contract 固定`、`build / install`、`local sample`、`stub 読込` は価値のある中間成果だが、完成そのものではない。
- `pass` を付ける時は、対象 app が本来の入出力を扱い、後段が消費する実生成物を出し、主要 blocker が残っていないことを要件とする。
- 利用者が迷わず進められ、状態と理由が分かり、主カメラ経路と人物経路を同時刻で比較でき、不確実性を含めてレビューでき、`attention point` と同時刻ハイライトから次の判断へ進めることを成功条件とする。
- Android app 内で重い再構成を完結させること、`COLMAP` や `3DGS` engine 本体を内製すること、`GNSS` 前提の地図表示を既定 UX にすること、外部一時文書を正本のまま残し続けることは非目標とする。

## 利用入口

- `trajectreview-correcting`、`trajectreview-modeling`、`trajectreview-reviewing`、統合 app、既存 session intake は、開発中から実使用まで閉じずに併存させる。
- 現場記録の標準例は `trajectreview-correcting` を使って説明してよいが、他入口を補助扱いとして閉じない。
- どの入口から入っても、後段は同じ artifact 契約へ収束する。
- 操作説明の優先順、実装優先順、`MRL` の進行順はあり得るが、それは `ux-b2t-hypo.md` で管理し、この文書では入口の可否差にしない。

## UX 原則

- `Next Action` は常に 1 件だけ提示する。
- `Thin Status` は `phase`、`pipeline`、`data_health`、`quality`、`issues` の 5 項目を基本とする。
- 利用者に探索を強要せず、レビューすべき `attention point` と同時刻ハイライトを時間範囲と理由付きで提示する。
- 正常時は薄く、異常時だけ強調する。
- `Timeline` を統合キーとして、space、trajectory、同時刻ハイライト、`attention point`、summary を束ねる。

### UX フェーズ

- `Intake`: 入力セッション folder から主カメラ動画と `IMU`、人物側 `IMU` を抽出し、単一セッションとして受理する。
- `Diagnose`: 実行可否と入力品質を判定する。
- `Run`: 一括処理 pipeline を進行させる。
- `Verify`: 空間品質と経路品質の成立を確認する。
- `Interpret`: レビューと改善判断を行う。

## 段階構造

- app 構成は `trajectreview-correcting`、`trajectreview-modeling`、`trajectreview-reviewing`、統合 app の 4 実行入口を許容する。
- 4 app は、複数人分担や手戻り時の原因分析速度を上げるための作業境界であり、実際の開発主体が admin と Codex の 2 名であることと矛盾しない。

### `InputPackaging`

- 責務: 現場記録、既存 session intake、端末内同期、`Google Drive` 転送を含む入力パッケージ化を行い、単一セッション入力へ正規化する。
- 主な処理: 現場記録、session folder intake、raw file 抽出、frame 抽出、`ARCore` pose 整理、`IMU` 整理、`BT` 整理、時刻整列、品質フラグ付与、端末内同期、`Google Drive` zip 転送。
- 入口: 現場記録起点、既存 session intake 起点、統合 app 起点のいずれから入っても同じ `SessionPackage` 契約へ収束する。
- 運搬面: `端末保存先` と `Google Drive` 転送先に分かれ、前者は `<session_id>/`、後者は zip を正本とする。
- post-recording 処理順: `raw 保存 -> 品質確認 -> derived 同期` を正とする。

### `SpaceReconstruction`

- 責務: 主空間の基準座標と再構成成果物を作る。
- 主な処理: frame 選別、`DA3Metric-Large` 入力生成、metric depth 推定、`ARCore pose` による world projection、空間品質集約。

### `TrajectoryReconstruction`

- 責務: 主カメラ経路と人物経路を主空間へ登録する。
- 主な処理: 主カメラ経路生成、人物 path 推定、`BT` による主体維持、視覚再拘束、見失い区間橋渡し、不確実性付与。

### `AssemblyAndViewer`

- 責務: 閲覧可能な成果物を組み立て、viewer で読む。
- 主な処理: timeline 生成、主体表示定義、同時刻ハイライト定義、`attention point` 統合、閲覧 manifest 生成。

## app 責務

### `trajectreview-correcting`

- 対象段階: `InputPackaging`
- 主責務: 現場記録、取得条件設定、source session 保存、入力補正の起点作成
- 完成条件:
  - camera / IMU / GNSS / BLE / ARCore 記録画面を持ち、source session を端末内へ保存する。
  - 同じ app 内で `session_package.json`、`sensor_quality.json`、`space_handoff_manifest.json`、`camera_calibration_summary.json` を生成する。
  - `data-check` が readiness、quality、blocker、recommended correction を返す。
  - preview 直下の状態表示に `現場の風景と経路を記録します。1. 条件設定⇒2. 収録⇒3. 転送` を置く。
  - `Data収録開始` は `端末保存先` 未設定の間は非活性とし、未設定時だけ `端末保存先：未設定` を表示する。
  - `品質確認` の詳細結果は popup で表示し、メイン画面には閾値未満の項目名だけを短く表示する。
  - `端末保存先` 同期中は session 詳細を縮退し、`Session: <session_id>` と `品質確認OK` だけを見せる。
  - `転送先を選択` は `Google Drive` URL 入力 / 保存と Android 標準保存画面経由の zip 保存先選択を兼ねる。
  - `Google Drive` の転送先 file は毎回 user が指定する。
  - `Google Drive` 転送 zip の既定名は、名称未指定なら `trajectreview-correcting-session-YYYYMMDD-HHMMSS.zip` とし、data 名を使う時も `<data-name>-session-YYYYMMDD-HHMMSS.zip` の形で `session-*` suffix を保持する。
  - `転送Data選択` と `Data名称変更` は保存済み session を扱う button 一覧 popup を持ち、warning または blocker を持つ data 名の先頭に `▲` を付け、取得日時と長さを確認できる。
  - `Data名称変更` popup は `戻る` button、`OFF：名称変更、ON：削除モード` toggle、`削除実行` button を持つ。
  - calibration 診断は `読取試行あり成功 0 件`、`coverage 低下`、`calibration export 実装前 data の可能性` を区別する。
  - `ARCore` 記録は同一 frame の pose、frame timestamp、image intrinsics、texture intrinsics、lens distortion を 1 record として保存する。

### `trajectreview-modeling`

- 対象段階: `SpaceReconstruction`、`TrajectoryReconstruction`
- 主責務: request 起点受付、model 入力確認、実行 gate、進行把握、result 受け渡し
- 完成条件:
  - スマホまたは PC からの request を起点に、`Google Drive` 上の input directory と result directory を指定した `Colab` job request を生成できる。
  - `Colab bootstrap package` が指定 directory から zip または `session_root/` を正規化し、runtime、dependency install、config、status 更新先、output path を再現可能に構築できる。
  - request 元画面は remote 実行中に waiting ring、現在段階、直近更新時刻を読み続けられる。
  - `DA3Metric-Large` による metric depth 推定と `ARCore pose` / intrinsics による world projection を実行し、主要 quality 指標と failure reason を route 単位で記録する。
  - 複数の sampling / intrinsics route を比較し、`benchmark_summary.json` と `selected_route.json` により暫定採用 route を固定する。
  - remote 実行完了後に download URL と result summary を返し、remote 実行結果を受理して `SpacePackage`、`TrajectoryPackage`、`space_quality.json`、`trajectory_quality.json`、`attention_seed.json` を更新する。
  - `local sample before colab` は preflight 用補助 route とし、完成判定の代替に使わない。

### `trajectreview-reviewing`

- 対象段階: `AssemblyAndViewer`
- 主責務: verify、review、same-time highlight、`attention point` 確認
- 完成条件:
  - `ReviewArtifact` 実体を読み、viewer、timeline、same-time highlight、`attention point` jump を提供する。
  - summary / stub 読込だけでなく、後段成果物そのものを利用者が操作できる。

### 統合 app

- 対象段階: 全段階
- 主責務: correcting、modeling、reviewing の全 workflow を 1 つの視点で束ねる
- 完成条件:
  - correcting、modeling、reviewing の本来機能を 1 app から順につなげられる。
  - workflow 全体の現在地と blocker を示しつつ、各段階の実生成物へ到達できる。

## artifact 契約

### `SessionPackage`

- 目的: 後段が迷わず扱える単一入力単位
- 必須要素: `session_id`、`timebase`、`frames`、`arcore_pose`、`imu`、`bt`、`quality`
- 任意要素: `gnss`
- 契約:
  - 全 record が共通単調時刻軸で比較できる。
  - `frame_id` と `image_path` が一意である。
  - 主体と端末の対応が追える。
  - 取得元 raw だけでなく、`trajectreview` 派生の受理判定、品質、対応表を同梱または併設参照できる。

### `SpacePackage`

- 目的: 主空間の唯一基準と再構成成果物を渡す
- 必須要素: `coordinate_system`、`valid_frames`、`rejected_frames`、`camera_path`、`colmap`、`gs_model`、`quality`
- 契約:
  - `GNSS` がない場合は `ARCore` local 空間を唯一基準とする。
  - `camera_path` は `timestamp_ns` を持つ。
  - 主カメラ path と空間品質の報告を含む。

### `TrajectoryPackage`

- 目的: 主空間座標系上に登録された主カメラ経路と人物経路を渡す
- 必須要素: `machine_trajectory`、`worker_trajectories`、`uncertainty`、`anchors`、`relinks`、`timeline`
- 契約:
  - すべての path は `SpacePackage.coordinate_system` に従う。
  - 各人物 path は `member_id` と一意対応する。
  - 見失い区間は不確実性 mode で識別できる。

### `ReviewArtifact`

- 目的: 開けばレビューを開始できる完成成果物
- 必須要素: `viewer_manifest`、`timeline`、`ui_config`、`space_assets`、`trajectory_assets`、`entrypoint`
- 契約:
  - `Assembly` だけが生成する。
  - `Viewer` は閲覧専用で消費する。
  - 時刻スライダは `TrajectoryPackage.timeline` と一致する。
  - 同時刻ハイライト情報を含む。

### 主要 file 契約

- `input_readiness.json`: 必須入力、任意入力、次 action 判定
- `sensor_quality.json`: stream ごとの品質低下と診断理由、時刻整列 delta、completeness score、pose coverage ratio
- `frame_pose_index.csv`: frame と pose の対応表
- `camera_calibration_summary.json`: `ARCore` frame timestamp、camera intrinsics、texture intrinsics、lens distortion の収集要約
- `member_identity_map.json`: 端末、主体、`BT` の対応表
- `session_package.json`: 正規化済み `SessionPackage` 実体
- `space_handoff_manifest.json`: `SpaceReconstruction` 着手可否、blocker、利用 artifact の要約
- `modeling/experiment_manifest.json`: route ごとの frame sampling、intrinsics mode、depth projection、resource 制約、出力先の定義
- `modeling/da3_input_manifest.json`: `DA3Metric-Large` に渡す画像入力、`ARCore` pose、intrinsics 指定
- `modeling/benchmark_summary.json`: sampling / intrinsics route ごとの比較結果
- `modeling/selected_route.json`: 暫定採用 route、research route、不採用理由、再評価条件
- `modeling/colab_job_request.json`: request 元、input directory、result directory、`Colab` remote 実行 parameter を束ねた request
- `modeling/job_status.json`: stage、updated_at、result availability、download URL、error summary
- `modeling/review_artifact_stub.json`: reviewing app と統合 app が読む review 用 stub
- `modeling/modeling_handoff_manifest.json`: reviewing 着手可否と blocker の要約
- `space_quality.json`: 主空間品質と coverage の要約
- `trajectory_quality.json`: 経路品質と不確実区間の要約
- `attention_seed.json`: `attention point` 候補の種
- `same_time_highlights.json`: 同じ時刻の位置関係を強調表示するための候補

## 外部連携境界

### package / bootstrap

- この project では、準備 UX、配布、install、bootstrap、実行環境整備も利用者主導 `MRL` / `mRL` の前段 gate として管理する。
- `trajectreview-modeling` の package は `Colab all-in` を主 route とし、`Google Drive` の指定 directory から zip または `session_root/` を受けて `session_root/` を正規化する `Colab bootstrap package` を持つ。
- PC 側は `Colab bootstrap package` の source、install script、config template、notebook template、version 固定情報、証跡を保持する。
- 既存の `COLMAP 4.0 + nerfstudio splatfacto` notebook は参考ひな形であり、`DA3Metric-Large` modeling の正本ではない。
- `DA3Metric-Large` の `Colab` 実装は greenfield とし、`Codex` が script / notebook を作成し、admin が `Colab` 実行結果を shared worklog に貼り戻す往復で具体化する。
- shared worklog は project に対する truth / plan / evidence の正本ではないが、共同作業の保持情報としては authoritative な log であり、正本反映の根拠 log として保持する。
- shared worklog の置き場は `--tgpce-map/prj-kisaragi_****/` 直下とし、file 名は `sharedlogs_<thema>.md` 形式に統一する。
- shared worklog を使う時は、読みやすさのために定型 header を持ち、header より下は `# codex` または `# admin` 見出しで末尾追記のみとする。
- 採用判断、gate 状態、artifact 契約、manual、evidence は必ず対応する正本文書または証跡文書へ別途反映する。
- shared worklog は定期的に振り返り、持続価値のある内容を `project-truth.md`、`ux-b2t-hypo.md`、admin evidence、product runbook へ反映した後、old log 本文を削除または reset してよい。
- `Colab` や remote notebook のように runtime が揮発する route では、途中修復手順ではなく fresh runtime からの最短 clean bootstrap を canonical route とする。
- 上記 route では、shared worklog の trial 往復とは別に、`--products/prj-kisaragi_0002/` 配下へ `最小 clean bootstrap runbook` を保持することを必須とする。
- `最小 clean bootstrap runbook` は `candidate` と `adopted` を分け、admin 実測で end-to-end 完了した手順だけを `truly pass` 扱いとする。
- 現在の `DA3Metric-Large` `Colab bootstrap` の正本は `--products/prj-kisaragi_0002/modeling/da3_colab_clean_bootstrap_runbook.md` とする。
- 上記 runbook の admin 実行は、`MRL-3` / `mRL-3.1` の bootstrap UX、`MRL-4` / `mRL-4.2` の `Google Drive` directory bootstrap、`MRL-5` / `mRL-5.2` の `Colab` metric depth 実行の candidate evidence を兼ねる。
- 現段階の DA3 bootstrap は、`GPU` を選べても最初は `CPU` で bootstrap / import / `1 frame` 推論確認を進めてよい。
- bootstrap 仕様が未確定な間は、blank restart だけに固定せず、同一 runtime で blocker を潰しながら `最小 clean bootstrap runbook` へ反映してよい。
- `2026-03-29` 時点で、admin 実測により `T4` 上の `Adopted Bootstrap v1` が成立し、single-frame の `DA3Metric-Large` metric depth 推論と `summary.json` 出力は end-to-end で通過した。
- `trajectreview-correcting` は Android app を正本実行入口としつつ、PC install package も別 process で設計し、artifact 互換性、保存先構成、導線を固定する。

### modeling route

- `DA3Metric-Large` を first target の metric depth 基盤とする。
- 最初から最終 route を固定せず、少なくとも `5fps`、`10fps`、`per-frame intrinsics` を比較候補として扱う。
- depth route は quality、runtime、resource usage、failure rate を比較して暫定採用 route を決める。
- route 比較は同一 session、同一 export contract、同一評価指標で行う。
- 暫定採用 route と research route は `selected_route.json` で分離し、既定 route の変更履歴を追えるようにする。

### `iSensorium` と intake source

- `Xperia 5 III` の設定条件、recording mode、raw output、時刻整列、sample count の詳細はこの文書末尾の `Xperia 5 III intake detail` に統合して保持する。
- `iSensorium` 由来で吸収した recording / parser / script の実装は、`--products/prj-kisaragi_0002/correcting/`、`--products/prj-kisaragi_0002/python/`、`--products/prj-kisaragi_0002/correcting/scripts/` を現行正規とする。旧 reference 配置は吸収済みで、以後の開発と検証は吸収後 path を使う。
- `iSensorium` 由来の入力正本は `session_manifest.json` または `manifest.json`、`video_frame_timestamps.csv` または `frames.csv`、`imu.csv`、`gnss.csv`、`bt.jsonl` または `ble_scan.jsonl` または `bt_events.csv` または `bt.csv`、`poses.jsonl` または `arcore_pose.jsonl` とする。
- legacy alias として `bt_events.csv`、`arcore_pose.csv` も受理対象に含める。

### `Xperia 5 III` intake detail

- 対象端末は `Xperia 5 III`、確認済み機種名は `SO-53B` とする。
- source 実装参照元は `C:\Users\tetsuya\sandbox\codev-db` だが、`trajectreview` は `kisaragi` 側へ吸収した仕様と現行正規配置を正として扱う。

#### 端末設定

- 必須権限は `CAMERA`、`RECORD_AUDIO`、`ACCESS_FINE_LOCATION`、`ACCESS_COARSE_LOCATION`、`BLUETOOTH_SCAN`、`BLUETOOTH_CONNECT` とする。
- 位置情報は `ON` を前提とする。`GNSS` を使わない運用でも、実装上は location permission を前提にする。
- `Bluetooth` は `ON` を前提とする。`BLE` を無効設定で運用する場合でも、再設定可能な状態を保つ。
- `Google Play Services for AR` が利用可能であることを前提にする。`ARCore` 自体は任意だが、有効時はこの依存がある。
- `video.mp4` を含む session directory を作れる空き容量を確保する。

#### 記録モード

- `STANDARD_HANDHELD` の既定値は `videoFrameLogIntervalMs = 100`、`imuIntervalMs = 20`、`gnssIntervalMs = 1000`、`bleIntervalMs = 2000`、`arCoreIntervalMs = 2000`、`bleEnabled = true`、`arCoreEnabled = true` とする。
- `POCKET_RECORDING` では `videoFrameLogIntervalMs` の最小を `250 ms`、`bleIntervalMs` の最小を `5000 ms`、`arCoreIntervalMs` の最小を `5000 ms` とし、`動画・IMU・GNSS` を主軸、`BLE / ARCore` を低頻度確認として扱う。

#### session directory と raw file

- 1 session ごとに `session-YYYYMMDD-HHMMSS` 形式の directory を作る。
- raw file は少なくとも `session_manifest.json`、`video.mp4`、`video_frame_timestamps.csv`、`imu.csv`、`gnss.csv`、`ble_scan.jsonl`、`arcore_pose.jsonl`、`video_events.jsonl` を持つ。
- `session_manifest.json` は session 全体 metadata、timebase、config、sample count、collector 状態を保持する。

#### 時刻整列

- すべての stream の整列基準は `elapsedRealtimeNanos` と session 単位の monotonic origin とする。
- `session_manifest.json` の `timebase` は `sessionStartWallTimeMs` と `sessionStartElapsedRealtimeNanos` を持つ。
- `video_frame_timestamps.csv` は `sensorTimestampNs`、`elapsedRealtimeNanos`、`wallTimeMillis`、`rotationDegrees`、`sessionElapsed` を出力する。
- `ble_scan.jsonl`、`arcore_pose.jsonl`、`video_events.jsonl` は各 record に `elapsedRealtimeNanos` を持つ。
- `imu.csv` と `gnss.csv` は parser 側で `elapsed_realtime_ns` を参照して join できる前提で扱う。

#### 数量確認

- 動画本体は `video.mp4` 1 file とする。
- frame 数は `video_frame_timestamps.csv` の行数を正とする。
- `IMU`、`GNSS`、`BLE`、`ARCore` の数量は、それぞれ `imu.csv`、`gnss.csv`、`ble_scan.jsonl`、`arcore_pose.jsonl` の行数と `session_manifest.json` の sample count の両方で確認する。
- `session_manifest.json` は finalize 時に `imuSampleCount`、`gnssSampleCount`、`bleSampleCount`、`arCoreSampleCount`、`collectorStatus`、`files` を持つ。
- `files` には各 output file の name と size を入れられる前提とする。

#### 名目取得間隔

- frame timeline は `100 ms`、`POCKET_RECORDING` では最小 `250 ms` とする。
- `IMU` は `20 ms`、約 `50 Hz` 相当とする。
- `GNSS` は `1000 ms`、約 `1 Hz` 相当とする。
- `BLE` は `2000 ms`、`POCKET_RECORDING` では最小 `5000 ms` とする。
- `ARCore` は `2000 ms`、`POCKET_RECORDING` では最小 `5000 ms` とする。
- 実際の件数は端末状態、権限、tracking 状態、OS 制約で増減するため、`trajectreview` 側では名目値ではなく manifest の sample count と実 file 行数を正として intake する。

#### intake 判断材料

- manifest では `sessionId`、`status`、`deviceModel`、`recordingMode`、`recordingConfig`、`modeBehavior`、`timebase`、`collectorStatus` を読む。
- file presence では `video.mp4`、`video_frame_timestamps.csv`、`imu.csv`、`gnss.csv`、`ble_scan.jsonl`、`arcore_pose.jsonl`、`video_events.jsonl` を確認する。
- 数量では `imuSampleCount`、`gnssSampleCount`、`bleSampleCount`、`arCoreSampleCount`、frame 行数を確認する。
- 時刻整列では `sessionStartElapsedRealtimeNanos` と各 stream の `elapsedRealtimeNanos` または `elapsed_realtime_ns` を確認する。

#### intake 上の扱い

- `GNSS` は source 実装では標準出力だが、`trajectreview` では任意入力として扱う。
- `BLE` と `ARCore` は欠落しても session 自体は存在し得るため、必須入力と optional input を分けて intake する。
- `Xperia 5 III` 実装では `deviceModel` が manifest に入るため、target hardware 妥当性確認に使える。
- 数量確認は sample count と file 行数の両方で行い、片側だけを真実とみなさない。

### bundle layout と transfer

- app 抽出結果は `session_id/isensorium/` と `session_id/trajectreview/` に分離する。
- `isensorium/` には source 側の raw file を保持する。
- `trajectreview/` には readiness、quality、frame-pose 対応、identity map、`session_package.json`、`space_handoff_manifest.json` を保持する。
- app は session folder 直下だけでなく、manifest を持つ 1 段下の child directory も抽出対象として受理する。
- `trajectreview-correcting` の転送は `Storage Access Framework` による `Google Drive` 保存場所選択を正規経路とし、`撮影データ`、`センサ記録`、`data-check結果と後段受け渡し`、`frame画像群` を group 単位で選択して zip 転送する。
- `Google Drive` 事前設定の既定対象 folder は `https://drive.google.com/drive/u/2/folders/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_` とし、app 内の `転送先を選択` dialog の初期値として保持する。
- Android の標準保存画面は端末 storage が先に見えることがあるため、`Google Drive` を使う時は左上メニューなどから provider を `Google Drive` へ切り替える。
- `Google Drive` 転送先 file は毎回 user が指定する。
- network 経由の PC companion route は保留とし、現時点の正規 UX には含めない。
- 保存済み data 一覧の lightweight `品質確認` では `images/` 未生成を懸念扱いにしない。`images/` は `frame画像群` を要求した転送時にだけ評価対象へ入る。
- `images/` は `品質確認` では生成せず、`frame画像群` が実際に必要になった転送時だけ生成する。
- `images/` 生成時は全 frame ではなく pose に対応する代表 frame を優先抽出し、転送待ち時間を抑える。
- 旧 `trajectreview-correcting/<session_id>/` 形式のスマホ内保存先が見つかった時は、可能な範囲で保存先直下の `<session_id>/` 形式へ移行する。

### quality / warning / no-GNSS

- `品質確認` 結果は data ごとに `trajectreview/` 配下 artifact として保持し、保存済み data 一覧で warning または blocker を `▲` 付きで可視化する。
- `転送Data選択` と `Data名称変更` の一覧を開く時は、保存済み session の軽量 `品質確認` を再実行してから `▲` 判定を更新し、古い summary を残さない。
- `▲` は `blocker` または再撮影 / 再確認を要する閾値超え warning がある時だけ付ける。
- `poseCoverageRatio` は `pose数 / frame数` ではなく、session 長と `arCoreIntervalMs` から見積もった期待 pose sample 数に対する達成率で扱う。
- `corecamera_shared_camera_trial` route でも `OffscreenArCorePoseSampler` の callback から image intrinsics、texture intrinsics、capture diagnostics を `arcore_pose.jsonl` へ保存する。
- `corecamera_shared_camera_trial` route の `ARCore` sampling は `arCoreIntervalMs` に追従し、高頻度固定 sampling をしない。
- `trackingState` warning は `TRACKING` 以外を 1 frame 含むだけでは出さず、初期 warmup の少数 frame を許容する。
- `camera intrinsics` / `texture intrinsics` / `lens distortion` の warning は、対応率が実運用閾値を下回る時にだけ出す。
- `GNSS` がない場合は主 `ARCore` 空間を唯一基準とし、絶対位置合わせを捨て、主空間への再拘束を正しさの基準にする。
- 主 `ARCore` 空間が唯一基準として安定していること、`ARCore` tracking quality を入力時点から厳格に記録すること、人物の主体維持を `BT` で支えること、見失い区間に不確実性を残すことを `GNSS` なし前提の成立条件とする。
