#6-2
from pathlib import Path
import json
import numpy as np


def load_json(path):
    p = Path(path)
    assert p.exists(), p
    return json.loads(p.read_text(encoding="utf-8"))


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


def estimate_pose_aware_similarity(
    local_c2w_rows: list[np.ndarray],
    global_c2w_rows: list[np.ndarray],
    estimate_scale: bool = True,
    scale_min: float = 0.8,
    scale_max: float = 1.3,
    center_rmse_max: float = 0.15,
    rotation_dir_max: float = 0.20,
) -> tuple[np.ndarray, dict]:
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

    if estimate_scale:
        denom = float(np.sum(src_rot ** 2))
        numer = float(np.sum(dst_c * src_rot))
        scale = numer / max(denom, 1e-12)
    else:
        scale = 1.0
    t = dst_mean - scale * (R @ src_mean)

    pred = (scale * (R @ src_centers.T)).T + t
    center_rmse = float(np.sqrt(np.mean(np.sum((pred - dst_centers) ** 2, axis=1))))
    rotation_dir_residual = float(np.mean(np.linalg.norm((R @ src_dirs.T).T - dst_dirs, axis=1)))

    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = scale * R
    T[:3, 3] = t
    diag = {
        "scale": float(scale),
        "rotation_det": float(np.linalg.det(R)),
        "center_rmse": center_rmse,
        "rotation_dir_residual": rotation_dir_residual,
        "positive_similarity_ok": bool(scale > 0.0),
        "scale_in_range_ok": bool(scale_min <= scale <= scale_max),
        "center_rmse_ok": bool(center_rmse <= center_rmse_max),
        "rotation_dir_ok": bool(rotation_dir_residual <= rotation_dir_max),
    }
    diag["hard_fail"] = bool(
        (scale <= 0.0)
        or (scale < scale_min)
        or (scale > scale_max)
        or (center_rmse > center_rmse_max)
        or (rotation_dir_residual > rotation_dir_max)
    )
    return T.astype(np.float32), diag


def transform_c2w_list(c2w_rows: list[np.ndarray], T: np.ndarray) -> list[np.ndarray]:
    out = []
    for c2w in c2w_rows:
        M = np.asarray(c2w, dtype=np.float64).copy()
        M[:3, :3] = T[:3, :3] @ M[:3, :3]
        M[:3, 3] = T[:3, :3] @ M[:3, 3] + T[:3, 3]
        out.append(M.astype(np.float32))
    return out
