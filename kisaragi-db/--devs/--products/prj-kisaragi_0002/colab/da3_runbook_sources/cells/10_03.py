#10-3

from pathlib import Path
import json
import numpy as np
import pandas as pd

config = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8"))
ctx = load_ctx()
persist_root = Path(ctx["probe_root"])
run_dir = persist_root / ctx.get("pipeline_slug", config.get("PIPELINE_SLUG", "da3_ngl_batch_v01"))
manifest_dir = run_dir / "manifests"
anchor_dir = persist_root / "01_anchor"

anchor_qc_path = anchor_dir / "full_anchor_pose_qc_arc.csv"
sequence_precheck_path = manifest_dir / "batch_chunk_sequence_precheck.csv"
edge_validation_path = manifest_dir / "adjacent_edge_validation.csv"

assert anchor_qc_path.exists(), anchor_qc_path
assert sequence_precheck_path.exists(), sequence_precheck_path
assert edge_validation_path.exists(), edge_validation_path

anchor_qc_df = pd.read_csv(anchor_qc_path)
sequence_df = pd.read_csv(sequence_precheck_path)
edge_df = pd.read_csv(edge_validation_path)

# centered roll を使う
if "roll_deg_centered" not in anchor_qc_df.columns:
    if "roll_deg_raw" in anchor_qc_df.columns:
        roll_base = float(np.nanmedian(anchor_qc_df["roll_deg_raw"]))
        roll_src = anchor_qc_df["roll_deg_raw"].to_numpy(float)
    else:
        roll_base = float(np.nanmedian(anchor_qc_df["roll_deg"]))
        roll_src = anchor_qc_df["roll_deg"].to_numpy(float)
    roll_centered = ((roll_src - roll_base + 180.0) % 360.0) - 180.0
    anchor_qc_df["roll_deg_centered"] = roll_centered

ROLL_CENTER_WARN_DEG = float(config.get("ANCHOR_QC_WARN_ABS_ROLL_CENTERED_DEG", 15.0))
PITCH_MIN_WARN_DEG = float(config.get("ANCHOR_QC_WARN_PITCH_MIN_DEG", -89.0))
PITCH_MAX_WARN_DEG = float(config.get("ANCHOR_QC_WARN_PITCH_MAX_DEG", 89.0))
YAW_JUMP_FAIL_DEG = float(config.get("ANCHOR_QC_MAX_DELTA_LENS_ANGLE_DEG", 45.0))

anchor_qc_df["roll_warn_centered"] = anchor_qc_df["roll_deg_centered"].abs() > ROLL_CENTER_WARN_DEG
anchor_qc_df["pitch_warn_band"] = (
    (anchor_qc_df["pitch_deg"] < PITCH_MIN_WARN_DEG) |
    (anchor_qc_df["pitch_deg"] > PITCH_MAX_WARN_DEG)
)
anchor_qc_df["yaw_jump_fail"] = anchor_qc_df["delta_lens_angle_deg"].abs() > YAW_JUMP_FAIL_DEG

bad_sequence_chunk_count = int((~sequence_df["is_monotonic"]).sum() + sequence_df["has_duplicate_sequence"].sum() + (sequence_df["bad_gap_count"] > 0).sum())

# edge_df の chunk単位 fail 数をゆるく集計
edge_fail_cols = [c for c in edge_df.columns if c.endswith("_fail") or c.endswith("_error")]
if "chunk_name" in edge_df.columns:
    if edge_fail_cols:
        tmp = edge_df.copy()
        row_bad = np.zeros(len(tmp), dtype=bool)
        for c in edge_fail_cols:
            if tmp[c].dtype == bool:
                row_bad |= tmp[c].fillna(False).to_numpy()
        bad_edge_chunk_count = int(tmp.loc[row_bad, "chunk_name"].nunique())
    else:
        bad_edge_chunk_count = 0
else:
    bad_edge_chunk_count = 0

summary = {
    "anchor_qc": {
        "row_count": int(len(anchor_qc_df)),
        "fail_count": int(anchor_qc_df["anchor_qc_fail"].sum()) if "anchor_qc_fail" in anchor_qc_df.columns else 0,
        "roll_warn_centered_count": int(anchor_qc_df["roll_warn_centered"].sum()),
        "pitch_warn_count": int(anchor_qc_df["pitch_warn_band"].sum()),
        "yaw_jump_fail_count": int(anchor_qc_df["yaw_jump_fail"].sum()),
    },
    "bad_sequence_chunk_count": int(bad_sequence_chunk_count),
    "bad_edge_chunk_count": int(bad_edge_chunk_count),
}

summary_path = manifest_dir / "batch_preflight_summary.json"
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(summary, ensure_ascii=False, indent=2))
display_stage_summary(
    "10-3",
    "batch preflight summary",
    inputs=[
        {"item": "anchor_qc", "path": str(anchor_qc_path)},
        {"item": "sequence_precheck", "path": str(sequence_precheck_path)},
        {"item": "edge_validation", "path": str(edge_validation_path)},
    ],
    outputs=[
        {"item": "batch_preflight_summary", "path": str(summary_path)},
    ],
    notes=[
        {"item": "bad_sequence_chunk_count", "value": int(summary["bad_sequence_chunk_count"])},
        {"item": "bad_edge_chunk_count", "value": int(summary["bad_edge_chunk_count"])},
    ],
)
