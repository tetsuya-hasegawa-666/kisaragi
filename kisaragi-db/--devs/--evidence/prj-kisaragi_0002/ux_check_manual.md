# ux_check_manual

## 目的

- `prj-kisaragi_0002` を実際に起動して、操作体験が最低限成立しているかを人が判断するための手順を書く。

## 対象

- Android app `trajectreview-correcting`
- Android app `trajectreview-modeling`
- Android app `trajectreview-reviewing`
- Android app `trajectreview`

## 操作手順

1. Android 端末で app `trajectreview-correcting` を起動する。
2. camera preview、記録モード、`保存先を選択` button、`現場撮影データ保存を開始` button が見えることを確認し、`保存先を選択` から同期先 folder を選べることを確認する。
3. `guarded replacement route` が OFF で `ARCore 記録を有効化` が ON の時、`frozen route では録画安定性を優先し、記録中の ARCore 収集を停止します。` が見えることを確認する。
4. `現場撮影データ保存を開始` を押し、preview が維持されたまま記録中表示へ切り替わることを確認する。
5. 5 秒以上待っても録画が自動停止しないことを確認する。
6. `現場撮影データ保存を停止` を押し、session summary が更新されることを確認する。
7. `data-check` 欄に `診断進行可`、`modeling 着手可`、`欠落入力`、`blocker`、`補正指示` が出ることを確認する。
8. `data-check を実行` を押し、同じ項目が再計算されることを確認する。
9. `data-check` 欄に `camera intrinsics 対応率`、`lens distortion 対応率`、`calibration frame 数` が出ることを確認する。
10. `PC 転送` 欄に `同一ネットワーク上の PC 候補を検索して選択してください` と、同一 `Wi-Fi` 上で PC 側 bootstrap script 待受が必要だと出ることを確認する。
11. `PC 候補を検索` を押し、件数 message が更新されることを確認する。
12. `対象 PC を選択` を押し、候補 dialog から同一ネットワーク上の対象 PC を選べることを確認する。
13. `PC 転送を実行` を押し、PC 側所定 folder に session が保存されることを確認する。
14. Android 端末で app `trajectreview-modeling` を起動する。
15. `bundle を選択` を押し、統合 app などで作られた `trajectreview_export/<session_id>` folder を選ぶ。
16. `軽量 model を実行` を押し、`spaceQuality`、`trajectoryQuality`、`colab_job_request.json` を含む出力一覧が見えることを確認する。
17. PC browser で [Google Colab](https://colab.research.google.com/) を開き、Google account で sign in する。
18. `ファイル` -> `ノートブックをアップロード` を選び、[trajectreview_da3metric_large_colab.ipynb](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\modeling\trajectreview_da3metric_large_colab.ipynb) を開く。menu 名が違う時は `Upload notebook` 相当を探す。
19. `ランタイム` -> `ランタイムのタイプを変更` で `GPU` を選ぶ。候補に `T4`、`L4`、`A100` などが見えた時は、その表示を記録する。
20. notebook の `CONFIG` cell を開き、`session_root` と `result_root` を今回使う値へ置き換える。値の意味はこの文書の `CONFIG に入れる値` を参照する。
21. `drive.mount('/content/drive')` の cell を実行し、Google Drive への access 許可画面が出たら許可する。
22. `session_root/` に、`colab_job_request.json` で要求された file と frame / image 入力を置く。迷った時は、先に file 名だけを Codex へ伝える。
23. install cell と `DA3Metric-Large` 実行 cell は、1 つずつ順に実行する。失敗したら、その cell の見出しと error message をそのまま控える。
24. Android 端末で app `trajectreview-reviewing` を起動する。
25. `結果 folder を選択` を押し、同じ `trajectreview_export/<session_id>` folder を選ぶ。
26. `結果を読込` を押し、`verify` または `review` の状態、`Attention`、`same_time` が見えることを確認する。
27. Android 端末で統合 app `trajectreview` を起動する。
28. `取得元を選択` を押して同じ session folder を選び、`保存先を選択` で出力先 folder を選ぶ。
29. `抽出を実行` の後に `軽量 model を実行` を押す。
30. `Thin Status` と `Attention` が実データ由来に更新され、`前へ` と `次へ` で段階を追えることを確認する。

## Colab へ入る時の考え方

- `Colab` は browser 上で動く notebook で、まず `Google account` へ sign in できれば入口に立てる。
- 最初に確認することは 3 つだけでよい。`notebook を開けたか`、`GPU runtime を選べたか`、`input file の置き場が分かったか`。
- `Colab` 未経験でも、いきなり全部理解する必要はない。1 cell ずつ順に実行し、止まった場所を Codex へ渡せばよい。
- password、認証 token、private key は Codex へ送らない。必要なのは secret ではなく、画面名、menu 名、file path、error message である。

## `CONFIG` に入れる値

- 前提
  - `Colab` で使うには、`Google Drive` または PC 側で `session_root/` が見える状態にする必要がある。
  - `trajectreview-correcting` の `PC 転送` が使える時は、その転送先を起点にしてよい。
  - `PC 転送` が未実装または未使用の時は、user 自身が `Google Drive` または PC へ copy する。
  - したがって notebook へ入れる主値は、`Google Drive` に置いた session folder の path になる。
- `session_root`
  - 何を入れるか: 今回処理する session folder そのものの path。
  - どこで見るか: `Google Drive` にコピーした `trajectreview_export/<session_id>/` の path。
  - 例: `/content/drive/MyDrive/trajectreview/input/session-20260327-153000`
  - 間違えやすい点: 親 folder ではなく、`session_package.json` などが入っている session folder まで含める。
- `result_root`
  - 何を入れるか: Google Drive 上で結果を書き戻す親 folder path。
  - 期待する構造: notebook が `result_root/session_id/route_id/` を自動で作る。
  - 例: `/content/drive/MyDrive/trajectreview/results`
  - 間違えやすい点: 出力先の親 folder を入れる。`session_id` や `route_id` は入れない。
- `route_id`
  - 基本方針: notebook が `selected_route.json` または `colab_job_request.json` から自動取得する。
  - 手動既定値: `route-da3metric-large-10fps-per-frame-intrinsics`
- `session_id`
  - 基本方針: notebook が `session_package.json` の `sessionId` から自動取得する。
- `input_root`
  - 基本方針: notebook が `session_root.parent` として自動取得する。

## Colab に置く入力 data

- 先に必要な作業
  - Android app で export した `trajectreview_export/<session_id>/` を、PC 転送または手動 copy で PC から見える場所へ置く。
  - `Colab` で使う時は、通常 `Google Drive/MyDrive/...` 配下へ置く。
  - まだ `Google Drive` に無い時は、その時点では `CONFIG` を確定できない。
- 最低限必要な file
  - `video.mp4`
  - `session_package.json`
  - `frame_pose_index.csv`
  - `camera_calibration_summary.json`
  - `sensor_quality.json`
  - `space_handoff_manifest.json`
- route 判断に使う file
  - `colab_job_request.json`
  - `selected_route.json`
  - `experiment_manifest.json`
  - `da3_input_manifest.json`
- 画像入力
  - notebook の現在仕様では `session_root/images/` に画像群がある前提で進む。
  - もし手元に動画しかない時は、そのままでは足りない。`video.mp4` に加えて、Colab へ渡す frame 画像群を `images/` に置く必要がある。
  - 画像 file 名の例: `frame_000001.png`、`frame_000002.png`
- 置き場の完成形
  - `session_root/video.mp4`
  - `session_root/session_package.json`
  - `session_root/frame_pose_index.csv`
  - `session_root/camera_calibration_summary.json`
  - `session_root/sensor_quality.json`
  - `session_root/space_handoff_manifest.json`
  - `session_root/images/<frame image files>`

## 分かりにくい項目の見分け方

- `session_root` を決める前に何を確認するか
  - `trajectreview_export/<session_id>/` が Android 側で生成されているか。
  - その folder を `Google Drive` または PC 側の作業場所へコピー済みか。
  - コピー後に `session_package.json` が見えているか。
- `session_id` が分からない時
  - `session_package.json` を開き、`sessionId` の値を見る。notebook も自動でこの値を使う。
- `route_id` が分からない時
  - `selected_route.json` を開き、`selectedRouteId` を見る。
  - それが無ければ `colab_job_request.json` の `defaultRouteId` を使う。
- `session_root` が分からない時
  - Google Drive で `session_package.json` が見える folder を開き、その path を使う。
- `input_root` が分からない時
  - `session_root` の 1 つ上の parent folder である。notebook が自動で決める。
- `result_root` が分からない時
  - notebook 実行後の結果をまとめて保存したい親 folder を 1 つ決め、その path を使う。
- `GPU runtime` が見つからない時
  - `ランタイム` または `Runtime` menu から `ランタイムのタイプを変更` を探す。
  - 無ければ、今見えている menu 名と画面名を Codex へ伝える。
- `images/` が無い時
  - `DA3Metric-Large` は画像入力が必要なので、その時点で止めてよい。
  - `video.mp4` しか無い、または frame 切り出し場所が分からない、という状態を Codex へ伝える。

## Android から PC / Drive へ渡す時の考え方

- 現在は自動転送ではない。
- `PC 転送` が使える時は、その機能で PC 側所定 folder へ渡す。
- `PC 転送` が使えない時は、`保存先を選択` で選んだ folder に export された data を、user が次段へ渡す。
- 渡し方の例
  - Android の file app で `Google Drive` 配下へ copy する
  - USB 接続で PC へ copy し、その後 `Google Drive` へ upload する
  - 既に `Google Drive` provider を保存先に選べる環境なら、その保存先を使う
- どの方法でも、最終的に `Google Drive` 上で `session_root/` が見える状態にする必要がある。

## Codex へ渡す最小情報

- `Colab` へ入れたかどうか。入れない時は、どの画面で止まったか。
- 開いた notebook 名。`Upload notebook` を使ったか、Drive 上の notebook を開いたか。
- `ランタイムのタイプ` で何が見えたか。`CPU` のままか、`T4`、`L4`、`A100` などが選べたか。
- `CONFIG` に入れた `session_root`、`result_root`。
- `CONFIG` に入れた値が、どの file や folder を根拠に決めたか。
- upload または Drive 配置した file 名。少なくとも `video.mp4`、`session_package.json`、`frame_pose_index.csv`、`sensor_quality.json`、`space_handoff_manifest.json` の有無。
- `camera_calibration_summary.json` の有無と、`imageIntrinsicsCoverageRatio`、`lensDistortionCoverageRatio` の値。
- `images/` folder の有無。ある時は画像枚数の概数。
- 失敗した cell の見出し、実行順、error message 全文。
- 実行後に出た output path と生成 file 名。

## Codex へ渡さなくてよい情報

- Google account の password
- browser に表示された認証 token
- personal mail address 全文
- private な Drive URL 全文

## pass の判断

- pass:
  - 4 app が起動する。
  - `correcting` で camera preview と `現場撮影データ保存を開始` が出る。
  - `correcting` で `保存先を選択` から同期先 folder を選べる。
  - `correcting` で記録開始と停止ができ、session summary が更新される。
  - `guarded replacement route` が OFF でも、5 秒以上の録画で自動停止や途切れが起きない。
  - `correcting` で `data-check` が動き、`診断進行可`、`modeling 着手可`、`blocker`、`補正指示` が出る。
  - `correcting` で `camera intrinsics 対応率`、`lens distortion 対応率`、`calibration frame 数` が出る。
  - `correcting` で同一ネットワーク上の対象 PC を選択し、PC 側所定 folder へ無線転送できる。
  - `modeling` で `colab_job_request.json` を含む modeling 結果が出る。
  - `Colab` で notebook を開き、`GPU` runtime を選び、`CONFIG` と入力 file の置き場を確認できる。
  - `reviewing` で `verify` または `review` 状態と `Attention` が出る。
  - 統合 app で `抽出` と `軽量 model` の両方が動き、`前へ` と `次へ` でも落ちない。
- fail:
  - いずれかの app が起動しない。
  - `correcting` で camera preview や記録開始 button が出ない。
  - `correcting` で保存先選択が出ない、または選んだ保存先が保持されない。
  - `correcting` で記録開始または停止ができない。
  - `guarded replacement route` が OFF の時に 5 秒程度で録画が自動停止する。
  - `correcting` で `data-check` が更新されない、または補正指示が出ない。
  - `correcting` で calibration 数値が出ない。
  - `correcting` で同一ネットワーク上の PC 候補が出ない、または対象 PC を選んでも転送できない。
  - `modeling` で `colab_job_request.json` を含む結果が出ない。
  - `Colab` で notebook を開けない、`GPU` runtime を選べない、入力 file の置き場が分からない。
  - `reviewing` で状態要約や `Attention` が出ない。
  - button を押すと落ちる、固まる、表示が大きく崩れる。

## 記録方法

- 記録する最小項目:
  - 実施日時
  - 端末名
  - `Colab` の runtime 表示
  - pass / fail
  - fail の時だけ、何が起きたかを 1 行で書く
