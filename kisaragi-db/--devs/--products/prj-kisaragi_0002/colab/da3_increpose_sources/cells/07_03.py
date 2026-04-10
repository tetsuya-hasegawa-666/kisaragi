#7-3

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
            if all((d / rel).exists() for rel in rels):
                return d
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
    "error": "01_anchor not found",
    "searched_roots": [str(p) for p in search_roots if p is not None],
    "expected": "01_anchor/camera_anchor_full_arc.csv",
}

anchor_dir = persist_root / "01_anchor"
anchor_path = anchor_dir / "camera_anchor_full_arc.csv"
anchor_df = pd.read_csv(anchor_path)

assert not anchor_df.empty, anchor_path

# sequence_index を保証
if "sequence_index" not in anchor_df.columns:
    if "frame_timestamp_ns" in anchor_df.columns:
        anchor_df = anchor_df.sort_values("frame_timestamp_ns", kind="stable").reset_index(drop=True)
    elif "timestamp_ns" in anchor_df.columns:
        anchor_df = anchor_df.sort_values("timestamp_ns", kind="stable").reset_index(drop=True)
    elif "timestamp" in anchor_df.columns:
        anchor_df = anchor_df.sort_values("timestamp", kind="stable").reset_index(drop=True)
    else:
        anchor_df = anchor_df.reset_index(drop=True)
    anchor_df["sequence_index"] = np.arange(len(anchor_df), dtype=np.int64)
else:
    anchor_df = anchor_df.sort_values("sequence_index", kind="stable").reset_index(drop=True)

required_cols = [
    "right_x","right_y","right_z",
    "up_x","up_y","up_z",
    "lens_x","lens_y","lens_z",
    "cam_cx","cam_cy","cam_cz",
]
missing = [c for c in required_cols if c not in anchor_df.columns]
assert not missing, {"missing_columns": missing, "anchor_path": str(anchor_path)}

def _normalize(v, eps=1e-12):
    n = np.linalg.norm(v, axis=1, keepdims=True)
    n = np.maximum(n, eps)
    return v / n

def _wrap_deg(x):
    return (x + 180.0) % 360.0 - 180.0

def _angle_deg(a, b, eps=1e-12):
    a = _normalize(a, eps)
    b = _normalize(b, eps)
    d = np.sum(a * b, axis=1)
    d = np.clip(d, -1.0, 1.0)
    return np.degrees(np.arccos(d))

# world basis: x right, y up, z forward を仮定
# lens = camera forward in world
# yaw   = atan2(fx, fz)
# pitch = atan2(-fy, sqrt(fx^2 + fz^2))
# roll  = up ベクトルの傾きから近似導出
lens = anchor_df[["lens_x","lens_y","lens_z"]].to_numpy(dtype=float)
up   = anchor_df[["up_x","up_y","up_z"]].to_numpy(dtype=float)
right = anchor_df[["right_x","right_y","right_z"]].to_numpy(dtype=float)
centers = anchor_df[["cam_cx","cam_cy","cam_cz"]].to_numpy(dtype=float)

lens = _normalize(lens)
up = _normalize(up)
right = _normalize(right)

fx, fy, fz = lens[:, 0], lens[:, 1], lens[:, 2]
ux, uy, uz = up[:, 0], up[:, 1], up[:, 2]

yaw_deg = np.degrees(np.arctan2(fx, fz))
pitch_deg = np.degrees(np.arctan2(-fy, np.sqrt(np.maximum(fx * fx + fz * fz, 1e-12))))

# roll 近似:
# forward を固定したときの up の回転を world-up 基準で表す
world_up = np.tile(np.array([[0.0, 1.0, 0.0]]), (len(anchor_df), 1))
proj_world_up = world_up - np.sum(world_up * lens, axis=1, keepdims=True) * lens
proj_up = up - np.sum(up * lens, axis=1, keepdims=True) * lens
proj_world_up = _normalize(proj_world_up)
proj_up = _normalize(proj_up)

cross_u = np.cross(proj_world_up, proj_up)
sign_roll = np.sign(np.sum(cross_u * lens, axis=1))
dot_roll = np.clip(np.sum(proj_world_up * proj_up, axis=1), -1.0, 1.0)
roll_deg = np.degrees(np.arccos(dot_roll)) * sign_roll

# 連続性
delta_yaw_deg = np.zeros(len(anchor_df), dtype=float)
delta_pitch_deg = np.zeros(len(anchor_df), dtype=float)
delta_roll_deg = np.zeros(len(anchor_df), dtype=float)
delta_pos = np.zeros(len(anchor_df), dtype=float)
delta_lens_angle_deg = np.zeros(len(anchor_df), dtype=float)
delta_up_angle_deg = np.zeros(len(anchor_df), dtype=float)

if len(anchor_df) >= 2:
    delta_yaw_deg[1:] = _wrap_deg(np.diff(yaw_deg))
    delta_pitch_deg[1:] = np.diff(pitch_deg)
    delta_roll_deg[1:] = _wrap_deg(np.diff(roll_deg))
    delta_pos[1:] = np.linalg.norm(np.diff(centers, axis=0), axis=1)
    delta_lens_angle_deg[1:] = _angle_deg(lens[:-1], lens[1:])
    delta_up_angle_deg[1:] = _angle_deg(up[:-1], up[1:])

delta2_pos = np.zeros(len(anchor_df), dtype=float)
delta2_rot = np.zeros(len(anchor_df), dtype=float)
if len(anchor_df) >= 3:
    delta2_pos[2:] = np.linalg.norm(centers[2:] - 2.0 * centers[1:-1] + centers[:-2], axis=1)
    delta2_rot[2:] = np.sqrt(
        (delta_yaw_deg[2:] - delta_yaw_deg[1:-1]) ** 2 +
        (delta_pitch_deg[2:] - delta_pitch_deg[1:-1]) ** 2 +
        (delta_roll_deg[2:] - delta_roll_deg[1:-1]) ** 2
    )

anchor_pose_diag_df = anchor_df.copy()
anchor_pose_diag_df["yaw_deg"] = yaw_deg
anchor_pose_diag_df["pitch_deg"] = pitch_deg
anchor_pose_diag_df["roll_deg"] = roll_deg
anchor_pose_diag_df["delta_yaw_deg"] = delta_yaw_deg
anchor_pose_diag_df["delta_pitch_deg"] = delta_pitch_deg
anchor_pose_diag_df["delta_roll_deg"] = delta_roll_deg
anchor_pose_diag_df["delta_pos"] = delta_pos
anchor_pose_diag_df["delta_lens_angle_deg"] = delta_lens_angle_deg
anchor_pose_diag_df["delta_up_angle_deg"] = delta_up_angle_deg
anchor_pose_diag_df["delta2_pos"] = delta2_pos
anchor_pose_diag_df["delta2_rot"] = delta2_rot

# prev / next
anchor_pose_diag_df["prev_sequence_index"] = anchor_pose_diag_df["sequence_index"].shift(1)
anchor_pose_diag_df["next_sequence_index"] = anchor_pose_diag_df["sequence_index"].shift(-1)

diag_csv = anchor_dir / "full_anchor_pose_diag_arc.csv"
anchor_pose_diag_df.to_csv(diag_csv, index=False)

summary = {
    "persist_root": str(persist_root),
    "anchor_path": str(anchor_path),
    "rows": int(len(anchor_pose_diag_df)),
    "yaw_deg_min": float(np.nanmin(yaw_deg)),
    "yaw_deg_max": float(np.nanmax(yaw_deg)),
    "pitch_deg_min": float(np.nanmin(pitch_deg)),
    "pitch_deg_max": float(np.nanmax(pitch_deg)),
    "roll_deg_min": float(np.nanmin(roll_deg)),
    "roll_deg_max": float(np.nanmax(roll_deg)),
    "delta_pos_max": float(np.nanmax(delta_pos)),
    "delta_lens_angle_deg_max": float(np.nanmax(delta_lens_angle_deg)),
    "delta2_pos_max": float(np.nanmax(delta2_pos)),
    "delta2_rot_max": float(np.nanmax(delta2_rot)),
    "diag_csv": str(diag_csv),
}
print(summary)
display_stage_summary(
    "7-3",
    "anchor pose diag",
    inputs=[
        {"item": "camera_anchor_full", "path": str(anchor_path)},
    ],
    outputs=[
        {"item": "full_anchor_pose_diag", "path": str(diag_csv)},
    ],
    notes=[
        {"item": "rows", "value": int(len(anchor_pose_diag_df))},
        {"item": "pitch_range_deg", "value": f"{summary['pitch_deg_min']:.3f} .. {summary['pitch_deg_max']:.3f}"},
    ],
)
