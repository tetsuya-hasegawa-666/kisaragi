#7-4

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

def _find_anchor_diag_root(search_roots):
    rel = "01_anchor/full_anchor_pose_diag_arc.csv"
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
            if (d / rel).exists():
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

persist_root = _find_anchor_diag_root(search_roots)
assert persist_root is not None, {
    "error": "full_anchor_pose_diag_arc.csv not found",
    "searched_roots": [str(p) for p in search_roots if p is not None],
}

anchor_dir = persist_root / "01_anchor"
diag_path = anchor_dir / "full_anchor_pose_diag_arc.csv"
df = pd.read_csv(diag_path)
assert not df.empty, diag_path

# ---- 閾値: まずは緩め。全落ち防止 ----
MAX_DELTA_POS = float(config.get("ANCHOR_QC_MAX_DELTA_POS", 5.0))
MAX_DELTA_LENS_ANGLE_DEG = float(config.get("ANCHOR_QC_MAX_DELTA_LENS_ANGLE_DEG", 45.0))
MAX_DELTA_UP_ANGLE_DEG = float(config.get("ANCHOR_QC_MAX_DELTA_UP_ANGLE_DEG", 45.0))
MAX_DELTA2_POS = float(config.get("ANCHOR_QC_MAX_DELTA2_POS", 5.0))
MAX_DELTA2_ROT = float(config.get("ANCHOR_QC_MAX_DELTA2_ROT", 60.0))

# warning 用
WARN_ABS_ROLL_CENTERED_DEG = float(
    config.get(
        "ANCHOR_QC_WARN_ABS_ROLL_CENTERED_DEG",
        config.get("ANCHOR_QC_WARN_ABS_ROLL_DEG", 45.0),
    )
)
WARN_PITCH_MIN_DEG = float(config.get("ANCHOR_QC_WARN_PITCH_MIN_DEG", -89.0))
WARN_PITCH_MAX_DEG = float(config.get("ANCHOR_QC_WARN_PITCH_MAX_DEG", 89.0))

for col in [
    "delta_pos", "delta_lens_angle_deg", "delta_up_angle_deg",
    "delta2_pos", "delta2_rot", "roll_deg", "pitch_deg"
]:
    if col not in df.columns:
        df[col] = 0.0

if "roll_deg_raw" not in df.columns:
    df["roll_deg_raw"] = df["roll_deg"].astype(float)

if "roll_deg_centered" not in df.columns:
    roll_base = float(np.nanmedian(df["roll_deg_raw"].to_numpy(dtype=float))) if len(df) > 0 else 0.0
    df["roll_deg_centered"] = ((df["roll_deg_raw"] - roll_base + 180.0) % 360.0) - 180.0

# ---- fail: 連続性の明確な破綻だけ ----
df["fail_delta_pos"] = df["delta_pos"].abs() > MAX_DELTA_POS
df["fail_delta_lens"] = df["delta_lens_angle_deg"].abs() > MAX_DELTA_LENS_ANGLE_DEG
df["fail_delta_up"] = df["delta_up_angle_deg"].abs() > MAX_DELTA_UP_ANGLE_DEG
df["fail_delta2_pos"] = df["delta2_pos"].abs() > MAX_DELTA2_POS
df["fail_delta2_rot"] = df["delta2_rot"].abs() > MAX_DELTA2_ROT

df["anchor_qc_fail"] = (
    df["fail_delta_pos"] |
    df["fail_delta_lens"] |
    df["fail_delta_up"] |
    df["fail_delta2_pos"] |
    df["fail_delta2_rot"]
)

# ---- warning: 姿勢帯域。まだ fail に使わない ----
df["warn_roll_band"] = df["roll_deg_centered"].abs() > WARN_ABS_ROLL_CENTERED_DEG
df["warn_pitch_band"] = (df["pitch_deg"] < WARN_PITCH_MIN_DEG) | (df["pitch_deg"] > WARN_PITCH_MAX_DEG)

# 先頭フレームは差分系が 0 or NaN になりやすいので fail解除
if len(df) > 0:
    first_idx = df.index[0]
    for c in ["fail_delta_pos", "fail_delta_lens", "fail_delta_up", "fail_delta2_pos", "fail_delta2_rot", "anchor_qc_fail"]:
        df.loc[first_idx, c] = False

fail_df = df[df["anchor_qc_fail"]].copy()
warn_df = df[df["warn_roll_band"] | df["warn_pitch_band"]].copy()

qc_csv = anchor_dir / "full_anchor_pose_qc_arc.csv"
fail_csv = anchor_dir / "full_anchor_pose_qc_fail_arc.csv"
warn_csv = anchor_dir / "full_anchor_pose_qc_warn_arc.csv"

df.to_csv(qc_csv, index=False)
fail_df.to_csv(fail_csv, index=False)
warn_df.to_csv(warn_csv, index=False)

summary = {
    "anchor_qc_rows": int(len(df)),
    "fail_rows": int(len(fail_df)),
    "warn_rows": int(len(warn_df)),
    "fail_count": int(len(fail_df)),
    "warn_count": int(len(warn_df)),
    "fail_rate": float(len(fail_df) / max(len(df), 1)),
    "warn_rate": float(len(warn_df) / max(len(df), 1)),
    "max_delta_pos": float(df["delta_pos"].abs().max()),
    "max_delta_lens_angle_deg": float(df["delta_lens_angle_deg"].abs().max()),
    "max_delta_up_angle_deg": float(df["delta_up_angle_deg"].abs().max()),
    "max_delta2_pos": float(df["delta2_pos"].abs().max()),
    "max_delta2_rot": float(df["delta2_rot"].abs().max()),
    "roll_deg_min": float(df["roll_deg"].min()),
    "roll_deg_max": float(df["roll_deg"].max()),
    "roll_deg_centered_min": float(df["roll_deg_centered"].min()),
    "roll_deg_centered_max": float(df["roll_deg_centered"].max()),
    "pitch_deg_min": float(df["pitch_deg"].min()),
    "pitch_deg_max": float(df["pitch_deg"].max()),
    "qc_csv": str(qc_csv),
    "fail_csv": str(fail_csv),
    "warn_csv": str(warn_csv),
}
print(summary)
display_stage_summary(
    "7-4",
    "anchor qc",
    inputs=[
        {"item": "full_anchor_pose_diag", "path": str(diag_path)},
    ],
    outputs=[
        {"item": "full_anchor_pose_qc", "path": str(qc_csv)},
        {"item": "full_anchor_pose_fail", "path": str(fail_csv)},
        {"item": "full_anchor_pose_warn", "path": str(warn_csv)},
    ],
    notes=[
        {"item": "fail_count", "value": int(summary["fail_count"])},
        {"item": "warn_count", "value": int(summary["warn_count"])},
    ],
)
