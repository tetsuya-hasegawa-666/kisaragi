# mrl-record

## 目的文

この文書は `prj-reviework` の `MRL` / `mRL` closeout 記録を残す正本とする。

## 記録ルール

- `MRL` または `mRL` が `pass` になったら 1 entry を追加する
- entry には issue、cause、resolution、recurrence prevention、remaining work、evidence path を含める
- planning 基線の再作成や大きな再開判断も entry として残してよい

## Entries

- record date: `2026-03-25`
  target MRL: `none`
  target mRL: `none`
  gate change: `initialized`
  issue: `reviework` の再開前提が外部一時文書に残っており、削除後に計画根拠を失う状態だった
  cause: 処理 4 段階、`GNSS` なし前提、UX 概念、package 契約が `prj-reviework` の正本文書へ十分に吸収されていなかった
  resolution: `project-truth.md`、`bdd-release-compass.md`、`tdd-test-matrix.md`、`current_state.md` を更新し、再開基線を `prj-reviework` 配下へ集約した
  recurrence prevention: 外部補助文書で採用した構想は、次の実装着手前に `project-truth` と BDD / TDD 正本へ同時反映する
  remaining work: 契約 closeout を実データ処理と viewer 実装へ接続する
  evidence path: `kisaragi-db/--devs/--plans/prj-reviework/bdd-release-compass.md`
- record date: `2026-03-25`
  target MRL: `MRL-1`
  target mRL: `mRL-1.1` から `mRL-1.4`
  gate change: `pass`
  issue: diagnose、実行可否 gate、分担インターフェースが planned または active のままだった
  cause: parser と controller が静的 demo 中心で、人物映り込みや readiness を判定する契約評価が未固定だった
  resolution: Python parser に `SessionPackage` インターフェース出力を追加し、Kotlin controller に diagnose と execute gate の契約評価を追加した
  recurrence prevention: 新しい入力契約は parser test と controller test の両方で固定する
  remaining work: 実データ入力を Android UI へ接続する
  evidence path: `kisaragi-db/--devs/--testcode/prj-reviework/test_session_parser.py`
- record date: `2026-03-25`
  target MRL: `MRL-2`
  target mRL: `mRL-2.1` から `mRL-2.3`
  gate change: `pass`
  issue: 主空間基準、`COLMAP` 安全 gate、空間品質要約が planned のままだった
  cause: controller が主空間品質と主カメラ path の契約を明示していなかった
  resolution: `SpacePackage` 契約を controller の verify 表示へ反映し、`COLMAP` blocking 時は `3DGS` を止める挙動を test で固定した
  recurrence prevention: 主空間再構成の gate は verify 表示と blocking 表示の両方で検証する
  remaining work: 実際の `COLMAP` 出力と接続する
  evidence path: `kisaragi-db/--devs/--testcode/prj-reviework/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt`
- record date: `2026-03-25`
  target MRL: `MRL-3`
  target mRL: `mRL-3.1` から `mRL-3.3`
  gate change: `pass`
  issue: 人物経路、relink、不確実性、同時刻ハイライトが planned のままだった
  cause: trajectory 契約が viewer demo に十分反映されていなかった
  resolution: 人物経路 summary、relink 判定、不確実区間、同時刻ハイライト、`attention point` を controller と test に追加した
  recurrence prevention: trajectory 系は relink と highlight の両方を同じ test file で固定する
  remaining work: 実データ由来の人物 path 生成へ接続する
  evidence path: `kisaragi-db/--devs/--testcode/prj-reviework/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt`
- record date: `2026-03-25`
  target MRL: `MRL-4`
  target mRL: `mRL-4.1` から `mRL-4.3`
  gate change: `pass`
  issue: `ReviewArtifact` 境界と独立運用 closeout が未完だった
  cause: `Assembly` の責務、viewer の読み取り専用境界、分担契約が docs と test で分離固定されていなかった
  resolution: `ReviewArtifact` 境界を controller test で固定し、独立運用と stage handoff を BDD / TDD / project-truth で正本化した
  recurrence prevention: 成果物境界は docs だけでなく controller test と対で closeout する
  remaining work: 実 viewer で `3DGS` 操作と同時刻ハイライトを実データ接続する
  evidence path: `kisaragi-db/--devs/--plans/prj-reviework/bdd-release-compass.md`
