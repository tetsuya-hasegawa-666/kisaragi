# AGENTS.md 更新履歴

## 目的

- この文書は `AGENTS.md` の更新履歴正本とする。

## 記録規則

- `AGENTS.md` を更新したら、この文書へ履歴を追加する。
- 更新履歴は新しい日付を上に置く。
- 各履歴は日時、文書名、標題、背景、目的、対処方法、対応内容、更新結果、新旧比較を持つ。

## 更新履歴

### 2026-03-29 AGENTS.md shared worklog の `--tgpce-map` 移管と命名統一

- 日時: `2026-03-29`
- 文書名: `AGENTS.md`
- 標題: collaborative log を `--tgpce-map` 直下へ移し `shared_worklog-<project-code>-<thema>.md` に統一
- 背景: notebook / script / error の往復 log は raw 生成物ではなく、人と AI の共同作業で参照し続ける可読性重視の保持情報であるため、`--exsams/` より `--tgpce-map/` の方が実態に合っていた。
- 目的: collaborative log の置き場、役割、命名規則を shared rule として固定し、project ごとに同じ読み方と参照方法で運用できるようにする。
- 対処方法: `--devs/` と `--exsams/` の説明、および協調原則と文書規則を更新し、shared worklog を `--tgpce-map/prj-kisaragi_****/shared_worklog-<project-code>-<thema>.md` として扱う rule を追加した。
- 対応内容: shared worklog は truth / plan / evidence の正本ではないが、共同作業の保持情報としては authoritative な log であり、正本反映の根拠 log として保持することを明記した。
- 更新結果: 長い code 往復や admin 実行結果は `--tgpce-map` 側の shared worklog に集約し、`--exsams/` は raw 生成物専用として整理された。
- 新旧比較:
  - 旧: collaborative log は `--exsams/` 配下の一時共有 log として扱っていた。
  - 新: collaborative log は `--tgpce-map/` 直下の `shared_worklog-<project-code>-<thema>.md` に統一し、保持情報としての authoritative log として扱う。

### 2026-03-29 AGENTS.md 長い code 往復の一時共有 log 既定化

- 日時: `2026-03-29`
- 文書名: `AGENTS.md`
- 標題: notebook / script / error 往復時の一時共有 log を shared rule 化
- 背景: `Colab` のように長い cell、error 全文、admin 実行結果を何度も往復する task では、chat へ直接 code を積み続けると誤送信や文脈取り違えが起きやすく、main code thread の参照元が揺れやすかった。
- 目的: 長い code 往復の canonical な面を `--exsams/` 配下の一時共有 log へ固定し、chat は要点整理と次 action の案内に集中させる。
- 対処方法: `協調原則` と `文書規則` に、一時共有 log を main code / raw response の既定面とする rule、回答前に最新追記を確認する rule、log 自体は正本や証跡の代替にしない rule を追記した。
- 対応内容: notebook cell、長い script、error 全文、admin 実行結果の往復を伴う task では、一時共有 log を基準に進めること、chat ではどの log を基準に答えるかを明示すること、log は header 付き追記専用を既定にすることを追加した。
- 更新結果: 今後は長い code 往復で context window だけに依存せず、`--exsams/` の一時共有 log を canonical な往復面として扱い、shared / project / evidence への反映漏れも抑えやすくなる。
- 新旧比較:
  - 旧: chat と一時 log の使い分けは project ごとの運用に依存し、shared rule としては弱かった。
  - 新: 長い code 往復では一時共有 log を既定面とし、chat は要点整理と次 action を返す補助面として扱う shared rule が追加された。

### 2026-03-29 AGENTS.md 一時共有 log の最下部追記固定

- 日時: `2026-03-29`
- 文書名: `AGENTS.md`
- 標題: shared log 本文の途中挿入禁止と最下部読み順固定
- 背景: shared log に本文途中の要約や説明が混じると、admin がどこから読めばよいか分かりにくく、時系列の追跡も難しくなる問題が出た。
- 目的: 一時共有 log の固定 header と時系列本文を明確に分け、header より下は最下部追記だけで運用する。
- 対処方法: `文書規則` に、一時共有 log は固定 header の下を `# codex` / `# admin` 見出しによる末尾追記だけに限定する rule と、正規読み順を「最下部から上へ」とする rule を追加した。
- 対応内容: 途中挿入、途中修正、本文中ほどへの要約追記を禁止し、Codex は回答前に最下部の最新追記を確認することを shared rule 化した。
- 更新結果: shared log は「上が固定説明、下が時系列本文」という読み方に統一され、admin と Codex がどこを見るべきか迷いにくくなった。
- 新旧比較:
  - 旧: header の下にも途中要約や説明を差し込む余地があり、読み順が揺れやすかった。
  - 新: header より下は最下部追記だけに固定し、正規読み順も最下部起点に統一した。

### 2026-03-28 AGENTS.md gate 状態語の再定義

- 日時: `2026-03-28`
- 文書名: `AGENTS.md`
- 標題: `ready`、`active`、`p-done`、`i-pass` への移行
- 背景: UX 評価と gate closeout で、`planned`、`pass`、`done` が phase 完了と統合完了を十分に区別できず、現時点評価をどう書くかも揺れていた。
- 目的: gate 状態語と UX 評価状態を同じ 4 値で統一し、phase 完了と統合完了を分けて追跡できるようにする。
- 対処方法: 開発計画節と統合計画書 rule を更新し、正本状態語を `ready`、`active`、`p-done`、`i-pass` へ置き換えた。
- 対応内容: `aspass` は会話や補足メモ用の補助語とし、正本文書では `p-done` または `i-pass` へ正規化する rule を追加した。
- 更新結果: 今後は phase 単位の成立確認を `p-done`、統合範囲までの成立確認を `i-pass` として一貫して管理する。
- 新旧比較:
  - 旧: `planned`、`active`、`pass`、`need`、`done` が文脈により混在していた。
  - 新: gate と UX 評価を `ready`、`active`、`p-done`、`i-pass` に統一し、`aspass` は補助語へ限定した。

### 2026-03-28 AGENTS.md 旧 category directory の全廃

- 日時: `2026-03-28`
- 文書名: `AGENTS.md`
- 標題: `--plans`、`--evidence`、`--project-truth`、`--state` の削除
- 背景: `prj-kisaragi_0001`、`prj-kisaragi_0002`、`prj-kisaragi_0003` の正本文書が `--tgpce-map/` にそろい、旧 category directory は空になった。
- 目的: 実体を持たない旧 category を削除し、`--devs` 構造を現行正本に合わせて簡潔化する。
- 対処方法: `AGENTS.md` と `--devs/agents.md` の構造説明から旧 category を外し、旧 category は吸収完了後に削除する rule へ更新した。
- 対応内容: `--plans/`、`--evidence/`、`--project-truth/`、`--state/` の directory 実体を削除した。
- 更新結果: `--devs/` は `--tgpce-map/`、`--products/`、`--testcode/`、`--testlogs/` の現行構成だけを持つ。
- 新旧比較:
  - 旧: `--plans`、`--evidence`、`--project-truth`、`--state` の空 directory が残っていた。
  - 新: 旧 category は削除し、正本構造は `--tgpce-map` 中心に整理された。

### 2026-03-28 AGENTS.md `0001` と `0003` の新文書ルール展開

- 日時: `2026-03-28`
- 文書名: `AGENTS.md`
- 標題: `--tgpce-map` 正式構成の他 project 展開
- 背景: `prj-kisaragi_0002` で先行していた `--tgpce-map` と新文書名の運用を、`prj-kisaragi_0001` と `prj-kisaragi_0003` にも適用する必要が生じた。
- 目的: `prj-kisaragi_0001`、`prj-kisaragi_0002`、`prj-kisaragi_0003` が同じ正本構造と file 名で運用できるようにし、以後の project 展開時に rule の差分を減らす。
- 対処方法: `AGENTS.md` の shared rule を `kisaragi_****` 共通の表現へ保ちつつ、admin 手順正本の記載も `--tgpce-map` 採用 project 基準へそろえた。
- 対応内容: admin 手順の共有記述を `admin-mrl-test-method.md` 基準へ更新し、`0001` / `0003` 側の移行に追従できる shared rule に整えた。
- 更新結果: `0001`、`0002`、`0003` は同じ `--tgpce-map` 正式構成で読める前提になり、個別 project ごとの差は project 文書側で管理できる。
- 新旧比較:
  - 旧: admin 手順の shared 記述が旧 `ux_check_manual.md` path 前提のままだった。
  - 新: `--tgpce-map` 採用 project では `admin-mrl-test-method.md` を正本に使う前提で統一した。

### 2026-03-28 AGENTS.md `--tgpce-map` 運用の `kisaragi_****` 一般化

- 日時: `2026-03-28`
- 文書名: `AGENTS.md`
- 標題: `0002` 固有運用の shared rule 化
- 背景: `prj-kisaragi_0002` で固めた `--tgpce-map`、統合計画書、admin 手順 / 証跡、Codex closeout の運用を、他 project にも同じ format で展開する前提が生まれた。
- 目的: `AGENTS.md` に残る `0002` 固有の開発運用表現を `prj-kisaragi_****` 共通 rule へ置き換え、shared rule と project 固有事項の境界を明確にする。
- 対処方法: `AGENTS.md` と `--devs/agents.md` の `0002` 固有表現を、`--tgpce-map/` 採用 project 共通の file 名と運用 rule に一般化した。
- 対応内容: `ux-b2t-hypo.md`、`codex-mrl-test-evidence.md`、`admin-mrl-test-method.md`、`admin-mrl-test-evidence.md` を `prj-kisaragi_****` 共通の正式名称として定義し、旧 `0002` 固有運用文言を shared rule から外した。
- 更新結果: `AGENTS.md` は project code 対応表を除き、`0002` 固有運用に依存せず、今後の `--tgpce-map` 展開にそのまま使える状態になった。
- 新旧比較:
  - 旧: `0002` 固有の file 名と運用が shared rule に混在していた。
  - 新: `--tgpce-map/` 採用 `prj-kisaragi_****` 共通の rule と file 名に一般化し、固有運用は project 文書へ戻した。

### 2026-03-28 AGENTS.md 一時調査出力の `--exsams` 集約

- 日時: `2026-03-28`
- 文書名: `AGENTS.md`
- 標題: `uidump` など一時調査出力の配置固定
- 背景: 実機 UI 調査で生成した `uidump*.xml` が workspace root に残り、raw 生成物の置き場が `--exsams/` に統一されていなかった。
- 目的: `device dump`、画面構造 dump、実機調査 XML などの一時出力を `--exsams/` 配下へ集約し、workspace root や他 category への散在を防ぐ。
- 対処方法: `AGENTS.md` の `--exsams/` rule へ、一時調査出力も `--exsams/` 配下だけに置くこと、外に出た場合は即時移動または削除することを追記した。
- 対応内容: `uidump*.xml` を削除し、同種出力の配置 rule を shared 化した。
- 更新結果: 今後は `uidump`、screen capture、tmp などの正本でない一時出力は `--exsams/` 配下だけで管理する。
- 新旧比較:
  - 旧: raw 生成物は `--exsams/` 想定だったが、一時調査出力の配置先が明文化されていなかった。
  - 新: 一時調査出力も `--exsams/` 配下へ固定し、外に出た場合の即時是正を rule 化した。

### 2026-03-28 AGENTS.md shared state file 廃止

- 日時: `2026-03-28`
- 文書名: `AGENTS.md`
- 標題: shared `current_state.md` と `decision_log.md` の廃止
- 背景: shared current / decision 専用 file を残すと、`AGENTS.md` と project 正本文書の間にもう 1 層の管理点が生まれ、`0002` の `b2t` 統合方針とも衝突していた。
- 目的: shared governance は `AGENTS.md` と `agents.md`、project 固有 current / decision は各 project の正本文書へ寄せ、shared state file を廃止する。
- 対処方法: `AGENTS.md` の shared state file 参照を削除し、承認、current、decision の記録先を `AGENTS.md` / `AGENTSmd-RH.md` と project 正本文書へ振り分ける rule に変更した。
- 対応内容: `AGENTS.md`、`README.md`、`--devs/agents.md`、`--state/agents.md` を更新し、shared `current_state.md` と `decision_log.md` を削除した。
- 更新結果: shared state の正本は `AGENTS.md` 系へ一本化され、project current / decision は project 側正本だけで追える構造になった。
- 新旧比較:
  - 旧: shared `current_state.md` と `decision_log.md` が存在し、shared governance の一部が別 file に分かれていた。
  - 新: shared governance は `AGENTS.md` と `agents.md` に統合し、project current / decision は project 正本文書へ集約した。

### 2026-03-28 AGENTS.md `--tgpce-map` pilot と shared / project current 境界整理

- 日時: `2026-03-28`
- 文書名: `AGENTS.md`
- 標題: `--tgpce-map` の pilot 運用と project current / decision の分離
- 背景: `prj-kisaragi_0002` で truth、plan、evidence、current が category ごとに分散し、再開時の把握と shared state との境界が読みにくくなっていた。
- 目的: `prj-kisaragi_0002` を先行対象として `--tgpce-map` へ正本文書を集約し、project 固有 current / decision を `b2t-plans-result.md` 中心へ戻す。
- 対処方法: `--devs/` 構造説明へ `--tgpce-map` pilot を追加し、適用対象を `prj-kisaragi_0002` に限定する rule、project current / decision を `b2t-plans-result.md` へ集約する rule を追記した。
- 対応内容: `--devs/` の構造説明、`AGENTS.md` と project 文書の境界、開発計画の path 記述を更新し、`--tgpce-map` 適用済み project の扱いを shared rule 化した。
- 更新結果: `prj-kisaragi_0002` は `--tgpce-map` 配下へ正本文書を移しやすくなり、shared `current_state.md` / `decision_log.md` へ project 固有記録を残し続ける必要がなくなった。
- 新旧比較:
  - 旧: `--plans`、`--evidence`、`--project-truth`、`--state` の category 分散が `prj-kisaragi_0002` にもそのまま残り、shared state に project 固有 current / decision が混在していた。
  - 新: `prj-kisaragi_0002` は `--tgpce-map` pilot で集約し、project current / decision は `b2t-plans-result.md` と project truth 側へ戻す方針を shared rule 化した。

### 2026-03-28 AGENTS.md project-truth と b2t の文書境界固定

- 日時: `2026-03-28`
- 文書名: `AGENTS.md`
- 標題: `project-truth.md`、`b2t-plans-result.md`、evidence 文書の役割境界固定
- 背景: `prj-kisaragi_0002` の整理で、`project-truth.md` に現在状態や UX の進行中情報が混在し、`b2t-plans-result.md` と役割が重なって読みにくくなっていた。
- 目的: shared rule として、`truth`、`b2t`、`ux_check_manual`、`mrl-ux-valid` の責務を明確に分け、同じ情報の二重管理を防ぐ。
- 対処方法: `文書規則` に `文書の役割境界` 節を追加し、各文書に書くべき内容と書かない内容を明文化した。
- 対応内容: `project-truth.md` は恒久事項のみ、`b2t-plans-result.md` は current state と gate 管理、`ux_check_manual.md` は操作手順、`mrl-ux-valid.md` は UX 証跡と close 根拠を持つ rule を追加した。
- 更新結果: 今後は `project-truth.md` から現在状態を除去しやすくなり、project 文書の境界を shared rule で再利用できる。
- 新旧比較:
  - 旧: 文書境界は project 内の局所判断に近く、shared rule としては固定されていなかった。
  - 新: `truth`、`b2t`、evidence 文書の責務を `AGENTS.md` で共有 rule 化した。

### 2026-03-28 AGENTS.md 表現圧縮と可読性調整

- 日時: `2026-03-28`
- 文書名: `AGENTS.md`
- 標題: 全体方針に合わせた表現圧縮
- 背景: `AGENTS.md` は rule 自体は有効だったが、同じ意味をより短く明確に書ける箇所が増え、`人が読みやすく、文字数当たりの情報量が最大` という文書方針に対して表現密度が不均一になっていた。
- 目的: rule の意味、優先関係、拘束力を変えずに、冗長な言い回しや読点の重さを減らし、全体を読み切りやすくする。
- 対処方法: 構造と rule は維持したまま、冗長表現、重複語、回りくどい助詞回しを圧縮し、文単位で可読性を揃えた。
- 対応内容: `AGENTS.md` 全体で、日本語の簡潔化、同義反復の圧縮、用語回しの統一、説明の短文化を行った。共有制御ファイル編集に伴い `current_state.md` に所有権記録も追加した。
- 更新結果: `AGENTS.md` は rule の意味を維持したまま、短く読みやすい文が増え、全体方針との整合が改善した。
- 新旧比較:
  - 旧: 意味は通るが、回りくどい表現や密度のばらつきが残っていた。
  - 新: 構造と rule を保ったまま表現を圧縮し、可読性と情報密度を揃えた。

### 2026-03-28 AGENTS.md shared / project 境界と `INITL` 導入

- 日時: `2026-03-28`
- 文書名: `AGENTS.md`
- 標題: shared rule と project 固有 truth の分離、および `INITL` / `mINITL` 追加
- 背景: `prj-kisaragi_0002` で `Colab all-in modeling`、package 化、install 導線のような準備 UX を計画へ入れる必要が生じた一方、`AGENTS.md` と project 文書の境界が曖昧なままだと、project 固有事項が shared rule へ混入しやすかった。
- 目的: `AGENTS.md` には project 横断 rule だけを残し、project 固有 UX / route / package 設計は project 文書へ分離すること、そして機能 behavior と準備 UX を `MRL` と `INITL` で分けて追跡できるようにする。
- 対処方法: `AGENTS.md` に `AGENTS.md と project 文書の境界` 節を追加し、`開発計画` と plan 文書標準へ `INITL` / `mINITL` rule を追記した。あわせて `prj-kisaragi_0002` 参照を shared rule の例示から外した。
- 対応内容: shared / project の責務分離、`INITL` の用途、`mrl-ux-valid.md` への証跡集約、`b2t-plans-result.md` での `INITL` 対応表必須化を明文化した。
- 更新結果: 今後は package、install、bootstrap、account 準備のような準備 UX を `INITL` として project ごとに管理でき、`AGENTS.md` へ project 固有事項を固定しにくくなった。
- 新旧比較:
  - 旧: `AGENTS.md` と project 文書の境界が暗黙で、特定 project を参照型にした rule も残っていた。準備 UX を `MRL` とどう分けるかも未定義だった。
  - 新: `AGENTS.md` は shared rule のみ、project 固有 truth は project 文書へ分離し、準備 UX は `INITL` / `mINITL` で別管理する。

### 2026-03-28 AGENTS.md 疑問点不整合一覧と `big-open` 明示 rule の追加

- 日時: `2026-03-28`
- 文書名: `AGENTS.md`
- 標題: `current_state` 冒頭 table と `big-open` response 明示
- 背景: `prj-kisaragi_0002` の `InputPackaging` と `correcting` の truth 追従を整理する中で、残問題の置き場が散在し、admin が一時引き取る検討項目を 1 箇所で読める必要が生じた。
- 目的: project ごとの残問題を `b2t-plans-result.md` の `current_state` 冒頭 table に集約し、影響が大きい未解決項目 `big-open` を response 上でも見落とさない運用を固定する。
- 対処方法: `開発計画` と `文書規則` に、`疑問点不整合一覧` table の必須化、`admin 状態` の 4 値、`big-open` がある時の response 明示 rule を追記した。
- 対応内容: `current_state` 冒頭 table の列要件と status 値を定義し、文書更新 response に `big-open` 明示を要求した。
- 更新結果: 今後は project 単位の open issue を 1 箇所で追え、影響が大きい未解決を response でも見逃しにくくなる。
- 新旧比較:
  - 旧: open issue は複数 section や chat に散りやすく、影響度も response で明示されないことがあった。
  - 新: `疑問点不整合一覧` を `current_state` 冒頭へ集約し、`big-open` は response でも必ず明示する。

### 2026-03-28 AGENTS.md 文書更新取りこぼしの再発防止

- 日時: `2026-03-28`
- 文書名: `AGENTS.md`
- 標題: 文書更新 task の未完了取りこぼし防止
- 背景: `prj-kisaragi_0002` の UI / UX 調整中に、文書更新が並行 task である前提を維持できず、理由説明のない入力待ちへ移ったため、正本整合の遅延と認識ずれが生じた。
- 目的: 複数指示を含む prompt と文書更新 task を処理する時、未完了指示を取りこぼさず、最低限の正本整合を閉じるまで入力待ちへ移らない shared rule を固定する。
- 対処方法: `協調原則` と `並行作業` に、未完了指示の保持、影響文書群の先行洗い出し、未更新理由の commentary 明示を追記した。
- 対応内容: 文書更新が必要な task では、正本文書群を最初に洗い出し、同じ task 内で最低限の整合更新を完了させること、未更新を残す時は理由と残件を commentary で説明することを明文化した。
- 更新結果: 今後は prompt 由来の文書更新要求を chat だけに残さず、取りこぼしや無説明の入力待ちを shared rule で防止できる。
- 新旧比較:
  - 旧: 文書更新は同 task 完了 rule があったが、複数指示 prompt の残件保持と、未更新理由の説明義務が明文化されていなかった。
  - 新: 未完了指示の保持、影響文書群の先行洗い出し、未更新理由の commentary 明示を shared rule として追加した。

### 2026-03-26 AGENTS.md warning と blocker の役割分離

- 日時: `2026-03-26`
- 文書名: `AGENTS.md`
- 標題: `warning` による後続停止の禁止
- 背景: `prj-kisaragi_0002` で data-check の警告表示自体は有益だった一方、警告があるだけで後続の `3DGS` 前段処理へ進めない構成が生じ、機能不全の再発防止が必要になった。
- 目的: `warning` を user への注意喚起情報として扱い、実行不能条件である `blocker` と混同して後続処理を止めない shared rule を固定する。
- 対処方法: `実装原則` に、`warning` の存在だけでは後続処理や継続操作を停止してはならないこと、停止してよいのは実行不能条件だけであることを追記した。
- 対応内容: `warning` は情報提示、`blocker` は実行不能条件という責務分離を明文化し、両者の混同を禁止した。
- 更新結果: 今後は警告を UX として表示しても、実行可能な後続処理は継続できる設計を shared rule として要求できる。
- 新旧比較:
  - 旧: 警告表示と実行停止条件の境界が shared rule として十分に固定されていなかった。
  - 新: `warning` では止めず、実行不能な `blocker` の時だけ止める rule を shared 化した。

### 2026-03-26 AGENTS.md mock 完了誤認の再発防止

- 日時: `2026-03-26`
- 文書名: `AGENTS.md`
- 標題: `UX-only` と本機能 `pass` の分離
- 背景: `prj-kisaragi_0002` で build、install、UX 確認、local sample 実装を本来機能の完成と近い意味で扱い、app の完成度を過大評価した。
- 目的: mock、stub、sample、説明用 UI の確認を、本機能 `MRL` / `mRL` の `pass` と取り違えない shared rule を固定する。
- 対処方法: `実装原則` に `UX 確認済み`、`contract 固定済み`、`build / install 済み`、`local sample 済み` を本機能完成と同義にしない rule を追加した。
- 対応内容: 本機能 gate の `pass` には、対象 app 自身で本来の入出力を扱い、後段が消費する実生成物を出し、主要 blocker が解消済みであることを要件化した。
- 更新結果: 今後は UX 検証や補助 route の確認だけでは、本来機能 gate を `pass` にできない。
- 新旧比較:
  - 旧: UX、contract、sample、install の確認と本機能完成の境界が shared rule として十分に明文化されていなかった。
  - 新: `UX-only` と本機能 `pass` を明確に分離し、mock 完了誤認を防ぐ rule を shared 化した。

### 2026-03-26 AGENTS.md workspace 外 directory の write 禁止

- 日時: `2026-03-26`
- 文書名: `AGENTS.md`
- 標題: `kisaragi` 作業時の workspace 外 access 制限
- 背景: `kisaragi` 作業中に外部 directory を参照する必要はある一方、workspace 外へ write 系 access を許すと管理境界と再現性が崩れる。
- 目的: `C:\Users\tetsuya\kisaragi` を作業中の workspace とする時、workspace 外 directory への access を `READ` のみに限定し、write 系操作を明確に禁止する。
- 対処方法: `AGENTS.md` に `workspace 外 access 制限` 節を追加し、`READ` 以外の access 禁止を shared rule として明文化した。
- 対応内容: 外部 directory への作成、編集、移動、削除、rename、生成物出力、cache 出力などを禁止し、必要情報は `kisaragi/` 配下へ吸収する運用を追記した。
- 更新結果: 今後 `kisaragi` 作業中は、workspace 外 directory への access は参照のみで扱い、write 系操作は行わない。
- 新旧比較:
  - 旧: 外部 directory 参照時の write 禁止が shared rule として明文化されていなかった。
  - 新: workspace 外 directory への access は `READ` のみに限定し、write 系 access を禁止する rule を shared 化した。

### 2026-03-25 AGENTS.md rule 外 `--` directory 生成の禁止

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: `--trial-data` のような rule 外 category 生成の禁止
- 背景: `prj-kisaragi_0002` の build 生成物が `--trial-data` へ出力され、許可済み category を迂回する directory 新設が発生した。
- 目的: `--` で始まる category directory の濫用を防ぎ、生成物は `--exsams` など既存 rule 内へ限定する。
- 対処方法: `共有 directory 統制` 節を追加し、Codex 判断での `--` category 新設禁止と、`--trial-data` のような rule 外出力先の禁止を shared rule として独立配置した。
- 対応内容: shared rule を独立節へ昇格し、`gradle.properties` も `--trial-data` から `--exsams` へ修正した。
- 更新結果: 今後の生成物は許可済み category のみを使い、rule 外の `--` directory を新設しない。
- 新旧比較:
  - 旧: rule 外の `--trial-data` を build 出力先として作れてしまい、禁止 rule も hygiene 節に埋もれていた。
  - 新: `--` category の無断新設と rule 外出力先の利用を shared rule として独立明示した。

### 2026-03-25 AGENTS.md project-name 対応表の No.2 更新

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: `prj-kisaragi_0002` の project-name を `prj-trajectreview` へ更新
- 背景: `project-code` は維持したまま、No.2 の project-name を現在の機能表現へ合わせて更新する指示が出た。
- 目的: immutable な `project-code` と可変な `project-name` の対応表を最新化し、関連文書と表示名の整合を保つ。
- 対処方法: `AGENTS.md` の対応表を更新し、`prj-kisaragi_0002` 配下の正本文書、README、表示名、Gradle project 名を `trajectreview` 基準へ同期した。
- 対応内容: `project-truth.md`、`b2t-plans-result.md`、`resume-startup-plan.md`、`mrl-record.md`、`README.md`、`strings.xml`、`settings.gradle.kts` などの人向け名称を更新した。
- 更新結果: `prj-kisaragi_0002` は directory 名を維持したまま、project-name と表示名を `prj-trajectreview` / `trajectreview` として扱う。
- 新旧比較:
  - 旧: No.2 は `prj-kisaragi_0002 : prj-reviework` だった。
  - 新: No.2 は `prj-kisaragi_0002 : prj-trajectreview` となり、関連表示も同期した。

### 2026-03-25 AGENTS.md 更新履歴を `AGENTSmd-RH.md` へ分離

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: 更新履歴正本の外部化
- 背景: `AGENTS.md` 本体が運用 rule と履歴を同時に抱えて肥大化し、rule の読み取り効率が落ちていた。
- 目的: 運用 rule の本文と更新履歴を分離し、`AGENTS.md` は rule、`AGENTSmd-RH.md` は履歴正本として扱えるようにする。
- 対処方法: `AGENTS.md` に `AGENTSmd-RH.md` を参照する rule を明記し、既存履歴をこの文書へ移した。
- 対応内容: `AGENTS.md` 末尾の更新履歴本文を削除し、`AGENTSmd-RH.md` 参照だけを残したうえで、既存全 entry をこの文書に統合した。
- 更新結果: 今後の `AGENTS.md` 履歴追加は、この文書に対して実施する。
- 新旧比較:
  - 旧: `AGENTS.md` 本体末尾に更新履歴本文を直接持っていた。
  - 新: `AGENTS.md` は履歴参照のみを持ち、更新履歴正本は `AGENTSmd-RH.md` に集約した。

### 2026-03-25 AGENTS.md project code を directory 正本へ適用

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: `prj-kisaragi_****` 形式の project directory 正本化
- 背景: project 名は将来変更され得るため、project 固有 directory と生成物の命名を immutable な `project-code` へ寄せたい要求が出た。
- 目的: `kisaragi/` 配下の project 固有 path と data 名を `project-code` 基準で安定化し、名称変更による参照破綻を防ぐ。
- 対処方法: `prj-<project-name>` と書いていた構造 rule を `prj-kisaragi_****` へ置換し、計画、evidence、raw artifact の path rule も code 基準へ統一した。
- 対応内容: `kisaragi-db/` 配下の project directory rule、`--exsams/` rule、計画書と evidence path rule、tree sync の確認 path を `prj-kisaragi_****` に更新した。
- 更新結果: 今後の project 固有 directory、生成物、識別 path は `project-name` ではなく `project-code` を使う。
- 新旧比較:
  - 旧: `prj-direview` や `prj-reviework` のように project 名を directory 名へ使っていた。
  - 新: `prj-kisaragi_0001`、`prj-kisaragi_0002` のように immutable な `project-code` を directory 名へ使う。

### 2026-03-25 AGENTS.md MRL 状態語の意味固定

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: `planned`、`active`、`pass` の意味固定
- 背景: `reviework` の `MRL` 更新時に、計画済み項目を一括で `pass` 扱いしてしまい、着手中と完了済みの区別が曖昧になった。
- 目的: `MRL`、`mRL`、TDD task の状態語を全 project で同じ意味で使い、過大な closeout を防ぐ。
- 対処方法: 開発計画節へ `planned`、`active`、`pass` の定義を追記した。
- 対応内容: `planned` を未着手、`active` を着手中、`pass` を `active` 後に完了した gate として固定した。
- 更新結果: 今後は `MRL` / `mRL` の進捗を、計画、着手中、完了で誤解なく管理できる。
- 新旧比較:
  - 旧: `planned` と `pass` の境界が明文化されていなかった。
  - 新: `planned`、`active`、`pass` の意味を shared rule として固定した。

### 2026-03-25 AGENTS.md resume-startup-plan の役割明確化

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: `resume-startup-plan.md` の用途固定
- 背景: `reviework` の補助計画書を残す理由が file 名だけでは伝わらず、通常計画書との違いが分かりにくかった。
- 目的: 中断後の再開時に現在地と立ち上げ順を短く掴むための補助文書であることを shared rule として明確にする。
- 対処方法: 開発計画節へ `resume-startup-plan.md` の役割を追記した。
- 対応内容: 正本を置き換えず、再開導線と初動確認項目を補助する文書として位置付けた。
- 更新結果: 今後は、補助計画を残す理由と使いどころを file 名と shared rule の両方から理解できる。
- 新旧比較:
  - 旧: 補助計画書を残す理由が文書構造上は明確でなかった。
  - 新: `resume-startup-plan.md` は再開時の現在地把握と立ち上げ順確認のための補助文書だと明示した。

### 2026-03-25 AGENTS.md B2T 統合正本への移行

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: `b2t-plans-result.md` への統合
- 背景: `bdd-release-compass.md`、`tdd-test-matrix.md`、project 個別 `current_state.md` の重複が強く、同じ project 真実を複数 file で同期する負荷が高かった。
- 目的: `current_state`、BDD、TDD を 1 つの正本へ統合し、計画と結果の同期漏れを減らす。
- 対処方法: 開発計画節と標準文書構成を `b2t-plans-result.md` 基準へ更新した。
- 対応内容: `b2t-plans-result.md` に `current_state` 章、BDD 章、TDD 章を必須化し、project 個別 `current_state.md` は原則統合管理に切り替えた。
- 更新結果: 今後は project ごとに `b2t-plans-result.md` と `mrl-record.md` を中心に運用する。
- 新旧比較:
  - 旧: `bdd-release-compass.md`、`tdd-test-matrix.md`、`prj-<project>/current_state.md` を別々に管理していた。
  - 新: `b2t-plans-result.md` 1 file に `current_state`、BDD、TDD を統合して管理する。

### 2026-03-25 AGENTS.md BDD 記法の識別子統一

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: `Purpose Story` と `System Behaviors` の識別子統一
- 背景: BDD 記法内で `コアストーリー` と `user stories`、`terminal behaviors` の呼び方が混在し、参照粒度が揺れていた。
- 目的: BDD 計画の読み方を全 project で統一し、`MRL`、受け入れ基準、TDD から同じ識別子で追えるようにする。
- 対処方法: BDD 章の必須構成を `Purpose Story`、`System Behaviors` に改め、`s-id` と `b-id` を受け入れ基準と `MRL` 対応表へ必須化した。
- 対応内容: `Purpose Story` を `s1` 形式、`System Behaviors` を `b1` 形式とし、`prj-reviework` の `b2t-plans-result.md` を記法見本に指定した。
- 更新結果: 今後の BDD 計画は、story、behavior、受け入れ基準、`MRL` を同じ識別子体系で横断参照できる。
- 新旧比較:
  - 旧: `コアストーリー`、`user stories`、`terminal behaviors` の呼称と識別子が project ごとに揺れ得た。
  - 新: `Purpose Story` は `s1`、`System Behaviors` は `b1`、受け入れ基準と `MRL` 対応表は `s-id` と `b-id` 必須で統一した。

### 2026-03-25 AGENTS.md 計画正本と MRL 参考位置付けの明確化

- 日時: `2026-03-25`
- 文書名: `AGENTS.md`
- 標題: plan 正本と参考情報の役割整理
- 背景: `prj-direview` の rename と UI 修正を先行実装した後、計画正本を project ごとに先に固定し、`MRL` と `mRL` は参考情報として扱う運用を全 project 共通で固定したい要求が出た。
- 目的: BDD/TDD 計画をどの project でも先に作ること、何を残すか、`MRL` と `mRL` をどう位置付けるかを shared control file に明文化する。
- 対処方法: 開発計画節へ必須作成 rule、計画正本 role、`market_release_lines.md` と `micro_release_lines.md` の参考 role を追記した。
- 対応内容: 実装前の plan 作成義務、検証方法と小 milestone の明示、`MRL` と `mRL` の参考情報化、closeout は `mrl-record.md` へ寄せる rule を追加した。
- 更新結果: 今後は project ごとに `b2t-plans-result.md` を正本計画として残し、`MRL` / `mRL` は補助的な release-line 参照として扱う運用を共通化した。
- 新旧比較:
  - 旧: `MRL` / `mRL` と計画正本の役割分担が明文化されていなかった。
  - 新: `b2t-plans-result.md` が正本、`MRL` / `mRL` は参考、closeout は `mrl-record.md` へ集約する方針を明示した。
