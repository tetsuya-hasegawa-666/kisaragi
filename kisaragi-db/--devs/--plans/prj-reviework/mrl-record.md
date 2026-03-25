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
  remaining work: `MRL-1` の `SessionPackage` intake summary、`Thin Status`、execute gate を実装と test へ落とす
  evidence path: `kisaragi-db/--devs/--plans/prj-reviework/bdd-release-compass.md`
