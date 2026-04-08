# da3_ngl_prepose_RB source inventory

この文書は `da3_runbook_sources/cell_manifest.json` と `da3_runbook_sources/markdown_manifest.json` を正として、canonical pair `da3_ngl_prepose_RB.md` / `da3_ngl_prepose_RB.ipynb` の code / markdown source 一覧を示す。

## Cell Inventory

| token | source_file | kind | heading | functions | top_level_variables | docs_id |
| --- | --- | --- | --- | --- | --- | --- |
| #1-1 | `cells/01_01.py` | `direct` | DA3 NGL Canonical Colab Runbook | - | - | `DOC-C01-01` |
| #2-1 | `cells/02_01.py` | `direct` | 2 Config | - | CONFIG | `DOC-C02-01` |
| #3-1 | `cells/03_01.py` | `direct` | 3 Input Select And Path Check | infer_session_id, scan_candidates, reset_extract_root, extract_selected_input, pick_best_raw_root, resolve_and_validate_paths | OAI_SHORTCUT_ID, SHORTCUT_ROOT, RAW_SCAN_ROOTS, RESULTS_ROOT_CANDIDATES, RESULTS_ROOT, EXTRACT_ROOT, RUNBOOK_CANDIDATE_DOC, RUNBOOK_SELECTED_DOC, RUNBOOK_PATHS_DOC, CONFIG_SNAPSHOT, PIPELINE_SLUG, candidate_doc | `DOC-C03-01` |
| #4-1 | `cells/04_01.py` | `direct` | 4 Tree Init | - | paths, selected_path, selected_kind, session_id, results_root, session_root, session_outer, images_dir, frame_record_path, frame_pose_index_path, config, route_slug | `DOC-C04-01` |
| #4-2 | `cells/04_02.py` | `direct` | 4 Tree Init | - | ctx, probe_root, managed_dirs | `DOC-C04-02` |
| #5-1 | `cells/05_install.py` | `direct` | 5 Install | - | repo_root, repo_url, src_root | `DOC-C05-01` |
| #6-1 | `cells/06_shared_helpers.py` | `direct` | 6 Shared Helpers | load_ctx, save_json, append_sequence_columns, rotmat_to_rpy_deg, _summary_rows, display_stage_summary, rotation_angle_deg_from_matrix, summarize_relative_transform | RUNBOOK_CTX_PATH | `DOC-C06-01` |
| #9-1 | `cells/09_01.py` | `direct` | 9 Record Manifest And Chunk Plan | ranked_image_dirs, lap_var, read_actual_wh, normalize_intrinsics_to_upright, quat_to_rot, pose_to_w2c, build_K | ctx, images_dir, frame_record_path, frame_pose_index_path, manifest_dir, CANONICAL_ORIENTATION_POLICY, BLUR_THRESHOLD, frame_pose_df, image_name_by_record_index, image_dir_ranking, resolved_images_dir, rows | `DOC-C09-01` |
| #9-2 | `cells/09_02.py` | `direct` | 9 Record Manifest And Chunk Plan | - | ctx, manifest_dir, managed_dirs, record_dir, anchor_diag, anchor_keep_cols, anchor_join, p, df, ts_col, df | `DOC-C09-02` |
| #9-3 | `cells/09_03.py` | `direct` | 9 Record Manifest And Chunk Plan | - | config, config_view | `DOC-C09-03` |
| #9-4 | `cells/09_04.py` | `direct` | 9 Record Manifest And Chunk Plan | sha256_file, to_4x4 | ctx, config_snapshot, manifest_dir, persist_root, pipeline_slug, pipeline_root, anchor_dir, chunk_manifest_dir, batch_runs_dir, merged_dir, MODEL_ID, BUNDLE_MODEL_SLUG | `DOC-C09-04` |
| #9-5 | `cells/09_05.py` | `direct` | 9 Record Manifest And Chunk Plan | - | ctx, probe_root, pipeline_root, chunk_manifest_dir, record_manifest_path, record_df, chunk_index_path, chunk_index_df, rows, out | `DOC-C09-05` |
| #10-1 | `cells/10_01.py` | `direct` | 10 Precheck | - | ctx, config_snapshot, manifest_dir, persist_root, pipeline_slug, pipeline_root, chunk_manifest_dir, chunk_index_all_path, chunk_index_df, rows, precheck_df, precheck_path | `DOC-C10-01` |
| #10-2 | `cells/10_02.py` | `direct` | 10 Precheck | - | ctx, pipeline_root, chunk_manifest_dir, idx_df, rows, edge_df, out | `DOC-C10-02` |
| #10-3 | `cells/10_03.py` | `direct` | 10 Precheck | - | config, ctx, persist_root, run_dir, manifest_dir, anchor_dir, anchor_qc_path, sequence_precheck_path, edge_validation_path, anchor_qc_df, sequence_df, edge_df | `DOC-C10-03` |
| #11-1 | `cells/11_01.py` | `direct` | 11 Run Preparation | - | ctx, manifest_dir, batch_plan_df, chunk_all_df, chunk_target_df | `DOC-C11-01` |
| #11-2 | `cells/11_02.py` | `direct` | 11 Run Preparation | load_json, save_json, load_ctx, find_first, normalize_rows, angle_deg | - | `DOC-C11-02` |
| #11-3 | `cells/11_03.py` | `direct` | 11 Run Preparation | - | ctx, probe_root, pipeline_root, chunk_manifest_dir, chunk_runs_dir, test_chunk_with_batch_path, test_batch_plan_path, canonical_chunk_with_batch_path, canonical_batch_plan_path, fallback_chunk_target_path, fallback_batch_plan_path, execution_chunks_df | `DOC-C11-03` |
| #11-4 | `cells/11_04.py` | `direct` | 11 Run Preparation | - | ctx, probe_root, pipeline_root, chunk_manifest_dir, chunk_runs_dir, manifest_dir, persist_root, anchor_dir, merged_dir, final_outputs_dir, final_outputs_diagnostics_dir, final_outputs_manifests_dir | `DOC-C11-04` |
| #11-5 | `cells/12_01.py` | `direct` | 11 Run Preparation | - | ctx, probe_root, pipeline_root, chunk_manifest_dir, chunk_runs_dir, final_outputs_diagnostics_dir, execution_chunks_path, execution_batch_plan_path, execution_chunks_df, execution_batch_plan_df, batch_execution_items_df, batch_execution_items_path | `DOC-C12-01` |
| #7-1 | `cells/07_01.py` | `direct` | 7 Full Prepose Build | build_anchor_inputs_from_zip | ctx_path, ctx, manifest_dir, da3_nested_dir, world_dir, final_outputs_dir, final_outputs_merged_dir, final_outputs_diagnostics_dir, final_outputs_manifests_dir, final_outputs_chunk_evidence_dir, images_dir, frame_record_path | `DOC-C07-01` |
| #7-2 | `cells/07_02.py` | `direct` | 7 Full Prepose Build | _existing, _find_manifest_triplet, _normalize_rows | config, search_roots, anchor_dir, manifest_dir, manifest_df, intrinsics, extrinsics_w2c, c2w, camera_centers, right_vecs, up_vecs, lens_vecs | `DOC-C07-02` |
| #7-3 | `cells/07_03.py` | `direct` | 7 Full Prepose Build | _existing, _find_anchor_root, _normalize, _wrap_deg, _angle_deg | config, search_roots, persist_root, anchor_dir, anchor_path, anchor_df, required_cols, missing, lens, up, right, centers | `DOC-C07-03` |
| #7-4 | `cells/12_chunk_wrapper.py` | `wrapper_body` | 7 Full Prepose Build | _resolve_device, _pick_pred_array, main | REPO_ROOT, SRC_ROOT | `DOC-C12-02` |
| #7-5 | `cells/12_03.py` | `direct` | 7 Full Prepose Build | - | ctx, probe_root, pipeline_root, chunk_manifest_dir, chunk_runs_dir, final_outputs_diagnostics_dir, wrapper_path, batch_execution_items_path, items_df, config_snapshot, DRY_RUN, DEVICE | `DOC-C12-03` |
| #7-6 | `cells/07matching_01.py` | `direct` | 7 Full Prepose Build | resolve_matching_chunk_names, resolve_chunk_artifact, to_4x4_batch, normalize_rows, angle_deg, lens_direction_from_c2w, up_direction_from_c2w, c2w_list_from_extrinsics, estimate_pose_aware_similarity, transform_c2w_list, pose_rows_to_frame_df, plot_pose_match, write_pose_match_html | ctx, config, probe_root, persist_root, pipeline_root, anchor_dir, chunk_manifest_dir, chunk_runs_dir, final_outputs_chunk_evidence_dir, final_outputs_diagnostics_dir, matching_dir, LOCAL_EXTRINSIC_MODE | `DOC-C07M-01` |
| #7-7 | `cells/07_07.py` | `direct` | 7 Full Prepose Build | to_4x4_batch, normalize_rows, angle_deg, summarize_split_metrics, lens_direction_from_c2w, up_direction_from_c2w, normalize_vec, build_anchor_c2w_list, local_c2w_list, estimate_pose_aware_similarity, transform_c2w_list, summarize_candidate, pick_selected_candidate | ctx, probe_root, persist_root, pipeline_root, chunk_manifest_dir, chunk_runs_dir, merged_dir, final_outputs_diagnostics_dir, anchor_dir, camera_anchor_full_path, batch_execution_items_path, items_df | `DOC-C07-07` |
| #8-1 | `cells/08_01.py` | `direct` | 8 Anchor QC And Plot | _existing, _find_anchor_diag_root | config, search_roots, persist_root, anchor_dir, diag_path, df, MAX_DELTA_POS, MAX_DELTA_LENS_ANGLE_DEG, MAX_DELTA_UP_ANGLE_DEG, MAX_DELTA2_POS, MAX_DELTA2_ROT, WARN_ABS_ROLL_CENTERED_DEG | `DOC-C08-01` |
| #8-2 | `cells/08_02.py` | `direct` | 8 Anchor QC And Plot | _existing, _find_anchor_root, _pick_first_existing, _resolve_center_cols, _resolve_lens_cols | config, search_roots, persist_root, anchor_dir, anchor_csv, df, lens_cols, plotly_html, plotly_png, centers, bbox_min, bbox_max | `DOC-C08-02` |
| #13-1 | `cells/13_01.py` | `direct` | 13 Prepose Graph Judge | - | ctx, probe_root, pipeline_root, chunk_manifest_dir, merged_dir, final_outputs_diagnostics_dir, validation_json, route_compare_json, route_compare_csv, graph_solution_csv, graph_edges_csv, graph_summary_json | `DOC-C13-01` |
| #14-1 | `cells/14_01.py` | `direct` | 14 Merge From Prepose Graph | ensure_target_chunk_manifest, resolve_chunk_output_dir, resolve_chunk_input_dir | missing_merge_deps, batch_preflight_status_path, ctx, probe_root, results_root, persist_root, modeling_session_id, manifest_dir, final_outputs_dir, final_outputs_merged_dir, final_outputs_diagnostics_dir, final_outputs_manifests_dir | `DOC-C14-01` |
| #15-1 | `cells/15_01.py` | `direct` | 15 Optional Bundle | - | merge_summary_path, ctx, probe_root, pipeline_root, merged_dir, pipeline_config_path, bundle_model_slug, merge_summary_doc_path, merge_summary, config_snapshot, download_local_bundle, local_bundle_base | `DOC-C15-01` |
| #16-1 | `cells/16_01.py` | `direct` | 16 Cleanup Inventory | path_size_bytes | ctx, probe_root, results_root, persist_root, manifest_dir, da3_nested_dir, da3_nested_gs_dir, world_dir, final_outputs_dir, final_outputs_merged_dir, final_outputs_diagnostics_dir, final_outputs_manifests_dir | `DOC-C16-01` |
| #16-2 | `cells/16_02.py` | `direct` | 16 Cleanup Inventory | - | ctx, pipeline_root, merged_dir, cleanup_plan_path, cleanup_plan, rows, cleanup_csv | `DOC-C16-02` |
| #17-1 | `cells/17_01.py` | `direct` | 17 Cleanup Apply | - | ctx, probe_root, pipeline_root, merged_dir, cleanup_plan_path, cleanup_csv_path, cleanup_plan, review_df, reviewed_paths, other_dir, deleted, moved_to_other | `DOC-C17-01` |

## Markdown Inventory

| leading_token | source_file | target_ref | prev_ref | next_ref | heading |
| --- | --- | --- | --- | --- | --- |
| #1-1 | `markdown/01_01.md` | #1-1 | なし | #2-1 | DA3 NGL Canonical Colab Runbook |
| #2-1 | `markdown/02_01.md` | #2-1 | #1-1 | #3-1 | 2 Config |
| #3-1 | `markdown/03_01.md` | #3-1 | #2-1 | #4-1..#4-2 | 3 Input Select And Path Check |
| #4-1 | `markdown/04_01.md` | #4-1..#4-2 | #3-1 | #5-1 | 4 Tree Init |
| #5-1 | `markdown/05_01.md` | #5-1 | #4-1..#4-2 | #6-1 | 5 Install |
| #6-1 | `markdown/06_01.md` | #6-1 | #5-1 | #9-1..#9-5 | 6 Shared Helpers |
| #9-1 | `markdown/09_01.md` | #9-1..#9-5 | #6-1 | #10-1..#10-3 | 9 Record Manifest And Chunk Plan |
| #10-1 | `markdown/10_01.md` | #10-1..#10-3 | #9-1..#9-5 | #11-1..#11-5 | 10 Precheck |
| #11-1 | `markdown/11_01.md` | #11-1..#11-5 | #10-1..#10-3 | #7-1..#7-7 | 11 Run Preparation |
| #7-1 | `markdown/07_01.md` | #7-1..#7-7 | #11-1..#11-5 | #8-1..#8-2 | 7 Full Prepose Build |
| #8-1 | `markdown/08_01.md` | #8-1..#8-2 | #7-1..#7-7 | #13-1 | 8 Anchor QC And Plot |
| #13-1 | `markdown/13_01.md` | #13-1 | #8-1..#8-2 | #14-1 | 13 Prepose Graph Judge |
| #14-1 | `markdown/14_01.md` | #14-1 | #13-1 | #15-1 | 14 Merge From Prepose Graph |
| #15-1 | `markdown/15_01.md` | #15-1 | #14-1 | #16-1..#16-2 | 15 Optional Bundle |
| #16-1 | `markdown/16_01.md` | #16-1..#16-2 | #15-1 | #17-1 | 16 Cleanup Inventory |
| #17-1 | `markdown/17_01.md` | #17-1 | #16-1..#16-2 | 終了 | 17 Cleanup Apply |

## Function And Class Inventory

| name | token | heading | docs_id |
| --- | --- | --- | --- |
| infer_session_id | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| scan_candidates | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| reset_extract_root | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| extract_selected_input | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| pick_best_raw_root | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| resolve_and_validate_paths | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| load_ctx | #6-1 | 6 Shared Helpers | `DOC-C06-01` |
| save_json | #6-1 | 6 Shared Helpers | `DOC-C06-01` |
| append_sequence_columns | #6-1 | 6 Shared Helpers | `DOC-C06-01` |
| rotmat_to_rpy_deg | #6-1 | 6 Shared Helpers | `DOC-C06-01` |
| _summary_rows | #6-1 | 6 Shared Helpers | `DOC-C06-01` |
| display_stage_summary | #6-1 | 6 Shared Helpers | `DOC-C06-01` |
| rotation_angle_deg_from_matrix | #6-1 | 6 Shared Helpers | `DOC-C06-01` |
| summarize_relative_transform | #6-1 | 6 Shared Helpers | `DOC-C06-01` |
| ranked_image_dirs | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| lap_var | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| read_actual_wh | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| normalize_intrinsics_to_upright | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| quat_to_rot | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| pose_to_w2c | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| build_K | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| sha256_file | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| to_4x4 | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| load_json | #11-2 | 11 Run Preparation | `DOC-C11-02` |
| save_json | #11-2 | 11 Run Preparation | `DOC-C11-02` |
| load_ctx | #11-2 | 11 Run Preparation | `DOC-C11-02` |
| find_first | #11-2 | 11 Run Preparation | `DOC-C11-02` |
| normalize_rows | #11-2 | 11 Run Preparation | `DOC-C11-02` |
| angle_deg | #11-2 | 11 Run Preparation | `DOC-C11-02` |
| build_anchor_inputs_from_zip | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| _existing | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| _find_manifest_triplet | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| _normalize_rows | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| _existing | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| _find_anchor_root | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| _normalize | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| _wrap_deg | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| _angle_deg | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| _resolve_device | #7-4 | 7 Full Prepose Build | `DOC-C12-02` |
| _pick_pred_array | #7-4 | 7 Full Prepose Build | `DOC-C12-02` |
| main | #7-4 | 7 Full Prepose Build | `DOC-C12-02` |
| resolve_matching_chunk_names | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| resolve_chunk_artifact | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| to_4x4_batch | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| normalize_rows | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| angle_deg | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| lens_direction_from_c2w | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| up_direction_from_c2w | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| c2w_list_from_extrinsics | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| estimate_pose_aware_similarity | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| transform_c2w_list | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| pose_rows_to_frame_df | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| plot_pose_match | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| write_pose_match_html | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| to_4x4_batch | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| normalize_rows | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| angle_deg | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| summarize_split_metrics | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| lens_direction_from_c2w | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| up_direction_from_c2w | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| normalize_vec | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| build_anchor_c2w_list | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| local_c2w_list | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| estimate_pose_aware_similarity | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| transform_c2w_list | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| summarize_candidate | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| pick_selected_candidate | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| _existing | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| _find_anchor_diag_root | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| _existing | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| _find_anchor_root | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| _pick_first_existing | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| _resolve_center_cols | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| _resolve_lens_cols | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| ensure_target_chunk_manifest | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| resolve_chunk_output_dir | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| resolve_chunk_input_dir | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| path_size_bytes | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |

## Variable Inventory

| name | token | heading | docs_id |
| --- | --- | --- | --- |
| CONFIG | #2-1 | 2 Config | `DOC-C02-01` |
| OAI_SHORTCUT_ID | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| SHORTCUT_ROOT | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| RAW_SCAN_ROOTS | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| RESULTS_ROOT_CANDIDATES | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| RESULTS_ROOT | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| EXTRACT_ROOT | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| RUNBOOK_CANDIDATE_DOC | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| RUNBOOK_SELECTED_DOC | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| RUNBOOK_PATHS_DOC | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| CONFIG_SNAPSHOT | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| PIPELINE_SLUG | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| candidate_doc | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| selected | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| session_id_hint | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| candidate_index_hint | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| policy | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| resolved | #3-1 | 3 Input Select And Path Check | `DOC-C03-01` |
| paths | #4-1 | 4 Tree Init | `DOC-C04-01` |
| selected_path | #4-1 | 4 Tree Init | `DOC-C04-01` |
| selected_kind | #4-1 | 4 Tree Init | `DOC-C04-01` |
| session_id | #4-1 | 4 Tree Init | `DOC-C04-01` |
| results_root | #4-1 | 4 Tree Init | `DOC-C04-01` |
| session_root | #4-1 | 4 Tree Init | `DOC-C04-01` |
| session_outer | #4-1 | 4 Tree Init | `DOC-C04-01` |
| images_dir | #4-1 | 4 Tree Init | `DOC-C04-01` |
| frame_record_path | #4-1 | 4 Tree Init | `DOC-C04-01` |
| frame_pose_index_path | #4-1 | 4 Tree Init | `DOC-C04-01` |
| config | #4-1 | 4 Tree Init | `DOC-C04-01` |
| route_slug | #4-1 | 4 Tree Init | `DOC-C04-01` |
| pipeline_slug | #4-1 | 4 Tree Init | `DOC-C04-01` |
| legacy_source_pipeline_slug | #4-1 | 4 Tree Init | `DOC-C04-01` |
| modeling_session_id | #4-1 | 4 Tree Init | `DOC-C04-01` |
| probe_root_name | #4-1 | 4 Tree Init | `DOC-C04-01` |
| probe_root | #4-1 | 4 Tree Init | `DOC-C04-01` |
| pipeline_root | #4-1 | 4 Tree Init | `DOC-C04-01` |
| merged_dir | #4-1 | 4 Tree Init | `DOC-C04-01` |
| da3_nested_dir | #4-1 | 4 Tree Init | `DOC-C04-01` |
| da3_nested_gs_dir | #4-1 | 4 Tree Init | `DOC-C04-01` |
| world_dir | #4-1 | 4 Tree Init | `DOC-C04-01` |
| manifest_dir | #4-1 | 4 Tree Init | `DOC-C04-01` |
| final_outputs_dir | #4-1 | 4 Tree Init | `DOC-C04-01` |
| final_outputs_merged_dir | #4-1 | 4 Tree Init | `DOC-C04-01` |
| final_outputs_diagnostics_dir | #4-1 | 4 Tree Init | `DOC-C04-01` |
| final_outputs_manifests_dir | #4-1 | 4 Tree Init | `DOC-C04-01` |
| final_outputs_chunk_evidence_dir | #4-1 | 4 Tree Init | `DOC-C04-01` |
| reset_before_run | #4-1 | 4 Tree Init | `DOC-C04-01` |
| context_doc | #4-1 | 4 Tree Init | `DOC-C04-01` |
| ctx | #4-2 | 4 Tree Init | `DOC-C04-02` |
| probe_root | #4-2 | 4 Tree Init | `DOC-C04-02` |
| managed_dirs | #4-2 | 4 Tree Init | `DOC-C04-02` |
| repo_root | #5-1 | 5 Install | `DOC-C05-01` |
| repo_url | #5-1 | 5 Install | `DOC-C05-01` |
| src_root | #5-1 | 5 Install | `DOC-C05-01` |
| RUNBOOK_CTX_PATH | #6-1 | 6 Shared Helpers | `DOC-C06-01` |
| ctx | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| images_dir | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| frame_record_path | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| frame_pose_index_path | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| manifest_dir | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| CANONICAL_ORIENTATION_POLICY | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| BLUR_THRESHOLD | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| frame_pose_df | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| image_name_by_record_index | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| image_dir_ranking | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| resolved_images_dir | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| rows | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| manifest_df | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| qc_df | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| adopt_df | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| adopted_rows | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| last_t | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| last_R | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| anchor_input_df | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| selected_df | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| Ks | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| exts | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| k_check | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| orientation_summary | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| summary | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| extrinsics_source_summary | #9-1 | 9 Record Manifest And Chunk Plan | `DOC-C09-01` |
| ctx | #9-2 | 9 Record Manifest And Chunk Plan | `DOC-C09-02` |
| manifest_dir | #9-2 | 9 Record Manifest And Chunk Plan | `DOC-C09-02` |
| managed_dirs | #9-2 | 9 Record Manifest And Chunk Plan | `DOC-C09-02` |
| record_dir | #9-2 | 9 Record Manifest And Chunk Plan | `DOC-C09-02` |
| anchor_diag | #9-2 | 9 Record Manifest And Chunk Plan | `DOC-C09-02` |
| anchor_keep_cols | #9-2 | 9 Record Manifest And Chunk Plan | `DOC-C09-02` |
| anchor_join | #9-2 | 9 Record Manifest And Chunk Plan | `DOC-C09-02` |
| p | #9-2 | 9 Record Manifest And Chunk Plan | `DOC-C09-02` |
| df | #9-2 | 9 Record Manifest And Chunk Plan | `DOC-C09-02` |
| ts_col | #9-2 | 9 Record Manifest And Chunk Plan | `DOC-C09-02` |
| df | #9-2 | 9 Record Manifest And Chunk Plan | `DOC-C09-02` |
| config | #9-3 | 9 Record Manifest And Chunk Plan | `DOC-C09-03` |
| config_view | #9-3 | 9 Record Manifest And Chunk Plan | `DOC-C09-03` |
| ctx | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| config_snapshot | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| manifest_dir | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| persist_root | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| pipeline_slug | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| pipeline_root | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| anchor_dir | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| chunk_manifest_dir | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| batch_runs_dir | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| merged_dir | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| MODEL_ID | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| BUNDLE_MODEL_SLUG | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| PROCESS_RES | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| CHUNK_SIZE | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| CHUNK_STEP | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| ADOPT_SIZE | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| BATCH_SIZE | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| config | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| input_manifest_path | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| intrinsics_path | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| extrinsics_path | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| input_df | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| input_extrinsics | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| chunks | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| start_pos | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| chunk_id | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| all_chunks_df | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| chunk_index_all_path | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| target_mode | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| target_ids_1based | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| chunk_index_target_path | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| batch_rows | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| batch_count | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| batch_plan_df | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| batch_plan_path | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| camera_anchor_full_path | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| anchor_df | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| chunk_sequence_anchor_index_rows | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| chunk_sequence_anchor_index_df | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| chunk_sequence_anchor_index_path | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| summary | #9-4 | 9 Record Manifest And Chunk Plan | `DOC-C09-04` |
| ctx | #9-5 | 9 Record Manifest And Chunk Plan | `DOC-C09-05` |
| probe_root | #9-5 | 9 Record Manifest And Chunk Plan | `DOC-C09-05` |
| pipeline_root | #9-5 | 9 Record Manifest And Chunk Plan | `DOC-C09-05` |
| chunk_manifest_dir | #9-5 | 9 Record Manifest And Chunk Plan | `DOC-C09-05` |
| record_manifest_path | #9-5 | 9 Record Manifest And Chunk Plan | `DOC-C09-05` |
| record_df | #9-5 | 9 Record Manifest And Chunk Plan | `DOC-C09-05` |
| chunk_index_path | #9-5 | 9 Record Manifest And Chunk Plan | `DOC-C09-05` |
| chunk_index_df | #9-5 | 9 Record Manifest And Chunk Plan | `DOC-C09-05` |
| rows | #9-5 | 9 Record Manifest And Chunk Plan | `DOC-C09-05` |
| out | #9-5 | 9 Record Manifest And Chunk Plan | `DOC-C09-05` |
| ctx | #10-1 | 10 Precheck | `DOC-C10-01` |
| config_snapshot | #10-1 | 10 Precheck | `DOC-C10-01` |
| manifest_dir | #10-1 | 10 Precheck | `DOC-C10-01` |
| persist_root | #10-1 | 10 Precheck | `DOC-C10-01` |
| pipeline_slug | #10-1 | 10 Precheck | `DOC-C10-01` |
| pipeline_root | #10-1 | 10 Precheck | `DOC-C10-01` |
| chunk_manifest_dir | #10-1 | 10 Precheck | `DOC-C10-01` |
| chunk_index_all_path | #10-1 | 10 Precheck | `DOC-C10-01` |
| chunk_index_df | #10-1 | 10 Precheck | `DOC-C10-01` |
| rows | #10-1 | 10 Precheck | `DOC-C10-01` |
| precheck_df | #10-1 | 10 Precheck | `DOC-C10-01` |
| precheck_path | #10-1 | 10 Precheck | `DOC-C10-01` |
| bad_chunk_count | #10-1 | 10 Precheck | `DOC-C10-01` |
| ctx | #10-2 | 10 Precheck | `DOC-C10-02` |
| pipeline_root | #10-2 | 10 Precheck | `DOC-C10-02` |
| chunk_manifest_dir | #10-2 | 10 Precheck | `DOC-C10-02` |
| idx_df | #10-2 | 10 Precheck | `DOC-C10-02` |
| rows | #10-2 | 10 Precheck | `DOC-C10-02` |
| edge_df | #10-2 | 10 Precheck | `DOC-C10-02` |
| out | #10-2 | 10 Precheck | `DOC-C10-02` |
| config | #10-3 | 10 Precheck | `DOC-C10-03` |
| ctx | #10-3 | 10 Precheck | `DOC-C10-03` |
| persist_root | #10-3 | 10 Precheck | `DOC-C10-03` |
| run_dir | #10-3 | 10 Precheck | `DOC-C10-03` |
| manifest_dir | #10-3 | 10 Precheck | `DOC-C10-03` |
| anchor_dir | #10-3 | 10 Precheck | `DOC-C10-03` |
| anchor_qc_path | #10-3 | 10 Precheck | `DOC-C10-03` |
| sequence_precheck_path | #10-3 | 10 Precheck | `DOC-C10-03` |
| edge_validation_path | #10-3 | 10 Precheck | `DOC-C10-03` |
| anchor_qc_df | #10-3 | 10 Precheck | `DOC-C10-03` |
| sequence_df | #10-3 | 10 Precheck | `DOC-C10-03` |
| edge_df | #10-3 | 10 Precheck | `DOC-C10-03` |
| ROLL_CENTER_WARN_DEG | #10-3 | 10 Precheck | `DOC-C10-03` |
| PITCH_MIN_WARN_DEG | #10-3 | 10 Precheck | `DOC-C10-03` |
| PITCH_MAX_WARN_DEG | #10-3 | 10 Precheck | `DOC-C10-03` |
| YAW_JUMP_FAIL_DEG | #10-3 | 10 Precheck | `DOC-C10-03` |
| bad_sequence_chunk_count | #10-3 | 10 Precheck | `DOC-C10-03` |
| edge_fail_cols | #10-3 | 10 Precheck | `DOC-C10-03` |
| summary | #10-3 | 10 Precheck | `DOC-C10-03` |
| summary_path | #10-3 | 10 Precheck | `DOC-C10-03` |
| ctx | #11-1 | 11 Run Preparation | `DOC-C11-01` |
| manifest_dir | #11-1 | 11 Run Preparation | `DOC-C11-01` |
| batch_plan_df | #11-1 | 11 Run Preparation | `DOC-C11-01` |
| chunk_all_df | #11-1 | 11 Run Preparation | `DOC-C11-01` |
| chunk_target_df | #11-1 | 11 Run Preparation | `DOC-C11-01` |
| ctx | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| probe_root | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| pipeline_root | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| chunk_manifest_dir | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| chunk_runs_dir | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| test_chunk_with_batch_path | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| test_batch_plan_path | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| canonical_chunk_with_batch_path | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| canonical_batch_plan_path | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| fallback_chunk_target_path | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| fallback_batch_plan_path | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| execution_chunks_df | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| execution_batch_plan_df | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| chunk_name_col | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| execution_chunk_out | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| execution_batch_out | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| summary | #11-3 | 11 Run Preparation | `DOC-C11-03` |
| ctx | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| probe_root | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| pipeline_root | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| chunk_manifest_dir | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| chunk_runs_dir | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| manifest_dir | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| persist_root | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| anchor_dir | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| merged_dir | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| final_outputs_dir | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| final_outputs_diagnostics_dir | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| final_outputs_manifests_dir | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| final_outputs_chunk_evidence_dir | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| final_outputs_merged_dir | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| execution_chunks_path | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| execution_batch_plan_path | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| target_chunks_df | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| batch_plan_df | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| chunk_name_col | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| batch_names | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| config_snapshot | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| delete_targets | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| reset_summary | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| record_manifest_path | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| anchor_pose_diag_path | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| anchor_qc_path | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| sequence_precheck_path | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| edge_validation_path | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| required_paths | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| missing_required | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| record_df | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| anchor_pose_df | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| anchor_qc_df | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| sequence_df | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| edge_df | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| record_count_match | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| sequence_bad_count | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| edge_bad_chunk_count | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| anchor_fail_count | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| image_path_col | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| missing_images | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| preflight | #11-4 | 11 Run Preparation | `DOC-C11-04` |
| ctx | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| probe_root | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| pipeline_root | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| chunk_manifest_dir | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| chunk_runs_dir | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| final_outputs_diagnostics_dir | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| execution_chunks_path | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| execution_batch_plan_path | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| execution_chunks_df | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| execution_batch_plan_df | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| batch_execution_items_df | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| batch_execution_items_path | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| batch_manifest_rows | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| batch_manifests_df | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| batch_manifests_path | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| summary | #11-5 | 11 Run Preparation | `DOC-C12-01` |
| ctx_path | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| ctx | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| manifest_dir | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| da3_nested_dir | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| world_dir | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| final_outputs_dir | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| final_outputs_merged_dir | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| final_outputs_diagnostics_dir | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| final_outputs_manifests_dir | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| final_outputs_chunk_evidence_dir | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| images_dir | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| frame_record_path | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| frame_pose_index_path | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| repo_root | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| repo_url | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| src_root | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| required_files | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| CANONICAL_ORIENTATION_POLICY | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| BLUR_THRESHOLD | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| missing_required | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| manifest_df | #7-1 | 7 Full Prepose Build | `DOC-C07-01` |
| config | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| search_roots | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| anchor_dir | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| manifest_dir | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| manifest_df | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| intrinsics | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| extrinsics_w2c | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| c2w | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| camera_centers | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| right_vecs | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| up_vecs | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| lens_vecs | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| right_vecs | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| up_vecs | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| lens_vecs | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| camera_center_df | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| camera_orientation_df | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| camera_anchor_full_df | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| camera_matrix_full_csv | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| camera_center_matrix_csv | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| camera_orientation_full_csv | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| camera_anchor_full_csv | #7-2 | 7 Full Prepose Build | `DOC-C07-02` |
| config | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| search_roots | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| persist_root | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| anchor_dir | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| anchor_path | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| anchor_df | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| required_cols | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| missing | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| lens | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| up | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| right | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| centers | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| lens | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| up | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| right | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| yaw_deg | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| pitch_deg | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| world_up | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| proj_world_up | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| proj_up | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| proj_world_up | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| proj_up | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| cross_u | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| sign_roll | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| dot_roll | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| roll_deg | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| delta_yaw_deg | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| delta_pitch_deg | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| delta_roll_deg | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| delta_pos | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| delta_lens_angle_deg | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| delta_up_angle_deg | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| delta2_pos | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| delta2_rot | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| anchor_pose_diag_df | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| diag_csv | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| summary | #7-3 | 7 Full Prepose Build | `DOC-C07-03` |
| REPO_ROOT | #7-4 | 7 Full Prepose Build | `DOC-C12-02` |
| SRC_ROOT | #7-4 | 7 Full Prepose Build | `DOC-C12-02` |
| ctx | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| probe_root | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| pipeline_root | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| chunk_manifest_dir | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| chunk_runs_dir | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| final_outputs_diagnostics_dir | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| wrapper_path | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| batch_execution_items_path | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| items_df | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| config_snapshot | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| DRY_RUN | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| DEVICE | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| MODEL_ID | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| PROCESS_RES | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| PROCESS_RES_METHOD | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| EXPORT_FORMAT | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| ALIGN_TO_INPUT_EXT_SCALE | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| INFER_GS | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| SHOW_CAMERAS | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| CONF_THRESH_PERCENTILE | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| NUM_MAX_POINTS | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| SKIP_ALREADY_SUCCESS | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| required_cols | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| missing_cols | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| rows | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| run_df | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| run_csv | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| summary | #7-5 | 7 Full Prepose Build | `DOC-C12-03` |
| ctx | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| config | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| probe_root | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| persist_root | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| pipeline_root | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| anchor_dir | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| chunk_manifest_dir | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| chunk_runs_dir | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| final_outputs_chunk_evidence_dir | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| final_outputs_diagnostics_dir | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| matching_dir | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| LOCAL_EXTRINSIC_MODE | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| LOCAL_CAMERA_BASIS | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| TRANSFORM_SCALE_MIN | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| TRANSFORM_SCALE_MAX | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| TRANSFORM_CENTER_RMSE_MAX | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| TRANSFORM_ROT_DIR_MAX | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| chunk_a_frames_path | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| chunk_a_pred_path | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| chunk_b_frames_path | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| chunk_b_pred_path | #7-6 | 7 Full Prepose Build | `DOC-C07M-01` |
| ctx | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| probe_root | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| persist_root | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| pipeline_root | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| chunk_manifest_dir | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| chunk_runs_dir | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| merged_dir | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| final_outputs_diagnostics_dir | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| anchor_dir | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| camera_anchor_full_path | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| batch_execution_items_path | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| items_df | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| sort_cols | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| anchor_full_df | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| required_anchor_cols | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| missing_anchor_cols | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| ROUTE_ARCORE | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| ROUTE_DA3 | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| PREFERRED_ROUTE_LABEL | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| LOCAL_EXTRINSIC_MODE | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| LOCAL_CAMERA_BASIS | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| PREMERGE_CENTER_ERROR_P95_MAX | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| PREMERGE_LENS_ERROR_DEG_P95_MAX | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| PREMERGE_DELTA_CENTER_ERROR_MAX | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| PREMERGE_DELTA_LENS_ERROR_DEG_MAX | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| TRANSFORM_SCALE_MIN | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| TRANSFORM_SCALE_MAX | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| TRANSFORM_CENTER_RMSE_MAX | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| TRANSFORM_ROT_DIR_MAX | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| route_world_pose_map | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| candidate_rows | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| selected_rows | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| graph_solution_rows | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| graph_edge_rows | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| residual_frames | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| missing_pred_chunks | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| previous_selected_chunk_name | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| previous_selected_T | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| candidate_df | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| route_compare_csv | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| residual_df | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| residual_csv | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| missing_pred_df | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| missing_pred_csv | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| validation_df | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| validation_csv | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| gate_csv | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| graph_solution_df | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| graph_solution_csv | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| graph_edges_df | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| graph_edges_csv | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| validation_json | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| route_compare_json | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| graph_summary_json | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| hard_fail_df | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| route_counts | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| fallback_count | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| route_compare_summary | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| graph_summary | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| summary | #7-7 | 7 Full Prepose Build | `DOC-C07-07` |
| config | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| search_roots | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| persist_root | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| anchor_dir | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| diag_path | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| df | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| MAX_DELTA_POS | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| MAX_DELTA_LENS_ANGLE_DEG | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| MAX_DELTA_UP_ANGLE_DEG | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| MAX_DELTA2_POS | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| MAX_DELTA2_ROT | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| WARN_ABS_ROLL_CENTERED_DEG | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| WARN_PITCH_MIN_DEG | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| WARN_PITCH_MAX_DEG | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| fail_df | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| warn_df | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| qc_csv | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| fail_csv | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| warn_csv | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| summary | #8-1 | 8 Anchor QC And Plot | `DOC-C08-01` |
| config | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| search_roots | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| persist_root | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| anchor_dir | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| anchor_csv | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| df | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| lens_cols | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| plotly_html | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| plotly_png | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| centers | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| bbox_min | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| bbox_max | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| diag | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| arrow_scale | #8-2 | 8 Anchor QC And Plot | `DOC-C08-02` |
| ctx | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| probe_root | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| pipeline_root | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| chunk_manifest_dir | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| merged_dir | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| final_outputs_diagnostics_dir | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| validation_json | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| route_compare_json | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| route_compare_csv | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| graph_solution_csv | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| graph_edges_csv | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| graph_summary_json | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| batch_execution_items_path | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| required_paths | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| missing_paths | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| validation | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| route_compare_summary | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| graph_summary | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| validation_df | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| route_compare_df | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| graph_edges_df | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| status | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| selected_route_counts | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| preferred_route_label | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| preferred_fallback_used_count | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| review_summary | #13-1 | 13 Prepose Graph Judge | `DOC-C13-01` |
| missing_merge_deps | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| batch_preflight_status_path | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| ctx | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| probe_root | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| results_root | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| persist_root | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| modeling_session_id | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| manifest_dir | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| final_outputs_dir | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| final_outputs_merged_dir | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| final_outputs_diagnostics_dir | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| final_outputs_manifests_dir | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| final_outputs_chunk_evidence_dir | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| pipeline_root | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| anchor_dir | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| chunk_manifest_dir | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| chunk_runs_dir | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| merged_dir | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| stage_11_2_dir | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| stage_11_3_dir | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| config_path | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| BUNDLE_MODEL_SLUG | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| REQUIRE_ALL_CHUNKS | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| config_snapshot | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| MAKE_DRIVE_BUNDLE | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| INFER_GS | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| batch_execution_items_path | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| TRANSFORM_SCALE_MIN | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| TRANSFORM_SCALE_MAX | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| TRANSFORM_CENTER_RMSE_MAX | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| TRANSFORM_ROT_DIR_MAX | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| ROUTE_ARCORE | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| ROUTE_DA3 | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| PREFERRED_ROUTE_LABEL | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| LOCAL_EXTRINSIC_MODE | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| LOCAL_CAMERA_BASIS | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| chunk_index_all_path | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| all_chunks_df | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| target_chunks_df | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| completed_chunk_names | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| pred_ready_chunk_names | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| ply_ready_chunk_names | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| completed_chunk_names | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| pred_ready_chunk_names | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| ply_ready_chunk_names | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| completed_chunks_df | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| pred_ready_target_chunk_names | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| ply_ready_target_chunk_names | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| batch_summaries | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| summary_rows | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| premerge_pose_validation_path | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| premerge_pose_validation | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| premerge_route_compare_path | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| prepose_chunk_graph_solution_path | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| prepose_chunk_graph_edges_path | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| prepose_chunk_graph_summary_path | #14-1 | 14 Merge From Prepose Graph | `DOC-C14-01` |
| merge_summary_path | #15-1 | 15 Optional Bundle | `DOC-C15-01` |
| ctx | #15-1 | 15 Optional Bundle | `DOC-C15-01` |
| probe_root | #15-1 | 15 Optional Bundle | `DOC-C15-01` |
| pipeline_root | #15-1 | 15 Optional Bundle | `DOC-C15-01` |
| merged_dir | #15-1 | 15 Optional Bundle | `DOC-C15-01` |
| pipeline_config_path | #15-1 | 15 Optional Bundle | `DOC-C15-01` |
| bundle_model_slug | #15-1 | 15 Optional Bundle | `DOC-C15-01` |
| merge_summary_doc_path | #15-1 | 15 Optional Bundle | `DOC-C15-01` |
| merge_summary | #15-1 | 15 Optional Bundle | `DOC-C15-01` |
| config_snapshot | #15-1 | 15 Optional Bundle | `DOC-C15-01` |
| download_local_bundle | #15-1 | 15 Optional Bundle | `DOC-C15-01` |
| local_bundle_base | #15-1 | 15 Optional Bundle | `DOC-C15-01` |
| local_bundle_zip | #15-1 | 15 Optional Bundle | `DOC-C15-01` |
| bundle_download_summary | #15-1 | 15 Optional Bundle | `DOC-C15-01` |
| ctx | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| probe_root | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| results_root | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| persist_root | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| manifest_dir | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| da3_nested_dir | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| da3_nested_gs_dir | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| world_dir | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| final_outputs_dir | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| final_outputs_merged_dir | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| final_outputs_diagnostics_dir | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| final_outputs_manifests_dir | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| final_outputs_chunk_evidence_dir | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| pipeline_root | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| anchor_dir | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| chunk_manifest_dir | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| chunk_runs_dir | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| merged_dir | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| merge_summary_path | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| merge_summary | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| merge_ok | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| kept_groups | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| delete_candidates | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| local_tmp_candidates | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| local_bundle_download_summary_path | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| local_bundle_zip | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| cleanup_plan | #16-1 | 16 Cleanup Inventory | `DOC-C16-01` |
| ctx | #16-2 | 16 Cleanup Inventory | `DOC-C16-02` |
| pipeline_root | #16-2 | 16 Cleanup Inventory | `DOC-C16-02` |
| merged_dir | #16-2 | 16 Cleanup Inventory | `DOC-C16-02` |
| cleanup_plan_path | #16-2 | 16 Cleanup Inventory | `DOC-C16-02` |
| cleanup_plan | #16-2 | 16 Cleanup Inventory | `DOC-C16-02` |
| rows | #16-2 | 16 Cleanup Inventory | `DOC-C16-02` |
| cleanup_csv | #16-2 | 16 Cleanup Inventory | `DOC-C16-02` |
| ctx | #17-1 | 17 Cleanup Apply | `DOC-C17-01` |
| probe_root | #17-1 | 17 Cleanup Apply | `DOC-C17-01` |
| pipeline_root | #17-1 | 17 Cleanup Apply | `DOC-C17-01` |
| merged_dir | #17-1 | 17 Cleanup Apply | `DOC-C17-01` |
| cleanup_plan_path | #17-1 | 17 Cleanup Apply | `DOC-C17-01` |
| cleanup_csv_path | #17-1 | 17 Cleanup Apply | `DOC-C17-01` |
| cleanup_plan | #17-1 | 17 Cleanup Apply | `DOC-C17-01` |
| review_df | #17-1 | 17 Cleanup Apply | `DOC-C17-01` |
| reviewed_paths | #17-1 | 17 Cleanup Apply | `DOC-C17-01` |
| other_dir | #17-1 | 17 Cleanup Apply | `DOC-C17-01` |
| deleted | #17-1 | 17 Cleanup Apply | `DOC-C17-01` |
| moved_to_other | #17-1 | 17 Cleanup Apply | `DOC-C17-01` |
| kept | #17-1 | 17 Cleanup Apply | `DOC-C17-01` |
| cleanup_result | #17-1 | 17 Cleanup Apply | `DOC-C17-01` |
