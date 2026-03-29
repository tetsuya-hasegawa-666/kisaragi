# sharedlogs_da3-colab.md

## 役割

- この file は `prj-kisaragi_0002` の `DA3Metric-Large` `Colab` 実装について、admin と Codex が notebook cell、script、error、観測結果を往復するための collaborative worklog とする。
- この file は `project-truth.md`、`ux-b2t-hypo.md`、admin evidence の代替ではない。
- この file は project に対する truth / plan / evidence の正本ではないが、共同作業の保持情報としては authoritative な worklog とし、正本反映の根拠 log として保持する。

## 読み方

- 固定 header はこの節までとする。
- これより下は `# codex` または `# admin` 見出しによる時系列追記だけを置く。
- 正規読み順は「最下部から上へ」とする。

## 記載ルール

- 途中挿入、途中修正、本文中ほどへの要約追記を禁止する。
- 既存本文は原則として書き換えず、必ず最下部へ追記する。
- `# codex` の追記は、必ず単調増加の通し番号 `v**` を付ける。
- 長い code と error は code block のまま貼る。
- shared rule 変更は `AGENTS.md`、project truth / plan / current 変更は `project-truth.md` と `ux-b2t-hypo.md`、gate 判定根拠は admin evidence へ別途反映する。

# codex

2026-03-29 v01 reset for fresh restart。

- この log は blank workspace からの再開用に初期化した。
- `DA3 Colab bootstrap` の正本は [da3_colab_clean_bootstrap_runbook.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\modeling\da3_colab_clean_bootstrap_runbook.md) とする。
- admin はまず正本の次の章を上から順に見る。
  - `blank workspace 前提`
  - `事前準備`
  - `準備確認`
  - `現在の status`
  - `Candidate Bootstrap v1`
  - `成功判定`
- この log は、上記正本を実行した結果を貼り戻す場所として使う。
- 現在の進捗は白紙に戻し、次回結果は fresh runtime からのものだけを残す。

# admin

```text
# 準備確認 1 res
Mounted at /content/drive
cwd /content
cuda_available False
drive_exists True
mydrive_exists True
shortcut_root_exists True
```

# admin

```text
# 準備確認 2 res
folder_root_exists True /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_
zip_exists True /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/session-20260328-103250.zip

```

# admin

```text
# 準備確認 3 res
repo_exists_before_bootstrap False
extract_root_exists_before_bootstrap False

```

# admin

```text
# Candidate Bootstrap v1 progress res
Step 1:
session_root_exists True /content/trajectreview_input/session-20260328-103250/trajectreview
images_dir_exists True /content/trajectreview_input/session-20260328-103250/trajectreview/images
image_count 182
first_image /content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000009.jpg

Step 2:
RUN git clone https://github.com/ByteDance-Seed/Depth-Anything-3.git /content/Depth-Anything-3
RUN python -m pip install --quiet addict evo moviepy==1.0.3 pygame pycolmap
bootstrap_done True /content/Depth-Anything-3

Step 3:
src_root_exists True /content/Depth-Anything-3/src
/usr/local/lib/python3.12/dist-packages/moviepy/config_defaults.py:47: SyntaxWarning: invalid escape sequence '\P'
  IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-6.8.8-Q16\magick.exe"
/usr/local/lib/python3.12/dist-packages/moviepy/video/io/ffmpeg_reader.py:294: SyntaxWarning: invalid escape sequence '\d'
  lines_video = [l for l in lines if ' Video: ' in l and re.search('\d+x\d+', l)]
/usr/local/lib/python3.12/dist-packages/moviepy/video/io/ffmpeg_reader.py:367: SyntaxWarning: invalid escape sequence '\d'
  rotation_lines = [l for l in lines if 'rotate          :' in l and re.search('\d+$', l)]
/usr/local/lib/python3.12/dist-packages/moviepy/video/io/ffmpeg_reader.py:370: SyntaxWarning: invalid escape sequence '\d'
  match = re.search('\d+$', rotation_line)
WARNING:py.warnings:/usr/local/lib/python3.12/dist-packages/moviepy/video/io/sliders.py:61: SyntaxWarning: "is" with 'str' literal. Did you mean "=="?
  if event.key is 'enter':

[WARN ] Dependency `gsplat` is required for rendering 3DGS. Install via: pip install git+https://github.com/nerfstudio-project/gsplat.git@0b4dddf04cb687367602c01196913cde6a743d70
---------------------------------------------------------------------------
ModuleNotFoundError                       Traceback (most recent call last)
/tmp/ipykernel_1078/2459757094.py in <cell line: 0>()
     13     sys.path.insert(0, src_str)
     14 
---> 15 from depth_anything_3.api import DepthAnything3
     16 print("import_ok", DepthAnything3)

3 frames
/content/Depth-Anything-3/src/depth_anything_3/utils/gsply_helpers.py in <module>
     17 import torch
     18 from einops import rearrange, repeat
---> 19 from plyfile import PlyData, PlyElement
     20 from torch import Tensor
     21 

ModuleNotFoundError: No module named 'plyfile'

---------------------------------------------------------------------------
NOTE: If your import is failing due to a missing package, you can
manually install dependencies using either !pip or !apt.

To view examples of installing some common dependencies, click the
"Open Examples" button below.
---------------------------------------------------------------------------

Step 4:

blocker:

```

# codex

2026-03-29 v02 continue on current runtime。

- ここからは blank restart に戻さず、現在の runtime を維持したまま blocker を解消し、bootstrap 仕様へ反映します。
- `Step 3` の blocker は `src_root` ではなく、`plyfile` 未install です。
- したがって次は `plyfile` だけ追加し、同じ runtime で `Step 3` を再試行します。

```python
# Step 3 dependency fix v02
import subprocess

subprocess.run(["python", "-m", "pip", "install", "--quiet", "plyfile"], check=True)
print("plyfile_install_ok")
```

```python
# Step 3 retry v02
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

# admin

```text
# Step 3 dependency fix v02 res
plyfile_install_ok
```

# admin

```text
# Step 3 retry v02 res
src_root_exists True /content/Depth-Anything-3/src
---------------------------------------------------------------------------
ModuleNotFoundError                       Traceback (most recent call last)
/tmp/ipykernel_1078/827092518.py in <cell line: 0>()
     14     sys.path.insert(0, src_str)
     15 
---> 16 from depth_anything_3.api import DepthAnything3
     17 print("import_ok", DepthAnything3)

3 frames
/content/Depth-Anything-3/src/depth_anything_3/utils/export/glb.py in <module>
     17 import os
     18 import numpy as np
---> 19 import trimesh
     20 
     21 from depth_anything_3.specs import Prediction

ModuleNotFoundError: No module named 'trimesh'

---------------------------------------------------------------------------
NOTE: If your import is failing due to a missing package, you can
manually install dependencies using either !pip or !apt.

To view examples of installing some common dependencies, click the
"Open Examples" button below.
---------------------------------------------------------------------------
```

# codex

2026-03-29 v03 continue on current runtime。

- `plyfile` は越えました。
- 次の blocker は `trimesh` 未install です。
- 同じ runtime を維持し、`trimesh` を追加して `Step 3` を再試行します。

```python
# Step 3 dependency fix v03
import subprocess

subprocess.run(["python", "-m", "pip", "install", "--quiet", "trimesh"], check=True)
print("trimesh_install_ok")
```

```python
# Step 3 retry v03
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

# admin

```text
# Step 3 dependency fix v03 res
trimesh_install_ok
```

# admin

```text
# Step 3 retry v03 res
src_root_exists True /content/Depth-Anything-3/src
import_ok <class 'depth_anything_3.api.DepthAnything3'>
```

# codex

2026-03-29 v04 continue on current runtime。

- `Step 3` は通過しました。
- 次は `Step 4` の `1 frame` 推論を実行し、保存 artifact と summary を確認します。

```python
# Step 4 run v04
import json
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from depth_anything_3.api import DepthAnything3

SESSION_ROOT = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
OUTPUT_ROOT = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v04")
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

# admin

```text
# Step 4 run v04 res
WARNING:py.warnings:/usr/local/lib/python3.12/dist-packages/huggingface_hub/utils/_auth.py:94: UserWarning: 
The secret `HF_TOKEN` does not exist in your Colab secrets.
To authenticate with the Hugging Face Hub, create a token in your settings tab (https://huggingface.co/settings/tokens), set it as secret in your Google Colab and restart your session.
You will be able to reuse this secret in all of your notebooks.
Please note that authentication is recommended but still optional to access public models or datasets.
  warnings.warn(

Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
WARNING:huggingface_hub.utils._http:Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
config.json: 100%
 847/847 [00:00<00:00, 42.1kB/s]
[INFO ] using MLP layer as FFN
model.safetensors: 100%
 1.34G/1.34G [00:12<00:00, 134MB/s]
[INFO ] Processed Images Done taking 0.18443822860717773 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 90.08614325523376 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0011453628540039062 seconds
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
/tmp/ipykernel_1078/826605900.py in <cell line: 0>()
     21 
     22 depth = np.asarray(prediction.depth[0])
---> 23 conf = np.asarray(prediction.conf[0])
     24 intrinsics = np.asarray(prediction.intrinsics[0])
     25 extrinsics = np.asarray(prediction.extrinsics[0])

TypeError: 'NoneType' object is not subscriptable
```

# codex

2026-03-29 v05 continue on current runtime。

- T4 上で core 推論自体は通過しています。
- 現在の blocker は `prediction.conf` が `None` なのに、保存処理で必須扱いしている点です。
- `HF_TOKEN` warning は public model download では optional なので、今は無視して進めてよいです。
- 次は `conf` / `intrinsics` / `extrinsics` を optional 扱いにした `Step 4` を再実行します。

```python
# Step 4 rerun v05
import json
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from depth_anything_3.api import DepthAnything3

SESSION_ROOT = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
OUTPUT_ROOT = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v05")
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

# admin

```text
# Step 4 rerun v05 res
[INFO ] using MLP layer as FFN
[INFO ] Processed Images Done taking 0.013252019882202148 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.47681665420532227 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0010962486267089844 seconds
{
  "image_path": "/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000009.jpg",
  "device": "cuda",
  "depth_shape": [
    378,
    504
  ],
  "conf_shape": null,
  "intrinsics_shape": null,
  "extrinsics_shape": null,
  "depth_min": 0.31544607877731323,
  "depth_max": 4.0310516357421875
}
saved: /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v05

```

# codex

2026-03-29 v06 bootstrap success。

- `Adopted Bootstrap v1` を成立として扱います。
- ここまでの single-frame bootstrap は end-to-end で通過しました。
- この結果は次の candidate evidence に反映済みです。
  - `INITRL-1`
  - `mINITRL-1.2`
  - `MRL-11`
  - `mRL-11.1`
  - `MRL-12`
  - `mRL-12.2`
- 次段は bootstrap そのものではなく、request 起点 UX、waiting ring、download URL、複数 frame / route 比較です。

# codex

2026-03-29 v07 next action。

- 次段の主目標は、`DA3Metric-Large` による `3DGS` 系主空間モデル生成までの system 構築です。
- 最初の action は `gsplat` import probe を通し、runtime 上で必要 package と import path を確定することです。
- その後に `ARCore pose` / intrinsics と depth の整列確認、world projection、実データ由来の最小 `3DGS` 系主空間モデル生成へ進みます。
- 実行結果を返してもらえれば、次の block を出します。

```python
# Step 5a gsplat import probe
import importlib
import sys

targets = ["gsplat", "gsplat.rendering", "gsplat.rasterization"]

for name in targets:
    try:
        mod = importlib.import_module(name)
        print("IMPORT_OK", name, getattr(mod, "__file__", "no_file"))
        print("VERSION", getattr(mod, "__version__", "no_version"))
    except Exception as exc:
        print("IMPORT_NG", name, type(exc).__name__, str(exc))

print("python", sys.version)
```

# admin

```text
# Step 5a gsplat import probe res
IMPORT_NG gsplat ModuleNotFoundError No module named 'gsplat'
IMPORT_NG gsplat.rendering ModuleNotFoundError No module named 'gsplat'
IMPORT_NG gsplat.rasterization ModuleNotFoundError No module named 'gsplat'
python 3.12.13 (main, Mar  4 2026, 09:23:07) [GCC 11.4.0]
```

# codex

2026-03-29 v08 next action。

- `gsplat` は未 install であることが確認できました。
- 次は、`pip` でそのまま入るか、wheel / build blocker があるかを切り分けます。
- 目的は install 成功そのものではなく、`Colab Python 3.12 + 現 runtime` で採れる最短 route を確定することです。

```python
# Step 5b gsplat install probe
import subprocess
import sys

cmds = [
    [sys.executable, "-m", "pip", "show", "gsplat"],
    [sys.executable, "-m", "pip", "install", "-q", "gsplat"],
    [sys.executable, "-m", "pip", "show", "gsplat"],
]

for cmd in cmds:
    print("RUN", " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print("RETURN_CODE", proc.returncode)
    if proc.stdout:
        print("STDOUT")
        print(proc.stdout)
    if proc.stderr:
        print("STDERR")
        print(proc.stderr)
```

# admin

```text
# Step 5b gsplat install probe res
RUN /usr/bin/python3 -m pip show gsplat
RETURN_CODE 1
STDERR
WARNING: Package(s) not found: gsplat

RUN /usr/bin/python3 -m pip install -q gsplat
RETURN_CODE 0
STDOUT
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6.5/6.5 MB 60.3 MB/s eta 0:00:00
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 56.3/56.3 kB 5.8 MB/s eta 0:00:00
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 180.7/180.7 kB 20.4 MB/s eta 0:00:00

RUN /usr/bin/python3 -m pip show gsplat
RETURN_CODE 0
STDOUT
Name: gsplat
Version: 1.5.3
Summary: Python package for differentiable rasterization of gaussians
Home-page: https://github.com/nerfstudio-project/gsplat
Author: 
Author-email: 
License: 
Location: /usr/local/lib/python3.12/dist-packages
Requires: jaxtyping, ninja, numpy, rich, torch
Required-by: 
```

# codex

2026-03-29 v09 next action。

- `Step 5b` は成功です。`gsplat 1.5.3` の install までは current runtime で通りました。
- 次は install 後の import 再確認を行い、module path と version が runtime から読めるかを確認します。
- これが通ったら world projection probe へ進みます。

```python
# Step 5c gsplat import reprobe
import importlib

targets = ["gsplat", "gsplat.rendering", "gsplat.rasterization"]

for name in targets:
    try:
        mod = importlib.import_module(name)
        print("IMPORT_OK", name, getattr(mod, "__file__", "no_file"))
        print("VERSION", getattr(mod, "__version__", "no_version"))
    except Exception as exc:
        print("IMPORT_NG", name, type(exc).__name__, str(exc))
```

# admin

```text
# Step 5c gsplat import reprobe res
IMPORT_OK gsplat /usr/local/lib/python3.12/dist-packages/gsplat/__init__.py
VERSION 1.5.3
IMPORT_OK gsplat.rendering /usr/local/lib/python3.12/dist-packages/gsplat/rendering.py
VERSION no_version
IMPORT_NG gsplat.rasterization ModuleNotFoundError No module named 'gsplat.rasterization'

```

# codex

2026-03-29 v10 next action。

- `Step 5c` は部分成功です。`gsplat` 本体と `gsplat.rendering` は import 済みです。
- NG は `gsplat.rasterization` だけで、これは module 不在か public API 名変更の可能性が高いです。
- 次は package 内の公開 symbol と submodule 一覧を見て、使うべき import path を確定します。

```python
# Step 5d gsplat api surface probe
import gsplat
import pkgutil

print("G_SPLAT_FILE", getattr(gsplat, "__file__", "no_file"))
print("G_SPLAT_VERSION", getattr(gsplat, "__version__", "no_version"))

symbols = [name for name in dir(gsplat) if not name.startswith("_")]
print("TOP_LEVEL_SYMBOLS", symbols[:120])

if hasattr(gsplat, "__path__"):
    subs = sorted(m.name for m in pkgutil.iter_modules(gsplat.__path__))
    print("SUBMODULES", subs)
else:
    print("SUBMODULES", "no_package_path")
```

# admin

```text
# Step 5d gsplat api surface probe res
G_SPLAT_FILE /usr/local/lib/python3.12/dist-packages/gsplat/__init__.py
G_SPLAT_VERSION 1.5.3
TOP_LEVEL_SYMBOLS ['DefaultStrategy', 'MCMCStrategy', 'PngCompression', 'RollingShutterType', 'SelectiveAdam', 'Strategy', 'accumulate', 'accumulate_2dgs', 'all', 'compression', 'cuda', 'distributed', 'export_splats', 'exporter', 'fully_fused_projection', 'fully_fused_projection_2dgs', 'fully_fused_projection_with_ut', 'isect_offset_encode', 'isect_tiles', 'optimizers', 'proj', 'quat_scale_to_covar_preci', 'rasterization', 'rasterization_2dgs', 'rasterization_2dgs_inria_wrapper', 'rasterization_inria_wrapper', 'rasterize_to_indices_in_range', 'rasterize_to_indices_in_range_2dgs', 'rasterize_to_pixels', 'rasterize_to_pixels_2dgs', 'rasterize_to_pixels_eval3d', 'relocation', 'rendering', 'spherical_harmonics', 'strategy', 'utils', 'version', 'warnings', 'world_to_cam']
SUBMODULES ['_helper', 'compression', 'cuda', 'distributed', 'exporter', 'optimizers', 'profile', 'relocation', 'rendering', 'strategy', 'utils', 'version']

```

# codex

2026-03-29 v11 next action。

- `Step 5d` により、`gsplat.rasterization` は submodule ではなく top-level symbol だと確認できました。
- したがって import path の問題は解消方向です。
- 次は `gsplat.rasterization` と関連 symbol が callable として使えるか、docstring / signature を見て最小呼び出し形を確定します。

```python
# Step 5e gsplat callable surface probe
import inspect
import gsplat

targets = [
    ("rasterization", gsplat.rasterization),
    ("rasterization_2dgs", gsplat.rasterization_2dgs),
    ("fully_fused_projection", gsplat.fully_fused_projection),
]

for name, obj in targets:
    print("NAME", name)
    print("TYPE", type(obj))
    print("CALLABLE", callable(obj))
    try:
        print("SIGNATURE", inspect.signature(obj))
    except Exception as exc:
        print("SIGNATURE_NG", type(exc).__name__, str(exc))
    doc = inspect.getdoc(obj)
    print("DOC_HEAD", None if doc is None else doc.splitlines()[:8])
    print("---")
```

# admin

```text
# Step 5e gsplat callable surface probe res
NAME rasterization
TYPE <class 'function'>
CALLABLE True
SIGNATURE (means: torch.Tensor, quats: torch.Tensor, scales: torch.Tensor, opacities: torch.Tensor, colors: torch.Tensor, viewmats: torch.Tensor, Ks: torch.Tensor, width: int, height: int, near_plane: float = 0.01, far_plane: float = 10000000000.0, radius_clip: float = 0.0, eps2d: float = 0.3, sh_degree: Optional[int] = None, packed: bool = True, tile_size: int = 16, backgrounds: Optional[torch.Tensor] = None, render_mode: Literal['RGB', 'D', 'ED', 'RGB+D', 'RGB+ED'] = 'RGB', sparse_grad: bool = False, absgrad: bool = False, rasterize_mode: Literal['classic', 'antialiased'] = 'classic', channel_chunk: int = 32, distributed: bool = False, camera_model: Literal['pinhole', 'ortho', 'fisheye', 'ftheta'] = 'pinhole', segmented: bool = False, covars: Optional[torch.Tensor] = None, with_ut: bool = False, with_eval3d: bool = False, radial_coeffs: Optional[torch.Tensor] = None, tangential_coeffs: Optional[torch.Tensor] = None, thin_prism_coeffs: Optional[torch.Tensor] = None, ftheta_coeffs: Optional[gsplat.cuda._wrapper.FThetaCameraDistortionParameters] = None, rolling_shutter: gsplat.cuda._wrapper.RollingShutterType = <RollingShutterType.GLOBAL: 4>, viewmats_rs: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor, Dict]
DOC_HEAD ['Rasterize a set of 3D Gaussians (N) to a batch of image planes (C).', '', 'This function provides a handful features for 3D Gaussian rasterization, which', 'we detail in the following notes. A complete profiling of the these features', 'can be found in the :ref:`profiling` page.', '', '.. note::', '    **Multi-GPU Distributed Rasterization**: This function can be used in a multi-GPU']
---
NAME rasterization_2dgs
TYPE <class 'function'>
CALLABLE True
SIGNATURE (means: torch.Tensor, quats: torch.Tensor, scales: torch.Tensor, opacities: torch.Tensor, colors: torch.Tensor, viewmats: torch.Tensor, Ks: torch.Tensor, width: int, height: int, near_plane: float = 0.01, far_plane: float = 10000000000.0, radius_clip: float = 0.0, eps2d: float = 0.3, sh_degree: Optional[int] = None, packed: bool = False, tile_size: int = 16, backgrounds: Optional[torch.Tensor] = None, render_mode: Literal['RGB', 'D', 'ED', 'RGB+D', 'RGB+ED'] = 'RGB', sparse_grad: bool = False, absgrad: bool = False, distloss: bool = False, depth_mode: Literal['expected', 'median'] = 'expected') -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, Dict]
DOC_HEAD ['Rasterize a set of 2D Gaussians (N) to a batch of image planes (C).', '', 'This function supports a handful of features, similar to the :func:`rasterization` function.', '', '.. warning::', '    This function is currently not differentiable w.r.t. the camera intrinsics `Ks`.', '', 'Args:']
---
NAME fully_fused_projection
TYPE <class 'function'>
CALLABLE True
SIGNATURE (means: torch.Tensor, covars: Optional[torch.Tensor], quats: Optional[torch.Tensor], scales: Optional[torch.Tensor], viewmats: torch.Tensor, Ks: torch.Tensor, width: int, height: int, eps2d: float = 0.3, near_plane: float = 0.01, far_plane: float = 10000000000.0, radius_clip: float = 0.0, packed: bool = False, sparse_grad: bool = False, calc_compensations: bool = False, camera_model: Literal['pinhole', 'ortho', 'fisheye', 'ftheta'] = 'pinhole', opacities: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]
DOC_HEAD ['Projects Gaussians to 2D.', '', 'This function fuse the process of computing covariances', '(:func:`quat_scale_to_covar_preci()`), transforming to camera space (:func:`world_to_cam()`),', 'and projection (:func:`proj()`).', '', '.. note::', '']
---
```

# codex

2026-03-29 v12 next action。

- `Step 5e` は成功です。`gsplat` の callable surface まで確認できました。
- 次は world projection 前提として、実 session から `ARCore pose`、`frame_pose_index.csv`、`camera_calibration_summary.json`、image 群の対応関係を 1 frame で確定します。
- 目的は `DA3Metric-Large` depth を主 `ARCore` 空間へ戻す最小入力を揃えることです。

```python
# Step 5f frame alignment probe
import csv
import json
from pathlib import Path

session_root = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
images_dir = session_root / "images"
frame_pose_index_path = session_root / "frame_pose_index.csv"
camera_summary_path = session_root / "camera_calibration_summary.json"
arcore_pose_path = session_root.parent / "isensorium" / "arcore_pose.jsonl"

print("session_root_exists", session_root.exists(), session_root)
print("images_dir_exists", images_dir.exists(), images_dir)
print("frame_pose_index_exists", frame_pose_index_path.exists(), frame_pose_index_path)
print("camera_summary_exists", camera_summary_path.exists(), camera_summary_path)
print("arcore_pose_exists", arcore_pose_path.exists(), arcore_pose_path)

rows = []
if frame_pose_index_path.exists():
    with frame_pose_index_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            rows.append(row)
            if i >= 4:
                break
print("frame_pose_index_head", rows)

if camera_summary_path.exists():
    summary = json.loads(camera_summary_path.read_text(encoding="utf-8"))
    print("camera_summary_keys", sorted(summary.keys()))

poses = []
if arcore_pose_path.exists():
    with arcore_pose_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            poses.append(json.loads(line))
            if i >= 2:
                break
print("arcore_pose_head_keys", [sorted(p.keys()) for p in poses])

images = sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.jpeg"))
print("image_count", len(images))
print("first_images", [p.name for p in images[:5]])
```

# admin

```text
# Step 5f frame alignment probe res
session_root_exists True /content/trajectreview_input/session-20260328-103250/trajectreview
images_dir_exists True /content/trajectreview_input/session-20260328-103250/trajectreview/images
frame_pose_index_exists True /content/trajectreview_input/session-20260328-103250/trajectreview/frame_pose_index.csv
camera_summary_exists True /content/trajectreview_input/session-20260328-103250/trajectreview/camera_calibration_summary.json
arcore_pose_exists False /content/trajectreview_input/session-20260328-103250/isensorium/arcore_pose.jsonl
frame_pose_index_head [{'frame_index': '0', 'image_file_name': '', 'frame_timestamp_ns': '916764341604734', 'pose_record_index': '1', 'pose_timestamp_ns': '916764623999078', 'time_delta_ms': '282.394', 'image_intrinsics_mode': 'session_fixed', 'tracking_state': 'PAUSED'}, {'frame_index': '1', 'image_file_name': '', 'frame_timestamp_ns': '916764374968796', 'pose_record_index': '1', 'pose_timestamp_ns': '916764623999078', 'time_delta_ms': '249.030', 'image_intrinsics_mode': 'session_fixed', 'tracking_state': 'PAUSED'}, {'frame_index': '2', 'image_file_name': '', 'frame_timestamp_ns': '916764408332807', 'pose_record_index': '1', 'pose_timestamp_ns': '916764623999078', 'time_delta_ms': '215.666', 'image_intrinsics_mode': 'session_fixed', 'tracking_state': 'PAUSED'}, {'frame_index': '3', 'image_file_name': '', 'frame_timestamp_ns': '916764441696869', 'pose_record_index': '1', 'pose_timestamp_ns': '916764623999078', 'time_delta_ms': '182.302', 'image_intrinsics_mode': 'session_fixed', 'tracking_state': 'PAUSED'}, {'frame_index': '4', 'image_file_name': '', 'frame_timestamp_ns': '916764475060880', 'pose_record_index': '1', 'pose_timestamp_ns': '916764623999078', 'time_delta_ms': '148.938', 'image_intrinsics_mode': 'session_fixed', 'tracking_state': 'PAUSED'}]
camera_summary_keys ['blockers', 'calibrationFrameCount', 'captureDiagnostics', 'coordinateSystem', 'imageIntrinsicsCount', 'imageIntrinsicsCoverageRatio', 'intrinsicsChangedDuringRecording', 'intrinsicsModeCandidate', 'legacySessionWithoutCalibration', 'lensDistortionCount', 'lensDistortionCoverageRatio', 'possiblePreCalibrationImplementationData', 'recommendedModelingRoutes', 'recordCount', 'sessionId', 'specVersion', 'textureIntrinsicsCount', 'textureIntrinsicsCoverageRatio', 'timestampEndNs', 'timestampStartNs', 'validPoseCount', 'warnings']
arcore_pose_head_keys []
image_count 182
first_images ['frame_000009.jpg', 'frame_000012.jpg', 'frame_000013.jpg', 'frame_000014.jpg', 'frame_000021.jpg']

```

# codex

2026-03-29 v13 next action。

- `Step 5f` は部分成功です。`frame_pose_index.csv`、`camera_calibration_summary.json`、`images/` は揃っています。
- 現在の blocker は `arcore_pose.jsonl` の path 仮定が外れている点です。
- 次は zip 展開後の実配置を列挙して、`arcore_pose` 実体 file と `session_manifest` の実 path を確定します。

```python
# Step 5g bundle layout probe
from pathlib import Path

root = Path("/content/trajectreview_input/session-20260328-103250")

print("ROOT", root, root.exists())

for path in sorted(root.rglob("*")):
    rel = path.relative_to(root)
    if path.is_dir():
        print("DIR ", rel)
    else:
        name = path.name.lower()
        if (
            "arcore" in name
            or "pose" in name
            or "manifest" in name
            or name.endswith(".jsonl")
            or name.endswith(".csv")
        ):
            print("FILE", rel)
```

# admin

```text
# Step 5g bundle layout probe res
ROOT /content/trajectreview_input/session-20260328-103250 True
FILE arcore_pose.jsonl
FILE ble_scan.jsonl
FILE gnss.csv
FILE imu.csv
FILE session_manifest.json
DIR  trajectreview
FILE trajectreview/frame_pose_index.csv
DIR  trajectreview/images
FILE trajectreview/space_handoff_manifest.json
FILE video_events.jsonl
FILE video_frame_timestamps.csv
```

# codex

2026-03-29 v14 next action。

- `arcore_pose.jsonl` の実体 path は session root 直下だと確認できました。
- これで path blocker は解消です。
- 次は `arcore_pose.jsonl` の record key と、`frame_pose_index.csv` の `pose_record_index` で参照できる実 pose record を 1 件取り、world projection に必要な最小 pose / intrinsics 入力を確定します。

```python
# Step 5h pose record probe
import csv
import json
from pathlib import Path

root = Path("/content/trajectreview_input/session-20260328-103250")
session_root = root / "trajectreview"
frame_pose_index_path = session_root / "frame_pose_index.csv"
arcore_pose_path = root / "arcore_pose.jsonl"

rows = []
with frame_pose_index_path.open("r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        rows.append(row)
        if i >= 9:
            break

poses = []
with arcore_pose_path.open("r", encoding="utf-8") as f:
    for line in f:
        poses.append(json.loads(line))

print("frame_pose_index_count_sample", len(rows))
print("arcore_pose_count", len(poses))

target = None
for row in rows:
    idx = int(row["pose_record_index"])
    if 0 <= idx < len(poses):
        target = (row, poses[idx])
        break

print("target_found", target is not None)
if target is not None:
    row, pose = target
    print("frame_pose_row", row)
    print("pose_keys", sorted(pose.keys()))
    for k in ["timestampNs", "elapsedRealtimeNanos", "trackingState", "cameraPose", "imageIntrinsics", "textureIntrinsics", "lensDistortion"]:
        if k in pose:
            print("pose_field", k, pose[k] if isinstance(pose[k], (int, float, str, type(None))) else type(pose[k]).__name__)
```

# admin

```text
# Step 5h pose record probe res
frame_pose_index_count_sample 10
arcore_pose_count 182
target_found True
frame_pose_row {'frame_index': '0', 'image_file_name': '', 'frame_timestamp_ns': '916764341604734', 'pose_record_index': '1', 'pose_timestamp_ns': '916764623999078', 'time_delta_ms': '282.394', 'image_intrinsics_mode': 'session_fixed', 'tracking_state': 'PAUSED'}
pose_keys ['captureDiagnostics', 'captureTimestampNs', 'elapsedRealtimeNanos', 'frameTimestampNs', 'imageIntrinsics', 'lensDistortion', 'pose', 'recordIndex', 'sessionId', 'textureIntrinsics', 'trackingFailureReason', 'trackingState', 'wallTimeMillis']
pose_field elapsedRealtimeNanos 916764772753921
pose_field trackingState PAUSED
pose_field imageIntrinsics dict
pose_field textureIntrinsics dict
pose_field lensDistortion dict

```

# codex

2026-03-29 v15 next action。

- `Step 5h` は成功です。world projection に必要な pose record は実在し、`imageIntrinsics` と `textureIntrinsics` も取れています。
- 次は `pose`、`imageIntrinsics`、`textureIntrinsics`、`lensDistortion` の内部 key と値 shape を確認し、world projection の最小入力を確定します。

```python
# Step 5i pose payload probe
import csv
import json
from pathlib import Path

root = Path("/content/trajectreview_input/session-20260328-103250")
session_root = root / "trajectreview"
frame_pose_index_path = session_root / "frame_pose_index.csv"
arcore_pose_path = root / "arcore_pose.jsonl"

with frame_pose_index_path.open("r", encoding="utf-8") as f:
    row = next(csv.DictReader(f))

pose_idx = int(row["pose_record_index"])
with arcore_pose_path.open("r", encoding="utf-8") as f:
    poses = [json.loads(line) for line in f]

pose = poses[pose_idx]

for field in ["pose", "imageIntrinsics", "textureIntrinsics", "lensDistortion", "captureDiagnostics"]:
    value = pose.get(field)
    print("FIELD", field, type(value).__name__)
    if isinstance(value, dict):
        print("KEYS", sorted(value.keys()))
        for k, v in value.items():
            if isinstance(v, dict):
                print("SUBDICT", k, sorted(v.keys()))
            elif isinstance(v, list):
                print("LIST", k, len(v), v[:8])
            else:
                print("VALUE", k, v)
    else:
        print("RAW", value)
    print("---")
```

# admin

```text
# Step 5i pose payload probe res
FIELD pose dict
KEYS ['qw', 'qx', 'qy', 'qz', 'tx', 'ty', 'tz']
VALUE tx 0
VALUE ty 0
VALUE tz 0
VALUE qx -5.9604645e-08
VALUE qy 0
VALUE qz -0.7071067
VALUE qw 0.7071067
---
FIELD imageIntrinsics dict
KEYS ['cx', 'cy', 'fx', 'fy', 'height', 'width']
VALUE fx 451.99124
VALUE fy 451.90652
VALUE cx 321.57803
VALUE cy 234.85765
VALUE width 640
VALUE height 480
---
FIELD textureIntrinsics dict
KEYS ['cx', 'cy', 'fx', 'fy', 'height', 'width']
VALUE fx 1355.9738
VALUE fy 1355.7195
VALUE cx 965.7341
VALUE cy 525.57294
VALUE width 1920
VALUE height 1080
---
FIELD lensDistortion dict
KEYS ['coefficients', 'model']
LIST coefficients 5 [0, 0, 0, 0, 0]
VALUE model android_lens_distortion
---
FIELD captureDiagnostics dict
KEYS ['imageIntrinsics', 'lensDistortion', 'textureIntrinsics']
SUBDICT imageIntrinsics ['failureReason', 'requested', 'succeeded']
SUBDICT textureIntrinsics ['failureReason', 'requested', 'succeeded']
SUBDICT lensDistortion ['failureReason', 'requested', 'succeeded']
---
```

# codex

2026-03-29 v16 next action。

- `Step 5i` は成功です。world projection の最小入力として `pose(tx,ty,tz,qx,qy,qz,qw)`、`imageIntrinsics(fx,fy,cx,cy,width,height)`、`depth_raw.npy` を結べる状態になりました。
- 次は `frame_000009.jpg` と `depth_raw.npy` を使い、画像中心付近の depth を camera 座標へ戻し、さらに pose で world 座標へ変換する最小 back-projection smoke test を行います。
- 目的は `DA3Metric-Large` depth を主 `ARCore` 空間へ戻せることの first proof を取ることです。

```python
# Step 5j world back-projection smoke test
import csv
import json
from pathlib import Path

import numpy as np

root = Path("/content/trajectreview_input/session-20260328-103250")
session_root = root / "trajectreview"
arcore_pose_path = root / "arcore_pose.jsonl"
depth_path = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v05/depth_raw.npy")

with arcore_pose_path.open("r", encoding="utf-8") as f:
    poses = [json.loads(line) for line in f]

pose = poses[1]
intr = pose["imageIntrinsics"]
depth = np.load(depth_path)

h, w = depth.shape
u = w // 2
v = h // 2
z = float(depth[v, u])

fx = float(intr["fx"])
fy = float(intr["fy"])
cx = float(intr["cx"])
cy = float(intr["cy"])

x_cam = (u - cx) / fx * z
y_cam = (v - cy) / fy * z
z_cam = z

qx = float(pose["pose"]["qx"])
qy = float(pose["pose"]["qy"])
qz = float(pose["pose"]["qz"])
qw = float(pose["pose"]["qw"])
tx = float(pose["pose"]["tx"])
ty = float(pose["pose"]["ty"])
tz = float(pose["pose"]["tz"])

q = np.array([qw, qx, qy, qz], dtype=np.float64)
q = q / np.linalg.norm(q)
qw, qx, qy, qz = q

R = np.array([
    [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
    [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
    [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)],
], dtype=np.float64)

cam_point = np.array([x_cam, y_cam, z_cam], dtype=np.float64)
world_point = R @ cam_point + np.array([tx, ty, tz], dtype=np.float64)

print("depth_shape", depth.shape)
print("sample_uv", [u, v])
print("sample_depth", z)
print("camera_point", cam_point.tolist())
print("world_point", world_point.tolist())
print("tracking_state", pose["trackingState"])
```

# admin

```text
# Step 5j world back-projection smoke test res
depth_shape (378, 504)
sample_uv [252, 189]
sample_depth 0.5909101366996765
camera_point [-0.09096274347837847, -0.059963176079481935, 0.5909101366996765]
world_point [-0.05996312626947611, 0.09096279328838429, 0.5909101340866039]
tracking_state PAUSED

```

# codex

2026-03-29 v17 next action。

- `Step 5j` は成功です。`DA3Metric-Large` depth の 1 点を主 `ARCore` 空間へ戻せる first proof が取れました。
- 次は depth 全体から間引いた point 群を world 座標へ変換し、`.npy` と `.ply` で保存できるかを確認します。
- 目的は `3DGS` 系主空間モデル生成の前段となる point export の成立確認です。

```python
# Step 5k point export smoke test
import json
from pathlib import Path

import numpy as np

root = Path("/content/trajectreview_input/session-20260328-103250")
arcore_pose_path = root / "arcore_pose.jsonl"
out_dir = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v05")
depth_path = out_dir / "depth_raw.npy"
points_npy = out_dir / "world_points_smoke.npy"
points_ply = out_dir / "world_points_smoke.ply"

with arcore_pose_path.open("r", encoding="utf-8") as f:
    poses = [json.loads(line) for line in f]

pose = poses[1]
intr = pose["imageIntrinsics"]
depth = np.load(depth_path)

fx = float(intr["fx"])
fy = float(intr["fy"])
cx = float(intr["cx"])
cy = float(intr["cy"])

qx = float(pose["pose"]["qx"])
qy = float(pose["pose"]["qy"])
qz = float(pose["pose"]["qz"])
qw = float(pose["pose"]["qw"])
tx = float(pose["pose"]["tx"])
ty = float(pose["pose"]["ty"])
tz = float(pose["pose"]["tz"])

q = np.array([qw, qx, qy, qz], dtype=np.float64)
q = q / np.linalg.norm(q)
qw, qx, qy, qz = q
R = np.array([
    [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
    [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
    [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)],
], dtype=np.float64)
t = np.array([tx, ty, tz], dtype=np.float64)

step = 24
points = []
for v in range(0, depth.shape[0], step):
    for u in range(0, depth.shape[1], step):
        z = float(depth[v, u])
        if not np.isfinite(z) or z <= 0:
            continue
        x = (u - cx) / fx * z
        y = (v - cy) / fy * z
        cam = np.array([x, y, z], dtype=np.float64)
        world = R @ cam + t
        points.append(world)

points = np.asarray(points, dtype=np.float32)
np.save(points_npy, points)

with points_ply.open("w", encoding="utf-8") as f:
    f.write("ply\nformat ascii 1.0\n")
    f.write(f"element vertex {len(points)}\n")
    f.write("property float x\nproperty float y\nproperty float z\n")
    f.write("end_header\n")
    for p in points:
        f.write(f"{p[0]} {p[1]} {p[2]}\n")

print("points_shape", points.shape)
print("points_npy_exists", points_npy.exists(), points_npy)
print("points_ply_exists", points_ply.exists(), points_ply)
print("first_points", points[:5].tolist())
```

# admin

```text
# Step 5k point export smoke test res
points_shape (336, 3)
points_npy_exists True /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v05/world_points_smoke.npy
points_ply_exists True /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v05/world_points_smoke.ply
first_points [[-1.0956165790557861, 1.4998884201049805, 2.1081550121307373], [-1.1172717809677124, 1.4153820276260376, 2.1498234272003174], [-1.1234573125839233, 1.308434009552002, 2.1617255210876465], [-0.8727853298187256, 0.9273160696029663, 1.6793893575668335], [-0.8485155701637268, 0.8148368000984192, 1.632690191268921]]

```

# codex

2026-03-29 v18 next action。

- `Step 5k` は成功です。主 `ARCore` 空間の point 群を `.npy` と `.ply` で保存できました。
- 次は `gsplat` を使って、この point 群から最小の `3DGS` 系主空間モデル入力形を組めるかを確認します。
- ここでは full training ではなく、`means`、`quats`、`scales`、`opacities`、`colors` の tensor を組み、`gsplat.rasterization` を 1 view で呼べるかを first target にします。

```python
# Step 5l gsplat rasterization smoke test
import json
from pathlib import Path

import numpy as np
import torch
import gsplat

root = Path("/content/trajectreview_input/session-20260328-103250")
arcore_pose_path = root / "arcore_pose.jsonl"
points_path = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v05/world_points_smoke.npy")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
points = np.load(points_path).astype(np.float32)
points = points[:128]

with arcore_pose_path.open("r", encoding="utf-8") as f:
    poses = [json.loads(line) for line in f]
pose = poses[1]
intr = pose["imageIntrinsics"]

means = torch.from_numpy(points).to(device)
quats = torch.tensor([[1.0, 0.0, 0.0, 0.0]] * len(points), dtype=torch.float32, device=device)
scales = torch.full((len(points), 3), 0.02, dtype=torch.float32, device=device)
opacities = torch.full((len(points),), 0.5, dtype=torch.float32, device=device)
colors = torch.full((len(points), 3), 0.7, dtype=torch.float32, device=device)

fx = float(intr["fx"])
fy = float(intr["fy"])
cx = float(intr["cx"])
cy = float(intr["cy"])
width = int(intr["width"])
height = int(intr["height"])

Ks = torch.tensor([[
    [fx, 0.0, cx],
    [0.0, fy, cy],
    [0.0, 0.0, 1.0],
]], dtype=torch.float32, device=device)

viewmats = torch.eye(4, dtype=torch.float32, device=device).unsqueeze(0)

render_colors, render_alphas, info = gsplat.rasterization(
    means=means,
    quats=quats,
    scales=scales,
    opacities=opacities,
    colors=colors,
    viewmats=viewmats,
    Ks=Ks,
    width=width,
    height=height,
    packed=False,
)

print("device", device)
print("means_shape", tuple(means.shape))
print("render_colors_shape", tuple(render_colors.shape))
print("render_alphas_shape", tuple(render_alphas.shape))
print("info_keys", sorted(info.keys()))
```

# admin

```text
# Step 5l gsplat rasterization smoke test res
gsplat: CUDA extension has been set up successfully in 772.22 seconds.
device cuda
means_shape (128, 3)
render_colors_shape (1, 480, 640, 3)
render_alphas_shape (1, 480, 640, 1)
info_keys ['batch_ids', 'camera_ids', 'conics', 'depths', 'flatten_ids', 'gaussian_ids', 'height', 'isect_ids', 'isect_offsets', 'means2d', 'n_batches', 'n_cameras', 'opacities', 'radii', 'tile_height', 'tile_size', 'tile_width', 'tiles_per_gauss', 'width']

```

# codex

2026-03-29 v19 next action。

- `Step 5l` は成功です。`gsplat.rasterization` が `cuda` 上で返り、最小 render path は成立しました。
- 次は render 結果を画像として保存し、同時に `gs_model` 候補 artifact の最小 manifest を置きます。
- 目的は `MRL-12` の `gs_model` 候補を file として残し、`space_quality.json` へ最小 closeout 情報を入れることです。

```python
# Step 5m render artifact smoke test
import json
from pathlib import Path

import numpy as np
from PIL import Image
import torch
import gsplat

root = Path("/content/trajectreview_input/session-20260328-103250")
arcore_pose_path = root / "arcore_pose.jsonl"
out_dir = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v05")
points_path = out_dir / "world_points_smoke.npy"
render_png = out_dir / "gsplat_render_smoke.png"
gs_model_manifest = out_dir / "gs_model_smoke.json"
space_quality_path = out_dir / "space_quality_smoke.json"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
points = np.load(points_path).astype(np.float32)[:128]

with arcore_pose_path.open("r", encoding="utf-8") as f:
    poses = [json.loads(line) for line in f]
pose = poses[1]
intr = pose["imageIntrinsics"]

means = torch.from_numpy(points).to(device)
quats = torch.tensor([[1.0, 0.0, 0.0, 0.0]] * len(points), dtype=torch.float32, device=device)
scales = torch.full((len(points), 3), 0.02, dtype=torch.float32, device=device)
opacities = torch.full((len(points),), 0.5, dtype=torch.float32, device=device)
colors = torch.full((len(points), 3), 0.7, dtype=torch.float32, device=device)

Ks = torch.tensor([[
    [float(intr["fx"]), 0.0, float(intr["cx"])],
    [0.0, float(intr["fy"]), float(intr["cy"])],
    [0.0, 0.0, 1.0],
]], dtype=torch.float32, device=device)

viewmats = torch.eye(4, dtype=torch.float32, device=device).unsqueeze(0)

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

img = render_colors[0].detach().float().clamp(0, 1).cpu().numpy()
Image.fromarray((img * 255).astype(np.uint8)).save(render_png)

manifest = {
    "artifact_type": "gs_model_smoke",
    "renderer": "gsplat",
    "point_source": str(points_path),
    "render_png": str(render_png),
    "num_points": int(len(points)),
    "device": str(device),
    "image_size": [int(intr["width"]), int(intr["height"])],
}
gs_model_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

space_quality = {
    "gsplat_rasterization_smoke": "pass",
    "num_points": int(len(points)),
    "render_png": str(render_png),
    "info_keys": sorted(info.keys()),
}
space_quality_path.write_text(json.dumps(space_quality, indent=2), encoding="utf-8")

print("render_png_exists", render_png.exists(), render_png)
print("gs_model_manifest_exists", gs_model_manifest.exists(), gs_model_manifest)
print("space_quality_exists", space_quality_path.exists(), space_quality_path)
print("manifest", json.dumps(manifest, indent=2))
```

# admin

```text
# Step 5m render artifact smoke test res

```
