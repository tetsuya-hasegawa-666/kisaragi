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
- 長い code と error は code block のまま貼る。
- shared rule 変更は `AGENTS.md`、project truth / plan / current 変更は `project-truth.md` と `ux-b2t-hypo.md`、gate 判定根拠は admin evidence へ別途反映する。

# codex

2026-03-29 移管時点の保持要約。

- 旧 `da3_colab_shared_worklog_20260329.md` は運用変更により廃止し、この file へ移管した。
- 既存の `COLMAP 4.0 + nerfstudio splatfacto` notebook は参考ひな形であり、`DA3Metric-Large` modeling の truth ではない。
- `DA3Metric-Large` の `Colab` 実装は greenfield として進めている。
- ここまでに `numpy` ABI 不整合、`pkg_resources`、`pygame`、`pycolmap`、`addict`、`evo` の import blocker は突破済みで、`Cell C` の import check は通過した。
- 現在の blocker は code や依存ではなく、`Cell D` の `SESSION_ROOT` が placeholder のままで、実データの `images/` path を指していない点である。
- この要約は継続に必要な内容だけを残した retained digest であり、旧 log の全文再掲ではない。

# codex

2026-03-29 次に admin がやること。

- まず `Inspect Cell` を実行して、`/content/drive/MyDrive/trajectreview/input/` 配下の実 session folder 名を確認する。
- 実 session folder 名が分かったら、`Cell D` の `SESSION_ROOT` を実値へ置き換える。
- `SESSION_ROOT/images/` が存在し、画像枚数が 1 枚以上あることを確認してから 1 frame 推論を再実行する。

```python
# Inspect Cell
from pathlib import Path

root = Path("/content/drive/MyDrive/trajectreview/input")
print("root_exists", root.exists(), root)

if root.exists():
    for p in sorted(root.iterdir()):
        print(p.name, "dir" if p.is_dir() else "file")
```

```python
# images existence check
from pathlib import Path

SESSION_ROOT = Path("/content/drive/MyDrive/trajectreview/input/<ここを実session名へ置換>")
images_dir = SESSION_ROOT / "images"
print("session_root_exists", SESSION_ROOT.exists(), SESSION_ROOT)
print("images_dir_exists", images_dir.exists(), images_dir)
if images_dir.exists():
    files = sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.jpeg"))
    print("image_count", len(files))
    if files:
        print("first_image", files[0])
```

```python
# Cell D rerun
import json
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from depth_anything_3.api import DepthAnything3

SESSION_ROOT = Path("/content/drive/MyDrive/trajectreview/input/<ここを実session名へ置換>")
OUTPUT_ROOT = Path("/content/drive/MyDrive/trajectreview/results/da3_smoke_v7")
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

```
