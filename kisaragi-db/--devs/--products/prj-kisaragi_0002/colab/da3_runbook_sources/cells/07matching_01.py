#7-6
from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go

ctx = load_ctx()
config = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8"))

probe_root = Path(ctx["probe_root"])
persist_root = Path(ctx.get("persist_root", probe_root))
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
anchor_dir = persist_root / "01_anchor"
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
final_outputs_chunk_evidence_dir = Path(ctx["final_outputs_chunk_evidence_dir"])
final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])

matching_dir = anchor_dir / "07matching"
matching_dir.mkdir(parents=True, exist_ok=True)

LOCAL_EXTRINSIC_MODE = "c2w"
LOCAL_CAMERA_BASIS = np.eye(4, dtype=np.float32)
LOCAL_CAMERA_BASIS[:3, :3] = np.array([
    [0.0, 1.0, 0.0],
    [0.0, 0.0, -1.0],
    [1.0, 0.0, 0.0],
], dtype=np.float32)

TRANSFORM_SCALE_MIN = 0.8
TRANSFORM_SCALE_MAX = 1.3
TRANSFORM_CENTER_RMSE_MAX = 0.15
TRANSFORM_ROT_DIR_MAX = 0.20


def resolve_matching_chunk_names() -> tuple[str | None, str | None]:
    explicit_a = str(config.get("MATCHING_CHUNK_A_NAME", "")).strip()
    explicit_b = str(config.get("MATCHING_CHUNK_B_NAME", "")).strip()
    if explicit_a and explicit_b:
        return explicit_a, explicit_b

    chunk_index_path = chunk_manifest_dir / "chunk_index_all.csv"
    if not chunk_index_path.exists():
        return None, None
    chunk_index_df = pd.read_csv(chunk_index_path)
    valid_ids = set(chunk_index_df["chunk_id"].astype(int).tolist())
    ids_1based = config.get("MATCHING_CHUNK_IDS_1BASED") or config.get("TARGET_CHUNK_IDS_1BASED") or []
    selected_ids = [int(x) - 1 for x in ids_1based if int(x) >= 1]
    selected_ids = [x for x in selected_ids if x in valid_ids]
    if len(selected_ids) < 2:
        return None, None
    selected_df = chunk_index_df.loc[chunk_index_df["chunk_id"].astype(int).isin(selected_ids)].copy()
    selected_df = selected_df.sort_values("chunk_id", kind="stable").reset_index(drop=True)
    return str(selected_df.iloc[0]["chunk_name"]), str(selected_df.iloc[1]["chunk_name"])


def resolve_chunk_artifact(explicit_path: str, chunk_name: str | None, filename: str) -> Path | None:
    if explicit_path:
        p = Path(explicit_path)
        assert p.exists(), {"missing_explicit_path": str(p), "chunk_name": chunk_name, "filename": filename}
        return p
    if not chunk_name:
        return None

    candidates = [
        final_outputs_chunk_evidence_dir / chunk_name / filename,
        chunk_runs_dir / chunk_name / filename,
    ]
    candidates += [p for p in chunk_runs_dir.glob(f"batch_*/{chunk_name}/{filename}")]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


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


def c2w_list_from_extrinsics(pred_extrinsics: np.ndarray) -> list[np.ndarray]:
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


def estimate_pose_aware_similarity(local_c2w_rows: list[np.ndarray], global_c2w_rows: list[np.ndarray], estimate_scale: bool = True) -> tuple[np.ndarray, dict]:
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
        "scale_in_range_ok": bool(TRANSFORM_SCALE_MIN <= scale <= TRANSFORM_SCALE_MAX),
        "center_rmse_ok": bool(center_rmse <= TRANSFORM_CENTER_RMSE_MAX),
        "rotation_dir_ok": bool(rotation_dir_residual <= TRANSFORM_ROT_DIR_MAX),
    }
    diag["hard_fail"] = bool(
        (scale <= 0.0)
        or (scale < TRANSFORM_SCALE_MIN)
        or (scale > TRANSFORM_SCALE_MAX)
        or (center_rmse > TRANSFORM_CENTER_RMSE_MAX)
        or (rotation_dir_residual > TRANSFORM_ROT_DIR_MAX)
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


def pose_rows_to_frame_df(chunk_name: str, frames_df: pd.DataFrame, c2w_rows: list[np.ndarray], variant: str, overlap_records: set[int]) -> pd.DataFrame:
    rows = []
    for frame_row, c2w in zip(frames_df.itertuples(index=False), c2w_rows):
        record_index = int(frame_row.record_index)
        center = np.asarray(c2w[:3, 3], dtype=np.float64)
        lens = lens_direction_from_c2w(c2w)
        up = up_direction_from_c2w(c2w)
        rows.append({
            "chunk_name": chunk_name,
            "variant": variant,
            "record_index": record_index,
            "chunk_local_index": int(getattr(frame_row, "chunk_local_index", len(rows))),
            "is_overlap": bool(record_index in overlap_records),
            "cx": float(center[0]),
            "cy": float(center[1]),
            "cz": float(center[2]),
            "fx": float(lens[0]),
            "fy": float(lens[1]),
            "fz": float(lens[2]),
            "ux": float(up[0]),
            "uy": float(up[1]),
            "uz": float(up[2]),
        })
    return pd.DataFrame(rows)


def plot_pose_match(a_df: pd.DataFrame, b_df: pd.DataFrame, b_aligned_df: pd.DataFrame, out_path: Path):
    fig = plt.figure(figsize=(14, 6))
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    ax2 = fig.add_subplot(1, 2, 2, projection="3d")

    def draw(ax, lhs: pd.DataFrame, rhs: pd.DataFrame, title: str):
        ax.plot(lhs["cx"], lhs["cy"], lhs["cz"], color="tab:blue", label=f"{lhs['chunk_name'].iloc[0]} raw")
        ax.plot(rhs["cx"], rhs["cy"], rhs["cz"], color="tab:orange", label=f"{rhs['chunk_name'].iloc[0]} {'aligned' if 'aligned' in rhs['variant'].iloc[0] else 'raw'}")
        lhs_overlap = lhs[lhs["is_overlap"]]
        rhs_overlap = rhs[rhs["is_overlap"]]
        if len(lhs_overlap):
            ax.scatter(lhs_overlap["cx"], lhs_overlap["cy"], lhs_overlap["cz"], color="tab:cyan", s=24)
        if len(rhs_overlap):
            ax.scatter(rhs_overlap["cx"], rhs_overlap["cy"], rhs_overlap["cz"], color="tab:red", s=24)
        ax.set_title(title)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("z")
        ax.legend(loc="best")

    draw(ax1, a_df, b_df, "pre-align overlap trajectories")
    draw(ax2, a_df, b_aligned_df, "post-align overlap trajectories")
    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_pose_match_html(a_df: pd.DataFrame, b_df: pd.DataFrame, b_aligned_df: pd.DataFrame, out_path: Path):
    fig = go.Figure()

    def add_trace(df: pd.DataFrame, name: str, color: str, show_overlap: bool):
        fig.add_trace(
            go.Scatter3d(
                x=df["cx"],
                y=df["cy"],
                z=df["cz"],
                mode="lines+markers",
                name=name,
                marker={"size": 3, "color": color},
                line={"width": 5, "color": color},
            )
        )
        if show_overlap:
            overlap_df = df[df["is_overlap"]]
            if len(overlap_df):
                fig.add_trace(
                    go.Scatter3d(
                        x=overlap_df["cx"],
                        y=overlap_df["cy"],
                        z=overlap_df["cz"],
                        mode="markers",
                        name=f"{name} overlap",
                        marker={"size": 5, "color": color, "symbol": "diamond"},
                    )
                )

    add_trace(a_df, f"{a_df['chunk_name'].iloc[0]} raw", "#1f77b4", True)
    add_trace(b_df, f"{b_df['chunk_name'].iloc[0]} raw", "#ff7f0e", True)
    add_trace(b_aligned_df, f"{b_aligned_df['chunk_name'].iloc[0]} aligned", "#2ca02c", True)
    fig.update_layout(
        title="overlap trajectory matching",
        scene={
            "xaxis_title": "x",
            "yaxis_title": "y",
            "zaxis_title": "z",
            "aspectmode": "data",
        },
        legend={"orientation": "h"},
        margin={"l": 0, "r": 0, "t": 48, "b": 0},
    )
    fig.write_html(str(out_path), include_plotlyjs="cdn")


chunk_a_name, chunk_b_name = resolve_matching_chunk_names()
chunk_a_frames_path = resolve_chunk_artifact(str(config.get("MATCHING_CHUNK_A_INPUT_FRAMES_PATH", "")).strip(), chunk_a_name, "chunk_input_frames.csv")
chunk_a_pred_path = resolve_chunk_artifact(str(config.get("MATCHING_CHUNK_A_PRED_EXTRINSICS_PATH", "")).strip(), chunk_a_name, "pred_extrinsics.npy")
chunk_b_frames_path = resolve_chunk_artifact(str(config.get("MATCHING_CHUNK_B_INPUT_FRAMES_PATH", "")).strip(), chunk_b_name, "chunk_input_frames.csv")
chunk_b_pred_path = resolve_chunk_artifact(str(config.get("MATCHING_CHUNK_B_PRED_EXTRINSICS_PATH", "")).strip(), chunk_b_name, "pred_extrinsics.npy")

if not all([chunk_a_name, chunk_b_name, chunk_a_frames_path, chunk_a_pred_path, chunk_b_frames_path, chunk_b_pred_path]):
    summary = {
        "status": "skipped",
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-overlap-pose-matching",
        "reason": "matching_inputs_missing",
        "chunk_a_name": chunk_a_name,
        "chunk_b_name": chunk_b_name,
        "chunk_a_frames_path": str(chunk_a_frames_path) if chunk_a_frames_path else None,
        "chunk_a_pred_extrinsics_path": str(chunk_a_pred_path) if chunk_a_pred_path else None,
        "chunk_b_frames_path": str(chunk_b_frames_path) if chunk_b_frames_path else None,
        "chunk_b_pred_extrinsics_path": str(chunk_b_pred_path) if chunk_b_pred_path else None,
        "hint": "set MATCHING_CHUNK_A/B_* explicit paths or rerun after chunk artifacts exist",
    }
    summary_json = matching_dir / "chunk_overlap_pose_matching_summary.json"
    save_json(summary_json, summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    display_stage_summary(
        "7-6",
        "overlap pose matching",
        outputs=[
            {"item": "matching_summary", "path": str(summary_json)},
        ],
        notes=[
            {"item": "status", "value": summary["status"]},
            {"item": "reason", "value": summary["reason"]},
        ],
    )
else:
    chunk_a_frames_df = pd.read_csv(chunk_a_frames_path).sort_values("chunk_local_index", kind="stable").reset_index(drop=True)
    chunk_b_frames_df = pd.read_csv(chunk_b_frames_path).sort_values("chunk_local_index", kind="stable").reset_index(drop=True)
    chunk_a_pred = np.load(chunk_a_pred_path)
    chunk_b_pred = np.load(chunk_b_pred_path)

    assert chunk_a_pred.shape[0] == len(chunk_a_frames_df), {"chunk_name": chunk_a_name, "pred_len": int(chunk_a_pred.shape[0]), "frame_len": int(len(chunk_a_frames_df))}
    assert chunk_b_pred.shape[0] == len(chunk_b_frames_df), {"chunk_name": chunk_b_name, "pred_len": int(chunk_b_pred.shape[0]), "frame_len": int(len(chunk_b_frames_df))}

    overlap_records = sorted(set(chunk_a_frames_df["record_index"].astype(int)) & set(chunk_b_frames_df["record_index"].astype(int)))
    assert len(overlap_records) >= 2, {"chunk_a_name": chunk_a_name, "chunk_b_name": chunk_b_name, "overlap_record_count": len(overlap_records)}
    overlap_record_set = set(overlap_records)

    chunk_a_map = {int(row.record_index): idx for idx, row in enumerate(chunk_a_frames_df.itertuples(index=False))}
    chunk_b_map = {int(row.record_index): idx for idx, row in enumerate(chunk_b_frames_df.itertuples(index=False))}
    overlap_a_indices = [chunk_a_map[r] for r in overlap_records]
    overlap_b_indices = [chunk_b_map[r] for r in overlap_records]

    chunk_a_c2w_all = c2w_list_from_extrinsics(chunk_a_pred)
    chunk_b_c2w_all = c2w_list_from_extrinsics(chunk_b_pred)
    chunk_a_c2w_overlap = [chunk_a_c2w_all[i] for i in overlap_a_indices]
    chunk_b_c2w_overlap = [chunk_b_c2w_all[i] for i in overlap_b_indices]

    T_b_to_a, align_diag = estimate_pose_aware_similarity(chunk_b_c2w_overlap, chunk_a_c2w_overlap, estimate_scale=True)
    chunk_b_c2w_aligned_all = transform_c2w_list(chunk_b_c2w_all, T_b_to_a)
    chunk_b_c2w_aligned_overlap = [chunk_b_c2w_aligned_all[i] for i in overlap_b_indices]

    centers_a = np.asarray([c[:3, 3] for c in chunk_a_c2w_overlap], dtype=np.float64)
    centers_b = np.asarray([c[:3, 3] for c in chunk_b_c2w_overlap], dtype=np.float64)
    centers_b_aligned = np.asarray([c[:3, 3] for c in chunk_b_c2w_aligned_overlap], dtype=np.float64)
    lens_a = np.asarray([lens_direction_from_c2w(c) for c in chunk_a_c2w_overlap], dtype=np.float64)
    lens_b = np.asarray([lens_direction_from_c2w(c) for c in chunk_b_c2w_overlap], dtype=np.float64)
    lens_b_aligned = np.asarray([lens_direction_from_c2w(c) for c in chunk_b_c2w_aligned_overlap], dtype=np.float64)
    up_a = np.asarray([up_direction_from_c2w(c) for c in chunk_a_c2w_overlap], dtype=np.float64)
    up_b = np.asarray([up_direction_from_c2w(c) for c in chunk_b_c2w_overlap], dtype=np.float64)
    up_b_aligned = np.asarray([up_direction_from_c2w(c) for c in chunk_b_c2w_aligned_overlap], dtype=np.float64)

    center_error_pre = np.linalg.norm(centers_b - centers_a, axis=1)
    center_error_post = np.linalg.norm(centers_b_aligned - centers_a, axis=1)
    lens_error_pre = angle_deg(lens_b, lens_a)
    lens_error_post = angle_deg(lens_b_aligned, lens_a)
    up_error_pre = angle_deg(up_b, up_a)
    up_error_post = angle_deg(up_b_aligned, up_a)

    pair_rows = []
    for record_index, a_idx, b_idx, ce_pre, ce_post, le_pre, le_post, ue_pre, ue_post in zip(
        overlap_records,
        overlap_a_indices,
        overlap_b_indices,
        center_error_pre,
        center_error_post,
        lens_error_pre,
        lens_error_post,
        up_error_pre,
        up_error_post,
    ):
        pair_rows.append({
            "chunk_a_name": chunk_a_name,
            "chunk_b_name": chunk_b_name,
            "record_index": int(record_index),
            "chunk_a_local_index": int(a_idx),
            "chunk_b_local_index": int(b_idx),
            "center_error_pre": float(ce_pre),
            "center_error_post": float(ce_post),
            "lens_error_deg_pre": float(le_pre),
            "lens_error_deg_post": float(le_post),
            "up_error_deg_pre": float(ue_pre),
            "up_error_deg_post": float(ue_post),
        })

    pair_df = pd.DataFrame(pair_rows)
    points_df = pd.concat([
        pose_rows_to_frame_df(chunk_a_name, chunk_a_frames_df, chunk_a_c2w_all, "chunk_a_raw", overlap_record_set),
        pose_rows_to_frame_df(chunk_b_name, chunk_b_frames_df, chunk_b_c2w_all, "chunk_b_raw", overlap_record_set),
        pose_rows_to_frame_df(chunk_b_name, chunk_b_frames_df, chunk_b_c2w_aligned_all, "chunk_b_aligned_to_a", overlap_record_set),
    ], ignore_index=True)

    pair_label = f"{chunk_a_name}__{chunk_b_name}"
    pair_csv = matching_dir / f"{pair_label}_overlap_pair_metrics_arc.csv"
    points_csv = matching_dir / f"{pair_label}_trajectory_points_arc.csv"
    transform_npy = matching_dir / f"{pair_label}_transform_b_to_a.npy"
    plot_png = matching_dir / f"{pair_label}_trajectory_match.png"
    plot_html = matching_dir / f"{pair_label}_trajectory_match.html"
    summary_json = matching_dir / f"{pair_label}_matching_summary.json"

    pair_df.to_csv(pair_csv, index=False, encoding="utf-8")
    points_df.to_csv(points_csv, index=False, encoding="utf-8")
    np.save(transform_npy, T_b_to_a.astype(np.float32))
    plot_pose_match(
        points_df.loc[points_df["variant"] == "chunk_a_raw"].copy(),
        points_df.loc[points_df["variant"] == "chunk_b_raw"].copy(),
        points_df.loc[points_df["variant"] == "chunk_b_aligned_to_a"].copy(),
        plot_png,
    )
    write_pose_match_html(
        points_df.loc[points_df["variant"] == "chunk_a_raw"].copy(),
        points_df.loc[points_df["variant"] == "chunk_b_raw"].copy(),
        points_df.loc[points_df["variant"] == "chunk_b_aligned_to_a"].copy(),
        plot_html,
    )

    summary = {
        "status": "ok",
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-overlap-pose-matching",
        "chunk_a_name": chunk_a_name,
        "chunk_b_name": chunk_b_name,
        "chunk_a_frames_path": str(chunk_a_frames_path),
        "chunk_a_pred_extrinsics_path": str(chunk_a_pred_path),
        "chunk_b_frames_path": str(chunk_b_frames_path),
        "chunk_b_pred_extrinsics_path": str(chunk_b_pred_path),
        "chunk_a_row_count": int(len(chunk_a_frames_df)),
        "chunk_b_row_count": int(len(chunk_b_frames_df)),
        "overlap_record_count": int(len(overlap_records)),
        "overlap_records": overlap_records,
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
        "hard_fail": bool(align_diag["hard_fail"]),
        "relative_scale": float(align_diag["scale"]),
        "relative_translation_norm": float(np.linalg.norm(T_b_to_a[:3, 3])),
        "relative_rotation_deg": float(rotation_angle_deg_from_matrix(T_b_to_a[:3, :3] / max(abs(float(align_diag["scale"])), 1e-12))),
        "center_error_pre_mean": float(center_error_pre.mean()),
        "center_error_pre_p95": float(np.quantile(center_error_pre, 0.95)),
        "center_error_post_mean": float(center_error_post.mean()),
        "center_error_post_p95": float(np.quantile(center_error_post, 0.95)),
        "lens_error_deg_pre_mean": float(lens_error_pre.mean()),
        "lens_error_deg_pre_p95": float(np.quantile(lens_error_pre, 0.95)),
        "lens_error_deg_post_mean": float(lens_error_post.mean()),
        "lens_error_deg_post_p95": float(np.quantile(lens_error_post, 0.95)),
        "up_error_deg_pre_mean": float(up_error_pre.mean()),
        "up_error_deg_pre_p95": float(np.quantile(up_error_pre, 0.95)),
        "up_error_deg_post_mean": float(up_error_post.mean()),
        "up_error_deg_post_p95": float(np.quantile(up_error_post, 0.95)),
        "pair_metrics_csv": str(pair_csv),
        "trajectory_points_csv": str(points_csv),
        "transform_npy": str(transform_npy),
        "plot_png": str(plot_png),
        "plot_html": str(plot_html),
    }
    save_json(summary_json, summary)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    display_stage_summary(
        "7-6",
        "overlap pose matching",
        inputs=[
            {"item": "chunk_a_input_frames", "path": str(chunk_a_frames_path)},
            {"item": "chunk_a_pred_extrinsics", "path": str(chunk_a_pred_path)},
            {"item": "chunk_b_input_frames", "path": str(chunk_b_frames_path)},
            {"item": "chunk_b_pred_extrinsics", "path": str(chunk_b_pred_path)},
        ],
        outputs=[
            {"item": "matching_summary", "path": str(summary_json)},
            {"item": "matching_pair_metrics", "path": str(pair_csv)},
            {"item": "matching_trajectory_points", "path": str(points_csv)},
            {"item": "matching_transform", "path": str(transform_npy)},
            {"item": "matching_plot", "path": str(plot_png)},
            {"item": "matching_plot_html", "path": str(plot_html)},
        ],
        notes=[
            {"item": "chunk_pair", "value": pair_label},
            {"item": "overlap_record_count", "value": int(len(overlap_records))},
            {"item": "relative_rotation_deg", "value": float(summary["relative_rotation_deg"])},
            {"item": "center_error_post_p95", "value": float(summary["center_error_post_p95"])},
            {"item": "lens_error_deg_post_p95", "value": float(summary["lens_error_deg_post_p95"])},
        ],
    )
