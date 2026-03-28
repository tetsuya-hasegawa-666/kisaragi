# agents.md

## --devs の役割

- この階層は、計画、状態、証跡、test code、product 実装物、および要約された test log を保持する category directory とする。

## 直下の構造

```text
--devs/
  --tgpce-map/
  --evidence/
  --plans/
  --products/
  --project-truth/
  --state/
  --testcode/
  --testlogs/
  agents.md
```

## 運用規則

- project ごとの実データは各 category 配下の `prj-<project名>/` へ置く。
- `--tgpce-map/` は、承認済み project の `truth`、`goal`、`plan`、`current`、`evidence-map` を 1 directory に集約する pilot / 正式移行先として使う。
- 現時点の `--tgpce-map/` 適用対象は `prj-kisaragi_0002` のみとする。
- `prj-kisaragi_0002` の project 固有 `current` は `b2t-plans-result.md` 冒頭 `current_state` 章を正本とし、旧 category へ重複配置しない。
- shared control file は `--state/current_state.md` と `--state/decision_log.md` を shared 用の正本とし、project 固有 current / decision を恒常的に混在させない。
- raw な試験生成物は `--exsams/` へ置き、`--testlogs/` には要約と最小限の manifest を置く。
