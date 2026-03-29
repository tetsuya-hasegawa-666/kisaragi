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

```

# admin

```text
# Step 3 retry v02 res

```
