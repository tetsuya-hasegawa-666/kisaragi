# verification-summary

- project: `prj-direview`
- verification date: `2026-03-25`

## command result

- `npm test`
  - result: pass
  - evidence: `../../../--exsams/prj-direview/logs/2026-03-25-npm-test.log`
  - summary: `8 files`, `28 tests` pass
- `npm run build`
  - result: pass
  - evidence: `../../../--exsams/prj-direview/logs/2026-03-25-npm-build.log`
  - dist file list: `./dist-file-list.txt`
- static preview smoke check
  - result: pass
  - evidence: `../../../--exsams/prj-direview/logs/2026-03-25-preview-check.txt`
  - summary: `index.html`、built JS、built CSS が `http://127.0.0.1:4173/` で `200` を返し、page title は `direview` だった
- built bundle string check
  - result: pass
  - summary: built JS に `direview`、`Explorer handoff`、`全閉`、`全開`、`prj-view`、`db-view` が含まれ、viewer UI の主要文字列を確認した
- launch shortcut smoke check
  - result: pass
  - evidence: `../../../--exsams/prj-direview/logs/2026-03-25-launcher-check.txt`
  - summary: `C:\Users\tetsuya\kisaragi\direview-launch.cmd` から起動した live-state は `kisaragi` 直下全体を `db-view` / `prj-view` で返し、既定 profile は `prj-view` として test で固定した

## conclusion

- `prj-direview` は `C:\Users\tetsuya\kisaragi\direview-launch.cmd` から起動し、`kisaragi` 直下全体を閲覧できる。`db-view` / `prj-view` の basis を切り替えつつ、既定は `prj-view` で起動できる。2026-03-25 時点の automated verification では正常運用継続可能と判断する。
- raw log と generated artifact は `kisaragi-db/--exsams/prj-direview/logs/` に保持する。
