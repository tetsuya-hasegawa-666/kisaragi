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

```
