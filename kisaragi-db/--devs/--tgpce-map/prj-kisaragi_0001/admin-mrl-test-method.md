# admin-mrl-test-method

## 文書の目的

- `prj-kisaragi_0001` の構築物を人が試用、使用、運用する時の手順を整理して保持する。

## 対象

- dashboard の起動
- 画面確認
- 手動 review 観点

## 手順

1. `C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0001` へ移動する。
2. 初回だけ `npm ci` を実行する。
3. `npm run dashboard` を実行する。
4. browser で `http://127.0.0.1:4173/` を開く。
5. page title が `direview` であることを確認する。
6. 左右 pane が並列表示され、basis tab、`全閉`、`全開`、expand depth input、automatic search が両側にあることを確認する。
7. 文書選択で Markdown と plain text reader が切り替わることを確認する。
8. `Explorer handoff` が configured roots 外 path を受け付けないことを確認する。

## アイコン起動

- 起動 script 正本は `C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0001\tools\launch-dashboard.ps1` とする。
- main launcher は `C:\Users\tetsuya\kisaragi\kisaragi_0001-launch.cmd` とする。
- `C:\Users\tetsuya\kisaragi\kisaragi_0001-launch.cmd` は `C:\Users\tetsuya\kisaragi` を表示 root にする。
- `db-view` tab と `prj-view` tab はどちらも `C:\Users\tetsuya\kisaragi` 直下を表示し、basis 選択を保ったまま tree を閲覧する。
- 既定の active tab は `prj-view` とする。
- shortcut は `C:\Users\tetsuya\kisaragi\kisaragi_0001-launch.lnk` を正本とする。
- launcher 起動後は browser が `http://127.0.0.1:4173/` を開き、PowerShell window は server stop まで残る。

## sticky path 表示

- 初期状態の sticky path は空白とする。
- directory を選択した時は、その directory までの path を sticky path に表示する。
- file を選択した時は、その file までの path を detail strip に表示する。

## 確認結果の記録方針

- 実施日時、対象 build、実施者、確認観点、結果、未解決事項を追記する。

## 最新確認

- 実施日時: `2026-03-25`
- 実施者: `Codex`
- 対象 build: `npm run build` 実行直後の local dist
- 確認観点:
  - `npm test` が pass する
  - `npm run build` が pass する
  - `C:\Users\tetsuya\kisaragi\kisaragi_0001-launch.cmd` が `db-view` と `prj-view` を返す
  - `db-view` と `prj-view` がともに `C:\Users\tetsuya\kisaragi` 直下全体を指す
  - built artifact を local static server で配信すると `index.html`、JS、CSS が `200` を返す
  - page title が `direview` である
  - built bundle に `Explorer handoff`、`全閉`、`全開`、`db-view`、`prj-view` が含まれる
- 結果: pass
- raw evidence:
  - `kisaragi-db/--exsams/prj-kisaragi_0001/logs/2026-03-25-npm-test.log`
  - `kisaragi-db/--exsams/prj-kisaragi_0001/logs/2026-03-25-npm-build.log`
  - `kisaragi-db/--exsams/prj-kisaragi_0001/logs/2026-03-25-preview-check.txt`
  - `kisaragi-db/--exsams/prj-kisaragi_0001/logs/2026-03-25-launcher-live-state.json`
  - `kisaragi-db/--exsams/prj-kisaragi_0001/logs/2026-03-25-launcher-check.txt`
- 未解決事項:
  - headless Edge による Vite dev server 直読は環境依存で timeout したため、今回の browser automation は static preview smoke check で代替した
