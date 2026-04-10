#10-1

from pathlib import Path
import json
import math

import numpy as np
import pandas as pd

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
run_status_path = final_outputs_diagnostics_dir / "batch_run_status_arc.csv"
seed_trace_path = final_outputs_diagnostics_dir / "incremental_seed_trace_arc.csv"

assert batch_execution_items_path.exists(), batch_execution_items_path
assert camera_anchor_full_path.exists(), camera_anchor_full_path

items_df = pd.read_csv(batch_execution_items_path)
assert not items_df.empty, batch_execution_items_path
sort_cols = [c for c in ["chunk_id", "batch_index", "batch_name", "chunk_name"] if c in items_df.columns]
if sort_cols:
    items_df = items_df.sort_values(sort_cols, kind="stable").reset_index(drop=True)

run_status_df = pd.read_csv(run_status_path) if run_status_path.exists() and run_status_path.stat().st_size > 0 else pd.DataFrame()
seed_trace_df = pd.read_csv(seed_trace_path) if seed_trace_path.exists() and seed_trace_path.stat().st_size > 0 else pd.DataFrame()

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
]
missing_anchor_cols = [c for c in required_anchor_cols if c not in anchor_full_df.columns]
assert not missing_anchor_cols, {"missing_anchor_columns": missing_anchor_cols}

# gate値は既存を踏襲
PREMERGE_CENTER_ERROR_P95_MAX = 0.25
PREMERGE_LENS_ERROR_DEG_P95_MAX = 12.0
PREMERGE_DELTA_CENTER_ERROR_MAX = 0.15
PREMERGE_DELTA_LENS_ERROR_DEG_MAX = 8.0

residual_csv = merged_dir / "pred_vs_anchor_pose_residual_arc.csv"
missing_pred_csv = merged_dir / "pred_vs_anchor_pose_residual_missing_pred_arc.csv"
gate_csv = merged_dir / "premerge_pose_gate_arc.csv"
route_compare_json = merged_dir / "premerge_route_compare_summary.json"
route_compare_csv = merged_dir / "premerge_route_compare_arc.csv"
graph_solution_csv = merged_dir / "prepose_chunk_graph_solution_arc.csv"   # downstream互換: chunk validation summary
graph_summary_json = merged_dir / "prepose_chunk_graph_summary.json"        # downstream互換: incremental summary
graph_opt_summary_json = merged_dir / "prepose_graph_optimization_summary.json"
validation_json = merged_dir / "premerge_pose_validation.json"
identity_transform_csv = chunk_manifest_dir / "chunk_global_transforms_arc.csv"

MAT_COLS = [f"t{r}{c}" for r in range(4) for c in range(4)]


def _record_col(df: pd.DataFrame) -> str:
    for c in ["record_index", "frame_index", "global_index", "index"]:
        if c in df.columns:
            return c
    raise AssertionError({"reason": "record index column not found", "columns": df.columns.tolist()})


def _safe_int(v):
    try:
        return int(v)
    except Exception:
        return None


def _normalize(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float64)
    n = np.linalg.norm(v)
    if n <= 1e-12:
        return np.zeros_like(v)
    return v / n


def _angle_deg(a: np.ndarray, b: np.ndarray) -> float:
    a = _normalize(a)
    b = _normalize(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom <= 1e-12:
        return float("nan")
    cosv = np.clip(float(np.dot(a, b)), -1.0, 1.0)
    return float(np.degrees(np.arccos(cosv)))


def _p95(series) -> float:
    arr = pd.Series(series).dropna().to_numpy(dtype=np.float64)
    if len(arr) == 0:
        return float("nan")
    return float(np.percentile(arr, 95))


def _max_abs(series) -> float:
    arr = pd.Series(series).dropna().to_numpy(dtype=np.float64)
    if len(arr) == 0:
        return float("nan")
    return float(np.max(np.abs(arr)))


def _ensure_pose_batch(arr: np.ndarray) -> np.ndarray:
    arr = np.asarray(arr, dtype=np.float64)
    if arr.ndim == 2:
        arr = arr[None, ...]
    if arr.shape[-2:] == (3, 4):
        out = np.repeat(np.eye(4, dtype=np.float64)[None, ...], arr.shape[0], axis=0)
        out[:, :3, :] = arr
        return out
    if arr.shape[-2:] == (4, 4):
        return arr
    raise AssertionError({"reason": "unexpected_pose_shape", "shape": tuple(arr.shape)})


def _w2c_to_c2w_batch(w2c_batch: np.ndarray) -> np.ndarray:
    out = []
    for M in _ensure_pose_batch(w2c_batch):
        out.append(np.linalg.inv(M))
    return np.stack(out, axis=0)


def _poses_to_center_lens(c2w_batch: np.ndarray):
    centers = c2w_batch[:, :3, 3]
    lens = -c2w_batch[:, :3, 2]
    lens = np.stack([_normalize(v) for v in lens], axis=0)
    return centers, lens


def _resolve_pred_path(item_row: pd.Series) -> Path | None:
    candidates = []

    for col in [
        "pred_extrinsics_path",
        "pred_extrinsics_npy",
        "chunk_pred_extrinsics_path",
        "output_pred_extrinsics_path",
    ]:
        if col in item_row.index and pd.notna(item_row[col]) and str(item_row[col]).strip():
            candidates.append(Path(str(item_row[col]).strip()))

    chunk_name = str(item_row.get("chunk_name", "")).strip()
    batch_name = str(item_row.get("batch_name", "")).strip()

    if "batch_work_dir" in item_row.index and pd.notna(item_row["batch_work_dir"]) and str(item_row["batch_work_dir"]).strip():
        batch_work_dir = Path(str(item_row["batch_work_dir"]).strip())
        if chunk_name:
            candidates.append(batch_work_dir / chunk_name / "pred_extrinsics.npy")
        candidates.append(batch_work_dir / "pred_extrinsics.npy")

    if chunk_name:
        candidates.append(chunk_runs_dir / chunk_name / "pred_extrinsics.npy")
        if batch_name:
            candidates.append(chunk_runs_dir / batch_name / chunk_name / "pred_extrinsics.npy")
        candidates.extend(sorted(chunk_runs_dir.glob(f"batch_*/{chunk_name}/pred_extrinsics.npy")))

    if not run_status_df.empty:
        rs = run_status_df.loc[run_status_df["chunk_name"].astype(str) == chunk_name].copy()
        if "batch_name" in run_status_df.columns and batch_name:
            rs2 = rs.loc[rs["batch_name"].astype(str) == batch_name].copy()
            if len(rs2):
                rs = rs2
        if len(rs):
            out_dir = Path(str(rs.iloc[-1]["out_dir"]))
            candidates.insert(0, out_dir / "pred_extrinsics.npy")

    seen = set()
    uniq = []
    for c in candidates:
        s = str(c)
        if s not in seen:
            uniq.append(c)
            seen.add(s)

    for c in uniq:
        if c.exists():
            return c
    return None


def _resolve_chunk_csv(item_row: pd.Series, pred_path: Path | None) -> Path | None:
    candidates = []

    for col in ["runtime_chunk_csv", "chunk_csv", "chunk_input_csv"]:
        if col in item_row.index and pd.notna(item_row[col]) and str(item_row[col]).strip():
            candidates.append(Path(str(item_row[col]).strip()))

    chunk_name = str(item_row.get("chunk_name", "")).strip()
    batch_name = str(item_row.get("batch_name", "")).strip()

    if pred_path is not None:
        candidates.append(pred_path.parent / "chunk_input_frames.csv")
        candidates.append(pred_path.parent / "_runtime" / "chunk_input_seeded.csv")

    if not run_status_df.empty:
        rs = run_status_df.loc[run_status_df["chunk_name"].astype(str) == chunk_name].copy()
        if "batch_name" in run_status_df.columns and batch_name:
            rs2 = rs.loc[rs["batch_name"].astype(str) == batch_name].copy()
            if len(rs2):
                rs = rs2
        if len(rs):
            if "runtime_chunk_csv" in rs.columns and pd.notna(rs.iloc[-1]["runtime_chunk_csv"]):
                candidates.insert(0, Path(str(rs.iloc[-1]["runtime_chunk_csv"])))

    seen = set()
    uniq = []
    for c in candidates:
        s = str(c)
        if s not in seen:
            uniq.append(c)
            seen.add(s)

    for c in uniq:
        if c.exists():
            return c
    return None


def _load_chunk_pose_df(item_row: pd.Series) -> pd.DataFrame:
    pred_path = _resolve_pred_path(item_row)
    chunk_csv_path = _resolve_chunk_csv(item_row, pred_path)

    chunk_name = str(item_row.get("chunk_name", ""))
    if pred_path is None:
        return pd.DataFrame(columns=[
            "chunk_name", "record_index", "chunk_local_index",
            "pred_cx_world", "pred_cy_world", "pred_cz_world",
            "pred_lens_x", "pred_lens_y", "pred_lens_z",
            "is_output_range", "is_adopt_range",
        ])

    assert chunk_csv_path is not None and chunk_csv_path.exists(), {
        "chunk_name": chunk_name,
        "reason": "chunk_csv_not_found",
        "pred_path": str(pred_path),
    }

    chunk_df = pd.read_csv(chunk_csv_path)
    rec_col = _record_col(chunk_df)
    pred_w2c = _ensure_pose_batch(np.load(pred_path))
    assert len(chunk_df) == len(pred_w2c), {
        "chunk_name": chunk_name,
        "reason": "row_count_mismatch",
        "chunk_rows": int(len(chunk_df)),
        "pred_rows": int(len(pred_w2c)),
        "chunk_csv": str(chunk_csv_path),
        "pred_path": str(pred_path),
    }

    c2w = _w2c_to_c2w_batch(pred_w2c)
    centers, lens = _poses_to_center_lens(c2w)

    if "is_output_range" not in chunk_df.columns:
        chunk_df["is_output_range"] = False
    if "is_adopt_range" not in chunk_df.columns:
        chunk_df["is_adopt_range"] = False

    out = pd.DataFrame({
        "chunk_name": chunk_name,
        "record_index": chunk_df[rec_col].astype(int).to_numpy(),
        "chunk_local_index": np.arange(len(chunk_df), dtype=int),
        "pred_cx_world": centers[:, 0],
        "pred_cy_world": centers[:, 1],
        "pred_cz_world": centers[:, 2],
        "pred_lens_x": lens[:, 0],
        "pred_lens_y": lens[:, 1],
        "pred_lens_z": lens[:, 2],
        "pred_path": str(pred_path),
        "chunk_csv_path": str(chunk_csv_path),
        "is_output_range": chunk_df["is_output_range"].astype(bool).to_numpy(),
        "is_adopt_range": chunk_df["is_adopt_range"].astype(bool).to_numpy(),
    })

    if "seed_pose_applied" in chunk_df.columns:
        out["seed_pose_applied"] = chunk_df["seed_pose_applied"].astype(bool).to_numpy()
    else:
        out["seed_pose_applied"] = False

    return out


items_eval_df = items_df.copy()

if not run_status_df.empty and {"chunk_name", "batch_name", "out_dir"}.issubset(run_status_df.columns):
    merge_cols = ["chunk_name", "batch_name"]
    rs_cols = [c for c in ["chunk_name", "batch_name", "status", "returncode", "outputs_exist", "out_dir", "runtime_chunk_csv", "seeded_overlap_count"] if c in run_status_df.columns]
    items_eval_df = items_eval_df.merge(
        run_status_df[rs_cols].drop_duplicates(subset=merge_cols, keep="last"),
        on=merge_cols,
        how="left",
        suffixes=("", "_run"),
    )

if not seed_trace_df.empty and "chunk_name" in seed_trace_df.columns:
    st_cols = [c for c in ["chunk_name", "seeded_overlap_count", "chunk_step", "overlap_size", "adopt_size", "pose_pipeline_mode"] if c in seed_trace_df.columns]
    items_eval_df = items_eval_df.merge(
        seed_trace_df[st_cols].drop_duplicates(subset=["chunk_name"], keep="last"),
        on="chunk_name",
        how="left",
        suffixes=("", "_seed"),
    )

chunk_pose_rows = []
missing_chunk_rows = []

for _, item_row in items_eval_df.iterrows():
    chunk_name = str(item_row.get("chunk_name", ""))
    pred_path = _resolve_pred_path(item_row)
    if pred_path is None:
        missing_chunk_rows.append({
            "chunk_name": chunk_name,
            "reason": "pred_extrinsics_not_found",
        })
        continue

    pose_df = _load_chunk_pose_df(item_row)
    if pose_df.empty:
        missing_chunk_rows.append({
            "chunk_name": chunk_name,
            "reason": "pose_df_empty",
            "pred_path": str(pred_path),
        })
        continue

    pose_df["chunk_id"] = _safe_int(item_row["chunk_id"]) if "chunk_id" in item_row.index else None
    pose_df["batch_name"] = str(item_row.get("batch_name", ""))
    pose_df["seeded_overlap_count"] = int(item_row["seeded_overlap_count"]) if pd.notna(item_row.get("seeded_overlap_count")) else 0
    chunk_pose_rows.append(pose_df)

all_chunk_pose_df = pd.concat(chunk_pose_rows, ignore_index=True) if chunk_pose_rows else pd.DataFrame()

anchor_eval_df = anchor_full_df[[
    "record_index",
    "cx_world", "cy_world", "cz_world",
    "anchor_lens_x", "anchor_lens_y", "anchor_lens_z",
]].copy()
anchor_eval_df["record_index"] = anchor_eval_df["record_index"].astype(int)
anchor_eval_df = anchor_eval_df.sort_values("record_index", kind="stable").reset_index(drop=True)

if all_chunk_pose_df.empty:
    raise AssertionError({"reason": "no_chunk_pose_loaded", "missing_chunk_rows": missing_chunk_rows[:10]})

all_chunk_pose_df = all_chunk_pose_df.sort_values(
    [c for c in ["chunk_id", "batch_name", "chunk_name", "chunk_local_index"] if c in all_chunk_pose_df.columns],
    kind="stable",
).reset_index(drop=True)

# 評価対象は output range のみ
eval_pose_df = all_chunk_pose_df.loc[all_chunk_pose_df["is_output_range"].fillna(False)].copy()

# global pred は adopt優先、その次に output range 最後勝ち
adopt_pose_df = eval_pose_df.loc[eval_pose_df["is_adopt_range"].fillna(False)].copy()

if len(adopt_pose_df):
    global_pred_df = (
        adopt_pose_df
        .drop_duplicates(subset=["record_index"], keep="last")
        .sort_values("record_index", kind="stable")
        .reset_index(drop=True)
    )
else:
    global_pred_df = (
        eval_pose_df
        .drop_duplicates(subset=["record_index"], keep="last")
        .sort_values("record_index", kind="stable")
        .reset_index(drop=True)
    )

target_record_indices = sorted(eval_pose_df["record_index"].astype(int).unique().tolist())

target_anchor_df = anchor_eval_df.loc[
    anchor_eval_df["record_index"].astype(int).isin(target_record_indices)
].copy()

residual_df = global_pred_df.merge(target_anchor_df, on="record_index", how="left")

residual_df["center_error_m"] = np.sqrt(
    (residual_df["pred_cx_world"] - residual_df["cx_world"]) ** 2 +
    (residual_df["pred_cy_world"] - residual_df["cy_world"]) ** 2 +
    (residual_df["pred_cz_world"] - residual_df["cz_world"]) ** 2
)

residual_df["lens_error_deg"] = [
    _angle_deg(
        np.array([px, py, pz], dtype=np.float64),
        np.array([ax, ay, az], dtype=np.float64),
    )
    for px, py, pz, ax, ay, az in zip(
        residual_df["pred_lens_x"], residual_df["pred_lens_y"], residual_df["pred_lens_z"],
        residual_df["anchor_lens_x"], residual_df["anchor_lens_y"], residual_df["anchor_lens_z"],
    )
]

residual_df["pred_exists"] = True
residual_df.to_csv(residual_csv, index=False, encoding="utf-8")

missing_pred_df = target_anchor_df.loc[
    ~target_anchor_df["record_index"].isin(global_pred_df["record_index"].astype(int))
].copy()
missing_pred_df["reason"] = "target_output_record_index_not_in_global_pred"
missing_pred_df.to_csv(missing_pred_csv, index=False, encoding="utf-8")

route_rows = []
if len(residual_df) >= 2:
    r = residual_df.sort_values("record_index", kind="stable").reset_index(drop=True)
    for i in range(1, len(r)):
        prev_row = r.iloc[i - 1]
        curr_row = r.iloc[i]

        pred_delta = np.array([
            curr_row["pred_cx_world"] - prev_row["pred_cx_world"],
            curr_row["pred_cy_world"] - prev_row["pred_cy_world"],
            curr_row["pred_cz_world"] - prev_row["pred_cz_world"],
        ], dtype=np.float64)
        anchor_delta = np.array([
            curr_row["cx_world"] - prev_row["cx_world"],
            curr_row["cy_world"] - prev_row["cy_world"],
            curr_row["cz_world"] - prev_row["cz_world"],
        ], dtype=np.float64)

        delta_center_error_m = float(np.linalg.norm(pred_delta - anchor_delta))

        prev_pred_lens = np.array([prev_row["pred_lens_x"], prev_row["pred_lens_y"], prev_row["pred_lens_z"]], dtype=np.float64)
        curr_pred_lens = np.array([curr_row["pred_lens_x"], curr_row["pred_lens_y"], curr_row["pred_lens_z"]], dtype=np.float64)
        prev_anchor_lens = np.array([prev_row["anchor_lens_x"], prev_row["anchor_lens_y"], prev_row["anchor_lens_z"]], dtype=np.float64)
        curr_anchor_lens = np.array([curr_row["anchor_lens_x"], curr_row["anchor_lens_y"], curr_row["anchor_lens_z"]], dtype=np.float64)

        pred_lens_delta_deg = _angle_deg(prev_pred_lens, curr_pred_lens)
        anchor_lens_delta_deg = _angle_deg(prev_anchor_lens, curr_anchor_lens)
        delta_lens_error_deg = float(abs(pred_lens_delta_deg - anchor_lens_delta_deg))

        route_rows.append({
            "prev_record_index": int(prev_row["record_index"]),
            "record_index": int(curr_row["record_index"]),
            "delta_center_error_m": delta_center_error_m,
            "pred_lens_delta_deg": pred_lens_delta_deg,
            "anchor_lens_delta_deg": anchor_lens_delta_deg,
            "delta_lens_error_deg": delta_lens_error_deg,
            "pred_chunk_name": str(curr_row["chunk_name"]),
            "pred_chunk_id": _safe_int(curr_row["chunk_id"]) if "chunk_id" in curr_row else None,
        })

route_compare_df = pd.DataFrame(route_rows)
route_compare_df.to_csv(route_compare_csv, index=False, encoding="utf-8")

chunk_gate_rows = []
for _, item_row in items_eval_df.iterrows():
    chunk_name = str(item_row.get("chunk_name", ""))
    chunk_id = _safe_int(item_row["chunk_id"]) if "chunk_id" in item_row.index else None

    chunk_eval_rows = residual_df.loc[residual_df["chunk_name"].astype(str) == chunk_name].copy()
    if len(chunk_eval_rows) == 0:
        chunk_gate_rows.append({
            "chunk_id": chunk_id,
            "chunk_name": chunk_name,
            "status": "missing",
            "record_count": 0,
            "seeded_overlap_count": int(item_row["seeded_overlap_count"]) if pd.notna(item_row.get("seeded_overlap_count")) else 0,
            "center_error_p95_m": np.nan,
            "lens_error_p95_deg": np.nan,
            "delta_center_error_max_m": np.nan,
            "delta_lens_error_max_deg": np.nan,
            "hard_fail": True,
            "anchor_warning": False,
            **{c: np.nan for c in MAT_COLS},
        })
        continue

    chunk_route_rows = route_compare_df.loc[route_compare_df["pred_chunk_name"].astype(str) == chunk_name].copy()
    center_error_p95_m = _p95(chunk_eval_rows["center_error_m"])
    lens_error_p95_deg = _p95(chunk_eval_rows["lens_error_deg"])
    delta_center_error_max_m = _max_abs(chunk_route_rows["delta_center_error_m"])
    delta_lens_error_max_deg = _max_abs(chunk_route_rows["delta_lens_error_deg"])

    hard_fail = (
        (pd.notna(center_error_p95_m) and center_error_p95_m > PREMERGE_CENTER_ERROR_P95_MAX)
        or (pd.notna(lens_error_p95_deg) and lens_error_p95_deg > PREMERGE_LENS_ERROR_DEG_P95_MAX)
    )
    anchor_warning = (
        (pd.notna(delta_center_error_max_m) and delta_center_error_max_m > PREMERGE_DELTA_CENTER_ERROR_MAX)
        or (pd.notna(delta_lens_error_max_deg) and delta_lens_error_max_deg > PREMERGE_DELTA_LENS_ERROR_DEG_MAX)
    )

    row = {
        "chunk_id": chunk_id,
        "chunk_name": chunk_name,
        "status": "ok" if not hard_fail else "hard_fail",
        "record_count": int(len(chunk_eval_rows)),
        "seeded_overlap_count": int(item_row["seeded_overlap_count"]) if pd.notna(item_row.get("seeded_overlap_count")) else 0,
        "center_error_p95_m": center_error_p95_m,
        "lens_error_p95_deg": lens_error_p95_deg,
        "delta_center_error_max_m": delta_center_error_max_m,
        "delta_lens_error_max_deg": delta_lens_error_max_deg,
        "hard_fail": bool(hard_fail),
        "anchor_warning": bool(anchor_warning),
    }
    I = np.eye(4, dtype=np.float64)
    for r in range(4):
        for c in range(4):
            row[f"t{r}{c}"] = float(I[r, c])
    chunk_gate_rows.append(row)

gate_df = pd.DataFrame(chunk_gate_rows)
gate_df.to_csv(gate_csv, index=False, encoding="utf-8")
gate_df.to_csv(graph_solution_csv, index=False, encoding="utf-8")  # downstream互換: identity列つき

identity_rows = []
for _, item_row in items_eval_df.iterrows():
    chunk_name = str(item_row.get("chunk_name", ""))
    row = {"chunk_name": chunk_name}
    I = np.eye(4, dtype=np.float64)
    for r in range(4):
        for c in range(4):
            row[f"t{r}{c}"] = float(I[r, c])
    identity_rows.append(row)
identity_df = pd.DataFrame(identity_rows)
identity_df.to_csv(identity_transform_csv, index=False, encoding="utf-8")

route_compare_summary = {
    "route_label": "continuous-gs-v07-chunk18-step6-context12-output6-adopt6-incremental",
    "selected_route_counts": [int(len(route_compare_df))],
    "preferred_route_label": "incremental_seeded_global_pose",
    "evaluation_scope": "output_range_only",
    "context_size": 12,
    "output_size": 6,
    "adopt_size": 6,
    "delta_center_error_max_m": _max_abs(route_compare_df["delta_center_error_m"]) if len(route_compare_df) else float("nan"),
    "delta_lens_error_max_deg": _max_abs(route_compare_df["delta_lens_error_deg"]) if len(route_compare_df) else float("nan"),
}
save_json(route_compare_json, route_compare_summary)

hard_fail_count = int(gate_df["hard_fail"].fillna(False).astype(bool).sum()) if len(gate_df) else 0
anchor_warning_count = int(gate_df["anchor_warning"].fillna(False).astype(bool).sum()) if len(gate_df) else 0
tested_chunk_count = int(len(gate_df))
missing_pred_count = int(len(missing_pred_df))

if hard_fail_count > 0:
    status = "hard_fail"
elif anchor_warning_count > 0:
    status = "warning"
else:
    status = "ok"

validation = {
    "status": status,
    "route": "continuous-gs-v07-chunk18-step6-context12-output6-adopt6-incremental",
    "preferred_route_label": "incremental_seeded_global_pose",
    "evaluation_scope": "output_range_only",
    "context_size": 12,
    "output_size": 6,
    "adopt_size": 6,
    "selected_route_counts": [int(len(route_compare_df))],
    "preferred_fallback_used_count": 0,
    "tested_chunk_count": tested_chunk_count,
    "hard_fail_count": hard_fail_count,
    "anchor_warning_count": anchor_warning_count,
    "missing_pred_count": missing_pred_count,
    "global_pred_record_count": int(len(global_pred_df)),
    "target_output_record_count": int(len(target_anchor_df)),
    "center_error_p95_m": _p95(residual_df["center_error_m"]) if len(residual_df) else float("nan"),
    "lens_error_p95_deg": _p95(residual_df["lens_error_deg"]) if len(residual_df) else float("nan"),
    "delta_center_error_max_m": _max_abs(route_compare_df["delta_center_error_m"]) if len(route_compare_df) else float("nan"),
    "delta_lens_error_max_deg": _max_abs(route_compare_df["delta_lens_error_deg"]) if len(route_compare_df) else float("nan"),
    "artifacts": {
        "residual_csv": str(residual_csv),
        "missing_pred_csv": str(missing_pred_csv),
        "gate_csv": str(gate_csv),
        "route_compare_csv": str(route_compare_csv),
        "graph_solution_csv_compat": str(graph_solution_csv),
        "identity_transform_csv": str(identity_transform_csv),
    },
}
save_json(validation_json, validation)

graph_summary = {
    "mode": "incremental_validation_only",
    "graph_mainflow_removed": True,
    "graph_edges_used": False,
    "graph_solution_csv_semantics": "chunk_validation_summary_with_identity_columns",
    "chunk_global_transforms_semantics": "identity_transforms_for_downstream_compat",
    "evaluation_scope": "output_range_only",
    "context_size": 12,
    "output_size": 6,
    "adopt_size": 6,
    "tested_chunk_count": tested_chunk_count,
    "status": status,
}
save_json(graph_summary_json, graph_summary)
save_json(graph_opt_summary_json, {
    "mode": "not_applicable",
    "reason": "sim3_graph_mainflow_removed",
    "status": status,
})

missing_chunk_df = pd.DataFrame(missing_chunk_rows)
if len(missing_chunk_df):
    display(missing_chunk_df.head(20))

print(json.dumps(validation, indent=2, ensure_ascii=False))
display(gate_df.head(20))
display(route_compare_df.head(20))
display(residual_df.head(20))

display_stage_summary(
    "10-1",
    "incremental premerge validation and compatibility artifacts",
    outputs=[
        {"item": "validation_json", "path": str(validation_json)},
        {"item": "gate_csv", "path": str(gate_csv)},
        {"item": "route_compare_csv", "path": str(route_compare_csv)},
        {"item": "residual_csv", "path": str(residual_csv)},
        {"item": "graph_solution_csv_compat", "path": str(graph_solution_csv)},
        {"item": "identity_transform_csv", "path": str(identity_transform_csv)},
    ],
)

items_df = pd.read_csv(batch_execution_items_path)
display(items_df[["chunk_id", "chunk_name", "batch_name", "batch_work_dir"]].head(20))
