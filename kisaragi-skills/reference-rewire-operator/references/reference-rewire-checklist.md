# reference rewire checklist

## 1. 変更定義

- old reference は 1 行で言えるか
- new reference は 1 行で言えるか
- rename、move、ownership change、contract change のどれか

## 2. 参照面棚卸し

- producer を列挙したか
- direct consumer を列挙したか
- secondary consumer を列挙したか
- docs / runbook / manual / evidence を列挙したか
- cleanup / export / download / viewer を列挙したか

## 3. 切替方式

- big-bang で切るか
- alias を置くか
- dual-read / dual-write が要るか
- hard fail 条件を決めたか

## 4. 実装順

- producer を先に直したか
- consumer を後追いで直したか
- tests を同じ task で直したか
- inventory / docs_id / design contract を直したか

## 5. grep 検査

- old path
- old file 名
- old key / field
- old docs_id
- old heading / section 名
- old helper import

## 6. 下流確認

- 生成できる
- 読み込める
- 文書から辿れる
- cleanup が新参照に追随している
- evidence path が新参照を指す

## 7. close 条件

- old reference を残す理由を書いたか
- alias を消す次条件を書いたか
- big-bang なら旧参照 0 件を確認したか
