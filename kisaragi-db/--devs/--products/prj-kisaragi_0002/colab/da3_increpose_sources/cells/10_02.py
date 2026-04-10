#10-2

ctx = load_ctx()

probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
merged_dir = Path(ctx.get("merged_dir", str(pipeline_root / "merged")))
merged_dir.mkdir(parents=True, exist_ok=True)

final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_diagnostics_dir.mkdir(parents=True, exist_ok=True)

validation_json = merged_dir / "premerge_pose_validation.json"
route_compare_json = merged_dir / "premerge_route_compare_summary.json"
route_compare_csv = merged_dir / "premerge_route_compare_arc.csv"
graph_solution_csv = merged_dir / "prepose_chunk_graph_solution_arc.csv"   # compat: chunk validation summary
graph_summary_json = merged_dir / "prepose_chunk_graph_summary.json"
batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"

required_paths = [
    validation_json,
    route_compare_json,
    route_compare_csv,
    graph_solution_csv,
    graph_summary_json,
    batch_execution_items_path,
]
missing_paths = [str(path) for path in required_paths if not path.exists()]
assert not missing_paths, {"reason": "missing_incremental_validation_artifacts", "missing_paths": missing_paths}

validation = load_json(validation_json)
route_compare_summary = load_json(route_compare_json)
graph_summary = load_json(graph_summary_json)

validation_df = pd.read_csv(graph_solution_csv) if graph_solution_csv.stat().st_size > 0 else pd.DataFrame()
route_compare_df = pd.read_csv(route_compare_csv) if route_compare_csv.stat().st_size > 0 else pd.DataFrame()

status = str(validation.get("status", "missing"))
selected_route_counts = validation.get("selected_route_counts", route_compare_summary.get("selected_route_counts", []))
preferred_route_label = str(validation.get("preferred_route_label", route_compare_summary.get("preferred_route_label", "")))
preferred_fallback_used_count = int(validation.get("preferred_fallback_used_count", 0))

review_summary = {
    "status": status,
    "route": "continuous-gs-v07-chunk18-step6-context12-output6-adopt6-incremental-review",
    "preferred_route_label": preferred_route_label,
    "selected_route_counts": selected_route_counts,
    "preferred_fallback_used_count": preferred_fallback_used_count,
    "tested_chunk_count": int(validation.get("tested_chunk_count", len(validation_df))),
    "hard_fail_count": int(validation.get("hard_fail_count", 0)),
    "anchor_warning_count": int(validation.get("anchor_warning_count", 0)),
    "missing_pred_count": int(validation.get("missing_pred_count", 0)),
    "target_output_record_count": int(validation.get("target_output_record_count", 0)),
    "global_pred_record_count": int(validation.get("global_pred_record_count", 0)),
    "evaluation_scope": "output_range_only",
    "context_size": 12,
    "output_size": 6,
    "adopt_size": 6,
    "graph_mainflow_removed": bool(graph_summary.get("graph_mainflow_removed", True)),
    "graph_edges_used": bool(graph_summary.get("graph_edges_used", False)),
    "route_compare_csv": str(route_compare_csv),
    "chunk_validation_summary_csv": str(graph_solution_csv),
    "incremental_validation_summary_json": str(graph_summary_json),
    "premerge_pose_validation_json": str(validation_json),
}
save_json(final_outputs_diagnostics_dir / "prepose_graph_gate_review.json", review_summary)

artifact_index = {
    "route_compare_csv": str(route_compare_csv),
    "chunk_validation_summary_csv": str(graph_solution_csv),
    "premerge_pose_validation_json": str(validation_json),
    "incremental_validation_summary_json": str(graph_summary_json),
}
save_json(final_outputs_diagnostics_dir / "premerge_validation_artifact_index.json", artifact_index)

print(json.dumps(review_summary, indent=2, ensure_ascii=False))
print(json.dumps(validation, indent=2, ensure_ascii=False))

if len(validation_df):
    display(validation_df)
if len(route_compare_df):
    display(route_compare_df.head(50))

display_stage_summary(
    "10-2",
    "incremental validation review",
    outputs=[
        {"item": "review_summary_json", "path": str(final_outputs_diagnostics_dir / "prepose_graph_gate_review.json")},
        {"item": "artifact_index_json", "path": str(final_outputs_diagnostics_dir / "premerge_validation_artifact_index.json")},
        {"item": "chunk_validation_summary_csv", "path": str(graph_solution_csv)},
        {"item": "route_compare_csv", "path": str(route_compare_csv)},
        {"item": "validation_json", "path": str(validation_json)},
    ],
)
