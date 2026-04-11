# kisaragi context-skill governance proposal

## 文書の目的

- `kisaragi/` 内で機能開発する時の前提情報管理を再整理し、上位文書を軽く保ちながら、実務の再現性を `skill` と `script` 側で最大化するための叩き台を示す。
- 今回の主な問題意識は、`prj-kisaragi_0002` の `3DGS` / `Colab` 開発で、context window に入れるべき情報の境界が曖昧だったため、考慮漏れ、参照漏れ、後戻りが多発したことである。
- 本文は現状把握、問題構造、責務分離案、skill 案、残る文書案を 1 本に集約する。

## 今回の把握対象

### shared governance

- `AGENTS.md`
- `kisaragi-db/agents.md`
- `kisaragi-db/--devs/agents.md`

### project governance と運用文書

- `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/project-truth.md`
- `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/hi-ai-unified-blueprint.md`
- `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/sharedlogs_da3-colab.md`
- `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/agents.md`
- `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_runbook_design_contract.md`

### 既存 skill

- `kisaragi-skills/skill-distributor/`
- `kisaragi-skills/phase-task-orchestrator/`
- `kisaragi-skills/documentation-watchkeeper/`
- `kisaragi-skills/design-first-script-builder/`
- `kisaragi-skills/reference-rewire-operator/`
- `kisaragi-skills/external-compute-output-keeper/`
- `kisaragi-skills/delivery-planning-keeper/`

## 現状構造の要約

### 1. shared rule 層は既にかなり強い

- `AGENTS.md` は directory governance、文書の正本境界、`MRL` / `mRL`、shared worklog、branch rule、script 編集時の運用 rule まで広く持っている。
- 特に `skill-distributor`、`phase-task-orchestrator`、`design-first-script-builder`、`reference-rewire-operator` を開発 prompt の既定入口にしたい意図がすでに書かれている。
- つまり思想そのものは不足しておらず、実務で毎回その思想を機械的に踏ませる面がまだ弱い。

### 2. `prj-kisaragi_0002` は project 文書の層もかなり整っている

- `project-truth.md` は恒久事項を保持し、`TraceCore`、artifact 契約、remote modeling の外部境界を持っている。
- `hi-ai-unified-blueprint.md` は `current_state`、疑問点不整合、`BDD`、`TDD`、`MRL` 対応表まで持つ。
- `sharedlogs_da3-colab.md` は admin と Codex の往復を蓄積しており、どこで何が崩れたかの実務 log としては非常に強い。

### 3. `Colab` 運用は source 管理面までかなり進んでいる

- `colab/agents.md` が `.md` / `.ipynb` pair と canonical pair を規定している。
- `da3_ngl_runbook_design_contract.md` が `da3_increpose_sources/` を canonical source とする rule、chunk path 契約、`#10-1` / `#11-1` の stage contract まで詳細に持っている。
- すでに「実務を source-managed にする」方向は成立しつつある。

## 今回の問題の本質

### 問題 1. 上位文書に「何を残すか」は定義されているが、下位の実行面へどう落とすかが毎回会話依存になりやすい

- `AGENTS.md` には rule がある。
- `project-truth.md` と `HAUB` には project 判断がある。
- しかし実際の task 着手時に「今回はどの文書だけ見ればよいか」「どの skill を起動し、何を入力し、何を検証するか」が一段抽象のまま残る。
- この隙間があるため、Codex は会話ごとに再解釈し、context window の使い方がぶれやすい。

### 問題 2. 判断根拠と作業手順が同じ文脈で混ざりやすい

- たとえば `HAUB` には判断理由と handoff 契約の両方がある。
- `design contract` には source 構造、path 契約、artifact 契約、運用 rule がまとめて入っている。
- これは人が読むには強いが、Codex に毎回読ませる単位としては大きく、必要部分だけ切り出しにくい。

### 問題 3. shared worklog は豊富だが、再利用しやすい task protocol へ十分に還元されていない

- `sharedlogs_da3-colab.md` には再発防止の材料が多い。
- 一方で、そこから「次回も同じ失敗を防ぐための定型プロンプト」「必須チェック順」「失敗時の自己修復順」として独立した skill / script へ昇格したものはまだ限定的である。
- そのため、同じ種類の task でも会話が変わると再び取りこぼしが起きる。

### 問題 4. 上位文書が軽量化されるほど、逆に「どの下位 contract を見ればよいか」を示す目次 skill が必要になる

- 上位文書を軽くする方向は正しい。
- ただし軽くするほど、実務では `router` と `guard` が必要になる。
- つまり、文書削減だけでは不十分で、「軽量な正本」と「重い実行 protocol を必ず引く skill」が同時に必要である。

## 提案する大枠

### 基本方針

- 人の意思、価値判断、gate、不可逆判断、project の恒久真実は上位文書へ残す。
- Codex に毎回同じ動きをさせたい実務 protocol は、可能な限り `skill` と `script` に落とす。
- worklog は trial 記録のままでは終わらせず、再発防止価値が確認できた段階で `skill` / `script` / `design contract` のいずれかへ昇格させる。

### 上位文書へ残すべきもの

- shared governance
- project の目的
- project 固有の不可逆判断
- gate の定義
- 採用中の canonical route
- admin が確認したい判断点
- 「なぜその route を採用するのか」の要約

### skill / script へ寄せるべきもの

- task 着手時の読むべき文書の列挙
- 変更対象ごとの必須 checklist
- script / notebook / runbook 編集時の phase 進行
- path / contract / artifact の read-write-handoff 検査
- external compute の clean bootstrap と保存順
- `sharedlog` から product 文書への昇格判定
- docs 更新漏れ検査

## 役割分離の提案

### 1. `AGENTS.md`

#### 残すもの

- shared governance のみ
- 文書階層 rule
- shared branch rule
- `MRL` / `mRL` / `INITL` の定義
- shared worklog の rule
- skill 起動 rule の原則

#### 減らしたいもの

- project 実務に踏み込む具体例の増殖
- `Colab` や notebook の詳細運用
- 特定 project の handoff 契約そのもの

#### 目指す状態

- `AGENTS.md` は「何が shared rule か」だけを保持する軽量な憲法に近づける。
- 具体運用は「どの skill を必ず起動するか」の rule までに留める。

### 2. `project-truth.md`

#### 残すもの

- project の最終目的
- 最小価値
- app 境界
- artifact 契約の恒久部分
- 外部境界
- 長期に保つべき canonical route

#### 減らしたいもの

- 日々変わる手順順序
- task 単位の detailed checklist
- 一時的な bootstrap の細部

#### 目指す状態

- 「何を作るか」と「何を不変条件として守るか」に集中させる。

### 3. `hi-ai-unified-blueprint.md`

#### 残すもの

- `current_state`
- 疑問点不整合一覧
- `BDD`
- `TDD`
- `MRL` / `mRL` 対応
- support-MRL
- 直近の採用 route と未解決の大論点

#### 減らしたいもの

- 実行手順そのもの
- notebook cell レベルの詳細
- source 管理の細部

#### 目指す状態

- 「今どこまで決まっていて、何が未解決か」を管理する project plan 正本に徹する。

### 4. design contract 系文書

#### 残すもの

- source 構造
- 主要 artifact 契約
- handoff 契約
- generator / sync utility / test の対応

#### 位置づけ

- `truth` や `HAUB` ではなく、実務 protocol の管理文書とする。
- skill や script が参照する設計契約の詳細面として使う。

### 5. shared worklog

#### 残すもの

- admin と Codex の時系列往復
- error 原文
- 試行経路
- 「何を正本へ反映済みか」の記録

#### 原則

- ここを再利用面にしない。
- 再発防止価値があるものは `skill`、`script`、`design contract`、`HAUB` へ昇格させる。

## 今回の方向に合わせた skill 構成案

以下は、今の `kisaragi` に追加または強化すると効果が大きいものを列挙する。

### A. 開発前提情報の収集と文脈固定

#### 1. `authoritative-doc-loader`

- 目的: 対象 path と task 種別から、読むべき `AGENTS.md`、`agents.md`、`project-truth.md`、`HAUB`、design contract、inventory を機械的に列挙する。
- 入力: 対象 file / directory、task 種別、project code
- 出力: `must_read_before`、`must_not_treat_as_truth`、`likely_update_targets`
- 効果: 毎回どの文書を context window に入れるかで迷わなくなる。

#### 2. `task-context-packager`

- 目的: 今回の task に必要な文書断片だけを抽出し、Codex が最初に読むべき compact context pack を作る。
- 入力: task 種別、変更対象、現在 gate
- 出力: `briefing.md` 相当の一時 pack
- 効果: 大きな `HAUB` や `sharedlog` を丸ごと読ませず、必要部分だけ固定できる。

#### 3. `decision-focus-clarifier`

- 目的: 今回の task で、人が判断したい点と Codex に委任する点を明示的に分ける。
- 入力: task、候補論点
- 出力: `human_checkpoints`、`delegated_judgements`
- 効果: 「どこまで自動で進めてよいか」のぶれを減らす。

### B. script / notebook / runbook 編集の定型化

#### 4. `script-change-guard`

- 目的: script / notebook / runbook 編集時に、必須の設計確認と関連文書確認を強制する。
- 主処理:
  - authoritative docs 読込
  - 関連 inventory の確認
  - source-sync 対象の確認
  - contract probe / unittest の実行候補提示
- 効果: 「まず直す」が起きにくくなる。

#### 5. `runbook-pair-sync-keeper`

- 目的: `.md` と `.ipynb` の pair 管理を徹底し、片側だけの更新を禁止する。
- 主処理:
  - source file 更新検知
  - pair 再生成
  - inventory 再生成
  - 差分 check
- 効果: notebook 系でのドリフトを機械的に抑える。

#### 6. `handoff-contract-enforcer`

- 目的: path、artifact、producer / consumer の handoff を `HAUB` と probe で強制整合する。
- 主処理:
  - handoff matrix の row 差分検知
  - source 側 write/read path 抽出
  - probe 実行
  - 不足 row の補完提案
- 効果: 今回の `Colab` のような path ずれ再発を抑える。

### C. external compute の再現性向上

#### 7. `external-runtime-bootstrap-keeper`

- 目的: `Colab`、remote notebook、remote GPU job で、fresh runtime 前提の最短 clean bootstrap を維持する。
- 主処理:
  - mount
  - input 解決
  - repo bootstrap
  - dependency install
  - quick smoke
  - persistent storage 先行保存
- 効果: context 依存の trial-and-error を減らせる。

#### 8. `persistent-output-first-guard`

- 目的: download や local zip より前に Drive などの永続保存先へ final output を固定する。
- 主処理:
  - output tree 初期化
  - manifest 生成
  - final output 必須 file の存在確認
  - cleanup 対象の列挙
- 効果: runtime 消失で成果物が蒸発しにくくなる。

#### 9. `runtime-self-heal-checklist`

- 目的: `Colab` 実行中のよくある欠落を self-heal 順序で案内する。
- 主処理:
  - input 未展開
  - stale notebook
  - missing manifest
  - compatibility alias
  - old path fallback
- 効果: sharedlog にしかない回復知識を定型化できる。

### D. 文書同期と決定履歴の整理

#### 10. `decision-log-promoter`

- 目的: 会話や sharedlog に出た持続価値のある判断を、`AGENTS.md` か `truth` / `HAUB` のどこへ昇格すべきか分類する。
- 出力:
  - shared governance
  - project truth
  - current_state
  - design contract
  - worklog only
- 効果: chat にだけ重要判断が残る状態を減らせる。

#### 11. `doc-slimming-reviewer`

- 目的: 上位文書が重くなった時に、何を skill / contract へ移すべきかを点検する。
- 観点:
  - 恒久事項か
  - project 固有か
  - task protocol か
  - script 実装詳細か
- 効果: 正本文書の肥大化を抑える。

#### 12. `sharedlog-to-product-promoter`

- 目的: shared worklog の成果を product 文書、skill、script、contract に昇格する。
- 効果: 過去の trial が再利用可能な資産になる。

## skill 化したい対象を grouped で見る

### group 1. 毎 task 必須の入口 skill

- `skill-distributor`
- `phase-task-orchestrator`
- `authoritative-doc-loader`
- `task-context-packager`

### group 2. script / notebook / runbook 編集時の必須 skill

- `script-change-guard`
- `design-first-script-builder`
- `reference-rewire-operator`
- `runbook-pair-sync-keeper`
- `handoff-contract-enforcer`

### group 3. external compute 系 task の必須 skill

- `external-runtime-bootstrap-keeper`
- `external-compute-output-keeper`
- `persistent-output-first-guard`
- `runtime-self-heal-checklist`

### group 4. 文書同期と軽量化の skill

- `documentation-watchkeeper`
- `decision-log-promoter`
- `doc-slimming-reviewer`
- `sharedlog-to-product-promoter`

## それでも残る文書と、その役割

skill を増やしても、文書は消えない。むしろ、何を文書へ残すかを明確にしてはじめて skill の価値が出る。

### 1. `AGENTS.md`

- shared rule の正本
- Codex と admin の協調原則
- 文書境界
- branch / hygiene / gate の共通 rule

### 2. 各階層 `agents.md`

- directory 単位の local rule
- 配下全体に効く path / artifact / storage rule
- project をまたがるほどではないが、その階層では恒久な rule

### 3. `project-truth.md`

- project 固有の恒久 truth
- project の価値、境界、app 構造、artifact 境界
- 「何を作るか」と「何を不変条件として守るか」

### 4. `hi-ai-unified-blueprint.md`

- project の現在地
- 未解決論点
- `BDD`
- `TDD`
- gate 対応
- 直近の採用 route と残件

### 5. `admin-mrl-test-method.md`

- admin が実際に操作する手順の正本
- UX check の再現 route
- 人が確認する batch 手順

### 6. `admin-mrl-test-evidence.md`

- admin 実測の正本
- `i-pass` の根拠
- UX check の結果記録

### 7. `codex-mrl-test-evidence.md`

- Codex 側 closeout の記録
- issue、cause、resolution、再発防止
- task 完了時の close 条件の記録

### 8. design contract 文書

- 実務 protocol の詳細
- source 面、handoff 面、artifact 面、sync 面
- skill が参照する詳細契約

### 9. inventory 文書

- source file 群の一覧
- 参照面の棚卸し
- 「どの file が何を担うか」の可視化

### 10. shared worklog

- trial の共同作業 log
- 生ログ保持
- 正本昇格前の観測事実

## 推奨する文書 topology

### 上位文書

- `AGENTS.md`
- 各階層 `agents.md`
- `project-truth.md`
- `hi-ai-unified-blueprint.md`
- `admin-mrl-test-method.md`
- `admin-mrl-test-evidence.md`
- `codex-mrl-test-evidence.md`

### 中位の管理文書

- design contract
- inventory
- runbook source inventory
- handoff matrix

### 下位の実行資産

- `skill`
- `script`
- `.md/.ipynb` pair
- unittest / probe

### 補助 log

- shared worklog
- test summary
- raw evidence summary

## 実務上の運用イメージ

### 開発開始時

1. `skill-distributor` が最小 skill 群を選ぶ
2. `phase-task-orchestrator` が phase と close 条件を固定する
3. `authoritative-doc-loader` が読むべき正本を列挙する
4. `task-context-packager` が今回の compact context を作る

### script / notebook 編集時

1. `script-change-guard` が design contract、inventory、関連正本を確認する
2. `design-first-script-builder` が変更設計を整理する
3. `reference-rewire-operator` が path / contract / output の切替を扱う
4. `runbook-pair-sync-keeper` が pair 再生成と inventory 更新を行う
5. `handoff-contract-enforcer` が `HAUB` と probe / unittest を確認する

### task close 時

1. `documentation-watchkeeper` が正本更新要否を判定する
2. `decision-log-promoter` が持続価値のある判断を昇格させる
3. `sharedlog-to-product-promoter` が sharedlog から再利用資産を抽出する
4. `codex-mrl-test-evidence.md` へ closeout を残す

## 導入順の提案

大改修は一度にやると崩れやすいため、次の順がよい。

### Step 1. skill 群の責務表を先に作る

- 既存 skill と新設 skill 候補を 1 表にまとめる。
- 各 skill に対して、入力、出力、参照文書、更新対象文書、必須 test を定義する。

### Step 2. `AGENTS.md` を軽量化する前に router skill を強化する

- 先に `authoritative-doc-loader` と `task-context-packager` を作る。
- これが無いまま `AGENTS.md` を削ると、実務の文脈固定が逆に弱くなる。

### Step 3. `prj-kisaragi_0002` を pilot project にする

- すでに `Colab`、design contract、inventory、probe があるため、最も skill 化しやすい。
- まず `Colab` 系の定型失敗を skill / script 化する。

### Step 4. sharedlog から再発知識を吸い上げる

- `sharedlogs_da3-colab.md` を題材に、self-heal checklist と bootstrap guard を切り出す。
- これが終わってから上位文書をさらに軽くする。

## 提案の要点

- 今足りないのは文書そのものより、「上位文書の判断を、毎 task の実行 protocol へ自動的に落とす skill 層」である。
- `AGENTS.md`、`truth`、`HAUB` は軽くしてよいが、その代わりに `authoritative-doc-loader`、`task-context-packager`、`script-change-guard`、`handoff-contract-enforcer` のような入口と guard が必要になる。
- `sharedlog` の豊富な失敗知識を再利用可能にするには、worklog を読む skill ではなく、worklog から protocol を昇格する skill が必要である。
- `prj-kisaragi_0002` はすでに source-managed 運用があるため、この方針を試す pilot として最適である。

## 次にやるとよい具体 task

1. `kisaragi-skills/` 配下に置く新設 skill 候補の責務表を別紙で作る
2. `authoritative-doc-loader` と `task-context-packager` の 2 skill を先行設計する
3. `prj-kisaragi_0002` 向けに `script-change-guard` と `handoff-contract-enforcer` の trial 版を作る
4. `sharedlogs_da3-colab.md` から recurring failure pattern を 10 件程度抽出し、self-heal checklist 化する
