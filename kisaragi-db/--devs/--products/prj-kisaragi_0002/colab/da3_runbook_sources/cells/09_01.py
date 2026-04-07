#9-1
from pathlib import Path
import csv
import json

import imageio.v3 as iio
import numpy as np
import pandas as pd
from PIL import Image

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
images_dir = Path(ctx["images_dir"])
frame_record_path = Path(ctx["frame_record_path"])
frame_pose_index_path = Path(ctx["frame_pose_index_path"])
manifest_dir = Path(ctx["manifest_dir"])

CANONICAL_ORIENTATION_POLICY = "upright_rot90cw_from_correcting"
BLUR_THRESHOLD = 8.0

with frame_record_path.open("r", encoding="utf-8") as f:
    frame_records = [json.loads(line) for line in f if line.strip()]

frame_pose_df = pd.read_csv(frame_pose_index_path) if frame_pose_index_path.exists() else pd.DataFrame()
image_name_by_record_index = {}
if len(frame_pose_df) > 0:
    image_name_col = next((c for c in ["image_file_name", "imageFileName", "frame_name"] if c in frame_pose_df.columns), None)
    record_index_col = next((c for c in ["pose_record_index", "record_index"] if c in frame_pose_df.columns), None)
    if image_name_col is not None and record_index_col is not None:
        tmp = frame_pose_df[[record_index_col, image_name_col]].copy()
        tmp = tmp.dropna()
        tmp[image_name_col] = tmp[image_name_col].astype(str).str.strip()
        tmp = tmp.loc[tmp[image_name_col] != ""]
        image_name_by_record_index = {
            int(getattr(row, record_index_col)): getattr(row, image_name_col)
            for row in tmp.itertuples(index=False)
        }
    elif "frame_index" in frame_pose_df.columns:
        sorted_image_names = sorted([
            *[p.name for p in images_dir.glob("*.jpg")],
            *[p.name for p in images_dir.glob("*.jpeg")],
            *[p.name for p in images_dir.glob("*.png")],
            *[p.name for p in images_dir.glob("*.JPG")],
            *[p.name for p in images_dir.glob("*.JPEG")],
            *[p.name for p in images_dir.glob("*.PNG")],
        ])
        record_index_col = next((c for c in ["pose_record_index", "record_index"] if c in frame_pose_df.columns), None)
        if record_index_col is not None:
            for row in frame_pose_df.itertuples(index=False):
                frame_idx = int(getattr(row, "frame_index"))
                if 0 <= frame_idx < len(sorted_image_names):
                    image_name_by_record_index[int(getattr(row, record_index_col))] = sorted_image_names[frame_idx]

def ranked_image_dirs(primary_dir: Path, frame_record_path: Path):
    session_outer = frame_record_path.parent
    session_root = session_outer / "trajectreview" if (session_outer / "trajectreview").exists() else session_outer
    candidates = [
        primary_dir,
        session_root / "images",
        session_root / "image",
        session_outer / "images",
        session_outer / "image",
        session_outer / "trajectreview" / "images",
        session_outer / "trajectreview" / "image",
    ]
    ranked = []
    seen = set()
    for p in candidates:
        key = str(p)
        if key in seen or not p.exists():
            continue
        seen.add(key)
        image_count = (
            len(list(p.glob("*.jpg"))) +
            len(list(p.glob("*.jpeg"))) +
            len(list(p.glob("*.png"))) +
            len(list(p.glob("*.JPG"))) +
            len(list(p.glob("*.JPEG"))) +
            len(list(p.glob("*.PNG")))
        )
        ranked.append((p, image_count))
    return sorted(ranked, key=lambda x: (-x[1], len(str(x[0]))))

def lap_var(image_path: Path) -> float:
    img = iio.imread(image_path)
    if img.ndim == 3:
        gray = img[..., :3].mean(axis=2).astype(np.float32)
    else:
        gray = img.astype(np.float32)
    gx = gray[:, 1:] - gray[:, :-1]
    gy = gray[1:, :] - gray[:-1, :]
    return float(np.var(gx) + np.var(gy))

def read_actual_wh(image_path: Path):
    with Image.open(image_path) as img:
        width, height = img.size
    return int(width), int(height)

def normalize_intrinsics_to_upright(intr, actual_width: int, actual_height: int):
    fx = intr.get("fx")
    fy = intr.get("fy")
    cx = intr.get("cx")
    cy = intr.get("cy")
    intr_width = intr.get("width")
    intr_height = intr.get("height")

    if None in [fx, fy, cx, cy, intr_width, intr_height]:
        return {
            "intrinsics_case": "missing_intrinsics",
            "rotation_applied_deg": None,
            "fx_canonical": None,
            "fy_canonical": None,
            "cx_canonical": None,
            "cy_canonical": None,
            "width_canonical": None,
            "height_canonical": None,
        }

    fx = float(fx)
    fy = float(fy)
    cx = float(cx)
    cy = float(cy)
    intr_width = int(intr_width)
    intr_height = int(intr_height)

    if intr_width == actual_width and intr_height == actual_height:
        return {
            "intrinsics_case": "already_upright",
            "rotation_applied_deg": 0,
            "fx_canonical": fx,
            "fy_canonical": fy,
            "cx_canonical": cx,
            "cy_canonical": cy,
            "width_canonical": actual_width,
            "height_canonical": actual_height,
        }

    if intr_width == actual_height and intr_height == actual_width:
        return {
            "intrinsics_case": "rot90cw_intrinsics_fixed",
            "rotation_applied_deg": 90,
            "fx_canonical": fy,
            "fy_canonical": fx,
            "cx_canonical": float(intr_height - 1) - cy,
            "cy_canonical": cx,
            "width_canonical": actual_width,
            "height_canonical": actual_height,
        }

    return {
        "intrinsics_case": "dimension_mismatch",
        "rotation_applied_deg": None,
        "fx_canonical": None,
        "fy_canonical": None,
        "cx_canonical": None,
        "cy_canonical": None,
        "width_canonical": None,
        "height_canonical": None,
    }

image_dir_ranking = ranked_image_dirs(images_dir, frame_record_path)
resolved_images_dir = image_dir_ranking[0][0]
rows = []
for rec in sorted(frame_records, key=lambda x: int(x.get("frameTimestampNs", 0))):
    image_name = str(rec.get("imageFileName", "") or "").strip()
    if not image_name:
        record_index = rec.get("recordIndex")
        if record_index is not None:
            image_name = str(image_name_by_record_index.get(int(record_index), "")).strip()
    image_path = resolved_images_dir / image_name if image_name else None
    image_exists = bool(image_name) and image_path.exists()
    intr = rec.get("imageIntrinsics") or {}
    pose = rec.get("pose") or {}
    blur_score = lap_var(image_path) if image_exists else None
    actual_width = None
    actual_height = None
    intr_norm = {
        "intrinsics_case": "image_missing",
        "rotation_applied_deg": None,
        "fx_canonical": None,
        "fy_canonical": None,
        "cx_canonical": None,
        "cy_canonical": None,
        "width_canonical": None,
        "height_canonical": None,
    }
    if image_exists:
        actual_width, actual_height = read_actual_wh(image_path)
        intr_norm = normalize_intrinsics_to_upright(intr, actual_width, actual_height)
    rows.append({
        "session_id": rec.get("sessionId"),
        "record_index": rec.get("recordIndex"),
        "frame_timestamp_ns": rec.get("frameTimestampNs"),
        "capture_timestamp_ns": rec.get("captureTimestampNs"),
        "tracking_state": rec.get("trackingState"),
        "image_file_name": image_name,
        "image_path": str(image_path) if image_path else "",
        "resolved_images_dir": str(resolved_images_dir),
        "image_name_source": "frame_record" if str(rec.get("imageFileName", "") or "").strip() else "frame_pose_index_fallback",
        "image_exists": image_exists,
        "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
        "actual_width": actual_width,
        "actual_height": actual_height,
        "fx": intr.get("fx"),
        "fy": intr.get("fy"),
        "cx": intr.get("cx"),
        "cy": intr.get("cy"),
        "width": intr.get("width"),
        "height": intr.get("height"),
        "intrinsics_case": intr_norm["intrinsics_case"],
        "rotation_applied_deg": intr_norm["rotation_applied_deg"],
        "fx_canonical": intr_norm["fx_canonical"],
        "fy_canonical": intr_norm["fy_canonical"],
        "cx_canonical": intr_norm["cx_canonical"],
        "cy_canonical": intr_norm["cy_canonical"],
        "width_canonical": intr_norm["width_canonical"],
        "height_canonical": intr_norm["height_canonical"],
        "tx": pose.get("tx"),
        "ty": pose.get("ty"),
        "tz": pose.get("tz"),
        "qx": pose.get("qx"),
        "qy": pose.get("qy"),
        "qz": pose.get("qz"),
        "qw": pose.get("qw"),
        "blur_score": blur_score,
    })

manifest_df = pd.DataFrame(rows)
manifest_df.to_csv(manifest_dir / "input_frame_manifest.csv", index=False, encoding="utf-8")

qc_df = manifest_df.copy()
qc_df["qc_tracking_ok"] = qc_df["tracking_state"].fillna("") == "TRACKING"
qc_df["qc_image_ok"] = qc_df["image_exists"].fillna(False)
qc_df["qc_orientation_ok"] = qc_df["intrinsics_case"].isin(["already_upright", "rot90cw_intrinsics_fixed"])
qc_df["qc_intrinsics_ok"] = qc_df[["fx_canonical", "fy_canonical", "cx_canonical", "cy_canonical", "width_canonical", "height_canonical"]].notna().all(axis=1)
qc_df["qc_pose_ok"] = qc_df[["tx", "ty", "tz", "qx", "qy", "qz", "qw"]].notna().all(axis=1)
qc_df["blur_score"] = pd.to_numeric(qc_df["blur_score"], errors="coerce")
qc_df["qc_blur_ok"] = qc_df["blur_score"].fillna(0.0).ge(BLUR_THRESHOLD).infer_objects(copy=False)
qc_df["qc_pass"] = qc_df[["qc_tracking_ok", "qc_image_ok", "qc_orientation_ok", "qc_intrinsics_ok", "qc_pose_ok"]].all(axis=1)
qc_df["skip_reason"] = ""
qc_df.loc[~qc_df["qc_tracking_ok"], "skip_reason"] = "tracking_not_ok"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_image_ok"], "skip_reason"] = "image_missing"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_orientation_ok"], "skip_reason"] = "orientation_mismatch"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_intrinsics_ok"], "skip_reason"] = "intrinsics_missing"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_pose_ok"], "skip_reason"] = "pose_missing"
qc_df.to_csv(manifest_dir / "input_frame_qc.csv", index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)

def quat_to_rot(qx, qy, qz, qw):
    xx, yy, zz = qx*qx, qy*qy, qz*qz
    xy, xz, yz = qx*qy, qx*qz, qy*qz
    wx, wy, wz = qw*qx, qw*qy, qw*qz
    return np.array([
        [1 - 2*(yy + zz), 2*(xy - wz), 2*(xz + wy)],
        [2*(xy + wz), 1 - 2*(xx + zz), 2*(yz - wx)],
        [2*(xz - wy), 2*(yz + wx), 1 - 2*(xx + yy)],
    ], dtype=np.float32)

def pose_to_w2c(row):
    R_c2w = quat_to_rot(float(row.qx), float(row.qy), float(row.qz), float(row.qw))
    t_c2w = np.array([float(row.tx), float(row.ty), float(row.tz)], dtype=np.float32)
    R_w2c = R_c2w.T
    t_w2c = -R_w2c @ t_c2w
    out = np.eye(4, dtype=np.float32)
    out[:3, :3] = R_w2c
    out[:3, 3] = t_w2c
    return out

def build_K(row):
    return np.array([
        [float(row.fx_canonical), 0.0, float(row.cx_canonical)],
        [0.0, float(row.fy_canonical), float(row.cy_canonical)],
        [0.0, 0.0, 1.0],
    ], dtype=np.float32)

adopt_df = qc_df.loc[qc_df["qc_pass"]].copy().sort_values("frame_timestamp_ns").reset_index(drop=True)
if len(adopt_df) < 2:
    fail_counts = {
        "frame_record_count": int(len(qc_df)),
        "qc_pass_count": int(len(adopt_df)),
        "tracking_not_ok": int((~qc_df["qc_tracking_ok"]).sum()),
        "image_missing": int((~qc_df["qc_image_ok"]).sum()),
        "orientation_mismatch": int((~qc_df["qc_orientation_ok"]).sum()),
        "intrinsics_missing": int((~qc_df["qc_intrinsics_ok"]).sum()),
        "pose_missing": int((~qc_df["qc_pose_ok"]).sum()),
        "blur_low_diag_only": int((~qc_df["qc_blur_ok"]).sum()),
        "skip_reason_counts": qc_df["skip_reason"].value_counts(dropna=False).to_dict(),
    }
    (manifest_dir / "qc_failure_summary.json").write_text(json.dumps(fail_counts, indent=2, ensure_ascii=False), encoding="utf-8")
    raise AssertionError(fail_counts)

adopted_rows = []
last_t = None
last_R = None
for row in adopt_df.itertuples(index=False):
    t = np.array([float(row.tx), float(row.ty), float(row.tz)], dtype=np.float32)
    R = quat_to_rot(float(row.qx), float(row.qy), float(row.qz), float(row.qw))
    baseline = None if last_t is None else float(np.linalg.norm(t - last_t))
    rot_delta = None if last_R is None else float(np.degrees(np.arccos(np.clip((np.trace(last_R.T @ R) - 1.0) / 2.0, -1.0, 1.0))))
    geometric_adopt = last_t is None or (baseline >= 0.05) or (rot_delta is not None and rot_delta >= 3.0)
    blur_boost = bool(row.qc_blur_ok) if pd.notna(row.qc_blur_ok) else False
    adopt = geometric_adopt or (last_t is None and blur_boost)
    adopted_rows.append({
        **row._asdict(),
        "baseline_from_prev_adopted_m": baseline,
        "rotation_from_prev_adopted_deg": rot_delta,
        "geometric_adopt": geometric_adopt,
        "anchor_input_adopted": adopt,
        "anchor_input_skip_reason": "" if adopt else "baseline_small",
    })
    if adopt:
        last_t = t
        last_R = R

anchor_input_df = pd.DataFrame(adopted_rows)
anchor_input_df.to_csv(manifest_dir / "pose_conversion_check.csv", index=False, encoding="utf-8")

selected_df = anchor_input_df.loc[anchor_input_df["anchor_input_adopted"]].copy().reset_index(drop=True)
assert len(selected_df) >= 2, {"selected_df": len(selected_df)}

Ks = np.stack([build_K(row) for row in selected_df.itertuples(index=False)], axis=0)
exts = np.stack([pose_to_w2c(row) for row in selected_df.itertuples(index=False)], axis=0)
np.save(manifest_dir / "intrinsics.npy", Ks)
np.save(manifest_dir / "extrinsics_w2c_arc.npy", exts)
selected_df.to_csv(manifest_dir / "da3_input_manifest.csv", index=False, encoding="utf-8")

k_check = selected_df[[
    "image_file_name",
    "canonical_orientation_policy",
    "intrinsics_case",
    "rotation_applied_deg",
    "width",
    "height",
    "actual_width",
    "actual_height",
    "width_canonical",
    "height_canonical",
    "fx",
    "fy",
    "cx",
    "cy",
    "fx_canonical",
    "fy_canonical",
    "cx_canonical",
    "cy_canonical",
]].copy()
k_check["resize_mode"] = "native"
k_check.to_csv(manifest_dir / "k_resize_check.csv", index=False, encoding="utf-8")

orientation_summary = {
    "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
    "already_upright_count": int((manifest_df["intrinsics_case"] == "already_upright").sum()),
    "rot90cw_intrinsics_fixed_count": int((manifest_df["intrinsics_case"] == "rot90cw_intrinsics_fixed").sum()),
    "dimension_mismatch_count": int((manifest_df["intrinsics_case"] == "dimension_mismatch").sum()),
    "image_missing_count": int((manifest_df["intrinsics_case"] == "image_missing").sum()),
}
(manifest_dir / "orientation_summary.json").write_text(json.dumps(orientation_summary, indent=2, ensure_ascii=False), encoding="utf-8")

summary = {
    "frame_record_count": int(len(manifest_df)),
    "qc_pass_count": int(len(adopt_df)),
    "qc_skip_count": int((~qc_df["qc_pass"]).sum()),
    "resolved_images_dir": str(resolved_images_dir),
    "resolved_images_dir_file_count": int(image_dir_ranking[0][1]),
    "frame_pose_index_path": str(frame_pose_index_path),
    "frame_pose_fallback_mapping_count": int(len(image_name_by_record_index)),
    "selected_count": int(len(selected_df)),
    "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
    "intrinsics_path": str(manifest_dir / "intrinsics.npy"),
    "extrinsics_path": str(manifest_dir / "extrinsics_w2c_arc.npy"),
    "orientation_summary_path": str(manifest_dir / "orientation_summary.json"),
}
extrinsics_source_summary = {
    "artifact": "extrinsics_w2c_arc.npy",
    "artifact_path": str(manifest_dir / "extrinsics_w2c_arc.npy"),
    "generated_by": "section_9_1.pose_to_w2c",
    "source_record_path": str(frame_record_path),
    "source_fields": ["pose.tx", "pose.ty", "pose.tz", "pose.qx", "pose.qy", "pose.qz", "pose.qw"],
    "source_sort_key": "frameTimestampNs",
    "matrix_space": "world_to_camera",
    "record_count": int(len(selected_df)),
}
(manifest_dir / "qc_summary.json").write_text(json.dumps({
    "frame_record_count": summary["frame_record_count"],
    "qc_pass_count": summary["qc_pass_count"],
    "qc_skip_count": summary["qc_skip_count"],
    "frame_record_path": str(frame_record_path),
    "images_dir": str(images_dir),
    "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
}, indent=2, ensure_ascii=False), encoding="utf-8")
(manifest_dir / "da3_input_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
(manifest_dir / "extrinsics_w2c_arc_source_summary.json").write_text(json.dumps(extrinsics_source_summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
display_stage_summary(
    "9-1",
    "record-native manifest rebuild",
    inputs=[
        {"item": "frame_record", "path": str(frame_record_path)},
        {"item": "images_dir", "path": str(images_dir)},
        {"item": "frame_pose_index", "path": str(frame_pose_index_path)},
    ],
    outputs=[
        {"item": "input_frame_manifest", "path": str(manifest_dir / "input_frame_manifest.csv")},
        {"item": "input_frame_qc", "path": str(manifest_dir / "input_frame_qc.csv")},
        {"item": "pose_conversion_check", "path": str(manifest_dir / "pose_conversion_check.csv")},
        {"item": "da3_input_manifest", "path": str(manifest_dir / "da3_input_manifest.csv")},
        {"item": "intrinsics", "path": str(manifest_dir / "intrinsics.npy")},
        {"item": "extrinsics_w2c", "path": str(manifest_dir / "extrinsics_w2c_arc.npy")},
        {"item": "orientation_summary", "path": str(manifest_dir / "orientation_summary.json")},
        {"item": "da3_input_summary", "path": str(manifest_dir / "da3_input_summary.json")},
    ],
    notes=[
        {"item": "extrinsics_source_rule", "value": "frame_record pose(tx,ty,tz,qx,qy,qz,qw) -> pose_to_w2c -> extrinsics_w2c_arc.npy"},
    ],
)
