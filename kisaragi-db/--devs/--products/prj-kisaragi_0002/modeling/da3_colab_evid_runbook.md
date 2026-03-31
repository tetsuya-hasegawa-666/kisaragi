# DA3 Colab Evid Runbook

## 文書の役割

- この文書は `prj-kisaragi_0002` の `DA3Metric-Large` `Colab` 実行について、fresh runtime から `DA3Metric-Large` による `3DGS` 系主空間モデル生成まで進めるための evid 正本 runbook とする。
- shared worklog の trial 往復をそのまま正本化せず、真に必要だった command と file 操作だけを抽出して保持する。
- `candidate` は現時点の最短候補、`adopted` は admin 実測で end-to-end 完了した `truly pass` 手順を示す。
- notebook 系 runbook の shared rule に従い、この file は `da3_colab_ref_runbook.md` と対で管理する。周辺説明、OK 条件、採用判断、補助情報は本 file に残し、貼り付け専用 block は companion 側にも同期する。

## blank workspace 前提

- この文書は、`Colab` の fresh runtime、つまり `/content/` 配下に前回の clone や install が残っていない状態から始める前提で書く。
- fresh runtime では `Google Drive` も未接続に戻るため、blank start のたびに最初の cell で `drive.mount("/content/drive", force_remount=True)` を必ず再実行する。
- admin は「前回の途中状態を引き継げる」と仮定せず、まずこの文書の `事前準備` と `準備確認` を実行する。
- 途中状態から再開するのは、bootstrap 自体の failure を切り分ける時だけに限定する。

## 運用 rule

- `Colab` runtime が揮発した時は、途中 patch の継ぎ足しより、この runbook の先頭からやり直すことを既定とする。
- shared worklog に新しい回避策が出た時は、この文書へ昇格が必要かを同じ task 内で判断する。
- `truly pass` と表現してよいのは、fresh runtime からこの runbook の `adopted` 手順で end-to-end 完了した時だけとする。
- ただし、bootstrap 仕様の未確定点を詰めている途中は、現在の runtime を維持したまま blocker を 1 件ずつ解消し、その結果をこの文書へ反映してよい。

## 実行案内

- この runbook は notebook 全体の `Run all` を前提にしない。
- 実行順は「上から順に」であり、`準備確認 3` の widget 選択だけ admin の手操作を挟む。
- 実施順は次の 3 block として扱う。
  - `A`: `準備確認 1` から `準備確認 2`
  - `B`: `準備確認 3` で input を 1 件選び、`selected input を保存` を押す
  - `C`: `準備確認 4` 以降を上から順に実行する
- `selected input` 未保存のまま `Step 1` 以降へ進んではならない。
- `Run all` が許容できるのは、将来 widget 選択を不要にする完全自動化へ切り替わった後だけとする。

## 実測済み運用

- `2026-03-31` admin 実測では、`準備確認 3` で widget から `[2] trajectreview-correcting-session-20260331-034831 [zip]` を選択した後、`Step 2` から `Step 4.5`、さらに `MRL-7 adopted one-block` まで成功した。
- 同日の別実測では、この session の `frame_pose_index.csv` が `image_file_name` 列を持ちながら全件空でも、`frame_index` 昇順と `images/` 実 file 列挙から `frame_name` を導出する schema 吸収で `MRL-7 adopted one-block` が通った。
- この時点の採用運用は「widget 選択を 1 回挟んでから、残りを上から順に流す」である。
- よって現時点の canonical 実行パターンは `Run all` ではなく、「選択介入ありの順次実行」である。

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

### 準備確認 2: Drive 上の入力候補を探索する

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

OK 条件:

- `scan_root_exists True` が少なくとも 1 件ある
- `candidate_count >= 1`
- `results_root` が writable な `MyDrive/trajectreview/modeling` または `trajectreview/modeling` を指す
- 同じ session zip が `shortcut-targets-by-id` と `MyDrive` の 2 経路で重複表示されない
- 使いたい session zip または session folder が index 付きで列挙される

NG 時の扱い:

- `scan_root_exists` がすべて `False` の時は、blank runtime で `Drive` 再接続前の可能性が高い。`準備確認 1` を再実行してから、この cell をやり直す。
- `scan_root_exists` は `True` だが `candidate_count = 0` の時は、その Drive 配下に対象 zip または `session_package.json` がまだ置かれていない。
- folder id `12jqKG1d7JEsFwFlqzHDdaAf7-HRdBvFT` は参照 link として見えても、直下で `mkdir` が通らない runtime がある。そのため runbook 正本では `results_root` の writable 先を `MyDrive/trajectreview/modeling` へ寄せる。

### 準備確認 3: 今回使う入力を画面で 1 件選ぶ

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

OK 条件:

- dropdown で候補を切り替えられる
- `selected input を保存` 後に `selected_exists True` が出る
- `path` が今回使う session zip または session folder を指している

### 準備確認 4: 選択結果の存在確認

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

OK 条件:

- `selected_path_exists True`
- `results_root_parent_exists True`

### 準備確認 5: blank workspace であることの確認

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

### install 2: DA3 import と export lazy-path に必要な custom dependency

```python
import subprocess

subprocess.run(
    ["python", "-m", "pip", "install", "--quiet", "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile", "trimesh"],
    check=True,
)
print("custom_dependency_install_ok")
```

### install 3: `3DGS` smoke 用 `gsplat`

```python
import subprocess

subprocess.run(
    ["python", "-m", "pip", "install", "--quiet", "gsplat"],
    check=True,
)
print("gsplat_install_ok")
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
- その前段として、Drive 上の任意 session zip または session folder を `Colab` 上の script だけで選び、後続 block が同じ selected input を参照できるようにする。

### 前提

- `事前準備` と `準備確認` が済んでいる
- `/content/runbook_selected_input.json` に今回使う入力が保存されている
- 結果出力先は、選択した `session_id` に応じて `trajectreview/modeling/<session_id>_da3_smoke_v24/` を使う

### Step 1: session zip を unzip して `session_root` を正規化する

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
    dest_root = extract_root / selected_path.name
    shutil.copytree(selected_path, dest_root)

pkg_hits = sorted(extract_root.rglob("session_package.json"))
assert pkg_hits, f"session_package.json not found under {extract_root}"
session_pkg = next((p for p in pkg_hits if p.parent.name == "trajectreview"), pkg_hits[0])

session_root = session_pkg.parent
session_outer = session_root.parent
images_dir = session_root / "images"
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

print("selected_kind", selected_kind)
print("selected_path", selected_path)
print("session_root_exists", session_root.exists(), session_root)
print("images_dir_exists", images_dir.exists(), images_dir)
files = sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.jpeg"))
print("image_count", len(files))
if files:
    print("first_image", files[0])
print("context_path", "/content/runbook_session_context.json")
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

context = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
SESSION_ROOT = Path(context["session_root"])
OUTPUT_ROOT = Path(context["da3_smoke_output_root"])
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
import json

context = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
SESSION_ROOT = Path(context["session_root"])
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

context = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
SESSION_ROOT = Path(context["session_root"])
SESSION_BUNDLE_ROOT = SESSION_ROOT.parent
OUTPUT_ROOT = Path(context["da3_smoke_output_root"])
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

context = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
SESSION_ROOT = Path(context["session_root"])
SESSION_BUNDLE_ROOT = SESSION_ROOT.parent
OUTPUT_ROOT = Path(context["da3_smoke_output_root"])
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
import json
import shutil

context = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
OUTPUT_ROOT = Path(context["da3_smoke_output_root"])

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

## `MRL-7` adopted one-block

### 位置づけ

- この節は、`mRL-7.1` と `mRL-7.2` を `p-done` にした最小かつ確実な実行 block をまとめる。
- ただし、ここに至るまでの step 分割による検討痕跡は重要なので、上の `Step 1` から `Step 5` は削除せず残す。
- 次回からの再実行は、この節の 1 block を優先し、問題が出た時だけ上の step 分割へ戻る。

### 前提

- `事前準備` と `準備確認` が済んでいる
- `/content/runbook_selected_input.json` に今回使う入力が保存されている
- `Step 1` から `Step 4.5` が通っている
- `probe_dir` は選択した `session_id` に応じて `trajectreview/modeling/<session_id>_da3_multiframe_probe_v01/` を使う

### 目的

- `mRL-7.1`
  - multi-frame window 選定
  - sampled frame depth batch
  - world fusion
  - preview / closeout
- `mRL-7.2`
  - gaussian parameter 初期化
  - `1 step` probe
  - `20 step` short optimization
  - render 改善確認用 artifact 保存

### adopted block

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

### この block の到達 artifact

- `mrl7_window_probe.json`
- `depth_batch_manifest.json`
- `world_points_multiframe.npy`
- `world_points_multiframe.ply`
- `world_points_multiframe_preview.png`
- `world_fusion_summary.json`
- `mrl7_closeout_summary.json`
- `gaussian_params_init.pt`
- `gaussian_params_optim20.pt`
- `gaussian_render_init.png`
- `gaussian_render_optim20.png`
- `gaussian_optim20_summary.json`

### この block の成功判定

- `window_span_sec` が出る
- `sample_frame_count >= 1`
- `processed_frames >= 1`
- `total_points >= 1`
- `loss_init` と `loss_final` が出る
- `loss_final < loss_init`
- `world_points_multiframe.ply` が保存される
- `gaussian_params_optim20.pt` が保存される
- `gaussian_render_optim20.png` が保存される

### 拡張実績

- 上の adopted block は `mRL-7.1` と `mRL-7.2` を `p-done` にした最小 path なので、runbook 正本では `20 step` を canonical とする。
- 同じ route を追加で伸ばす拡張実績として、`500 step` と `2500 step` も確認済みである。
- 同じ route を中間長さで追加学習する時は、下の `1000 step` block を使ってよい。
- `2500 step` 実績では、`loss_init = 0.18226878345012665` から `loss_final = 0.009165632538497448` まで低下し、`gaussian_render_optim2500.png` は取得背景にかなり近い構図まで改善した。
- これらの拡張実績は、最小 runbook を置き換えるものではなく、後続 `MRL-**` の optimization 強化 evidence として扱う。

### `1000 step` 追加学習 block

- 用途:
  - `20 step` canonical 実行後に、同じ runtime でそのまま gaussian optimization を `1000 step` まで伸ばしたい時に使う。
  - 前提として、上の adopted block が通っており、`means`、`scales`、`quats`、`opacities`、`colors`、`target`、`world_dir`、`render_once()`、`save_png()` が同じ notebook runtime に残っていること。

```python
# gaussian optim 1000
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

OK 条件:

- `loss_init` と `loss_final` が出る
- 原則として `loss_final < loss_init`
- `gaussian_params_optim1000.pt` が保存される
- `gaussian_render_optim1000.png` が保存される
- `gaussian_optim1000_summary.json` が保存される

拡張 artifact:

- `gaussian_params_optim500.pt`
- `gaussian_render_optim500.png`
- `gaussian_optim500_summary.json`
- `gaussian_params_optim1000.pt`
- `gaussian_render_optim1000.png`
- `gaussian_optim1000_summary.json`
- `gaussian_params_optim2500.pt`
- `gaussian_render_optim2500.png`
- `gaussian_optim2500_summary.json`

### `MyDrive` 可視 folder への copy block

- 用途:
  - 既定では成果物は `modeling` 用 Drive folder へ直接保存する。
  - それとは別に、admin が `MyDrive` 直下の見やすい path へ複製したい時だけ、この block を使う。
- 保存先:
  - `/content/drive/MyDrive/trajectreview/modeling_visible/<session_id>/world_fusion_v01`
- 前提:
  - 上の adopted block が通っており、`world_dir` と `session_id` が同じ runtime に残っている。

```python
# copy artifacts to visible MyDrive folder
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

OK 条件:

- `visible_dir` が出る
- `copied_count >= 1`
- 少なくとも `world_points_multiframe.ply` または `gaussian_render_optim20.png` 以上が copy される
- Drive UI の `MyDrive/trajectreview/modeling_visible/...` から対象 file を確認できる
