# DA3 NGL Canonical Colab Runbook

任意の `correcting` session zip を入力として、`DA3NESTED-GIANT-LARGE-1.1` の公式 API / CLI 基準で sequence anchor、chunk 実行、merge を行う。説明は最小限にし、設定値は #2 に集約する。


# 1 Runtime Mount

実行順: #1 -> #2 -> #3 -> #4 -> #5 -> #6 -> #7 -> #8 -> #9 -> #10 -> #11 -> #12 -> #13 -> #14

```python
#1-1
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


# 2 Config

実行順: #2 の値を必要に応じて変更してから #3 へ進む

```python
#2-1
from pathlib import Path
import json
import pandas as pd
from IPython.display import display

CONFIG = {
    "PROJECT_SLUG": "da3_ngl_run_v01",
    "PIPELINE_SLUG": "da3_ngl_batch_v01",
    "MODEL_ID": "depth-anything/DA3NESTED-GIANT-LARGE-1.1",
    "BUNDLE_MODEL_SLUG": "nestedgiantlarge11",
    "BATCH_SIZE": 3,
    "CHUNK_SIZE": 18,
    "CHUNK_STEP": 12,
    "ADOPT_SIZE": 12,
    "PROCESS_RES": 504,
    "PROCESS_RES_METHOD": "upper_bound_resize",
    "EXPORT_FORMAT": "mini_npz",
    "ALIGN_TO_INPUT_EXT_SCALE": True,
    "INFER_GS": False,
    "SHOW_CAMERAS": False,
    "CONF_THRESH_PERCENTILE": 40.0,
    "NUM_MAX_POINTS": 1000000,
    "SKIP_ALREADY_SUCCESS": True,
    "RESET_TARGET_OUTPUTS_BEFORE_RUN": True,
    "MAKE_DRIVE_BUNDLE": False,
    "DOWNLOAD_LOCAL_BUNDLE": False,
    "USE_TARGET_CHUNK_WINDOW": False,
    "TARGET_CHUNK_WINDOW_START_1BASED": 1,
    "TARGET_CHUNK_WINDOW_COUNT": 0,
    "ROLL_BAND_DEG": 20.0,
    "PITCH_MIN_DEG": -85.0,
    "PITCH_MAX_DEG": -1.0,
    "YAW_JUMP_MAX_DEG": 90.0,
    "ANCHOR_QC_WARN_ABS_ROLL_CENTERED_DEG": 15.0,
    "ANCHOR_QC_WARN_PITCH_MIN_DEG": -89.0,
    "ANCHOR_QC_WARN_PITCH_MAX_DEG": 89.0,
    "ANCHOR_QC_MAX_DELTA_LENS_ANGLE_DEG": 45.0,
    "AUTO_SELECT_SESSION_ID": "",
    "AUTO_SELECT_CANDIDATE_INDEX": None,
    "AUTO_SELECT_POLICY": "latest_modified",
}
Path('/content/config_snapshot.json').write_text(json.dumps(CONFIG, indent=2, ensure_ascii=False), encoding='utf-8')
display(pd.DataFrame([{"item": k, "value": str(v)} for k, v in CONFIG.items()]))
```


# 3 Input Select And Path Check

実行順: #3 -> #4。ここで入力と保存先の存在・アクセス可否を確定する

```python
#3-1
from pathlib import Path
import json
import shutil
import zipfile

# ===== 固定定数 =====
OAI_SHORTCUT_ID = "1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_"
SHORTCUT_ROOT = Path(f"/content/drive/.shortcut-targets-by-id/{OAI_SHORTCUT_ID}")

# 探索対象は correcting zip のみ
RAW_SCAN_ROOTS = [
    SHORTCUT_ROOT / "trajectreview" / "correcting",
    Path("/content/drive/MyDrive/trajectreview/correcting"),
]

# 保存先は modeling
RESULTS_ROOT_CANDIDATES = [
    Path("/content/drive/MyDrive/trajectreview/modeling"),
    SHORTCUT_ROOT / "trajectreview" / "modeling",
]

RESULTS_ROOT = next((p for p in RESULTS_ROOT_CANDIDATES if p.exists()), RESULTS_ROOT_CANDIDATES[0])
RESULTS_ROOT.mkdir(parents=True, exist_ok=True)

EXTRACT_ROOT = Path("/content/trajectreview_input")
RUNBOOK_CANDIDATE_DOC = Path("/content/runbook_drive_candidates.json")
RUNBOOK_SELECTED_DOC = Path("/content/runbook_selected_input.json")
RUNBOOK_PATHS_DOC = Path("/content/runbook_paths.json")
CONFIG_SNAPSHOT = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8")) if Path("/content/config_snapshot.json").exists() else {}
PIPELINE_SLUG = CONFIG_SNAPSHOT.get("PIPELINE_SLUG", "da3_ngl_batch_v01")

def infer_session_id(path: Path) -> str:
    return path.stem

def scan_candidates(scan_roots):
    zip_map = {}
    for root in scan_roots:
        if not root.exists():
            continue
        for zip_path in sorted(root.rglob("*.zip")):
            stat = zip_path.stat()
            key = (infer_session_id(zip_path), stat.st_size)
            zip_map[key] = {
                "kind": "zip",
                "session_id": infer_session_id(zip_path),
                "label": f"{infer_session_id(zip_path)} [zip]",
                "path": str(zip_path),
                "size_bytes": stat.st_size,
                "mtime_ns": int(stat.st_mtime_ns),
            }
    return sorted(list(zip_map.values()), key=lambda x: (x["session_id"], x["path"]))

def reset_extract_root():
    if EXTRACT_ROOT.exists():
        shutil.rmtree(EXTRACT_ROOT)
    EXTRACT_ROOT.mkdir(parents=True, exist_ok=True)

def extract_selected_input(selected_path: Path, selected_kind: str):
    assert selected_kind == "zip", {"selected_kind": selected_kind, "expected": "zip"}
    reset_extract_root()
    with zipfile.ZipFile(selected_path, "r") as zf:
        zf.extractall(EXTRACT_ROOT)

def pick_best_raw_root(base: Path) -> Path:
    manifest_hits = sorted(base.rglob("session_manifest.json"))
    if manifest_hits:
        root = manifest_hits[0].parent
        if root.name != "trajectreview" and (root / "trajectreview").exists():
            return root / "trajectreview"
        return root
    package_hits = sorted(base.rglob("session_package.json"))
    if package_hits:
        pkg_parent = package_hits[0].parent
        root = pkg_parent.parent if pkg_parent.name == "trajectreview" else pkg_parent
        if root.name != "trajectreview" and (root / "trajectreview").exists():
            return root / "trajectreview"
        return root
    frame_hits = sorted(list(base.rglob("frame_record.jsonl")) + list(base.rglob("arcore_pose.jsonl")))
    image_dir_hits = sorted([p for p in base.rglob("*") if p.is_dir() and p.name in {"images", "image"}])
    candidate_roots = []
    for p in frame_hits:
        candidate_roots.append(p.parent)
        if (p.parent / "trajectreview").exists():
            candidate_roots.append(p.parent / "trajectreview")
    for p in image_dir_hits:
        candidate_roots.append(p.parent)
        if (p.parent / "trajectreview").exists():
            candidate_roots.append(p.parent / "trajectreview")
    for c in candidate_roots:
        if c.name == "trajectreview":
            return c
    if candidate_roots:
        root = candidate_roots[0]
        if root.name != "trajectreview" and (root / "trajectreview").exists():
            return root / "trajectreview"
        return root
    dirs = [p for p in base.iterdir() if p.is_dir()]
    if len(dirs) == 1:
        only = dirs[0]
        if (only / "trajectreview").exists():
            return only / "trajectreview"
        return only
    raise AssertionError(f"raw session root not found under {base}")

def resolve_and_validate_paths(selected_doc: dict):
    selected_path = Path(selected_doc["path"])
    selected_kind = selected_doc["kind"]
    session_id = selected_doc["session_id"]
    assert selected_path.exists(), f"selected input missing: {selected_path}"
    assert selected_kind == "zip", {"selected_kind": selected_kind, "expected": "zip"}
    extract_selected_input(selected_path, selected_kind)
    session_root = pick_best_raw_root(EXTRACT_ROOT)
    if session_root.name != "trajectreview" and (session_root / "trajectreview").exists():
        session_root = session_root / "trajectreview"
    session_outer = session_root.parent if session_root.name == "trajectreview" else session_root
    image_dir_candidates = [
        session_root / "images",
        session_root / "image",
        session_outer / "images",
        session_outer / "image",
        session_outer / "trajectreview" / "images",
        session_outer / "trajectreview" / "image",
    ]
    valid_image_dirs = []
    for p in image_dir_candidates:
        if not p.exists():
            continue
        image_count = len(list(p.glob("*.jpg"))) + len(list(p.glob("*.jpeg"))) + len(list(p.glob("*.png"))) + len(list(p.glob("*.JPG"))) + len(list(p.glob("*.JPEG"))) + len(list(p.glob("*.PNG")))
        valid_image_dirs.append((p, image_count))
    assert valid_image_dirs, {"image_dir_candidates": [str(p) for p in image_dir_candidates]}
    valid_image_dirs = sorted(valid_image_dirs, key=lambda x: (-x[1], len(str(x[0]))))
    images_dir = valid_image_dirs[0][0]
    frame_record_candidates = [
        session_outer / "frame_record.jsonl",
        session_root / "frame_record.jsonl",
        session_root / "arcore_pose.jsonl",
        session_outer / "arcore_pose.jsonl",
        session_outer / "trajectreview" / "frame_record.jsonl",
        session_outer / "trajectreview" / "arcore_pose.jsonl",
    ]
    frame_record_path = next((p for p in frame_record_candidates if p.exists()), None)
    assert frame_record_path is not None, {"frame_record_candidates": [str(p) for p in frame_record_candidates]}
    modeling_session_id = session_id.replace("trajectreview-correcting-session-", "trajectreview-modeling-session-", 1) if session_id.startswith("trajectreview-correcting-session-") else f"trajectreview-modeling-session-{session_id}"
    probe_root = RESULTS_ROOT / modeling_session_id
    da3_nested_dir = probe_root / "da3_nested_giant_large"
    da3_nested_gs_dir = probe_root / "da3_nested_gs"
    world_dir = probe_root / "world_fusion_v01"
    manifest_dir = probe_root / "manifests"
    final_outputs_dir = probe_root / "final_outputs"
    final_outputs_merged_dir = final_outputs_dir / "merged"
    final_outputs_diagnostics_dir = final_outputs_dir / "diagnostics"
    final_outputs_manifests_dir = final_outputs_dir / "manifests"
    final_outputs_chunk_evidence_dir = final_outputs_dir / "chunk_evidence"
    for p in [probe_root, da3_nested_dir, da3_nested_gs_dir, world_dir, manifest_dir, final_outputs_dir, final_outputs_merged_dir, final_outputs_diagnostics_dir, final_outputs_manifests_dir, final_outputs_chunk_evidence_dir]:
        p.mkdir(parents=True, exist_ok=True)
    return {
        "session_id": session_id,
        "selected_kind": selected_kind,
        "source_family": "correcting_zip_only",
        "selected_path": str(selected_path),
        "results_root": str(RESULTS_ROOT),
        "results_root_visibility": "google_drive_mydrive_visible",
        "extract_root": str(EXTRACT_ROOT),
        "probe_root": str(probe_root),
        "manifest_dir": str(manifest_dir),
        "da3_nested_dir": str(da3_nested_dir),
        "da3_nested_gs_dir": str(da3_nested_gs_dir),
        "world_dir": str(world_dir),
        "final_outputs_dir": str(final_outputs_dir),
        "final_outputs_merged_dir": str(final_outputs_merged_dir),
        "final_outputs_diagnostics_dir": str(final_outputs_diagnostics_dir),
        "final_outputs_manifests_dir": str(final_outputs_manifests_dir),
        "final_outputs_chunk_evidence_dir": str(final_outputs_chunk_evidence_dir),
        "images_dir": str(images_dir),
        "images_dir_file_count": int(valid_image_dirs[0][1]),
        "image_dir_candidates_ranked": [{"path": str(p), "image_count": int(c)} for p, c in valid_image_dirs],
        "frame_record_path": str(frame_record_path),
        "session_root": str(session_root),
        "session_outer": str(session_outer),
        "input_mode": "zip_only",
    }

candidate_doc = {
    "results_root": str(RESULTS_ROOT),
    "results_root_visibility": "google_drive_mydrive_visible",
    "scan_roots": [str(p) for p in RAW_SCAN_ROOTS],
    "candidate_count": 0,
    "candidates": scan_candidates(RAW_SCAN_ROOTS),
}
candidate_doc["candidate_count"] = len(candidate_doc["candidates"])
RUNBOOK_CANDIDATE_DOC.write_text(json.dumps(candidate_doc, indent=2, ensure_ascii=False), encoding="utf-8")

assert candidate_doc["candidate_count"] > 0, {"scan_roots": candidate_doc["scan_roots"]}

selected = None
session_id_hint = str(CONFIG_SNAPSHOT.get("AUTO_SELECT_SESSION_ID", "") or "").strip()
candidate_index_hint = CONFIG_SNAPSHOT.get("AUTO_SELECT_CANDIDATE_INDEX", None)
policy = str(CONFIG_SNAPSHOT.get("AUTO_SELECT_POLICY", "latest_modified"))

if session_id_hint:
    matched = [c for c in candidate_doc["candidates"] if c["session_id"] == session_id_hint]
    assert matched, {"AUTO_SELECT_SESSION_ID": session_id_hint, "available_session_ids": sorted(set(c["session_id"] for c in candidate_doc["candidates"]))[:50]}
    selected = sorted(matched, key=lambda x: (-x["mtime_ns"], x["path"]))[0]
elif candidate_index_hint is not None:
    idx = int(candidate_index_hint)
    assert 0 <= idx < len(candidate_doc["candidates"]), {"AUTO_SELECT_CANDIDATE_INDEX": idx, "candidate_count": len(candidate_doc["candidates"])}
    selected = candidate_doc["candidates"][idx]
else:
    if policy == "latest_modified":
        selected = sorted(candidate_doc["candidates"], key=lambda x: (-x["mtime_ns"], x["path"]))[0]
    elif policy == "largest_zip":
        selected = sorted(candidate_doc["candidates"], key=lambda x: (-x["size_bytes"], -x["mtime_ns"], x["path"]))[0]
    else:
        selected = candidate_doc["candidates"][0]

RUNBOOK_SELECTED_DOC.write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8")
resolved = resolve_and_validate_paths(selected)
RUNBOOK_PATHS_DOC.write_text(json.dumps(resolved, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps({
    "selected": selected,
    "resolved": resolved,
}, indent=2, ensure_ascii=False))
```


# 4 Tree Init

実行順: #4 -> #5。以降の全 block はここで生成した context と tree を使う

```python
#4-1
from pathlib import Path
import json

paths = json.loads(Path("/content/runbook_paths.json").read_text(encoding="utf-8"))
selected_path = Path(paths["selected_path"])
selected_kind = paths["selected_kind"]
session_id = paths["session_id"]
results_root = Path(paths["results_root"])
assert str(results_root).startswith("/content/drive/MyDrive/"), results_root
results_root.mkdir(parents=True, exist_ok=True)
session_root = Path(paths["session_root"])
session_outer = Path(paths["session_outer"])
images_dir = Path(paths["images_dir"])
frame_record_path = Path(paths["frame_record_path"])
frame_pose_index_path = session_root / "frame_pose_index.csv"
config = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8")) if Path("/content/config_snapshot.json").exists() else {}
route_slug = config.get("PROJECT_SLUG", "da3_record_sequence_anchor_rebuild_v02")
pipeline_slug = config.get("PIPELINE_SLUG", "da3_ngl_batch_v01")
legacy_source_pipeline_slug = "continuous_gs_v06_chunk18_overlap6_adopt12"
modeling_session_id = session_id.replace("trajectreview-correcting-session-", "trajectreview-modeling-session-", 1) if session_id.startswith("trajectreview-correcting-session-") else f"trajectreview-modeling-session-{session_id}"
probe_root_name = modeling_session_id
probe_root = Path(paths["probe_root"])
pipeline_root = probe_root / pipeline_slug
merged_dir = pipeline_root / "merged"
da3_nested_dir = Path(paths["da3_nested_dir"])
da3_nested_gs_dir = Path(paths["da3_nested_gs_dir"])
world_dir = Path(paths["world_dir"])
manifest_dir = Path(paths["manifest_dir"])
final_outputs_dir = Path(paths["final_outputs_dir"])
final_outputs_merged_dir = Path(paths["final_outputs_merged_dir"])
final_outputs_diagnostics_dir = Path(paths["final_outputs_diagnostics_dir"])
final_outputs_manifests_dir = Path(paths["final_outputs_manifests_dir"])
final_outputs_chunk_evidence_dir = Path(paths["final_outputs_chunk_evidence_dir"])

for p in [
    probe_root,
    da3_nested_dir,
    da3_nested_gs_dir,
    world_dir,
    manifest_dir,
    final_outputs_dir,
    final_outputs_merged_dir,
    final_outputs_diagnostics_dir,
    final_outputs_manifests_dir,
    final_outputs_chunk_evidence_dir,
]:
    p.mkdir(parents=True, exist_ok=True)

context_doc = {
    "session_id": session_id,
    "modeling_session_id": modeling_session_id,
    "selected_kind": selected_kind,
    "selected_path": str(selected_path),
    "results_root": str(results_root),
    "results_root_visibility": "google_drive_mydrive_visible",
    "route_slug": route_slug,
    "pipeline_slug": pipeline_slug,
    "legacy_source_pipeline_slug": legacy_source_pipeline_slug,
    "probe_root_name": probe_root_name,
    "session_outer": str(session_outer),
    "session_root": str(session_root),
    "images_dir": str(images_dir),
    "frame_record_path": str(frame_record_path),
    "frame_pose_index_path": str(frame_pose_index_path),
    "probe_root": str(probe_root),
    "da3_nested_dir": str(da3_nested_dir),
    "da3_nested_gs_dir": str(da3_nested_gs_dir),
    "world_dir": str(world_dir),
    "manifest_dir": str(manifest_dir),
    "merged_dir": str(merged_dir),
    "final_outputs_dir": str(final_outputs_dir),
    "final_outputs_merged_dir": str(final_outputs_merged_dir),
    "final_outputs_diagnostics_dir": str(final_outputs_diagnostics_dir),
    "final_outputs_manifests_dir": str(final_outputs_manifests_dir),
    "final_outputs_chunk_evidence_dir": str(final_outputs_chunk_evidence_dir),
    "input_mode": "zip_only",
    "add_suffix": "",
}
Path("/content/runbook_session_context.json").write_text(json.dumps(context_doc, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(context_doc, indent=2, ensure_ascii=False))
```

```python
#4-2
from pathlib import Path
import json

ctx = json.loads(Path('/content/runbook_session_context.json').read_text(encoding='utf-8'))
probe_root = Path(ctx['probe_root'])
managed_dirs = {
    '00_config': probe_root / '00_config',
    '01_anchor': probe_root / '01_anchor',
    '02_records': probe_root / '02_records',
    '03_batch_plan': probe_root / '03_batch_plan',
    '04_batch_runs': probe_root / '04_batch_runs',
    '05_merge': probe_root / '05_merge',
    '06_cleanup': probe_root / '06_cleanup',
    'other': probe_root / 'other',
}
for p in managed_dirs.values():
    p.mkdir(parents=True, exist_ok=True)
Path('/content/runbook_managed_dirs.json').write_text(json.dumps({k:str(v) for k,v in managed_dirs.items()}, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({k:str(v) for k,v in managed_dirs.items()}, indent=2, ensure_ascii=False))
```


# 5 Install

実行順: #5 -> #6。runtime が fresh の時だけ必須

```python
#5-1
from pathlib import Path
import inspect
import subprocess
import sys

repo_root = Path("/content/Depth-Anything-3")
repo_url = "https://github.com/ByteDance-Seed/Depth-Anything-3.git"
src_root = repo_root / "src"

if not repo_root.exists():
    subprocess.run(["git", "clone", "--depth", "1", repo_url, str(repo_root)], check=True)
else:
    print("repo already exists:", repo_root)

subprocess.run([
    "python", "-m", "pip", "install", "--quiet",
    "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile", "trimesh", "gsplat", "e3nn"
], check=True)

assert repo_root.exists(), repo_root
assert src_root.exists(), src_root
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from depth_anything_3.api import DepthAnything3
import gsplat
import e3nn

print("repo_exists", repo_root.exists(), repo_root)
print("dependency_install_ok")
print("depth_anything_3_import_ok", DepthAnything3)
print("gsplat_version", getattr(gsplat, "__version__", "unknown"))
print("e3nn_version", getattr(e3nn, "__version__", "unknown"))
print("inference_sig", inspect.signature(DepthAnything3.inference))
```


# 6 Shared Helpers

実行順: #6 -> #7。以降の全 block はこの helper を前提にする

```python
#6-1
from pathlib import Path
import json, math, shutil
import numpy as np
import pandas as pd
from IPython.display import Markdown, display

RUNBOOK_CTX_PATH = Path('/content/runbook_session_context.json')


def load_ctx() -> dict:
    return json.loads(RUNBOOK_CTX_PATH.read_text(encoding='utf-8'))


def save_json(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')


def append_sequence_columns(df: pd.DataFrame, timestamp_col: str = 'frame_timestamp_ns') -> pd.DataFrame:
    out = df.copy()
    if timestamp_col in out.columns:
        out = out.sort_values(timestamp_col, kind='stable').reset_index(drop=True)
    else:
        out = out.reset_index(drop=True)
    out['sequence_index'] = np.arange(len(out), dtype=np.int64)
    out['prev_sequence_index'] = out['sequence_index'] - 1
    out['next_sequence_index'] = out['sequence_index'] + 1
    out.loc[out['sequence_index'] == 0, 'prev_sequence_index'] = -1
    out.loc[out['sequence_index'] == len(out) - 1, 'next_sequence_index'] = -1
    return out


def rotmat_to_rpy_deg(R: np.ndarray):
    sy = math.sqrt(float(R[0,0] * R[0,0] + R[1,0] * R[1,0]))
    singular = sy < 1e-6
    if not singular:
        roll = math.degrees(math.atan2(float(R[2,1]), float(R[2,2])))
        pitch = math.degrees(math.atan2(float(-R[2,0]), sy))
        yaw = math.degrees(math.atan2(float(R[1,0]), float(R[0,0])))
    else:
        roll = math.degrees(math.atan2(float(-R[1,2]), float(R[1,1])))
        pitch = math.degrees(math.atan2(float(-R[2,0]), sy))
        yaw = 0.0
    return roll, pitch, yaw


def _summary_rows(items, kind: str):
    rows = []
    for item in (items or []):
        if isinstance(item, (str, Path)):
            item = {"item": Path(item).name, "path": str(item)}
        row = dict(item)
        row.setdefault("kind", kind)
        if "item" not in row:
            row["item"] = row.pop("label", row.pop("name", ""))
        path_value = row.get("path")
        if path_value:
            p = Path(path_value)
            row.setdefault("exists", p.exists())
            row.setdefault("is_dir", p.exists() and p.is_dir())
            if p.exists() and p.is_file():
                row.setdefault("bytes", int(p.stat().st_size))
        rows.append(row)
    return rows


def display_stage_summary(stage_no: str, title: str, inputs=None, outputs=None, notes=None):
    display(Markdown(f"### {stage_no} summary"))
    if notes:
        display(pd.DataFrame(_summary_rows(notes, "note")))
    if inputs:
        display(pd.DataFrame(_summary_rows(inputs, "input")))
    if outputs:
        display(pd.DataFrame(_summary_rows(outputs, "output")))
```


# 7 Full Anchor Build

実行順: #7 -> #8。全 frame を 1 record 1 row で anchor 化する

```python
#7-1
from pathlib import Path
import csv
import json
import subprocess

import imageio.v3 as iio
import numpy as np
import pandas as pd
from PIL import Image

ctx_path = Path("/content/runbook_session_context.json")
assert ctx_path.exists(), ctx_path
ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
manifest_dir = Path(ctx["manifest_dir"])
da3_nested_dir = Path(ctx["da3_nested_dir"])
world_dir = Path(ctx["world_dir"])
final_outputs_dir = Path(ctx["final_outputs_dir"])
final_outputs_merged_dir = Path(ctx["final_outputs_merged_dir"])
final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_manifests_dir = Path(ctx["final_outputs_manifests_dir"])
final_outputs_chunk_evidence_dir = Path(ctx["final_outputs_chunk_evidence_dir"])
images_dir = Path(ctx["images_dir"])
frame_record_path = Path(ctx["frame_record_path"])
frame_pose_index_path = Path(ctx["frame_pose_index_path"])

repo_root = Path("/content/Depth-Anything-3")
repo_url = "https://github.com/ByteDance-Seed/Depth-Anything-3.git"
src_root = repo_root / "src"
if not repo_root.exists():
    print("Depth-Anything-3 repo not found. Cloning automatically...")
    subprocess.run(["git", "clone", "--depth", "1", repo_url, str(repo_root)], check=True)
assert repo_root.exists(), repo_root
assert src_root.exists(), src_root
assert (src_root / "depth_anything_3" / "api.py").exists(), src_root / "depth_anything_3" / "api.py"

for p in [manifest_dir, da3_nested_dir, world_dir, final_outputs_dir, final_outputs_merged_dir, final_outputs_diagnostics_dir, final_outputs_manifests_dir, final_outputs_chunk_evidence_dir]:
    p.mkdir(parents=True, exist_ok=True)

required_files = {
    "input_manifest": manifest_dir / "da3_input_manifest.csv",
    "intrinsics": manifest_dir / "intrinsics.npy",
    "extrinsics": manifest_dir / "extrinsics_w2c_arc.npy",
}

CANONICAL_ORIENTATION_POLICY = "upright_rot90cw_from_correcting"
BLUR_THRESHOLD = 8.0

def build_anchor_inputs_from_zip():
    assert frame_record_path.exists(), {"frame_record_path": str(frame_record_path)}
    with frame_record_path.open("r", encoding="utf-8") as f:
        frame_records = [json.loads(line) for line in f if line.strip()]
    assert len(frame_records) > 0, "frame_record.jsonl empty"

    frame_pose_df = pd.read_csv(frame_pose_index_path) if frame_pose_index_path.exists() else pd.DataFrame()
    image_name_by_record_index = {}
    if len(frame_pose_df) > 0:
        image_name_col = next((c for c in ["image_file_name", "imageFileName", "frame_name"] if c in frame_pose_df.columns), None)
        record_index_col = next((c for c in ["pose_record_index", "record_index"] if c in frame_pose_df.columns), None)
        if image_name_col is not None and record_index_col is not None:
            tmp = frame_pose_df[[record_index_col, image_name_col]].copy().dropna()
            tmp[image_name_col] = tmp[image_name_col].astype(str).str.strip()
            tmp = tmp.loc[tmp[image_name_col] != ""]
            image_name_by_record_index = {
                int(getattr(row, record_index_col)): getattr(row, image_name_col)
                for row in tmp.itertuples(index=False)
            }
        elif "frame_index" in frame_pose_df.columns:
            sorted_image_names = sorted([
                *[p.name for p in images_dir.glob("*.jpg")], *[p.name for p in images_dir.glob("*.jpeg")], *[p.name for p in images_dir.glob("*.png")],
                *[p.name for p in images_dir.glob("*.JPG")], *[p.name for p in images_dir.glob("*.JPEG")], *[p.name for p in images_dir.glob("*.PNG")],
            ])
            record_index_col = next((c for c in ["pose_record_index", "record_index"] if c in frame_pose_df.columns), None)
            if record_index_col is not None:
                for row in frame_pose_df.itertuples(index=False):
                    frame_idx = int(getattr(row, "frame_index"))
                    if 0 <= frame_idx < len(sorted_image_names):
                        image_name_by_record_index[int(getattr(row, record_index_col))] = sorted_image_names[frame_idx]

    def ranked_image_dirs(primary_dir: Path, frame_record_path: Path):
        session_outer = frame_record_path.parent
        session_root = session_outer / "trajectreview" if (session_outer / "trajectreview").exists() else session_outer
        candidates = [
            primary_dir,
            session_root / "images", session_root / "image",
            session_outer / "images", session_outer / "image",
            session_outer / "trajectreview" / "images", session_outer / "trajectreview" / "image",
        ]
        ranked, seen = [], set()
        for p in candidates:
            key = str(p)
            if key in seen or not p.exists():
                continue
            seen.add(key)
            image_count = sum(len(list(p.glob(ext))) for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"])
            ranked.append((p, image_count))
        return sorted(ranked, key=lambda x: (-x[1], len(str(x[0]))))

    def lap_var(image_path: Path) -> float:
        img = iio.imread(image_path)
        gray = img[..., :3].mean(axis=2).astype(np.float32) if img.ndim == 3 else img.astype(np.float32)
        gx = gray[:, 1:] - gray[:, :-1]
        gy = gray[1:, :] - gray[:-1, :]
        return float(np.var(gx) + np.var(gy))

    def read_actual_wh(image_path: Path):
        with Image.open(image_path) as img:
            width, height = img.size
        return int(width), int(height)

    def normalize_intrinsics_to_upright(intr, actual_width: int, actual_height: int):
        fx, fy, cx, cy = intr.get("fx"), intr.get("fy"), intr.get("cx"), intr.get("cy")
        intr_width, intr_height = intr.get("width"), intr.get("height")
        if None in [fx, fy, cx, cy, intr_width, intr_height]:
            return {"intrinsics_case": "missing_intrinsics", "rotation_applied_deg": None, "fx_canonical": None, "fy_canonical": None, "cx_canonical": None, "cy_canonical": None, "width_canonical": None, "height_canonical": None}
        fx, fy, cx, cy = float(fx), float(fy), float(cx), float(cy)
        intr_width, intr_height = int(intr_width), int(intr_height)
        if intr_width == actual_width and intr_height == actual_height:
            return {"intrinsics_case": "already_upright", "rotation_applied_deg": 0, "fx_canonical": fx, "fy_canonical": fy, "cx_canonical": cx, "cy_canonical": cy, "width_canonical": actual_width, "height_canonical": actual_height}
        if intr_width == actual_height and intr_height == actual_width:
            return {"intrinsics_case": "rot90cw_intrinsics_fixed", "rotation_applied_deg": 90, "fx_canonical": fy, "fy_canonical": fx, "cx_canonical": float(intr_height - 1) - cy, "cy_canonical": cx, "width_canonical": actual_width, "height_canonical": actual_height}
        return {"intrinsics_case": "dimension_mismatch", "rotation_applied_deg": None, "fx_canonical": None, "fy_canonical": None, "cx_canonical": None, "cy_canonical": None, "width_canonical": None, "height_canonical": None}

    image_dir_ranking = ranked_image_dirs(images_dir, frame_record_path)
    assert len(image_dir_ranking) > 0, {"images_dir": str(images_dir), "frame_record_path": str(frame_record_path)}
    resolved_images_dir = image_dir_ranking[0][0]

    rows = []
    for rec in sorted(frame_records, key=lambda x: int(x.get("frameTimestampNs", 0) or 0)):
        image_name = str(rec.get("imageFileName", "") or "").strip()
        if not image_name:
            record_index = rec.get("recordIndex")
            if record_index is not None:
                image_name = str(image_name_by_record_index.get(int(record_index), "")).strip()
        image_path = resolved_images_dir / image_name if image_name else None
        image_exists = bool(image_name) and image_path.exists()
        intr = rec.get("imageIntrinsics") or {}
        pose = rec.get("pose") or {}
        blur_score = lap_var(image_path) if image_exists else None
        actual_width = actual_height = None
        intr_norm = {"intrinsics_case": "image_missing", "rotation_applied_deg": None, "fx_canonical": None, "fy_canonical": None, "cx_canonical": None, "cy_canonical": None, "width_canonical": None, "height_canonical": None}
        if image_exists:
            actual_width, actual_height = read_actual_wh(image_path)
            intr_norm = normalize_intrinsics_to_upright(intr, actual_width, actual_height)
        rows.append({
            "session_id": rec.get("sessionId"),
            "record_index": rec.get("recordIndex"),
            "frame_timestamp_ns": rec.get("frameTimestampNs"),
            "capture_timestamp_ns": rec.get("captureTimestampNs"),
            "tracking_state": rec.get("trackingState"),
            "image_file_name": image_name,
            "image_path": str(image_path) if image_path else "",
            "resolved_images_dir": str(resolved_images_dir),
            "image_name_source": "frame_record" if str(rec.get("imageFileName", "") or "").strip() else "frame_pose_index_fallback",
            "image_exists": image_exists,
            "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
            "actual_width": actual_width,
            "actual_height": actual_height,
            "fx": intr.get("fx"), "fy": intr.get("fy"), "cx": intr.get("cx"), "cy": intr.get("cy"), "width": intr.get("width"), "height": intr.get("height"),
            **intr_norm,
            "tx": pose.get("tx"), "ty": pose.get("ty"), "tz": pose.get("tz"),
            "qx": pose.get("qx"), "qy": pose.get("qy"), "qz": pose.get("qz"), "qw": pose.get("qw"),
            "blur_score": blur_score,
        })

    manifest_df = pd.DataFrame(rows)
    manifest_df.to_csv(manifest_dir / "input_frame_manifest.csv", index=False, encoding="utf-8")

    qc_df = manifest_df.copy()
    qc_df["qc_tracking_ok"] = qc_df["tracking_state"].fillna("") == "TRACKING"
    qc_df["qc_image_ok"] = qc_df["image_exists"].fillna(False)
    qc_df["qc_orientation_ok"] = qc_df["intrinsics_case"].isin(["already_upright", "rot90cw_intrinsics_fixed"])
    qc_df["qc_intrinsics_ok"] = qc_df[["fx_canonical", "fy_canonical", "cx_canonical", "cy_canonical", "width_canonical", "height_canonical"]].notna().all(axis=1)
    qc_df["qc_pose_ok"] = qc_df[["tx", "ty", "tz", "qx", "qy", "qz", "qw"]].notna().all(axis=1)
    qc_df["blur_score"] = pd.to_numeric(qc_df["blur_score"], errors="coerce")
    qc_df["qc_blur_ok"] = qc_df["blur_score"].fillna(0.0).ge(BLUR_THRESHOLD).infer_objects(copy=False)
    qc_df["qc_pass"] = qc_df[["qc_tracking_ok", "qc_image_ok", "qc_orientation_ok", "qc_intrinsics_ok", "qc_pose_ok"]].all(axis=1)
    qc_df["skip_reason"] = ""
    qc_df.loc[~qc_df["qc_tracking_ok"], "skip_reason"] = "tracking_not_ok"
    qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_image_ok"], "skip_reason"] = "image_missing"
    qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_orientation_ok"], "skip_reason"] = "orientation_mismatch"
    qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_intrinsics_ok"], "skip_reason"] = "intrinsics_missing"
    qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_pose_ok"], "skip_reason"] = "pose_missing"
    qc_df.to_csv(manifest_dir / "input_frame_qc.csv", index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)

    def quat_to_rot(qx, qy, qz, qw):
        xx, yy, zz = qx*qx, qy*qy, qz*qz
        xy, xz, yz = qx*qy, qx*qz, qy*qz
        wx, wy, wz = qw*qx, qw*qy, qw*qz
        return np.array([
            [1 - 2*(yy + zz), 2*(xy - wz), 2*(xz + wy)],
            [2*(xy + wz), 1 - 2*(xx + zz), 2*(yz - wx)],
            [2*(xz - wy), 2*(yz + wx), 1 - 2*(xx + yy)],
        ], dtype=np.float32)

    def pose_to_w2c(row):
        R_c2w = quat_to_rot(float(row.qx), float(row.qy), float(row.qz), float(row.qw))
        t_c2w = np.array([float(row.tx), float(row.ty), float(row.tz)], dtype=np.float32)
        R_w2c = R_c2w.T
        t_w2c = -R_w2c @ t_c2w
        out = np.eye(4, dtype=np.float32)
        out[:3, :3] = R_w2c
        out[:3, 3] = t_w2c
        return out

    def build_K(row):
        return np.array([
            [float(row.fx_canonical), 0.0, float(row.cx_canonical)],
            [0.0, float(row.fy_canonical), float(row.cy_canonical)],
            [0.0, 0.0, 1.0],
        ], dtype=np.float32)

    adopt_df = qc_df.loc[qc_df["qc_pass"]].copy().sort_values("frame_timestamp_ns").reset_index(drop=True)
    if len(adopt_df) < 2:
        fail_counts = {
            "frame_record_count": int(len(qc_df)),
            "qc_pass_count": int(len(adopt_df)),
            "tracking_not_ok": int((~qc_df["qc_tracking_ok"]).sum()),
            "image_missing": int((~qc_df["qc_image_ok"]).sum()),
            "orientation_mismatch": int((~qc_df["qc_orientation_ok"]).sum()),
            "intrinsics_missing": int((~qc_df["qc_intrinsics_ok"]).sum()),
            "pose_missing": int((~qc_df["qc_pose_ok"]).sum()),
            "blur_low_diag_only": int((~qc_df["qc_blur_ok"]).sum()),
            "skip_reason_counts": qc_df["skip_reason"].value_counts(dropna=False).to_dict(),
        }
        (manifest_dir / "qc_failure_summary.json").write_text(json.dumps(fail_counts, indent=2, ensure_ascii=False), encoding="utf-8")
        raise AssertionError(fail_counts)

    adopted_rows = []
    last_t = None
    last_R = None
    for row in adopt_df.itertuples(index=False):
        t = np.array([float(row.tx), float(row.ty), float(row.tz)], dtype=np.float32)
        R = quat_to_rot(float(row.qx), float(row.qy), float(row.qz), float(row.qw))
        baseline = None if last_t is None else float(np.linalg.norm(t - last_t))
        rot_delta = None if last_R is None else float(np.degrees(np.arccos(np.clip((np.trace(last_R.T @ R) - 1.0) / 2.0, -1.0, 1.0))))
        geometric_adopt = last_t is None or (baseline >= 0.05) or (rot_delta is not None and rot_delta >= 3.0)
        blur_boost = bool(row.qc_blur_ok) if pd.notna(row.qc_blur_ok) else False
        adopt = geometric_adopt or (last_t is None and blur_boost)
        adopted_rows.append({
            **row._asdict(),
            "baseline_from_prev_adopted_m": baseline,
            "rotation_from_prev_adopted_deg": rot_delta,
            "geometric_adopt": geometric_adopt,
            "anchor_input_adopted": adopt,
            "anchor_input_skip_reason": "" if adopt else "baseline_small",
        })
        if adopt:
            last_t = t
            last_R = R

    anchor_input_df = pd.DataFrame(adopted_rows)
    anchor_input_df.to_csv(manifest_dir / "pose_conversion_check.csv", index=False, encoding="utf-8")

    selected_df = anchor_input_df.loc[anchor_input_df["anchor_input_adopted"]].copy().reset_index(drop=True)
    assert len(selected_df) >= 2, {"selected_df": len(selected_df)}
    Ks = np.stack([build_K(row) for row in selected_df.itertuples(index=False)], axis=0)
    exts = np.stack([pose_to_w2c(row) for row in selected_df.itertuples(index=False)], axis=0)
    np.save(manifest_dir / "intrinsics.npy", Ks)
    np.save(manifest_dir / "extrinsics_w2c_arc.npy", exts)
    selected_df.to_csv(manifest_dir / "da3_input_manifest.csv", index=False, encoding="utf-8")

    k_check = selected_df[[
        "image_file_name", "canonical_orientation_policy", "intrinsics_case", "rotation_applied_deg", "width", "height",
        "actual_width", "actual_height", "width_canonical", "height_canonical", "fx", "fy", "cx", "cy",
        "fx_canonical", "fy_canonical", "cx_canonical", "cy_canonical",
    ]].copy()
    k_check["resize_mode"] = "native"
    k_check.to_csv(manifest_dir / "k_resize_check.csv", index=False, encoding="utf-8")

    orientation_summary = {
        "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
        "already_upright_count": int((manifest_df["intrinsics_case"] == "already_upright").sum()),
        "rot90cw_intrinsics_fixed_count": int((manifest_df["intrinsics_case"] == "rot90cw_intrinsics_fixed").sum()),
        "dimension_mismatch_count": int((manifest_df["intrinsics_case"] == "dimension_mismatch").sum()),
        "image_missing_count": int((manifest_df["intrinsics_case"] == "image_missing").sum()),
    }
    (manifest_dir / "orientation_summary.json").write_text(json.dumps(orientation_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "frame_record_count": int(len(manifest_df)),
        "qc_pass_count": int(len(adopt_df)),
        "qc_skip_count": int((~qc_df["qc_pass"]).sum()),
        "resolved_images_dir": str(resolved_images_dir),
        "resolved_images_dir_file_count": int(image_dir_ranking[0][1]),
        "frame_pose_index_path": str(frame_pose_index_path),
        "frame_pose_fallback_mapping_count": int(len(image_name_by_record_index)),
        "selected_count": int(len(selected_df)),
        "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
        "intrinsics_path": str(manifest_dir / "intrinsics.npy"),
        "extrinsics_path": str(manifest_dir / "extrinsics_w2c_arc.npy"),
        "orientation_summary_path": str(manifest_dir / "orientation_summary.json"),
        "built_from": "zip_frame_record",
    }
    extrinsics_source_summary = {
        "artifact": "extrinsics_w2c_arc.npy",
        "artifact_path": str(manifest_dir / "extrinsics_w2c_arc.npy"),
        "generated_by": "build_anchor_inputs_from_zip.pose_to_w2c",
        "source_record_path": str(frame_record_path),
        "source_fields": ["pose.tx", "pose.ty", "pose.tz", "pose.qx", "pose.qy", "pose.qz", "pose.qw"],
        "source_sort_key": "frameTimestampNs",
        "matrix_space": "world_to_camera",
        "record_count": int(len(selected_df)),
    }
    (manifest_dir / "qc_summary.json").write_text(json.dumps({
        "frame_record_count": summary["frame_record_count"],
        "qc_pass_count": summary["qc_pass_count"],
        "qc_skip_count": summary["qc_skip_count"],
        "frame_record_path": str(frame_record_path),
        "images_dir": str(images_dir),
        "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    (manifest_dir / "da3_input_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (manifest_dir / "extrinsics_w2c_arc_source_summary.json").write_text(json.dumps(extrinsics_source_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary

missing_required = {key: str(path) for key, path in required_files.items() if not path.exists()}
if missing_required:
    print({"message": "anchor inputs missing; building from zip source", "missing": missing_required})
    build_summary = build_anchor_inputs_from_zip()
    print(json.dumps(build_summary, indent=2, ensure_ascii=False))

for key, path in required_files.items():
    assert path.exists(), {key: str(path)}

manifest_df = pd.read_csv(required_files["input_manifest"])
assert not manifest_df.empty, "input manifest empty"
print({
    "input_manifest": str(required_files["input_manifest"]),
    "intrinsics": str(required_files["intrinsics"]),
    "extrinsics": str(required_files["extrinsics"]),
    "row_count": int(len(manifest_df)),
})
display_stage_summary(
    "7-1",
    "full anchor input prepare",
    inputs=[
        {"item": "frame_record", "path": str(frame_record_path)},
        {"item": "images_dir", "path": str(images_dir)},
        {"item": "frame_pose_index", "path": str(frame_pose_index_path)},
    ],
    outputs=[
        {"item": "input_frame_manifest", "path": str(manifest_dir / "input_frame_manifest.csv")},
        {"item": "input_frame_qc", "path": str(manifest_dir / "input_frame_qc.csv")},
        {"item": "pose_conversion_check", "path": str(manifest_dir / "pose_conversion_check.csv")},
        {"item": "da3_input_manifest", "path": str(required_files["input_manifest"])},
        {"item": "intrinsics", "path": str(required_files["intrinsics"])},
        {"item": "extrinsics_w2c", "path": str(required_files["extrinsics"])},
        {"item": "extrinsics_w2c_source_summary", "path": str(manifest_dir / "extrinsics_w2c_arc_source_summary.json")},
        {"item": "da3_input_summary", "path": str(manifest_dir / "da3_input_summary.json")},
    ],
    notes=[
        {"item": "extrinsics_source_rule", "value": "frame_record pose(tx,ty,tz,qx,qy,qz,qw) を pose_to_w2c で world_to_camera 行列へ変換"},
    ],
)
```

```python
#7-2

from pathlib import Path
import json
import numpy as np
import pandas as pd

config = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8"))

def _existing(p):
    if not p:
        return None
    p = Path(p)
    return p if p.exists() else None

def _find_manifest_triplet(search_roots):
    rels = [
        ("manifests/da3_input_manifest.csv", "manifests/intrinsics.npy", "manifests/extrinsics_w2c_arc.npy"),
        ("00_config/da3_input_manifest.csv", "00_config/intrinsics.npy", "00_config/extrinsics_w2c_arc.npy"),
    ]
    for root in search_roots:
        if root is None:
            continue
        root = Path(root)
        if root.is_file():
            root = root.parent
        if not root.exists():
            continue

        # root 自体と配下を少し探索
        candidate_dirs = [root]
        candidate_dirs += [p for p in root.glob("*") if p.is_dir()]
        candidate_dirs += [p for p in root.glob("*/*") if p.is_dir()]

        seen = set()
        for d in candidate_dirs:
            d = d.resolve()
            if str(d) in seen:
                continue
            seen.add(str(d))
            for a, b, c in rels:
                pa = d / a
                pb = d / b
                pc = d / c
                if pa.exists() and pb.exists() and pc.exists():
                    return d, pa, pb, pc
    return None, None, None, None

# まず config から探索起点を集める
search_roots = [
    _existing(config.get("persist_root")),
    _existing(config.get("google_drive_run_root")),
    _existing(config.get("run_root")),
    _existing(config.get("persist_dir")),
    _existing(config.get("output_root")),
    _existing(config.get("project_root")),
    _existing(config.get("session_dir")),
    _existing(config.get("target_probe_root")),
    _existing(config.get("probe_root")),
    Path("/content/drive/MyDrive/trajectreview"),
    Path("/content/drive/MyDrive"),
]

persist_root, input_manifest_path, intrinsics_path, extrinsics_path = _find_manifest_triplet(search_roots)

assert persist_root is not None, {
    "error": "manifest triplet not found",
    "searched_roots": [str(p) for p in search_roots if p is not None],
    "expected_files": [
        "manifests/da3_input_manifest.csv",
        "manifests/intrinsics.npy",
        "manifests/extrinsics_w2c_arc.npy",
    ],
}

anchor_dir = persist_root / "01_anchor"
manifest_dir = input_manifest_path.parent
anchor_dir.mkdir(parents=True, exist_ok=True)

manifest_df = pd.read_csv(input_manifest_path)
intrinsics = np.load(intrinsics_path)
extrinsics_w2c = np.load(extrinsics_path)

assert len(manifest_df) > 0, "da3_input_manifest.csv is empty"
assert extrinsics_w2c.ndim == 3 and extrinsics_w2c.shape[1:] == (4, 4), extrinsics_w2c.shape
assert len(manifest_df) == extrinsics_w2c.shape[0], {
    "manifest_rows": len(manifest_df),
    "extrinsics_rows": int(extrinsics_w2c.shape[0]),
}
assert intrinsics.ndim == 3 and intrinsics.shape[1:] == (3, 3), intrinsics.shape
assert intrinsics.shape[0] == len(manifest_df), {
    "manifest_rows": len(manifest_df),
    "intrinsics_rows": int(intrinsics.shape[0]),
}

# c2w
c2w = np.linalg.inv(extrinsics_w2c)

# camera center / basis
camera_centers = c2w[:, :3, 3]
right_vecs = c2w[:, :3, 0]
up_vecs = c2w[:, :3, 1]
lens_vecs = -c2w[:, :3, 2]

def _normalize_rows(x: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n = np.linalg.norm(x, axis=1, keepdims=True)
    n = np.maximum(n, eps)
    return x / n

right_vecs = _normalize_rows(right_vecs)
up_vecs = _normalize_rows(up_vecs)
lens_vecs = _normalize_rows(lens_vecs)

# sequence_index
if "frame_timestamp_ns" in manifest_df.columns:
    ts_col = "frame_timestamp_ns"
elif "timestamp_ns" in manifest_df.columns:
    ts_col = "timestamp_ns"
elif "timestamp" in manifest_df.columns:
    ts_col = "timestamp"
else:
    ts_col = None

if "sequence_index" not in manifest_df.columns:
    if ts_col is not None:
        manifest_df = manifest_df.sort_values(ts_col, kind="stable").reset_index(drop=True)
    else:
        manifest_df = manifest_df.reset_index(drop=True)
    manifest_df["sequence_index"] = np.arange(len(manifest_df), dtype=np.int64)
else:
    manifest_df = manifest_df.sort_values("sequence_index", kind="stable").reset_index(drop=True)

camera_center_df = pd.DataFrame({
    "sequence_index": manifest_df["sequence_index"].astype(int),
    "cam_cx": camera_centers[:, 0],
    "cam_cy": camera_centers[:, 1],
    "cam_cz": camera_centers[:, 2],
})

camera_orientation_df = pd.DataFrame({
    "sequence_index": manifest_df["sequence_index"].astype(int),
    "right_x": right_vecs[:, 0],
    "right_y": right_vecs[:, 1],
    "right_z": right_vecs[:, 2],
    "up_x": up_vecs[:, 0],
    "up_y": up_vecs[:, 1],
    "up_z": up_vecs[:, 2],
    "lens_x": lens_vecs[:, 0],
    "lens_y": lens_vecs[:, 1],
    "lens_z": lens_vecs[:, 2],
})

camera_anchor_full_df = manifest_df.copy()
camera_anchor_full_df["cam_cx"] = camera_centers[:, 0]
camera_anchor_full_df["cam_cy"] = camera_centers[:, 1]
camera_anchor_full_df["cam_cz"] = camera_centers[:, 2]
camera_anchor_full_df["right_x"] = right_vecs[:, 0]
camera_anchor_full_df["right_y"] = right_vecs[:, 1]
camera_anchor_full_df["right_z"] = right_vecs[:, 2]
camera_anchor_full_df["up_x"] = up_vecs[:, 0]
camera_anchor_full_df["up_y"] = up_vecs[:, 1]
camera_anchor_full_df["up_z"] = up_vecs[:, 2]
camera_anchor_full_df["lens_x"] = lens_vecs[:, 0]
camera_anchor_full_df["lens_y"] = lens_vecs[:, 1]
camera_anchor_full_df["lens_z"] = lens_vecs[:, 2]

camera_matrix_full_csv = anchor_dir / "camera_matrix_full_arc.csv"
camera_center_matrix_csv = anchor_dir / "camera_center_matrix_arc.csv"
camera_orientation_full_csv = anchor_dir / "camera_orientation_full_arc.csv"
camera_anchor_full_csv = anchor_dir / "camera_anchor_full_arc.csv"

pd.DataFrame(
    extrinsics_w2c.reshape(extrinsics_w2c.shape[0], -1),
    columns=[f"w2c_{r}{c}" for r in range(4) for c in range(4)]
).assign(sequence_index=manifest_df["sequence_index"].astype(int)).to_csv(camera_matrix_full_csv, index=False)

camera_center_df.to_csv(camera_center_matrix_csv, index=False)
camera_orientation_df.to_csv(camera_orientation_full_csv, index=False)
camera_anchor_full_df.to_csv(camera_anchor_full_csv, index=False)

np.save(anchor_dir / "extrinsics_w2c_arc.npy", extrinsics_w2c)
np.save(anchor_dir / "intrinsics.npy", intrinsics)
np.save(anchor_dir / "c2w_arc.npy", c2w)

print({
    "persist_root": str(persist_root),
    "manifest_dir": str(manifest_dir),
    "rows": len(manifest_df),
    "camera_matrix_full_csv": str(camera_matrix_full_csv),
    "camera_center_matrix_csv": str(camera_center_matrix_csv),
    "camera_orientation_full_csv": str(camera_orientation_full_csv),
    "camera_anchor_full_csv": str(camera_anchor_full_csv),
})
display_stage_summary(
    "7-2",
    "full anchor build",
    inputs=[
        {"item": "da3_input_manifest", "path": str(input_manifest_path)},
        {"item": "intrinsics", "path": str(intrinsics_path)},
        {"item": "extrinsics_w2c", "path": str(extrinsics_path)},
        {"item": "extrinsics_w2c_source_summary", "path": str(manifest_dir / "extrinsics_w2c_arc_source_summary.json")},
    ],
    outputs=[
        {"item": "camera_matrix_full", "path": str(camera_matrix_full_csv)},
        {"item": "camera_center_matrix", "path": str(camera_center_matrix_csv)},
        {"item": "camera_orientation_full", "path": str(camera_orientation_full_csv)},
        {"item": "camera_anchor_full", "path": str(camera_anchor_full_csv)},
        {"item": "anchor_extrinsics_w2c", "path": str(anchor_dir / "extrinsics_w2c_arc.npy")},
        {"item": "anchor_intrinsics", "path": str(anchor_dir / "intrinsics.npy")},
        {"item": "anchor_c2w", "path": str(anchor_dir / "c2w_arc.npy")},
    ],
    notes=[
        {"item": "row_count", "value": int(len(manifest_df))},
        {"item": "matrix_source", "value": "manifests/extrinsics_w2c_arc.npy を c2w へ反転し basis / center を再構成"},
    ],
)
```

```python
#7-3

from pathlib import Path
import json
import numpy as np
import pandas as pd

config = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8"))

def _existing(p):
    if not p:
        return None
    p = Path(p)
    return p if p.exists() else None

def _find_anchor_root(search_roots):
    rels = [
        "01_anchor/camera_anchor_full_arc.csv",
        "01_anchor/camera_center_matrix_arc.csv",
        "01_anchor/camera_orientation_full_arc.csv",
    ]
    for root in search_roots:
        if root is None:
            continue
        root = Path(root)
        if root.is_file():
            root = root.parent
        if not root.exists():
            continue

        candidate_dirs = [root]
        candidate_dirs += [p for p in root.glob("*") if p.is_dir()]
        candidate_dirs += [p for p in root.glob("*/*") if p.is_dir()]

        seen = set()
        for d in candidate_dirs:
            d = d.resolve()
            if str(d) in seen:
                continue
            seen.add(str(d))
            if all((d / rel).exists() for rel in rels):
                return d
    return None

search_roots = [
    _existing(config.get("persist_root")),
    _existing(config.get("google_drive_run_root")),
    _existing(config.get("run_root")),
    _existing(config.get("persist_dir")),
    _existing(config.get("output_root")),
    _existing(config.get("project_root")),
    _existing(config.get("session_dir")),
    _existing(config.get("target_probe_root")),
    _existing(config.get("probe_root")),
    Path("/content/drive/MyDrive/trajectreview"),
    Path("/content/drive/MyDrive"),
]

persist_root = _find_anchor_root(search_roots)
assert persist_root is not None, {
    "error": "01_anchor not found",
    "searched_roots": [str(p) for p in search_roots if p is not None],
    "expected": "01_anchor/camera_anchor_full_arc.csv",
}

anchor_dir = persist_root / "01_anchor"
anchor_path = anchor_dir / "camera_anchor_full_arc.csv"
anchor_df = pd.read_csv(anchor_path)

assert not anchor_df.empty, anchor_path

# sequence_index を保証
if "sequence_index" not in anchor_df.columns:
    if "frame_timestamp_ns" in anchor_df.columns:
        anchor_df = anchor_df.sort_values("frame_timestamp_ns", kind="stable").reset_index(drop=True)
    elif "timestamp_ns" in anchor_df.columns:
        anchor_df = anchor_df.sort_values("timestamp_ns", kind="stable").reset_index(drop=True)
    elif "timestamp" in anchor_df.columns:
        anchor_df = anchor_df.sort_values("timestamp", kind="stable").reset_index(drop=True)
    else:
        anchor_df = anchor_df.reset_index(drop=True)
    anchor_df["sequence_index"] = np.arange(len(anchor_df), dtype=np.int64)
else:
    anchor_df = anchor_df.sort_values("sequence_index", kind="stable").reset_index(drop=True)

required_cols = [
    "right_x","right_y","right_z",
    "up_x","up_y","up_z",
    "lens_x","lens_y","lens_z",
    "cam_cx","cam_cy","cam_cz",
]
missing = [c for c in required_cols if c not in anchor_df.columns]
assert not missing, {"missing_columns": missing, "anchor_path": str(anchor_path)}

def _normalize(v, eps=1e-12):
    n = np.linalg.norm(v, axis=1, keepdims=True)
    n = np.maximum(n, eps)
    return v / n

def _wrap_deg(x):
    return (x + 180.0) % 360.0 - 180.0

def _angle_deg(a, b, eps=1e-12):
    a = _normalize(a, eps)
    b = _normalize(b, eps)
    d = np.sum(a * b, axis=1)
    d = np.clip(d, -1.0, 1.0)
    return np.degrees(np.arccos(d))

# world basis: x right, y up, z forward を仮定
# lens = camera forward in world
# yaw   = atan2(fx, fz)
# pitch = atan2(-fy, sqrt(fx^2 + fz^2))
# roll  = up ベクトルの傾きから近似導出
lens = anchor_df[["lens_x","lens_y","lens_z"]].to_numpy(dtype=float)
up   = anchor_df[["up_x","up_y","up_z"]].to_numpy(dtype=float)
right = anchor_df[["right_x","right_y","right_z"]].to_numpy(dtype=float)
centers = anchor_df[["cam_cx","cam_cy","cam_cz"]].to_numpy(dtype=float)

lens = _normalize(lens)
up = _normalize(up)
right = _normalize(right)

fx, fy, fz = lens[:, 0], lens[:, 1], lens[:, 2]
ux, uy, uz = up[:, 0], up[:, 1], up[:, 2]

yaw_deg = np.degrees(np.arctan2(fx, fz))
pitch_deg = np.degrees(np.arctan2(-fy, np.sqrt(np.maximum(fx * fx + fz * fz, 1e-12))))

# roll 近似:
# forward を固定したときの up の回転を world-up 基準で表す
world_up = np.tile(np.array([[0.0, 1.0, 0.0]]), (len(anchor_df), 1))
proj_world_up = world_up - np.sum(world_up * lens, axis=1, keepdims=True) * lens
proj_up = up - np.sum(up * lens, axis=1, keepdims=True) * lens
proj_world_up = _normalize(proj_world_up)
proj_up = _normalize(proj_up)

cross_u = np.cross(proj_world_up, proj_up)
sign_roll = np.sign(np.sum(cross_u * lens, axis=1))
dot_roll = np.clip(np.sum(proj_world_up * proj_up, axis=1), -1.0, 1.0)
roll_deg = np.degrees(np.arccos(dot_roll)) * sign_roll

# 連続性
delta_yaw_deg = np.zeros(len(anchor_df), dtype=float)
delta_pitch_deg = np.zeros(len(anchor_df), dtype=float)
delta_roll_deg = np.zeros(len(anchor_df), dtype=float)
delta_pos = np.zeros(len(anchor_df), dtype=float)
delta_lens_angle_deg = np.zeros(len(anchor_df), dtype=float)
delta_up_angle_deg = np.zeros(len(anchor_df), dtype=float)

if len(anchor_df) >= 2:
    delta_yaw_deg[1:] = _wrap_deg(np.diff(yaw_deg))
    delta_pitch_deg[1:] = np.diff(pitch_deg)
    delta_roll_deg[1:] = _wrap_deg(np.diff(roll_deg))
    delta_pos[1:] = np.linalg.norm(np.diff(centers, axis=0), axis=1)
    delta_lens_angle_deg[1:] = _angle_deg(lens[:-1], lens[1:])
    delta_up_angle_deg[1:] = _angle_deg(up[:-1], up[1:])

delta2_pos = np.zeros(len(anchor_df), dtype=float)
delta2_rot = np.zeros(len(anchor_df), dtype=float)
if len(anchor_df) >= 3:
    delta2_pos[2:] = np.linalg.norm(centers[2:] - 2.0 * centers[1:-1] + centers[:-2], axis=1)
    delta2_rot[2:] = np.sqrt(
        (delta_yaw_deg[2:] - delta_yaw_deg[1:-1]) ** 2 +
        (delta_pitch_deg[2:] - delta_pitch_deg[1:-1]) ** 2 +
        (delta_roll_deg[2:] - delta_roll_deg[1:-1]) ** 2
    )

anchor_pose_diag_df = anchor_df.copy()
anchor_pose_diag_df["yaw_deg"] = yaw_deg
anchor_pose_diag_df["pitch_deg"] = pitch_deg
anchor_pose_diag_df["roll_deg"] = roll_deg
anchor_pose_diag_df["delta_yaw_deg"] = delta_yaw_deg
anchor_pose_diag_df["delta_pitch_deg"] = delta_pitch_deg
anchor_pose_diag_df["delta_roll_deg"] = delta_roll_deg
anchor_pose_diag_df["delta_pos"] = delta_pos
anchor_pose_diag_df["delta_lens_angle_deg"] = delta_lens_angle_deg
anchor_pose_diag_df["delta_up_angle_deg"] = delta_up_angle_deg
anchor_pose_diag_df["delta2_pos"] = delta2_pos
anchor_pose_diag_df["delta2_rot"] = delta2_rot

# prev / next
anchor_pose_diag_df["prev_sequence_index"] = anchor_pose_diag_df["sequence_index"].shift(1)
anchor_pose_diag_df["next_sequence_index"] = anchor_pose_diag_df["sequence_index"].shift(-1)

diag_csv = anchor_dir / "full_anchor_pose_diag_arc.csv"
anchor_pose_diag_df.to_csv(diag_csv, index=False)

summary = {
    "persist_root": str(persist_root),
    "anchor_path": str(anchor_path),
    "rows": int(len(anchor_pose_diag_df)),
    "yaw_deg_min": float(np.nanmin(yaw_deg)),
    "yaw_deg_max": float(np.nanmax(yaw_deg)),
    "pitch_deg_min": float(np.nanmin(pitch_deg)),
    "pitch_deg_max": float(np.nanmax(pitch_deg)),
    "roll_deg_min": float(np.nanmin(roll_deg)),
    "roll_deg_max": float(np.nanmax(roll_deg)),
    "delta_pos_max": float(np.nanmax(delta_pos)),
    "delta_lens_angle_deg_max": float(np.nanmax(delta_lens_angle_deg)),
    "delta2_pos_max": float(np.nanmax(delta2_pos)),
    "delta2_rot_max": float(np.nanmax(delta2_rot)),
    "diag_csv": str(diag_csv),
}
print(summary)
display_stage_summary(
    "7-3",
    "anchor pose diag",
    inputs=[
        {"item": "camera_anchor_full", "path": str(anchor_path)},
    ],
    outputs=[
        {"item": "full_anchor_pose_diag", "path": str(diag_csv)},
    ],
    notes=[
        {"item": "rows", "value": int(len(anchor_pose_diag_df))},
        {"item": "pitch_range_deg", "value": f"{summary['pitch_deg_min']:.3f} .. {summary['pitch_deg_max']:.3f}"},
    ],
)
```


# 8 Anchor QC And Plot

実行順: #8 -> #9。anchor の fail / warning と可視化を先に確認する

```python
#8-1

from pathlib import Path
import json
import numpy as np
import pandas as pd

config = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8"))

def _existing(p):
    if not p:
        return None
    p = Path(p)
    return p if p.exists() else None

def _find_anchor_diag_root(search_roots):
    rel = "01_anchor/full_anchor_pose_diag_arc.csv"
    for root in search_roots:
        if root is None:
            continue
        root = Path(root)
        if root.is_file():
            root = root.parent
        if not root.exists():
            continue

        candidate_dirs = [root]
        candidate_dirs += [p for p in root.glob("*") if p.is_dir()]
        candidate_dirs += [p for p in root.glob("*/*") if p.is_dir()]

        seen = set()
        for d in candidate_dirs:
            d = d.resolve()
            if str(d) in seen:
                continue
            seen.add(str(d))
            if (d / rel).exists():
                return d
    return None

search_roots = [
    _existing(config.get("persist_root")),
    _existing(config.get("google_drive_run_root")),
    _existing(config.get("run_root")),
    _existing(config.get("persist_dir")),
    _existing(config.get("output_root")),
    _existing(config.get("project_root")),
    _existing(config.get("session_dir")),
    _existing(config.get("target_probe_root")),
    _existing(config.get("probe_root")),
    Path("/content/drive/MyDrive/trajectreview"),
    Path("/content/drive/MyDrive"),
]

persist_root = _find_anchor_diag_root(search_roots)
assert persist_root is not None, {
    "error": "full_anchor_pose_diag_arc.csv not found",
    "searched_roots": [str(p) for p in search_roots if p is not None],
}

anchor_dir = persist_root / "01_anchor"
diag_path = anchor_dir / "full_anchor_pose_diag_arc.csv"
df = pd.read_csv(diag_path)
assert not df.empty, diag_path

# ---- 閾値: まずは緩め。全落ち防止 ----
MAX_DELTA_POS = float(config.get("ANCHOR_QC_MAX_DELTA_POS", 5.0))
MAX_DELTA_LENS_ANGLE_DEG = float(config.get("ANCHOR_QC_MAX_DELTA_LENS_ANGLE_DEG", 45.0))
MAX_DELTA_UP_ANGLE_DEG = float(config.get("ANCHOR_QC_MAX_DELTA_UP_ANGLE_DEG", 45.0))
MAX_DELTA2_POS = float(config.get("ANCHOR_QC_MAX_DELTA2_POS", 5.0))
MAX_DELTA2_ROT = float(config.get("ANCHOR_QC_MAX_DELTA2_ROT", 60.0))

# warning 用
WARN_ABS_ROLL_DEG = float(config.get("ANCHOR_QC_WARN_ABS_ROLL_DEG", 45.0))
WARN_PITCH_MIN_DEG = float(config.get("ANCHOR_QC_WARN_PITCH_MIN_DEG", -89.0))
WARN_PITCH_MAX_DEG = float(config.get("ANCHOR_QC_WARN_PITCH_MAX_DEG", 89.0))

for col in [
    "delta_pos", "delta_lens_angle_deg", "delta_up_angle_deg",
    "delta2_pos", "delta2_rot", "roll_deg", "pitch_deg"
]:
    if col not in df.columns:
        df[col] = 0.0

# ---- fail: 連続性の明確な破綻だけ ----
df["fail_delta_pos"] = df["delta_pos"].abs() > MAX_DELTA_POS
df["fail_delta_lens"] = df["delta_lens_angle_deg"].abs() > MAX_DELTA_LENS_ANGLE_DEG
df["fail_delta_up"] = df["delta_up_angle_deg"].abs() > MAX_DELTA_UP_ANGLE_DEG
df["fail_delta2_pos"] = df["delta2_pos"].abs() > MAX_DELTA2_POS
df["fail_delta2_rot"] = df["delta2_rot"].abs() > MAX_DELTA2_ROT

df["anchor_qc_fail"] = (
    df["fail_delta_pos"] |
    df["fail_delta_lens"] |
    df["fail_delta_up"] |
    df["fail_delta2_pos"] |
    df["fail_delta2_rot"]
)

# ---- warning: 姿勢帯域。まだ fail に使わない ----
df["warn_roll_band"] = df["roll_deg"].abs() > WARN_ABS_ROLL_DEG
df["warn_pitch_band"] = (df["pitch_deg"] < WARN_PITCH_MIN_DEG) | (df["pitch_deg"] > WARN_PITCH_MAX_DEG)

# 先頭フレームは差分系が 0 or NaN になりやすいので fail解除
if len(df) > 0:
    first_idx = df.index[0]
    for c in ["fail_delta_pos", "fail_delta_lens", "fail_delta_up", "fail_delta2_pos", "fail_delta2_rot", "anchor_qc_fail"]:
        df.loc[first_idx, c] = False

fail_df = df[df["anchor_qc_fail"]].copy()
warn_df = df[df["warn_roll_band"] | df["warn_pitch_band"]].copy()

qc_csv = anchor_dir / "full_anchor_pose_qc_arc.csv"
fail_csv = anchor_dir / "full_anchor_pose_qc_fail_arc.csv"
warn_csv = anchor_dir / "full_anchor_pose_qc_warn_arc.csv"

df.to_csv(qc_csv, index=False)
fail_df.to_csv(fail_csv, index=False)
warn_df.to_csv(warn_csv, index=False)

summary = {
    "anchor_qc_rows": int(len(df)),
    "fail_rows": int(len(fail_df)),
    "warn_rows": int(len(warn_df)),
    "fail_rate": float(len(fail_df) / max(len(df), 1)),
    "warn_rate": float(len(warn_df) / max(len(df), 1)),
    "max_delta_pos": float(df["delta_pos"].abs().max()),
    "max_delta_lens_angle_deg": float(df["delta_lens_angle_deg"].abs().max()),
    "max_delta_up_angle_deg": float(df["delta_up_angle_deg"].abs().max()),
    "max_delta2_pos": float(df["delta2_pos"].abs().max()),
    "max_delta2_rot": float(df["delta2_rot"].abs().max()),
    "roll_deg_min": float(df["roll_deg"].min()),
    "roll_deg_max": float(df["roll_deg"].max()),
    "pitch_deg_min": float(df["pitch_deg"].min()),
    "pitch_deg_max": float(df["pitch_deg"].max()),
    "qc_csv": str(qc_csv),
    "fail_csv": str(fail_csv),
    "warn_csv": str(warn_csv),
}
print(summary)
display_stage_summary(
    "8-1",
    "anchor qc",
    inputs=[
        {"item": "full_anchor_pose_diag", "path": str(diag_path)},
    ],
    outputs=[
        {"item": "full_anchor_pose_qc", "path": str(qc_csv)},
        {"item": "full_anchor_pose_fail", "path": str(fail_csv)},
        {"item": "full_anchor_pose_warn", "path": str(warn_csv)},
    ],
    notes=[
        {"item": "fail_count", "value": int(summary["fail_count"])},
        {"item": "warn_count", "value": int(summary["warn_count"])},
    ],
)
```

```python
#8-2

from pathlib import Path
import json
import numpy as np
import pandas as pd

config = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8"))

def _existing(p):
    if not p:
        return None
    p = Path(p)
    return p if p.exists() else None

def _find_anchor_root(search_roots):
    rels = [
        "01_anchor/camera_anchor_full_arc.csv",
        "01_anchor/full_anchor_pose_diag_arc.csv",
        "01_anchor/camera_center_matrix_arc.csv",
        "01_anchor/camera_orientation_full_arc.csv",
    ]
    for root in search_roots:
        if root is None:
            continue
        root = Path(root)
        if root.is_file():
            root = root.parent
        if not root.exists():
            continue

        candidate_dirs = [root]
        candidate_dirs += [p for p in root.glob("*") if p.is_dir()]
        candidate_dirs += [p for p in root.glob("*/*") if p.is_dir()]

        seen = set()
        for d in candidate_dirs:
            d = d.resolve()
            if str(d) in seen:
                continue
            seen.add(str(d))
            if any((d / rel).exists() for rel in rels):
                return d
    return None

def _pick_first_existing(paths):
    for p in paths:
        if p.exists():
            return p
    return None

def _resolve_center_cols(df: pd.DataFrame):
    candidates = [
        ("cam_cx", "cam_cy", "cam_cz"),
        ("cx", "cy", "cz"),
        ("camera_center_x", "camera_center_y", "camera_center_z"),
        ("tx", "ty", "tz"),
    ]
    for cols in candidates:
        if all(c in df.columns for c in cols):
            return cols
    raise ValueError(f"camera center columns not found; columns={list(df.columns)}")

def _resolve_lens_cols(df: pd.DataFrame):
    candidates = [
        ("lens_x", "lens_y", "lens_z"),
        ("forward_x", "forward_y", "forward_z"),
        ("dir_x", "dir_y", "dir_z"),
    ]
    for cols in candidates:
        if all(c in df.columns for c in cols):
            return cols
    return None

search_roots = [
    _existing(config.get("persist_root")),
    _existing(config.get("google_drive_run_root")),
    _existing(config.get("run_root")),
    _existing(config.get("persist_dir")),
    _existing(config.get("output_root")),
    _existing(config.get("project_root")),
    _existing(config.get("session_dir")),
    _existing(config.get("target_probe_root")),
    _existing(config.get("probe_root")),
    Path("/content/drive/MyDrive/trajectreview"),
    Path("/content/drive/MyDrive"),
]

persist_root = _find_anchor_root(search_roots)
assert persist_root is not None, {
    "error": "anchor root not found",
    "searched_roots": [str(p) for p in search_roots if p is not None],
}

anchor_dir = persist_root / "01_anchor"
anchor_csv = _pick_first_existing([
    anchor_dir / "full_anchor_pose_diag_arc.csv",
    anchor_dir / "camera_anchor_full_arc.csv",
    anchor_dir / "camera_center_matrix_arc.csv",
])

assert anchor_csv is not None, {"missing_anchor_csv_in": str(anchor_dir)}

df = pd.read_csv(anchor_csv)
assert not df.empty, anchor_csv

# sequence 順に並べる
if "sequence_index" in df.columns:
    df = df.sort_values("sequence_index", kind="stable").reset_index(drop=True)
elif "frame_timestamp_ns" in df.columns:
    df = df.sort_values("frame_timestamp_ns", kind="stable").reset_index(drop=True)
elif "timestamp_ns" in df.columns:
    df = df.sort_values("timestamp_ns", kind="stable").reset_index(drop=True)
elif "timestamp" in df.columns:
    df = df.sort_values("timestamp", kind="stable").reset_index(drop=True)
else:
    df = df.reset_index(drop=True)

cx_col, cy_col, cz_col = _resolve_center_cols(df)
lens_cols = _resolve_lens_cols(df)

plotly_html = anchor_dir / "full_anchor_preview_arc.html"
plotly_png = anchor_dir / "full_anchor_preview_arc.png"

centers = df[[cx_col, cy_col, cz_col]].to_numpy(dtype=float)

# 矢印長
bbox_min = np.nanmin(centers, axis=0)
bbox_max = np.nanmax(centers, axis=0)
diag = float(np.linalg.norm(bbox_max - bbox_min))
arrow_scale = max(diag * 0.03, 0.02)

# Plotly 可視化
try:
    import plotly.graph_objects as go

    fig = go.Figure()

    fig.add_trace(go.Scatter3d(
        x=centers[:, 0],
        y=centers[:, 1],
        z=centers[:, 2],
        mode="lines+markers",
        name="camera_centers",
        marker=dict(size=2),
        line=dict(width=4),
        text=[f"idx={i}" for i in range(len(df))],
        hovertemplate="x=%{x:.3f}<br>y=%{y:.3f}<br>z=%{z:.3f}<br>%{text}<extra></extra>",
    ))

    if lens_cols is not None:
        lens = df[list(lens_cols)].to_numpy(dtype=float)
        lens_norm = np.linalg.norm(lens, axis=1, keepdims=True)
        lens_norm = np.maximum(lens_norm, 1e-12)
        lens = lens / lens_norm
        ends = centers + lens * arrow_scale

        step = max(len(df) // 40, 1)  # 矢印が多すぎないよう間引き
        for i in range(0, len(df), step):
            fig.add_trace(go.Scatter3d(
                x=[centers[i, 0], ends[i, 0]],
                y=[centers[i, 1], ends[i, 1]],
                z=[centers[i, 2], ends[i, 2]],
                mode="lines",
                name="lens_dir" if i == 0 else None,
                showlegend=(i == 0),
                line=dict(width=3),
                hoverinfo="skip",
            ))

    fig.update_layout(
        title="Full Anchor Preview",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, t=40, b=0),
    )

    fig.write_html(str(plotly_html), include_plotlyjs="cdn")
    preview_result = {
        "plotly_preview": "saved",
        "anchor_csv": str(anchor_csv),
        "html": str(plotly_html),
        "rows": int(len(df)),
        "center_cols": [cx_col, cy_col, cz_col],
        "lens_cols": list(lens_cols) if lens_cols is not None else None,
    }
except Exception as e:
    preview_result = {
        "plotly_preview": "skipped",
        "reason": repr(e),
        "anchor_csv": str(anchor_csv),
        "rows": int(len(df)),
        "available_columns": list(df.columns),
    }

print(preview_result)
display_stage_summary(
    "8-2",
    "full anchor preview",
    inputs=[
        {"item": "anchor_csv", "path": str(anchor_csv)},
    ],
    outputs=[
        {"item": "full_anchor_preview_html", "path": str(plotly_html)},
        {"item": "full_anchor_preview_png", "path": str(plotly_png)},
    ],
    notes=[
        {"item": "rows", "value": int(preview_result["rows"])},
        {"item": "center_cols", "value": "|".join(preview_result.get("center_cols", [])) if preview_result.get("center_cols") else ""},
        {"item": "lens_cols", "value": "|".join(preview_result.get("lens_cols", [])) if preview_result.get("lens_cols") else ""},
    ],
)
```


# 9 Record Manifest And Chunk Plan

実行順: #9 -> #10。chunk 条件は #2 の設定値だけを参照する

```python
#9-1
from pathlib import Path
import csv
import json

import imageio.v3 as iio
import numpy as np
import pandas as pd
from PIL import Image

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
images_dir = Path(ctx["images_dir"])
frame_record_path = Path(ctx["frame_record_path"])
frame_pose_index_path = Path(ctx["frame_pose_index_path"])
manifest_dir = Path(ctx["manifest_dir"])

CANONICAL_ORIENTATION_POLICY = "upright_rot90cw_from_correcting"
BLUR_THRESHOLD = 8.0

with frame_record_path.open("r", encoding="utf-8") as f:
    frame_records = [json.loads(line) for line in f if line.strip()]

frame_pose_df = pd.read_csv(frame_pose_index_path) if frame_pose_index_path.exists() else pd.DataFrame()
image_name_by_record_index = {}
if len(frame_pose_df) > 0:
    image_name_col = next((c for c in ["image_file_name", "imageFileName", "frame_name"] if c in frame_pose_df.columns), None)
    record_index_col = next((c for c in ["pose_record_index", "record_index"] if c in frame_pose_df.columns), None)
    if image_name_col is not None and record_index_col is not None:
        tmp = frame_pose_df[[record_index_col, image_name_col]].copy()
        tmp = tmp.dropna()
        tmp[image_name_col] = tmp[image_name_col].astype(str).str.strip()
        tmp = tmp.loc[tmp[image_name_col] != ""]
        image_name_by_record_index = {
            int(getattr(row, record_index_col)): getattr(row, image_name_col)
            for row in tmp.itertuples(index=False)
        }
    elif "frame_index" in frame_pose_df.columns:
        sorted_image_names = sorted([
            *[p.name for p in images_dir.glob("*.jpg")],
            *[p.name for p in images_dir.glob("*.jpeg")],
            *[p.name for p in images_dir.glob("*.png")],
            *[p.name for p in images_dir.glob("*.JPG")],
            *[p.name for p in images_dir.glob("*.JPEG")],
            *[p.name for p in images_dir.glob("*.PNG")],
        ])
        record_index_col = next((c for c in ["pose_record_index", "record_index"] if c in frame_pose_df.columns), None)
        if record_index_col is not None:
            for row in frame_pose_df.itertuples(index=False):
                frame_idx = int(getattr(row, "frame_index"))
                if 0 <= frame_idx < len(sorted_image_names):
                    image_name_by_record_index[int(getattr(row, record_index_col))] = sorted_image_names[frame_idx]

def ranked_image_dirs(primary_dir: Path, frame_record_path: Path):
    session_outer = frame_record_path.parent
    session_root = session_outer / "trajectreview" if (session_outer / "trajectreview").exists() else session_outer
    candidates = [
        primary_dir,
        session_root / "images",
        session_root / "image",
        session_outer / "images",
        session_outer / "image",
        session_outer / "trajectreview" / "images",
        session_outer / "trajectreview" / "image",
    ]
    ranked = []
    seen = set()
    for p in candidates:
        key = str(p)
        if key in seen or not p.exists():
            continue
        seen.add(key)
        image_count = (
            len(list(p.glob("*.jpg"))) +
            len(list(p.glob("*.jpeg"))) +
            len(list(p.glob("*.png"))) +
            len(list(p.glob("*.JPG"))) +
            len(list(p.glob("*.JPEG"))) +
            len(list(p.glob("*.PNG")))
        )
        ranked.append((p, image_count))
    return sorted(ranked, key=lambda x: (-x[1], len(str(x[0]))))

def lap_var(image_path: Path) -> float:
    img = iio.imread(image_path)
    if img.ndim == 3:
        gray = img[..., :3].mean(axis=2).astype(np.float32)
    else:
        gray = img.astype(np.float32)
    gx = gray[:, 1:] - gray[:, :-1]
    gy = gray[1:, :] - gray[:-1, :]
    return float(np.var(gx) + np.var(gy))

def read_actual_wh(image_path: Path):
    with Image.open(image_path) as img:
        width, height = img.size
    return int(width), int(height)

def normalize_intrinsics_to_upright(intr, actual_width: int, actual_height: int):
    fx = intr.get("fx")
    fy = intr.get("fy")
    cx = intr.get("cx")
    cy = intr.get("cy")
    intr_width = intr.get("width")
    intr_height = intr.get("height")

    if None in [fx, fy, cx, cy, intr_width, intr_height]:
        return {
            "intrinsics_case": "missing_intrinsics",
            "rotation_applied_deg": None,
            "fx_canonical": None,
            "fy_canonical": None,
            "cx_canonical": None,
            "cy_canonical": None,
            "width_canonical": None,
            "height_canonical": None,
        }

    fx = float(fx)
    fy = float(fy)
    cx = float(cx)
    cy = float(cy)
    intr_width = int(intr_width)
    intr_height = int(intr_height)

    if intr_width == actual_width and intr_height == actual_height:
        return {
            "intrinsics_case": "already_upright",
            "rotation_applied_deg": 0,
            "fx_canonical": fx,
            "fy_canonical": fy,
            "cx_canonical": cx,
            "cy_canonical": cy,
            "width_canonical": actual_width,
            "height_canonical": actual_height,
        }

    if intr_width == actual_height and intr_height == actual_width:
        return {
            "intrinsics_case": "rot90cw_intrinsics_fixed",
            "rotation_applied_deg": 90,
            "fx_canonical": fy,
            "fy_canonical": fx,
            "cx_canonical": float(intr_height - 1) - cy,
            "cy_canonical": cx,
            "width_canonical": actual_width,
            "height_canonical": actual_height,
        }

    return {
        "intrinsics_case": "dimension_mismatch",
        "rotation_applied_deg": None,
        "fx_canonical": None,
        "fy_canonical": None,
        "cx_canonical": None,
        "cy_canonical": None,
        "width_canonical": None,
        "height_canonical": None,
    }

image_dir_ranking = ranked_image_dirs(images_dir, frame_record_path)
resolved_images_dir = image_dir_ranking[0][0]
rows = []
for rec in sorted(frame_records, key=lambda x: int(x.get("frameTimestampNs", 0))):
    image_name = str(rec.get("imageFileName", "") or "").strip()
    if not image_name:
        record_index = rec.get("recordIndex")
        if record_index is not None:
            image_name = str(image_name_by_record_index.get(int(record_index), "")).strip()
    image_path = resolved_images_dir / image_name if image_name else None
    image_exists = bool(image_name) and image_path.exists()
    intr = rec.get("imageIntrinsics") or {}
    pose = rec.get("pose") or {}
    blur_score = lap_var(image_path) if image_exists else None
    actual_width = None
    actual_height = None
    intr_norm = {
        "intrinsics_case": "image_missing",
        "rotation_applied_deg": None,
        "fx_canonical": None,
        "fy_canonical": None,
        "cx_canonical": None,
        "cy_canonical": None,
        "width_canonical": None,
        "height_canonical": None,
    }
    if image_exists:
        actual_width, actual_height = read_actual_wh(image_path)
        intr_norm = normalize_intrinsics_to_upright(intr, actual_width, actual_height)
    rows.append({
        "session_id": rec.get("sessionId"),
        "record_index": rec.get("recordIndex"),
        "frame_timestamp_ns": rec.get("frameTimestampNs"),
        "capture_timestamp_ns": rec.get("captureTimestampNs"),
        "tracking_state": rec.get("trackingState"),
        "image_file_name": image_name,
        "image_path": str(image_path) if image_path else "",
        "resolved_images_dir": str(resolved_images_dir),
        "image_name_source": "frame_record" if str(rec.get("imageFileName", "") or "").strip() else "frame_pose_index_fallback",
        "image_exists": image_exists,
        "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
        "actual_width": actual_width,
        "actual_height": actual_height,
        "fx": intr.get("fx"),
        "fy": intr.get("fy"),
        "cx": intr.get("cx"),
        "cy": intr.get("cy"),
        "width": intr.get("width"),
        "height": intr.get("height"),
        "intrinsics_case": intr_norm["intrinsics_case"],
        "rotation_applied_deg": intr_norm["rotation_applied_deg"],
        "fx_canonical": intr_norm["fx_canonical"],
        "fy_canonical": intr_norm["fy_canonical"],
        "cx_canonical": intr_norm["cx_canonical"],
        "cy_canonical": intr_norm["cy_canonical"],
        "width_canonical": intr_norm["width_canonical"],
        "height_canonical": intr_norm["height_canonical"],
        "tx": pose.get("tx"),
        "ty": pose.get("ty"),
        "tz": pose.get("tz"),
        "qx": pose.get("qx"),
        "qy": pose.get("qy"),
        "qz": pose.get("qz"),
        "qw": pose.get("qw"),
        "blur_score": blur_score,
    })

manifest_df = pd.DataFrame(rows)
manifest_df.to_csv(manifest_dir / "input_frame_manifest.csv", index=False, encoding="utf-8")

qc_df = manifest_df.copy()
qc_df["qc_tracking_ok"] = qc_df["tracking_state"].fillna("") == "TRACKING"
qc_df["qc_image_ok"] = qc_df["image_exists"].fillna(False)
qc_df["qc_orientation_ok"] = qc_df["intrinsics_case"].isin(["already_upright", "rot90cw_intrinsics_fixed"])
qc_df["qc_intrinsics_ok"] = qc_df[["fx_canonical", "fy_canonical", "cx_canonical", "cy_canonical", "width_canonical", "height_canonical"]].notna().all(axis=1)
qc_df["qc_pose_ok"] = qc_df[["tx", "ty", "tz", "qx", "qy", "qz", "qw"]].notna().all(axis=1)
qc_df["blur_score"] = pd.to_numeric(qc_df["blur_score"], errors="coerce")
qc_df["qc_blur_ok"] = qc_df["blur_score"].fillna(0.0).ge(BLUR_THRESHOLD).infer_objects(copy=False)
qc_df["qc_pass"] = qc_df[["qc_tracking_ok", "qc_image_ok", "qc_orientation_ok", "qc_intrinsics_ok", "qc_pose_ok"]].all(axis=1)
qc_df["skip_reason"] = ""
qc_df.loc[~qc_df["qc_tracking_ok"], "skip_reason"] = "tracking_not_ok"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_image_ok"], "skip_reason"] = "image_missing"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_orientation_ok"], "skip_reason"] = "orientation_mismatch"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_intrinsics_ok"], "skip_reason"] = "intrinsics_missing"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_pose_ok"], "skip_reason"] = "pose_missing"
qc_df.to_csv(manifest_dir / "input_frame_qc.csv", index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)

def quat_to_rot(qx, qy, qz, qw):
    xx, yy, zz = qx*qx, qy*qy, qz*qz
    xy, xz, yz = qx*qy, qx*qz, qy*qz
    wx, wy, wz = qw*qx, qw*qy, qw*qz
    return np.array([
        [1 - 2*(yy + zz), 2*(xy - wz), 2*(xz + wy)],
        [2*(xy + wz), 1 - 2*(xx + zz), 2*(yz - wx)],
        [2*(xz - wy), 2*(yz + wx), 1 - 2*(xx + yy)],
    ], dtype=np.float32)

def pose_to_w2c(row):
    R_c2w = quat_to_rot(float(row.qx), float(row.qy), float(row.qz), float(row.qw))
    t_c2w = np.array([float(row.tx), float(row.ty), float(row.tz)], dtype=np.float32)
    R_w2c = R_c2w.T
    t_w2c = -R_w2c @ t_c2w
    out = np.eye(4, dtype=np.float32)
    out[:3, :3] = R_w2c
    out[:3, 3] = t_w2c
    return out

def build_K(row):
    return np.array([
        [float(row.fx_canonical), 0.0, float(row.cx_canonical)],
        [0.0, float(row.fy_canonical), float(row.cy_canonical)],
        [0.0, 0.0, 1.0],
    ], dtype=np.float32)

adopt_df = qc_df.loc[qc_df["qc_pass"]].copy().sort_values("frame_timestamp_ns").reset_index(drop=True)
if len(adopt_df) < 2:
    fail_counts = {
        "frame_record_count": int(len(qc_df)),
        "qc_pass_count": int(len(adopt_df)),
        "tracking_not_ok": int((~qc_df["qc_tracking_ok"]).sum()),
        "image_missing": int((~qc_df["qc_image_ok"]).sum()),
        "orientation_mismatch": int((~qc_df["qc_orientation_ok"]).sum()),
        "intrinsics_missing": int((~qc_df["qc_intrinsics_ok"]).sum()),
        "pose_missing": int((~qc_df["qc_pose_ok"]).sum()),
        "blur_low_diag_only": int((~qc_df["qc_blur_ok"]).sum()),
        "skip_reason_counts": qc_df["skip_reason"].value_counts(dropna=False).to_dict(),
    }
    (manifest_dir / "qc_failure_summary.json").write_text(json.dumps(fail_counts, indent=2, ensure_ascii=False), encoding="utf-8")
    raise AssertionError(fail_counts)

adopted_rows = []
last_t = None
last_R = None
for row in adopt_df.itertuples(index=False):
    t = np.array([float(row.tx), float(row.ty), float(row.tz)], dtype=np.float32)
    R = quat_to_rot(float(row.qx), float(row.qy), float(row.qz), float(row.qw))
    baseline = None if last_t is None else float(np.linalg.norm(t - last_t))
    rot_delta = None if last_R is None else float(np.degrees(np.arccos(np.clip((np.trace(last_R.T @ R) - 1.0) / 2.0, -1.0, 1.0))))
    geometric_adopt = last_t is None or (baseline >= 0.05) or (rot_delta is not None and rot_delta >= 3.0)
    blur_boost = bool(row.qc_blur_ok) if pd.notna(row.qc_blur_ok) else False
    adopt = geometric_adopt or (last_t is None and blur_boost)
    adopted_rows.append({
        **row._asdict(),
        "baseline_from_prev_adopted_m": baseline,
        "rotation_from_prev_adopted_deg": rot_delta,
        "geometric_adopt": geometric_adopt,
        "anchor_input_adopted": adopt,
        "anchor_input_skip_reason": "" if adopt else "baseline_small",
    })
    if adopt:
        last_t = t
        last_R = R

anchor_input_df = pd.DataFrame(adopted_rows)
anchor_input_df.to_csv(manifest_dir / "pose_conversion_check.csv", index=False, encoding="utf-8")

selected_df = anchor_input_df.loc[anchor_input_df["anchor_input_adopted"]].copy().reset_index(drop=True)
assert len(selected_df) >= 2, {"selected_df": len(selected_df)}

Ks = np.stack([build_K(row) for row in selected_df.itertuples(index=False)], axis=0)
exts = np.stack([pose_to_w2c(row) for row in selected_df.itertuples(index=False)], axis=0)
np.save(manifest_dir / "intrinsics.npy", Ks)
np.save(manifest_dir / "extrinsics_w2c_arc.npy", exts)
selected_df.to_csv(manifest_dir / "da3_input_manifest.csv", index=False, encoding="utf-8")

k_check = selected_df[[
    "image_file_name",
    "canonical_orientation_policy",
    "intrinsics_case",
    "rotation_applied_deg",
    "width",
    "height",
    "actual_width",
    "actual_height",
    "width_canonical",
    "height_canonical",
    "fx",
    "fy",
    "cx",
    "cy",
    "fx_canonical",
    "fy_canonical",
    "cx_canonical",
    "cy_canonical",
]].copy()
k_check["resize_mode"] = "native"
k_check.to_csv(manifest_dir / "k_resize_check.csv", index=False, encoding="utf-8")

orientation_summary = {
    "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
    "already_upright_count": int((manifest_df["intrinsics_case"] == "already_upright").sum()),
    "rot90cw_intrinsics_fixed_count": int((manifest_df["intrinsics_case"] == "rot90cw_intrinsics_fixed").sum()),
    "dimension_mismatch_count": int((manifest_df["intrinsics_case"] == "dimension_mismatch").sum()),
    "image_missing_count": int((manifest_df["intrinsics_case"] == "image_missing").sum()),
}
(manifest_dir / "orientation_summary.json").write_text(json.dumps(orientation_summary, indent=2, ensure_ascii=False), encoding="utf-8")

summary = {
    "frame_record_count": int(len(manifest_df)),
    "qc_pass_count": int(len(adopt_df)),
    "qc_skip_count": int((~qc_df["qc_pass"]).sum()),
    "resolved_images_dir": str(resolved_images_dir),
    "resolved_images_dir_file_count": int(image_dir_ranking[0][1]),
    "frame_pose_index_path": str(frame_pose_index_path),
    "frame_pose_fallback_mapping_count": int(len(image_name_by_record_index)),
    "selected_count": int(len(selected_df)),
    "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
    "intrinsics_path": str(manifest_dir / "intrinsics.npy"),
    "extrinsics_path": str(manifest_dir / "extrinsics_w2c_arc.npy"),
    "orientation_summary_path": str(manifest_dir / "orientation_summary.json"),
}
extrinsics_source_summary = {
    "artifact": "extrinsics_w2c_arc.npy",
    "artifact_path": str(manifest_dir / "extrinsics_w2c_arc.npy"),
    "generated_by": "section_9_1.pose_to_w2c",
    "source_record_path": str(frame_record_path),
    "source_fields": ["pose.tx", "pose.ty", "pose.tz", "pose.qx", "pose.qy", "pose.qz", "pose.qw"],
    "source_sort_key": "frameTimestampNs",
    "matrix_space": "world_to_camera",
    "record_count": int(len(selected_df)),
}
(manifest_dir / "qc_summary.json").write_text(json.dumps({
    "frame_record_count": summary["frame_record_count"],
    "qc_pass_count": summary["qc_pass_count"],
    "qc_skip_count": summary["qc_skip_count"],
    "frame_record_path": str(frame_record_path),
    "images_dir": str(images_dir),
    "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
}, indent=2, ensure_ascii=False), encoding="utf-8")
(manifest_dir / "da3_input_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
(manifest_dir / "extrinsics_w2c_arc_source_summary.json").write_text(json.dumps(extrinsics_source_summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
display_stage_summary(
    "9-1",
    "record-native manifest rebuild",
    inputs=[
        {"item": "frame_record", "path": str(frame_record_path)},
        {"item": "images_dir", "path": str(images_dir)},
        {"item": "frame_pose_index", "path": str(frame_pose_index_path)},
    ],
    outputs=[
        {"item": "input_frame_manifest", "path": str(manifest_dir / "input_frame_manifest.csv")},
        {"item": "input_frame_qc", "path": str(manifest_dir / "input_frame_qc.csv")},
        {"item": "pose_conversion_check", "path": str(manifest_dir / "pose_conversion_check.csv")},
        {"item": "da3_input_manifest", "path": str(manifest_dir / "da3_input_manifest.csv")},
        {"item": "intrinsics", "path": str(manifest_dir / "intrinsics.npy")},
        {"item": "extrinsics_w2c", "path": str(manifest_dir / "extrinsics_w2c_arc.npy")},
        {"item": "orientation_summary", "path": str(manifest_dir / "orientation_summary.json")},
        {"item": "da3_input_summary", "path": str(manifest_dir / "da3_input_summary.json")},
    ],
    notes=[
        {"item": "extrinsics_source_rule", "value": "frame_record pose(tx,ty,tz,qx,qy,qz,qw) -> pose_to_w2c -> extrinsics_w2c_arc.npy"},
    ],
)
```

```python
#9-2
from pathlib import Path
import json
import pandas as pd

ctx = load_ctx()
manifest_dir = Path(ctx['manifest_dir'])
managed_dirs = json.loads(Path('/content/runbook_managed_dirs.json').read_text(encoding='utf-8'))
record_dir = Path(managed_dirs['02_records'])
record_dir.mkdir(parents=True, exist_ok=True)
anchor_diag = pd.read_csv(Path(managed_dirs['01_anchor']) / 'full_anchor_pose_diag_arc.csv')
anchor_keep_cols = [c for c in ['sequence_index','roll_deg','pitch_deg','yaw_deg','delta_roll_deg','delta_pitch_deg','delta_yaw_deg','delta_pos','delta2_pos','delta2_rot'] if c in anchor_diag.columns]
anchor_join = anchor_diag[anchor_keep_cols].copy() if anchor_keep_cols else pd.DataFrame()

p = manifest_dir / 'da3_input_manifest.csv'
assert p.exists(), p
df = pd.read_csv(p)
ts_col = next((c for c in ['frame_timestamp_ns','timestamp_ns','timestamp'] if c in df.columns), None)
df = append_sequence_columns(df, ts_col or 'frame_timestamp_ns')
if not anchor_join.empty and 'sequence_index' in df.columns:
    df = df.merge(anchor_join, on='sequence_index', how='left', suffixes=('', '_anchor'))
df['is_time_adjacent_valid'] = True
df.to_csv(p, index=False, encoding='utf-8')
df.to_csv(record_dir / 'record_manifest.csv', index=False, encoding='utf-8')
print({'updated_manifest': str(p), 'rows': len(df)})
display_stage_summary(
    "9-2",
    "record manifest refresh",
    inputs=[
        {"item": "da3_input_manifest", "path": str(p)},
        {"item": "full_anchor_pose_diag", "path": str(Path(managed_dirs['01_anchor']) / 'full_anchor_pose_diag_arc.csv')},
    ],
    outputs=[
        {"item": "record_manifest", "path": str(record_dir / 'record_manifest.csv')},
        {"item": "da3_input_manifest_updated", "path": str(p)},
    ],
    notes=[
        {"item": "rows", "value": int(len(df))},
    ],
)
```

```python
#9-3
from pathlib import Path
import json

config = json.loads(Path('/content/config_snapshot.json').read_text(encoding='utf-8'))
config_view = pd.DataFrame([
    {'item': 'BATCH_SIZE', 'value': config['BATCH_SIZE']},
    {'item': 'CHUNK_SIZE', 'value': config['CHUNK_SIZE']},
    {'item': 'CHUNK_STEP', 'value': config['CHUNK_STEP']},
    {'item': 'ADOPT_SIZE', 'value': config['ADOPT_SIZE']},
    {'item': 'PROCESS_RES', 'value': config['PROCESS_RES']},
])
display(config_view)
display_stage_summary(
    "9-3",
    "config snapshot preview",
    inputs=[
        {"item": "config_snapshot", "path": "/content/config_snapshot.json"},
    ],
    outputs=[],
    notes=config_view.to_dict(orient='records'),
)
```

```python
#9-4

from pathlib import Path
import json
import math
import hashlib

import numpy as np
import pandas as pd

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
config_snapshot = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8")) if Path("/content/config_snapshot.json").exists() else {}

manifest_dir = Path(ctx["manifest_dir"])
persist_root = Path(ctx.get("persist_root", manifest_dir.parent))
pipeline_slug = ctx.get("pipeline_slug", config_snapshot.get("PIPELINE_SLUG", "da3_ngl_batch_v01"))

pipeline_root = persist_root / pipeline_slug
anchor_dir = persist_root / "01_anchor"
chunk_manifest_dir = pipeline_root / "manifests"
batch_runs_dir = pipeline_root / "04_batch_runs"
merged_dir = pipeline_root / "05_merge"

for p in [pipeline_root, chunk_manifest_dir, batch_runs_dir, merged_dir]:
    p.mkdir(parents=True, exist_ok=True)

MODEL_ID = "depth-anything/DA3NESTED-GIANT-LARGE-1.1"
BUNDLE_MODEL_SLUG = "nestedgiantlarge11"
PROCESS_RES = int(config_snapshot.get("PROCESS_RES", 504))
CHUNK_SIZE = int(config_snapshot.get("CHUNK_SIZE", 18))
CHUNK_STEP = int(config_snapshot.get("CHUNK_STEP", 12))
ADOPT_SIZE = int(config_snapshot.get("ADOPT_SIZE", 12))
BATCH_SIZE = int(config_snapshot.get("BATCH_SIZE", 3))

config = {
    "MODEL_ID": MODEL_ID,
    "BUNDLE_MODEL_SLUG": BUNDLE_MODEL_SLUG,
    "PROCESS_RES": PROCESS_RES,
    "CHUNK_SIZE": CHUNK_SIZE,
    "CHUNK_STEP": CHUNK_STEP,
    "ADOPT_SIZE": ADOPT_SIZE,
    "BATCH_SIZE": BATCH_SIZE,
    "GLOBAL_CAMERA_SOURCE": "manifests/extrinsics_w2c_arc.npy",
    "CANONICAL_ANCHOR_MODE": "lens=-c2w_z, up=c2w_y",
    "PIPELINE_SLUG": pipeline_slug,
    "TARGET_POLICY": "canonical_full_set",
    "TEST_EXECUTION_LIMITER_LOCATION": "#11-3",
}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

input_manifest_path = manifest_dir / "da3_input_manifest.csv"
intrinsics_path = manifest_dir / "intrinsics.npy"
extrinsics_path = manifest_dir / "extrinsics_w2c_arc.npy"

assert input_manifest_path.exists(), input_manifest_path
assert intrinsics_path.exists(), intrinsics_path
assert extrinsics_path.exists(), extrinsics_path

input_df = pd.read_csv(input_manifest_path).reset_index(drop=True)
assert len(input_df) >= 2, {"frame_count": len(input_df)}

input_extrinsics = np.load(extrinsics_path).astype(np.float32)
assert input_extrinsics.shape[0] == len(input_df), {
    "input_extrinsics_shape": tuple(input_extrinsics.shape),
    "frame_count": len(input_df),
}
assert input_df["record_index"].notnull().all(), "record_index contains null"
assert input_df["record_index"].is_unique, "record_index must be unique"
assert input_df["frame_timestamp_ns"].notnull().all(), "frame_timestamp_ns contains null"
assert input_df["frame_timestamp_ns"].is_monotonic_increasing, "frame_timestamp_ns must be monotonic increasing"

config["INPUT_MANIFEST_SHA256"] = sha256_file(input_manifest_path)
config["INPUT_EXTRINSICS_SHA256"] = sha256_file(extrinsics_path)
(pipeline_root / "pipeline_config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

def to_4x4(ext):
    ext = np.asarray(ext).astype(np.float32)
    if ext.shape == (4, 4):
        return ext
    if ext.shape == (3, 4):
        M = np.eye(4, dtype=np.float32)
        M[:3, :] = ext
        return M
    raise ValueError(f"unexpected extrinsic shape: {ext.shape}")

# ----- global chunk 生成 -----
chunks = []
start_pos = 0
chunk_id = 0

while start_pos < len(input_df):
    end_pos = min(start_pos + CHUNK_SIZE, len(input_df))
    chunk_df = input_df.iloc[start_pos:end_pos].copy().reset_index(drop=True)
    if len(chunk_df) < 2:
        break

    chunk_name = f"chunk_{chunk_id:04d}_{start_pos:05d}_{end_pos-1:05d}"
    chunk_df["chunk_id"] = int(chunk_id)
    chunk_df["chunk_name"] = chunk_name
    chunk_df["chunk_local_index"] = range(len(chunk_df))

    adopt_local_start = max(0, len(chunk_df) - min(ADOPT_SIZE, len(chunk_df)))
    adopt_local_end = len(chunk_df) - 1
    chunk_df["is_adopted_region"] = chunk_df["chunk_local_index"] >= adopt_local_start

    chunk_csv = chunk_manifest_dir / f"{chunk_name}.csv"
    chunk_df.to_csv(chunk_csv, index=False, encoding="utf-8")

    chunks.append({
        "chunk_id": int(chunk_id),
        "chunk_name": chunk_name,
        "global_start": int(start_pos),
        "global_end": int(end_pos - 1),
        "frame_count": int(len(chunk_df)),
        "adopt_local_start": int(adopt_local_start),
        "adopt_local_end": int(adopt_local_end),
        "chunk_csv": str(chunk_csv),
    })

    if end_pos == len(input_df):
        break

    start_pos += CHUNK_STEP
    chunk_id += 1

all_chunks_df = pd.DataFrame(chunks)
assert len(all_chunks_df) >= 1, "no chunks generated"

chunk_index_all_path = chunk_manifest_dir / "chunk_index_all.csv"
all_chunks_df.to_csv(chunk_index_all_path, index=False, encoding="utf-8")

# ----- 正本 target = 全chunk集合 -----
target_chunks_df = all_chunks_df.copy().reset_index(drop=True)
target_chunks_df["target_local_chunk_index"] = range(len(target_chunks_df))

chunk_index_target_path = chunk_manifest_dir / "chunk_index_target.csv"
target_chunks_df.to_csv(chunk_index_target_path, index=False, encoding="utf-8")

# ----- batch plan は target_local_chunk_index 基準で全件生成 -----
batch_rows = []
batch_count = math.ceil(len(target_chunks_df) / BATCH_SIZE)

for batch_index in range(batch_count):
    s = batch_index * BATCH_SIZE
    e = min(s + BATCH_SIZE, len(target_chunks_df))
    batch_rows.append({
        "batch_index": int(batch_index),
        "chunk_from": int(s),       # target_local_chunk_index の開始
        "chunk_to": int(e - 1),     # target_local_chunk_index の終了
        "chunk_count": int(e - s),
        "chunk_names": "|".join(target_chunks_df.iloc[s:e]["chunk_name"].tolist()),
        "global_chunk_ids": "|".join(target_chunks_df.iloc[s:e]["chunk_id"].astype(int).astype(str).tolist()),
    })

batch_plan_df = pd.DataFrame(batch_rows)
batch_plan_path = chunk_manifest_dir / "batch_plan.csv"
batch_plan_df.to_csv(batch_plan_path, index=False, encoding="utf-8")

# ----- full anchor のコピー/索引化（#2系生成物の利用） -----
camera_anchor_full_path = anchor_dir / "camera_anchor_full_arc.csv"
assert camera_anchor_full_path.exists(), camera_anchor_full_path

anchor_df = pd.read_csv(camera_anchor_full_path)
assert not anchor_df.empty, camera_anchor_full_path
assert "record_index" in anchor_df.columns, anchor_df.columns.tolist()
assert "sequence_index" in anchor_df.columns, anchor_df.columns.tolist()

chunk_sequence_anchor_index_rows = []

for row in all_chunks_df.itertuples(index=False):
    chunk_csv_path = Path(row.chunk_csv)
    chunk_df = pd.read_csv(chunk_csv_path)
    chunk_anchor_df = chunk_df.merge(
        anchor_df,
        on=["record_index"],
        how="left",
        suffixes=("", "_anchor")
    )
    assert len(chunk_anchor_df) == len(chunk_df), {"chunk_name": row.chunk_name, "reason": "anchor merge row count mismatch"}

    missing_anchor = chunk_anchor_df["sequence_index_anchor"].isna().sum() if "sequence_index_anchor" in chunk_anchor_df.columns else 0
    if "sequence_index_anchor" in chunk_anchor_df.columns:
        chunk_anchor_df = chunk_anchor_df.rename(columns={"sequence_index_anchor": "sequence_index"})
    if "frame_timestamp_ns_anchor" in chunk_anchor_df.columns and "frame_timestamp_ns" not in chunk_anchor_df.columns:
        chunk_anchor_df = chunk_anchor_df.rename(columns={"frame_timestamp_ns_anchor": "frame_timestamp_ns"})

    chunk_anchor_csv = chunk_manifest_dir / f"{row.chunk_name}_sequence_anchor.csv"
    chunk_anchor_df.to_csv(chunk_anchor_csv, index=False, encoding="utf-8")

    chunk_sequence_anchor_index_rows.append({
        "chunk_id": int(row.chunk_id),
        "chunk_name": row.chunk_name,
        "global_start": int(row.global_start),
        "global_end": int(row.global_end),
        "frame_count": int(row.frame_count),
        "chunk_csv": str(chunk_csv_path),
        "chunk_sequence_anchor_csv": str(chunk_anchor_csv),
        "missing_anchor_count": int(missing_anchor),
    })

chunk_sequence_anchor_index_df = pd.DataFrame(chunk_sequence_anchor_index_rows)
chunk_sequence_anchor_index_path = chunk_manifest_dir / "chunk_sequence_anchor_index.csv"
chunk_sequence_anchor_index_df.to_csv(chunk_sequence_anchor_index_path, index=False, encoding="utf-8")

summary = {
    "route": "da3_record_sequence_anchor_batch_plan_full_target",
    "global_camera_source": "manifests/extrinsics_w2c_arc.npy",
    "frame_count": int(len(input_df)),
    "chunk_count": int(len(all_chunks_df)),
    "target_chunk_count": int(len(target_chunks_df)),
    "batch_count": int(batch_count),
    "pipeline_root": str(pipeline_root),
    "anchor_dir": str(anchor_dir),
    "camera_anchor_full_path": str(camera_anchor_full_path),
    "bundle_model_slug": BUNDLE_MODEL_SLUG,
    "input_extrinsics_path": str(extrinsics_path),
    "chunk_index_all_path": str(chunk_index_all_path),
    "chunk_index_target_path": str(chunk_index_target_path),
    "chunk_sequence_anchor_index_path": str(chunk_sequence_anchor_index_path),
    "batch_plan_path": str(batch_plan_path),
    "target_policy": "full_set",
    "test_execution_limiter_location": "#11-3",
}

(chunk_manifest_dir / "batch_plan_summary.json").write_text(
    json.dumps(summary, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print(json.dumps(summary, indent=2, ensure_ascii=False))
display(batch_plan_df)
display_stage_summary(
    "9-4",
    "batch plan build",
    inputs=[
        {"item": "record_manifest", "path": str(input_manifest_path)},
        {"item": "extrinsics_w2c", "path": str(extrinsics_path)},
        {"item": "camera_anchor_full", "path": str(camera_anchor_full_path)},
    ],
    outputs=[
        {"item": "pipeline_config", "path": str(pipeline_root / "pipeline_config.json")},
        {"item": "chunk_index_all", "path": str(chunk_index_all_path)},
        {"item": "chunk_index_target", "path": str(chunk_index_target_path)},
        {"item": "batch_plan", "path": str(batch_plan_path)},
        {"item": "chunk_sequence_anchor_index", "path": str(chunk_sequence_anchor_index_path)},
        {"item": "batch_plan_summary", "path": str(chunk_manifest_dir / "batch_plan_summary.json")},
    ],
    notes=[
        {"item": "chunk_count", "value": int(len(all_chunks_df))},
        {"item": "batch_count", "value": int(batch_count)},
    ],
)
```

```python
#9-5
from pathlib import Path
import json
import pandas as pd

ctx = load_ctx()
probe_root = Path(ctx['probe_root'])
pipeline_root = probe_root / ctx.get('pipeline_slug', 'da3_ngl_batch_v01')
chunk_manifest_dir = pipeline_root / 'manifests'
record_manifest_path = Path(json.loads(Path('/content/runbook_managed_dirs.json').read_text(encoding='utf-8'))['02_records']) / 'record_manifest.csv'
record_df = pd.read_csv(record_manifest_path) if record_manifest_path.exists() else None
if record_df is not None:
    keep_cols = [c for c in ['sequence_index','roll_deg','pitch_deg','yaw_deg','delta_roll_deg','delta_pitch_deg','delta_yaw_deg','delta_pos','delta2_pos','delta2_rot'] if c in record_df.columns]
    join_df = record_df[['image_file_name', *keep_cols]].drop_duplicates() if 'image_file_name' in record_df.columns else record_df[keep_cols + ['sequence_index']].copy()
else:
    join_df = None

chunk_index_path = chunk_manifest_dir / 'chunk_index_all.csv'
assert chunk_index_path.exists(), chunk_index_path
chunk_index_df = pd.read_csv(chunk_index_path)
rows = []
for row in chunk_index_df.itertuples(index=False):
    chunk_csv = Path(getattr(row, 'chunk_csv')) if getattr(row, 'chunk_csv', None) else None
    if chunk_csv is None or not chunk_csv.exists():
        continue
    cdf = pd.read_csv(chunk_csv)
    ts_col = next((c for c in ['frame_timestamp_ns','timestamp_ns','timestamp'] if c in cdf.columns), None)
    cdf = append_sequence_columns(cdf, ts_col or 'frame_timestamp_ns')
    if join_df is not None:
        common = [c for c in ['image_file_name', 'sequence_index'] if c in cdf.columns and c in join_df.columns]
        if common:
            cdf = cdf.merge(join_df, on=common, how='left', suffixes=('', '_record'))
    cdf['adjacent_edge_src_sequence_index'] = cdf['sequence_index']
    cdf['adjacent_edge_dst_sequence_index'] = cdf['sequence_index'].shift(-1).fillna(-1).astype(int)
    cdf['adjacent_edge_valid'] = cdf['adjacent_edge_dst_sequence_index'] >= 0
    cdf['adjacent_pair_role'] = 'interior'
    if len(cdf) > 0:
        cdf.loc[cdf.index[0], 'adjacent_pair_role'] = 'head'
        cdf.loc[cdf.index[-1], 'adjacent_pair_role'] = 'tail'
    ext_path = chunk_csv.with_name(chunk_csv.stem + '_sequence_anchor.csv')
    cdf.to_csv(ext_path, index=False, encoding='utf-8')
    rows.append({'chunk_name': getattr(row, 'chunk_name', chunk_csv.stem), 'chunk_csv_ext': str(ext_path), 'row_count': int(len(cdf))})

out = chunk_manifest_dir / 'chunk_sequence_anchor_index.csv'
pd.DataFrame(rows).to_csv(out, index=False, encoding='utf-8')
print({'chunk_sequence_anchor_index': str(out), 'chunk_count': len(rows)})
display_stage_summary(
    "9-5",
    "chunk sequence anchor index refresh",
    inputs=[
        {"item": "chunk_index_all", "path": str(chunk_index_path)},
        {"item": "record_manifest", "path": str(record_manifest_path)},
    ],
    outputs=[
        {"item": "chunk_sequence_anchor_index", "path": str(out)},
    ],
    notes=[
        {"item": "chunk_count", "value": int(len(rows))},
    ],
)
```


# 10 Precheck

実行順: #10 -> #11。sequence / edge / batch 前 QC を通してから実行する

```python
#10-1

from pathlib import Path
import json
import pandas as pd
import numpy as np

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
config_snapshot = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8")) if Path("/content/config_snapshot.json").exists() else {}

manifest_dir = Path(ctx["manifest_dir"])
persist_root = Path(ctx.get("persist_root", manifest_dir.parent))
pipeline_slug = ctx.get("pipeline_slug", config_snapshot.get("PIPELINE_SLUG", "da3_ngl_batch_v01"))
pipeline_root = persist_root / pipeline_slug
chunk_manifest_dir = pipeline_root / "manifests"

chunk_index_all_path = chunk_manifest_dir / "chunk_index_all.csv"
assert chunk_index_all_path.exists(), chunk_index_all_path

chunk_index_df = pd.read_csv(chunk_index_all_path)
assert not chunk_index_df.empty, chunk_index_all_path
assert "chunk_name" in chunk_index_df.columns, chunk_index_df.columns.tolist()
assert "chunk_csv" in chunk_index_df.columns, chunk_index_df.columns.tolist()

rows = []

for row in chunk_index_df.itertuples(index=False):
    chunk_name = row.chunk_name
    chunk_csv = Path(row.chunk_csv)
    assert chunk_csv.exists(), {"chunk_name": chunk_name, "missing_chunk_csv": str(chunk_csv)}

    chunk_df = pd.read_csv(chunk_csv)
    assert not chunk_df.empty, {"chunk_name": chunk_name, "reason": "empty chunk csv"}

    # sequence_index がなければ record_index / timestamp で代用
    if "sequence_index" in chunk_df.columns:
        seq = chunk_df["sequence_index"].astype(int).to_numpy()
    elif "record_index" in chunk_df.columns:
        seq = chunk_df["record_index"].astype(int).to_numpy()
    else:
        raise AssertionError({"chunk_name": chunk_name, "reason": "sequence_index/record_index not found", "columns": chunk_df.columns.tolist()})

    is_monotonic = bool(np.all(np.diff(seq) > 0)) if len(seq) >= 2 else True
    has_duplicate_sequence = bool(pd.Series(seq).duplicated().any())
    bad_gap_count = int(np.sum(np.diff(seq) != 1)) if len(seq) >= 2 else 0

    rows.append({
        "chunk_id": int(row.chunk_id) if "chunk_id" in chunk_index_df.columns else None,
        "chunk_name": chunk_name,
        "row_count": int(len(chunk_df)),
        "sequence_min": int(seq.min()) if len(seq) else None,
        "sequence_max": int(seq.max()) if len(seq) else None,
        "is_monotonic": is_monotonic,
        "has_duplicate_sequence": has_duplicate_sequence,
        "bad_gap_count": bad_gap_count,
        "chunk_csv": str(chunk_csv),
    })

precheck_df = pd.DataFrame(rows)
precheck_path = chunk_manifest_dir / "batch_chunk_sequence_precheck.csv"
precheck_df.to_csv(precheck_path, index=False, encoding="utf-8")

bad_chunk_count = int(
    ((~precheck_df["is_monotonic"]) | (precheck_df["has_duplicate_sequence"]) | (precheck_df["bad_gap_count"] > 0)).sum()
)

print(precheck_df.head())
print({
    "precheck_csv": str(precheck_path),
    "bad_chunk_count": bad_chunk_count,
    "chunk_count": int(len(precheck_df)),
})
display_stage_summary(
    "10-1",
    "batch chunk sequence precheck",
    inputs=[
        {"item": "chunk_index_all", "path": str(chunk_index_all_path)},
    ],
    outputs=[
        {"item": "batch_chunk_sequence_precheck", "path": str(precheck_path)},
    ],
    notes=[
        {"item": "bad_chunk_count", "value": int(bad_chunk_count)},
        {"item": "chunk_count", "value": int(len(precheck_df))},
    ],
)
```

```python
#10-2
from pathlib import Path
import json
import pandas as pd

ctx = load_ctx()
pipeline_root = Path(ctx['probe_root']) / ctx.get('pipeline_slug', 'da3_ngl_batch_v01')
chunk_manifest_dir = pipeline_root / 'manifests'
idx_df = pd.read_csv(chunk_manifest_dir / 'chunk_sequence_anchor_index.csv')
rows=[]
for row in idx_df.itertuples(index=False):
    cdf = pd.read_csv(Path(row.chunk_csv_ext))
    miss = cdf.loc[cdf['adjacent_edge_valid'] & ((cdf['adjacent_edge_dst_sequence_index'] - cdf['adjacent_edge_src_sequence_index']) != 1)].copy() if 'adjacent_edge_valid' in cdf.columns else pd.DataFrame()
    rows.append({'chunk_name': row.chunk_name, 'missing_or_bad_edge_count': int(len(miss))})
edge_df = pd.DataFrame(rows)
out = chunk_manifest_dir / 'adjacent_edge_validation.csv'
edge_df.to_csv(out, index=False, encoding='utf-8')
display(edge_df)
display_stage_summary(
    "10-2",
    "adjacent edge validation",
    inputs=[
        {"item": "chunk_sequence_anchor_index", "path": str(chunk_manifest_dir / 'chunk_sequence_anchor_index.csv')},
    ],
    outputs=[
        {"item": "adjacent_edge_validation", "path": str(out)},
    ],
    notes=[
        {"item": "chunk_count", "value": int(len(edge_df))},
    ],
)
```

```python
#10-3

from pathlib import Path
import json
import numpy as np
import pandas as pd

config = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8"))
ctx = load_ctx()
persist_root = Path(ctx["probe_root"])
run_dir = persist_root / ctx.get("pipeline_slug", config.get("PIPELINE_SLUG", "da3_ngl_batch_v01"))
manifest_dir = run_dir / "manifests"
anchor_dir = persist_root / "01_anchor"

anchor_qc_path = anchor_dir / "full_anchor_pose_qc_arc.csv"
sequence_precheck_path = manifest_dir / "batch_chunk_sequence_precheck.csv"
edge_validation_path = manifest_dir / "adjacent_edge_validation.csv"

assert anchor_qc_path.exists(), anchor_qc_path
assert sequence_precheck_path.exists(), sequence_precheck_path
assert edge_validation_path.exists(), edge_validation_path

anchor_qc_df = pd.read_csv(anchor_qc_path)
sequence_df = pd.read_csv(sequence_precheck_path)
edge_df = pd.read_csv(edge_validation_path)

# centered roll を使う
if "roll_deg_centered" not in anchor_qc_df.columns:
    if "roll_deg_raw" in anchor_qc_df.columns:
        roll_base = float(np.nanmedian(anchor_qc_df["roll_deg_raw"]))
        roll_src = anchor_qc_df["roll_deg_raw"].to_numpy(float)
    else:
        roll_base = float(np.nanmedian(anchor_qc_df["roll_deg"]))
        roll_src = anchor_qc_df["roll_deg"].to_numpy(float)
    roll_centered = ((roll_src - roll_base + 180.0) % 360.0) - 180.0
    anchor_qc_df["roll_deg_centered"] = roll_centered

ROLL_CENTER_WARN_DEG = float(config.get("ANCHOR_QC_WARN_ABS_ROLL_CENTERED_DEG", 15.0))
PITCH_MIN_WARN_DEG = float(config.get("ANCHOR_QC_WARN_PITCH_MIN_DEG", -89.0))
PITCH_MAX_WARN_DEG = float(config.get("ANCHOR_QC_WARN_PITCH_MAX_DEG", 89.0))
YAW_JUMP_FAIL_DEG = float(config.get("ANCHOR_QC_MAX_DELTA_LENS_ANGLE_DEG", 45.0))

anchor_qc_df["roll_warn_centered"] = anchor_qc_df["roll_deg_centered"].abs() > ROLL_CENTER_WARN_DEG
anchor_qc_df["pitch_warn_band"] = (
    (anchor_qc_df["pitch_deg"] < PITCH_MIN_WARN_DEG) |
    (anchor_qc_df["pitch_deg"] > PITCH_MAX_WARN_DEG)
)
anchor_qc_df["yaw_jump_fail"] = anchor_qc_df["delta_lens_angle_deg"].abs() > YAW_JUMP_FAIL_DEG

bad_sequence_chunk_count = int((~sequence_df["is_monotonic"]).sum() + sequence_df["has_duplicate_sequence"].sum() + (sequence_df["bad_gap_count"] > 0).sum())

# edge_df の chunk単位 fail 数をゆるく集計
edge_fail_cols = [c for c in edge_df.columns if c.endswith("_fail") or c.endswith("_error")]
if "chunk_name" in edge_df.columns:
    if edge_fail_cols:
        tmp = edge_df.copy()
        row_bad = np.zeros(len(tmp), dtype=bool)
        for c in edge_fail_cols:
            if tmp[c].dtype == bool:
                row_bad |= tmp[c].fillna(False).to_numpy()
        bad_edge_chunk_count = int(tmp.loc[row_bad, "chunk_name"].nunique())
    else:
        bad_edge_chunk_count = 0
else:
    bad_edge_chunk_count = 0

summary = {
    "anchor_qc": {
        "row_count": int(len(anchor_qc_df)),
        "fail_count": int(anchor_qc_df["anchor_qc_fail"].sum()) if "anchor_qc_fail" in anchor_qc_df.columns else 0,
        "roll_warn_centered_count": int(anchor_qc_df["roll_warn_centered"].sum()),
        "pitch_warn_count": int(anchor_qc_df["pitch_warn_band"].sum()),
        "yaw_jump_fail_count": int(anchor_qc_df["yaw_jump_fail"].sum()),
    },
    "bad_sequence_chunk_count": int(bad_sequence_chunk_count),
    "bad_edge_chunk_count": int(bad_edge_chunk_count),
}

summary_path = manifest_dir / "batch_preflight_summary.json"
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(summary, ensure_ascii=False, indent=2))
display_stage_summary(
    "10-3",
    "batch preflight summary",
    inputs=[
        {"item": "anchor_qc", "path": str(anchor_qc_path)},
        {"item": "sequence_precheck", "path": str(sequence_precheck_path)},
        {"item": "edge_validation", "path": str(edge_validation_path)},
    ],
    outputs=[
        {"item": "batch_preflight_summary", "path": str(summary_path)},
    ],
    notes=[
        {"item": "bad_sequence_chunk_count", "value": int(summary["bad_sequence_chunk_count"])},
        {"item": "bad_edge_chunk_count", "value": int(summary["bad_edge_chunk_count"])},
    ],
)
```


# 11 Run Preparation

実行順: #11 -> #12。reset と execution target 確定を先に行う

```python
#11-1

from pathlib import Path
import json
import pandas as pd

ctx = load_ctx()
manifest_dir = Path(ctx["probe_root"]) / ctx.get("pipeline_slug", "da3_ngl_batch_v01") / "manifests"

batch_plan_df = pd.read_csv(manifest_dir / "batch_plan.csv")
chunk_all_df = pd.read_csv(manifest_dir / "chunk_index_all.csv")
chunk_target_df = pd.read_csv(manifest_dir / "chunk_index_target.csv")

display(batch_plan_df)
display(chunk_all_df[[c for c in ["chunk_id","chunk_name"] if c in chunk_all_df.columns]].head(10))
display(chunk_all_df[[c for c in ["chunk_id","chunk_name"] if c in chunk_all_df.columns]].tail(10))
display(chunk_target_df[[c for c in chunk_target_df.columns if c in ["chunk_id","chunk_name"]]])
display_stage_summary(
    "11-1",
    "run preparation preview",
    inputs=[
        {"item": "batch_plan", "path": str(manifest_dir / "batch_plan.csv")},
        {"item": "chunk_index_all", "path": str(manifest_dir / "chunk_index_all.csv")},
        {"item": "chunk_index_target", "path": str(manifest_dir / "chunk_index_target.csv")},
    ],
    outputs=[],
    notes=[
        {"item": "batch_count", "value": int(len(batch_plan_df))},
        {"item": "all_chunk_count", "value": int(len(chunk_all_df))},
        {"item": "target_chunk_count", "value": int(len(chunk_target_df))},
    ],
)
```

```python
#11-2
from pathlib import Path
import json, os, shutil, subprocess, shlex, math, hashlib
import numpy as np
import pandas as pd

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def load_ctx():
    return load_json("/content/runbook_session_context.json")

def find_first(paths):
    for p in paths:
        p = Path(p)
        if p.exists():
            return p
    return None

def normalize_rows(x, eps=1e-12):
    x = np.asarray(x, dtype=float)
    n = np.linalg.norm(x, axis=1, keepdims=True)
    n = np.maximum(n, eps)
    return x / n

def angle_deg(a, b):
    a = normalize_rows(a)
    b = normalize_rows(b)
    d = np.sum(a * b, axis=1)
    d = np.clip(d, -1.0, 1.0)
    return np.degrees(np.arccos(d))

print("common helpers loaded")
```

```python
#11-3

ctx = load_ctx()
probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"

chunk_manifest_dir.mkdir(parents=True, exist_ok=True)
chunk_runs_dir.mkdir(parents=True, exist_ok=True)

test_chunk_with_batch_path = chunk_manifest_dir / "test_only_target_chunk_with_batch.csv"
test_batch_plan_path = chunk_manifest_dir / "test_only_target_batch_plan.csv"

canonical_chunk_with_batch_path = chunk_manifest_dir / "target_chunk_with_batch.csv"
canonical_batch_plan_path = chunk_manifest_dir / "target_batch_plan.csv"

fallback_chunk_target_path = chunk_manifest_dir / "chunk_index_target.csv"
fallback_batch_plan_path = chunk_manifest_dir / "batch_plan.csv"

if test_chunk_with_batch_path.exists():
    execution_chunk_path = test_chunk_with_batch_path
    execution_mode_chunks = "test_only"
elif canonical_chunk_with_batch_path.exists():
    execution_chunk_path = canonical_chunk_with_batch_path
    execution_mode_chunks = "canonical_target_with_batch"
else:
    execution_chunk_path = fallback_chunk_target_path
    execution_mode_chunks = "canonical_chunk_index_target"

if test_batch_plan_path.exists():
    execution_batch_plan_path = test_batch_plan_path
    execution_mode_batch_plan = "test_only"
elif canonical_batch_plan_path.exists():
    execution_batch_plan_path = canonical_batch_plan_path
    execution_mode_batch_plan = "canonical_target_batch_plan"
else:
    execution_batch_plan_path = fallback_batch_plan_path
    execution_mode_batch_plan = "canonical_batch_plan"

assert execution_chunk_path.exists(), {"missing_execution_chunk_source": str(execution_chunk_path)}
assert execution_batch_plan_path.exists(), {"missing_execution_batch_source": str(execution_batch_plan_path)}

execution_chunks_df = pd.read_csv(execution_chunk_path)
execution_batch_plan_df = pd.read_csv(execution_batch_plan_path)

assert not execution_chunks_df.empty, execution_chunk_path
assert not execution_batch_plan_df.empty, execution_batch_plan_path

chunk_name_col = next((c for c in ["chunk_name", "chunk_id", "name"] if c in execution_chunks_df.columns), None)
assert chunk_name_col is not None, {"execution_chunk_columns": execution_chunks_df.columns.tolist()}

if "batch_name" not in execution_batch_plan_df.columns:
    if "batch_index" in execution_batch_plan_df.columns:
        execution_batch_plan_df["batch_name"] = execution_batch_plan_df["batch_index"].astype(int).map(lambda x: f"batch_{x:03d}")
    else:
        execution_batch_plan_df["batch_name"] = [f"batch_{i:03d}" for i in range(len(execution_batch_plan_df))]

if "batch_name" not in execution_chunks_df.columns and "batch_index" in execution_chunks_df.columns:
    execution_chunks_df["batch_name"] = execution_chunks_df["batch_index"].astype(int).map(lambda x: f"batch_{x:03d}")

execution_chunk_out = chunk_manifest_dir / "execution_target_chunks.csv"
execution_batch_out = chunk_manifest_dir / "execution_target_batch_plan.csv"

execution_chunks_df.to_csv(execution_chunk_out, index=False, encoding="utf-8")
execution_batch_plan_df.to_csv(execution_batch_out, index=False, encoding="utf-8")

summary = {
    "status": "ok",
    "execution_mode_chunks": execution_mode_chunks,
    "execution_mode_batch_plan": execution_mode_batch_plan,
    "execution_chunk_source": str(execution_chunk_path),
    "execution_batch_plan_source": str(execution_batch_plan_path),
    "execution_chunk_rows": int(len(execution_chunks_df)),
    "execution_batch_rows": int(len(execution_batch_plan_df)),
    "execution_chunk_names_sample": execution_chunks_df[chunk_name_col].astype(str).head(10).tolist(),
    "execution_batch_names": execution_batch_plan_df["batch_name"].astype(str).tolist(),
    "execution_chunk_out": str(execution_chunk_out),
    "execution_batch_out": str(execution_batch_out),
}

save_json(chunk_manifest_dir / "execution_target_resolution_summary.json", summary)

print(json.dumps(summary, indent=2, ensure_ascii=False))
display(execution_chunks_df.head())
display(execution_batch_plan_df)
display_stage_summary(
    "11-3",
    "execution target resolve",
    inputs=[
        {"item": "chunk_index_target", "path": str(fallback_chunk_target_path)},
        {"item": "batch_plan", "path": str(fallback_batch_plan_path)},
    ],
    outputs=[
        {"item": "execution_target_chunks", "path": str(execution_chunk_out)},
        {"item": "execution_target_batch_plan", "path": str(execution_batch_out)},
        {"item": "execution_target_resolution_summary", "path": str(chunk_manifest_dir / "execution_target_resolution_summary.json")},
    ],
    notes=[
        {"item": "execution_mode_chunks", "value": execution_mode_chunks},
        {"item": "execution_mode_batch_plan", "value": execution_mode_batch_plan},
    ],
)
```

```python
#11-4

ctx = load_ctx()

probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"

manifest_dir = Path(ctx["manifest_dir"])
persist_root = Path(ctx.get("persist_root", manifest_dir.parent))
anchor_dir = persist_root / "01_anchor"

merged_dir = Path(ctx["merged_dir"])
final_outputs_dir = Path(ctx["final_outputs_dir"])
final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_manifests_dir = Path(ctx["final_outputs_manifests_dir"])
final_outputs_chunk_evidence_dir = Path(ctx["final_outputs_chunk_evidence_dir"])
final_outputs_merged_dir = Path(ctx["final_outputs_merged_dir"])

execution_chunks_path = chunk_manifest_dir / "execution_target_chunks.csv"
execution_batch_plan_path = chunk_manifest_dir / "execution_target_batch_plan.csv"

assert execution_chunks_path.exists(), execution_chunks_path
assert execution_batch_plan_path.exists(), execution_batch_plan_path

target_chunks_df = pd.read_csv(execution_chunks_path)
batch_plan_df = pd.read_csv(execution_batch_plan_path)

assert not target_chunks_df.empty, execution_chunks_path
assert not batch_plan_df.empty, execution_batch_plan_path

chunk_name_col = next((c for c in ["chunk_name", "chunk_id", "name"] if c in target_chunks_df.columns), None)
assert chunk_name_col is not None, {"target_chunk_columns": target_chunks_df.columns.tolist()}

batch_names = batch_plan_df["batch_name"].astype(str).tolist() if "batch_name" in batch_plan_df.columns else [f"batch_{int(v):03d}" for v in batch_plan_df["batch_index"].tolist()]

config_snapshot = load_json("/content/config_snapshot.json")
delete_targets = []
if bool(config_snapshot.get("RESET_TARGET_OUTPUTS_BEFORE_RUN", True)):
    for row in target_chunks_df.itertuples(index=False):
        chunk_name = str(getattr(row, chunk_name_col))
        delete_targets.append(chunk_runs_dir / chunk_name)
        delete_targets.append(chunk_manifest_dir / f"{chunk_name}_to_w0.npy")
    for batch_name in batch_names:
        delete_targets.append(chunk_runs_dir / batch_name)
    delete_targets.extend([merged_dir, final_outputs_dir])

deleted, missing = [], []
for path in delete_targets:
    if not path.exists():
        missing.append(str(path))
        continue
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    deleted.append(str(path))

for p in [merged_dir, final_outputs_dir, final_outputs_diagnostics_dir, final_outputs_manifests_dir, final_outputs_chunk_evidence_dir, final_outputs_merged_dir]:
    p.mkdir(parents=True, exist_ok=True)

reset_summary = {
    "status": "ok",
    "route": "da3_ngl_batch_v01_target_output_reset",
    "probe_root": str(probe_root),
    "chunk_source_path": str(execution_chunks_path),
    "batch_source_path": str(execution_batch_plan_path),
    "target_chunk_count": int(len(target_chunks_df)),
    "target_batch_count": int(len(batch_names)),
    "deleted_count": int(len(deleted)),
    "missing_count": int(len(missing)),
}
save_json(final_outputs_diagnostics_dir / "target_output_reset_summary.json", reset_summary)

# preflight
record_manifest_path = manifest_dir / "da3_input_manifest.csv"
anchor_pose_diag_path = anchor_dir / "full_anchor_pose_diag_arc.csv"
anchor_qc_path = anchor_dir / "full_anchor_pose_qc_arc.csv"
sequence_precheck_path = chunk_manifest_dir / "batch_chunk_sequence_precheck.csv"
edge_validation_path = chunk_manifest_dir / "adjacent_edge_validation.csv"

required_paths = {
    "record_manifest": record_manifest_path,
    "anchor_pose_diag": anchor_pose_diag_path,
    "anchor_qc": anchor_qc_path,
    "sequence_precheck": sequence_precheck_path,
    "edge_validation": edge_validation_path,
}
missing_required = {k: str(p) for k, p in required_paths.items() if not p.exists()}
assert not missing_required, {"missing_required": missing_required}

record_df = pd.read_csv(record_manifest_path)
anchor_pose_df = pd.read_csv(anchor_pose_diag_path)
anchor_qc_df = pd.read_csv(anchor_qc_path)
sequence_df = pd.read_csv(sequence_precheck_path)
edge_df = pd.read_csv(edge_validation_path)

record_count_match = len(record_df) == len(anchor_pose_df)
sequence_bad_count = int(((~sequence_df["is_monotonic"]) | (sequence_df["has_duplicate_sequence"]) | (sequence_df["bad_gap_count"] > 0)).sum()) if len(sequence_df) else 0
edge_bad_chunk_count = 0
if len(edge_df) and "chunk_name" in edge_df.columns:
    fail_cols = [c for c in edge_df.columns if c.endswith("_fail")]
    if fail_cols:
        bad_mask = np.zeros(len(edge_df), dtype=bool)
        for c in fail_cols:
            bad_mask |= edge_df[c].fillna(False).astype(bool).to_numpy()
        edge_bad_chunk_count = int(edge_df.loc[bad_mask, "chunk_name"].nunique())
anchor_fail_count = int(anchor_qc_df["anchor_qc_fail"].sum()) if "anchor_qc_fail" in anchor_qc_df.columns else 0

image_path_col = next((c for c in ["image_path", "image_abs_path"] if c in record_df.columns), None)
missing_images = []
if image_path_col is not None:
    target_record_indices = set()
    if "record_index" in target_chunks_df.columns:
        target_record_indices = set(target_chunks_df["record_index"].dropna().astype(int).tolist())
    else:
        for row in target_chunks_df.itertuples(index=False):
            chunk_name = str(getattr(row, chunk_name_col))
            chunk_csv = chunk_manifest_dir / f"{chunk_name}.csv"
            if chunk_csv.exists():
                cdf = pd.read_csv(chunk_csv)
                if "record_index" in cdf.columns:
                    target_record_indices.update(cdf["record_index"].dropna().astype(int).tolist())
    sub = record_df[record_df["record_index"].astype(int).isin(sorted(target_record_indices))].copy() if target_record_indices and "record_index" in record_df.columns else record_df.copy()
    for r in sub.itertuples(index=False):
        p = Path(getattr(r, image_path_col))
        if not p.exists():
            missing_images.append(str(p))

if missing_images:
    pd.DataFrame({"missing_image_path": missing_images}).to_csv(final_outputs_diagnostics_dir / "batch_execution_preflight_missing_images.csv", index=False, encoding="utf-8")

fatal_issues, warnings = [], []
if not record_count_match:
    fatal_issues.append({"type": "record_anchor_count_mismatch", "record_rows": int(len(record_df)), "anchor_rows": int(len(anchor_pose_df))})
if sequence_bad_count > 0:
    fatal_issues.append({"type": "sequence_precheck_failed", "bad_chunk_count": sequence_bad_count})
if edge_bad_chunk_count > 0:
    warnings.append({"type": "adjacent_edge_validation_has_failures", "bad_chunk_count": edge_bad_chunk_count})
if anchor_fail_count > 0:
    warnings.append({"type": "anchor_qc_failures_present", "anchor_fail_count": anchor_fail_count})
if missing_images:
    fatal_issues.append({"type": "missing_images", "missing_image_count": int(len(missing_images))})

preflight = {
    "status": "fatal" if fatal_issues else "ok_with_warnings" if warnings else "ok",
    "target_chunk_count": int(len(target_chunks_df)),
    "target_batch_count": int(len(batch_plan_df)),
    "record_rows": int(len(record_df)),
    "anchor_rows": int(len(anchor_pose_df)),
    "record_anchor_count_match": bool(record_count_match),
    "sequence_bad_chunk_count": int(sequence_bad_count),
    "edge_bad_chunk_count": int(edge_bad_chunk_count),
    "anchor_fail_count": int(anchor_fail_count),
    "missing_image_count": int(len(missing_images)),
    "fatal_issues": fatal_issues,
    "warnings": warnings,
}
save_json(final_outputs_diagnostics_dir / "batch_execution_preflight.json", preflight)
print(json.dumps({"reset_summary": reset_summary, "preflight": preflight}, indent=2, ensure_ascii=False))
display_stage_summary(
    "11-4",
    "reset and preflight",
    inputs=[
        {"item": "execution_target_chunks", "path": str(execution_chunks_path)},
        {"item": "execution_target_batch_plan", "path": str(execution_batch_plan_path)},
        {"item": "record_manifest", "path": str(record_manifest_path)},
        {"item": "anchor_pose_diag", "path": str(anchor_pose_diag_path)},
        {"item": "anchor_qc", "path": str(anchor_qc_path)},
    ],
    outputs=[
        {"item": "target_output_reset_summary", "path": str(final_outputs_diagnostics_dir / "target_output_reset_summary.json")},
        {"item": "batch_execution_preflight", "path": str(final_outputs_diagnostics_dir / "batch_execution_preflight.json")},
        {"item": "batch_execution_preflight_missing_images", "path": str(final_outputs_diagnostics_dir / "batch_execution_preflight_missing_images.csv")},
    ],
    notes=[
        {"item": "fatal_issue_count", "value": int(len(fatal_issues))},
        {"item": "warning_count", "value": int(len(warnings))},
    ],
)
assert not fatal_issues, preflight
```


# 12 Run Batches

実行順: #12 -> #13。input 生成、official wrapper 生成、chunk 実行を行う

```python
#12-1

ctx = load_ctx()

probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
chunk_runs_dir.mkdir(parents=True, exist_ok=True)

final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_diagnostics_dir.mkdir(parents=True, exist_ok=True)

execution_chunks_path = chunk_manifest_dir / "execution_target_chunks.csv"
execution_batch_plan_path = chunk_manifest_dir / "execution_target_batch_plan.csv"
assert execution_chunks_path.exists(), execution_chunks_path
assert execution_batch_plan_path.exists(), execution_batch_plan_path

execution_chunks_df = pd.read_csv(execution_chunks_path)
execution_batch_plan_df = pd.read_csv(execution_batch_plan_path)

if "batch_name" not in execution_batch_plan_df.columns:
    execution_batch_plan_df["batch_name"] = execution_batch_plan_df["batch_index"].astype(int).map(lambda x: f"batch_{x:03d}")

if "target_local_chunk_index" not in execution_chunks_df.columns:
    execution_chunks_df = execution_chunks_df.copy().reset_index(drop=True)
    execution_chunks_df["target_local_chunk_index"] = range(len(execution_chunks_df))

if "batch_index" not in execution_chunks_df.columns:
    def resolve_batch_index(local_idx: int):
        hit = execution_batch_plan_df[(execution_batch_plan_df["chunk_from"].astype(int) <= int(local_idx)) &
                                      (execution_batch_plan_df["chunk_to"].astype(int) >= int(local_idx))]
        if len(hit) == 0:
            return None
        return int(hit.sort_values("batch_index", kind="stable").iloc[0]["batch_index"])
    execution_chunks_df["batch_index"] = execution_chunks_df["target_local_chunk_index"].map(resolve_batch_index)

assert execution_chunks_df["batch_index"].notna().all(), {"unresolved_target_local_chunk_indices": execution_chunks_df.loc[execution_chunks_df["batch_index"].isna(), "target_local_chunk_index"].tolist()}
execution_chunks_df["batch_index"] = execution_chunks_df["batch_index"].astype(int)

if "batch_name" not in execution_chunks_df.columns:
    execution_chunks_df["batch_name"] = execution_chunks_df["batch_index"].astype(int).map(lambda x: f"batch_{x:03d}")

rows, missing_files = [], []
for b_row in execution_batch_plan_df.itertuples(index=False):
    batch_index = int(b_row.batch_index) if hasattr(b_row, "batch_index") else None
    batch_name = str(b_row.batch_name)
    batch_work_dir = chunk_runs_dir / batch_name
    batch_work_dir.mkdir(parents=True, exist_ok=True)

    batch_chunks_df = execution_chunks_df[execution_chunks_df["batch_index"].astype(int) == batch_index].copy().sort_values("target_local_chunk_index", kind="stable").reset_index(drop=True)
    assert not batch_chunks_df.empty, {"batch_name": batch_name, "batch_index": batch_index}

    for c_row in batch_chunks_df.itertuples(index=False):
        chunk_name = str(getattr(c_row, "chunk_name"))
        chunk_csv_path = chunk_manifest_dir / f"{chunk_name}.csv"
        chunk_anchor_csv_path = chunk_manifest_dir / f"{chunk_name}_sequence_anchor.csv"
        if not chunk_csv_path.exists():
            missing_files.append(str(chunk_csv_path))
        if not chunk_anchor_csv_path.exists():
            missing_files.append(str(chunk_anchor_csv_path))
        rows.append({
            "batch_index": int(batch_index),
            "batch_name": batch_name,
            "chunk_id": int(getattr(c_row, "chunk_id")) if "chunk_id" in execution_chunks_df.columns else None,
            "chunk_name": chunk_name,
            "target_local_chunk_index": int(getattr(c_row, "target_local_chunk_index")),
            "chunk_csv": str(chunk_csv_path),
            "chunk_sequence_anchor_csv": str(chunk_anchor_csv_path),
            "batch_work_dir": str(batch_work_dir),
        })

assert not missing_files, {"missing_chunk_related_files_count": len(missing_files), "missing_chunk_related_files_sample": missing_files[:10]}

batch_execution_items_df = pd.DataFrame(rows).sort_values(["batch_index", "target_local_chunk_index"], kind="stable").reset_index(drop=True)
batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
batch_execution_items_df.to_csv(batch_execution_items_path, index=False, encoding="utf-8")

batch_manifest_rows = []
for batch_name, batch_df in batch_execution_items_df.groupby("batch_name", sort=True):
    batch_work_dir = Path(batch_df.iloc[0]["batch_work_dir"])
    batch_manifest_dir = batch_work_dir / "manifests"
    batch_manifest_dir.mkdir(parents=True, exist_ok=True)
    batch_chunk_index_path = batch_manifest_dir / "batch_chunk_index.csv"
    batch_df.to_csv(batch_chunk_index_path, index=False, encoding="utf-8")
    batch_manifest_rows.append({
        "batch_name": str(batch_name),
        "batch_index": int(batch_df.iloc[0]["batch_index"]),
        "chunk_count": int(len(batch_df)),
        "chunk_names": "|".join(batch_df["chunk_name"].astype(str).tolist()),
        "batch_work_dir": str(batch_work_dir),
        "batch_chunk_index_path": str(batch_chunk_index_path),
    })

batch_manifests_df = pd.DataFrame(batch_manifest_rows).sort_values(["batch_index", "batch_name"], kind="stable").reset_index(drop=True)
batch_manifests_path = chunk_manifest_dir / "batch_manifests.csv"
batch_manifests_df.to_csv(batch_manifests_path, index=False, encoding="utf-8")

summary = {
    "status": "ok",
    "batch_count": int(len(batch_manifests_df)),
    "chunk_count_total": int(batch_execution_items_df.shape[0]),
    "batch_execution_items_path": str(batch_execution_items_path),
    "batch_manifests_path": str(batch_manifests_path),
    "batch_names": batch_manifests_df["batch_name"].astype(str).tolist(),
}
save_json(final_outputs_diagnostics_dir / "batch_input_generation_summary.json", summary)

print(json.dumps(summary, indent=2, ensure_ascii=False))
display(batch_execution_items_df)
display(batch_manifests_df)
display_stage_summary(
    "12-1",
    "batch input generation",
    inputs=[
        {"item": "execution_target_chunks", "path": str(execution_chunks_path)},
        {"item": "execution_target_batch_plan", "path": str(execution_batch_plan_path)},
    ],
    outputs=[
        {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
        {"item": "batch_manifests", "path": str(batch_manifests_path)},
        {"item": "batch_input_generation_summary", "path": str(final_outputs_diagnostics_dir / "batch_input_generation_summary.json")},
    ],
    notes=[
        {"item": "batch_count", "value": int(len(batch_manifests_df))},
        {"item": "chunk_count_total", "value": int(batch_execution_items_df.shape[0])},
    ],
)
```

```python
#12-2

from pathlib import Path
import textwrap

repo_root = Path("/content/Depth-Anything-3")
src_root = repo_root / "src"
assert repo_root.exists(), repo_root
assert src_root.exists(), src_root

wrapper_path = repo_root / "run_da3_chunk_local.py"

wrapper_code = r'''
import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

REPO_ROOT = Path("/content/Depth-Anything-3")
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from depth_anything_3.api import DepthAnything3


def _resolve_device(device_arg: str) -> str:
    if device_arg and device_arg != "auto":
        return device_arg
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _pick_pred_array(prediction, attr_names):
    for name in attr_names:
        if hasattr(prediction, name):
            v = getattr(prediction, name)
            if v is None:
                continue
            try:
                arr = np.asarray(v)
                return arr
            except Exception:
                pass
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk-csv", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--model-id", required=True)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--process-res", type=int, default=504)
    ap.add_argument("--process-res-method", default="upper_bound_resize")
    ap.add_argument("--export-format", default="mini_npz")
    ap.add_argument("--infer-gs", action="store_true")
    ap.add_argument("--align-to-input-ext-scale", action="store_true")
    ap.add_argument("--show-cameras", action="store_true")
    ap.add_argument("--conf-thresh-percentile", type=float, default=40.0)
    ap.add_argument("--num-max-points", type=int, default=1_000_000)
    args = ap.parse_args()

    chunk_csv = Path(args.chunk_csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(chunk_csv)
    assert len(df) >= 2, {"chunk_csv": str(chunk_csv), "reason": "need at least 2 frames"}

    required_cols = ["image_path", "fx_canonical", "fy_canonical", "cx_canonical", "cy_canonical"]
    missing = [c for c in required_cols if c not in df.columns]
    assert not missing, {"chunk_csv": str(chunk_csv), "missing_required_columns": missing}

    image_paths = df["image_path"].astype(str).tolist()
    missing_images = [p for p in image_paths if not Path(p).exists()]
    assert not missing_images, {"missing_images_count": len(missing_images), "sample": missing_images[:10]}

    if not {"tx", "ty", "tz", "qx", "qy", "qz", "qw"}.issubset(df.columns):
        raise AssertionError({"reason": "pose quaternion/translation columns missing", "columns": df.columns.tolist()})

    # notebook側で既に extrinsics_w2c_arc.npy を整備している想定だが、
    # chunk csv だけからも走れるように tx/ty/tz + qx/qy/qz/qw からは再構成しない。
    # 代わりに chunk csv に extrinsics 参照列が無い場合は、w2c は使わず image-only API にフォールバックする。
    use_pose_conditioning = False
    extrinsics = None

    if {"w2c_00","w2c_01","w2c_02","w2c_03","w2c_10","w2c_11","w2c_12","w2c_13","w2c_20","w2c_21","w2c_22","w2c_23","w2c_30","w2c_31","w2c_32","w2c_33"}.issubset(df.columns):
        mats = []
        for r in df.itertuples(index=False):
            M = np.array([
                [r.w2c_00, r.w2c_01, r.w2c_02, r.w2c_03],
                [r.w2c_10, r.w2c_11, r.w2c_12, r.w2c_13],
                [r.w2c_20, r.w2c_21, r.w2c_22, r.w2c_23],
                [r.w2c_30, r.w2c_31, r.w2c_32, r.w2c_33],
            ], dtype=np.float32)
            mats.append(M)
        extrinsics = np.stack(mats, axis=0)
        use_pose_conditioning = True
    elif {"extrinsics_path", "chunk_local_index"}.issubset(df.columns):
        # 予備: 外部npyへの参照があればそれを使えるようにする余地
        pass

    intrinsics = []
    for r in df.itertuples(index=False):
        K = np.array([
            [float(r.fx_canonical), 0.0, float(r.cx_canonical)],
            [0.0, float(r.fy_canonical), float(r.cy_canonical)],
            [0.0, 0.0, 1.0],
        ], dtype=np.float32)
        intrinsics.append(K)
    intrinsics = np.stack(intrinsics, axis=0)

    device = _resolve_device(args.device)
    model = DepthAnything3.from_pretrained(args.model_id)
    model = model.to(device)

    inference_kwargs = dict(
        image=image_paths,
        intrinsics=intrinsics,
        process_res=args.process_res,
        process_res_method=args.process_res_method,
        export_dir=str(out_dir),
        export_format=args.export_format,
        conf_thresh_percentile=args.conf_thresh_percentile,
        num_max_points=args.num_max_points,
        show_cameras=bool(args.show_cameras),
    )

    if use_pose_conditioning:
        inference_kwargs["extrinsics"] = extrinsics
        inference_kwargs["align_to_input_ext_scale"] = bool(args.align_to_input_ext_scale)

    if args.infer_gs:
        inference_kwargs["infer_gs"] = True

    prediction = model.inference(**inference_kwargs)

    # pred_extrinsics / pred_intrinsics を後段互換で保存
    pred_ext = _pick_pred_array(prediction, ["extrinsics", "pred_extrinsics", "camera_extrinsics"])
    pred_ixt = _pick_pred_array(prediction, ["intrinsics", "pred_intrinsics", "camera_intrinsics"])

    # API docs によれば align_to_input_ext_scale=True の場合、返る extrinsics は入力 extrinsics に置換される。
    # 後段互換のため、pose conditioning時に pred_ext が拾えなければ入力 extrinsics を保存する。
    if pred_ext is None and extrinsics is not None:
        pred_ext = extrinsics
    if pred_ixt is None:
        pred_ixt = intrinsics

    if pred_ext is not None:
        np.save(out_dir / "pred_extrinsics.npy", np.asarray(pred_ext, dtype=np.float32))
    if pred_ixt is not None:
        np.save(out_dir / "pred_intrinsics.npy", np.asarray(pred_ixt, dtype=np.float32))

    df.to_csv(out_dir / "chunk_input_frames.csv", index=False, encoding="utf-8")

    summary = {
        "status": "ok",
        "chunk_csv": str(chunk_csv),
        "out_dir": str(out_dir),
        "model_id": args.model_id,
        "device": device,
        "frame_count": int(len(df)),
        "use_pose_conditioning": bool(use_pose_conditioning),
        "align_to_input_ext_scale": bool(args.align_to_input_ext_scale),
        "infer_gs": bool(args.infer_gs),
        "pred_extrinsics_saved": bool((out_dir / "pred_extrinsics.npy").exists()),
        "pred_intrinsics_saved": bool((out_dir / "pred_intrinsics.npy").exists()),
    }
    (out_dir / "_SUCCESS.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''

wrapper_path.write_text(textwrap.dedent(wrapper_code), encoding="utf-8")
print({"wrapper_path": str(wrapper_path), "exists": wrapper_path.exists()})
display_stage_summary(
    "12-2",
    "local wrapper generator",
    inputs=[
        {"item": "Depth-Anything-3 repo", "path": str(repo_root)},
    ],
    outputs=[
        {"item": "run_da3_chunk_local.py", "path": str(wrapper_path)},
    ],
    notes=[
        {"item": "model_api", "value": "depth_anything_3.api.DepthAnything3"},
    ],
)
```

```python
#12-3

from pathlib import Path
import json
import subprocess
import pandas as pd

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))

probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
chunk_runs_dir.mkdir(parents=True, exist_ok=True)

final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_diagnostics_dir.mkdir(parents=True, exist_ok=True)

wrapper_path = Path("/content/Depth-Anything-3/run_da3_chunk_local.py")
assert wrapper_path.exists(), wrapper_path

batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
assert batch_execution_items_path.exists(), batch_execution_items_path

items_df = pd.read_csv(batch_execution_items_path)
assert not items_df.empty, batch_execution_items_path

# 実行設定
config_snapshot = load_json("/content/config_snapshot.json")
DRY_RUN = False
DEVICE = "auto"   # "auto" / "cuda" / "cpu"
MODEL_ID = config_snapshot.get("MODEL_ID", "depth-anything/DA3NESTED-GIANT-LARGE-1.1")
PROCESS_RES = int(config_snapshot.get("PROCESS_RES", 504))
PROCESS_RES_METHOD = str(config_snapshot.get("PROCESS_RES_METHOD", "upper_bound_resize"))
EXPORT_FORMAT = str(config_snapshot.get("EXPORT_FORMAT", "mini_npz"))
ALIGN_TO_INPUT_EXT_SCALE = bool(config_snapshot.get("ALIGN_TO_INPUT_EXT_SCALE", True))
INFER_GS = bool(config_snapshot.get("INFER_GS", False))
SHOW_CAMERAS = bool(config_snapshot.get("SHOW_CAMERAS", False))
CONF_THRESH_PERCENTILE = float(config_snapshot.get("CONF_THRESH_PERCENTILE", 40.0))
NUM_MAX_POINTS = int(config_snapshot.get("NUM_MAX_POINTS", 1_000_000))
SKIP_ALREADY_SUCCESS = bool(config_snapshot.get("SKIP_ALREADY_SUCCESS", True))

required_cols = ["batch_name", "chunk_name", "chunk_csv", "batch_work_dir"]
missing_cols = [c for c in required_cols if c not in items_df.columns]
assert not missing_cols, {"missing_columns": missing_cols, "available": items_df.columns.tolist()}

rows = []

for row in items_df.itertuples(index=False):
    batch_name = str(row.batch_name)
    chunk_name = str(row.chunk_name)
    chunk_csv = Path(row.chunk_csv)
    batch_work_dir = Path(row.batch_work_dir)
    out_dir = batch_work_dir / chunk_name
    out_dir.mkdir(parents=True, exist_ok=True)

    assert chunk_csv.exists(), {"chunk_name": chunk_name, "missing_chunk_csv": str(chunk_csv)}

    success_json = out_dir / "_SUCCESS.json"
    stderr_txt = out_dir / "run_stderr.txt"
    stdout_txt = out_dir / "run_stdout.txt"

    if SKIP_ALREADY_SUCCESS and success_json.exists():
        rows.append({
            "batch_name": batch_name,
            "chunk_name": chunk_name,
            "status": "skipped_already_success",
            "returncode": 0,
            "outputs_exist": (out_dir / "pred_extrinsics.npy").exists(),
            "out_dir": str(out_dir),
        })
        continue

    cmd = [
        "python3", str(wrapper_path),
        "--chunk-csv", str(chunk_csv),
        "--out-dir", str(out_dir),
        "--model-id", MODEL_ID,
        "--device", DEVICE,
        "--process-res", str(PROCESS_RES),
        "--process-res-method", PROCESS_RES_METHOD,
        "--export-format", EXPORT_FORMAT,
        "--conf-thresh-percentile", str(CONF_THRESH_PERCENTILE),
        "--num-max-points", str(NUM_MAX_POINTS),
    ]

    if ALIGN_TO_INPUT_EXT_SCALE:
        cmd.append("--align-to-input-ext-scale")
    if INFER_GS:
        cmd.append("--infer-gs")
    if SHOW_CAMERAS:
        cmd.append("--show-cameras")

    if DRY_RUN:
        rows.append({
            "batch_name": batch_name,
            "chunk_name": chunk_name,
            "status": "dry_run",
            "returncode": None,
            "outputs_exist": False,
            "command": " ".join(cmd),
            "out_dir": str(out_dir),
        })
        continue

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd="/content/Depth-Anything-3",
    )

    stdout_txt.write_text(proc.stdout or "", encoding="utf-8")
    stderr_txt.write_text(proc.stderr or "", encoding="utf-8")

    outputs_exist = (out_dir / "pred_extrinsics.npy").exists()

    if proc.returncode == 0 and outputs_exist:
        status = "ok"
    else:
        status = "failed"
        failed_json = out_dir / "_FAILED.json"
        failed_json.write_text(json.dumps({
            "status": "failed",
            "returncode": proc.returncode,
            "command": cmd,
            "stdout_path": str(stdout_txt),
            "stderr_path": str(stderr_txt),
            "outputs_exist": outputs_exist,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    rows.append({
        "batch_name": batch_name,
        "chunk_name": chunk_name,
        "status": status,
        "returncode": int(proc.returncode),
        "outputs_exist": bool(outputs_exist),
        "command": " ".join(cmd),
        "out_dir": str(out_dir),
    })

run_df = pd.DataFrame(rows)
run_csv = chunk_manifest_dir / "batch_run_results.csv"
run_df.to_csv(run_csv, index=False, encoding="utf-8")

summary = {
    "status": "ok",
    "dry_run": DRY_RUN,
    "row_count": int(len(run_df)),
    "ok_count": int((run_df["status"] == "ok").sum()) if len(run_df) else 0,
    "failed_count": int((run_df["status"] == "failed").sum()) if len(run_df) else 0,
    "dry_run_count": int((run_df["status"] == "dry_run").sum()) if len(run_df) else 0,
    "skipped_already_success_count": int((run_df["status"] == "skipped_already_success").sum()) if len(run_df) else 0,
    "run_csv": str(run_csv),
}
(final_outputs_diagnostics_dir / "batch_run_results_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print(json.dumps(summary, ensure_ascii=False, indent=2))
display(run_df)
display_stage_summary(
    "12-3",
    "run batches",
    inputs=[
        {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
        {"item": "local_wrapper", "path": str(wrapper_path)},
        {"item": "config_snapshot", "path": "/content/config_snapshot.json"},
    ],
    outputs=[
        {"item": "batch_run_results", "path": str(run_csv)},
        {"item": "batch_run_results_summary", "path": str(final_outputs_diagnostics_dir / "batch_run_results_summary.json")},
    ],
    notes=[
        {"item": "ok_count", "value": int(summary["ok_count"])},
        {"item": "failed_count", "value": int(summary["failed_count"])},
        {"item": "skipped_already_success_count", "value": int(summary["skipped_already_success_count"])},
    ],
)
```


# 13 Batch Validation

実行順: #13 -> #14。anchor 残差と continuity gate を確認する

```python
#13-1

ctx = load_ctx()

probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"

final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_diagnostics_dir.mkdir(parents=True, exist_ok=True)

batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
assert batch_execution_items_path.exists(), batch_execution_items_path

items_df = pd.read_csv(batch_execution_items_path)
assert not items_df.empty, batch_execution_items_path

def resolve_center_cols(df: pd.DataFrame):
    candidates = [
        ("cam_cx", "cam_cy", "cam_cz"),
        ("cx_world", "cy_world", "cz_world"),
        ("tx", "ty", "tz"),
        ("cx", "cy", "cz"),
    ]
    return next((cols for cols in candidates if all(c in df.columns for c in cols)), None)

def resolve_ypr_cols(df: pd.DataFrame):
    candidates = [
        ("yaw_deg", "pitch_deg", "roll_deg"),
        ("yaw_deg_record", "pitch_deg_record", "roll_deg_record"),
    ]
    return next((cols for cols in candidates if all(c in df.columns for c in cols)), None)

def resolve_lens_cols(df: pd.DataFrame):
    candidates = [
        ("lens_x", "lens_y", "lens_z"),
        ("anchor_lens_x", "anchor_lens_y", "anchor_lens_z"),
        ("forward_x", "forward_y", "forward_z"),
    ]
    return next((cols for cols in candidates if all(c in df.columns for c in cols)), None)

def lens_from_yaw_pitch_deg(yaw_deg: np.ndarray, pitch_deg: np.ndarray) -> np.ndarray:
    yaw = np.deg2rad(yaw_deg.astype(float))
    pitch = np.deg2rad(pitch_deg.astype(float))
    fx = np.sin(yaw) * np.cos(pitch)
    fy = -np.sin(pitch)
    fz = np.cos(yaw) * np.cos(pitch)
    return normalize_rows(np.stack([fx, fy, fz], axis=1))

residual_rows = []
missing_pred_chunks = []

for row in items_df.itertuples(index=False):
    batch_name = str(row.batch_name)
    chunk_name = str(row.chunk_name)
    batch_work_dir = Path(row.batch_work_dir)
    chunk_anchor_csv = Path(row.chunk_sequence_anchor_csv)

    assert chunk_anchor_csv.exists(), {"chunk_name": chunk_name, "missing_anchor_csv": str(chunk_anchor_csv)}
    anchor_df = pd.read_csv(chunk_anchor_csv)
    assert not anchor_df.empty, {"chunk_name": chunk_name, "reason": "empty anchor csv"}

    center_cols = resolve_center_cols(anchor_df)
    lens_cols = resolve_lens_cols(anchor_df)
    ypr_cols = resolve_ypr_cols(anchor_df)

    assert center_cols is not None, {"chunk_name": chunk_name, "reason": "center cols not found", "available_columns": anchor_df.columns.tolist()}
    assert (lens_cols is not None) or (ypr_cols is not None), {"chunk_name": chunk_name, "reason": "neither lens cols nor yaw/pitch/roll cols found", "available_columns": anchor_df.columns.tolist()}

    pred_candidates = [
        batch_work_dir / chunk_name / "pred_extrinsics.npy",
        chunk_runs_dir / chunk_name / "pred_extrinsics.npy",
        batch_work_dir / f"{chunk_name}_pred_extrinsics.npy",
    ]
    pred_path = next((p for p in pred_candidates if p.exists()), None)

    if pred_path is None:
        missing_pred_chunks.append({"batch_name": batch_name, "chunk_name": chunk_name, "reason": "pred_extrinsics.npy not found yet"})
        continue

    # pred = np.load(pred_path)
    # assert pred.ndim == 3 and pred.shape[1:] == (4, 4), {"chunk_name": chunk_name, "pred_shape": tuple(pred.shape)}

    # n = min(len(anchor_df), pred.shape[0])
    # if n <= 0:
    #     continue

    # pred = pred[:n]
    # a = anchor_df.iloc[:n].copy()

    # pred_c2w = np.linalg.inv(pred)

    pred = np.load(pred_path)

    def to_4x4_batch(arr: np.ndarray) -> np.ndarray:
        arr = np.asarray(arr)
        assert arr.ndim == 3, {"pred_shape": tuple(arr.shape)}
        if arr.shape[1:] == (4, 4):
            return arr.astype(np.float32)
        if arr.shape[1:] == (3, 4):
            out = np.repeat(np.eye(4, dtype=np.float32)[None, :, :], arr.shape[0], axis=0)
            out[:, :3, :] = arr.astype(np.float32)
            return out
        raise AssertionError({"pred_shape": tuple(arr.shape), "expected": "(N,4,4) or (N,3,4)"})

    pred = to_4x4_batch(pred)

    n = min(len(anchor_df), pred.shape[0])
    if n <= 0:
        continue

    pred = pred[:n]
    pred_c2w = np.linalg.inv(pred)

    pred_center = pred_c2w[:, :3, 3]
    pred_lens = -pred_c2w[:, :3, 2]
    a = anchor_df.iloc[:n].copy()


    anchor_center = a[list(center_cols)].to_numpy(float)
    if lens_cols is not None:
        anchor_lens = a[list(lens_cols)].to_numpy(float)
    else:
        yaw_col, pitch_col, _ = ypr_cols
        anchor_lens = lens_from_yaw_pitch_deg(a[yaw_col].to_numpy(float), a[pitch_col].to_numpy(float))

    center_error = np.linalg.norm(pred_center - anchor_center, axis=1)
    lens_error_deg = angle_deg(pred_lens, anchor_lens)

    delta_center_error = np.zeros(n, dtype=float)
    delta_lens_error_deg = np.zeros(n, dtype=float)
    if n >= 2:
        delta_center_error[1:] = np.abs(np.diff(center_error))
        delta_lens_error_deg[1:] = np.abs(np.diff(lens_error_deg))

    for i in range(n):
        residual_rows.append({
            "batch_name": batch_name,
            "chunk_name": chunk_name,
            "local_index": int(i),
            "record_index": int(a.iloc[i]["record_index"]) if "record_index" in a.columns and pd.notna(a.iloc[i]["record_index"]) else None,
            "sequence_index": int(a.iloc[i]["sequence_index"]) if "sequence_index" in a.columns and pd.notna(a.iloc[i]["sequence_index"]) else None,
            "center_error": float(center_error[i]),
            "lens_error_deg": float(lens_error_deg[i]),
            "delta_center_error": float(delta_center_error[i]),
            "delta_lens_error_deg": float(delta_lens_error_deg[i]),
            "pred_extrinsics_path": str(pred_path),
        })

residual_df = pd.DataFrame(residual_rows)
residual_csv = chunk_manifest_dir / "pred_vs_anchor_pose_residual.csv"
residual_df.to_csv(residual_csv, index=False, encoding="utf-8")

missing_pred_df = pd.DataFrame(missing_pred_chunks)
missing_pred_csv = chunk_manifest_dir / "pred_vs_anchor_pose_residual_missing_pred.csv"
missing_pred_df.to_csv(missing_pred_csv, index=False, encoding="utf-8")

gate_rows = []
if len(residual_df):
    for chunk_name, cdf in residual_df.groupby("chunk_name", sort=True):
        gate_rows.append({
            "chunk_name": chunk_name,
            "row_count": int(len(cdf)),
            "center_error_mean": float(cdf["center_error"].mean()),
            "center_error_p95": float(cdf["center_error"].quantile(0.95)),
            "lens_error_deg_mean": float(cdf["lens_error_deg"].mean()),
            "lens_error_deg_p95": float(cdf["lens_error_deg"].quantile(0.95)),
            "delta_center_error_max": float(cdf["delta_center_error"].max()),
            "delta_lens_error_deg_max": float(cdf["delta_lens_error_deg"].max()),
        })
gate_df = pd.DataFrame(gate_rows)
gate_csv = chunk_manifest_dir / "premerge_pose_gate.csv"
gate_df.to_csv(gate_csv, index=False, encoding="utf-8")

if len(residual_df) == 0:
    status = "not_run"
elif len(missing_pred_df) > 0:
    status = "partial"
else:
    status = "ok"

summary = {
    "status": status,
    "residual_row_count": int(len(residual_df)),
    "missing_pred_chunk_count": int(len(missing_pred_df)),
    "gate_chunk_count": int(len(gate_df)),
    "residual_csv": str(residual_csv),
    "missing_pred_csv": str(missing_pred_csv),
    "gate_csv": str(gate_csv),
}
if len(residual_df) > 0:
    summary["center_error_mean"] = float(residual_df["center_error"].mean())
    summary["center_error_p95"] = float(residual_df["center_error"].quantile(0.95))
    summary["lens_error_deg_mean"] = float(residual_df["lens_error_deg"].mean())
    summary["lens_error_deg_p95"] = float(residual_df["lens_error_deg"].quantile(0.95))

save_json(final_outputs_diagnostics_dir / "premerge_pose_gate_summary.json", summary)
save_json(final_outputs_diagnostics_dir / "batch_residual_summary.json", summary)

print(json.dumps(summary, indent=2, ensure_ascii=False))
if len(gate_df):
    display(gate_df)
if len(missing_pred_df):
    display(missing_pred_df.head())
display_stage_summary(
    "13-1",
    "prediction validation",
    inputs=[
        {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
    ],
    outputs=[
        {"item": "pred_vs_anchor_pose_residual", "path": str(residual_csv)},
        {"item": "pred_vs_anchor_pose_residual_missing_pred", "path": str(missing_pred_csv)},
        {"item": "premerge_pose_gate", "path": str(gate_csv)},
        {"item": "premerge_pose_gate_summary", "path": str(final_outputs_diagnostics_dir / "premerge_pose_gate_summary.json")},
        {"item": "batch_residual_summary", "path": str(final_outputs_diagnostics_dir / "batch_residual_summary.json")},
    ],
    notes=[
        {"item": "status", "value": status},
        {"item": "missing_pred_chunk_count", "value": int(len(missing_pred_df))},
    ],
)
```


# 14 Merge

実行順: #14 完了で Drive 正本の main 出力まで終了

```python
#14-1
from pathlib import Path
import json
import shutil
import os
import subprocess
import sys

import numpy as np
import pandas as pd

missing_merge_deps = []
for module_name, package_name in [
    ("trimesh", "trimesh"),
    ("plyfile", "plyfile"),
    ("scipy", "scipy"),
]:
    try:
        __import__(module_name)
    except ModuleNotFoundError:
        missing_merge_deps.append(package_name)

if missing_merge_deps:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet", *missing_merge_deps],
        check=True,
    )

import trimesh
from plyfile import PlyData, PlyElement
from scipy.spatial import cKDTree

batch_preflight_status_path = Path("/content/runbook_batch_preflight_status.json")
if not batch_preflight_status_path.exists():
    print("# warning: batch execution preflight was not run; continued by self-heal path")

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
probe_root = Path(ctx["probe_root"])
results_root = Path(ctx["results_root"])
modeling_session_id = ctx["modeling_session_id"]
manifest_dir = Path(ctx["manifest_dir"])
final_outputs_dir = Path(ctx["final_outputs_dir"])
final_outputs_merged_dir = Path(ctx["final_outputs_merged_dir"])
final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_manifests_dir = Path(ctx["final_outputs_manifests_dir"])
final_outputs_chunk_evidence_dir = Path(ctx["final_outputs_chunk_evidence_dir"])

pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
global_pose_dir = pipeline_root / "global_pose_bootstrap"
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
merged_dir = Path(ctx.get("merged_dir", str(pipeline_root / "merged")))
merged_dir.mkdir(parents=True, exist_ok=True)
stage_11_2_dir = final_outputs_dir / "stage_11_2"
stage_11_3_dir = final_outputs_dir / "stage_11_3"
for p in [final_outputs_dir, final_outputs_merged_dir, final_outputs_diagnostics_dir, final_outputs_manifests_dir, final_outputs_chunk_evidence_dir, stage_11_2_dir, stage_11_3_dir]:
    p.mkdir(parents=True, exist_ok=True)

config_path = pipeline_root / "pipeline_config.json"
if config_path.exists():
    config = json.loads(config_path.read_text(encoding="utf-8"))
else:
    config = {
        "MODEL_ID": "depth-anything/DA3NESTED-GIANT-LARGE-1.1",
        "BUNDLE_MODEL_SLUG": "nestedgiantlarge11",
        "PROCESS_RES": 504,
        "CHUNK_SIZE": 18,
        "STEP": 12,
        "ADOPT_SIZE": 12,
        "CHUNKS_PER_BATCH": 3,
        "GLOBAL_CAMERA_SOURCE": "extrinsics_w2c_arc.npy",
        "USE_TARGET_CHUNK_WINDOW": False,
        "TARGET_CHUNK_WINDOW_START_1BASED": 1,
        "TARGET_CHUNK_WINDOW_COUNT": 0,
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
BUNDLE_MODEL_SLUG = config["BUNDLE_MODEL_SLUG"]
REQUIRE_ALL_CHUNKS = True
config_snapshot = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8")) if Path("/content/config_snapshot.json").exists() else {}
MAKE_DRIVE_BUNDLE = bool(config_snapshot.get("MAKE_DRIVE_BUNDLE", False))

chunk_index_all_path = chunk_manifest_dir / "chunk_index_all.csv"
if chunk_index_all_path.exists():
    all_chunks_df = pd.read_csv(chunk_index_all_path)
else:
    inferred_chunk_names = sorted({
        p.parent.name
        for p in chunk_runs_dir.glob("*/_SUCCESS.json")
    } | {
        p.parent.parent.name
        for p in chunk_runs_dir.glob("*/gs_ply/0000.ply")
    } | {
        p.parent.parent.name
        for p in chunk_runs_dir.glob("*/gs_video/0000_extend.mp4")
    })
    all_chunks_df = pd.DataFrame([
        {
            "chunk_id": i,
            "chunk_name": name,
            "global_start": None,
            "global_end": None,
            "frame_count": None,
            "adopt_local_start": None,
            "adopt_local_end": None,
            "chunk_csv": None,
        }
        for i, name in enumerate(inferred_chunk_names)
    ])
    chunk_manifest_dir.mkdir(parents=True, exist_ok=True)
    all_chunks_df.to_csv(chunk_index_all_path, index=False, encoding="utf-8")

def ensure_target_chunk_manifest():
    target_path = chunk_manifest_dir / "chunk_index_target.csv"
    if target_path.exists():
        return pd.read_csv(target_path)
    all_path = chunk_manifest_dir / "chunk_index_all.csv"
    assert all_path.exists(), all_path
    base_df = pd.read_csv(all_path)
    if config.get("USE_TARGET_CHUNK_WINDOW", False):
        start_0 = max(0, int(config.get("TARGET_CHUNK_WINDOW_START_1BASED", 1)) - 1)
        end_0 = min(start_0 + int(config.get("TARGET_CHUNK_WINDOW_COUNT", 3)), len(base_df))
        target_chunks_df = base_df.iloc[start_0:end_0].copy().reset_index(drop=True)
    else:
        target_chunks_df = base_df.copy().reset_index(drop=True)
    target_chunks_df.to_csv(target_path, index=False, encoding="utf-8")
    return target_chunks_df

def resolve_chunk_input_dir(chunk_name: str) -> Path:
    primary = chunk_runs_dir / chunk_name
    assert (primary / "pred_extrinsics.npy").exists() and (primary / "chunk_input_frames.csv").exists(), {
        "chunk_name": chunk_name,
        "missing_dir": str(primary),
        "reason": "run #10-1 before #11",
    }
    return primary

completed_chunk_names = sorted({
    p.parent.name
    for p in chunk_runs_dir.glob("*/_SUCCESS.json")
})
ply_ready_chunk_names = sorted({
    p.parent.name
    for p in chunk_runs_dir.glob("*/gs_ply/0000.ply")
})
all_chunks_df = pd.read_csv(chunk_manifest_dir / "chunk_index_all.csv")
target_chunks_df = ensure_target_chunk_manifest()
completed_chunks_df = target_chunks_df[target_chunks_df["chunk_name"].isin(completed_chunk_names)].copy()
ply_ready_target_chunk_names = sorted(set(ply_ready_chunk_names) & set(target_chunks_df["chunk_name"].tolist()))

batch_summaries = sorted({
    str(p) for p in chunk_runs_dir.glob("batch_*/batch_summary.json")
})
summary_rows = [json.loads(Path(p).read_text(encoding="utf-8")) for p in batch_summaries]
(merged_dir / "all_batch_summary_arc.json").write_text(json.dumps(summary_rows, indent=2, ensure_ascii=False), encoding="utf-8")
premerge_pose_validation_path = merged_dir / "premerge_pose_validation.json"

if not premerge_pose_validation_path.exists():
    merge_summary = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "status": "skipped",
        "reason": "premerge_pose_validation_required",
        "premerge_pose_validation_path": str(premerge_pose_validation_path),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary_arc.json"),
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
    raise AssertionError("run #10-5 pre-merge pose gate before #11 merge")

premerge_pose_validation = json.loads(premerge_pose_validation_path.read_text(encoding="utf-8"))
if premerge_pose_validation.get("status") != "ok":
    merge_summary = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "status": "skipped",
        "reason": "premerge_pose_validation_failed",
        "premerge_pose_validation_path": str(premerge_pose_validation_path),
        "hard_fail_count": int(premerge_pose_validation.get("hard_fail_count", 0)),
        "failed_chunks": premerge_pose_validation.get("failed_chunks", []),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary_arc.json"),
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
    raise AssertionError(premerge_pose_validation)

if REQUIRE_ALL_CHUNKS and len(completed_chunks_df) < len(target_chunks_df):
    merge_summary = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "status": "skipped",
        "reason": "waiting_for_all_chunks",
        "completed_chunk_count": int(len(completed_chunks_df)),
        "ply_ready_chunk_count": int(len(ply_ready_target_chunk_names)),
        "all_chunk_count": int(len(target_chunks_df)),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary_arc.json"),
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
else:
    global_centers_df = pd.read_csv(global_pose_dir / "camera_center_matrix_arc.csv")
    global_camera_matrix_df = pd.read_csv(global_pose_dir / "camera_matrix_full_arc.csv")
    global_anchor_df = pd.read_csv(global_pose_dir / "camera_anchor_full_arc.csv")
    input_manifest_path = manifest_dir / "da3_input_manifest.csv"
    assert input_manifest_path.exists(), input_manifest_path
    input_manifest_df = pd.read_csv(input_manifest_path)
    assert global_anchor_df["record_index"].is_unique, "global anchor record_index must be unique"
    OWNER_TOPK = 6
    OWNER_W_DIST = 1.0
    OWNER_W_DIR = 0.35
    OWNER_W_BLUR = 0.25
    OWNER_W_INDEX = 0.02
    OWNER_RECORD_MARGIN = 6
    TRANSFORM_CENTER_RMSE_WARN = 0.25
    TRANSFORM_ROT_DIR_WARN = 0.25

    def load_scene_any(path: Path):
        loaded = trimesh.load(str(path), force="scene")
        if isinstance(loaded, trimesh.Scene):
            return loaded
        scene = trimesh.Scene()
        if hasattr(loaded, "geometry"):
            for name, geom in loaded.geometry.items():
                scene.add_geometry(geom, node_name=name)
        else:
            scene.add_geometry(loaded)
        return scene

    def iter_baked_scene_geometry(scene: trimesh.Scene):
        dumped = None
        if hasattr(scene, "dump"):
            try:
                dumped = scene.dump(concatenate=False)
            except TypeError:
                dumped = scene.dump()
        if isinstance(dumped, (list, tuple)) and len(dumped) > 0:
            for idx, geom in enumerate(dumped):
                if geom is None:
                    continue
                if hasattr(geom, "copy"):
                    geom = geom.copy()
                yield f"dump_{idx:04d}", geom
            return
        for gname, geom in scene.geometry.items():
            geom2 = geom.copy() if hasattr(geom, "copy") else geom
            yield str(gname), geom2

    def to_4x4(ext):
        ext = np.asarray(ext).astype(np.float32)
        if ext.shape == (4, 4):
            return ext
        if ext.shape == (3, 4):
            M = np.eye(4, dtype=np.float32)
            M[:3, :] = ext
            return M
        raise ValueError(f"unexpected extrinsic shape: {ext.shape}")

    def c2w_rows_to_map(df: pd.DataFrame):
        out = {}
        cols = [f"m{i}{j}" for i in range(4) for j in range(4)]
        for row in df.itertuples(index=False):
            M = np.array([getattr(row, c) for c in cols], dtype=np.float32).reshape(4, 4)
            out[int(row.record_index)] = M
        return out

    def lens_direction_from_c2w(c2w: np.ndarray):
        axis = -np.asarray(c2w[:3, 2], dtype=np.float32)
        norm = float(np.linalg.norm(axis))
        return axis / max(norm, 1e-12)

    def up_direction_from_c2w(c2w: np.ndarray):
        axis = -np.asarray(c2w[:3, 1], dtype=np.float32)
        norm = float(np.linalg.norm(axis))
        return axis / max(norm, 1e-12)

    def normalize_vec(vec: np.ndarray, fallback: np.ndarray):
        vec = np.asarray(vec, dtype=np.float32)
        norm = float(np.linalg.norm(vec))
        if norm <= 1e-12:
            fallback = np.asarray(fallback, dtype=np.float32)
            fallback_norm = float(np.linalg.norm(fallback))
            assert fallback_norm > 1e-12, "fallback vector must be non-zero"
            return fallback / fallback_norm
        return vec / norm

    def build_anchor_c2w(fallback_c2w: np.ndarray, rec) -> np.ndarray:
        M = np.asarray(fallback_c2w, dtype=np.float32).copy()
        center = np.array([float(rec.cx_world), float(rec.cy_world), float(rec.cz_world)], dtype=np.float32)
        anchor_lens = normalize_vec(
            np.array([float(rec.anchor_lens_x), float(rec.anchor_lens_y), float(rec.anchor_lens_z)], dtype=np.float32),
            lens_direction_from_c2w(M),
        )
        anchor_up = normalize_vec(
            np.array([float(rec.anchor_up_x), float(rec.anchor_up_y), float(rec.anchor_up_z)], dtype=np.float32),
            up_direction_from_c2w(M),
        )
        z_col = normalize_vec(-anchor_lens, M[:3, 2])
        x_seed = np.cross(-anchor_up, z_col)
        x_col = normalize_vec(x_seed, M[:3, 0])
        y_col = normalize_vec(np.cross(z_col, x_col), M[:3, 1])
        if float(np.dot(y_col, -anchor_up)) < 0.0:
            x_col = -x_col
            y_col = -y_col
        M[:3, 0] = x_col
        M[:3, 1] = y_col
        M[:3, 2] = z_col
        M[:3, 3] = center
        return M

    def c2w_list_from_extrinsics(extrinsics):
        mats = []
        for ext in extrinsics:
            c2w = np.linalg.inv(to_4x4(ext)).astype(np.float32)
            mats.append((c2w @ LOCAL_CAMERA_BASIS).astype(np.float32))
        return mats

    def estimate_pose_aware_similarity(local_c2w_list, global_c2w_list, estimate_scale=True):
        assert len(local_c2w_list) == len(global_c2w_list) >= 2, {"local_len": len(local_c2w_list), "global_len": len(global_c2w_list)}

        src_dirs = []
        dst_dirs = []
        src_centers = []
        dst_centers = []
        for local_c2w, global_c2w in zip(local_c2w_list, global_c2w_list):
            src_dirs.append(lens_direction_from_c2w(local_c2w))
            src_dirs.append(up_direction_from_c2w(local_c2w))
            dst_dirs.append(lens_direction_from_c2w(global_c2w))
            dst_dirs.append(up_direction_from_c2w(global_c2w))
            src_centers.append(local_c2w[:3, 3])
            dst_centers.append(global_c2w[:3, 3])

        src_dirs = np.asarray(src_dirs, dtype=np.float64)
        dst_dirs = np.asarray(dst_dirs, dtype=np.float64)
        src_centers = np.asarray(src_centers, dtype=np.float64)
        dst_centers = np.asarray(dst_centers, dtype=np.float64)

        H = dst_dirs.T @ src_dirs
        U, _, Vt = np.linalg.svd(H)
        S = np.eye(3, dtype=np.float64)
        if np.linalg.det(U) * np.linalg.det(Vt) < 0:
            S[-1, -1] = -1.0
        R = U @ S @ Vt

        src_mean = src_centers.mean(axis=0)
        dst_mean = dst_centers.mean(axis=0)
        src_c = src_centers - src_mean
        dst_c = dst_centers - dst_mean
        src_rot = (R @ src_c.T).T

        if estimate_scale:
            denom = float(np.sum(src_rot ** 2))
            numer = float(np.sum(dst_c * src_rot))
            scale = numer / max(denom, 1e-12)
        else:
            scale = 1.0

        t = dst_mean - scale * (R @ src_mean)
        pred = (scale * (R @ src_centers.T)).T + t
        center_rmse = float(np.sqrt(np.mean(np.sum((pred - dst_centers) ** 2, axis=1))))
        rot_residual = float(np.mean(np.linalg.norm((R @ src_dirs.T).T - dst_dirs, axis=1)))

        T = np.eye(4, dtype=np.float64)
        T[:3, :3] = scale * R
        T[:3, 3] = t
        diag = {
            "scale": float(scale),
            "rotation_det": float(np.linalg.det(R)),
            "center_rmse": center_rmse,
            "rotation_dir_residual": rot_residual,
            "positive_similarity_ok": bool(scale > 0.0),
            "scale_in_range_ok": bool(TRANSFORM_SCALE_MIN <= scale <= TRANSFORM_SCALE_MAX),
            "center_rmse_ok": bool(center_rmse <= TRANSFORM_CENTER_RMSE_MAX),
            "rotation_dir_ok": bool(rot_residual <= TRANSFORM_ROT_DIR_MAX),
        }
        diag["hard_fail"] = bool(
            (scale <= 0.0)
            or (scale < TRANSFORM_SCALE_MIN)
            or (scale > TRANSFORM_SCALE_MAX)
            or (center_rmse > TRANSFORM_CENTER_RMSE_MAX)
            or (rot_residual > TRANSFORM_ROT_DIR_MAX)
        )
        return T.astype(np.float32), diag

    global_camera_map = c2w_rows_to_map(global_camera_matrix_df)
    global_frame_meta_df = global_anchor_df.merge(
        input_manifest_df[["record_index", "qc_blur_ok", "blur_score"]],
        on="record_index",
        how="left",
    )
    global_frame_meta_df["lens_x"] = global_frame_meta_df["anchor_lens_x"].astype(float)
    global_frame_meta_df["lens_y"] = global_frame_meta_df["anchor_lens_y"].astype(float)
    global_frame_meta_df["lens_z"] = global_frame_meta_df["anchor_lens_z"].astype(float)
    global_frame_meta_df["qc_blur_ok"] = global_frame_meta_df["qc_blur_ok"].fillna(False).astype(bool)
    global_frame_meta_df["blur_score"] = global_frame_meta_df["blur_score"].fillna(0.0)
    global_frame_meta_df = global_frame_meta_df.sort_values("record_index").reset_index(drop=True)
    global_center_tree = cKDTree(global_frame_meta_df[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32))

    def assign_vertex_owners(xyz_w: np.ndarray, chunk_df: pd.DataFrame):
        chunk_record_df = global_frame_meta_df.loc[
            global_frame_meta_df["record_index"].isin(chunk_df["record_index"].astype(int).tolist())
        ].copy()
        record_min = int(chunk_df["record_index"].min())
        record_max = int(chunk_df["record_index"].max())
        candidate_mode = "chunk_only"
        candidate_df = chunk_record_df
        if len(candidate_df) < 2:
            candidate_mode = "chunk_with_margin"
            candidate_df = global_frame_meta_df.loc[
                global_frame_meta_df["record_index"].between(record_min - OWNER_RECORD_MARGIN, record_max + OWNER_RECORD_MARGIN)
            ].copy()
        if len(candidate_df) < 2:
            candidate_mode = "global_fallback"
            candidate_df = global_frame_meta_df.copy()
        candidate_tree = cKDTree(candidate_df[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32))

        k = min(OWNER_TOPK, len(candidate_df))
        dists, idxs = candidate_tree.query(xyz_w, k=k)
        if k == 1:
            dists = dists[:, None]
            idxs = idxs[:, None]

        candidate_meta = candidate_df.iloc[idxs.reshape(-1)].reset_index(drop=True)
        candidate_centers = candidate_meta[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32).reshape(len(xyz_w), k, 3)
        candidate_axes = candidate_meta[["lens_x", "lens_y", "lens_z"]].to_numpy(dtype=np.float32).reshape(len(xyz_w), k, 3)
        candidate_blur_ok = candidate_meta["qc_blur_ok"].to_numpy(dtype=bool).reshape(len(xyz_w), k)
        candidate_records = candidate_meta["record_index"].to_numpy(dtype=np.int64).reshape(len(xyz_w), k)

        view_vec = xyz_w[:, None, :] - candidate_centers
        view_norm = np.linalg.norm(view_vec, axis=2, keepdims=True)
        view_dir = view_vec / np.maximum(view_norm, 1e-12)
        dir_cos = np.sum(view_dir * candidate_axes, axis=2)
        dir_term = 1.0 - np.clip(dir_cos, -1.0, 1.0)
        blur_penalty = np.where(candidate_blur_ok, 0.0, 1.0)

        chunk_record_center = float(chunk_df["record_index"].median())
        chunk_record_span = float(max(chunk_df["record_index"].max() - chunk_df["record_index"].min(), 1))
        index_penalty = np.minimum(np.abs(candidate_records - chunk_record_center) / chunk_record_span, 1.0)

        score = (
            OWNER_W_DIST * np.asarray(dists, dtype=np.float32)
            + OWNER_W_DIR * dir_term.astype(np.float32)
            + OWNER_W_BLUR * blur_penalty.astype(np.float32)
            + OWNER_W_INDEX * index_penalty.astype(np.float32)
        )

        best_local = np.argmin(score, axis=1)
        row_idx = np.arange(len(xyz_w))
        return pd.DataFrame({
            "vertex_index": np.arange(len(xyz_w), dtype=np.int64),
            "owner_record_index": candidate_records[row_idx, best_local].astype(np.int64),
            "owner_candidate_mode": candidate_mode,
            "owner_candidate_record_min": int(candidate_df["record_index"].min()),
            "owner_candidate_record_max": int(candidate_df["record_index"].max()),
            "owner_score": score[row_idx, best_local].astype(np.float32),
            "owner_dist": np.asarray(dists, dtype=np.float32)[row_idx, best_local].astype(np.float32),
            "owner_dir_cos": dir_cos[row_idx, best_local].astype(np.float32),
            "owner_blur_ok": candidate_blur_ok[row_idx, best_local].astype(bool),
        })

    transform_rows = []
    keep_rows = []
    warning_rows = []
    all_vertices = []
    dtype_ref = None
    master_scene = trimesh.Scene()
    owner_hist_rows = []
    chunk_assign_rows = []

    for row in completed_chunks_df.itertuples(index=False):
        out_dir = chunk_runs_dir / row.chunk_name
        input_dir = resolve_chunk_input_dir(row.chunk_name)
        ply_path = input_dir / "gs_ply" / "0000.ply"
        pred_ext_path = input_dir / "pred_extrinsics.npy"
        chunk_input_path = input_dir / "chunk_input_frames.csv"
        glb_path = input_dir / "scene.glb"
        if not (ply_path.exists() and pred_ext_path.exists() and chunk_input_path.exists()):
            continue

        out_dir.mkdir(parents=True, exist_ok=True)

        chunk_df = pd.read_csv(chunk_input_path)
        pred_extrinsics = np.load(pred_ext_path)
        chunk_df.attrs["chunk_name"] = row.chunk_name
        assert chunk_df["record_index"].is_unique, f"duplicate record_index in chunk_input_frames: {row.chunk_name}"
        assert pred_extrinsics.shape[0] == len(chunk_df), {"chunk_name": row.chunk_name, "pred_len": int(pred_extrinsics.shape[0]), "chunk_len": int(len(chunk_df))}

        local_c2w_list = c2w_list_from_extrinsics(pred_extrinsics)
        local_centers = np.stack([m[:3, 3] for m in local_c2w_list], axis=0).astype(np.float32)

        merged = chunk_df.merge(
            global_anchor_df,
            on=["record_index", "image_file_name", "image_path", "frame_timestamp_ns", "capture_timestamp_ns"],
            how="left",
            validate="one_to_one",
        )
        assert len(merged) == len(chunk_df), {"chunk_name": row.chunk_name, "merged_len": len(merged), "chunk_len": len(chunk_df)}
        assert not merged[["cx_world", "cy_world", "cz_world", "anchor_lens_x", "anchor_lens_y", "anchor_lens_z", "anchor_up_x", "anchor_up_y", "anchor_up_z"]].isnull().any().any(), f"global anchor missing: {row.chunk_name}"
        global_c2w_list = [build_anchor_c2w(global_camera_map[int(rec.record_index)], rec) for rec in merged.itertuples(index=False)]

        T_c_to_w0, align_diag = estimate_pose_aware_similarity(local_c2w_list, global_c2w_list, estimate_scale=True)

        T_path = chunk_manifest_dir / f"{row.chunk_name}_to_w0.npy"
        np.save(T_path, T_c_to_w0)
        transform_rows.append({
            "chunk_name": row.chunk_name,
            "frame_count": int(len(chunk_df)),
            "transform_path": str(T_path),
            "local_camera_basis": "perm_yxz_sign_ppn",
            "scale": float(align_diag["scale"]),
            "rotation_det": float(align_diag["rotation_det"]),
            "center_rmse": float(align_diag["center_rmse"]),
            "rotation_dir_residual": float(align_diag["rotation_dir_residual"]),
            "positive_similarity_ok": bool(align_diag["positive_similarity_ok"]),
            "scale_in_range_ok": bool(align_diag["scale_in_range_ok"]),
            "center_rmse_ok": bool(align_diag["center_rmse_ok"]),
            "rotation_dir_ok": bool(align_diag["rotation_dir_ok"]),
            "hard_fail": bool(align_diag["hard_fail"]),
        })
        assert not align_diag["hard_fail"], {
            "chunk_name": row.chunk_name,
            "reason": "invalid_pose_similarity",
            "align_diag": align_diag,
        }

        adopted_record_set = set(chunk_df.loc[chunk_df["is_adopted_region"] == True, "record_index"].astype(int).tolist())

        ply = PlyData.read(str(ply_path))
        df = pd.DataFrame(ply["vertex"].data)
        xyz = df[["x", "y", "z"]].to_numpy(dtype=np.float32)

        A = T_c_to_w0[:3, :3].astype(np.float32)
        t32 = T_c_to_w0[:3, 3].astype(np.float32)
        xyz_w = (A @ xyz.T).T + t32
        assignment_df = assign_vertex_owners(xyz_w, chunk_df)
        assignment_df["chunk_name"] = row.chunk_name
        keep = assignment_df["owner_record_index"].isin(adopted_record_set).to_numpy(dtype=bool)
        assignment_df["kept"] = keep
        assignment_df.to_csv(out_dir / "vertex_assignment_summary.csv", index=False, encoding="utf-8")

        chunk_evidence_dir = final_outputs_chunk_evidence_dir / row.chunk_name
        chunk_evidence_dir.mkdir(parents=True, exist_ok=True)
        chunk_evidence_copy_plan = [
            (out_dir / "vertex_assignment_summary.csv", chunk_evidence_dir / "vertex_assignment_summary.csv"),
            (out_dir / "chunk_input_frames.csv", chunk_evidence_dir / "chunk_input_frames.csv"),
            (out_dir / "pred_extrinsics.npy", chunk_evidence_dir / "pred_extrinsics.npy"),
            (out_dir / "pred_intrinsics.npy", chunk_evidence_dir / "pred_intrinsics.npy"),
        ]
        for src, dst in chunk_evidence_copy_plan:
            if src.exists():
                shutil.copy2(src, dst)

        owner_hist = assignment_df.groupby("owner_record_index", as_index=False).size().rename(columns={"size": "owner_vertex_count"})
        owner_hist["chunk_name"] = row.chunk_name
        owner_hist_rows.append(owner_hist)

        chunk_assign = assignment_df.groupby(["owner_record_index", "owner_blur_ok"], as_index=False).agg(
            owner_vertex_count=("vertex_index", "count"),
            owner_score_mean=("owner_score", "mean"),
            owner_dist_mean=("owner_dist", "mean"),
            owner_dir_cos_mean=("owner_dir_cos", "mean"),
        )
        chunk_assign["chunk_name"] = row.chunk_name
        chunk_assign_rows.append(chunk_assign)

        df["x"] = xyz_w[:, 0]
        df["y"] = xyz_w[:, 1]
        df["z"] = xyz_w[:, 2]
        df = df.loc[keep].copy()

        if len(df) > 0:
            records = df.to_records(index=False)
            if dtype_ref is None:
                dtype_ref = records.dtype
            else:
                records = records.astype(dtype_ref, copy=False)
            all_vertices.append(records)

        transform_warning = bool(
            align_diag["center_rmse"] > TRANSFORM_CENTER_RMSE_WARN
            or align_diag["rotation_dir_residual"] > TRANSFORM_ROT_DIR_WARN
        )
        keep_zero_chunk = int(len(df)) == 0
        warning_rows.append({
            "chunk_name": row.chunk_name,
            "transform_warning": transform_warning,
            "keep_zero_chunk": keep_zero_chunk,
            "fallback_used": False,
        })
        keep_rows.append({
            "chunk_name": row.chunk_name,
            "kept_vertices": int(len(df)),
            "owner_record_unique_count": int(assignment_df["owner_record_index"].nunique()),
            "owner_candidate_mode": str(assignment_df["owner_candidate_mode"].iloc[0]),
            "owner_record_min": int(assignment_df["owner_record_index"].min()),
            "owner_record_max": int(assignment_df["owner_record_index"].max()),
            "owner_blur_ok_ratio": float(assignment_df["owner_blur_ok"].mean()),
            "owner_score_mean": float(assignment_df["owner_score"].mean()),
        })
        assert not keep_zero_chunk, {"chunk_name": row.chunk_name, "reason": "keep_zero_chunk"}

        if glb_path.exists():
            scene = load_scene_any(glb_path)
            for gname, geom in iter_baked_scene_geometry(scene):
                geom2 = geom.copy() if hasattr(geom, "copy") else geom
                if hasattr(geom2, "apply_transform"):
                    geom2.apply_transform(T_c_to_w0)
                master_scene.add_geometry(geom2, node_name=f"{row.chunk_name}_{gname}")

    transform_df = pd.DataFrame(transform_rows)
    transform_df.to_csv(chunk_manifest_dir / "chunk_global_transforms_arc.csv", index=False, encoding="utf-8")

    keep_df = pd.DataFrame(keep_rows)
    keep_summary_path = merged_dir / "chunk_keep_summary_arc.csv"
    keep_df.to_csv(keep_summary_path, index=False, encoding="utf-8")
    transform_quality_path = merged_dir / "chunk_transform_quality_arc.csv"
    transform_df.to_csv(transform_quality_path, index=False, encoding="utf-8")

    if owner_hist_rows:
        pd.concat(owner_hist_rows, ignore_index=True).to_csv(merged_dir / "owner_record_histogram_arc.csv", index=False, encoding="utf-8")
    if chunk_assign_rows:
        pd.concat(chunk_assign_rows, ignore_index=True).to_csv(merged_dir / "chunk_assignment_summary_arc.csv", index=False, encoding="utf-8")

    warning_summary = {
        "transform_warning_count": int(sum(bool(x["transform_warning"]) for x in warning_rows)),
        "keep_zero_chunk_count": int(sum(bool(x["keep_zero_chunk"]) for x in warning_rows)),
        "fallback_used_count": 0,
        "rows": warning_rows,
    }
    (merged_dir / "merge_warning_summary_arc.json").write_text(json.dumps(warning_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    merged_ply_path = merged_dir / "merged_gs_arc.ply"
    if all_vertices:
        merged_vertices = np.concatenate(all_vertices, axis=0)
        PlyData([PlyElement.describe(merged_vertices, "vertex")], text=False).write(str(merged_ply_path))

    stage_11_2_copy_plan = [
        (merged_ply_path, stage_11_2_dir / "merged_gs_arc.ply"),
        (chunk_manifest_dir / "chunk_global_transforms_arc.csv", stage_11_2_dir / "chunk_global_transforms_arc.csv"),
        (keep_summary_path, stage_11_2_dir / "chunk_keep_summary_arc.csv"),
        (transform_quality_path, stage_11_2_dir / "chunk_transform_quality_arc.csv"),
        (merged_dir / "owner_record_histogram_arc.csv", stage_11_2_dir / "owner_record_histogram_arc.csv"),
        (merged_dir / "chunk_assignment_summary_arc.csv", stage_11_2_dir / "chunk_assignment_summary_arc.csv"),
        (merged_dir / "merge_warning_summary_arc.json", stage_11_2_dir / "merge_warning_summary_arc.json"),
        (merged_dir / "all_batch_summary_arc.json", stage_11_2_dir / "all_batch_summary_arc.json"),
    ]
    stage_11_2_files = []
    for src, dst in stage_11_2_copy_plan:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            stage_11_2_files.append(str(dst))
    merge_resume_state = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "stage": "11-2-complete",
        "completed_chunk_count": int(len(completed_chunks_df)),
        "all_chunk_count": int(len(target_chunks_df)),
        "stage_11_2_dir": str(stage_11_2_dir),
        "stage_11_2_files": stage_11_2_files,
        "merged_ply_path": str(merged_ply_path) if merged_ply_path.exists() else None,
    }
    (final_outputs_diagnostics_dir / "merge_resume_state.json").write_text(json.dumps(merge_resume_state, indent=2, ensure_ascii=False), encoding="utf-8")

    merged_glb_path = merged_dir / "merged_scene_arc.glb"
    if len(master_scene.geometry) > 0:
        master_scene.export(str(merged_glb_path))

    for src in stage_11_2_dir.glob("*"):
        if src.is_file():
            shutil.copy2(src, stage_11_3_dir / src.name)
    if merged_glb_path.exists():
        shutil.copy2(merged_glb_path, stage_11_3_dir / "merged_scene_arc.glb")
    merge_resume_state.update({
        "stage": "11-3-complete",
        "stage_11_3_dir": str(stage_11_3_dir),
        "merged_glb_path": str(merged_glb_path) if merged_glb_path.exists() else None,
    })
    (final_outputs_diagnostics_dir / "merge_resume_state.json").write_text(json.dumps(merge_resume_state, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(final_outputs_diagnostics_dir / "merge_resume_state.json", stage_11_3_dir / "merge_resume_state.json")

    final_output_copy_plan = [
        (merged_ply_path, final_outputs_merged_dir / "merged_gs_arc.ply"),
        (merged_glb_path, final_outputs_merged_dir / "merged_scene_arc.glb"),
        (chunk_manifest_dir / "chunk_global_transforms_arc.csv", final_outputs_diagnostics_dir / "chunk_global_transforms_arc.csv"),
        (keep_summary_path, final_outputs_diagnostics_dir / "chunk_keep_summary_arc.csv"),
        (transform_quality_path, final_outputs_diagnostics_dir / "chunk_transform_quality_arc.csv"),
        (merged_dir / "owner_record_histogram_arc.csv", final_outputs_diagnostics_dir / "owner_record_histogram_arc.csv"),
        (merged_dir / "chunk_assignment_summary_arc.csv", final_outputs_diagnostics_dir / "chunk_assignment_summary_arc.csv"),
        (merged_dir / "merge_warning_summary_arc.json", final_outputs_diagnostics_dir / "merge_warning_summary_arc.json"),
        (merged_dir / "all_batch_summary_arc.json", final_outputs_diagnostics_dir / "all_batch_summary_arc.json"),
        (input_manifest_path, final_outputs_manifests_dir / "da3_input_manifest.csv"),
        (global_pose_dir / "camera_center_matrix_arc.csv", final_outputs_manifests_dir / "camera_center_matrix_arc.csv"),
        (global_pose_dir / "camera_matrix_full_arc.csv", final_outputs_manifests_dir / "camera_matrix_full_arc.csv"),
        (global_pose_dir / "camera_anchor_full_arc.csv", final_outputs_manifests_dir / "camera_anchor_full_arc.csv"),
        (chunk_manifest_dir / "chunk_index_all.csv", final_outputs_manifests_dir / "chunk_index_all.csv"),
        (chunk_manifest_dir / "batch_plan.csv", final_outputs_manifests_dir / "batch_plan.csv"),
    ]
    final_output_files = []
    for src, dst in final_output_copy_plan:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            final_output_files.append({
                "label": dst.name,
                "source_path": str(src),
                "drive_path": str(dst),
            })

    bundle_summary = {
        "status": "drive_only",
        "reason": "drive_outputs_ready_local_bundle_is_separate_stage",
    }

    if MAKE_DRIVE_BUNDLE:
        bundle_summary = {
            "status": "drive_only",
            "drive_visible_dir": str(probe_root),
            "drive_pipeline_root": str(pipeline_root),
            "drive_results_root": str(results_root),
            "local_bundle_stage": "#11-1",
            "download_requested": False,
        }

    final_output_manifest = {
        "status": "ok" if final_output_files else "partial",
        "drive_visible_dir": str(probe_root),
        "final_outputs_dir": str(final_outputs_dir),
        "final_outputs_merged_dir": str(final_outputs_merged_dir),
        "final_outputs_diagnostics_dir": str(final_outputs_diagnostics_dir),
        "final_outputs_manifests_dir": str(final_outputs_manifests_dir),
        "final_outputs_chunk_evidence_dir": str(final_outputs_chunk_evidence_dir),
        "stage_11_2_dir": str(stage_11_2_dir),
        "stage_11_3_dir": str(stage_11_3_dir),
        "chunk_evidence_dirs": sorted([str(p) for p in final_outputs_chunk_evidence_dir.glob("*") if p.is_dir()]),
        "file_count": int(len(final_output_files)),
        "files": final_output_files,
    }
    (final_outputs_dir / "final_output_manifest_arc.json").write_text(json.dumps(final_output_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    merge_summary = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "status": "ok" if all_vertices else "skipped",
        "reason": None if all_vertices else "no kept vertices",
        "completed_chunk_count": int(len(completed_chunks_df)),
        "all_chunk_count": int(len(target_chunks_df)),
        "merged_ply_path": str(merged_ply_path) if merged_ply_path.exists() else None,
        "merged_glb_path": str(merged_glb_path) if merged_glb_path.exists() else None,
        "chunk_global_transforms_path": str(chunk_manifest_dir / "chunk_global_transforms_arc.csv"),
        "chunk_keep_summary_path": str(keep_summary_path),
        "chunk_transform_quality_path": str(transform_quality_path),
        "owner_record_histogram_path": str(merged_dir / "owner_record_histogram_arc.csv"),
        "chunk_assignment_summary_path": str(merged_dir / "chunk_assignment_summary_arc.csv"),
        "merge_warning_summary_path": str(merged_dir / "merge_warning_summary_arc.json"),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary_arc.json"),
        "final_outputs_dir": str(final_outputs_dir),
        "final_output_manifest_path": str(final_outputs_dir / "final_output_manifest_arc.json"),
        "bundle_summary": bundle_summary,
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(merged_dir / "merge_summary.json", final_outputs_diagnostics_dir / "merge_summary.json")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
    display_stage_summary(
        "14-1",
        "merge",
        inputs=[
            {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
            {"item": "camera_anchor_full", "path": str(global_pose_dir / "camera_anchor_full_arc.csv")},
            {"item": "da3_input_manifest", "path": str(input_manifest_path)},
        ],
        outputs=[
            {"item": "merge_summary", "path": str(merged_dir / "merge_summary.json")},
            {"item": "merged_gs", "path": str(merged_ply_path)},
            {"item": "merged_scene_glb", "path": str(merged_glb_path)},
            {"item": "final_output_manifest", "path": str(final_outputs_dir / "final_output_manifest_arc.json")},
            {"item": "chunk_global_transforms", "path": str(chunk_manifest_dir / "chunk_global_transforms_arc.csv")},
            {"item": "chunk_keep_summary", "path": str(keep_summary_path)},
            {"item": "chunk_transform_quality", "path": str(transform_quality_path)},
        ],
        notes=[
            {"item": "completed_chunk_count", "value": int(len(completed_chunks_df))},
            {"item": "status", "value": merge_summary["status"]},
        ],
    )
```


# 15 Optional Bundle

実行順: #15 は任意。Drive 保存後に local zip が必要な時だけ使う

```python
#15-1
from pathlib import Path
import json
import shutil

merge_summary_path = Path("/content/runbook_session_context.json")
ctx = json.loads(merge_summary_path.read_text(encoding="utf-8"))
probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
merged_dir = Path(ctx.get("merged_dir", str(pipeline_root / "merged")))
pipeline_config_path = pipeline_root / "pipeline_config.json"
bundle_model_slug = "bundle"
if pipeline_config_path.exists():
    pipeline_config = json.loads(pipeline_config_path.read_text(encoding="utf-8"))
    bundle_model_slug = pipeline_config.get("BUNDLE_MODEL_SLUG", bundle_model_slug)
merge_summary_doc_path = merged_dir / "merge_summary.json"
assert merge_summary_doc_path.exists(), f"merge_summary not found: {merge_summary_doc_path}"
merge_summary = json.loads(merge_summary_doc_path.read_text(encoding="utf-8"))
assert merge_summary.get("status") == "ok", merge_summary
config_snapshot = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8")) if Path("/content/config_snapshot.json").exists() else {}
download_local_bundle = bool(config_snapshot.get("DOWNLOAD_LOCAL_BUNDLE", False))

local_bundle_base = f"{ctx['modeling_session_id']}_{bundle_model_slug}_{ctx.get('pipeline_slug', 'da3_ngl_batch_v01')}"
local_bundle_zip = Path("/content") / f"{local_bundle_base}.zip"
if local_bundle_zip.exists():
    local_bundle_zip.unlink()
shutil.make_archive(str(local_bundle_zip.with_suffix("")), "zip", root_dir=str(probe_root))

bundle_download_summary = {
    "status": "ok",
    "route": "da3-seq-anchor-batch-v02-local-bundle-download",
    "local_bundle_zip": str(local_bundle_zip),
    "manual_download_hint": f"from google.colab import files; files.download(r'{local_bundle_zip}')",
    "download_requested": download_local_bundle,
}
(merged_dir / "local_bundle_download_summary.json").write_text(
    json.dumps(bundle_download_summary, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
if download_local_bundle:
    from google.colab import files
    files.download(str(local_bundle_zip))
print(json.dumps(bundle_download_summary, indent=2, ensure_ascii=False))
print("# manual_download_hint")
print(bundle_download_summary["manual_download_hint"])
display_stage_summary(
    "15-1",
    "optional local bundle",
    inputs=[
        {"item": "merge_summary", "path": str(merge_summary_doc_path)},
    ],
    outputs=[
        {"item": "local_bundle_download_summary", "path": str(merged_dir / "local_bundle_download_summary.json")},
        {"item": "local_bundle_zip", "path": str(local_bundle_zip)},
    ],
    notes=[
        {"item": "download_requested", "value": bool(download_local_bundle)},
    ],
)
```


# 16 Cleanup Inventory

実行順: #16 -> #17。後片付け前に inventory を確認する

```python
#16-1
from pathlib import Path
import json
import os

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
probe_root = Path(ctx["probe_root"])
results_root = Path(ctx["results_root"])
manifest_dir = Path(ctx["manifest_dir"])
da3_nested_dir = Path(ctx["da3_nested_dir"])
da3_nested_gs_dir = Path(ctx["da3_nested_gs_dir"])
world_dir = Path(ctx["world_dir"])
final_outputs_dir = Path(ctx["final_outputs_dir"])
final_outputs_merged_dir = Path(ctx["final_outputs_merged_dir"])
final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_manifests_dir = Path(ctx["final_outputs_manifests_dir"])
final_outputs_chunk_evidence_dir = Path(ctx["final_outputs_chunk_evidence_dir"])

pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
global_pose_dir = pipeline_root / "global_pose_bootstrap"
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
merged_dir = Path(ctx.get("merged_dir", str(pipeline_root / "merged")))
merge_summary_path = merged_dir / "merge_summary.json"

def path_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return int(path.stat().st_size)
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            fp = Path(root) / name
            try:
                total += int(fp.stat().st_size)
            except FileNotFoundError:
                pass
    return int(total)

merge_summary = json.loads(merge_summary_path.read_text(encoding="utf-8")) if merge_summary_path.exists() else {}
merge_ok = bool(merge_summary.get("status") == "ok")

kept_groups = [
    {"block": "#6", "label": "manifest_dir", "path": str(manifest_dir)},
    {"block": "#6", "label": "final_outputs_dir", "path": str(final_outputs_dir)},
    {"block": "#6", "label": "final_outputs_merged_dir", "path": str(final_outputs_merged_dir)},
    {"block": "#6", "label": "final_outputs_diagnostics_dir", "path": str(final_outputs_diagnostics_dir)},
    {"block": "#6", "label": "final_outputs_manifests_dir", "path": str(final_outputs_manifests_dir)},
    {"block": "#6", "label": "final_outputs_chunk_evidence_dir", "path": str(final_outputs_chunk_evidence_dir)},
    {"block": "#7", "label": "da3_nested_dir", "path": str(da3_nested_dir)},
    {"block": "#7", "label": "da3_nested_gs_dir", "path": str(da3_nested_gs_dir)},
    {"block": "#7", "label": "world_dir", "path": str(world_dir)},
    {"block": "#8", "label": "global_pose_dir", "path": str(global_pose_dir)},
    {"block": "#8", "label": "chunk_manifest_dir", "path": str(chunk_manifest_dir)},
    {"block": "#11", "label": "merged_dir", "path": str(merged_dir)},
    {"block": "#11", "label": "da3_nested_gs_dir", "path": str(da3_nested_gs_dir)},
]

delete_candidates = []
if chunk_runs_dir.exists() and merge_ok:
    delete_candidates.append({
        "block": "#10",
        "path": str(chunk_runs_dir),
        "kind": "drive_dir",
        "reason": "chunk intermediate gs outputs already merged",
        "size_bytes": path_size_bytes(chunk_runs_dir),
    })

local_tmp_candidates = [
    ("#2", Path("/content/runbook_selected_input.json"), "local_tmp", "selected input pointer"),
    ("#4", Path("/content/runbook_paths.json"), "local_tmp", "resolved path cache"),
    ("#5", Path("/content/runbook_session_context.json"), "local_tmp", "session context cache"),
    ("#5", Path("/content/trajectreview_input"), "local_tmp", "extracted input workspace"),
]
local_bundle_download_summary_path = merged_dir / "local_bundle_download_summary.json"
local_bundle_zip = None
if local_bundle_download_summary_path.exists():
    local_bundle_zip = json.loads(local_bundle_download_summary_path.read_text(encoding="utf-8")).get("local_bundle_zip")
if not local_bundle_zip:
    local_bundle_zip = merge_summary.get("bundle_summary", {}).get("local_bundle_zip")
if local_bundle_zip:
    local_tmp_candidates.append(("#11", Path(local_bundle_zip), "local_tmp", "download-only local bundle zip"))

for block_no, p, kind, reason in local_tmp_candidates:
    if p.exists():
        delete_candidates.append({
            "block": block_no,
            "path": str(p),
            "kind": kind,
            "reason": reason,
            "size_bytes": path_size_bytes(p),
        })

cleanup_plan = {
    "drive_visible_dir": str(probe_root),
    "drive_final_outputs_dir": str(final_outputs_dir),
    "results_root": str(results_root),
    "merge_status": merge_summary.get("status"),
    "kept_groups": kept_groups,
    "delete_candidate_count": int(len(delete_candidates)),
    "delete_candidate_total_bytes": int(sum(x["size_bytes"] for x in delete_candidates)),
    "delete_candidates": delete_candidates,
}
(merged_dir / "cleanup_plan.json").write_text(json.dumps(cleanup_plan, indent=2, ensure_ascii=False), encoding="utf-8")
Path(final_outputs_diagnostics_dir).mkdir(parents=True, exist_ok=True)
(final_outputs_diagnostics_dir / "cleanup_plan.json").write_text(json.dumps(cleanup_plan, indent=2, ensure_ascii=False), encoding="utf-8")
print("# cleanup_plan")
print(json.dumps(cleanup_plan, indent=2, ensure_ascii=False))
display_stage_summary(
    "16-1",
    "cleanup plan",
    inputs=[
        {"item": "merge_summary", "path": str(merge_summary_path)},
    ],
    outputs=[
        {"item": "cleanup_plan_merged", "path": str(merged_dir / "cleanup_plan.json")},
        {"item": "cleanup_plan_final_outputs", "path": str(final_outputs_diagnostics_dir / "cleanup_plan.json")},
    ],
    notes=[
        {"item": "delete_candidate_count", "value": int(cleanup_plan["delete_candidate_count"])},
    ],
)
```

```python
#16-2
from pathlib import Path
import json
import pandas as pd

ctx = load_ctx()
pipeline_root = Path(ctx['probe_root']) / ctx.get('pipeline_slug', 'da3_ngl_batch_v01')
merged_dir = Path(ctx.get('merged_dir', str(pipeline_root / 'merged')))
cleanup_plan_path = merged_dir / 'cleanup_plan.json'
assert cleanup_plan_path.exists(), cleanup_plan_path
cleanup_plan = json.loads(cleanup_plan_path.read_text(encoding='utf-8'))
rows=[]
for item in cleanup_plan.get('delete_candidates', []):
    rows.append({
        'action': 'delete',
        'path': item['path'],
        'kind': item.get('kind',''),
        'reason': item.get('reason',''),
        'size_bytes': item.get('size_bytes',0),
    })
for item in cleanup_plan.get('kept_groups', []):
    rows.append({
        'action': 'keep',
        'path': item['path'],
        'kind': item.get('kind','keep'),
        'reason': item.get('reason', item.get('label','keep_group')),
        'size_bytes': item.get('size_bytes',0),
    })
cleanup_csv = merged_dir / 'cleanup_inventory_review_v02.csv'
pd.DataFrame(rows).to_csv(cleanup_csv, index=False, encoding='utf-8')
print({'cleanup_inventory_review_csv': str(cleanup_csv), 'row_count': len(rows)})
display_stage_summary(
    "16-2",
    "cleanup inventory review csv",
    inputs=[
        {"item": "cleanup_plan", "path": str(cleanup_plan_path)},
    ],
    outputs=[
        {"item": "cleanup_inventory_review_v02", "path": str(cleanup_csv)},
    ],
    notes=[
        {"item": "row_count", "value": int(len(rows))},
    ],
)
```


# 17 Cleanup Apply

実行順: #17 は reviewed csv を確認後にだけ実行する

```python
#17-1
import json
import shutil
import pandas as pd

ctx = load_ctx()
probe_root = Path(ctx['probe_root'])
pipeline_root = probe_root / ctx.get('pipeline_slug', 'da3_ngl_batch_v01')
merged_dir = Path(ctx.get('merged_dir', str(pipeline_root / 'merged')))
cleanup_plan_path = merged_dir / 'cleanup_plan.json'
cleanup_csv_path = merged_dir / 'cleanup_inventory_review_v02.csv'
assert cleanup_plan_path.exists(), cleanup_plan_path
assert cleanup_csv_path.exists(), cleanup_csv_path

cleanup_plan = json.loads(cleanup_plan_path.read_text(encoding='utf-8'))
review_df = pd.read_csv(cleanup_csv_path)
review_df['action'] = review_df['action'].astype(str).str.strip().str.lower()
reviewed_paths = set(review_df['path'].astype(str))
other_dir = probe_root / 'other'
other_dir.mkdir(parents=True, exist_ok=True)

deleted = []
moved_to_other = []
kept = []

for row in review_df.itertuples(index=False):
    p = Path(row.path)
    action = str(row.action).strip().lower()
    if action == 'delete' and p.exists():
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        deleted.append(str(p))
    elif action in {'keep', 'other'}:
        kept.append(str(p))

for item in cleanup_plan.get('delete_candidates', []):
    src = Path(item['path'])
    if str(src) in reviewed_paths or not src.exists():
        continue
    dst = other_dir / src.name
    n = 1
    while dst.exists():
        dst = other_dir / f'{src.stem}_mv{n:02d}{src.suffix}'
        n += 1
    shutil.move(str(src), str(dst))
    moved_to_other.append({'src': str(src), 'dst': str(dst)})

cleanup_result = {
    'status': 'ok',
    'deleted': deleted,
    'moved_to_other': moved_to_other,
    'kept': kept,
}
(merged_dir / 'cleanup_apply_log.json').write_text(json.dumps(cleanup_result, indent=2, ensure_ascii=False), encoding='utf-8')
pd.DataFrame(
    [{'action': 'deleted', 'path': p} for p in deleted]
    + [{'action': 'moved_to_other', 'path': x['src'], 'dst': x['dst']} for x in moved_to_other]
    + [{'action': 'kept', 'path': p} for p in kept]
).to_csv(merged_dir / 'cleanup_apply_log.csv', index=False, encoding='utf-8')
print(json.dumps(cleanup_result, indent=2, ensure_ascii=False))
display_stage_summary(
    "17-1",
    "cleanup apply",
    inputs=[
        {"item": "cleanup_plan", "path": str(cleanup_plan_path)},
        {"item": "cleanup_inventory_review_v02", "path": str(cleanup_csv_path)},
    ],
    outputs=[
        {"item": "cleanup_apply_log_json", "path": str(merged_dir / 'cleanup_apply_log.json')},
        {"item": "cleanup_apply_log_csv", "path": str(merged_dir / 'cleanup_apply_log.csv')},
    ],
    notes=[
        {"item": "deleted_count", "value": int(len(deleted))},
        {"item": "moved_to_other_count", "value": int(len(moved_to_other))},
    ],
)
```
