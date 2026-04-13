# kisaragi upper document lightweighting proposal

## 概案名対応

| 現行正式名 | 概案名 | `test/` refresh file 名 |
| --- | --- | --- |
| `AGENTS.md` | `Shared Governance Core` | `AGENTS.md` |
| `AGENTSmd-RH.md` | `Shared Governance Core History` | `AGENTSmd-RH.md` |
| `kisaragi-skills/agents.md` | `Skill Structure Ledger` | `agents.md` |
| `project-truth.md` | `Project Truth Core` | `project-truth-core.md` |
| `hi-ai-unified-blueprint.md` | `Realtime Compass And Status` | `realtime-compass-and-status.md` |
| `admin-mrl-test-method.md` | `Admin UX Method` | `admin-ux-method.md` |
| `admin-mrl-test-evidence.md` | `Admin UX Evidence` | `realtime-compass-and-status.md` へ吸収 |
| `codex-mrl-test-evidence.md` | `Codex Gate Closeout` | `realtime-compass-and-status.md` へ吸収 |
| `resume-startup-plan.md` | `Restart Launch Pad` | `realtime-compass-and-status.md` へ吸収 |
| `sharedlogs_<thema>.md` | `Collaborative Worklog` | `collaborative-worklog_<thema>.md` |

## 目的

- `skill-distributor -> skill-planner -> child skill / specialist skill` の運用を前提に、上位文書から機械処理へ落とせる責務を整理する。
- 正本は文書に残しつつ、文書が持つべきでない実務手順、判定補助、同期補助を child skill へ移す。
- file 名は当面変えず、まずは各文書の責務と密度を整える。

## 基本方針

- 文書は `意思決定`、`恒久 truth`、`gate 状態`、`admin 判断` を持つ。
- skill は `読取補助`、`差分抽出`、`task 分割`、`同期実行`、`evidence 反映補助` を持つ。
- 文書から落とすのは `どう判定するか` と `どう実行するか` のうち、繰り返し機械化できる部分である。
- 文書に残すのは `何を正とするか`、`何を禁じるか`、`何を完了とみなすか`、`なぜそうするか` である。
- canonical は後から並立追加する前提で増やさず、必須 canonical 要素を先に定義し、追加時は具体定義不足の補完として扱う。
- refresh では `resume-startup-plan.md` と `*-mrl-test-evidence.md` を separate canonical から外し、`realtime-compass-and-status.md` に吸収する。
- `sharedlogs_<thema>.md` は ring buffer とし、上限 `50k` を超える前に durable fact を昇格し、本文は循環更新する。

## `AGENTS.md` から外す `D` の吸収先

| `AGENTS.md` で外す内容 | 吸収先 |
| --- | --- |
| refresh canonical set 定義 | `refresh-file-map.md`、対象 project 文書 |
| `HAUB` 非同一視メモ | 本 proposal、`agents_skillification_review.md` |
| `test refresh addendum` | 本 proposal、対象 project refresh 文書 |
| `skill gap` | `skill-direct-gap-list.md` |
| admin evidence / Codex closeout / restart の compass 吸収方針 | 本 proposal、対象 project `realtime-compass-and-status.md` |

## child skill へ落とす責務

| family | child skill | 文書から落とせる責務 |
| --- | --- | --- |
| distributor child | `rule-snapshot-reader` | 最新 rule 面の読取順、rule snapshot の要約手順 |
| distributor child | `authoritative-doc-scope-resolver` | 今回読むべき文書と更新候補文書の機械切り分け |
| distributor child | `rule-diff-clarifier` | prompt と現行 rule の差分抽出、shared / project 切り分け |
| planner child | `task-intent-normalizer` | prompt 意図の実務型への正規化 |
| planner child | `task-scope-splitter` | 複数指示の task 単位への分割 |
| planner child | `close-condition-definer` | close 条件、必要 test、必要 evidence の整理 |
| script / docs child | `doc-target-resolver` | code 変更時の文書更新先洗い出し |
| script / docs child | `test-and-evidence-recorder` | test 結果と evidence 正本反映の補助 |
| runtime child | `artifact-handoff-mapper` | producer / consumer artifact 契約の整理 |
| runtime child | `path-contract-scanner` | path read / write 契約と alias 棚卸し |
| external child | `drive-input-bootstrap-checker` | `Drive mount -> input 解決` の初動確認 |
| external child | `runtime-bootstrap-scope-resolver` | clean bootstrap runbook へ昇格すべき範囲の抽出 |
| closeout child | `evidence-destination-resolver` | 既存 evidence 面への記録先選定 |
| closeout child | `log-promotable-facts-extractor` | shared log から正本へ昇格すべき事実の抽出 |

## 文書ごとの概案

### 1. `AGENTS.md`

- 概案名: `Shared Governance Core`
- 役割整理:

| 残す責務 | 落とす責務 | 移行先 | 統合・重複整理 |
| --- | --- | --- | --- |
| shared directory rule | prompt をどう読み解くか | `rule-snapshot-reader`、`rule-diff-clarifier` | shared rule 本体だけ残し、読解手順は削る |
| authoritative 文書の優先順位 | 文書更新先をどう機械選定するか | `authoritative-doc-scope-resolver`、`doc-target-resolver` | 優先順位だけ残し、都度選定ロジックは child skill へ統合する |
| branch / encoding / hygiene | close 条件をどう組み立てるか | `close-condition-definer` | hygiene 原則は残し、task close 組立ては除去する |
| 可逆 / 不可逆判断 | evidence 記録先をどう都度選ぶか | `evidence-destination-resolver` | 承認境界だけ残し、記録 routing 手順は child skill へ移す |
| shared gate 語彙 | task 分割の一般手順 | `task-scope-splitter` | 状態語だけ残し、 task 分割アルゴリズムは持たない |
| skill 運用の最上位原則 | 実行順の詳細定型 | `skill-planner` | 最上位原則だけ残し、 orchestration detail は planner へ集約する |
- 理由:
  - `AGENTS.md` は shared rule の正本であり、毎 task の手順書になると重すぎる。
  - child skill で吸収できる部分まで抱えると、shared governance と実務補助が混線する。

### 2. `kisaragi-skills/agents.md`

- 概案名: `Skill Structure Ledger`
- 役割整理:

| 残す責務 | 落とす責務 | 移行先 | 統合・重複整理 |
| --- | --- | --- | --- |
| skill 一覧 | project 固有の手順 | project 文書群 | registry から project 固有 detail を排除する |
| parent / child / specialist の関係 | task ごとの実行例の詳細 | 各 `SKILL.md`、`references/` | 構造説明に集中し、運用例は各 skill 側へ寄せる |
| family ごとの役割境界 | project 別の route 説明 | project `HAUB`、runbook 群 | family 境界だけ残し、 route 例は project 側に統合する |
| trigger ownership の所在 | 実務アルゴリズム本文 | `skill-distributor`、`skill-planner` | ownership 記述だけ残し、処理本文は親 skill へ集約する |
- 理由:
  - この文書は skill registry と構造説明に徹した方が drift しにくい。

### 3. `project-truth.md`

- 概案名: `Project Truth Core`
- 役割整理:

| 残す責務 | 落とす責務 | 移行先 | 統合・重複整理 |
| --- | --- | --- | --- |
| 最終目的 | prompt 処理の仕方 | `rule-snapshot-reader`、`task-intent-normalizer` | truth は目的面に戻し、 prompt 解釈文は除去する |
| 最小価値 | 文書更新漏れ防止の実務手順 | `doc-target-resolver`、`script-doc-sync-enforcer` | 価値定義だけ残し、同期手順は skill へ統合する |
| app / artifact / 外部境界 | task 分割の機械手順 | `task-scope-splitter` | 境界定義は残し、 task structuring は child skill へ移す |
| project 固有の恒久 contract | evidence routing の細則 | `evidence-destination-resolver` | contract は残し、記録先選定 detail は別出しする |
| 採用済み canonical route の判断 | clean bootstrap の一般アルゴリズム | `runtime-bootstrap-scope-resolver`、`drive-input-bootstrap-checker` | 採用 route 判断だけ残し、 bootstrap 手順は runbook / skill へ寄せる |
- 理由:
  - `project-truth.md` は project の不変面を持つべきで、task 実務の定型は skill 側へ寄せた方が保守しやすい。

### 4. `realtime-compass-and-status.md`

- 概案名: `Realtime Compass And Status`
- 役割整理:

| 残す責務 | 落とす責務 | 移行先 | 統合・重複整理 |
| --- | --- | --- | --- |
| `current_state` | 文書読取順の説明 | `authoritative-doc-scope-resolver` | 状態だけ残し、読取手順は child skill へ移す |
| 疑問点不整合一覧 | code 変更時の一般的な同期アルゴリズム | `script-doc-sync-enforcer`、`doc-target-resolver` | 論点管理だけ残し、同期 algorithm は排除する |
| BDD / TDD | shared log から何を昇格するかの一般則 | `log-promotable-facts-extractor` | plan と log 管理の重複を分離する |
| gate 対応表と `p-done` 根拠 | test 記録先 routing の一般則 | `test-and-evidence-recorder`、`evidence-destination-resolver` | `p-done` 行自体が旧 evidence 相当の根拠を持つようにし、routing algorithm は skill へ寄せる |
| support-MRL | task close 組立ての手順 | `close-condition-definer` | temporary goal だけ残し、 close 組立て本文は削る |
| project 固有の比較設計 | fresh runtime 再現の一般手順 | `runtime-bootstrap-scope-resolver` | 比較設計は残すが、採用済み route は active decision でなく canonical contract として扱う |
| 再開導線 | restart 専用補助文書 | `realtime-compass-and-status.md` 自身 | restart note は separate 文書にせず `current_state` から直に再開できるよう統合する |
- 理由:
  - `HAUB` は project の進行正本であり、restart と evidence を別 file に分けるより 1 面で current / gate / 根拠を追える方が軽い。

### 5. `admin-mrl-test-method.md`

- 概案名: `Admin UX Method`
- 役割整理:

| 残す責務 | 落とす責務 | 移行先 | 統合・重複整理 |
| --- | --- | --- | --- |
| admin が実施する手順 | Codex 側の test 実行手順 | `test-and-evidence-recorder`、specialist skill 群 | admin 操作と Codex 実装手順の混在を解消する |
| UX check の観点 | evidence routing の機械判定 | `evidence-destination-resolver` | UX 観点だけ残し、記録 routing は child skill へ移す |
| 手順ごとの確認条件 | task close の一般条件 | `close-condition-definer` | admin 確認条件と task close 条件の重複を分離する |
- 理由:
  - 人間の操作手順書に AI 内部運用まで混ぜると読みにくくなる。

### 6. `admin-mrl-test-evidence.md`

- 概案名: `Admin UX Evidence`
- 役割整理:

| 残す責務 | 落とす責務 | 移行先 | 統合・重複整理 |
| --- | --- | --- | --- |
| refresh canonical では separate 正本にしない | admin 実測結果 | `realtime-compass-and-status.md` | `p-done` / `i-pass` 根拠を compass へ統合し、旧 file は temp archive とする |
| refresh canonical では separate 正本にしない | UX 判断 | `realtime-compass-and-status.md` | method と evidence の cross reference を compass 1 面へ寄せる |
| refresh canonical では separate 正本にしない | gate close の根拠 | `realtime-compass-and-status.md`、必要時 `--testlogs/` | evidence 面の並立をやめる |
- 理由:
  - refresh では `p-done` の計画と根拠を同じ table / section で追う方が軽い。

### 7. `codex-mrl-test-evidence.md`

- 概案名: `Codex Gate Closeout`
- 役割整理:

| 残す責務 | 落とす責務 | 移行先 | 統合・重複整理 |
| --- | --- | --- | --- |
| refresh canonical では separate 正本にしない | gate change、issue / cause / resolution | `realtime-compass-and-status.md` | Codex closeout も `p-done` / `active` の根拠欄へ統合する |
| refresh canonical では separate 正本にしない | recurrence prevention | `realtime-compass-and-status.md` | closeout detail を current / gate と同一面へ寄せる |
| refresh canonical では separate 正本にしない | evidence path | `realtime-compass-and-status.md`、`--testlogs/` | path 記録は compass へ集約する |
- 理由:
  - refresh では `p-done` 到達条件と closeout 根拠を分けない方が drift しにくい。

### 8. `resume-startup-plan.md`

- 概案名: `Restart Launch Pad`
- 役割整理:

| 残す責務 | 落とす責務 | 移行先 | 統合・重複整理 |
| --- | --- | --- | --- |
| refresh canonical では separate 正本にしない | 再開順、直近 blocker、初動確認 | `realtime-compass-and-status.md` | restart 導線は current_state 冒頭へ吸収し、separate note はやめる |
- 理由:
  - current を見れば再開できる構造にした方が管理点が減る。

### 9. `sharedlogs_<thema>.md`

- 概案名: `Collaborative Worklog`
- 役割整理:

| 残す責務 | 落とす責務 | 移行先 | 統合・重複整理 |
| --- | --- | --- | --- |
| notebook cell 往復 | canonical runbook | product runbook 群、`runtime-bootstrap-scope-resolver` | worklog と runbook の重複を解消する |
| error 全文 | 恒久 truth | `project-truth.md`、`HAUB` | raw error と恒久判断の混在を解消する |
| 直近 trial | gate close の唯一根拠 | `realtime-compass-and-status.md`、必要時 `--testlogs/` | log と根拠の役割を分離する |
| admin / codex の一時共同作業面 | 昇格対象の手作業抽出 | `log-promotable-facts-extractor` | 正本昇格作業を child skill 側へ統合する |
- 理由:
  - shared log は ring buffer 前提であり、持続価値のある事実は `log-promotable-facts-extractor` で正本へ昇格させるべきである。

## `--tgpce-map/` 再割付表

現時点の `--tgpce-map/prj-kisaragi_****/` の正式文書について、この方針での再割付を次のように固定する。

| 正式文書名 | 主責務 | ownership | child skill へ落とす責務 | 備考 |
| --- | --- | --- | --- | --- |
| `project-truth.md` | 恒久 truth、最終目的、最小価値、app / artifact / 外部境界、採用済み canonical contract | truth ownership | prompt 解釈、文書同期手順、close 判定手順、bootstrap 一般手順 | active な route 比較や blocker は持たない |
| `hi-ai-unified-blueprint.md` | current_state、疑問点不整合一覧、BDD、TDD、MRL / INITL / support-MRL、次の一手、採用済み canonical contract、`p-done` / `i-pass` 根拠 | current / gate / next action / evidence ownership | 文書読取順、一般的な同期 algorithm、sharedlog 昇格一般則、close 組立て detail | 採用済み route は active decision でなく canonical contract として扱う |
| `admin-mrl-test-method.md` | admin UX 手順、確認観点、手順ごとの確認条件 | admin method ownership | Codex 側 test 実行手順、evidence routing 判定、task close 一般条件 | 人の操作書に徹する |
| `admin-mrl-test-evidence.md` | refresh canonical では `HAUB` へ吸収 | temp archive ownership | separate evidence 運用全体 | 旧証跡の退避先としてだけ残す |
| `codex-mrl-test-evidence.md` | refresh canonical では `HAUB` へ吸収 | temp archive ownership | separate closeout 運用全体 | 旧 closeout の退避先としてだけ残す |
| `resume-startup-plan.md` | refresh canonical では `HAUB` へ吸収 | temp archive ownership | separate restart 運用全体 | 旧 restart note の退避先としてだけ残す |
| `sharedlogs_<thema>.md` | notebook cell、長い script、error 全文、admin / codex の raw collaborative trace | worklog ownership | 昇格対象の手作業抽出、canonical runbook、恒久 truth、gate close の唯一根拠 | `50k` 上限の ring buffer とする |

## `--tgpce-map/` 再割付の結論

- `--tgpce-map/` の正式文書 7 本について、役割再割付の受け皿はすべて定義済みである。
- したがって、構造上「割り振り先が未定の正式文書」は現時点では無い。
- ただし、文書本文の中身には混在が残る可能性があり、再割付が難しいのは「文書そのもの」ではなく「文書内の一部段落」である。

## 割付が難しいもの

再割付が難しい、または混在しやすいものは次である。

| 対象 | 難しい理由 | 基本方針 |
| --- | --- | --- |
| `sharedlogs_<thema>.md` に残った採用済み bootstrap や contract | 共同作業 log から product runbook / truth へ昇格しきれず残留しやすい | `log-promotable-facts-extractor` 前提で runbook / truth / evidence へ昇格する |
| `hi-ai-unified-blueprint.md` の route 比較記述のうち、既に採用済みになったもの | active decision と採用済み canonical contract を分ける必要がなくなる | 採用済みなら active 状態を消し、canonical contract として扱う |
| `sharedlogs_<thema>.md` の ring buffer 前に残る旧本文 | 既存 log が `50k` を大きく超えていると一気に整理しにくい | refresh では temp archive へ退避し、新 canonical worklog を `50k` 制限で再開する |

## 上位文書で今後さらに薄くできる記述

| 対象記述 | 受け皿 skill | 文書に残すべき最小形 |
| --- | --- | --- |
| 「何を読んでから着手するか」の詳細手順 | `rule-snapshot-reader` / `authoritative-doc-scope-resolver` | authoritative 優先順位だけ残す |
| 「複数指示をどう分けるか」の説明 | `task-scope-splitter` | 取りこぼし禁止だけ残す |
| 「何をもって close とするか」の組み立て方 | `close-condition-definer` | close に test と evidence が要る原則だけ残す |
| 「どの文書を更新するか」の都度判断 | `doc-target-resolver` | 同期必須の原則だけ残す |
| 「test 結果をどこへ書くか」の細かな routing | `test-and-evidence-recorder` / `evidence-destination-resolver` | 既存記録先を使う原則だけ残す |
| 「shared log から何を昇格するか」の判断 | `log-promotable-facts-extractor` | log を唯一正本にしない原則だけ残す |
| `Drive mount -> input 解決` の細かな確認順 | `drive-input-bootstrap-checker` | external compute は clean bootstrap を正にする原則だけ残す |

## 推奨する次の順序

1. `AGENTS.md` から実務アルゴリズム文を洗い出し、原則文だけ残す。
2. `kisaragi-skills/agents.md` に parent / child / specialist の family map を固定する。
3. `project-truth.md` と `HAUB` から、機械処理化できる説明を child skill へ逃がし、判断文だけ残す。
4. `sharedlogs` 運用で、昇格対象を `log-promotable-facts-extractor` 前提に寄せる。

## この案にした理由

- 正本は文書、実務の再現性は skill という分担を明確にするため。
- 上位文書が大きくなる主因は、判断文に加えて判定手順まで抱えることにあるため。
- child skill を増やすことで、`skill-distributor` を集中型のまま軽くし、同時に上位文書も軽くできるため。
- project ごとの差は文書に残し、project 横断の繰り返し処理は skill に寄せる方が drift を抑えやすいため。

