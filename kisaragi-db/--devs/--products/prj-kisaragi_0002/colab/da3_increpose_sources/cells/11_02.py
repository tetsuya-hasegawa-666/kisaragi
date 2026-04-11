#11-2
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ctx = load_ctx()
probe_root = Path(ctx["probe_root"])
persist_root = Path(ctx.get("persist_root", probe_root))
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
merge_persist_only_dir = Path(ctx.get("stage_11_persist_only_dir", str(Path(ctx["final_outputs_dir"]) / "#11-1" / "persist_only")))
merged_dir = merge_persist_only_dir / "diagnostics"
merged_dir.mkdir(parents=True, exist_ok=True)
anchor_dir = persist_root / "01_anchor"

anchor_path = anchor_dir / "camera_anchor_full_arc.csv"
graph_solution_path = Path(ctx.get("stage_10_persist_only_dir", str(Path(ctx["final_outputs_dir"]) / "#10-1" / "persist_only"))) / "prepose_chunk_graph_solution_arc.csv"
transform_path = chunk_manifest_dir / "chunk_global_transforms_arc.csv"
merged_camera_pose_path = merge_persist_only_dir / "diagnostics" / "merged_camera_pose_arc.csv"
chunk_execution_plan_path = chunk_manifest_dir / "chunk_execution_plan.csv"
merge_summary_path = merge_persist_only_dir / "diagnostics" / "merge_summary.json"
merge_output_report_path = merge_persist_only_dir / "merge_output_report.json"

required = [anchor_path, chunk_execution_plan_path]
missing = [str(p) for p in required if not p.exists()]
assert not missing, {"missing_required": missing}

anchor_df = pd.read_csv(anchor_path)
items_df = pd.read_csv(chunk_execution_plan_path)
if "is_target" in items_df.columns:
    items_df = items_df.loc[items_df["is_target"].fillna(False)].copy()
merge_summary = load_json(merge_summary_path) if merge_summary_path.exists() else {}
merge_output_report = load_json(merge_output_report_path) if merge_output_report_path.exists() else {}

transform_df = pd.read_csv(graph_solution_path) if graph_solution_path.exists() else (pd.read_csv(transform_path) if transform_path.exists() else pd.DataFrame())


def _resolve_center_cols(df: pd.DataFrame):
    for cols in [
        ("cx_world", "cy_world", "cz_world"),
        ("cam_cx", "cam_cy", "cam_cz"),
        ("cx", "cy", "cz"),
        ("camera_center_x", "camera_center_y", "camera_center_z"),
        ("tx", "ty", "tz"),
    ]:
        if all(c in df.columns for c in cols):
            return cols
    raise AssertionError({"reason": "center columns not found", "columns": df.columns.tolist()})


def _resolve_dir_cols(df: pd.DataFrame):
    for cols in [
        ("anchor_lens_x", "anchor_lens_y", "anchor_lens_z"),
        ("lens_x", "lens_y", "lens_z"),
        ("forward_x", "forward_y", "forward_z"),
        ("dir_x", "dir_y", "dir_z"),
    ]:
        if all(c in df.columns for c in cols):
            return cols
    return None


def _load_transform_map(df: pd.DataFrame) -> dict:
    if df is None or len(df) == 0 or "chunk_name" not in df.columns:
        return {}
    mat_cols = [f"t{r}{c}" for r in range(4) for c in range(4)]
    if not set(mat_cols).issubset(df.columns):
        return {}
    out = {}
    for row in df.itertuples(index=False):
        M = np.eye(4, dtype=np.float32)
        for r in range(4):
            for c in range(4):
                M[r, c] = float(getattr(row, f"t{r}{c}"))
        out[str(row.chunk_name)] = M
    return out


def _resolve_chunk_output_dir(chunk_name: str) -> Path | None:
    direct = chunk_runs_dir / chunk_name
    if direct.exists():
        return direct
    hits = sorted(chunk_runs_dir.glob(f"batch_*/{chunk_name}"))
    return hits[0] if hits else None


def _sample_indices(n: int, k: int = 12) -> np.ndarray:
    if n <= 0:
        return np.array([], dtype=int)
    if n <= k:
        return np.arange(n, dtype=int)
    return np.unique(np.linspace(0, n - 1, num=k, dtype=int))


def _py_bool(value) -> bool:
    return bool(value)


def _poses_to_centers_dirs(c2w: np.ndarray):
    centers = c2w[:, :3, 3]
    lens = -c2w[:, :3, 2]
    norms = np.linalg.norm(lens, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)
    lens = lens / norms
    return centers, lens

anchor_center_cols = _resolve_center_cols(anchor_df)
anchor_dir_cols = _resolve_dir_cols(anchor_df)
anchor_view_df = anchor_df.copy()
if "sequence_index" in anchor_view_df.columns:
    anchor_view_df = anchor_view_df.sort_values("sequence_index", kind="stable").reset_index(drop=True)
elif "frame_timestamp_ns" in anchor_view_df.columns:
    anchor_view_df = anchor_view_df.sort_values("frame_timestamp_ns", kind="stable").reset_index(drop=True)
anchor_centers = anchor_view_df[list(anchor_center_cols)].to_numpy(dtype=float)
anchor_dirs = anchor_view_df[list(anchor_dir_cols)].to_numpy(dtype=float) if anchor_dir_cols is not None else None

transform_map = _load_transform_map(transform_df)
chunk_rows = []
chunk_plot_items = []
merged_pose_rows = []

item_cols = [c for c in ["chunk_id", "batch_index", "chunk_name", "chunk_csv"] if c in items_df.columns]
if item_cols:
    items_unique_df = items_df[item_cols].drop_duplicates().sort_values([c for c in ["chunk_id", "batch_index", "chunk_name"] if c in item_cols], kind="stable")
else:
    items_unique_df = items_df[["chunk_name", "chunk_csv"]].drop_duplicates()

for row in items_unique_df.itertuples(index=False):
    chunk_name = str(row.chunk_name)
    chunk_csv = Path(row.chunk_csv)
    if not chunk_csv.exists():
        continue
    out_dir = _resolve_chunk_output_dir(chunk_name)
    if out_dir is None:
        continue
    pred_path = out_dir / "pred_extrinsics.npy"
    if not pred_path.exists():
        continue
    local_df = pd.read_csv(chunk_csv)
    pred = to_4x4_batch(np.load(pred_path))
    if len(local_df) != pred.shape[0]:
        n = min(len(local_df), pred.shape[0])
        local_df = local_df.iloc[:n].copy()
        pred = pred[:n]
    T = transform_map.get(chunk_name, np.eye(4, dtype=np.float32))
    world = np.einsum("ij,njk->nik", T, pred)
    centers, lens = _poses_to_centers_dirs(world)
    sample_idx = _sample_indices(len(centers), 10)
    chunk_plot_items.append({
        "chunk_name": chunk_name,
        "centers": centers,
        "lens": lens,
        "sample_idx": sample_idx,
    })
    record_index_col = "record_index" if "record_index" in local_df.columns else None
    sequence_col = "sequence_index" if "sequence_index" in local_df.columns else None
    for i in range(len(local_df)):
        chunk_rows.append({
            "chunk_name": chunk_name,
            "local_index": int(i),
            "record_index": int(local_df.iloc[i][record_index_col]) if record_index_col else None,
            "sequence_index": int(local_df.iloc[i][sequence_col]) if sequence_col else None,
            "cx": float(centers[i,0]),
            "cy": float(centers[i,1]),
            "cz": float(centers[i,2]),
            "lens_x": float(lens[i,0]),
            "lens_y": float(lens[i,1]),
            "lens_z": float(lens[i,2]),
        })
        merged_pose_rows.append({
            "chunk_name": chunk_name,
            "record_index": int(local_df.iloc[i][record_index_col]) if record_index_col else None,
            "sequence_index": int(local_df.iloc[i][sequence_col]) if sequence_col else None,
            "cx": float(centers[i,0]),
            "cy": float(centers[i,1]),
            "cz": float(centers[i,2]),
            "lens_x": float(lens[i,0]),
            "lens_y": float(lens[i,1]),
            "lens_z": float(lens[i,2]),
        })

chunk_pose_review_csv = merged_dir / "chunk_pose_review_arc.csv"
pd.DataFrame(chunk_rows).to_csv(chunk_pose_review_csv, index=False, encoding="utf-8")

merged_pose_csv = merged_dir / "merged_pose_review_arc.csv"
if merged_camera_pose_path.exists() and merged_camera_pose_path.stat().st_size > 0:
    merged_df = pd.read_csv(merged_camera_pose_path)
    rename_map = {
        "cx_world": "cx",
        "cy_world": "cy",
        "cz_world": "cz",
        "anchor_lens_x": "lens_x",
        "anchor_lens_y": "lens_y",
        "anchor_lens_z": "lens_z",
    }
    merged_df = merged_df.rename(columns={k: v for k, v in rename_map.items() if k in merged_df.columns})
    keep_cols = [c for c in ["chunk_name", "record_index", "sequence_index", "cx", "cy", "cz", "lens_x", "lens_y", "lens_z"] if c in merged_df.columns]
    merged_df = merged_df[keep_cols].copy()
else:
    merged_df = pd.DataFrame(merged_pose_rows)
    if len(merged_df):
        if merged_df["record_index"].notna().any():
            merged_df = merged_df.sort_values(["record_index", "chunk_name"], kind="stable").drop_duplicates(["record_index"], keep="first")
        elif merged_df["sequence_index"].notna().any():
            merged_df = merged_df.sort_values(["sequence_index", "chunk_name"], kind="stable").drop_duplicates(["sequence_index"], keep="first")
        merged_df = merged_df.reset_index(drop=True)
merged_df.to_csv(merged_pose_csv, index=False, encoding="utf-8")

fig = make_subplots(
    rows=1,
    cols=3,
    specs=[[{"type": "scene"}, {"type": "scene"}, {"type": "scene"}]],
    subplot_titles=("full anchor", "chunks globalized", "merged trajectory"),
)

# panel 1: full anchor
fig.add_trace(go.Scatter3d(
    x=anchor_centers[:,0], y=anchor_centers[:,1], z=anchor_centers[:,2],
    mode="lines+markers", name="full_anchor", marker=dict(size=2),
    line=dict(width=4), showlegend=True,
), row=1, col=1)
if anchor_dirs is not None and len(anchor_centers):
    sample_idx = _sample_indices(len(anchor_centers), 12)
    for i in sample_idx:
        p = anchor_centers[i]
        d = anchor_dirs[i]
        fig.add_trace(go.Scatter3d(
            x=[p[0], p[0] + d[0] * 0.2],
            y=[p[1], p[1] + d[1] * 0.2],
            z=[p[2], p[2] + d[2] * 0.2],
            mode="lines", name="full_anchor_dir" if i == sample_idx[0] else None,
            showlegend=_py_bool(i == sample_idx[0]),
        ), row=1, col=1)

# panel 2: each chunk
for item in chunk_plot_items:
    centers = item["centers"]
    fig.add_trace(go.Scatter3d(
        x=centers[:,0], y=centers[:,1], z=centers[:,2],
        mode="lines+markers", name=item["chunk_name"], marker=dict(size=2), line=dict(width=4),
    ), row=1, col=2)
    for i in item["sample_idx"]:
        p = centers[i]
        d = item["lens"][i]
        fig.add_trace(go.Scatter3d(
            x=[p[0], p[0] + d[0] * 0.2],
            y=[p[1], p[1] + d[1] * 0.2],
            z=[p[2], p[2] + d[2] * 0.2],
            mode="lines", showlegend=False,
        ), row=1, col=2)

# panel 3: merged trajectory
if len(merged_df):
    fig.add_trace(go.Scatter3d(
        x=merged_df["cx"], y=merged_df["cy"], z=merged_df["cz"],
        mode="lines+markers", name="merged_pose", marker=dict(size=2), line=dict(width=5),
    ), row=1, col=3)
    for i in _sample_indices(len(merged_df), 12):
        p = merged_df.loc[i, ["cx", "cy", "cz"]].to_numpy(dtype=float)
        d = merged_df.loc[i, ["lens_x", "lens_y", "lens_z"]].to_numpy(dtype=float)
        fig.add_trace(go.Scatter3d(
            x=[p[0], p[0] + d[0] * 0.2],
            y=[p[1], p[1] + d[1] * 0.2],
            z=[p[2], p[2] + d[2] * 0.2],
            mode="lines", showlegend=False,
        ), row=1, col=3)

for scene_name in ["scene", "scene2", "scene3"]:
    fig.update_layout(**{scene_name: dict(aspectmode="data")})
fig.update_layout(height=700, width=1800, title="full anchor / chunk / merged pose review")

review_html = merged_dir / "premerge_pose_review_panel.html"
fig.write_html(str(review_html), include_plotlyjs="cdn")

review_summary = {
    "status": "ok",
    "merge_status": merge_summary.get("status"),
    "merge_output_status": merge_output_report.get("status"),
    "full_anchor_rows": int(len(anchor_df)),
    "chunk_review_rows": int(len(chunk_rows)),
    "merged_review_rows": int(len(merged_df)),
    "review_html": str(review_html),
    "chunk_pose_review_csv": str(chunk_pose_review_csv),
    "merged_pose_review_csv": str(merged_pose_csv),
    "transform_source": str(graph_solution_path if graph_solution_path.exists() else transform_path),
    "merged_camera_pose_source": str(merged_camera_pose_path) if merged_camera_pose_path.exists() else None,
}
save_json(merged_dir / "premerge_pose_review_summary.json", review_summary)
print(json.dumps(review_summary, indent=2, ensure_ascii=False))
display_stage_summary(
    "11-2",
    "merge review visualization",
    inputs=[
        {"item": "camera_anchor_full", "path": str(anchor_path)},
        {"item": "chunk_execution_plan", "path": str(chunk_execution_plan_path)},
        {"item": "chunk_global_transforms_or_graph_solution", "path": str(graph_solution_path if graph_solution_path.exists() else transform_path)},
        {"item": "merge_summary", "path": str(merge_summary_path)},
        {"item": "merge_output_report", "path": str(merge_output_report_path)},
    ],
    outputs=[
        {"item": "chunk_pose_review", "path": str(chunk_pose_review_csv)},
        {"item": "merged_pose_review", "path": str(merged_pose_csv)},
        {"item": "premerge_pose_review_panel", "path": str(review_html)},
        {"item": "premerge_pose_review_summary", "path": str(merged_dir / "premerge_pose_review_summary.json")},
        {"item": "merged_camera_pose", "path": str(merged_camera_pose_path)},
    ],
    notes=[
        {"item": "chunk_count", "value": int(len(chunk_plot_items))},
        {"item": "merged_review_rows", "value": int(len(merged_df))},
    ],
)
