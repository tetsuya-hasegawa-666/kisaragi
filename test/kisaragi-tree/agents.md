# agents.md

- `kisaragi-tree/` 配下は junction によって構成し、実データ copy は持たない。
- 直接編集せず、更新は常に `kisaragi-db/` 正本側で行う。
- data の追加削除時は tree sync 実行物で追従させ、閲覧 UI が対応できる状態を保つ。
