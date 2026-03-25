# iSensorium Xperia5III intake spec

この文書は `prj-kisaragi_0002` が `iSensorium` source data を受理するための `Xperia 5 III` 実装依存仕様を保持する正本とする。

## 対象

- 対象端末: `Xperia 5 III`
- 確認済み機種名: `SO-53B`
- source 実装参照元: `C:\Users\tetsuya\sandbox\codev-db`
- `trajectreview` はこの仕様を前提に `InputPackaging` を行う

## 端末設定

### 必須権限

- `CAMERA`
- `RECORD_AUDIO`
- `ACCESS_FINE_LOCATION`
- `ACCESS_COARSE_LOCATION`
- `BLUETOOTH_SCAN`
- `BLUETOOTH_CONNECT`

### 事前状態

- 位置情報を `ON` にする。`GNSS` を取らない運用でも、実装上は location permission を前提にしている
- `Bluetooth` を `ON` にする。`BLE` を無効設定で運用する場合でも、再設定の余地を残す
- `Google Play Services for AR` を利用可能な状態にする。`ARCore` 自体は任意だが、有効時はこの依存がある
- 十分な空き容量を確保する。`video.mp4` を含む session directory が作られる

## 記録モード

### `STANDARD_HANDHELD`

- 主用途: 手持ち計測
- 既定値:
  - `videoFrameLogIntervalMs = 100`
  - `imuIntervalMs = 20`
  - `gnssIntervalMs = 1000`
  - `bleIntervalMs = 2000`
  - `arCoreIntervalMs = 2000`
  - `bleEnabled = true`
  - `arCoreEnabled = true`

### `POCKET_RECORDING`

- 主用途: ポケット収納計測
- 実装上の補正:
  - `videoFrameLogIntervalMs` は最小 `250 ms`
  - `bleIntervalMs` は `BLE` 有効時の最小 `5000 ms`
  - `arCoreIntervalMs` は `ARCore` 有効時の最小 `5000 ms`
- 振る舞い:
  - `動画・IMU・GNSS` を主軸に扱う
  - `BLE / ARCore` は低頻度確認として扱う

## session directory と出力 file

1 session ごとに `session-YYYYMMDD-HHMMSS` 形式の directory が作られ、少なくとも次を出力する。

| stream | file | 内容 |
| --- | --- | --- |
| manifest | `session_manifest.json` | session 全体 metadata、timebase、config、sample count、collector 状態 |
| video | `video.mp4` | 主カメラ動画 |
| frame timeline | `video_frame_timestamps.csv` | 動画 frame と単調時刻の対応 |
| imu | `imu.csv` | `IMU` 系 sample |
| gnss | `gnss.csv` | `GNSS` sample |
| ble | `ble_scan.jsonl` | `BLE` scan event |
| arcore | `arcore_pose.jsonl` | `ARCore` pose sample |
| video events | `video_events.jsonl` | recording start / status / finalize などの event |

## 時刻整列仕様

- すべての stream の整列基準は `elapsedRealtimeNanos` と session 単位の monotonic origin とする
- `session_manifest.json` の `timebase` は次を持つ
  - `sessionStartWallTimeMs`
  - `sessionStartElapsedRealtimeNanos`
- `video_frame_timestamps.csv` は `sensorTimestampNs`、`elapsedRealtimeNanos`、`wallTimeMillis`、`rotationDegrees`、`sessionElapsed` を出力する
- `ble_scan.jsonl`、`arcore_pose.jsonl`、`video_events.jsonl` は各 record に `elapsedRealtimeNanos` を持つ
- `imu.csv` と `gnss.csv` は parser 側で `elapsed_realtime_ns` を参照して join できる前提で扱う

## どのデータがどれだけ取れるか

### raw stream

- 動画本体: `video.mp4` 1 file
- frame timeline: `video_frame_timestamps.csv` の全行数
- `IMU`: `imu.csv` の全行数
- `GNSS`: `gnss.csv` の全行数
- `BLE`: `ble_scan.jsonl` の全行数
- `ARCore`: `arcore_pose.jsonl` の全行数

### 数量確認に使う正本値

- `session_manifest.json` は finalize 時に次を持つ
  - `imuSampleCount`
  - `gnssSampleCount`
  - `bleSampleCount`
  - `arCoreSampleCount`
  - `collectorStatus`
  - `files`
- `files` には各 output file の name と size を入れられる
- frame 数は `video_frame_timestamps.csv` の行数で把握する

### 名目上の取得間隔

| stream | 名目間隔 | 補足 |
| --- | --- | --- |
| frame timeline | `100 ms` | `POCKET_RECORDING` では最小 `250 ms` |
| `IMU` | `20 ms` | 約 `50 Hz` 相当 |
| `GNSS` | `1000 ms` | 約 `1 Hz` 相当 |
| `BLE` | `2000 ms` | `POCKET_RECORDING` では最小 `5000 ms` |
| `ARCore` | `2000 ms` | `POCKET_RECORDING` では最小 `5000 ms` |

- 実際の件数は端末状態、権限、tracking 状態、OS 制約で増減する
- `trajectreview` 側では名目値ではなく、manifest の sample count と実 file 行数を正として intake する

## `trajectreview` が intake で使う判断材料

- manifest:
  - `sessionId`
  - `status`
  - `deviceModel`
  - `recordingMode`
  - `recordingConfig`
  - `modeBehavior`
  - `timebase`
  - `collectorStatus`
- file presence:
  - `video.mp4`
  - `video_frame_timestamps.csv`
  - `imu.csv`
  - `gnss.csv`
  - `ble_scan.jsonl`
  - `arcore_pose.jsonl`
  - `video_events.jsonl`
- 数量:
  - `imuSampleCount`
  - `gnssSampleCount`
  - `bleSampleCount`
  - `arCoreSampleCount`
  - frame 行数
- 時刻整列:
  - `sessionStartElapsedRealtimeNanos`
  - 各 stream の `elapsedRealtimeNanos` または `elapsed_realtime_ns`

## `trajectreview` への示唆

- `GNSS` は source 実装では標準出力だが、`trajectreview` では任意入力として扱う
- `BLE` と `ARCore` は欠落しても session 自体は存在し得るため、必須入力と optional input を分けて intake する
- `Xperia 5 III` 実装では `deviceModel` が manifest に入るため、target hardware 妥当性確認に使える
- 数量確認は sample count と file 行数の両方で行い、片側だけを真実とみなさない
