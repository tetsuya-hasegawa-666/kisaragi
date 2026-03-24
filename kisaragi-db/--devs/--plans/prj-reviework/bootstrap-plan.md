# ブートストラップ計画

## 目標

- `reviework` を sandbox 配下の独立 project として起動する
- `iSensorium` から流用可能な資産を `prj-reviework` にコピーする
- UX 構想の矛盾点と不足点を source-of-truth に反映する

## Phase 1

- docs bootstrap
- copy plan 起票
- current state 作成

## Phase 2

- parser / validator copy
- Android review screen bootstrap
- test scaffold 追加
- build output と test 生成物の出力先を `--trial-data` / `--testlogs` に固定する

## Phase 3

- `SessionPackage` / `ReviewArtifact` contract 詳細化
- pipeline 実行面の host / backend 分離判断
- `COLMAP` / `3DGS` integration route の計画化
- `bdd-release-compass.md` と `tdd-test-matrix.md` に沿って terminal behavior 単位へ分解する

## 完了条件

- docs navigation が成立している
- `prj-reviework` products が `prj-isensorium` へ依存せず独立参照できる
- 最低 1 本の Python test と 1 本の Kotlin unit test が通る
- BDD / TDD plan が `project-core.md` と矛盾なく接続されている
