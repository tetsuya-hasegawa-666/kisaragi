# 現在状態

## 計画状況

- current plan set: `none`
- latest completed plan set: `2026-03-22-007`
- latest completed market release: `MRL-28`
- latest completed micro release: `mRL-28-3`
- current blocker: `none`

## 完了済みベースライン

- 2 画面の read-only viewer shell
- `codev-db` / `codev-view` source profile switch
- 両 pane の compact tree explorer
- 両 pane の自動 partial-match search
- expand depth で制御する tree expansion
- Markdown と plain-text reader
- Explorer handoff

## 現行 UI 仕様

- source-of-truth artifact: `kisaragi-db/--devs/--project-truth/prj-direview/project-core.md`
- source-of-truth UI spec: `kisaragi-db/--devs/--plans/prj-direview/bdd-release-compass.md`
- default basis is `codev-view`
- both panes stay side by side even in responsive mode
- both panes have the same controls: `全閉`, `全開`, expand depth input, basis tabs, automatic search
- file reader supports Markdown and plain-text oriented files including `.env` and script/config sources
- text selection in tree labels and reader bodies must remain selectable without immediate deselection

## 最新検証

- `npm test`
- `npm run build`

## 完了 evidence

- latest evidence: `Codex retest`
- visual and operator validation remain user-side checks

## 2026-03-24 作業所有権

- Codex が `bdd-release-compass.md` と `tdd-test-matrix.md` の新規整備を担当する
