# project-truth

## 目的

`prj-kisaragi_0001` は、`kisaragi-db` と `kisaragi-tree` を dual-pane の read-only viewer で比較し、構造確認、文書読解、比較対象の選定、Explorer handoff を高速に行うための project である。

## 完成判定

- launcher から `db-view` と `prj-view` を開ける
- 両 pane が独立状態を保ったまま basis switch、search、reader を提供する
- Markdown と plain text 系 file を app 内で安全に読める
- Explorer handoff が read-only 境界を壊さない

## 利用入口

- 既定入口は `npm run dashboard`
- Windows launcher は `kisaragi_0001-launch.cmd`
- 補助入口として local static preview と desktop shortcut を許容する

## UX 原則

- live source は read-only first を維持する
- dual-pane の左右独立状態を崩さない
- file explorer と reader を分離しない
- unsupported binary file は viewer に持ち込まない
- Explorer handoff は reveal のみとし、content mutation は行わない

## 段階構造

### Source Discovery

- launcher mode では `db-view` と `prj-view` の 2 profile を返す
- configured roots 外の path を扱わない

### Comparison Workspace

- each pane は `profileId`、`searchQuery`、`expandDepth`、`expandedPaths`、`selectedPath` を独立保持する
- compact tree と sticky trail で比較対象へ素早く到達できる

### Reading Surface

- `.md` は Markdown 表示する
- supported text file は plain text 表示する

### External Handoff

- Explorer handoff は configured roots 内の reveal target だけを解決する

## app 責務

### dashboard

- dual-pane state shell を持つ
- compact tree、automatic partial-match search、reader、Explorer handoff を一体で提供する

### launcher

- `kisaragi/` 直下を表示 root として browser を起動する
- default basis は `prj-view` とする

## artifact 契約

### source profile contract

- launcher mode では `db-view` と `prj-view` を返す
- `db-view` は launcher の 1 つ上の `kisaragi-db` を `projectRoot` とする
- `prj-view` は launcher の 1 つ上の `kisaragi-tree` を `projectRoot` とする

### display contract

- `.md` は Markdown、その他 supported text file は plain text とする
- source code、config、script、`.env`、log 系 text file を表示対象に含める

### navigation contract

- search は submit button なしで自動実行する
- partial-match とし、matching branch を auto-expand する

## 外部連携境界

- browser page title は `direview`
- entry command は `npm run dashboard`
- desktop shortcut は `kisaragi_0001-launch.lnk` を正本とする
- 補助 reference として `market_release_lines.md`、`micro_release_lines.md` を `--tgpce-map` 同階層に置いてよい
