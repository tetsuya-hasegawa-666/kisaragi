---
name: reference-rewire-operator
description: 設計変更で path、file 名、docs_id、manifest 名、helper 所有、contract 名、generated output 名などの参照先を切り替える時に使う。変更前の参照面棚卸し、producer と consumer の追跡、互換窓口の要否判断、code と文書の同時更新、旧参照残骸の grep 検査、下流確認を同じ task で閉じたい時に発動する。対象 project が `HAUB` などの handoff 対照表や contract probe を持つ時は、その row 更新と probe / test 実行まで必須にする。
---

# Reference Rewire Operator

設計変更で参照先を変える時に、「置換したから終わり」を防ぐ skill とする。

## Core Workflow

1. 何の参照を切り替えるのかを 1 行で固定する。
   例: `旧 session root -> probe_root`、`old docs_id -> new docs_id`、`raw image dir -> trajectreview/image`
2. 変更前の参照面を棚卸しする。
   少なくとも producer、consumer、authoritative file、generated artifact、test、manual、evidence を列挙する。
3. 参照の型を分類する。
   - path / file 名
   - ID / token / docs_id
   - 関数 / helper 所有
   - contract key / JSON field
   - generated output / handoff artifact
   - 文書上の canonical 名
4. 切替方針を決める。
   - 一括置換で閉じるか
   - alias / compatibility window を置くか
   - dual-write / dual-read が要るか
   - old reference を hard fail にするか warning に留めるか
5. producer 側から先に直す。
   生成名、保存先、manifest、summary、handoff を先に固定し、consumer が読む値を曖昧にしない。
6. consumer 側を追随させる。
   parser、loader、preflight、viewer、cleanup、runbook、manual、evidence を同じ task で更新する。
7. project が `HAUB` などの handoff 対照表を持つ時は、producer token、consumer token、canonical path row を code 変更へ追随させる。
8. 旧参照残骸を grep で確認する。
   rename 後に旧 path、旧 ID、旧 key、旧 heading が残っていないかを確認する。
9. 下流確認を行う。
   少なくとも「生成できる」「読める」「文書から辿れる」の 3 点を確認する。
10. contract probe や source test を持つ project では、同じ task で必ず実行し、参照切替後の row と実装が一致していることを確認する。

## Typical Actions

- 置換前に `old -> new` 対応表を短く作る。
- `grep` / `rg` で old reference の出現箇所を先に全部洗う。
- 参照元と参照先を同じ粒度で並べる。
- helper 移設では call site だけでなく import、tests、inventory、design contract を同時更新する。
- path 変更では生成物 writer、reader、cleanup、download、evidence path を同時更新する。
- directory handoff 変更では、`batch_work_dir` のような親 scope path と `chunk_out_dir` のような leaf scope path を混同せず、二重ネストが起きないかを producer / consumer の両方で確認する。
- old manifest や旧 suffix 付き dir 名が残りうる移行期は、reader 側に `chunk_0005_*` のような legacy path fallback が必要かを明示的に判断する。
- docs_id 変更では表、source inventory、design contract、runbook 説明、test 名寄せを同時更新する。
- canonical 名変更では truth、plan、manual、resume、closeout の順に上位から直す。
- compatibility を置く時は終了条件を明記する。

## Guard Rails

- `grep 置換だけ` で終わらせない。
- producer より先に consumer だけ直さない。
- code だけ直して正本文書を放置しない。
- alias を置いたら、どこで消すかを書かずに放置しない。
- generated output 名を変えたのに cleanup 対象や evidence path を旧名のまま残さない。
- 参照変更を 1 file の局所修正に見せかけて、実際は多段 handoff を壊したままにしない。
- `HAUB` handoff 対照表や path contract probe を持つ project で、それらを更新せずに path / output / reader を変えない。
- parent scope directory と leaf artifact directory を同じ key 名で使い回し、`chunk_name` などを二重付与しない。
- producer を直した直後でも admin 実測が旧 manifest を再利用し得るなら、reader 側で旧 path を一時吸収する fallback を置く。

## Minimum Deliverables

- 変更対象の `old -> new` 対応表
- producer / consumer / docs の影響メモ
- 更新後の grep 結果
- 最低 1 つの downstream check

## Verification

- `references/reference-rewire-checklist.md` を順に確認する。
- 文書更新がある task では、authoritative file を先に直し、pointer / manual / evidence を後追いでそろえる。
- 可能なら `rg "old-reference"` を 0 件にする。残す場合は意図を説明する。
- rename や移設の後は `git diff --check` と対象 test / script 実行を行う。
- `HAUB` 対照表と contract probe を持つ project では、row 更新後に probe / test を実行し、結果を close 条件に含める。

## When To Read References

- 詳細 checklist が要る時は `references/reference-rewire-checklist.md` を読む。
- 変更が大きく、どの consumer を追うべきか迷う時だけ読み直せばよい。
