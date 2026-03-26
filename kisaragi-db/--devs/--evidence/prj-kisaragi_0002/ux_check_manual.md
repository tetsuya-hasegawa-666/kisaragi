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
2. `取得元を選択` を押し、取得元の session folder を選ぶ。
3. `保存先を選択` を押し、抽出結果を書き出す folder を選ぶ。
4. `抽出を実行` を押し、`trajectreview_export/<session_id>`、`診断進行可`、`空間再構成進行可`、`充足率`、`pose 対応率` が見えることを確認する。
5. Android 端末で app `trajectreview-modeling` を起動する。
6. `bundle を選択` を押し、手順 4 で作られた `trajectreview_export/<session_id>` folder を選ぶ。
7. `軽量 model を実行` を押し、`spaceQuality`、`trajectoryQuality`、`colab_job_request.json` を含む出力一覧が見えることを確認する。
8. Android 端末で app `trajectreview-reviewing` を起動する。
9. `結果 folder を選択` を押し、同じ `trajectreview_export/<session_id>` folder を選ぶ。
10. `結果を読込` を押し、`verify` または `review` の状態、`Attention`、`same_time` が見えることを確認する。
11. Android 端末で統合 app `trajectreview` を起動する。
12. `取得元を選択` を押して同じ session folder を選び、`保存先を選択` で出力先 folder を選ぶ。
13. `抽出を実行` の後に `軽量 model を実行` を押す。
14. `Thin Status` と `Attention` が実データ由来に更新され、`前へ` と `次へ` で段階を追えることを確認する。

## pass の判断

- pass:
  - 4 app が起動する。
  - `correcting` で `trajectreview_export/<session_id>` と quality 数値が出る。
  - `modeling` で `colab_job_request.json` を含む modeling 結果が出る。
  - `reviewing` で `verify` または `review` 状態と `Attention` が出る。
  - 統合 app で `抽出` と `軽量 model` の両方が動き、`前へ` と `次へ` でも落ちない。
- fail:
  - いずれかの app が起動しない。
  - `correcting` で bundle 名や quality 数値が出ない。
  - `modeling` で `colab_job_request.json` を含む結果が出ない。
  - `reviewing` で状態要約や `Attention` が出ない。
  - button を押すと落ちる、固まる、表示が大きく崩れる。

## 記録方法

- 記録する最小項目:
  - 実施日時
  - 端末名
  - pass / fail
  - fail の時だけ、何が起きたかを 1 行で書く
