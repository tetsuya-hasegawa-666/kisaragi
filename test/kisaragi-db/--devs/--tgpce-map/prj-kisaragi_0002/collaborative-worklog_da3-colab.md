# collaborative-worklog_da3-colab.md
- 概案名: `Collaborative Worklog`

## 役割

- この file は `prj-kisaragi_0002` の `DA3Metric-Large` `Colab` 実装について、admin と Codex が notebook cell、script、error、観測結果を往復するための ring-buffer worklog とする。
- この file は `project-truth-core.md`、`realtime-compass-and-status.md`、`admin-ux-method.md` の代替ではない。
- durable fact は速やかに `project-truth-core.md` または `realtime-compass-and-status.md` へ昇格する。
- ring buffer 導入前の旧本文は `temp-pre-ringbuffer-collaborative-worklog_da3-colab.md` へ退避済みとする。

## 容量制限

- 本文は `50k` 文字を上限とする。
- 上限を超える前に、持続価値のある内容を正本へ昇格する。
- 昇格後は、固定 header を残しつつ古い本文を削除し、最新往復だけを保持する。
- old log を唯一の保持場所にしてはならない。

## 読み方

- 固定 header はこの節までとする。
- これより下は `# codex` または `# admin` 見出しによる時系列追記だけを置く。
- 正規読み順は「最下部から上へ」とする。

## 記載ルール

- 途中挿入、途中修正、本文中ほどへの要約追記を禁止する。
- 既存本文は原則として書き換えず、必ず最下部へ追記する。
- `# codex` の追記は、必ず単調増加の通し番号 `v**` を付ける。
- shared rule 変更は `AGENTS.md`、project truth / plan / gate / evidence 変更は `project-truth-core.md` と `realtime-compass-and-status.md` へ別途反映する。

# codex

2026-04-13 v00 ring buffer reset。

- 旧本文は `temp-pre-ringbuffer-collaborative-worklog_da3-colab.md` へ退避した。
- 以後は `50k` 上限で運用する。
- durable fact は `realtime-compass-and-status.md` と `project-truth-core.md` を正とする。

# admin

```text
# <next-step> res

```

