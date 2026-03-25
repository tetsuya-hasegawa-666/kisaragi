# 再開ブートストラップ計画

## 目標

- `trajectreview` の再開計画を `prj-kisaragi_0002` 配下の正本文書だけで読める状態にする
- 外部一時文書に残っていた処理構造と UX 構想を `project-truth.md` と `b2t-plans-result.md` へ吸収する
- `MRL-1` の実装着手に直結する task を明確にする

## 第 1 段階

- `project-truth.md` に 4 段階処理構造とパッケージ契約を固定する
- 4 分担の入力、出力、受け渡し条件を固定する
- `b2t-plans-result.md` の BDD 章に terminal behavior と `MRL` / `mRL` を固定する
- `b2t-plans-result.md` の TDD 章に検証 task と優先順を固定する
- `mrl-record.md` を作成し、再開基線を記録する

## 第 2 段階

- `SessionPackage` intake summary を実装し、`Thin Status` 診断と execute gate の test を先に置く
- `COLMAP` failure から diagnose へ戻る return path を明示する
- 主 `ARCore` 空間を唯一基準とする `SpacePackage` 契約を実装へ落とす

## 第 3 段階

- `TrajectoryPackage`、relink、不確実性、`attention point` を実データ由来で成立させる
- `ReviewArtifact` と viewer の責務境界を固定する
- 独立運用境界と生成物 routing を継続確認する

## 完了条件

- 外部参照が削除されても `prj-kisaragi_0002` の正本文書だけで再開判断ができる
- `MRL-1` 着手に必要な terminal behavior と TDD task が矛盾なく接続している
- `b2t-plans-result.md` の `current_state` 章から次の実装着手順が 3 件以内で読める
