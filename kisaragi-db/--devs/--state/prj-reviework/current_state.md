# 現在状態

## 役割

- `prj-reviework` は review / reconstruction workflow の bootstrap project とする
- `Next Action + Thin Status` を中核 UX とし、`iSensorium` の session handling を入口として流用する

## 現在の focus

- source-of-truth を先に固定する
- artifact 正本は `project-core.md` に統合済みとする
- `iSensorium` から parser / validator と UI skeleton pattern を独立コピーする
- `COLMAP`、`3DGS`、`Trajectory`、`Assembly` を新規責務として切り出す
- build output、test report、Python cache の出力先を `--trial-data` / `--testlogs` に固定する
- `project-core.md` を基準に BDD / TDD plan を `--process/--plans/prj-reviework/` へ追加した

## blocker 境界

- `COLMAP` / `3DGS` 実行基盤は未選定
- `Viewer` の最終実装先は Android 固定ではない
- `GNSS` は optional input として扱う前提に補正済み

## 次の確認

1. execute readiness gate の条件を実装へ落とす
2. `COLMAP` failure から diagnose へ戻る return path を定義する
3. verify / interpret の quality summary と attention point synthesis を実装へ落とす
4. `run_android_unit_tests.ps1` と `run_python_tests.ps1` の運用を基準にし、生成物が `--products` に戻らないことを維持する
