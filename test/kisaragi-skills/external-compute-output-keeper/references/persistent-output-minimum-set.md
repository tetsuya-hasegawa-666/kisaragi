# persistent output minimum set

## 目的

- external compute task で、final output と最低限残すべき付随情報の最小集合を固定する。

## 最小集合

- final output 実体
- `final_output_manifest.json`
- input / output 対応が分かる summary
- transform や contract 解釈に必要な manifest / csv / json

## 原則

- local zip より先に visible storage へ保存する
- cleanup 対象と keep 対象を分ける
- final output の再解釈に必要な情報を local tmp にしか残さない構成を避ける
