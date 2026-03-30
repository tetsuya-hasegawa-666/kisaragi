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
| camera data | `ARCore` 相当の pose、intrinsics、時刻同期情報を取得できる |
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

- 空間生成の主経路は `DA3Metric-Large` と `ARCore pose` / intrinsics の統合とする。
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

## artifact 契約

### `SessionPackage`

- 単一入力単位の正規化 artifact とする。
- 主 camera 動画、`IMU`、`ARCore` pose、`BT`、品質要約を束ねる。
- 任意入力として `GNSS` を許容する。

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
- `Colab` runtime の bootstrap は product 側 runbook を正本とする。

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

## ネーミング

| 名称 | 意味 |
| --- | --- |
| `TraceCore` | `1分` 動画で成立させる最小核 |
| `FieldProcess OS` | `10時間` 運用まで拡張した将来基盤 |

- 開発上の前提は「いまは `TraceCore` を作る」で固定する。
