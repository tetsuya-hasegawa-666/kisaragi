# 現在状態

## 共有制御

- この文書は project 横断の shared current state 正本とする。
- 2026-03-28: Codex が `AGENTS.md` の全体方針に合わせた表現圧縮と、`AGENTSmd-RH.md` を含む関連文書の整合更新を担当する。
- 2026-03-28: Codex が `AGENTS.md` の shared / project 境界 rule、`INITL` / `mINITL` rule、`prj-kisaragi_0002` の `Colab all-in modeling` と package 準備計画の整合更新を担当する。
- 2026-03-28: Codex が `prj-kisaragi_0002` の `correcting` 保存先 / 転送先 UX 分離と、`AGENTS.md` 再発防止 rule、`project-truth.md`、`b2t-plans-result.md`、`ux_check_manual.md`、`mrl-ux-valid.md` の整合更新を担当する。
- 2026-03-28: Codex が `prj-kisaragi_0002` の `correcting` を `raw 保存 -> 品質確認 -> derived 同期` の順へ組み替え、`frame画像群` を転送時生成へ寄せる実装と文書整合を担当する。
- 2026-03-28: Codex が `prj-kisaragi_0002` の `Google Drive` 転送先を都度入力前提へ切り替え、`ISS-002` close のための実装と文書整合を担当する。
- 2026-03-28: Codex が `prj-kisaragi_0002` の `Google Drive` 転送 zip 名を `session-*` suffix 必須規則へ揃え、将来の help 必要性を `ISS-006` として記録する。
- 2026-03-28: Codex が `prj-kisaragi_0002` の `project-truth.md` から現在状態を外し、`b2t-plans-result.md` と evidence への役割分離、および `ISS-001` close の文書整合を担当する。
- 2026-03-28: Codex が `prj-kisaragi_0002` の `isensorium_xperia5iii_intake_spec.md` を `project-truth.md` の末尾へ統合し、`Xperia 5 III` intake 詳細を truth 単体でも読めるようにする。
- 2026-03-28: Codex が `prj-kisaragi_0002` の `reference_isensorium_verified_20260325` 配下を吸収し、`correcting` / `python` / `correcting/scripts` / `correcting-test` を現行正規配置へ整理する。
- 2026-03-26: Codex が `MRL` 記載順と `pass` 判定基準の是正のため、`current_state.md`、`decision_log.md`、`AGENTS.md`、`b2t-plans-result.md`、`mrl-record.md`、`mrl-ux-valid.md` の整合更新を担当する。
- 2026-03-26: Codex が `prj-kisaragi_0002` の mock 完了誤認を是正するため、`b2t-plans-result.md`、`project-truth.md`、`mrl-record.md`、`mrl-ux-valid.md`、`AGENTS.md`、`AGENTSmd-RH.md` の整合更新を担当する。
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
- 2026-03-25: Codex が `prj-kisaragi_0002` の `MRL-6` として、`session_package.json`、`space_handoff_manifest.json`、主カメラ動画を含む後段 handoff 加工を完了まで進める。
- 2026-03-26: Codex が `prj-kisaragi_0002` の `MRL-7` として、`correcting`、`modeling`、`reviewing`、統合 app の 4 app 構成と役割境界の中間成果を進める。
- 2026-03-26: Codex が `prj-kisaragi_0002` の `MRL-8` として、各 app の実 bundle 読込と `modeling` の `local sample before colab` を中間成果として進める。
- 2026-03-26: 人間承認により、`C:\Users\tetsuya\kisaragi` 作業中の workspace 外 directory access は `READ` のみを許可し、write 系 access を禁止する shared rule を採用する。
- 2026-03-26: 人間確認により、`prj-kisaragi_0002` の app 状態は `UX と局所 logic の確認が一部できた段階` であり、`本来機能が使える完成 app` とは扱わない。
- 2026-03-26: Codex が `prj-kisaragi_0002` の `MRL-5C` 実装と局所確認を進め、`trajectreview-correcting` 単体で `現場記録 -> data-check -> correction guidance` を実機 session で確認した。
- 2026-03-26: 人間承認により、`prj-kisaragi_0002` の `trajectreview-modeling` は `DA3Metric-Large` を first target とし、single route 固定ではなく `比較基盤`、`比較実験`、`採用 route の運用化` の 3 段 `MRL-9A` から `MRL-9C` で進める。
- 2026-03-26: 人間承認により、`MRL` 対応表は `planned` から `pass` への時系列ではなく、運用順 `correcting -> modeling -> reviewing` を優先して記載する。
- 2026-03-26: 人間承認により、`MRL` / `mRL` の `pass` は admin の `UX check 完了` があるものだけに限定し、既存 `pass` も同基準で再評価する。
- 2026-03-26: 人間承認により、admin の `UX check` は 1 gate ずつに限らず、関連する複数 `MRL` / `mRL` を 1 回の batch でまとめて実施してよい。
- 2026-03-26: Codex が `prj-kisaragi_0002` の admin batch `UX check` 雛形、`DA3Metric-Large` Colab notebook、remote result import helper、関連 test を整備する。
- 2026-03-27: 人間承認により、`prj-kisaragi_0002` の `trajectreview-modeling` は `ARCore pose`、frame timestamp、camera intrinsics を保持した session bundle を前提に、`DA3Metric-Large` の metric depth と world projection を Colab で比較運用する。
- 2026-03-27: Codex が `prj-kisaragi_0002` の `MRL-5D` として、`trajectreview-correcting` の `1 回以上 data-check -> Google Drive転送先選択 -> Google Drive転送` を実装する。
- 2026-03-27: Codex が `prj-kisaragi_0002` の calibration export interface 一時要件を `MRL-5C`、`MRL-6`、`MRL-9A` の正本へ吸収し、`arcore_pose.jsonl`、`camera_calibration_summary.json`、`frame_pose_index.csv`、`images/` の接続を実装する。
- 2026-03-27: Codex が top `README.md` を GitHub 向け repository overview として整備し、正本文書への入口を整理したうえで push を担当する。

## 人間確認待ち

- 現時点の記録なし

## 全体 blocker

- 現時点の記録なし

## 次の確認

- `prj-kisaragi_0002` の `UX-only` gate と `本機能完成` gate を分離し、誤って `pass` を付けた `MRL` を是正する
- `prj-kisaragi_0002` の `modeling` で、Colab notebook を実アカウント / GPU 上で起動し、`DA3Metric-Large` の metric depth 推定と point-cloud export の remote 実測を取る
- `prj-kisaragi_0002` の `MRL-9A` として `DA3Metric-Large` metric depth と world projection の実行証跡を追加する
- `prj-kisaragi_0002` の `MRL-5D` として `correcting` の `Google Drive` transfer を都度入力前提で局所検証し、admin 手順を evidence へ反映する
- `prj-kisaragi_0002` の `MRL-9B` として sampling / intrinsics route の remote 実測比較結果を `benchmark_summary.json` へ反映する
- `prj-kisaragi_0002` の `MRL-9C` として remote result import 後の `SpacePackage` / `TrajectoryPackage` 更新を app 側へ接続する
- `prj-kisaragi_0002` の `correcting` で、60 秒収録に対して `品質確認` が数秒級で終わることを実機で再確認し、必要なら `Storage Access Framework` 同期のさらなる短縮策を入れる
- `prj-kisaragi_0002` の `MRL` 表を `correcting -> modeling -> reviewing` 順へ再編し、admin `UX check` 未完の `pass` を `active` / `planned` へ戻す
- `prj-kisaragi_0001` と `prj-kisaragi_0002` rename 後の stale 参照と test routing を確認する
- `AGENTS.md` の branch 規則と state / decision path 規則の整合を維持する
- `AGENTS.md` の Guard から未存在 `issue-note.md` 依存を外す
- tree sync 実行物の起動方法と再生成手順を Windows 運用マニュアルへ追記する
- `prj-kisaragi_0002` の抽出 bundle を `SpaceReconstruction` 実装へ接続する
- `prj-kisaragi_0002` の `iSensorium` source intake 仕様を `Xperia 5 III` 実機操作手順へ結び付ける
- `prj-kisaragi_0002` の `iSensorium` collector 起動順と state transition を verified mirror から追加抽出する
- `prj-kisaragi_0002` の `space_handoff_manifest.json` を実 `SpaceReconstruction` engine へ接続する
- `prj-kisaragi_0002` の `colab_job_request.json`、`camera_calibration_summary.json`、生成 notebook を admin の batch `UX check` 手順へ接続する
