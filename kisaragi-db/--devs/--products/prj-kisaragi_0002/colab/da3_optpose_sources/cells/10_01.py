#10-1

from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as SciRot

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
sort_cols = [c for c in ["chunk_id", "batch_index", "batch_name", "chunk_name"] if c in items_df.columns]
if sort_cols:
    items_df = items_df.sort_values(sort_cols, kind="stable").reset_index(drop=True)

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

ROUTE_ARCORE = "arcore_anchor_baseline"
ROUTE_DA3 = "da3_predicted_primary"
PREFERRED_ROUTE_LABEL = ROUTE_DA3
LOCAL_EXTRINSIC_MODE = "c2w"
LOCAL_CAMERA_BASIS = np.eye(4, dtype=np.float32)
LOCAL_CAMERA_BASIS[:3, :3] = np.array([
    [0.0, 1.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.0, 0.0, -1.0],
], dtype=np.float32)

PREMERGE_CENTER_ERROR_P95_MAX = 0.25
PREMERGE_LENS_ERROR_DEG_P95_MAX = 12.0
PREMERGE_DELTA_CENTER_ERROR_MAX = 0.15
PREMERGE_DELTA_LENS_ERROR_DEG_MAX = 8.0
TRANSFORM_SCALE_MIN = 0.8
TRANSFORM_SCALE_MAX = 1.3
TRANSFORM_CENTER_RMSE_MAX = 0.15
TRANSFORM_ROT_DIR_MAX = 0.20


SIM3_GRAPH_OPTIMIZATION = True
GRAPH_OPT_MAX_NFEV = 400
GRAPH_PRIOR_WEIGHT = 0.05
GRAPH_EDGE_TRANSLATION_WEIGHT = 1.0
GRAPH_EDGE_ROTATION_WEIGHT = 0.35
GRAPH_EDGE_SCALE_WEIGHT = 0.20
GRAPH_ANCHOR_WEIGHT = 0.02
GRAPH_ANCHOR_ROT_WEIGHT = 0.01
GRAPH_ANCHOR_FRAME_TRANSLATION_WEIGHT = 0.60
GRAPH_ANCHOR_FRAME_DIRECTION_WEIGHT = 0.45
GRAPH_ANCHOR_OVERLAP_FRAME_WEIGHT = 0.20
GRAPH_ANCHOR_NONOVERLAP_FRAME_WEIGHT = 1.00

def summarize_split_metrics(values: np.ndarray, overlap_mask: np.ndarray, prefix: str) -> dict:
    values = np.asarray(values, dtype=np.float64)
    overlap_mask = np.asarray(overlap_mask, dtype=bool)
    nonoverlap_mask = ~overlap_mask

    def pack(mask: np.ndarray, label: str) -> dict:
        count = int(mask.sum())
        base = {
            f"{prefix}_{label}_count": count,
            f"{prefix}_{label}_mean": None,
            f"{prefix}_{label}_p95": None,
            f"{prefix}_{label}_max": None,
        }
        if count <= 0:
            return base
        subset = values[mask]
        base[f"{prefix}_{label}_mean"] = float(subset.mean())
        base[f"{prefix}_{label}_p95"] = float(np.quantile(subset, 0.95))
        base[f"{prefix}_{label}_max"] = float(subset.max())
        return base

    out = {}
    out.update(pack(overlap_mask, "overlap"))
    out.update(pack(nonoverlap_mask, "nonoverlap"))
    return out

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


def transform_c2w_list(c2w_rows: list[np.ndarray], T: np.ndarray) -> list[np.ndarray]:
    out = []
    for c2w in c2w_rows:
        M = np.asarray(c2w, dtype=np.float64).copy()
        M[:3, :3] = T[:3, :3] @ M[:3, :3]
        M[:3, 3] = T[:3, :3] @ M[:3, 3] + T[:3, 3]
        out.append(M.astype(np.float32))
    return out


def summarize_candidate(
    *,
    batch_name: str,
    chunk_name: str,
    route_label: str,
    route_source: str,
    route_overlap_record_count: int,
    overlap_record_indices: list[int],
    transformed_rows: list[np.ndarray],
    anchor_df: pd.DataFrame,
    align_diag: dict,
) -> tuple[dict, pd.DataFrame]:
    n = len(transformed_rows)
    pred_center = np.stack([m[:3, 3] for m in transformed_rows], axis=0)
    pred_lens = np.stack([lens_direction_from_c2w(m) for m in transformed_rows], axis=0)
    anchor_center = anchor_df[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=float)
    anchor_lens = anchor_df[["anchor_lens_x", "anchor_lens_y", "anchor_lens_z"]].to_numpy(dtype=float)
    record_indices = anchor_df["record_index"].astype(int).to_numpy()
    overlap_index_set = {int(x) for x in overlap_record_indices}
    overlap_mask = np.array([int(x) in overlap_index_set for x in record_indices], dtype=bool)

    center_error = np.linalg.norm(pred_center - anchor_center, axis=1)
    lens_error_deg = angle_deg(pred_lens, anchor_lens)
    delta_center_error = np.zeros(n, dtype=float)
    delta_lens_error_deg = np.zeros(n, dtype=float)
    if n >= 2:
        delta_center_error[1:] = np.abs(np.diff(center_error))
        delta_lens_error_deg[1:] = np.abs(np.diff(lens_error_deg))

    residual_df = pd.DataFrame({
        "batch_name": batch_name,
        "chunk_name": chunk_name,
        "route_label": route_label,
        "route_source": route_source,
        "route_overlap_record_count": int(route_overlap_record_count),
        "route_overlap_local_count": int(overlap_mask.sum()),
        "route_nonoverlap_local_count": int((~overlap_mask).sum()),
        "route_overlap_record_indices": ",".join(str(int(x)) for x in sorted(overlap_index_set)),
        "local_index": np.arange(n, dtype=np.int64),
        "record_index": record_indices,
        "sequence_index": anchor_df["sequence_index"].astype(int).to_numpy() if "sequence_index" in anchor_df.columns else np.arange(n, dtype=np.int64),
        "is_overlap_record": overlap_mask.astype(bool),
        "center_error": center_error.astype(float),
        "lens_error_deg": lens_error_deg.astype(float),
        "delta_center_error": delta_center_error.astype(float),
        "delta_lens_error_deg": delta_lens_error_deg.astype(float),
        "local_extrinsic_mode": LOCAL_EXTRINSIC_MODE,
        "local_camera_basis": "perm_yxz_sign_ppn",
        "transform_scale": float(align_diag["scale"]),
        "transform_rotation_det": float(align_diag["rotation_det"]),
        "transform_center_rmse": float(align_diag["center_rmse"]),
        "transform_rotation_dir_residual": float(align_diag["rotation_dir_residual"]),
    })

    center_error_p95 = float(np.quantile(center_error, 0.95))
    lens_error_deg_p95 = float(np.quantile(lens_error_deg, 0.95))
    delta_center_error_max = float(delta_center_error.max())
    delta_lens_error_deg_max = float(delta_lens_error_deg.max())
    center_split = summarize_split_metrics(center_error, overlap_mask, "center_error")
    lens_split = summarize_split_metrics(lens_error_deg, overlap_mask, "lens_error_deg")
    residual_warning = bool(
        (center_error_p95 > PREMERGE_CENTER_ERROR_P95_MAX)
        or (lens_error_deg_p95 > PREMERGE_LENS_ERROR_DEG_P95_MAX)
        or (delta_center_error_max > PREMERGE_DELTA_CENTER_ERROR_MAX)
        or (delta_lens_error_deg_max > PREMERGE_DELTA_LENS_ERROR_DEG_MAX)
    )
    candidate = {
        "batch_name": batch_name,
        "chunk_name": chunk_name,
        "route_label": route_label,
        "route_source": route_source,
        "route_overlap_record_count": int(route_overlap_record_count),
        "route_overlap_local_count": int(overlap_mask.sum()),
        "route_nonoverlap_local_count": int((~overlap_mask).sum()),
        "row_count": int(n),
        "local_extrinsic_mode": LOCAL_EXTRINSIC_MODE,
        "local_camera_basis": "perm_yxz_sign_ppn",
        "scale": float(align_diag["scale"]),
        "rotation_det": float(align_diag["rotation_det"]),
        "center_rmse": float(align_diag["center_rmse"]),
        "rotation_dir_residual": float(align_diag["rotation_dir_residual"]),
        "positive_similarity_ok": bool(align_diag["positive_similarity_ok"]),
        "scale_in_range_ok": bool(align_diag["scale_in_range_ok"]),
        "center_rmse_ok": bool(align_diag["center_rmse_ok"]),
        "rotation_dir_ok": bool(align_diag["rotation_dir_ok"]),
        "center_error_mean": float(center_error.mean()),
        "center_error_p95": center_error_p95,
        "lens_error_deg_mean": float(lens_error_deg.mean()),
        "lens_error_deg_p95": lens_error_deg_p95,
        "delta_center_error_max": delta_center_error_max,
        "delta_lens_error_deg_max": delta_lens_error_deg_max,
        "center_error_p95_ok": bool(center_error_p95 <= PREMERGE_CENTER_ERROR_P95_MAX),
        "lens_error_deg_p95_ok": bool(lens_error_deg_p95 <= PREMERGE_LENS_ERROR_DEG_P95_MAX),
        "delta_center_error_ok": bool(delta_center_error_max <= PREMERGE_DELTA_CENTER_ERROR_MAX),
        "delta_lens_error_deg_ok": bool(delta_lens_error_deg_max <= PREMERGE_DELTA_LENS_ERROR_DEG_MAX),
        "align_hard_fail": bool(align_diag["hard_fail"]),
        "anchor_warning": residual_warning,
        "residual_warning": residual_warning,
        "hard_fail": bool(align_diag["hard_fail"]),
    }
    candidate.update(center_split)
    candidate.update(lens_split)
    return candidate, residual_df


def pick_selected_candidate(candidates: list[dict]) -> tuple[dict, bool]:
    by_label = {c["route_label"]: c for c in candidates}
    preferred = by_label.get(PREFERRED_ROUTE_LABEL)
    baseline = by_label.get(ROUTE_ARCORE)
    preferred_anchor_warning = bool(preferred["anchor_warning"]) if preferred is not None else False
    if (
        preferred is not None
        and not preferred["align_hard_fail"]
        and not preferred_anchor_warning
    ):
        selected = preferred
    elif baseline is not None and not baseline["align_hard_fail"]:
        selected = baseline
    elif preferred is not None:
        selected = preferred
    elif baseline is not None:
        selected = baseline
    else:
        raise AssertionError({"reason": "no route candidates"})
    fallback_used = bool(selected["route_label"] != PREFERRED_ROUTE_LABEL)
    return selected, fallback_used


route_world_pose_map: dict[int, np.ndarray] = {}
candidate_rows = []
selected_rows = []
graph_solution_rows = []
graph_edge_rows = []
residual_frames = []
missing_pred_chunks = []
graph_node_measurements = {}
previous_selected_chunk_name = None
previous_selected_T = None

for row in items_df.itertuples(index=False):
    batch_name = str(row.batch_name)
    chunk_name = str(row.chunk_name)
    batch_work_dir = Path(row.batch_work_dir)

    chunk_anchor_csv_value = getattr(row, "chunk_sequence_anchor_csv", "")
    chunk_anchor_csv = None
    if pd.notna(chunk_anchor_csv_value):
        chunk_anchor_csv_value = str(chunk_anchor_csv_value).strip()
        if chunk_anchor_csv_value:
            chunk_anchor_csv = Path(chunk_anchor_csv_value)

    if chunk_anchor_csv is not None and chunk_anchor_csv.exists():
        chunk_df = pd.read_csv(chunk_anchor_csv)
    else:
        chunk_csv_value = getattr(row, "chunk_csv", "")
        assert pd.notna(chunk_csv_value) and str(chunk_csv_value).strip(), {"chunk_name": chunk_name, "reason": "chunk_csv missing"}
        chunk_csv = Path(str(chunk_csv_value).strip())
        assert chunk_csv.exists(), {"chunk_name": chunk_name, "missing_chunk_csv": str(chunk_csv)}
        chunk_base_df = pd.read_csv(chunk_csv)
        assert not chunk_base_df.empty, {"chunk_name": chunk_name, "reason": "empty chunk csv"}
        assert "record_index" in chunk_base_df.columns, {"chunk_name": chunk_name, "reason": "record_index missing in chunk csv"}

        anchor_cols = [c for c in anchor_full_df.columns if c not in chunk_base_df.columns or c == "record_index"]
        chunk_df = chunk_base_df.merge(
            anchor_full_df[anchor_cols].copy(),
            on="record_index",
            how="left",
            validate="many_to_one",
        )

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

    existing_anchor_cols = [c for c in required_anchor_cols if c in chunk_df.columns]
    if set(required_anchor_cols).issubset(set(chunk_df.columns)):
        anchor_df = chunk_df.copy()
    else:
        missing_join_cols = [c for c in required_anchor_cols if c not in chunk_df.columns]
        anchor_df = chunk_df.merge(
            anchor_full_df[["record_index", *[c for c in missing_join_cols if c != "record_index"]]].copy(),
            on="record_index",
            how="left",
            validate="many_to_one",
        )
    assert not anchor_df[[c for c in required_anchor_cols[1:] if c in anchor_df.columns]].isnull().any().any(), {
        "chunk_name": chunk_name,
        "reason": "full anchor join failed",
        "missing_columns": [c for c in required_anchor_cols if c not in anchor_df.columns],
    }
    assert set(required_anchor_cols).issubset(set(anchor_df.columns)), {
        "chunk_name": chunk_name,
        "reason": "required anchor columns missing after normalization",
        "missing_columns": [c for c in required_anchor_cols if c not in anchor_df.columns],
    }

    pred = to_4x4_batch(np.load(pred_path))
    n = min(len(anchor_df), pred.shape[0])
    if n <= 1:
        continue
    pred = pred[:n]
    anchor_df = anchor_df.iloc[:n].copy().reset_index(drop=True)

    local_rows = local_c2w_list(pred)
    global_rows = build_anchor_c2w_list(anchor_df)

    baseline_T, baseline_align = estimate_pose_aware_similarity(
        local_rows,
        global_rows,
        estimate_scale=True,
        scale_min=TRANSFORM_SCALE_MIN,
        scale_max=TRANSFORM_SCALE_MAX,
        center_rmse_max=TRANSFORM_CENTER_RMSE_MAX,
        rotation_dir_max=TRANSFORM_ROT_DIR_MAX,
    )
    baseline_transformed = transform_c2w_list(local_rows, baseline_T)
    baseline_candidate, baseline_residual_df = summarize_candidate(
        batch_name=batch_name,
        chunk_name=chunk_name,
        route_label=ROUTE_ARCORE,
        route_source="anchor_full_sequence",
        route_overlap_record_count=int(n),
        overlap_record_indices=anchor_df["record_index"].astype(int).tolist(),
        transformed_rows=baseline_transformed,
        anchor_df=anchor_df,
        align_diag=baseline_align,
    )
    candidate_rows.append(baseline_candidate)
    residual_frames.append(baseline_residual_df)

    overlap_local_rows = []
    overlap_world_rows = []
    overlap_record_indices = []
    for idx, record_index in enumerate(anchor_df["record_index"].astype(int).tolist()):
        if record_index in route_world_pose_map:
            overlap_local_rows.append(local_rows[idx])
            overlap_world_rows.append(route_world_pose_map[record_index])
            overlap_record_indices.append(int(record_index))

    if overlap_world_rows:
        experimental_source = "predicted_overlap"
        experimental_overlap_record_count = len(overlap_world_rows)
        if len(overlap_world_rows) >= 2:
            experimental_T, experimental_align = estimate_pose_aware_similarity(
                overlap_local_rows,
                overlap_world_rows,
                estimate_scale=True,
                scale_min=TRANSFORM_SCALE_MIN,
                scale_max=TRANSFORM_SCALE_MAX,
                center_rmse_max=TRANSFORM_CENTER_RMSE_MAX,
                rotation_dir_max=TRANSFORM_ROT_DIR_MAX,
            )
        else:
            experimental_T = baseline_T.copy()
            experimental_align = dict(baseline_align)
            experimental_align["center_rmse"] = float(baseline_align["center_rmse"])
            experimental_align["rotation_dir_residual"] = float(baseline_align["rotation_dir_residual"])
            experimental_source = "predicted_overlap_seeded_single_record"
    else:
        experimental_source = "seed_from_arcore_baseline"
        experimental_overlap_record_count = 0
        experimental_T = baseline_T.copy()
        experimental_align = dict(baseline_align)

    experimental_transformed = transform_c2w_list(local_rows, experimental_T)
    experimental_candidate, experimental_residual_df = summarize_candidate(
        batch_name=batch_name,
        chunk_name=chunk_name,
        route_label=ROUTE_DA3,
        route_source=experimental_source,
        route_overlap_record_count=int(experimental_overlap_record_count),
        overlap_record_indices=overlap_record_indices,
        transformed_rows=experimental_transformed,
        anchor_df=anchor_df,
        align_diag=experimental_align,
    )
    candidate_rows.append(experimental_candidate)
    residual_frames.append(experimental_residual_df)

    candidates = [baseline_candidate, experimental_candidate]
    selected_candidate, fallback_used = pick_selected_candidate(candidates)
    selected_candidate = dict(selected_candidate)
    selected_candidate["preferred_route_label"] = PREFERRED_ROUTE_LABEL
    selected_candidate["fallback_used"] = bool(fallback_used)
    selected_candidate["fallback_reason"] = (
        None if not fallback_used else "preferred_route_hard_fail_or_unavailable"
    )

    selected_transformed = experimental_transformed if selected_candidate["route_label"] == ROUTE_DA3 else baseline_transformed
    selected_T = experimental_T if selected_candidate["route_label"] == ROUTE_DA3 else baseline_T
    selected_align = experimental_align if selected_candidate["route_label"] == ROUTE_DA3 else baseline_align
    for record_index, world_pose in zip(anchor_df["record_index"].astype(int).tolist(), selected_transformed):
        route_world_pose_map[int(record_index)] = world_pose

    graph_parent_chunk_name = previous_selected_chunk_name
    relative_transform = summarize_relative_transform(previous_selected_T, selected_T)
    selected_candidate["graph_parent_chunk_name"] = graph_parent_chunk_name
    selected_candidate["relative_scale"] = float(relative_transform["relative_scale"])
    selected_candidate["relative_translation_norm"] = float(relative_transform["relative_translation_norm"])
    selected_candidate["relative_rotation_deg"] = float(relative_transform["relative_rotation_deg"])
    if bool(selected_candidate["fallback_used"]):
        selected_candidate["fallback_reason"] = "preferred_route_warning_or_hard_fail"
    selected_rows.append(selected_candidate)
    graph_node_measurements[chunk_name] = {
        "batch_name": batch_name,
        "chunk_name": chunk_name,
        "local_rows": [m.copy() for m in local_rows],
        "anchor_df": anchor_df.copy(),
        "overlap_record_indices": [int(x) for x in overlap_record_indices],
        "route_source": str(selected_candidate["route_source"]),
    }

    graph_solution_row = {
        "batch_name": batch_name,
        "chunk_name": chunk_name,
        "graph_parent_chunk_name": graph_parent_chunk_name,
        "route_label": str(selected_candidate["route_label"]),
        "requested_route_label": str(selected_candidate["route_label"]),
        "preferred_route_label": PREFERRED_ROUTE_LABEL,
        "fallback_used": bool(fallback_used),
        "preferred_fallback_used": bool(str(selected_candidate["route_label"]) != PREFERRED_ROUTE_LABEL),
        "route_source": str(selected_candidate["route_source"]),
        "route_overlap_record_count": int(selected_candidate["route_overlap_record_count"]),
        "route_overlap_local_count": int(selected_candidate.get("route_overlap_local_count", 0)),
        "route_nonoverlap_local_count": int(selected_candidate.get("route_nonoverlap_local_count", 0)),
        "row_count": int(n),
        "local_extrinsic_mode": LOCAL_EXTRINSIC_MODE,
        "local_camera_basis": "perm_yxz_sign_ppn",
        "scale": float(selected_align["scale"]),
        "rotation_det": float(selected_align["rotation_det"]),
        "center_rmse": float(selected_align["center_rmse"]),
        "rotation_dir_residual": float(selected_align["rotation_dir_residual"]),
        "positive_similarity_ok": bool(selected_align["positive_similarity_ok"]),
        "scale_in_range_ok": bool(selected_align["scale_in_range_ok"]),
        "center_rmse_ok": bool(selected_align["center_rmse_ok"]),
        "rotation_dir_ok": bool(selected_align["rotation_dir_ok"]),
        "align_hard_fail": bool(selected_align["hard_fail"]),
        "residual_hard_fail": bool(selected_candidate["hard_fail"]),
        "hard_fail": bool(selected_candidate["hard_fail"]),
        "center_error_mean": float(selected_candidate["center_error_mean"]),
        "center_error_p95": float(selected_candidate["center_error_p95"]),
        "lens_error_deg_mean": float(selected_candidate["lens_error_deg_mean"]),
        "lens_error_deg_p95": float(selected_candidate["lens_error_deg_p95"]),
        "delta_center_error_max": float(selected_candidate["delta_center_error_max"]),
        "delta_lens_error_deg_max": float(selected_candidate["delta_lens_error_deg_max"]),
        "center_error_overlap_p95": selected_candidate.get("center_error_overlap_p95"),
        "center_error_nonoverlap_p95": selected_candidate.get("center_error_nonoverlap_p95"),
        "lens_error_deg_overlap_p95": selected_candidate.get("lens_error_deg_overlap_p95"),
        "lens_error_deg_nonoverlap_p95": selected_candidate.get("lens_error_deg_nonoverlap_p95"),
        "relative_scale": float(relative_transform["relative_scale"]),
        "relative_translation_norm": float(relative_transform["relative_translation_norm"]),
        "relative_rotation_deg": float(relative_transform["relative_rotation_deg"]),
    }
    for r in range(4):
        for c in range(4):
            graph_solution_row[f"t{r}{c}"] = float(selected_T[r, c])
    graph_solution_rows.append(graph_solution_row)
    graph_edge_rows.append({
        "batch_name": batch_name,
        "chunk_name": chunk_name,
        "graph_parent_chunk_name": graph_parent_chunk_name,
        "route_label": str(selected_candidate["route_label"]),
        "route_source": str(selected_candidate["route_source"]),
        "route_overlap_record_count": int(selected_candidate["route_overlap_record_count"]),
        "route_overlap_local_count": int(selected_candidate.get("route_overlap_local_count", 0)),
        "route_nonoverlap_local_count": int(selected_candidate.get("route_nonoverlap_local_count", 0)),
        "center_error_overlap_p95": selected_candidate.get("center_error_overlap_p95"),
        "center_error_nonoverlap_p95": selected_candidate.get("center_error_nonoverlap_p95"),
        "lens_error_deg_overlap_p95": selected_candidate.get("lens_error_deg_overlap_p95"),
        "lens_error_deg_nonoverlap_p95": selected_candidate.get("lens_error_deg_nonoverlap_p95"),
        "relative_scale": float(relative_transform["relative_scale"]),
        "relative_translation_norm": float(relative_transform["relative_translation_norm"]),
        "relative_rotation_deg": float(relative_transform["relative_rotation_deg"]),
        "center_rmse": float(selected_align["center_rmse"]),
        "rotation_dir_residual": float(selected_align["rotation_dir_residual"]),
        "fallback_used": bool(fallback_used),
        "preferred_fallback_used": bool(str(selected_candidate["route_label"]) != PREFERRED_ROUTE_LABEL),
        "hard_fail": bool(selected_candidate["hard_fail"]),
    })
    previous_selected_chunk_name = chunk_name
    previous_selected_T = selected_T.copy()

candidate_df = pd.DataFrame(candidate_rows)
route_compare_csv = merged_dir / "premerge_route_compare_arc.csv"
candidate_df.to_csv(route_compare_csv, index=False, encoding="utf-8")

residual_df = pd.concat(residual_frames, ignore_index=True) if residual_frames else pd.DataFrame()
residual_csv = chunk_manifest_dir / "pred_vs_anchor_pose_residual.csv"
residual_df.to_csv(residual_csv, index=False, encoding="utf-8")

missing_pred_df = pd.DataFrame(missing_pred_chunks)
missing_pred_csv = chunk_manifest_dir / "pred_vs_anchor_pose_residual_missing_pred.csv"
missing_pred_df.to_csv(missing_pred_csv, index=False, encoding="utf-8")



def sim3_matrix_to_params(T: np.ndarray, allow_scale: bool = True) -> np.ndarray:
    T = np.asarray(T, dtype=np.float64)
    A = T[:3, :3]
    det = float(np.linalg.det(A))
    scale = np.cbrt(abs(det)) if abs(det) > 1e-12 else 1.0
    scale = max(scale, 1e-8)
    Rm = A / scale
    U, _, Vt = np.linalg.svd(Rm)
    Rm = U @ Vt
    if np.linalg.det(Rm) < 0:
        U[:, -1] *= -1.0
        Rm = U @ Vt
    rotvec = SciRot.from_matrix(Rm).as_rotvec()
    t = T[:3, 3].astype(np.float64)
    log_scale = math.log(scale) if allow_scale else 0.0
    return np.concatenate([rotvec, t, np.array([log_scale], dtype=np.float64)])


def params_to_sim3_matrix(params: np.ndarray, allow_scale: bool = True) -> np.ndarray:
    params = np.asarray(params, dtype=np.float64)
    rot = SciRot.from_rotvec(params[:3]).as_matrix()
    t = params[3:6]
    scale = math.exp(float(params[6])) if allow_scale else 1.0
    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = scale * rot
    T[:3, 3] = t
    return T


def invert_sim3(T: np.ndarray) -> np.ndarray:
    T = np.asarray(T, dtype=np.float64)
    A = T[:3, :3]
    t = T[:3, 3]
    A_inv = np.linalg.inv(A)
    out = np.eye(4, dtype=np.float64)
    out[:3, :3] = A_inv
    out[:3, 3] = -(A_inv @ t)
    return out


def compose_sim3(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return np.asarray(A, dtype=np.float64) @ np.asarray(B, dtype=np.float64)


def edge_transform_from_row(row: pd.Series) -> np.ndarray:
    T = np.eye(4, dtype=np.float64)
    for r in range(4):
        for c in range(4):
            key = f"t{r}{c}"
            T[r, c] = float(row[key])
    return T


def sim3_residual_vec(pred: np.ndarray, target: np.ndarray, allow_scale: bool = True) -> np.ndarray:
    pred_p = sim3_matrix_to_params(pred, allow_scale=allow_scale)
    tgt_p = sim3_matrix_to_params(target, allow_scale=allow_scale)
    return pred_p - tgt_p


def refine_graph_solution(
    initial_solution_df: pd.DataFrame,
    edge_df: pd.DataFrame,
    node_measurements: dict[str, dict],
    allow_scale: bool = True,
):
    if len(initial_solution_df) <= 1:
        summary = {
            "optimization_enabled": True,
            "allow_scale": bool(allow_scale),
            "status": "skipped_single_chunk",
            "node_count": int(len(initial_solution_df)),
            "edge_count": int(len(edge_df)),
        }
        return initial_solution_df.copy(), edge_df.copy(), summary

    node_names = initial_solution_df["chunk_name"].astype(str).tolist()
    root_name = str(node_names[0])
    init_map = {str(r.chunk_name): edge_transform_from_row(pd.Series(r._asdict())) for r in initial_solution_df.itertuples(index=False)}
    name_to_idx = {name: i for i, name in enumerate(node_names)}
    opt_names = [name for name in node_names if name != root_name]

    x0 = []
    for name in opt_names:
        x0.append(sim3_matrix_to_params(init_map[name], allow_scale=allow_scale))
    x0 = np.concatenate(x0, axis=0) if x0 else np.zeros((0,), dtype=np.float64)

    def unpack(x: np.ndarray):
        out = {root_name: init_map[root_name].copy()}
        offset = 0
        for name in opt_names:
            out[name] = params_to_sim3_matrix(x[offset:offset+7], allow_scale=allow_scale)
            offset += 7
        return out

    edge_records = []
    for row in edge_df.itertuples(index=False):
        child = str(row.chunk_name)
        parent = str(row.graph_parent_chunk_name) if pd.notna(row.graph_parent_chunk_name) else None
        if not parent or parent == 'nan':
            continue
        T_child = init_map[child]
        T_parent = init_map[parent]
        T_rel = compose_sim3(invert_sim3(T_parent), T_child)
        overlap = float(getattr(row, 'route_overlap_local_count', 0) or 0)
        quality = 1.0 / max(float(getattr(row, 'center_rmse', 0.02) or 0.02), 1e-3)
        weight = max(1.0, min(10.0, overlap + 1.0)) * max(0.5, min(8.0, quality * 0.1))
        edge_records.append((parent, child, T_rel, weight))

    def residual_fn(x: np.ndarray) -> np.ndarray:
        T_map = unpack(x)
        res = []
        for parent, child, T_rel, weight in edge_records:
            pred_rel = compose_sim3(invert_sim3(T_map[parent]), T_map[child])
            rv = sim3_residual_vec(pred_rel, T_rel, allow_scale=allow_scale)
            rv[:3] *= GRAPH_EDGE_ROTATION_WEIGHT
            rv[3:6] *= GRAPH_EDGE_TRANSLATION_WEIGHT
            rv[6] *= GRAPH_EDGE_SCALE_WEIGHT if allow_scale else 0.0
            res.append(math.sqrt(weight) * rv)
        for name in opt_names:
            prior = sim3_residual_vec(T_map[name], init_map[name], allow_scale=allow_scale)
            prior[:3] *= GRAPH_ANCHOR_ROT_WEIGHT
            prior[3:6] *= GRAPH_ANCHOR_WEIGHT
            prior[6] *= GRAPH_ANCHOR_WEIGHT if allow_scale else 0.0
            res.append(GRAPH_PRIOR_WEIGHT * prior)
        for name in opt_names:
            measurement = node_measurements.get(name)
            if measurement is None:
                continue
            transformed_rows = transform_c2w_list(measurement["local_rows"], T_map[name])
            anchor_df = measurement["anchor_df"]
            overlap_index_set = {int(x) for x in measurement["overlap_record_indices"]}
            for idx, (world_pose, anchor_row) in enumerate(zip(transformed_rows, anchor_df.itertuples(index=False))):
                record_index = int(anchor_row.record_index)
                frame_weight = (
                    GRAPH_ANCHOR_OVERLAP_FRAME_WEIGHT
                    if record_index in overlap_index_set
                    else GRAPH_ANCHOR_NONOVERLAP_FRAME_WEIGHT
                )
                pred_center = np.asarray(world_pose[:3, 3], dtype=np.float64)
                anchor_center = np.array(
                    [float(anchor_row.cx_world), float(anchor_row.cy_world), float(anchor_row.cz_world)],
                    dtype=np.float64,
                )
                center_res = (pred_center - anchor_center) * (GRAPH_ANCHOR_FRAME_TRANSLATION_WEIGHT * frame_weight)
                res.append(center_res)

                pred_lens = lens_direction_from_c2w(world_pose).astype(np.float64)
                anchor_lens = normalize_vec(
                    np.array(
                        [float(anchor_row.anchor_lens_x), float(anchor_row.anchor_lens_y), float(anchor_row.anchor_lens_z)],
                        dtype=np.float64,
                    ),
                    np.array([0.0, 0.0, -1.0], dtype=np.float64),
                )
                lens_res = (pred_lens - anchor_lens) * (GRAPH_ANCHOR_FRAME_DIRECTION_WEIGHT * frame_weight)
                res.append(lens_res)
        if not res:
            return np.zeros((0,), dtype=np.float64)
        return np.concatenate(res, axis=0)

    lsq = least_squares(residual_fn, x0, loss='soft_l1', f_scale=1.0, max_nfev=GRAPH_OPT_MAX_NFEV)
    refined_map = unpack(lsq.x)

    refined_solution_df = initial_solution_df.copy()
    refined_solution_df['graph_optimization_enabled'] = True
    refined_solution_df['graph_optimization_allow_scale'] = bool(allow_scale)
    refined_solution_df['graph_optimization_cost'] = float(lsq.cost)
    refined_solution_df['graph_optimization_success'] = bool(lsq.success)
    refined_solution_df['graph_optimization_status'] = int(lsq.status)
    refined_solution_df['graph_optimization_nfev'] = int(lsq.nfev)
    refined_solution_df['graph_optimization_optimality'] = float(lsq.optimality)

    for idx, row in refined_solution_df.iterrows():
        T = refined_map[str(row['chunk_name'])]
        for r in range(4):
            for c in range(4):
                refined_solution_df.at[idx, f't{r}{c}'] = float(T[r, c])

    refined_edges_df = edge_df.copy()
    opt_edge_residuals = []
    for idx, row in refined_edges_df.iterrows():
        child = str(row['chunk_name'])
        parent = row['graph_parent_chunk_name']
        if pd.isna(parent):
            refined_edges_df.at[idx, 'graph_opt_edge_translation_residual'] = 0.0
            refined_edges_df.at[idx, 'graph_opt_edge_rotation_residual_deg'] = 0.0
            refined_edges_df.at[idx, 'graph_opt_edge_log_scale_residual'] = 0.0
            continue
        parent = str(parent)
        pred_rel = compose_sim3(invert_sim3(refined_map[parent]), refined_map[child])
        init_rel = compose_sim3(invert_sim3(init_map[parent]), init_map[child])
        rv = sim3_residual_vec(pred_rel, init_rel, allow_scale=allow_scale)
        trans_res = float(np.linalg.norm(rv[3:6]))
        rot_res_deg = float(np.degrees(np.linalg.norm(rv[:3])))
        scale_res = float(abs(rv[6])) if allow_scale else 0.0
        refined_edges_df.at[idx, 'graph_opt_edge_translation_residual'] = trans_res
        refined_edges_df.at[idx, 'graph_opt_edge_rotation_residual_deg'] = rot_res_deg
        refined_edges_df.at[idx, 'graph_opt_edge_log_scale_residual'] = scale_res
        opt_edge_residuals.append((trans_res, rot_res_deg, scale_res))

    summary = {
        "optimization_enabled": True,
        "allow_scale": bool(allow_scale),
        "status": "ok" if bool(lsq.success) else "warning",
        "success": bool(lsq.success),
        "solver_status": int(lsq.status),
        "message": str(lsq.message),
        "cost": float(lsq.cost),
        "optimality": float(lsq.optimality),
        "nfev": int(lsq.nfev),
        "node_count": int(len(initial_solution_df)),
        "edge_count": int(len(edge_records)),
    }
    if opt_edge_residuals:
        trans_vals = np.asarray([x[0] for x in opt_edge_residuals], dtype=float)
        rot_vals = np.asarray([x[1] for x in opt_edge_residuals], dtype=float)
        scale_vals = np.asarray([x[2] for x in opt_edge_residuals], dtype=float)
        summary.update({
            "edge_translation_residual_mean": float(trans_vals.mean()),
            "edge_translation_residual_p95": float(np.quantile(trans_vals, 0.95)),
            "edge_rotation_residual_deg_mean": float(rot_vals.mean()),
            "edge_rotation_residual_deg_p95": float(np.quantile(rot_vals, 0.95)),
            "edge_log_scale_residual_mean": float(scale_vals.mean()),
            "edge_log_scale_residual_p95": float(np.quantile(scale_vals, 0.95)),
        })
    return refined_solution_df, refined_edges_df, summary


def recompute_solution_metrics(solution_df: pd.DataFrame, node_measurements: dict[str, dict]) -> pd.DataFrame:
    if solution_df.empty:
        return solution_df.copy()
    refreshed_rows = []
    for row in solution_df.itertuples(index=False):
        chunk_name = str(row.chunk_name)
        measurement = node_measurements.get(chunk_name)
        if measurement is None:
            refreshed_rows.append(pd.Series(row._asdict()).to_dict())
            continue
        T = edge_transform_from_row(pd.Series(row._asdict()))
        transformed_rows = transform_c2w_list(measurement["local_rows"], T)
        align_diag = {
            "scale": float(getattr(row, "scale")),
            "rotation_det": float(getattr(row, "rotation_det")),
            "center_rmse": float(getattr(row, "center_rmse")),
            "rotation_dir_residual": float(getattr(row, "rotation_dir_residual")),
            "positive_similarity_ok": bool(getattr(row, "positive_similarity_ok")),
            "scale_in_range_ok": bool(getattr(row, "scale_in_range_ok")),
            "center_rmse_ok": bool(getattr(row, "center_rmse_ok")),
            "rotation_dir_ok": bool(getattr(row, "rotation_dir_ok")),
            "hard_fail": bool(getattr(row, "align_hard_fail", getattr(row, "hard_fail"))),
        }
        refreshed_candidate, _ = summarize_candidate(
            batch_name=str(getattr(row, "batch_name")),
            chunk_name=chunk_name,
            route_label=str(getattr(row, "route_label")),
            route_source=str(getattr(row, "route_source")),
            route_overlap_record_count=int(getattr(row, "route_overlap_record_count")),
            overlap_record_indices=measurement["overlap_record_indices"],
            transformed_rows=transformed_rows,
            anchor_df=measurement["anchor_df"],
            align_diag=align_diag,
        )
        row_dict = pd.Series(row._asdict()).to_dict()
        row_dict.update(refreshed_candidate)
        row_dict["hard_fail"] = bool(row_dict["align_hard_fail"] or row_dict["anchor_warning"])
        refreshed_candidate = row_dict
        refreshed_rows.append(refreshed_candidate)
    return pd.DataFrame(refreshed_rows)

graph_solution_df = pd.DataFrame(graph_solution_rows)
graph_edges_df = pd.DataFrame(graph_edge_rows)

graph_optimization_summary = {
    "optimization_enabled": False,
    "status": "not_run",
    "allow_scale": bool(SIM3_GRAPH_OPTIMIZATION),
}
if len(graph_solution_df):
    graph_solution_df, graph_edges_df, graph_optimization_summary = refine_graph_solution(
        graph_solution_df,
        graph_edges_df,
        graph_node_measurements,
        allow_scale=bool(SIM3_GRAPH_OPTIMIZATION),
    )
    graph_solution_df = recompute_solution_metrics(graph_solution_df, graph_node_measurements)

validation_df = graph_solution_df.copy() if len(graph_solution_df) else pd.DataFrame(selected_rows)
validation_csv = merged_dir / "premerge_pose_validation.csv"
validation_df.to_csv(validation_csv, index=False, encoding="utf-8")

gate_csv = chunk_manifest_dir / "premerge_pose_gate.csv"
validation_df.to_csv(gate_csv, index=False, encoding="utf-8")

graph_solution_csv = merged_dir / "prepose_chunk_graph_solution_arc.csv"
graph_solution_df.to_csv(graph_solution_csv, index=False, encoding="utf-8")

graph_edges_csv = merged_dir / "prepose_chunk_graph_edges_arc.csv"
graph_edges_df.to_csv(graph_edges_csv, index=False, encoding="utf-8")

validation_json = merged_dir / "premerge_pose_validation.json"
route_compare_json = merged_dir / "premerge_route_compare_summary.json"
graph_summary_json = merged_dir / "prepose_chunk_graph_summary.json"
graph_opt_summary_json = merged_dir / "prepose_graph_optimization_summary.json"
hard_fail_df = validation_df[validation_df["hard_fail"]].copy() if len(validation_df) else validation_df.copy()
anchor_warning_df = validation_df[validation_df["anchor_warning"].fillna(False).astype(bool)].copy() if len(validation_df) else validation_df.copy()

if len(validation_df) == 0:
    status = "not_run"
elif len(missing_pred_df) > 0:
    status = "partial"
elif len(hard_fail_df) > 0:
    status = "fail"
elif len(anchor_warning_df) > 0:
    status = "warning"
else:
    status = "ok"

route_counts = (
    validation_df.groupby("route_label", as_index=False).size().rename(columns={"size": "chunk_count"}).to_dict(orient="records")
    if len(validation_df)
    else []
)
fallback_count = int(validation_df["fallback_used"].fillna(False).astype(bool).sum()) if len(validation_df) else 0
route_compare_summary = {
    "status": status,
    "route": "continuous-gs-v06-chunk18-overlap6-adopt12-route-compare",
    "candidate_row_count": int(len(candidate_df)),
    "selected_chunk_count": int(len(validation_df)),
    "selected_route_counts": route_counts,
    "fallback_count": fallback_count,
    "preferred_route_label": PREFERRED_ROUTE_LABEL,
    "route_compare_csv": str(route_compare_csv),
    "prepose_chunk_graph_solution_csv": str(graph_solution_csv),
    "prepose_chunk_graph_edges_csv": str(graph_edges_csv),
    "selected_chunks": validation_df[
        [
            "chunk_name",
            "route_label",
            "route_source",
            "fallback_used",
            "route_overlap_record_count",
            "route_overlap_local_count",
            "route_nonoverlap_local_count",
            "center_error_p95",
            "lens_error_deg_p95",
            "center_error_overlap_p95",
            "center_error_nonoverlap_p95",
            "lens_error_deg_overlap_p95",
            "lens_error_deg_nonoverlap_p95",
            "relative_rotation_deg",
            "relative_translation_norm",
            "relative_scale",
            "center_rmse",
            "rotation_dir_residual",
        ]
    ].to_dict(orient="records") if len(validation_df) else [],
}

graph_summary = {
    "status": status,
    "graph_optimization": graph_optimization_summary,
    "route": "continuous-gs-v06-chunk18-overlap6-adopt12-prepose-graph-build",
    "selected_chunk_count": int(len(graph_solution_df)),
    "preferred_route_label": PREFERRED_ROUTE_LABEL,
    "preferred_fallback_used_count": int(graph_solution_df["preferred_fallback_used"].fillna(False).astype(bool).sum()) if len(graph_solution_df) else 0,
    "graph_solution_csv": str(graph_solution_csv),
    "graph_edges_csv": str(graph_edges_csv),
    "selected_chunks": graph_solution_df[
        [
            "chunk_name",
            "graph_parent_chunk_name",
            "route_label",
            "route_source",
            "fallback_used",
            "preferred_fallback_used",
            "route_overlap_local_count",
            "route_nonoverlap_local_count",
            "center_error_overlap_p95",
            "center_error_nonoverlap_p95",
            "lens_error_deg_overlap_p95",
            "lens_error_deg_nonoverlap_p95",
            "relative_rotation_deg",
            "relative_translation_norm",
            "relative_scale",
            "center_rmse",
            "rotation_dir_residual",
        ]
    ].to_dict(orient="records") if len(graph_solution_df) else [],
}

summary = {
    "status": status,
    "route": "continuous-gs-v06-chunk18-overlap6-adopt12-premerge-pose-gate",
    "residual_row_count": int(len(residual_df)),
    "missing_pred_chunk_count": int(len(missing_pred_df)),
    "gate_chunk_count": int(len(validation_df)),
    "residual_csv": str(residual_csv),
    "missing_pred_csv": str(missing_pred_csv),
    "gate_csv": str(gate_csv),
    "validation_csv": str(validation_csv),
    "route_compare_csv": str(route_compare_csv),
    "route_compare_json": str(route_compare_json),
    "prepose_chunk_graph_solution_csv": str(graph_solution_csv),
    "prepose_chunk_graph_edges_csv": str(graph_edges_csv),
    "prepose_chunk_graph_summary_json": str(graph_summary_json),
    "prepose_graph_optimization_summary_json": str(graph_opt_summary_json),
    "preferred_route_label": PREFERRED_ROUTE_LABEL,
    "thresholds": {
        "center_error_p95_max": PREMERGE_CENTER_ERROR_P95_MAX,
        "lens_error_deg_p95_max": PREMERGE_LENS_ERROR_DEG_P95_MAX,
        "delta_center_error_max": PREMERGE_DELTA_CENTER_ERROR_MAX,
        "delta_lens_error_deg_max": PREMERGE_DELTA_LENS_ERROR_DEG_MAX,
        "transform_scale_min": TRANSFORM_SCALE_MIN,
        "transform_scale_max": TRANSFORM_SCALE_MAX,
        "transform_center_rmse_max": TRANSFORM_CENTER_RMSE_MAX,
        "transform_rotation_dir_residual_max": TRANSFORM_ROT_DIR_MAX,
    },
    "tested_chunk_count": int(len(validation_df)),
    "hard_fail_count": int(len(hard_fail_df)),
    "anchor_warning_count": int(len(anchor_warning_df)),
    "fallback_count": fallback_count,
    "selected_route_counts": route_counts,
    "failed_chunks": hard_fail_df[
        [
            "chunk_name",
            "route_label",
            "center_error_p95",
            "lens_error_deg_p95",
            "delta_center_error_max",
            "delta_lens_error_deg_max",
            "center_rmse",
            "rotation_dir_residual",
        ]
    ].to_dict(orient="records") if len(hard_fail_df) else [],
    "anchor_warning_chunks": validation_df[
        [
            "chunk_name",
            "route_label",
            "route_source",
            "center_error_p95",
            "lens_error_deg_p95",
            "delta_center_error_max",
            "delta_lens_error_deg_max",
        ]
    ].loc[validation_df["anchor_warning"].fillna(False).astype(bool)].to_dict(orient="records") if len(validation_df) else [],
}
if len(validation_df):
    summary["center_error_mean"] = float(validation_df["center_error_mean"].mean())
    summary["center_error_p95"] = float(validation_df["center_error_p95"].quantile(0.95))
    summary["lens_error_deg_mean"] = float(validation_df["lens_error_deg_mean"].mean())
    summary["lens_error_deg_p95"] = float(validation_df["lens_error_deg_p95"].quantile(0.95))
    summary["transform_scale_mean"] = float(validation_df["scale"].mean())
    summary["transform_center_rmse_mean"] = float(validation_df["center_rmse"].mean())
    summary["transform_rotation_dir_residual_mean"] = float(validation_df["rotation_dir_residual"].mean())
    summary["selected_chunks"] = validation_df[
        [
            "chunk_name",
            "route_label",
            "route_source",
            "fallback_used",
            "route_overlap_record_count",
            "route_overlap_local_count",
            "route_nonoverlap_local_count",
            "center_error_p95",
            "lens_error_deg_p95",
            "center_error_overlap_p95",
            "center_error_nonoverlap_p95",
            "lens_error_deg_overlap_p95",
            "lens_error_deg_nonoverlap_p95",
            "relative_rotation_deg",
            "relative_translation_norm",
            "relative_scale",
            "center_rmse",
            "rotation_dir_residual",
        ]
    ].to_dict(orient="records")

save_json(route_compare_json, route_compare_summary)
save_json(graph_summary_json, graph_summary)
save_json(graph_opt_summary_json, graph_optimization_summary)
save_json(validation_json, summary)
save_json(final_outputs_diagnostics_dir / "premerge_route_compare_summary.json", route_compare_summary)
save_json(final_outputs_diagnostics_dir / "prepose_chunk_graph_summary.json", graph_summary)
save_json(final_outputs_diagnostics_dir / "prepose_graph_optimization_summary.json", graph_optimization_summary)
save_json(final_outputs_diagnostics_dir / "premerge_pose_gate_summary.json", summary)
save_json(final_outputs_diagnostics_dir / "batch_residual_summary.json", summary)
save_json(final_outputs_diagnostics_dir / "premerge_pose_validation.json", summary)

print(json.dumps(summary, indent=2, ensure_ascii=False))
if len(validation_df):
    display(validation_df)
if len(candidate_df):
    display(candidate_df)
if len(missing_pred_df):
    display(missing_pred_df.head())
display_stage_summary(
    "10-1",
    "prepose graph build and gate",
    inputs=[
        {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
        {"item": "camera_anchor_full_arc", "path": str(camera_anchor_full_path)},
    ],
    outputs=[
        {"item": "pred_vs_anchor_pose_residual", "path": str(residual_csv)},
        {"item": "pred_vs_anchor_pose_residual_missing_pred", "path": str(missing_pred_csv)},
        {"item": "premerge_pose_gate", "path": str(gate_csv)},
        {"item": "premerge_route_compare_summary", "path": str(route_compare_json)},
        {"item": "prepose_chunk_graph_solution", "path": str(graph_solution_csv)},
        {"item": "prepose_chunk_graph_edges", "path": str(graph_edges_csv)},
        {"item": "prepose_chunk_graph_summary", "path": str(graph_summary_json)},
        {"item": "prepose_graph_optimization_summary", "path": str(graph_opt_summary_json)},
        {"item": "premerge_pose_gate_summary", "path": str(final_outputs_diagnostics_dir / "premerge_pose_gate_summary.json")},
        {"item": "premerge_pose_validation", "path": str(validation_json)},
        {"item": "batch_residual_summary", "path": str(final_outputs_diagnostics_dir / "batch_residual_summary.json")},
    ],
    notes=[
        {"item": "status", "value": status},
        {"item": "preferred_route_label", "value": PREFERRED_ROUTE_LABEL},
        {"item": "missing_pred_chunk_count", "value": int(len(missing_pred_df))},
        {"item": "hard_fail_count", "value": int(len(hard_fail_df))},
        {"item": "anchor_warning_count", "value": int(len(anchor_warning_df))},
        {"item": "fallback_count", "value": fallback_count},
    ],
)

# TODO(from pre-#7 deferred anchor-derived features):
# - #9-2 で行っていた full_anchor_pose_diag_arc.csv の record manifest 結合
# - #9-4 で行っていた camera_anchor_full_arc.csv -> chunk_xxx_sequence_anchor.csv / chunk_sequence_anchor_index.csv 生成
# - #9-5 で行っていた sequence-anchor 派生列 / adjacent edge 派生列の付与
# - #10-2 で行っていた adjacent edge validation
# - #10-3 で行っていた full_anchor_pose_qc_arc.csv を用いた anchor QC summary
# - #11-4 で行っていた anchor pose / anchor QC を含む preflight 拡張
