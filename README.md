# kisaragi

`kisaragi` は、project ごとの正本文書、実装、証跡、運用 rule を 1 つの workspace で管理する repository です。最上位の運用正本は [AGENTS.md](./AGENTS.md) です。

## top 構造

| path | 役割 | 入口文書 |
| --- | --- | --- |
| [`AGENTS.md`](./AGENTS.md) | repository 全体の shared control file | [`AGENTS.md`](./AGENTS.md) |
| [`kisaragi-db/`](./kisaragi-db/) | project ごとの計画、状態、証跡、実装物の正本 | [`kisaragi-db/agents.md`](./kisaragi-db/agents.md) |
| [`kisaragi-ruling/`](./kisaragi-ruling/) | 運用 rule と ruling の置き場 | [`AGENTS.md`](./AGENTS.md) |
| [`kisaragi-skills/`](./kisaragi-skills/) | skill 正本 | [`AGENTS.md`](./AGENTS.md) |
| [`kisaragi-tree/`](./kisaragi-tree/) | junction による閲覧 tree | [`kisaragi-tree/agents.md`](./kisaragi-tree/agents.md) |

## 現在の project 対応

| project code | project 名 | 概要 | 主な入口 |
| --- | --- | --- | --- |
| `prj-kisaragi_0001` | `prj-direview` | read-only dual-pane viewer project | [`project-truth.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0001/project-truth.md) |
| `prj-kisaragi_0002` | `prj-trajectreview` | `correcting`、`modeling`、`reviewing` の 4 app 構成で `3DGS` と trajectory review を進める project | [`project-truth.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/project-truth.md) |
| `prj-kisaragi_0003` | `remote-pwsh` | remote recovery と smartphone fallback の project | [`project-truth.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0003/project-truth.md) |

## `prj-kisaragi_0002` の入口

- project truth: [`project-truth.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/project-truth.md)
- 統合計画書: [`ux-b2t-hypo.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/ux-b2t-hypo.md)
- Codex gate 記録: [`codex-mrl-test-evidence.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/codex-mrl-test-evidence.md)
- admin 手順: [`admin-mrl-test-method.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-method.md)
- admin 証跡: [`admin-mrl-test-evidence.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-evidence.md)

## `prj-kisaragi_0001` の入口

- project truth: [`project-truth.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0001/project-truth.md)
- 統合計画書: [`ux-b2t-hypo.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0001/ux-b2t-hypo.md)
- Codex gate 記録: [`codex-mrl-test-evidence.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0001/codex-mrl-test-evidence.md)
- admin 手順: [`admin-mrl-test-method.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0001/admin-mrl-test-method.md)
- admin 証跡: [`admin-mrl-test-evidence.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0001/admin-mrl-test-evidence.md)
- 参考 release line: [`market_release_lines.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0001/market_release_lines.md)

## `prj-kisaragi_0003` の入口

- project truth: [`project-truth.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0003/project-truth.md)
- 統合計画書: [`ux-b2t-hypo.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0003/ux-b2t-hypo.md)
- Codex gate 記録: [`codex-mrl-test-evidence.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0003/codex-mrl-test-evidence.md)
- admin 手順: [`admin-mrl-test-method.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0003/admin-mrl-test-method.md)
- admin 証跡: [`admin-mrl-test-evidence.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0003/admin-mrl-test-evidence.md)

## 読み始め方

1. repository 全体の rule は [AGENTS.md](./AGENTS.md) を読む。
2. project の狙いは `project-truth` を読む。
3. 現在の実装計画と gate は `ux-b2t-hypo.md` と `codex-mrl-test-evidence.md` を読む。
4. 人が試す手順は `admin-mrl-test-method.md` を読む。
