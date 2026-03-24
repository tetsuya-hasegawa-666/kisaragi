# project-core

この文書は `prj-codev-viewer` の artifact 正本を統合した `project-core.md` とする。

## 目的

`prj-codev-viewer` は `codev-db` と `codev-view` を read-only で比較閲覧する dual-pane viewer であり、構造確認、文書読解、比較対象の選定、Explorer handoff を高速に行うために存在する。

## north star

- operator は basis を切り替えながら project 構造をすばやく比較できる
- operator は supported text file を viewer 内で安全に読める
- operator は編集を viewer に持ち込まず、必要時だけ Explorer handoff で外部編集へ移る
- dual-pane の左右独立状態を保ち、比較のための視線移動を最小化する

## user value

- `codev-db` 正本と `codev-view` view layer を同じ UI で見比べられる
- file explorer と reader を分離せず、比較準備から読解までを同一画面で完結できる
- in-app editing を持たないため、live source を安全に扱える

## project contract

### source profile contract

- profile は `codev-db` と `codev-view` の 2 系統を持つ
- each pane は独立した `profileId`、`searchQuery`、`expandDepth`、`expandedPaths`、`selectedPath` を持つ
- default basis は `codev-view` とする
- source path は configured roots の外へ出ない

### file display contract

- `.md` は Markdown 表示する
- そのほかの supported text file は plain text 表示する
- source code、config、script、`.env`、log 系 text file を表示対象に含める
- unsupported binary file は tree から除外する

### search and navigation contract

- search は submit button なしで自動実行する
- partial-match とし、prefix match のみに限定しない
- matching branch を auto-expand する
- tree label の選択性と IME composition を壊さない

### launch contract

- browser page title は `codev-viewer`
- entry command は `npm run dashboard`
- dashboard は dual-pane read-only shell として起動する

### safety boundary

- live source は read-only first とする
- in-app editing、draft、apply flow は対象外とする
- Explorer handoff は file / directory の reveal のみとし、content mutation は行わない

## system blueprint

### module structure

- `shared-core`: dual-pane state shell、pane-local state、render orchestration
- `document-workspace`: compact tree explorer、automatic partial-match search、Markdown / plain-text reader
- `workspace-access`: source profile manifest、profile switch contract、Explorer reveal target resolution
- `tools/liveProjectSnapshot.ts`: filesystem snapshot、displayable text file discovery、reveal target resolution

### MVC boundary

- Model: repository、source profile manifest、document tree contract、reveal contract
- Controller: profile switch、search、expand-depth、tree expand / collapse、selection、Explorer handoff
- View: 左右 pane、compact trail strip、Markdown reader、plain-text reader、日本語 operator wording

### interaction flow

1. live snapshot が configured roots から source profile と displayable text file を収集する
2. each pane が自分の active profile、search query、expand depth、expanded path、selected path を保持する
3. selection mode では compact tree と auto-expanded search result を表示する
4. file selection 時だけその pane を reader mode に切り替える
5. reader mode は compact trail strip と file body を表示する
6. Explorer handoff は常に外部 action として残す

## success criteria

- 両 pane が basis switch、search、compact tree navigation、file reading を独立して提供できる
- Markdown と plain text 系 file が app 外へ出ずに読める
- Explorer handoff が read-only viewer を壊さずに動作する
- responsive 時も左右 split を維持する
