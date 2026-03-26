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
2. camera preview、記録モード、`現場撮影データ保存を開始` button が見えることを確認する。
3. `guarded replacement route` が OFF で `ARCore 記録を有効化` が ON の時、`frozen route では録画安定性を優先し、記録中の ARCore 収集を停止します。` が見えることを確認する。
4. `現場撮影データ保存を開始` を押し、preview が維持されたまま記録中表示へ切り替わることを確認する。
5. 5 秒以上待っても録画が自動停止しないことを確認する。
6. `現場撮影データ保存を停止` を押し、session summary が更新されることを確認する。
7. `data-check` 欄に `診断進行可`、`modeling 着手可`、`欠落入力`、`blocker`、`補正指示` が出ることを確認する。
8. `data-check を実行` を押し、同じ項目が再計算されることを確認する。
9. Android 端末で app `trajectreview-modeling` を起動する。
10. `bundle を選択` を押し、統合 app などで作られた `trajectreview_export/<session_id>` folder を選ぶ。
11. `軽量 model を実行` を押し、`spaceQuality`、`trajectoryQuality`、`colab_job_request.json` を含む出力一覧が見えることを確認する。
12. Android 端末で app `trajectreview-reviewing` を起動する。
13. `結果 folder を選択` を押し、同じ `trajectreview_export/<session_id>` folder を選ぶ。
14. `結果を読込` を押し、`verify` または `review` の状態、`Attention`、`same_time` が見えることを確認する。
15. Android 端末で統合 app `trajectreview` を起動する。
16. `取得元を選択` を押して同じ session folder を選び、`保存先を選択` で出力先 folder を選ぶ。
17. `抽出を実行` の後に `軽量 model を実行` を押す。
18. `Thin Status` と `Attention` が実データ由来に更新され、`前へ` と `次へ` で段階を追えることを確認する。

## pass の判断

- pass:
  - 4 app が起動する。
  - `correcting` で camera preview と `現場撮影データ保存を開始` が出る。
  - `correcting` で記録開始と停止ができ、session summary が更新される。
  - `guarded replacement route` が OFF でも、5 秒以上の録画で自動停止や途切れが起きない。
  - `correcting` で `data-check` が動き、`診断進行可`、`modeling 着手可`、`blocker`、`補正指示` が出る。
  - `modeling` で `colab_job_request.json` を含む modeling 結果が出る。
  - `reviewing` で `verify` または `review` 状態と `Attention` が出る。
  - 統合 app で `抽出` と `軽量 model` の両方が動き、`前へ` と `次へ` でも落ちない。
- fail:
  - いずれかの app が起動しない。
  - `correcting` で camera preview や記録開始 button が出ない。
  - `correcting` で記録開始または停止ができない。
  - `guarded replacement route` が OFF の時に 5 秒程度で録画が自動停止する。
  - `correcting` で `data-check` が更新されない、または補正指示が出ない。
  - `modeling` で `colab_job_request.json` を含む結果が出ない。
  - `reviewing` で状態要約や `Attention` が出ない。
  - button を押すと落ちる、固まる、表示が大きく崩れる。

## 記録方法

- 記録する最小項目:
  - 実施日時
  - 端末名
  - pass / fail
  - fail の時だけ、何が起きたかを 1 行で書く
