# kisaragi context-skill governance proposal

## 文書の目的

- `test/AGENTS.md` を軽量な shared governance core とし、実行詳細を skill / script / reference へ分離する refresh 方針を整理する。
- 旧 refresh 版の `skill-invoker -> skill-planner` 主線を、`receipt-manager -> skill-invoker -> skill-planner -> response-manager` へ再編した時の役割境界を示す。

## 問題意識

- 旧構成では prompt 解釈、skill 選定、順序管理、応答整形が近接しており、責務境界がやや重なっていた。
- `AGENTS.md` に残す shared rule と、skill / proposal 文書へ逃がす実行 detail の境界がまだ曖昧だった。
- skill 群の実装在庫と、将来必要な manager 群の目標像が別文書に散っていた。

## 新しい主線

| 層 | owner | やること | やらないこと |
| --- | --- | --- | --- |
| 入口前段 | `receipt-manager` | prompt 全受領、要求解釈、暗黙要求推論、制約抽出 | skill 選定、実行、応答整形 |
| 統合入口 | `skill-invoker` | 必要 skill 集合、読込下限、defer / block 判定 | 実行順設計、応答整形、直接編集 |
| 順序管理 | `skill-planner` | 発火、順序、phase、handoff、close 条件 | skill 集合の再選定、事実改変 |
| 実処理 | manager / specialist skill | 個別処理 | 上位 routing の上書き |
| 出口後段 | `response-manager` | admin 向け応答整形 | 事実改変、未実施事項の実施済み化 |

## shared 文書に残すもの

- 全体構造
- 責務境界
- 強制順序
- directory rule
- 文書運用 rule
- gate / branch / safety / wording の shared rule

## skill / script / reference へ寄せるもの

- 起動判定 detail
- 読込対象の最小集合
- phase の具体 checklist
- 実行手順
- probe / test / evidence の実務 detail
- 具体例と matrix

## refresh target manager 群

| family | target skill |
| --- | --- |
| intake | `receipt-manager` |
| invoke | `skill-invoker` |
| orchestration | `skill-planner` |
| response | `response-manager` |
| governance | `governance-manager` |
| document | `document-control-manager` |
| writing | `writing-normalizer` |
| structure | `workspace-structure-manager` |
| registry | `project-registry-manager` |
| plan / gate | `plan-gate-manager` |
| implementation | `implementation-quality-manager` |
| worklog / runtime | `worklog-runtime-manager` |
| git | `git-hygiene-manager` |
| access / safety | `access-safety-manager` |
| collaboration | `collaboration-decision-manager` |
| research | `research-execution-manager` |
| windows ops | `windows-ops-manager` |
| evidence | `evidence-trace-manager` |

## 既存 skill の扱い

- 現行単一入口は `skill-invoker` へ名称統一し、責務は `receipt-manager` と `skill-invoker` へ分解する。
- 現行 `skill-planner` は維持し、実行順と phase 管理に専念させる。
- 既存 specialist skill は execution 層として存続し、manager 群の内部実装候補として再配置する。

## 導入順

1. `test/AGENTS.md` と `test/kisaragi-skills/agents.md` で新主線を固定する。
2. `test/kisaragi-skills/kisaragi_skill_trigger_system_map.md` で流れ図と ownership map を更新する。
3. `test/kisaragi-skills/kisaragi_pilot_skill_spec.md` で `receipt-manager`、`skill-invoker`、`response-manager` を含む pilot skill 群を定義する。
4. 既存 specialist skill を、新しい manager 群のどこへ吸収・委譲するかを段階的に再整理する。

## 結論

- `AGENTS.md` は憲法として軽量化する。
- prompt 解釈、skill 集合確定、順序管理、応答整形は別 layer に分ける。
- 現行 skill 在庫は捨てず、refresh target manager 群の execution 面として再利用する。
