# AGENTS skillification review

## 判定記号

| 記号 | 意味 |
| --- | --- |
| `K` | `AGENTS.md` に shared rule として残す |
| `E` | execution skill へ落とせる |
| `M` | manager skill へ昇格候補 |
| `R` | reference / proposal 文書へ逃がす |
| `D` | 本体から外す |

## 新主線前提の判定

| 章 | 残し方 | 理由 |
| --- | --- | --- |
| `この文書の役割` | `K` | shared governance core の定義そのもの |
| `基本原則` | `K` | wording、encoding、読込順、shared / project 境界 |
| `全体構成` | `K` | `receipt-manager -> skill-invoker -> skill-planner -> response-manager` の主線 |
| `強制順序` | `K` | layer の順序は shared rule |
| `receipt-manager 規則` | `K+M` | 原則は shared、処理本文は manager skill |
| `skill-invoker 規則` | `K+M` | 原則は shared、判定 detail は manager skill |
| `skill-planner 規則` | `K+E` | phase 原則は shared、実行 detail は planner 本体 |
| `response-manager 規則` | `K+M` | 応答整形の責務境界を固定するため |
| `文書運用` | `K` | 正本境界は shared |
| `ディレクトリ構造` | `K` | shared structure |
| `directory 統制` | `K` | shared safety |
| `plan / gate 規則` | `K+M` | 状態語は shared、運用 detail は `plan-gate-manager` 候補 |
| `実装原則` | `K+M` | BDD / TDD / warning-blocker 原則は shared |
| `branch / git hygiene` | `K+M` | hygiene 原則は shared、実務 detail は `git-hygiene-manager` 候補 |
| `access / safety` | `K+M` | rule は shared、実務 guard は manager skill |
| `協調規則` | `K` | 人間 / AI 境界、承認方針 |
| `研究方法` | `K+M` | stance は shared、探索 detail は `research-execution-manager` 候補 |
| `Windows 運用` | `K+M` | 入口 rule は shared、操作 detail は `windows-ops-manager` 候補 |
| `参照先一覧` | `K` | どこを authoritative とみなすかの shared 目次 |
| `refresh target skill` | `R` | manager 設計一覧として保持 |
| `skill 作成時の共通記載項目` | `K` | skill 文書の最小 schema |
| `禁止事項` | `K` | shared guard rail |
| `更新情報` | `K` | 履歴参照 rule |

## 結論

- `test/AGENTS.md` は manager 主線、shared rule、禁止事項に集中させる。
- skill 選定 detail は `skill-invoker`、phase detail は `skill-planner`、応答 detail は `response-manager` へ逃がす。
- proposal 文書は、実装済み skill 在庫と refresh target manager 群の橋渡しを担当する。
