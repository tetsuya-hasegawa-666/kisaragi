# BDD-Release-Compass

## 文書の役割

この文書は `prj-reviework` の提供価値、`Purpose Story`、`System Behaviors`、`MRL` / `mRL` の対応を定義する正本計画書とする。

## 目指す姿

- reviework は、1台のスマホカメラ（IMUも取得）による連続動画と、IMU付き機器（主にスマホ）を持つ人が、その動画に頻繁に映り込むという状況下で、最も効果を発揮するシステムである。

- 連続動画＋IMUのデータと、IMU付きスマホを携帯する（動画無し）人のデータを入力するだけで、撮影した現場の3DGSの構成と、そこの中での画像を取得しているものの経路と、そこに移りこむ人の経路が、3DGS地図上で表示され、表示された3DGSを操作できるシステムである。

- また、経路は時系列情報を持ち、経路上の同じ時刻の場所をハイライトできる。

## 提供方針

- `GNSS` の有無に関わらず成立する計画を既定とする
- `Timeline` を統合キーとして先に固定する
- 実行前に `Diagnose` と実行可否 gate を成立させる
- 主空間、経路、閲覧成果物を 4 段階契約で分離する
- 外部文書に残っていた構想は `prj-reviework` の正本文書へ吸収し、以後はここを参照する

## Purpose Story

- `s1`: 利用者は session folder を投入し、必須入力と任意入力の充足を把握できる
- `s2`: 利用者は `Diagnose` で不足入力、品質低下、修正理由を読める
- `s3`: 利用者は実行可否 gate を満たした時だけ `処理を開始` を受け取れる
- `s4`: 利用者は実行中に `完了を待つ` と現在段階だけを見ればよい
- `s5`: 利用者は `COLMAP` が densification 不可なら `3DGS` 開始前に修正へ戻れる
- `s6`: 利用者は `GNSS` がなくても、主 `ARCore` 空間を基準に空間再構成の成立を確認できる
- `s7`: 利用者は作業機と作業員の経路を同じ `Timeline` で比較できる
- `s8`: 利用者は見失い区間と再拘束の不確実性を理由付きで把握できる
- `s9`: 利用者は `Verify` で空間品質と軌跡品質の弱点を同時に読める
- `s10`: 利用者は `Interpret` で `attention point` を時間範囲と理由付きで絞り込める
- `s11`: 利用者は `ReviewArtifact` を閲覧専用 viewer で開き、時刻同期レビューを開始できる
- `s12`: 運用者は `reviework` を外部 project や一時文書に依存せず独立運用できる

## System Behaviors

- `b1`: session folder が受理されると、`SessionPackage` に必須入力、任意入力、時刻基準、品質フラグの要約が反映される
- `b2`: `Diagnose` は、欠落入力、品質低下、修正理由を `Thin Status` で返す
- `b3`: 実行可否 gate は、`InputPackaging`、`SpaceReconstruction` 前提、`TrajectoryReconstruction` 前提の readiness を満たした時だけ `処理を開始` を返す
- `b4`: 実行 phase は、`Next Action` を常に `完了を待つ` 1 件に保ち、現在段階を別 line で返す
- `b5`: `COLMAP.status != READY_FOR_DENSIFICATION` のとき、`3DGS` を開始せず `入力条件を見直す` を返す
- `b6`: `SpacePackage` は主空間の唯一基準を返し、`GNSS` がない場合は主 `ARCore` local 空間を採用する
- `b7`: `TrajectoryPackage` は作業機 path、作業員 path、不確実性、再拘束点を同じ `Timeline` 上で返す
- `b8`: relink は visual match confidence、time gap、anchor proximity、`BT` 主体維持を使って判定し、不成立時は不確実性を上げる
- `b9`: `Verify` は空間品質と軌跡品質を同時に返し、`Interpret` は `attention point` を時間範囲と理由付きで返す
- `b10`: `Assembly` は唯一の `ReviewArtifact` 生成者であり、`Viewer` は閲覧専用の消費だけを行う
- `b11`: parser は `bt.jsonl` / `poses.jsonl` と `ble_scan.jsonl` / `arcore_pose.jsonl` の両方を受理する
- `b12`: `reviework` の docs、build、test、生成物経路は `prj-reviework` 配下で完結し、要約と生の生成物を分離する
- `b13`: `InputPackaging` は `iSensorium` 生出力に加えて、`input_readiness.json`、`sensor_quality.json`、`frame_pose_index.csv`、`member_identity_map.json` を分担インターフェースとして出力する
- `b14`: 4 分担の各段階は、前段の出力契約だけを読めば次段へ着手できる

## 受け入れ基準

| s-id | b-id | 観点 | 受け入れ基準 |
| --- | --- | --- | --- |
| `s1` | `b1`,`b11`,`b13` | 受理契約 | `frames`、`imu`、`bt`、任意 `poses` / `gnss`、追加出力の有無が 1 つの要約として読める |
| `s2` | `b2` | diagnose UX | `phase`、`pipeline`、`data_health`、`quality`、`issues` の 5 項目で理由が読める |
| `s3` | `b3` | 実行可否 gate | readiness 未達時は `処理を開始` を返さず、修正 action を返す |
| `s4` | `b4` | 実行 UX | `Next Action` は常に 1 件で、現在段階は補足 line に分離される |
| `s5` | `b5` | パイプライン安全性 | `COLMAP` failure 時に `3DGS` を開始しない |
| `s6` | `b6` | 空間基準 | `GNSS` がない時でも基準座標と空間品質の説明がある |
| `s7` | `b7` | 経路契約 | 作業機と作業員の path が同じ時刻軸で比較できる |
| `s8` | `b8` | relink 不確実性 | 再拘束失敗時に不確実性 mode と理由が更新される |
| `s9` | `b9` | verify UX | 空間品質と軌跡品質の弱点が同時に読める |
| `s10` | `b9` | interpret UX | `attention point` に時間範囲と理由が入る |
| `s11` | `b10` | 成果物境界 | `ReviewArtifact` 生成責務が `Assembly` に限定される |
| `s12` | `b12`,`b14` | 独立運用 | docs / build / test が project 内で完結し、段階間契約だけで分担着手できる |

## `MRL` 対応表

| MRL | mRL | 目的 | 関連 s-id | 関連 b-id | 現在 gate |
| --- | --- | --- | --- | --- | --- |
| `MRL-1` | `-` | 受理と診断の基礎線を成立させる | `s1`,`s2`,`s3` | `b1`,`b2`,`b3`,`b11`,`b13`,`b14` | `active` |
| `MRL-1` | `mRL-1.1` | `SessionPackage` 受理契約 | `s1` | `b1`,`b11`,`b13` | `active` |
| `MRL-1` | `mRL-1.2` | `Thin Status` 診断基線 | `s2` | `b2` | `planned` |
| `MRL-1` | `mRL-1.3` | 実行可否 gate | `s3` | `b3` | `planned` |
| `MRL-1` | `mRL-1.4` | 分担インターフェース固定 | `s1`,`s12` | `b13`,`b14` | `active` |
| `MRL-2` | `-` | 主空間再構成の基礎線を成立させる | `s4`,`s5`,`s6` | `b4`,`b5`,`b6` | `planned` |
| `MRL-2` | `mRL-2.1` | 主空間基準固定 | `s4`,`s6` | `b4`,`b6` | `planned` |
| `MRL-2` | `mRL-2.2` | `COLMAP` から `3DGS` への安全 gate | `s5` | `b5` | `planned` |
| `MRL-2` | `mRL-2.3` | 空間品質要約 | `s6`,`s9` | `b6`,`b9` | `planned` |
| `MRL-3` | `-` | 経路再構成と解釈の基礎線を成立させる | `s7`,`s8`,`s9`,`s10` | `b7`,`b8`,`b9` | `planned` |
| `MRL-3` | `mRL-3.1` | `TrajectoryPackage` 契約 | `s7` | `b7` | `planned` |
| `MRL-3` | `mRL-3.2` | relink と不確実性 | `s8` | `b8` | `planned` |
| `MRL-3` | `mRL-3.3` | `Verify` / `Interpret` | `s9`,`s10` | `b9` | `planned` |
| `MRL-4` | `-` | 成果物組立と運用硬化を成立させる | `s11`,`s12` | `b10`,`b12`,`b14` | `active` |
| `MRL-4` | `mRL-4.1` | `ReviewArtifact` と viewer 境界 | `s11` | `b10` | `planned` |
| `MRL-4` | `mRL-4.2` | 独立 project 境界 | `s12` | `b12`,`b14` | `active` |
| `MRL-4` | `mRL-4.3` | 生成物 routing hygiene | `s12` | `b12` | `pass` |
