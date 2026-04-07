#13-2

from pathlib import Path
import itertools
import json

import numpy as np
import pandas as pd

ctx = load_ctx()

probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
merged_dir = Path(ctx.get("merged_dir", str(pipeline_root / "merged")))
merged_dir.mkdir(parents=True, exist_ok=True)

final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_diagnostics_dir.mkdir(parents=True, exist_ok=True)

batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
premerge_pose_validation_path = merged_dir / "premerge_pose_validation.json"

assert batch_execution_items_path.exists(), batch_execution_items_path
assert premerge_pose_validation_path.exists(), premerge_pose_validation_path

items_df = pd.read_csv(batch_execution_items_path)
premerge_pose_validation = json.loads(premerge_pose_validation_path.read_text(encoding="utf-8"))
failed_chunks = premerge_pose_validation.get("failed_chunks", [])
failed_chunk_names = [str(row["chunk_name"]) for row in failed_chunks]


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


def lens_from_yaw_pitch_deg(yaw_deg: np.ndarray, pitch_deg: np.ndarray) -> np.ndarray:
    yaw = np.deg2rad(yaw_deg.astype(float))
    pitch = np.deg2rad(pitch_deg.astype(float))
    fx = np.sin(yaw) * np.cos(pitch)
    fy = -np.sin(pitch)
    fz = np.cos(yaw) * np.cos(pitch)
    return normalize_rows(np.stack([fx, fy, fz], axis=1))


def resolve_cols(df: pd.DataFrame, candidates: list[tuple[str, str, str]], kind: str) -> tuple[str, str, str]:
    cols = next((c for c in candidates if all(name in df.columns for name in c)), None)
    assert cols is not None, {"reason": f"{kind} cols not found", "available_columns": df.columns.tolist()}
    return cols


def rotate_about_axis(vec: np.ndarray, axis: np.ndarray, angle_rad: float) -> np.ndarray:
    axis = np.asarray(axis, dtype=np.float64)
    axis = axis / max(float(np.linalg.norm(axis)), 1e-12)
    vec = np.asarray(vec, dtype=np.float64)
    c = float(np.cos(angle_rad))
    s = float(np.sin(angle_rad))
    return vec * c + np.cross(axis, vec) * s + axis * np.dot(axis, vec) * (1.0 - c)


def build_anchor_c2w_list(anchor_df: pd.DataFrame) -> list[np.ndarray]:
    center_cols = resolve_cols(
        anchor_df,
        [("cam_cx", "cam_cy", "cam_cz"), ("cx_world", "cy_world", "cz_world"), ("tx", "ty", "tz")],
        "center",
    )

    centers = anchor_df[list(center_cols)].to_numpy(dtype=np.float32)
    lens_cols = next((
        c for c in [
            ("anchor_lens_x", "anchor_lens_y", "anchor_lens_z"),
            ("lens_x", "lens_y", "lens_z"),
            ("forward_x", "forward_y", "forward_z"),
        ] if all(name in anchor_df.columns for name in c)
    ), None)
    up_cols = next((
        c for c in [
            ("anchor_up_x", "anchor_up_y", "anchor_up_z"),
            ("up_x", "up_y", "up_z"),
        ] if all(name in anchor_df.columns for name in c)
    ), None)
    ypr_cols = next((
        c for c in [
            ("yaw_deg_record", "pitch_deg_record", "roll_deg_record"),
            ("yaw_deg", "pitch_deg", "roll_deg"),
        ] if all(name in anchor_df.columns for name in c)
    ), None)

    if lens_cols is not None:
        lens = normalize_rows(anchor_df[list(lens_cols)].to_numpy(dtype=np.float32)).astype(np.float32)
    else:
        assert ypr_cols is not None, {"reason": "lens cols not found", "available_columns": anchor_df.columns.tolist()}
        yaw_col, pitch_col, _ = ypr_cols
        lens = lens_from_yaw_pitch_deg(anchor_df[yaw_col].to_numpy(float), anchor_df[pitch_col].to_numpy(float)).astype(np.float32)

    if up_cols is not None:
        up = normalize_rows(anchor_df[list(up_cols)].to_numpy(dtype=np.float32)).astype(np.float32)
    else:
        assert ypr_cols is not None, {"reason": "up cols not found", "available_columns": anchor_df.columns.tolist()}
        _, _, roll_col = ypr_cols
        world_up = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        up_rows = []
        for lens_vec, roll_deg in zip(lens, anchor_df[roll_col].to_numpy(float)):
            z_col = -np.asarray(lens_vec, dtype=np.float64)
            x_seed = np.cross(-world_up, z_col)
            if float(np.linalg.norm(x_seed)) <= 1e-12:
                x_seed = np.array([1.0, 0.0, 0.0], dtype=np.float64)
            x_col = x_seed / max(float(np.linalg.norm(x_seed)), 1e-12)
            y_seed = np.cross(z_col, x_col)
            y_col = y_seed / max(float(np.linalg.norm(y_seed)), 1e-12)
            up_rows.append(rotate_about_axis(y_col, lens_vec, np.deg2rad(float(roll_deg))))
        up = normalize_rows(np.asarray(up_rows, dtype=np.float32)).astype(np.float32)

    mats = []
    for center, lens_vec, up_vec in zip(centers, lens, up):
        z_col = -lens_vec
        x_seed = np.cross(-up_vec, z_col)
        x_col = x_seed / max(float(np.linalg.norm(x_seed)), 1e-12)
        y_seed = np.cross(z_col, x_col)
        y_col = y_seed / max(float(np.linalg.norm(y_seed)), 1e-12)
        if float(np.dot(y_col, -up_vec)) < 0.0:
            x_col = -x_col
            y_col = -y_col
        M = np.eye(4, dtype=np.float32)
        M[:3, 0] = x_col.astype(np.float32)
        M[:3, 1] = y_col.astype(np.float32)
        M[:3, 2] = z_col.astype(np.float32)
        M[:3, 3] = center.astype(np.float32)
        mats.append(M)
    return mats


def basis_matrix(diag: tuple[int, int, int], signs: tuple[int, int, int]) -> np.ndarray:
    base = np.eye(4, dtype=np.float32)
    rot = np.zeros((3, 3), dtype=np.float32)
    for row_i, axis_i in enumerate(diag):
        rot[row_i, axis_i] = float(signs[row_i])
    base[:3, :3] = rot
    return base


def lens_direction_from_c2w(c2w: np.ndarray) -> np.ndarray:
    axis = -np.asarray(c2w[:3, 2], dtype=np.float64)
    return axis / max(float(np.linalg.norm(axis)), 1e-12)


def up_direction_from_c2w(c2w: np.ndarray) -> np.ndarray:
    axis = -np.asarray(c2w[:3, 1], dtype=np.float64)
    return axis / max(float(np.linalg.norm(axis)), 1e-12)


def local_c2w_candidates(pred_extrinsics: np.ndarray, extrinsic_mode: str, basis: np.ndarray) -> list[np.ndarray]:
    mats = []
    for ext in to_4x4_batch(pred_extrinsics):
        if extrinsic_mode == "w2c":
            c2w = np.linalg.inv(ext).astype(np.float32)
        elif extrinsic_mode == "c2w":
            c2w = ext.astype(np.float32)
        else:
            raise AssertionError({"unsupported_extrinsic_mode": extrinsic_mode})
        mats.append((c2w @ basis).astype(np.float32))
    return mats


def estimate_pose_aware_similarity(local_c2w_list: list[np.ndarray], global_c2w_list: list[np.ndarray]) -> tuple[np.ndarray, dict]:
    assert len(local_c2w_list) == len(global_c2w_list) >= 2

    src_dirs, dst_dirs, src_centers, dst_centers = [], [], [], []
    for local_c2w, global_c2w in zip(local_c2w_list, global_c2w_list):
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

    finite_dir_mask = np.isfinite(src_dirs).all(axis=1) & np.isfinite(dst_dirs).all(axis=1)
    finite_center_mask = np.isfinite(src_centers).all(axis=1) & np.isfinite(dst_centers).all(axis=1)
    if int(finite_dir_mask.sum()) < 4 or int(finite_center_mask.sum()) < 2:
        raise AssertionError({
            "reason": "insufficient_finite_pose_samples",
            "finite_dir_count": int(finite_dir_mask.sum()),
            "finite_center_count": int(finite_center_mask.sum()),
        })
    src_dirs = src_dirs[finite_dir_mask]
    dst_dirs = dst_dirs[finite_dir_mask]
    src_centers = src_centers[finite_center_mask]
    dst_centers = dst_centers[finite_center_mask]

    H = dst_dirs.T @ src_dirs
    try:
        U, _, Vt = np.linalg.svd(H)
    except np.linalg.LinAlgError as exc:
        raise AssertionError({
            "reason": "svd_did_not_converge",
            "matrix": H.tolist(),
            "finite_dir_count": int(len(src_dirs)),
            "finite_center_count": int(len(src_centers)),
            "detail": str(exc),
        }) from exc
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

    pred_centers = (scale * (R @ src_centers.T)).T + t
    center_error = np.linalg.norm(pred_centers - dst_centers, axis=1)
    pred_dirs = (R @ src_dirs.T).T
    lens_error_deg = angle_deg(pred_dirs[0::2], dst_dirs[0::2])

    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = scale * R
    T[:3, 3] = t
    diag = {
        "scale": float(scale),
        "rotation_det": float(np.linalg.det(R)),
        "center_rmse": float(np.sqrt(np.mean(np.sum((pred_centers - dst_centers) ** 2, axis=1)))),
        "rotation_dir_residual": float(np.mean(np.linalg.norm(pred_dirs - dst_dirs, axis=1))),
        "center_error_p95": float(np.quantile(center_error, 0.95)),
        "lens_error_deg_p95": float(np.quantile(lens_error_deg, 0.95)),
        "center_error_mean": float(np.mean(center_error)),
        "lens_error_deg_mean": float(np.mean(lens_error_deg)),
    }
    return T.astype(np.float32), diag


basis_candidates = {
    "identity": np.eye(4, dtype=np.float32),
    "perm_yxz_sign_ppn": basis_matrix((1, 0, 2), (1, 1, -1)),
    "perm_yxz_sign_ppp": basis_matrix((1, 0, 2), (1, 1, 1)),
    "perm_yxz_sign_pnp": basis_matrix((1, 0, 2), (1, -1, 1)),
    "perm_yxz_sign_pnn": basis_matrix((1, 0, 2), (1, -1, -1)),
    "identity_flip_z": basis_matrix((0, 1, 2), (1, 1, -1)),
}

candidate_rows = []
best_rows = []

for failed in failed_chunk_names:
    hit = items_df.loc[items_df["chunk_name"].astype(str) == failed].copy()
    assert not hit.empty, {"chunk_name": failed, "reason": "missing batch_execution_items row"}
    row = hit.iloc[0]
    anchor_csv = Path(row["chunk_sequence_anchor_csv"])
    batch_work_dir = Path(row["batch_work_dir"])
    pred_candidates = [
        batch_work_dir / failed / "pred_extrinsics.npy",
        pipeline_root / "chunk_runs" / failed / "pred_extrinsics.npy",
        batch_work_dir / f"{failed}_pred_extrinsics.npy",
    ]
    pred_path = next((p for p in pred_candidates if p.exists()), None)
    assert pred_path is not None, {"chunk_name": failed, "reason": "pred_extrinsics.npy not found"}

    anchor_df = pd.read_csv(anchor_csv)
    pred_extrinsics = to_4x4_batch(np.load(pred_path))
    n = min(len(anchor_df), pred_extrinsics.shape[0])
    assert n >= 2, {"chunk_name": failed, "reason": "insufficient rows for pose probe", "row_count": int(n)}
    anchor_df = anchor_df.iloc[:n].copy()
    pred_extrinsics = pred_extrinsics[:n]
    global_c2w_list = build_anchor_c2w_list(anchor_df)

    for extrinsic_mode, (basis_label, basis) in itertools.product(["w2c", "c2w"], basis_candidates.items()):
        local_c2w_list = local_c2w_candidates(pred_extrinsics, extrinsic_mode, basis)
        try:
            _, diag = estimate_pose_aware_similarity(local_c2w_list, global_c2w_list)
        except AssertionError as exc:
            diag = {
                "scale": None,
                "rotation_det": None,
                "center_rmse": float("inf"),
                "rotation_dir_residual": float("inf"),
                "center_error_p95": float("inf"),
                "lens_error_deg_p95": float("inf"),
                "center_error_mean": float("inf"),
                "lens_error_deg_mean": float("inf"),
                "probe_error": exc.args[0] if exc.args else "probe_failed",
            }
        candidate_rows.append({
            "chunk_name": failed,
            "extrinsic_mode": extrinsic_mode,
            "basis_label": basis_label,
            **diag,
        })

candidate_df = pd.DataFrame(candidate_rows).sort_values(
    ["chunk_name", "center_rmse", "center_error_p95", "rotation_dir_residual", "lens_error_deg_p95"],
    kind="stable",
).reset_index(drop=True)

if len(candidate_df):
    best_df = candidate_df.groupby("chunk_name", as_index=False, sort=True).first()
    best_rows = best_df.to_dict(orient="records")
else:
    best_df = pd.DataFrame()

probe_csv = merged_dir / "premerge_pose_probe_candidates.csv"
probe_json = merged_dir / "premerge_pose_probe_summary.json"
candidate_df.to_csv(probe_csv, index=False, encoding="utf-8")

summary = {
    "status": "ok" if len(best_df) else "not_run",
    "route": "continuous-gs-v06-chunk18-overlap6-adopt12-premerge-pose-probe",
    "failed_chunk_count": int(len(failed_chunk_names)),
    "candidate_row_count": int(len(candidate_df)),
    "probe_csv": str(probe_csv),
    "best_candidates": best_rows,
}
save_json(probe_json, summary)
save_json(final_outputs_diagnostics_dir / "premerge_pose_probe_summary.json", summary)

print(json.dumps(summary, indent=2, ensure_ascii=False))
if len(candidate_df):
    display(candidate_df)
display_stage_summary(
    "13-2",
    "pre-merge pose probe",
    inputs=[
        {"item": "premerge_pose_validation", "path": str(premerge_pose_validation_path)},
        {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
    ],
    outputs=[
        {"item": "premerge_pose_probe_candidates", "path": str(probe_csv)},
        {"item": "premerge_pose_probe_summary", "path": str(probe_json)},
    ],
    notes=[
        {"item": "failed_chunk_count", "value": int(len(failed_chunk_names))},
        {"item": "candidate_row_count", "value": int(len(candidate_df))},
    ],
)
