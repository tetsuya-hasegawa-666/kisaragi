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

## 現在の status

- `candidate` はあり
- `adopted` はあり
- `2026-03-29` に admin 実測で `Step 1` から `Step 4` まで end-to-end 完了した
- 現在の次段は、single-frame bootstrap 成立を踏まえて `gsplat` import、world projection、実データによる `3DGS` 系主空間モデル生成を通し、その後に request 起点 UX、waiting ring、download URL、複数 frame / route 比較へ広げる点である
- `HF_TOKEN` warning は public model の download では optional であり、現段階の blocker ではない
- `gsplat` warning は single-frame bootstrap では blocker ではなかったが、今後の `3DGS` 系主空間モデル生成では import と実行可否を明示確認する必要がある
- `2026-03-29` の `Step 5b gsplat install probe` では、`Python 3.12` の `Colab` runtime 上で `pip install gsplat` が成功し、`gsplat 1.5.3` が `/usr/local/lib/python3.12/dist-packages` に入ることを確認した
- `2026-03-29` の `Step 5c` と `Step 5d` と `Step 5e` により、`gsplat 1.5.3` は import 可能で、`rasterization`、`rasterization_2dgs`、`fully_fused_projection` が callable として利用可能だと確認した
- `2026-03-29` の `Step 5f` から `Step 5j` により、bundle 実配置、`arcore_pose.jsonl` の実 path、pose / intrinsics payload、depth 1 点の world back-projection smoke test が成功した
- `2026-03-29` の `Step 5k` により、`DA3Metric-Large` depth と `ARCore pose` / intrinsics から主 `ARCore` 空間の point 群を `.npy` と `.ply` で保存できることを確認した
- `2026-03-29` の `Step 5l` により、`gsplat.rasterization` を `cuda` 上で呼び、`render_colors` と `render_alphas` を返せることを確認した
- `2026-03-29` の `Step 5m` により、`gsplat_render_smoke.png`、`gs_model_smoke.json`、`space_quality_smoke.json` を保存できることを確認した
- `2026-03-29` の `Step 5n` により、`space_package_smoke.json` を生成し、`gs_model` 候補 artifact と `quality` を `SpacePackage` 形へ接続できることを確認した
- `2026-03-29` の `Step 5o` により、`space_package.contract.json`、`space_quality.contract.json`、`gs_model.contract.json` を生成し、smoke artifact を contract 名へ寄せられることを確認した
- `2026-03-29` の `Step 5p` により、single-frame bootstrap から `3DGS` 系主空間モデル生成 smoke までの到達 artifact 一式がそろっていることを確認した
- 現在の次 block は `Candidate Bootstrap v1` の closeout を admin evidence と `MRL-12` closeout へ接続することだが、runbook の candidate 自体は `3DGS` 生成 smoke まで拡張可能な状態になった

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
run(["python", "-m", "pip", "install", "--quiet", "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile", "trimesh"])
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
- 現在の runbook では `DA3Metric-Large` の metric depth 推論を主目的にしているため、`gsplat` は必須 dependency に含めない。
- `MRL-12` の次段では、この warning を放置せず、`gsplat` import probe と実データ `3DGS` 生成 smoke test を shared worklog で詰める。

## 次段の shared worklog 運用

- `gsplat` import から実データ `3DGS` 系主空間モデル生成までの command block は、この runbookへ即断で長文化せず、まず [sharedlogs_da3-colab.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\sharedlogs_da3-colab.md) で `# codex v**` と `# admin` の往復で確定させる。
- Codex は 1 回につき 1 つの目的だけを持つ短い command block を shared worklog へ追記する。
- admin は block ごとの実行結果を、その block title を保ったまま `# admin` に貼り戻す。
- Codex は結果を読んで、次 block を出すか、runbook / 正本文書へ昇格させるかを判断する。
- shared worklog で成立した持続事項は、この runbook、[ux-b2t-hypo.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\ux-b2t-hypo.md)、必要なら admin evidence へ同じ task 内で反映する。

## 次段でやること

- `Step 5a`: `gsplat` import probe を通し、runtime 上で必要 package と import path を確定する。
- `Step 5b`: `gsplat` install probe を通し、`pip install gsplat` が current runtime で成立するかを確認する。
- `Step 5c`: install 後の `gsplat` import probe を通し、runtime 上で import path と version を確定する。
- `Step 5d`: `gsplat` の top-level symbol と submodule 一覧を確認し、使うべき import path を確定する。
- `Step 5e`: `rasterization`、`rasterization_2dgs`、`fully_fused_projection` の signature を確認し、最小呼び出し形を確定する。
- `Step 5f`: `session_package.json`、`arcore_pose.jsonl`、`frame_pose_index.csv`、image 群から、`DA3Metric-Large` depth と `ARCore pose` を同一 frame 集合へ揃える。
- `Step 5g`: 1 frame の pose / intrinsics payload を確認し、world projection の最小入力 shape を確定する。
- `Step 5h`: world back-projection smoke test を通し、depth 1 点を主 `ARCore` 空間へ戻せることを確認する。
- `Step 5i`: depth から point 群を書き出す point export probe を通し、主 `ARCore` 空間の点群を保存できることを確認する。
- `Step 5j`: point 群または `DA3Metric-Large` 出力を入力として、実データ由来の最小 `3DGS` 系主空間モデル生成を試す。
- `Step 5k`: `gsplat.rasterization` を 1 view で実行し、最小 render が返ることを確認する。
- `Step 5l`: rendered image、`gs_model` 候補 artifact、`space_quality.json` の最小記録を保存する。
- `Step 5m`: `SpacePackage` への組み込み方を確定する。
- `Step 5n`: smoke artifact を正式 contract 名へ寄せ、handoff で読める path / file 名へ整理する。
- `Step 5o`: 上記が 1 route で通ったら、runbook の `candidate` を `3DGS` 生成まで拡張する。

## shared worklog へ出す command block の単位

- block 1: `gsplat` import だけを確認する probe
- block 2: 実 session から複数 frame を読み、depth 推論対象 frame を決める probe
- block 3: `ARCore pose` / intrinsics と depth の整列確認 probe
- block 4: world projection で point 群を書き出す probe
- block 5: 最小 `3DGS` 系主空間モデル生成 probe
- block 6: `gs_model`、`space_quality.json`、`SpacePackage` 保存 probe

## shared worklog に貼る時の template

- Codex は次の形で block を出す。

```text
# codex

2026-03-29 v07 step-5a gsplat import probe。

- 目的: `gsplat` import 可否と version を確認する。
- 成功条件: import error が出ず、version または module path を取得できる。
- 失敗時の扱い: install 不足か path 問題かを切り分ける。

```python
# Step 5a gsplat import probe
...
```
```

- admin は次の形で返す。

```text
# admin

```text
# Step 5a gsplat import probe res
...
```
```

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

## Adopted Bootstrap

### Adopted Bootstrap v1

- 実施日: `2026-03-29`
- 実施者: `admin`
- 実行環境:
  - `Google Colab`
  - `T4`
  - `device = cuda`
- 採用理由:
  - blank workspace から `準備確認 1` から `Step 4` まで通った
  - `summary.json`、`depth_preview.png`、`depth_raw.npy` が生成された
  - `conf`、`intrinsics`、`extrinsics` は `None` 許容で end-to-end 完了した
- 採用手順:
  - 現時点では `Candidate Bootstrap v1` の手順をそのまま `Adopted Bootstrap v1` として採用する
- 実測 summary:
  - `image_path`: `/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000009.jpg`
  - `device`: `cuda`
  - `depth_shape`: `[378, 504]`
  - `conf_shape`: `null`
  - `intrinsics_shape`: `null`
  - `extrinsics_shape`: `null`
  - `depth_min`: `0.31544607877731323`
  - `depth_max`: `4.0310516357421875`

## Candidate 拡張状況

- `2026-03-29` 時点で、`Candidate Bootstrap v1` は single-frame depth bootstrap だけでなく、以下の `3DGS` 系主空間モデル生成 smoke まで到達済みである。
- 到達 artifact:
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
- この段階は `MRL-12` の `gs_model` 候補 artifact と `SpacePackage` smoke contract を作れることの candidate proof である。
- まだ admin evidence 正本と `MRL-12` closeout への反映は別途必要であり、この runbook 単独で `i-pass` を意味しない。
