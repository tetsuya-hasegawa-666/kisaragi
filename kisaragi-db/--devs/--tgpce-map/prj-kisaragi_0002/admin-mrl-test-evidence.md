# admin-mrl-test-evidence

## 目的

この文書は `prj-kisaragi_0002` の `MRL` / `mRL` が `p-done` または `i-pass` になった根拠を、UX と実行証跡の両面から集約する。

## 2026-03-26 再評価

- 判定:
  - admin `UX check 完了` を `i-pass` 必須条件にする shared rule へ更新したため、既存の `pass` 解釈は全件再評価対象になった
  - 旧番号時代の `MRL` 既存 `pass` は、admin `UX check` 記録が明示されるまで `active` または `ready` として扱う
  - admin `UX check` は app 運用順に沿って、関連 gate をまとめた batch で実施してよい
  - 2026-03-25 から 2026-03-26 に記録した旧番号時代の一部 gate は、`UX-only`、`build / install`、`local sample`、summary 読込の確認としては有効だった
  - ただし、これらは `本来機能が app として完成した証拠` ではないため、対応する `MRL` / `mRL` の一部を `active` / `ready` へ戻した
- 維持する evidence:
  - 記録画面への到達、bundle 読込、request 生成、summary 表示、multi-app build は中間成果として引き続き有効である
  - Python unittest、Android unit test、device install、短時間 harness、局所 service 実行結果は、admin `UX check` 前の候補 evidence として引き続き有効である
- 取り消す解釈:
  - `correcting`、`modeling`、`reviewing`、統合 app が本来機能完成であるという解釈は採らない
  - admin `UX check` 未完でも `i-pass` にできるという解釈は採らない

## admin batch UX check rule

- `i-pass` に必要な `UX check` は admin が実施したものだけを有効とする
- `UX check` は 1 gate 単位に限らず、関連する複数 `MRL` / `mRL` を 1 回の batch でまとめて実施してよい
- batch 記録には、対象 `MRL` / `mRL`、実施日時、端末または環境、`ready / active / p-done / i-pass / fail`、失敗時の要点を必ず含める
- `admin-mrl-test-evidence.md` は admin batch `UX check` の記録場所として使う

## correcting batch 定義

- 対象 `MRL`:
  - `MRL-1`
  - `MRL-2`
- 対象 `mRL`:
  - `mRL-1.1` から `mRL-1.3`
  - `mRL-2.1` から `mRL-2.3`
- admin 操作観点:
  - `trajectreview-correcting` で記録開始、停止、session 保存ができる
- `data-check` に readiness、blocker、recommended correction が出る
- export 後の bundle に `session_package.json`、`space_handoff_manifest.json`、`sensor_quality.json` が出る

## 2026-03-31 `MRL-8` close evidence

- 対象 gate:
  - `MRL-8`
  - `mRL-8.1`
  - `mRL-8.2`
- UX 観点:
  - `Colab` 上で Drive 内の session zip 候補が重複なしに 3 件だけ列挙される
  - admin が dropdown widget で 1 件を選び、`selected input` を保存できる
  - 選んだ input がそのまま bootstrap 本体と `MRL-7 adopted one-block` の両方へ流れる
- 実行観点:
  - `Step 8a4 canonical candidate rescan`:
    - `candidate_count = 3`
    - canonical path は `shortcut-targets-by-id` 側だけを残す
  - `Step 8d retry after canonical candidate rescan`:
    - admin は `[2] trajectreview-correcting-session-20260331-034831 [zip]` を widget で選択
    - `selected_exists = true`
    - `session_root = /content/trajectreview_input/session-20260331-034831/trajectreview`
    - `image_count = 26`
    - `Step 2` から `Step 4.5` が `cuda` で成功
  - `Step 8e selected-input mrl7 adopted one-block`:
    - 同じ selected input を使って `MRL-7 adopted one-block` が成功
    - `processed_frames = 12`
    - `skipped_frames = 0`
    - `total_points = 4608`
- 判定:
  - hardcoded zip path を編集せず、fresh runtime から任意 session input を選んで runbook 本体と `MRL-7` one-block へ handoff できる
  - `MRL-8`、`mRL-8.1`、`mRL-8.2` を `p-done` とする
- 主要 evidence:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/da3_colab_evid_runbook.md`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/evidence/`
  - `trajectreview/results/trajectreview-correcting-session-20260331-034831_da3_smoke_v24/`
  - `trajectreview/results/trajectreview-correcting-session-20260331-034831_da3_multiframe_probe_v01/world_fusion_v01/`
  - `Google Drive` 転送と handoff bundle を 1 回の収録から読める

## 2026-03-31 `MRL-2S` bounded stop candidate evidence

- 対象 gate:
  - `MRL-2S`
  - `mRL-2S.1`
  - `mRL-2S.2`
- 実施者:
  - `admin`
- 端末 / 環境:
  - `Xperia 5 III`
  - Android app `trajectreview-correcting`
- 結果要点:
  - `通常計測` で `2分30秒` 超から `3分` 近い収録を行っても app は落ちなかった
  - `撮影停止` 後に停止処理が完了し、session が止まらず残る事象は再現しなかった
  - status card の `経過時間` は停止要求時点で凍結し、その後に増え続けなかった
  - したがって `1min15s` 前後の `OOM` と、停止後 finalize hang の両方について、短中時間帯の主導線は改善を確認できた
- 未完:
  - `10min` 連続収録での keep-awake 維持と finalize 完了は未確認
  - そのため `MRL-2S` と `mRL-2S.1` / `mRL-2S.2` はまだ `active`
- evidence path:
  - `kisaragi-db/--exsams/prj-kisaragi_0002/device-debug/20260331-stop-hang/`

### correcting batch 記録テンプレート

- batch id: `correcting-batch-YYYYMMDD-01`
- 実施日時:
- 実施者: `admin`
- 端末 / 環境:
- 対象 `MRL` / `mRL`:
  - `MRL-1`
  - `MRL-2`
- 結果: `ready / active / p-done / i-pass / fail`
- fail の時の要点:
- evidence path:

## modeling batch 定義

- 対象 `MRL`:
  - `MRL-3`
  - `MRL-4`
  - `MRL-5`
  - `MRL-6`
  - `MRL-7`
- 対象 `mRL`:
  - `mRL-3.1` から `mRL-3.3`
  - `mRL-4.1` から `mRL-4.3`
  - `mRL-5.1`
  - `mRL-6.1` から `mRL-6.2`
  - `mRL-7.1` から `mRL-7.2`
- admin 操作観点:
  - [da3_colab_evid_runbook.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\modeling\da3_colab_evid_runbook.md) を fresh runtime から実行し、bootstrap UX が再現可能である
  - `trajectreview-correcting` 由来の実 data を入力に、`DA3Metric-Large` から `3DGS` 系主空間モデル候補を smoke 生成できる
  - `trajectreview-modeling` で実 bundle を読み、request 元、input directory、result directory を含む `colab_job_request.json` を生成できる
  - `Google Drive` directory 指定で `Colab` route の入力位置を決められる
  - waiting ring、現在段階、`job_status.json` の更新は `MRL-3.3` 以降の未達項目として残す
  - `MRL-5` は 10s 前後の整った実動画から `multi-frame` densify で粗い再現モデルを得る段とし、route 比較本体には含めない

### modeling batch 記録テンプレート

- batch id: `modeling-batch-YYYYMMDD-01`
- 実施日時:
- 実施者: `admin`
- 端末 / 環境:
- 対象 `MRL` / `mRL`:
  - `MRL-3`
  - `MRL-4`
  - `MRL-5`
  - `MRL-6`
  - `MRL-7`
- 結果: `ready / active / p-done / i-pass / fail`
- fail の時の要点:
- evidence path:

## 2026-03-29 modeling bootstrap candidate evidence

- 対象 gate:
  - `MRL-3`
  - `mRL-3.2`
  - `MRL-4`
  - `mRL-4.2`
- 実施環境:
  - `Google Colab`
  - `T4`
- 結果要点:
  - `DA3Metric-Large` `Colab bootstrap` は blank workspace から `準備確認 1` から `Step 4` まで通過した
  - `summary.json`、`depth_preview.png`、`depth_raw.npy` が生成された
  - `prediction.conf`、`intrinsics`、`extrinsics` は `None` を許容し、single-frame の end-to-end 完了を確認した
  - `HF_TOKEN` warning は public model download の範囲では blocker ではなかった
  - `MRL-5` の `multi-frame` densify、route 比較や採用固定はこの bootstrap candidate には含めない
- evidence path:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/da3_colab_evid_runbook.md`

## 2026-03-29 correcting batch `MRL-1` と `MRL-2` close evidence

- 対象 gate:
  - `MRL-1`
  - `mRL-1.1` から `mRL-1.3`
  - `MRL-2`
  - `mRL-2.1` から `mRL-2.3`
- 実施者:
  - `admin`
- 判定:
  - この batch は `correcting` の実データ取得、`data-check`、`Google Drive` 転送、`SpaceReconstruction` handoff bundle 生成までを根拠に `p-done`
- 結果要点:
  - `trajectreview-correcting` で実 session 記録、停止、session 保存が通っている
  - `data-check` に readiness、blocker、recommended correction が出る
  - `sensor_quality.json`、`session_package.json`、`space_handoff_manifest.json`、`frame_pose_index.csv`、`camera_calibration_summary.json` が実 session から生成されている
  - calibration capture 診断と intrinsics 実収集の candidate evidence がそろっている
  - `Google Drive` 転送先選択、zip 転送、既存 data 再転送の UX が candidate evidence として確認されている
  - 転送済み data が `MRL-4` の `DA3Metric-Large` `3DGS` smoke 生成に実際に使われており、`correcting -> modeling` の handoff 実績がある
  - `session_package.json` と `space_handoff_manifest.json` により `SpaceReconstruction` 着手可否を後段へ渡せている
- 補足:
  - この batch は `p-done` 判定であり、admin `UX check 完了` を伴う `i-pass` ではない
  - request 起点 modeling、waiting ring、remote result import、reviewing viewer は `MRL-3` 以降と後続 `MRL-**` に別置きした
- evidence path:
  - `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-method.md`
  - `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/ux-b2t-hypo.md`
  - `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-evidence.md`

## 2026-03-29 modeling preflight close evidence

- 対象 gate:
  - `MRL-3`
  - `mRL-3.1`
  - `mRL-3.2`
- 実施者:
  - `admin`
- 判定:
  - この段は `p-done`
- 結果要点:
  - `trajectreview-modeling` 側で実 bundle snapshot 読込と request preflight 生成の candidate evidence がある
  - `Google Drive` directory bootstrap と unzip / 配置正規化は runbook の採用手順で実行実績がある
  - waiting ring、`job_status.json`、download URL は `mRL-3.3` と後続 `MRL-**` に残した
- evidence path:
  - `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/ux-b2t-hypo.md`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/da3_colab_evid_runbook.md`

## 2026-03-29 `MRL-4` `3DGS` smoke candidate evidence

- 対象 gate:
  - `MRL-4`
  - `mRL-4.2`
  - `mRL-4.3`
- 実施者:
  - `admin`
- 実施環境:
  - `Google Colab`
  - `T4`
  - notebook evidence: `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/evidence/trajectreview_modeling_20260329_gpu-evidence.ipynb`
- 入力 data:
  - `trajectreview-correcting` で取得した `session-20260328-103250.zip`
  - `Google Drive` shortcut 配下 `trajectreview/correcting/session-20260328-103250.zip`
- 結果要点:
  - `correcting` 実 data から `DA3Metric-Large` single-frame depth 推論が通過した
  - `arcore_pose.jsonl`、`frame_pose_index.csv`、`camera_calibration_summary.json`、`images/` を使い、depth の world back-projection smoke を確認した
  - `world_points_smoke.npy` と `world_points_smoke.ply` を生成できた
  - `gsplat` install / import / callable 確認を通し、`gsplat.rasterization` を `cuda` 上で返せた
  - `gsplat_render_smoke.png`、`gs_model_smoke.json`、`space_quality_smoke.json`、`space_package_smoke.json` を生成できた
  - `gs_model.contract.json`、`space_quality.contract.json`、`space_package.contract.json` を生成し、smoke artifact を contract 名へ寄せられた
  - この段の `MRL-4 p-done` 候補判断は、「ある程度整った correcting 実 data から `3DGS` 系主空間モデル候補を再現でき、admin が生成 artifact を取得できること」を基準に置く
  - `trajectreview-modeling` 本体への正式統合と `multi-frame` / `multi-route` 比較は、この candidate evidence の必須条件から分離し、後続 gate へ送る
- 主要 artifact:
  - `depth_raw.npy`
  - `depth_preview.png`
  - `world_points_smoke.npy`
  - `world_points_smoke.ply`
  - `gsplat_render_smoke.png`
  - `gs_model_smoke.json`
  - `space_quality_smoke.json`
  - `space_package_smoke.json`
  - `gs_model.contract.json`
  - `space_quality.contract.json`
  - `space_package.contract.json`
- local downloaded evidence:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/evidence/da3_smoke_v05/`
- evidence path:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/da3_colab_evid_runbook.md`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/evidence/trajectreview_modeling_20260329_gpu-evidence.ipynb`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/evidence/da3_smoke_v05/`

## 2026-03-29 modeling evidence bundle close evidence

- 対象 gate:
  - `MRL-4`
  - `mRL-4.3`
- 実施者:
  - `admin`
- 判定:
  - この段は `p-done` 根拠を補強する evidence close
- 結果要点:
  - `Google Colab` 実行 notebook evidence を product 側へ保存済みである
  - local downloaded smoke artifact 一式を product 側 evidence へ保存済みである
  - admin が後で local 可視化や再確認を行うための参照 bundle が揃っている
- evidence path:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/evidence/trajectreview_modeling_20260329_gpu-evidence.ipynb`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/evidence/da3_smoke_v05/`

## 2026-03-30 `mRL-7.1` multi-frame point-fusion close evidence

- 対象 gate:
  - `mRL-7.1`
- 実施者:
  - `admin`
- 実施環境:
  - `Google Colab`
  - `T4`
- 入力 data:
  - `trajectreview-correcting` で取得した `session-20260328-103250.zip`
  - `Google Drive` shortcut 配下 `trajectreview/correcting/session-20260328-103250.zip`
- 判定:
  - `mRL-7.1` は `p-done`
  - `MRL-7` 全体は `active` を維持する
- 結果要点:
  - fresh runtime から input zip を再展開し、`session_package.json`、`frame_pose_index.csv`、`camera_calibration_summary.json`、`images/` を再発見できた
  - `frame_pose_index.csv` の実列を基準に `aligned_frame_count = 182` を確認できた
  - この session の最長連続 window は約 `3.95s` であり、`10s` 理想値には届かないため、今回の `mRL-7.1` は実 session の最長連続 window を正として進めた
  - sampled `12 frame` に対して `DA3Metric-Large` depth batch を `cuda` で完走し、`failed_frames = 0` を確認できた
  - world fusion では `11 frame` を主 `ARCore` 空間へ戻し、`1 frame` は skip した
  - `world_points_multiframe.npy`、`world_points_multiframe.ply`、`world_fusion_summary.json` を保存できた
  - `total_points = 3696` の multi-frame 点群を `world_points_multiframe_preview.png` と `mrl7_closeout_summary.json` へ閉じ、`candidate-visible-proof` を保存できた
  - ここでは `multi-frame` sampling、depth batch、world fusion、preview closeout までを `mRL-7.1` の成立範囲とする
  - `PLY` viewer での目視確認と、人軌跡重畳を含む `TraceCore` 最小表示は `mRL-7.2` へ送る
- 主要 artifact:
  - `mrl7_window_probe.json`
  - `depth_batch_manifest.json`
  - `world_points_multiframe.npy`
  - `world_points_multiframe.ply`
  - `world_fusion_summary.json`
  - `world_points_multiframe_preview.png`
  - `mrl7_closeout_summary.json`
- evidence path:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/da3_colab_evid_runbook.md`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/evidence/mrl7_multiframe_viewer_bundle/`

## 2026-03-30 `mRL-7.2` gaussian short-optimization candidate evidence

- 対象 gate:
  - `mRL-7.2`
- 実施者:
  - `admin`
- 実施環境:
  - `Google Colab`
  - `T4`
- 判定:
  - `mRL-7.2` は `p-done`
  - `MRL-7` 全体も、この段の到達範囲では `p-done`
- 結果要点:
  - multi-frame point cloud から最小 gaussian parameter を初期化し、`means`、`scales`、`quats`、`opacities`、`colors` を tensor として保持できた
  - `gsplat.rasterization` の forward / backward が通り、`1 step` probe は `backward_ok = true` で通過した
  - 続けて `20 step` の短い optimization が通り、loss は `0.18226878345012665` から `0.035895735025405884` まで低下した
  - `gaussian_params_init.pt`、`gaussian_params_optim20.pt`、`gaussian_render_init.png`、`gaussian_render_optim20.png`、`gaussian_optim20_summary.json` を保存できた
  - さらに `500 step` 版では、loss は `0.18226878345012665` から `0.01154774148017168` まで低下した
  - `2500 step` 版では、loss は `0.18226878345012665` から `0.009165632538497448` まで低下した
  - admin の目視で [gaussian_render_optim500.png](/Users/tetsuya/kisaragi/kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/evidence/gaussian_optim500_bundle/gaussian_render_optim500.png) と [gaussian_render_optim2500.png](/Users/tetsuya/kisaragi/kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/evidence/gaussian_optim2500_bundle/gaussian_render_optim2500.png) は「かなり再現されている」「取得背景に近い構図」と確認できた
  - admin の目視で `gaussian_render_optim20.png` は取得背景に近い構図へ改善を確認できた
  - この段では「multi-frame point cloud から gaussian parameter を初期化し、短い optimization で見た目改善を確認する」を `mRL-7.2` の成立範囲とする
  - viewer で読む正式 gaussian scene 形式の固定、長時間 optimization、multi-view optimization の拡張は後続 `MRL-**` へ送る
- 主要 artifact:
  - `gaussian_init_summary.json`
  - `gaussian_one_step_probe.json`
  - `gaussian_params_init.pt`
  - `gaussian_params_optim20.pt`
  - `gaussian_render_init.png`
  - `gaussian_render_optim20.png`
  - `gaussian_optim20_summary.json`
- evidence path:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/evidence/gaussian_short_optim_bundle/`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/evidence/gaussian_optim500_bundle/`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/evidence/gaussian_optim2500_bundle/`

## reviewing batch 定義

- 対象 `MRL`:
  - `MRL-**`
- 対象 `mRL`:
  - `mRL-**.4`
  - `mRL-**.5`
- admin 操作観点:
  - `trajectreview-reviewing` で実 `ReviewArtifact` を読み、verify / review 状態を確認できる
  - same-time highlight と `attention point` 操作ができる
  - 統合 app から correcting、modeling、reviewing の流れと担当境界を確認できる
  - app 間の切り分け理由を UI 上で読める

### reviewing batch 記録テンプレート

- batch id: `reviewing-batch-YYYYMMDD-01`
- 実施日時:
- 実施者: `admin`
- 端末 / 環境:
- 対象 `MRL` / `mRL`:
  - `MRL-**`
- 結果: `ready / active / p-done / i-pass / fail`
- fail の時の要点:
- evidence path:

## 2026-03-26 `MRL-2` candidate evidence

- 対象 gate:
  - `MRL-2`
  - `mRL-2.1` から `mRL-2.3`
- UX 観点:
  - `trajectreview-correcting` で `現場撮影データ保存を開始` と `現場撮影データ保存を停止` が動く
  - 1 つ目の block で `データ保存先ディレクトリ選択` から同期先 folder を選び、その保持状態を app 内で確認できる
  - camera preview は上部固定で見え続け、下部 scroll で 4 block を順に操作できる
  - 記録開始や停止などの状態文は preview 直下の status card に出て、下部操作 block を塞がない
  - 記録停止後に同じ app 内で `data-check` 欄へ `診断進行可`、`modeling 着手可`、`blocker`、`補正指示` が表示される
  - `data-check` 欄へ `camera intrinsics 対応率`、`lens distortion 対応率`、`calibration frame 数` が表示される
  - `arcore_pose.jsonl` は `sessionId`、`recordIndex`、`captureTimestampNs`、nested `pose` / `imageIntrinsics` / `textureIntrinsics` / `lensDistortion` を持つ
  - `camera_calibration_summary.json` は `intrinsicsModeCandidate`、`recommendedModelingRoutes`、`warnings`、`blockers` を持つ
  - `frame_pose_index.csv` は `image_file_name`、`pose_record_index`、`time_delta_ms` を持ち、`images/` と `arcore_pose.jsonl` を再リンクできる
  - 3 つ目の block で `data-check` により、最新 session から結果を再計算できる
- 実装 / test 観点:
  - JVM unit test:
    - `:correcting:testDebugUnitTest`
  - build / install:
    - `:correcting:assembleDebug`
    - `:correcting:installDebug`
  - device verification:
    - short harness を `com.reviework.correcting` 向けに実行し、`session-20260326-193340/trajectreview/` 配下へ derived artifact が生成されることを確認した
- 実 session 観点:
  - `sensor_quality.json`
  - `session_package.json`
  - `space_handoff_manifest.json`
  - `frame_pose_index.csv`
  - `camera_calibration_summary.json`
  - `member_identity_map.json`
  - 不十分な収録では `video.mp4 が不足しています` のような blocker と correction guidance を返す
- 主要 evidence:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/CorrectingDataCheckService.kt`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/MainActivity.kt`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/res/layout/activity_main.xml`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/test/java/com/isensorium/app/CorrectingDataCheckServiceSmokeTest.java`

## 2026-03-27 `MRL-3` candidate evidence

- 対象 gate:
  - `MRL-3`
  - `mRL-3.1` から `mRL-3.3`
- UX 観点:
  - preview 直下の状態表示には `現場の風景と経路を記録します。1. 条件設定⇒2. 収録⇒3. 転送` が表示される
  - `端末保存先` が未設定の間は `Data収録開始` が非活性で、`端末保存先：未設定` が表示される
  - `転送先を選択` 直下の小さい補助表示は出ず、転送条件は `転送実行` 直下の comment に集約される
  - 1 つ目の block は見出しが `1. 条件設定` で、1 行目が `Sampling条件` / `端末保存先`、2 行目が保存先状態表示、3 行目が `送信Dataset` / `Data名称変更` の 2 列になる
  - 2 つ目の block は見出しが `2. 収録` で、1 行目が記録開始 / 停止 toggle、2 行目が `品質確認` / `転送Data選択` の 2 列になる
  - 3 つ目の block は 1 行目の `転送先を選択` / `転送実行` の 2 列、その下の転送状態表示で構成される
- `端末保存先` により、`Storage Access Framework` からスマホ内の同期先 folder を選べる
- 収録停止後は、まず raw session を `端末保存先` へ保存し、その後に `data-check` を走らせる
- 収録停止後の自動 `data-check` と端末保存先同期では、待機文言を出して非活性理由を明示する
- 待機表示は `Data収録開始` 直下へ寄せ、短文 + ring / bar + 次の収録可否の 1 文で示す
- `品質確認` の詳細は popup へ寄せ、メイン画面には閾値未満の項目名だけを残す
- `端末保存先` 同期中は session 詳細を縮退し、`Session: <session_id>` と `品質確認OK` のみを残す
- shared camera route の `ARCore` sampling は `arCoreIntervalMs` に従い、画像抽出は pose 対応 frame 優先に絞る
- `品質確認` は lightweight 判定を優先し、`frame画像群` は転送で実際に要求された時だけ生成する
- `転送実行` 中の comment と waiting ring は `転送実行` button 直下に表示し、recording 側 indicator と分離する
- `trackingState` warning は初期 warmup の少数 frame を許容し、non-tracking 率が高い時だけ `▲` と案内文を返す
- `転送Data選択` と `Data名称変更` の一覧表示前には保存済み data の lightweight `品質確認` を再実行し、`▲` を更新する
- `▲` は blocker または閾値超え warning がある時だけ付け、軽微な `coverage < 1.0` や `images/` 未生成だけでは付けない
- 保存済み data 一覧の lightweight `品質確認` では `images/` 未生成を `▲` 原因に含めない
- `corecamera_shared_camera_trial` route の calibration 診断は、`captureDiagnostics` が実データで立つことを追加確認対象にする
- `送信Dataset` popup で送信 group を選べる
- `転送Data選択` popup で `data-check` 済み data を複数選べ、懸念がある data は `▲` 付きで見える
- `転送Data選択` popup は `Data名称変更` popup と同系統の button 一覧 UI へ揃え、取得日時、長さ、`▲` を button 外の小テキストで確認できる
- `Data名称変更` popup に保存済み data の取得日時と長さが出て、名称変更できる
- `Data名称変更` popup はメイン画面寄りの button 一覧で区切りが見え、rename 後も親 popup に残る
- popup 最上段に `戻る`、次行に `OFF：名称変更、ON：削除モード` toggle があり、ON かつ選択済み時だけ `削除実行` が活性になる
- `転送先を選択` popup で `Google Drive` URL を保持し、`保存先fileを設定する` から Android 標準保存画面経由で保存場所と zip file 名を選べる。端末 storage が先に見える時は user が provider を `Google Drive` へ切り替える
- `転送実行` は `転送Data` と `Google Drive` 転送先がそろうと有効になり、直下コメントで設定済み / 未設定を読める
- `Google Drive` 転送先 file は毎回 user が選び直す前提とし、前回転送の document grant を再利用しない
- zip 保存先 file 名の既定値は、名称未指定なら `trajectreview-correcting-session-YYYYMMDD-HHMMSS.zip`、data 名を使う時は `<data-name>-session-YYYYMMDD-HHMMSS.zip` とする
- 既存の `data-check` 済み session を選んだ時は、その session を再転送できる
- 記録停止後は `data-check` が自動実行され、新しい記録開始時には `data-check` 成功回数が `0` に戻る
- `poseCoverageRatio` は `ARCore` の期待 sample 数基準で算出し、`video frame` 数に引きずられない
- スマホ内保存先は選択した folder 直下の `<session_id>/` とし、`data-check` 後に同期する
- `Google Drive` 転送先は選択した保存場所に zip を作成し、選択した group だけを zip に含める。複数 data を選んだ時は zip 内に複数 session directory を含める
- 実装 / test 観点:
  - JVM unit test:
    - `:correcting:testDebugUnitTest`
  - build / install:
    - `:correcting:assembleDebug`
    - `:correcting:installDebug`
- 制約:
  - `Google Drive` app または provider が端末上で選択可能である必要がある
  - そのため `MRL-3` は admin 実機 UX check 前の `candidate evidence` として扱う
- 主要 evidence:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/MainActivity.kt`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/res/layout/activity_main.xml`

## 2026-03-25 candidate evidence

- 対象 gate:
  - `MRL-2` から `MRL-5`
  - `mRL-2.1` から `mRL-5.3`
- UX 観点:
  - `Next Action + Thin Status` で diagnose、run、verify、review を段階別に読める
  - 同時刻ハイライト、`attention point`、不確実区間、成果物境界を UI 契約として保持できる
  - 4 分担の handoff contract を code と文書の両方で読める
- 実装 / test 観点:
  - Python unittest: `test_session_parser.py`、`test_project_contracts.py`
  - Android unit test: `ReviewScreenControllerTest.kt`
  - script 実行:
    - `run_python_tests.ps1`
    - `run_android_unit_tests.ps1`
- routing 観点:
  - raw build cache、binary results、pycache は `kisaragi-db/--exsams/prj-kisaragi_0002/` に出力する
  - 要約 report と summary は `kisaragi-db/--devs/--testlogs/prj-kisaragi_0002/` に出力する
- 主要 evidence:
  - `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/ux-b2t-hypo.md`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_project_contracts.py`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/scripts/run_python_tests.ps1`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/scripts/run_android_unit_tests.ps1`

## 残作業

- `correcting` の `現場記録 -> intake -> diagnose -> correction export` を 1 app 内で閉じる
- `modeling` の `Colab` handoff と remote result import を実装する
- `reviewing` の実 `ReviewArtifact` viewer と same-time highlight 操作を実装する
- 統合 app の end-to-end と、本機能 `pass` の再 closeout を実施する

## 2026-03-25 latest exsams output recheck

- 対象:
  - `run_python_tests.ps1`
  - `run_android_unit_tests.ps1`
- 結果:
  - Python unittest: pass
  - Android unit test: pass
- 最新 raw output 確認:
  - Python: `--exsams/prj-kisaragi_0002/python-pycache/.../test_project_contracts.cpython-314.pyc` と `test_session_parser.cpython-314.pyc` が `2026-03-25 19:12:07` に更新された
  - Android: `--exsams/prj-kisaragi_0002/gradle-user-home/daemon/8.10.2/registry.bin.lock` などの Gradle raw artifact が `2026-03-25 19:12:08` に更新された
- 判定: `prj-kisaragi_0002` は、最も最近実施した test の raw data を `--exsams` 側へ出力できる

## 2026-03-25 `MRL-2` candidate evidence

- 対象 gate:
  - `MRL-2`
  - `mRL-2.1`
- UX 観点:
  - app 起動直後に `入力セッションを選択` が `Next Action` として見える
  - `Extraction` card で抽出元、抽出先、`ready_for_diagnose`、欠落入力、quality 数値を 1 画面で読める
  - `admin-mrl-test-method.md` を、抽出 UI を含む最小操作手順へ更新した
- 実装 / test 観点:
  - Python unittest: `test_session_parser.py`
  - Android unit test: `ReviewScreenControllerTest.kt`、`ISensoriumExtractionServiceTest.kt`
  - script 実行:
    - `run_python_tests.ps1`
    - `run_android_unit_tests.ps1`
  - device install:
    - `gradlew.bat installDebug`
- 抽出 bundle 観点:
  - raw file は `session_id/isensorium/`
  - 派生 file は `session_id/trajectreview/`
  - `sensor_quality.json` に時刻整列 delta、completeness score、pose coverage ratio が入る
- 主要 evidence:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/ISensoriumExtractionService.kt`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ISensoriumExtractionServiceTest.kt`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py`
  - `kisaragi-db/--devs/--testlogs/prj-kisaragi_0002/reports/python-unittest-summary.md`
  - `kisaragi-db/--devs/--testlogs/prj-kisaragi_0002/reports/android-test-summary.md`

## 2026-03-25 `MRL-3` candidate evidence

- 対象 gate:
  - `MRL-3`
  - `mRL-3.3`
- UX 観点:
  - 抽出結果画面で `ready_for_space_reconstruction` と blocker を確認できる
  - raw bundle に主カメラ動画を保持したまま、後段着手判断を 1 画面で行える
- 実装 / test 観点:
  - Python unittest: `test_session_parser.py`、`test_project_contracts.py`
  - Android unit test: `ISensoriumExtractionServiceTest.kt`
  - device install:
    - `gradlew.bat installDebug`
- handoff artifact 観点:
  - `session_package.json` が timebase、source file、stream count、quality 指標、required / optional input を保持する
  - `space_handoff_manifest.json` が `ready_for_space_reconstruction`、blocker、consumed artifact、next action を保持する
  - `video.mp4` と `video_events.jsonl` を raw bundle に保持する
- 主要 evidence:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/ISensoriumExtractionService.kt`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/python/session_parser.py`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ISensoriumExtractionServiceTest.kt`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py`
- 
## 2026-03-26 `MRL-**` support candidate evidence

- 対象 gate:
  - `MRL-**`
  - `mRL-**.5`
- UX 観点:
  - `trajectreview-correcting`、`trajectreview-modeling`、`trajectreview-reviewing`、統合 app がそれぞれ自分の役割だけを主表示にする
  - 統合 app は `correcting / modeling / reviewing` を 1 画面で俯瞰できる
- 実装 / test 観点:
  - Android unit test: `ReviewScreenControllerTest.kt`
  - build:
    - `:app:testDebugUnitTest`
    - `:correcting:assembleDebug`
    - `:modeling:assembleDebug`
    - `:reviewing:assembleDebug`
  - device install:
    - `:app:installDebug`
    - `:correcting:installDebug`
    - `:modeling:installDebug`
    - `:reviewing:installDebug`
- 主要 evidence:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/settings.gradle.kts`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/AppWorkflowProfile.kt`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/MainActivity.kt`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt`

## 2026-03-26 `MRL-4` candidate evidence

- 対象 gate:
  - `MRL-4`
  - `mRL-4.1` から `mRL-4.2`
- UX 観点:
  - `correcting` と統合 app は抽出した実 bundle を再読込して実データ状態を表示する
  - `modeling` は `Colab` account 未取得でも local sample model と `colab_job_request.json` を生成する
  - `reviewing` と統合 app は `local_model_summary.json` と `review_artifact_stub.json` を読んで verify / review 状態を組み立てる
- 実装 / test 観点:
  - Android unit test:
    - `WorkflowBundleServiceTest.kt`
    - `LocalModelingServiceTest.kt`
    - `ReviewScreenControllerTest.kt`
  - build / install:
    - `:app:testDebugUnitTest`
    - `:correcting:assembleDebug`
    - `:modeling:assembleDebug`
    - `:reviewing:assembleDebug`
    - `:app:installDebug`
    - `:correcting:installDebug`
    - `:modeling:installDebug`
    - `:reviewing:installDebug`
- 生成 artifact 観点:
  - `local_model_summary.json`
  - `colab_job_request.json`
  - `review_artifact_stub.json`
  - `modeling_handoff_manifest.json`
- 主要 evidence:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/WorkflowBundleService.kt`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/LocalModelingService.kt`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/WorkflowBundleServiceTest.kt`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/LocalModelingServiceTest.kt`
