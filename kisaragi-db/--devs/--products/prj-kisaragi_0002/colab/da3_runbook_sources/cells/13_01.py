#13-1

ctx = load_ctx()

probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"

final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_diagnostics_dir.mkdir(parents=True, exist_ok=True)

batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
assert batch_execution_items_path.exists(), batch_execution_items_path

items_df = pd.read_csv(batch_execution_items_path)
assert not items_df.empty, batch_execution_items_path

def resolve_center_cols(df: pd.DataFrame):
    candidates = [
        ("cam_cx", "cam_cy", "cam_cz"),
        ("cx_world", "cy_world", "cz_world"),
        ("tx", "ty", "tz"),
        ("cx", "cy", "cz"),
    ]
    return next((cols for cols in candidates if all(c in df.columns for c in cols)), None)

def resolve_ypr_cols(df: pd.DataFrame):
    candidates = [
        ("yaw_deg", "pitch_deg", "roll_deg"),
        ("yaw_deg_record", "pitch_deg_record", "roll_deg_record"),
    ]
    return next((cols for cols in candidates if all(c in df.columns for c in cols)), None)

def resolve_lens_cols(df: pd.DataFrame):
    candidates = [
        ("lens_x", "lens_y", "lens_z"),
        ("anchor_lens_x", "anchor_lens_y", "anchor_lens_z"),
        ("forward_x", "forward_y", "forward_z"),
    ]
    return next((cols for cols in candidates if all(c in df.columns for c in cols)), None)

def lens_from_yaw_pitch_deg(yaw_deg: np.ndarray, pitch_deg: np.ndarray) -> np.ndarray:
    yaw = np.deg2rad(yaw_deg.astype(float))
    pitch = np.deg2rad(pitch_deg.astype(float))
    fx = np.sin(yaw) * np.cos(pitch)
    fy = -np.sin(pitch)
    fz = np.cos(yaw) * np.cos(pitch)
    return normalize_rows(np.stack([fx, fy, fz], axis=1))

residual_rows = []
missing_pred_chunks = []

for row in items_df.itertuples(index=False):
    batch_name = str(row.batch_name)
    chunk_name = str(row.chunk_name)
    batch_work_dir = Path(row.batch_work_dir)
    chunk_anchor_csv = Path(row.chunk_sequence_anchor_csv)

    assert chunk_anchor_csv.exists(), {"chunk_name": chunk_name, "missing_anchor_csv": str(chunk_anchor_csv)}
    anchor_df = pd.read_csv(chunk_anchor_csv)
    assert not anchor_df.empty, {"chunk_name": chunk_name, "reason": "empty anchor csv"}

    center_cols = resolve_center_cols(anchor_df)
    lens_cols = resolve_lens_cols(anchor_df)
    ypr_cols = resolve_ypr_cols(anchor_df)

    assert center_cols is not None, {"chunk_name": chunk_name, "reason": "center cols not found", "available_columns": anchor_df.columns.tolist()}
    assert (lens_cols is not None) or (ypr_cols is not None), {"chunk_name": chunk_name, "reason": "neither lens cols nor yaw/pitch/roll cols found", "available_columns": anchor_df.columns.tolist()}

    pred_candidates = [
        batch_work_dir / chunk_name / "pred_extrinsics.npy",
        chunk_runs_dir / chunk_name / "pred_extrinsics.npy",
        batch_work_dir / f"{chunk_name}_pred_extrinsics.npy",
    ]
    pred_path = next((p for p in pred_candidates if p.exists()), None)

    if pred_path is None:
        missing_pred_chunks.append({"batch_name": batch_name, "chunk_name": chunk_name, "reason": "pred_extrinsics.npy not found yet"})
        continue

    # pred = np.load(pred_path)
    # assert pred.ndim == 3 and pred.shape[1:] == (4, 4), {"chunk_name": chunk_name, "pred_shape": tuple(pred.shape)}

    # n = min(len(anchor_df), pred.shape[0])
    # if n <= 0:
    #     continue

    # pred = pred[:n]
    # a = anchor_df.iloc[:n].copy()

    # pred_c2w = np.linalg.inv(pred)

    pred = np.load(pred_path)

    def to_4x4_batch(arr: np.ndarray) -> np.ndarray:
        arr = np.asarray(arr)
        assert arr.ndim == 3, {"pred_shape": tuple(arr.shape)}
        if arr.shape[1:] == (4, 4):
            return arr.astype(np.float32)
        if arr.shape[1:] == (3, 4):
            out = np.repeat(np.eye(4, dtype=np.float32)[None, :, :], arr.shape[0], axis=0)
            out[:, :3, :] = arr.astype(np.float32)
            return out
        raise AssertionError({"pred_shape": tuple(arr.shape), "expected": "(N,4,4) or (N,3,4)"})

    pred = to_4x4_batch(pred)

    n = min(len(anchor_df), pred.shape[0])
    if n <= 0:
        continue

    pred = pred[:n]
    pred_c2w = np.linalg.inv(pred)

    pred_center = pred_c2w[:, :3, 3]
    pred_lens = -pred_c2w[:, :3, 2]
    a = anchor_df.iloc[:n].copy()


    anchor_center = a[list(center_cols)].to_numpy(float)
    if lens_cols is not None:
        anchor_lens = a[list(lens_cols)].to_numpy(float)
    else:
        yaw_col, pitch_col, _ = ypr_cols
        anchor_lens = lens_from_yaw_pitch_deg(a[yaw_col].to_numpy(float), a[pitch_col].to_numpy(float))

    center_error = np.linalg.norm(pred_center - anchor_center, axis=1)
    lens_error_deg = angle_deg(pred_lens, anchor_lens)

    delta_center_error = np.zeros(n, dtype=float)
    delta_lens_error_deg = np.zeros(n, dtype=float)
    if n >= 2:
        delta_center_error[1:] = np.abs(np.diff(center_error))
        delta_lens_error_deg[1:] = np.abs(np.diff(lens_error_deg))

    for i in range(n):
        residual_rows.append({
            "batch_name": batch_name,
            "chunk_name": chunk_name,
            "local_index": int(i),
            "record_index": int(a.iloc[i]["record_index"]) if "record_index" in a.columns and pd.notna(a.iloc[i]["record_index"]) else None,
            "sequence_index": int(a.iloc[i]["sequence_index"]) if "sequence_index" in a.columns and pd.notna(a.iloc[i]["sequence_index"]) else None,
            "center_error": float(center_error[i]),
            "lens_error_deg": float(lens_error_deg[i]),
            "delta_center_error": float(delta_center_error[i]),
            "delta_lens_error_deg": float(delta_lens_error_deg[i]),
            "pred_extrinsics_path": str(pred_path),
        })

residual_df = pd.DataFrame(residual_rows)
residual_csv = chunk_manifest_dir / "pred_vs_anchor_pose_residual.csv"
residual_df.to_csv(residual_csv, index=False, encoding="utf-8")

missing_pred_df = pd.DataFrame(missing_pred_chunks)
missing_pred_csv = chunk_manifest_dir / "pred_vs_anchor_pose_residual_missing_pred.csv"
missing_pred_df.to_csv(missing_pred_csv, index=False, encoding="utf-8")

gate_rows = []
if len(residual_df):
    for chunk_name, cdf in residual_df.groupby("chunk_name", sort=True):
        gate_rows.append({
            "chunk_name": chunk_name,
            "row_count": int(len(cdf)),
            "center_error_mean": float(cdf["center_error"].mean()),
            "center_error_p95": float(cdf["center_error"].quantile(0.95)),
            "lens_error_deg_mean": float(cdf["lens_error_deg"].mean()),
            "lens_error_deg_p95": float(cdf["lens_error_deg"].quantile(0.95)),
            "delta_center_error_max": float(cdf["delta_center_error"].max()),
            "delta_lens_error_deg_max": float(cdf["delta_lens_error_deg"].max()),
        })
gate_df = pd.DataFrame(gate_rows)
gate_csv = chunk_manifest_dir / "premerge_pose_gate.csv"
gate_df.to_csv(gate_csv, index=False, encoding="utf-8")

if len(residual_df) == 0:
    status = "not_run"
elif len(missing_pred_df) > 0:
    status = "partial"
else:
    status = "ok"

summary = {
    "status": status,
    "residual_row_count": int(len(residual_df)),
    "missing_pred_chunk_count": int(len(missing_pred_df)),
    "gate_chunk_count": int(len(gate_df)),
    "residual_csv": str(residual_csv),
    "missing_pred_csv": str(missing_pred_csv),
    "gate_csv": str(gate_csv),
}
if len(residual_df) > 0:
    summary["center_error_mean"] = float(residual_df["center_error"].mean())
    summary["center_error_p95"] = float(residual_df["center_error"].quantile(0.95))
    summary["lens_error_deg_mean"] = float(residual_df["lens_error_deg"].mean())
    summary["lens_error_deg_p95"] = float(residual_df["lens_error_deg"].quantile(0.95))

save_json(final_outputs_diagnostics_dir / "premerge_pose_gate_summary.json", summary)
save_json(final_outputs_diagnostics_dir / "batch_residual_summary.json", summary)

print(json.dumps(summary, indent=2, ensure_ascii=False))
if len(gate_df):
    display(gate_df)
if len(missing_pred_df):
    display(missing_pred_df.head())
display_stage_summary(
    "13-1",
    "prediction validation",
    inputs=[
        {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
    ],
    outputs=[
        {"item": "pred_vs_anchor_pose_residual", "path": str(residual_csv)},
        {"item": "pred_vs_anchor_pose_residual_missing_pred", "path": str(missing_pred_csv)},
        {"item": "premerge_pose_gate", "path": str(gate_csv)},
        {"item": "premerge_pose_gate_summary", "path": str(final_outputs_diagnostics_dir / "premerge_pose_gate_summary.json")},
        {"item": "batch_residual_summary", "path": str(final_outputs_diagnostics_dir / "batch_residual_summary.json")},
    ],
    notes=[
        {"item": "status", "value": status},
        {"item": "missing_pred_chunk_count", "value": int(len(missing_pred_df))},
    ],
)
