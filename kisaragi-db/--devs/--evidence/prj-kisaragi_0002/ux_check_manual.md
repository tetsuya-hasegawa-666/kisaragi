# ux_check_manual

## 目的

- `prj-kisaragi_0002` を実際に起動して、操作体験が最低限成立しているかを人が判断するための手順を書く。

## 対象

- Android app `trajectreview`

## 操作手順

1. Android 端末で app `trajectreview` を起動する。
2. 画面に `Next Action`、`抽出`、`Thin Status`、`Attention` が見えることを確認する。
3. 最初の `Next Action` が `iSensorium セッションを選択` になっていることを確認する。
4. `セッションを選択` を押し、`iSensorium` の session folder を 1 つ選ぶ。
5. `抽出` 欄の先頭が `選択元:` で始まり、選んだ folder 名が見えることを確認する。
6. `抽出を実行` を押す。
7. `抽出` 欄に `抽出先:`、`診断進行可:`、`欠落入力:`、`充足率:`、`pose 対応率:` が見えることを確認する。
8. `前へ` と `次へ` の button が押せることを確認する。
9. 画面が固まらず、文字が途中で切れず、読めることを確認する。

## pass の判断

- pass:
  - app が起動する。
  - `Next Action`、`抽出`、`Thin Status`、`Attention` が見える。
  - 最初の `Next Action` が `iSensorium セッションを選択` である。
  - `抽出を実行` の後に `抽出先:` と quality 数値が表示される。
  - `前へ` と `次へ` を押しても落ちない。
- fail:
  - app が起動しない。
  - 上の文字が見えない。
  - 最初の `Next Action` が空、または別の文字になっている。
  - `抽出を実行` しても `抽出先:` と quality 数値が出ない。
  - button を押すと落ちる、固まる、表示が大きく崩れる。

## 記録方法

- 記録する最小項目:
  - 実施日時
  - 端末名
  - pass / fail
  - fail の時だけ、何が起きたかを 1 行で書く
