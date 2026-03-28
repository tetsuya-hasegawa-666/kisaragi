# agents.md

## --state の役割

- この階層は、`--tgpce-map/` 未適用 project の legacy state 文書を一時保持する。

## shared と per-project の関係

- shared governance の正本は `AGENTS.md` と各階層 `agents.md` とする。
- project 固有の current state は、原則として各 project の `b2t-plans-result.md` の `current_state` 章で保持する。
- `--state/` は migration 前の legacy current を一時保持してよいが、新しい shared `current_state.md` や `decision_log.md` をここへ増やさない。
