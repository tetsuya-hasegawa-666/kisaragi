# DA3 Colab Evid Runbook

## 文書の役割

- `Colab` modeling の canonical runbook とする。
- canonical input は `session_manifest.json`、`frame_record.jsonl`、`trajectreview/image` または `trajectreview/images` とする。
- `frame_pose_index.csv` は診断用、`arcore_pose.jsonl` は fallback とする。
- canonical route は `MRL-10 record-native DA3 route` とし、`proof route` と `production route` を分離する。
- `1 record = image + pose + intrinsics + timestamp` の構造を `Colab` 側で壊さないことを最優先とする。

## Route Policy

- `proof route`
  - QC 通過後の subset を使って短く壊れ方を見る。
  - 既定では `baseline thinning` 後の先頭 `24` frame までを使う。
- `production route`
  - QC 通過した全 record を主対象にする。
  - 固定枚数 cap は置かない。
  - thinning は `skip reason` を残す時だけ許可する。
- record-native canonical route では常に
  - `image[]`
  - `intrinsics[N,3,3]`
  - `extrinsics_w2c[N,4,4]`
  を manifest として生成する。
- `DA3Metric-Large` は現行 upstream 制約により image-only 推論とし、`intrinsics` / `extrinsics_w2c` は world projection と評価証跡に使う。
- `Giant` proof living route は `DA3NESTED-GIANT-LARGE-1.1`、`da3_estimated pose`、`debug_gs_readback` bundle を canonical とする。

## Orientation Policy

- canonical image は `correcting` 側で `90度右回転` 済みの upright JPEG を受け取る前提とする。
- `Colab` 側は image pixel を再回転しない。
- `Block 1` では、実画像の `width` / `height` と `frame_record.jsonl` の `imageIntrinsics` を照合し、すでに upright ならそのまま使う。
- legacy session のように intrinsics だけ raw 向きで `width` / `height` が swap している時は、`90度右回転` の式で `fx` / `fy` / `cx` / `cy` を canonical upright 基準へ補正する。
- 上記の判定結果は `input_frame_manifest.csv`、`k_resize_check.csv`、`orientation_summary.json` に残す。

## Bundle Naming Policy

- `correcting` 側の canonical zip 名は `trajectreview/correcting/trajectreview-correcting-session-YYYYMMDD-HHMMSS.zip` とする。
- `modeling` 側の bundle zip 名は `trajectreview/modeling/trajectreview-modeling-session-YYYYMMDD-HHMMSS_<model_slug>.zip` とする。
- `Colab` runbook では `selected input` の `session_id` が `trajectreview-correcting-session-*` なら、bundle 出力時に `trajectreview-modeling-session-*` へ置き換えて使う。
- binary `gs_ply` は text viewer で文字化けするため、runbook は header、property stats、focus stats、`xyz_only.ply` を `debug_gs_visible_copy/` と bundle zip に同梱する。

## 実行順

1. `準備確認 1-4`
2. `install 1-4`
3. `MRL-10 Block 1`
4. `MRL-10 Block 2`
5. 必要時のみ `MRL-10 Block 3`
6. 必要時のみ `MRL-10 Block 4`
7. 必要時のみ `MRL-10 Block 5` を `RUN_BATCH_INDEX` を変えながら繰り返す
   - 例: `0`, `1`, `2`, `3` ...
   - 1 回の `Block 5` で `3chunk` だけ処理する
8. 最後に `MRL-10 Block 6`

## 準備確認

### 準備確認 1

```python
#1
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

### 準備確認 2

```python
#2
from pathlib import Path
import json

shortcut_root = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_")
scan_roots = [
    shortcut_root / "trajectreview",
    Path("/content/drive/MyDrive/trajectreview"),
]
results_root = Path("/content/drive/MyDrive/trajectreview/modeling")
results_root.mkdir(parents=True, exist_ok=True)
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
    "results_root_visibility": "google_drive_mydrive_visible",
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

### 準備確認 3

```python
#3
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

### 準備確認 4

```python
#4
from pathlib import Path
import json

selected_doc = json.loads(Path("/content/runbook_selected_input.json").read_text(encoding="utf-8"))
print("selected_path_exists", Path(selected_doc["path"]).exists(), selected_doc["path"])
print("results_root", selected_doc["results_root"])
print("results_root_visible_on_drive_ui", str(selected_doc["results_root"]).startswith("/content/drive/MyDrive/"))
```

## install

### install 1

```python
#5
from pathlib import Path
import shutil
import subprocess

repo_root = Path("/content/Depth-Anything-3")
if repo_root.exists():
    shutil.rmtree(repo_root)
subprocess.run(["git", "clone", "https://github.com/ByteDance-Seed/Depth-Anything-3.git", str(repo_root)], check=True)
print("repo_exists", repo_root.exists(), repo_root)
```

### install 2

```python
#6
import subprocess
subprocess.run(["python", "-m", "pip", "install", "--quiet", "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile", "trimesh", "gsplat", "e3nn"], check=True)
print("dependency_install_ok")
```

### install 3

```python
#7
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

### install 4

```python
#8
import inspect
from depth_anything_3.api import DepthAnything3

print("inference_sig", inspect.signature(DepthAnything3.inference))
```

## MRL-10 record-native DA3 route

### Block 1: 正規化 + QC + DA3 input pack

```python
#9
from pathlib import Path
import json
import shutil
import zipfile

selected_doc = json.loads(Path("/content/runbook_selected_input.json").read_text(encoding="utf-8"))
selected_path = Path(selected_doc["path"])
selected_kind = selected_doc["kind"]
session_id = selected_doc["session_id"]
results_root = Path(selected_doc["results_root"])
assert str(results_root).startswith("/content/drive/MyDrive/"), results_root
results_root.mkdir(parents=True, exist_ok=True)

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
route_slug = "da3_record_route_v01"
modeling_session_id = session_id.replace("trajectreview-correcting-session-", "trajectreview-modeling-session-", 1) if session_id.startswith("trajectreview-correcting-session-") else f"trajectreview-modeling-session-{session_id}"
probe_root_name = f"{modeling_session_id}_{route_slug}"
probe_root = results_root / probe_root_name
proof_metric_dir = probe_root / "proof_metriclarge"
prod_metric_dir = probe_root / "prod_metriclarge"
proof_giant_dir = probe_root / "proof_giant"
world_dir = probe_root / "world_fusion_v01"
manifest_dir = probe_root / "manifests"

for p in [probe_root, proof_metric_dir, prod_metric_dir, proof_giant_dir, world_dir, manifest_dir]:
    p.mkdir(parents=True, exist_ok=True)

context_doc = {
    "session_id": session_id,
    "modeling_session_id": modeling_session_id,
    "selected_kind": selected_kind,
    "selected_path": str(selected_path),
    "results_root": str(results_root),
    "results_root_visibility": "google_drive_mydrive_visible",
    "route_slug": route_slug,
    "probe_root_name": probe_root_name,
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

### Phase B: QC と manifest 化

```python
#10
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

### Block 2: MetricLarge proof + production + world export

```python
#11
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import torch
from PIL import Image
ctx_path = Path("/content/runbook_session_context.json")
assert ctx_path.exists(), ctx_path
ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
manifest_dir = Path(ctx["manifest_dir"])
proof_metric_dir = Path(ctx["proof_metric_dir"])
prod_metric_dir = Path(ctx["prod_metric_dir"])
world_dir = Path(ctx["world_dir"])

repo_root = Path("/content/Depth-Anything-3")
src_root = repo_root / "src"
assert repo_root.exists(), repo_root
assert src_root.exists(), src_root
assert (src_root / "depth_anything_3" / "api.py").exists(), src_root / "depth_anything_3" / "api.py"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))
for name in list(sys.modules.keys()):
    if name.startswith("depth_anything_3"):
        del sys.modules[name]

from depth_anything_3.api import DepthAnything3

required_dirs = [manifest_dir, proof_metric_dir, prod_metric_dir, world_dir]
for p in required_dirs:
    p.mkdir(parents=True, exist_ok=True)

required_files = {
    "proof_manifest": manifest_dir / "da3_input_manifest_proof.csv",
    "prod_manifest": manifest_dir / "da3_input_manifest_prod.csv",
    "proof_intrinsics": manifest_dir / "intrinsics_proof.npy",
    "proof_extrinsics": manifest_dir / "extrinsics_w2c_proof.npy",
    "prod_intrinsics": manifest_dir / "intrinsics_prod.npy",
    "prod_extrinsics": manifest_dir / "extrinsics_w2c_prod.npy",
}
for key, path in required_files.items():
    assert path.exists(), {key: str(path)}

proof_df = pd.read_csv(required_files["proof_manifest"])
prod_df = pd.read_csv(required_files["prod_manifest"])
assert not proof_df.empty, "proof manifest empty"
assert not prod_df.empty, "prod manifest empty"

required_columns = {
    "image_path",
    "image_file_name",
    "canonical_orientation_policy",
    "intrinsics_case",
}
assert required_columns.issubset(proof_df.columns), {
    "missing_in_proof": sorted(required_columns - set(proof_df.columns))
}
assert required_columns.issubset(prod_df.columns), {
    "missing_in_prod": sorted(required_columns - set(prod_df.columns))
}

proof_images = proof_df["image_path"].tolist()
prod_images = prod_df["image_path"].tolist()
assert len(proof_images) >= 2, {"proof_image_count": len(proof_images)}
assert len(prod_images) >= 2, {"prod_image_count": len(prod_images)}

for label, image_paths in [("proof", proof_images), ("prod", prod_images)]:
    missing = [p for p in image_paths if not Path(p).exists()]
    assert not missing, {f"{label}_missing_images_head": missing[:10], f"{label}_missing_count": len(missing)}

proof_intrinsics = np.load(required_files["proof_intrinsics"])
proof_extrinsics = np.load(required_files["proof_extrinsics"])
prod_intrinsics = np.load(required_files["prod_intrinsics"])
prod_extrinsics = np.load(required_files["prod_extrinsics"])

assert proof_intrinsics.shape == (len(proof_df), 3, 3), {
    "proof_intrinsics_shape": tuple(proof_intrinsics.shape),
    "proof_count": len(proof_df),
}
assert proof_extrinsics.shape[0] == len(proof_df), {
    "proof_extrinsics_shape": tuple(proof_extrinsics.shape),
    "proof_count": len(proof_df),
}
assert prod_intrinsics.shape == (len(prod_df), 3, 3), {
    "prod_intrinsics_shape": tuple(prod_intrinsics.shape),
    "prod_count": len(prod_df),
}
assert prod_extrinsics.shape[0] == len(prod_df), {
    "prod_extrinsics_shape": tuple(prod_extrinsics.shape),
    "prod_count": len(prod_df),
}

preflight = {
    "ctx_path": str(ctx_path),
    "repo_root": str(repo_root),
    "manifest_dir": str(manifest_dir),
    "proof_metric_dir": str(proof_metric_dir),
    "prod_metric_dir": str(prod_metric_dir),
    "world_dir": str(world_dir),
    "proof_image_count": len(proof_images),
    "prod_image_count": len(prod_images),
    "proof_intrinsics_shape": list(proof_intrinsics.shape),
    "proof_extrinsics_shape": list(proof_extrinsics.shape),
    "prod_intrinsics_shape": list(prod_intrinsics.shape),
    "prod_extrinsics_shape": list(prod_extrinsics.shape),
}
(manifest_dir / "metriclarge_block2_preflight.json").write_text(json.dumps(preflight, indent=2, ensure_ascii=False), encoding="utf-8")

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
assert np.isfinite(prod_intrinsics).all(), "prod intrinsics has non-finite value"
assert np.isfinite(prod_extrinsics).all(), "prod extrinsics has non-finite value"

all_points = []
per_frame = []
skipped_frames = []
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
        skipped_frames.append({"image_file_name": row.image_file_name, "reason": "no_valid_depth"})
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
    "skipped_frames": skipped_frames,
    "total_points": int(len(merged)),
    "stride": stride,
    "depth_source": "prod_prediction.depth",
    "world_projection_input_mode": "frame_record_intrinsics_and_pose",
    "canonical_orientation_policy": str(prod_df["canonical_orientation_policy"].iloc[0]),
    "npy_path": str(world_dir / "world_points_multiframe.npy"),
    "ply_path": str(world_dir / "world_points_multiframe.ply"),
}
(proof_metric_dir / "export_summary.json").write_text(json.dumps(proof_summary, indent=2, ensure_ascii=False), encoding="utf-8")
(prod_metric_dir / "export_summary.json").write_text(json.dumps(prod_summary, indent=2, ensure_ascii=False), encoding="utf-8")
(world_dir / "export_summary.json").write_text(json.dumps(world_summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({
    "preflight_path": str(manifest_dir / "metriclarge_block2_preflight.json"),
    "proof_image_count": proof_summary["image_count"],
    "prod_image_count": prod_summary["image_count"],
    "processed_frames": world_summary["processed_frames"],
    "total_points": world_summary["total_points"],
    "world_dir": str(world_dir),
}, indent=2, ensure_ascii=False))
```

### Block 3: Continuous GS bootstrap + batch plan

```python
#12
from pathlib import Path
import gc
import json
import math
import sys

import numpy as np
import pandas as pd
import torch

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
probe_root = Path(ctx["probe_root"])

pipeline_root = probe_root / "continuous_gs_v05_chunk3_sequential"
global_pose_dir = pipeline_root / "global_pose_bootstrap"
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
merged_dir = pipeline_root / "merged"

for p in [pipeline_root, global_pose_dir, chunk_manifest_dir, chunk_runs_dir, merged_dir]:
    p.mkdir(parents=True, exist_ok=True)

MODEL_ID = "depth-anything/DA3NESTED-GIANT-LARGE-1.1"
BUNDLE_MODEL_SLUG = "".join(ch.lower() for ch in MODEL_ID.split("/")[-1] if ch.isalnum()).replace("da3nested", "")
PROCESS_RES = 504
CHUNK_SIZE = 3
STEP = 3
ADOPT_SIZE = 3
CHUNKS_PER_BATCH = 3
BOOTSTRAP_EXPORT_FORMAT = "npz"
BOOTSTRAP_INFER_GS = False

config = {
    "MODEL_ID": MODEL_ID,
    "BUNDLE_MODEL_SLUG": BUNDLE_MODEL_SLUG,
    "PROCESS_RES": PROCESS_RES,
    "CHUNK_SIZE": CHUNK_SIZE,
    "STEP": STEP,
    "ADOPT_SIZE": ADOPT_SIZE,
    "CHUNKS_PER_BATCH": CHUNKS_PER_BATCH,
    "BOOTSTRAP_EXPORT_FORMAT": BOOTSTRAP_EXPORT_FORMAT,
    "BOOTSTRAP_INFER_GS": BOOTSTRAP_INFER_GS,
}
(pipeline_root / "pipeline_config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

prod_df = pd.read_csv(manifest_dir / "da3_input_manifest_prod.csv").reset_index(drop=True)
assert len(prod_df) >= 2, {"prod_frame_count": len(prod_df)}

chunks = []
start_pos = 0
chunk_id = 0
while start_pos < len(prod_df):
    end_pos = min(start_pos + CHUNK_SIZE, len(prod_df))
    chunk_df = prod_df.iloc[start_pos:end_pos].copy().reset_index(drop=True)
    if len(chunk_df) < 2:
        break

    chunk_name = f"chunk_{chunk_id:04d}_{start_pos:05d}_{end_pos-1:05d}"
    chunk_df["chunk_local_index"] = range(len(chunk_df))
    chunk_df["is_adopted_region"] = chunk_df["chunk_local_index"] < min(ADOPT_SIZE, len(chunk_df))

    chunk_csv = chunk_manifest_dir / f"{chunk_name}.csv"
    chunk_df.to_csv(chunk_csv, index=False, encoding="utf-8")

    chunks.append({
        "chunk_id": int(chunk_id),
        "chunk_name": chunk_name,
        "global_start": int(start_pos),
        "global_end": int(end_pos - 1),
        "frame_count": int(len(chunk_df)),
        "adopt_local_start": 0,
        "adopt_local_end": int(min(ADOPT_SIZE, len(chunk_df)) - 1),
        "chunk_csv": str(chunk_csv),
    })

    if end_pos == len(prod_df):
        break
    start_pos += STEP
    chunk_id += 1

all_chunks_df = pd.DataFrame(chunks)
assert len(all_chunks_df) >= 1, "no chunks generated"
all_chunks_df.to_csv(chunk_manifest_dir / "chunk_index_all.csv", index=False, encoding="utf-8")
all_chunks_df.to_csv(chunk_manifest_dir / "chunk_index_target.csv", index=False, encoding="utf-8")

batch_rows = []
batch_count = math.ceil(len(all_chunks_df) / CHUNKS_PER_BATCH)
for batch_index in range(batch_count):
    s = batch_index * CHUNKS_PER_BATCH
    e = min(s + CHUNKS_PER_BATCH, len(all_chunks_df))
    batch_rows.append({
        "batch_index": batch_index,
        "chunk_from": s,
        "chunk_to": e - 1,
        "chunk_count": e - s,
        "chunk_names": "|".join(all_chunks_df.iloc[s:e]["chunk_name"].tolist()),
    })
batch_plan_df = pd.DataFrame(batch_rows)
batch_plan_df.to_csv(chunk_manifest_dir / "batch_plan.csv", index=False, encoding="utf-8")

bootstrap_df = prod_df.copy()
bootstrap_df.to_csv(global_pose_dir / "bootstrap_input_frames.csv", index=False, encoding="utf-8")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = DepthAnything3.from_pretrained(MODEL_ID).to(device=device)

prediction = model.inference(
    image=bootstrap_df["image_path"].tolist(),
    infer_gs=BOOTSTRAP_INFER_GS,
    process_res=PROCESS_RES,
    export_dir=str(global_pose_dir),
    export_format=BOOTSTRAP_EXPORT_FORMAT,
)

pred_intrinsics = getattr(prediction, "intrinsics", None)
pred_extrinsics = getattr(prediction, "extrinsics", None)
assert pred_intrinsics is not None, "bootstrap intrinsics missing"
assert pred_extrinsics is not None, "bootstrap extrinsics missing"

pred_intrinsics = np.asarray(pred_intrinsics).astype(np.float32)
pred_extrinsics = np.asarray(pred_extrinsics).astype(np.float32)

np.save(global_pose_dir / "pred_intrinsics.npy", pred_intrinsics)
np.save(global_pose_dir / "pred_extrinsics.npy", pred_extrinsics)

def to_4x4(ext):
    ext = np.asarray(ext).astype(np.float32)
    if ext.shape == (4, 4):
        return ext
    if ext.shape == (3, 4):
        M = np.eye(4, dtype=np.float32)
        M[:3, :] = ext
        return M
    raise ValueError(f"unexpected extrinsic shape: {ext.shape}")

rows = []
pose_rows = []
for i, row in enumerate(bootstrap_df.itertuples(index=False)):
    w2c = to_4x4(pred_extrinsics[i])
    c2w = np.linalg.inv(w2c)
    center = c2w[:3, 3]
    rows.append({
        "bootstrap_index": i,
        "record_index": int(row.record_index),
        "image_file_name": row.image_file_name,
        "image_path": row.image_path,
        "cx_world": float(center[0]),
        "cy_world": float(center[1]),
        "cz_world": float(center[2]),
    })
    pose_rows.append({
        "bootstrap_index": i,
        "record_index": int(row.record_index),
        "image_file_name": row.image_file_name,
        "m00": float(c2w[0, 0]), "m01": float(c2w[0, 1]), "m02": float(c2w[0, 2]), "m03": float(c2w[0, 3]),
        "m10": float(c2w[1, 0]), "m11": float(c2w[1, 1]), "m12": float(c2w[1, 2]), "m13": float(c2w[1, 3]),
        "m20": float(c2w[2, 0]), "m21": float(c2w[2, 1]), "m22": float(c2w[2, 2]), "m23": float(c2w[2, 3]),
        "m30": float(c2w[3, 0]), "m31": float(c2w[3, 1]), "m32": float(c2w[3, 2]), "m33": float(c2w[3, 3]),
    })

camera_centers_df = pd.DataFrame(rows)
camera_centers_df.to_csv(global_pose_dir / "camera_center_matrix.csv", index=False, encoding="utf-8")

camera_matrix_df = pd.DataFrame(pose_rows)
camera_matrix_df.to_csv(global_pose_dir / "camera_matrix_full.csv", index=False, encoding="utf-8")

summary = {
    "route": "continuous-gs-v05-chunk3-sequential-bootstrap",
    "bootstrap_mode": "pose_only_no_gs",
    "bootstrap_export_format": BOOTSTRAP_EXPORT_FORMAT,
    "bootstrap_frame_count": int(len(bootstrap_df)),
    "chunk_count": int(len(all_chunks_df)),
    "batch_count": int(batch_count),
    "global_pose_dir": str(global_pose_dir),
    "bundle_model_slug": BUNDLE_MODEL_SLUG,
    "chunk_index_all_path": str(chunk_manifest_dir / "chunk_index_all.csv"),
    "batch_plan_path": str(chunk_manifest_dir / "batch_plan.csv"),
}
(global_pose_dir / "export_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

del prediction
del model
gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()

print(json.dumps(summary, indent=2, ensure_ascii=False))
print("\n# batch_plan")
print(batch_plan_df.to_string(index=False))
```

### Block 4: 3chunk sequential helper

```python
#13
from pathlib import Path
import gc
import json
import sys
import shutil

import numpy as np
import pandas as pd
import torch
import trimesh
from plyfile import PlyData, PlyElement

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
probe_root = Path(ctx["probe_root"])

pipeline_root = probe_root / "continuous_gs_v05_chunk3_sequential"
global_pose_dir = pipeline_root / "global_pose_bootstrap"
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
merged_dir = pipeline_root / "merged"

config = json.loads((pipeline_root / "pipeline_config.json").read_text(encoding="utf-8"))
MODEL_ID = config["MODEL_ID"]
PROCESS_RES = config["PROCESS_RES"]
CHUNKS_PER_BATCH = config["CHUNKS_PER_BATCH"]

target_chunks_df = pd.read_csv(chunk_manifest_dir / "chunk_index_target.csv")
global_centers_df = pd.read_csv(global_pose_dir / "camera_center_matrix.csv")

def to_4x4(ext):
    ext = np.asarray(ext).astype(np.float32)
    if ext.shape == (4, 4):
        return ext
    if ext.shape == (3, 4):
        M = np.eye(4, dtype=np.float32)
        M[:3, :] = ext
        return M
    raise ValueError(f"unexpected extrinsic shape: {ext.shape}")

def camera_centers_from_extrinsics(extrinsics):
    centers = []
    for ext in extrinsics:
        w2c = to_4x4(ext)
        c2w = np.linalg.inv(w2c)
        centers.append(c2w[:3, 3])
    return np.stack(centers, axis=0)

def umeyama_alignment(src, dst, estimate_scale=True):
    src = np.asarray(src, dtype=np.float64)
    dst = np.asarray(dst, dtype=np.float64)

    src_mean = src.mean(axis=0)
    dst_mean = dst.mean(axis=0)
    src_c = src - src_mean
    dst_c = dst - dst_mean

    cov = (dst_c.T @ src_c) / src.shape[0]
    U, D, Vt = np.linalg.svd(cov)
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[-1, -1] = -1

    R = U @ S @ Vt
    if estimate_scale:
        var_src = np.mean(np.sum(src_c ** 2, axis=1))
        scale = np.trace(np.diag(D) @ S) / max(var_src, 1e-12)
    else:
        scale = 1.0

    t = dst_mean - scale * (R @ src_mean)
    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = scale * R
    T[:3, 3] = t
    return T.astype(np.float32)

def load_scene_any(path: Path):
    loaded = trimesh.load(str(path), force="scene")
    if isinstance(loaded, trimesh.Scene):
        return loaded
    scene = trimesh.Scene()
    if hasattr(loaded, "geometry"):
        for name, geom in loaded.geometry.items():
            scene.add_geometry(geom, node_name=name)
    else:
        scene.add_geometry(loaded)
    return scene

def process_batch(run_batch_index: int):
    batch_start = run_batch_index * CHUNKS_PER_BATCH
    batch_end = min(batch_start + CHUNKS_PER_BATCH, len(target_chunks_df))

    if batch_start >= len(target_chunks_df):
        print(json.dumps({
            "status": "skip",
            "reason": "batch_out_of_range",
            "run_batch_index": int(run_batch_index),
            "available_batch_count": int((len(target_chunks_df) + CHUNKS_PER_BATCH - 1) // CHUNKS_PER_BATCH),
        }, indent=2, ensure_ascii=False))
        return

    batch_chunks_df = target_chunks_df.iloc[batch_start:batch_end].copy().reset_index(drop=True)
    batch_name = f"batch_{run_batch_index:03d}"
    batch_dir = chunk_runs_dir / batch_name
    batch_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DepthAnything3.from_pretrained(MODEL_ID).to(device=device)

    X = global_centers_df[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32)
    X0 = X - X.mean(axis=0, keepdims=True)
    _, _, Vt = np.linalg.svd(X0, full_matrices=False)
    axis = Vt[0]
    axis = axis / np.linalg.norm(axis)

    run_rows = []
    transform_rows = []
    keep_rows = []
    batch_records = []
    batch_scene = trimesh.Scene()

    for row in batch_chunks_df.itertuples(index=False):
        chunk_df = pd.read_csv(row.chunk_csv)
        images = chunk_df["image_path"].tolist()

        out_dir = chunk_runs_dir / row.chunk_name
        done_flag = out_dir / "_SUCCESS.json"

        if done_flag.exists():
            pred_extrinsics = np.load(out_dir / "pred_extrinsics.npy")
            chunk_df = pd.read_csv(out_dir / "chunk_input_frames.csv")
        else:
            if out_dir.exists():
                shutil.rmtree(out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            prediction = model.inference(
                image=images,
                infer_gs=True,
                process_res=PROCESS_RES,
                export_dir=str(out_dir),
                export_format="npz-glb-gs_ply-gs_video",
            )

            pred_intrinsics = getattr(prediction, "intrinsics", None)
            pred_extrinsics = getattr(prediction, "extrinsics", None)

            assert pred_intrinsics is not None, f"intrinsics missing: {row.chunk_name}"
            assert pred_extrinsics is not None, f"extrinsics missing: {row.chunk_name}"

            np.save(out_dir / "pred_intrinsics.npy", np.asarray(pred_intrinsics).astype(np.float32))
            np.save(out_dir / "pred_extrinsics.npy", np.asarray(pred_extrinsics).astype(np.float32))
            chunk_df.to_csv(out_dir / "chunk_input_frames.csv", index=False, encoding="utf-8")
            done_flag.write_text(json.dumps({"chunk_name": row.chunk_name}, indent=2, ensure_ascii=False), encoding="utf-8")

        pred_extrinsics = np.asarray(pred_extrinsics).astype(np.float32)
        local_centers = camera_centers_from_extrinsics(pred_extrinsics)

        merged = chunk_df.merge(
            global_centers_df[["record_index", "cx_world", "cy_world", "cz_world"]],
            on="record_index",
            how="left",
        )
        assert len(merged) == len(chunk_df), {"chunk_name": row.chunk_name, "merged_len": len(merged), "chunk_len": len(chunk_df)}

        src = local_centers
        dst = merged[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32)
        T_c_to_w0 = umeyama_alignment(src, dst, estimate_scale=True)

        T_path = chunk_manifest_dir / f"{row.chunk_name}_to_w0.npy"
        np.save(T_path, T_c_to_w0.astype(np.float32))

        transform_rows.append({
            "chunk_name": row.chunk_name,
            "frame_count": int(len(chunk_df)),
            "transform_path": str(T_path),
        })

        ply_path = out_dir / "gs_ply" / "0000.ply"
        glb_path = out_dir / "scene.glb"

        run_rows.append({
            "batch_name": batch_name,
            "chunk_name": row.chunk_name,
            "frame_count": int(len(chunk_df)),
            "ply_exists": bool(ply_path.exists()),
            "glb_exists": bool(glb_path.exists()),
            "out_dir": str(out_dir),
        })

        if ply_path.exists():
            T = np.load(T_path).astype(np.float32)
            A = T[:3, :3]
            t = T[:3, 3]

            adopted = chunk_df.loc[chunk_df["is_adopted_region"] == True].copy()
            adopted_world = global_centers_df.loc[
                global_centers_df["record_index"].isin(adopted["record_index"].tolist()),
                ["cx_world", "cy_world", "cz_world"],
            ].to_numpy(dtype=np.float32)
            adopted_proj = adopted_world @ axis
            left = float(adopted_proj.min())
            right = float(adopted_proj.max())

            ply = PlyData.read(str(ply_path))
            df = pd.DataFrame(ply["vertex"].data)
            xyz = df[["x", "y", "z"]].to_numpy(dtype=np.float32)

            xyz_w = (A @ xyz.T).T + t
            proj_w = xyz_w @ axis
            keep = (proj_w >= left) & (proj_w < right + 1e-6)

            df["x"] = xyz_w[:, 0]
            df["y"] = xyz_w[:, 1]
            df["z"] = xyz_w[:, 2]
            df = df.loc[keep].copy()

            if len(df) > 0:
                batch_records.append(df.to_records(index=False))

            keep_rows.append({
                "batch_name": batch_name,
                "chunk_name": row.chunk_name,
                "kept_vertices": int(len(df)),
                "left": left,
                "right": right,
            })

        if glb_path.exists():
            scene = load_scene_any(glb_path)
            T = np.load(T_path).astype(np.float32)
            for gname, geom in scene.geometry.items():
                geom2 = geom.copy()
                if hasattr(geom2, "apply_transform"):
                    geom2.apply_transform(T)
                batch_scene.add_geometry(geom2, node_name=f"{row.chunk_name}_{gname}")

    run_df = pd.DataFrame(run_rows)
    run_df.to_csv(batch_dir / "chunk_run_summary.csv", index=False, encoding="utf-8")

    transform_df = pd.DataFrame(transform_rows)
    transform_df.to_csv(batch_dir / "chunk_global_transforms.csv", index=False, encoding="utf-8")

    keep_df = pd.DataFrame(keep_rows)
    keep_df.to_csv(batch_dir / "chunk_keep_summary.csv", index=False, encoding="utf-8")

    batch_ply_path = batch_dir / f"{batch_name}_merged_gs.ply"
    if batch_records:
        batch_records_concat = np.concatenate(batch_records, axis=0)
        PlyData([PlyElement.describe(batch_records_concat, "vertex")], text=False).write(str(batch_ply_path))

    batch_glb_path = batch_dir / f"{batch_name}_merged_scene.glb"
    if len(batch_scene.geometry) > 0:
        batch_scene.export(str(batch_glb_path))

    batch_summary = {
        "status": "ok",
        "batch_name": batch_name,
        "run_batch_index": int(run_batch_index),
        "chunk_count": int(len(batch_chunks_df)),
        "chunk_names": batch_chunks_df["chunk_name"].tolist(),
        "batch_ply_path": str(batch_ply_path) if batch_ply_path.exists() else None,
        "batch_glb_path": str(batch_glb_path) if batch_glb_path.exists() else None,
    }
    (batch_dir / "batch_summary.json").write_text(json.dumps(batch_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print(json.dumps(batch_summary, indent=2, ensure_ascii=False))
```

### Block 5: 3chunk sequential batch run

- この block は 1 回で `3chunk` だけ処理する。
- `RUN_BATCH_INDEX = 0` は先頭 `3chunk`、`RUN_BATCH_INDEX = 1` は次の `3chunk` を意味する。
- `batch_plan.csv` を見ながら `0`, `1`, `2`, `3` ... と順に実行する。
- 全 batch を回し終わるまでは `Block 6` を実行しない。

```python
#14
RUN_BATCH_INDEX = 0
process_batch(RUN_BATCH_INDEX)
```

```python
#14-01
RUN_BATCH_INDEX = 1
process_batch(RUN_BATCH_INDEX)
```

```python
#14-02
RUN_BATCH_INDEX = 2
process_batch(RUN_BATCH_INDEX)
```

```python
#14-03
RUN_BATCH_INDEX = 3
process_batch(RUN_BATCH_INDEX)
```

### Block 6: Final rebuild merge + bundle

```python
#15
from pathlib import Path
import json
import shutil

import numpy as np
import pandas as pd
import trimesh
from plyfile import PlyData, PlyElement

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
probe_root = Path(ctx["probe_root"])
results_root = Path(ctx["results_root"])
modeling_session_id = ctx["modeling_session_id"]

pipeline_root = probe_root / "continuous_gs_v05_chunk3_sequential"
global_pose_dir = pipeline_root / "global_pose_bootstrap"
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
merged_dir = pipeline_root / "merged"
merged_dir.mkdir(parents=True, exist_ok=True)

config = json.loads((pipeline_root / "pipeline_config.json").read_text(encoding="utf-8"))
BUNDLE_MODEL_SLUG = config["BUNDLE_MODEL_SLUG"]
REQUIRE_ALL_CHUNKS = True
MAKE_DRIVE_BUNDLE = True
DOWNLOAD_LOCAL_BUNDLE = False

all_chunks_df = pd.read_csv(chunk_manifest_dir / "chunk_index_all.csv")
completed_chunk_names = sorted({
    p.parent.name
    for p in chunk_runs_dir.glob("*/gs_ply/0000.ply")
})
completed_chunks_df = all_chunks_df[all_chunks_df["chunk_name"].isin(completed_chunk_names)].copy()

batch_summaries = sorted(chunk_runs_dir.glob("batch_*/batch_summary.json"))
summary_rows = [json.loads(p.read_text(encoding="utf-8")) for p in batch_summaries]
(merged_dir / "all_batch_summary.json").write_text(json.dumps(summary_rows, indent=2, ensure_ascii=False), encoding="utf-8")

if REQUIRE_ALL_CHUNKS and len(completed_chunks_df) < len(all_chunks_df):
    merge_summary = {
        "route": "continuous-gs-v05-chunk3-sequential-merge",
        "status": "skipped",
        "reason": "waiting_for_all_chunks",
        "completed_chunk_count": int(len(completed_chunks_df)),
        "all_chunk_count": int(len(all_chunks_df)),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary.json"),
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
else:
    global_centers_df = pd.read_csv(global_pose_dir / "camera_center_matrix.csv")
    X = global_centers_df[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32)
    X0 = X - X.mean(axis=0, keepdims=True)
    _, _, Vt = np.linalg.svd(X0, full_matrices=False)
    axis = Vt[0]
    axis = axis / np.linalg.norm(axis)
    global_centers_df["proj"] = X @ axis

    def load_scene_any(path: Path):
        loaded = trimesh.load(str(path), force="scene")
        if isinstance(loaded, trimesh.Scene):
            return loaded
        scene = trimesh.Scene()
        if hasattr(loaded, "geometry"):
            for name, geom in loaded.geometry.items():
                scene.add_geometry(geom, node_name=name)
        else:
            scene.add_geometry(loaded)
        return scene

    def to_4x4(ext):
        ext = np.asarray(ext).astype(np.float32)
        if ext.shape == (4, 4):
            return ext
        if ext.shape == (3, 4):
            M = np.eye(4, dtype=np.float32)
            M[:3, :] = ext
            return M
        raise ValueError(f"unexpected extrinsic shape: {ext.shape}")

    transform_rows = []
    keep_rows = []
    all_vertices = []
    dtype_ref = None
    master_scene = trimesh.Scene()

    for row in completed_chunks_df.itertuples(index=False):
        out_dir = chunk_runs_dir / row.chunk_name
        ply_path = out_dir / "gs_ply" / "0000.ply"
        pred_ext_path = out_dir / "pred_extrinsics.npy"
        chunk_input_path = out_dir / "chunk_input_frames.csv"
        glb_path = out_dir / "scene.glb"
        if not (ply_path.exists() and pred_ext_path.exists() and chunk_input_path.exists()):
            continue

        chunk_df = pd.read_csv(chunk_input_path)
        pred_extrinsics = np.load(pred_ext_path)

        local_centers = []
        for ext in pred_extrinsics:
            w2c = to_4x4(ext)
            c2w = np.linalg.inv(w2c)
            local_centers.append(c2w[:3, 3])
        local_centers = np.stack(local_centers, axis=0)

        merged = chunk_df.merge(
            global_centers_df[["record_index", "cx_world", "cy_world", "cz_world", "proj"]],
            on="record_index",
            how="left",
        )
        assert not merged[["cx_world", "cy_world", "cz_world"]].isnull().any().any(), f"global center missing: {row.chunk_name}"

        src = np.asarray(local_centers, dtype=np.float64)
        dst = merged[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32).astype(np.float64)
        src_mean = src.mean(axis=0)
        dst_mean = dst.mean(axis=0)
        src_c = src - src_mean
        dst_c = dst - dst_mean
        cov = (dst_c.T @ src_c) / src.shape[0]
        U, D, Vt2 = np.linalg.svd(cov)
        S = np.eye(3)
        if np.linalg.det(U) * np.linalg.det(Vt2) < 0:
            S[-1, -1] = -1
        R = U @ S @ Vt2
        var_src = np.mean(np.sum(src_c ** 2, axis=1))
        scale = np.trace(np.diag(D) @ S) / max(var_src, 1e-12)
        t = dst_mean - scale * (R @ src_mean)
        T_c_to_w0 = np.eye(4, dtype=np.float32)
        T_c_to_w0[:3, :3] = (scale * R).astype(np.float32)
        T_c_to_w0[:3, 3] = t.astype(np.float32)

        T_path = chunk_manifest_dir / f"{row.chunk_name}_to_w0.npy"
        np.save(T_path, T_c_to_w0)
        transform_rows.append({
            "chunk_name": row.chunk_name,
            "frame_count": int(len(chunk_df)),
            "transform_path": str(T_path),
        })

        adopted_proj = merged.loc[merged["is_adopted_region"] == True, "proj"].to_numpy(dtype=np.float32)
        if len(adopted_proj) == 0:
            keep_rows.append({"chunk_name": row.chunk_name, "kept_vertices": 0, "left": None, "right": None})
            continue

        left = float(adopted_proj.min())
        right = float(adopted_proj.max())

        ply = PlyData.read(str(ply_path))
        df = pd.DataFrame(ply["vertex"].data)
        xyz = df[["x", "y", "z"]].to_numpy(dtype=np.float32)

        A = T_c_to_w0[:3, :3].astype(np.float32)
        t32 = T_c_to_w0[:3, 3].astype(np.float32)
        xyz_w = (A @ xyz.T).T + t32
        proj_w = xyz_w @ axis
        keep = (proj_w >= left) & (proj_w < right + 1e-6)

        df["x"] = xyz_w[:, 0]
        df["y"] = xyz_w[:, 1]
        df["z"] = xyz_w[:, 2]
        df = df.loc[keep].copy()

        if len(df) > 0:
            records = df.to_records(index=False)
            if dtype_ref is None:
                dtype_ref = records.dtype
            else:
                records = records.astype(dtype_ref, copy=False)
            all_vertices.append(records)

        keep_rows.append({
            "chunk_name": row.chunk_name,
            "kept_vertices": int(len(df)),
            "left": left,
            "right": right,
        })

        if glb_path.exists():
            scene = load_scene_any(glb_path)
            for gname, geom in scene.geometry.items():
                geom2 = geom.copy()
                if hasattr(geom2, "apply_transform"):
                    geom2.apply_transform(T_c_to_w0)
                master_scene.add_geometry(geom2, node_name=f"{row.chunk_name}_{gname}")

    transform_df = pd.DataFrame(transform_rows)
    transform_df.to_csv(chunk_manifest_dir / "chunk_global_transforms.csv", index=False, encoding="utf-8")

    keep_df = pd.DataFrame(keep_rows)
    keep_summary_path = merged_dir / "chunk_keep_summary.csv"
    keep_df.to_csv(keep_summary_path, index=False, encoding="utf-8")

    merged_ply_path = merged_dir / "merged_gs.ply"
    if all_vertices:
        merged_vertices = np.concatenate(all_vertices, axis=0)
        PlyData([PlyElement.describe(merged_vertices, "vertex")], text=False).write(str(merged_ply_path))

    merged_glb_path = merged_dir / "merged_scene.glb"
    if len(master_scene.geometry) > 0:
        master_scene.export(str(merged_glb_path))

    bundle_summary = {
        "status": "skipped",
        "reason": "MAKE_DRIVE_BUNDLE is False",
    }

    if MAKE_DRIVE_BUNDLE:
        drive_bundle_base = f"{modeling_session_id}_{BUNDLE_MODEL_SLUG}_continuousgsv05chunk3seq"
        drive_bundle_dir = results_root / drive_bundle_base
        drive_bundle_zip = results_root / f"{drive_bundle_base}.zip"
        local_bundle_zip = Path("/content") / f"{drive_bundle_base}.zip"

        if drive_bundle_dir.exists():
            shutil.rmtree(drive_bundle_dir)
        if drive_bundle_zip.exists():
            drive_bundle_zip.unlink()
        if local_bundle_zip.exists():
            local_bundle_zip.unlink()

        shutil.copytree(pipeline_root, drive_bundle_dir)
        shutil.make_archive(str(drive_bundle_zip.with_suffix("")), "zip", root_dir=str(drive_bundle_dir))

        bundle_summary = {
            "status": "ok",
            "drive_bundle_dir": str(drive_bundle_dir),
            "drive_bundle_zip": str(drive_bundle_zip),
        }

        if DOWNLOAD_LOCAL_BUNDLE:
            from google.colab import files
            shutil.copy2(drive_bundle_zip, local_bundle_zip)
            bundle_summary["local_bundle_zip"] = str(local_bundle_zip)
            files.download(str(local_bundle_zip))

    merge_summary = {
        "route": "continuous-gs-v05-chunk3-sequential-merge",
        "status": "ok" if all_vertices else "skipped",
        "reason": None if all_vertices else "no kept vertices",
        "completed_chunk_count": int(len(completed_chunks_df)),
        "all_chunk_count": int(len(all_chunks_df)),
        "merged_ply_path": str(merged_ply_path) if merged_ply_path.exists() else None,
        "merged_glb_path": str(merged_glb_path) if merged_glb_path.exists() else None,
        "chunk_global_transforms_path": str(chunk_manifest_dir / "chunk_global_transforms.csv"),
        "chunk_keep_summary_path": str(keep_summary_path),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary.json"),
        "bundle_summary": bundle_summary,
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
```
