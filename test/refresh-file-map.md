# refresh-file-map.md

## 記号

| 記号 | 意味 |
| --- | --- |
| `C` | refresh canonical |
| `O` | current origin snapshot |
| `T` | temp archive |
| `M` | original mirror |

## shared control

| 原本 | `C` | `O` | 備考 |
| --- | --- | --- | --- |
| `AGENTS.md` | `AGENTS.md` | `temp-current-origin-AGENTS.md` | refresh control |
| `AGENTSmd-RH.md` | `AGENTSmd-RH.md` | `temp-current-origin-AGENTSmd-RH.md` | refresh history |
| `kisaragi-skills/agents.md` | `kisaragi-skills/agents.md` | `kisaragi-skills/temp-current-origin-agents.md` | refresh skill ledger |

## `prj-kisaragi_0002` `--tgpce-map`

| 原本 | `C` | `O` | `T` | refresh 方針 |
| --- | --- | --- | --- | --- |
| `project-truth.md` | `project-truth-core.md` | `temp-current-origin-project-truth.md` | `-` | truth を圧縮再編 |
| `hi-ai-unified-blueprint.md` | `realtime-compass-and-status.md` | `temp-current-origin-hi-ai-unified-blueprint.md` | `-` | current / plan / gate / evidence 統合 |
| `admin-mrl-test-method.md` | `admin-ux-method.md` | `temp-current-origin-admin-mrl-test-method.md` | `-` | manual を維持 |
| `admin-mrl-test-evidence.md` | `realtime-compass-and-status.md` | `temp-current-origin-admin-mrl-test-evidence.md` | `temp-absorbed-admin-ux-evidence.md` | compass へ吸収 |
| `codex-mrl-test-evidence.md` | `realtime-compass-and-status.md` | `temp-current-origin-codex-mrl-test-evidence.md` | `temp-absorbed-codex-gate-closeout.md` | compass へ吸収 |
| `resume-startup-plan.md` | `realtime-compass-and-status.md` | `temp-current-origin-resume-startup-plan.md` | `temp-absorbed-restart-launch-pad.md` | compass へ吸収 |
| `sharedlogs_da3-colab.md` | `collaborative-worklog_da3-colab.md` | `temp-current-origin-sharedlogs_da3-colab.md` | `temp-pre-ringbuffer-collaborative-worklog_da3-colab.md` | `50k` ring buffer 化 |

## product / testlogs mirror

| scope | 原本件数 | `test/` 件数 | 状態 |
| --- | --- | --- | --- |
| `--products/prj-kisaragi_0002` `*.md/*.ipynb/*.json` | `112` | `112` | `M` |
| `--testlogs/prj-kisaragi_0002` `*.md/*.json/*.csv/*.txt` | `3` | `3` | `M` |

## refresh canonical set

| 区分 | file |
| --- | --- |
| shared control | `AGENTS.md` |
| shared history | `AGENTSmd-RH.md` |
| skill ledger | `kisaragi-skills/agents.md` |
| project truth | `project-truth-core.md` |
| project compass | `realtime-compass-and-status.md` |
| admin method | `admin-ux-method.md` |
| worklog | `collaborative-worklog_da3-colab.md` |

## 運用 rule

| 対象 | 正規 rule |
| --- | --- |
| restart | `realtime-compass-and-status.md` の `current_state` と `次の一手` から再開する |
| `p-done` / `i-pass` 根拠 | `realtime-compass-and-status.md` に統合する |
| old evidence / closeout / restart | temp archive としてだけ残す |
| worklog | `50k` ring buffer、durable fact は先に正本昇格 |

