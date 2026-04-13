# drive input resolution rule

## 目的

- external compute task の初動で、`Drive mount -> input 解決` を固定する。

## rule

1. まず Drive mount 状態を確認する
2. input 候補 root を固定する
3. input zip / folder 候補を列挙する
4. 選択した input の canonical path を固定する
5. 実行前に、その canonical path を後続 block が共通参照できることを確認する

## 禁止

- hardcoded path を暗黙前提にする
- selected input を block ごとに別解決する
- unzip 前提を確認せずに後続 block へ進む
