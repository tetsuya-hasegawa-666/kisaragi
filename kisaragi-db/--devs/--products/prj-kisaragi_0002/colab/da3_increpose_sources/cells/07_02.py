#7-2

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

def _find_manifest_triplet(search_roots):
    rels = [
        ("manifests/da3_input_manifest.csv", "manifests/intrinsics.npy", "manifests/extrinsics_w2c_arc.npy"),
        ("00_config/da3_input_manifest.csv", "00_config/intrinsics.npy", "00_config/extrinsics_w2c_arc.npy"),
    ]
    for root in search_roots:
        if root is None:
            continue
        root = Path(root)
        if root.is_file():
            root = root.parent
        if not root.exists():
            continue

        # root 自体と配下を少し探索
        candidate_dirs = [root]
        candidate_dirs += [p for p in root.glob("*") if p.is_dir()]
        candidate_dirs += [p for p in root.glob("*/*") if p.is_dir()]

        seen = set()
        for d in candidate_dirs:
            d = d.resolve()
            if str(d) in seen:
                continue
            seen.add(str(d))
            for a, b, c in rels:
                pa = d / a
                pb = d / b
                pc = d / c
                if pa.exists() and pb.exists() and pc.exists():
                    return d, pa, pb, pc
    return None, None, None, None

# まず config から探索起点を集める
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

persist_root, input_manifest_path, intrinsics_path, extrinsics_path = _find_manifest_triplet(search_roots)

assert persist_root is not None, {
    "error": "manifest triplet not found",
    "searched_roots": [str(p) for p in search_roots if p is not None],
    "expected_files": [
        "manifests/da3_input_manifest.csv",
        "manifests/intrinsics.npy",
        "manifests/extrinsics_w2c_arc.npy",
    ],
}

anchor_dir = persist_root / "01_anchor"
manifest_dir = input_manifest_path.parent
anchor_dir.mkdir(parents=True, exist_ok=True)

manifest_df = pd.read_csv(input_manifest_path)
intrinsics = np.load(intrinsics_path)
extrinsics_w2c = np.load(extrinsics_path)

assert len(manifest_df) > 0, "da3_input_manifest.csv is empty"
assert extrinsics_w2c.ndim == 3 and extrinsics_w2c.shape[1:] == (4, 4), extrinsics_w2c.shape
assert len(manifest_df) == extrinsics_w2c.shape[0], {
    "manifest_rows": len(manifest_df),
    "extrinsics_rows": int(extrinsics_w2c.shape[0]),
}
assert intrinsics.ndim == 3 and intrinsics.shape[1:] == (3, 3), intrinsics.shape
assert intrinsics.shape[0] == len(manifest_df), {
    "manifest_rows": len(manifest_df),
    "intrinsics_rows": int(intrinsics.shape[0]),
}

# c2w
c2w = np.linalg.inv(extrinsics_w2c)

# camera center / basis
camera_centers = c2w[:, :3, 3]
right_vecs = c2w[:, :3, 0]
up_vecs = c2w[:, :3, 1]
lens_vecs = -c2w[:, :3, 2]

def _normalize_rows(x: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n = np.linalg.norm(x, axis=1, keepdims=True)
    n = np.maximum(n, eps)
    return x / n

right_vecs = _normalize_rows(right_vecs)
up_vecs = _normalize_rows(up_vecs)
lens_vecs = _normalize_rows(lens_vecs)

# sequence_index
if "frame_timestamp_ns" in manifest_df.columns:
    ts_col = "frame_timestamp_ns"
elif "timestamp_ns" in manifest_df.columns:
    ts_col = "timestamp_ns"
elif "timestamp" in manifest_df.columns:
    ts_col = "timestamp"
else:
    ts_col = None

if "sequence_index" not in manifest_df.columns:
    if ts_col is not None:
        manifest_df = manifest_df.sort_values(ts_col, kind="stable").reset_index(drop=True)
    else:
        manifest_df = manifest_df.reset_index(drop=True)
    manifest_df["sequence_index"] = np.arange(len(manifest_df), dtype=np.int64)
else:
    manifest_df = manifest_df.sort_values("sequence_index", kind="stable").reset_index(drop=True)

camera_center_df = pd.DataFrame({
    "record_index": manifest_df["record_index"].astype(int),
    "sequence_index": manifest_df["sequence_index"].astype(int),
    "cam_cx": camera_centers[:, 0],
    "cam_cy": camera_centers[:, 1],
    "cam_cz": camera_centers[:, 2],
    "cx_world": camera_centers[:, 0],
    "cy_world": camera_centers[:, 1],
    "cz_world": camera_centers[:, 2],
})

camera_orientation_df = pd.DataFrame({
    "record_index": manifest_df["record_index"].astype(int),
    "sequence_index": manifest_df["sequence_index"].astype(int),
    "right_x": right_vecs[:, 0],
    "right_y": right_vecs[:, 1],
    "right_z": right_vecs[:, 2],
    "up_x": up_vecs[:, 0],
    "up_y": up_vecs[:, 1],
    "up_z": up_vecs[:, 2],
    "lens_x": lens_vecs[:, 0],
    "lens_y": lens_vecs[:, 1],
    "lens_z": lens_vecs[:, 2],
})

camera_anchor_full_df = manifest_df.copy()
camera_anchor_full_df["cam_cx"] = camera_centers[:, 0]
camera_anchor_full_df["cam_cy"] = camera_centers[:, 1]
camera_anchor_full_df["cam_cz"] = camera_centers[:, 2]
camera_anchor_full_df["cx_world"] = camera_centers[:, 0]
camera_anchor_full_df["cy_world"] = camera_centers[:, 1]
camera_anchor_full_df["cz_world"] = camera_centers[:, 2]
camera_anchor_full_df["right_x"] = right_vecs[:, 0]
camera_anchor_full_df["right_y"] = right_vecs[:, 1]
camera_anchor_full_df["right_z"] = right_vecs[:, 2]
camera_anchor_full_df["up_x"] = up_vecs[:, 0]
camera_anchor_full_df["up_y"] = up_vecs[:, 1]
camera_anchor_full_df["up_z"] = up_vecs[:, 2]
camera_anchor_full_df["anchor_up_x"] = up_vecs[:, 0]
camera_anchor_full_df["anchor_up_y"] = up_vecs[:, 1]
camera_anchor_full_df["anchor_up_z"] = up_vecs[:, 2]
camera_anchor_full_df["lens_x"] = lens_vecs[:, 0]
camera_anchor_full_df["lens_y"] = lens_vecs[:, 1]
camera_anchor_full_df["lens_z"] = lens_vecs[:, 2]
camera_anchor_full_df["anchor_lens_x"] = lens_vecs[:, 0]
camera_anchor_full_df["anchor_lens_y"] = lens_vecs[:, 1]
camera_anchor_full_df["anchor_lens_z"] = lens_vecs[:, 2]
for r in range(4):
    for c in range(4):
        camera_anchor_full_df[f"w2c_{r}{c}"] = extrinsics_w2c[:, r, c]

camera_matrix_full_csv = anchor_dir / "camera_matrix_full_arc.csv"
camera_center_matrix_csv = anchor_dir / "camera_center_matrix_arc.csv"
camera_orientation_full_csv = anchor_dir / "camera_orientation_full_arc.csv"
camera_anchor_full_csv = anchor_dir / "camera_anchor_full_arc.csv"

pd.DataFrame(
    extrinsics_w2c.reshape(extrinsics_w2c.shape[0], -1),
    columns=[f"w2c_{r}{c}" for r in range(4) for c in range(4)]
).assign(
    record_index=manifest_df["record_index"].astype(int),
    sequence_index=manifest_df["sequence_index"].astype(int),
).to_csv(camera_matrix_full_csv, index=False)

camera_center_df.to_csv(camera_center_matrix_csv, index=False)
camera_orientation_df.to_csv(camera_orientation_full_csv, index=False)
camera_anchor_full_df.to_csv(camera_anchor_full_csv, index=False)

np.save(anchor_dir / "extrinsics_w2c_arc.npy", extrinsics_w2c)
np.save(anchor_dir / "intrinsics.npy", intrinsics)
np.save(anchor_dir / "c2w_arc.npy", c2w)

print({
    "persist_root": str(persist_root),
    "manifest_dir": str(manifest_dir),
    "rows": len(manifest_df),
    "camera_matrix_full_csv": str(camera_matrix_full_csv),
    "camera_center_matrix_csv": str(camera_center_matrix_csv),
    "camera_orientation_full_csv": str(camera_orientation_full_csv),
    "camera_anchor_full_csv": str(camera_anchor_full_csv),
})
display_stage_summary(
    "7-2",
    "full anchor build",
    inputs=[
        {"item": "da3_input_manifest", "path": str(input_manifest_path)},
        {"item": "intrinsics", "path": str(intrinsics_path)},
        {"item": "extrinsics_w2c", "path": str(extrinsics_path)},
        {"item": "extrinsics_w2c_source_summary", "path": str(manifest_dir / "extrinsics_w2c_arc_source_summary.json")},
    ],
    outputs=[
        {"item": "camera_matrix_full", "path": str(camera_matrix_full_csv)},
        {"item": "camera_center_matrix", "path": str(camera_center_matrix_csv)},
        {"item": "camera_orientation_full", "path": str(camera_orientation_full_csv)},
        {"item": "camera_anchor_full", "path": str(camera_anchor_full_csv)},
        {"item": "anchor_extrinsics_w2c", "path": str(anchor_dir / "extrinsics_w2c_arc.npy")},
        {"item": "anchor_intrinsics", "path": str(anchor_dir / "intrinsics.npy")},
        {"item": "anchor_c2w", "path": str(anchor_dir / "c2w_arc.npy")},
    ],
    notes=[
        {"item": "row_count", "value": int(len(manifest_df))},
        {"item": "matrix_source", "value": "manifests/extrinsics_w2c_arc.npy を c2w へ反転し basis / center を再構成"},
    ],
)
