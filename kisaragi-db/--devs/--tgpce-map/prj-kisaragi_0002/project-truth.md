# project-truth

この文書は `prj-kisaragi_0002` の恒久事項だけを保持する正本とする。

## 文書の役割

- 何を作るか
- 最小で何を成立させるか
- 何を後段へ回すか
- app / artifact / 外部境界をどう切るか

現在状態、未完 gate、優先順位、細かい運用順は [ux-b2t-hypo.md](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/ux-b2t-hypo.md) に置く。

## 最終目的

- 作業後に manager が、現場空間、人、作業機、時間の関係を確認し、作業 process を理解できるようにする。
- 最小構成で直接扱うのは、空間、移動、相対位置、時系列の把握である。
- 人がその場で具体的に何をしていたかの理解は、最小構成の範囲外とする。
- 最終到達点は `10時間` 作業の一貫処理、一貫閲覧とする。
- 最優先は `1分` 程度の動画で成立させることとする。

## 最小構成

- 最小構成名は `TraceCore` とする。
- `TraceCore` は、`3DGS` 上に主空間、主カメラ経路、人軌跡を重ね、移動、位置関係、時系列を把握できる最小構成とする。
- 人物個体 `ID` は最小構成では確定しない。
- `GNSS` は任意入力とし、ない場合は主 `ARCore` 空間を唯一基準とする。
- 短時間でも安っぽく見えないことを要件に含める。

### 最小構成で直接扱う価値

| 項目 | 内容 |
| --- | --- |
| 空間理解 | 現場の見た目と位置関係が分かる |
| 動き理解 | camera と人がどう動いたか分かる |
| 相対理解 | 人と camera の関係が分かる |
| 時系列理解 | どの順で動いたか分かる |
| 信頼感 | 確認に使える見た目である |

### 後段へ回すもの

| 項目 | 理由 |
| --- | --- |
| 人物個体 `ID` の確定 | 最小価値に必須ではない |
| 人物ごとの厳密再同定 | 初手で必要ない |
| 具体的な作業内容理解 | 背景と軌跡だけでは不足する |
| 高度な `IMU` 融合 | 初手として重い |
| `10時間` 対応 | 最終目標だが初手ではない |
| 高度分析 `UI` | まずは見えることが先である |

## レビュー価値仮説

- `TraceCore` は、何を表示するかだけでなく、どう見れば価値が出るかを先に固定する。
- 最小で価値が出る見方は、全体俯瞰、時系列再生、camera と人の相対表示、滞留箇所確認、軌跡の重なり確認とする。
- viewer や分析機能は、この見方を支援する方向で拡張する。

## 前提

| 項目 | 内容 |
| --- | --- |
| camera data | `ARCore` の `camera.pose` を正として、採択 frame ごとの pose、intrinsics、時刻同期情報、対応 image を同時取得できる |
| camera `IMU` | 動画撮影と同時取得できる |
| 人物側 `IMU` | 映り込む人が `IMU` 付き smartphone を保持している |
| 取得頻度 | `5` から `10fps` 程度 |
| 初期対象 | `1分` 程度の動画 |

## システム対象

本 project は次の 3 つを同時に扱う。

| 対象 | 内容 |
| --- | --- |
| 空間 | `DA3Metric-Large` と `3DGS` により再現する現場空間 |
| camera 経路 | 撮影側の移動 |
| 人経路 | 映り込む人の移動 |

この 3 つが同じ時間軸で結び付いて見えれば、最小 review 価値は成立する。

## 段階構造

| 段階 | 目的 |
| --- | --- |
| intake | 入力 bundle を正規化し、後段へ渡せる状態にする |
| modeling | 主空間と経路の成立可否を判断し、採用 route を決める |
| reviewing | 空間、経路、same-time highlight、`attention point` を review 可能に束ねる |
| scaling | 長尺化、品質改善、運用導線の安定化を行う |

## 開発原則

- 空間生成の主経路は、採択 frame ごとの image、`camera.pose`、intrinsics を正にした `DA3Metric-Large` / `3DGS` 前処理入力とする。
- remote modeling の canonical `Colab` route でも、主入力は `frame_record.jsonl` と対応 image 群を正とし、`frame_pose_index.csv` は診断用の二次資料として扱う。
- `Colab` 側は `1 record = image + pose + intrinsics + timestamp` の構造を壊さずに読み、`intrinsics[N,3,3]` と `extrinsics_w2c[N,4,4]` を canonical manifest として常に生成する。
- `DA3Metric-Large` の現行 canonical route は image-only 推論とし、`frame_record` 由来の `intrinsics` / `extrinsics_w2c` は world projection、QC、比較証跡に使う。
- `DA3 Giant` / `Giant Large` の現行 living route は `DA3NESTED-GIANT-LARGE-1.1` を使い、`da3_estimated pose` で `gs_ply` / `gs_video` を生成し、`debug_gs_readback` と bundle manifest を残す。
- 画像向きは main contract の一部とし、raw 向きのまま silently 扱わない。回転正規化を行う時は image 回転、`width` / `height`、`K` 補正、manifest 記録を同時に行う。
- `trajectreview-correcting` の canonical 静止画は、現行端末では raw image が左へ `90度` 倒れて見える前提で、record 保存時に `90度右回転` の portrait upright へ正規化して保持する。`frame_record.jsonl` の `imageIntrinsics` と manifest も同じ向き基準へそろえる。
- `Colab` runbook は `proof route` と `production route` を分離し、軽量確認と本番 candidate を混在させない。
- 通常の重い再構成 flow を主経路にしない。
- route は最初から 1 本に固定せず、比較したうえで暫定採用 route を決める。
- `IMU` は初期から全部統合せず、価値が大きい箇所に限定して使う。
- viewer 実装より先に、`TraceCore` の最小表示を成立させる。

## app 境界

| app | 主責務 |
| --- | --- |
| `trajectreview-correcting` | 現場記録、既存 session intake、入力 bundle 正規化、転送 |
| `trajectreview-modeling` | request 起点、remote modeling、route 比較、result 受け渡し |
| `trajectreview-reviewing` | verify、review、same-time highlight、`attention point` 表示 |
| 統合 app | 全 workflow の束ねと現在地表示 |

- 4 app は分担境界であり、どの入口から入っても後段は同じ artifact 契約へ収束する。
- `trajectreview-correcting` は前面表示中に端末を自動 sleep させず、少なくとも `通常計測` の `10min` 連続収録を first stability target とする。
- `trajectreview-correcting` の data 削除は、app 内 session root だけでなく `端末保存先` に同期済みの同名 directory まで含めて完了させる。
- `端末保存先` に正規に残るものは session directory だけとし、app が生成した転送 zip は削除時の cleanup 対象とする。

## スマホ側 data 抽出根拠

- `DA3` / `3DGS` 前段では、同一 update で観測した image、pose、intrinsics、timestamp の結び付きが壊れないことを最優先にする。
- そのため、smartphone 側では `ARCore Session.update()` の採択 frame を recording 中に直接 `frame_record` と対応 image へ保存し、転送後の nearest-link や再抽出を canonical route にしない。
- pose の正規値は画面向き依存の `displayOrientedPose` ではなく、後段計算で座標系の意味を固定しやすい `camera.pose` を使う。
- `video.mp4` は重要な再確認入力であり、取得品質の見直し、再抽出、debug、後段比較に使うため保持する。ただし canonical な時系列参照は採択 frame record 側に置く。
- `textureIntrinsics`、`lensDistortion`、`captureDiagnostics` は後段比較、端末差診断、quality audit に有益なため残すが、主入力成立の必須条件には置かない。
- image を取得できなかった update は、pose だけ残すと image と pose の時系列一貫性が壊れるため、主記録として採択しない。
- JPEG を毎 update 保存すると recording 安定性を損ないやすいため、保存対象は採択 frame のみに限定する。
- 学習用の静止画は raw sensor 向きのままでは左へ `90度` 倒れて読みにくいため、smartphone 側で `90度右回転` の upright JPEG を canonical image とする。その時は `imageIntrinsics.width` / `height` と principal point を同時に補正し、record と manifest に回転 policy を残す。
- 採択条件は data 契約の一部であるため、`Sampling条件` popup で user が収録前に確認・変更できるようにする。
- parser、transfer、runbook、modeling script は同じ canonical input を読む必要があるため、smartphone 側抽出方式の変更は app 内実装だけでなく handoff 契約全体へ同時反映する。

## artifact 契約

### `SessionPackage`

- 単一入力単位の正規化 artifact とする。
- この機能の記載名は、trajectreview-correctingとする。
- 主入力は、時系列一貫性を保つ canonical 参照として、採択 frame ごとの image と `camera.pose` / intrinsics を束ねた `frame_record` 系列とする。
- `video.mp4` は重要度を下げずに補助入力として保持し、再確認、再抽出、検証に使える状態を維持する。ただし `DA3` / `3DGS` 前段の canonical 時系列参照には置かない。
- `textureIntrinsics`、`lensDistortion`、`captureDiagnostics` は残してよいが、主入力成立の必須条件には置かない。
- `NotYetAvailableException` などで image を取得できなかった update は、主記録として採択しない。
- `trajectreview/image/` に保存する canonical 静止画は `90度右回転` の upright JPEG とし、`frame_record.jsonl` と manifest に同じ orientation policy を残す。
- `IMU`、`BT`、品質要約を同じ package へ束ねる。
- 任意入力として `GNSS` を許容する。
- 以降に渡すデータの一例を以下に示す。trajectreview-correctingがtrajectreview-modelingに渡すもの。

```text
session-20260402-034558/
  ble_scan.jsonl (14792 bytes)
  frame_record.jsonl (5298736 bytes)
  gnss.csv (2969 bytes)
  imu.csv (1505158 bytes)
  session_manifest.json (4746 bytes)
  trajectreview/
    camera_calibration_summary.json (1266 bytes)
    frame_pose_index.csv (531517 bytes)
    image/ (5336 jpg)
      first:
        frame_1324352771786398.jpg
        frame_1324352805150461.jpg
        frame_1324352838576222.jpg
      last:
        frame_1324530698930018.jpg
        frame_1324530732294028.jpg
        frame_1324530765658091.jpg
    input_readiness.json (366 bytes)
    member_identity_map.json (816 bytes)
    sensor_quality.json (1631 bytes)
    session_package.json (2339 bytes)
    space_handoff_manifest.json (694 bytes)
  video.mp4 (33005360 bytes)
  video_events.jsonl (331 bytes)
  video_frame_timestamps.csv (667797 bytes)

summary:
  frame_record_count: 5336
  image_count: 5336
  duration_sec: 177.993871693
  effective_fps: 29.9785602124742
```

### `SpacePackage`

- 主空間の唯一基準と再構成成果物を渡す。
- `GNSS` がない場合は主 `ARCore` local 空間を唯一基準とする。
- 主空間、主 camera path、空間品質、`gs_model` を含む。

### `TrajectoryPackage`

- 主空間座標系上の主 camera path と人物 path を渡す。
- 人物個体 `ID` が未確定でも path、不確実性、再拘束点、timeline を扱えるようにする。

### `ReviewArtifact`

- review 開始に必要な完成成果物とする。
- `Assembly` だけが生成する。
- `3DGS` 空間表現、経路、same-time highlight、`attention point`、timeline を含む。

## 外部境界

### remote modeling

- remote modeling の主経路は `Google Drive` と `Colab` を使う route とする。
- `Colab` runtime の bootstrap は product 側 runbook を正本とし、record-native canonical input、明示 `K` / `pose` 入力、`proof` / `production` 分離を同じ contract で維持する。

### route 比較

- `DA3Metric-Large` を first target の depth 基盤とする。
- route 比較は同一 session、同一 export contract、同一評価指標で行う。
- 比較結果は product 側の評価 artifact に集約し、採用 route は handoff 契約で固定する。

### input 受理

- `InputPackaging` は raw input を受理し、`SessionPackage` へ正規化する。
- legacy alias を含む複数入力名を受理してよいが、後段契約は `SessionPackage` へ統一する。

## UX 原則

- `Next Action` は常に 1 件だけ提示する。
- `Thin Status` は軽く読み取れることを優先する。
- `Timeline` を統合キーとして、space、trajectory、same-time highlight、`attention point` を束ねる。
- 正常時は薄く、異常時だけ強調する。
- `correcting` の収録中 status には、収録開始からの経過時間を表示し、`撮影停止` を押した後は停止要求時点の時刻で凍結する。
- `correcting` の停止は UI thread を塞がず、停止処理中であることを明示しながら完了まで待てるようにする。
- `correcting` は前面表示中の screen off と自動減光で収録を止めない。
- 長時間収録の安定化では、まず `通常計測` の `10min` 連続稼働を成立条件とする。
- `correcting` の `frame画像群` は recording 中に採択 frame だけを `trajectreview/image/` へ保存し、毎 update 全保存は行わない。
- `correcting` の pose 正規化では `displayOrientedPose` ではなく `camera.pose` を正とする。

## ネーミング

| 名称 | 意味 |
| --- | --- |
| `TraceCore` | `1分` 動画で成立させる最小核 |
| `FieldProcess OS` | `10時間` 運用まで拡張した将来基盤 |

- 開発上の前提は「いまは `TraceCore` を作る」で固定する。
