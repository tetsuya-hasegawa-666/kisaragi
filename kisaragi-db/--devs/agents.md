# agents.md

## --devs の役割

- この階層は、計画、状態、証跡、test code、product 実装物、および要約された test log を保持する category directory とする。

## 直下の構造

```text
--devs/
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
- shared control file は `--state/current_state.md` と `--state/decision_log.md` を正本とする。
- raw な試験生成物は `--exsams/` へ置き、`--testlogs/` には要約と最小限の manifest を置く。
