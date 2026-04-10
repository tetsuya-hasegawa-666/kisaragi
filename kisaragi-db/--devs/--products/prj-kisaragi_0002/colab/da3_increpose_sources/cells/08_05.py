#8-5

ctx = load_ctx()
probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"

chunk_manifest_dir.mkdir(parents=True, exist_ok=True)
chunk_runs_dir.mkdir(parents=True, exist_ok=True)

test_chunk_with_batch_path = chunk_manifest_dir / "test_only_target_chunk_with_batch.csv"
test_batch_plan_path = chunk_manifest_dir / "test_only_target_batch_plan.csv"

canonical_chunk_with_batch_path = chunk_manifest_dir / "target_chunk_with_batch.csv"
canonical_batch_plan_path = chunk_manifest_dir / "target_batch_plan.csv"

fallback_chunk_target_path = chunk_manifest_dir / "chunk_index_target.csv"
fallback_batch_plan_path = chunk_manifest_dir / "batch_plan.csv"

if test_chunk_with_batch_path.exists():
    execution_chunk_path = test_chunk_with_batch_path
    execution_mode_chunks = "test_only"
elif canonical_chunk_with_batch_path.exists():
    execution_chunk_path = canonical_chunk_with_batch_path
    execution_mode_chunks = "canonical_target_with_batch"
else:
    execution_chunk_path = fallback_chunk_target_path
    execution_mode_chunks = "canonical_chunk_index_target"

if test_batch_plan_path.exists():
    execution_batch_plan_path = test_batch_plan_path
    execution_mode_batch_plan = "test_only"
elif canonical_batch_plan_path.exists():
    execution_batch_plan_path = canonical_batch_plan_path
    execution_mode_batch_plan = "canonical_target_batch_plan"
else:
    execution_batch_plan_path = fallback_batch_plan_path
    execution_mode_batch_plan = "canonical_batch_plan"

assert execution_chunk_path.exists(), {"missing_execution_chunk_source": str(execution_chunk_path)}
assert execution_batch_plan_path.exists(), {"missing_execution_batch_source": str(execution_batch_plan_path)}

execution_chunks_df = pd.read_csv(execution_chunk_path)
execution_batch_plan_df = pd.read_csv(execution_batch_plan_path)

assert not execution_chunks_df.empty, execution_chunk_path
assert not execution_batch_plan_df.empty, execution_batch_plan_path

chunk_name_col = next((c for c in ["chunk_name", "chunk_id", "name"] if c in execution_chunks_df.columns), None)
assert chunk_name_col is not None, {"execution_chunk_columns": execution_chunks_df.columns.tolist()}

if "batch_name" not in execution_batch_plan_df.columns:
    if "batch_index" in execution_batch_plan_df.columns:
        execution_batch_plan_df["batch_name"] = execution_batch_plan_df["batch_index"].astype(int).map(lambda x: f"batch_{x:03d}")
    else:
        execution_batch_plan_df["batch_name"] = [f"batch_{i:03d}" for i in range(len(execution_batch_plan_df))]

if "batch_name" not in execution_chunks_df.columns and "batch_index" in execution_chunks_df.columns:
    execution_chunks_df["batch_name"] = execution_chunks_df["batch_index"].astype(int).map(lambda x: f"batch_{x:03d}")

execution_chunk_out = chunk_manifest_dir / "execution_target_chunks.csv"
execution_batch_out = chunk_manifest_dir / "execution_target_batch_plan.csv"

execution_chunks_df.to_csv(execution_chunk_out, index=False, encoding="utf-8")
execution_batch_plan_df.to_csv(execution_batch_out, index=False, encoding="utf-8")

summary = {
    "status": "ok",
    "execution_mode_chunks": execution_mode_chunks,
    "execution_mode_batch_plan": execution_mode_batch_plan,
    "execution_chunk_source": str(execution_chunk_path),
    "execution_batch_plan_source": str(execution_batch_plan_path),
    "execution_chunk_rows": int(len(execution_chunks_df)),
    "execution_batch_rows": int(len(execution_batch_plan_df)),
    "execution_chunk_names_sample": execution_chunks_df[chunk_name_col].astype(str).head(10).tolist(),
    "execution_chunk_names_all": execution_chunks_df[chunk_name_col].astype(str).tolist(),
    "execution_batch_names": execution_batch_plan_df["batch_name"].astype(str).tolist(),
    "execution_chunk_out": str(execution_chunk_out),
    "execution_batch_out": str(execution_batch_out),
}

save_json(chunk_manifest_dir / "execution_target_resolution_summary.json", summary)

print(json.dumps(summary, indent=2, ensure_ascii=False))
display(execution_chunks_df.head())
display(execution_batch_plan_df)
display_stage_summary(
    "8-5",
    "execution target resolve",
    inputs=[
        {"item": "chunk_index_target", "path": str(fallback_chunk_target_path)},
        {"item": "batch_plan", "path": str(fallback_batch_plan_path)},
    ],
    outputs=[
        {"item": "execution_target_chunks", "path": str(execution_chunk_out)},
        {"item": "execution_target_batch_plan", "path": str(execution_batch_out)},
        {"item": "execution_target_resolution_summary", "path": str(chunk_manifest_dir / "execution_target_resolution_summary.json")},
    ],
    notes=[
        {"item": "execution_mode_chunks", "value": execution_mode_chunks},
        {"item": "execution_mode_batch_plan", "value": execution_mode_batch_plan},
    ],
)
