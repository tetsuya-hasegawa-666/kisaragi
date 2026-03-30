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

2026-03-29 v24 cleanup for next use。

- `Step 1` から `Step 5p` までの持続事項は、次の正本へ反映済みです。
  - [da3_colab_clean_bootstrap_runbook.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\modeling\da3_colab_clean_bootstrap_runbook.md)
  - [ux-b2t-hypo.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\ux-b2t-hypo.md)
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
