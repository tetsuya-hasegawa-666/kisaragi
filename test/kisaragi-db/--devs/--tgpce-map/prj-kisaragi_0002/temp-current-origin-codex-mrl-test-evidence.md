# codex-mrl-test-evidence

## 目的文

この文書は `prj-kisaragi_0002` の `MRL` / `mRL` closeout 記録を残す正本とする。

## 記録ルール

- `MRL` または `mRL` が `pass` になったら 1 entry を追加する
- entry には issue、cause、resolution、recurrence prevention、remaining work、evidence path を含める
- planning 基線の再作成や大きな再開判断も entry として残してよい
- `2026-03-29` の再編以後は、現行 gate を `correcting` phase の `MRL-1` と `MRL-2`、`modeling` phase の `MRL-3` から `MRL-7`、および後続 `MRL-**` で読む。再編前 entry は必要に応じて現行対応を本文へ補記する

## Entries

- record date: `2026-04-11`
  target MRL: `MRL-10`
  target mRL: `support-MRL-S1`, `mRL-10.5`
  gate change: `active directory/reference stabilization started`
  issue: `#11-1` では `merged_dir`、`final_outputs_merged_dir`、`final_outputs_diagnostics_dir`、`final_outputs_manifests_dir`、`stage_11_2_dir`、`stage_11_3_dir` に同系統 file が重複しやすく、さらに `#11-1` が `#10-1` の current contract を旧前提で読んだ時に access failure や reference drift を起こしやすかった
  cause: graph / merge の final access contract が `pipeline_root/merged` と `final_outputs/*` の混在で曖昧なまま増築され、producer と consumer の間に `どこが canonical 実体か` を明示する stage-level handoff manifest がなかった
  resolution: `HAUB`、`project-truth`、`resume-startup-plan.md`、`da3_ngl_runbook_design_contract.md` を更新し、temporary objective を `support-MRL-S1` として明記したうえで、`#10-1` と `#11-1` の final access contract を `final_outputs/#10-1/{re_access,persist_only}`、`final_outputs/#11-1/{re_access,persist_only}` へ再編した。続けて stage 管理 file を `#08-3=chunk_execution_plan.csv`、`#10-1=graph_gate_report.json`、`#11-1=merge_output_report.json` の 1 file へ統合し、runtime workspace 名も `runtime_workspace/` に固定した。`#11-1/persist_only/manifests/` は `merge_input_report.json` の 1 file へ集約し、input / anchor manifest の多重 copy をやめた
  recurrence prevention: 以後 `#08-3`、`#10-1`、`#11-1` の参照変更では、runtime pointer を見ても relation 管理は `HAUB` に戻して判断する。workspace directory 名は意味語を優先して `runtime_workspace` に固定し、`HAUB` の `Increpose Path Handoff Matrix`、source test、path contract probe を同じ task で更新・実行する
  remaining work: `support-MRL-S1` は temporary objective なので、admin が truth / HAUB 上の配置最適化を目視確認し、不要と判断するまで残す。`BLK-1`、`BLK-2`、`BLK-5`、`BLK-10` は引き続き open である
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/hi-ai-unified-blueprint.md`, `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/project-truth.md`, `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_runbook_design_contract.md`, `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_increpose_sources/cells/10_01.py`, `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_increpose_sources/cells/11_01.py`

- record date: `2026-04-11`
  target MRL: `MRL-10`
  target mRL: `mRL-10.5`
  gate change: `active recurrence-prevention strengthened`
  issue: `da3_ngl_increpose_RB` は canonical pair へ切り替えた後も、directory 定義、生成物出力先、reader 側参照のずれが発生しやすく、shared worklog にしか残っていない修復知識へ依存すると再発防止にならなかった
  cause: `#8-3`、`#8-5`、`#8-9`、`#10-1`、`#11-1`、`#11-2` の artifact handoff は notebook cell をまたいでおり、producer / consumer / canonical path の authoritative contract と機械検査が永続文書へ十分固定されていなかった
  resolution: [hi-ai-unified-blueprint.md](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/hi-ai-unified-blueprint.md) に `Increpose Path Handoff Matrix` を恒久 contract として明記し、[da3_increpose_path_contract_probe.py](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--testcode/prj-kisaragi_0002/da3_increpose_path_contract_probe.py) と [test_da3_increpose_path_contract_probe.py](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_da3_increpose_path_contract_probe.py)、[test_da3_increpose_sources.py](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_da3_increpose_sources.py) を使う再検査 route を永続化した。`2026-04-11` の再検査では `critical_rule_failures=[]`、`haub_contract_failures=[]`、`6 tests OK` を確認した
  recurrence prevention: 今後 `da3_ngl_increpose_RB` の script / notebook source を編集する task では、`HAUB` handoff matrix 更新、probe 実行、関連 unittest 実行を同じ task で必須にする。shared worklog は判断の起点には使ってよいが、永続 contract の保持場所にしない
  remaining work: path / reference 整合は現時点で clean だが、`BLK-1` の merge quality と `BLK-5` の correcting 長時間実収録安定化は未解消であり、`mRL-10.4` と `MRL-2S` の主 blocker は残る
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/hi-ai-unified-blueprint.md`, `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/da3_increpose_path_contract_probe.py`, `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_da3_increpose_path_contract_probe.py`, `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_da3_increpose_sources.py`

- record date: `2026-04-11`
  target MRL: `MRL-10`
  target mRL: `mRL-10.5`
  gate change: `active authoritative recheck completed`
  issue: shared worklog の `v129` で batch/chunk 二重ネスト起因の `pred_extrinsics_not_found` 修復は記録されていたが、`batch_work_dir` と `chunk_out_dir` の scope 分離、および `chunk_0005_*` のような legacy suffix dir を reader が吸収する契約が恒久文書へ十分固定されていなかった
  cause: source と test は更新済みでも、`HAUB` current_state、path handoff matrix、resume、runbook 設計契約へ同じ detail を揃えていなければ、shared worklog を見ない再開時に directory 解釈を誤読できる余地が残っていた
  resolution: [hi-ai-unified-blueprint.md](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/hi-ai-unified-blueprint.md) の `modeling` current_state と `Increpose Path Handoff Matrix` に batch/chunk scope 分離と legacy suffix fallback を追記し、[resume-startup-plan.md](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/resume-startup-plan.md) と [da3_ngl_runbook_design_contract.md](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_runbook_design_contract.md) も同期した。あわせて `authoritative-doc-guard` で再確認し、shared worklog は照合元に使っても正本にはしない運用を再検証した
  recurrence prevention: `da3_ngl_increpose_RB` の script / notebook source を編集する時は、`AGENTS.md`、`project-truth.md`、`HAUB` を先に確認し、編集後は `HAUB` matrix、runbook 設計契約、必要なら resume / closeout まで同 task で見直す。shared worklog は差分の手掛かりに限定し、恒久 contract の保持先にしない
  remaining work: source / pair / authority docs の参照整合は再検査でそろったが、`BLK-1` の multi-frame merge quality と `BLK-5` の `3min` 実収録安定化は未解消のままである
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_runbook_design_contract.md`, `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/hi-ai-unified-blueprint.md`, `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/resume-startup-plan.md`

- record date: `2026-04-08`
  target MRL: `MRL-2R`、`MRL-10`
  target mRL: `mRL-2R.3`、`mRL-10.5c`
  gate change: `active documentation contract expanded`
  issue: `HAUB` の後段一覧表は実質的に `modeling` 用 `DA3` inventory へ寄っており、`correcting` 側の local product script / source は同じ思想で追えなかった。このままだと Colab で起きた不整合を防ぐ inventory 運用を `correcting` 側へ横展開できず、local product の script 管理が chat 依存のまま残る
  cause: `modeling` 側は `da3_runbook_sources/`、design contract、source inventory がそろっていた一方、`correcting` 側には `HAUB` から辿れる inventory 正本がなく、PowerShell helper と Kotlin orchestration / handoff source の責務面が一覧化されていなかった
  resolution: [correcting_script_manifest.json](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/correcting_script_manifest.json) と [build_correcting_inventory.py](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/build_correcting_inventory.py) を追加し、[correcting_script_source_inventory.md](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/correcting_script_source_inventory.md) を生成する形へ切り替えた。あわせて [hi-ai-unified-blueprint.md](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/hi-ai-unified-blueprint.md) の一覧表を `correcting` 用 / `modeling` 用の 2 本へ分離し、admin 手順、resume、runbook 設計契約も同じ inventory 参照へ更新した
  recurrence prevention: local product script / source を更新した時は、`correcting_script_manifest.json` と `correcting_script_source_inventory.md` を同じ task で更新する。`modeling` だけに inventory 規律を閉じず、`HAUB` の入口表も phase ごとに分離したまま維持する
  remaining work: `correcting` 側 inventory は現状をありのまま記載した段階であり、責務再編や粒度最適化は後段で行う。`BLK-1`、`BLK-2`、`BLK-10` は引き続き `big-open` のまま残る
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/correcting_script_source_inventory.md`, `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/hi-ai-unified-blueprint.md`

- record date: `2026-04-07`
  target MRL: `MRL-10`
  target mRL: `mRL-10.5`、`mRL-10.5b`、`mRL-10.5c`
  gate change: `active`
  issue: 添付 notebook と現行 canonical pair は block 数こそそろっていたが、内部では `repo bootstrap`、`context load`、helper 定義、wrapper source が notebook 内へ繰り返し埋め込まれていた。このままだと `mRL-10.5` の「拡張に開き修正に閉じる」目的に反し、局所修正で閉じられない
  cause: これまでの runbook は pair そのものの可搬性を優先し、authoring 面の source 分離と docs 契約を後回しにしていた。結果として `#12-2` の wrapper のような重い実装が cell 内 string に閉じ込められ、再利用 helper も notebook 直編集依存になっていた
  resolution: [da3_ngl_runbook_design_contract.md](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_runbook_design_contract.md) を追加し、stage 責務、source-sync 対象、docs ID、変更ゲートを固定した。あわせて `da3_runbook_sources/sync_da3_runbook_sources.py` を追加し、`#5-1`、`#6-1`、`#12-2` を source file から canonical pair へ同期できる構成へ切り替える土台を作った。さらに [design-first-script-builder](/C:/Users/tetsuya/kisaragi/kisaragi-skills/design-first-script-builder/SKILL.md) を新設し、設計審査票、関数表、docs ID 契約を先に作る protocol を skill 化した
  recurrence prevention: runbook / notebook の再構成では、algorithm 修正の前に設計契約書、source-sync 面、`HAUB` の関数 / 変数一覧を同じ task で更新する。再出現する helper や generated wrapper を見つけた時は、cell を直接肥大化させず source file と同期 script へ逃がす
  remaining work: source-sync 対象はまだ一部であり、anchor / chunk plan / merge の重い stage までは未分離である。次は `#7`、`#9`、`#14` のうち再利用性が高い helper を同じ方式で局所 source 化し、pair と source のズレ検査も追加する必要がある。`BLK-1` と `BLK-2` は継続して `big-open` のまま残る
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_runbook_design_contract.md`

- record date: `2026-04-07`
  target MRL: `MRL-10`
  target mRL: `mRL-10.5`、`mRL-10.5a`、`mRL-10.5b`、`mRL-10.5c`
  gate change: `active`
  issue: [da3_ngl_prepose_RB.md](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_prepose_RB.md) は canonical pair として使い始めていたが、`HAUB` 上では `mRL-10.5` の意図が「runbook 構成そのものの gate」だと読めず、旧 `da3_colab_evid_runbook.md` 名や `Block 3-6` 記法も残っていた。このままだと、runbook 設計変更の意味が artifact algorithm の一部なのか、運用面の closeout なのかを後から追えない
  cause: `MRL-10` の実装を先に進める中で、runbook pair の正本切替、`#1`-`#17` への再構成、official API / CLI 基準統一、provenance 可視化、stage summary 可視化を同時に入れたが、その設計意図を `MRL` 表と closeout 記録へ十分に昇格していなかった
  resolution: [hi-ai-unified-blueprint.md](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/hi-ai-unified-blueprint.md) の `MRL-10` 対応表を更新し、`mRL-10.5` を canonical runbook pair 自体の設計 gate として明記した。あわせて旧 runbook 名と旧 block 記法を [da3_ngl_prepose_RB.md](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_prepose_RB.md) の `#1`-`#17` 基準へ置き換え、`mRL-10.5c` を追加して `extrinsics_w2c_arc.npy` provenance、anchor 以降の input / output summary、section と code cell 番号一致を canonical 条件へ含めた
  recurrence prevention: runbook 正本の名称、section 構成、admin 実行順、provenance 可視化、`.md/.ipynb` 同期のいずれかを変更した時は、同じ task で `HAUB` の `MRL-10.5` と `codex-mrl-test-evidence.md` を同時更新し、algorithm gate と runbook architecture gate を混在させない
  remaining work: `mRL-10.5` はまだ `active` であり、admin が fresh runtime から [da3_ngl_prepose_RB.ipynb](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_prepose_RB.ipynb) の `#1`-`#17` を使って clean bootstrap し、stage summary と provenance 表示が運用上も十分読めるかを batch で確認する必要がある。加えて `BLK-1` の merge 品質問題は別途残る
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_prepose_RB.md`

- record date: `2026-04-02`
  target MRL: `MRL-10`
  target mRL: `mRL-10.1`、`mRL-10.2`、`mRL-10.3`
  gate change: `active`
  issue: `correcting` 側の canonical image が `90度右回転` 済み upright JPEG に変わる前提が固まった一方、main runbook pair と計画文書はまだ `MRL-11` を別立てし、`Colab` 側で orientation をどう扱うかが一貫していなかった。さらに添付 notebook の `DA3NESTED-GIANT-LARGE-1.1` living spec と `debug_gs_readback` 系証跡も、main canonical route へ完全には吸収できていなかった
  cause: これまでの runbook は raw 向き由来の回転論点を `viewer 側の後処理` に寄せており、`frame_record.jsonl`、upright image、legacy intrinsics 補正、manifest 記録を 1 つの canonical contract に束ね切れていなかった
  resolution: [da3_ngl_prepose_RB.md](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_prepose_RB.md) と [da3_ngl_prepose_RB.ipynb](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_prepose_RB.ipynb) を更新し、`correcting` から渡る `90度右回転` 済み upright image を canonical input として固定した。`MRL-10 Block 1` は image pixel を再回転せず、実画像寸法と `imageIntrinsics` の照合で legacy session だけ `K` を upright 基準へ補正し、`input_frame_manifest.csv`、`k_resize_check.csv`、`orientation_summary.json` に残す構成へ変更した。`MetricLarge` / `Giant` の summary も同じ orientation policy と `intrinsics_case_counts` を返すようそろえ、計画側では `MRL-11` を単独 gate にせず `MRL-10` へ吸収する方向へ整理した
  recurrence prevention: image 向きの問題は `viewer` の見え方だけで処理せず、input image、`K`、manifest、export summary、downloader bundle を同じ task で同時更新する。`correcting` 側 contract が変わった時は runbook の `.md/.ipynb` pair と `hi-ai-unified-blueprint.md` を同日中に更新し、別 `MRL` に残しっぱなしにしない
  remaining work: admin 実測で `MRL-10` を通し、`orientation_summary.json`、`k_resize_check.csv`、`proof_giant` export が upright 基準で整合することを確認して `p-done` / `i-pass` 判定へ進める。後続は top camera renderer と reviewing viewer 接続である
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_prepose_RB.md`

- record date: `2026-04-01`
  target MRL: `MRL-2R`
  target mRL: `mRL-2R.1`
  gate change: `active`
  issue: 実機では `frame_record.jsonl` と image の 1:1 は成立したが、`採択数=1` でも `record_fps ≒ 7.67` に留まり、停止後は画面に error が残り `session_manifest.json` も `finalized_with_error` / `sharedCamera=closed_with_error` になっていた。場当たり patch を続ける前に、`ARCore shared-camera` の公式 route と現行実装の差分を確認する必要があった
  cause: 現行 `correcting` は `shared-camera` route で `CameraCaptureSession.onConfigured()` 中に `Session.resume()` を呼び、`Config.UpdateMode.LATEST_CAMERA_IMAGE` のまま `33ms` delay polling で `Session.update()` を回していた。これに対し Google の `Shared camera access with ARCore` は、`setRepeatingRequest()` を `onConfigured()` で行い、`Session.resume()` は `onActive()` で行う sample を示している。また `Config.UpdateMode` reference は、`BLOCKING` では `update()` が通常 new camera image を待ち、`LATEST_CAMERA_IMAGE` は即 return して最新 frame を返すだけだと明記している。`Frame.acquireCameraImage()` reference でも、画像は数 frame 分 `NotYetAvailableException` を返し得るとされているため、`LATEST + postDelayed` で fixed polling する構成は canonical record 採択 loop と相性が悪い
  resolution: 公式 route に合わせて `RecordingCoordinator.kt` を修正し、`shared-camera` session の `updateMode` を `BLOCKING` へ変更した。`createSharedCaptureSession()` では `Session.resume()` を `onConfigured()` から `onActive()` へ移し、`sharedCamera.setCaptureCallback()` も resume 成功後に設定する形へ寄せた。さらに `OffscreenArCorePoseSampler` は `sampleIntervalMs` による delay polling をやめ、`BLOCKING` `Session.update()` を連続実行する loop に変えた。補助の `ArCoreLogger` 側 session も `BLOCKING` へそろえた。これで `採択数=1` の意味を `ARCore` update cadence により素直に近づけ、`record` 採択を handler の timing ずれへ依存させない構成にした
  source: [ARCore Shared camera access with ARCore](https://developers.google.com/ar/develop/java/camera-sharing) `Last updated 2024-10-31 UTC`、[ARCore Config.UpdateMode reference](https://developers.google.com/ar/reference/java/com/google/ar/core/Config.UpdateMode) `Last updated 2024-10-31 UTC`、[ARCore Frame.acquireCameraImage reference](https://developers.google.com/ar/reference/java/com/google/ar/core/Frame#acquireCameraImage()) `Last updated 2024-10-31 UTC`、[official shared_camera_java sample](https://raw.githubusercontent.com/google-ar/arcore-android-sdk/master/samples/shared_camera_java/app/src/main/java/com/google/ar/core/examples/java/sharedcamera/SharedCameraActivity.java)
  recurrence prevention: `ARCore` の lifecycle と frame cadence は独自推測で調整せず、`shared-camera` の resume / pause 位置、`updateMode` の意味、`acquireCameraImage()` の例外条件を公式 reference に照らしてから変更する。record 採択 loop は `sleep` / `postDelayed` 依存より、`Session.update()` の契約に沿って設計する
  remaining work: この修正 build は compile / install / launch まで確認したが、まだ実機で再収録して `record_fps` と stop 後 error 消失を再測定していない。次は `SO-53B` で短時間収録を行い、`採択数=1` での `frame_record.jsonl` 件数、`trajectreview/image/` 件数、`video_fps`、`sharedCamera=closed_with_error` の残存有無を確認する
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/RecordingCoordinator.kt`

- record date: `2026-04-01`
  target MRL: `MRL-2R`
  target mRL: `mRL-2R.1`
  gate change: `active`
  issue: `採択数=1` で `約30fps` 相当の `frame_record.jsonl` と対応 image を取りたいが、実機 `SO-53B` の `corecamera_shared_camera_trial` route では初回実測が `47s / 25 record / 25 image` と極端に低かった
  cause: `OffscreenArCorePoseSampler` が `cameraHandler` を video recorder callback と共有し、さらに image 保存を同期 JPEG 化で処理していたため、`ARCore update` と image 保存が同じ lane で詰まっていた。加えて `TrialCpuImageVideoRecorder` でも frame ごとの大きな allocation があり、`OOM` で収録継続を壊していた
  resolution: `FrameRecordImageIo.kt` を `raw plane snapshotter` / `JPEG persister` / `save queue` に分離し、`TrialCpuImageVideoRecorder` は codec input buffer へ直接 I420 を書く形へ変更した。`OffscreenArCorePoseSampler` は sampler 専用 thread と image save queue を持つ構成へ変更し、preview bitmap の recycle も追加した。実機再測定では `session-20260401-215102` で `frame_record.jsonl = 56`、`trajectreview/image = 56`、`video_frame_timestamps.csv = 314` を確認し、record と image の 1:1 は成立した
  recurrence prevention: image 保存方式、preview 表示、video encoder feed をそれぞれ独立 service に分離し、record 採択 loop を blocking I/O と大きな heap allocation へ従属させない
  remaining work: `採択数=1 -> 約30fps` にはまだ未達で、同 session の実測は `record_fps ≒ 7.67`、`video_fps ≒ 36.29` だった。さらに `session_manifest.json` は `finalized_with_error` / `sharedCamera=closed_with_error` が残っている。次は `shared-camera` route で `Session.update()` 自体が低 cadence になる原因を切り分け、`ARCore update cadence`、`acquireCameraImage` availability、stop 時の runtime close error を個別に潰す必要がある
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/CoreCameraTrialRuntime.kt`

- record date: `2026-04-01`
  target MRL: `MRL-2R`
  target mRL: `mRL-2R.1`、`mRL-2R.2`、`mRL-2R.3`
  gate change: `active`
  issue: canonical input を `frame_record.jsonl` と record 単位 `trajectreview/image/` へ切り替える方針は固まっていたが、runtime、`Sampling条件` popup、Google Drive 転送、parser、modeling preflight が旧 `arcore_pose.jsonl` / 転送時抽出前提のまま分断していた
  cause: `correcting` は `ARCore` pose を jsonl に保存していた一方、画像は `MediaMetadataRetriever` で転送時抽出し、popup も `ARCoreのtimestamp(ms)` / `ARCore 記録` という旧入力を持っていた。さらに `Google Drive` への `.jsonl` 書き込みでは MIME が `application/json` になっており、provider 側で `.jsonl.json` へ変形されていた
  resolution: `RecordingCoordinator.kt` と `CoreCameraTrialRuntime.kt` を更新し、`camera.pose` を正とした採択 frame だけを `frame_record.jsonl` と `trajectreview/image/` へ recording 中に保存する構成へ切り替えた。`MainActivity.kt` の `Sampling条件` popup は `主記録採択間隔` と `TRACKING時のみ主記録化` を持つ構成へ変更し、`.jsonl` は generic MIME で転送して拡張子二重化を防止した。`CorrectingDataCheckService.kt`、`session_parser.py`、`LocalModelingService.kt`、`review_contracts.py` も `frame_record.jsonl` と `trajectreview/image/` を primary に読むよう更新した。`correcting` / `app` の Kotlin compile、unit test、`correcting:installDebug` を実施済み
  recurrence prevention: record 単位で取得した data は全段で record 単位のまま扱い、画像の後抽出や nearest-link を canonical route に戻さない。`jsonl` 転送では MIME による provider 側 rename を避け、表示名の拡張子を正として保つ
  remaining work: `MRL-2R` の admin UX check を実機で行い、`Sampling条件` popup、record 生成、`Google Drive` 転送 zip 内の `frame_record.jsonl` / `trajectreview/image/`、modeling 側 preflight 読込を batch で確認する。legacy fallback に残る `MediaMetadataRetriever` route は compatibility 隔離として整理を続ける
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/RecordingCoordinator.kt`

- record date: `2026-04-01`
  target MRL: `MRL-2`
  target mRL: `mRL-2.3`
  gate change: `active`
  issue: `frame画像群` は転送時にだけ生成する方針へ変えた後も、抽出元の pose sample を基準に間引いていたため、学習用 frame が `5fps` を下回り得た
  cause: `CorrectingDataCheckService.extractImages()` が `selectedImageFrameIndexes()` で pose timestamp 近傍 frame だけを選び、転送用 `images/` の sampling floor を持っていなかった
  resolution: 転送用 `images/` 選択を frame timeline 基準へ変更し、元の frame timeline が `5fps` 以上なら抽出後も `5fps` を下回らず、元の frame timeline が `5fps` 未満なら無間引きで保持する `min 5fps or all if sparse` 方針へ修正した。unit test も追加し、dense source と sparse source の両方で選択結果を固定した
  recurrence prevention: 学習入力に使う `images/` は pose sample や lightweight check 都合へ従属させず、modeling の最低成立条件から sampling floor を先に固定する
  remaining work: 実機で `frame画像群` を ON にした転送を 1 回行い、生成された `images/` の枚数と session duration から `5fps` floor を満たすことを admin 手順で確認する
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/correcting-test/java/com/isensorium/app/CorrectingDataCheckServiceTest.java`

- record date: `2026-03-31`
  target MRL: `MRL-2S`
  target mRL: `mRL-2S.1`、`mRL-2S.2`
  gate change: `active`
  issue: `通常計測` の長時間収録は screen off 抑止だけでは閉じず、`1min15s` 前後で app crash が起きていた
  cause: 実機 crash log で `isensorium-shared-camera-trial` thread の `OutOfMemoryError` を確認した。`TrialCpuImageVideoRecorder` が収録中の全 YUV frame を RAM に保持し、停止時にまとめて encode していた
  resolution: `MainActivity` 側で keep-awake を追加済みの前提で、`TrialCpuImageVideoRecorder` を逐次 encode 方式へ変更し、収録中に `MediaCodec` / `MediaMuxer` へ流し込む構成へ切り替えた。frame をメモリへ蓄積しないため、長時間側は frame drop 許容で連続稼働を優先する
  recurrence prevention: `correcting` の長時間収録問題は screen off と crash を分離して扱い、実機 crash 時は `exit-info` と crash buffer を必ず取得してから route 切替や sampling 仮説へ進む
  remaining work: 修正 build を実機で `3min` 収録し、落ちないこと、session が `finalized` になること、`video.mp4` が残ることを admin 手順で確認する
  evidence path: `kisaragi-db/--exsams/prj-kisaragi_0002/device-debug/`

- record date: `2026-03-31`
  target MRL: `MRL-2S`
  target mRL: `mRL-2S.2`
  gate change: `active`
  issue: `OOM` 修正後の `2min30s` 実収録では crash しなくなったが、`撮影停止` 後に session が `recording` のまま止まり、停止処理が完了しなかった
  cause: 実機 session `session-20260331-044636` では `video.mp4` が `26MB` まで伸びていた一方、`session_manifest.json` は `status=recording` のまま、`video_events.jsonl` も空だった。`TrialCpuImageVideoRecorder.finishEncoding()` は `MediaCodec.INFO_TRY_AGAIN_LATER` が続いた時に終端 drain の抜け条件がなく、`stopAndRelease()` が無限待ちになる経路を持っていた
  resolution: `CoreCameraTrialRuntime.kt` の `drainCodec(endOfStream=true)` に `5s` の `STOP_DRAIN_TIMEOUT_NS` を追加し、`EOS` が返らない時は timeout で抜けて finalize を進める bounded stop に変更した
  recurrence prevention: 停止不良は `video.mp4` の成長有無、`session_manifest.json` の `status`、`video_events.jsonl` の有無を同時に見て、crash と finalize hang を分離して扱う
  remaining work: bounded stop 版を実機へ入れ直し、`3min` 収録で `撮影停止` 後に session が `finalized` まで進むかを admin 手順で確認する
  evidence path: `kisaragi-db/--exsams/prj-kisaragi_0002/device-debug/`

- record date: `2026-03-29`
  target MRL: `MRL-1`、`MRL-2`
  target mRL: `mRL-1.1` から `mRL-1.3`、`mRL-2.1` から `mRL-2.3`
  gate change: `p-done`
  issue: `correcting` 側は実データ取得と `Google Drive` 転送を完了し、その data が `MRL-5` の `3DGS` smoke 生成へ実際に使われていたが、gate 表では `active` / `ready` が多く残っていた
  cause: `candidate evidence` は個別に蓄積されていた一方で、`correcting -> modeling` handoff 実績をまとめて `p-done` 判定へ昇格する close 記録が不足していた
  resolution: `MRL-1` と `MRL-2` を、実 session 記録、`data-check`、calibration 診断、`Google Drive` 転送、`session_package.json` / `space_handoff_manifest.json` による handoff bundle 生成、さらにその転送済み data が `MRL-5` で実利用された事実を根拠に `p-done` へ更新した
  recurrence prevention: `correcting` 側の実データ取得と転送が後段 gate の実行証跡へ接続した時は、個別 candidate evidence のまま残さず、前段 gate 群をまとめて `p-done` 判定へ引き上げる
  remaining work: `MRL-3` 以降の `modeling` を継続し、reviewing viewer や multi-app 統合は後続 `MRL-**` で扱う
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-evidence.md`

- record date: `2026-03-29`
  target MRL: `MRL-3`、`MRL-4`、`MRL-5`、`MRL-6`
  target mRL: `mRL-3.1`、`mRL-4.1`、`mRL-4.2`、`mRL-5.1`、`mRL-5.2`、`mRL-5.3`、`mRL-6.1`、`mRL-6.2`
  gate change: `p-done`
  issue: `modeling` の bootstrap、preflight、single-frame smoke、evidence bundle 取得が別番号に分散していたため、どこまでを完了済みとみなすかが曖昧だった
  cause: `3DGS` 系 smoke artifact と local downloaded evidence が揃った後も、phase 単位の完了範囲と次段の焦点を更新し切れていなかった
  resolution: `MRL-3` を bootstrap / install、`MRL-4` を bundle 読込 / request preflight / directory intake、`MRL-5` を single-frame `3DGS` smoke、`MRL-6` を product 側 evidence bundle 取得として再整理し、ここまでを `p-done` へ更新した。`10s` 前後の整った実動画を使う `multi-frame` densify と `ぼんやり見える再現モデル` の確認は `MRL-7` へ移した
  recurrence prevention: stage が切り替わる時は、evidence 追加だけで終わらせず、`hi-ai-unified-blueprint.md` の gate 状態、次段の焦点、補助再開メモを同じ task で更新する
  remaining work: `MRL-7` として `multi-frame` densify と `PLY` viewer での可視化確認へ進み、route 比較と `selected_route.json` 生成は後続の利用者向け `MRL-**` に紐づく補助 gate で扱う
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/evidence/da3_smoke_v05/`

- record date: `2026-03-29`
  target MRL: `MRL-5`
  target mRL: `mRL-5.2`、`mRL-5.3`
  gate change: `candidate evidence strengthened`
  issue: `MRL-5` は depth bootstrap までは通っていたが、`correcting` 実 data から `3DGS` 系主空間モデル候補を再現できるか、また smoke artifact を `SpacePackage` 形へ接続できるかが未記録だった
  cause: 初期 closeout は single-frame depth bootstrap の成立確認を優先し、world projection、point export、`gsplat` rasterization、contract artifact 生成の結果を正本へ昇格し切れていなかった
  resolution: `DA3Metric-Large` single-frame depth、world back-projection、point export、`gsplat` rasterization、`gs_model_smoke.json`、`space_quality_smoke.json`、`space_package_smoke.json`、contract 名 artifact 生成までを `Candidate Bootstrap v1` と `admin-mrl-test-evidence.md` へ反映し、`MRL-5` の candidate proof を「correcting 実 data から `3DGS` 系主空間モデル候補を再現できる」水準まで引き上げた
  recurrence prevention: Colab 往復で得た持続価値のある結果は、shared worklog のみへ残さず、runbook、admin evidence、必要なら closeout 記録へ同じ task で反映する
  remaining work: `admin-mrl-test-evidence.md` を根拠に `MRL-5 p-done` 判定を行うか判断し、後続 gate では `trajectreview-modeling` 正式統合と `multi-frame` / `multi-route` を別 MRL として進める
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_prepose_RB.md`

- record date: `2026-03-30`
  target MRL: `MRL-7`
  target mRL: `mRL-7.1`
  gate change: `p-done`
  issue: `MRL-7` は `TraceCore` multi-frame visible reconstruction を主 target にしていたが、shared log にしか進捗が無く、`active` の中身が正本から読めなかった
  cause: fresh runtime からの再立ち上げ、window 探索、depth batch、world fusion、preview closeout を優先し、`admin-mrl-test-evidence.md` と `hi-ai-unified-blueprint.md` への反映が後ろにずれていた
  resolution: 実 session の最長連続 window 約 `3.95s` を正として sampled `12 frame` の depth batch を実行し、`11 frame` / `3696 points` の multi-frame world fusion、`world_points_multiframe_preview.png`、`mrl7_closeout_summary.json` を保存した。この範囲を `mRL-7.1` として切り出し `p-done` に上げ、`PLY` viewer 目視確認と人軌跡重畳を含む最小表示は `mRL-7.2` へ分離した
  recurrence prevention: `MRL-7` 以降の Colab 往復では、shared worklog の step 成功ごとに、どこまでをその `mRL` の成立範囲に含めるかを同日中に正本へ固定する
  remaining work: `mRL-7.2` として `PLY` viewer での目視確認、人軌跡重畳を含む `TraceCore` 最小表示、全体俯瞰 / 時系列 / 相対表示 / 滞留 / 交錯の価値確認を進める
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-evidence.md`

- record date: `2026-03-30`
  target MRL: `MRL-7`
  target mRL: `mRL-7.2`
  gate change: `p-done`
  issue: `正規 gaussian parameter の生成と最適化` を始める前は、点群と smoke render までしかなく、`3DGS` 本体へ入れたとは言いにくかった
  cause: point cloud と `gsplat.rasterization` smoke を先行して成立させた一方、gaussian parameter の tensor 初期化、backward、短い optimization loop の確認が未着手だった
  resolution: multi-frame point cloud から gaussian parameter を初期化し、`gsplat` 上で `1 step` probe と `20 step` の短い optimization を通した。`loss_init = 0.18226878345012665` から `loss_final = 0.035895735025405884` まで低下し、`gaussian_params_init.pt`、`gaussian_params_optim20.pt`、`gaussian_render_init.png`、`gaussian_render_optim20.png` を保存した。さらに `500 step` と `2500 step` の拡張 optimization も実行し、`2500 step` 版では `loss_final = 0.009165632538497448` まで低下、admin の目視で `gaussian_render_optim2500.png` が「かなり再現されている」「取得背景に近い構図」と確認できたため、この範囲を `mRL-7.2 p-done` とした
  recurrence prevention: Colab 上で `3DGS` 本体へ進む時は、最初に `1 step` backward probe を通し、引数 shape や path 解決を潰してから短い optimization loop と目視確認へ進む
  remaining work: viewer で読む正式 gaussian scene 形式の固定、artifact download の標準化、multi-view 条件の拡張、人軌跡重畳を含む `TraceCore` 最小表示は後続 `MRL-**` で進める
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-evidence.md`

- record date: `2026-03-31`
  target MRL: `MRL-8`
  target mRL: `mRL-8.1`、`mRL-8.2`
  gate change: `p-done`
  issue: `DA3 Colab` runbook は特定 zip path を hardcode しており、fresh runtime で別 session を試すたびに手編集が必要だった
  cause: input candidate scan は文字列 path ベースで重複し、`shortcut-targets-by-id` と `MyDrive` の同一実体 zip を canonical に 1 件へ寄せられていなかった。また selected input を runbook 本体と `MRL-7` one-block の両方へ handoff する closeout が未記録だった
  resolution: candidate scan を `session_id + size_bytes` と path rank で canonical 化し、widget で selected input を保存する前段を runbook 正本へ組み込んだ。admin は `[2] trajectreview-correcting-session-20260331-034831 [zip]` を選択し、`Step 8d` で `Step 2` から `Step 4.5`、`Step 8e` で `MRL-7 adopted one-block` を同じ input から end-to-end で実行できた
  recurrence prevention: Drive mount で同一実体が複数 path に見える時は `resolve()` だけに頼らず、session-level key と優先順位で canonical candidate list を作ってから widget UX を確定する
  remaining work: `MRL-8` で確立した selected input handoff を、後続 `job_status.json`、request UX、result download、viewer formalization へ接続する
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_prepose_RB.md`

- record date: `2026-03-26`
  target MRL: `旧番号時代の全 gate`
  target mRL: `current pass entries all`
  gate change: `reverted to active/planned`
  issue: admin `UX check 完了` 前でも、test、contract、build、local sample、局所 device 確認を根拠に `pass` を付けていた
  cause: `pass` の必須条件として admin `UX check` と batch check 運用を shared rule へ明文化していなかった
  resolution: `AGENTS.md`、`hi-ai-unified-blueprint.md`、関連 admin test 文書を更新し、`MRL` 記載順を運用順 `correcting -> modeling -> reviewing` に統一し、admin `UX check` 未完の gate を `active` / `planned` へ戻した
  recurrence prevention: 以後の `pass` は admin `UX check 完了` が記録された gate のみに付与し、関連 gate は batch でまとめて確認範囲を記録する
  remaining work: admin 向け batch `UX check` の対象範囲、手順、結果記録を `admin-mrl-test-evidence.md` へ追加し、各 gate を再 closeout する
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/hi-ai-unified-blueprint.md`
- record date: `2026-03-26`
  target MRL: `MRL-1`
  target mRL: `mRL-1.1`、`mRL-1.2`、`mRL-1.3`
  gate change: `pass`
  issue: `trajectreview-correcting` は記録画面だけで、同じ app 内の `data-check` と correction guidance が不足していた
  cause: `correcting` は verified mirror の recording screen に依存しており、session 停止後の intake / diagnose を app 内で閉じていなかった
  resolution: `CorrectingDataCheckService` を追加し、最新 session 再読込、`sensor_quality.json`、`session_package.json`、`space_handoff_manifest.json` 生成、recommended correction 表示を `correcting` 内へ実装した
  recurrence prevention: `correcting` の gate は記録画面だけで close せず、実 session から derived artifact が生成され、app 上に correction guidance が表示されるまで `pass` にしない
  remaining work: `modeling` 側の `Colab` handoff と `reviewing` 側の実 `ReviewArtifact` viewer を継続する
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-evidence.md`
- record date: `2026-03-26`
  target MRL: `旧番号時代の correcting / modeling / multi-app 補助 gate`
  target mRL: `旧番号時代の sample / build / summary 系 mRL`
  gate change: `reverted to active/planned`
  issue: `UX 確認`、`build / install`、`local sample`、summary 読込を本来機能完成に近い意味で扱い、app の完成度を過大に closeout していた
  cause: `UX-only` gate と本機能 gate を分離せず、multi-app 骨格と実 app 機能の境界を `MRL` 表へ十分に反映していなかった
  resolution: `hi-ai-unified-blueprint.md` と `project-truth.md` を再設計し、correcting、modeling、reviewing、統合 app の完成条件を本来機能基準へ引き直し、該当 gate を `active` / `planned` へ戻した
  recurrence prevention: mock、stub、sample、contract、build / install は補助 gate として別扱いにし、本機能 `pass` は実入出力と実生成物の end-to-end 証跡がある時だけ付与する
  remaining work: `correcting` の end-to-end、`Colab` handoff、remote result import、実 `ReviewArtifact` viewer、統合 app の end-to-end を実装する
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/hi-ai-unified-blueprint.md`
- record date: `2026-03-25`
  target MRL: `none`
  target mRL: `none`
  gate change: `initialized`
  issue: `trajectreview` の再開前提が外部一時文書に残っており、削除後に計画根拠を失う状態だった
  cause: 処理 4 段階、`GNSS` なし前提、UX 概念、package 契約が `prj-kisaragi_0002` の正本文書へ十分に吸収されていなかった
  resolution: `project-truth.md` と計画正本を更新し、再開基線を `prj-kisaragi_0002` 配下へ集約した
  recurrence prevention: 外部補助文書で採用した構想は、次の実装着手前に `project-truth` と BDD / TDD 正本へ同時反映する
  remaining work: 契約 closeout を実データ処理と viewer 実装へ接続する
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/hi-ai-unified-blueprint.md`
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
  target MRL: `MRL-2` から `MRL-4`
  target mRL: `mRL-1.2`、`mRL-1.3`、`mRL-2.x`、`mRL-3.x`、`mRL-4.x`
  gate change: `reverted to active/planned`
  issue: 契約 test と文書整合だけで `pass` 扱いしたため、着手中と完了済みの境界を取り違えた
  cause: `planned`、`active`、`pass` の運用意味を文書へ明文化する前に、契約固定済み項目を一括 closeout してしまった
  resolution: `AGENTS.md` に状態語の意味を追加し、計画正本の gate を保守的に `active` / `planned` へ修正した
  recurrence prevention: `MRL` / `mRL` の closeout は、実装、検証、残作業の 3 点がそろった項目だけに限定する
  remaining work: 実データ接続、viewer 実装、生成物 routing を継続し、`active` と `planned` を順次 close する
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/hi-ai-unified-blueprint.md`
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
- record date: `2026-03-25`
  target MRL: `MRL-5`
  target mRL: `mRL-5.1` から `mRL-5.3`
  gate change: `pass`
  issue: `trajectreview` が UI mock のままで、入力セッション folder から raw と追加出力を app 自身では取り出せなかった
  cause: `InputPackaging` は Python parser 契約までは固定済みだったが、Android app 側に source 選択、export、quality summary の導線がなかった
  resolution: Kotlin extractor を追加し、legacy alias intake、`isensorium/` と `trajectreview/` の分離 export、quality 数値表示付き UI、Python / Android test を実装した
  recurrence prevention: `InputPackaging` の route 変更は、parser 互換 test、Android export test、UX manual を同じ task で更新する
  remaining work: 抽出 bundle を後段の実空間再構成と viewer 実装へ接続する
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ISensoriumExtractionServiceTest.kt`
- record date: `2026-03-25`
  target MRL: `MRL-2`
  target mRL: `mRL-2.3`
  gate change: `pass`
  issue: 抽出 bundle は生成できても、`SpaceReconstruction` がそのまま消費できる concrete handoff artifact と主カメラ動画保持が不足していた
  cause: `MRL-5` までは intake と quality summary を優先し、`SessionPackage` 実体と stage-2 gate を抽象契約のまま残していた
  resolution: `video.mp4` と `video_events.jsonl` を raw bundle に含め、`session_package.json`、`space_handoff_manifest.json`、space gate 表示を Python / Android の両方へ実装した
  recurrence prevention: 後段 stage の abstract contract を追加した時は、同じ session で concrete artifact 名、UI summary、Python validator をそろえる
  remaining work: `space_handoff_manifest.json` を実 `SpaceReconstruction` engine の入口へ接続する
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ISensoriumExtractionServiceTest.kt`
- record date: `2026-03-26`
  target MRL: `MRL-**`
  target mRL: `mRL-**.5`
  gate change: `pass`
  issue: 4 app 分割の骨格は入ったが、build、install、role-specific UX の成立を closeout できていなかった
  cause: module 追加と共通 source 再利用までは進んでいた一方、統合 app との関係と app 単位切り分け表示の evidence が不足していた
  resolution: `correcting`、`modeling`、`reviewing`、統合 app の 4 module を build / install し、role-specific workflow 表示と担当境界 summary を controller / activity へ実装した
  recurrence prevention: multi-app 導入時は module build、unit test、device install、役割表示を同じ gate で closeout する
  remaining work: 実 bundle 読込と local modeling による mock 依存の解消
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/settings.gradle.kts`
- record date: `2026-03-26`
  target MRL: `MRL-3`
  target mRL: `mRL-3.1` から `mRL-3.2`
  gate change: `pass`
  issue: 4 app が mock snapshot 固定だと、実データでの UX 確認と `Colab` 前提 modeling handoff を進められなかった
  cause: extracting 後の bundle を再読込する service と、`Colab` account 未取得期間の local sample modeling route が未実装だった
  resolution: `WorkflowBundleService` で実 bundle から state を再構成し、`LocalModelingService` で `local_model_summary.json`、`colab_job_request.json`、`review_artifact_stub.json` を生成し、4 app すべてで実データ UX を使えるようにした
  recurrence prevention: 実データ UX が必要な段階は mock snapshot だけで closeout せず、bundle reader、生成 artifact、reviewing 側読込の 3 点を必須とする
  remaining work: `colab_job_request.json` を実 `Colab` 実行へ接続し、sample output を本物の `3DGS` 成果物へ置き換える
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/WorkflowBundleServiceTest.kt`
- record date: `2026-03-31`
  target MRL: `MRL-9`
  target mRL: `mRL-9.1`
  gate change: `p-done`
  issue: `DA3 Giant` の Gaussian branch は docs 上の route が見えていても、実行 method、`e3nn` 依存、保存先 contract が未固定で、`gs_ply` / `gs_video` 出力まで到達できていなかった
  cause: 初回 block では `DepthAnything3.infer(...)` を想定していたが、実 method は `inference(...)` だった。また `e3nn` install 後に stale import が残り、`matrix_to_angles` 未定義で落ちていた
  resolution: `Step 9d` で repo docs / API を再探索し、`da3-giant` + `infer_gs=True` + `export_format=\"npz-glb-gs_ply-gs_video\"` を固定した。`e3nn` install を `DepthAnything3` import 前へ移し、module reload 後に `inference()` を再実行して `gs_ply/0000.ply`、`gs_video/0000_extend.mp4`、`scene.glb`、`exports/npz/results.npz` の生成に成功した
  recurrence prevention: `MRL-9` を統合済みの main runbook pair では、`e3nn` install を import 前に置く。Gaussian branch failure では dependency 追加後の stale import を疑い、module reload または fresh import 順を先に確認する
  remaining work: `mRL-9.2` として `gs_ply` を `SuperSplat` または `PlayCanvas Model Viewer` で開き、自由視点 scene として読めることを admin evidence 化する
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_prepose_RB.md`
- record date: `2026-03-31`
  target MRL: `MRL-9`
  target mRL: `mRL-9.2`
  gate change: `p-done`
  issue: `gs_ply` が生成できても、外部 viewer で自由視点 scene として読めるかが未確認だった
  cause: `mRL-9.1` は Colab export までを閉じており、viewer 側の admin UX 確認を別 gate に分けていた
  resolution: `gs_ply/0000.ply` を `PlayCanvas Model Viewer` に読み込み、自由視点 scene として表示されることを admin が確認した
  recurrence prevention: `gs_ply` route を close する時は、export 成功だけでなく viewer 側の opening evidence も同じ日付で残す
  remaining work: top camera renderer、path overlay、request / status UX は後続 `MRL-**` へ送る
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-evidence.md`
- record date: `2026-04-06`
  target MRL: `MRL-10`
  target mRL: `mRL-10.5`、`mRL-10.5a`、`mRL-10.5b`
  gate change: `active route pivot`
  issue: main `Colab` route が旧系の route 名、preflight、reference notebook 非反映、notebook companion 未同期を抱えたままで、`1 record = image + pose + intrinsics + timestamp` を anchor とする canonical route が docs と code で揃っていなかった
  cause: `record-native` 方針の採用後も、main runbook pair と周辺文書、preflight route 名、handoff 契約が部分的に旧 route のまま残っていた
  resolution: `da3_record_sequence_anchor_rebuild7.ipynb` を `--exsams` へ read-only reference として追加し、その precheck、可視化、adjacent continuity、pre-merge gate 構成を main [da3_ngl_prepose_RB.md](/C:/Users/tetsuya/kisaragi/kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_prepose_RB.md) へ昇格した。canonical route は `sequence-anchor first`、`1 frame = 1 record`、`strict one-to-one join`、`depth-anything/DA3NESTED-GIANT-LARGE-1.1` の official API / CLI 基準へ固定し、`.md` 正本から `.ipynb` companion を再生成した。あわせて `project-truth.md`、`hi-ai-unified-blueprint.md`、`resume-startup-plan.md`、`admin-mrl-test-method.md`、`session_parser.py`、`review_contracts.py`、`CorrectingDataCheckService.kt` の route / contract を同期した
  recurrence prevention: route pivot 時は、reference notebook を `--exsams` へ取り込み、main runbook `.md` を先に更新してから companion `.ipynb` を再生成する。current-truth 文書、preflight route、handoff contract、app 既定値の grep 残骸確認を同じ task で行う
  remaining work: existing session data で main route の end-to-end 実測を継続し、chunk/merge 品質の open issue を `mRL-10.4` 系で閉じる
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_prepose_RB.md`, `kisaragi-db/--exsams/prj-kisaragi_0002/colab-inputs/da3_record_sequence_anchor_rebuild7.ipynb`
- record date: `2026-04-07`
  target MRL: `MRL-10`
  target mRL: `mRL-10.5`
  gate change: `active authoring contract hardened`
  issue: refreshed canonical pair は source 分離と設計契約を導入したが、markdown source-sync が `re.sub` replacement により `\\n` を実 newline へ壊し、wrapper cell と docs inventory の全件追跡も弱かった
  cause: pair 同期 utility が code block を plain replacement string で置換しており、wrapper source 内の backslash sequence を verbatim 保持できていなかった。また inventory は cell 一覧中心で、function / variable 契約の追跡粒度が不足していた
  resolution: `da3_runbook_sources/sync_da3_runbook_sources.py` を callable replacement へ修正し、`#12-2` wrapper の `lstrip(\"\\n\")` を markdown / ipynb の両方で保持できるようにした。`build_inventory.py` は `Cell Inventory`、`Function And Class Inventory`、`Variable Inventory` を生成する形へ拡張し、`da3_ngl_runbook_source_inventory.md`、`da3_ngl_runbook_design_contract.md`、`hi-ai-unified-blueprint.md` を同期した。`test_da3_runbook_sources.py` には wrapper escape 保持と inventory section の regression test を追加し、`unittest` 5件 pass と skill validator pass を確認した
  recurrence prevention: canonical pair の直接修正後は必ず source-sync と inventory 再生成を行い、wrapper の backslash sequence と inventory section を test で固定する。設計契約変更時は `HAUB` 側の inventory 入口と source inventory 正本を同じ task で更新する
  remaining work: `BLK-1` と `BLK-2` を閉じる end-to-end 実測を継続する
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_runbook_sources/sync_da3_runbook_sources.py`, `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_ngl_runbook_source_inventory.md`, `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_da3_runbook_sources.py`
- record date: `2026-04-07`
  target MRL: `MRL-10`
  target mRL: `mRL-10.5`
  gate change: `active shared pose contract consolidated`
  issue: `#7`、`#9`、`#14` がそれぞれ image dir 解決、intrinsics 正規化、pose 行列化、camera basis 変換を重複実装しており、`DA3` で `3DGS` を成立させるうえで camera trajectory / pose の統一参照が崩れやすかった。加えて `#14-1` には `batch_execution_items_path` 未定義の runtime bug が残っていた
  cause: canonical pair の stage 分離を先行し、camera / pose の共通契約を `#6 Shared Helpers` へ引き上げ切れていなかった
  resolution: `06_shared_helpers.py` に `load_frame_records`、`build_image_name_by_record_index`、`ranked_image_dirs`、`normalize_intrinsics_to_upright`、`quat_to_rot`、`pose_to_w2c`、`build_K`、`to_4x4`、`lens_direction_from_c2w`、`build_anchor_c2w`、`c2w_list_from_extrinsics`、`TRANSFORM_*`、`LOCAL_CAMERA_BASIS` を追加し、`#7-1`、`#9-1`、`#14-1` が同じ helper を使う構成へ寄せた。`#14-1` では `batch_execution_items_path` も明示定義した。これにより preview、record-native manifest、merge の 3 段が同じ pose / orientation / anchor basis 契約でつながる
  recurrence prevention: camera / pose 系ロジックを新設する時はまず `#6 Shared Helpers` へ追加し、stage cell 側へ同種の数式や path 解決を再実装しない。merge stage の summary input は required path を cell 先頭で固定する
  remaining work: canonical route の end-to-end 実測で `BLK-1`、`BLK-2` の品質 blocker を閉じる
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_runbook_sources/cells/06_shared_helpers.py`, `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_runbook_sources/cells/07_01.py`, `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_runbook_sources/cells/09_01.py`, `kisaragi-db/--devs/--products/prj-kisaragi_0002/colab/da3_runbook_sources/cells/14_01.py`


