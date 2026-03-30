# admin-mrl-test-method

## 目的

- `prj-kisaragi_0002` を実際に起動して、操作体験が最低限成立しているかを人が判断するための手順を書く。

## 対象

- Android app `trajectreview-correcting`
- Android app `trajectreview-modeling`
- Android app `trajectreview-reviewing`
- Android app `trajectreview`

## 操作手順

1. Android 端末で app `trajectreview-correcting` を起動する。
2. preview 直下の状態表示に `現場の風景と経路を記録します。1. 条件設定⇒2. 収録⇒3. 転送` が表示され、独立した最上段見出しや `Correcting mode` が出ていないことを確認する。
3. 1 つ目の block の見出しが `1. 条件設定` で、1 行目が左右 2 分割で、左に `Sampling条件`、右に `端末保存先` があることを確認する。
4. `Sampling条件` を押すと popup が出て、`ARCore撮影(ON)・ポケット計測(OFF)`、`BLE記録`、`ARCoreのtimestamp(ms)`、`ARCore`、`IMU`、`GNSS`、`BLE` を編集できることを確認する。
5. `端末保存先` を押し、スマホ内の同期先 folder を選べることを確認する。未設定時だけ直下に `端末保存先：未設定` が表示され、設定後はその表示が消えることを確認する。
6. 1 つ目の block の次の行が左右 2 分割で、左に `送信Dataset`、右に `Data名称変更` があることを確認する。
7. `送信Dataset` を押すと popup が出て、`撮影データ`、`センサ記録`、`data-check結果と後段受け渡し`、`frame画像群` を ON / OFF できることを確認する。
8. `Data名称変更` を押すと popup の最上段に `戻る` button、次行に `OFF：名称変更、ON：削除モード` toggle が出て、一覧はメイン画面系の button 形式で表示されることを確認する。
9. toggle が OFF の時に data button を押すと名称変更 popup が出て、変更完了後や cancel 後も親 popup に戻ることを確認する。
10. toggle を ON にすると削除 mode に切り替わり、複数 data を選べることを確認する。選択前は `削除実行` が非活性、選択後は活性になり、押すと端末内 data と `端末保存先` に同期済みの同名 directory が実際に削除されることを確認する。`端末保存先` に app が作った転送 zip が残っていた場合は、それも cleanup されることを確認する。
11. 2 つ目の block の見出しが `2. 収録` で、`端末保存先` が未設定の間は `Data収録開始` が非活性であることを確認する。保存先を設定すると活性になり、押すと preview 直下の status card に開始状態が出て、冒頭に `経過時間: mm:ss` が表示され、preview が維持されたまま session 情報が表示され、同じ位置の button 表示が `撮影停止` に切り替わることを確認する。
12. `撮影停止` を押した後は、status card の `経過時間` が停止要求時点で止まり、そのまま増え続けないことを確認する。
13. `撮影停止` の後は、`Data収録開始` 直下に ring / bar と `何をしているか` の短文、さらに `次の収録は待機推奨か` の 1 文が表示され、停止処理中、処理中、未設定が区別できることを確認する。
13. 収録停止後は、まず `端末保存先へ保存中です。` が表示され、raw session が先に保存されることを確認する。
14. その後に `自動で品質確認を実行中です。` が表示されることを確認する。
15. `端末保存先` 同期中は session 詳細が縮退し、`Session: <session_id>` と `品質確認OK` だけが残ることを確認する。
16. 5 秒以上待っても録画が自動停止しないことを確認する。
17. 同じ位置の `撮影停止` button を押し、session summary が更新されることを確認する。
18. `通常計測` のまま `10min` 連続収録を行い、画面が自動減光や screen off に入らず、収録が継続することを確認する。
19. 上の長時間収録後に `撮影停止` を押し、app が落ちずに session を finalize できることを確認する。
20. 2 つ目の block の 2 行目が左右 2 分割で、左に `品質確認`、右に `転送Data選択` があることを確認する。
21. `品質確認` を押すと popup で詳細結果が表示されることを確認する。メイン画面には閾値未満の項目名だけが短く残ることを確認する。`corecamera_shared_camera_trial` route では `camera intrinsics 対応率` と `captureDiagnostics` の整合を見る。
22. `trackingState` は初期 warmup の少数 frame だけでは `▲` にならないことを確認する。`▲` が出る場合だけ、収録時間を少し長くする、急な動きを避ける、特徴点が少ない面を避ける案内が返ることを確認する。
23. `転送Data選択` または `Data名称変更` を開く時に保存済み data の軽量 `品質確認` が更新され、その結果で `▲` が付き直ることを確認する。
24. `転送Data選択` を押すと、`Data名称変更` と同系統の popup が出ることを確認する。最上段に `戻る`、下部に `OK` があり、保存済み data を button 一覧から複数選べることを確認する。
25. 取得日時、長さ、`▲` は button 外の小テキストで読めることを確認する。`▲` は blocker または閾値超え warning がある data にだけ付くことを確認する。軽微な `coverage < 1.0` や一覧時点の `images/` 未生成だけでは `▲` が付かないことを確認する。
26. 3 つ目の block の 1 行目が左右 2 分割で、左に `転送先を選択`、右に `転送実行` があることを確認する。
27. `転送先を選択` を押すと、`Google Drive` folder URL を入力できる popup が出ることを確認する。初期値が `https://drive.google.com/drive/u/2/folders/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_` であることを確認する。
28. popup で URL を編集して `OK` を押すと URL が保存されることを確認する。
29. 同じ popup の `保存先fileを設定する` を押すと Android の標準保存画面が開くことを確認する。端末 storage が先に見える場合は、左上メニューなどから `Google Drive` を選べることを確認する。そこで選んだ zip 保存先 file が app の転送先設定になることを確認する。
30. 続けて zip 保存先 file 名を選べることを確認する。転送先直下の小さい補助表示は出ず、下のコメントだけで `転送Data` と `転送先` の設定済み / 未設定が分かることを確認する。転送先 file は毎回選び直す前提であることを確認する。
31. zip 保存先 file 名の既定値が、名称未指定なら `trajectreview-correcting-session-YYYYMMDD-HHMMSS.zip` 形式で入ることを確認する。data 名を使う時も `<data-name>-session-YYYYMMDD-HHMMSS.zip` の形で `session-*` suffix が付くことを確認する。
32. `転送実行` は `転送Data` と `転送先` が設定済みなら活性になり、選択した `Google Drive` 保存場所に zip が保存され、ON にした group だけが zip 内に入ることを確認する。`frame画像群` を ON にした時だけ `images/` が生成されることを確認する。転送完了後は次回のために再度 `転送先を選択` が必要になることを確認する。
33. `転送実行` 中の comment と waiting ring は `転送実行` button の直下に出ることを確認する。`Data収録開始` の直下には出ないことを確認する。
24. Android 端末で app `trajectreview-modeling` を起動する。
25. `bundle を選択` を押し、統合 app などで作られた `trajectreview_export/<session_id>` folder を選ぶ。
26. `軽量 model を実行` を押し、`spaceQuality`、`trajectoryQuality`、`colab_job_request.json` を含む出力一覧が見えることを確認する。
27. `DA3Metric-Large` の `Colab bootstrap` は [da3_colab_clean_bootstrap_runbook.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\modeling\da3_colab_clean_bootstrap_runbook.md) を正本として扱う。runbook 本体へ入る前に、同文書の `準備確認 2` から `準備確認 4` を実行して Drive 上の input 候補探索、selected input 固定、存在確認を済ませる。この runbook の admin 実行は `MRL-3` / `mRL-3.2` と `MRL-4` / `mRL-4.2` の candidate evidence を兼ねる。`gs_model` を含む `SpacePackage` 実生成確認は `MRL-4` 本体で確認し、`MRL-5` は 10s 前後の整った実動画からの `multi-frame` densify による粗い再現モデル段として別扱いにする。route 比較と採用固定は後続 `MRL-**` の課題とする。
27. PC browser で [Google Colab](https://colab.research.google.com/) を開き、Google account で sign in する。
28. `ファイル` -> `ノートブックをアップロード` を選び、[trajectreview_da3metric_large_colab.ipynb](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\modeling\trajectreview_da3metric_large_colab.ipynb) を開く。menu 名が違う時は `Upload notebook` 相当を探す。
29. `ランタイム` -> `ランタイムのタイプを変更` で `GPU` を選ぶ。候補に `T4`、`L4`、`A100` などが見えた時は、その表示を記録する。
30. notebook の `CONFIG` cell を開き、`session_root` と `result_root` を今回使う値へ置き換える。値の意味はこの文書の `CONFIG に入れる値` を参照する。
31. `drive.mount('/content/drive')` の cell を実行し、Google Drive への access 許可画面が出たら許可する。
32. `session_root/` に、`colab_job_request.json` で要求された file と frame / image 入力を置く。迷った時は、先に file 名だけを Codex へ伝える。
33. install cell と `DA3Metric-Large` 実行 cell は、1 つずつ順に実行する。失敗したら、その cell の見出しと error message をそのまま控える。
34. Android 端末で app `trajectreview-reviewing` を起動する。
35. `結果 folder を選択` を押し、同じ `trajectreview_export/<session_id>` folder を選ぶ。
36. `結果を読込` を押し、`verify` または `review` の状態、`Attention`、`same_time` が見えることを確認する。
37. Android 端末で統合 app `trajectreview` を起動する。
38. `取得元を選択` を押して同じ session folder を選び、必要なら `端末保存先` で同期済み session を確認する。
39. `抽出を実行` の後に `軽量 model を実行` を押す。
40. `Thin Status` と `Attention` が実データ由来に更新され、`前へ` と `次へ` で段階を追えることを確認する。

## Colab へ入る時の考え方

- `Colab` は browser 上で動く notebook で、まず `Google account` へ sign in できれば入口に立てる。
- 最初に確認することは 3 つだけでよい。`notebook を開けたか`、`GPU runtime を選べたか`、`input file の置き場が分かったか`。
- `Colab` 未経験でも、いきなり全部理解する必要はない。1 cell ずつ順に実行し、止まった場所を Codex へ渡せばよい。
- password、認証 token、private key は Codex へ送らない。必要なのは secret ではなく、画面名、menu 名、file path、error message である。

## `CONFIG` に入れる値

- 前提
  - `Colab` で使うには、`Google Drive` または PC 側で `session_root/` が見える状態にする必要がある。
  - `trajectreview-correcting` の `Google Drive転送` が使える時は、その転送先を起点にしてよい。
  - `Google Drive転送` を使わない時は、user 自身が `Google Drive` または PC へ copy する。
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
- Android app で export した `trajectreview_export/<session_id>/` を、`Google Drive転送` または手動 copy で `Google Drive` から見える場所へ置く。
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
  - `correcting` は `品質確認` では `images/` を生成しない。`送信Dataset` で `frame画像群` を ON にして転送した時だけ生成する。
  - もし手元に動画しか無い時は、そのままでは足りない。`video.mp4` に加えて、Colab へ渡す frame 画像群を `images/` に置く必要がある。
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
  - まず `correcting` の `送信Dataset` で `frame画像群` を ON にして再転送する。
  - それでも無い時は、その時点で止めてよい。
  - `video.mp4` しか無い、または frame 切り出し場所が分からない、という状態を Codex へ伝える。

## Android から PC / Drive へ渡す時の考え方

- 現在は自動転送ではない。
- `Google Drive転送` が使える時は、その機能で選択済み `Google Drive` folder へ渡す。
- `Google Drive転送` を使わない時は、`端末保存先` で選んだ folder に同期された data を、user が次段へ渡す。
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

## `p-done` / `i-pass` の判断

- `p-done` / `i-pass`:
  - 4 app が起動する。
  - `correcting` で camera preview と `現場撮影データ保存を開始` が出る。
  - `correcting` で `端末保存先` から同期先 folder を選べる。
  - `correcting` で記録開始と停止ができ、session summary が更新される。
  - `guarded replacement route` が OFF でも、5 秒以上の録画で自動停止や途切れが起きない。
  - `correcting` で `data-check` が動き、`診断進行可`、`modeling 着手可`、`blocker`、`補正指示` が出る。
  - `correcting` で `camera intrinsics 対応率`、`lens distortion 対応率`、`calibration frame 数` が出る。
  - `correcting` で保存済み data 一覧に取得日時と長さが出る。
  - `correcting` で送信する data group を閲覧・選択できる。
  - `correcting` で既存 data を選び直して再転送できる。
  - `correcting` で data 名を変更できる。
  - `correcting` で `転送先を選択` から `Google Drive` 保存場所と zip file 名を決め、選んだ場所へ zip を転送できる。
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
  - `correcting` で保存済み data の取得日時または長さが見えない。
  - `correcting` で送信 group が見えない、または選択が反映されない。
  - `correcting` で既存 data の選択や rename ができない。
  - `correcting` で `転送先を選択` が開かない、または選んだ `Google Drive` 保存場所へ zip を転送できない。
  - `modeling` で `colab_job_request.json` を含む結果が出ない。
  - `Colab` で notebook を開けない、`GPU` runtime を選べない、入力 file の置き場が分からない。
  - `reviewing` で状態要約や `Attention` が出ない。
  - button を押すと落ちる、固まる、表示が大きく崩れる。

## 記録方法

- 記録する最小項目:
  - 実施日時
  - 端末名
  - `Colab` の runtime 表示
  - `ready / active / p-done / i-pass / fail`
  - fail の時だけ、何が起きたかを 1 行で書く
