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
  target mRL: `mRL-1.1`、`mRL-1.4`
  gate change: `pass`
  issue: 受理契約と分担インターフェースの入口固定が未完だった
  cause: parser と controller が静的 demo 中心で、人物映り込みや readiness を判定する契約評価が未固定だった
  resolution: Python parser に `SessionPackage` インターフェース出力を追加し、入力契約と段階間インターフェースを test で固定した
  recurrence prevention: 新しい入力契約は parser test と controller test の両方で固定する
  remaining work: diagnose と execute gate を `active` で継続し、実データ入力を Android UI へ接続する
  evidence path: `kisaragi-db/--devs/--testcode/prj-reviework/test_session_parser.py`
- record date: `2026-03-25`
- record date: `2026-03-25`
  target MRL: `MRL-2` から `MRL-4`
  target mRL: `mRL-1.2`、`mRL-1.3`、`mRL-2.x`、`mRL-3.x`、`mRL-4.x`
  gate change: `reverted to active/planned`
  issue: 契約 test と文書整合だけで `pass` 扱いしたため、着手中と完了済みの境界を取り違えた
  cause: `planned`、`active`、`pass` の運用意味を文書へ明文化する前に、契約固定済み項目を一括 closeout してしまった
  resolution: `AGENTS.md` に状態語の意味を追加し、`bdd-release-compass.md`、`tdd-test-matrix.md`、`current_state.md` の gate を保守的に `active` / `planned` へ修正した
  recurrence prevention: `MRL` / `mRL` の closeout は、実装、検証、残作業の 3 点がそろった項目だけに限定する
  remaining work: 実データ接続、viewer 実装、生成物 routing を継続し、`active` と `planned` を順次 close する
  evidence path: `kisaragi-db/--devs/--plans/prj-reviework/bdd-release-compass.md`
