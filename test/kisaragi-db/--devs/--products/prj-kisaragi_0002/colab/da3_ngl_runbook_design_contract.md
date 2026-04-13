# da3_ngl_increpose_RB design contract

この文書は `da3_ngl_increpose_RB.md` / `da3_ngl_increpose_RB.ipynb` を source 根拠情報から再構築する時の authoring 契約詳細とする。日常運用で最初に見る要約面は `HAUB` の modeling 用一覧表直後の契約表とし、本書はその補助詳細を担う。

## 目的

- `da3_increpose_sources/` を canonical source とし、notebook 上の code cell と markdown cell の両方を管理対象にする。
- 各 markdown cell は対応する `#No`、その直前の `#No`、その直後の `#No` を先頭に持ち、複数 pattern は `#9-1..#9-5` のような最短表現で示す。
- `#6 Shared Helpers` を camera trajectory / pose / intrinsics / anchor basis の唯一の共通契約面とし、`#7`、`#8`、`#9`、`#10`、`#11` が同じ参照面で動くようにする。
- 実行順の基本は `#1` から `#11` の top-to-bottom とし、`#8` は `sliding_window_incremental_seeded` による chunk 実行準備と本実行、`#9` は 2 chunk overlap の係数導出、`#10` は graph build / gate、`#11` は merge / review を担う。
- `#8-9` は前 chunk の adopted pose を次 chunk の context へ seed し、`incremental_seed_trace_arc.csv` と `batch_run_status_arc.csv` を固定 artifact として残す。
- `#9-1` は 2 chunk overlap pose を同一座標系へ再現する matching 面とし、chunk A/B の `pred_extrinsics.npy` と `chunk_input_frames.csv` から overlap 対応、relative transform、matching residual を固定 artifact として残す。
- `#10-1` は chunk 間の predicted pose を global graph へ上げる build / gate 面とし、`prepose_chunk_graph_solution_arc.csv`、`prepose_chunk_graph_summary.json`、`premerge_pose_validation.json` を固定しつつ、`chunk_global_transforms_arc.csv` 互換の matrix contract も維持する。
- `#11-1` は merge engine 面とし、graph で決めた chunk-to-world を使って merged pose / NGL bundle / GS artifact を出し、`#11-2` は review visualization を作る。
- `HAUB` の script 一覧表は `correcting` 用と `modeling` 用を分離し、`modeling` 側は cell ごとの役割だけでなく、主要 data 名、reference directories、主要 output / handoff を含む 1 表で管理する。`correcting` 側は別の local product inventory を参照し、両表の思想をそろえて参照面の取り違えを防ぐ。

## source 根拠情報

| item | path | role |
| --- | --- | --- |
| code manifest | `da3_increpose_sources/cell_manifest.json` | code cell token と source file の対応 |
| markdown manifest | `da3_increpose_sources/markdown_manifest.json` | markdown cell の順序、対応 token、前後参照 |
| code source | `da3_increpose_sources/cells/*.py` | 各 code cell の根拠情報 |
| markdown source | `da3_increpose_sources/markdown/*.md` | 各 markdown cell の根拠情報 |
| sync utility | `da3_increpose_sources/sync_da3_increpose_sources.py` | source 根拠情報から pair を再構築する |
| inventory utility | `da3_increpose_sources/build_increpose_inventory.py` | code / markdown inventory を生成する |
| HAUB integrated tables | `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/hi-ai-unified-blueprint.md` | `correcting` 用 / `modeling` 用の統合入口を管理する |
| correcting inventory | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/correcting_script_source_inventory.md` | local product script / source の現状をありのまま追う |

## markdown cell rule

- markdown source file は先頭 3 行を必須とする。
- 1 行目は `#No: ...`
- 2 行目は `前: ...`
- 3 行目は `次: ...`
- 複数連番は `#4-1..#4-2` のように最短表現で書く。
- markdown 本文は、その直後の code cell 群の実働内容と出力契約に合わせる。

## 再構築 rule

- `sync_da3_increpose_sources.py` は markdown cell と code cell を source 根拠情報から順に組み立て、`.md` と `.ipynb` を同時更新する。
- notebook companion を直接編集した時は、その内容を `da3_increpose_sources/` 側へ戻すか、再度 source 根拠情報に寄せて同期し直す。
- inventory 更新時は `build_increpose_inventory.py` を再実行し、`da3_ngl_increpose_source_inventory.md` を同じ task で更新する。
- `#8-9` は `sliding_window_incremental_seeded` の execution 面として、`record_index -> accepted pose` の map を次 chunk へ引き継ぐ contract を壊してはならない。少なくとも `seed_pose_applied`、`seeded_overlap_count`、`incremental_seed_trace_arc.csv`、`batch_run_status_arc.csv` を残す。
- `#8-3` と `#8-9` の directory contract は、`batch_work_dir = chunk_runs/<batch_name>/` を parent scope、`chunk_out_dir = chunk_runs/<batch_name>/<chunk_name>/` を leaf scope として分離する。旧 manifest が `batch_work_dir` に chunk path や `chunk_0005_*` のような suffix 付き legacy chunk dir を入れていても、`#8-9`、`#10-1`、`#11-1` の reader / writer は batch scope へ正規化して二重ネストを防ぐ。
- `runtime workspace` directory 名は `runtime_workspace/` を canonical とする。`pipeline_slug` の default はこの値に固定し、route 名を workspace directory 名に混ぜない。
- `#08-3` は planning の管理 file を `runtime_workspace/manifests/chunk_execution_plan.csv` へ統合する。target subset、execution batch、chunk scope path は同 file の列で表し、旧 CSV 群は互換派生に留める。
- `#10-1` と `#11-1` の final access contract は `probe_root/final_outputs/#10-1/`、`probe_root/final_outputs/#11-1/` を stage root とし、その直下を `re_access/` と `persist_only/` に固定する。`persist_only/` が canonical file 実体であり、関係定義の管理正本は `HAUB` に置く。`re_access/` は後段再参照を助ける派生 pointer だけに使う。
- `#10-1` は graph build / gate の stage 管理 file を `#10-1/persist_only/graph_gate_report.json` に統合する。`#10-1/re_access/graph_contract_manifest.json` を生成してよいが、その schema と内容は `HAUB` handoff matrix に従う派生物であり、手修正してはならない。`#11-1` は `full graph solution` のような旧前提を推測せず、まず `HAUB` を見てから必要なら派生 pointer を読む。
- `#11-1` は merge / review の canonical file 実体を `#11-1/persist_only/merged`、`diagnostics`、`manifests`、`chunk_evidence` に保存し、stage 管理 file は `#11-1/persist_only/merge_output_report.json` に統合する。`manifests/` は `merge_input_report.json` に集約し、input manifest や anchor CSV を多重 copy しない。`#11-1/re_access/` には `11_2_handoff_manifest.json`、`11_3_handoff_manifest.json`、`merge_resume_state.json`、`stage_access_index.json` のような再開導線だけを置く。同系統 file を `merged_dir`、`stage_11_2_dir`、`stage_11_3_dir`、`final_outputs_*` へ多重 copy しない。`re_access/` が持つのは path pointer と stage summary だけであり、関係定義そのものは持たない。
- `#7-2` の `camera_anchor_full_arc.csv` は center / lens だけでなく `w2c_*` matrix 列も持ち、`#8-3` の chunk csv へそのまま引き継ぐ。`#8-8` wrapper はこの `w2c_*` を pose conditioning 入力として使い、DA3 戻り値に `pred_extrinsics` が無い場合でも input extrinsics を `pred_extrinsics.npy` として保存できなければならない。
- `#9-1` は matching 結果を `overlap_pair_metrics_arc.csv`、`trajectory_points_arc.csv`、`transform_b_to_a.npy`、`trajectory_match.png`、`trajectory_match.html`、`matching_summary.json` として `persist_root/01_anchor/07matching/` に固定する。summary には `relative_scale`、`relative_translation_norm`、`relative_rotation_deg`、pre/post residual を含める。
- `#10-1` は graph / gate 面として、最低でも `center_error_p95`、`lens_error_deg_p95`、`delta_center_error_max`、`delta_lens_error_deg_max` と `chunk_global_transforms_arc.csv` 互換の matrix 列を残す。`run_status_path` と `seed_trace_path` を読む contract を外してはならない。
- `#11-1` は merge engine 面として、`merged_camera_pose_arc.csv`、`merged_camera_matrix_arc.csv`、`ngl_bundle_manifest_dir`、`chunk_global_transforms_arc.csv`、`merge_summary.json` を同時に更新し、graph 由来の chunk-to-world 解釈を merge 結果まで追跡可能に保つ。
- `HAUB` の `modeling` 用一覧表を更新する時は、少なくとも `role`、`key data names`、`reference directories`、`main outputs / handoff` の 4 列を維持し、runbook の参照面変更を同じ task で反映する。
- `HAUB` には `Increpose Path Handoff Matrix` を持たせ、主要 artifact ごとの producer token、consumer token、canonical path / pattern を管理する。directory / output / read 参照の整合確認はこの表を正として行う。
- `correcting` 側で local product script / source を更新した時も、同じ 4 列を `correcting_script_source_inventory.md` と `HAUB` の correct 用一覧表へ同時反映する。
- 各 row では、どの reference directory を見ているかを曖昧名ではなく `persist_root/01_anchor`、`pipeline_root/manifests` のような具体 path で書く。
