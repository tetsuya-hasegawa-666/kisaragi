# sharedlogs_da3-colab.md

## 役割

- この file は `prj-kisaragi_0002` の `DA3Metric-Large` `Colab` 実装について、admin と Codex が notebook cell、script、error、観測結果を往復するための collaborative worklog とする。
- この file は `project-truth.md`、`hi-ai-unified-blueprint.md`、admin evidence の代替ではない。
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
- shared rule 変更は `AGENTS.md`、project truth / plan / current 変更は `project-truth.md` と `hi-ai-unified-blueprint.md`、gate 判定根拠は admin evidence へ別途反映する。

# codex

2026-03-29 v24 cleanup for next use。

- `Step 1` から `Step 5p` までの持続事項は、次の正本へ反映済みです。
  - [da3_colab_clean_bootstrap_runbook.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\modeling\da3_colab_clean_bootstrap_runbook.md)
  - [hi-ai-unified-blueprint.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\hi-ai-unified-blueprint.md)
  - [admin-mrl-test-evidence.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\admin-mrl-test-evidence.md)
  - [codex-mrl-test-evidence.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\codex-mrl-test-evidence.md)
- notebook 証跡と local downloaded artifact は product 側へ移設済みです。
  - `modeling/evidence/trajectreview_modeling_20260329_gpu-evidence.ipynb`
  - `modeling/evidence/da3_smoke_v05/`
- この log 本文はいったん reset し、次回は `MRL-7` の `multi-frame` densify から再開します。
- 次回は fresh runtime 前提で、まず runbook と `MRL-7` の target を確認したうえで、必要な command block だけをここへ再追記してください。

# admin

```text
# <next-step> res

```

# codex

2026-03-29 v25 step-7a multi-frame window probe。

- 目的: `mRL-7.1` の最初の block として、実 session から `10s` 前後の連続 window と、`multi-frame` densify に使う候補 frame 群を確定する。
- 成功条件:
  - `frame_pose_index.csv` と `images/` を読み、frame ごとの時刻と path を取得できる
  - `10s` 前後の window 候補を 1 件以上出せる
  - その window から `12 frame` 前後の sampled frame 候補を出せる
  - 結果を `mrl7_window_probe.json` として保存できる
- 失敗時の扱い:
  - timestamp key 不一致なら、まず実 key 名を列挙して切り分ける
  - `10s` 連続 window が取れないなら、まず最長連続 window を返す

```python
# Step 7a multi-frame window probe
from pathlib import Path
import json
import math
import pandas as pd

SESSION_ROOT = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
OUTPUT_ROOT = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01")
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

frame_index_path = SESSION_ROOT / "frame_pose_index.csv"
images_dir = SESSION_ROOT / "images"

assert frame_index_path.exists(), frame_index_path
assert images_dir.exists(), images_dir

df = pd.read_csv(frame_index_path)
print("columns", list(df.columns))
print("rows", len(df))

time_candidates = [
    "frame_timestamp_ns",
    "capture_timestamp_ns",
    "timestamp_ns",
    "frameTimestampNs",
    "captureTimestampNs",
]
frame_candidates = [
    "frame_name",
    "image_file",
    "image_path",
    "filename",
]

time_col = next((c for c in time_candidates if c in df.columns), None)
frame_col = next((c for c in frame_candidates if c in df.columns), None)

if frame_col is None:
    derived = []
    for idx in range(len(df)):
        jpg = images_dir / f"frame_{idx:06d}.jpg"
        png = images_dir / f"frame_{idx:06d}.png"
        derived.append(jpg.name if jpg.exists() else png.name if png.exists() else None)
    df["derived_frame_name"] = derived
    frame_col = "derived_frame_name"

assert time_col is not None, {"missing_time_col": list(df.columns)}
assert frame_col is not None, {"missing_frame_col": list(df.columns)}

work = df[[time_col, frame_col]].copy()
work = work.dropna().reset_index(drop=True)
work["frame_name"] = work[frame_col].astype(str)
work["image_path"] = work["frame_name"].apply(lambda x: str(images_dir / x))
work = work[work["image_path"].map(lambda p: Path(p).exists())].reset_index(drop=True)
work["timestamp_sec"] = work[time_col].astype("float64") / 1e9

assert len(work) > 0, "no aligned frames found"

target_sec = 10.0
best = None
left = 0
for right in range(len(work)):
    while left < right and (work.loc[right, "timestamp_sec"] - work.loc[left, "timestamp_sec"]) > target_sec:
        left += 1
    span = work.loc[right, "timestamp_sec"] - work.loc[left, "timestamp_sec"]
    count = right - left + 1
    score = (abs(target_sec - span), -count)
    if best is None or score < best["score"]:
        best = {
            "left": left,
            "right": right,
            "span_sec": float(span),
            "count": int(count),
            "score": score,
        }

window = work.iloc[best["left"]:best["right"] + 1].reset_index(drop=True)
sample_count = min(12, len(window))
sample_indices = sorted({round(i * (len(window) - 1) / max(sample_count - 1, 1)) for i in range(sample_count)})
sampled = window.iloc[sample_indices].reset_index(drop=True)

result = {
    "session_root": str(SESSION_ROOT),
    "frame_index_path": str(frame_index_path),
    "time_col": time_col,
    "frame_col": frame_col,
    "aligned_frame_count": int(len(work)),
    "window_start_sec": float(window["timestamp_sec"].iloc[0]),
    "window_end_sec": float(window["timestamp_sec"].iloc[-1]),
    "window_span_sec": float(window["timestamp_sec"].iloc[-1] - window["timestamp_sec"].iloc[0]),
    "window_frame_count": int(len(window)),
    "sample_frame_count": int(len(sampled)),
    "sample_frames": sampled[["frame_name", "timestamp_sec", "image_path"]].to_dict(orient="records"),
}

out_path = OUTPUT_ROOT / "mrl7_window_probe.json"
out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "time_col": result["time_col"],
    "frame_col": result["frame_col"],
    "aligned_frame_count": result["aligned_frame_count"],
    "window_span_sec": result["window_span_sec"],
    "window_frame_count": result["window_frame_count"],
    "sample_frame_count": result["sample_frame_count"],
    "first_sample": result["sample_frames"][0] if result["sample_frames"] else None,
    "last_sample": result["sample_frames"][-1] if result["sample_frames"] else None,
    "saved": str(out_path),
}, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7a multi-frame window probe res
---------------------------------------------------------------------------
AssertionError                            Traceback (most recent call last)
/tmp/ipykernel_4762/1256230407.py in <cell line: 0>()
     12 images_dir = SESSION_ROOT / "images"
     13 
---> 14 assert frame_index_path.exists(), frame_index_path
     15 assert images_dir.exists(), images_dir
     16 

AssertionError: /content/trajectreview_input/session-20260328-103250/trajectreview/frame_pose_index.csv

```

# codex

2026-03-29 v26 step-7a1 session-root rediscovery probe。

- 目的: `frame_pose_index.csv` が無いので、fresh runtime 上の実 `session_root`、`frame_pose_index.csv`、`images/` の配置を再特定する。
- 成功条件:
  - `session_package.json`、`frame_pose_index.csv`、`images/` の実 path を 1 組以上見つける
  - 次 block で使うべき `SESSION_ROOT` を 1 つに絞れる
- 失敗時の扱い:
  - `/content/trajectreview_input` 自体が無ければ、まず unzip 未実行として扱う
  - `frame_pose_index.csv` だけ無ければ、近い calibration file と `images/` を手掛かりに候補 root を返す

```python
# Step 7a1 session-root rediscovery probe
from pathlib import Path
import json

search_roots = [
    Path("/content/trajectreview_input"),
    Path("/content"),
]

hits = []
for root in search_roots:
    if not root.exists():
        continue
    for pkg in root.rglob("session_package.json"):
        session_root = pkg.parent
        frame_pose = next(iter(session_root.rglob("frame_pose_index.csv")), None)
        images_dir = next((p for p in session_root.rglob("images") if p.is_dir()), None)
        calib = next(iter(session_root.rglob("camera_calibration_summary.json")), None)
        hits.append({
            "session_root": str(session_root),
            "session_package_json": str(pkg),
            "frame_pose_index_csv": None if frame_pose is None else str(frame_pose),
            "camera_calibration_summary_json": None if calib is None else str(calib),
            "images_dir": None if images_dir is None else str(images_dir),
            "image_count": 0 if images_dir is None else len(list(images_dir.glob("*.jpg"))) + len(list(images_dir.glob("*.png"))),
        })

result = {
    "search_roots": [str(p) for p in search_roots],
    "hit_count": len(hits),
    "hits": hits[:20],
}

print(json.dumps(result, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7a1 session-root rediscovery probe res
{
  "search_roots": [
    "/content/trajectreview_input",
    "/content"
  ],
  "hit_count": 0,
  "hits": []
}
```

# codex

2026-03-29 v27 step-7a2 input-zip restore probe。

- 目的: fresh runtime 上で unzip 前と判明したため、入力 zip の実在を確認し、`/content/trajectreview_input` へ展開して `SESSION_ROOT` を復元する。
- 成功条件:
  - 入力 zip が存在する
  - `/content/trajectreview_input` 配下へ展開できる
  - `session_package.json`、`frame_pose_index.csv`、`images/` の実 path を返せる
- 失敗時の扱い:
  - zip が無ければ Drive mount または shortcut path を再確認する
  - 展開後も `frame_pose_index.csv` が無ければ、その session の実配置差分として次 block で file 探索に切り替える

```python
# Step 7a2 input-zip restore probe
from pathlib import Path
import json
import shutil
import zipfile

zip_path = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/session-20260328-103250.zip")
extract_root = Path("/content/trajectreview_input")

assert zip_path.exists(), {"zip_not_found": str(zip_path)}

if extract_root.exists():
    shutil.rmtree(extract_root)
extract_root.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(extract_root)

hits = []
for pkg in extract_root.rglob("session_package.json"):
    session_root = pkg.parent
    frame_pose = next(iter(session_root.rglob("frame_pose_index.csv")), None)
    images_dir = next((p for p in session_root.rglob("images") if p.is_dir()), None)
    calib = next(iter(session_root.rglob("camera_calibration_summary.json")), None)
    hits.append({
        "session_root": str(session_root),
        "session_package_json": str(pkg),
        "frame_pose_index_csv": None if frame_pose is None else str(frame_pose),
        "camera_calibration_summary_json": None if calib is None else str(calib),
        "images_dir": None if images_dir is None else str(images_dir),
        "image_count": 0 if images_dir is None else len(list(images_dir.glob("*.jpg"))) + len(list(images_dir.glob("*.png"))),
    })

result = {
    "zip_path": str(zip_path),
    "extract_root": str(extract_root),
    "hit_count": len(hits),
    "hits": hits[:20],
}

print(json.dumps(result, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7a2 input-zip restore probe res

```

# codex

2026-03-30 v28 startup to step-7a2 block。

- 目的: fresh runtime から `MRL-7` の前提を戻し、`step-7a2` まで一気に進める。
- 成功条件:
  - Drive mount、zip 存在確認、blank workspace 確認が通る
  - unzip、repo clone、dependency install、`DepthAnything3` import、`1 frame` 推論、`gsplat` surface 確認が通る
  - `step-7a2` で `session_package.json`、`frame_pose_index.csv`、`images/` の path 候補を返せる
- 返してほしいもの:
  - `Step 4 summary`
  - `Step 7a2 input-zip restore probe res`

```python
# Startup to Step 7a2

# 1. Drive mount / runtime check
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

# 2. zip existence
folder_root = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_")
zip_path = folder_root / "trajectreview" / "correcting" / "session-20260328-103250.zip"
print("folder_root_exists", folder_root.exists(), folder_root)
print("zip_exists", zip_path.exists(), zip_path)

# 3. blank workspace check
print("repo_exists_before_bootstrap", Path("/content/Depth-Anything-3").exists())
print("extract_root_exists_before_bootstrap", Path("/content/trajectreview_input").exists())

# 4. unzip input zip
import shutil
import zipfile

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

# 5. clone repo and install dependencies
import subprocess

def run(cmd):
    print("RUN", " ".join(cmd))
    subprocess.run(cmd, check=True)

repo_root = Path("/content/Depth-Anything-3")
if repo_root.exists():
    shutil.rmtree(repo_root)

run(["git", "clone", "https://github.com/ByteDance-Seed/Depth-Anything-3.git", str(repo_root)])
run(["python", "-m", "pip", "install", "--quiet", "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile", "trimesh", "gsplat"])
print("bootstrap_done", repo_root.exists(), repo_root)

# 6. import check
import sys

REPO_ROOT = Path("/content/Depth-Anything-3")
src_root = REPO_ROOT / "src"
print("src_root_exists", src_root.exists(), src_root)
assert src_root.exists(), f"src not found: {src_root}"
src_str = str(src_root)
if src_str not in sys.path:
    sys.path.insert(0, src_str)

from depth_anything_3.api import DepthAnything3
print("import_ok", DepthAnything3)

# 7. one-frame inference
import json
import numpy as np
from PIL import Image

OUTPUT_ROOT = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v24")
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

images = sorted((session_root / "images").glob("*.png")) + sorted((session_root / "images").glob("*.jpg")) + sorted((session_root / "images").glob("*.jpeg"))
assert images, f"images not found under {session_root / 'images'}"

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
print("STEP4_SUMMARY")
print(json.dumps(summary, indent=2))

# 8. gsplat surface check
import gsplat
print("gsplat_version", getattr(gsplat, "__version__", "unknown"))
print("rasterization_type", type(gsplat.rasterization).__name__)
print("rasterization_2dgs_type", type(gsplat.rasterization_2dgs).__name__)
print("fully_fused_projection_type", type(gsplat.fully_fused_projection).__name__)

# 9. step-7a2 restore probe result
hits = []
for pkg in extract_root.rglob("session_package.json"):
    root = pkg.parent
    frame_pose = next(iter(root.rglob("frame_pose_index.csv")), None)
    images_dir = next((p for p in root.rglob("images") if p.is_dir()), None)
    calib = next(iter(root.rglob("camera_calibration_summary.json")), None)
    hits.append({
        "session_root": str(root),
        "session_package_json": str(pkg),
        "frame_pose_index_csv": None if frame_pose is None else str(frame_pose),
        "camera_calibration_summary_json": None if calib is None else str(calib),
        "images_dir": None if images_dir is None else str(images_dir),
        "image_count": 0 if images_dir is None else len(list(images_dir.glob("*.jpg"))) + len(list(images_dir.glob("*.png"))),
    })

result = {
    "zip_path": str(zip_path),
    "extract_root": str(extract_root),
    "hit_count": len(hits),
    "hits": hits[:20],
}

print("STEP7A2_RESULT")
print(json.dumps(result, indent=2, ensure_ascii=False))
```

# admin

```text
# Startup to Step 7a2 res
Mounted at /content/drive
cwd /content
cuda_available True
drive_exists True
mydrive_exists True
shortcut_root_exists True
folder_root_exists True /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_
zip_exists True /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/session-20260328-103250.zip
repo_exists_before_bootstrap False
extract_root_exists_before_bootstrap False
session_root_exists True /content/trajectreview_input/session-20260328-103250/trajectreview
images_dir_exists True /content/trajectreview_input/session-20260328-103250/trajectreview/images
image_count 182
first_image /content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000009.jpg
RUN git clone https://github.com/ByteDance-Seed/Depth-Anything-3.git /content/Depth-Anything-3
RUN python -m pip install --quiet addict evo moviepy==1.0.3 pygame pycolmap plyfile trimesh gsplat
bootstrap_done True /content/Depth-Anything-3
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

import_ok <class 'depth_anything_3.api.DepthAnything3'>
WARNING:py.warnings:/usr/local/lib/python3.12/dist-packages/huggingface_hub/utils/_auth.py:94: UserWarning: 
The secret `HF_TOKEN` does not exist in your Colab secrets.
To authenticate with the Hugging Face Hub, create a token in your settings tab (https://huggingface.co/settings/tokens), set it as secret in your Google Colab and restart your session.
You will be able to reuse this secret in all of your notebooks.
Please note that authentication is recommended but still optional to access public models or datasets.
  warnings.warn(

config.json: 100%
 847/847 [00:00<00:00, 51.0kB/s]
[INFO ] using MLP layer as FFN
model.safetensors: 100%
 1.34G/1.34G [00:09<00:00, 125MB/s]
[INFO ] Processed Images Done taking 0.1296095848083496 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 1.6938645839691162 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0019145011901855469 seconds
STEP4_SUMMARY
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
gsplat_version 1.5.3
rasterization_type function
rasterization_2dgs_type function
fully_fused_projection_type function
STEP7A2_RESULT
{
  "zip_path": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/session-20260328-103250.zip",
  "extract_root": "/content/trajectreview_input",
  "hit_count": 1,
  "hits": [
    {
      "session_root": "/content/trajectreview_input/session-20260328-103250/trajectreview",
      "session_package_json": "/content/trajectreview_input/session-20260328-103250/trajectreview/session_package.json",
      "frame_pose_index_csv": "/content/trajectreview_input/session-20260328-103250/trajectreview/frame_pose_index.csv",
      "camera_calibration_summary_json": "/content/trajectreview_input/session-20260328-103250/trajectreview/camera_calibration_summary.json",
      "images_dir": "/content/trajectreview_input/session-20260328-103250/trajectreview/images",
      "image_count": 182
    }
  ]
}
```

# codex

2026-03-30 v29 step-7b multi-frame window selection。

- 目的: 確定した `SESSION_ROOT` から、`MRL-7` の `10s` 前後 window と sampled frame 群を決める。
- 成功条件:
  - `frame_pose_index.csv` の実 column を確認できる
  - `10s` 前後の連続 window を 1 件選べる
  - その window から `12 frame` 前後の sampled frame を返せる
  - `mrl7_window_probe.json` を保存できる
- 失敗時の扱い:
  - 時刻 column 名が想定外なら、まず実 column を見て切り分ける
  - frame 名 column が無ければ `images/` と index から導出する

```python
# Step 7b multi-frame window selection
from pathlib import Path
import json
import pandas as pd

SESSION_ROOT = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
OUTPUT_ROOT = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01")
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

frame_index_path = SESSION_ROOT / "frame_pose_index.csv"
images_dir = SESSION_ROOT / "images"

df = pd.read_csv(frame_index_path)
print("columns", list(df.columns))
print("rows", len(df))

time_candidates = [
    "frame_timestamp_ns",
    "capture_timestamp_ns",
    "timestamp_ns",
    "frameTimestampNs",
    "captureTimestampNs",
]
frame_candidates = [
    "frame_name",
    "image_file",
    "image_path",
    "filename",
]

time_col = next((c for c in time_candidates if c in df.columns), None)
frame_col = next((c for c in frame_candidates if c in df.columns), None)

if frame_col is None:
    derived = []
    image_files = sorted(list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpeg")))
    for idx in range(len(df)):
        derived.append(image_files[idx].name if idx < len(image_files) else None)
    df["derived_frame_name"] = derived
    frame_col = "derived_frame_name"

assert time_col is not None, {"missing_time_col": list(df.columns)}
assert frame_col is not None, {"missing_frame_col": list(df.columns)}

work = df[[time_col, frame_col]].copy()
work = work.dropna().reset_index(drop=True)
work["frame_name"] = work[frame_col].astype(str)
work["image_path"] = work["frame_name"].apply(lambda x: str(images_dir / x))
work = work[work["image_path"].map(lambda p: Path(p).exists())].reset_index(drop=True)
work["timestamp_sec"] = work[time_col].astype("float64") / 1e9

assert len(work) > 0, "no aligned frames found"

target_sec = 10.0
best = None
left = 0
for right in range(len(work)):
    while left < right and (work.loc[right, "timestamp_sec"] - work.loc[left, "timestamp_sec"]) > target_sec:
        left += 1
    span = work.loc[right, "timestamp_sec"] - work.loc[left, "timestamp_sec"]
    count = right - left + 1
    score = (abs(target_sec - span), -count)
    if best is None or score < best["score"]:
        best = {
            "left": left,
            "right": right,
            "span_sec": float(span),
            "count": int(count),
            "score": score,
        }

window = work.iloc[best["left"]:best["right"] + 1].reset_index(drop=True)
sample_count = min(12, len(window))
sample_indices = sorted({round(i * (len(window) - 1) / max(sample_count - 1, 1)) for i in range(sample_count)})
sampled = window.iloc[sample_indices].reset_index(drop=True)

result = {
    "session_root": str(SESSION_ROOT),
    "frame_index_path": str(frame_index_path),
    "time_col": time_col,
    "frame_col": frame_col,
    "aligned_frame_count": int(len(work)),
    "window_start_sec": float(window["timestamp_sec"].iloc[0]),
    "window_end_sec": float(window["timestamp_sec"].iloc[-1]),
    "window_span_sec": float(window["timestamp_sec"].iloc[-1] - window["timestamp_sec"].iloc[0]),
    "window_frame_count": int(len(window)),
    "sample_frame_count": int(len(sampled)),
    "sample_frames": sampled[["frame_name", "timestamp_sec", "image_path"]].to_dict(orient="records"),
}

out_path = OUTPUT_ROOT / "mrl7_window_probe.json"
out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "time_col": result["time_col"],
    "frame_col": result["frame_col"],
    "aligned_frame_count": result["aligned_frame_count"],
    "window_span_sec": result["window_span_sec"],
    "window_frame_count": result["window_frame_count"],
    "sample_frame_count": result["sample_frame_count"],
    "first_sample": result["sample_frames"][0] if result["sample_frames"] else None,
    "last_sample": result["sample_frames"][-1] if result["sample_frames"] else None,
    "saved": str(out_path),
}, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7b multi-frame window selection res
columns ['frame_index', 'image_file_name', 'frame_timestamp_ns', 'pose_record_index', 'pose_timestamp_ns', 'time_delta_ms', 'image_intrinsics_mode', 'tracking_state']
rows 521
{
  "time_col": "frame_timestamp_ns",
  "frame_col": "derived_frame_name",
  "aligned_frame_count": 182,
  "window_span_sec": 3.953939746017568,
  "window_frame_count": 182,
  "sample_frame_count": 12,
  "first_sample": {
    "frame_name": "frame_000009.jpg",
    "timestamp_sec": 916764.341604734,
    "image_path": "/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000009.jpg"
  },
  "last_sample": {
    "frame_name": "frame_000520.jpg",
    "timestamp_sec": 916768.29554448,
    "image_path": "/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000520.jpg"
  },
  "saved": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/mrl7_window_probe.json"
}
```

# codex

2026-03-30 v30 step-7c sampled-frame depth batch。

- 目的: `Step 7b` で決めた `12 frame` を対象に、`DA3Metric-Large` depth を一括生成して `MRL-7` の multi-frame densify 入力を作る。
- 読み替え:
  - 今回の実 session では `10s` 理想に対して、実際の連続 window は約 `3.95s` だった
  - この段では `10s` 固定にこだわらず、実 session の最長連続 window を正として進める
- 成功条件:
  - `mrl7_window_probe.json` から sampled frame を読める
  - `12 frame` 前後の depth を保存できる
  - `depth_batch_manifest.json` を保存できる
- 失敗時の扱い:
  - VRAM や runtime が厳しければ `max_frames = 8` へ落として再実行する
  - 1 枚でも推論 failure が出たら、その frame 名を manifest に残して続行する

```python
# Step 7c sampled-frame depth batch
from pathlib import Path
import json
import numpy as np
from PIL import Image
import torch

from depth_anything_3.api import DepthAnything3

probe_dir = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01")
probe_path = probe_dir / "mrl7_window_probe.json"
out_dir = probe_dir / "depth_batch_v01"
out_dir.mkdir(parents=True, exist_ok=True)

probe = json.loads(probe_path.read_text(encoding="utf-8"))
sample_frames = probe["sample_frames"]
max_frames = 12
sample_frames = sample_frames[:max_frames]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = DepthAnything3.from_pretrained("depth-anything/DA3METRIC-LARGE").to(device=device)

manifest = {
    "device": str(device),
    "requested_frames": len(probe["sample_frames"]),
    "processed_frames": 0,
    "failed_frames": [],
    "outputs": [],
}

for idx, item in enumerate(sample_frames):
    image_path = Path(item["image_path"])
    frame_name = item["frame_name"]
    stem = image_path.stem
    try:
        pred = model.inference([str(image_path)])
        depth = np.asarray(pred.depth[0])
        depth_path = out_dir / f"{stem}_depth.npy"
        preview_path = out_dir / f"{stem}_depth.png"
        np.save(depth_path, depth)

        depth_min = float(depth.min())
        depth_max = float(depth.max())
        norm = np.zeros_like(depth, dtype=np.float32) if depth_max <= depth_min else (depth - depth_min) / (depth_max - depth_min)
        Image.fromarray((norm * 255).astype(np.uint8)).save(preview_path)

        manifest["outputs"].append({
            "frame_name": frame_name,
            "image_path": str(image_path),
            "timestamp_sec": item["timestamp_sec"],
            "depth_path": str(depth_path),
            "preview_path": str(preview_path),
            "depth_shape": list(depth.shape),
            "depth_min": depth_min,
            "depth_max": depth_max,
        })
        manifest["processed_frames"] += 1
        print("DEPTH_OK", idx, frame_name, depth.shape, depth_min, depth_max)
    except Exception as exc:
        manifest["failed_frames"].append({
            "frame_name": frame_name,
            "image_path": str(image_path),
            "error_type": type(exc).__name__,
            "error": str(exc),
        })
        print("DEPTH_NG", idx, frame_name, type(exc).__name__, str(exc))

manifest_path = out_dir / "depth_batch_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "device": manifest["device"],
    "processed_frames": manifest["processed_frames"],
    "failed_frames": len(manifest["failed_frames"]),
    "first_output": None if not manifest["outputs"] else manifest["outputs"][0],
    "last_output": None if not manifest["outputs"] else manifest["outputs"][-1],
    "saved": str(manifest_path),
}, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7c sampled-frame depth batch res
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
WARNING:huggingface_hub.utils._http:Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
[INFO ] using MLP layer as FFN
[INFO ] Processed Images Done taking 0.026829004287719727 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.44693803787231445 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0011518001556396484 seconds
DEPTH_OK 0 frame_000009.jpg (378, 504) 0.31544607877731323 4.0310516357421875
[INFO ] Processed Images Done taking 0.016257762908935547 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.3539915084838867 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0009372234344482422 seconds
DEPTH_OK 1 frame_000058.jpg (378, 504) 0.3436773717403412 4.366101264953613
[INFO ] Processed Images Done taking 0.018395185470581055 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35202765464782715 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0011284351348876953 seconds
DEPTH_OK 2 frame_000103.jpg (378, 504) 0.35914379358291626 3.650329351425171
[INFO ] Processed Images Done taking 0.016307592391967773 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35187506675720215 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0012009143829345703 seconds
DEPTH_OK 3 frame_000143.jpg (378, 504) 0.28807052969932556 2.6115517616271973
[INFO ] Processed Images Done taking 0.015880823135375977 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.3542790412902832 seconds
[INFO ] Conversion to Prediction Done. Time: 0.001153707504272461 seconds
DEPTH_OK 4 frame_000189.jpg (378, 504) 0.26627305150032043 2.6933023929595947
[INFO ] Processed Images Done taking 0.01707601547241211 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35399818420410156 seconds
[INFO ] Conversion to Prediction Done. Time: 0.000926971435546875 seconds
DEPTH_OK 5 frame_000230.jpg (378, 504) 0.3931887149810791 3.402815103530884
[INFO ] Processed Images Done taking 0.013835906982421875 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.3553924560546875 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0009696483612060547 seconds
DEPTH_OK 6 frame_000274.jpg (378, 504) 0.47461241483688354 4.119905948638916
[INFO ] Processed Images Done taking 0.02049994468688965 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.3538358211517334 seconds
[INFO ] Conversion to Prediction Done. Time: 0.000934600830078125 seconds
DEPTH_OK 7 frame_000314.jpg (378, 504) 0.4533892273902893 4.051567077636719
[INFO ] Processed Images Done taking 0.015220880508422852 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.3534739017486572 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0011980533599853516 seconds
DEPTH_OK 8 frame_000356.jpg (378, 504) 0.36209359765052795 2.9028055667877197
[INFO ] Processed Images Done taking 0.013386964797973633 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35712122917175293 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0011417865753173828 seconds
DEPTH_OK 9 frame_000395.jpg (378, 504) 0.28270581364631653 1.9280147552490234
[INFO ] Processed Images Done taking 0.016958951950073242 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.3567516803741455 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0011949539184570312 seconds
DEPTH_OK 10 frame_000457.jpg (378, 504) 0.300882488489151 3.6980714797973633
[INFO ] Processed Images Done taking 0.016394615173339844 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35483551025390625 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0009105205535888672 seconds
DEPTH_OK 11 frame_000520.jpg (378, 504) 0.2709210515022278 3.517655611038208
{
  "device": "cuda",
  "processed_frames": 12,
  "failed_frames": 0,
  "first_output": {
    "frame_name": "frame_000009.jpg",
    "image_path": "/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000009.jpg",
    "timestamp_sec": 916764.341604734,
    "depth_path": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/depth_batch_v01/frame_000009_depth.npy",
    "preview_path": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/depth_batch_v01/frame_000009_depth.png",
    "depth_shape": [
      378,
      504
    ],
    "depth_min": 0.31544607877731323,
    "depth_max": 4.0310516357421875
  },
  "last_output": {
    "frame_name": "frame_000520.jpg",
    "image_path": "/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000520.jpg",
    "timestamp_sec": 916768.29554448,
    "depth_path": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/depth_batch_v01/frame_000520_depth.npy",
    "preview_path": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/depth_batch_v01/frame_000520_depth.png",
    "depth_shape": [
      378,
      504
    ],
    "depth_min": 0.2709210515022278,
    "depth_max": 3.517655611038208
  },
  "saved": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/depth_batch_v01/depth_batch_manifest.json"
}
```

# codex

2026-03-30 v31 step-7d multi-frame world-point fusion。

- 目的: `12 frame` の depth batch を `ARCore pose` と `frame_pose_index.csv` で world へ戻し、multi-frame 点群を統合して `PLY` を出す。
- 成功条件:
  - `depth_batch_manifest.json` を読める
  - 各 frame の `pose_record_index` を引ける
  - world point 群を結合して `.npy` と `.ply` を保存できる
  - frame ごとの点数 summary を保存できる
- 失敗時の扱い:
  - 一部 frame で pose が引けなければ、その frame 名を `skipped_frames` に残して続行する
  - 点数が極端に多ければ sampling stride を `24 -> 32` へ上げる

```python
# Step 7d multi-frame world-point fusion
from pathlib import Path
import json
import numpy as np
import pandas as pd

SESSION_ROOT = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
SESSION_BUNDLE_ROOT = SESSION_ROOT.parent
probe_dir = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01")
batch_dir = probe_dir / "depth_batch_v01"
manifest_path = batch_dir / "depth_batch_manifest.json"
out_dir = probe_dir / "world_fusion_v01"
out_dir.mkdir(parents=True, exist_ok=True)

frame_index = pd.read_csv(SESSION_ROOT / "frame_pose_index.csv")
pose_path = SESSION_ROOT / "arcore_pose.jsonl"
if not pose_path.exists():
    pose_path = SESSION_BUNDLE_ROOT / "arcore_pose.jsonl"

with pose_path.open("r", encoding="utf-8") as f:
    pose_records = [json.loads(line) for line in f if line.strip()]

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
outputs = manifest["outputs"]

frame_name_to_row = {}
for _, row in frame_index.iterrows():
    image_name = row.get("image_file_name")
    if isinstance(image_name, str) and image_name:
        frame_name_to_row[image_name] = row

all_points = []
per_frame = []
skipped = []
stride = 24

for item in outputs:
    frame_name = item["frame_name"]
    row = frame_name_to_row.get(frame_name)
    if row is None:
        skipped.append({"frame_name": frame_name, "reason": "frame_index_row_not_found"})
        continue

    pose_idx = int(row["pose_record_index"])
    if pose_idx < 0 or pose_idx >= len(pose_records):
        skipped.append({"frame_name": frame_name, "reason": "pose_record_index_out_of_range", "pose_record_index": pose_idx})
        continue

    record = pose_records[pose_idx]
    pose = record["pose"]
    intr = record["imageIntrinsics"]
    depth = np.load(item["depth_path"])

    h, w = depth.shape
    grid_y, grid_x = np.mgrid[0:h:stride, 0:w:stride]
    z = depth[grid_y, grid_x]
    x = (grid_x - float(intr["cx"])) * z / float(intr["fx"])
    y = (grid_y - float(intr["cy"])) * z / float(intr["fy"])
    camera_points = np.stack([x, y, z], axis=-1).reshape(-1, 3)

    t = np.array([pose["tx"], pose["ty"], pose["tz"]], dtype=np.float32)
    world_points = camera_points.astype(np.float32) + t

    all_points.append(world_points)
    per_frame.append({
        "frame_name": frame_name,
        "pose_record_index": pose_idx,
        "point_count": int(len(world_points)),
        "timestamp_sec": item["timestamp_sec"],
    })
    print("WORLD_OK", frame_name, len(world_points), pose_idx)

assert all_points, "no world points generated"

merged = np.concatenate(all_points, axis=0).astype(np.float32)
npy_path = out_dir / "world_points_multiframe.npy"
ply_path = out_dir / "world_points_multiframe.ply"
summary_path = out_dir / "world_fusion_summary.json"

np.save(npy_path, merged)

with ply_path.open("w", encoding="utf-8") as f:
    f.write("ply\nformat ascii 1.0\n")
    f.write(f"element vertex {len(merged)}\n")
    f.write("property float x\nproperty float y\nproperty float z\n")
    f.write("end_header\n")
    for p in merged:
        f.write(f\"{p[0]} {p[1]} {p[2]}\\n\")

summary = {
    "stride": stride,
    "processed_frames": len(per_frame),
    "skipped_frames": skipped,
    "total_points": int(len(merged)),
    "per_frame": per_frame,
    "npy_path": str(npy_path),
    "ply_path": str(ply_path),
}
summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "processed_frames": summary["processed_frames"],
    "skipped_frames": len(summary["skipped_frames"]),
    "total_points": summary["total_points"],
    "first_frame": None if not per_frame else per_frame[0],
    "last_frame": None if not per_frame else per_frame[-1],
    "saved_npy": str(npy_path),
    "saved_ply": str(ply_path),
    "saved_summary": str(summary_path),
}, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7d multi-frame world-point fusion res

```

# codex

2026-03-30 v32 step-7d retry after syntax fix。

- 原因: 前 block の `PLY` 書き出しで `f.write(f\"...\")` となっており、Python syntax error になる。
- 対応: それ以外は変えず、`PLY` 書き出し行だけ直した retry block を実行する。
- 成功条件:
  - `world_points_multiframe.npy`
  - `world_points_multiframe.ply`
  - `world_fusion_summary.json`
  が保存される

```python
# Step 7d retry after syntax fix
from pathlib import Path
import json
import numpy as np
import pandas as pd

SESSION_ROOT = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
SESSION_BUNDLE_ROOT = SESSION_ROOT.parent
probe_dir = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01")
batch_dir = probe_dir / "depth_batch_v01"
manifest_path = batch_dir / "depth_batch_manifest.json"
out_dir = probe_dir / "world_fusion_v01"
out_dir.mkdir(parents=True, exist_ok=True)

frame_index = pd.read_csv(SESSION_ROOT / "frame_pose_index.csv")
pose_path = SESSION_ROOT / "arcore_pose.jsonl"
if not pose_path.exists():
    pose_path = SESSION_BUNDLE_ROOT / "arcore_pose.jsonl"

with pose_path.open("r", encoding="utf-8") as f:
    pose_records = [json.loads(line) for line in f if line.strip()]

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
outputs = manifest["outputs"]

frame_name_to_row = {}
for _, row in frame_index.iterrows():
    image_name = row.get("image_file_name")
    if isinstance(image_name, str) and image_name:
        frame_name_to_row[image_name] = row

all_points = []
per_frame = []
skipped = []
stride = 24

for item in outputs:
    frame_name = item["frame_name"]
    row = frame_name_to_row.get(frame_name)
    if row is None:
        skipped.append({"frame_name": frame_name, "reason": "frame_index_row_not_found"})
        continue

    pose_idx = int(row["pose_record_index"])
    if pose_idx < 0 or pose_idx >= len(pose_records):
        skipped.append({"frame_name": frame_name, "reason": "pose_record_index_out_of_range", "pose_record_index": pose_idx})
        continue

    record = pose_records[pose_idx]
    pose = record["pose"]
    intr = record["imageIntrinsics"]
    depth = np.load(item["depth_path"])

    h, w = depth.shape
    grid_y, grid_x = np.mgrid[0:h:stride, 0:w:stride]
    z = depth[grid_y, grid_x]
    x = (grid_x - float(intr["cx"])) * z / float(intr["fx"])
    y = (grid_y - float(intr["cy"])) * z / float(intr["fy"])
    camera_points = np.stack([x, y, z], axis=-1).reshape(-1, 3)

    t = np.array([pose["tx"], pose["ty"], pose["tz"]], dtype=np.float32)
    world_points = camera_points.astype(np.float32) + t

    all_points.append(world_points)
    per_frame.append({
        "frame_name": frame_name,
        "pose_record_index": pose_idx,
        "point_count": int(len(world_points)),
        "timestamp_sec": item["timestamp_sec"],
    })
    print("WORLD_OK", frame_name, len(world_points), pose_idx)

assert all_points, "no world points generated"

merged = np.concatenate(all_points, axis=0).astype(np.float32)
npy_path = out_dir / "world_points_multiframe.npy"
ply_path = out_dir / "world_points_multiframe.ply"
summary_path = out_dir / "world_fusion_summary.json"

np.save(npy_path, merged)

with ply_path.open("w", encoding="utf-8") as f:
    f.write("ply\nformat ascii 1.0\n")
    f.write(f"element vertex {len(merged)}\n")
    f.write("property float x\nproperty float y\nproperty float z\n")
    f.write("end_header\n")
    for p in merged:
        f.write(f"{p[0]} {p[1]} {p[2]}\n")

summary = {
    "stride": stride,
    "processed_frames": len(per_frame),
    "skipped_frames": skipped,
    "total_points": int(len(merged)),
    "per_frame": per_frame,
    "npy_path": str(npy_path),
    "ply_path": str(ply_path),
}
summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "processed_frames": summary["processed_frames"],
    "skipped_frames": len(summary["skipped_frames"]),
    "total_points": summary["total_points"],
    "first_frame": None if not per_frame else per_frame[0],
    "last_frame": None if not per_frame else per_frame[-1],
    "saved_npy": str(npy_path),
    "saved_ply": str(ply_path),
    "saved_summary": str(summary_path),
}, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7d retry after syntax fix res
WORLD_OK frame_000009.jpg 336 1
WORLD_OK frame_000058.jpg 336 17
WORLD_OK frame_000103.jpg 336 34
WORLD_OK frame_000143.jpg 336 50
WORLD_OK frame_000189.jpg 336 67
WORLD_OK frame_000230.jpg 336 83
WORLD_OK frame_000274.jpg 336 100
WORLD_OK frame_000314.jpg 336 116
WORLD_OK frame_000356.jpg 336 133
WORLD_OK frame_000395.jpg 336 149
WORLD_OK frame_000457.jpg 336 166
{
  "processed_frames": 11,
  "skipped_frames": 1,
  "total_points": 3696,
  "first_frame": {
    "frame_name": "frame_000009.jpg",
    "pose_record_index": 1,
    "point_count": 336,
    "timestamp_sec": 916764.341604734
  },
  "last_frame": {
    "frame_name": "frame_000457.jpg",
    "pose_record_index": 166,
    "point_count": 336,
    "timestamp_sec": 916767.944921453
  },
  "saved_npy": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/world_fusion_v01/world_points_multiframe.npy",
  "saved_ply": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/world_fusion_v01/world_points_multiframe.ply",
  "saved_summary": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/world_fusion_v01/world_fusion_summary.json"
}

```

# codex

2026-03-30 v33 step-7e closeout preview and summary。

- 判定: `Step 7d` は実質成功。
  - `processed_frames = 11`
  - `skipped_frames = 1`
  - `total_points = 3696`
  - `world_points_multiframe.npy` と `world_points_multiframe.ply` 保存済み
- 目的: admin が `PLY` viewer で確認する前に、最小 preview と `MRL-7` closeout 用 summary を保存する。
- 成功条件:
  - `world_points_multiframe_preview.png` を保存できる
  - `mrl7_closeout_summary.json` を保存できる
  - skipped frame を summary に残せる

```python
# Step 7e closeout preview and summary
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt

probe_dir = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01")
world_dir = probe_dir / "world_fusion_v01"
summary_path = world_dir / "world_fusion_summary.json"
points_path = world_dir / "world_points_multiframe.npy"
preview_path = world_dir / "world_points_multiframe_preview.png"
closeout_path = world_dir / "mrl7_closeout_summary.json"

summary = json.loads(summary_path.read_text(encoding="utf-8"))
points = np.load(points_path)

fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection="3d")
sample = points[::4] if len(points) > 4000 else points
ax.scatter(sample[:, 0], sample[:, 1], sample[:, 2], s=1, alpha=0.6)
ax.set_title("MRL-7 multiframe world points preview")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_zlabel("z")
plt.tight_layout()
plt.savefig(preview_path, dpi=180)
plt.close(fig)

closeout = {
    "status": "candidate-visible-proof",
    "processed_frames": summary["processed_frames"],
    "skipped_frames": summary["skipped_frames"],
    "total_points": summary["total_points"],
    "preview_path": str(preview_path),
    "ply_path": summary["ply_path"],
    "npy_path": summary["npy_path"],
    "per_frame_point_count": [x["point_count"] for x in summary["per_frame"]],
}
closeout_path.write_text(json.dumps(closeout, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "preview_exists": preview_path.exists(),
    "closeout_exists": closeout_path.exists(),
    "processed_frames": closeout["processed_frames"],
    "skipped_frames": len(closeout["skipped_frames"]),
    "total_points": closeout["total_points"],
    "preview_path": str(preview_path),
    "closeout_path": str(closeout_path),
}, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7e closeout preview and summary res
{
  "preview_exists": true,
  "closeout_exists": true,
  "processed_frames": 11,
  "skipped_frames": 1,
  "total_points": 3696,
  "preview_path": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/world_fusion_v01/world_points_multiframe_preview.png",
  "closeout_path": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/world_fusion_v01/mrl7_closeout_summary.json"
}
```

# codex

2026-03-30 v34 step-7f multiframe viewer bundle export。

- 判定: `mRL-7.1` は `p-done` として閉じる。
  - 実 session の最長連続 window を正にした `multi-frame` sampling
  - `12 frame` depth batch
  - `11 frame` world fusion
  - `3696 points`
  - preview と closeout summary 保存
- 目的: `mRL-7.2` の最初の command として、admin が local viewer で見られる bundle を 1 zip にまとめる。
- 成功条件:
  - `mrl7_multiframe_viewer_bundle.zip` を作れる
  - `world_points_multiframe.ply`、`world_points_multiframe_preview.png`、`mrl7_closeout_summary.json` を同梱できる
  - download 用の file path を返せる

```python
# Step 7f multiframe viewer bundle export
from pathlib import Path
import json
import shutil

probe_dir = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01")
world_dir = probe_dir / "world_fusion_v01"
bundle_dir = probe_dir / "viewer_bundle_v01"
bundle_zip = Path("/content/mrl7_multiframe_viewer_bundle.zip")

if bundle_dir.exists():
    shutil.rmtree(bundle_dir)
bundle_dir.mkdir(parents=True, exist_ok=True)

copy_targets = [
    "world_points_multiframe.ply",
    "world_points_multiframe.npy",
    "world_points_multiframe_preview.png",
    "world_fusion_summary.json",
    "mrl7_closeout_summary.json",
]

copied = []
for name in copy_targets:
    src = world_dir / name
    assert src.exists(), {"missing_artifact": str(src)}
    dst = bundle_dir / name
    shutil.copy2(src, dst)
    copied.append(str(dst))

if bundle_zip.exists():
    bundle_zip.unlink()

archive_base = str(bundle_zip.with_suffix(""))
shutil.make_archive(archive_base, "zip", root_dir=str(bundle_dir))

print(json.dumps({
    "bundle_dir": str(bundle_dir),
    "bundle_zip": str(bundle_zip),
    "bundle_zip_exists": bundle_zip.exists(),
    "copied_count": len(copied),
    "copied_names": [Path(x).name for x in copied],
}, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7f multiframe viewer bundle export res
{
  "bundle_dir": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/viewer_bundle_v01",
  "bundle_zip": "/content/mrl7_multiframe_viewer_bundle.zip",
  "bundle_zip_exists": true,
  "copied_count": 5,
  "copied_names": [
    "world_points_multiframe.ply",
    "world_points_multiframe.npy",
    "world_points_multiframe_preview.png",
    "world_fusion_summary.json",
    "mrl7_closeout_summary.json"
  ]
}
```

# codex

2026-03-30 v35 step-7g viewer bundle download。

- 判定: `Step 7f` は成功。
  - local viewer 用 zip は作成済み
  - `world_points_multiframe.ply`
  - `world_points_multiframe_preview.png`
  - `mrl7_closeout_summary.json`
  を 1 bundle にまとめられた
- 目的: admin が local PC に zip を落として、`mRL-7.2` の `PLY` viewer 目視確認へ入れる状態にする。
- 成功条件:
  - browser download が始まる
  - local に `mrl7_multiframe_viewer_bundle.zip` を保存できる

```python
# Step 7g viewer bundle download
from pathlib import Path
from google.colab import files

bundle_zip = Path("/content/mrl7_multiframe_viewer_bundle.zip")
assert bundle_zip.exists(), {"bundle_zip_not_found": str(bundle_zip)}

print({
    "bundle_zip": str(bundle_zip),
    "size_bytes": bundle_zip.stat().st_size,
})

files.download(str(bundle_zip))
```

# admin

```text
# Step 7g viewer bundle download res
{'bundle_zip': '/content/mrl7_multiframe_viewer_bundle.zip', 'size_bytes': 447776}
```

# codex

2026-03-30 v36 step-7h local viewer check。

- 判定: `Step 7g` は成功。
  - download 開始に必要な zip は存在した
  - `size_bytes = 447776`
- 目的: `mRL-7.2` の最初の admin 目視確認として、local PC で `PLY` を開き、空間のまとまりと見え方を短く記録する。
- 手順:
  - local へ保存した `mrl7_multiframe_viewer_bundle.zip` を展開する
  - `world_points_multiframe_preview.png` を先に見る
  - `world_points_multiframe.ply` を `CloudCompare` または `MeshLab` で開く
  - 回転 / zoom して、少なくとも `1` つの空間らしい塊が見えるかを見る
- 成功条件:
  - `PLY` を local viewer で開ける
  - `空間らしい塊が見える / 見えない / 判断しにくい` の 3 択で返せる
  - 必要なら screenshot path を返せる

```text
# local viewer check

1. `mrl7_multiframe_viewer_bundle.zip` を展開
2. `world_points_multiframe_preview.png` を確認
3. `world_points_multiframe.ply` を `CloudCompare` または `MeshLab` で開く
4. 点群を回して次を短く判断
   - `space_visible`: yes / no / unclear
   - `shape_note`: 1 行
   - `next_need`: none / denser points / color / trajectory overlay
```

# admin

```text
# Step 7h local viewer check res

```

# codex

2026-03-30 v37 step-7i gaussian-init-and-one-step-optim probe。

- 判定: 次は `正規 gaussian parameter の生成と最適化` へ入る。
- 目的: current multi-frame point cloud から最小 gaussian parameter を初期化し、`gsplat` 上で `1 step` の最適化が物理的に回るかを確認する。
- この step で見ること:
  - `means`
  - `scales`
  - `quats`
  - `opacities`
  - `colors`
  を tensor として持てるか
  - `rasterization` の forward / backward が通るか
  - loss が数値として出るか
- 成功条件:
  - `gaussian_init_summary.json` を保存できる
  - `gaussian_one_step_probe.json` を保存できる
  - `loss_before`、`loss_after`、`backward_ok` を返せる

```python
# Step 7i gaussian-init-and-one-step-optim probe
from pathlib import Path
import json
import math
import numpy as np
import torch
import imageio.v3 as iio
import pandas as pd
import gsplat

probe_dir = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01")
world_dir = probe_dir / "world_fusion_v01"
batch_dir = probe_dir / "depth_batch_v01"
window_path = probe_dir / "mrl7_window_probe.json"
session_root = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")

points_path = world_dir / "world_points_multiframe.npy"
summary_out = world_dir / "gaussian_init_summary.json"
probe_out = world_dir / "gaussian_one_step_probe.json"

assert points_path.exists(), {"points_not_found": str(points_path)}
assert window_path.exists(), {"window_probe_not_found": str(window_path)}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
points_np = np.load(points_path).astype(np.float32)
window_info = json.loads(window_path.read_text(encoding="utf-8"))
sampled = window_info["sampled_frames"]
assert sampled, "sampled_frames empty"

# 初期点数を絞る。まずは「正規 gaussian parameter を持てるか」と「1 step 回るか」を見る。
max_points = 1024
if len(points_np) > max_points:
    pick = np.linspace(0, len(points_np) - 1, max_points).astype(np.int64)
    points_np = points_np[pick]

first_frame = sampled[0]["frame_name"]
image_path = session_root / "images" / first_frame
assert image_path.exists(), {"image_not_found": str(image_path)}
image = iio.imread(image_path)
if image.ndim == 2:
    image = np.stack([image, image, image], axis=-1)
image = image[..., :3]
target_h, target_w = image.shape[:2]
target = torch.from_numpy(image.astype(np.float32) / 255.0).to(device)

# 最小の camera 情報は session の実 record から引く
frame_pose_df = pd.read_csv(session_root / "frame_pose_index.csv")
row = frame_pose_df.loc[frame_pose_df["image_file_name"] == first_frame].iloc[0]
pose_index = int(row["pose_record_index"])

records = []
with (session_root / "arcore_pose.jsonl").open("r", encoding="utf-8") as f:
    for line in f:
        records.append(json.loads(line))
pose_rec = records[pose_index]

intr = pose_rec["imageIntrinsics"]
pose = pose_rec["pose"]

fx = float(intr["fx"])
fy = float(intr["fy"])
cx = float(intr["cx"])
cy = float(intr["cy"])
width = int(intr["width"])
height = int(intr["height"])

tx = float(pose["tx"])
ty = float(pose["ty"])
tz = float(pose["tz"])
qx = float(pose["qx"])
qy = float(pose["qy"])
qz = float(pose["qz"])
qw = float(pose["qw"])

def quat_to_rot(qx, qy, qz, qw):
    xx, yy, zz = qx*qx, qy*qy, qz*qz
    xy, xz, yz = qx*qy, qx*qz, qy*qz
    wx, wy, wz = qw*qx, qw*qy, qw*qz
    return np.array([
        [1 - 2*(yy + zz), 2*(xy - wz), 2*(xz + wy)],
        [2*(xy + wz), 1 - 2*(xx + zz), 2*(yz - wx)],
        [2*(xz - wy), 2*(yz + wx), 1 - 2*(xx + yy)],
    ], dtype=np.float32)

R_wc = quat_to_rot(qx, qy, qz, qw)
t_wc = np.array([tx, ty, tz], dtype=np.float32)
R_cw = R_wc.T
t_cw = -R_cw @ t_wc

viewmat = np.eye(4, dtype=np.float32)
viewmat[:3, :3] = R_cw
viewmat[:3, 3] = t_cw
viewmat = torch.from_numpy(viewmat).to(device)

K = torch.tensor([
    [fx, 0.0, cx],
    [0.0, fy, cy],
    [0.0, 0.0, 1.0],
], dtype=torch.float32, device=device)

means = torch.nn.Parameter(torch.from_numpy(points_np).to(device))
scales = torch.nn.Parameter(torch.full((len(points_np), 3), math.log(0.03), dtype=torch.float32, device=device))
quats = torch.nn.Parameter(torch.tensor([[0.0, 0.0, 0.0, 1.0]], dtype=torch.float32, device=device).repeat(len(points_np), 1))
opacities = torch.nn.Parameter(torch.full((len(points_np), 1), 0.1, dtype=torch.float32, device=device))

# まずは白色で開始。ここは probe なので color 学習可能かだけを見る。
colors = torch.nn.Parameter(torch.full((len(points_np), 3), 0.7, dtype=torch.float32, device=device))

summary_out.write_text(json.dumps({
    "point_count": int(len(points_np)),
    "target_frame": first_frame,
    "target_hw": [int(target_h), int(target_w)],
    "fx": fx,
    "fy": fy,
    "cx": cx,
    "cy": cy,
}, indent=2, ensure_ascii=False), encoding="utf-8")

optimizer = torch.optim.Adam([means, scales, quats, opacities, colors], lr=1e-2)

def render_once():
    render_colors, render_alphas, meta = gsplat.rasterization(
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
    pred = render_colors[0]
    return pred, render_alphas[0]

optimizer.zero_grad(set_to_none=True)
pred0, alpha0 = render_once()
loss0 = torch.mean((pred0 - target) ** 2)
loss0.backward()
optimizer.step()

optimizer.zero_grad(set_to_none=True)
pred1, alpha1 = render_once()
loss1 = torch.mean((pred1 - target) ** 2)

result = {
    "backward_ok": True,
    "point_count": int(len(points_np)),
    "target_frame": first_frame,
    "loss_before": float(loss0.detach().cpu().item()),
    "loss_after": float(loss1.detach().cpu().item()),
    "alpha_mean_after": float(alpha1.mean().detach().cpu().item()),
    "summary_path": str(summary_out),
    "probe_path": str(probe_out),
}
probe_out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(result, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7i gaussian-init-and-one-step-optim probe res
---------------------------------------------------------------------------
KeyError                                  Traceback (most recent call last)
/tmp/ipykernel_3356/2166920141.py in <cell line: 0>()
     25 points_np = np.load(points_path).astype(np.float32)
     26 window_info = json.loads(window_path.read_text(encoding="utf-8"))
---> 27 sampled = window_info["sampled_frames"]
     28 assert sampled, "sampled_frames empty"
     29 

KeyError: 'sampled_frames'
```

# codex

2026-03-30 v38 step-7i1 window-schema-fix-and-retry。

- 判定: `Step 7i` の失敗は gaussian 最適化本体ではなく、`mrl7_window_probe.json` の key 想定違い。
- 目的: まず window probe の実 key を確認し、その場で sampled list を吸収して `gaussian init + 1 step optim` を retry する。
- 成功条件:
  - `window_keys` を表示できる
  - sampled frame list を実 key から取得できる
  - `gaussian_one_step_probe.json` を保存できる

```python
# Step 7i1 window-schema-fix-and-retry
from pathlib import Path
import json
import math
import numpy as np
import torch
import imageio.v3 as iio
import pandas as pd
import gsplat

probe_dir = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01")
world_dir = probe_dir / "world_fusion_v01"
window_path = probe_dir / "mrl7_window_probe.json"
session_root = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")

points_path = world_dir / "world_points_multiframe.npy"
summary_out = world_dir / "gaussian_init_summary.json"
probe_out = world_dir / "gaussian_one_step_probe.json"

window_info = json.loads(window_path.read_text(encoding="utf-8"))
window_keys = sorted(window_info.keys())

sampled = (
    window_info.get("sampled_frames")
    or window_info.get("sampled_images")
    or window_info.get("sampled")
    or window_info.get("sampled_frame_names")
)
assert sampled, {"window_keys": window_keys, "error": "sampled list not found"}

first_item = sampled[0]
if isinstance(first_item, dict):
    first_frame = first_item.get("frame_name") or first_item.get("image_file_name") or first_item.get("name")
else:
    first_frame = str(first_item)
assert first_frame, {"window_keys": window_keys, "sampled_example": first_item}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
points_np = np.load(points_path).astype(np.float32)
max_points = 1024
if len(points_np) > max_points:
    pick = np.linspace(0, len(points_np) - 1, max_points).astype(np.int64)
    points_np = points_np[pick]

image_path = session_root / "images" / first_frame
assert image_path.exists(), {"image_not_found": str(image_path), "first_frame": first_frame}
image = iio.imread(image_path)
if image.ndim == 2:
    image = np.stack([image, image, image], axis=-1)
image = image[..., :3]
target_h, target_w = image.shape[:2]
target = torch.from_numpy(image.astype(np.float32) / 255.0).to(device)

frame_pose_df = pd.read_csv(session_root / "frame_pose_index.csv")
row = frame_pose_df.loc[frame_pose_df["image_file_name"] == first_frame].iloc[0]
pose_index = int(row["pose_record_index"])

records = []
with (session_root / "arcore_pose.jsonl").open("r", encoding="utf-8") as f:
    for line in f:
        records.append(json.loads(line))
pose_rec = records[pose_index]

intr = pose_rec["imageIntrinsics"]
pose = pose_rec["pose"]

fx = float(intr["fx"])
fy = float(intr["fy"])
cx = float(intr["cx"])
cy = float(intr["cy"])

tx = float(pose["tx"])
ty = float(pose["ty"])
tz = float(pose["tz"])
qx = float(pose["qx"])
qy = float(pose["qy"])
qz = float(pose["qz"])
qw = float(pose["qw"])

def quat_to_rot(qx, qy, qz, qw):
    xx, yy, zz = qx*qx, qy*qy, qz*qz
    xy, xz, yz = qx*qy, qx*qz, qy*qz
    wx, wy, wz = qw*qx, qw*qy, qw*qz
    return np.array([
        [1 - 2*(yy + zz), 2*(xy - wz), 2*(xz + wy)],
        [2*(xy + wz), 1 - 2*(xx + zz), 2*(yz - wx)],
        [2*(xz - wy), 2*(yz + wx), 1 - 2*(xx + yy)],
    ], dtype=np.float32)

R_wc = quat_to_rot(qx, qy, qz, qw)
t_wc = np.array([tx, ty, tz], dtype=np.float32)
R_cw = R_wc.T
t_cw = -R_cw @ t_wc

viewmat = np.eye(4, dtype=np.float32)
viewmat[:3, :3] = R_cw
viewmat[:3, 3] = t_cw
viewmat = torch.from_numpy(viewmat).to(device)

K = torch.tensor([
    [fx, 0.0, cx],
    [0.0, fy, cy],
    [0.0, 0.0, 1.0],
], dtype=torch.float32, device=device)

means = torch.nn.Parameter(torch.from_numpy(points_np).to(device))
scales = torch.nn.Parameter(torch.full((len(points_np), 3), math.log(0.03), dtype=torch.float32, device=device))
quats = torch.nn.Parameter(torch.tensor([[0.0, 0.0, 0.0, 1.0]], dtype=torch.float32, device=device).repeat(len(points_np), 1))
opacities = torch.nn.Parameter(torch.full((len(points_np), 1), 0.1, dtype=torch.float32, device=device))
colors = torch.nn.Parameter(torch.full((len(points_np), 3), 0.7, dtype=torch.float32, device=device))

summary_out.write_text(json.dumps({
    "window_keys": window_keys,
    "point_count": int(len(points_np)),
    "target_frame": first_frame,
    "target_hw": [int(target_h), int(target_w)],
    "fx": fx,
    "fy": fy,
    "cx": cx,
    "cy": cy,
}, indent=2, ensure_ascii=False), encoding="utf-8")

optimizer = torch.optim.Adam([means, scales, quats, opacities, colors], lr=1e-2)

def render_once():
    render_colors, render_alphas, meta = gsplat.rasterization(
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

optimizer.zero_grad(set_to_none=True)
pred0, alpha0 = render_once()
loss0 = torch.mean((pred0 - target) ** 2)
loss0.backward()
optimizer.step()

optimizer.zero_grad(set_to_none=True)
pred1, alpha1 = render_once()
loss1 = torch.mean((pred1 - target) ** 2)

result = {
    "backward_ok": True,
    "window_keys": window_keys,
    "point_count": int(len(points_np)),
    "target_frame": first_frame,
    "loss_before": float(loss0.detach().cpu().item()),
    "loss_after": float(loss1.detach().cpu().item()),
    "alpha_mean_after": float(alpha1.mean().detach().cpu().item()),
    "summary_path": str(summary_out),
    "probe_path": str(probe_out),
}
probe_out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(result, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7i1 window-schema-fix-and-retry res
---------------------------------------------------------------------------
AssertionError                            Traceback (most recent call last)
/tmp/ipykernel_3356/2704158401.py in <cell line: 0>()
     27     or window_info.get("sampled_frame_names")
     28 )
---> 29 assert sampled, {"window_keys": window_keys, "error": "sampled list not found"}
     30 
     31 first_item = sampled[0]

AssertionError: {'window_keys': ['aligned_frame_count', 'frame_col', 'frame_index_path', 'sample_frame_count', 'sample_frames', 'session_root', 'time_col', 'window_end_sec', 'window_frame_count', 'window_span_sec', 'window_start_sec'], 'error': 'sampled list not found'}

```

# codex

2026-03-30 v39 step-7i2 sample-frames-key-fix。

- 判定: 実 key は `sample_frames`。
- 目的: `sample_frames` を吸収して、同じ gaussian init + 1 step optim を retry する。
- 成功条件:
  - `target_frame` を決められる
  - `gaussian_one_step_probe.json` を保存できる
  - `loss_before`、`loss_after`、`backward_ok` を返せる

```python
# Step 7i2 sample-frames-key-fix
from pathlib import Path
import json
import math
import numpy as np
import torch
import imageio.v3 as iio
import pandas as pd
import gsplat

probe_dir = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01")
world_dir = probe_dir / "world_fusion_v01"
window_path = probe_dir / "mrl7_window_probe.json"
session_root = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")

points_path = world_dir / "world_points_multiframe.npy"
summary_out = world_dir / "gaussian_init_summary.json"
probe_out = world_dir / "gaussian_one_step_probe.json"

window_info = json.loads(window_path.read_text(encoding="utf-8"))
window_keys = sorted(window_info.keys())

sampled = (
    window_info.get("sampled_frames")
    or window_info.get("sample_frames")
    or window_info.get("sampled_images")
    or window_info.get("sampled")
    or window_info.get("sampled_frame_names")
)
assert sampled, {"window_keys": window_keys, "error": "sampled list not found"}

first_item = sampled[0]
if isinstance(first_item, dict):
    first_frame = (
        first_item.get("frame_name")
        or first_item.get("image_file_name")
        or first_item.get("name")
    )
else:
    first_frame = str(first_item)
assert first_frame, {"window_keys": window_keys, "sampled_example": first_item}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
points_np = np.load(points_path).astype(np.float32)
max_points = 1024
if len(points_np) > max_points:
    pick = np.linspace(0, len(points_np) - 1, max_points).astype(np.int64)
    points_np = points_np[pick]

image_path = session_root / "images" / first_frame
assert image_path.exists(), {"image_not_found": str(image_path), "first_frame": first_frame}
image = iio.imread(image_path)
if image.ndim == 2:
    image = np.stack([image, image, image], axis=-1)
image = image[..., :3]
target_h, target_w = image.shape[:2]
target = torch.from_numpy(image.astype(np.float32) / 255.0).to(device)

frame_pose_df = pd.read_csv(session_root / "frame_pose_index.csv")
row = frame_pose_df.loc[frame_pose_df["image_file_name"] == first_frame].iloc[0]
pose_index = int(row["pose_record_index"])

records = []
with (session_root / "arcore_pose.jsonl").open("r", encoding="utf-8") as f:
    for line in f:
        records.append(json.loads(line))
pose_rec = records[pose_index]

intr = pose_rec["imageIntrinsics"]
pose = pose_rec["pose"]

fx = float(intr["fx"])
fy = float(intr["fy"])
cx = float(intr["cx"])
cy = float(intr["cy"])

tx = float(pose["tx"])
ty = float(pose["ty"])
tz = float(pose["tz"])
qx = float(pose["qx"])
qy = float(pose["qy"])
qz = float(pose["qz"])
qw = float(pose["qw"])

def quat_to_rot(qx, qy, qz, qw):
    xx, yy, zz = qx*qx, qy*qy, qz*qz
    xy, xz, yz = qx*qy, qx*qz, qy*qz
    wx, wy, wz = qw*qx, qw*qy, qw*qz
    return np.array([
        [1 - 2*(yy + zz), 2*(xy - wz), 2*(xz + wy)],
        [2*(xy + wz), 1 - 2*(xx + zz), 2*(yz - wx)],
        [2*(xz - wy), 2*(yz + wx), 1 - 2*(xx + yy)],
    ], dtype=np.float32)

R_wc = quat_to_rot(qx, qy, qz, qw)
t_wc = np.array([tx, ty, tz], dtype=np.float32)
R_cw = R_wc.T
t_cw = -R_cw @ t_wc

viewmat = np.eye(4, dtype=np.float32)
viewmat[:3, :3] = R_cw
viewmat[:3, 3] = t_cw
viewmat = torch.from_numpy(viewmat).to(device)

K = torch.tensor([
    [fx, 0.0, cx],
    [0.0, fy, cy],
    [0.0, 0.0, 1.0],
], dtype=torch.float32, device=device)

means = torch.nn.Parameter(torch.from_numpy(points_np).to(device))
scales = torch.nn.Parameter(torch.full((len(points_np), 3), math.log(0.03), dtype=torch.float32, device=device))
quats = torch.nn.Parameter(torch.tensor([[0.0, 0.0, 0.0, 1.0]], dtype=torch.float32, device=device).repeat(len(points_np), 1))
opacities = torch.nn.Parameter(torch.full((len(points_np), 1), 0.1, dtype=torch.float32, device=device))
colors = torch.nn.Parameter(torch.full((len(points_np), 3), 0.7, dtype=torch.float32, device=device))

summary_out.write_text(json.dumps({
    "window_keys": window_keys,
    "point_count": int(len(points_np)),
    "target_frame": first_frame,
    "target_hw": [int(target_h), int(target_w)],
    "fx": fx,
    "fy": fy,
    "cx": cx,
    "cy": cy,
}, indent=2, ensure_ascii=False), encoding="utf-8")

optimizer = torch.optim.Adam([means, scales, quats, opacities, colors], lr=1e-2)

def render_once():
    render_colors, render_alphas, meta = gsplat.rasterization(
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

optimizer.zero_grad(set_to_none=True)
pred0, alpha0 = render_once()
loss0 = torch.mean((pred0 - target) ** 2)
loss0.backward()
optimizer.step()

optimizer.zero_grad(set_to_none=True)
pred1, alpha1 = render_once()
loss1 = torch.mean((pred1 - target) ** 2)

result = {
    "backward_ok": True,
    "window_keys": window_keys,
    "point_count": int(len(points_np)),
    "target_frame": first_frame,
    "loss_before": float(loss0.detach().cpu().item()),
    "loss_after": float(loss1.detach().cpu().item()),
    "alpha_mean_after": float(alpha1.mean().detach().cpu().item()),
    "summary_path": str(summary_out),
    "probe_path": str(probe_out),
}
probe_out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(result, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7i2 sample-frames-key-fix res
---------------------------------------------------------------------------
FileNotFoundError                         Traceback (most recent call last)
/tmp/ipykernel_3356/3339517874.py in <cell line: 0>()
     62 
     63 records = []
---> 64 with (session_root / "arcore_pose.jsonl").open("r", encoding="utf-8") as f:
     65     for line in f:
     66         records.append(json.loads(line))

/usr/lib/python3.12/pathlib.py in open(self, mode, buffering, encoding, errors, newline)
   1011         if "b" not in mode:
   1012             encoding = io.text_encoding(encoding)
-> 1013         return io.open(self, mode, buffering, encoding, errors, newline)
   1014 
   1015     def read_bytes(self):

FileNotFoundError: [Errno 2] No such file or directory: '/content/trajectreview_input/session-20260328-103250/trajectreview/arcore_pose.jsonl'

```

# codex

2026-03-30 v40 step-7i3 arcore-pose-path-fix。

- 判定: 今回の失敗も gaussian 最適化本体ではなく `arcore_pose.jsonl` の path 解決違い。
- 既知:
  - `frame_pose_index.csv` と `images/` は `.../trajectreview/` 配下
  - `arcore_pose.jsonl` は 1 つ上の session root にある場合がある
- 目的: `arcore_pose.jsonl` を再探索して実 path を確定し、そのまま `gaussian init + 1 step optim` を retry する。
- 成功条件:
  - `arcore_pose_path` を返せる
  - `gaussian_one_step_probe.json` を保存できる
  - `loss_before`、`loss_after`、`backward_ok` を返せる

```python
# Step 7i3 arcore-pose-path-fix
from pathlib import Path
import json
import math
import numpy as np
import torch
import imageio.v3 as iio
import pandas as pd
import gsplat

probe_dir = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01")
world_dir = probe_dir / "world_fusion_v01"
window_path = probe_dir / "mrl7_window_probe.json"
session_root = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
session_outer = session_root.parent

points_path = world_dir / "world_points_multiframe.npy"
summary_out = world_dir / "gaussian_init_summary.json"
probe_out = world_dir / "gaussian_one_step_probe.json"

window_info = json.loads(window_path.read_text(encoding="utf-8"))
window_keys = sorted(window_info.keys())
sampled = (
    window_info.get("sampled_frames")
    or window_info.get("sample_frames")
    or window_info.get("sampled_images")
    or window_info.get("sampled")
    or window_info.get("sampled_frame_names")
)
assert sampled, {"window_keys": window_keys, "error": "sampled list not found"}

first_item = sampled[0]
if isinstance(first_item, dict):
    first_frame = (
        first_item.get("frame_name")
        or first_item.get("image_file_name")
        or first_item.get("name")
    )
else:
    first_frame = str(first_item)
assert first_frame, {"window_keys": window_keys, "sampled_example": first_item}

arcore_pose_candidates = [
    session_root / "arcore_pose.jsonl",
    session_outer / "arcore_pose.jsonl",
]
arcore_pose_path = next((p for p in arcore_pose_candidates if p.exists()), None)
assert arcore_pose_path is not None, {
    "arcore_pose_candidates": [str(p) for p in arcore_pose_candidates]
}

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
points_np = np.load(points_path).astype(np.float32)
max_points = 1024
if len(points_np) > max_points:
    pick = np.linspace(0, len(points_np) - 1, max_points).astype(np.int64)
    points_np = points_np[pick]

image_path = session_root / "images" / first_frame
assert image_path.exists(), {"image_not_found": str(image_path), "first_frame": first_frame}
image = iio.imread(image_path)
if image.ndim == 2:
    image = np.stack([image, image, image], axis=-1)
image = image[..., :3]
target_h, target_w = image.shape[:2]
target = torch.from_numpy(image.astype(np.float32) / 255.0).to(device)

frame_pose_df = pd.read_csv(session_root / "frame_pose_index.csv")
row = frame_pose_df.loc[frame_pose_df["image_file_name"] == first_frame].iloc[0]
pose_index = int(row["pose_record_index"])

records = []
with arcore_pose_path.open("r", encoding="utf-8") as f:
    for line in f:
        records.append(json.loads(line))
pose_rec = records[pose_index]

intr = pose_rec["imageIntrinsics"]
pose = pose_rec["pose"]

fx = float(intr["fx"])
fy = float(intr["fy"])
cx = float(intr["cx"])
cy = float(intr["cy"])

tx = float(pose["tx"])
ty = float(pose["ty"])
tz = float(pose["tz"])
qx = float(pose["qx"])
qy = float(pose["qy"])
qz = float(pose["qz"])
qw = float(pose["qw"])

def quat_to_rot(qx, qy, qz, qw):
    xx, yy, zz = qx*qx, qy*qy, qz*qz
    xy, xz, yz = qx*qy, qx*qz, qy*qz
    wx, wy, wz = qw*qx, qw*qy, qw*qz
    return np.array([
        [1 - 2*(yy + zz), 2*(xy - wz), 2*(xz + wy)],
        [2*(xy + wz), 1 - 2*(xx + zz), 2*(yz - wx)],
        [2*(xz - wy), 2*(yz + wx), 1 - 2*(xx + yy)],
    ], dtype=np.float32)

R_wc = quat_to_rot(qx, qy, qz, qw)
t_wc = np.array([tx, ty, tz], dtype=np.float32)
R_cw = R_wc.T
t_cw = -R_cw @ t_wc

viewmat = np.eye(4, dtype=np.float32)
viewmat[:3, :3] = R_cw
viewmat[:3, 3] = t_cw
viewmat = torch.from_numpy(viewmat).to(device)

K = torch.tensor([
    [fx, 0.0, cx],
    [0.0, fy, cy],
    [0.0, 0.0, 1.0],
], dtype=torch.float32, device=device)

means = torch.nn.Parameter(torch.from_numpy(points_np).to(device))
scales = torch.nn.Parameter(torch.full((len(points_np), 3), math.log(0.03), dtype=torch.float32, device=device))
quats = torch.nn.Parameter(torch.tensor([[0.0, 0.0, 0.0, 1.0]], dtype=torch.float32, device=device).repeat(len(points_np), 1))
opacities = torch.nn.Parameter(torch.full((len(points_np), 1), 0.1, dtype=torch.float32, device=device))
colors = torch.nn.Parameter(torch.full((len(points_np), 3), 0.7, dtype=torch.float32, device=device))

summary_out.write_text(json.dumps({
    "window_keys": window_keys,
    "arcore_pose_path": str(arcore_pose_path),
    "point_count": int(len(points_np)),
    "target_frame": first_frame,
    "target_hw": [int(target_h), int(target_w)],
    "fx": fx,
    "fy": fy,
    "cx": cx,
    "cy": cy,
}, indent=2, ensure_ascii=False), encoding="utf-8")

optimizer = torch.optim.Adam([means, scales, quats, opacities, colors], lr=1e-2)

def render_once():
    render_colors, render_alphas, meta = gsplat.rasterization(
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

optimizer.zero_grad(set_to_none=True)
pred0, alpha0 = render_once()
loss0 = torch.mean((pred0 - target) ** 2)
loss0.backward()
optimizer.step()

optimizer.zero_grad(set_to_none=True)
pred1, alpha1 = render_once()
loss1 = torch.mean((pred1 - target) ** 2)

result = {
    "backward_ok": True,
    "window_keys": window_keys,
    "arcore_pose_path": str(arcore_pose_path),
    "point_count": int(len(points_np)),
    "target_frame": first_frame,
    "loss_before": float(loss0.detach().cpu().item()),
    "loss_after": float(loss1.detach().cpu().item()),
    "alpha_mean_after": float(alpha1.mean().detach().cpu().item()),
    "summary_path": str(summary_out),
    "probe_path": str(probe_out),
}
probe_out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(result, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7i3 arcore-pose-path-fix res
---------------------------------------------------------------------------
AssertionError                            Traceback (most recent call last)
/tmp/ipykernel_3356/3487645675.py in <cell line: 0>()
    154 
    155 optimizer.zero_grad(set_to_none=True)
--> 156 pred0, alpha0 = render_once()
    157 loss0 = torch.mean((pred0 - target) ** 2)
    158 loss0.backward()

1 frames
/usr/local/lib/python3.12/dist-packages/gsplat/rendering.py in rasterization(means, quats, scales, opacities, colors, viewmats, Ks, width, height, near_plane, far_plane, radius_clip, eps2d, sh_degree, packed, tile_size, backgrounds, render_mode, sparse_grad, absgrad, rasterize_mode, channel_chunk, distributed, camera_model, segmented, covars, with_ut, with_eval3d, radial_coeffs, tangential_coeffs, thin_prism_coeffs, ftheta_coeffs, rolling_shutter, viewmats_rs)
    283         tri_indices = ([0, 0, 0, 1, 1, 2], [0, 1, 2, 1, 2, 2])
    284         covars = covars[..., tri_indices[0], tri_indices[1]]
--> 285     assert opacities.shape == batch_dims + (N,), opacities.shape
    286     assert viewmats.shape == batch_dims + (C, 4, 4), viewmats.shape
    287     assert Ks.shape == batch_dims + (C, 3, 3), Ks.shape

AssertionError: torch.Size([1024, 1])
```

# codex

2026-03-30 v41 step-7i4 opacity-shape-fix。

- 判定: 今回は `gsplat.rasterization` の実引数 shape mismatch。
- 原因:
  - `opacities` を `(N, 1)` で渡していた
  - `gsplat` 側の期待は `(N,)`
- 目的: shape だけ直して、同じ `gaussian init + 1 step optim` を retry する。
- 成功条件:
  - `backward_ok = true`
  - `loss_before`、`loss_after` を返せる
  - `gaussian_one_step_probe.json` を保存できる

```python
# Step 7i4 opacity-shape-fix
from pathlib import Path
import json
import math
import numpy as np
import torch
import imageio.v3 as iio
import pandas as pd
import gsplat

probe_dir = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01")
world_dir = probe_dir / "world_fusion_v01"
window_path = probe_dir / "mrl7_window_probe.json"
session_root = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
session_outer = session_root.parent

points_path = world_dir / "world_points_multiframe.npy"
summary_out = world_dir / "gaussian_init_summary.json"
probe_out = world_dir / "gaussian_one_step_probe.json"

window_info = json.loads(window_path.read_text(encoding="utf-8"))
sampled = (
    window_info.get("sampled_frames")
    or window_info.get("sample_frames")
    or window_info.get("sampled_images")
    or window_info.get("sampled")
    or window_info.get("sampled_frame_names")
)
assert sampled, "sampled list not found"

first_item = sampled[0]
if isinstance(first_item, dict):
    first_frame = (
        first_item.get("frame_name")
        or first_item.get("image_file_name")
        or first_item.get("name")
    )
else:
    first_frame = str(first_item)

arcore_pose_candidates = [
    session_root / "arcore_pose.jsonl",
    session_outer / "arcore_pose.jsonl",
]
arcore_pose_path = next((p for p in arcore_pose_candidates if p.exists()), None)
assert arcore_pose_path is not None, "arcore_pose.jsonl not found"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
points_np = np.load(points_path).astype(np.float32)
max_points = 1024
if len(points_np) > max_points:
    pick = np.linspace(0, len(points_np) - 1, max_points).astype(np.int64)
    points_np = points_np[pick]

image_path = session_root / "images" / first_frame
image = iio.imread(image_path)
if image.ndim == 2:
    image = np.stack([image, image, image], axis=-1)
image = image[..., :3]
target_h, target_w = image.shape[:2]
target = torch.from_numpy(image.astype(np.float32) / 255.0).to(device)

frame_pose_df = pd.read_csv(session_root / "frame_pose_index.csv")
row = frame_pose_df.loc[frame_pose_df["image_file_name"] == first_frame].iloc[0]
pose_index = int(row["pose_record_index"])

records = []
with arcore_pose_path.open("r", encoding="utf-8") as f:
    for line in f:
        records.append(json.loads(line))
pose_rec = records[pose_index]

intr = pose_rec["imageIntrinsics"]
pose = pose_rec["pose"]

fx = float(intr["fx"])
fy = float(intr["fy"])
cx = float(intr["cx"])
cy = float(intr["cy"])

tx = float(pose["tx"])
ty = float(pose["ty"])
tz = float(pose["tz"])
qx = float(pose["qx"])
qy = float(pose["qy"])
qz = float(pose["qz"])
qw = float(pose["qw"])

def quat_to_rot(qx, qy, qz, qw):
    xx, yy, zz = qx*qx, qy*qy, qz*qz
    xy, xz, yz = qx*qy, qx*qz, qy*qz
    wx, wy, wz = qw*qx, qw*qy, qw*qz
    return np.array([
        [1 - 2*(yy + zz), 2*(xy - wz), 2*(xz + wy)],
        [2*(xy + wz), 1 - 2*(xx + zz), 2*(yz - wx)],
        [2*(xz - wy), 2*(yz + wx), 1 - 2*(xx + yy)],
    ], dtype=np.float32)

R_wc = quat_to_rot(qx, qy, qz, qw)
t_wc = np.array([tx, ty, tz], dtype=np.float32)
R_cw = R_wc.T
t_cw = -R_cw @ t_wc

viewmat = np.eye(4, dtype=np.float32)
viewmat[:3, :3] = R_cw
viewmat[:3, 3] = t_cw
viewmat = torch.from_numpy(viewmat).to(device)

K = torch.tensor([
    [fx, 0.0, cx],
    [0.0, fy, cy],
    [0.0, 0.0, 1.0],
], dtype=torch.float32, device=device)

means = torch.nn.Parameter(torch.from_numpy(points_np).to(device))
scales = torch.nn.Parameter(torch.full((len(points_np), 3), math.log(0.03), dtype=torch.float32, device=device))
quats = torch.nn.Parameter(torch.tensor([[0.0, 0.0, 0.0, 1.0]], dtype=torch.float32, device=device).repeat(len(points_np), 1))
opacities = torch.nn.Parameter(torch.full((len(points_np),), 0.1, dtype=torch.float32, device=device))
colors = torch.nn.Parameter(torch.full((len(points_np), 3), 0.7, dtype=torch.float32, device=device))

summary_out.write_text(json.dumps({
    "point_count": int(len(points_np)),
    "target_frame": first_frame,
    "target_hw": [int(target_h), int(target_w)],
    "arcore_pose_path": str(arcore_pose_path),
}, indent=2, ensure_ascii=False), encoding="utf-8")

optimizer = torch.optim.Adam([means, scales, quats, opacities, colors], lr=1e-2)

def render_once():
    render_colors, render_alphas, meta = gsplat.rasterization(
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

optimizer.zero_grad(set_to_none=True)
pred0, alpha0 = render_once()
loss0 = torch.mean((pred0 - target) ** 2)
loss0.backward()
optimizer.step()

optimizer.zero_grad(set_to_none=True)
pred1, alpha1 = render_once()
loss1 = torch.mean((pred1 - target) ** 2)

result = {
    "backward_ok": True,
    "point_count": int(len(points_np)),
    "target_frame": first_frame,
    "loss_before": float(loss0.detach().cpu().item()),
    "loss_after": float(loss1.detach().cpu().item()),
    "alpha_mean_after": float(alpha1.mean().detach().cpu().item()),
    "summary_path": str(summary_out),
    "probe_path": str(probe_out),
}
probe_out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(result, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7i4 opacity-shape-fix res
gsplat: CUDA extension has been set up successfully in 807.06 seconds.
{
  "backward_ok": true,
  "point_count": 1024,
  "target_frame": "frame_000009.jpg",
  "loss_before": 0.18226878345012665,
  "loss_after": 0.15842102468013763,
  "alpha_mean_after": 0.7462685108184814,
  "summary_path": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/world_fusion_v01/gaussian_init_summary.json",
  "probe_path": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/world_fusion_v01/gaussian_one_step_probe.json"
}

```

# codex

2026-03-30 v42 step-7j gaussian-short-optim-and-save。

- 判定: `gaussian init + 1 step optim` は成功。
  - `backward_ok = true`
  - `point_count = 1024`
  - `loss_before = 0.18226878345012665`
  - `loss_after = 0.15842102468013763`
- 目的: 正規 gaussian parameter を file として保存し、短い optimization で loss が継続して下がるかを見る。
- この step で保存するもの:
  - `gaussian_params_init.pt`
  - `gaussian_params_optim20.pt`
  - `gaussian_render_init.png`
  - `gaussian_render_optim20.png`
  - `gaussian_optim20_summary.json`
- 成功条件:
  - 20 step 走る
  - `loss_history` を保存できる
  - `render_init` と `render_optim20` の 2 枚を保存できる

```python
# Step 7j gaussian-short-optim-and-save
from pathlib import Path
import json
import math
import numpy as np
import torch
import imageio.v3 as iio
import pandas as pd
from PIL import Image
import gsplat

probe_dir = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01")
world_dir = probe_dir / "world_fusion_v01"
window_path = probe_dir / "mrl7_window_probe.json"
session_root = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
session_outer = session_root.parent

out_init_pt = world_dir / "gaussian_params_init.pt"
out_optim_pt = world_dir / "gaussian_params_optim20.pt"
out_init_png = world_dir / "gaussian_render_init.png"
out_optim_png = world_dir / "gaussian_render_optim20.png"
out_summary = world_dir / "gaussian_optim20_summary.json"

window_info = json.loads(window_path.read_text(encoding="utf-8"))
sampled = (
    window_info.get("sampled_frames")
    or window_info.get("sample_frames")
    or window_info.get("sampled_images")
    or window_info.get("sampled")
    or window_info.get("sampled_frame_names")
)
assert sampled, "sampled list not found"

first_item = sampled[0]
if isinstance(first_item, dict):
    first_frame = (
        first_item.get("frame_name")
        or first_item.get("image_file_name")
        or first_item.get("name")
    )
else:
    first_frame = str(first_item)

arcore_pose_candidates = [
    session_root / "arcore_pose.jsonl",
    session_outer / "arcore_pose.jsonl",
]
arcore_pose_path = next((p for p in arcore_pose_candidates if p.exists()), None)
assert arcore_pose_path is not None, "arcore_pose.jsonl not found"

points_np = np.load(world_dir / "world_points_multiframe.npy").astype(np.float32)
max_points = 1024
if len(points_np) > max_points:
    pick = np.linspace(0, len(points_np) - 1, max_points).astype(np.int64)
    points_np = points_np[pick]

image = iio.imread(session_root / "images" / first_frame)
if image.ndim == 2:
    image = np.stack([image, image, image], axis=-1)
image = image[..., :3]
target_h, target_w = image.shape[:2]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
target = torch.from_numpy(image.astype(np.float32) / 255.0).to(device)

frame_pose_df = pd.read_csv(session_root / "frame_pose_index.csv")
row = frame_pose_df.loc[frame_pose_df["image_file_name"] == first_frame].iloc[0]
pose_index = int(row["pose_record_index"])

records = []
with arcore_pose_path.open("r", encoding="utf-8") as f:
    for line in f:
        records.append(json.loads(line))
pose_rec = records[pose_index]

intr = pose_rec["imageIntrinsics"]
pose = pose_rec["pose"]

fx = float(intr["fx"])
fy = float(intr["fy"])
cx = float(intr["cx"])
cy = float(intr["cy"])

tx = float(pose["tx"])
ty = float(pose["ty"])
tz = float(pose["tz"])
qx = float(pose["qx"])
qy = float(pose["qy"])
qz = float(pose["qz"])
qw = float(pose["qw"])

def quat_to_rot(qx, qy, qz, qw):
    xx, yy, zz = qx*qx, qy*qy, qz*qz
    xy, xz, yz = qx*qy, qx*qz, qy*qz
    wx, wy, wz = qw*qx, qw*qy, qw*qz
    return np.array([
        [1 - 2*(yy + zz), 2*(xy - wz), 2*(xz + wy)],
        [2*(xy + wz), 1 - 2*(xx + zz), 2*(yz - wx)],
        [2*(xz - wy), 2*(yz + wx), 1 - 2*(xx + yy)],
    ], dtype=np.float32)

R_wc = quat_to_rot(qx, qy, qz, qw)
t_wc = np.array([tx, ty, tz], dtype=np.float32)
R_cw = R_wc.T
t_cw = -R_cw @ t_wc

viewmat = np.eye(4, dtype=np.float32)
viewmat[:3, :3] = R_cw
viewmat[:3, 3] = t_cw
viewmat = torch.from_numpy(viewmat).to(device)

K = torch.tensor([
    [fx, 0.0, cx],
    [0.0, fy, cy],
    [0.0, 0.0, 1.0],
], dtype=torch.float32, device=device)

means = torch.nn.Parameter(torch.from_numpy(points_np).to(device))
scales = torch.nn.Parameter(torch.full((len(points_np), 3), math.log(0.03), dtype=torch.float32, device=device))
quats = torch.nn.Parameter(torch.tensor([[0.0, 0.0, 0.0, 1.0]], dtype=torch.float32, device=device).repeat(len(points_np), 1))
opacities = torch.nn.Parameter(torch.full((len(points_np),), 0.1, dtype=torch.float32, device=device))
colors = torch.nn.Parameter(torch.full((len(points_np), 3), 0.7, dtype=torch.float32, device=device))

optimizer = torch.optim.Adam([means, scales, quats, opacities, colors], lr=1e-2)

def render_once():
    render_colors, render_alphas, meta = gsplat.rasterization(
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

pred_init, alpha_init = render_once()
loss_init = torch.mean((pred_init - target) ** 2)
save_png(out_init_png, pred_init)

torch.save({
    "means": means.detach().cpu(),
    "scales_log": scales.detach().cpu(),
    "quats": torch.nn.functional.normalize(quats.detach(), dim=-1).cpu(),
    "opacities_logit": opacities.detach().cpu(),
    "colors": colors.detach().cpu(),
}, out_init_pt)

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
save_png(out_optim_png, pred_final)

torch.save({
    "means": means.detach().cpu(),
    "scales_log": scales.detach().cpu(),
    "quats": torch.nn.functional.normalize(quats.detach(), dim=-1).cpu(),
    "opacities_logit": opacities.detach().cpu(),
    "colors": colors.detach().cpu(),
}, out_optim_pt)

summary = {
    "backward_ok": True,
    "point_count": int(len(points_np)),
    "target_frame": first_frame,
    "loss_init": float(loss_init.detach().cpu().item()),
    "loss_final": float(loss_final.detach().cpu().item()),
    "loss_history_head": loss_history[:5],
    "loss_history_tail": loss_history[-5:],
    "alpha_mean_final": float(alpha_final.mean().detach().cpu().item()),
    "init_pt": str(out_init_pt),
    "optim20_pt": str(out_optim_pt),
    "init_png": str(out_init_png),
    "optim20_png": str(out_optim_png),
}
out_summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7j gaussian-short-optim-and-save res
{
  "backward_ok": true,
  "point_count": 1024,
  "target_frame": "frame_000009.jpg",
  "loss_init": 0.18226878345012665,
  "loss_final": 0.035895735025405884,
  "loss_history_head": [
    0.18226878345012665,
    0.18226878345012665,
    0.15842102468013763,
    0.1356389969587326,
    0.11426380276679993
  ],
  "loss_history_tail": [
    0.04233400151133537,
    0.040969572961330414,
    0.03969380632042885,
    0.038406822830438614,
    0.03710860386490822
  ],
  "alpha_mean_final": 0.6769227981567383,
  "init_pt": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/world_fusion_v01/gaussian_params_init.pt",
  "optim20_pt": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/world_fusion_v01/gaussian_params_optim20.pt",
  "init_png": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/world_fusion_v01/gaussian_render_init.png",
  "optim20_png": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/world_fusion_v01/gaussian_render_optim20.png"
}

improvement_visible: yes
shape_note: 取得背景に近い構図へ改善を確認
next_need: more steps / multiview extension / viewer export

```

# codex

2026-03-30 v43 step-7k gaussian-optim500-and-save。

- 判定: `20 step` 版は成功し、admin 目視でも改善が確認できた。
- 目的: 同じ route を `500 step` まで伸ばし、loss と見た目の改善幅を確認する。
- 保存するもの:
  - `gaussian_params_optim500.pt`
  - `gaussian_render_optim500.png`
  - `gaussian_optim500_summary.json`
- 成功条件:
  - `500 step` 完走
  - `loss_final` を返せる
  - `gaussian_render_optim500.png` を保存できる

```python
# Step 7k gaussian-optim500-and-save
from pathlib import Path
import json
import math
import numpy as np
import torch
import imageio.v3 as iio
import pandas as pd
from PIL import Image
import gsplat

probe_dir = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01")
world_dir = probe_dir / "world_fusion_v01"
window_path = probe_dir / "mrl7_window_probe.json"
session_root = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
session_outer = session_root.parent

out_optim_pt = world_dir / "gaussian_params_optim2500.pt"
out_optim_png = world_dir / "gaussian_render_optim2500.png"
out_summary = world_dir / "gaussian_optim2500_summary.json"

window_info = json.loads(window_path.read_text(encoding="utf-8"))
sampled = (
    window_info.get("sampled_frames")
    or window_info.get("sample_frames")
    or window_info.get("sampled_images")
    or window_info.get("sampled")
    or window_info.get("sampled_frame_names")
)
assert sampled, "sampled list not found"

first_item = sampled[0]
if isinstance(first_item, dict):
    first_frame = (
        first_item.get("frame_name")
        or first_item.get("image_file_name")
        or first_item.get("name")
    )
else:
    first_frame = str(first_item)

arcore_pose_candidates = [
    session_root / "arcore_pose.jsonl",
    session_outer / "arcore_pose.jsonl",
]
arcore_pose_path = next((p for p in arcore_pose_candidates if p.exists()), None)
assert arcore_pose_path is not None, "arcore_pose.jsonl not found"

points_np = np.load(world_dir / "world_points_multiframe.npy").astype(np.float32)
max_points = 1024
if len(points_np) > max_points:
    pick = np.linspace(0, len(points_np) - 1, max_points).astype(np.int64)
    points_np = points_np[pick]

image = iio.imread(session_root / "images" / first_frame)
if image.ndim == 2:
    image = np.stack([image, image, image], axis=-1)
image = image[..., :3]
target_h, target_w = image.shape[:2]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
target = torch.from_numpy(image.astype(np.float32) / 255.0).to(device)

frame_pose_df = pd.read_csv(session_root / "frame_pose_index.csv")
row = frame_pose_df.loc[frame_pose_df["image_file_name"] == first_frame].iloc[0]
pose_index = int(row["pose_record_index"])

records = []
with arcore_pose_path.open("r", encoding="utf-8") as f:
    for line in f:
        records.append(json.loads(line))
pose_rec = records[pose_index]

intr = pose_rec["imageIntrinsics"]
pose = pose_rec["pose"]

fx = float(intr["fx"])
fy = float(intr["fy"])
cx = float(intr["cx"])
cy = float(intr["cy"])

tx = float(pose["tx"])
ty = float(pose["ty"])
tz = float(pose["tz"])
qx = float(pose["qx"])
qy = float(pose["qy"])
qz = float(pose["qz"])
qw = float(pose["qw"])

def quat_to_rot(qx, qy, qz, qw):
    xx, yy, zz = qx*qx, qy*qy, qz*qz
    xy, xz, yz = qx*qy, qx*qz, qy*qz
    wx, wy, wz = qw*qx, qw*qy, qw*qz
    return np.array([
        [1 - 2*(yy + zz), 2*(xy - wz), 2*(xz + wy)],
        [2*(xy + wz), 1 - 2*(xx + zz), 2*(yz - wx)],
        [2*(xz - wy), 2*(yz + wx), 1 - 2*(xx + yy)],
    ], dtype=np.float32)

R_wc = quat_to_rot(qx, qy, qz, qw)
t_wc = np.array([tx, ty, tz], dtype=np.float32)
R_cw = R_wc.T
t_cw = -R_cw @ t_wc

viewmat = np.eye(4, dtype=np.float32)
viewmat[:3, :3] = R_cw
viewmat[:3, 3] = t_cw
viewmat = torch.from_numpy(viewmat).to(device)

K = torch.tensor([
    [fx, 0.0, cx],
    [0.0, fy, cy],
    [0.0, 0.0, 1.0],
], dtype=torch.float32, device=device)

means = torch.nn.Parameter(torch.from_numpy(points_np).to(device))
scales = torch.nn.Parameter(torch.full((len(points_np), 3), math.log(0.03), dtype=torch.float32, device=device))
quats = torch.nn.Parameter(torch.tensor([[0.0, 0.0, 0.0, 1.0]], dtype=torch.float32, device=device).repeat(len(points_np), 1))
opacities = torch.nn.Parameter(torch.full((len(points_np),), 0.1, dtype=torch.float32, device=device))
colors = torch.nn.Parameter(torch.full((len(points_np), 3), 0.7, dtype=torch.float32, device=device))

optimizer = torch.optim.Adam([means, scales, quats, opacities, colors], lr=1e-2)

def render_once():
    render_colors, render_alphas, meta = gsplat.rasterization(
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

pred_init, _ = render_once()
loss_init = torch.mean((pred_init - target) ** 2)

loss_history = [float(loss_init.detach().cpu().item())]
for _ in range(2500):
    optimizer.zero_grad(set_to_none=True)
    pred, alpha = render_once()
    loss = torch.mean((pred - target) ** 2)
    loss.backward()
    optimizer.step()
    loss_history.append(float(loss.detach().cpu().item()))

pred_final, alpha_final = render_once()
loss_final = torch.mean((pred_final - target) ** 2)
save_png(out_optim_png, pred_final)

torch.save({
    "means": means.detach().cpu(),
    "scales_log": scales.detach().cpu(),
    "quats": torch.nn.functional.normalize(quats.detach(), dim=-1).cpu(),
    "opacities_logit": opacities.detach().cpu(),
    "colors": colors.detach().cpu(),
}, out_optim_pt)

summary = {
    "backward_ok": True,
    "point_count": int(len(points_np)),
    "target_frame": first_frame,
    "loss_init": float(loss_init.detach().cpu().item()),
    "loss_final": float(loss_final.detach().cpu().item()),
    "loss_history_head": loss_history[:5],
    "loss_history_tail": loss_history[-5:],
    "alpha_mean_final": float(alpha_final.mean().detach().cpu().item()),
    "optim2500_pt": str(out_optim_pt),
    "optim2500_png": str(out_optim_png),
}
out_summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7k gaussian-optim500-and-save res


from pathlib import Path
from google.colab import files
import shutil

world_dir = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_multiframe_probe_v01/world_fusion_v01")
bundle_dir = Path("/content/gaussian_optim2500_bundle")
bundle_zip = Path("/content/gaussian_optim2500_bundle.zip")

if bundle_dir.exists():
    shutil.rmtree(bundle_dir)
bundle_dir.mkdir(parents=True, exist_ok=True)

targets = [
    "gaussian_params_optim2500.pt",
    "gaussian_render_optim2500.png",
    "gaussian_optim2500_summary.json",
]

for name in targets:
    src = world_dir / name
    assert src.exists(), f"missing: {src}"
    shutil.copy2(src, bundle_dir / name)

if bundle_zip.exists():
    bundle_zip.unlink()

shutil.make_archive(str(bundle_zip.with_suffix("")), "zip", root_dir=str(bundle_dir))
print(bundle_zip)
files.download(str(bundle_zip))




```

# codex v44

`MRL-8` の first block として、runbook 本体へ入る前に Drive 上の input 候補を列挙し、selected input を固定する。fresh runtime では `drive.mount('/content/drive')` の後に実行する。

```python
# Step 8a drive input candidate scan and select
from pathlib import Path
import json

shortcut_root = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_")
scan_roots = [
    shortcut_root / "trajectreview",
    Path("/content/drive/MyDrive/trajectreview"),
]
results_root_candidates = [
    shortcut_root / "trajectreview" / "results",
    Path("/content/drive/MyDrive/trajectreview/results"),
]
results_root = next((p for p in results_root_candidates if p.exists()), results_root_candidates[0])
candidate_doc_path = Path("/content/runbook_drive_candidates.json")
selected_doc_path = Path("/content/runbook_selected_input.json")

def infer_session_id(path: Path) -> str:
    return path.stem if path.suffix.lower() == ".zip" else path.name

candidates = []
seen = set()
for root in scan_roots:
    if not root.exists():
        continue
    for zip_path in sorted(root.rglob("*.zip")):
        key = ("zip", str(zip_path))
        if key in seen:
            continue
        seen.add(key)
        candidates.append({
            "kind": "zip",
            "session_id": infer_session_id(zip_path),
            "label": f"{infer_session_id(zip_path)} [zip]",
            "path": str(zip_path),
        })
    for pkg_path in sorted(root.rglob("session_package.json")):
        session_root = pkg_path.parent
        key = ("dir", str(session_root))
        if key in seen:
            continue
        seen.add(key)
        candidates.append({
            "kind": "dir",
            "session_id": infer_session_id(session_root),
            "label": f"{infer_session_id(session_root)} [dir]",
            "path": str(session_root),
        })

candidate_doc = {
    "scan_roots": [str(p) for p in scan_roots if p.exists()],
    "results_root": str(results_root),
    "candidate_count": len(candidates),
    "candidates": candidates,
}
candidate_doc_path.write_text(json.dumps(candidate_doc, indent=2, ensure_ascii=False), encoding="utf-8")

print("candidate_doc_path", candidate_doc_path)
print("results_root", results_root)
print("candidate_count", len(candidates))
for idx, item in enumerate(candidates):
    print(f"[{idx}] {item['label']}: {item['path']}")

assert candidates, "no input candidates found"

SELECTED_INDEX = 0
selected = candidates[SELECTED_INDEX]
selected_doc = {
    "selected_index": SELECTED_INDEX,
    "kind": selected["kind"],
    "session_id": selected["session_id"],
    "label": selected["label"],
    "path": selected["path"],
    "results_root": str(results_root),
}
selected_doc_path.write_text(json.dumps(selected_doc, indent=2, ensure_ascii=False), encoding="utf-8")

print("selected_doc_path", selected_doc_path)
print(json.dumps(selected_doc, indent=2, ensure_ascii=False))
print("selected_exists", Path(selected["path"]).exists())
```

# admin

```text
# Step 8a drive input candidate scan and select res
candidate_doc_path /content/runbook_drive_candidates.json
results_root /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results
candidate_count 0
---------------------------------------------------------------------------
AssertionError                            Traceback (most recent call last)
/tmp/ipykernel_7424/229012291.py in <cell line: 0>()
     62     print(f"[{idx}] {item['label']}: {item['path']}")
     63 
---> 64 assert candidates, "no input candidates found"
     65 
     66 SELECTED_INDEX = 0

AssertionError: no input candidates found
```

# codex v45

blank runtime では `Drive` 再接続が必要なので、先に remount と scan root 実在確認を行う。`scan_root_exists` が全部 `False` なら mount 問題、`scan_root_exists` があるのに `candidate_count 0` なら Drive 配下に対象 data が無い。

```python
# Step 8a1 drive remount and scan-root diagnostic
from pathlib import Path
import json
from google.colab import drive

drive.mount("/content/drive", force_remount=True)

shortcut_root = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_")
scan_roots = [
    shortcut_root / "trajectreview",
    Path("/content/drive/MyDrive/trajectreview"),
]
results_root_candidates = [
    shortcut_root / "trajectreview" / "results",
    Path("/content/drive/MyDrive/trajectreview/results"),
]
results_root = next((p for p in results_root_candidates if p.exists()), results_root_candidates[0])

diag = {
    "shortcut_root_exists": shortcut_root.exists(),
    "scan_root_exists": {str(p): p.exists() for p in scan_roots},
    "results_root_exists": results_root.exists(),
    "results_root": str(results_root),
}
print(json.dumps(diag, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 8a1 drive remount and scan-root diagnostic res
candidate_doc_path /content/runbook_drive_candidates.json
results_root /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results
candidate_count 6
[0] session-20260328-103250 [zip]: /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/session-20260328-103250.zip
[1] trajectreview-correcting-export [zip]: /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/trajectreview-correcting-export.zip
[2] trajectreview-correcting-session-20260331-034831 [zip]: /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/trajectreview-correcting-session-20260331-034831.zip
[3] session-20260328-103250 [zip]: /content/drive/MyDrive/trajectreview/correcting/session-20260328-103250.zip
[4] trajectreview-correcting-export [zip]: /content/drive/MyDrive/trajectreview/correcting/trajectreview-correcting-export.zip
[5] trajectreview-correcting-session-20260331-034831 [zip]: /content/drive/MyDrive/trajectreview/correcting/trajectreview-correcting-session-20260331-034831.zip
selected_doc_path /content/runbook_selected_input.json
{
  "selected_index": 0,
  "kind": "zip",
  "session_id": "session-20260328-103250",
  "label": "session-20260328-103250 [zip]",
  "path": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/session-20260328-103250.zip",
  "results_root": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results"
}
selected_exists True
```

# codex v46

`MRL-8.2` へ進む。selected input は固定できたので、次はその selected input を `Step 1` と同じ logic で展開し、`session_root`、`images/`、`runbook_session_context.json` まで生成する。

```python
# Step 8b selected-input extract and context build
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
    dest_root = extract_root / selected_path.name
    shutil.copytree(selected_path, dest_root)

pkg_hits = sorted(extract_root.rglob("session_package.json"))
assert pkg_hits, f"session_package.json not found under {extract_root}"
session_pkg = next((p for p in pkg_hits if p.parent.name == "trajectreview"), pkg_hits[0])

session_root = session_pkg.parent
session_outer = session_root.parent
images_dir = session_root / "images"
files = sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.jpeg"))

smoke_output_root = results_root / f"{session_id}_da3_smoke_v24"
multiframe_probe_root = results_root / f"{session_id}_da3_multiframe_probe_v01"
context = {
    "selected_path": str(selected_path),
    "selected_kind": selected_kind,
    "session_id": session_id,
    "session_root": str(session_root),
    "session_outer": str(session_outer),
    "images_dir": str(images_dir),
    "results_root": str(results_root),
    "da3_smoke_output_root": str(smoke_output_root),
    "multiframe_probe_root": str(multiframe_probe_root),
}
Path("/content/runbook_session_context.json").write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")

result = {
    "selected_kind": selected_kind,
    "selected_path": str(selected_path),
    "session_root_exists": session_root.exists(),
    "session_root": str(session_root),
    "images_dir_exists": images_dir.exists(),
    "images_dir": str(images_dir),
    "image_count": len(files),
    "first_image": None if not files else str(files[0]),
    "context_path": "/content/runbook_session_context.json",
}
print(json.dumps(result, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 8b selected-input extract and context build res
{
  "selected_kind": "zip",
  "selected_path": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/session-20260328-103250.zip",
  "session_root_exists": true,
  "session_root": "/content/trajectreview_input/session-20260328-103250/trajectreview",
  "images_dir_exists": true,
  "images_dir": "/content/trajectreview_input/session-20260328-103250/trajectreview/images",
  "image_count": 182,
  "first_image": "/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000009.jpg",
  "context_path": "/content/runbook_session_context.json"
}
```

# codex v47

`MRL-8` の接続確認として、selected input をそのまま使って `Step 2` から `Step 4.5` を一気に流す。ここが通れば、runbook 前段の Drive input select と本体 bootstrap は接続済みと判断できる。

```python
# Step 8c selected-input startup-to-step4p5
import sys
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
import torch

context = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
SESSION_ROOT = Path(context["session_root"])
OUTPUT_ROOT = Path(context["da3_smoke_output_root"])
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

def run(cmd):
    print("RUN", " ".join(cmd))
    subprocess.run(cmd, check=True)

repo_root = Path("/content/Depth-Anything-3")
if repo_root.exists():
    shutil.rmtree(repo_root)

run(["git", "clone", "https://github.com/ByteDance-Seed/Depth-Anything-3.git", str(repo_root)])
run(["python", "-m", "pip", "install", "--quiet", "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile", "trimesh", "gsplat"])

src_root = repo_root / "src"
assert src_root.exists(), f"src not found: {src_root}"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from depth_anything_3.api import DepthAnything3
import gsplat

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
    "selected_path": context["selected_path"],
    "session_root": str(SESSION_ROOT),
    "image_path": str(image_path),
    "device": str(device),
    "depth_shape": list(depth.shape),
    "conf_shape": None if conf is None else list(conf.shape),
    "intrinsics_shape": None if intrinsics is None else list(intrinsics.shape),
    "extrinsics_shape": None if extrinsics is None else list(extrinsics.shape),
    "depth_min": depth_min,
    "depth_max": depth_max,
    "output_root": str(OUTPUT_ROOT),
    "gsplat_version": getattr(gsplat, "__version__", "unknown"),
    "rasterization_type": type(gsplat.rasterization).__name__,
}
(OUTPUT_ROOT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 8c selected-input startup-to-step4p5 res
RUN git clone https://github.com/ByteDance-Seed/Depth-Anything-3.git /content/Depth-Anything-3
RUN python -m pip install --quiet addict evo moviepy==1.0.3 pygame pycolmap plyfile trimesh gsplat
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

WARNING:py.warnings:/usr/local/lib/python3.12/dist-packages/huggingface_hub/utils/_auth.py:94: UserWarning: 
The secret `HF_TOKEN` does not exist in your Colab secrets.
To authenticate with the Hugging Face Hub, create a token in your settings tab (https://huggingface.co/settings/tokens), set it as secret in your Google Colab and restart your session.
You will be able to reuse this secret in all of your notebooks.
Please note that authentication is recommended but still optional to access public models or datasets.
  warnings.warn(

config.json: 100%
 847/847 [00:00<00:00, 49.3kB/s]
[INFO ] using MLP layer as FFN
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
WARNING:huggingface_hub.utils._http:Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
model.safetensors: 100%
 1.34G/1.34G [00:09<00:00, 118MB/s]
[INFO ] Processed Images Done taking 0.09908866882324219 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 1.7259190082550049 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0018324851989746094 seconds
{
  "selected_path": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/session-20260328-103250.zip",
  "session_root": "/content/trajectreview_input/session-20260328-103250/trajectreview",
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
  "depth_max": 4.0310516357421875,
  "output_root": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/session-20260328-103250_da3_smoke_v24",
  "gsplat_version": "1.5.3",
  "rasterization_type": "function"
}
```

# codex v48

現在の `Step 8a` は `SELECTED_INDEX = 0` 固定で、admin が画面で選べる状態ではなかった。ここを widget 選択へ差し替える。dropdown で候補を選び、button を押した時だけ `/content/runbook_selected_input.json` を保存する。

```python
# Step 8a2 widget-based input selection
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

# admin

```text
# Step 8a2 widget-based input selection res
skip
```

# codex v49

直前の `Step 8c` は成功しており、Drive input select 後の bootstrap 本体接続は通っている。未確認なのは「admin が widget で選んだ input が、そのまま extract / context build / startup-to-step4p5 へ流れるか」だけなので、ここを 1 block で確認する。

```python
# Step 8d widget-select to startup-to-step4p5
from pathlib import Path
import json
import shutil
import subprocess
import sys
import zipfile

import ipywidgets as widgets
from IPython.display import display
import numpy as np
from PIL import Image
import torch

candidate_doc_path = Path("/content/runbook_drive_candidates.json")
selected_doc_path = Path("/content/runbook_selected_input.json")
context_doc_path = Path("/content/runbook_session_context.json")
extract_root = Path("/content/trajectreview_input")

candidate_doc = json.loads(candidate_doc_path.read_text(encoding="utf-8"))
assert candidate_doc["candidate_count"] >= 1, candidate_doc

options = [(f"[{idx}] {item['label']}", idx) for idx, item in enumerate(candidate_doc["candidates"])]
dropdown = widgets.Dropdown(options=options, description="input", layout=widgets.Layout(width="95%"))
button = widgets.Button(description="選択して Step 8d を実行", button_style="success")
output = widgets.Output()
display(dropdown, button, output)
print("操作: dropdown で 1 件選び、`選択して Step 8d を実行` を押す")

def run(cmd):
    print("RUN", " ".join(cmd))
    subprocess.run(cmd, check=True)

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

    selected_path = Path(selected_doc["path"])
    selected_kind = selected_doc["kind"]
    session_id = selected_doc["session_id"]
    results_root = Path(selected_doc["results_root"])

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
    files = sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.jpeg"))

    smoke_output_root = results_root / f"{session_id}_da3_smoke_v24"
    context = {
        "selected_path": str(selected_path),
        "selected_kind": selected_kind,
        "session_id": session_id,
        "session_root": str(session_root),
        "session_outer": str(session_outer),
        "images_dir": str(images_dir),
        "results_root": str(results_root),
        "da3_smoke_output_root": str(smoke_output_root),
    }
    context_doc_path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")

    repo_root = Path("/content/Depth-Anything-3")
    if repo_root.exists():
        shutil.rmtree(repo_root)

    run(["git", "clone", "https://github.com/ByteDance-Seed/Depth-Anything-3.git", str(repo_root)])
    run(["python", "-m", "pip", "install", "--quiet", "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile", "trimesh", "gsplat"])

    src_root = repo_root / "src"
    assert src_root.exists(), f"src not found: {src_root}"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

    from depth_anything_3.api import DepthAnything3
    import gsplat

    smoke_output_root.mkdir(parents=True, exist_ok=True)
    image_path = files[0]

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
    Image.fromarray((depth_norm * 255).astype(np.uint8)).save(smoke_output_root / "depth_preview.png")
    np.save(smoke_output_root / "depth_raw.npy", depth)
    if conf is not None:
        np.save(smoke_output_root / "conf_raw.npy", conf)
    if intrinsics is not None:
        np.save(smoke_output_root / "intrinsics.npy", intrinsics)
    if extrinsics is not None:
        np.save(smoke_output_root / "extrinsics.npy", extrinsics)

    result = {
        "selected_index": selected_index,
        "selected_path": str(selected_path),
        "selected_exists": selected_path.exists(),
        "session_root": str(session_root),
        "image_count": len(files),
        "first_image": str(image_path),
        "device": str(device),
        "depth_shape": list(depth.shape),
        "depth_min": depth_min,
        "depth_max": depth_max,
        "output_root": str(smoke_output_root),
        "gsplat_version": getattr(gsplat, "__version__", "unknown"),
        "rasterization_type": type(gsplat.rasterization).__name__,
    }

    with output:
        output.clear_output()
        print(json.dumps(result, indent=2, ensure_ascii=False))

button.on_click(on_click)
```

# admin

```text
# Step 8d widget-select to startup-to-step4p5 res
skip
```

# codex v50

dropdown に同じ `zip` が 2 回出るのは正常ではない。`shortcut-targets-by-id` と `MyDrive` が同じ実体を別 path 文字列として返していた。candidate scan を `resolve()` ベースで dedupe し、widget 候補を再生成する。

```python
# Step 8a3 deduped candidate rescan
from pathlib import Path
import json

shortcut_root = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_")
scan_roots = [
    shortcut_root / "trajectreview",
    Path("/content/drive/MyDrive/trajectreview"),
]
results_root_candidates = [
    shortcut_root / "trajectreview" / "results",
    Path("/content/drive/MyDrive/trajectreview/results"),
]
results_root = next((p for p in results_root_candidates if p.exists()), results_root_candidates[0])
candidate_doc_path = Path("/content/runbook_drive_candidates.json")

def infer_session_id(path: Path) -> str:
    return path.stem if path.suffix.lower() == ".zip" else path.name

candidates = []
seen = set()
for root in scan_roots:
    if not root.exists():
        continue
    for zip_path in sorted(root.rglob("*.zip")):
        real_zip = zip_path.resolve()
        key = ("zip", str(real_zip))
        if key in seen:
            continue
        seen.add(key)
        candidates.append({
            "kind": "zip",
            "session_id": infer_session_id(zip_path),
            "label": f"{infer_session_id(zip_path)} [zip]",
            "path": str(real_zip),
        })
    for pkg_path in sorted(root.rglob("session_package.json")):
        session_root = pkg_path.parent
        real_session_root = session_root.resolve()
        key = ("dir", str(real_session_root))
        if key in seen:
            continue
        seen.add(key)
        candidates.append({
            "kind": "dir",
            "session_id": infer_session_id(session_root),
            "label": f"{infer_session_id(session_root)} [dir]",
            "path": str(real_session_root),
        })

candidate_doc = {
    "scan_roots": [str(p) for p in scan_roots if p.exists()],
    "scan_root_exists": {str(p): p.exists() for p in scan_roots},
    "results_root": str(results_root),
    "candidate_count": len(candidates),
    "candidates": candidates,
}
candidate_doc_path.write_text(json.dumps(candidate_doc, indent=2, ensure_ascii=False), encoding="utf-8")

print("candidate_doc_path", candidate_doc_path)
print("candidate_count", len(candidates))
for idx, item in enumerate(candidates):
    print(f"[{idx}] {item['label']}: {item['path']}")
```

# admin

```text
# Step 8a3 deduped candidate rescan res
candidate_doc_path /content/runbook_drive_candidates.json
candidate_count 6
[0] session-20260328-103250 [zip]: /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/session-20260328-103250.zip
[1] trajectreview-correcting-export [zip]: /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/trajectreview-correcting-export.zip
[2] trajectreview-correcting-session-20260331-034831 [zip]: /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/trajectreview-correcting-session-20260331-034831.zip
[3] session-20260328-103250 [zip]: /content/drive/MyDrive/trajectreview/correcting/session-20260328-103250.zip
[4] trajectreview-correcting-export [zip]: /content/drive/MyDrive/trajectreview/correcting/trajectreview-correcting-export.zip
[5] trajectreview-correcting-session-20260331-034831 [zip]: /content/drive/MyDrive/trajectreview/correcting/trajectreview-correcting-session-20260331-034831.zip

```

# codex v51

`resolve()` でも `shortcut-targets-by-id` と `MyDrive` が別 path のまま残るので、mount 実装上は同一実体と判定できなかった。次は `session_id + size_bytes` を同一 zip の key とみなし、同じ key が複数 root にある時は `shortcut-targets-by-id` 側を優先して 1 件だけ残す。

```python
# Step 8a4 canonical candidate rescan
from pathlib import Path
import json

shortcut_root = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_")
scan_roots = [
    shortcut_root / "trajectreview",
    Path("/content/drive/MyDrive/trajectreview"),
]
results_root_candidates = [
    shortcut_root / "trajectreview" / "results",
    Path("/content/drive/MyDrive/trajectreview/results"),
]
results_root = next((p for p in results_root_candidates if p.exists()), results_root_candidates[0])
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
print("candidate_count", len(candidates))
for idx, item in enumerate(candidates):
    extra = f" size={item['size_bytes']}" if "size_bytes" in item else ""
    print(f"[{idx}] {item['label']}: {item['path']}{extra}")
```

# admin

```text
# Step 8a4 canonical candidate rescan res
candidate_doc_path /content/runbook_drive_candidates.json
candidate_count 3
[0] session-20260328-103250 [zip]: /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/session-20260328-103250.zip size=19941917
[1] trajectreview-correcting-export [zip]: /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/trajectreview-correcting-export.zip size=45758075
[2] trajectreview-correcting-session-20260331-034831 [zip]: /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/trajectreview-correcting-session-20260331-034831.zip size=11822606

```

# codex v52

candidate の重複は解消した。次はこの 3 件だけを対象に、admin が widget で 1 件選び、その選択結果を使って `Step 2` から `Step 4.5` まで通す。`v49` と同じ目的だが、前提となる candidate list は `v51` の canonical rescan 後の 3 件版を使う。

```python
# Step 8d retry after canonical candidate rescan
from pathlib import Path
import json
import shutil
import subprocess
import sys
import zipfile

import ipywidgets as widgets
from IPython.display import display
import numpy as np
from PIL import Image
import torch

candidate_doc_path = Path("/content/runbook_drive_candidates.json")
selected_doc_path = Path("/content/runbook_selected_input.json")
context_doc_path = Path("/content/runbook_session_context.json")
extract_root = Path("/content/trajectreview_input")

candidate_doc = json.loads(candidate_doc_path.read_text(encoding="utf-8"))
assert candidate_doc["candidate_count"] >= 1, candidate_doc

options = [(f"[{idx}] {item['label']}", idx) for idx, item in enumerate(candidate_doc["candidates"])]
dropdown = widgets.Dropdown(options=options, description="input", layout=widgets.Layout(width="95%"))
button = widgets.Button(description="選択して Step 8d を実行", button_style="success")
output = widgets.Output()
display(dropdown, button, output)
print("操作: dropdown で 1 件選び、`選択して Step 8d を実行` を押す")

def run(cmd):
    print("RUN", " ".join(cmd))
    subprocess.run(cmd, check=True)

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

    selected_path = Path(selected_doc["path"])
    selected_kind = selected_doc["kind"]
    session_id = selected_doc["session_id"]
    results_root = Path(selected_doc["results_root"])

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
    files = sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.jpeg"))

    smoke_output_root = results_root / f"{session_id}_da3_smoke_v24"
    context = {
        "selected_path": str(selected_path),
        "selected_kind": selected_kind,
        "session_id": session_id,
        "session_root": str(session_root),
        "session_outer": str(session_outer),
        "images_dir": str(images_dir),
        "results_root": str(results_root),
        "da3_smoke_output_root": str(smoke_output_root),
    }
    context_doc_path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")

    repo_root = Path("/content/Depth-Anything-3")
    if repo_root.exists():
        shutil.rmtree(repo_root)

    run(["git", "clone", "https://github.com/ByteDance-Seed/Depth-Anything-3.git", str(repo_root)])
    run(["python", "-m", "pip", "install", "--quiet", "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile", "trimesh", "gsplat"])

    src_root = repo_root / "src"
    assert src_root.exists(), f"src not found: {src_root}"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

    from depth_anything_3.api import DepthAnything3
    import gsplat

    smoke_output_root.mkdir(parents=True, exist_ok=True)
    assert files, f"images not found under {images_dir}"
    image_path = files[0]

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
    Image.fromarray((depth_norm * 255).astype(np.uint8)).save(smoke_output_root / "depth_preview.png")
    np.save(smoke_output_root / "depth_raw.npy", depth)
    if conf is not None:
        np.save(smoke_output_root / "conf_raw.npy", conf)
    if intrinsics is not None:
        np.save(smoke_output_root / "intrinsics.npy", intrinsics)
    if extrinsics is not None:
        np.save(smoke_output_root / "extrinsics.npy", extrinsics)

    result = {
        "selected_index": selected_index,
        "selected_path": str(selected_path),
        "selected_exists": selected_path.exists(),
        "session_root": str(session_root),
        "image_count": len(files),
        "first_image": str(image_path),
        "device": str(device),
        "depth_shape": list(depth.shape),
        "depth_min": depth_min,
        "depth_max": depth_max,
        "output_root": str(smoke_output_root),
        "gsplat_version": getattr(gsplat, "__version__", "unknown"),
        "rasterization_type": type(gsplat.rasterization).__name__,
    }

    with output:
        output.clear_output()
        print(json.dumps(result, indent=2, ensure_ascii=False))

button.on_click(on_click)
```

# admin

```text
# Step 8d retry after canonical candidate rescan res
input

[2] trajectreview-correcting-session-20260331-034831 [zip]
{
  "selected_index": 2,
  "selected_path": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/trajectreview-correcting-session-20260331-034831.zip",
  "selected_exists": true,
  "session_root": "/content/trajectreview_input/session-20260331-034831/trajectreview",
  "image_count": 26,
  "first_image": "/content/trajectreview_input/session-20260331-034831/trajectreview/images/frame_000052.jpg",
  "device": "cuda",
  "depth_shape": [
    378,
    504
  ],
  "depth_min": 0.8689900040626526,
  "depth_max": 2.0749411582946777,
  "output_root": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/trajectreview-correcting-session-20260331-034831_da3_smoke_v24",
  "gsplat_version": "1.5.3",
  "rasterization_type": "function"
}
操作: dropdown で 1 件選び、`選択して Step 8d を実行` を押す
RUN git clone https://github.com/ByteDance-Seed/Depth-Anything-3.git /content/Depth-Anything-3
RUN python -m pip install --quiet addict evo moviepy==1.0.3 pygame pycolmap plyfile trimesh gsplat
[INFO ] using MLP layer as FFN
[INFO ] Processed Images Done taking 0.01624274253845215 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.44126439094543457 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0010578632354736328 seconds
```

# codex v53

`Step 8d` は成功で、admin が widget で選んだ session が `Step 2` から `Step 4.5` まで接続された。次は同じ selected input を使って、runbook の `MRL-7 adopted one-block` が hardcoded session ではなく選択済み session に対して end-to-end で通るかを確認する。

```python
# Step 8e selected-input mrl7 adopted one-block
from pathlib import Path
import json
import math
import shutil
import subprocess
import sys
import zipfile

import imageio.v3 as iio
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
import torch

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
probe_dir.mkdir(parents=True, exist_ok=True)
world_dir.mkdir(parents=True, exist_ok=True)

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
frame_pose_csv = session_root / "frame_pose_index.csv"
assert frame_pose_csv.exists(), frame_pose_csv

repo_root = Path("/content/Depth-Anything-3")
if repo_root.exists():
    shutil.rmtree(repo_root)

def run(cmd):
    print("RUN", " ".join(cmd))
    subprocess.run(cmd, check=True)

run(["git", "clone", "https://github.com/ByteDance-Seed/Depth-Anything-3.git", str(repo_root)])
run(["python", "-m", "pip", "install", "--quiet", "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile", "trimesh", "gsplat"])

src_root = repo_root / "src"
assert src_root.exists(), f"src not found: {src_root}"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from depth_anything_3.api import DepthAnything3

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = DepthAnything3.from_pretrained("depth-anything/DA3METRIC-LARGE").to(device=device)

df = pd.read_csv(frame_pose_csv)
time_candidates = ["frame_timestamp_ns", "capture_timestamp_ns", "timestamp_ns", "captureTimestampNs"]
time_col = next((c for c in time_candidates if c in df.columns), None)
assert time_col is not None, {"columns": list(df.columns)}

image_files = sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpeg"))
assert image_files, images_dir
frame_names = [p.name for p in image_files]
df = df.iloc[: len(frame_names)].copy()
df["frame_name"] = frame_names[: len(df)]
df = df.sort_values(time_col).reset_index(drop=True)
df["delta_s"] = df[time_col].diff().fillna(0) / 1e9

segments = []
start = 0
for i in range(1, len(df)):
    if float(df.loc[i, "delta_s"]) > 0.5:
        segments.append((start, i - 1))
        start = i
segments.append((start, len(df) - 1))
best_seg = max(segments, key=lambda x: x[1] - x[0])
seg_df = df.iloc[best_seg[0] : best_seg[1] + 1].reset_index(drop=True)

sample_count = min(12, len(seg_df))
sample_indices = np.linspace(0, len(seg_df) - 1, num=sample_count, dtype=int)
sample_df = seg_df.iloc[sample_indices].reset_index(drop=True)
sample_frames = sample_df["frame_name"].tolist()

window_doc = {
    "session_id": session_id,
    "time_col": time_col,
    "aligned_frame_count": int(len(df)),
    "segment_start_index": int(best_seg[0]),
    "segment_end_index": int(best_seg[1]),
    "segment_duration_s": float((seg_df[time_col].iloc[-1] - seg_df[time_col].iloc[0]) / 1e9) if len(seg_df) >= 2 else 0.0,
    "sample_frames": sample_frames,
}
(probe_dir / "mrl7_window_probe.json").write_text(json.dumps(window_doc, indent=2, ensure_ascii=False), encoding="utf-8")

depth_rows = []
depth_dir = probe_dir / "depth_batch_v01"
depth_dir.mkdir(parents=True, exist_ok=True)

for frame_name in sample_frames:
    image_path = images_dir / frame_name
    pred = model.inference([str(image_path)])
    depth = np.asarray(pred.depth[0]).astype(np.float32)
    depth_path = depth_dir / f"{Path(frame_name).stem}_depth.npy"
    preview_path = depth_dir / f"{Path(frame_name).stem}_depth.png"
    np.save(depth_path, depth)
    dmin = float(depth.min())
    dmax = float(depth.max())
    dnorm = np.zeros_like(depth, dtype=np.float32) if dmax <= dmin else (depth - depth_min) / (dmax - dmin)
    Image.fromarray((dnorm * 255).astype(np.uint8)).save(preview_path)
    depth_rows.append({
        "frame_name": frame_name,
        "image_path": str(image_path),
        "depth_path": str(depth_path),
        "depth_preview_path": str(preview_path),
        "depth_shape": list(depth.shape),
        "depth_min": dmin,
        "depth_max": dmax,
    })

depth_manifest = {
    "session_id": session_id,
    "processed_frames": len(depth_rows),
    "failed_frames": 0,
    "rows": depth_rows,
}
(probe_dir / "depth_batch_manifest.json").write_text(json.dumps(depth_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

arcore_pose_candidates = [
    session_root / "arcore_pose.jsonl",
    session_outer / "arcore_pose.jsonl",
]
arcore_pose_path = next((p for p in arcore_pose_candidates if p.exists()), None)
assert arcore_pose_path is not None, {"arcore_pose_candidates": [str(p) for p in arcore_pose_candidates]}

with arcore_pose_path.open("r", encoding="utf-8") as f:
    pose_rows = [json.loads(line) for line in f if line.strip()]

def quat_to_rot(qx, qy, qz, qw):
    xx, yy, zz = qx * qx, qy * qy, qz * qz
    xy, xz, yz = qx * qy, qx * qz, qy * qz
    wx, wy, wz = qw * qx, qw * qy, qw * qz
    return np.array([
        [1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy)],
        [2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx)],
        [2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy)],
    ], dtype=np.float32)

world_points = []
processed = 0
skipped = 0

for row in depth_rows:
    frame_name = row["frame_name"]
    match = sample_df[sample_df["frame_name"] == frame_name]
    if match.empty or "pose_record_index" not in match.columns:
        skipped += 1
        continue
    pose_idx = int(match.iloc[0]["pose_record_index"])
    if pose_idx < 0 or pose_idx >= len(pose_rows):
        skipped += 1
        continue
    pose_rec = pose_rows[pose_idx]
    pose = pose_rec.get("pose", {})
    intr = pose_rec.get("imageIntrinsics", {})
    if not pose or not intr:
        skipped += 1
        continue

    depth = np.load(row["depth_path"]).astype(np.float32)
    h, w = depth.shape
    fx = float(intr["fx"])
    fy = float(intr["fy"])
    cx = float(intr["cx"])
    cy = float(intr["cy"])

    ys = np.linspace(0, h - 1, num=min(16, h), dtype=int)
    xs = np.linspace(0, w - 1, num=min(24, w), dtype=int)
    xv, yv = np.meshgrid(xs, ys)
    zv = depth[yv, xv]
    valid = np.isfinite(zv) & (zv > 0)
    if not np.any(valid):
        skipped += 1
        continue

    xv = xv[valid].astype(np.float32)
    yv = yv[valid].astype(np.float32)
    zv = zv[valid].astype(np.float32)

    x_cam = (xv - cx) * zv / fx
    y_cam = (yv - cy) * zv / fy
    cam_pts = np.stack([x_cam, y_cam, zv], axis=1)

    tx = float(pose["tx"])
    ty = float(pose["ty"])
    tz = float(pose["tz"])
    qx = float(pose["qx"])
    qy = float(pose["qy"])
    qz = float(pose["qz"])
    qw = float(pose["qw"])
    rot = quat_to_rot(qx, qy, qz, qw)
    trans = np.array([tx, ty, tz], dtype=np.float32)
    world = (rot @ cam_pts.T).T + trans
    world_points.append(world)
    processed += 1

assert world_points, "no world points generated"
points_np = np.concatenate(world_points, axis=0).astype(np.float32)
np.save(world_dir / "world_points_multiframe.npy", points_np)

with (world_dir / "world_points_multiframe.ply").open("w", encoding="utf-8") as f:
    f.write("ply\n")
    f.write("format ascii 1.0\n")
    f.write(f"element vertex {points_np.shape[0]}\n")
    f.write("property float x\n")
    f.write("property float y\n")
    f.write("property float z\n")
    f.write("end_header\n")
    for x, y, z in points_np:
        f.write(f"{x} {y} {z}\n")

sample = points_np
if len(sample) > 5000:
    idx = np.linspace(0, len(sample) - 1, num=5000, dtype=int)
    sample = sample[idx]
fig = plt.figure(figsize=(6, 6))
ax = fig.add_subplot(111, projection="3d")
ax.scatter(sample[:, 0], sample[:, 1], sample[:, 2], s=1, alpha=0.6)
ax.set_title("MRL-7 multiframe world points preview")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_zlabel("z")
plt.tight_layout()
plt.savefig(world_dir / "world_points_multiframe_preview.png", dpi=180)
plt.close(fig)

world_summary = {
    "session_id": session_id,
    "processed_frames": processed,
    "skipped_frames": skipped,
    "total_points": int(points_np.shape[0]),
    "world_points_npy": str(world_dir / "world_points_multiframe.npy"),
    "world_points_ply": str(world_dir / "world_points_multiframe.ply"),
    "preview_path": str(world_dir / "world_points_multiframe_preview.png"),
}
(world_dir / "world_fusion_summary.json").write_text(json.dumps(world_summary, indent=2, ensure_ascii=False), encoding="utf-8")

closeout = {
    "status": "candidate-visible-proof",
    "processed_frames": processed,
    "skipped_frames": skipped,
    "total_points": int(points_np.shape[0]),
    "window_probe_path": str(probe_dir / "mrl7_window_probe.json"),
    "depth_manifest_path": str(probe_dir / "depth_batch_manifest.json"),
    "world_summary_path": str(world_dir / "world_fusion_summary.json"),
}
(world_dir / "mrl7_closeout_summary.json").write_text(json.dumps(closeout, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "selected_path": str(selected_path),
    "session_id": session_id,
    "processed_frames": processed,
    "skipped_frames": skipped,
    "total_points": int(points_np.shape[0]),
    "world_dir": str(world_dir),
}, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 8e selected-input mrl7 adopted one-block res
RUN git clone https://github.com/ByteDance-Seed/Depth-Anything-3.git /content/Depth-Anything-3
RUN python -m pip install --quiet addict evo moviepy==1.0.3 pygame pycolmap plyfile trimesh gsplat
[INFO ] using MLP layer as FFN
[INFO ] Processed Images Done taking 0.015479326248168945 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.46178698539733887 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0010619163513183594 seconds
[INFO ] Processed Images Done taking 0.015416383743286133 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.3542144298553467 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0008351802825927734 seconds
[INFO ] Processed Images Done taking 0.011445045471191406 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35576891899108887 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0011758804321289062 seconds
[INFO ] Processed Images Done taking 0.021262407302856445 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.3544149398803711 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0011382102966308594 seconds
[INFO ] Processed Images Done taking 0.02000594139099121 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35317397117614746 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0010786056518554688 seconds
[INFO ] Processed Images Done taking 0.01982259750366211 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35514116287231445 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0012149810791015625 seconds
[INFO ] Processed Images Done taking 0.018063068389892578 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.34446215629577637 seconds
[INFO ] Conversion to Prediction Done. Time: 0.002073049545288086 seconds
[INFO ] Processed Images Done taking 0.01976180076599121 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35852694511413574 seconds
[INFO ] Conversion to Prediction Done. Time: 0.00110626220703125 seconds
[INFO ] Processed Images Done taking 0.019734621047973633 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.3572218418121338 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0010759830474853516 seconds
[INFO ] Processed Images Done taking 0.01919698715209961 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35421252250671387 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0011446475982666016 seconds
[INFO ] Processed Images Done taking 0.024491548538208008 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35954761505126953 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0010840892791748047 seconds
[INFO ] Processed Images Done taking 0.012181758880615234 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.3527512550354004 seconds
[INFO ] Conversion to Prediction Done. Time: 0.001003265380859375 seconds
{
  "selected_path": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/trajectreview-correcting-session-20260331-034831.zip",
  "session_id": "trajectreview-correcting-session-20260331-034831",
  "processed_frames": 12,
  "skipped_frames": 0,
  "total_points": 4608,
  "world_dir": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/trajectreview-correcting-session-20260331-034831_da3_multiframe_probe_v01/world_fusion_v01"
}
```

# codex v54

install 1 の error は command 自体ではなく、`bash` command を Python cell に貼ったことが原因である。ここからは install command を Colab でそのまま動く Python block に寄せる。shell magics を使わず、`subprocess.run(...)` で統一する。

```python
# Install 1 and 2 retry
from pathlib import Path
import shutil
import subprocess

repo_root = Path("/content/Depth-Anything-3")
if repo_root.exists():
    shutil.rmtree(repo_root)

def run(cmd):
    print("RUN", " ".join(cmd))
    subprocess.run(cmd, check=True)

run(["git", "clone", "https://github.com/ByteDance-Seed/Depth-Anything-3.git", str(repo_root)])
run(["python", "-m", "pip", "install", "--quiet", "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile", "trimesh", "gsplat"])

print("repo_exists", repo_root.exists(), repo_root)
```

# admin

```text
# Install 1 and 2 retry res
RUN git clone https://github.com/ByteDance-Seed/Depth-Anything-3.git /content/Depth-Anything-3
RUN python -m pip install --quiet addict evo moviepy==1.0.3 pygame pycolmap plyfile trimesh gsplat
repo_exists True /content/Depth-Anything-3
```

# codex v55

`MRL-7 adopted one-block` の今回の failure は gaussian 側ではなく、window 選定の手前で `best_window` が作れなかったことにある。まず `frame_pose_index.csv` の実 column、非空 row 数、image file 対応列の有無を診断し、今回の selected session に対する最小吸収 key を確定する。

```python
# Step 7x frame-pose schema diagnostic
from pathlib import Path
import json
import pandas as pd

selected_doc = json.loads(Path("/content/runbook_selected_input.json").read_text(encoding="utf-8"))
session_id = selected_doc["session_id"]
extract_root = Path("/content/trajectreview_input")
pkg_hits = sorted(extract_root.rglob("session_package.json"))
assert pkg_hits, f"session_package.json not found under {extract_root}"
session_pkg = next((p for p in pkg_hits if p.parent.name == "trajectreview"), pkg_hits[0])
session_root = session_pkg.parent
images_dir = session_root / "images"
frame_pose_path = session_root / "frame_pose_index.csv"

assert frame_pose_path.exists(), frame_pose_path
df = pd.read_csv(frame_pose_path)
image_files = sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpeg"))

frame_candidates = [
    "image_file_name",
    "frame_name",
    "image_file",
    "image_path",
    "file_name",
]
time_candidates = [
    "frame_timestamp_ns",
    "capture_timestamp_ns",
    "timestamp_ns",
    "captureTimestampNs",
]

frame_col = next((c for c in frame_candidates if c in df.columns), None)
time_col = next((c for c in time_candidates if c in df.columns), None)

non_null_count = None if frame_col is None else int(df[frame_col].notna().sum())
head_rows = df.head(5).fillna("").to_dict(orient="records")

result = {
    "session_id": session_id,
    "frame_pose_path": str(frame_pose_path),
    "row_count": int(len(df)),
    "columns": list(df.columns),
    "frame_col": frame_col,
    "time_col": time_col,
    "frame_col_non_null_count": non_null_count,
    "image_count": int(len(image_files)),
    "first_images": [p.name for p in image_files[:5]],
    "head_rows": head_rows,
}

print(json.dumps(result, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7x frame-pose schema diagnostic res
{
  "session_id": "trajectreview-correcting-session-20260331-034831",
  "frame_pose_path": "/content/trajectreview_input/session-20260331-034831/trajectreview/frame_pose_index.csv",
  "row_count": 1598,
  "columns": [
    "frame_index",
    "image_file_name",
    "frame_timestamp_ns",
    "pose_record_index",
    "pose_timestamp_ns",
    "time_delta_ms",
    "image_intrinsics_mode",
    "tracking_state"
  ],
  "frame_col": "image_file_name",
  "time_col": "frame_timestamp_ns",
  "frame_col_non_null_count": 0,
  "image_count": 26,
  "first_images": [
    "frame_000052.jpg",
    "frame_000113.jpg",
    "frame_000174.jpg",
    "frame_000235.jpg",
    "frame_000296.jpg"
  ],
  "head_rows": [
    {
      "frame_index": 0,
      "image_file_name": "",
      "frame_timestamp_ns": 1151705116150917,
      "pose_record_index": 1,
      "pose_timestamp_ns": 1151706833371421,
      "time_delta_ms": 1717.221,
      "image_intrinsics_mode": "session_fixed",
      "tracking_state": "TRACKING"
    },
    {
      "frame_index": 1,
      "image_file_name": "",
      "frame_timestamp_ns": 1151705149514980,
      "pose_record_index": 1,
      "pose_timestamp_ns": 1151706833371421,
      "time_delta_ms": 1683.856,
      "image_intrinsics_mode": "session_fixed",
      "tracking_state": "TRACKING"
    },
    {
      "frame_index": 2,
      "image_file_name": "",
      "frame_timestamp_ns": 1151705182878990,
      "pose_record_index": 1,
      "pose_timestamp_ns": 1151706833371421,
      "time_delta_ms": 1650.492,
      "image_intrinsics_mode": "session_fixed",
      "tracking_state": "TRACKING"
    },
    {
      "frame_index": 3,
      "image_file_name": "",
      "frame_timestamp_ns": 1151705216243053,
      "pose_record_index": 1,
      "pose_timestamp_ns": 1151706833371421,
      "time_delta_ms": 1617.128,
      "image_intrinsics_mode": "session_fixed",
      "tracking_state": "TRACKING"
    },
    {
      "frame_index": 4,
      "image_file_name": "",
      "frame_timestamp_ns": 1151705249607063,
      "pose_record_index": 1,
      "pose_timestamp_ns": 1151706833371421,
      "time_delta_ms": 1583.764,
      "image_intrinsics_mode": "session_fixed",
      "tracking_state": "TRACKING"
    }
  ]
}
```

# codex v56

原因は `frame_pose_index.csv` の `image_file_name` 列が存在するが全件空であることだった。この session では `images/` 側の実 file 列挙を `frame_index` 昇順へ対応付ける必要がある。`adopted one-block` の window 選定部だけをその schema に吸収した retry block を渡す。

```python
# Step 7y one-block schema-fix retry
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
assert "frame_index" in frame_pose_df.columns
assert "frame_timestamp_ns" in frame_pose_df.columns
assert "pose_record_index" in frame_pose_df.columns

rows = frame_pose_df.copy()
rows = rows.sort_values("frame_index").reset_index(drop=True)

image_files = sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpeg"))
assert image_files, images_dir

frame_names = [p.name for p in image_files]
usable_count = min(len(rows), len(frame_names))
rows = rows.iloc[:usable_count].copy()
rows["image_file_name"] = frame_names[:usable_count]
rows["timestamp_sec"] = rows["frame_timestamp_ns"].astype(np.float64) / 1e9

gaps = rows["timestamp_sec"].diff().fillna(0.0)
window_break = gaps > 0.2
window_id = window_break.cumsum()
rows["window_id"] = window_id

best_window = None
for _, g in rows.groupby("window_id"):
    span = float(g["timestamp_sec"].iloc[-1] - g["timestamp_sec"].iloc[0]) if len(g) >= 2 else 0.0
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
    "frame_col": "image_file_name(derived_from_images_dir)",
    "time_col": "frame_timestamp_ns",
    "aligned_frame_count": int(len(rows)),
    "window_span_sec": float(best_window["span_sec"]),
    "window_frame_count": int(best_window["frame_count"]),
    "window_start_sec": float(g["timestamp_sec"].iloc[0]),
    "window_end_sec": float(g["timestamp_sec"].iloc[-1]),
    "sample_frame_count": int(len(sample_rows)),
    "sample_frames": sample_rows[["image_file_name", "pose_record_index", "timestamp_sec"]].rename(
        columns={"image_file_name": "frame_name"}
    ).to_dict(orient="records"),
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
    f.write("ply\nformat ascii 1.0\n")
    f.write(f"element vertex {len(merged)}\n")
    f.write("property float x\nproperty float y\nproperty float z\n")
    f.write("end_header\n")
    for p in merged:
        f.write(f"{p[0]} {p[1]} {p[2]}\n")

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

print(json.dumps({
    "session_id": session_id,
    "derived_frame_mapping": True,
    "window_span_sec": window_probe["window_span_sec"],
    "sample_frame_count": window_probe["sample_frame_count"],
    "processed_frames": world_summary["processed_frames"],
    "skipped_frames": len(world_summary["skipped_frames"]),
    "total_points": world_summary["total_points"],
    "world_dir": str(world_dir),
}, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7y one-block schema-fix retry res
[INFO ] using MLP layer as FFN
[INFO ] Processed Images Done taking 0.015917062759399414 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.4734489917755127 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0011992454528808594 seconds
[INFO ] Processed Images Done taking 0.013476371765136719 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35451388359069824 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0010387897491455078 seconds
[INFO ] Processed Images Done taking 0.012862920761108398 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.3576667308807373 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0010676383972167969 seconds
[INFO ] Processed Images Done taking 0.012304544448852539 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35817885398864746 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0008702278137207031 seconds
[INFO ] Processed Images Done taking 0.01228642463684082 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35579419136047363 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0010852813720703125 seconds
[INFO ] Processed Images Done taking 0.012594938278198242 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.361072301864624 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0010123252868652344 seconds
[INFO ] Processed Images Done taking 0.012558221817016602 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.3604557514190674 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0009686946868896484 seconds
[INFO ] Processed Images Done taking 0.017222166061401367 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35862016677856445 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0008745193481445312 seconds
[INFO ] Processed Images Done taking 0.018078327178955078 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.358720064163208 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0011081695556640625 seconds
[INFO ] Processed Images Done taking 0.018384695053100586 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.35830068588256836 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0013642311096191406 seconds
[INFO ] Processed Images Done taking 0.017238855361938477 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.3560307025909424 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0009531974792480469 seconds
[INFO ] Processed Images Done taking 0.01888728141784668 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.3580751419067383 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0010709762573242188 seconds
{
  "session_id": "trajectreview-correcting-session-20260331-034831",
  "derived_frame_mapping": true,
  "window_span_sec": 0.8341010939329863,
  "sample_frame_count": 12,
  "processed_frames": 12,
  "skipped_frames": 0,
  "total_points": 4032,
  "world_dir": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/trajectreview-correcting-session-20260331-034831_da3_multiframe_probe_v01/world_fusion_v01"
}
```

# codex v57

```text
# Step 7z gaussian continue from step-7y

- 目的:
  - 今回だけ fresh 再立ち上げではなく、`Step 7y` 直後の runtime をそのまま継続して gaussian `20 step` へ進む。
- 前提:
  - `Step 7y one-block schema-fix retry` が同じ runtime で成功している。
  - `merged`, `window_probe`, `images_dir`, `pose_records`, `quat_to_rot`, `device`, `world_dir` が notebook memory に残っている。
- 到達:
  - `gaussian_params_init.pt`
  - `gaussian_params_optim20.pt`
  - `gaussian_render_init.png`
  - `gaussian_render_optim20.png`
  - `gaussian_optim20_summary.json`
```

```python
# Step 7z gaussian continue from step-7y
import math
import torch
import torch.nn.functional as F
import imageio.v3 as iio

first_rec = window_probe["sample_frames"][0]
first_frame = first_rec["frame_name"]
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
        quats=F.normalize(quats, dim=-1),
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

def save_png(path, tensor_img):
    arr = torch.clamp(tensor_img.detach(), 0.0, 1.0).cpu().numpy()
    Image.fromarray((arr * 255).astype(np.uint8)).save(path)

optimizer = torch.optim.Adam([means, scales, quats, opacities, colors], lr=1e-2)

pred_init, _ = render_once()
loss_init = torch.mean((pred_init - target) ** 2)
save_png(world_dir / "gaussian_render_init.png", pred_init)
torch.save({
    "means": means.detach().cpu(),
    "scales_log": scales.detach().cpu(),
    "quats": F.normalize(quats.detach(), dim=-1).cpu(),
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
    "quats": F.normalize(quats.detach(), dim=-1).cpu(),
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
(world_dir / "gaussian_optim20_summary.json").write_text(
    json.dumps(gaussian_summary, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(json.dumps({
    "target_frame": first_frame,
    "point_count": gaussian_summary["point_count"],
    "loss_init": gaussian_summary["loss_init"],
    "loss_final": gaussian_summary["loss_final"],
    "world_dir": str(world_dir),
}, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 7z gaussian continue from step-7y res
{
  "target_frame": "frame_000052.jpg",
  "point_count": 1024,
  "loss_init": 0.1796136051416397,
  "loss_final": 0.021261239424347878,
  "world_dir": "/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/trajectreview-correcting-session-20260331-034831_da3_multiframe_probe_v01/world_fusion_v01"
}
```

# codex v58

```text
# Step 7z2 gaussian-optim1000 continue from step-7z

- 目的:
  - 今回だけ `Step 7z` の直後 runtime をそのまま使い、gaussian optimization を `1000 step` まで伸ばす。
- 前提:
  - `Step 7z gaussian continue from step-7y` が同じ runtime で成功している。
  - `means`, `scales`, `quats`, `opacities`, `colors`, `target`, `world_dir`, `render_once`, `save_png` が残っている。
- 到達:
  - `gaussian_params_optim1000.pt`
  - `gaussian_render_optim1000.png`
  - `gaussian_optim1000_summary.json`
```

```python
# Step 7z2 gaussian-optim1000 continue from step-7z
optimizer = torch.optim.Adam([means, scales, quats, opacities, colors], lr=1e-2)

pred_init_1000, _ = render_once()
loss_init_1000 = torch.mean((pred_init_1000 - target) ** 2)

loss_history_1000 = [float(loss_init_1000.detach().cpu().item())]
for _ in range(1000):
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

# admin

```text
# Step 7z2 gaussian-optim1000 continue from step-7z res

```

# codex v59

```text
# Step 7z3 copy artifacts to visible MyDrive folder

- 目的:
  - `shortcut-targets-by-id` 配下では見えにくい output を、admin が Drive UI から直接確認しやすい `MyDrive` 配下へ明示 copy する。
- 保存先:
  - `/content/drive/MyDrive/trajectreview_visible_results/prj-kisaragi_0002/trajectreview-correcting-session-20260331-034831/world_fusion_v01`
- 前提:
  - `Step 7z` または `Step 7z2` まで通っていて、`world_dir` が同じ runtime に残っている。
```

```python
# Step 7z3 copy artifacts to visible MyDrive folder
from pathlib import Path
import shutil
import json

visible_dir = Path("/content/drive/MyDrive/trajectreview_visible_results/prj-kisaragi_0002/trajectreview-correcting-session-20260331-034831/world_fusion_v01")
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
    "gaussian_params_optim1000.pt",
    "gaussian_render_optim1000.png",
    "gaussian_optim1000_summary.json",
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

# admin

```text
# Step 7z3 copy artifacts to visible MyDrive folder res

```

# codex v60

```text
# Step 9a giant-infer-gs entrypoint probe

- 目的:
  - 現在の `Depth-Anything-3` clone の中で、`DA3 Giant` / `Giant Large` と `infer_gs=True` を受ける entrypoint、model id 候補、`gs_ply` / `gs_video` 関連の引数名を特定する。
  - `MRL-9` の first config を repo 実体に合わせて固定する。
- rollback baseline:
  - 既存の `MetricLarge route` は変更しない。
- 前提:
  - `/content/Depth-Anything-3` が存在する。
  - 可能なら `/content/runbook_selected_input.json` も残っている。
- 到達:
  - `/content/mrl9_entrypoint_probe.json`
  - `infer_gs` / `gs_ply` / `gs_video` / `giant` に関する hit list
```

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

# admin

```text
# Step 9a giant-infer-gs entrypoint probe res

one blockでエラーです


---------------------------------------------------------------------------
OSError                                   Traceback (most recent call last)
/tmp/ipykernel_17764/1970725003.py in <cell line: 0>()
     48 assert arcore_pose_path.exists(), arcore_pose_path
     49 
---> 50 probe_dir.mkdir(parents=True, exist_ok=True)
     51 world_dir.mkdir(parents=True, exist_ok=True)
     52 

/usr/lib/python3.12/pathlib.py in mkdir(self, mode, parents, exist_ok)
   1309         """
   1310         try:
-> 1311             os.mkdir(self, mode)
   1312         except FileNotFoundError:
   1313             if not parents or self.parent == self:

OSError: [Errno 95] Operation not supported: '/content/drive/.shortcut-targets-by-id/12jqKG1d7JEsFwFlqzHDdaAf7-HRdBvFT/trajectreview-correcting-session-20260331-034831_da3_multiframe_probe_v01'


```

# codex v61

```text
# Step 9b writable-results-root-fix

- 原因:
  - selected input は正しいが、`results_root = /content/drive/.shortcut-targets-by-id/12jqKG1d7JEsFwFlqzHDdaAf7-HRdBvFT` 直下で `mkdir` が通らない。
- 目的:
  - `results_root` を admin から見える writable path に正規化し、`MRL-7 adopted one-block` / `MRL-9` の両方で使える保存先へ固定する。
- 方針:
  - 第一候補を `/content/drive/MyDrive/trajectreview/modeling`
  - 既存 `results_root` は evidence 用に保持しつつ、runtime では writable root を `runbook_selected_input.json` に上書きする。
```

```python
# Step 9b writable-results-root-fix
from pathlib import Path
import json

selected_doc_path = Path("/content/runbook_selected_input.json")
selected_doc = json.loads(selected_doc_path.read_text(encoding="utf-8"))

old_results_root = Path(selected_doc["results_root"])
preferred_roots = [
    Path("/content/drive/MyDrive/trajectreview/modeling"),
    Path("/content/drive/MyDrive/trajectreview_visible_results/prj-kisaragi_0002"),
]
writable_root = next((p for p in preferred_roots if p.exists()), preferred_roots[0])
writable_root.mkdir(parents=True, exist_ok=True)

probe_dir = writable_root / f"{selected_doc['session_id']}_da3_multiframe_probe_v01"
probe_dir.mkdir(parents=True, exist_ok=True)

selected_doc["results_root"] = str(writable_root)
selected_doc["results_root_previous"] = str(old_results_root)
selected_doc_path.write_text(json.dumps(selected_doc, indent=2, ensure_ascii=False), encoding="utf-8")

result = {
    "session_id": selected_doc["session_id"],
    "old_results_root": str(old_results_root),
    "new_results_root": str(writable_root),
    "probe_dir_exists": probe_dir.exists(),
    "probe_dir": str(probe_dir),
}
print(json.dumps(result, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 9b writable-results-root-fix res
{
  "session_id": "trajectreview-correcting-session-20260331-034831",
  "old_results_root": "/content/drive/.shortcut-targets-by-id/12jqKG1d7JEsFwFlqzHDdaAf7-HRdBvFT",
  "new_results_root": "/content/drive/MyDrive/trajectreview/modeling",
  "probe_dir_exists": true,
  "probe_dir": "/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3_multiframe_probe_v01"
}
```

# codex v62

```text
# Step 9c rerun one-block after writable-results-root-fix

- 目的:
  - `results_root` を writable path に直した同じ runtime で、直前に落ちた one-block をそのまま再実行する。
- 前提:
  - `Step 9b writable-results-root-fix` が成功している。
  - `/content/runbook_selected_input.json` の `results_root` が `/content/drive/MyDrive/trajectreview/modeling` へ更新済みである。
- 到達:
  - `probe_dir` と `world_dir` が `MyDrive/trajectreview/modeling/...` 配下に作られる。
  - 以前の `OSError: [Errno 95] Operation not supported` が消える。
- 実行:
  - 直前に落ちた one-block を、code は変えずにそのままもう一度実行する。
```

# admin

```text
# Step 9c rerun one-block after writable-results-root-fix res
WARNING:py.warnings:/usr/local/lib/python3.12/dist-packages/huggingface_hub/utils/_auth.py:94: UserWarning: 
The secret `HF_TOKEN` does not exist in your Colab secrets.
To authenticate with the Hugging Face Hub, create a token in your settings tab (https://huggingface.co/settings/tokens), set it as secret in your Google Colab and restart your session.
You will be able to reuse this secret in all of your notebooks.
Please note that authentication is recommended but still optional to access public models or datasets.
  warnings.warn(

Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
WARNING:huggingface_hub.utils._http:Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
config.json: 100%
 847/847 [00:00<00:00, 104kB/s]
[INFO ] using MLP layer as FFN
model.safetensors: 100%
 1.34G/1.34G [00:05<00:00, 263MB/s]
[INFO ] Processed Images Done taking 0.09307742118835449 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 1.5097167491912842 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0018341541290283203 seconds
[INFO ] Processed Images Done taking 0.010960102081298828 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.044922828674316406 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0007348060607910156 seconds
[INFO ] Processed Images Done taking 0.011121988296508789 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.04599738121032715 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0007758140563964844 seconds
[INFO ] Processed Images Done taking 0.010864496231079102 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.04751086235046387 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0009031295776367188 seconds
[INFO ] Processed Images Done taking 0.00902700424194336 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.046828269958496094 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0007572174072265625 seconds
[INFO ] Processed Images Done taking 0.010274648666381836 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.047478675842285156 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0007724761962890625 seconds
[INFO ] Processed Images Done taking 0.010695457458496094 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.04694986343383789 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0009264945983886719 seconds
[INFO ] Processed Images Done taking 0.009404182434082031 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.047452688217163086 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0007190704345703125 seconds
[INFO ] Processed Images Done taking 0.009318113327026367 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.04698443412780762 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0007166862487792969 seconds
[INFO ] Processed Images Done taking 0.008845806121826172 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.04787015914916992 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0009462833404541016 seconds
[INFO ] Processed Images Done taking 0.009125709533691406 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.04761815071105957 seconds
[INFO ] Conversion to Prediction Done. Time: 0.00069427490234375 seconds
[INFO ] Processed Images Done taking 0.009153366088867188 seconds. Shape:  torch.Size([1, 3, 378, 504])
[INFO ] Model Forward Pass Done. Time: 0.047577857971191406 seconds
[INFO ] Conversion to Prediction Done. Time: 0.0007116794586181641 seconds
gsplat: CUDA extension has been set up successfully in 195.22 seconds.
{
  "window_span_sec": 0.8341010939329863,
  "sample_frame_count": 12,
  "processed_frames": 12,
  "skipped_frames": 0,
  "total_points": 4032,
  "loss_init": 0.17961707711219788,
  "loss_final": 0.02125917188823223,
  "world_dir": "/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3_multiframe_probe_v01/world_fusion_v01"
}
```

# codex v63

```text
# Step 9d giant-infer-gs entrypoint probe after baseline pass

- 判断:
  - `Step 9c` で writable results root 前提の baseline one-block は通った。
  - ここで `1000 step` を伸ばすより、`MRL-9` の本題である `Giant + infer_gs=True` の entrypoint 固定を先に進める。
- 目的:
  - 現在の runtime をそのまま使って、`Depth-Anything-3` clone 内の `infer_gs` / `gs_ply` / `gs_video` / `Giant` 関連 entrypoint を特定する。
  - 次の `mRL-9.1` block を repo 実体に合わせて固定する。
- 前提:
  - `/content/Depth-Anything-3` が存在する。
  - `Step 9c` が成功している。
```

```python
# Step 9d giant-infer-gs entrypoint probe after baseline pass
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

# admin

```text
# Step 9d giant-infer-gs entrypoint probe after baseline pass res
{
  "probe_path": "/content/mrl9_entrypoint_probe.json",
  "hit_count": 244,
  "from_pretrained_sig": "(pretrained_model_name_or_path: Union[str, pathlib.Path], *, force_download: bool = False, token: Union[str, bool, NoneType] = None, cache_dir: Union[str, pathlib.Path, NoneType] = None, local_files_only: bool = False, revision: Optional[str] = None, **model_kwargs) -> ~T",
  "api_init_sig": "(self, model_name: 'str' = 'da3-large', **kwargs)"
}
/content/Depth-Anything-3/README.md:20: This work presents **Depth Anything 3 (DA3)**, a model that predicts spatially consistent geometry from
/content/Depth-Anything-3/README.md:22: In pursuit of minimal modeling, DA3 yields two key insights:
/content/Depth-Anything-3/README.md:26: 🏆 DA3 significantly outperforms
/content/Depth-Anything-3/README.md:43: - **11-12-2025:** 🚀 New models and [**DA3-Streaming**](da3_streaming/README.md) released! Handle ultra-long video sequence inference with less than 12GB GPU memory via sliding-window streaming inference. Special thanks to [Kai Deng](https://github.com/DengKaiCQ) for his contribution to DA3-Streaming!
/content/Depth-Anything-3/README.md:46: - **25-11-2025:** Add [Awesome DA3 Projects](#-awesome-da3-projects), a community-driven section featuring DA3-based applications.
/content/Depth-Anything-3/README.md:54: - 🌟 **DA3 Main Series** (`DA3-Giant`, `DA3-Large`, `DA3-Base`, `DA3-Small`) These are our flagship foundation models, trained with a unified depth-ray representation. By varying the input configuration, a single model can perform a wide range of tasks:
/content/Depth-Anything-3/README.md:61: - 📐 **DA3 Metric Series** (`DA3Metric-Large`) A specialized model fine-tuned for metric depth estimation in monocular settings, ideal for applications requiring real-world scale.
/content/Depth-Anything-3/README.md:63: - 🔍 **DA3 Monocular Series** (`DA3Mono-Large`). A dedicated model for high-quality relative monocular depth estimation. Unlike disparity-based models (e.g.,  [Depth Anything 2](https://github.com/DepthAnything/Depth-Anything-V2)), it directly predicts depth, resulting in superior geometric accuracy.
/content/Depth-Anything-3/README.md:65: 🔗 Leveraging these available models, we developed a **nested series** (`DA3Nested-Giant-Large`). This series combines a any-view giant model with a metric model to reconstruct visual geometry at a real-world metric scale.
/content/Depth-Anything-3/README.md:104: model = DepthAnything3.from_pretrained("depth-anything/DA3NESTED-GIANT-LARGE")
/content/Depth-Anything-3/README.md:125: export MODEL_DIR=depth-anything/DA3NESTED-GIANT-LARGE
/content/Depth-Anything-3/README.md:207: Generally, you should observe that DA3-LARGE achieves comparable results to VGGT.
/content/Depth-Anything-3/README.md:211: ⚠️ Models with the `-1.1` suffix are retrained after fixing a training bug; prefer these refreshed checkpoints. The original `DA3NESTED-GIANT-LARGE`, `DA3-GIANT`, and `DA3-LARGE` remain available but are deprecated. You could expect much better performance for street scenes with the `-1.1` models.
/content/Depth-Anything-3/README.md:216: | [DA3NESTED-GIANT-LARGE-1.1](https://huggingface.co/depth-anything/DA3NESTED-GIANT-LARGE-1.1)  | 1.40B     | ✅             | ✅            | ✅             | ✅     | ✅             | ✅         | CC BY-NC 4.0   |
/content/Depth-Anything-3/README.md:217: | [DA3NESTED-GIANT-LARGE](https://huggingface.co/depth-anything/DA3NESTED-GIANT-LARGE)  | 1.40B     | ✅             | ✅            | ✅             | ✅     | ✅             | ✅         | CC BY-NC 4.0   |
/content/Depth-Anything-3/README.md:219: | [DA3-GIANT-1.1](https://huggingface.co/depth-anything/DA3-GIANT-1.1)                     | 1.15B     | ✅             | ✅            | ✅             | ✅     |               |           | CC BY-NC 4.0   |
/content/Depth-Anything-3/README.md:220: | [DA3-GIANT](https://huggingface.co/depth-anything/DA3-GIANT)                     | 1.15B     | ✅             | ✅            | ✅             | ✅     |               |           | CC BY-NC 4.0   |
/content/Depth-Anything-3/README.md:221: | [DA3-LARGE-1.1](https://huggingface.co/depth-anything/DA3-LARGE-1.1)                     | 0.35B     | ✅             | ✅            | ✅             |       |               |           | CC BY-NC 4.0     |
/content/Depth-Anything-3/README.md:222: | [DA3-LARGE](https://huggingface.co/depth-anything/DA3-LARGE)                     | 0.35B     | ✅             | ✅            | ✅             |       |               |           | CC BY-NC 4.0     |
/content/Depth-Anything-3/README.md:223: | [DA3-BASE](https://huggingface.co/depth-anything/DA3-BASE)                     | 0.12B     | ✅             | ✅            | ✅             |       |               |           | Apache 2.0     |
/content/Depth-Anything-3/README.md:224: | [DA3-SMALL](https://huggingface.co/depth-anything/DA3-SMALL)                     | 0.08B     | ✅             | ✅            | ✅             |       |               |           | Apache 2.0     |
/content/Depth-Anything-3/README.md:227: | [DA3METRIC-LARGE](https://huggingface.co/depth-anything/DA3METRIC-LARGE)              | 0.35B     | ✅             |              |               |       | ✅             | ✅         | Apache 2.0     |
/content/Depth-Anything-3/README.md:230: | [DA3MONO-LARGE](https://huggingface.co/depth-anything/DA3MONO-LARGE)                | 0.35B     | ✅             |              |               |               |       | ✅         | Apache 2.0     |
/content/Depth-Anything-3/README.md:235: - **Monocular Metric Depth**: To obtain metric depth in meters from `DA3METRIC-LARGE`, use `metric_depth = focal * net_output / 300.`, where `focal` is the focal length in pixels (typically the average of fx and fy from the camera intrinsic matrix K). Note that the output from `DA3NESTED-GIANT-LARGE` is already in meters.
/content/Depth-Anything-3/README.md:239: <summary>AUC3 Results for DA3NESTED-GIANT-LARGE</summary>
/content/Depth-Anything-3/README.md:254: ## 🏢 Awesome DA3 Projects
/content/Depth-Anything-3/README.md:256: A community-curated list of Depth Anything 3 integrations across 3D tools, creative pipelines, robotics, and web/VR viewers, including but not limited to these. You are welcome to submit your DA3-based project via PR, and we will review and feature it if applicable.
/content/Depth-Anything-3/README.md:258: - [DA3-blender](https://github.com/xy-gao/DA3-blender): Blender addon for DA3-based 3D reconstruction from a set of images.
/content/Depth-Anything-3/README.md:262: - [DA3-ROS2-Wrapper](https://github.com/GerdsenAI/GerdsenAI-Depth-Anything-3-ROS2-Wrapper): Real-time DA3 depth in ROS2 with multi-camera support.
/content/Depth-Anything-3/README.md:264: - [DA3-ROS2-CPP-TensorRT](https://github.com/ika-rwth-aachen/ros2-depth-anything-v3-trt): DA3 ROS2 C++ TensorRT Inference Node: a ROS2 node for DA3 depth estimation using TensorRT for real-time inference.
/content/Depth-Anything-3/README.md:266: - [VideoDepthViewer3D](https://github.com/amariichi/VideoDepthViewer3D): Streaming videos with DA3 metric depth to a Three.js/WebXR 3D viewer for VR/stereo playback.
/content/Depth-Anything-3/docs/API.md:33: model = DepthAnything3.from_pretrained("depth-anything/DA3NESTED-GIANT-LARGE").to("cuda")
/content/Depth-Anything-3/docs/API.md:73: # Note: infer_gs=True requires da3-giant or da3nested-giant-large model
/content/Depth-Anything-3/docs/API.md:74: model = DepthAnything3(model_name="da3-giant").to("cuda")
/content/Depth-Anything-3/docs/API.md:81: export_format="npz-glb-gs_ply-gs_video",
/content/Depth-Anything-3/docs/API.md:83: infer_gs=True,  # Required for gs_ply and gs_video exports
/content/Depth-Anything-3/docs/API.md:144: - 🦾 `"da3-giant"` - 1.15B params, any-view model with GS support
/content/Depth-Anything-3/docs/API.md:150: - 🎯 `"da3nested-giant-large"` - 1.40B params, nested model with all features
/content/Depth-Anything-3/docs/API.md:162: infer_gs=True,                   # Enable Gaussian branch for gs exports
/content/Depth-Anything-3/docs/API.md:165: render_exts=render_extrinsics,    # Optional renders for gs_video

```

# codex v64

```text
## 2026-03-31 v64 Step 9e giant infer_gs first execution

- 基準:
  - `Step 9d` で `DepthAnything3(model_name="da3-giant")` と `infer_gs=True` が repo 実体として確認できた。
  - rollback baseline は `MetricLarge route` とする。
- 目的:
  - `da3-giant` で `infer_gs=True` を実行し、`gs_ply` / `gs_video` を含む export が最小 1 本通るか確認する。
- 前提:
  - `/content/Depth-Anything-3` が存在する。
  - `/content/runbook_selected_input.json` が存在する。
  - writable `results_root` が `/content/drive/MyDrive/trajectreview/modeling` に向いている。
  - `selected input` は zip でも dir でもよい。
```

```python
# Step 9e giant infer_gs first execution
from pathlib import Path
import json
import shutil
import zipfile
import sys
import traceback

import torch

repo_root = Path("/content/Depth-Anything-3")
assert repo_root.exists(), {"repo_not_found": str(repo_root)}

src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from depth_anything_3.api import DepthAnything3

selected_doc_path = Path("/content/runbook_selected_input.json")
assert selected_doc_path.exists(), {"selected_doc_not_found": str(selected_doc_path)}
selected_doc = json.loads(selected_doc_path.read_text(encoding="utf-8"))

input_path = Path(selected_doc["path"])
results_root = Path(selected_doc["results_root"])
assert input_path.exists(), {"input_not_found": str(input_path)}
results_root.mkdir(parents=True, exist_ok=True)

extract_root = Path("/content/trajectreview_input")
if extract_root.exists():
    shutil.rmtree(extract_root)
extract_root.mkdir(parents=True, exist_ok=True)

if input_path.is_file() and input_path.suffix.lower() == ".zip":
    with zipfile.ZipFile(input_path, "r") as zf:
        zf.extractall(extract_root)
    session_root_candidates = [p.parent for p in extract_root.rglob("session_package.json")]
    assert session_root_candidates, {"session_package_not_found_under": str(extract_root)}
    session_root = session_root_candidates[0]
else:
    session_root = input_path

images_dir = next((p for p in session_root.rglob("images") if p.is_dir()), None)
assert images_dir is not None, {"images_dir_not_found_under": str(session_root)}

image_paths = sorted(list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpeg")))
assert image_paths, {"images_not_found": str(images_dir)}

sample_images = image_paths[: min(60, len(image_paths))]
session_id = selected_doc["session_id"]
probe_dir = results_root / f"{session_id}_da3giant_infergs_probe_v01"
probe_dir.mkdir(parents=True, exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
summary = {
    "session_id": session_id,
    "input_path": str(input_path),
    "session_root": str(session_root),
    "images_dir": str(images_dir),
    "image_count_total": len(image_paths),
    "image_count_used": len(sample_images),
    "results_root": str(results_root),
    "probe_dir": str(probe_dir),
    "device": device,
    "model_name": "da3-giant",
    "infer_gs": True,
    "export_format": "npz-glb-gs_ply-gs_video",
}

try:
    model = DepthAnything3(model_name="da3-giant").to(device)
    outputs = model.infer(
        [str(p) for p in sample_images],
        fps=1,
        num_frames=len(sample_images),
        process_res=504,
        infer_gs=True,
        export_dir=str(probe_dir),
        export_format="npz-glb-gs_ply-gs_video",
        chunk_size=20,
    )
    summary["infer_call"] = "ok"
    summary["output_type"] = type(outputs).__name__
except Exception as e:
    summary["infer_call"] = "error"
    summary["error_type"] = type(e).__name__
    summary["error_message"] = str(e)
    summary["traceback_tail"] = traceback.format_exc().splitlines()[-20:]

exported = []
for p in sorted(probe_dir.rglob("*")):
    if p.is_file():
        exported.append(str(p))
summary["exported_files"] = exported

summary_path = probe_dir / "step9e_giant_infergs_summary.json"
summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "summary_path": str(summary_path),
    "infer_call": summary["infer_call"],
    "exported_file_count": len(exported),
    "probe_dir": str(probe_dir),
}, indent=2, ensure_ascii=False))
for item in exported[:40]:
    print(item)
if summary["infer_call"] != "ok":
    print(json.dumps({
        "error_type": summary.get("error_type"),
        "error_message": summary.get("error_message"),
    }, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 9e giant infer_gs first execution res
[INFO ] using SwiGLU layer as FFN
[WARN ] Dependency 'e3nn' not found. Required for rotating the camera space SH coeff
{
  "summary_path": "/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/step9e_giant_infergs_summary.json",
  "infer_call": "error",
  "exported_file_count": 0,
  "probe_dir": "/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01"
}
{
  "error_type": "AttributeError",
  "error_message": "'DepthAnything3' object has no attribute 'infer'"
}
```

# codex v65

```text
## 2026-03-31 v65 Step 9f giant infer_gs api-method fix

- 原因:
  - `Step 9e` の失敗は `infer_gs` 非対応ではなく、`DepthAnything3` に `infer` method が存在しないことだった。
- 目的:
  - `docs/API.md` の実例と `dir(model)` / `inspect.signature(...)` を突き合わせて、正しい呼び出し method に修正する。
  - その場で `da3-giant` + `infer_gs=True` の first execution を retry する。
- 前提:
  - `/content/Depth-Anything-3` が存在する。
  - `/content/runbook_selected_input.json` が存在する。
  - `Step 9e` で作った `probe_dir` は再利用してよい。
```

```python
# Step 9f giant infer_gs api-method fix
from pathlib import Path
import json
import shutil
import zipfile
import sys
import traceback
import inspect

import torch

repo_root = Path("/content/Depth-Anything-3")
assert repo_root.exists(), {"repo_not_found": str(repo_root)}

src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from depth_anything_3.api import DepthAnything3

api_doc_path = repo_root / "docs" / "API.md"
api_doc_text = api_doc_path.read_text(encoding="utf-8", errors="ignore") if api_doc_path.exists() else ""
api_doc_hits = [line for line in api_doc_text.splitlines() if "infer_gs" in line or "export_format" in line or "da3-giant" in line][:40]

selected_doc_path = Path("/content/runbook_selected_input.json")
assert selected_doc_path.exists(), {"selected_doc_not_found": str(selected_doc_path)}
selected_doc = json.loads(selected_doc_path.read_text(encoding="utf-8"))

input_path = Path(selected_doc["path"])
results_root = Path(selected_doc["results_root"])
assert input_path.exists(), {"input_not_found": str(input_path)}
results_root.mkdir(parents=True, exist_ok=True)

extract_root = Path("/content/trajectreview_input")
if extract_root.exists():
    shutil.rmtree(extract_root)
extract_root.mkdir(parents=True, exist_ok=True)

if input_path.is_file() and input_path.suffix.lower() == ".zip":
    with zipfile.ZipFile(input_path, "r") as zf:
        zf.extractall(extract_root)
    session_root_candidates = [p.parent for p in extract_root.rglob("session_package.json")]
    assert session_root_candidates, {"session_package_not_found_under": str(extract_root)}
    session_root = session_root_candidates[0]
else:
    session_root = input_path

images_dir = next((p for p in session_root.rglob("images") if p.is_dir()), None)
assert images_dir is not None, {"images_dir_not_found_under": str(session_root)}
image_paths = sorted(list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpeg")))
assert image_paths, {"images_not_found": str(images_dir)}

sample_images = image_paths[: min(60, len(image_paths))]
session_id = selected_doc["session_id"]
probe_dir = results_root / f"{session_id}_da3giant_infergs_probe_v01"
probe_dir.mkdir(parents=True, exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = DepthAnything3(model_name="da3-giant").to(device)

public_methods = sorted([name for name in dir(model) if not name.startswith("_")])
callable_names = []
for name in public_methods:
    try:
        attr = getattr(model, name)
    except Exception:
        continue
    if callable(attr):
        callable_names.append(name)

preferred_method_name = None
preferred_method_sig = None
for candidate in ["inference", "forward", "__call__", "predict"]:
    if hasattr(model, candidate):
        attr = getattr(model, candidate)
        if callable(attr):
            preferred_method_name = candidate
            try:
                preferred_method_sig = str(inspect.signature(attr))
            except Exception:
                preferred_method_sig = "signature_unavailable"
            break

summary = {
    "session_id": session_id,
    "device": device,
    "probe_dir": str(probe_dir),
    "api_doc_hits": api_doc_hits,
    "callable_names_head": callable_names[:80],
    "preferred_method_name": preferred_method_name,
    "preferred_method_sig": preferred_method_sig,
}

try:
    if preferred_method_name == "inference":
        outputs = model.inference(
            [str(p) for p in sample_images],
            fps=1,
            num_frames=len(sample_images),
            process_res=504,
            infer_gs=True,
            export_dir=str(probe_dir),
            export_format="npz-glb-gs_ply-gs_video",
            chunk_size=20,
        )
    elif preferred_method_name in {"forward", "__call__"}:
        outputs = getattr(model, preferred_method_name)(
            [str(p) for p in sample_images],
            fps=1,
            num_frames=len(sample_images),
            process_res=504,
            infer_gs=True,
            export_dir=str(probe_dir),
            export_format="npz-glb-gs_ply-gs_video",
            chunk_size=20,
        )
    else:
        raise RuntimeError(f"no_supported_method: {preferred_method_name}")

    summary["infer_call"] = "ok"
    summary["output_type"] = type(outputs).__name__
except Exception as e:
    summary["infer_call"] = "error"
    summary["error_type"] = type(e).__name__
    summary["error_message"] = str(e)
    summary["traceback_tail"] = traceback.format_exc().splitlines()[-20:]

exported = []
for p in sorted(probe_dir.rglob("*")):
    if p.is_file():
        exported.append(str(p))
summary["exported_files"] = exported

summary_path = probe_dir / "step9f_giant_infergs_summary.json"
summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "summary_path": str(summary_path),
    "preferred_method_name": summary["preferred_method_name"],
    "preferred_method_sig": summary["preferred_method_sig"],
    "infer_call": summary["infer_call"],
    "exported_file_count": len(exported),
    "probe_dir": str(probe_dir),
}, indent=2, ensure_ascii=False))
for line in api_doc_hits[:20]:
    print(line)
for item in exported[:40]:
    print(item)
if summary["infer_call"] != "ok":
    print(json.dumps({
        "error_type": summary.get("error_type"),
        "error_message": summary.get("error_message"),
    }, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 9f giant infer_gs api-method fix res
[INFO ] using SwiGLU layer as FFN
{
  "summary_path": "/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/step9f_giant_infergs_summary.json",
  "preferred_method_name": "inference",
  "preferred_method_sig": "(image: 'list[np.ndarray | Image.Image | str]', extrinsics: 'np.ndarray | None' = None, intrinsics: 'np.ndarray | None' = None, align_to_input_ext_scale: 'bool' = True, infer_gs: 'bool' = False, use_ray_pose: 'bool' = False, ref_view_strategy: 'str' = 'saddle_balanced', render_exts: 'np.ndarray | None' = None, render_ixts: 'np.ndarray | None' = None, render_hw: 'tuple[int, int] | None' = None, process_res: 'int' = 504, process_res_method: 'str' = 'upper_bound_resize', export_dir: 'str | None' = None, export_format: 'str' = 'mini_npz', export_feat_layers: 'Sequence[int] | None' = None, conf_thresh_percentile: 'float' = 40.0, num_max_points: 'int' = 1000000, show_cameras: 'bool' = True, feat_vis_fps: 'int' = 15, export_kwargs: 'Optional[dict]' = {}) -> 'Prediction'",
  "infer_call": "error",
  "exported_file_count": 1,
  "probe_dir": "/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01"
}
    export_format="mini_npz-glb"
    export_format="feat_vis",
# Note: infer_gs=True requires da3-giant or da3nested-giant-large model
model = DepthAnything3(model_name="da3-giant").to("cuda")
    export_format="npz-glb-gs_ply-gs_video",
    infer_gs=True,  # Required for gs_ply and gs_video exports
    export_format="mini_npz-glb-depth_vis-feat_vis",
    export_format="glb",
    - 🦾 `"da3-giant"` - 1.15B params, any-view model with GS support
    infer_gs=True,                   # Enable Gaussian branch for gs exports
    export_format="mini_npz",
    export_kwargs={}                  # Optional, additional arguments to export functions. export_format:key:val, see 'Parameters/Export Parameters' for details
#### `infer_gs` (default: False)
`"gs_video"` in `export_format`). They describe an auxiliary camera trajectory
#### `export_format` (default: "mini_npz")
These parameters are passed directly to the `inference()` method and only apply when `export_format` includes `"glb"`.
These parameters are passed directly to the `inference()` method and only apply when `export_format` includes `"feat_vis"`.
These parameters are passed directly to the `inference()` method and only apply when `export_format` includes `"gs_ply"` or `"gs_video"`.
  - Access pattern: `export_kwargs[export_format][key] = value`
- **Requirements**: Must set `infer_gs=True` when calling `inference()`. Only supported by `da3-giant` and `da3nested-giant-large` models.
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/step9e_giant_infergs_summary.json
{
  "error_type": "TypeError",
  "error_message": "DepthAnything3.inference() got an unexpected keyword argument 'fps'"
}
```

# codex v66

```text
## 2026-03-31 v66 Step 9g giant infer_gs inference-signature fix

- 確定したこと:
  - 正しい method は `DepthAnything3.inference(...)`
  - `infer_gs=True` は `da3-giant` で有効化できる
- 今回の failure:
  - `fps`、`num_frames`、`chunk_size` は `inference()` signature に無い
- 目的:
  - `inference()` signature にある引数だけへ絞って、`gs_ply` / `gs_video` export を retry する
  - `render_exts` / `render_ixts` などが要る前に、まず最小 export が通るかを見る
```

```python
# Step 9g giant infer_gs inference-signature fix
from pathlib import Path
import json
import shutil
import zipfile
import sys
import traceback
import inspect

import torch

repo_root = Path("/content/Depth-Anything-3")
assert repo_root.exists(), {"repo_not_found": str(repo_root)}

src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from depth_anything_3.api import DepthAnything3

selected_doc_path = Path("/content/runbook_selected_input.json")
assert selected_doc_path.exists(), {"selected_doc_not_found": str(selected_doc_path)}
selected_doc = json.loads(selected_doc_path.read_text(encoding="utf-8"))

input_path = Path(selected_doc["path"])
results_root = Path(selected_doc["results_root"])
assert input_path.exists(), {"input_not_found": str(input_path)}
results_root.mkdir(parents=True, exist_ok=True)

extract_root = Path("/content/trajectreview_input")
if extract_root.exists():
    shutil.rmtree(extract_root)
extract_root.mkdir(parents=True, exist_ok=True)

if input_path.is_file() and input_path.suffix.lower() == ".zip":
    with zipfile.ZipFile(input_path, "r") as zf:
        zf.extractall(extract_root)
    session_root_candidates = [p.parent for p in extract_root.rglob("session_package.json")]
    assert session_root_candidates, {"session_package_not_found_under": str(extract_root)}
    session_root = session_root_candidates[0]
else:
    session_root = input_path

images_dir = next((p for p in session_root.rglob("images") if p.is_dir()), None)
assert images_dir is not None, {"images_dir_not_found_under": str(session_root)}
image_paths = sorted(list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpeg")))
assert image_paths, {"images_not_found": str(images_dir)}

sample_images = [str(p) for p in image_paths[: min(60, len(image_paths))]]
session_id = selected_doc["session_id"]
probe_dir = results_root / f"{session_id}_da3giant_infergs_probe_v01"
probe_dir.mkdir(parents=True, exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = DepthAnything3(model_name="da3-giant").to(device)
inference_sig = str(inspect.signature(model.inference))

summary = {
    "session_id": session_id,
    "device": device,
    "probe_dir": str(probe_dir),
    "sample_count": len(sample_images),
    "inference_sig": inference_sig,
    "infer_gs": True,
    "export_format": "npz-glb-gs_ply-gs_video",
}

try:
    outputs = model.inference(
        image=sample_images,
        infer_gs=True,
        process_res=504,
        export_dir=str(probe_dir),
        export_format="npz-glb-gs_ply-gs_video",
    )
    summary["infer_call"] = "ok"
    summary["output_type"] = type(outputs).__name__
except Exception as e:
    summary["infer_call"] = "error"
    summary["error_type"] = type(e).__name__
    summary["error_message"] = str(e)
    summary["traceback_tail"] = traceback.format_exc().splitlines()[-20:]

exported = []
for p in sorted(probe_dir.rglob("*")):
    if p.is_file():
        exported.append(str(p))
summary["exported_files"] = exported

summary_path = probe_dir / "step9g_giant_infergs_summary.json"
summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "summary_path": str(summary_path),
    "infer_call": summary["infer_call"],
    "sample_count": summary["sample_count"],
    "exported_file_count": len(exported),
    "probe_dir": str(probe_dir),
}, indent=2, ensure_ascii=False))
for item in exported[:40]:
    print(item)
if summary["infer_call"] != "ok":
    print(json.dumps({
        "error_type": summary.get("error_type"),
        "error_message": summary.get("error_message"),
    }, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 9g giant infer_gs inference-signature fix res
[INFO ] using SwiGLU layer as FFN
[INFO ] Processed Images Done taking 0.08628129959106445 seconds. Shape:  torch.Size([26, 3, 378, 504])
[INFO ] Selecting reference view using strategy: saddle_balanced
{
  "summary_path": "/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/step9g_giant_infergs_summary.json",
  "infer_call": "error",
  "sample_count": 26,
  "exported_file_count": 2,
  "probe_dir": "/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01"
}
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/step9e_giant_infergs_summary.json
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/step9f_giant_infergs_summary.json
{
  "error_type": "NameError",
  "error_message": "name 'matrix_to_angles' is not defined"
}
```

# codex v67

```text
## 2026-03-31 v67 Step 9h install e3nn and retry giant infer_gs

- 解釈:
  - `Step 9g` では `da3-giant` 本体は実行され、failure は Gaussian branch 内で起きている。
  - 直前 warning の `Dependency 'e3nn' not found` と、今回の `matrix_to_angles` 未定義は整合する。
- 目的:
  - `e3nn` を追加 install し、同じ `da3-giant + infer_gs=True` を retry する。
  - これで `gs_ply` / `gs_video` export が進むか確認する。
```

```python
# Step 9h install e3nn and retry giant infer_gs
from pathlib import Path
import json
import shutil
import zipfile
import sys
import traceback
import subprocess

import torch

def run(cmd):
    print("RUN", " ".join(cmd))
    subprocess.run(cmd, check=True)

run(["python", "-m", "pip", "install", "--quiet", "e3nn"])

repo_root = Path("/content/Depth-Anything-3")
assert repo_root.exists(), {"repo_not_found": str(repo_root)}
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from depth_anything_3.api import DepthAnything3

selected_doc_path = Path("/content/runbook_selected_input.json")
assert selected_doc_path.exists(), {"selected_doc_not_found": str(selected_doc_path)}
selected_doc = json.loads(selected_doc_path.read_text(encoding="utf-8"))

input_path = Path(selected_doc["path"])
results_root = Path(selected_doc["results_root"])
assert input_path.exists(), {"input_not_found": str(input_path)}
results_root.mkdir(parents=True, exist_ok=True)

extract_root = Path("/content/trajectreview_input")
if extract_root.exists():
    shutil.rmtree(extract_root)
extract_root.mkdir(parents=True, exist_ok=True)

if input_path.is_file() and input_path.suffix.lower() == ".zip":
    with zipfile.ZipFile(input_path, "r") as zf:
        zf.extractall(extract_root)
    session_root_candidates = [p.parent for p in extract_root.rglob("session_package.json")]
    assert session_root_candidates, {"session_package_not_found_under": str(extract_root)}
    session_root = session_root_candidates[0]
else:
    session_root = input_path

images_dir = next((p for p in session_root.rglob("images") if p.is_dir()), None)
assert images_dir is not None, {"images_dir_not_found_under": str(session_root)}
image_paths = sorted(list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpeg")))
assert image_paths, {"images_not_found": str(images_dir)}

sample_images = [str(p) for p in image_paths[: min(60, len(image_paths))]]
session_id = selected_doc["session_id"]
probe_dir = results_root / f"{session_id}_da3giant_infergs_probe_v01"
probe_dir.mkdir(parents=True, exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
summary = {
    "session_id": session_id,
    "device": device,
    "probe_dir": str(probe_dir),
    "sample_count": len(sample_images),
    "infer_gs": True,
    "export_format": "npz-glb-gs_ply-gs_video",
}

try:
    model = DepthAnything3(model_name="da3-giant").to(device)
    outputs = model.inference(
        image=sample_images,
        infer_gs=True,
        process_res=504,
        export_dir=str(probe_dir),
        export_format="npz-glb-gs_ply-gs_video",
    )
    summary["infer_call"] = "ok"
    summary["output_type"] = type(outputs).__name__
except Exception as e:
    summary["infer_call"] = "error"
    summary["error_type"] = type(e).__name__
    summary["error_message"] = str(e)
    summary["traceback_tail"] = traceback.format_exc().splitlines()[-20:]

exported = []
for p in sorted(probe_dir.rglob("*")):
    if p.is_file():
        exported.append(str(p))
summary["exported_files"] = exported

summary_path = probe_dir / "step9h_giant_infergs_summary.json"
summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "summary_path": str(summary_path),
    "infer_call": summary["infer_call"],
    "sample_count": summary["sample_count"],
    "exported_file_count": len(exported),
    "probe_dir": str(probe_dir),
}, indent=2, ensure_ascii=False))
for item in exported[:40]:
    print(item)
if summary["infer_call"] != "ok":
    print(json.dumps({
        "error_type": summary.get("error_type"),
        "error_message": summary.get("error_message"),
    }, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 9h install e3nn and retry giant infer_gs res
RUN python -m pip install --quiet e3nn
[INFO ] using SwiGLU layer as FFN
[INFO ] Processed Images Done taking 0.08308768272399902 seconds. Shape:  torch.Size([26, 3, 378, 504])
[INFO ] Selecting reference view using strategy: saddle_balanced
{
  "summary_path": "/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/step9h_giant_infergs_summary.json",
  "infer_call": "error",
  "sample_count": 26,
  "exported_file_count": 3,
  "probe_dir": "/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01"
}
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/step9e_giant_infergs_summary.json
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/step9f_giant_infergs_summary.json
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/step9g_giant_infergs_summary.json
{
  "error_type": "NameError",
  "error_message": "name 'matrix_to_angles' is not defined"
}
```

# codex v68

```text
## 2026-03-31 v68 Step 9i matrix_to_angles source diagnostic

- 判定:
  - `e3nn` install 後も `matrix_to_angles` 未定義のままなので、dependency 不足ではなく repo 側の import / symbol 解決不整合の可能性が高い。
- 目的:
  - `matrix_to_angles` を参照している source file と、その file の import / definition 状態を特定する。
  - 次に patch なしで回避できるか、repo local patch が要るかを切り分ける。
```

```python
# Step 9i matrix_to_angles source diagnostic
from pathlib import Path
import json

repo_root = Path("/content/Depth-Anything-3")
assert repo_root.exists(), {"repo_not_found": str(repo_root)}

hits = []
definitions = []
for path in repo_root.rglob("*.py"):
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        continue
    for lineno, line in enumerate(lines, start=1):
        if "matrix_to_angles" in line:
            hits.append({
                "file": str(path),
                "line": lineno,
                "text": line.strip(),
            })
            if "def matrix_to_angles" in line or "matrix_to_angles =" in line or "import matrix_to_angles" in line or "from" in line:
                definitions.append({
                    "file": str(path),
                    "line": lineno,
                    "text": line.strip(),
                })

context = []
for item in hits[:10]:
    path = Path(item["file"])
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    start = max(0, item["line"] - 6)
    end = min(len(lines), item["line"] + 6)
    context.append({
        "file": item["file"],
        "line": item["line"],
        "snippet": [{"line": i + 1, "text": lines[i]} for i in range(start, end)],
    })

summary = {
    "repo_root": str(repo_root),
    "hit_count": len(hits),
    "hits_head": hits[:40],
    "definitions_head": definitions[:20],
    "context": context,
}

probe_path = Path("/content/mrl9_matrix_to_angles_probe.json")
probe_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "probe_path": str(probe_path),
    "hit_count": len(hits),
    "definition_count": len(definitions),
}, indent=2, ensure_ascii=False))
for item in hits[:20]:
    print(f"{item['file']}:{item['line']}: {item['text']}")
```

# admin

```text
# Step 9i matrix_to_angles source diagnostic res
{
  "probe_path": "/content/mrl9_matrix_to_angles_probe.json",
  "hit_count": 2,
  "definition_count": 1
}
/content/Depth-Anything-3/src/depth_anything_3/utils/sh_helpers.py:20: from e3nn.o3 import matrix_to_angles, wigner_D
/content/Depth-Anything-3/src/depth_anything_3/utils/sh_helpers.py:76: alpha, beta, gamma = matrix_to_angles(permuted_rotations_so3)

```

# codex v69

```text
## 2026-03-31 v69 Step 9j reload after e3nn install

- 確定したこと:
  - `matrix_to_angles` 自体は source にあり、`sh_helpers.py` で `from e3nn.o3 import matrix_to_angles, wigner_D` している。
  - にもかかわらず実行時に未定義なのは、`e3nn` install 前に `depth_anything_3` を import した影響で、module 側が stale import 状態の可能性が高い。
- 目的:
  - Python process を再起動せずに、`depth_anything_3` 関連 module を `sys.modules` から落として再 import し、`da3-giant + infer_gs=True` を retry する。
  - これで通れば、runbook 側は `e3nn` install を `DepthAnything3` import 前へ移すだけでよい。
```

```python
# Step 9j reload after e3nn install
from pathlib import Path
import json
import shutil
import zipfile
import sys
import traceback
import subprocess
import importlib

import torch

def run(cmd):
    print("RUN", " ".join(cmd))
    subprocess.run(cmd, check=True)

run(["python", "-m", "pip", "install", "--quiet", "e3nn"])

for name in list(sys.modules.keys()):
    if name == "depth_anything_3" or name.startswith("depth_anything_3."):
        del sys.modules[name]
importlib.invalidate_caches()

repo_root = Path("/content/Depth-Anything-3")
assert repo_root.exists(), {"repo_not_found": str(repo_root)}
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

import e3nn
from e3nn.o3 import matrix_to_angles
from depth_anything_3.api import DepthAnything3

selected_doc_path = Path("/content/runbook_selected_input.json")
assert selected_doc_path.exists(), {"selected_doc_not_found": str(selected_doc_path)}
selected_doc = json.loads(selected_doc_path.read_text(encoding="utf-8"))

input_path = Path(selected_doc["path"])
results_root = Path(selected_doc["results_root"])
assert input_path.exists(), {"input_not_found": str(input_path)}
results_root.mkdir(parents=True, exist_ok=True)

extract_root = Path("/content/trajectreview_input")
if extract_root.exists():
    shutil.rmtree(extract_root)
extract_root.mkdir(parents=True, exist_ok=True)

if input_path.is_file() and input_path.suffix.lower() == ".zip":
    with zipfile.ZipFile(input_path, "r") as zf:
        zf.extractall(extract_root)
    session_root_candidates = [p.parent for p in extract_root.rglob("session_package.json")]
    assert session_root_candidates, {"session_package_not_found_under": str(extract_root)}
    session_root = session_root_candidates[0]
else:
    session_root = input_path

images_dir = next((p for p in session_root.rglob("images") if p.is_dir()), None)
assert images_dir is not None, {"images_dir_not_found_under": str(session_root)}
image_paths = sorted(list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpeg")))
assert image_paths, {"images_not_found": str(images_dir)}

sample_images = [str(p) for p in image_paths[: min(60, len(image_paths))]]
session_id = selected_doc["session_id"]
probe_dir = results_root / f"{session_id}_da3giant_infergs_probe_v01"
probe_dir.mkdir(parents=True, exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
summary = {
    "session_id": session_id,
    "device": device,
    "probe_dir": str(probe_dir),
    "sample_count": len(sample_images),
    "infer_gs": True,
    "export_format": "npz-glb-gs_ply-gs_video",
    "e3nn_version": getattr(e3nn, "__version__", "unknown"),
    "matrix_to_angles_import_ok": callable(matrix_to_angles),
}

try:
    model = DepthAnything3(model_name="da3-giant").to(device)
    outputs = model.inference(
        image=sample_images,
        infer_gs=True,
        process_res=504,
        export_dir=str(probe_dir),
        export_format="npz-glb-gs_ply-gs_video",
    )
    summary["infer_call"] = "ok"
    summary["output_type"] = type(outputs).__name__
except Exception as e:
    summary["infer_call"] = "error"
    summary["error_type"] = type(e).__name__
    summary["error_message"] = str(e)
    summary["traceback_tail"] = traceback.format_exc().splitlines()[-20:]

exported = []
for p in sorted(probe_dir.rglob("*")):
    if p.is_file():
        exported.append(str(p))
summary["exported_files"] = exported

summary_path = probe_dir / "step9j_giant_infergs_summary.json"
summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "summary_path": str(summary_path),
    "infer_call": summary["infer_call"],
    "sample_count": summary["sample_count"],
    "exported_file_count": len(exported),
    "probe_dir": str(probe_dir),
    "e3nn_version": summary["e3nn_version"],
    "matrix_to_angles_import_ok": summary["matrix_to_angles_import_ok"],
}, indent=2, ensure_ascii=False))
for item in exported[:40]:
    print(item)
if summary["infer_call"] != "ok":
    print(json.dumps({
        "error_type": summary.get("error_type"),
        "error_message": summary.get("error_message"),
    }, indent=2, ensure_ascii=False))
```

# admin

```text
# Step 9j reload after e3nn install res
RUN python -m pip install --quiet e3nn
Error registering eval resolver: resolver 'eval' is already registered
[INFO ] using SwiGLU layer as FFN
[INFO ] Processed Images Done taking 0.08770465850830078 seconds. Shape:  torch.Size([26, 3, 378, 504])
[INFO ] Selecting reference view using strategy: saddle_balanced
[INFO ] Model Forward Pass Done. Time: 5.5808165073394775 seconds
[INFO ] Conversion to Prediction Done. Time: 0.008238792419433594 seconds
[INFO ] conf_thresh_percentile: 40.0
[INFO ] num max points: 1000000
[INFO ] Exporting to GLB with num_max_points: 1000000
WARNING:py.warnings:/content/Depth-Anything-3/src/depth_anything_3/utils/layout_helpers.py:116: UserWarning: Using a non-tuple sequence for multidimensional indexing is deprecated and will be changed in pytorch 2.9; use x[tuple(seq)] instead of x[seq]. In pytorch 2.9 this will be interpreted as tensor index, x[torch.tensor(seq)], which will result either in an error or a different result (Triggered internally at /pytorch/torch/csrc/autograd/python_variable_indexing.cpp:357.)
  result[selector] = overlay

Moviepy - Building video /content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/gs_video/0000_extend.mp4.
Moviepy - Writing video /content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/gs_video/0000_extend.mp4

Moviepy - Done !
Moviepy - video ready /content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/gs_video/0000_extend.mp4
[INFO ] Export Results Done. Time: 24.24264168739319 seconds
{
  "summary_path": "/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/step9j_giant_infergs_summary.json",
  "infer_call": "ok",
  "sample_count": 26,
  "exported_file_count": 35,
  "probe_dir": "/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01",
  "e3nn_version": "0.6.0",
  "matrix_to_angles_import_ok": true
}
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0000.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0001.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0002.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0003.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0004.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0005.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0006.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0007.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0008.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0009.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0010.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0011.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0012.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0013.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0014.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0015.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0016.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0017.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0018.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0019.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0020.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0021.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0022.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0023.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0024.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/depth_vis/0025.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/exports/npz/results.npz
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/gs_ply/0000.ply
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/gs_video/0000_extend.mp4
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/scene.glb
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/scene.jpg
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/step9e_giant_infergs_summary.json
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/step9f_giant_infergs_summary.json
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/step9g_giant_infergs_summary.json
/content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/step9h_giant_infergs_summary.json

```






# admin

RUN python -m pip install --quiet e3nn
[INFO ] using SwiGLU layer as FFN
[INFO ] Processed Images Done taking 0.08192300796508789 seconds. Shape:  torch.Size([26, 3, 378, 504])
[INFO ] Selecting reference view using strategy: saddle_balanced
[INFO ] Model Forward Pass Done. Time: 5.419279336929321 seconds
[INFO ] Conversion to Prediction Done. Time: 0.008611917495727539 seconds
[INFO ] conf_thresh_percentile: 40.0
[INFO ] num max points: 1000000
[INFO ] Exporting to GLB with num_max_points: 1000000
[ERROR] No valid depth values found. Reason: quantile() input tensor must be non-empty
WARNING:py.warnings:/content/Depth-Anything-3/src/depth_anything_3/utils/layout_helpers.py:116: UserWarning: Using a non-tuple sequence for multidimensional indexing is deprecated and will be changed in pytorch 2.9; use x[tuple(seq)] instead of x[seq]. In pytorch 2.9 this will be interpreted as tensor index, x[torch.tensor(seq)], which will result either in an error or a different result (Triggered internally at /pytorch/torch/csrc/autograd/python_variable_indexing.cpp:357.)
  result[selector] = overlay

Moviepy - Building video /content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/gs_video/0000_extend.mp4.
Moviepy - Writing video /content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/gs_video/0000_extend.mp4

                                                               Moviepy - Done !
Moviepy - video ready /content/drive/MyDrive/trajectreview/modeling/trajectreview-correcting-session-20260331-034831_da3giant_infergs_probe_v01/gs_video/0000_extend.mp4
[INFO ] Export Results Done. Time: 22.63803482055664 seconds

# codex v70

- `correcting` 側の canonical image を `90度右回転` 済み upright JPEG とする前提で、main runbook pair を刷新した。
- `MRL-10 Block 1` は image pixel を再回転せず、実画像寸法と `imageIntrinsics` を照合して legacy session のみ `K` を upright 基準へ補正する。
- 新規 manifest は `orientation_summary.json` を追加し、`input_frame_manifest.csv`、`k_resize_check.csv`、`MetricLarge` / `Giant` の `export_summary.json` に同じ orientation policy を残す。
- `MRL-11` は単独 route ではなく `MRL-10` へ吸収する方針へ整理した。

# admin

```text
# MRL-10 upright route res

```

# codex v71

- `MRL-10 mRL-10.4` の採用方針を `pose-aware alignment 維持 + owner_record ベース merge` に更新した。
- `PCA 1軸 keep` と terminal `all keep fallback` は runbook 正本から外し、各 Gaussian を `top-k` frame に対する `distance + direction + blur_penalty + index_penalty` score で `owner_record_index` へ帰属させる。
- keep 条件は `owner_record_index ∈ adopted_record_set(chunk)` に固定し、`keep_zero_chunk` は hard error とする。
- 追加証跡は `vertex_assignment_summary.csv`、`owner_record_histogram.csv`、`chunk_assignment_summary.csv`、`merge_warning_summary.json`、`chunk_transform_quality.csv` とし、`Block 6` bundle で Drive visible dir / Drive zip / local visible dir / local zip に同梱する。
- rollback point は branch `codex/mrl10-merge-baseline-20260404` を使う。

# codex v72

- `#10-1` で `chunk_0001_00012_00029` が `keep_zero_chunk` になった原因は、owner 候補 frame を chunk 外まで広げた結果、overlap chunk の vertex が前後 chunk の record へ吸われ、当該 chunk の adopted tail へ 1 点も残らなかったためである。
- runbook の owner 推定は、候補 frame をまず当該 chunk の record 群だけに制限し、候補不足の時だけ `OWNER_RECORD_MARGIN` 付き局所近傍、最後に全体 fallback を使う形へ変更した。
- 追加証跡として `owner_candidate_mode` を `vertex_assignment_summary.csv` と `chunk_keep_summary.csv` に残すようにした。これにより `chunk_only`、`chunk_with_margin`、`global_fallback` のどれで owner を決めたかを後から追える。

# codex v73

- Drive 容量圧迫を避けるため、`MRL-10` の保存 policy を `1 correcting session = 1 modeling directory` に固定した。
- Drive 正本は `probe_root` だけとし、`pipeline_root` を別名 directory や zip に複製しない。download 用 zip は必要時だけ `/content/...zip` に作る。
- `merge_summary.json` の `bundle_summary` は `drive_visible_dir = probe_root` を返し、Drive 側の確認先を 1 か所へ揃える。

# codex v74

- `#11` の最後に `cleanup_plan.json` と `cleanup_result.json` を追加し、final merge 完了後に yes/no で不可視生成物だけを削除できるようにした。
- Drive 側の削除対象は `chunk_runs/` に限定し、`probe_root` 配下の final / proof / manifest / merged 証跡は保持する。
- local 側の削除対象は `runbook_selected_input.json`、`runbook_paths.json`、`runbook_session_context.json`、`/content/trajectreview_input/`、local bundle zip である。

