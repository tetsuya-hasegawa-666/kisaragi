# mrl-record

## 目的文

この文書は `prj-kisaragi_0002` の `MRL` / `mRL` closeout 記録を残す正本とする。

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
  cause: 処理 4 段階、`GNSS` なし前提、UX 概念、package 契約が `prj-kisaragi_0002` の正本文書へ十分に吸収されていなかった
  resolution: `project-truth.md` と計画正本を更新し、再開基線を `prj-kisaragi_0002` 配下へ集約した
  recurrence prevention: 外部補助文書で採用した構想は、次の実装着手前に `project-truth` と BDD / TDD 正本へ同時反映する
  remaining work: 契約 closeout を実データ処理と viewer 実装へ接続する
  evidence path: `kisaragi-db/--devs/--plans/prj-kisaragi_0002/b2t-plans-result.md`
- record date: `2026-03-25`
  target MRL: `MRL-1`
  target mRL: `mRL-1.1`、`mRL-1.4`
  gate change: `pass`
  issue: 受理契約と分担インターフェースの入口固定が未完だった
  cause: parser と controller が静的 demo 中心で、人物映り込みや readiness を判定する契約評価が未固定だった
  resolution: Python parser に `SessionPackage` インターフェース出力を追加し、入力契約と段階間インターフェースを test で固定した
  recurrence prevention: 新しい入力契約は parser test と controller test の両方で固定する
  remaining work: diagnose と execute gate を `active` で継続し、実データ入力を Android UI へ接続する
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py`
- record date: `2026-03-25`
- record date: `2026-03-25`
  target MRL: `MRL-2` から `MRL-4`
  target mRL: `mRL-1.2`、`mRL-1.3`、`mRL-2.x`、`mRL-3.x`、`mRL-4.x`
  gate change: `reverted to active/planned`
  issue: 契約 test と文書整合だけで `pass` 扱いしたため、着手中と完了済みの境界を取り違えた
  cause: `planned`、`active`、`pass` の運用意味を文書へ明文化する前に、契約固定済み項目を一括 closeout してしまった
  resolution: `AGENTS.md` に状態語の意味を追加し、計画正本の gate を保守的に `active` / `planned` へ修正した
  recurrence prevention: `MRL` / `mRL` の closeout は、実装、検証、残作業の 3 点がそろった項目だけに限定する
  remaining work: 実データ接続、viewer 実装、生成物 routing を継続し、`active` と `planned` を順次 close する
  evidence path: `kisaragi-db/--devs/--plans/prj-kisaragi_0002/b2t-plans-result.md`
- record date: `2026-03-25`
  target MRL: `MRL-1`
  target mRL: `mRL-1.2`、`mRL-1.3`
  gate change: `pass`
  issue: diagnose と execute gate が contract demo 止まりで、完了扱いに戻せていなかった
  cause: 状態語修正後に、再評価済み evidence を gate 表へ戻していなかった
  resolution: Kotlin controller / unit test を evidence として再評価し、diagnose と execute readiness gate を `pass` に戻した
  recurrence prevention: 状態語訂正時も、有効な evidence を持つ task は再 closeout する
  remaining work: 実データ pipeline への接続
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt`
- record date: `2026-03-25`
  target MRL: `MRL-2`
  target mRL: `mRL-2.1` から `mRL-2.3`
  gate change: `pass`
  issue: 主空間基準、安全 gate、品質要約が契約固定済みでも closeout 未反映だった
  cause: 状態語見直し時に保守的に `active` へ戻した後、再判定を保留していた
  resolution: `SpacePackage` 関連の controller test を再評価し、`COLMAP` safety gate と coordinate contract を `pass` に更新した
  recurrence prevention: `MRL` closeout は TDD `pass` 一覧と突き合わせて更新する
  remaining work: 実空間再構成 engine との接続拡張
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt`
- record date: `2026-03-25`
  target MRL: `MRL-3`
  target mRL: `mRL-3.1` から `mRL-3.3`
  gate change: `pass`
  issue: 人物経路、不確実性、同時刻ハイライトが closeout 未反映だった
  cause: trajectory contract の実装と test は存在したが、状態訂正後に再 closeout していなかった
  resolution: relink、不確実区間、same-time highlight、attention point を Kotlin test evidence として再評価し、`pass` に更新した
  recurrence prevention: trajectory 系は同一 test file の pass 状態を `MRL` 表へ反映する
  remaining work: 実データ由来 path の拡張
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt`
- record date: `2026-03-25`
  target MRL: `MRL-4`
  target mRL: `mRL-4.1` から `mRL-4.3`
  gate change: `pass`
  issue: stage handoff contract、独立運用 scan、output routing hygiene の完了証跡が不足していた
  cause: docs のみで管理していたため、project 境界と routing の自動検査がなかった
  resolution: `review_contracts.py` と `test_project_contracts.py` を追加し、`run_android_unit_tests.ps1` と `run_python_tests.ps1` を `--exsams` / `--testlogs` 分離運用へ更新した
  recurrence prevention: handoff contract と routing は code と script 実行結果の両方を evidence にする
  remaining work: 実 viewer への contract 接続拡張
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_project_contracts.py`
