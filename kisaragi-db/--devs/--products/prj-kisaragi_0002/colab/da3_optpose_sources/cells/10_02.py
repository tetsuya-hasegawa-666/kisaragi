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
graph_solution_csv = merged_dir / "prepose_chunk_graph_solution_arc.csv"
graph_edges_csv = merged_dir / "prepose_chunk_graph_edges_arc.csv"
graph_summary_json = merged_dir / "prepose_chunk_graph_summary.json"
batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"

required_paths = [
    validation_json,
    route_compare_json,
    route_compare_csv,
    graph_solution_csv,
    graph_edges_csv,
    graph_summary_json,
    batch_execution_items_path,
]
missing_paths = [str(path) for path in required_paths if not path.exists()]
assert not missing_paths, {"reason": "missing_prepose_graph_artifacts", "missing_paths": missing_paths}

validation = load_json(validation_json)
route_compare_summary = load_json(route_compare_json)
graph_summary = load_json(graph_summary_json)

validation_df = pd.read_csv(graph_solution_csv)
route_compare_df = pd.read_csv(route_compare_csv)
graph_edges_df = pd.read_csv(graph_edges_csv)

status = str(validation.get("status", "missing"))
selected_route_counts = validation.get("selected_route_counts", route_compare_summary.get("selected_route_counts", []))
preferred_route_label = str(validation.get("preferred_route_label", route_compare_summary.get("preferred_route_label", "")))
preferred_fallback_used_count = int(validation.get("preferred_fallback_used_count", 0))

review_summary = {
    "status": status,
    "route": "continuous-gs-v06-chunk18-overlap6-adopt12-prepose-graph-review",
    "preferred_route_label": preferred_route_label,
    "selected_route_counts": selected_route_counts,
    "preferred_fallback_used_count": preferred_fallback_used_count,
    "tested_chunk_count": int(validation.get("tested_chunk_count", len(validation_df))),
    "hard_fail_count": int(validation.get("hard_fail_count", 0)),
    "anchor_warning_count": int(validation.get("anchor_warning_count", 0)),
    "route_compare_csv": str(route_compare_csv),
    "prepose_chunk_graph_solution_csv": str(graph_solution_csv),
    "prepose_chunk_graph_edges_csv": str(graph_edges_csv),
    "prepose_chunk_graph_summary_json": str(graph_summary_json),
    "premerge_pose_validation_json": str(validation_json),
}
save_json(final_outputs_diagnostics_dir / "prepose_graph_gate_review.json", review_summary)

print(json.dumps(review_summary, indent=2, ensure_ascii=False))
if len(validation_df):
    display(validation_df)
if len(route_compare_df):
    display(route_compare_df)
if len(graph_edges_df):
    display(graph_edges_df)

display_stage_summary(
    "10-2",
    "prepose graph review gate",
    inputs=[
        {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
        {"item": "premerge_pose_validation", "path": str(validation_json)},
        {"item": "premerge_route_compare_summary", "path": str(route_compare_json)},
        {"item": "prepose_chunk_graph_summary", "path": str(graph_summary_json)},
    ],
    outputs=[
        {"item": "premerge_route_compare", "path": str(route_compare_csv)},
        {"item": "prepose_chunk_graph_solution", "path": str(graph_solution_csv)},
        {"item": "prepose_chunk_graph_edges", "path": str(graph_edges_csv)},
        {"item": "prepose_graph_gate_review", "path": str(final_outputs_diagnostics_dir / "prepose_graph_gate_review.json")},
    ],
    notes=[
        {"item": "status", "value": status},
        {"item": "preferred_route_label", "value": preferred_route_label},
        {"item": "preferred_fallback_used_count", "value": preferred_fallback_used_count},
        {"item": "hard_fail_count", "value": int(validation.get("hard_fail_count", 0))},
        {"item": "anchor_warning_count", "value": int(validation.get("anchor_warning_count", 0))},
    ],
)

assert status in {"ok", "warning"}, validation
