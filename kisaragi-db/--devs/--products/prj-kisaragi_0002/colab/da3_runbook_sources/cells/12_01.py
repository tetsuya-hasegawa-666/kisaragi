#12-1

ctx = load_ctx()

probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
chunk_runs_dir.mkdir(parents=True, exist_ok=True)

final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_diagnostics_dir.mkdir(parents=True, exist_ok=True)

execution_chunks_path = chunk_manifest_dir / "execution_target_chunks.csv"
execution_batch_plan_path = chunk_manifest_dir / "execution_target_batch_plan.csv"
assert execution_chunks_path.exists(), execution_chunks_path
assert execution_batch_plan_path.exists(), execution_batch_plan_path

execution_chunks_df = pd.read_csv(execution_chunks_path)
execution_batch_plan_df = pd.read_csv(execution_batch_plan_path)

if "batch_name" not in execution_batch_plan_df.columns:
    execution_batch_plan_df["batch_name"] = execution_batch_plan_df["batch_index"].astype(int).map(lambda x: f"batch_{x:03d}")

if "target_local_chunk_index" not in execution_chunks_df.columns:
    execution_chunks_df = execution_chunks_df.copy().reset_index(drop=True)
    execution_chunks_df["target_local_chunk_index"] = range(len(execution_chunks_df))

if "batch_index" not in execution_chunks_df.columns:
    def resolve_batch_index(local_idx: int):
        hit = execution_batch_plan_df[(execution_batch_plan_df["chunk_from"].astype(int) <= int(local_idx)) &
                                      (execution_batch_plan_df["chunk_to"].astype(int) >= int(local_idx))]
        if len(hit) == 0:
            return None
        return int(hit.sort_values("batch_index", kind="stable").iloc[0]["batch_index"])
    execution_chunks_df["batch_index"] = execution_chunks_df["target_local_chunk_index"].map(resolve_batch_index)

assert execution_chunks_df["batch_index"].notna().all(), {"unresolved_target_local_chunk_indices": execution_chunks_df.loc[execution_chunks_df["batch_index"].isna(), "target_local_chunk_index"].tolist()}
execution_chunks_df["batch_index"] = execution_chunks_df["batch_index"].astype(int)

if "batch_name" not in execution_chunks_df.columns:
    execution_chunks_df["batch_name"] = execution_chunks_df["batch_index"].astype(int).map(lambda x: f"batch_{x:03d}")

rows, missing_files = [], []
for b_row in execution_batch_plan_df.itertuples(index=False):
    batch_index = int(b_row.batch_index) if hasattr(b_row, "batch_index") else None
    batch_name = str(b_row.batch_name)
    batch_work_dir = chunk_runs_dir / batch_name
    batch_work_dir.mkdir(parents=True, exist_ok=True)

    batch_chunks_df = execution_chunks_df[execution_chunks_df["batch_index"].astype(int) == batch_index].copy().sort_values("target_local_chunk_index", kind="stable").reset_index(drop=True)
    assert not batch_chunks_df.empty, {"batch_name": batch_name, "batch_index": batch_index}

    for c_row in batch_chunks_df.itertuples(index=False):
        chunk_name = str(getattr(c_row, "chunk_name"))
        chunk_csv_path = chunk_manifest_dir / f"{chunk_name}.csv"
        chunk_anchor_csv_path = chunk_manifest_dir / f"{chunk_name}_sequence_anchor.csv"
        if not chunk_csv_path.exists():
            missing_files.append(str(chunk_csv_path))
        if not chunk_anchor_csv_path.exists():
            missing_files.append(str(chunk_anchor_csv_path))
        rows.append({
            "batch_index": int(batch_index),
            "batch_name": batch_name,
            "chunk_id": int(getattr(c_row, "chunk_id")) if "chunk_id" in execution_chunks_df.columns else None,
            "chunk_name": chunk_name,
            "target_local_chunk_index": int(getattr(c_row, "target_local_chunk_index")),
            "chunk_csv": str(chunk_csv_path),
            "chunk_sequence_anchor_csv": str(chunk_anchor_csv_path),
            "batch_work_dir": str(batch_work_dir),
        })

assert not missing_files, {"missing_chunk_related_files_count": len(missing_files), "missing_chunk_related_files_sample": missing_files[:10]}

batch_execution_items_df = pd.DataFrame(rows).sort_values(["batch_index", "target_local_chunk_index"], kind="stable").reset_index(drop=True)
batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
batch_execution_items_df.to_csv(batch_execution_items_path, index=False, encoding="utf-8")

batch_manifest_rows = []
for batch_name, batch_df in batch_execution_items_df.groupby("batch_name", sort=True):
    batch_work_dir = Path(batch_df.iloc[0]["batch_work_dir"])
    batch_manifest_dir = batch_work_dir / "manifests"
    batch_manifest_dir.mkdir(parents=True, exist_ok=True)
    batch_chunk_index_path = batch_manifest_dir / "batch_chunk_index.csv"
    batch_df.to_csv(batch_chunk_index_path, index=False, encoding="utf-8")
    batch_manifest_rows.append({
        "batch_name": str(batch_name),
        "batch_index": int(batch_df.iloc[0]["batch_index"]),
        "chunk_count": int(len(batch_df)),
        "chunk_names": "|".join(batch_df["chunk_name"].astype(str).tolist()),
        "batch_work_dir": str(batch_work_dir),
        "batch_chunk_index_path": str(batch_chunk_index_path),
    })

batch_manifests_df = pd.DataFrame(batch_manifest_rows).sort_values(["batch_index", "batch_name"], kind="stable").reset_index(drop=True)
batch_manifests_path = chunk_manifest_dir / "batch_manifests.csv"
batch_manifests_df.to_csv(batch_manifests_path, index=False, encoding="utf-8")

summary = {
    "status": "ok",
    "batch_count": int(len(batch_manifests_df)),
    "chunk_count_total": int(batch_execution_items_df.shape[0]),
    "batch_execution_items_path": str(batch_execution_items_path),
    "batch_manifests_path": str(batch_manifests_path),
    "batch_names": batch_manifests_df["batch_name"].astype(str).tolist(),
}
save_json(final_outputs_diagnostics_dir / "batch_input_generation_summary.json", summary)
save_json(
    Path("/content/runbook_batch_preflight_status.json"),
    {
        "status": "ok",
        "route": "da3_record_sequence_anchor_batch_plan_execution_preflight",
        "batch_execution_items_path": str(batch_execution_items_path),
        "batch_manifests_path": str(batch_manifests_path),
        "execution_chunks_path": str(execution_chunks_path),
        "execution_batch_plan_path": str(execution_batch_plan_path),
    },
)

print(json.dumps(summary, indent=2, ensure_ascii=False))
display(batch_execution_items_df)
display(batch_manifests_df)
display_stage_summary(
    "12-1",
    "batch input generation",
    inputs=[
        {"item": "execution_target_chunks", "path": str(execution_chunks_path)},
        {"item": "execution_target_batch_plan", "path": str(execution_batch_plan_path)},
    ],
    outputs=[
        {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
        {"item": "batch_manifests", "path": str(batch_manifests_path)},
        {"item": "batch_input_generation_summary", "path": str(final_outputs_diagnostics_dir / "batch_input_generation_summary.json")},
    ],
    notes=[
        {"item": "batch_count", "value": int(len(batch_manifests_df))},
        {"item": "chunk_count_total", "value": int(batch_execution_items_df.shape[0])},
    ],
)
