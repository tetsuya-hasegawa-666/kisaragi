# DA3 Colab Clean Bootstrap Runbook

## 文書の役割

- この文書は `prj-kisaragi_0002` の `DA3Metric-Large` `Colab` 実行について、fresh runtime からの最短 clean bootstrap を保持する product-side runbook とする。
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

## 現在の status

- `candidate` はあり
- `adopted` は未成立
- 現在の blocker は、`Step 3` で `plyfile` が未install のため `depth_anything_3.api` import が止まる点である
- 現在は blank restart を強制せず、同じ runtime で blocker を潰しながら bootstrap 仕様を確定する段階である

## 事前準備

- `Google Colab` notebook を新規に開く
- `Runtime` は可能なら `T4` 以上の GPU を選ぶ
- `Google Drive` を mount できる account で入る
- 対象 folder id `1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_` への access があることを確認する
- `GPU` を選べても、初回は `CPU` で bootstrap / import / 1 frame まで進めてよい

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

## Candidate Bootstrap v1

### 目的

- `Google Drive` shortcut 配下の session zip を読み、`session_root` を正規化し、`DA3Metric-Large` の `1 frame` 推論まで進む。

### 前提

- `事前準備` と `準備確認` が済んでいる
- 対象 folder id は `1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_`
- 対象 zip は `trajectreview/correcting/session-20260328-103250.zip`
- 結果出力先は `trajectreview/results/da3_smoke_v24/`

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

### Step 2: DA3 repo と custom dependency を fresh runtime へ入れる

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
run(["python", "-m", "pip", "install", "--quiet", "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile"])
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

### Step 4: `1 frame` 推論を実行する

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
conf = np.asarray(prediction.conf[0])
intrinsics = np.asarray(prediction.intrinsics[0])
extrinsics = np.asarray(prediction.extrinsics[0])

depth_min = float(depth.min())
depth_max = float(depth.max())
depth_norm = np.zeros_like(depth, dtype=np.float32) if depth_max <= depth_min else (depth - depth_min) / (depth_max - depth_min)
Image.fromarray((depth_norm * 255).astype(np.uint8)).save(OUTPUT_ROOT / "depth_preview.png")

np.save(OUTPUT_ROOT / "depth_raw.npy", depth)
np.save(OUTPUT_ROOT / "conf_raw.npy", conf)
np.save(OUTPUT_ROOT / "intrinsics.npy", intrinsics)
np.save(OUTPUT_ROOT / "extrinsics.npy", extrinsics)

summary = {
    "image_path": str(image_path),
    "device": str(device),
    "depth_shape": list(depth.shape),
    "conf_shape": list(conf.shape),
    "intrinsics_shape": list(intrinsics.shape),
    "extrinsics_shape": list(extrinsics.shape),
    "depth_min": depth_min,
    "depth_max": depth_max,
}

(OUTPUT_ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
print("saved:", OUTPUT_ROOT)
```

### 成功判定

- `session_root_exists True`
- `images_dir_exists True`
- `image_count >= 1`
- `src_root_exists True`
- `import_ok` が出る
- `summary.json` が生成される
- `depth_preview.png`、`depth_raw.npy`、`conf_raw.npy`、`intrinsics.npy`、`extrinsics.npy` が保存される

## Adopted Bootstrap

- 未確定
- admin 実測で fresh runtime から end-to-end 完了した時に、ここへ `truly pass` 手順を昇格する
