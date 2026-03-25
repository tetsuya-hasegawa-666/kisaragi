# 現在状態

## 役割

- `prj-reviework` は、主空間再構成と経路レビューを 4 段階一括処理で扱う project とする
- `Next Action + Thin Status` を中核 UX とし、`SessionPackage`、`SpacePackage`、`TrajectoryPackage`、`ReviewArtifact` の契約で進める

## 現在の重点

- 外部一時文書に残っていた処理構造と UX 概念を `prj-reviework` の正本文書へ吸収した
- 4 分担作業のための段階間インターフェースと追加出力を正本文書へ明示する
- `MRL-1` の入口である `SessionPackage` intake summary、`Thin Status`、実行可否 gate を次の実装対象とする
- `GNSS` は任意入力とし、既定は `GNSS` なしでも成立する設計とする
- 主 `ARCore` 空間を唯一基準とする `SpacePackage` 契約を基準に進める

## 阻害要因の境界

- `COLMAP` と `3DGS` の実行基盤は未選定である
- 作業員 path の視覚再拘束に使う実データ条件が未確定である
- `ReviewArtifact` の最終 viewer 実装先は Android 固定ではない

## 次の確認

1. `InputPackaging` の分担用インターフェース出力を Python parser に追加する
2. `SessionPackage` intake summary と実行可否 gate の fail する test を追加する
3. 主 `ARCore` 空間を唯一基準とする `SpacePackage` 契約と `COLMAP` failure return path を定義する

## 2026-03-25 作業所有権

- Codex が `project-truth.md`、`bdd-release-compass.md`、`tdd-test-matrix.md`、`mrl-record.md`、`current_state.md` の再開基線整備を担当する
