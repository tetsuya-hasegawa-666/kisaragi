# agents.md

## kisaragi-db の役割

- この階層は、project で発生する文書、状態、実装、証跡、試験生成物の正本管理層とする。

## 直下の構造

```text
kisaragi-db/
  --devs/
  --exsams/
  agents.md
```

## 直下の各要素

- `--devs/` は、計画、状態、証跡、test code、product 実装物、要約された test log を保持する。
- `--exsams/` は、開発中に生成される raw な試験生成物を project 単位で保持する。

## 補足

- skills の唯一の正本は `kisaragi-skills/` とし、`kisaragi-db/` 配下に skills 層は持たない。
