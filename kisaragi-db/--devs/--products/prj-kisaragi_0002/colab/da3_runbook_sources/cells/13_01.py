#13-1

ctx = load_ctx()

probe_root = Path(ctx["probe_root"])
persist_root = Path(ctx.get("persist_root", probe_root))
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
merged_dir = Path(ctx.get("merged_dir", str(pipeline_root / "merged")))
merged_dir.mkdir(parents=True, exist_ok=True)

final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_diagnostics_dir.mkdir(parents=True, exist_ok=True)

anchor_dir = persist_root / "01_anchor"
camera_anchor_full_path = anchor_dir / "camera_anchor_full_arc.csv"

batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
assert batch_execution_items_path.exists(), batch_execution_items_path
assert camera_anchor_full_path.exists(), camera_anchor_full_path

items_df = pd.read_csv(batch_execution_items_path)
assert not items_df.empty, batch_execution_items_path

anchor_full_df = pd.read_csv(camera_anchor_full_path)
if "cx_world" not in anchor_full_df.columns and "cam_cx" in anchor_full_df.columns:
    anchor_full_df["cx_world"] = anchor_full_df["cam_cx"]
    anchor_full_df["cy_world"] = anchor_full_df["cam_cy"]
    anchor_full_df["cz_world"] = anchor_full_df["cam_cz"]
if "anchor_lens_x" not in anchor_full_df.columns and "lens_x" in anchor_full_df.columns:
    anchor_full_df["anchor_lens_x"] = anchor_full_df["lens_x"]
    anchor_full_df["anchor_lens_y"] = anchor_full_df["lens_y"]
    anchor_full_df["anchor_lens_z"] = anchor_full_df["lens_z"]
if "anchor_up_x" not in anchor_full_df.columns and "up_x" in anchor_full_df.columns:
    anchor_full_df["anchor_up_x"] = anchor_full_df["up_x"]
    anchor_full_df["anchor_up_y"] = anchor_full_df["up_y"]
    anchor_full_df["anchor_up_z"] = anchor_full_df["up_z"]

required_anchor_cols = [
    "record_index",
    "cx_world", "cy_world", "cz_world",
    "anchor_lens_x", "anchor_lens_y", "anchor_lens_z",
    "anchor_up_x", "anchor_up_y", "anchor_up_z",
]
missing_anchor_cols = [c for c in required_anchor_cols if c not in anchor_full_df.columns]
assert not missing_anchor_cols, {"missing_anchor_columns": missing_anchor_cols}

LOCAL_EXTRINSIC_MODE = "c2w"
LOCAL_CAMERA_BASIS = np.eye(4, dtype=np.float32)
LOCAL_CAMERA_BASIS[:3, :3] = np.array([
    [0.0, 1.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.0, 0.0, -1.0],
], dtype=np.float32)


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


def normalize_rows(arr: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    arr = np.asarray(arr, dtype=np.float64)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    norm = np.linalg.norm(arr, axis=1, keepdims=True)
    return arr / np.maximum(norm, eps)


def angle_deg(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = normalize_rows(a)
    b = normalize_rows(b)
    dot = np.sum(a * b, axis=1)
    dot = np.clip(dot, -1.0, 1.0)
    return np.degrees(np.arccos(dot))


def lens_direction_from_c2w(c2w: np.ndarray) -> np.ndarray:
    axis = -np.asarray(c2w[:3, 2], dtype=np.float64)
    return axis / max(float(np.linalg.norm(axis)), 1e-12)


def up_direction_from_c2w(c2w: np.ndarray) -> np.ndarray:
    axis = -np.asarray(c2w[:3, 1], dtype=np.float64)
    return axis / max(float(np.linalg.norm(axis)), 1e-12)


def normalize_vec(vec: np.ndarray, fallback: np.ndarray) -> np.ndarray:
    vec = np.asarray(vec, dtype=np.float64)
    norm = float(np.linalg.norm(vec))
    if norm <= 1e-12:
        fallback = np.asarray(fallback, dtype=np.float64)
        fallback_norm = float(np.linalg.norm(fallback))
        assert fallback_norm > 1e-12, "fallback vector must be non-zero"
        return fallback / fallback_norm
    return vec / norm


def build_anchor_c2w_list(anchor_df: pd.DataFrame) -> list[np.ndarray]:
    mats = []
    for rec in anchor_df.itertuples(index=False):
        center = np.array([float(rec.cx_world), float(rec.cy_world), float(rec.cz_world)], dtype=np.float64)
        anchor_lens = normalize_vec(
            np.array([float(rec.anchor_lens_x), float(rec.anchor_lens_y), float(rec.anchor_lens_z)], dtype=np.float64),
            np.array([0.0, 0.0, -1.0], dtype=np.float64),
        )
        anchor_up = normalize_vec(
            np.array([float(rec.anchor_up_x), float(rec.anchor_up_y), float(rec.anchor_up_z)], dtype=np.float64),
            np.array([0.0, -1.0, 0.0], dtype=np.float64),
        )
        z_col = normalize_vec(-anchor_lens, np.array([0.0, 0.0, 1.0], dtype=np.float64))
        x_seed = np.cross(-anchor_up, z_col)
        x_col = normalize_vec(x_seed, np.array([1.0, 0.0, 0.0], dtype=np.float64))
        y_col = normalize_vec(np.cross(z_col, x_col), np.array([0.0, 1.0, 0.0], dtype=np.float64))
        if float(np.dot(y_col, -anchor_up)) < 0.0:
            x_col = -x_col
            y_col = -y_col
        M = np.eye(4, dtype=np.float32)
        M[:3, 0] = x_col.astype(np.float32)
        M[:3, 1] = y_col.astype(np.float32)
        M[:3, 2] = z_col.astype(np.float32)
        M[:3, 3] = center.astype(np.float32)
        mats.append(M)
    return mats


def local_c2w_list(pred_extrinsics: np.ndarray) -> list[np.ndarray]:
    mats = []
    for ext in to_4x4_batch(pred_extrinsics):
        raw = ext.astype(np.float32)
        if LOCAL_EXTRINSIC_MODE == "c2w":
            c2w = raw
        elif LOCAL_EXTRINSIC_MODE == "w2c":
            c2w = np.linalg.inv(raw).astype(np.float32)
        else:
            raise AssertionError({"unsupported_extrinsic_mode": LOCAL_EXTRINSIC_MODE})
        mats.append((c2w @ LOCAL_CAMERA_BASIS).astype(np.float32))
    return mats


def estimate_pose_aware_similarity(local_c2w_rows: list[np.ndarray], global_c2w_rows: list[np.ndarray]) -> tuple[np.ndarray, dict]:
    assert len(local_c2w_rows) == len(global_c2w_rows) >= 2, {"local_len": len(local_c2w_rows), "global_len": len(global_c2w_rows)}

    src_dirs, dst_dirs, src_centers, dst_centers = [], [], [], []
    for local_c2w, global_c2w in zip(local_c2w_rows, global_c2w_rows):
        src_dirs.append(lens_direction_from_c2w(local_c2w))
        src_dirs.append(up_direction_from_c2w(local_c2w))
        dst_dirs.append(lens_direction_from_c2w(global_c2w))
        dst_dirs.append(up_direction_from_c2w(global_c2w))
        src_centers.append(local_c2w[:3, 3])
        dst_centers.append(global_c2w[:3, 3])

    src_dirs = np.asarray(src_dirs, dtype=np.float64)
    dst_dirs = np.asarray(dst_dirs, dtype=np.float64)
    src_centers = np.asarray(src_centers, dtype=np.float64)
    dst_centers = np.asarray(dst_centers, dtype=np.float64)

    H = dst_dirs.T @ src_dirs
    U, _, Vt = np.linalg.svd(H)
    S = np.eye(3, dtype=np.float64)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[-1, -1] = -1.0
    R = U @ S @ Vt

    src_mean = src_centers.mean(axis=0)
    dst_mean = dst_centers.mean(axis=0)
    src_c = src_centers - src_mean
    dst_c = dst_centers - dst_mean
    src_rot = (R @ src_c.T).T

    denom = float(np.sum(src_rot ** 2))
    numer = float(np.sum(dst_c * src_rot))
    scale = numer / max(denom, 1e-12)
    t = dst_mean - scale * (R @ src_mean)

    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = scale * R
    T[:3, 3] = t
    diag = {
        "scale": float(scale),
        "rotation_det": float(np.linalg.det(R)),
        "center_rmse": float(np.sqrt(np.mean(np.sum((((scale * (R @ src_centers.T)).T + t) - dst_centers) ** 2, axis=1)))),
        "rotation_dir_residual": float(np.mean(np.linalg.norm(((R @ src_dirs.T).T - dst_dirs), axis=1))),
    }
    return T.astype(np.float32), diag


def transform_c2w_list(c2w_rows: list[np.ndarray], T: np.ndarray) -> list[np.ndarray]:
    out = []
    for c2w in c2w_rows:
        M = np.asarray(c2w, dtype=np.float64).copy()
        M[:3, :3] = T[:3, :3] @ M[:3, :3]
        M[:3, 3] = T[:3, :3] @ M[:3, 3] + T[:3, 3]
        out.append(M.astype(np.float32))
    return out


residual_rows = []
missing_pred_chunks = []

for row in items_df.itertuples(index=False):
    batch_name = str(row.batch_name)
    chunk_name = str(row.chunk_name)
    batch_work_dir = Path(row.batch_work_dir)
    chunk_anchor_csv = Path(row.chunk_sequence_anchor_csv)

    assert chunk_anchor_csv.exists(), {"chunk_name": chunk_name, "missing_anchor_csv": str(chunk_anchor_csv)}
    chunk_df = pd.read_csv(chunk_anchor_csv)
    assert not chunk_df.empty, {"chunk_name": chunk_name, "reason": "empty anchor csv"}
    assert "record_index" in chunk_df.columns, {"chunk_name": chunk_name, "reason": "record_index missing"}

    pred_candidates = [
        batch_work_dir / chunk_name / "pred_extrinsics.npy",
        chunk_runs_dir / chunk_name / "pred_extrinsics.npy",
        batch_work_dir / f"{chunk_name}_pred_extrinsics.npy",
    ]
    pred_path = next((p for p in pred_candidates if p.exists()), None)
    if pred_path is None:
        missing_pred_chunks.append({"batch_name": batch_name, "chunk_name": chunk_name, "reason": "pred_extrinsics.npy not found yet"})
        continue

    anchor_df = chunk_df.merge(
        anchor_full_df[required_anchor_cols],
        on="record_index",
        how="left",
        validate="many_to_one",
    )
    assert not anchor_df[required_anchor_cols[1:]].isnull().any().any(), {
        "chunk_name": chunk_name,
        "reason": "full anchor join failed",
    }

    pred = to_4x4_batch(np.load(pred_path))
    n = min(len(anchor_df), pred.shape[0])
    if n <= 0:
        continue

    pred = pred[:n]
    anchor_df = anchor_df.iloc[:n].copy()

    local_rows = local_c2w_list(pred)
    global_rows = build_anchor_c2w_list(anchor_df)
    T_c_to_w0, align_diag = estimate_pose_aware_similarity(local_rows, global_rows)
    transformed_rows = transform_c2w_list(local_rows, T_c_to_w0)

    pred_center = np.stack([m[:3, 3] for m in transformed_rows], axis=0)
    pred_lens = np.stack([lens_direction_from_c2w(m) for m in transformed_rows], axis=0)
    anchor_center = anchor_df[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=float)
    anchor_lens = anchor_df[["anchor_lens_x", "anchor_lens_y", "anchor_lens_z"]].to_numpy(dtype=float)

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
            "record_index": int(anchor_df.iloc[i]["record_index"]) if pd.notna(anchor_df.iloc[i]["record_index"]) else None,
            "sequence_index": int(anchor_df.iloc[i]["sequence_index"]) if "sequence_index" in anchor_df.columns and pd.notna(anchor_df.iloc[i]["sequence_index"]) else None,
            "center_error": float(center_error[i]),
            "lens_error_deg": float(lens_error_deg[i]),
            "delta_center_error": float(delta_center_error[i]),
            "delta_lens_error_deg": float(delta_lens_error_deg[i]),
            "pred_extrinsics_path": str(pred_path),
            "local_extrinsic_mode": LOCAL_EXTRINSIC_MODE,
            "local_camera_basis": "perm_yxz_sign_ppn",
            "transform_scale": float(align_diag["scale"]),
            "transform_rotation_det": float(align_diag["rotation_det"]),
            "transform_center_rmse": float(align_diag["center_rmse"]),
            "transform_rotation_dir_residual": float(align_diag["rotation_dir_residual"]),
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
            "local_extrinsic_mode": str(cdf["local_extrinsic_mode"].iloc[0]),
            "local_camera_basis": str(cdf["local_camera_basis"].iloc[0]),
            "transform_scale_mean": float(cdf["transform_scale"].mean()),
            "transform_center_rmse_mean": float(cdf["transform_center_rmse"].mean()),
            "transform_rotation_dir_residual_mean": float(cdf["transform_rotation_dir_residual"].mean()),
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

PREMERGE_CENTER_ERROR_P95_MAX = 0.25
PREMERGE_LENS_ERROR_DEG_P95_MAX = 12.0
PREMERGE_DELTA_CENTER_ERROR_MAX = 0.15
PREMERGE_DELTA_LENS_ERROR_DEG_MAX = 8.0

validation_rows = []
if len(gate_df):
    for row in gate_df.itertuples(index=False):
        center_error_p95 = float(row.center_error_p95)
        lens_error_deg_p95 = float(row.lens_error_deg_p95)
        delta_center_error_max = float(row.delta_center_error_max)
        delta_lens_error_deg_max = float(row.delta_lens_error_deg_max)
        validation_rows.append({
            "chunk_name": str(row.chunk_name),
            "row_count": int(row.row_count),
            "local_extrinsic_mode": str(row.local_extrinsic_mode),
            "local_camera_basis": str(row.local_camera_basis),
            "transform_scale_mean": float(row.transform_scale_mean),
            "transform_center_rmse_mean": float(row.transform_center_rmse_mean),
            "transform_rotation_dir_residual_mean": float(row.transform_rotation_dir_residual_mean),
            "center_error_mean": float(row.center_error_mean),
            "center_error_p95": center_error_p95,
            "lens_error_deg_mean": float(row.lens_error_deg_mean),
            "lens_error_deg_p95": lens_error_deg_p95,
            "delta_center_error_max": delta_center_error_max,
            "delta_lens_error_deg_max": delta_lens_error_deg_max,
            "center_error_p95_ok": bool(center_error_p95 <= PREMERGE_CENTER_ERROR_P95_MAX),
            "lens_error_deg_p95_ok": bool(lens_error_deg_p95 <= PREMERGE_LENS_ERROR_DEG_P95_MAX),
            "delta_center_error_ok": bool(delta_center_error_max <= PREMERGE_DELTA_CENTER_ERROR_MAX),
            "delta_lens_error_deg_ok": bool(delta_lens_error_deg_max <= PREMERGE_DELTA_LENS_ERROR_DEG_MAX),
            "hard_fail": bool(
                (center_error_p95 > PREMERGE_CENTER_ERROR_P95_MAX)
                or (lens_error_deg_p95 > PREMERGE_LENS_ERROR_DEG_P95_MAX)
                or (delta_center_error_max > PREMERGE_DELTA_CENTER_ERROR_MAX)
                or (delta_lens_error_deg_max > PREMERGE_DELTA_LENS_ERROR_DEG_MAX)
            ),
        })
validation_df = pd.DataFrame(validation_rows)
validation_csv = merged_dir / "premerge_pose_validation.csv"
validation_df.to_csv(validation_csv, index=False, encoding="utf-8")
hard_fail_df = validation_df[validation_df["hard_fail"]].copy() if len(validation_df) else validation_df.copy()
validation_json = merged_dir / "premerge_pose_validation.json"

if len(residual_df) == 0:
    status = "not_run"
elif len(missing_pred_df) > 0:
    status = "partial"
elif len(hard_fail_df) > 0:
    status = "fail"
else:
    status = "ok"

summary = {
    "status": status,
    "route": "continuous-gs-v06-chunk18-overlap6-adopt12-premerge-pose-gate",
    "residual_row_count": int(len(residual_df)),
    "missing_pred_chunk_count": int(len(missing_pred_df)),
    "gate_chunk_count": int(len(gate_df)),
    "residual_csv": str(residual_csv),
    "missing_pred_csv": str(missing_pred_csv),
    "gate_csv": str(gate_csv),
    "validation_csv": str(validation_csv),
    "local_extrinsic_mode": LOCAL_EXTRINSIC_MODE,
    "local_camera_basis": "perm_yxz_sign_ppn",
    "thresholds": {
        "center_error_p95_max": PREMERGE_CENTER_ERROR_P95_MAX,
        "lens_error_deg_p95_max": PREMERGE_LENS_ERROR_DEG_P95_MAX,
        "delta_center_error_max": PREMERGE_DELTA_CENTER_ERROR_MAX,
        "delta_lens_error_deg_max": PREMERGE_DELTA_LENS_ERROR_DEG_MAX,
    },
    "tested_chunk_count": int(len(validation_df)),
    "hard_fail_count": int(len(hard_fail_df)),
    "failed_chunks": hard_fail_df[
        ["chunk_name", "center_error_p95", "lens_error_deg_p95", "delta_center_error_max", "delta_lens_error_deg_max"]
    ].to_dict(orient="records") if len(hard_fail_df) else [],
}
if len(residual_df) > 0:
    summary["center_error_mean"] = float(residual_df["center_error"].mean())
    summary["center_error_p95"] = float(residual_df["center_error"].quantile(0.95))
    summary["lens_error_deg_mean"] = float(residual_df["lens_error_deg"].mean())
    summary["lens_error_deg_p95"] = float(residual_df["lens_error_deg"].quantile(0.95))
    summary["transform_scale_mean"] = float(residual_df["transform_scale"].mean())
    summary["transform_center_rmse_mean"] = float(residual_df["transform_center_rmse"].mean())
    summary["transform_rotation_dir_residual_mean"] = float(residual_df["transform_rotation_dir_residual"].mean())

save_json(validation_json, summary)
save_json(final_outputs_diagnostics_dir / "premerge_pose_gate_summary.json", summary)
save_json(final_outputs_diagnostics_dir / "batch_residual_summary.json", summary)
save_json(final_outputs_diagnostics_dir / "premerge_pose_validation.json", summary)

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
        {"item": "camera_anchor_full_arc", "path": str(camera_anchor_full_path)},
    ],
    outputs=[
        {"item": "pred_vs_anchor_pose_residual", "path": str(residual_csv)},
        {"item": "pred_vs_anchor_pose_residual_missing_pred", "path": str(missing_pred_csv)},
        {"item": "premerge_pose_gate", "path": str(gate_csv)},
        {"item": "premerge_pose_gate_summary", "path": str(final_outputs_diagnostics_dir / "premerge_pose_gate_summary.json")},
        {"item": "premerge_pose_validation", "path": str(validation_json)},
        {"item": "batch_residual_summary", "path": str(final_outputs_diagnostics_dir / "batch_residual_summary.json")},
    ],
    notes=[
        {"item": "status", "value": status},
        {"item": "local_extrinsic_mode", "value": LOCAL_EXTRINSIC_MODE},
        {"item": "local_camera_basis", "value": "perm_yxz_sign_ppn"},
        {"item": "missing_pred_chunk_count", "value": int(len(missing_pred_df))},
        {"item": "hard_fail_count", "value": int(len(hard_fail_df))},
    ],
)
