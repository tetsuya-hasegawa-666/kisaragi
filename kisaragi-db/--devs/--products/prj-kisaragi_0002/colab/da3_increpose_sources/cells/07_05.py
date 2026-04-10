#7-5

from pathlib import Path
import json
import numpy as np
import pandas as pd

config = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8"))

def _existing(p):
    if not p:
        return None
    p = Path(p)
    return p if p.exists() else None

def _find_anchor_root(search_roots):
    rels = [
        "01_anchor/camera_anchor_full_arc.csv",
        "01_anchor/full_anchor_pose_diag_arc.csv",
        "01_anchor/camera_center_matrix_arc.csv",
        "01_anchor/camera_orientation_full_arc.csv",
    ]
    for root in search_roots:
        if root is None:
            continue
        root = Path(root)
        if root.is_file():
            root = root.parent
        if not root.exists():
            continue

        candidate_dirs = [root]
        candidate_dirs += [p for p in root.glob("*") if p.is_dir()]
        candidate_dirs += [p for p in root.glob("*/*") if p.is_dir()]

        seen = set()
        for d in candidate_dirs:
            d = d.resolve()
            if str(d) in seen:
                continue
            seen.add(str(d))
            if any((d / rel).exists() for rel in rels):
                return d
    return None

def _pick_first_existing(paths):
    for p in paths:
        if p.exists():
            return p
    return None

def _resolve_center_cols(df: pd.DataFrame):
    candidates = [
        ("cam_cx", "cam_cy", "cam_cz"),
        ("cx", "cy", "cz"),
        ("camera_center_x", "camera_center_y", "camera_center_z"),
        ("tx", "ty", "tz"),
    ]
    for cols in candidates:
        if all(c in df.columns for c in cols):
            return cols
    raise ValueError(f"camera center columns not found; columns={list(df.columns)}")

def _resolve_lens_cols(df: pd.DataFrame):
    candidates = [
        ("lens_x", "lens_y", "lens_z"),
        ("forward_x", "forward_y", "forward_z"),
        ("dir_x", "dir_y", "dir_z"),
    ]
    for cols in candidates:
        if all(c in df.columns for c in cols):
            return cols
    return None

search_roots = [
    _existing(config.get("persist_root")),
    _existing(config.get("google_drive_run_root")),
    _existing(config.get("run_root")),
    _existing(config.get("persist_dir")),
    _existing(config.get("output_root")),
    _existing(config.get("project_root")),
    _existing(config.get("session_dir")),
    _existing(config.get("target_probe_root")),
    _existing(config.get("probe_root")),
    Path("/content/drive/MyDrive/trajectreview"),
    Path("/content/drive/MyDrive"),
]

persist_root = _find_anchor_root(search_roots)
assert persist_root is not None, {
    "error": "anchor root not found",
    "searched_roots": [str(p) for p in search_roots if p is not None],
}

anchor_dir = persist_root / "01_anchor"
anchor_csv = _pick_first_existing([
    anchor_dir / "full_anchor_pose_diag_arc.csv",
    anchor_dir / "camera_anchor_full_arc.csv",
    anchor_dir / "camera_center_matrix_arc.csv",
])

assert anchor_csv is not None, {"missing_anchor_csv_in": str(anchor_dir)}

df = pd.read_csv(anchor_csv)
assert not df.empty, anchor_csv

# sequence 順に並べる
if "sequence_index" in df.columns:
    df = df.sort_values("sequence_index", kind="stable").reset_index(drop=True)
elif "frame_timestamp_ns" in df.columns:
    df = df.sort_values("frame_timestamp_ns", kind="stable").reset_index(drop=True)
elif "timestamp_ns" in df.columns:
    df = df.sort_values("timestamp_ns", kind="stable").reset_index(drop=True)
elif "timestamp" in df.columns:
    df = df.sort_values("timestamp", kind="stable").reset_index(drop=True)
else:
    df = df.reset_index(drop=True)

cx_col, cy_col, cz_col = _resolve_center_cols(df)
lens_cols = _resolve_lens_cols(df)

plotly_html = anchor_dir / "full_anchor_preview_arc.html"
plotly_png = anchor_dir / "full_anchor_preview_arc.png"

centers = df[[cx_col, cy_col, cz_col]].to_numpy(dtype=float)

# 矢印長
bbox_min = np.nanmin(centers, axis=0)
bbox_max = np.nanmax(centers, axis=0)
diag = float(np.linalg.norm(bbox_max - bbox_min))
arrow_scale = max(diag * 0.03, 0.02)

# Plotly 可視化
try:
    import plotly.graph_objects as go

    fig = go.Figure()

    fig.add_trace(go.Scatter3d(
        x=centers[:, 0],
        y=centers[:, 1],
        z=centers[:, 2],
        mode="lines+markers",
        name="camera_centers",
        marker=dict(size=2),
        line=dict(width=4),
        text=[f"idx={i}" for i in range(len(df))],
        hovertemplate="x=%{x:.3f}<br>y=%{y:.3f}<br>z=%{z:.3f}<br>%{text}<extra></extra>",
    ))

    if lens_cols is not None:
        lens = df[list(lens_cols)].to_numpy(dtype=float)
        lens_norm = np.linalg.norm(lens, axis=1, keepdims=True)
        lens_norm = np.maximum(lens_norm, 1e-12)
        lens = lens / lens_norm
        ends = centers + lens * arrow_scale

        step = max(len(df) // 40, 1)  # 矢印が多すぎないよう間引き
        for i in range(0, len(df), step):
            fig.add_trace(go.Scatter3d(
                x=[centers[i, 0], ends[i, 0]],
                y=[centers[i, 1], ends[i, 1]],
                z=[centers[i, 2], ends[i, 2]],
                mode="lines",
                name="lens_dir" if i == 0 else None,
                showlegend=(i == 0),
                line=dict(width=3),
                hoverinfo="skip",
            ))

    fig.update_layout(
        title="Full Anchor Preview",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, t=40, b=0),
    )

    fig.write_html(str(plotly_html), include_plotlyjs="cdn")
    preview_result = {
        "plotly_preview": "saved",
        "anchor_csv": str(anchor_csv),
        "html": str(plotly_html),
        "rows": int(len(df)),
        "center_cols": [cx_col, cy_col, cz_col],
        "lens_cols": list(lens_cols) if lens_cols is not None else None,
    }
except Exception as e:
    preview_result = {
        "plotly_preview": "skipped",
        "reason": repr(e),
        "anchor_csv": str(anchor_csv),
        "rows": int(len(df)),
        "available_columns": list(df.columns),
    }

print(preview_result)
display_stage_summary(
    "7-5",
    "full anchor preview",
    inputs=[
        {"item": "anchor_csv", "path": str(anchor_csv)},
    ],
    outputs=[
        {"item": "full_anchor_preview_html", "path": str(plotly_html)},
        {"item": "full_anchor_preview_png", "path": str(plotly_png)},
    ],
    notes=[
        {"item": "rows", "value": int(preview_result["rows"])},
        {"item": "center_cols", "value": "|".join(preview_result.get("center_cols", [])) if preview_result.get("center_cols") else ""},
        {"item": "lens_cols", "value": "|".join(preview_result.get("lens_cols", [])) if preview_result.get("lens_cols") else ""},
    ],
)
