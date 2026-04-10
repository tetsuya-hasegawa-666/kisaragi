#8-6

ctx = load_ctx()

probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"

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
        delete_targets.append(merged_dir / chunk_name)
    delete_targets.extend([
        final_outputs_dir,
        final_outputs_diagnostics_dir,
        final_outputs_manifests_dir,
        final_outputs_chunk_evidence_dir,
        final_outputs_merged_dir,
    ])

delete_status = []
for target in delete_targets:
    if target.exists():
        if target.is_dir():
            shutil.rmtree(target)
            delete_status.append({"path": str(target), "deleted": True, "kind": "dir"})
        else:
            target.unlink()
            delete_status.append({"path": str(target), "deleted": True, "kind": "file"})
    else:
        delete_status.append({"path": str(target), "deleted": False, "kind": "missing"})

for p in [chunk_runs_dir, merged_dir, final_outputs_dir, final_outputs_diagnostics_dir, final_outputs_manifests_dir, final_outputs_chunk_evidence_dir, final_outputs_merged_dir]:
    p.mkdir(parents=True, exist_ok=True)

record_manifest_path = Path(json.loads(Path("/content/runbook_managed_dirs.json").read_text(encoding="utf-8"))["02_records"]) / "record_manifest.csv"
sequence_precheck_path = chunk_manifest_dir / "batch_chunk_sequence_precheck.csv"

assert record_manifest_path.exists(), record_manifest_path
assert sequence_precheck_path.exists(), sequence_precheck_path

record_df = pd.read_csv(record_manifest_path)
sequence_df = pd.read_csv(sequence_precheck_path)

record_count = int(len(record_df))
target_chunk_count = int(len(target_chunks_df))
sequence_bad_chunk_count = int(((~sequence_df["is_monotonic"]) | (sequence_df["has_duplicate_sequence"]) | (sequence_df["bad_gap_count"] > 0)).sum()) if len(sequence_df) > 0 else 0

fatal_issues = []
warnings = []

if record_count == 0:
    fatal_issues.append({"type": "record_manifest_empty"})
if target_chunk_count == 0:
    fatal_issues.append({"type": "target_chunks_empty"})
if sequence_bad_chunk_count > 0:
    fatal_issues.append({"type": "sequence_precheck_failed", "bad_chunk_count": sequence_bad_chunk_count})

status = "ready" if len(fatal_issues) == 0 else "blocked"

preflight_summary = {
    "status": status,
    "record_rows": int(record_count),
    "target_chunk_count": int(target_chunk_count),
    "sequence_bad_chunk_count": int(sequence_bad_chunk_count),
    "batch_count": int(len(batch_names)),
    "fatal_issues": fatal_issues,
    "warnings": warnings,
    "delete_status": delete_status,
    "anchor_derived_checks_deferred_to_stage7": True,
}

preflight_path = final_outputs_diagnostics_dir / "run_preflight_summary.json"
preflight_path.write_text(json.dumps(preflight_summary, ensure_ascii=False, indent=2), encoding="utf-8")

print(preflight_summary)

display_stage_summary(
    "8-6",
    "run preflight",
    inputs=[
        {"item": "record_manifest", "path": str(record_manifest_path)},
        {"item": "sequence_precheck", "path": str(sequence_precheck_path)},
        {"item": "execution_target_chunks", "path": str(execution_chunks_path)},
        {"item": "execution_target_batch_plan", "path": str(execution_batch_plan_path)},
    ],
    outputs=[
        {"item": "run_preflight_summary", "path": str(preflight_path)},
    ],
    notes=[
        {"item": "status", "value": status},
        {"item": "record_rows", "value": int(record_count)},
        {"item": "target_chunk_count", "value": int(target_chunk_count)},
        {"item": "sequence_bad_chunk_count", "value": int(sequence_bad_chunk_count)},
        {"item": "anchor_derived_checks_deferred_to_stage7", "value": True},
    ],
)
