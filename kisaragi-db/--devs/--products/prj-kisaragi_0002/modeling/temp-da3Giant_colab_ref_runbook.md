# temp DA3 Giant Colab Ref Runbook

- `temp-da3Giant_colab_evid_runbook.md` の貼り付け用 companion とする。
- 更新は必ず `temp-da3Giant_colab_evid_runbook.md` と 2 file set で行う。
- rollback baseline は `MetricLarge route` とし、この file は `MRL-9` の `DA3 Giant` / `Giant Large` route だけを追加管理する。
- fresh runtime では上から順に実行し、`準備確認 3` の widget 選択を挟んでから残りを流す。

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
writable_results_root_candidates = [
    Path("/content/drive/MyDrive/trajectreview/modeling"),
    shortcut_root / "trajectreview" / "modeling",
]
scan_roots = [
    shortcut_root / "trajectreview",
    Path("/content/drive/MyDrive/trajectreview"),
]
results_root = next((p for p in writable_results_root_candidates if p.exists()), writable_results_root_candidates[0])
candidate_doc_path = Path("/content/runbook_drive_candidates.json")

def infer_session_id(path: Path) -> str:
    return path.stem if path.suffix.lower() == ".zip" else path.name

def candidate_rank(path: Path) -> int:
    s = str(path)
    if ".shortcut-targets-by-id" in s:
        return 0
    if "/MyDrive/" in s:
        return 1
    return 9

zip_map = {}
dir_map = {}
for root in scan_roots:
    if not root.exists():
        continue
    for zip_path in sorted(root.rglob("*.zip")):
        stat = zip_path.stat()
        key = (infer_session_id(zip_path), stat.st_size)
        cand = {
            "kind": "zip",
            "session_id": infer_session_id(zip_path),
            "label": f"{infer_session_id(zip_path)} [zip]",
            "path": str(zip_path),
            "size_bytes": stat.st_size,
        }
        prev = zip_map.get(key)
        if prev is None or candidate_rank(zip_path) < candidate_rank(Path(prev["path"])):
            zip_map[key] = cand
    for pkg_path in sorted(root.rglob("session_package.json")):
        session_root = pkg_path.parent
        key = infer_session_id(session_root)
        cand = {
            "kind": "dir",
            "session_id": infer_session_id(session_root),
            "label": f"{infer_session_id(session_root)} [dir]",
            "path": str(session_root),
        }
        prev = dir_map.get(key)
        if prev is None or candidate_rank(session_root) < candidate_rank(Path(prev["path"])):
            dir_map[key] = cand

candidates = sorted(
    list(zip_map.values()) + list(dir_map.values()),
    key=lambda x: (x["session_id"], x["kind"], x["path"]),
)

candidate_doc = {
    "scan_roots": [str(p) for p in scan_roots if p.exists()],
    "scan_root_exists": {str(p): p.exists() for p in scan_roots},
    "results_root": str(results_root),
    "candidate_count": len(candidates),
    "candidates": candidates,
}
candidate_doc_path.write_text(json.dumps(candidate_doc, indent=2, ensure_ascii=False), encoding="utf-8")

print("candidate_doc_path", candidate_doc_path)
print("results_root", results_root)
for root in scan_roots:
    print("scan_root_exists", root.exists(), root)
print("candidate_count", len(candidates))
for idx, item in enumerate(candidates):
    extra = f" size={item['size_bytes']}" if "size_bytes" in item else ""
    print(f"[{idx}] {item['label']}: {item['path']}{extra}")
```

## 準備確認 3

```python
from pathlib import Path
import json
import ipywidgets as widgets
from IPython.display import display

candidate_doc_path = Path("/content/runbook_drive_candidates.json")
selected_doc_path = Path("/content/runbook_selected_input.json")

candidate_doc = json.loads(candidate_doc_path.read_text(encoding="utf-8"))
assert candidate_doc["candidate_count"] >= 1, candidate_doc

options = [(f"[{idx}] {item['label']}", idx) for idx, item in enumerate(candidate_doc["candidates"])]
dropdown = widgets.Dropdown(options=options, description="input", layout=widgets.Layout(width="95%"))
button = widgets.Button(description="selected input を保存", button_style="success")
output = widgets.Output()

def on_click(_):
    selected_index = dropdown.value
    selected = candidate_doc["candidates"][selected_index]
    selected_doc = {
        "selected_index": selected_index,
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
print("操作: dropdown で 1 件選び、`selected input を保存` を押す")
```

## 準備確認 4

```python
from pathlib import Path
import json

selected_doc = json.loads(Path("/content/runbook_selected_input.json").read_text(encoding="utf-8"))
selected_path = Path(selected_doc["path"])
results_root = Path(selected_doc["results_root"])

print("selected_kind", selected_doc["kind"])
print("selected_session_id", selected_doc["session_id"])
print("selected_path_exists", selected_path.exists(), selected_path)
print("results_root_parent_exists", results_root.parent.exists(), results_root.parent)
```

## 準備確認 5

```python
from pathlib import Path

print("repo_exists_before_bootstrap", Path("/content/Depth-Anything-3").exists())
print("extract_root_exists_before_bootstrap", Path("/content/trajectreview_input").exists())
```

## install 1

```python
from pathlib import Path
import shutil
import subprocess

repo_root = Path("/content/Depth-Anything-3")
if repo_root.exists():
    shutil.rmtree(repo_root)

subprocess.run(
    ["git", "clone", "https://github.com/ByteDance-Seed/Depth-Anything-3.git", str(repo_root)],
    check=True,
)
print("repo_exists", repo_root.exists(), repo_root)
```

## install 2

```python
import subprocess

subprocess.run(
    ["python", "-m", "pip", "install", "--quiet", "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile", "trimesh"],
    check=True,
)
print("custom_dependency_install_ok")
```

## install 3

```python
import subprocess

subprocess.run(
    ["python", "-m", "pip", "install", "--quiet", "gsplat"],
    check=True,
)
print("gsplat_install_ok")
```

## install 4

```python
import sys
from pathlib import Path

repo_root = Path("/content/Depth-Anything-3")
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from depth_anything_3.api import DepthAnything3
import gsplat

print("repo_root_exists", repo_root.exists(), repo_root)
print("src_root_exists", src_root.exists(), src_root)
print("depth_anything_3_import_ok", DepthAnything3)
print("gsplat_module", gsplat.__file__)
print("gsplat_version", getattr(gsplat, "__version__", "unknown"))
```

## `MRL-7` adopted one-block

```python
from pathlib import Path
import json
import math
import shutil
import zipfile

import imageio.v3 as iio
import numpy as np
import pandas as pd
import torch
from PIL import Image
import gsplat
from depth_anything_3.api import DepthAnything3

selected_doc = json.loads(Path("/content/runbook_selected_input.json").read_text(encoding="utf-8"))
selected_path = Path(selected_doc["path"])
selected_kind = selected_doc["kind"]
session_id = selected_doc["session_id"]
results_root = Path(selected_doc["results_root"])
extract_root = Path("/content/trajectreview_input")
probe_dir = results_root / f"{session_id}_da3_multiframe_probe_v01"
world_dir = probe_dir / "world_fusion_v01"

if extract_root.exists():
    shutil.rmtree(extract_root)
extract_root.mkdir(parents=True, exist_ok=True)

if selected_kind == "zip":
    with zipfile.ZipFile(selected_path, "r") as zf:
        zf.extractall(extract_root)
else:
    dest_root = extract_root / selected_path.name
    shutil.copytree(selected_path, dest_root)

pkg_hits = sorted(extract_root.rglob("session_package.json"))
assert pkg_hits, f"session_package.json not found under {extract_root}"
session_pkg = next((p for p in pkg_hits if p.parent.name == "trajectreview"), pkg_hits[0])
session_root = session_pkg.parent
session_outer = session_root.parent
images_dir = session_root / "images"
frame_pose_path = session_root / "frame_pose_index.csv"
arcore_pose_path = session_root / "arcore_pose.jsonl"
if not arcore_pose_path.exists():
    arcore_pose_path = session_outer / "arcore_pose.jsonl"

assert images_dir.exists(), images_dir
assert frame_pose_path.exists(), frame_pose_path
assert arcore_pose_path.exists(), arcore_pose_path

probe_dir.mkdir(parents=True, exist_ok=True)
world_dir.mkdir(parents=True, exist_ok=True)

frame_pose_df = pd.read_csv(frame_pose_path)
assert "frame_timestamp_ns" in frame_pose_df.columns
assert "pose_record_index" in frame_pose_df.columns
image_files = sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.jpeg"))
assert image_files, images_dir

frame_name_col = "image_file_name" if "image_file_name" in frame_pose_df.columns else None
has_named_frames = False
if frame_name_col is not None:
    frame_names = frame_pose_df[frame_name_col].fillna("").astype(str).str.strip()
    has_named_frames = bool((frame_names != "").any())

if has_named_frames:
    rows = frame_pose_df.loc[frame_names != ""].copy()
    rows["frame_name"] = rows[frame_name_col].astype(str).str.strip()
    derived_frame_mapping = False
else:
    assert "frame_index" in frame_pose_df.columns, frame_pose_df.columns.tolist()
    rows = frame_pose_df.sort_values("frame_index").reset_index(drop=True).copy()
    assign_count = min(len(rows), len(image_files))
    assert assign_count >= 1, {"rows": len(rows), "image_files": len(image_files)}
    rows = rows.iloc[:assign_count].copy()
    rows["frame_name"] = [p.name for p in image_files[:assign_count]]
    derived_frame_mapping = True

rows["timestamp_sec"] = rows["frame_timestamp_ns"].astype(np.float64) / 1e9
rows = rows.sort_values("timestamp_sec").reset_index(drop=True)

gaps = rows["timestamp_sec"].diff().fillna(0.0)
window_break = gaps > 0.2
window_id = window_break.cumsum()
rows["window_id"] = window_id

best_window = None
for _, g in rows.groupby("window_id"):
    span = float(g["timestamp_sec"].iloc[-1] - g["timestamp_sec"].iloc[0])
    item = {
        "span_sec": span,
        "frame_count": int(len(g)),
        "rows": g.reset_index(drop=True),
    }
    if best_window is None or item["span_sec"] > best_window["span_sec"]:
        best_window = item

assert best_window is not None
g = best_window["rows"]
sample_count = min(12, len(g))
pick = np.linspace(0, len(g) - 1, sample_count).astype(int)
sample_rows = g.iloc[pick].reset_index(drop=True)

window_probe = {
    "session_root": str(session_root),
    "frame_index_path": str(frame_pose_path),
    "frame_col": "frame_name",
    "derived_frame_mapping": derived_frame_mapping,
    "time_col": "frame_timestamp_ns",
    "aligned_frame_count": int(len(rows)),
    "window_span_sec": float(best_window["span_sec"]),
    "window_frame_count": int(best_window["frame_count"]),
    "window_start_sec": float(g["timestamp_sec"].iloc[0]),
    "window_end_sec": float(g["timestamp_sec"].iloc[-1]),
    "sample_frame_count": int(len(sample_rows)),
    "sample_frames": sample_rows[["frame_name", "pose_record_index", "timestamp_sec"]].to_dict(orient="records"),
}
(probe_dir / "mrl7_window_probe.json").write_text(json.dumps(window_probe, indent=2, ensure_ascii=False), encoding="utf-8")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = DepthAnything3.from_pretrained("depth-anything/DA3METRIC-LARGE").to(device=device)

depth_dir = probe_dir / "depth_batch_v01"
depth_dir.mkdir(parents=True, exist_ok=True)
depth_manifest = []
for rec in window_probe["sample_frames"]:
    frame_name = rec["frame_name"]
    image_path = images_dir / frame_name
    prediction = model.inference([str(image_path)])
    depth = np.asarray(prediction.depth[0]).astype(np.float32)
    out_npy = depth_dir / f"{Path(frame_name).stem}_depth.npy"
    np.save(out_npy, depth)
    depth_manifest.append({
        "frame_name": frame_name,
        "pose_record_index": int(rec["pose_record_index"]),
        "timestamp_sec": float(rec["timestamp_sec"]),
        "depth_path": str(out_npy),
        "depth_shape": list(depth.shape),
    })
(probe_dir / "depth_batch_manifest.json").write_text(json.dumps(depth_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

with arcore_pose_path.open("r", encoding="utf-8") as f:
    pose_records = [json.loads(line) for line in f if line.strip()]

def quat_to_rot(qx, qy, qz, qw):
    xx, yy, zz = qx*qx, qy*qy, qz*qz
    xy, xz, yz = qx*qy, qx*qz, qy*qz
    wx, wy, wz = qw*qx, qw*qy, qw*qz
    return np.array([
        [1 - 2*(yy + zz), 2*(xy - wz), 2*(xz + wy)],
        [2*(xy + wz), 1 - 2*(xx + zz), 2*(yz - wx)],
        [2*(xz - wy), 2*(yz + wx), 1 - 2*(xx + yy)],
    ], dtype=np.float32)

all_points = []
per_frame = []
skipped = []
stride = 24
for rec in depth_manifest:
    pose_idx = int(rec["pose_record_index"])
    if pose_idx >= len(pose_records):
        skipped.append({"frame_name": rec["frame_name"], "reason": "pose_index_out_of_range"})
        continue
    record = pose_records[pose_idx]
    intr = record["imageIntrinsics"]
    pose = record["pose"]
    depth = np.load(rec["depth_path"]).astype(np.float32)
    h, w = depth.shape
    grid_y, grid_x = np.mgrid[0:h:stride, 0:w:stride]
    z = depth[grid_y, grid_x]
    valid = np.isfinite(z) & (z > 0.0)
    if not np.any(valid):
        skipped.append({"frame_name": rec["frame_name"], "reason": "no_valid_depth"})
        continue
    px = grid_x[valid].astype(np.float32)
    py = grid_y[valid].astype(np.float32)
    zz = z[valid].astype(np.float32)
    x = (px - float(intr["cx"])) * zz / float(intr["fx"])
    y = (py - float(intr["cy"])) * zz / float(intr["fy"])
    cam = np.stack([x, y, zz], axis=-1)

    R_wc = quat_to_rot(
        float(pose["qx"]), float(pose["qy"]), float(pose["qz"]), float(pose["qw"])
    )
    t_wc = np.array([float(pose["tx"]), float(pose["ty"]), float(pose["tz"])], dtype=np.float32)
    world = (R_wc @ cam.T).T + t_wc
    all_points.append(world)
    per_frame.append({
        "frame_name": rec["frame_name"],
        "pose_record_index": pose_idx,
        "point_count": int(len(world)),
        "timestamp_sec": float(rec["timestamp_sec"]),
    })

assert all_points, "no world points generated"
merged = np.concatenate(all_points, axis=0).astype(np.float32)
np.save(world_dir / "world_points_multiframe.npy", merged)

with (world_dir / "world_points_multiframe.ply").open("w", encoding="utf-8") as f:
    f.write("ply\\nformat ascii 1.0\\n")
    f.write(f"element vertex {len(merged)}\\n")
    f.write("property float x\\nproperty float y\\nproperty float z\\n")
    f.write("end_header\\n")
    for p in merged:
        f.write(f"{p[0]} {p[1]} {p[2]}\\n")

world_summary = {
    "stride": stride,
    "processed_frames": len(per_frame),
    "skipped_frames": skipped,
    "total_points": int(len(merged)),
    "per_frame": per_frame,
    "npy_path": str(world_dir / "world_points_multiframe.npy"),
    "ply_path": str(world_dir / "world_points_multiframe.ply"),
}
(world_dir / "world_fusion_summary.json").write_text(json.dumps(world_summary, indent=2, ensure_ascii=False), encoding="utf-8")

sample = merged[::4] if len(merged) > 4000 else merged
sample_min = sample.min(axis=0)
sample_max = sample.max(axis=0)
sample_norm = (sample - sample_min) / np.maximum(sample_max - sample_min, 1e-6)
preview = np.zeros((800, 800, 3), dtype=np.uint8)
xy = sample_norm[:, :2]
px = np.clip((xy[:, 0] * 799).astype(int), 0, 799)
py = np.clip((xy[:, 1] * 799).astype(int), 0, 799)
preview[799 - py, px] = 255
Image.fromarray(preview).save(world_dir / "world_points_multiframe_preview.png")

closeout = {
    "status": "candidate-visible-proof",
    "processed_frames": world_summary["processed_frames"],
    "skipped_frames": world_summary["skipped_frames"],
    "total_points": world_summary["total_points"],
    "preview_path": str(world_dir / "world_points_multiframe_preview.png"),
    "ply_path": world_summary["ply_path"],
    "npy_path": world_summary["npy_path"],
    "per_frame_point_count": [x["point_count"] for x in per_frame],
}
(world_dir / "mrl7_closeout_summary.json").write_text(json.dumps(closeout, indent=2, ensure_ascii=False), encoding="utf-8")

first_frame = window_probe["sample_frames"][0]["frame_name"]
first_rec = window_probe["sample_frames"][0]
image = iio.imread(images_dir / first_frame)
if image.ndim == 2:
    image = np.stack([image, image, image], axis=-1)
image = image[..., :3]
target_h, target_w = image.shape[:2]
target = torch.from_numpy(image.astype(np.float32) / 255.0).to(device)

pose_index = int(first_rec["pose_record_index"])
pose_rec = pose_records[pose_index]
intr = pose_rec["imageIntrinsics"]
pose = pose_rec["pose"]
R_wc = quat_to_rot(float(pose["qx"]), float(pose["qy"]), float(pose["qz"]), float(pose["qw"]))
t_wc = np.array([float(pose["tx"]), float(pose["ty"]), float(pose["tz"])], dtype=np.float32)
R_cw = R_wc.T
t_cw = -R_cw @ t_wc
viewmat = np.eye(4, dtype=np.float32)
viewmat[:3, :3] = R_cw
viewmat[:3, 3] = t_cw
viewmat = torch.from_numpy(viewmat).to(device)
K = torch.tensor([
    [float(intr["fx"]), 0.0, float(intr["cx"])],
    [0.0, float(intr["fy"]), float(intr["cy"])],
    [0.0, 0.0, 1.0],
], dtype=torch.float32, device=device)

points_np = merged
max_points = 1024
if len(points_np) > max_points:
    pick = np.linspace(0, len(points_np) - 1, max_points).astype(np.int64)
    points_np = points_np[pick]

means = torch.nn.Parameter(torch.from_numpy(points_np).to(device))
scales = torch.nn.Parameter(torch.full((len(points_np), 3), math.log(0.03), dtype=torch.float32, device=device))
quats = torch.nn.Parameter(torch.tensor([[0.0, 0.0, 0.0, 1.0]], dtype=torch.float32, device=device).repeat(len(points_np), 1))
opacities = torch.nn.Parameter(torch.full((len(points_np),), 0.1, dtype=torch.float32, device=device))
colors = torch.nn.Parameter(torch.full((len(points_np), 3), 0.7, dtype=torch.float32, device=device))

def render_once():
    render_colors, render_alphas, _ = gsplat.rasterization(
        means=means,
        quats=torch.nn.functional.normalize(quats, dim=-1),
        scales=torch.exp(scales),
        opacities=torch.sigmoid(opacities),
        colors=colors,
        viewmats=viewmat[None, ...],
        Ks=K[None, ...],
        width=target_w,
        height=target_h,
        packed=False,
    )
    return render_colors[0], render_alphas[0]

def save_png(path: Path, tensor_img: torch.Tensor):
    arr = torch.clamp(tensor_img.detach(), 0.0, 1.0).cpu().numpy()
    Image.fromarray((arr * 255).astype(np.uint8)).save(path)

optimizer = torch.optim.Adam([means, scales, quats, opacities, colors], lr=1e-2)

pred_init, _ = render_once()
loss_init = torch.mean((pred_init - target) ** 2)
save_png(world_dir / "gaussian_render_init.png", pred_init)
torch.save({
    "means": means.detach().cpu(),
    "scales_log": scales.detach().cpu(),
    "quats": torch.nn.functional.normalize(quats.detach(), dim=-1).cpu(),
    "opacities_logit": opacities.detach().cpu(),
    "colors": colors.detach().cpu(),
}, world_dir / "gaussian_params_init.pt")

loss_history = [float(loss_init.detach().cpu().item())]
for _ in range(20):
    optimizer.zero_grad(set_to_none=True)
    pred, alpha = render_once()
    loss = torch.mean((pred - target) ** 2)
    loss.backward()
    optimizer.step()
    loss_history.append(float(loss.detach().cpu().item()))

pred_final, alpha_final = render_once()
loss_final = torch.mean((pred_final - target) ** 2)
save_png(world_dir / "gaussian_render_optim20.png", pred_final)
torch.save({
    "means": means.detach().cpu(),
    "scales_log": scales.detach().cpu(),
    "quats": torch.nn.functional.normalize(quats.detach(), dim=-1).cpu(),
    "opacities_logit": opacities.detach().cpu(),
    "colors": colors.detach().cpu(),
}, world_dir / "gaussian_params_optim20.pt")

gaussian_summary = {
    "backward_ok": True,
    "point_count": int(len(points_np)),
    "target_frame": first_frame,
    "loss_init": float(loss_init.detach().cpu().item()),
    "loss_final": float(loss_final.detach().cpu().item()),
    "loss_history_head": loss_history[:5],
    "loss_history_tail": loss_history[-5:],
    "alpha_mean_final": float(alpha_final.mean().detach().cpu().item()),
    "init_pt": str(world_dir / "gaussian_params_init.pt"),
    "optim20_pt": str(world_dir / "gaussian_params_optim20.pt"),
    "init_png": str(world_dir / "gaussian_render_init.png"),
    "optim20_png": str(world_dir / "gaussian_render_optim20.png"),
}
(world_dir / "gaussian_optim20_summary.json").write_text(json.dumps(gaussian_summary, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "window_span_sec": window_probe["window_span_sec"],
    "sample_frame_count": window_probe["sample_frame_count"],
    "processed_frames": world_summary["processed_frames"],
    "skipped_frames": len(world_summary["skipped_frames"]),
    "total_points": world_summary["total_points"],
    "loss_init": gaussian_summary["loss_init"],
    "loss_final": gaussian_summary["loss_final"],
    "world_dir": str(world_dir),
}, indent=2, ensure_ascii=False))
```

## `1000 step` 追加学習 block

```python
optimizer = torch.optim.Adam([means, scales, quats, opacities, colors], lr=1e-2)

pred_init_1000, _ = render_once()
loss_init_1000 = torch.mean((pred_init_1000 - target) ** 2)

loss_history_1000 = [float(loss_init_1000.detach().cpu().item())]
for step in range(1000):
    optimizer.zero_grad(set_to_none=True)
    pred, alpha = render_once()
    loss = torch.mean((pred - target) ** 2)
    loss.backward()
    optimizer.step()
    loss_history_1000.append(float(loss.detach().cpu().item()))

pred_final_1000, alpha_final_1000 = render_once()
loss_final_1000 = torch.mean((pred_final_1000 - target) ** 2)

save_png(world_dir / "gaussian_render_optim1000.png", pred_final_1000)
torch.save({
    "means": means.detach().cpu(),
    "scales_log": scales.detach().cpu(),
    "quats": torch.nn.functional.normalize(quats.detach(), dim=-1).cpu(),
    "opacities_logit": opacities.detach().cpu(),
    "colors": colors.detach().cpu(),
}, world_dir / "gaussian_params_optim1000.pt")

gaussian_summary_1000 = {
    "backward_ok": True,
    "point_count": int(means.shape[0]),
    "loss_init": float(loss_init_1000.detach().cpu().item()),
    "loss_final": float(loss_final_1000.detach().cpu().item()),
    "loss_history_head": loss_history_1000[:5],
    "loss_history_tail": loss_history_1000[-5:],
    "alpha_mean_final": float(alpha_final_1000.mean().detach().cpu().item()),
    "optim1000_pt": str(world_dir / "gaussian_params_optim1000.pt"),
    "optim1000_png": str(world_dir / "gaussian_render_optim1000.png"),
}
(world_dir / "gaussian_optim1000_summary.json").write_text(
    json.dumps(gaussian_summary_1000, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(json.dumps({
    "point_count": int(means.shape[0]),
    "loss_init": gaussian_summary_1000["loss_init"],
    "loss_final": gaussian_summary_1000["loss_final"],
    "optim1000_pt": gaussian_summary_1000["optim1000_pt"],
    "optim1000_png": gaussian_summary_1000["optim1000_png"],
}, indent=2, ensure_ascii=False))
```

## `MyDrive` 可視 folder への copy block

```python
from pathlib import Path
import shutil
import json

visible_dir = Path("/content/drive/MyDrive/trajectreview/modeling_visible") / session_id / "world_fusion_v01"
visible_dir.mkdir(parents=True, exist_ok=True)

targets = [
    "mrl7_window_probe.json",
    "depth_batch_manifest.json",
    "world_points_multiframe.npy",
    "world_points_multiframe.ply",
    "world_points_multiframe_preview.png",
    "world_fusion_summary.json",
    "mrl7_closeout_summary.json",
    "gaussian_params_init.pt",
    "gaussian_params_optim20.pt",
    "gaussian_render_init.png",
    "gaussian_render_optim20.png",
    "gaussian_optim20_summary.json",
    "gaussian_params_optim500.pt",
    "gaussian_render_optim500.png",
    "gaussian_optim500_summary.json",
    "gaussian_params_optim1000.pt",
    "gaussian_render_optim1000.png",
    "gaussian_optim1000_summary.json",
    "gaussian_params_optim2500.pt",
    "gaussian_render_optim2500.png",
    "gaussian_optim2500_summary.json",
]

copied = []
missing = []
for name in targets:
    src = world_dir / name
    if src.exists():
        shutil.copy2(src, visible_dir / name)
        copied.append(name)
    else:
        missing.append(name)

summary = {
    "source_world_dir": str(world_dir),
    "visible_dir": str(visible_dir),
    "copied_count": len(copied),
    "missing_count": len(missing),
    "copied": copied,
    "missing": missing,
}
print(json.dumps(summary, indent=2, ensure_ascii=False))
```

## `MRL-9` giant Gaussian branch

```python
# Step 9a giant-infer-gs entrypoint probe
from pathlib import Path
import json
import inspect
import sys

repo_root = Path("/content/Depth-Anything-3")
assert repo_root.exists(), {"repo_not_found": str(repo_root)}

src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

patterns = ["infer_gs", "gs_ply", "gs_video", "giant", "Giant", "DA3"]
hits = []

for path in repo_root.rglob("*"):
    if not path.is_file():
        continue
    if path.suffix.lower() not in {".py", ".md", ".txt", ".yaml", ".yml", ".json"}:
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for lineno, line in enumerate(text.splitlines(), start=1):
        if any(p in line for p in patterns):
            hits.append({
                "file": str(path),
                "line": lineno,
                "text": line.strip(),
            })

from depth_anything_3.api import DepthAnything3

summary = {
    "repo_root": str(repo_root),
    "src_root": str(src_root),
    "api_import_ok": True,
    "from_pretrained_sig": str(inspect.signature(DepthAnything3.from_pretrained)),
    "api_init_sig": str(inspect.signature(DepthAnything3.__init__)),
    "hit_count": len(hits),
    "hits_head": hits[:80],
}

probe_path = Path("/content/mrl9_entrypoint_probe.json")
probe_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "probe_path": str(probe_path),
    "hit_count": summary["hit_count"],
    "from_pretrained_sig": summary["from_pretrained_sig"],
    "api_init_sig": summary["api_init_sig"],
}, indent=2, ensure_ascii=False))
for item in summary["hits_head"][:40]:
    print(f"{item['file']}:{item['line']}: {item['text']}")
```
