#11-4

ctx = load_ctx()

probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"

manifest_dir = Path(ctx["manifest_dir"])
persist_root = Path(ctx.get("persist_root", manifest_dir.parent))
anchor_dir = persist_root / "01_anchor"

merged_dir = Path(ctx["merged_dir"])
final_outputs_dir = Path(ctx["final_outputs_dir"])
final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_manifests_dir = Path(ctx["final_outputs_manifests_dir"])
final_outputs_chunk_evidence_dir = Path(ctx["final_outputs_chunk_evidence_dir"])
final_outputs_merged_dir = Path(ctx["final_outputs_merged_dir"])

execution_chunks_path = chunk_manifest_dir / "execution_target_chunks.csv"
execution_batch_plan_path = chunk_manifest_dir / "execution_target_batch_plan.csv"

assert execution_chunks_path.exists(), execution_chunks_path
assert execution_batch_plan_path.exists(), execution_batch_plan_path

target_chunks_df = pd.read_csv(execution_chunks_path)
batch_plan_df = pd.read_csv(execution_batch_plan_path)

assert not target_chunks_df.empty, execution_chunks_path
assert not batch_plan_df.empty, execution_batch_plan_path

chunk_name_col = next((c for c in ["chunk_name", "chunk_id", "name"] if c in target_chunks_df.columns), None)
assert chunk_name_col is not None, {"target_chunk_columns": target_chunks_df.columns.tolist()}

batch_names = batch_plan_df["batch_name"].astype(str).tolist() if "batch_name" in batch_plan_df.columns else [f"batch_{int(v):03d}" for v in batch_plan_df["batch_index"].tolist()]

config_snapshot = load_json("/content/config_snapshot.json")
delete_targets = []
if bool(config_snapshot.get("RESET_TARGET_OUTPUTS_BEFORE_RUN", True)):
    for row in target_chunks_df.itertuples(index=False):
        chunk_name = str(getattr(row, chunk_name_col))
        delete_targets.append(chunk_runs_dir / chunk_name)
        delete_targets.append(chunk_manifest_dir / f"{chunk_name}_to_w0.npy")
    for batch_name in batch_names:
        delete_targets.append(chunk_runs_dir / batch_name)
    delete_targets.extend([merged_dir, final_outputs_dir])

deleted, missing = [], []
for path in delete_targets:
    if not path.exists():
        missing.append(str(path))
        continue
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    deleted.append(str(path))

for p in [merged_dir, final_outputs_dir, final_outputs_diagnostics_dir, final_outputs_manifests_dir, final_outputs_chunk_evidence_dir, final_outputs_merged_dir]:
    p.mkdir(parents=True, exist_ok=True)

reset_summary = {
    "status": "ok",
    "route": "da3_ngl_batch_v01_target_output_reset",
    "probe_root": str(probe_root),
    "chunk_source_path": str(execution_chunks_path),
    "batch_source_path": str(execution_batch_plan_path),
    "target_chunk_count": int(len(target_chunks_df)),
    "target_batch_count": int(len(batch_names)),
    "deleted_count": int(len(deleted)),
    "missing_count": int(len(missing)),
}
save_json(final_outputs_diagnostics_dir / "target_output_reset_summary.json", reset_summary)

# preflight
record_manifest_path = manifest_dir / "da3_input_manifest.csv"
anchor_pose_diag_path = anchor_dir / "full_anchor_pose_diag_arc.csv"
anchor_qc_path = anchor_dir / "full_anchor_pose_qc_arc.csv"
sequence_precheck_path = chunk_manifest_dir / "batch_chunk_sequence_precheck.csv"
edge_validation_path = chunk_manifest_dir / "adjacent_edge_validation.csv"

required_paths = {
    "record_manifest": record_manifest_path,
    "anchor_pose_diag": anchor_pose_diag_path,
    "anchor_qc": anchor_qc_path,
    "sequence_precheck": sequence_precheck_path,
    "edge_validation": edge_validation_path,
}
missing_required = {k: str(p) for k, p in required_paths.items() if not p.exists()}
assert not missing_required, {"missing_required": missing_required}

record_df = pd.read_csv(record_manifest_path)
anchor_pose_df = pd.read_csv(anchor_pose_diag_path)
anchor_qc_df = pd.read_csv(anchor_qc_path)
sequence_df = pd.read_csv(sequence_precheck_path)
edge_df = pd.read_csv(edge_validation_path)

record_count_match = len(record_df) == len(anchor_pose_df)
sequence_bad_count = int(((~sequence_df["is_monotonic"]) | (sequence_df["has_duplicate_sequence"]) | (sequence_df["bad_gap_count"] > 0)).sum()) if len(sequence_df) else 0
edge_bad_chunk_count = 0
if len(edge_df) and "chunk_name" in edge_df.columns:
    fail_cols = [c for c in edge_df.columns if c.endswith("_fail")]
    if fail_cols:
        bad_mask = np.zeros(len(edge_df), dtype=bool)
        for c in fail_cols:
            bad_mask |= edge_df[c].fillna(False).astype(bool).to_numpy()
        edge_bad_chunk_count = int(edge_df.loc[bad_mask, "chunk_name"].nunique())
anchor_fail_count = int(anchor_qc_df["anchor_qc_fail"].sum()) if "anchor_qc_fail" in anchor_qc_df.columns else 0

image_path_col = next((c for c in ["image_path", "image_abs_path"] if c in record_df.columns), None)
missing_images = []
if image_path_col is not None:
    target_record_indices = set()
    if "record_index" in target_chunks_df.columns:
        target_record_indices = set(target_chunks_df["record_index"].dropna().astype(int).tolist())
    else:
        for row in target_chunks_df.itertuples(index=False):
            chunk_name = str(getattr(row, chunk_name_col))
            chunk_csv = chunk_manifest_dir / f"{chunk_name}.csv"
            if chunk_csv.exists():
                cdf = pd.read_csv(chunk_csv)
                if "record_index" in cdf.columns:
                    target_record_indices.update(cdf["record_index"].dropna().astype(int).tolist())
    sub = record_df[record_df["record_index"].astype(int).isin(sorted(target_record_indices))].copy() if target_record_indices and "record_index" in record_df.columns else record_df.copy()
    for r in sub.itertuples(index=False):
        p = Path(getattr(r, image_path_col))
        if not p.exists():
            missing_images.append(str(p))

if missing_images:
    pd.DataFrame({"missing_image_path": missing_images}).to_csv(final_outputs_diagnostics_dir / "batch_execution_preflight_missing_images.csv", index=False, encoding="utf-8")

fatal_issues, warnings = [], []
if not record_count_match:
    fatal_issues.append({"type": "record_anchor_count_mismatch", "record_rows": int(len(record_df)), "anchor_rows": int(len(anchor_pose_df))})
if sequence_bad_count > 0:
    fatal_issues.append({"type": "sequence_precheck_failed", "bad_chunk_count": sequence_bad_count})
if edge_bad_chunk_count > 0:
    warnings.append({"type": "adjacent_edge_validation_has_failures", "bad_chunk_count": edge_bad_chunk_count})
if anchor_fail_count > 0:
    warnings.append({"type": "anchor_qc_failures_present", "anchor_fail_count": anchor_fail_count})
if missing_images:
    fatal_issues.append({"type": "missing_images", "missing_image_count": int(len(missing_images))})

preflight = {
    "status": "fatal" if fatal_issues else "ok_with_warnings" if warnings else "ok",
    "target_chunk_count": int(len(target_chunks_df)),
    "target_batch_count": int(len(batch_plan_df)),
    "record_rows": int(len(record_df)),
    "anchor_rows": int(len(anchor_pose_df)),
    "record_anchor_count_match": bool(record_count_match),
    "sequence_bad_chunk_count": int(sequence_bad_count),
    "edge_bad_chunk_count": int(edge_bad_chunk_count),
    "anchor_fail_count": int(anchor_fail_count),
    "missing_image_count": int(len(missing_images)),
    "fatal_issues": fatal_issues,
    "warnings": warnings,
}
save_json(final_outputs_diagnostics_dir / "batch_execution_preflight.json", preflight)
print(json.dumps({"reset_summary": reset_summary, "preflight": preflight}, indent=2, ensure_ascii=False))
display_stage_summary(
    "11-4",
    "reset and preflight",
    inputs=[
        {"item": "execution_target_chunks", "path": str(execution_chunks_path)},
        {"item": "execution_target_batch_plan", "path": str(execution_batch_plan_path)},
        {"item": "record_manifest", "path": str(record_manifest_path)},
        {"item": "anchor_pose_diag", "path": str(anchor_pose_diag_path)},
        {"item": "anchor_qc", "path": str(anchor_qc_path)},
    ],
    outputs=[
        {"item": "target_output_reset_summary", "path": str(final_outputs_diagnostics_dir / "target_output_reset_summary.json")},
        {"item": "batch_execution_preflight", "path": str(final_outputs_diagnostics_dir / "batch_execution_preflight.json")},
        {"item": "batch_execution_preflight_missing_images", "path": str(final_outputs_diagnostics_dir / "batch_execution_preflight_missing_images.csv")},
    ],
    notes=[
        {"item": "fatal_issue_count", "value": int(len(fatal_issues))},
        {"item": "warning_count", "value": int(len(warnings))},
    ],
)
assert not fatal_issues, preflight
