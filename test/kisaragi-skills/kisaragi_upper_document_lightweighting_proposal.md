# kisaragi upper document lightweighting proposal

## 概案名対応

| 現行正式名 | 概案名 | `test/` refresh file 名 |
| --- | --- | --- |
| `AGENTS.md` | `Shared Governance Core` | `AGENTS.md` |
| `AGENTSmd-RH.md` | `Shared Governance Core History` | `AGENTSmd-RH.md` |
| `kisaragi-skills/agents.md` | `Skill Structure Ledger` | `agents.md` |

## 目的

- `AGENTS.md` を軽量な shared governance core とし、実行 detail を skill / script / reference へ逃がす。
- 新主線は `receipt-manager -> skill-invoker -> skill-planner -> response-manager` とする。
- 上位文書には原則と境界だけを残し、手順や matrix は下位へ分離する。

## 基本方針

- 文書に残すのは `何を正とするか`、`何を禁じるか`、`何を完了とみなすか`。
- skill に送るのは `どう判定するか`、`どう順序立てるか`、`どう反映するか`。
- `receipt-manager` は prompt 解釈、`skill-invoker` は skill 集合確定、`skill-planner` は orchestration、`response-manager` は応答整形に専念させる。

## 上位文書へ残すもの

| 文書 | 残すもの |
| --- | --- |
| `AGENTS.md` | shared rule、責務境界、強制順序、禁止事項、文書運用、gate / branch / safety 原則 |
| `AGENTSmd-RH.md` | 履歴 |
| `kisaragi-skills/agents.md` | 実装済み skill 在庫、refresh target manager 群、再配置方針 |

## 上位文書から外すもの

| 内容 | 吸収先 |
| --- | --- |
| prompt 解釈 detail | `receipt-manager` |
| skill 要否判断 detail | `skill-invoker` |
| 実行順 detail | `skill-planner` |
| 応答整形 detail | `response-manager` |
| matrix、例、細かい手順 | 各 skill の `references/` と proposal 文書 |

## 実装済み skill の扱い

- legacy 入口 skill は `skill-invoker` へ名称統一し、旧名称は使わない。
- `skill-planner` は存続し、selection owner ではなく orchestration owner に固定する。
- 既存 specialist skill は execution 層へ再配置する。

## 結論

- 軽量化の中心は削除ではなく責務分離である。
- `AGENTS.md` は憲法へ寄せ、proposal / skill 文書が実務 detail を持つ構造へ揃える。
