# test

`test/` は refresh 用の軽量 workspace です。root には `AGENTS.md` と `README.md` だけを置き、その他の文書は `kisaragi-db/`、`kisaragi-skills/`、`kisaragi-tree/` 配下で管理します。

## top 構造

| path | 役割 | 入口文書 |
| --- | --- | --- |
| [`AGENTS.md`](./AGENTS.md) | `test/` 全体の shared control file | [`AGENTS.md`](./AGENTS.md) |
| [`kisaragi-db/`](./kisaragi-db/) | 履歴、計画、状態、証跡、snapshot の保持先 | [`kisaragi-db/agents.md`](./kisaragi-db/agents.md) |
| [`kisaragi-skills/`](./kisaragi-skills/) | skill 正本、refresh 設計、trigger / pilot / proposal 文書 | [`kisaragi-skills/agents.md`](./kisaragi-skills/agents.md) |
| [`kisaragi-tree/`](./kisaragi-tree/) | junction による閲覧 tree | [`kisaragi-tree/agents.md`](./kisaragi-tree/agents.md) |

## refresh 文書の配置

| 主題 | 配置先 |
| --- | --- |
| shared history | [`kisaragi-db/--devs/AGENTSmd-RH.md`](./kisaragi-db/--devs/AGENTSmd-RH.md) |
| refresh file map | [`kisaragi-db/--devs/refresh-file-map.md`](./kisaragi-db/--devs/refresh-file-map.md) |
| skill governance proposal | [`kisaragi-skills/kisaragi_context_skill_governance_proposal.md`](./kisaragi-skills/kisaragi_context_skill_governance_proposal.md) |
| pilot skill spec | [`kisaragi-skills/kisaragi_pilot_skill_spec.md`](./kisaragi-skills/kisaragi_pilot_skill_spec.md) |
| trigger system map | [`kisaragi-skills/kisaragi_skill_trigger_system_map.md`](./kisaragi-skills/kisaragi_skill_trigger_system_map.md) |
| lightweighting proposal | [`kisaragi-skills/kisaragi_upper_document_lightweighting_proposal.md`](./kisaragi-skills/kisaragi_upper_document_lightweighting_proposal.md) |
| skillification review | [`kisaragi-skills/agents_skillification_review.md`](./kisaragi-skills/agents_skillification_review.md) |
| gap list | [`kisaragi-skills/skill-direct-gap-list.md`](./kisaragi-skills/skill-direct-gap-list.md) |

## 読み始め方

1. shared rule は [AGENTS.md](./AGENTS.md) を読む。
2. skill 構造は [`kisaragi-skills/agents.md`](./kisaragi-skills/agents.md) を読む。
3. refresh の履歴と snapshot は [`kisaragi-db/--devs/`](./kisaragi-db/--devs/) を見る。

