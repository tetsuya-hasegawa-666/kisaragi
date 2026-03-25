# BDD リリースコンパス

この文書は、`prj-kisaragi_0001` の user value、core story、terminal behavior、release line の対応をまとめる正本計画書である。

## 文書の位置付け

- 実装前に target behavior、受け入れ基準、検証方針、到達したい milestone を明示する正本とする。
- `market_release_lines.md` と `micro_release_lines.md` は、この文書を補助する参考情報として扱う。
- `MRL` と `mRL` の表現はこの文書の terminal behavior と受け入れ基準に従属し、矛盾した場合はこの文書を優先する。
- release-line の附番は `2026-03-25` の今回修正開始を `MRL-1` / `mRL-1.1` の起点とする。
- `prj-kisaragi_0001` は `codev-viewer` の実装資産を基底に改名と再構成を進めた project として扱う。

## ノーススター

operator は launcher 配置から導いた workspace root から `db-view` と `prj-view` を dual-pane の read-only viewer で安全に閲覧し、basis 切替、構造確認、文書読解、Explorer handoff を同一画面で迷わず進められる。

## 提供方針

- live source は read-only first を維持する
- dual-pane の左右独立状態を崩さずに basis switch と読解を両立させる
- file explorer と reader を分離せず、比較準備から読解までを一連の flow として扱う
- in-app editing を持ち込まず、必要時だけ Explorer handoff へ渡す

## コアストーリー

1. operator は launcher mode で `prj-view` を既定に、`db-view` と `prj-view` を basis 単位で切り替えられる
2. operator は左右 pane を独立状態のまま保って比較できる
3. operator は compact tree と自動 search で対象文書へ素早く到達できる
4. operator は Markdown と plain text 系 file を viewer 内で安全に読める
5. operator は configured roots 外の path を handoff できず、read-only 境界が守られる
6. operator は unsupported binary file を UI に持ち込まずに済む
7. operator は responsive 時も左右 split を維持したまま比較を続けられる
8. operator は必要時だけ Explorer handoff で外部編集系 tool へ移れる
9. operator は `npm run dashboard` と launcher icon を入口に、`direview` として dashboard を起動できる

## terminal behaviors

- `B1`: viewer は 1 つ以上の source profile の文書を収集し、launcher mode では `db-view` と `prj-view` を返す
- `B2`: left pane と right pane は profile、search、expand state、selection を独立して保持する
- `B3`: document workspace は profile tab、compact expandable tree、sticky trail を表示できる
- `B4`: search は submit button なしで自動実行され、partial-match の結果 branch を展開する
- `B5`: Markdown file を選択すると、reading layout で本文を読める
- `B6`: non-Markdown の supported text file を選択すると、plain text として読める
- `B7`: Explorer handoff は configured roots 内だけを reveal target として解決し、外側 path は拒否する
- `B8`: code target と consultation 系導線は read-only policy note と phase gate を保つ
- `B9`: dashboard は `npm run dashboard` と launcher icon を entry にし、browser page title を `direview` に固定する

## 受け入れ基準

| behavior_id | 観点 | 受け入れ基準 |
| --- | --- | --- |
| `B1` | source profile | 収集結果に profile metadata が入り、launcher mode では `db-view` と `prj-view` が読める |
| `B2` | dual-pane state | 左右 pane の切替や選択が互いの状態を上書きしない |
| `B3` | navigation UI | profile tab、compact tree、sticky trail が同一 workspace で読め、未選択時は sticky trail が空白になる |
| `B4` | search UX | submit 操作なしで matching branch が展開される |
| `B5` | Markdown reader | Markdown file 選択時に reading layout が表示される |
| `B6` | plain text reader | non-Markdown の supported text file が plain text で表示される |
| `B7` | safety boundary | configured roots 外 path は reveal target として拒否される |
| `B8` | read-only policy | code consultation は phase gate の内側に保たれ、編集機能を持ち込まない |
| `B9` | launch contract | `npm run dashboard` または launcher icon で dashboard が起動し、page title が `direview` になる |

## MRL 対応表

### MRL-1 source profile foundation line

- user stories: `1`, `2`, `5`
- current gate: `pass`

#### mRL-1.1 source profile manifest contract

- `B1` を成立させる
- gate: `pass`

#### mRL-1.2 shell switch and read-only reset

- `B2`、`B8` を成立させる
- gate: `pass`

#### mRL-1.3 documentation and state alignment

- `B1`、`B8` の計画と状態記録をそろえる
- gate: `pass`

### MRL-2 comparison workspace line

- user stories: `2`, `3`, `4`, `7`
- current gate: `pass`

#### mRL-2.1 compare lane selection model

- `B2`、`B3` を成立させる
- gate: `pass`

#### mRL-2.2 side-by-side preview contract

- `B5`、`B6` を成立させる
- gate: `pass`

#### mRL-2.3 cross-profile comparison evidence

- `B3`、`B4` の比較 UX を evidence で固定する
- gate: `pass`

### MRL-3 local handoff line

- user stories: `5`, `6`, `8`
- current gate: `pass`

#### mRL-3.1 reveal target resolution

- `B7` を成立させる
- gate: `pass`

#### mRL-3.2 right click Explorer handoff

- `B7`、`B8` を成立させる
- gate: `pass`

#### mRL-3.3 no-edit UX close

- `B8` を成立させる
- gate: `pass`

### MRL-4 launch and UI direction line

- user stories: `3`, `4`, `7`, `9`
- current gate: `pass`

#### mRL-4.1 launch method candidates

- `B9` を成立させる
- gate: `pass`

#### mRL-4.2 global UI composition direction

- `B3`、`B5`、`B6` を成立させる
- gate: `pass`

#### mRL-4.3 implementation-start close

- `B9` と UI 全体方針の整合を固定する
- gate: `pass`
