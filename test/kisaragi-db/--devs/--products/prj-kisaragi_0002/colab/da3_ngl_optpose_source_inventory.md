# da3_ngl_optpose_RB source inventory

この文書は `da3_optpose_sources/cell_manifest.json` と `da3_optpose_sources/markdown_manifest.json` を基準に、`da3_ngl_optpose_RB.md` / `da3_ngl_optpose_RB.ipynb` の source 一覧を示す。

## Cell Inventory

| token | source_file | kind | heading | functions | top_level_variables | docs_id |
| --- | --- | --- | --- | --- | --- | --- |
| #1-1 | `cells/01_01.py` | `direct` | 1 Runtime Bootstrap | - | - | `DOC-O01-01` |
| #2-1 | `cells/02_01.py` | `direct` | 2 Config | - | CONFIG | `DOC-O02-01` |
| #3-1 | `cells/03_01.py` | `direct` | 3 Input Select And Path Check | slugify_name, infer_session_id, scan_candidates, reset_extract_root, extract_selected_input, pick_best_raw_root, resolve_and_validate_paths | OAI_SHORTCUT_ID, SHORTCUT_ROOT, RAW_SCAN_ROOTS, RESULTS_ROOT_CANDIDATES, RESULTS_ROOT, EXTRACT_ROOT, RUNBOOK_CANDIDATE_DOC, RUNBOOK_SELECTED_DOC, RUNBOOK_PATHS_DOC, CONFIG_SNAPSHOT, PIPELINE_SLUG, candidate_doc | `DOC-O03-01` |
| #4-1 | `cells/04_01.py` | `direct` | 4 Tree Init | write_json, ensure_tree_pointer | paths, selected_path, selected_kind, session_id, results_root, session_root, session_outer, images_dir, frame_record_path, frame_pose_index_path, config, route_slug | `DOC-O04-01` |
| #4-2 | `cells/04_02.py` | `direct` | 4 Tree Init | - | ctx, probe_root, run_root, canonical_dirs, managed_dirs, compatibility_aliases, doc | `DOC-O04-02` |
| #5-1 | `cells/05_01.py` | `direct` | 5 Install | - | repo_root, repo_url, src_root | `DOC-O05-01` |
| #6-1 | `cells/06_01.py` | `direct` | 6 Shared Helpers | load_ctx, save_json, append_sequence_columns, rotmat_to_rpy_deg, _summary_rows, display_stage_summary, rotation_angle_deg_from_matrix, summarize_relative_transform | RUNBOOK_CTX_PATH | `DOC-O06-01` |
| #6-2 | `cells/06_02.py` | `direct` | 6 Shared Helpers | load_json, to_4x4_batch, normalize_rows, angle_deg, lens_direction_from_c2w, up_direction_from_c2w, estimate_pose_aware_similarity, transform_c2w_list | - | `DOC-O06-02` |
| #7-1 | `cells/07_01.py` | `direct` | 7 Full Anchor Build | build_anchor_inputs_from_zip | ctx_path, ctx, manifest_dir, da3_nested_dir, world_dir, final_outputs_dir, final_outputs_merged_dir, final_outputs_diagnostics_dir, final_outputs_manifests_dir, final_outputs_chunk_evidence_dir, images_dir, frame_record_path | `DOC-O07-01` |
| #7-2 | `cells/07_02.py` | `direct` | 7 Full Anchor Build | _existing, _find_manifest_triplet, _normalize_rows | config, search_roots, anchor_dir, manifest_dir, manifest_df, intrinsics, extrinsics_w2c, c2w, camera_centers, right_vecs, up_vecs, lens_vecs | `DOC-O07-02` |
| #7-3 | `cells/07_03.py` | `direct` | 7 Full Anchor Build | _existing, _find_anchor_root, _normalize, _wrap_deg, _angle_deg | config, search_roots, persist_root, anchor_dir, anchor_path, anchor_df, required_cols, missing, lens, up, right, centers | `DOC-O07-03` |
| #7-4 | `cells/07_04.py` | `direct` | 7 Full Anchor Build | _existing, _find_anchor_diag_root | config, search_roots, persist_root, anchor_dir, diag_path, df, MAX_DELTA_POS, MAX_DELTA_LENS_ANGLE_DEG, MAX_DELTA_UP_ANGLE_DEG, MAX_DELTA2_POS, MAX_DELTA2_ROT, WARN_ABS_ROLL_CENTERED_DEG | `DOC-O07-04` |
| #7-5 | `cells/07_05.py` | `direct` | 7 Full Anchor Build | _existing, _find_anchor_root, _pick_first_existing, _resolve_center_cols, _resolve_lens_cols | config, search_roots, persist_root, anchor_dir, anchor_csv, df, lens_cols, plotly_html, plotly_png, centers, bbox_min, bbox_max | `DOC-O07-05` |
| #8-1 | `cells/08_01.py` | `direct` | 8 Chunk Run Preparation And Execution | ranked_image_dirs, lap_var, read_actual_wh, normalize_intrinsics_to_upright, quat_to_rot, pose_to_w2c, build_K | ctx, images_dir, frame_record_path, frame_pose_index_path, manifest_dir, CANONICAL_ORIENTATION_POLICY, BLUR_THRESHOLD, frame_pose_df, image_name_by_record_index, image_dir_ranking, resolved_images_dir, rows | `DOC-O08-01` |
| #8-2 | `cells/08_02.py` | `direct` | 8 Chunk Run Preparation And Execution | - | ctx, manifest_dir, managed_dirs, record_dir, p, df, ts_col, df | `DOC-O08-02` |
| #8-3 | `cells/08_03.py` | `direct` | 8 Chunk Run Preparation And Execution | sha256_file, to_4x4 | ctx, config_snapshot, manifest_dir, persist_root, pipeline_slug, pipeline_root, anchor_dir, chunk_manifest_dir, batch_runs_dir, merged_dir, MODEL_ID, BUNDLE_MODEL_SLUG | `DOC-O08-03` |
| #8-4 | `cells/08_04.py` | `direct` | 8 Chunk Run Preparation And Execution | - | ctx, config_snapshot, manifest_dir, persist_root, pipeline_slug, pipeline_root, chunk_manifest_dir, chunk_index_all_path, chunk_index_df, rows, precheck_df, precheck_path | `DOC-O08-04` |
| #8-5 | `cells/08_05.py` | `direct` | 8 Chunk Run Preparation And Execution | - | ctx, probe_root, pipeline_root, chunk_manifest_dir, chunk_runs_dir, test_chunk_with_batch_path, test_batch_plan_path, canonical_chunk_with_batch_path, canonical_batch_plan_path, fallback_chunk_target_path, fallback_batch_plan_path, execution_chunks_df | `DOC-O08-05` |
| #8-6 | `cells/08_06.py` | `direct` | 8 Chunk Run Preparation And Execution | - | ctx, probe_root, pipeline_root, chunk_manifest_dir, chunk_runs_dir, merged_dir, final_outputs_dir, final_outputs_diagnostics_dir, final_outputs_manifests_dir, final_outputs_chunk_evidence_dir, final_outputs_merged_dir, execution_chunks_path | `DOC-O08-06` |
| #8-7 | `cells/08_07.py` | `direct` | 8 Chunk Run Preparation And Execution | - | ctx, probe_root, pipeline_root, chunk_manifest_dir, chunk_runs_dir, final_outputs_diagnostics_dir, execution_chunks_path, execution_batch_plan_path, execution_chunks_df, execution_batch_plan_df, batch_execution_items_df, batch_execution_items_path | `DOC-O08-07` |
| #8-8 | `cells/08_08.py` | `direct` | 8 Chunk Run Preparation And Execution | - | repo_root, src_root, wrapper_path, wrapper_code | `DOC-O08-08` |
| #8-9 | `cells/08_09.py` | `direct` | 8 Chunk Run Preparation And Execution | - | ctx, probe_root, pipeline_root, chunk_manifest_dir, chunk_runs_dir, final_outputs_diagnostics_dir, wrapper_path, batch_execution_items_path, items_df, config_snapshot, DRY_RUN, DEVICE | `DOC-O08-09` |
| #9-1 | `cells/09_01.py` | `direct` | 9 Chunk Alignment Coefficient Derivation | resolve_matching_chunk_names, resolve_chunk_artifact, c2w_list_from_extrinsics, pose_rows_to_frame_df, plot_pose_match, write_pose_match_html | ctx, config, probe_root, persist_root, pipeline_root, anchor_dir, chunk_manifest_dir, chunk_runs_dir, final_outputs_chunk_evidence_dir, final_outputs_diagnostics_dir, matching_dir, LOCAL_EXTRINSIC_MODE | `DOC-O09-01` |
| #10-1 | `cells/10_01.py` | `direct` | 10 Global Prepose Graph And Gate | summarize_split_metrics, normalize_vec, build_anchor_c2w_list, local_c2w_list, transform_c2w_list, summarize_candidate, pick_selected_candidate, sim3_matrix_to_params, params_to_sim3_matrix, invert_sim3, compose_sim3, edge_transform_from_row, sim3_residual_vec, refine_graph_solution, recompute_solution_metrics | ctx, probe_root, persist_root, pipeline_root, chunk_manifest_dir, chunk_runs_dir, merged_dir, final_outputs_diagnostics_dir, anchor_dir, camera_anchor_full_path, batch_execution_items_path, items_df | `DOC-O10-01` |
| #10-2 | `cells/10_02.py` | `direct` | 10 Global Prepose Graph And Gate | - | ctx, probe_root, pipeline_root, chunk_manifest_dir, merged_dir, final_outputs_diagnostics_dir, validation_json, route_compare_json, route_compare_csv, graph_solution_csv, graph_edges_csv, graph_summary_json | `DOC-O10-02` |
| #11-1 | `cells/11_01.py` | `direct` | 11 Merge And Review | ensure_target_chunk_manifest, resolve_chunk_output_dir, resolve_chunk_input_dir | missing_merge_deps, batch_preflight_status_path, ctx, probe_root, results_root, persist_root, modeling_session_id, manifest_dir, final_outputs_dir, final_outputs_merged_dir, final_outputs_diagnostics_dir, final_outputs_manifests_dir | `DOC-O11-01` |
| #11-2 | `cells/11_02.py` | `direct` | 11 Merge And Review | _resolve_center_cols, _resolve_dir_cols, _load_transform_map, _resolve_chunk_output_dir, _sample_indices, _py_bool, _poses_to_centers_dirs | ctx, probe_root, persist_root, pipeline_root, chunk_manifest_dir, chunk_runs_dir, merged_dir, anchor_dir, anchor_path, graph_solution_path, transform_path, merged_camera_pose_path | `DOC-O11-02` |

## Markdown Inventory

| leading_token | source_file | target_ref | prev_ref | next_ref | heading |
| --- | --- | --- | --- | --- | --- |
| #1-1 | `markdown/01_01.md` | #1-1 | なし | #2-1 | 1 Runtime Bootstrap |
| #2-1 | `markdown/02_01.md` | #2-1 | #1-1 | #3-1 | 2 Config |
| #3-1 | `markdown/03_01.md` | #3-1 | #2-1 | #4-1..#4-2 | 3 Input Select And Path Check |
| #4-1 | `markdown/04_01.md` | #4-1 | #3-1 | #4-2 | 4 Tree Init |
| #4-2 | `markdown/04_02.md` | #4-2 | #4-1 | #5-1 | 4 Tree Init |
| #5-1 | `markdown/05_01.md` | #5-1 | #4-2 | #6-1 | 5 Install |
| #6-1 | `markdown/06_01.md` | #6-1 | #5-1 | #6-2 | 6 Shared Helpers |
| #6-2 | `markdown/06_02.md` | #6-2 | #6-1 | #7-1 | 6 Shared Helpers |
| #7-1 | `markdown/07_01.md` | #7-1 | #6-2 | #7-2 | 7 Full Anchor Build |
| #7-2 | `markdown/07_02.md` | #7-2 | #7-1 | #7-3 | 7 Full Anchor Build |
| #7-3 | `markdown/07_03.md` | #7-3 | #7-2 | #7-4 | 7 Full Anchor Build |
| #7-4 | `markdown/07_04.md` | #7-4 | #7-3 | #7-5 | 7 Full Anchor Build |
| #7-5 | `markdown/07_05.md` | #7-5 | #7-4 | #8-1 | 7 Full Anchor Build |
| #8-1 | `markdown/08_01.md` | #8-1 | #7-5 | #8-2 | 8 Chunk Run Preparation And Execution |
| #8-2 | `markdown/08_02.md` | #8-2 | #8-1 | #8-3 | 8 Chunk Run Preparation And Execution |
| #8-3 | `markdown/08_03.md` | #8-3 | #8-2 | #8-4 | 8 Chunk Run Preparation And Execution |
| #8-4 | `markdown/08_04.md` | #8-4 | #8-3 | #8-5 | 8 Chunk Run Preparation And Execution |
| #8-5 | `markdown/08_05.md` | #8-5 | #8-4 | #8-6 | 8 Chunk Run Preparation And Execution |
| #8-6 | `markdown/08_06.md` | #8-6 | #8-5 | #8-7 | 8 Chunk Run Preparation And Execution |
| #8-7 | `markdown/08_07.md` | #8-7 | #8-6 | #8-8 | 8 Chunk Run Preparation And Execution |
| #8-8 | `markdown/08_08.md` | #8-8 | #8-7 | #8-9 | 8 Chunk Run Preparation And Execution |
| #8-9 | `markdown/08_09.md` | #8-9 | #8-8 | #9-1 | 8 Chunk Run Preparation And Execution |
| #9-1 | `markdown/09_01.md` | #9-1 | #8-9 | #10-1 | 9 Chunk Alignment Coefficient Derivation |
| #10-1 | `markdown/10_01.md` | #10-1 | #9-1 | #10-2 | 10 Global Prepose Graph And Gate |
| #10-2 | `markdown/10_02.md` | #10-2 | #10-1 | #11-1 | 10 Global Prepose Graph And Gate |
| #11-1 | `markdown/11_01.md` | #11-1 | #10-2 | #11-2 | 11 Merge And Review |
| #11-2 | `markdown/11_02.md` | #11-2 | #11-1 | 終了 | 11 Merge And Review |

## Function And Class Inventory

| name | token | heading | docs_id |
| --- | --- | --- | --- |
| slugify_name | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| infer_session_id | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| scan_candidates | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| reset_extract_root | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| extract_selected_input | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| pick_best_raw_root | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| resolve_and_validate_paths | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| write_json | #4-1 | 4 Tree Init | `DOC-O04-01` |
| ensure_tree_pointer | #4-1 | 4 Tree Init | `DOC-O04-01` |
| load_ctx | #6-1 | 6 Shared Helpers | `DOC-O06-01` |
| save_json | #6-1 | 6 Shared Helpers | `DOC-O06-01` |
| append_sequence_columns | #6-1 | 6 Shared Helpers | `DOC-O06-01` |
| rotmat_to_rpy_deg | #6-1 | 6 Shared Helpers | `DOC-O06-01` |
| _summary_rows | #6-1 | 6 Shared Helpers | `DOC-O06-01` |
| display_stage_summary | #6-1 | 6 Shared Helpers | `DOC-O06-01` |
| rotation_angle_deg_from_matrix | #6-1 | 6 Shared Helpers | `DOC-O06-01` |
| summarize_relative_transform | #6-1 | 6 Shared Helpers | `DOC-O06-01` |
| load_json | #6-2 | 6 Shared Helpers | `DOC-O06-02` |
| to_4x4_batch | #6-2 | 6 Shared Helpers | `DOC-O06-02` |
| normalize_rows | #6-2 | 6 Shared Helpers | `DOC-O06-02` |
| angle_deg | #6-2 | 6 Shared Helpers | `DOC-O06-02` |
| lens_direction_from_c2w | #6-2 | 6 Shared Helpers | `DOC-O06-02` |
| up_direction_from_c2w | #6-2 | 6 Shared Helpers | `DOC-O06-02` |
| estimate_pose_aware_similarity | #6-2 | 6 Shared Helpers | `DOC-O06-02` |
| transform_c2w_list | #6-2 | 6 Shared Helpers | `DOC-O06-02` |
| build_anchor_inputs_from_zip | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| _existing | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| _find_manifest_triplet | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| _normalize_rows | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| _existing | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| _find_anchor_root | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| _normalize | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| _wrap_deg | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| _angle_deg | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| _existing | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| _find_anchor_diag_root | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| _existing | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| _find_anchor_root | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| _pick_first_existing | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| _resolve_center_cols | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| _resolve_lens_cols | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| ranked_image_dirs | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| lap_var | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| read_actual_wh | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| normalize_intrinsics_to_upright | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| quat_to_rot | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| pose_to_w2c | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| build_K | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| sha256_file | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| to_4x4 | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| resolve_matching_chunk_names | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| resolve_chunk_artifact | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| c2w_list_from_extrinsics | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| pose_rows_to_frame_df | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| plot_pose_match | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| write_pose_match_html | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| summarize_split_metrics | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| normalize_vec | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| build_anchor_c2w_list | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| local_c2w_list | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| transform_c2w_list | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| summarize_candidate | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| pick_selected_candidate | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| sim3_matrix_to_params | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| params_to_sim3_matrix | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| invert_sim3 | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| compose_sim3 | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| edge_transform_from_row | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| sim3_residual_vec | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| refine_graph_solution | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| recompute_solution_metrics | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| ensure_target_chunk_manifest | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| resolve_chunk_output_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| resolve_chunk_input_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| _resolve_center_cols | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| _resolve_dir_cols | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| _load_transform_map | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| _resolve_chunk_output_dir | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| _sample_indices | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| _py_bool | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| _poses_to_centers_dirs | #11-2 | 11 Merge And Review | `DOC-O11-02` |

## Variable Inventory

| name | token | heading | docs_id |
| --- | --- | --- | --- |
| CONFIG | #2-1 | 2 Config | `DOC-O02-01` |
| OAI_SHORTCUT_ID | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| SHORTCUT_ROOT | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| RAW_SCAN_ROOTS | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| RESULTS_ROOT_CANDIDATES | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| RESULTS_ROOT | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| EXTRACT_ROOT | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| RUNBOOK_CANDIDATE_DOC | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| RUNBOOK_SELECTED_DOC | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| RUNBOOK_PATHS_DOC | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| CONFIG_SNAPSHOT | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| PIPELINE_SLUG | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| candidate_doc | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| selected | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| session_id_hint | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| candidate_index_hint | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| policy | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| resolved | #3-1 | 3 Input Select And Path Check | `DOC-O03-01` |
| paths | #4-1 | 4 Tree Init | `DOC-O04-01` |
| selected_path | #4-1 | 4 Tree Init | `DOC-O04-01` |
| selected_kind | #4-1 | 4 Tree Init | `DOC-O04-01` |
| session_id | #4-1 | 4 Tree Init | `DOC-O04-01` |
| results_root | #4-1 | 4 Tree Init | `DOC-O04-01` |
| session_root | #4-1 | 4 Tree Init | `DOC-O04-01` |
| session_outer | #4-1 | 4 Tree Init | `DOC-O04-01` |
| images_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| frame_record_path | #4-1 | 4 Tree Init | `DOC-O04-01` |
| frame_pose_index_path | #4-1 | 4 Tree Init | `DOC-O04-01` |
| config | #4-1 | 4 Tree Init | `DOC-O04-01` |
| route_slug | #4-1 | 4 Tree Init | `DOC-O04-01` |
| pipeline_slug | #4-1 | 4 Tree Init | `DOC-O04-01` |
| modeling_session_id | #4-1 | 4 Tree Init | `DOC-O04-01` |
| probe_root_name | #4-1 | 4 Tree Init | `DOC-O04-01` |
| probe_root | #4-1 | 4 Tree Init | `DOC-O04-01` |
| tree_schema_version | #4-1 | 4 Tree Init | `DOC-O04-01` |
| run_id | #4-1 | 4 Tree Init | `DOC-O04-01` |
| run_timestamp_utc | #4-1 | 4 Tree Init | `DOC-O04-01` |
| runtime_root | #4-1 | 4 Tree Init | `DOC-O04-01` |
| validation_root | #4-1 | 4 Tree Init | `DOC-O04-01` |
| validation_runs_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| validation_current_alias | #4-1 | 4 Tree Init | `DOC-O04-01` |
| validation_latest_alias | #4-1 | 4 Tree Init | `DOC-O04-01` |
| run_root | #4-1 | 4 Tree Init | `DOC-O04-01` |
| run_runtime_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| run_validation_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| run_logs_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| run_config_snapshot_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| pipeline_root | #4-1 | 4 Tree Init | `DOC-O04-01` |
| chunk_manifest_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| chunk_runs_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| merged_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| da3_nested_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| da3_nested_gs_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| world_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| manifest_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| final_outputs_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| final_outputs_merged_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| final_outputs_diagnostics_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| final_outputs_manifests_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| final_outputs_chunk_evidence_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| delivery_root | #4-1 | 4 Tree Init | `DOC-O04-01` |
| delivery_releases_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| delivery_release_latest_alias | #4-1 | 4 Tree Init | `DOC-O04-01` |
| delivery_release_stable_alias | #4-1 | 4 Tree Init | `DOC-O04-01` |
| delivery_end_user_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| delivery_technical_reference_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| delivery_operator_private_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| legacy_root | #4-1 | 4 Tree Init | `DOC-O04-01` |
| migration_root | #4-1 | 4 Tree Init | `DOC-O04-01` |
| archive_root | #4-1 | 4 Tree Init | `DOC-O04-01` |
| validation_anchor_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| validation_records_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| validation_batch_plan_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| validation_chunk_runs_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| validation_merged_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| validation_manifest_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| validation_review_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| validation_other_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| runtime_extract_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| runtime_model_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| runtime_cleanup_dir | #4-1 | 4 Tree Init | `DOC-O04-01` |
| compatibility_aliases | #4-1 | 4 Tree Init | `DOC-O04-01` |
| reset_before_run | #4-1 | 4 Tree Init | `DOC-O04-01` |
| config_snapshot_path | #4-1 | 4 Tree Init | `DOC-O04-01` |
| config_hash | #4-1 | 4 Tree Init | `DOC-O04-01` |
| pointer_logs | #4-1 | 4 Tree Init | `DOC-O04-01` |
| context_doc | #4-1 | 4 Tree Init | `DOC-O04-01` |
| ctx | #4-2 | 4 Tree Init | `DOC-O04-02` |
| probe_root | #4-2 | 4 Tree Init | `DOC-O04-02` |
| run_root | #4-2 | 4 Tree Init | `DOC-O04-02` |
| canonical_dirs | #4-2 | 4 Tree Init | `DOC-O04-02` |
| managed_dirs | #4-2 | 4 Tree Init | `DOC-O04-02` |
| compatibility_aliases | #4-2 | 4 Tree Init | `DOC-O04-02` |
| doc | #4-2 | 4 Tree Init | `DOC-O04-02` |
| repo_root | #5-1 | 5 Install | `DOC-O05-01` |
| repo_url | #5-1 | 5 Install | `DOC-O05-01` |
| src_root | #5-1 | 5 Install | `DOC-O05-01` |
| RUNBOOK_CTX_PATH | #6-1 | 6 Shared Helpers | `DOC-O06-01` |
| ctx_path | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| ctx | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| manifest_dir | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| da3_nested_dir | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| world_dir | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| final_outputs_dir | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| final_outputs_merged_dir | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| final_outputs_diagnostics_dir | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| final_outputs_manifests_dir | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| final_outputs_chunk_evidence_dir | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| images_dir | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| frame_record_path | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| frame_pose_index_path | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| repo_root | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| repo_url | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| src_root | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| required_files | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| CANONICAL_ORIENTATION_POLICY | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| BLUR_THRESHOLD | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| missing_required | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| manifest_df | #7-1 | 7 Full Anchor Build | `DOC-O07-01` |
| config | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| search_roots | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| anchor_dir | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| manifest_dir | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| manifest_df | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| intrinsics | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| extrinsics_w2c | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| c2w | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| camera_centers | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| right_vecs | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| up_vecs | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| lens_vecs | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| right_vecs | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| up_vecs | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| lens_vecs | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| camera_center_df | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| camera_orientation_df | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| camera_anchor_full_df | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| camera_matrix_full_csv | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| camera_center_matrix_csv | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| camera_orientation_full_csv | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| camera_anchor_full_csv | #7-2 | 7 Full Anchor Build | `DOC-O07-02` |
| config | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| search_roots | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| persist_root | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| anchor_dir | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| anchor_path | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| anchor_df | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| required_cols | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| missing | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| lens | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| up | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| right | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| centers | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| lens | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| up | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| right | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| yaw_deg | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| pitch_deg | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| world_up | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| proj_world_up | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| proj_up | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| proj_world_up | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| proj_up | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| cross_u | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| sign_roll | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| dot_roll | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| roll_deg | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| delta_yaw_deg | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| delta_pitch_deg | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| delta_roll_deg | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| delta_pos | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| delta_lens_angle_deg | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| delta_up_angle_deg | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| delta2_pos | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| delta2_rot | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| anchor_pose_diag_df | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| diag_csv | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| summary | #7-3 | 7 Full Anchor Build | `DOC-O07-03` |
| config | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| search_roots | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| persist_root | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| anchor_dir | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| diag_path | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| df | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| MAX_DELTA_POS | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| MAX_DELTA_LENS_ANGLE_DEG | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| MAX_DELTA_UP_ANGLE_DEG | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| MAX_DELTA2_POS | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| MAX_DELTA2_ROT | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| WARN_ABS_ROLL_CENTERED_DEG | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| WARN_PITCH_MIN_DEG | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| WARN_PITCH_MAX_DEG | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| fail_df | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| warn_df | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| qc_csv | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| fail_csv | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| warn_csv | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| summary | #7-4 | 7 Full Anchor Build | `DOC-O07-04` |
| config | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| search_roots | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| persist_root | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| anchor_dir | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| anchor_csv | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| df | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| lens_cols | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| plotly_html | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| plotly_png | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| centers | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| bbox_min | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| bbox_max | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| diag | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| arrow_scale | #7-5 | 7 Full Anchor Build | `DOC-O07-05` |
| ctx | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| images_dir | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| frame_record_path | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| frame_pose_index_path | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| manifest_dir | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| CANONICAL_ORIENTATION_POLICY | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| BLUR_THRESHOLD | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| frame_pose_df | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| image_name_by_record_index | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| image_dir_ranking | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| resolved_images_dir | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| rows | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| manifest_df | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| qc_df | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| adopt_df | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| adopted_rows | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| last_t | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| last_R | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| anchor_input_df | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| selected_df | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| Ks | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| exts | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| k_check | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| orientation_summary | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| summary | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| extrinsics_source_summary | #8-1 | 8 Chunk Run Preparation And Execution | `DOC-O08-01` |
| ctx | #8-2 | 8 Chunk Run Preparation And Execution | `DOC-O08-02` |
| manifest_dir | #8-2 | 8 Chunk Run Preparation And Execution | `DOC-O08-02` |
| managed_dirs | #8-2 | 8 Chunk Run Preparation And Execution | `DOC-O08-02` |
| record_dir | #8-2 | 8 Chunk Run Preparation And Execution | `DOC-O08-02` |
| p | #8-2 | 8 Chunk Run Preparation And Execution | `DOC-O08-02` |
| df | #8-2 | 8 Chunk Run Preparation And Execution | `DOC-O08-02` |
| ts_col | #8-2 | 8 Chunk Run Preparation And Execution | `DOC-O08-02` |
| df | #8-2 | 8 Chunk Run Preparation And Execution | `DOC-O08-02` |
| ctx | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| config_snapshot | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| manifest_dir | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| persist_root | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| pipeline_slug | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| pipeline_root | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| anchor_dir | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| chunk_manifest_dir | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| batch_runs_dir | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| merged_dir | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| MODEL_ID | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| BUNDLE_MODEL_SLUG | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| PROCESS_RES | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| CHUNK_SIZE | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| CHUNK_STEP | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| ADOPT_SIZE | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| BATCH_SIZE | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| config | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| input_manifest_path | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| intrinsics_path | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| extrinsics_path | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| input_df | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| input_extrinsics | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| chunks | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| start_pos | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| chunk_id | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| all_chunks_df | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| chunk_index_all_path | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| target_mode | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| target_ids_1based | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| chunk_index_target_path | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| batch_rows | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| batch_count | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| batch_plan_df | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| batch_plan_path | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| run_manifest | #8-3 | 8 Chunk Run Preparation And Execution | `DOC-O08-03` |
| ctx | #8-4 | 8 Chunk Run Preparation And Execution | `DOC-O08-04` |
| config_snapshot | #8-4 | 8 Chunk Run Preparation And Execution | `DOC-O08-04` |
| manifest_dir | #8-4 | 8 Chunk Run Preparation And Execution | `DOC-O08-04` |
| persist_root | #8-4 | 8 Chunk Run Preparation And Execution | `DOC-O08-04` |
| pipeline_slug | #8-4 | 8 Chunk Run Preparation And Execution | `DOC-O08-04` |
| pipeline_root | #8-4 | 8 Chunk Run Preparation And Execution | `DOC-O08-04` |
| chunk_manifest_dir | #8-4 | 8 Chunk Run Preparation And Execution | `DOC-O08-04` |
| chunk_index_all_path | #8-4 | 8 Chunk Run Preparation And Execution | `DOC-O08-04` |
| chunk_index_df | #8-4 | 8 Chunk Run Preparation And Execution | `DOC-O08-04` |
| rows | #8-4 | 8 Chunk Run Preparation And Execution | `DOC-O08-04` |
| precheck_df | #8-4 | 8 Chunk Run Preparation And Execution | `DOC-O08-04` |
| precheck_path | #8-4 | 8 Chunk Run Preparation And Execution | `DOC-O08-04` |
| bad_chunk_count | #8-4 | 8 Chunk Run Preparation And Execution | `DOC-O08-04` |
| ctx | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| probe_root | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| pipeline_root | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| chunk_manifest_dir | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| chunk_runs_dir | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| test_chunk_with_batch_path | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| test_batch_plan_path | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| canonical_chunk_with_batch_path | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| canonical_batch_plan_path | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| fallback_chunk_target_path | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| fallback_batch_plan_path | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| execution_chunks_df | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| execution_batch_plan_df | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| chunk_name_col | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| execution_chunk_out | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| execution_batch_out | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| summary | #8-5 | 8 Chunk Run Preparation And Execution | `DOC-O08-05` |
| ctx | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| probe_root | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| pipeline_root | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| chunk_manifest_dir | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| chunk_runs_dir | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| merged_dir | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| final_outputs_dir | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| final_outputs_diagnostics_dir | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| final_outputs_manifests_dir | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| final_outputs_chunk_evidence_dir | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| final_outputs_merged_dir | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| execution_chunks_path | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| execution_batch_plan_path | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| target_chunks_df | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| batch_plan_df | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| chunk_name_col | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| batch_names | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| config_snapshot | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| delete_targets | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| delete_status | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| record_manifest_path | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| sequence_precheck_path | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| record_df | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| sequence_df | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| record_count | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| target_chunk_count | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| sequence_bad_chunk_count | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| fatal_issues | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| warnings | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| status | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| preflight_summary | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| preflight_path | #8-6 | 8 Chunk Run Preparation And Execution | `DOC-O08-06` |
| ctx | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| probe_root | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| pipeline_root | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| chunk_manifest_dir | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| chunk_runs_dir | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| final_outputs_diagnostics_dir | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| execution_chunks_path | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| execution_batch_plan_path | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| execution_chunks_df | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| execution_batch_plan_df | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| batch_execution_items_df | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| batch_execution_items_path | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| batch_manifest_rows | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| batch_manifests_df | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| batch_manifests_path | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| summary | #8-7 | 8 Chunk Run Preparation And Execution | `DOC-O08-07` |
| repo_root | #8-8 | 8 Chunk Run Preparation And Execution | `DOC-O08-08` |
| src_root | #8-8 | 8 Chunk Run Preparation And Execution | `DOC-O08-08` |
| wrapper_path | #8-8 | 8 Chunk Run Preparation And Execution | `DOC-O08-08` |
| wrapper_code | #8-8 | 8 Chunk Run Preparation And Execution | `DOC-O08-08` |
| ctx | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| probe_root | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| pipeline_root | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| chunk_manifest_dir | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| chunk_runs_dir | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| final_outputs_diagnostics_dir | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| wrapper_path | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| batch_execution_items_path | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| items_df | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| config_snapshot | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| DRY_RUN | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| DEVICE | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| MODEL_ID | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| PROCESS_RES | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| PROCESS_RES_METHOD | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| EXPORT_FORMAT | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| ALIGN_TO_INPUT_EXT_SCALE | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| INFER_GS | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| SHOW_CAMERAS | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| CONF_THRESH_PERCENTILE | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| NUM_MAX_POINTS | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| SKIP_ALREADY_SUCCESS | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| required_cols | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| missing_cols | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| rows | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| run_df | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| run_csv | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| summary | #8-9 | 8 Chunk Run Preparation And Execution | `DOC-O08-09` |
| ctx | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| config | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| probe_root | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| persist_root | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| pipeline_root | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| anchor_dir | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| chunk_manifest_dir | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| chunk_runs_dir | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| final_outputs_chunk_evidence_dir | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| final_outputs_diagnostics_dir | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| matching_dir | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| LOCAL_EXTRINSIC_MODE | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| LOCAL_CAMERA_BASIS | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| TRANSFORM_SCALE_MIN | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| TRANSFORM_SCALE_MAX | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| TRANSFORM_CENTER_RMSE_MAX | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| TRANSFORM_ROT_DIR_MAX | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| chunk_a_frames_path | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| chunk_a_pred_path | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| chunk_b_frames_path | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| chunk_b_pred_path | #9-1 | 9 Chunk Alignment Coefficient Derivation | `DOC-O09-01` |
| ctx | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| probe_root | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| persist_root | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| pipeline_root | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| chunk_manifest_dir | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| chunk_runs_dir | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| merged_dir | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| final_outputs_diagnostics_dir | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| anchor_dir | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| camera_anchor_full_path | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| batch_execution_items_path | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| items_df | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| sort_cols | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| anchor_full_df | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| required_anchor_cols | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| missing_anchor_cols | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| ROUTE_ARCORE | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| ROUTE_DA3 | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| PREFERRED_ROUTE_LABEL | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| LOCAL_EXTRINSIC_MODE | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| LOCAL_CAMERA_BASIS | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| PREMERGE_CENTER_ERROR_P95_MAX | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| PREMERGE_LENS_ERROR_DEG_P95_MAX | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| PREMERGE_DELTA_CENTER_ERROR_MAX | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| PREMERGE_DELTA_LENS_ERROR_DEG_MAX | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| TRANSFORM_SCALE_MIN | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| TRANSFORM_SCALE_MAX | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| TRANSFORM_CENTER_RMSE_MAX | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| TRANSFORM_ROT_DIR_MAX | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| SIM3_GRAPH_OPTIMIZATION | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| GRAPH_OPT_MAX_NFEV | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| GRAPH_PRIOR_WEIGHT | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| GRAPH_EDGE_TRANSLATION_WEIGHT | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| GRAPH_EDGE_ROTATION_WEIGHT | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| GRAPH_EDGE_SCALE_WEIGHT | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| GRAPH_ANCHOR_WEIGHT | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| GRAPH_ANCHOR_ROT_WEIGHT | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| GRAPH_ANCHOR_FRAME_TRANSLATION_WEIGHT | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| GRAPH_ANCHOR_FRAME_DIRECTION_WEIGHT | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| GRAPH_ANCHOR_OVERLAP_FRAME_WEIGHT | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| GRAPH_ANCHOR_NONOVERLAP_FRAME_WEIGHT | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| route_world_pose_map | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| candidate_rows | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| selected_rows | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| graph_solution_rows | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| graph_edge_rows | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| residual_frames | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| missing_pred_chunks | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| graph_node_measurements | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| previous_selected_chunk_name | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| previous_selected_T | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| candidate_df | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| route_compare_csv | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| residual_df | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| residual_csv | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| missing_pred_df | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| missing_pred_csv | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| graph_solution_df | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| graph_edges_df | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| graph_optimization_summary | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| validation_df | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| validation_csv | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| gate_csv | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| graph_solution_csv | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| graph_edges_csv | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| validation_json | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| route_compare_json | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| graph_summary_json | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| graph_opt_summary_json | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| hard_fail_df | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| anchor_warning_df | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| route_counts | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| fallback_count | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| route_compare_summary | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| graph_summary | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| summary | #10-1 | 10 Global Prepose Graph And Gate | `DOC-O10-01` |
| ctx | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| probe_root | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| pipeline_root | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| chunk_manifest_dir | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| merged_dir | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| final_outputs_diagnostics_dir | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| validation_json | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| route_compare_json | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| route_compare_csv | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| graph_solution_csv | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| graph_edges_csv | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| graph_summary_json | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| batch_execution_items_path | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| required_paths | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| missing_paths | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| validation | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| route_compare_summary | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| graph_summary | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| validation_df | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| route_compare_df | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| graph_edges_df | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| status | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| selected_route_counts | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| preferred_route_label | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| preferred_fallback_used_count | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| review_summary | #10-2 | 10 Global Prepose Graph And Gate | `DOC-O10-02` |
| missing_merge_deps | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| batch_preflight_status_path | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| ctx | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| probe_root | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| results_root | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| persist_root | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| modeling_session_id | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| manifest_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| final_outputs_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| final_outputs_merged_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| final_outputs_diagnostics_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| final_outputs_manifests_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| final_outputs_chunk_evidence_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| pipeline_root | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| anchor_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| chunk_manifest_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| chunk_runs_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| merged_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| stage_11_2_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| stage_11_3_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| config_path | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| BUNDLE_MODEL_SLUG | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| REQUIRE_ALL_CHUNKS | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| config_snapshot | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| MAKE_DRIVE_BUNDLE | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| INFER_GS | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| batch_execution_items_path | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| TRANSFORM_SCALE_MIN | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| TRANSFORM_SCALE_MAX | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| TRANSFORM_CENTER_RMSE_MAX | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| TRANSFORM_ROT_DIR_MAX | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| ROUTE_ARCORE | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| ROUTE_DA3 | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| PREFERRED_ROUTE_LABEL | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| LOCAL_EXTRINSIC_MODE | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| LOCAL_CAMERA_BASIS | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| chunk_index_all_path | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| all_chunks_df | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| target_chunks_df | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| completed_chunk_names | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| pred_ready_chunk_names | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| ply_ready_chunk_names | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| completed_chunk_names | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| pred_ready_chunk_names | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| ply_ready_chunk_names | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| completed_chunks_df | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| pred_ready_target_chunk_names | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| ply_ready_target_chunk_names | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| batch_summaries | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| summary_rows | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| premerge_pose_validation_path | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| premerge_pose_validation | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| premerge_route_compare_path | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| prepose_chunk_graph_solution_path | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| prepose_chunk_graph_edges_path | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| prepose_chunk_graph_summary_path | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| premerge_validation_csv_path | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| allowed_premerge_status | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| transform_df | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| integrated_pose_df | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| merged_camera_pose_csv | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| merged_camera_matrix_csv | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| merged_camera_c2w_npy | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| merged_camera_w2c_npy | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| ngl_bundle_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| ngl_bundle_manifest_dir | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| ngl_input_manifest_path | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| ngl_intrinsics_path | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| ngl_extrinsics_path | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| ngl_pose_summary_path | #11-1 | 11 Merge And Review | `DOC-O11-01` |
| ctx | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| probe_root | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| persist_root | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| pipeline_root | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| chunk_manifest_dir | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| chunk_runs_dir | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| merged_dir | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| anchor_dir | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| anchor_path | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| graph_solution_path | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| transform_path | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| merged_camera_pose_path | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| batch_execution_items_path | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| merge_summary_path | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| required | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| missing | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| anchor_df | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| items_df | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| merge_summary | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| transform_df | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| anchor_center_cols | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| anchor_dir_cols | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| anchor_view_df | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| anchor_centers | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| anchor_dirs | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| transform_map | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| chunk_rows | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| chunk_plot_items | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| merged_pose_rows | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| item_cols | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| chunk_pose_review_csv | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| merged_pose_csv | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| fig | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| review_html | #11-2 | 11 Merge And Review | `DOC-O11-02` |
| review_summary | #11-2 | 11 Merge And Review | `DOC-O11-02` |
