# 現在状態

## 共有制御

- この文書は project 横断の shared current state 正本とする。
- 2026-03-25: Codex が `project code` 命名規則に合わせた `prj-kisaragi_****` rename と全参照整合を担当する。
- 2026-03-25: Codex が `AGENTS.md` の Guard、branch 補足、Windows 運用マニュアル追記を担当する。
- 2026-03-25: Codex が今回に限る許可に基づき、`AGENTS.md` の `<order>` を含む全体圧縮を担当する。
- 2026-03-25: 人間承認により、全 project で `b2t-plans-result.md` を実装前の正本計画書とし、`MRL` / `mRL` は参考情報として扱う運用を採用する。
- 2026-03-25: 人間承認により、全 project の `b2t-plans-result.md` の BDD 章は `Purpose Story` を `s1` 形式、`System Behaviors` を `b1` 形式で記述し、`kisaragi-db/--devs/--plans/prj-kisaragi_0002/b2t-plans-result.md` を記法見本とする運用を採用する。
- 2026-03-25: 人間承認により、`MRL` 作業を開始したら、blocker があっても他に進められる作業を継続し、他に何もできない状態になるまで止まらない運用を採用する。
- 2026-03-25: 人間確認により、`planned` は未着手、`active` は着手中、`pass` は `active` 後に完了した gate として扱う。
- 2026-03-25: 人間承認により、project 個別の `current_state` は `b2t-plans-result.md` の `current_state` 章へ統合して管理する。
- 2026-03-25: 人間承認により、`prj-kisaragi_0002` は UI mock に `iSensorium` 抽出機能を統合し、`MRL-5` として完了まで継続する。
- 2026-03-25: Codex が `C:\Users\tetsuya\sandbox\codev-db` を解析し、`prj-kisaragi_0002` の `iSensorium` source intake 仕様を `project-truth` へ吸収する。
- 2026-03-25: Codex が `iSensorium` verified mirror を `prj-kisaragi_0002` の `--products` / `--testcode` へ保持し、`project-truth` から参照できる状態へ整える。
- 2026-03-25: Codex が `iSensorium` verified mirror を比較用 app `kisaragi-iSensorium` として `Xperia 5 III` へ install し、本来の `iSensorium` と並行比較できる状態へ整える。

## 人間確認待ち

- 現時点の記録なし

## 全体 blocker

- 現時点の記録なし

## 次の確認

- `prj-kisaragi_0001` と `prj-kisaragi_0002` rename 後の stale 参照と test routing を確認する
- `AGENTS.md` の branch 規則と state / decision path 規則の整合を維持する
- `AGENTS.md` の Guard から未存在 `issue-note.md` 依存を外す
- tree sync 実行物の起動方法と再生成手順を Windows 運用マニュアルへ追記する
- `prj-kisaragi_0002` の抽出 bundle を `SpaceReconstruction` 実装へ接続する
- `prj-kisaragi_0002` の `iSensorium` source intake 仕様を `Xperia 5 III` 実機操作手順へ結び付ける
- `prj-kisaragi_0002` の `iSensorium` collector 起動順と state transition を verified mirror から追加抽出する
