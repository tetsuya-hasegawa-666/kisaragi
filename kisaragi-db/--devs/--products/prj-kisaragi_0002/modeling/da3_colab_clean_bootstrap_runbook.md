# DA3 Colab Clean Bootstrap Runbook

## 文書の役割

- この文書は `prj-kisaragi_0002` の `DA3Metric-Large` `Colab` 実行について、fresh runtime から `DA3Metric-Large` による `3DGS` 系主空間モデル生成まで進めるための clean bootstrap と作業導線を保持する product-side runbook とする。
- shared worklog の trial 往復をそのまま正本化せず、真に必要だった command と file 操作だけを抽出して保持する。
- `candidate` は現時点の最短候補、`adopted` は admin 実測で end-to-end 完了した `truly pass` 手順を示す。

## blank workspace 前提

- この文書は、`Colab` の fresh runtime、つまり `/content/` 配下に前回の clone や install が残っていない状態から始める前提で書く。
- admin は「前回の途中状態を引き継げる」と仮定せず、まずこの文書の `事前準備` と `準備確認` を実行する。
- 途中状態から再開するのは、bootstrap 自体の failure を切り分ける時だけに限定する。

## 運用 rule

- `Colab` runtime が揮発した時は、途中 patch の継ぎ足しより、この runbook の先頭からやり直すことを既定とする。
- shared worklog に新しい回避策が出た時は、この文書へ昇格が必要かを同じ task 内で判断する。
- `truly pass` と表現してよいのは、fresh runtime からこの runbook の `adopted` 手順で end-to-end 完了した時だけとする。
- ただし、bootstrap 仕様の未確定点を詰めている途中は、現在の runtime を維持したまま blocker を 1 件ずつ解消し、その結果をこの文書へ反映してよい。

## 事前準備

- `Google Colab` notebook を新規に開く
- `Runtime` は可能なら `T4` 以上の GPU を選ぶ
- `Google Drive` を mount できる account で入る
- 対象 folder id `1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_` への access があることを確認する
- `GPU` を選べても、初回は `CPU` で bootstrap / import / 1 frame まで進めてよい
- 運用の目安として、`Step 1` から `Step 3` は `CPU` または `GPU` のどちらでも進めてよい
- `Step 4` は `CPU` だと極端に遅いか停止しやすいため、`GPU` runtime を推奨する

## 準備確認

### 準備確認 1: runtime と Drive mount の確認

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

OK 条件:

- `drive_exists True`
- `mydrive_exists True`
- `shortcut_root_exists True`
- `cuda_available` は `True` が理想。`False` でも bootstrap は進められる。今回の初回確認は `CPU` 前提でもよい

### 準備確認 2: 対象 folder と zip の存在確認

```python
from pathlib import Path

folder_root = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_")
zip_path = folder_root / "trajectreview" / "correcting" / "session-20260328-103250.zip"

print("folder_root_exists", folder_root.exists(), folder_root)
print("zip_exists", zip_path.exists(), zip_path)
```

OK 条件:

- `folder_root_exists True`
- `zip_exists True`

### 準備確認 3: blank workspace であることの確認

```python
from pathlib import Path

print("repo_exists_before_bootstrap", Path("/content/Depth-Anything-3").exists())
print("extract_root_exists_before_bootstrap", Path("/content/trajectreview_input").exists())
```

OK 条件:

- 両方 `False` が理想
- `True` の時は、この runbook の Step 1 と Step 2 が削除して作り直すので、そのまま続けてよい

## install 正本

- この runbook で使う install / bootstrap command の正本はこの節とする。
- shared worklog に trial が残っていても、採用する install 手順はここだけを見る。
- `3DGS` 系主空間モデル生成 smoke まで進む時は、`gsplat` install を含める。

### install 1: DA3 repo clone

```bash
git clone https://github.com/ByteDance-Seed/Depth-Anything-3.git /content/Depth-Anything-3
```

### install 2: DA3 import と export lazy-path に必要な custom dependency

```bash
python -m pip install --quiet addict evo moviepy==1.0.3 pygame pycolmap plyfile trimesh
```

### install 3: `3DGS` smoke 用 `gsplat`

```bash
python -m pip install --quiet gsplat
```

### install 4: install 結果の最小確認

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

OK 条件:

- `repo_root_exists True`
- `src_root_exists True`
- `depth_anything_3_import_ok` が出る
- `gsplat_module` が出る

補足:

- `gsplat` は single-frame depth bootstrap だけなら optional だったが、この runbook の現在目的は `3DGS` 系主空間モデル生成 smoke まで含むため、install 正本に昇格した。
- 以後 `3DGS` smoke まで進める時は、`pip install gsplat` を省略しない。

## Candidate Bootstrap v1

### 目的

- `Google Drive` shortcut 配下の session zip を読み、`session_root` を正規化し、`DA3Metric-Large` の `1 frame` 推論、world back-projection、point export、`gsplat` rasterization、`gs_model` / `SpacePackage` smoke artifact 生成まで進む。

### 前提

- `事前準備` と `準備確認` が済んでいる
- 対象 folder id は `1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_`
- 対象 zip は `trajectreview/correcting/session-20260328-103250.zip`
- 結果出力先は `trajectreview/results/da3_smoke_v05/`

### Step 1: session zip を unzip して `session_root` を正規化する

```python
from pathlib import Path
import shutil
import zipfile

zip_path = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/session-20260328-103250.zip")
extract_root = Path("/content/trajectreview_input")

if extract_root.exists():
    shutil.rmtree(extract_root)
extract_root.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(extract_root)

session_root = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
images_dir = session_root / "images"

print("session_root_exists", session_root.exists(), session_root)
print("images_dir_exists", images_dir.exists(), images_dir)
files = sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.jpeg"))
print("image_count", len(files))
if files:
    print("first_image", files[0])
```

### Step 2: DA3 repo と dependency を fresh runtime へ入れる

```python
import shutil
import subprocess
from pathlib import Path

def run(cmd):
    print("RUN", " ".join(cmd))
    subprocess.run(cmd, check=True)

repo_root = Path("/content/Depth-Anything-3")
if repo_root.exists():
    shutil.rmtree(repo_root)

run(["git", "clone", "https://github.com/ByteDance-Seed/Depth-Anything-3.git", str(repo_root)])
run(["python", "-m", "pip", "install", "--quiet", "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile", "trimesh", "gsplat"])
print("bootstrap_done", repo_root.exists(), repo_root)
```

### Step 3: repo path を attach して import を確認する

```python
import sys
from pathlib import Path

REPO_ROOT = Path("/content/Depth-Anything-3")
assert REPO_ROOT.exists(), f"repo not found: {REPO_ROOT}"

src_root = REPO_ROOT / "src"
print("src_root_exists", src_root.exists(), src_root)
assert src_root.exists(), f"src not found: {src_root}"

src_str = str(src_root)
if src_str not in sys.path:
    sys.path.insert(0, src_str)

from depth_anything_3.api import DepthAnything3
print("import_ok", DepthAnything3)
```

補足:

- `Dependency gsplat is required for rendering 3DGS` の warning は、`DepthAnything3` import 時に `3DGS rendering` 系 code path が見えていることを示す。
- 現在の runbook では `DA3Metric-Large` metric depth と `3DGS` 系主空間モデル生成 smoke までを対象にするため、`gsplat` は必須 dependency として install する。

### Step 4: `1 frame` 推論を実行する

- 推奨:
  - `cuda_available True` の状態で実行する
  - `CPU` のままでも試せるが、途中停止や長時間待機が起きやすい
  - `Step 1` から `Step 3` が通った時点でいったん止め、後で `GPU` runtime に切り替えて `Step 4` から再開してよい

```python
import json
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from depth_anything_3.api import DepthAnything3

SESSION_ROOT = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
OUTPUT_ROOT = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v24")
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

images = sorted((SESSION_ROOT / "images").glob("*.png")) + sorted((SESSION_ROOT / "images").glob("*.jpg")) + sorted((SESSION_ROOT / "images").glob("*.jpeg"))
assert images, f"images not found under {SESSION_ROOT / 'images'}"

image_path = images[0]
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = DepthAnything3.from_pretrained("depth-anything/DA3METRIC-LARGE").to(device=device)
prediction = model.inference([str(image_path)])

depth = np.asarray(prediction.depth[0])
conf = None if prediction.conf is None else np.asarray(prediction.conf[0])
intrinsics = None if prediction.intrinsics is None else np.asarray(prediction.intrinsics[0])
extrinsics = None if prediction.extrinsics is None else np.asarray(prediction.extrinsics[0])

depth_min = float(depth.min())
depth_max = float(depth.max())
depth_norm = np.zeros_like(depth, dtype=np.float32) if depth_max <= depth_min else (depth - depth_min) / (depth_max - depth_min)
Image.fromarray((depth_norm * 255).astype(np.uint8)).save(OUTPUT_ROOT / "depth_preview.png")

np.save(OUTPUT_ROOT / "depth_raw.npy", depth)
if conf is not None:
    np.save(OUTPUT_ROOT / "conf_raw.npy", conf)
if intrinsics is not None:
    np.save(OUTPUT_ROOT / "intrinsics.npy", intrinsics)
if extrinsics is not None:
    np.save(OUTPUT_ROOT / "extrinsics.npy", extrinsics)

summary = {
    "image_path": str(image_path),
    "device": str(device),
    "depth_shape": list(depth.shape),
    "conf_shape": None if conf is None else list(conf.shape),
    "intrinsics_shape": None if intrinsics is None else list(intrinsics.shape),
    "extrinsics_shape": None if extrinsics is None else list(extrinsics.shape),
    "depth_min": depth_min,
    "depth_max": depth_max,
}

(OUTPUT_ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
print("saved:", OUTPUT_ROOT)
```

### Step 4.5: `gsplat` surface を最小確認する

```python
import gsplat

print("gsplat_version", getattr(gsplat, "__version__", "unknown"))
print("rasterization_type", type(gsplat.rasterization).__name__)
print("rasterization_2dgs_type", type(gsplat.rasterization_2dgs).__name__)
print("fully_fused_projection_type", type(gsplat.fully_fused_projection).__name__)
```

OK 条件:

- `gsplat_version` が出る
- `rasterization_type function`
- `rasterization_2dgs_type function`
- `fully_fused_projection_type function`

### Step 5: `3DGS` smoke candidate を生成する

- ここからは single-frame depth bootstrap の上に、world back-projection、point export、`gsplat` rasterization、`SpacePackage` smoke contract を積む。
- 完全な試行錯誤ログは shared worklog に残すが、採用済みの最小到達物はこの節で追えるようにする。

#### Step 5a: session file 配置を確認する

```python
from pathlib import Path

SESSION_ROOT = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
SESSION_BUNDLE_ROOT = SESSION_ROOT.parent
arcore_pose_path = SESSION_ROOT / "arcore_pose.jsonl"
if not arcore_pose_path.exists():
    arcore_pose_path = SESSION_BUNDLE_ROOT / "arcore_pose.jsonl"

print("session_root_exists", SESSION_ROOT.exists(), SESSION_ROOT)
print("bundle_root_exists", SESSION_BUNDLE_ROOT.exists(), SESSION_BUNDLE_ROOT)
print("arcore_pose_exists", arcore_pose_path.exists(), arcore_pose_path)
print("frame_pose_index_exists", (SESSION_ROOT / "frame_pose_index.csv").exists())
print("camera_calibration_exists", (SESSION_ROOT / "camera_calibration_summary.json").exists())
print("images_exists", (SESSION_ROOT / "images").exists())
```

#### Step 5b: world point export を生成する

```python
from pathlib import Path
import json
import numpy as np
import pandas as pd

SESSION_ROOT = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
SESSION_BUNDLE_ROOT = SESSION_ROOT.parent
OUTPUT_ROOT = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v05")
arcore_pose_path = SESSION_ROOT / "arcore_pose.jsonl"
if not arcore_pose_path.exists():
    arcore_pose_path = SESSION_BUNDLE_ROOT / "arcore_pose.jsonl"

depth = np.load(OUTPUT_ROOT / "depth_raw.npy")
frame_index = pd.read_csv(SESSION_ROOT / "frame_pose_index.csv")

with open(arcore_pose_path, "r", encoding="utf-8") as f:
    pose_records = [json.loads(line) for line in f if line.strip()]

row = frame_index.iloc[0]
pose_idx = int(row["pose_record_index"])
record = pose_records[pose_idx]
pose = record["pose"]
intr = record["imageIntrinsics"]

h, w = depth.shape
grid_y, grid_x = np.mgrid[0:h:24, 0:w:24]
z = depth[grid_y, grid_x]
x = (grid_x - intr["cx"]) * z / intr["fx"]
y = (grid_y - intr["cy"]) * z / intr["fy"]
camera_points = np.stack([x, y, z], axis=-1).reshape(-1, 3)

tx, ty, tz = pose["tx"], pose["ty"], pose["tz"]
world_points = camera_points + np.array([tx, ty, tz], dtype=np.float32)

np.save(OUTPUT_ROOT / "world_points_smoke.npy", world_points.astype(np.float32))

ply_path = OUTPUT_ROOT / "world_points_smoke.ply"
with open(ply_path, "w", encoding="utf-8") as f:
    f.write("ply\nformat ascii 1.0\n")
    f.write(f"element vertex {len(world_points)}\n")
    f.write("property float x\nproperty float y\nproperty float z\n")
    f.write("end_header\n")
    for p in world_points:
        f.write(f"{p[0]} {p[1]} {p[2]}\n")

print("points_shape", world_points.shape)
print("saved_npy", OUTPUT_ROOT / "world_points_smoke.npy")
print("saved_ply", ply_path)
```

#### Step 5c: `gsplat` 最小 render と smoke artifact を生成する

```python
from pathlib import Path
import json
import numpy as np
from PIL import Image
import torch
import gsplat

SESSION_ROOT = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
SESSION_BUNDLE_ROOT = SESSION_ROOT.parent
OUTPUT_ROOT = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v05")
arcore_pose_path = SESSION_ROOT / "arcore_pose.jsonl"
if not arcore_pose_path.exists():
    arcore_pose_path = SESSION_BUNDLE_ROOT / "arcore_pose.jsonl"

points = np.load(OUTPUT_ROOT / "world_points_smoke.npy").astype(np.float32)[:128]

with arcore_pose_path.open("r", encoding="utf-8") as f:
    poses = [json.loads(line) for line in f if line.strip()]
pose = poses[1]
intr = pose["imageIntrinsics"]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
means = torch.tensor(points, dtype=torch.float32, device=device)
quats = torch.tensor([[1.0, 0.0, 0.0, 0.0]] * len(points), dtype=torch.float32, device=device)
scales = torch.full((len(points), 3), 0.02, dtype=torch.float32, device=device)
opacities = torch.full((len(points),), 0.5, dtype=torch.float32, device=device)
colors = torch.full((len(points), 3), 0.7, dtype=torch.float32, device=device)
viewmats = torch.eye(4, dtype=torch.float32, device=device)[None, ...]
Ks = torch.tensor([[
    [float(intr["fx"]), 0.0, float(intr["cx"])],
    [0.0, float(intr["fy"]), float(intr["cy"])],
    [0.0, 0.0, 1.0],
]], dtype=torch.float32, device=device)

render_colors, render_alphas, info = gsplat.rasterization(
    means=means,
    quats=quats,
    scales=scales,
    opacities=opacities,
    colors=colors,
    viewmats=viewmats,
    Ks=Ks,
    width=int(intr["width"]),
    height=int(intr["height"]),
    packed=False,
)

img = (render_colors[0].detach().clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)
Image.fromarray(img).save(OUTPUT_ROOT / "gsplat_render_smoke.png")

gs_model = {
    "artifact_type": "gs_model_smoke",
    "renderer": "gsplat",
    "num_points": int(len(points)),
    "render_png": "gsplat_render_smoke.png",
    "point_source": "world_points_smoke.npy",
    "image_size": [int(intr["width"]), int(intr["height"])],
    "device": str(device),
}
space_quality = {
    "gsplat_rasterization_smoke": "pass",
    "point_count": int(len(points)),
    "render_png": "gsplat_render_smoke.png",
    "info_keys": sorted(info.keys()),
}
space_package = {
    "coordinate_system": "arcore_local",
    "camera_path_source": arcore_pose_path.name,
    "gs_model": {
        "artifact_type": "gs_model_smoke",
        "renderer": "gsplat",
        "manifest_path": "gs_model_smoke.json",
        "preview_path": "gsplat_render_smoke.png",
        "point_cloud_npy": "world_points_smoke.npy",
        "point_cloud_ply": "world_points_smoke.ply",
    },
    "quality": space_quality,
}

(OUTPUT_ROOT / "gs_model_smoke.json").write_text(json.dumps(gs_model, indent=2), encoding="utf-8")
(OUTPUT_ROOT / "space_quality_smoke.json").write_text(json.dumps(space_quality, indent=2), encoding="utf-8")
(OUTPUT_ROOT / "space_package_smoke.json").write_text(json.dumps(space_package, indent=2), encoding="utf-8")

print("device", device)
print("render_colors_shape", tuple(render_colors.shape))
print("render_alphas_shape", tuple(render_alphas.shape))
print("info_keys", sorted(info.keys()))
print("saved", OUTPUT_ROOT)
```

#### Step 5d: contract 名へ寄せる

```python
from pathlib import Path
import shutil

OUTPUT_ROOT = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v05")

shutil.copy2(OUTPUT_ROOT / "gs_model_smoke.json", OUTPUT_ROOT / "gs_model.contract.json")
shutil.copy2(OUTPUT_ROOT / "space_quality_smoke.json", OUTPUT_ROOT / "space_quality.contract.json")
shutil.copy2(OUTPUT_ROOT / "space_package_smoke.json", OUTPUT_ROOT / "space_package.contract.json")

for name in [
    "gs_model.contract.json",
    "space_quality.contract.json",
    "space_package.contract.json",
]:
    print(name, (OUTPUT_ROOT / name).exists())
```

### Step 5 の到達 artifact

- `depth_raw.npy`
- `depth_preview.png`
- `world_points_smoke.npy`
- `world_points_smoke.ply`
- `gsplat_render_smoke.png`
- `gs_model_smoke.json`
- `space_quality_smoke.json`
- `space_package_smoke.json`
- `gs_model.contract.json`
- `space_quality.contract.json`
- `space_package.contract.json`

### 成功判定

- `session_root_exists True`
- `images_dir_exists True`
- `image_count >= 1`
- `src_root_exists True`
- `import_ok` が出る
- `summary.json` が生成される
- `depth_preview.png` と `depth_raw.npy` が保存される
- `conf_raw.npy`、`intrinsics.npy`、`extrinsics.npy` は `None` でなければ保存される
- `world_points_smoke.npy` と `world_points_smoke.ply` が保存される
- `gsplat_render_smoke.png`、`gs_model_smoke.json`、`space_quality_smoke.json` が保存される
- `space_package_smoke.json`、`gs_model.contract.json`、`space_quality.contract.json`、`space_package.contract.json` が保存される
