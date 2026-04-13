# agents.md

## --devs の役割

- この階層は、計画、状態、証跡、test code、product 実装物、および要約された test log を保持する category directory とする。

## 直下の構造

```text
--devs/
  --tgpce-map/
  --products/
  --testcode/
  --testlogs/
  agents.md
```

## 運用規則

- project ごとの実データは各 category 配下の `prj-<project名>/` へ置く。
- `--tgpce-map/` は、承認済み project の `truth`、`goal`、`plan`、`current`、`evidence-map` を 1 directory に集約する正式移行先として使う。
- `--tgpce-map/` を採用した `prj-kisaragi_****` の project 固有 `current` は `realtime-compass-and-status.md` 冒頭 `current_state` 章を正本とし、旧 category へ重複配置しない。
- 旧 category の `--plans/`、`--evidence/`、`--project-truth/`、`--state/` は吸収完了後に削除する。
- shared governance の正本は `AGENTS.md` と各階層 `agents.md` とし、shared current / decision 専用 file は置かない。
- raw な試験生成物は `--exsams/` へ置き、`--testlogs/` には要約と最小限の manifest を置く。




