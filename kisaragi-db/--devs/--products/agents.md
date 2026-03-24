# agents.md

## --products の役割

- この階層は、project ごとの product 実装物を保持する。

## 運用規則

- build cache、`node_modules/`、`dist/` などの生成物は正本にしない。
- 正本は source と最小限の設定ファイルに限る。
