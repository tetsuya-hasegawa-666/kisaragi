# DA3 Colab Ref Runbook

- `da3_colab_evid_runbook.md` の貼り付け用 companion とする。
- 更新は必ず `da3_colab_evid_runbook.md` と 2 file set で行う。
- canonical input は `session_manifest.json`、`frame_record.jsonl`、`trajectreview/image` または `trajectreview/images` とする。
- canonical route は `MRL-10 record-native DA3 route` とし、`proof route` と `production route` を分離する。
- `MRL-10` の `MetricLarge route` は image-only 推論、`Giant route` は `DA3NESTED-GIANT-LARGE-1.1` と `debug_gs_readback` bundle を現行 living spec とする。
- canonical image は `correcting` 側で `90度右回転` 済みの upright JPEG を受け取る前提とする。
- `Colab` 側は image pixel を再回転しない。
- `Block 1` では実画像の `width` / `height` と `frame_record.jsonl` の `imageIntrinsics` を照合し、legacy session だけ `K` を `90度右回転` の式で補正する。
- `correcting` input が `trajectreview-correcting-session-YYYYMMDD-HHMMSS.zip` の時、modeling bundle zip は `trajectreview-modeling-session-YYYYMMDD-HHMMSS_<model_slug>.zip` として `MyDrive/trajectreview/modeling` へ保存する。
- binary `gs_ply` は text viewer で文字化けするため、runbook は `debug_gs_visible_copy/` に header、property stats、focus stats、`xyz_only.ply` を複製し、bundle zip に同梱する。

## 実行順

1. `準備確認 1-4`
2. `install 1-4`
3. `MRL-10 Block 1`
4. `MRL-10 Block 2`
5. 必要時のみ `MRL-10 Block 3`
6. 必要時のみ `MRL-10 Block 4`

## 準備確認 1

```python
import os
from pathlib import Path
import torch
from google.colab import drive

drive.mount("/content/drive", force_remount=True)

print("cwd", os.getcwd())
print("cuda_available", torch.cuda.is_available())
print("drive_exists", Path("/content/drive").exists())
print("mydrive_exists", Path("/content/drive/MyDrive").exists())
print("shortcut_root_exists", Path("/content/drive/.shortcut-targets-by-id").exists())
```

## 準備確認 2

```python
from pathlib import Path
import json

shortcut_root = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_")
scan_roots = [
    shortcut_root / "trajectreview",
    Path("/content/drive/MyDrive/trajectreview"),
]
results_root_candidates = [
    Path("/content/drive/MyDrive/trajectreview/modeling"),
    shortcut_root / "trajectreview" / "modeling",
]
results_root = next((p for p in results_root_candidates if p.exists()), results_root_candidates[0])
candidate_doc_path = Path("/content/runbook_drive_candidates.json")

def infer_session_id(path: Path) -> str:
    return path.stem if path.suffix.lower() == ".zip" else path.name

zip_map = {}
dir_map = {}
for root in scan_roots:
    if not root.exists():
        continue
    for zip_path in sorted(root.rglob("*.zip")):
        stat = zip_path.stat()
        key = (infer_session_id(zip_path), stat.st_size)
        zip_map[key] = {
            "kind": "zip",
            "session_id": infer_session_id(zip_path),
            "label": f"{infer_session_id(zip_path)} [zip]",
            "path": str(zip_path),
            "size_bytes": stat.st_size,
        }
    for manifest_path in sorted(root.rglob("session_manifest.json")):
        session_dir = manifest_path.parent
        dir_map[infer_session_id(session_dir)] = {
            "kind": "dir",
            "session_id": infer_session_id(session_dir),
            "label": f"{infer_session_id(session_dir)} [dir]",
            "path": str(session_dir),
        }

candidate_doc = {
    "results_root": str(results_root),
    "candidate_count": len(zip_map) + len(dir_map),
    "candidates": sorted(list(zip_map.values()) + list(dir_map.values()), key=lambda x: (x["session_id"], x["kind"], x["path"])),
}
candidate_doc_path.write_text(json.dumps(candidate_doc, indent=2, ensure_ascii=False), encoding="utf-8")
print("candidate_doc_path", candidate_doc_path)
print("results_root", results_root)
print("candidate_count", candidate_doc["candidate_count"])
for idx, item in enumerate(candidate_doc["candidates"]):
    print(f"[{idx}] {item['label']}: {item['path']}")
```

## 準備確認 3

```python
from pathlib import Path
import json
import ipywidgets as widgets
from IPython.display import display

candidate_doc = json.loads(Path("/content/runbook_drive_candidates.json").read_text(encoding="utf-8"))
selected_doc_path = Path("/content/runbook_selected_input.json")
options = [(f"[{idx}] {item['label']}", idx) for idx, item in enumerate(candidate_doc["candidates"])]
dropdown = widgets.Dropdown(options=options, description="input", layout=widgets.Layout(width="95%"))
button = widgets.Button(description="selected input を保存", button_style="success")
output = widgets.Output()

def on_click(_):
    selected = candidate_doc["candidates"][dropdown.value]
    selected_doc = {
        "selected_index": dropdown.value,
        "kind": selected["kind"],
        "session_id": selected["session_id"],
        "label": selected["label"],
        "path": selected["path"],
        "results_root": candidate_doc["results_root"],
    }
    selected_doc_path.write_text(json.dumps(selected_doc, indent=2, ensure_ascii=False), encoding="utf-8")
    with output:
        output.clear_output()
        print(json.dumps(selected_doc, indent=2, ensure_ascii=False))
        print("selected_exists", Path(selected["path"]).exists())

button.on_click(on_click)
display(dropdown, button, output)
```

## 準備確認 4

```python
from pathlib import Path
import json

selected_doc = json.loads(Path("/content/runbook_selected_input.json").read_text(encoding="utf-8"))
print("selected_path_exists", Path(selected_doc["path"]).exists(), selected_doc["path"])
print("results_root", selected_doc["results_root"])
```

## install 1

```python
from pathlib import Path
import shutil
import subprocess

repo_root = Path("/content/Depth-Anything-3")
if repo_root.exists():
    shutil.rmtree(repo_root)
subprocess.run(["git", "clone", "https://github.com/ByteDance-Seed/Depth-Anything-3.git", str(repo_root)], check=True)
print("repo_exists", repo_root.exists(), repo_root)
```

## install 2

```python
import subprocess
subprocess.run(["python", "-m", "pip", "install", "--quiet", "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile", "trimesh", "gsplat", "e3nn"], check=True)
print("dependency_install_ok")
```

## install 3

```python
import sys
from pathlib import Path

repo_root = Path("/content/Depth-Anything-3")
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from depth_anything_3.api import DepthAnything3
import gsplat
import e3nn

print("depth_anything_3_import_ok", DepthAnything3)
print("gsplat_version", getattr(gsplat, "__version__", "unknown"))
print("e3nn_version", getattr(e3nn, "__version__", "unknown"))
```

## install 4

```python
import inspect
from depth_anything_3.api import DepthAnything3

print("inference_sig", inspect.signature(DepthAnything3.inference))
```

## MRL-10 Block 1

```python
from pathlib import Path
import json
import shutil
import zipfile

selected_doc = json.loads(Path("/content/runbook_selected_input.json").read_text(encoding="utf-8"))
selected_path = Path(selected_doc["path"])
selected_kind = selected_doc["kind"]
session_id = selected_doc["session_id"]
results_root = Path(selected_doc["results_root"])

extract_root = Path("/content/trajectreview_input")
if extract_root.exists():
    shutil.rmtree(extract_root)
extract_root.mkdir(parents=True, exist_ok=True)

if selected_kind == "zip":
    with zipfile.ZipFile(selected_path, "r") as zf:
        zf.extractall(extract_root)
else:
    shutil.copytree(selected_path, extract_root / selected_path.name)

session_manifest_hits = sorted(extract_root.rglob("session_manifest.json"))
if session_manifest_hits:
    session_outer = session_manifest_hits[0].parent
else:
    pkg_hits = sorted(extract_root.rglob("session_package.json"))
    assert pkg_hits, f"session_manifest.json or session_package.json not found under {extract_root}"
    session_outer = pkg_hits[0].parent.parent if pkg_hits[0].parent.name == "trajectreview" else pkg_hits[0].parent

session_root = session_outer / "trajectreview" if (session_outer / "trajectreview").exists() else session_outer

image_dir_candidates = [
    session_root / "images",
    session_root / "image",
    session_outer / "images",
    session_outer / "image",
]
source_images_dir = next((p for p in image_dir_candidates if p.exists()), None)
assert source_images_dir is not None, {"image_dir_candidates": [str(p) for p in image_dir_candidates]}

images_dir = session_root / "images"
if source_images_dir != images_dir:
    if images_dir.exists():
        shutil.rmtree(images_dir)
    shutil.copytree(source_images_dir, images_dir)

frame_record_candidates = [
    session_outer / "frame_record.jsonl",
    session_root / "frame_record.jsonl",
    session_root / "arcore_pose.jsonl",
    session_outer / "arcore_pose.jsonl",
]
frame_record_path = next((p for p in frame_record_candidates if p.exists()), None)
assert frame_record_path is not None, {"frame_record_candidates": [str(p) for p in frame_record_candidates]}

frame_pose_index_path = session_root / "frame_pose_index.csv"
probe_root = results_root / f"{session_id}_da3_record_route_v01"
proof_metric_dir = probe_root / "proof_metriclarge"
prod_metric_dir = probe_root / "prod_metriclarge"
proof_giant_dir = probe_root / "proof_giant"
world_dir = probe_root / "world_fusion_v01"
manifest_dir = probe_root / "manifests"
modeling_session_id = session_id.replace("trajectreview-correcting-session-", "trajectreview-modeling-session-", 1) if session_id.startswith("trajectreview-correcting-session-") else f"trajectreview-modeling-session-{session_id}"

for p in [probe_root, proof_metric_dir, prod_metric_dir, proof_giant_dir, world_dir, manifest_dir]:
    p.mkdir(parents=True, exist_ok=True)

context_doc = {
    "session_id": session_id,
    "modeling_session_id": modeling_session_id,
    "selected_kind": selected_kind,
    "selected_path": str(selected_path),
    "results_root": str(results_root),
    "session_outer": str(session_outer),
    "session_root": str(session_root),
    "images_dir": str(images_dir),
    "frame_record_path": str(frame_record_path),
    "frame_pose_index_path": str(frame_pose_index_path),
    "probe_root": str(probe_root),
    "proof_metric_dir": str(proof_metric_dir),
    "prod_metric_dir": str(prod_metric_dir),
    "proof_giant_dir": str(proof_giant_dir),
    "world_dir": str(world_dir),
    "manifest_dir": str(manifest_dir),
}
Path("/content/runbook_session_context.json").write_text(json.dumps(context_doc, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(context_doc, indent=2, ensure_ascii=False))
```

## MRL-10 Phase B

```python
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
manifest_dir = Path(ctx["manifest_dir"])

CANONICAL_ORIENTATION_POLICY = "upright_rot90cw_from_correcting"
BLUR_THRESHOLD = 8.0

with frame_record_path.open("r", encoding="utf-8") as f:
    frame_records = [json.loads(line) for line in f if line.strip()]

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

rows = []
for rec in sorted(frame_records, key=lambda x: int(x.get("frameTimestampNs", 0))):
    image_name = str(rec.get("imageFileName", "")).strip()
    image_path = images_dir / image_name if image_name else None
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
qc_df["qc_blur_ok"] = qc_df["blur_score"].fillna(0.0) >= BLUR_THRESHOLD
qc_df["qc_pass"] = qc_df[["qc_tracking_ok", "qc_image_ok", "qc_orientation_ok", "qc_intrinsics_ok", "qc_pose_ok", "qc_blur_ok"]].all(axis=1)
qc_df["skip_reason"] = ""
qc_df.loc[~qc_df["qc_tracking_ok"], "skip_reason"] = "tracking_not_ok"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_image_ok"], "skip_reason"] = "image_missing"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_orientation_ok"], "skip_reason"] = "orientation_mismatch"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_intrinsics_ok"], "skip_reason"] = "intrinsics_missing"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_pose_ok"], "skip_reason"] = "pose_missing"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_blur_ok"], "skip_reason"] = "blur_low"
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
assert len(adopt_df) >= 2, {"qc_pass_count": len(adopt_df)}

adopted_rows = []
last_t = None
last_R = None
for row in adopt_df.itertuples(index=False):
    t = np.array([float(row.tx), float(row.ty), float(row.tz)], dtype=np.float32)
    R = quat_to_rot(float(row.qx), float(row.qy), float(row.qz), float(row.qw))
    baseline = None if last_t is None else float(np.linalg.norm(t - last_t))
    rot_delta = None if last_R is None else float(np.degrees(np.arccos(np.clip((np.trace(last_R.T @ R) - 1.0) / 2.0, -1.0, 1.0))))
    adopt = last_t is None or (baseline >= 0.05) or (rot_delta is not None and rot_delta >= 3.0)
    adopted_rows.append({
        **row._asdict(),
        "baseline_from_prev_adopted_m": baseline,
        "rotation_from_prev_adopted_deg": rot_delta,
        "prod_adopted": adopt,
        "prod_skip_reason": "" if adopt else "baseline_small",
    })
    if adopt:
        last_t = t
        last_R = R

prod_df = pd.DataFrame(adopted_rows)
prod_df.to_csv(manifest_dir / "pose_conversion_check.csv", index=False, encoding="utf-8")

prod_selected = prod_df.loc[prod_df["prod_adopted"]].copy().reset_index(drop=True)
proof_selected = prod_selected.head(min(24, len(prod_selected))).copy()
assert len(proof_selected) >= 2, {"proof_selected": len(proof_selected)}

for name, df in [("proof", proof_selected), ("prod", prod_selected)]:
    Ks = np.stack([build_K(row) for row in df.itertuples(index=False)], axis=0)
    exts = np.stack([pose_to_w2c(row) for row in df.itertuples(index=False)], axis=0)
    np.save(manifest_dir / f"intrinsics_{name}.npy", Ks)
    np.save(manifest_dir / f"extrinsics_w2c_{name}.npy", exts)
    df.to_csv(manifest_dir / f"da3_input_manifest_{name}.csv", index=False, encoding="utf-8")

k_check = prod_selected[[
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
    "prod_selected_count": int(len(prod_selected)),
    "proof_selected_count": int(len(proof_selected)),
    "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
    "proof_intrinsics_path": str(manifest_dir / "intrinsics_proof.npy"),
    "proof_extrinsics_path": str(manifest_dir / "extrinsics_w2c_proof.npy"),
    "prod_intrinsics_path": str(manifest_dir / "intrinsics_prod.npy"),
    "prod_extrinsics_path": str(manifest_dir / "extrinsics_w2c_prod.npy"),
    "orientation_summary_path": str(manifest_dir / "orientation_summary.json"),
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
print(json.dumps(summary, indent=2, ensure_ascii=False))
```

## MRL-10 Block 2

```python
from pathlib import Path
import json

import numpy as np
import pandas as pd
import torch
from PIL import Image
from depth_anything_3.api import DepthAnything3

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
manifest_dir = Path(ctx["manifest_dir"])
proof_metric_dir = Path(ctx["proof_metric_dir"])
prod_metric_dir = Path(ctx["prod_metric_dir"])
world_dir = Path(ctx["world_dir"])

proof_df = pd.read_csv(manifest_dir / "da3_input_manifest_proof.csv")
proof_images = proof_df["image_path"].tolist()
proof_intrinsics = np.load(manifest_dir / "intrinsics_proof.npy")
proof_extrinsics = np.load(manifest_dir / "extrinsics_w2c_proof.npy")

prod_df = pd.read_csv(manifest_dir / "da3_input_manifest_prod.csv")
prod_images = prod_df["image_path"].tolist()
prod_intrinsics = np.load(manifest_dir / "intrinsics_prod.npy")
prod_extrinsics = np.load(manifest_dir / "extrinsics_w2c_prod.npy")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = DepthAnything3.from_pretrained("depth-anything/DA3METRIC-LARGE").to(device=device)
proof_prediction = model.inference(
    image=proof_images,
    infer_gs=False,
    process_res=504,
    export_dir=str(proof_metric_dir),
    export_format="mini_npz-depth_vis",
)
prod_prediction = model.inference(
    image=prod_images,
    infer_gs=False,
    process_res=504,
    export_dir=str(prod_metric_dir),
    export_format="mini_npz-depth_vis",
)

depths = np.asarray(prod_prediction.depth)
assert depths is not None and len(depths) == len(prod_df), {
    "depth_count": None if depths is None else len(depths),
    "prod_selected_count": len(prod_df),
}
all_points = []
per_frame = []
stride = 24
for idx, row in enumerate(prod_df.itertuples(index=False)):
    depth = np.asarray(depths[idx]).astype(np.float32)
    K = prod_intrinsics[idx]
    w2c = prod_extrinsics[idx]
    c2w = np.linalg.inv(w2c)
    h, w = depth.shape
    grid_y, grid_x = np.mgrid[0:h:stride, 0:w:stride]
    z = depth[grid_y, grid_x]
    valid = np.isfinite(z) & (z > 0.0)
    if not np.any(valid):
        continue
    px = grid_x[valid].astype(np.float32)
    py = grid_y[valid].astype(np.float32)
    zz = z[valid].astype(np.float32)
    x = (px - K[0, 2]) * zz / K[0, 0]
    y = (py - K[1, 2]) * zz / K[1, 1]
    cam = np.stack([x, y, zz], axis=-1)
    cam_h = np.concatenate([cam, np.ones((len(cam), 1), dtype=np.float32)], axis=1)
    world = (c2w @ cam_h.T).T[:, :3]
    all_points.append(world)
    per_frame.append({"image_file_name": row.image_file_name, "point_count": int(len(world))})

assert all_points, "no world points generated"
merged = np.concatenate(all_points, axis=0).astype(np.float32)
np.save(world_dir / "world_points_multiframe.npy", merged)

with (world_dir / "world_points_multiframe.ply").open("w", encoding="utf-8") as f:
    f.write("ply\nformat ascii 1.0\n")
    f.write(f"element vertex {len(merged)}\n")
    f.write("property float x\nproperty float y\nproperty float z\n")
    f.write("end_header\n")
    for p in merged:
        f.write(f"{p[0]} {p[1]} {p[2]}\n")

sample = merged[::4] if len(merged) > 4000 else merged
mins = sample.min(axis=0)
maxs = sample.max(axis=0)
norm = (sample - mins) / np.maximum(maxs - mins, 1e-6)
preview = np.zeros((800, 800, 3), dtype=np.uint8)
px = np.clip((norm[:, 0] * 799).astype(int), 0, 799)
py = np.clip((norm[:, 1] * 799).astype(int), 0, 799)
preview[799 - py, px] = 255
Image.fromarray(preview).save(world_dir / "world_points_multiframe_preview.png")

proof_summary = {
    "route": "MetricLarge-proof",
    "image_count": len(proof_images),
    "proof_metric_dir": str(proof_metric_dir),
    "prediction_type": str(type(proof_prediction).__name__),
    "da3_camera_input_mode": "image_only",
    "canonical_orientation_policy": str(proof_df["canonical_orientation_policy"].iloc[0]),
    "intrinsics_case_counts": proof_df["intrinsics_case"].value_counts().to_dict(),
}
prod_summary = {
    "route": "MetricLarge-production",
    "image_count": len(prod_images),
    "prod_metric_dir": str(prod_metric_dir),
    "prediction_type": str(type(prod_prediction).__name__),
    "da3_camera_input_mode": "image_only",
    "canonical_orientation_policy": str(prod_df["canonical_orientation_policy"].iloc[0]),
    "intrinsics_case_counts": prod_df["intrinsics_case"].value_counts().to_dict(),
}
world_summary = {
    "route": "MetricLarge-production-world",
    "processed_frames": len(per_frame),
    "total_points": int(len(merged)),
    "stride": stride,
    "depth_source": "prod_prediction.depth",
    "world_projection_input_mode": "frame_record_intrinsics_and_pose",
    "canonical_orientation_policy": str(prod_df["canonical_orientation_policy"].iloc[0]),
}
(proof_metric_dir / "export_summary.json").write_text(json.dumps(proof_summary, indent=2, ensure_ascii=False), encoding="utf-8")
(prod_metric_dir / "export_summary.json").write_text(json.dumps(prod_summary, indent=2, ensure_ascii=False), encoding="utf-8")
(world_dir / "export_summary.json").write_text(json.dumps(world_summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({
    "proof_image_count": proof_summary["image_count"],
    "prod_image_count": prod_summary["image_count"],
    "processed_frames": world_summary["processed_frames"],
    "total_points": world_summary["total_points"],
}, indent=2, ensure_ascii=False))
```

## MRL-10 Block 3

```python
from pathlib import Path
import json
import sys
import shutil

import numpy as np
import pandas as pd
import torch
from plyfile import PlyData

for name in list(sys.modules.keys()):
    if name.startswith("depth_anything_3"):
        del sys.modules[name]

repo_root = Path("/content/Depth-Anything-3")
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from depth_anything_3.api import DepthAnything3

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
manifest_dir = Path(ctx["manifest_dir"])
proof_giant_dir = Path(ctx["proof_giant_dir"])
probe_root = Path(ctx["probe_root"])
results_root = Path(ctx["results_root"])
modeling_session_id = ctx["modeling_session_id"]

proof_df = pd.read_csv(manifest_dir / "da3_input_manifest_proof.csv")
proof_images = proof_df["image_path"].tolist()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = DepthAnything3.from_pretrained("depth-anything/DA3NESTED-GIANT-LARGE-1.1").to(device=device)

PROCESS_RES = 1008
REF_VIEW_STRATEGY = "middle"
CONF_THRESH_PERCENTILE = 25.0
NUM_MAX_POINTS = 1250000

prediction = model.inference(
    image=proof_images,
    infer_gs=True,
    process_res=PROCESS_RES,
    ref_view_strategy=REF_VIEW_STRATEGY,
    export_dir=str(proof_giant_dir),
    export_format="npz-glb-gs_ply-gs_video",
    conf_thresh_percentile=CONF_THRESH_PERCENTILE,
    num_max_points=NUM_MAX_POINTS,
)

proof_df.to_csv(proof_giant_dir / "proof_gs_input_frames.csv", index=False, encoding="utf-8")

generated = []
for p in sorted(proof_giant_dir.rglob("*")):
    if p.is_file():
        generated.append({
            "relative_path": str(p.relative_to(proof_giant_dir)),
            "size_bytes": int(p.stat().st_size),
        })

generated_df = pd.DataFrame(generated)
generated_df.to_csv(proof_giant_dir / "generated_files_debug.csv", index=False, encoding="utf-8")

gs_related = generated_df[
    generated_df["relative_path"].str.contains(r"(?:^gs_|/gs_|\.glb$|\.ply$|proof_gs_input_frames\.csv)", regex=True)
].copy()
gs_related.to_csv(proof_giant_dir / "generated_gs_related_files_debug.csv", index=False, encoding="utf-8")

gs_ply_path = proof_giant_dir / "gs_ply" / "0000.ply"
debug_read_dir = proof_giant_dir / "debug_gs_readback"
debug_visible_dir = proof_giant_dir / "debug_gs_visible_copy"
debug_read_dir.mkdir(parents=True, exist_ok=True)
debug_visible_dir.mkdir(parents=True, exist_ok=True)

if gs_ply_path.exists():
    with open(gs_ply_path, "rb") as f:
        head = f.read(8192).decode("latin1", errors="ignore")
    (debug_read_dir / "0000_header.txt").write_text(head, encoding="utf-8")
    shutil.copy2(debug_read_dir / "0000_header.txt", debug_visible_dir / "0000_header.txt")

    ply = PlyData.read(str(gs_ply_path))
    v = ply["vertex"]
    names = list(v.data.dtype.names)

    rows = []
    for name in names:
        arr = np.asarray(v[name])
        rec = {"property": name, "shape": str(arr.shape), "dtype": str(arr.dtype)}
        if np.issubdtype(arr.dtype, np.number):
            finite = np.isfinite(arr)
            rec["finite_count"] = int(finite.sum())
            rec["total_count"] = int(arr.size)
            if finite.any():
                af = arr[finite]
                rec["min"] = float(af.min())
                rec["max"] = float(af.max())
                rec["mean"] = float(af.mean())
        rows.append(rec)
    pd.DataFrame(rows).to_csv(debug_read_dir / "0000_property_stats.csv", index=False, encoding="utf-8")
    shutil.copy2(debug_read_dir / "0000_property_stats.csv", debug_visible_dir / "0000_property_stats.csv")

    xyz = np.stack([np.asarray(v["x"]), np.asarray(v["y"]), np.asarray(v["z"])], axis=1)
    xyz_mask = np.isfinite(xyz).all(axis=1)
    with open(debug_read_dir / "0000_xyz_only.ply", "w", encoding="utf-8") as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {int(xyz_mask.sum())}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("end_header\n")
        for p in xyz[xyz_mask]:
            f.write(f"{p[0]} {p[1]} {p[2]}\n")
    shutil.copy2(debug_read_dir / "0000_xyz_only.ply", debug_visible_dir / "0000_xyz_only.ply")

    focus_cols = [n for n in names if any(k in n.lower() for k in ["scale", "opacity", "rot", "quaternion"])]
    focus_rows = []
    for name in focus_cols:
        arr = np.asarray(v[name])
        finite = np.isfinite(arr)
        rec = {"property": name, "finite_count": int(finite.sum()), "total_count": int(arr.size)}
        if finite.any():
            af = arr[finite]
            rec["min"] = float(af.min())
            rec["max"] = float(af.max())
            rec["mean"] = float(af.mean())
        focus_rows.append(rec)
    pd.DataFrame(focus_rows).to_csv(debug_read_dir / "0000_focus_stats.csv", index=False, encoding="utf-8")
    shutil.copy2(debug_read_dir / "0000_focus_stats.csv", debug_visible_dir / "0000_focus_stats.csv")

bundle_model_slug = "giant"
drive_bundle_base = f"{modeling_session_id}_{bundle_model_slug}"
drive_bundle_dir = results_root / drive_bundle_base
drive_bundle_zip = results_root / f"{drive_bundle_base}.zip"

if drive_bundle_dir.exists():
    shutil.rmtree(drive_bundle_dir)
drive_bundle_dir.mkdir(parents=True, exist_ok=True)

bundle_file_count = 0
for src in sorted(probe_root.rglob("*")):
    if not src.is_file():
        continue
    dst = drive_bundle_dir / src.relative_to(probe_root)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    bundle_file_count += 1

if drive_bundle_zip.exists():
    drive_bundle_zip.unlink()
shutil.make_archive(str(drive_bundle_zip.with_suffix("")), "zip", root_dir=str(drive_bundle_dir))

summary = {
    "route": "Giant-proof-da3-estimated-pose",
    "image_count": len(proof_images),
    "proof_giant_dir": str(proof_giant_dir),
    "prediction_type": str(type(prediction).__name__),
    "camera_pose_source": "da3_estimated",
    "model_id": "depth-anything/DA3NESTED-GIANT-LARGE-1.1",
    "process_res": PROCESS_RES,
    "ref_view_strategy": REF_VIEW_STRATEGY,
    "conf_thresh_percentile": CONF_THRESH_PERCENTILE,
    "num_max_points": NUM_MAX_POINTS,
    "generated_file_count": int(len(generated_df)),
    "generated_gs_related_file_count": int(len(gs_related)),
    "generated_files_manifest": str(proof_giant_dir / "generated_files_debug.csv"),
    "generated_gs_related_manifest": str(proof_giant_dir / "generated_gs_related_files_debug.csv"),
    "debug_gs_readback_dir": str(debug_read_dir),
    "debug_gs_visible_copy_dir": str(debug_visible_dir),
    "drive_bundle_dir": str(drive_bundle_dir),
    "drive_bundle_zip": str(drive_bundle_zip),
    "drive_bundle_file_count": int(bundle_file_count),
    "canonical_orientation_policy": str(proof_df["canonical_orientation_policy"].iloc[0]),
    "intrinsics_case_counts": proof_df["intrinsics_case"].value_counts().to_dict(),
}
(proof_giant_dir / "export_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
print("\n# gs_related_files")
print(gs_related.to_string(index=False))
```

## MRL-10 Block 4

```python
from pathlib import Path
import json
from google.colab import files
import shutil

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
results_root = Path(ctx["results_root"])
modeling_session_id = ctx["modeling_session_id"]

bundle_model_slug = "giant"
drive_bundle_base = f"{modeling_session_id}_{bundle_model_slug}"
drive_bundle_zip = results_root / f"{drive_bundle_base}.zip"
local_bundle_zip = Path("/content") / f"{drive_bundle_base}.zip"

assert drive_bundle_zip.exists(), drive_bundle_zip
shutil.copy2(drive_bundle_zip, local_bundle_zip)
print("drive_bundle_zip", drive_bundle_zip)
print("local_bundle_zip", local_bundle_zip)
files.download(str(local_bundle_zip))
```
