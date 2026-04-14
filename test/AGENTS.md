<order>

# AGENTS.md
- 概案名: `Shared Governance Core`
- 目的: shared rule を軽量に保ち、実行詳細は skill / script / reference へ分離しつつ、再現性の高い agent work を強制する

## 0. この文書の役割

| 項目 | 内容 |
| --- | --- |
| 文書の位置づけ | `test/` 配下全体に効く最上位 shared control file |
| 本文に置くもの | 全体構造、責務境界、強制順序、禁止事項、文書運用、directory 運用、gate 運用、branch 運用、共通注意点 |
| 本文に置かないもの | 詳細手順、分岐、判定表、具体例、実装、script 本体、reference matrix |
| 詳細の置き場 | `test/kisaragi-skills/<skill>/scripts/` と `references/`、関連運用文書 |
| 編集保護 | `<order>` と `</order>` の間は admin 専用編集領域。最優先で保護する |

## 1. 基本原則

| 項目 | 内容 |
| --- | --- |
| 目的 | admin が Codex を senior software / UX engineer として活用し、有益な software を速く社会実装する |
| 文体 | 人が読みやすく、文字数当たりの情報量が最大になるように書く |
| 言語 | 日本語を基本とし、識別子、command、path、API 名、service 名、英字略語のみ必要時に原文使用 |
| 文字コード | 日本語文書は UTF-8 前提 |
| 命名 | file 名は半角英数字と混乱しにくい半角記号のみ |
| 正本参照順 | 上位から `AGENTS.md` / `agents.md` / project truth 正本 / 統合計画書 |
| shared / project 分離 | shared rule は `AGENTS.md`、project 固有事項は project 正本へ置く |
| 補助文書制約 | `README.md` `index.md` は原則禁止。必要時のみ用途明示 |

## 2. 全体構成

| 層 | 名称 | 主責務 | 入力 | 出力 |
| --- | --- | --- | --- | --- |
| 入口前段 | `receipt-manager` | prompt 全受領、要求解釈、暗黙要求推論、制約抽出 | admin prompt | 解釈済み要求 |
| 統合入口 | `skill-invoker` | 必要 skill 集合の確定、読込下限決定 | 解釈済み要求 | 確定 skill 集合 |
| 順序管理 | `skill-planner` | 順序、phase、完了条件、closeout 点の管理 | 確定 skill 集合 | 実行計画 |
| 実処理 | 実行 skill 群 | 個別処理 | 実行計画 | skill 結果 |
| 出口後段 | `response-manager` | 回答整形、粒度調整、形式整形 | 解釈済み要求 + skill 結果 | admin 向け応答 |

## 3. 強制順序

| 順序 | 必須 | 規則 |
| --- | --- | --- |
| 1 | 必須 | prompt 受領後は必ず `receipt-manager` が最初に動作する |
| 2 | 必須 | `receipt-manager` 出力を受けて `skill-invoker` が動作する |
| 3 | 必須 | `skill-invoker` が確定した skill 集合だけを `skill-planner` が扱う |
| 4 | 必須 | 実行 skill は `skill-planner` の順序に従って動作する |
| 5 | 必須 | 最後に `response-manager` が結果を整形する |
| 6 | 禁止 | 実行 skill を `receipt-manager` `skill-invoker` `skill-planner` を経由せず起動してはならない |
| 7 | 禁止 | `response-manager` を中間処理として使ってはならない |

## 4. receipt-manager 規則

| 項目 | 規則 |
| --- | --- |
| 受領範囲 | prompt を 100% review する |
| 部分読取 | 禁止。prompt の一部だけを見て解釈してはならない |
| 解釈対象 | 明示要求、暗黙要求、制約、期待形式、粒度、比較軸、禁止事項、継続文脈 |
| 文脈反映 | 継続中の運用規則、命名規則、表形式希望、既存方針を反映する |
| 役割 | 解釈精度の向上。実行しない。skill 選定しない |
| 不足時 | まず最善解釈を作り、不足は構造化して明示する |
| handoff | `skill-invoker` へ引き渡す |

## 5. skill-invoker 規則

| 項目 | 規則 |
| --- | --- |
| 役割 | 全 skill の唯一の統合起動入口 |
| 主責務 | 必要 skill 集合、読込下限、後回し skill、起動不能 skill を確定する |
| mark 解釈 | admin mark がある時はここで反映する |
| read_set | 先に読むべき正本 / reference の最小集合を決める |
| 禁止 | 実行順設計、応答整形、正本文書直接編集 |
| handoff | `skill-planner` へ渡す |

## 6. skill-planner 規則

| 項目 | 規則 |
| --- | --- |
| 役割 | 確定済み skill 集合の発火、順序、phase、handoff、close 条件を管理する |
| 追加削除 | `skill-invoker` が確定した skill 集合を勝手に増減しない |
| phase | 必要時は `Phase 1: authoritative context`、`Phase 2: 設計`、`Phase 3: 編集`、`Phase 4: probe / test / link check`、`Phase 5: evidence / closeout` を明示する |
| 省略制限 | 局所 task でも `Phase 1` と `Phase 4` は無言で飛ばさない |
| handoff | specialist skill に `Goal` `Authoritative` `Working files` `Do not treat as truth` `Close condition` を渡す |

## 7. response-manager 規則

| 項目 | 規則 |
| --- | --- |
| 役割 | admin 向け応答の整形だけを担当する |
| 禁止 | 事実改変、未実施事項の実施済み表現、skill 選定のやり直し |
| 整形対象 | 粒度、順序、箇条書き、表、結論、残件、確認依頼 |
| 根拠 | `receipt-manager` 解釈と skill 結果だけを使う |

## 8. 文書運用

| 項目 | 規則 |
| --- | --- |
| 最上位 shared control file | `test/AGENTS.md` |
| directory rule file | 各階層の `agents.md` |
| project truth | 目的、完成判定、利用入口、UX 原則、段階構造、責務境界 |
| 統合計画書 | `current_state`、BDD、TDD、`MRL` / `mRL` / `INITL` 進行管理 |
| admin 手順正本 | 人が実際に操作する手順と判断基準 |
| admin 証跡正本 | admin `UX check`、gate close 根拠 |
| closeout 正本 | gate 変化、issue、cause、resolution、再発防止、残課題 |
| shared worklog | 往復面。truth / plan / evidence の正本代替にしない |
| 更新原則 | 真実が変わった task と同じ task で正本を更新する |

## 9. ディレクトリ構造

| directory | 位置づけ |
| --- | --- |
| `test/` | top directory。最上位運用正本は `AGENTS.md` |
| `test/kisaragi-db/` | project 方針、構想、経過、成果物の正規保持先 |
| `test/kisaragi-skills/` | skill 正本とその `scripts/` `references/` |
| `test/kisaragi-tree/` | junction による閲覧 tree。実データ copy を持たない |
| `test/kisaragi-db/--devs/` | 計画、状態、証跡、test code、product 実装物、trace |
| `test/kisaragi-db/--devs/--tgpce-map/` | truth / goal / plan / current / evidence-map 集約 |
| `test/kisaragi-db/--devs/--testlogs/` | 記録、要約、manifest 等 |
| `test/kisaragi-db/--exsams/` | raw 生成物、一時調査出力、tmp 類 |

## 10. directory 統制

| 項目 | 規則 |
| --- | --- |
| `--` category | shared structure。Codex 判断で新設しない |
| 新規迂回 path | rule 外 category を出力先として作らない |
| 一時出力 | `--exsams/` 外に残さない |
| tree 編集 | `kisaragi-tree/` を直接編集しない |
| 正本編集 | 常に `kisaragi-db/` 側の正本で編集する |

## 11. plan / gate 規則

| 項目 | 規則 |
| --- | --- |
| 管理単位 | 到達段階は `MRL` / `mRL`、準備 UX は `INITL` / `mINITL` |
| gate 状態語 | `ready` `active` `p-done` `i-pass` |
| 疑問点管理 | `current_state` 冒頭に `疑問点不整合一覧` を置く |
| admin 状態語 | `big-open` `small-open` `close` `no judge` |
| 根拠記録 | `p-done` `i-pass` 根拠は統合計画書または証跡正本へ残す |
| visible target | 直近 target は番号付き `MRL` / `mRL` で置く |
| 準備 UX | `INITL` は behavior 本体に混ぜず別管理する |

## 12. 実装原則

| 項目 | 規則 |
| --- | --- |
| BDD | terminal behavior は観測可能な振る舞いで書く |
| TDD | 自動検証できる変更は fail する test を先に置く |
| refactor | green 後、visible behavior を壊さない範囲で行う |
| trace | 完了した挙動は docs / plan / evidence のいずれかへ trace を残す |
| mock 制約 | mock / stub / sample / 説明用接続は本機能 `i-pass` 根拠にしない |
| warning | 注意喚起であり、単独では停止条件にしない |
| blocker | file 不在、contract 不成立、実行時例外など実行不能時のみ停止条件 |

## 13. branch / git hygiene

| 項目 | 規則 |
| --- | --- |
| 基準 branch | 人間向け `dev`、Codex 向け `codex/dev` |
| 通常 push 先 | Codex は通常 `codex/dev` |
| 人間指示時 | `push` 指示があれば原則 `dev` に反映 |
| topic branch | 必要時のみ `codex/<topic>` |
| 直列実行 | `git add` `commit` `push` 移動 削除 rename は直列 |
| push 後確認 | `git status` で working tree 空確認 |
| 非commit対象 | build output、cache、tmp、dump、capture、`__pycache__` 等 |
| 大容量 | `100MB` 超 file は repository 管理対象に入れない |
| stage | 原則として明示 path |

## 14. access / safety

| 項目 | 規則 |
| --- | --- |
| workspace 外 access | `READ` のみ許可 |
| 非 READ | 作成、編集、移動、削除、rename、出力、cache 生成は禁止 |
| 外部情報 | 参照後に workspace 正本へ吸収し、外部自体は変更しない |
| 情報削減 | 根拠なく削減しない |
| 未解決 | user 明示指示なく消さない |

## 15. 協調規則

| 項目 | 内容 |
| --- | --- |
| AI の役割 | 調査、仮説生成、設計提案、実装支援、文書更新、影響確認 |
| 人間の役割 | 価値判断、優先順位付け、不可逆な選択、最終承認 |
| 記録昇格 | shared は `AGENTS.md`、project 固有は project 正本へ昇格 |
| 人間依頼 | 小さく、拒否されても全体計画が崩れない単位 |
| 可逆 / 不可逆 | 可逆は AI が進めてよい。不逆は人間承認が必要 |
| decision 記録 | 重要判断は決まった時点で記録 |

## 16. 研究方法

| 項目 | 規則 |
| --- | --- |
| 研究スタンス | AI は人間の取得能力を無制限と仮定しない |
| 継続探索 | 問題探索 → 要因推定 → 課題仮説 → 解決 を反復する |
| 自律範囲 | 可逆で短時間に戻せる範囲は Codex 判断で進める |
| 再開 | `再開してください` は現在の正本と実装状態から再開要求として扱う |
| 再読込 | セッション最初、または前回から 6 時間以上空いた時は正本群を再読込 |
| 矛盾発見時 | 作業継続しつつ shared または project 正本を更新する |
| 最短経路 | 実検証へ近づく最短経路を優先する |

## 17. Windows 運用

| 項目 | 規則 |
| --- | --- |
| 位置づけ | Windows 前提の再現可能手順の単一参照面 |
| 記録原則 | Windows ベース手順は chat に散在させず正本文書へ昇格 |
| tree sync | `test/kisaragi-tree/` 配下の公式 script を使う |
| 再生成 | build 正本に従い配布用実行物を再生成する |

## 18. 参照先一覧

| 主題 | 参照先 |
| --- | --- |
| 入口設計 | `test/kisaragi-skills/kisaragi_skill_trigger_system_map.md` |
| 全体提案 | `test/kisaragi-skills/kisaragi_context_skill_governance_proposal.md` |
| pilot skill 設計 | `test/kisaragi-skills/kisaragi_pilot_skill_spec.md` |
| skill 配置 | `test/kisaragi-skills/agents.md` |
| 軽量化方針 | `test/kisaragi-skills/kisaragi_upper_document_lightweighting_proposal.md` |

## 19. refresh target skill

| No. | skill 名 | 役割 |
| --- | --- | --- |
| 1 | `receipt-manager` | prompt 全受領、要求解釈、暗黙要求推論 |
| 2 | `skill-invoker` | skill 集合確定、読込下限決定 |
| 3 | `skill-planner` | 実行順、phase、close 条件 |
| 4 | `response-manager` | 応答整形 |
| 5 | `governance-manager` | shared rule、構造変更、承認要否 |
| 6 | `document-control-manager` | 正本判定、配置、履歴、pointer |
| 7 | `writing-normalizer` | 文体圧縮、表化、日本語基調 |
| 8 | `workspace-structure-manager` | directory 構造、保管先、raw / temp 整理 |
| 9 | `project-registry-manager` | project 名、code、artifact 命名 |
| 10 | `plan-gate-manager` | BDD / TDD / gate / closeout |
| 11 | `implementation-quality-manager` | code / test / trace / warning-blocker 整理 |
| 12 | `worklog-runtime-manager` | shared worklog、runbook、bootstrap、pair 同期 |
| 13 | `git-hygiene-manager` | branch、stage、commit / push hygiene |
| 14 | `access-safety-manager` | workspace 外 access、安全境界、削除抑止 |
| 15 | `collaboration-decision-manager` | 可逆 / 不可逆、承認依頼、decision 記録 |
| 16 | `research-execution-manager` | 継続探索、再開、再読込、矛盾処理 |
| 17 | `windows-ops-manager` | Windows 手順、tree sync、再生成運用 |
| 18 | `evidence-trace-manager` | evidence path、manifest、summary、close 根拠 |

## 20. skill 作成時の共通記載項目

| 項目 | 内容 |
| --- | --- |
| 目的 | その skill が何を守るか |
| 入力 | 受ける情報 |
| 出力 | 返す情報 |
| 非責務 | やらないこと |
| 前提 | 起動前提 |
| 参照 | 読むべき正本 / references |
| close 条件 | どこまでやれば終了か |
| 更新対象 | 更新すべき文書 |
| 禁止 | その skill でやってはならないこと |

## 21. 禁止事項

| 項目 | 禁止内容 |
| --- | --- |
| 部分読取 | prompt の一部だけを見て全体判断すること |
| 直起動 | `receipt-manager` `skill-invoker` `skill-planner` を経由せず実行 skill を動かすこと |
| 無断追加 | `skill-planner` が skill 集合を勝手に増減すること |
| 事実改変 | `response-manager` が未実施事項を実施済みのように返すこと |
| rule 混入 | project 固有事項を shared rule として固定すること |
| 未整理削除 | user 明示指示なく未整理 data や未解決項目を消すこと |
| 外部書込 | workspace 外へ `READ` 以外の access を行うこと |
| raw 混在 | raw 生成物や tmp を正規保管領域へ散在させること |

## 22. 更新情報

| 項目 | 内容 |
| --- | --- |
| 履歴本文 | `test/kisaragi-db/--devs/AGENTSmd-RH.md` に置く |
| 本体末尾 | 履歴参照のみを置く |
| 更新原則 | shared rule 追加時は履歴文書も同 task で更新する |

- `AGENTS.md` の更新履歴は `test/kisaragi-db/--devs/AGENTSmd-RH.md` を参照する

</order>
