# 現在状態

## 役割

- `prj-reviework` は、主空間再構成と経路レビューを 4 段階一括処理で扱う project とする
- `Next Action + Thin Status` を中核 UX とし、`SessionPackage`、`SpacePackage`、`TrajectoryPackage`、`ReviewArtifact` の契約で進める

## 現在の重点

- 現行計画の `MRL` / `mRL` と `T1` から `T16` は、contract 実装、test、routing 実行で `pass` になった
- 4 分担作業のための段階間インターフェースと追加出力を正本文書へ明示した
- Kotlin controller と Python parser により、受理、gate、空間品質、人物経路、同時刻ハイライト、成果物境界の契約を固定した
- `GNSS` は任意入力とし、既定は `GNSS` なしでも成立する設計を維持する

## 阻害要因の境界

- `COLMAP` と `3DGS` の実行基盤は未選定である
- 人物 path の視覚再拘束に使う実データ条件が未確定である
- `ReviewArtifact` の最終 viewer 実装先は Android 固定ではない

## 次の確認

1. parser と controller の契約評価を実データ読込へ接続する
2. `3DGS` と viewer の実成果物を `ReviewArtifact` 契約へ接続する
3. 同時刻ハイライトを実データから自動生成する

## 2026-03-25 作業所有権

- Codex が `project-truth.md`、`bdd-release-compass.md`、`tdd-test-matrix.md`、`mrl-record.md`、`current_state.md` の再開基線整備と、過大 closeout の修正後の `MRL` 継続作業を担当する
