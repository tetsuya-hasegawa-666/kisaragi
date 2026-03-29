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
# Inspect Cell res
root_exists False /content/drive/MyDrive/trajectreview/input
```

# codex

2026-03-29 v13。

- `root_exists False` なので、`/content/drive/MyDrive/trajectreview/input` という想定 path 自体が外れています。
- 現在の blocker は `session_root` 未設定より前段の「Google Drive 上の input root が別の場所にある」点です。
- 次は `MyDrive` 直下と `session_package.json` の所在を探索して、実 `session_root` 候補を特定します。

```python
# Drive root inspect v13
from pathlib import Path

drive_root = Path("/content/drive/MyDrive")
print("drive_root_exists", drive_root.exists(), drive_root)
if drive_root.exists():
    for p in sorted(drive_root.iterdir()):
        print(p.name, "dir" if p.is_dir() else "file")
```

```python
# Recursive session hint inspect v13
from pathlib import Path

drive_root = Path("/content/drive/MyDrive")
patterns = [
    "session_package.json",
    "camera_calibration_summary.json",
    "frame_pose_index.csv",
]

for pattern in patterns:
    found = list(drive_root.rglob(pattern))
    print("pattern", pattern, "count", len(found))
    for p in found[:10]:
        print(" ", p)
```

- `session_package.json` が見つかった folder が実 `session_root` 候補です。
- この 2 つの結果を最下部へ追記してください。こちらで `SESSION_ROOT` の実値を確定します。

# admin

```text
falseです、admin側の設定の問題かどうかも検討してください
```

# codex

2026-03-29 v14。

- はい、その可能性があります。ここでの `False` は code ではなく、admin 側の `Google Drive mount`、使用 account、または保存先想定の問題である可能性があります。
- 切り分けるべき候補は 3 つです。
  - `drive.mount('/content/drive')` が未実行、または mount 失敗
  - Colab で開いている Google account と、data を置いた Google Drive account が違う
  - data 自体がまだ Google Drive に置かれていない、または想定外の folder にある
- 次は path 探索ではなく、mount と account 側を先に確認します。

```python
# Drive mount state check v14
from pathlib import Path

paths = [
    Path("/content/drive"),
    Path("/content/drive/MyDrive"),
    Path("/content/drive/Shareddrives"),
]

for p in paths:
    print(p, p.exists(), p.is_dir() if p.exists() else None)
    if p.exists():
        try:
            children = list(p.iterdir())[:10]
            print(" children:", [c.name for c in children])
        except Exception as e:
            print(" children_error:", repr(e))
```

```python
# Remount if needed v14
from google.colab import drive
drive.mount('/content/drive', force_remount=True)
```

```python
# Post-remount quick check v14
from pathlib import Path

root = Path("/content/drive/MyDrive")
print("mydrive_exists", root.exists(), root)
if root.exists():
    for p in sorted(root.iterdir()):
        print(p.name, "dir" if p.is_dir() else "file")
```

- さらに admin 側で確認してほしいこと:
  - Colab 右上の account と、Drive に data を置いた account が同じか
  - `Google Drive` 上に session zip または session folder を本当に置いたか
  - `correcting` から転送した先が `マイドライブ` なのか、共有ドライブなのか
- 上の 3 cell の結果と、account / 保存先の確認結果を最下部へ追記してください。

# admin

```text
# Drive root inspect v13 res
drive_root_exists False /content/drive/MyDrive
```

# codex

2026-03-29 v15。

- `/content/drive/MyDrive` 自体が `False` なので、現段階では path 仮定ではなく `Drive mount` 自体が成立していない可能性が高いです。
- この場合、`session_root` 探索を続けても意味が薄いので、先に `drive.mount('/content/drive', force_remount=True)` を実行して mount を成立させる必要があります。
- したがって、いま優先すべき切り分けは次の順です。
  1. `drive.mount('/content/drive', force_remount=True)` の実行結果
  2. 実行後に `/content/drive/MyDrive` が `True` になるか
  3. それでも `False` なら account / browser auth 側の問題

```python
# Remount now v15
from google.colab import drive
drive.mount('/content/drive', force_remount=True)
```

```python
# Recheck after remount v15
from pathlib import Path

paths = [
    Path("/content/drive"),
    Path("/content/drive/MyDrive"),
    Path("/content/drive/Shareddrives"),
]

for p in paths:
    print(p, p.exists(), p.is_dir() if p.exists() else None)
    if p.exists():
        try:
            print(" children:", [c.name for c in list(p.iterdir())[:10]])
        except Exception as e:
            print(" children_error:", repr(e))
```

- もし remount 実行時に認証画面が出たら、その account が data を置いた Google account と同じか確認してください。
- remount 後の 2 cell の結果を最下部へ追記してください。

# admin

```text
# Remount now v15 res
Mounted at /content/drive
```

```text
# Recheck after remount v15 res
/content/drive True True
 children: ['MyDrive', '.shortcut-targets-by-id', '.Trash-0', '.Encrypted']
/content/drive/MyDrive True True
 children: ['SiMa.aiのフィジカルAI解説.gdoc', 'MCP技術の最先端と未来.gdoc', 'PVPフレームワークと開発ツール調査.gdoc', '作りたいものの本質を研究検討して定義するための情報構築.gdoc', '屋外で作業する人をリアルタイムに地図上に表現するシステム.gdoc', '抽象化した作りたいものについて（仮説の前提）.gdoc', '実現パターンの提示.gdoc', '現場地図条件追加.gdoc', 'Data_Correcting_System.zip', 'Colab Notebooks']
/content/drive/Shareddrives False None
```

# codex

2026-03-29 v16。

- `Drive mount` は成立しました。`/content/drive/MyDrive` も見えています。
- したがって、現在の blocker は mount ではなく、「実データが `MyDrive` のどこにあるか未特定」である点です。
- いま見えている候補は少なくとも 2 つです。
  - `Data_Correcting_System.zip`
  - `Colab Notebooks`
- 次は `session_package.json` を実際に含む path を特定します。まず zip か folder かを切り分けます。

```python
# Candidate inspect v16
from pathlib import Path

candidates = [
    Path("/content/drive/MyDrive/Data_Correcting_System.zip"),
    Path("/content/drive/MyDrive/Colab Notebooks"),
]

for p in candidates:
    print("path", p)
    print(" exists", p.exists())
    print(" is_file", p.is_file() if p.exists() else None)
    print(" is_dir", p.is_dir() if p.exists() else None)
```

```python
# Search session files in MyDrive v16
from pathlib import Path

drive_root = Path("/content/drive/MyDrive")
patterns = [
    "session_package.json",
    "camera_calibration_summary.json",
    "frame_pose_index.csv",
]

for pattern in patterns:
    found = list(drive_root.rglob(pattern))
    print("pattern", pattern, "count", len(found))
    for p in found[:20]:
        print(" ", p)
```

- `session_package.json` が見つかった folder が実 `session_root` 候補です。
- もし search が 0 件で、`Data_Correcting_System.zip` が存在するなら、次段はその zip の中身確認へ進みます。
- まずは上の 2 cell の結果を最下部へ追記してください。

# admin

```text
# Candidate inspect v16 res
path /content/drive/MyDrive/Data_Correcting_System.zip
 exists True
 is_file True
 is_dir False
path /content/drive/MyDrive/Colab Notebooks
 exists True
 is_file False
 is_dir True
```

# admin

```text
# Search session files in MyDrive v16 res
pattern session_package.json count 0
pattern camera_calibration_summary.json count 0
pattern frame_pose_index.csv count 0
```

# codex

2026-03-29 v17。

- `MyDrive` 直下では `session_package.json` が 0 件で、`Data_Correcting_System.zip` は実在しています。
- したがって、現時点の最有力仮説は「実データは zip 内にあり、まだ unzip / 正規化されていない」です。
- 次は zip の中身を確認して、`session_package.json` や `images/` が zip 内にあるかを見ます。

```python
# Zip inspect v17
from pathlib import Path
import zipfile

zip_path = Path("/content/drive/MyDrive/Data_Correcting_System.zip")
print("zip_exists", zip_path.exists(), zip_path)

with zipfile.ZipFile(zip_path, "r") as zf:
    names = zf.namelist()
    print("entry_count", len(names))
    for name in names[:100]:
        print(name)
```

```python
# Zip target search v17
from pathlib import Path
import zipfile

zip_path = Path("/content/drive/MyDrive/Data_Correcting_System.zip")
targets = [
    "session_package.json",
    "camera_calibration_summary.json",
    "frame_pose_index.csv",
    "/images/",
]

with zipfile.ZipFile(zip_path, "r") as zf:
    names = zf.namelist()
    for target in targets:
        hits = [name for name in names if target in name]
        print("target", target, "count", len(hits))
        for hit in hits[:20]:
            print(" ", hit)
```

- もし zip 内に `session_package.json` があるなら、次段はその zip を Colab 作業用 directory へ unzip して `session_root` を正規化します。
- まずは上の 2 cell の結果を返してください。

# admin

```text
# Zip inspect v17 res

```

# admin

```text
# Zip target search v17 res

```

# admin

```text
# Data_Correcting_System.zip note
Data_Correcting_System.zipは全く違う案件で置いたものですので違います
```

# codex

2026-03-29 v18。

- `Data_Correcting_System.zip` は無関係な file として除外します。こちらの候補選定が誤りでした。
- したがって、現在の探索対象は `MyDrive` 全体の中で `prj-kisaragi_0002` 実 data に関係する folder / zip / notebook 周辺です。
- 次は `Colab Notebooks` 配下と、`MyDrive` 全体から `trajectreview`、`session`、`camera_calibration_summary.json`、`frame_pose_index.csv` を手掛かりに再探索します。

```python
# Colab Notebooks inspect v18
from pathlib import Path

root = Path("/content/drive/MyDrive/Colab Notebooks")
print("exists", root.exists(), root)
if root.exists():
    for p in sorted(root.rglob("*")):
        print(p)
        if len(str(p)) > 0:
            pass
```

```python
# Broad hint search v18
from pathlib import Path

drive_root = Path("/content/drive/MyDrive")
hints = [
    "*trajectreview*",
    "*session*",
    "camera_calibration_summary.json",
    "frame_pose_index.csv",
    "session_package.json",
]

for hint in hints:
    found = list(drive_root.rglob(hint))
    print("hint", hint, "count", len(found))
    for p in found[:30]:
        print(" ", p)
```

- `session_package.json`、`camera_calibration_summary.json`、`frame_pose_index.csv` のどれかが見つかった path を最優先候補にします。
- `Colab Notebooks` 配下に zip や data folder があれば、それも候補です。
- 上の 2 cell の結果を返してください。

# admin

```text
# Colab Notebooks inspect v18 res

```

# admin

```text
# Broad hint search v18 res

```

# admin

```text
# Drive folder hint
マイドライブの
https://drive.google.com/drive/folders/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_?usp=sharing
ここにあります、見えていない可能性があります
```

# codex

2026-03-29 v19。

- その URL は重要な手掛かりです。
- こちらからは Google login redirect になり、folder 中身は直接確認できませんでした。したがって、いま切り分けるべきなのは「Colab で mount した `MyDrive` に shortcut として見えているか」「`共有アイテム` 側にだけあって `MyDrive` に入っていないか」です。
- `MyDrive` 直下に見えていないなら、次のどちらかの可能性が高いです。
  - その folder は `共有アイテム` にだけあり、`MyDrive` へショートカット追加されていない
  - mount している account と、その URL を持つ account が違う

```python
# Shortcut / shared root inspect v19
from pathlib import Path

paths = [
    Path("/content/drive/MyDrive"),
    Path("/content/drive/.shortcut-targets-by-id"),
]

for p in paths:
    print("path", p, "exists", p.exists())
    if p.exists():
        for child in list(p.iterdir())[:30]:
            print(" ", child)
```

```python
# Folder id search hint v19
from pathlib import Path

shortcut_root = Path("/content/drive/.shortcut-targets-by-id")
folder_id = "1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_"
print("shortcut_root_exists", shortcut_root.exists(), shortcut_root)

if shortcut_root.exists():
    for p in shortcut_root.rglob("*"):
        if folder_id in str(p):
            print("hit", p)
```

- admin 側の確認項目:
  - その URL の folder をブラウザで開いたとき、`マイドライブにショートカットを追加` 済みか
  - Colab で mount している Google account と、その URL を開ける Google account が同じか
- 上の 2 cell の結果と、account / shortcut の確認結果を最下部へ追記してください。

# admin

```text
# shortcut/account check res
ショートカットを追加し、アカウントも正しいことを確認しました
```

# codex

2026-03-29 v20。

- `マイドライブにショートカット追加` 済みで、account も正しいなら、次は Colab mount 上で `.shortcut-targets-by-id` 配下にその folder が見えるかを直接確認します。
- ここで見えれば、その実 path を `session_root` 候補として扱えます。

```python
# Shortcut root inspect v20
from pathlib import Path

root = Path("/content/drive/.shortcut-targets-by-id")
print("exists", root.exists(), root)
if root.exists():
    for p in sorted(root.iterdir()):
        print(p.name, "dir" if p.is_dir() else "file")
```

```python
# Folder id direct inspect v20
from pathlib import Path

folder_id = "1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_"
target = Path("/content/drive/.shortcut-targets-by-id") / folder_id
print("target_exists", target.exists(), target)
if target.exists():
    for p in sorted(target.rglob("*")):
        print(p)
```

- もし `target_exists True` なら、その配下に `session_package.json` や `images/` があるかを見て `SESSION_ROOT` を確定します。
- 上の 2 cell の結果を返してください。

# admin

```text
# Shortcut root inspect v20 res
exists True /content/drive/.shortcut-targets-by-id
```

# admin

```text
# Folder id direct inspect v20 res
target_exists True /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_
/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview
/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting
/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/session-20260328-103250.zip
/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/trajectreview-correcting-export.zip
/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results
/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v7

```

# codex

2026-03-29 v21。

- 実データの置き場は見えました。main root は次です。
  - `/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview`
- その下に `correcting/session-20260328-103250.zip` があるので、次はこの zip を Colab 作業用 directory に unzip して `session_root` を正規化します。
- `results/da3_smoke_v7` は既存結果置き場なので、入力は `correcting/session-20260328-103250.zip` を優先します。

```python
# Unzip session v21
from pathlib import Path
import zipfile
import shutil

zip_path = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/session-20260328-103250.zip")
extract_root = Path("/content/trajectreview_input")

if extract_root.exists():
    shutil.rmtree(extract_root)
extract_root.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(extract_root)

print("zip_exists", zip_path.exists(), zip_path)
print("extract_root", extract_root)
for p in sorted(extract_root.rglob("*")):
    print(p)
```

```python
# Detect session_root v21
from pathlib import Path

extract_root = Path("/content/trajectreview_input")
candidates = list(extract_root.rglob("session_package.json"))
print("session_package_count", len(candidates))
for p in candidates:
    print("session_package", p)
    print("session_root_candidate", p.parent)
```

```python
# Check images under detected session_root v21
from pathlib import Path

SESSION_ROOT = Path("/content/trajectreview_input/<ここを session_root_candidate に置換>")
images_dir = SESSION_ROOT / "images"
print("session_root_exists", SESSION_ROOT.exists(), SESSION_ROOT)
print("images_dir_exists", images_dir.exists(), images_dir)
if images_dir.exists():
    files = sorted(images_dir.glob("*.png")) + sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.jpeg"))
    print("image_count", len(files))
    if files:
        print("first_image", files[0])
```

- `session_package_count >= 1` で `images_dir_exists True`、`image_count >= 1` まで行けたら、次段は `Cell D` の `SESSION_ROOT` をその path に置き換えて再実行します。
- 上の 3 cell の結果を返してください。

# admin

```text
# Unzip session v21 res
zip_exists True /content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/correcting/session-20260328-103250.zip
extract_root /content/trajectreview_input
/content/trajectreview_input/session-20260328-103250
/content/trajectreview_input/session-20260328-103250/arcore_pose.jsonl
/content/trajectreview_input/session-20260328-103250/ble_scan.jsonl
/content/trajectreview_input/session-20260328-103250/gnss.csv
/content/trajectreview_input/session-20260328-103250/imu.csv
/content/trajectreview_input/session-20260328-103250/session_manifest.json
/content/trajectreview_input/session-20260328-103250/trajectreview
/content/trajectreview_input/session-20260328-103250/trajectreview/camera_calibration_summary.json
/content/trajectreview_input/session-20260328-103250/trajectreview/frame_pose_index.csv
/content/trajectreview_input/session-20260328-103250/trajectreview/images
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000009.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000012.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000013.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000014.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000021.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000022.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000028.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000031.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000037.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000040.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000041.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000045.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000048.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000050.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000051.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000055.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000058.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000060.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000061.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000068.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000070.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000071.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000076.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000080.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000082.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000083.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000087.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000090.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000092.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000093.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000097.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000099.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000101.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000103.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000104.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000107.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000111.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000113.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000114.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000119.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000122.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000123.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000127.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000129.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000131.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000133.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000137.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000140.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000142.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000143.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000147.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000150.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000152.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000153.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000157.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000159.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000161.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000163.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000167.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000171.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000172.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000176.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000179.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000181.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000182.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000186.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000189.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000191.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000192.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000196.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000199.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000200.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000202.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000206.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000209.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000211.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000215.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000217.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000220.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000221.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000225.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000228.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000230.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000234.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000237.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000239.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000240.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000244.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000247.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000249.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000250.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000254.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000257.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000259.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000260.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000264.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000267.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000269.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000270.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000274.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000276.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000278.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000280.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000283.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000286.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000289.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000290.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000293.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000297.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000299.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000300.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000304.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000306.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000309.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000310.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000314.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000316.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000318.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000320.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000324.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000326.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000328.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000330.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000331.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000335.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000337.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000340.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000344.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000347.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000349.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000350.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000354.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000356.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000359.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000363.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000366.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000368.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000369.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000373.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000375.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000377.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000379.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000380.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000384.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000386.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000388.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000390.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000391.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000395.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000398.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000400.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000405.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000408.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000413.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000415.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000417.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000423.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000425.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000431.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000433.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000434.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000440.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000442.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000449.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000453.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000457.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000459.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000465.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000469.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000470.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000477.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000479.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000480.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000485.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000487.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000489.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000500.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000503.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000508.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000511.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000517.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000520.jpg
/content/trajectreview_input/session-20260328-103250/trajectreview/input_readiness.json
/content/trajectreview_input/session-20260328-103250/trajectreview/member_identity_map.json
/content/trajectreview_input/session-20260328-103250/trajectreview/sensor_quality.json
/content/trajectreview_input/session-20260328-103250/trajectreview/session_package.json
/content/trajectreview_input/session-20260328-103250/trajectreview/space_handoff_manifest.json
/content/trajectreview_input/session-20260328-103250/video.mp4
/content/trajectreview_input/session-20260328-103250/video_events.jsonl
/content/trajectreview_input/session-20260328-103250/video_frame_timestamps.csv
```

# admin

```text
# Detect session_root v21 res
session_package_count 1
session_package /content/trajectreview_input/session-20260328-103250/trajectreview/session_package.json
session_root_candidate /content/trajectreview_input/session-20260328-103250/trajectreview
```

# admin

```text
# Check images under detected session_root v21 res
session_root_exists False /content/trajectreview_input/<ここを session_root_candidate に置換>
images_dir_exists False /content/trajectreview_input/<ここを session_root_candidate に置換>/images
```

# codex

2026-03-29 v22。

- `session_root_candidate` は確定しました。
  - `/content/trajectreview_input/session-20260328-103250/trajectreview`
- 直前の `False` は code 失敗ではなく、確認 cell の placeholder を実 path に置き換えていないことが原因です。
- 次は placeholder を実値へ置き換えて、`images/` 存在確認と `Cell D` 再実行を行います。

```python
# Check images under detected session_root v22
from pathlib import Path

SESSION_ROOT = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
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
# Cell D rerun v22
import json
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from depth_anything_3.api import DepthAnything3

SESSION_ROOT = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
OUTPUT_ROOT = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v22")
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

- `Check images under detected session_root v22` が通ったら、そのまま `Cell D rerun v22` を実行してください。
- `Cell D rerun v22` が落ちたら error 全文を返してください。

# admin

```text
# Check images under detected session_root v22 res
session_root_exists True /content/trajectreview_input/session-20260328-103250/trajectreview
images_dir_exists True /content/trajectreview_input/session-20260328-103250/trajectreview/images
image_count 182
first_image /content/trajectreview_input/session-20260328-103250/trajectreview/images/frame_000009.jpg
```

# admin

```text
# Cell D rerun v22 res
---------------------------------------------------------------------------
ModuleNotFoundError                       Traceback (most recent call last)
/tmp/ipykernel_29678/3642200570.py in <cell line: 0>()
      6 from PIL import Image
      7 import torch
----> 8 from depth_anything_3.api import DepthAnything3
      9 
     10 SESSION_ROOT = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")

ModuleNotFoundError: No module named 'depth_anything_3'

---------------------------------------------------------------------------
NOTE: If your import is failing due to a missing package, you can
manually install dependencies using either !pip or !apt.

To view examples of installing some common dependencies, click the
"Open Examples" button below.
---------------------------------------------------------------------------
```

# codex

2026-03-29 v23。

- `session_root` と `images/` は成立しました。
  - `session_root_exists True`
  - `images_dir_exists True`
  - `image_count 182`
- 現在の blocker は data ではなく、runtime 上で `depth_anything_3` module 解決が外れている点です。
- 次は install 全やり直しではなく、repo path を runtime に戻して import context を再確立します。

```python
# Reattach repo path and import check v23
import sys
from pathlib import Path

REPO_ROOT = Path("/content/Depth-Anything-3")
print("repo_exists", REPO_ROOT.exists(), REPO_ROOT)
assert REPO_ROOT.exists(), f"repo not found: {REPO_ROOT}"

repo_str = str(REPO_ROOT)
if repo_str not in sys.path:
    sys.path.insert(0, repo_str)

print("sys_path_head", sys.path[:5])

from depth_anything_3.api import DepthAnything3
print("import_ok", DepthAnything3)
```

```python
# Cell D rerun v23
import json
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from depth_anything_3.api import DepthAnything3

SESSION_ROOT = Path("/content/trajectreview_input/session-20260328-103250/trajectreview")
OUTPUT_ROOT = Path("/content/drive/.shortcut-targets-by-id/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_/trajectreview/results/da3_smoke_v23")
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

- `Reattach repo path and import check v23` が通ったら、そのまま `Cell D rerun v23` を実行してください。
- `repo_exists False` の場合は、その結果だけ返してください。そこで clone / patch の再投入へ切り替えます。
- `import` が別 error で落ちた場合は traceback 全文を返してください。

# admin

```text
# Reattach repo path and import check v23 res

```

# admin

```text
# Cell D rerun v23 res

```
