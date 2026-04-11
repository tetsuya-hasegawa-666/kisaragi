#8-5

ctx = load_ctx()
probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "runtime_workspace")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
config_snapshot = load_json("/content/config_snapshot.json") if Path("/content/config_snapshot.json").exists() else {}

chunk_execution_plan_path = chunk_manifest_dir / "chunk_execution_plan.csv"
chunk_manifest_dir.mkdir(parents=True, exist_ok=True)
chunk_runs_dir.mkdir(parents=True, exist_ok=True)

test_chunk_with_batch_path = chunk_manifest_dir / "test_only_target_chunk_with_batch.csv"
test_batch_plan_path = chunk_manifest_dir / "test_only_target_batch_plan.csv"

canonical_chunk_with_batch_path = chunk_manifest_dir / "target_chunk_with_batch.csv"
canonical_batch_plan_path = chunk_manifest_dir / "target_batch_plan.csv"

fallback_chunk_target_path = chunk_manifest_dir / "chunk_index_target.csv"
fallback_batch_plan_path = chunk_manifest_dir / "batch_plan.csv"
batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
chunk_index_all_path = chunk_manifest_dir / "chunk_index_all.csv"

def build_target_chunk_and_batch_plan():
    assert chunk_execution_plan_path.exists(), chunk_execution_plan_path
    base_df = pd.read_csv(chunk_execution_plan_path)

    assert not base_df.empty, {"reason": "base_chunk_manifest_empty", "chunk_manifest_dir": str(chunk_manifest_dir)}
    assert "chunk_id" in base_df.columns, base_df.columns.tolist()
    assert "chunk_name" in base_df.columns, base_df.columns.tolist()

    target_mode = str(config_snapshot.get("TARGET_CHUNK_MODE", "selected_chunk_ids_1based"))
    if target_mode == "full_set":
        target_chunks_df = base_df.copy().reset_index(drop=True)
    elif target_mode == "selected_chunk_ids_1based":
        valid_chunk_ids = set(base_df["chunk_id"].astype(int).tolist())
        selected_chunk_ids = sorted({int(x) - 1 for x in config_snapshot.get("TARGET_CHUNK_IDS_1BASED", []) if int(x) >= 1})
        selected_chunk_ids = [x for x in selected_chunk_ids if x in valid_chunk_ids]
        assert selected_chunk_ids, {
            "reason": "selected target chunk ids resolved empty",
            "selected_chunk_ids_1based": config_snapshot.get("TARGET_CHUNK_IDS_1BASED", []),
            "valid_chunk_ids_0based": sorted(valid_chunk_ids),
        }
        target_chunks_df = base_df.loc[base_df["chunk_id"].astype(int).isin(selected_chunk_ids)].copy()
        target_chunks_df = target_chunks_df.sort_values("chunk_id", kind="stable").reset_index(drop=True)
    elif bool(config_snapshot.get("USE_TARGET_CHUNK_WINDOW", False)):
        start_0 = max(0, int(config_snapshot.get("TARGET_CHUNK_WINDOW_START_1BASED", 1)) - 1)
        count = int(config_snapshot.get("TARGET_CHUNK_WINDOW_COUNT", 0))
        assert count > 0, {"reason": "target_chunk_window_count_must_be_positive", "count": count}
        end_0 = min(start_0 + count, len(base_df))
        target_chunks_df = base_df.iloc[start_0:end_0].copy().reset_index(drop=True)
    else:
        raise AssertionError({"reason": "unsupported target chunk mode", "target_mode": target_mode})

    if "target_local_chunk_index" not in target_chunks_df.columns:
        target_chunks_df["target_local_chunk_index"] = range(len(target_chunks_df))

    if "execution_batch_index" not in target_chunks_df.columns:
        batch_size = int(config_snapshot.get("BATCH_SIZE", 1))
        target_chunks_df["execution_batch_index"] = target_chunks_df["target_local_chunk_index"].astype(int) // batch_size

    if "execution_batch_name" not in target_chunks_df.columns:
        target_chunks_df["execution_batch_name"] = target_chunks_df["execution_batch_index"].astype(int).map(lambda x: f"batch_{x:03d}")

    batch_plan_df = (
        target_chunks_df.groupby(["execution_batch_index", "execution_batch_name"], sort=True)
        .agg(
            chunk_from=("target_local_chunk_index", "min"),
            chunk_to=("target_local_chunk_index", "max"),
            chunk_count=("chunk_name", "size"),
        )
        .reset_index()
        .rename(columns={"execution_batch_index": "batch_index", "execution_batch_name": "batch_name"})
    )

    base_df["is_target"] = base_df["chunk_name"].astype(str).isin(target_chunks_df["chunk_name"].astype(str))
    target_index_map = dict(zip(target_chunks_df["chunk_name"].astype(str), target_chunks_df["target_local_chunk_index"].astype(int)))
    target_batch_index_map = dict(zip(target_chunks_df["chunk_name"].astype(str), target_chunks_df["execution_batch_index"].astype(int)))
    target_batch_name_map = dict(zip(target_chunks_df["chunk_name"].astype(str), target_chunks_df["execution_batch_name"].astype(str)))
    base_df["target_local_chunk_index"] = base_df["chunk_name"].astype(str).map(target_index_map)
    base_df["execution_batch_index"] = base_df["chunk_name"].astype(str).map(target_batch_index_map)
    base_df["execution_batch_name"] = base_df["chunk_name"].astype(str).map(target_batch_name_map)
    base_df["target_local_chunk_index"] = base_df["target_local_chunk_index"].astype("Int64")
    base_df["execution_batch_index"] = base_df["execution_batch_index"].astype("Int64")
    base_df["execution_batch_name"] = base_df["execution_batch_name"].fillna("")
    base_df.to_csv(chunk_execution_plan_path, index=False, encoding="utf-8")

    target_chunks_df.to_csv(fallback_chunk_target_path, index=False, encoding="utf-8")
    batch_plan_df.to_csv(fallback_batch_plan_path, index=False, encoding="utf-8")
    return target_chunks_df, batch_plan_df

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

if (not execution_chunk_path.exists()) or (not execution_batch_plan_path.exists()):
    build_target_chunk_and_batch_plan()

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
    "chunk_execution_plan_path": str(chunk_execution_plan_path),
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
    "self_heal_chunk_index_target_exists": bool(fallback_chunk_target_path.exists()),
    "self_heal_batch_plan_exists": bool(fallback_batch_plan_path.exists()),
}

save_json(chunk_manifest_dir / "execution_target_resolution_summary.json", summary)

print(json.dumps(summary, indent=2, ensure_ascii=False))
display(execution_chunks_df.head())
display(execution_batch_plan_df)
display_stage_summary(
    "8-5",
    "execution target resolve",
    inputs=[
        {"item": "chunk_execution_plan", "path": str(chunk_execution_plan_path)},
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
