# agents.md

## kisaragi-tree の役割

- この階層は、`kisaragi-db/` の正本を project 単位で見やすく束ねる tree layer とする。

## 運用規則

- この階層で直接編集しない。
- 更新は `kisaragi-db/` 側の正本変更後に tree sync 実行物で追従させる。
- tree 配下は junction によって構成し、実データの copy は持たない。
