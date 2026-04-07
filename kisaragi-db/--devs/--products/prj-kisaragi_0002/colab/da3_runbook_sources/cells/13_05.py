#13-5

from pathlib import Path
import json

import numpy as np
import pandas as pd

ctx = load_ctx()

probe_root = Path(ctx["probe_root"])
persist_root = Path(ctx.get("persist_root", probe_root))
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
anchor_dir = persist_root / "01_anchor"
merged_dir = Path(ctx.get("merged_dir", str(pipeline_root / "merged")))
merged_dir.mkdir(parents=True, exist_ok=True)

final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_diagnostics_dir.mkdir(parents=True, exist_ok=True)

camera_anchor_full_path = anchor_dir / "camera_anchor_full_arc.csv"
assert camera_anchor_full_path.exists(), camera_anchor_full_path

anchor_df = pd.read_csv(camera_anchor_full_path)
assert not anchor_df.empty, camera_anchor_full_path

if "cx_world" not in anchor_df.columns and "cam_cx" in anchor_df.columns:
    anchor_df["cx_world"] = anchor_df["cam_cx"]
    anchor_df["cy_world"] = anchor_df["cam_cy"]
    anchor_df["cz_world"] = anchor_df["cam_cz"]
if "anchor_lens_x" not in anchor_df.columns and "lens_x" in anchor_df.columns:
    anchor_df["anchor_lens_x"] = anchor_df["lens_x"]
    anchor_df["anchor_lens_y"] = anchor_df["lens_y"]
    anchor_df["anchor_lens_z"] = anchor_df["lens_z"]
if "anchor_up_x" not in anchor_df.columns and "up_x" in anchor_df.columns:
    anchor_df["anchor_up_x"] = anchor_df["up_x"]
    anchor_df["anchor_up_y"] = anchor_df["up_y"]
    anchor_df["anchor_up_z"] = anchor_df["up_z"]

required_cols = [
    "record_index",
    "cx_world", "cy_world", "cz_world",
    "anchor_lens_x", "anchor_lens_y", "anchor_lens_z",
    "anchor_up_x", "anchor_up_y", "anchor_up_z",
]
missing = [c for c in required_cols if c not in anchor_df.columns]
assert not missing, {"missing_columns": missing, "camera_anchor_full_path": str(camera_anchor_full_path)}


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


centers = anchor_df[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float64)
lens = normalize_rows(anchor_df[["anchor_lens_x", "anchor_lens_y", "anchor_lens_z"]].to_numpy(dtype=np.float64))
up = normalize_rows(anchor_df[["anchor_up_x", "anchor_up_y", "anchor_up_z"]].to_numpy(dtype=np.float64))
right = normalize_rows(np.cross(-up, -lens))
up_ortho = normalize_rows(np.cross(-lens, right))

lens_norm = np.linalg.norm(lens, axis=1)
up_norm = np.linalg.norm(up, axis=1)
right_norm = np.linalg.norm(right, axis=1)
lens_up_dot = np.sum(lens * up, axis=1)
lens_right_dot = np.sum(lens * right, axis=1)
up_right_dot = np.sum(up * right, axis=1)
ortho_up_error_deg = angle_deg(up, up_ortho)

delta_pos = np.zeros(len(anchor_df), dtype=np.float64)
delta_lens_deg = np.zeros(len(anchor_df), dtype=np.float64)
delta_up_deg = np.zeros(len(anchor_df), dtype=np.float64)
if len(anchor_df) >= 2:
    delta_pos[1:] = np.linalg.norm(np.diff(centers, axis=0), axis=1)
    delta_lens_deg[1:] = angle_deg(lens[:-1], lens[1:])
    delta_up_deg[1:] = angle_deg(up[:-1], up[1:])

valid_df = anchor_df[["record_index"]].copy()
valid_df["lens_norm"] = lens_norm
valid_df["up_norm"] = up_norm
valid_df["right_norm"] = right_norm
valid_df["lens_up_dot"] = lens_up_dot
valid_df["lens_right_dot"] = lens_right_dot
valid_df["up_right_dot"] = up_right_dot
valid_df["ortho_up_error_deg"] = ortho_up_error_deg
valid_df["delta_pos"] = delta_pos
valid_df["delta_lens_deg"] = delta_lens_deg
valid_df["delta_up_deg"] = delta_up_deg
valid_df["lens_nonzero_ok"] = lens_norm > 0.5
valid_df["up_nonzero_ok"] = up_norm > 0.5
valid_df["right_nonzero_ok"] = right_norm > 0.5
valid_df["lens_up_ortho_ok"] = np.abs(lens_up_dot) < 0.1
valid_df["ortho_up_ok"] = ortho_up_error_deg < 10.0
valid_df["trajectory_step_ok"] = delta_pos < 0.5
valid_df["orientation_step_ok"] = (delta_lens_deg < 20.0) & (delta_up_deg < 20.0)
valid_df["qc_pass"] = (
    valid_df["lens_nonzero_ok"]
    & valid_df["up_nonzero_ok"]
    & valid_df["right_nonzero_ok"]
    & valid_df["lens_up_ortho_ok"]
    & valid_df["ortho_up_ok"]
)

validation_csv = merged_dir / "arcore_anchor_trajectory_validation.csv"
summary_json = merged_dir / "arcore_anchor_trajectory_validation_summary.json"
valid_df.to_csv(validation_csv, index=False, encoding="utf-8")

summary = {
    "status": "ok" if bool(valid_df["qc_pass"].all()) else "warn",
    "route": "continuous-gs-v06-chunk18-overlap6-adopt12-arcore-anchor-validation",
    "row_count": int(len(valid_df)),
    "qc_pass_count": int(valid_df["qc_pass"].sum()),
    "qc_fail_count": int((~valid_df["qc_pass"]).sum()),
    "lens_nonzero_fail_count": int((~valid_df["lens_nonzero_ok"]).sum()),
    "up_nonzero_fail_count": int((~valid_df["up_nonzero_ok"]).sum()),
    "ortho_fail_count": int((~valid_df["lens_up_ortho_ok"]).sum()),
    "ortho_up_fail_count": int((~valid_df["ortho_up_ok"]).sum()),
    "delta_pos_max": float(valid_df["delta_pos"].max()),
    "delta_lens_deg_max": float(valid_df["delta_lens_deg"].max()),
    "delta_up_deg_max": float(valid_df["delta_up_deg"].max()),
    "validation_csv": str(validation_csv),
}
save_json(summary_json, summary)
save_json(final_outputs_diagnostics_dir / "arcore_anchor_trajectory_validation_summary.json", summary)

print(json.dumps(summary, indent=2, ensure_ascii=False))
display(valid_df)
display_stage_summary(
    "13-5",
    "arcore anchor trajectory validation",
    inputs=[
        {"item": "camera_anchor_full_arc", "path": str(camera_anchor_full_path)},
    ],
    outputs=[
        {"item": "arcore_anchor_trajectory_validation", "path": str(validation_csv)},
        {"item": "arcore_anchor_trajectory_validation_summary", "path": str(summary_json)},
    ],
    notes=[
        {"item": "qc_fail_count", "value": int((~valid_df["qc_pass"]).sum())},
        {"item": "status", "value": summary["status"]},
    ],
)
