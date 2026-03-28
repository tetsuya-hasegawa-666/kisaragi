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
| `prj-kisaragi_0001` | `prj-direview` | release / behavior / test matrix を持つ project | [`project-core.md`](./kisaragi-db/--devs/--project-truth/prj-kisaragi_0001/project-core.md) |
| `prj-kisaragi_0002` | `prj-trajectreview` | `correcting`、`modeling`、`reviewing` の 4 app 構成で `3DGS` と trajectory review を進める project | [`project-truth.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/project-truth.md) |
| `prj-remote-pwsh` | remote PowerShell tooling | remote recovery と architecture の参照 project | [`north_star.md`](./kisaragi-db/--devs/--project-truth/prj-remote-pwsh/north_star.md) |

## `prj-kisaragi_0002` の入口

- project truth: [`project-truth.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/project-truth.md)
- 計画正本: [`b2t-plans-result.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/b2t-plans-result.md)
- gate 記録: [`mrl-record.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/mrl-record.md)
- UX check manual: [`ux_check_manual.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/ux_check_manual.md)
- UX / gate evidence: [`mrl-ux-valid.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/mrl-ux-valid.md)
- intake spec: [`isensorium_xperia5iii_intake_spec.md`](./kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/isensorium_xperia5iii_intake_spec.md)

## `prj-kisaragi_0001` の入口

- project core: [`project-core.md`](./kisaragi-db/--devs/--project-truth/prj-kisaragi_0001/project-core.md)
- BDD compass: [`bdd-release-compass.md`](./kisaragi-db/--devs/--plans/prj-kisaragi_0001/bdd-release-compass.md)
- TDD matrix: [`tdd-test-matrix.md`](./kisaragi-db/--devs/--plans/prj-kisaragi_0001/tdd-test-matrix.md)
- release line: [`market_release_lines.md`](./kisaragi-db/--devs/--plans/prj-kisaragi_0001/market_release_lines.md)
- UX manual: [`ux_check_manual.md`](./kisaragi-db/--devs/--evidence/prj-kisaragi_0001/ux_check_manual.md)

## 読み始め方

1. repository 全体の rule は [AGENTS.md](./AGENTS.md) を読む。
2. project の狙いは `project-truth` を読む。
3. 現在の実装計画と gate は `b2t-plans-result.md` と `mrl-record.md` を読む。
4. 人が試す手順は `ux_check_manual.md` を読む。
