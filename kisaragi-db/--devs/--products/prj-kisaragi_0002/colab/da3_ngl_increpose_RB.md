#No: #1-1
前: なし
次: #2-1

# 1 Runtime Bootstrap

この markdown cell は `#1-1` の runtime 導入を説明する。Drive mount、GPU 可用性確認、workspace の開始条件をそろえ、設定固定の `#2-1` へ渡す。

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

#No: #2-1
前: #1-1
次: #3-1

# 2 Config

この markdown cell は `#2-1` の config 固定を説明する。model、chunk、export、cleanup、target chunk をここで決め、入力選択の `#3-1` へ渡す。

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
    "BATCH_SIZE": 2,
    "CHUNK_SIZE": 18,
    "CHUNK_STEP": 6,
    "CONTEXT_SIZE": 12,
    "OUTPUT_SIZE": 6,
    "ADOPT_SIZE": 6,
    "TEST_TOTAL_FRAMES": 36,
    "PROCESS_RES": 504,
    "PROCESS_RES_METHOD": "upper_bound_resize",
    "DEVICE": "cuda",
    "EXPORT_FORMAT": "npz-glb-gs_ply-gs_video",
    "ALIGN_TO_INPUT_EXT_SCALE": True,
    "INFER_GS": True,
    "SHOW_CAMERAS": False,
    "CONF_THRESH_PERCENTILE": 40.0,
    "NUM_MAX_POINTS": 1000000,
    "SKIP_ALREADY_SUCCESS": True,
    "RESET_TARGET_OUTPUTS_BEFORE_RUN": True,
    "MAKE_DRIVE_BUNDLE": False,
    "DOWNLOAD_LOCAL_BUNDLE": False,
    "TARGET_CHUNK_MODE": "selected_chunk_ids_1based",
    "TARGET_CHUNK_IDS_1BASED": [6, 7],
    "MATCHING_CHUNK_IDS_1BASED": [6, 7],
    "MATCHING_CHUNK_A_NAME": "",
    "MATCHING_CHUNK_B_NAME": "",
    "MATCHING_CHUNK_A_INPUT_FRAMES_PATH": "",
    "MATCHING_CHUNK_A_PRED_EXTRINSICS_PATH": "",
    "MATCHING_CHUNK_B_INPUT_FRAMES_PATH": "",
    "MATCHING_CHUNK_B_PRED_EXTRINSICS_PATH": "",
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
    "POSE_PIPELINE_MODE": "sliding_window_incremental_seeded",
    "OVERLAP_SIZE": 12,
    "SEED_USE_PREV_POSE": True,
    "EVAL_ONLY_OUTPUT_RANGE": True,
    "OUTPUT_START_LOCAL_IDX": 12,
    "OUTPUT_END_LOCAL_IDX": 18,
}
assert CONFIG["CHUNK_SIZE"] == CONFIG["CONTEXT_SIZE"] + CONFIG["OUTPUT_SIZE"], CONFIG
assert CONFIG["CHUNK_STEP"] == CONFIG["OUTPUT_SIZE"] == CONFIG["ADOPT_SIZE"], CONFIG
assert CONFIG["OVERLAP_SIZE"] == CONFIG["CHUNK_SIZE"] - CONFIG["CHUNK_STEP"], CONFIG
assert CONFIG["OUTPUT_START_LOCAL_IDX"] == CONFIG["CONTEXT_SIZE"], CONFIG
assert CONFIG["OUTPUT_END_LOCAL_IDX"] == CONFIG["CHUNK_SIZE"], CONFIG

Path('/content/config_snapshot.json').write_text(json.dumps(CONFIG, indent=2, ensure_ascii=False), encoding='utf-8')
display(pd.DataFrame([{"item": k, "value": str(v)} for k, v in CONFIG.items()]))
```

#No: #3-1
前: #2-1
次: #4-1..#4-2

# 3 Input Select And Path Check

この markdown cell は `#3-1` の入力選択と path 検証を説明する。selected input、session root、result root、extract root を確定し、tree 初期化へ渡す。

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
    stage_10_dir = final_outputs_dir / "#10-1"
    stage_10_reaccess_dir = stage_10_dir / "re_access"
    stage_10_persist_only_dir = stage_10_dir / "persist_only"
    stage_11_dir = final_outputs_dir / "#11-1"
    stage_11_reaccess_dir = stage_11_dir / "re_access"
    stage_11_persist_only_dir = stage_11_dir / "persist_only"
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
        stage_10_reaccess_dir,
        stage_10_persist_only_dir,
        stage_11_reaccess_dir,
        stage_11_persist_only_dir,
    ]:
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
        "stage_10_dir": str(stage_10_dir),
        "stage_10_reaccess_dir": str(stage_10_reaccess_dir),
        "stage_10_persist_only_dir": str(stage_10_persist_only_dir),
        "stage_11_dir": str(stage_11_dir),
        "stage_11_reaccess_dir": str(stage_11_reaccess_dir),
        "stage_11_persist_only_dir": str(stage_11_persist_only_dir),
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

#No: #4-1
前: #3-1
次: #4-2

# 4 Tree Init

この markdown cell は `#4-1` の session context 初期化を説明する。selected input から runbook session context を組み立て、managed dir 作成前提をそろえる。

```python
#4-1
from pathlib import Path
import json
import shutil

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
legacy_source_pipeline_slug = "continuous_gs_v07_chunk18_step6_adopt6_incremental"
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
stage_10_dir = Path(paths["stage_10_dir"])
stage_10_reaccess_dir = Path(paths["stage_10_reaccess_dir"])
stage_10_persist_only_dir = Path(paths["stage_10_persist_only_dir"])
stage_11_dir = Path(paths["stage_11_dir"])
stage_11_reaccess_dir = Path(paths["stage_11_reaccess_dir"])
stage_11_persist_only_dir = Path(paths["stage_11_persist_only_dir"])

reset_before_run = bool(config.get("RESET_TARGET_OUTPUTS_BEFORE_RUN", True))
if reset_before_run and probe_root.exists():
    probe_root_resolved = probe_root.resolve()
    results_root_resolved = results_root.resolve()
    assert str(probe_root_resolved).startswith(str(results_root_resolved)), {
        "reason": "probe_root_outside_results_root",
        "probe_root": str(probe_root_resolved),
        "results_root": str(results_root_resolved),
    }
    shutil.rmtree(probe_root_resolved)

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
    stage_10_reaccess_dir,
    stage_10_persist_only_dir,
    stage_11_reaccess_dir,
    stage_11_persist_only_dir,
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
    "stage_10_dir": str(stage_10_dir),
    "stage_10_reaccess_dir": str(stage_10_reaccess_dir),
    "stage_10_persist_only_dir": str(stage_10_persist_only_dir),
    "stage_11_dir": str(stage_11_dir),
    "stage_11_reaccess_dir": str(stage_11_reaccess_dir),
    "stage_11_persist_only_dir": str(stage_11_persist_only_dir),
    "input_mode": "zip_only",
    "add_suffix": "",
    "reset_target_outputs_before_run": reset_before_run,
}
Path("/content/runbook_session_context.json").write_text(json.dumps(context_doc, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(context_doc, indent=2, ensure_ascii=False))
```

#No: #4-2
前: #4-1
次: #5-1

# 4 Tree Init

この markdown cell は `#4-2` の managed dir 宣言を説明する。runbook が扱う directory tree を固定し、install の `#5-1` へ渡す。

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

#No: #5-1
前: #4-2
次: #6-1

# 5 Install

この markdown cell は `#5-1` の install / import 準備を説明する。Depth-Anything-3 repo、runtime dependency、import path をそろえる。

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

#No: #6-1
前: #5-1
次: #6-2

# 6 Shared Helpers

この markdown cell は `#6-1` の共通 helper を説明する。context、JSON I/O、summary 表示、pose 比較に使う基礎 helper をここへ集約する。

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


def rotation_angle_deg_from_matrix(R: np.ndarray) -> float:
    R = np.asarray(R, dtype=np.float64)
    cos_theta = np.clip((np.trace(R) - 1.0) / 2.0, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_theta)))


def summarize_relative_transform(parent_T: np.ndarray | None, child_T: np.ndarray) -> dict:
    child_T = np.asarray(child_T, dtype=np.float64)
    if parent_T is None:
        return {
            "relative_scale": 1.0,
            "relative_translation_norm": 0.0,
            "relative_rotation_deg": 0.0,
        }

    parent_T = np.asarray(parent_T, dtype=np.float64)
    rel = np.linalg.inv(parent_T) @ child_T
    rot_scale = rel[:3, :3]
    det = float(np.linalg.det(rot_scale))
    if np.isfinite(det) and abs(det) > 1e-12:
        scale = float(np.sign(det) * (abs(det) ** (1.0 / 3.0)))
    else:
        scale = 1.0
    if abs(scale) > 1e-12:
        R = rot_scale / scale
    else:
        R = rot_scale
    return {
        "relative_scale": float(scale),
        "relative_translation_norm": float(np.linalg.norm(rel[:3, 3])),
        "relative_rotation_deg": rotation_angle_deg_from_matrix(R),
    }
```

#No: #6-2
前: #6-1
次: #7-1

# 6 Shared Helpers

この markdown cell は `#6-2` の補助 helper を説明する。後段の graph / merge review で使う軽量 helper を `#6` に寄せ、後段セルから重複定義を外しやすくする。

```python
#6-2
from pathlib import Path
import json
import numpy as np


def load_json(path):
    p = Path(path)
    assert p.exists(), p
    return json.loads(p.read_text(encoding="utf-8"))


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


def normalize_rows(arr: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    arr = np.asarray(arr, dtype=np.float64)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    norm = np.linalg.norm(arr, axis=1, keepdims=True)
    return arr / np.maximum(norm, eps)


def angle_deg(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = normalize_rows(a)
    b = normalize_rows(b)
    dot = np.sum(a * b, axis=1)
    dot = np.clip(dot, -1.0, 1.0)
    return np.degrees(np.arccos(dot))


def lens_direction_from_c2w(c2w: np.ndarray) -> np.ndarray:
    axis = -np.asarray(c2w[:3, 2], dtype=np.float64)
    return axis / max(float(np.linalg.norm(axis)), 1e-12)


def up_direction_from_c2w(c2w: np.ndarray) -> np.ndarray:
    axis = -np.asarray(c2w[:3, 1], dtype=np.float64)
    return axis / max(float(np.linalg.norm(axis)), 1e-12)


def estimate_pose_aware_similarity(
    local_c2w_rows: list[np.ndarray],
    global_c2w_rows: list[np.ndarray],
    estimate_scale: bool = True,
    scale_min: float = 0.8,
    scale_max: float = 1.3,
    center_rmse_max: float = 0.15,
    rotation_dir_max: float = 0.20,
) -> tuple[np.ndarray, dict]:
    assert len(local_c2w_rows) == len(global_c2w_rows) >= 2, {"local_len": len(local_c2w_rows), "global_len": len(global_c2w_rows)}

    src_dirs, dst_dirs, src_centers, dst_centers = [], [], [], []
    for local_c2w, global_c2w in zip(local_c2w_rows, global_c2w_rows):
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
    rotation_dir_residual = float(np.mean(np.linalg.norm((R @ src_dirs.T).T - dst_dirs, axis=1)))

    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = scale * R
    T[:3, 3] = t
    diag = {
        "scale": float(scale),
        "rotation_det": float(np.linalg.det(R)),
        "center_rmse": center_rmse,
        "rotation_dir_residual": rotation_dir_residual,
        "positive_similarity_ok": bool(scale > 0.0),
        "scale_in_range_ok": bool(scale_min <= scale <= scale_max),
        "center_rmse_ok": bool(center_rmse <= center_rmse_max),
        "rotation_dir_ok": bool(rotation_dir_residual <= rotation_dir_max),
    }
    diag["hard_fail"] = bool(
        (scale <= 0.0)
        or (scale < scale_min)
        or (scale > scale_max)
        or (center_rmse > center_rmse_max)
        or (rotation_dir_residual > rotation_dir_max)
    )
    return T.astype(np.float32), diag


def transform_c2w_list(c2w_rows: list[np.ndarray], T: np.ndarray) -> list[np.ndarray]:
    out = []
    for c2w in c2w_rows:
        M = np.asarray(c2w, dtype=np.float64).copy()
        M[:3, :3] = T[:3, :3] @ M[:3, :3]
        M[:3, 3] = T[:3, :3] @ M[:3, 3] + T[:3, 3]
        out.append(M.astype(np.float32))
    return out
```

#No: #7-1
前: #6-2
次: #7-2

# 7 Full Anchor Build

この markdown cell は `#7-1` の full anchor 入力準備を説明する。record-native input を整え、full anchor build の前提 artifact をそろえる。

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

#No: #7-2
前: #7-1
次: #7-3

# 7 Full Anchor Build

この markdown cell は `#7-2` の full anchor build 本体を説明する。camera matrix、camera center、orientation、anchor full table を生成する。

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
    "record_index": manifest_df["record_index"].astype(int),
    "sequence_index": manifest_df["sequence_index"].astype(int),
    "cam_cx": camera_centers[:, 0],
    "cam_cy": camera_centers[:, 1],
    "cam_cz": camera_centers[:, 2],
    "cx_world": camera_centers[:, 0],
    "cy_world": camera_centers[:, 1],
    "cz_world": camera_centers[:, 2],
})

camera_orientation_df = pd.DataFrame({
    "record_index": manifest_df["record_index"].astype(int),
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
camera_anchor_full_df["cx_world"] = camera_centers[:, 0]
camera_anchor_full_df["cy_world"] = camera_centers[:, 1]
camera_anchor_full_df["cz_world"] = camera_centers[:, 2]
camera_anchor_full_df["right_x"] = right_vecs[:, 0]
camera_anchor_full_df["right_y"] = right_vecs[:, 1]
camera_anchor_full_df["right_z"] = right_vecs[:, 2]
camera_anchor_full_df["up_x"] = up_vecs[:, 0]
camera_anchor_full_df["up_y"] = up_vecs[:, 1]
camera_anchor_full_df["up_z"] = up_vecs[:, 2]
camera_anchor_full_df["anchor_up_x"] = up_vecs[:, 0]
camera_anchor_full_df["anchor_up_y"] = up_vecs[:, 1]
camera_anchor_full_df["anchor_up_z"] = up_vecs[:, 2]
camera_anchor_full_df["lens_x"] = lens_vecs[:, 0]
camera_anchor_full_df["lens_y"] = lens_vecs[:, 1]
camera_anchor_full_df["lens_z"] = lens_vecs[:, 2]
camera_anchor_full_df["anchor_lens_x"] = lens_vecs[:, 0]
camera_anchor_full_df["anchor_lens_y"] = lens_vecs[:, 1]
camera_anchor_full_df["anchor_lens_z"] = lens_vecs[:, 2]
for r in range(4):
    for c in range(4):
        camera_anchor_full_df[f"w2c_{r}{c}"] = extrinsics_w2c[:, r, c]

camera_matrix_full_csv = anchor_dir / "camera_matrix_full_arc.csv"
camera_center_matrix_csv = anchor_dir / "camera_center_matrix_arc.csv"
camera_orientation_full_csv = anchor_dir / "camera_orientation_full_arc.csv"
camera_anchor_full_csv = anchor_dir / "camera_anchor_full_arc.csv"

pd.DataFrame(
    extrinsics_w2c.reshape(extrinsics_w2c.shape[0], -1),
    columns=[f"w2c_{r}{c}" for r in range(4) for c in range(4)]
).assign(
    record_index=manifest_df["record_index"].astype(int),
    sequence_index=manifest_df["sequence_index"].astype(int),
).to_csv(camera_matrix_full_csv, index=False)

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

#No: #7-3
前: #7-2
次: #7-4

# 7 Full Anchor Build

この markdown cell は `#7-3` の anchor pose diag を説明する。roll/pitch/yaw と差分診断を計算し、QC 前提を作る。

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

#No: #7-4
前: #7-3
次: #7-5

# 7 Full Anchor Build

この markdown cell は `#7-4` の anchor QC を説明する。姿勢外れ値を fail/warn で切り分け、以後の chunk build へ渡す。

```python
#7-4

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
WARN_ABS_ROLL_CENTERED_DEG = float(
    config.get(
        "ANCHOR_QC_WARN_ABS_ROLL_CENTERED_DEG",
        config.get("ANCHOR_QC_WARN_ABS_ROLL_DEG", 45.0),
    )
)
WARN_PITCH_MIN_DEG = float(config.get("ANCHOR_QC_WARN_PITCH_MIN_DEG", -89.0))
WARN_PITCH_MAX_DEG = float(config.get("ANCHOR_QC_WARN_PITCH_MAX_DEG", 89.0))

for col in [
    "delta_pos", "delta_lens_angle_deg", "delta_up_angle_deg",
    "delta2_pos", "delta2_rot", "roll_deg", "pitch_deg"
]:
    if col not in df.columns:
        df[col] = 0.0

if "roll_deg_raw" not in df.columns:
    df["roll_deg_raw"] = df["roll_deg"].astype(float)

if "roll_deg_centered" not in df.columns:
    roll_base = float(np.nanmedian(df["roll_deg_raw"].to_numpy(dtype=float))) if len(df) > 0 else 0.0
    df["roll_deg_centered"] = ((df["roll_deg_raw"] - roll_base + 180.0) % 360.0) - 180.0

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
df["warn_roll_band"] = df["roll_deg_centered"].abs() > WARN_ABS_ROLL_CENTERED_DEG
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
    "fail_count": int(len(fail_df)),
    "warn_count": int(len(warn_df)),
    "fail_rate": float(len(fail_df) / max(len(df), 1)),
    "warn_rate": float(len(warn_df) / max(len(df), 1)),
    "max_delta_pos": float(df["delta_pos"].abs().max()),
    "max_delta_lens_angle_deg": float(df["delta_lens_angle_deg"].abs().max()),
    "max_delta_up_angle_deg": float(df["delta_up_angle_deg"].abs().max()),
    "max_delta2_pos": float(df["delta2_pos"].abs().max()),
    "max_delta2_rot": float(df["delta2_rot"].abs().max()),
    "roll_deg_min": float(df["roll_deg"].min()),
    "roll_deg_max": float(df["roll_deg"].max()),
    "roll_deg_centered_min": float(df["roll_deg_centered"].min()),
    "roll_deg_centered_max": float(df["roll_deg_centered"].max()),
    "pitch_deg_min": float(df["pitch_deg"].min()),
    "pitch_deg_max": float(df["pitch_deg"].max()),
    "qc_csv": str(qc_csv),
    "fail_csv": str(fail_csv),
    "warn_csv": str(warn_csv),
}
print(summary)
display_stage_summary(
    "7-4",
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

#No: #7-5
前: #7-4
次: #8-1

# 7 Full Anchor Build

この markdown cell は `#7-5` の full anchor preview を説明する。anchor trajectory を可視化し、admin が基準経路を確認できるようにする。

```python
#7-5

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
    "7-5",
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

#No: #8-1
前: #7-5
次: #8-2

# 8 Chunk Run Preparation And Execution

この markdown cell は `#8-1` の record-native manifest rebuild を説明する。chunk 実行に渡す manifest の土台を作る。

```python
#8-1
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
    "8-1",
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

#No: #8-2
前: #8-1
次: #8-3

# 8 Chunk Run Preparation And Execution

この markdown cell は `#8-2` の record manifest refresh を説明する。sequence index と anchor 由来補助列を manifest へ補う。

```python
#8-2
from pathlib import Path
import json
import pandas as pd

ctx = load_ctx()
manifest_dir = Path(ctx['manifest_dir'])
managed_dirs = json.loads(Path('/content/runbook_managed_dirs.json').read_text(encoding='utf-8'))
record_dir = Path(managed_dirs['02_records'])
record_dir.mkdir(parents=True, exist_ok=True)

p = manifest_dir / 'da3_input_manifest.csv'
assert p.exists(), p
df = pd.read_csv(p)
ts_col = next((c for c in ['frame_timestamp_ns','timestamp_ns','timestamp'] if c in df.columns), None)
df = append_sequence_columns(df, ts_col or 'frame_timestamp_ns')
df['is_time_adjacent_valid'] = True
df.to_csv(p, index=False, encoding='utf-8')
df.to_csv(record_dir / 'record_manifest.csv', index=False, encoding='utf-8')
print({'updated_manifest': str(p), 'rows': len(df)})
display_stage_summary(
    "8-2",
    "record manifest refresh",
    inputs=[
        {"item": "da3_input_manifest", "path": str(p)},
    ],
    outputs=[
        {"item": "record_manifest", "path": str(record_dir / 'record_manifest.csv')},
        {"item": "da3_input_manifest_updated", "path": str(p)},
    ],
    notes=[
        {"item": "rows", "value": int(len(df))},
        {"item": "anchor_derived_join", "value": False},
    ],
)
```

#No: #8-3
前: #8-2
次: #8-4

# 8 Chunk Run Preparation And Execution

この markdown cell は `#8-3` の chunk/batch plan build を説明する。anchor full から `batch_execution_items.csv`、`chunk_input_manifest_arc.csv`、`chunk_index_all.csv`、および各 `chunk_XXXX.csv` を生成する。`batch_work_dir` は `chunk_runs/<batch_name>/` を指す batch scope とし、chunk 固有出力先は `chunk_out_dir = chunk_runs/<batch_name>/<chunk_name>/` で管理する。

```python
#8-3

from pathlib import Path
import pandas as pd
import numpy as np

ctx = load_ctx()

if "CFG" not in globals():
    CFG = {
        "CHUNK_SIZE": 18,
        "CHUNK_STEP": 6,
        "CONTEXT_SIZE": 12,
        "OUTPUT_SIZE": 6,
        "ADOPT_SIZE": 6,
        "BATCH_SIZE": 1,
    }

probe_root = Path(ctx["probe_root"])
persist_root = Path(ctx.get("persist_root", probe_root))
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")

chunk_manifest_dir = pipeline_root / "manifests"
chunk_manifest_dir.mkdir(parents=True, exist_ok=True)

chunk_runs_dir = pipeline_root / "chunk_runs"
chunk_runs_dir.mkdir(parents=True, exist_ok=True)

anchor_dir = persist_root / "01_anchor"
camera_anchor_full_path = anchor_dir / "camera_anchor_full_arc.csv"
assert camera_anchor_full_path.exists(), camera_anchor_full_path

anchor_df = pd.read_csv(camera_anchor_full_path).reset_index(drop=True)
assert "record_index" in anchor_df.columns, "record_index column is required"

CHUNK_SIZE = int(CFG["CHUNK_SIZE"])
CHUNK_STEP = int(CFG["CHUNK_STEP"])
CONTEXT_SIZE = int(CFG["CONTEXT_SIZE"])
OUTPUT_SIZE = int(CFG["OUTPUT_SIZE"])
ADOPT_SIZE = int(CFG["ADOPT_SIZE"])
BATCH_SIZE = int(CFG.get("BATCH_SIZE", 1))

assert CHUNK_SIZE == CONTEXT_SIZE + OUTPUT_SIZE, {
    "CHUNK_SIZE": CHUNK_SIZE,
    "CONTEXT_SIZE": CONTEXT_SIZE,
    "OUTPUT_SIZE": OUTPUT_SIZE,
}
assert OUTPUT_SIZE == 6
assert ADOPT_SIZE == 6
assert CHUNK_STEP == 6

n = len(anchor_df)
execution_rows = []
chunk_input_rows = []
chunk_index_rows = []

chunk_id = 0

for start_index in range(0, n - CHUNK_SIZE + 1, CHUNK_STEP):
    end_index = start_index + CHUNK_SIZE

    output_start_index = start_index + CONTEXT_SIZE
    output_end_index = end_index

    adopt_start_index = end_index - ADOPT_SIZE
    adopt_end_index = end_index

    chunk_name = f"chunk_{chunk_id:04d}"

    batch_index = chunk_id // BATCH_SIZE
    batch_name = f"batch_{batch_index:04d}"
    batch_work_dir = chunk_runs_dir / batch_name
    chunk_out_dir = batch_work_dir / chunk_name
    chunk_csv_path = chunk_manifest_dir / f"{chunk_name}.csv"

    execution_rows.append({
        "chunk_id": int(chunk_id),
        "chunk_name": chunk_name,
        "batch_index": int(batch_index),
        "batch_name": batch_name,
        "batch_work_dir": str(batch_work_dir),
        "chunk_out_dir": str(chunk_out_dir),
        "start_index": int(start_index),
        "end_index": int(end_index),
        "chunk_size": int(CHUNK_SIZE),
        "chunk_step": int(CHUNK_STEP),
        "context_size": int(CONTEXT_SIZE),
        "output_size": int(OUTPUT_SIZE),
        "adopt_size": int(ADOPT_SIZE),
        "output_start_index": int(output_start_index),
        "output_end_index": int(output_end_index),
        "adopt_start_index": int(adopt_start_index),
        "adopt_end_index": int(adopt_end_index),
    })

    for local_idx in range(CHUNK_SIZE):
        global_idx = start_index + local_idx
        row = anchor_df.iloc[global_idx].to_dict()

        row.update({
            "chunk_id": int(chunk_id),
            "chunk_name": chunk_name,
            "batch_index": int(batch_index),
            "batch_name": batch_name,
            "chunk_local_index": int(local_idx),
            "record_index": int(anchor_df.iloc[global_idx]["record_index"]),
            "is_context_range": bool(local_idx < CONTEXT_SIZE),
            "is_output_range": bool(CONTEXT_SIZE <= local_idx < CHUNK_SIZE),
            "is_adopt_range": bool(local_idx >= CHUNK_SIZE - ADOPT_SIZE),
        })
        chunk_input_rows.append(row)

    chunk_df = pd.DataFrame(chunk_input_rows[-CHUNK_SIZE:]).copy()
    chunk_df.to_csv(chunk_csv_path, index=False, encoding="utf-8")

    chunk_index_rows.append({
        "chunk_id": int(chunk_id),
        "chunk_name": chunk_name,
        "batch_index": int(batch_index),
        "batch_name": batch_name,
        "batch_work_dir": str(batch_work_dir),
        "chunk_out_dir": str(chunk_out_dir),
        "global_start": int(start_index),
        "global_end": int(end_index - 1),
        "frame_count": int(CHUNK_SIZE),
        "chunk_size": int(CHUNK_SIZE),
        "chunk_step": int(CHUNK_STEP),
        "context_size": int(CONTEXT_SIZE),
        "output_size": int(OUTPUT_SIZE),
        "adopt_size": int(ADOPT_SIZE),
        "adopt_local_start": int(CHUNK_SIZE - ADOPT_SIZE),
        "adopt_local_end": int(CHUNK_SIZE - 1),
        "output_start_index": int(output_start_index),
        "output_end_index": int(output_end_index - 1),
        "adopt_start_index": int(adopt_start_index),
        "adopt_end_index": int(adopt_end_index - 1),
        "chunk_csv": str(chunk_csv_path),
    })

    chunk_id += 1

batch_execution_items_df = pd.DataFrame(execution_rows)
batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
batch_execution_items_df.to_csv(batch_execution_items_path, index=False, encoding="utf-8")

chunk_input_manifest_df = pd.DataFrame(chunk_input_rows)
chunk_input_manifest_path = chunk_manifest_dir / "chunk_input_manifest_arc.csv"
chunk_input_manifest_df.to_csv(chunk_input_manifest_path, index=False, encoding="utf-8")

chunk_index_all_df = pd.DataFrame(chunk_index_rows)
chunk_index_all_path = chunk_manifest_dir / "chunk_index_all.csv"
chunk_index_all_df.to_csv(chunk_index_all_path, index=False, encoding="utf-8")

display(batch_execution_items_df.head(10))
display(chunk_input_manifest_df.head(20))
display(chunk_index_all_df.head(10))

print("chunks:", len(batch_execution_items_df))
print("chunk execution manifest:", batch_execution_items_path)
print("chunk input manifest:", chunk_input_manifest_path)
print("chunk index manifest:", chunk_index_all_path)
```

#No: #8-4
前: #8-3
次: #8-5

# 8 Chunk Run Preparation And Execution

この markdown cell は `#8-4` の batch chunk sequence precheck を説明する。`#8-3` が生成した `batch_execution_items.csv` と各 `chunk_XXXX.csv` を基準に、chunk 内 sequence の連続性と gap を診断する。

```python
#8-4

from pathlib import Path
import pandas as pd
import numpy as np

ctx = load_ctx()
probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"

batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
chunk_input_manifest_path = chunk_manifest_dir / "chunk_input_manifest_arc.csv"
chunk_index_all_path = chunk_manifest_dir / "chunk_index_all.csv"

if batch_execution_items_path.exists():
    chunk_index_df = pd.read_csv(batch_execution_items_path)
    source_label = "batch_execution_items"
elif chunk_index_all_path.exists():
    chunk_index_df = pd.read_csv(chunk_index_all_path)
    source_label = "chunk_index_all"
else:
    raise AssertionError({
        "missing_required_manifest": [
            str(batch_execution_items_path),
            str(chunk_index_all_path),
        ]
    })

assert not chunk_index_df.empty, {"source_label": source_label, "chunk_manifest_dir": str(chunk_manifest_dir)}
assert "chunk_name" in chunk_index_df.columns, chunk_index_df.columns.tolist()

input_manifest_df = pd.read_csv(chunk_input_manifest_path) if chunk_input_manifest_path.exists() else pd.DataFrame()

rows = []

for row in chunk_index_df.itertuples(index=False):
    chunk_name = row.chunk_name
    chunk_csv_value = getattr(row, "chunk_csv", "")
    chunk_csv = Path(str(chunk_csv_value)) if str(chunk_csv_value).strip() else (chunk_manifest_dir / f"{chunk_name}.csv")
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
        "record_index_min": int(chunk_df["record_index"].min()) if "record_index" in chunk_df.columns and len(chunk_df) else None,
        "record_index_max": int(chunk_df["record_index"].max()) if "record_index" in chunk_df.columns and len(chunk_df) else None,
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
    "source_label": source_label,
    "chunk_input_manifest_rows": int(len(input_manifest_df)),
})
display_stage_summary(
    "8-4",
    "batch chunk sequence precheck",
    inputs=[
        {"item": source_label, "path": str(batch_execution_items_path if source_label == "batch_execution_items" else chunk_index_all_path)},
        {"item": "chunk_input_manifest_arc", "path": str(chunk_input_manifest_path)},
    ],
    outputs=[
        {"item": "batch_chunk_sequence_precheck", "path": str(precheck_path)},
    ],
    notes=[
        {"item": "bad_chunk_count", "value": int(bad_chunk_count)},
        {"item": "chunk_count", "value": int(len(precheck_df))},
        {"item": "source_label", "value": source_label},
    ],
)
```

#No: #8-5
前: #8-4
次: #8-6

# 8 Chunk Run Preparation And Execution

この markdown cell は `#8-5` の execution target resolve を説明する。target chunk と batch plan の正本を解決し、欠けている時は `chunk_index_all.csv` と config から `chunk_index_target.csv` / `batch_plan.csv` を self-heal して後段実行対象を固定する。

```python
#8-5

ctx = load_ctx()
probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
config_snapshot = load_json("/content/config_snapshot.json") if Path("/content/config_snapshot.json").exists() else {}

chunk_manifest_dir.mkdir(parents=True, exist_ok=True)
chunk_runs_dir.mkdir(parents=True, exist_ok=True)

test_chunk_with_batch_path = chunk_manifest_dir / "test_only_target_chunk_with_batch.csv"
test_batch_plan_path = chunk_manifest_dir / "test_only_target_batch_plan.csv"

canonical_chunk_with_batch_path = chunk_manifest_dir / "target_chunk_with_batch.csv"
canonical_batch_plan_path = chunk_manifest_dir / "target_batch_plan.csv"

fallback_chunk_target_path = chunk_manifest_dir / "chunk_index_target.csv"
fallback_batch_plan_path = chunk_manifest_dir / "batch_plan.csv"
batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
chunk_index_all_path = chunk_manifest_dir / "chunk_index_all.csv"

def build_target_chunk_and_batch_plan():
    if batch_execution_items_path.exists():
        base_df = pd.read_csv(batch_execution_items_path)
    else:
        assert chunk_index_all_path.exists(), {
            "missing_required_manifest": [
                str(batch_execution_items_path),
                str(chunk_index_all_path),
            ]
        }
        base_df = pd.read_csv(chunk_index_all_path)

    assert not base_df.empty, {"reason": "base_chunk_manifest_empty", "chunk_manifest_dir": str(chunk_manifest_dir)}
    assert "chunk_id" in base_df.columns, base_df.columns.tolist()
    assert "chunk_name" in base_df.columns, base_df.columns.tolist()

    target_mode = str(config_snapshot.get("TARGET_CHUNK_MODE", "selected_chunk_ids_1based"))
    if target_mode == "full_set":
        target_chunks_df = base_df.copy().reset_index(drop=True)
    elif target_mode == "selected_chunk_ids_1based":
        valid_chunk_ids = set(base_df["chunk_id"].astype(int).tolist())
        selected_chunk_ids = sorted({int(x) - 1 for x in config_snapshot.get("TARGET_CHUNK_IDS_1BASED", []) if int(x) >= 1})
        selected_chunk_ids = [x for x in selected_chunk_ids if x in valid_chunk_ids]
        assert selected_chunk_ids, {
            "reason": "selected target chunk ids resolved empty",
            "selected_chunk_ids_1based": config_snapshot.get("TARGET_CHUNK_IDS_1BASED", []),
            "valid_chunk_ids_0based": sorted(valid_chunk_ids),
        }
        target_chunks_df = base_df.loc[base_df["chunk_id"].astype(int).isin(selected_chunk_ids)].copy()
        target_chunks_df = target_chunks_df.sort_values("chunk_id", kind="stable").reset_index(drop=True)
    elif bool(config_snapshot.get("USE_TARGET_CHUNK_WINDOW", False)):
        start_0 = max(0, int(config_snapshot.get("TARGET_CHUNK_WINDOW_START_1BASED", 1)) - 1)
        count = int(config_snapshot.get("TARGET_CHUNK_WINDOW_COUNT", 0))
        assert count > 0, {"reason": "target_chunk_window_count_must_be_positive", "count": count}
        end_0 = min(start_0 + count, len(base_df))
        target_chunks_df = base_df.iloc[start_0:end_0].copy().reset_index(drop=True)
    else:
        raise AssertionError({"reason": "unsupported target chunk mode", "target_mode": target_mode})

    if "target_local_chunk_index" not in target_chunks_df.columns:
        target_chunks_df["target_local_chunk_index"] = range(len(target_chunks_df))

    if "batch_index" not in target_chunks_df.columns:
        batch_size = int(config_snapshot.get("BATCH_SIZE", 1))
        target_chunks_df["batch_index"] = target_chunks_df["target_local_chunk_index"].astype(int) // batch_size

    if "batch_name" not in target_chunks_df.columns:
        target_chunks_df["batch_name"] = target_chunks_df["batch_index"].astype(int).map(lambda x: f"batch_{x:03d}")

    batch_plan_df = (
        target_chunks_df.groupby(["batch_index", "batch_name"], sort=True)
        .agg(
            chunk_from=("target_local_chunk_index", "min"),
            chunk_to=("target_local_chunk_index", "max"),
            chunk_count=("chunk_name", "size"),
        )
        .reset_index()
    )

    target_chunks_df.to_csv(fallback_chunk_target_path, index=False, encoding="utf-8")
    batch_plan_df.to_csv(fallback_batch_plan_path, index=False, encoding="utf-8")
    return target_chunks_df, batch_plan_df

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

if (not execution_chunk_path.exists()) or (not execution_batch_plan_path.exists()):
    build_target_chunk_and_batch_plan()

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
    "execution_chunk_names_all": execution_chunks_df[chunk_name_col].astype(str).tolist(),
    "execution_batch_names": execution_batch_plan_df["batch_name"].astype(str).tolist(),
    "execution_chunk_out": str(execution_chunk_out),
    "execution_batch_out": str(execution_batch_out),
    "self_heal_chunk_index_target_exists": bool(fallback_chunk_target_path.exists()),
    "self_heal_batch_plan_exists": bool(fallback_batch_plan_path.exists()),
}

save_json(chunk_manifest_dir / "execution_target_resolution_summary.json", summary)

print(json.dumps(summary, indent=2, ensure_ascii=False))
display(execution_chunks_df.head())
display(execution_batch_plan_df)
display_stage_summary(
    "8-5",
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

#No: #8-6
前: #8-5
次: #8-7

# 8 Chunk Run Preparation And Execution

この markdown cell は `#8-6` の run preflight を説明する。reset と実行前診断を行い、fatal/warning を切り分ける。

```python
#8-6

ctx = load_ctx()

probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"

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
        delete_targets.append(merged_dir / chunk_name)
    delete_targets.extend([
        final_outputs_dir,
        final_outputs_diagnostics_dir,
        final_outputs_manifests_dir,
        final_outputs_chunk_evidence_dir,
        final_outputs_merged_dir,
    ])

delete_status = []
for target in delete_targets:
    if target.exists():
        if target.is_dir():
            shutil.rmtree(target)
            delete_status.append({"path": str(target), "deleted": True, "kind": "dir"})
        else:
            target.unlink()
            delete_status.append({"path": str(target), "deleted": True, "kind": "file"})
    else:
        delete_status.append({"path": str(target), "deleted": False, "kind": "missing"})

for p in [chunk_runs_dir, merged_dir, final_outputs_dir, final_outputs_diagnostics_dir, final_outputs_manifests_dir, final_outputs_chunk_evidence_dir, final_outputs_merged_dir]:
    p.mkdir(parents=True, exist_ok=True)

record_manifest_path = Path(json.loads(Path("/content/runbook_managed_dirs.json").read_text(encoding="utf-8"))["02_records"]) / "record_manifest.csv"
sequence_precheck_path = chunk_manifest_dir / "batch_chunk_sequence_precheck.csv"

assert record_manifest_path.exists(), record_manifest_path
assert sequence_precheck_path.exists(), sequence_precheck_path

record_df = pd.read_csv(record_manifest_path)
sequence_df = pd.read_csv(sequence_precheck_path)

record_count = int(len(record_df))
target_chunk_count = int(len(target_chunks_df))
sequence_bad_chunk_count = int(((~sequence_df["is_monotonic"]) | (sequence_df["has_duplicate_sequence"]) | (sequence_df["bad_gap_count"] > 0)).sum()) if len(sequence_df) > 0 else 0

fatal_issues = []
warnings = []

if record_count == 0:
    fatal_issues.append({"type": "record_manifest_empty"})
if target_chunk_count == 0:
    fatal_issues.append({"type": "target_chunks_empty"})
if sequence_bad_chunk_count > 0:
    fatal_issues.append({"type": "sequence_precheck_failed", "bad_chunk_count": sequence_bad_chunk_count})

status = "ready" if len(fatal_issues) == 0 else "blocked"

preflight_summary = {
    "status": status,
    "record_rows": int(record_count),
    "target_chunk_count": int(target_chunk_count),
    "sequence_bad_chunk_count": int(sequence_bad_chunk_count),
    "batch_count": int(len(batch_names)),
    "fatal_issues": fatal_issues,
    "warnings": warnings,
    "delete_status": delete_status,
    "anchor_derived_checks_deferred_to_stage7": True,
}

preflight_path = final_outputs_diagnostics_dir / "run_preflight_summary.json"
preflight_path.write_text(json.dumps(preflight_summary, ensure_ascii=False, indent=2), encoding="utf-8")

print(preflight_summary)

display_stage_summary(
    "8-6",
    "run preflight",
    inputs=[
        {"item": "record_manifest", "path": str(record_manifest_path)},
        {"item": "sequence_precheck", "path": str(sequence_precheck_path)},
        {"item": "execution_target_chunks", "path": str(execution_chunks_path)},
        {"item": "execution_target_batch_plan", "path": str(execution_batch_plan_path)},
    ],
    outputs=[
        {"item": "run_preflight_summary", "path": str(preflight_path)},
    ],
    notes=[
        {"item": "status", "value": status},
        {"item": "record_rows", "value": int(record_count)},
        {"item": "target_chunk_count", "value": int(target_chunk_count)},
        {"item": "sequence_bad_chunk_count", "value": int(sequence_bad_chunk_count)},
        {"item": "anchor_derived_checks_deferred_to_stage7", "value": True},
    ],
)
```

#No: #8-7
前: #8-6
次: #8-8

# 8 Chunk Run Preparation And Execution

この markdown cell は `#8-7` の batch execution item generation を説明する。batch ごとの chunk 実行入力一覧を生成する。

```python
#8-7

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
        if not chunk_csv_path.exists():
            missing_files.append(str(chunk_csv_path))
        rows.append({
            "batch_index": int(batch_index),
            "batch_name": batch_name,
            "chunk_id": int(getattr(c_row, "chunk_id")) if "chunk_id" in execution_chunks_df.columns else None,
            "chunk_name": chunk_name,
            "target_local_chunk_index": int(getattr(c_row, "target_local_chunk_index")),
            "chunk_csv": str(chunk_csv_path),
            # sequence-anchor manifest は anchor 構築後に生成する
            "chunk_sequence_anchor_csv": "",
            "batch_work_dir": str(batch_work_dir),
        })

assert not missing_files, {"missing_chunk_csv_count": len(missing_files), "missing_chunk_csv_sample": missing_files[:10]}

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
    "sequence_anchor_manifest_deferred": True,
}
save_json(final_outputs_diagnostics_dir / "batch_input_generation_summary.json", summary)
save_json(
    Path("/content/runbook_batch_preflight_status.json"),
    {
        "status": "ok",
        "route": "da3_record_sequence_anchor_batch_plan_execution_prepose_build",
        "batch_execution_items_path": str(batch_execution_items_path),
        "batch_manifests_path": str(batch_manifests_path),
        "sequence_anchor_manifest_deferred": True,
    },
)

print(summary)
display_stage_summary(
    "8-7",
    "batch execution item generation",
    inputs=[
        {"item": "execution_target_chunks", "path": str(execution_chunks_path)},
        {"item": "execution_target_batch_plan", "path": str(execution_batch_plan_path)},
    ],
    outputs=[
        {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
        {"item": "batch_manifests", "path": str(batch_manifests_path)},
    ],
    notes=[
        {"item": "sequence_anchor_manifest_deferred", "value": True},
    ],
)
```

#No: #8-8
前: #8-7
次: #8-9

# 8 Chunk Run Preparation And Execution

この markdown cell は `#8-8` の runner wrapper 書き出しを説明する。chunk 実行 wrapper を 1 箇所で生成し、実行 contract を固定する。

```python
#8-8

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
        "export_format": str(args.export_format),
        "pred_extrinsics_saved": bool((out_dir / "pred_extrinsics.npy").exists()),
        "pred_intrinsics_saved": bool((out_dir / "pred_intrinsics.npy").exists()),
        "gs_ply_saved": bool((out_dir / "gs_ply" / "0000.ply").exists()),
        "gs_video_saved": bool((out_dir / "gs_video" / "0000_extend.mp4").exists()),
        "scene_glb_saved": bool((out_dir / "scene.glb").exists()),
    }
    (out_dir / "_SUCCESS.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''

wrapper_path.write_text(textwrap.dedent(wrapper_code).lstrip("\n"), encoding="utf-8")
print({"wrapper_path": str(wrapper_path), "size_bytes": wrapper_path.stat().st_size})
display_stage_summary(
    "8-8",
    "write chunk runner wrapper",
    outputs=[
        {"item": "wrapper_path", "path": str(wrapper_path)},
    ],
)
```

#No: #8-9
前: #8-8
次: #9-1

# 8 Chunk Run Preparation And Execution

この markdown cell は `#8-9` の batch 実行を説明する。target chunk を順次実行し、artifact は `chunk_runs/<batch_name>/<chunk_name>/` 配下へ chunk 単位で残す。`batch_execution_items.csv` の `batch_work_dir` が旧互換で chunk path を指していても、実行時に batch scope へ正規化して二重ネストを防ぐ。

```python
#8-9

from pathlib import Path
import json
import subprocess
import pandas as pd
import numpy as np

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
sort_cols = [c for c in ["chunk_id", "batch_index", "target_local_chunk_index", "chunk_name"] if c in items_df.columns]
if sort_cols:
    items_df = items_df.sort_values(sort_cols, kind="stable").reset_index(drop=True)

config_snapshot = load_json("/content/config_snapshot.json")
DRY_RUN = False
DEVICE = str(config_snapshot.get("DEVICE", "cuda")).strip().lower()
assert DEVICE in {"auto", "cuda", "cpu"}, {"DEVICE": DEVICE, "reason": "unsupported device"}
MODEL_ID = config_snapshot.get("MODEL_ID", "depth-anything/DA3NESTED-GIANT-LARGE-1.1")
PROCESS_RES = int(config_snapshot.get("PROCESS_RES", 504))
PROCESS_RES_METHOD = str(config_snapshot.get("PROCESS_RES_METHOD", "upper_bound_resize"))
EXPORT_FORMAT = str(config_snapshot.get("EXPORT_FORMAT", "mini_npz"))
ALIGN_TO_INPUT_EXT_SCALE = bool(config_snapshot.get("ALIGN_TO_INPUT_EXT_SCALE", True))
INFER_GS = bool(config_snapshot.get("INFER_GS", True))
SHOW_CAMERAS = bool(config_snapshot.get("SHOW_CAMERAS", False))
CONF_THRESH_PERCENTILE = float(config_snapshot.get("CONF_THRESH_PERCENTILE", 40.0))
NUM_MAX_POINTS = int(config_snapshot.get("NUM_MAX_POINTS", 1_000_000))
SKIP_ALREADY_SUCCESS = bool(config_snapshot.get("SKIP_ALREADY_SUCCESS", True))

CHUNK_SIZE = int(config_snapshot.get("CHUNK_SIZE", 18))
CHUNK_STEP = int(config_snapshot.get("CHUNK_STEP", 6))
CONTEXT_SIZE = int(config_snapshot.get("CONTEXT_SIZE", CHUNK_SIZE - CHUNK_STEP))
OUTPUT_SIZE = int(config_snapshot.get("OUTPUT_SIZE", CHUNK_STEP))
OVERLAP_SIZE = int(config_snapshot.get("OVERLAP_SIZE", max(0, CHUNK_SIZE - CHUNK_STEP)))
ADOPT_SIZE = int(config_snapshot.get("ADOPT_SIZE", CHUNK_STEP))
POSE_PIPELINE_MODE = str(config_snapshot.get("POSE_PIPELINE_MODE", "sliding_window_incremental_seeded"))

assert CHUNK_SIZE == CONTEXT_SIZE + OUTPUT_SIZE, {
    "CHUNK_SIZE": CHUNK_SIZE,
    "CONTEXT_SIZE": CONTEXT_SIZE,
    "OUTPUT_SIZE": OUTPUT_SIZE,
}
assert OUTPUT_SIZE == CHUNK_STEP == ADOPT_SIZE, {
    "OUTPUT_SIZE": OUTPUT_SIZE,
    "CHUNK_STEP": CHUNK_STEP,
    "ADOPT_SIZE": ADOPT_SIZE,
}

if INFER_GS and "gs_ply" not in EXPORT_FORMAT:
    EXPORT_FORMAT = "npz-glb-gs_ply-gs_video"

required_cols = ["batch_name", "chunk_name", "chunk_csv", "batch_work_dir"]
missing_cols = [c for c in required_cols if c not in items_df.columns]
assert not missing_cols, {"missing_columns": missing_cols, "available": items_df.columns.tolist()}

MAT_COLS = [f"w2c_{r}{c}" for r in range(4) for c in range(4)]

def ensure_pose4x4_batch(arr: np.ndarray) -> np.ndarray:
    arr = np.asarray(arr, dtype=np.float32)
    if arr.ndim == 2:
        arr = arr[None, ...]
    if arr.shape[-2:] == (4, 4):
        return arr
    if arr.shape[-2:] == (3, 4):
        out = np.repeat(np.eye(4, dtype=np.float32)[None, ...], arr.shape[0], axis=0)
        out[:, :3, :] = arr
        return out
    raise AssertionError({"reason": "unexpected_pose_shape", "shape": tuple(arr.shape)})

def apply_incremental_seed_to_chunk_df(chunk_df: pd.DataFrame, accepted_pose_by_record_index: dict[int, np.ndarray]):
    run_df = chunk_df.copy().reset_index(drop=True)

    if "chunk_local_index" not in run_df.columns:
        run_df["chunk_local_index"] = np.arange(len(run_df), dtype=np.int64)
    if "is_context_range" not in run_df.columns:
        run_df["is_context_range"] = run_df["chunk_local_index"] < CONTEXT_SIZE
    if "is_output_range" not in run_df.columns:
        run_df["is_output_range"] = run_df["chunk_local_index"] >= CONTEXT_SIZE
    if "is_adopted_region" not in run_df.columns:
        run_df["is_adopted_region"] = run_df["chunk_local_index"] >= (len(run_df) - ADOPT_SIZE)

    for col in MAT_COLS:
        if col not in run_df.columns:
            run_df[col] = np.nan

    run_df["seed_pose_applied"] = False

    seeded_local_indices = []
    for i, row in run_df.iterrows():
        local_idx = int(row["chunk_local_index"])
        if local_idx >= CONTEXT_SIZE:
            continue
        rec = int(row["record_index"])
        pose = accepted_pose_by_record_index.get(rec)
        if pose is None:
            continue
        pose = ensure_pose4x4_batch(pose)[0]
        for r in range(4):
            for c in range(4):
                run_df.at[i, f"w2c_{r}{c}"] = float(pose[r, c])
        run_df.at[i, "seed_pose_applied"] = True
        seeded_local_indices.append(local_idx)

    return run_df, seeded_local_indices

def update_accepted_pose_map_from_chunk(run_df: pd.DataFrame, pred_ext: np.ndarray, accepted_pose_by_record_index: dict[int, np.ndarray]):
    pred_ext = ensure_pose4x4_batch(pred_ext)
    assert len(run_df) == len(pred_ext), {
        "reason": "run_df_pred_len_mismatch",
        "run_df_len": len(run_df),
        "pred_len": len(pred_ext),
    }
    adopt_mask = run_df["is_adopted_region"].astype(bool).to_numpy()
    adopt_rows = run_df.loc[adopt_mask].copy().reset_index(drop=True)
    adopt_pose = pred_ext[adopt_mask]
    for row, M in zip(adopt_rows.itertuples(index=False), adopt_pose):
        accepted_pose_by_record_index[int(row.record_index)] = np.asarray(M, dtype=np.float32)
    return accepted_pose_by_record_index

seed_pose_by_record_index: dict[int, np.ndarray] = {}
rows = []
seed_trace_rows = []
all_batch_summary = []

for _, item_row in items_df.iterrows():
    batch_name = str(item_row["batch_name"])
    chunk_name = str(item_row["chunk_name"])
    chunk_csv = Path(str(item_row["chunk_csv"]))
    raw_batch_work_dir = Path(str(item_row["batch_work_dir"]))
    batch_work_dir = raw_batch_work_dir
    if batch_work_dir.name == chunk_name or batch_work_dir.name.startswith(f"{chunk_name}_"):
        batch_work_dir = batch_work_dir.parent

    if "chunk_out_dir" in item_row.index and pd.notna(item_row["chunk_out_dir"]) and str(item_row["chunk_out_dir"]).strip():
        out_dir = Path(str(item_row["chunk_out_dir"]).strip())
    else:
        out_dir = batch_work_dir / chunk_name
    runtime_dir = out_dir / "_runtime"

    batch_work_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    stdout_txt = batch_work_dir / "stdout.txt"
    stderr_txt = batch_work_dir / "stderr.txt"
    runtime_chunk_csv = runtime_dir / "chunk_input_seeded.csv"

    chunk_df = pd.read_csv(chunk_csv)
    assert len(chunk_df) == CHUNK_SIZE, {
        "chunk_name": chunk_name,
        "frame_count": int(len(chunk_df)),
        "expected_chunk_size": int(CHUNK_SIZE),
    }

    run_df, seeded_local_indices = apply_incremental_seed_to_chunk_df(chunk_df, seed_pose_by_record_index)
    run_df.to_csv(runtime_chunk_csv, index=False, encoding="utf-8")

    pred_path = out_dir / "pred_extrinsics.npy"
    if SKIP_ALREADY_SUCCESS and pred_path.exists():
        rc = 0
        out = ""
        err = ""
        outputs_exist = True
        pred_ext = ensure_pose4x4_batch(np.load(pred_path))
        seed_pose_by_record_index = update_accepted_pose_map_from_chunk(run_df, pred_ext, seed_pose_by_record_index)
        status = "skipped_existing"
    else:
        cmd = [
            "python3", str(wrapper_path),
            "--chunk-csv", str(runtime_chunk_csv),
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
            rc = 0
            out = ""
            err = ""
        else:
            proc = subprocess.run(cmd, text=True, capture_output=True)
            rc = int(proc.returncode)
            out = proc.stdout
            err = proc.stderr
            stdout_txt.write_text(out or "", encoding="utf-8")
            stderr_txt.write_text(err or "", encoding="utf-8")

        outputs_exist = pred_path.exists()
        status = "ok" if (rc == 0 and outputs_exist) else "failed"
        if rc == 0 and outputs_exist:
            pred_ext = ensure_pose4x4_batch(np.load(pred_path))
            seed_pose_by_record_index = update_accepted_pose_map_from_chunk(run_df, pred_ext, seed_pose_by_record_index)

    rows.append({
        "batch_name": batch_name,
        "chunk_name": chunk_name,
        "chunk_id": int(item_row["chunk_id"]) if "chunk_id" in item_row.index else None,
        "status": status,
        "returncode": int(rc),
        "outputs_exist": bool(outputs_exist),
        "out_dir": str(out_dir),
        "chunk_csv": str(chunk_csv),
        "runtime_chunk_csv": str(runtime_chunk_csv),
        "record_count": int(len(run_df)),
        "context_size": int(CONTEXT_SIZE),
        "output_size": int(OUTPUT_SIZE),
        "adopt_size": int(ADOPT_SIZE),
        "seeded_overlap_count": int(len(seeded_local_indices)),
        "seeded_overlap_local_indices": json.dumps(seeded_local_indices, ensure_ascii=False),
        "batch_work_dir": str(batch_work_dir),
    })
    seed_trace_rows.append({
        "chunk_name": chunk_name,
        "record_count": int(len(run_df)),
        "context_size": int(CONTEXT_SIZE),
        "output_size": int(OUTPUT_SIZE),
        "chunk_step": int(CHUNK_STEP),
        "overlap_size": int(OVERLAP_SIZE),
        "adopt_size": int(ADOPT_SIZE),
        "seeded_overlap_count": int(len(seeded_local_indices)),
        "seeded_overlap_local_indices": json.dumps(seeded_local_indices, ensure_ascii=False),
        "pose_pipeline_mode": POSE_PIPELINE_MODE,
    })
    all_batch_summary.append({
        "batch_name": batch_name,
        "chunk_name": chunk_name,
        "status": status,
        "out_dir": str(out_dir),
        "runtime_chunk_csv": str(runtime_chunk_csv),
    })

run_df_summary = pd.DataFrame(rows)
run_status_path = final_outputs_diagnostics_dir / "batch_run_status_arc.csv"
run_df_summary.to_csv(run_status_path, index=False, encoding="utf-8")

seed_trace_path = final_outputs_diagnostics_dir / "incremental_seed_trace_arc.csv"
pd.DataFrame(seed_trace_rows).to_csv(seed_trace_path, index=False, encoding="utf-8")

all_batch_summary_path = merged_dir = pipeline_root / "merged"
merged_dir.mkdir(parents=True, exist_ok=True)
all_batch_summary_json = merged_dir / "all_batch_summary_arc.json"
save_json(all_batch_summary_json, {
    "route": "sliding_window_incremental_seeded",
    "chunk_count": int(len(run_df_summary)),
    "failed_count": int((run_df_summary["status"] == "failed").sum()) if len(run_df_summary) else 0,
    "records": all_batch_summary,
})

print(run_df_summary)
display(run_df_summary)
display_stage_summary(
    "8-9",
    "chunk execution (sequential seeded sliding-window)",
    inputs=[
        {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
        {"item": "wrapper", "path": str(wrapper_path)},
    ],
    outputs=[
        {"item": "batch_run_status", "path": str(run_status_path)},
        {"item": "incremental_seed_trace", "path": str(seed_trace_path)},
        {"item": "all_batch_summary", "path": str(all_batch_summary_json)},
    ],
    notes=[
        {"item": "chunk_count", "value": int(len(run_df_summary))},
        {"item": "failed_count", "value": int((run_df_summary["status"] == "failed").sum()) if len(run_df_summary) else 0},
        {"item": "pose_pipeline_mode", "value": POSE_PIPELINE_MODE},
        {"item": "chunk_size", "value": int(CHUNK_SIZE)},
        {"item": "context_size", "value": int(CONTEXT_SIZE)},
        {"item": "output_size", "value": int(OUTPUT_SIZE)},
        {"item": "chunk_step", "value": int(CHUNK_STEP)},
        {"item": "adopt_size", "value": int(ADOPT_SIZE)},
    ],
)
```

#No: #9-1
前: #8-9
次: #10-1

# 9 Chunk Alignment Coefficient Derivation

この markdown cell は `#9-1` の overlap pose matching を説明する。2 chunk の overlap pose を同一座標系へ重ね、relative transform と残差を出す。

```python
#9-1
from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go

ctx = load_ctx()
config = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8"))

probe_root = Path(ctx["probe_root"])
persist_root = Path(ctx.get("persist_root", probe_root))
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
anchor_dir = persist_root / "01_anchor"
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
final_outputs_chunk_evidence_dir = Path(ctx["final_outputs_chunk_evidence_dir"])
final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])

matching_dir = anchor_dir / "07matching"
matching_dir.mkdir(parents=True, exist_ok=True)

LOCAL_EXTRINSIC_MODE = "c2w"
LOCAL_CAMERA_BASIS = np.eye(4, dtype=np.float32)
LOCAL_CAMERA_BASIS[:3, :3] = np.array([
    [0.0, 1.0, 0.0],
    [0.0, 0.0, -1.0],
    [1.0, 0.0, 0.0],
], dtype=np.float32)

TRANSFORM_SCALE_MIN = 0.8
TRANSFORM_SCALE_MAX = 1.3
TRANSFORM_CENTER_RMSE_MAX = 0.15
TRANSFORM_ROT_DIR_MAX = 0.20


def resolve_matching_chunk_names() -> tuple[str | None, str | None]:
    explicit_a = str(config.get("MATCHING_CHUNK_A_NAME", "")).strip()
    explicit_b = str(config.get("MATCHING_CHUNK_B_NAME", "")).strip()
    if explicit_a and explicit_b:
        return explicit_a, explicit_b

    chunk_index_path = chunk_manifest_dir / "chunk_index_all.csv"
    if not chunk_index_path.exists():
        return None, None
    chunk_index_df = pd.read_csv(chunk_index_path)
    valid_ids = set(chunk_index_df["chunk_id"].astype(int).tolist())
    ids_1based = config.get("MATCHING_CHUNK_IDS_1BASED") or config.get("TARGET_CHUNK_IDS_1BASED") or []
    selected_ids = [int(x) - 1 for x in ids_1based if int(x) >= 1]
    selected_ids = [x for x in selected_ids if x in valid_ids]
    if len(selected_ids) < 2:
        return None, None
    selected_df = chunk_index_df.loc[chunk_index_df["chunk_id"].astype(int).isin(selected_ids)].copy()
    selected_df = selected_df.sort_values("chunk_id", kind="stable").reset_index(drop=True)
    return str(selected_df.iloc[0]["chunk_name"]), str(selected_df.iloc[1]["chunk_name"])


def resolve_chunk_artifact(explicit_path: str, chunk_name: str | None, filename: str) -> Path | None:
    if explicit_path:
        p = Path(explicit_path)
        assert p.exists(), {"missing_explicit_path": str(p), "chunk_name": chunk_name, "filename": filename}
        return p
    if not chunk_name:
        return None

    candidates = [
        final_outputs_chunk_evidence_dir / chunk_name / filename,
        chunk_runs_dir / chunk_name / filename,
    ]
    candidates += [p for p in chunk_runs_dir.glob(f"batch_*/{chunk_name}/{filename}")]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None

def c2w_list_from_extrinsics(pred_extrinsics: np.ndarray) -> list[np.ndarray]:
    mats = []
    for ext in to_4x4_batch(pred_extrinsics):
        raw = ext.astype(np.float32)
        if LOCAL_EXTRINSIC_MODE == "c2w":
            c2w = raw
        elif LOCAL_EXTRINSIC_MODE == "w2c":
            c2w = np.linalg.inv(raw).astype(np.float32)
        else:
            raise AssertionError({"unsupported_extrinsic_mode": LOCAL_EXTRINSIC_MODE})
        mats.append((c2w @ LOCAL_CAMERA_BASIS).astype(np.float32))
    return mats

def pose_rows_to_frame_df(chunk_name: str, frames_df: pd.DataFrame, c2w_rows: list[np.ndarray], variant: str, overlap_records: set[int]) -> pd.DataFrame:
    rows = []
    for frame_row, c2w in zip(frames_df.itertuples(index=False), c2w_rows):
        record_index = int(frame_row.record_index)
        center = np.asarray(c2w[:3, 3], dtype=np.float64)
        lens = lens_direction_from_c2w(c2w)
        up = up_direction_from_c2w(c2w)
        rows.append({
            "chunk_name": chunk_name,
            "variant": variant,
            "record_index": record_index,
            "chunk_local_index": int(getattr(frame_row, "chunk_local_index", len(rows))),
            "is_overlap": bool(record_index in overlap_records),
            "cx": float(center[0]),
            "cy": float(center[1]),
            "cz": float(center[2]),
            "fx": float(lens[0]),
            "fy": float(lens[1]),
            "fz": float(lens[2]),
            "ux": float(up[0]),
            "uy": float(up[1]),
            "uz": float(up[2]),
        })
    return pd.DataFrame(rows)


def plot_pose_match(a_df: pd.DataFrame, b_df: pd.DataFrame, b_aligned_df: pd.DataFrame, out_path: Path):
    fig = plt.figure(figsize=(14, 6))
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    ax2 = fig.add_subplot(1, 2, 2, projection="3d")

    def draw(ax, lhs: pd.DataFrame, rhs: pd.DataFrame, title: str):
        ax.plot(lhs["cx"], lhs["cy"], lhs["cz"], color="tab:blue", label=f"{lhs['chunk_name'].iloc[0]} raw")
        ax.plot(rhs["cx"], rhs["cy"], rhs["cz"], color="tab:orange", label=f"{rhs['chunk_name'].iloc[0]} {'aligned' if 'aligned' in rhs['variant'].iloc[0] else 'raw'}")
        lhs_overlap = lhs[lhs["is_overlap"]]
        rhs_overlap = rhs[rhs["is_overlap"]]
        if len(lhs_overlap):
            ax.scatter(lhs_overlap["cx"], lhs_overlap["cy"], lhs_overlap["cz"], color="tab:cyan", s=24)
        if len(rhs_overlap):
            ax.scatter(rhs_overlap["cx"], rhs_overlap["cy"], rhs_overlap["cz"], color="tab:red", s=24)
        ax.set_title(title)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("z")
        ax.legend(loc="best")

    draw(ax1, a_df, b_df, "pre-align overlap trajectories")
    draw(ax2, a_df, b_aligned_df, "post-align overlap trajectories")
    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_pose_match_html(a_df: pd.DataFrame, b_df: pd.DataFrame, b_aligned_df: pd.DataFrame, out_path: Path):
    fig = go.Figure()

    def add_trace(df: pd.DataFrame, name: str, color: str, show_overlap: bool):
        fig.add_trace(
            go.Scatter3d(
                x=df["cx"],
                y=df["cy"],
                z=df["cz"],
                mode="lines+markers",
                name=name,
                marker={"size": 3, "color": color},
                line={"width": 5, "color": color},
            )
        )
        if show_overlap:
            overlap_df = df[df["is_overlap"]]
            if len(overlap_df):
                fig.add_trace(
                    go.Scatter3d(
                        x=overlap_df["cx"],
                        y=overlap_df["cy"],
                        z=overlap_df["cz"],
                        mode="markers",
                        name=f"{name} overlap",
                        marker={"size": 5, "color": color, "symbol": "diamond"},
                    )
                )

    add_trace(a_df, f"{a_df['chunk_name'].iloc[0]} raw", "#1f77b4", True)
    add_trace(b_df, f"{b_df['chunk_name'].iloc[0]} raw", "#ff7f0e", True)
    add_trace(b_aligned_df, f"{b_aligned_df['chunk_name'].iloc[0]} aligned", "#2ca02c", True)
    fig.update_layout(
        title="overlap trajectory matching",
        scene={
            "xaxis_title": "x",
            "yaxis_title": "y",
            "zaxis_title": "z",
            "aspectmode": "data",
        },
        legend={"orientation": "h"},
        margin={"l": 0, "r": 0, "t": 48, "b": 0},
    )
    fig.write_html(str(out_path), include_plotlyjs="cdn")


chunk_a_name, chunk_b_name = resolve_matching_chunk_names()
chunk_a_frames_path = resolve_chunk_artifact(str(config.get("MATCHING_CHUNK_A_INPUT_FRAMES_PATH", "")).strip(), chunk_a_name, "chunk_input_frames.csv")
chunk_a_pred_path = resolve_chunk_artifact(str(config.get("MATCHING_CHUNK_A_PRED_EXTRINSICS_PATH", "")).strip(), chunk_a_name, "pred_extrinsics.npy")
chunk_b_frames_path = resolve_chunk_artifact(str(config.get("MATCHING_CHUNK_B_INPUT_FRAMES_PATH", "")).strip(), chunk_b_name, "chunk_input_frames.csv")
chunk_b_pred_path = resolve_chunk_artifact(str(config.get("MATCHING_CHUNK_B_PRED_EXTRINSICS_PATH", "")).strip(), chunk_b_name, "pred_extrinsics.npy")

if not all([chunk_a_name, chunk_b_name, chunk_a_frames_path, chunk_a_pred_path, chunk_b_frames_path, chunk_b_pred_path]):
    summary = {
        "status": "skipped",
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-overlap-pose-matching",
        "reason": "matching_inputs_missing",
        "chunk_a_name": chunk_a_name,
        "chunk_b_name": chunk_b_name,
        "chunk_a_frames_path": str(chunk_a_frames_path) if chunk_a_frames_path else None,
        "chunk_a_pred_extrinsics_path": str(chunk_a_pred_path) if chunk_a_pred_path else None,
        "chunk_b_frames_path": str(chunk_b_frames_path) if chunk_b_frames_path else None,
        "chunk_b_pred_extrinsics_path": str(chunk_b_pred_path) if chunk_b_pred_path else None,
        "hint": "set MATCHING_CHUNK_A/B_* explicit paths or rerun after chunk artifacts exist",
    }
    summary_json = matching_dir / "chunk_overlap_pose_matching_summary.json"
    save_json(summary_json, summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    display_stage_summary(
    "9-1",
    "overlap pose matching",
        outputs=[
            {"item": "matching_summary", "path": str(summary_json)},
        ],
        notes=[
            {"item": "status", "value": summary["status"]},
            {"item": "reason", "value": summary["reason"]},
        ],
    )
else:
    chunk_a_frames_df = pd.read_csv(chunk_a_frames_path).sort_values("chunk_local_index", kind="stable").reset_index(drop=True)
    chunk_b_frames_df = pd.read_csv(chunk_b_frames_path).sort_values("chunk_local_index", kind="stable").reset_index(drop=True)
    chunk_a_pred = np.load(chunk_a_pred_path)
    chunk_b_pred = np.load(chunk_b_pred_path)

    assert chunk_a_pred.shape[0] == len(chunk_a_frames_df), {"chunk_name": chunk_a_name, "pred_len": int(chunk_a_pred.shape[0]), "frame_len": int(len(chunk_a_frames_df))}
    assert chunk_b_pred.shape[0] == len(chunk_b_frames_df), {"chunk_name": chunk_b_name, "pred_len": int(chunk_b_pred.shape[0]), "frame_len": int(len(chunk_b_frames_df))}

    overlap_records = sorted(set(chunk_a_frames_df["record_index"].astype(int)) & set(chunk_b_frames_df["record_index"].astype(int)))
    assert len(overlap_records) >= 2, {"chunk_a_name": chunk_a_name, "chunk_b_name": chunk_b_name, "overlap_record_count": len(overlap_records)}
    overlap_record_set = set(overlap_records)

    chunk_a_map = {int(row.record_index): idx for idx, row in enumerate(chunk_a_frames_df.itertuples(index=False))}
    chunk_b_map = {int(row.record_index): idx for idx, row in enumerate(chunk_b_frames_df.itertuples(index=False))}
    overlap_a_indices = [chunk_a_map[r] for r in overlap_records]
    overlap_b_indices = [chunk_b_map[r] for r in overlap_records]

    chunk_a_c2w_all = c2w_list_from_extrinsics(chunk_a_pred)
    chunk_b_c2w_all = c2w_list_from_extrinsics(chunk_b_pred)
    chunk_a_c2w_overlap = [chunk_a_c2w_all[i] for i in overlap_a_indices]
    chunk_b_c2w_overlap = [chunk_b_c2w_all[i] for i in overlap_b_indices]

    T_b_to_a, align_diag = estimate_pose_aware_similarity(
        chunk_b_c2w_overlap,
        chunk_a_c2w_overlap,
        estimate_scale=True,
        scale_min=TRANSFORM_SCALE_MIN,
        scale_max=TRANSFORM_SCALE_MAX,
        center_rmse_max=TRANSFORM_CENTER_RMSE_MAX,
        rotation_dir_max=TRANSFORM_ROT_DIR_MAX,
    )
    chunk_b_c2w_aligned_all = transform_c2w_list(chunk_b_c2w_all, T_b_to_a)
    chunk_b_c2w_aligned_overlap = [chunk_b_c2w_aligned_all[i] for i in overlap_b_indices]

    centers_a = np.asarray([c[:3, 3] for c in chunk_a_c2w_overlap], dtype=np.float64)
    centers_b = np.asarray([c[:3, 3] for c in chunk_b_c2w_overlap], dtype=np.float64)
    centers_b_aligned = np.asarray([c[:3, 3] for c in chunk_b_c2w_aligned_overlap], dtype=np.float64)
    lens_a = np.asarray([lens_direction_from_c2w(c) for c in chunk_a_c2w_overlap], dtype=np.float64)
    lens_b = np.asarray([lens_direction_from_c2w(c) for c in chunk_b_c2w_overlap], dtype=np.float64)
    lens_b_aligned = np.asarray([lens_direction_from_c2w(c) for c in chunk_b_c2w_aligned_overlap], dtype=np.float64)
    up_a = np.asarray([up_direction_from_c2w(c) for c in chunk_a_c2w_overlap], dtype=np.float64)
    up_b = np.asarray([up_direction_from_c2w(c) for c in chunk_b_c2w_overlap], dtype=np.float64)
    up_b_aligned = np.asarray([up_direction_from_c2w(c) for c in chunk_b_c2w_aligned_overlap], dtype=np.float64)

    center_error_pre = np.linalg.norm(centers_b - centers_a, axis=1)
    center_error_post = np.linalg.norm(centers_b_aligned - centers_a, axis=1)
    lens_error_pre = angle_deg(lens_b, lens_a)
    lens_error_post = angle_deg(lens_b_aligned, lens_a)
    up_error_pre = angle_deg(up_b, up_a)
    up_error_post = angle_deg(up_b_aligned, up_a)

    pair_rows = []
    for record_index, a_idx, b_idx, ce_pre, ce_post, le_pre, le_post, ue_pre, ue_post in zip(
        overlap_records,
        overlap_a_indices,
        overlap_b_indices,
        center_error_pre,
        center_error_post,
        lens_error_pre,
        lens_error_post,
        up_error_pre,
        up_error_post,
    ):
        pair_rows.append({
            "chunk_a_name": chunk_a_name,
            "chunk_b_name": chunk_b_name,
            "record_index": int(record_index),
            "chunk_a_local_index": int(a_idx),
            "chunk_b_local_index": int(b_idx),
            "center_error_pre": float(ce_pre),
            "center_error_post": float(ce_post),
            "lens_error_deg_pre": float(le_pre),
            "lens_error_deg_post": float(le_post),
            "up_error_deg_pre": float(ue_pre),
            "up_error_deg_post": float(ue_post),
        })

    pair_df = pd.DataFrame(pair_rows)
    points_df = pd.concat([
        pose_rows_to_frame_df(chunk_a_name, chunk_a_frames_df, chunk_a_c2w_all, "chunk_a_raw", overlap_record_set),
        pose_rows_to_frame_df(chunk_b_name, chunk_b_frames_df, chunk_b_c2w_all, "chunk_b_raw", overlap_record_set),
        pose_rows_to_frame_df(chunk_b_name, chunk_b_frames_df, chunk_b_c2w_aligned_all, "chunk_b_aligned_to_a", overlap_record_set),
    ], ignore_index=True)

    pair_label = f"{chunk_a_name}__{chunk_b_name}"
    pair_csv = matching_dir / f"{pair_label}_overlap_pair_metrics_arc.csv"
    points_csv = matching_dir / f"{pair_label}_trajectory_points_arc.csv"
    transform_npy = matching_dir / f"{pair_label}_transform_b_to_a.npy"
    plot_png = matching_dir / f"{pair_label}_trajectory_match.png"
    plot_html = matching_dir / f"{pair_label}_trajectory_match.html"
    summary_json = matching_dir / f"{pair_label}_matching_summary.json"

    pair_df.to_csv(pair_csv, index=False, encoding="utf-8")
    points_df.to_csv(points_csv, index=False, encoding="utf-8")
    np.save(transform_npy, T_b_to_a.astype(np.float32))
    plot_pose_match(
        points_df.loc[points_df["variant"] == "chunk_a_raw"].copy(),
        points_df.loc[points_df["variant"] == "chunk_b_raw"].copy(),
        points_df.loc[points_df["variant"] == "chunk_b_aligned_to_a"].copy(),
        plot_png,
    )
    write_pose_match_html(
        points_df.loc[points_df["variant"] == "chunk_a_raw"].copy(),
        points_df.loc[points_df["variant"] == "chunk_b_raw"].copy(),
        points_df.loc[points_df["variant"] == "chunk_b_aligned_to_a"].copy(),
        plot_html,
    )

    summary = {
        "status": "ok",
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-overlap-pose-matching",
        "chunk_a_name": chunk_a_name,
        "chunk_b_name": chunk_b_name,
        "chunk_a_frames_path": str(chunk_a_frames_path),
        "chunk_a_pred_extrinsics_path": str(chunk_a_pred_path),
        "chunk_b_frames_path": str(chunk_b_frames_path),
        "chunk_b_pred_extrinsics_path": str(chunk_b_pred_path),
        "chunk_a_row_count": int(len(chunk_a_frames_df)),
        "chunk_b_row_count": int(len(chunk_b_frames_df)),
        "overlap_record_count": int(len(overlap_records)),
        "overlap_records": overlap_records,
        "local_extrinsic_mode": LOCAL_EXTRINSIC_MODE,
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
        "relative_scale": float(align_diag["scale"]),
        "relative_translation_norm": float(np.linalg.norm(T_b_to_a[:3, 3])),
        "relative_rotation_deg": float(rotation_angle_deg_from_matrix(T_b_to_a[:3, :3] / max(abs(float(align_diag["scale"])), 1e-12))),
        "center_error_pre_mean": float(center_error_pre.mean()),
        "center_error_pre_p95": float(np.quantile(center_error_pre, 0.95)),
        "center_error_post_mean": float(center_error_post.mean()),
        "center_error_post_p95": float(np.quantile(center_error_post, 0.95)),
        "lens_error_deg_pre_mean": float(lens_error_pre.mean()),
        "lens_error_deg_pre_p95": float(np.quantile(lens_error_pre, 0.95)),
        "lens_error_deg_post_mean": float(lens_error_post.mean()),
        "lens_error_deg_post_p95": float(np.quantile(lens_error_post, 0.95)),
        "up_error_deg_pre_mean": float(up_error_pre.mean()),
        "up_error_deg_pre_p95": float(np.quantile(up_error_pre, 0.95)),
        "up_error_deg_post_mean": float(up_error_post.mean()),
        "up_error_deg_post_p95": float(np.quantile(up_error_post, 0.95)),
        "pair_metrics_csv": str(pair_csv),
        "trajectory_points_csv": str(points_csv),
        "transform_npy": str(transform_npy),
        "plot_png": str(plot_png),
        "plot_html": str(plot_html),
    }
    save_json(summary_json, summary)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    display_stage_summary(
        "9-1",
        "overlap pose matching",
        inputs=[
            {"item": "chunk_a_input_frames", "path": str(chunk_a_frames_path)},
            {"item": "chunk_a_pred_extrinsics", "path": str(chunk_a_pred_path)},
            {"item": "chunk_b_input_frames", "path": str(chunk_b_frames_path)},
            {"item": "chunk_b_pred_extrinsics", "path": str(chunk_b_pred_path)},
        ],
        outputs=[
            {"item": "matching_summary", "path": str(summary_json)},
            {"item": "matching_pair_metrics", "path": str(pair_csv)},
            {"item": "matching_trajectory_points", "path": str(points_csv)},
            {"item": "matching_transform", "path": str(transform_npy)},
            {"item": "matching_plot", "path": str(plot_png)},
            {"item": "matching_plot_html", "path": str(plot_html)},
        ],
        notes=[
            {"item": "chunk_pair", "value": pair_label},
            {"item": "overlap_record_count", "value": int(len(overlap_records))},
            {"item": "relative_rotation_deg", "value": float(summary["relative_rotation_deg"])},
            {"item": "center_error_post_p95", "value": float(summary["center_error_post_p95"])},
            {"item": "lens_error_deg_post_p95", "value": float(summary["lens_error_deg_post_p95"])},
        ],
    )
```

#No: #10-1
前: #9-1
次: #10-2

# 10 Global Prepose Graph And Gate

この markdown cell は `#10-1` の global prepose graph build と gate を説明する。chunk 間整列を graph へ固定し、merge 前 validation を作る。

```python
#10-1

from pathlib import Path
import json
import math

import numpy as np
import pandas as pd

ctx = load_ctx()

probe_root = Path(ctx["probe_root"])
persist_root = Path(ctx.get("persist_root", probe_root))
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
merged_dir = Path(ctx.get("merged_dir", str(pipeline_root / "merged")))
merged_dir.mkdir(parents=True, exist_ok=True)

final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_diagnostics_dir.mkdir(parents=True, exist_ok=True)
stage_10_reaccess_dir = Path(ctx.get("stage_10_reaccess_dir", str(final_outputs_diagnostics_dir.parent / "#10-1" / "re_access")))
stage_10_persist_only_dir = Path(ctx.get("stage_10_persist_only_dir", str(final_outputs_diagnostics_dir.parent / "#10-1" / "persist_only")))
stage_10_reaccess_dir.mkdir(parents=True, exist_ok=True)
stage_10_persist_only_dir.mkdir(parents=True, exist_ok=True)

anchor_dir = persist_root / "01_anchor"
camera_anchor_full_path = anchor_dir / "camera_anchor_full_arc.csv"

batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
run_status_path = final_outputs_diagnostics_dir / "batch_run_status_arc.csv"
seed_trace_path = final_outputs_diagnostics_dir / "incremental_seed_trace_arc.csv"

assert batch_execution_items_path.exists(), batch_execution_items_path
assert camera_anchor_full_path.exists(), camera_anchor_full_path

items_df = pd.read_csv(batch_execution_items_path)
assert not items_df.empty, batch_execution_items_path
sort_cols = [c for c in ["chunk_id", "batch_index", "batch_name", "chunk_name"] if c in items_df.columns]
if sort_cols:
    items_df = items_df.sort_values(sort_cols, kind="stable").reset_index(drop=True)

run_status_df = pd.read_csv(run_status_path) if run_status_path.exists() and run_status_path.stat().st_size > 0 else pd.DataFrame()
seed_trace_df = pd.read_csv(seed_trace_path) if seed_trace_path.exists() and seed_trace_path.stat().st_size > 0 else pd.DataFrame()

anchor_full_df = pd.read_csv(camera_anchor_full_path)

if "cx_world" not in anchor_full_df.columns and "cam_cx" in anchor_full_df.columns:
    anchor_full_df["cx_world"] = anchor_full_df["cam_cx"]
    anchor_full_df["cy_world"] = anchor_full_df["cam_cy"]
    anchor_full_df["cz_world"] = anchor_full_df["cam_cz"]
if "anchor_lens_x" not in anchor_full_df.columns and "lens_x" in anchor_full_df.columns:
    anchor_full_df["anchor_lens_x"] = anchor_full_df["lens_x"]
    anchor_full_df["anchor_lens_y"] = anchor_full_df["lens_y"]
    anchor_full_df["anchor_lens_z"] = anchor_full_df["lens_z"]
if "anchor_up_x" not in anchor_full_df.columns and "up_x" in anchor_full_df.columns:
    anchor_full_df["anchor_up_x"] = anchor_full_df["up_x"]
    anchor_full_df["anchor_up_y"] = anchor_full_df["up_y"]
    anchor_full_df["anchor_up_z"] = anchor_full_df["up_z"]

required_anchor_cols = [
    "record_index",
    "cx_world", "cy_world", "cz_world",
    "anchor_lens_x", "anchor_lens_y", "anchor_lens_z",
]
missing_anchor_cols = [c for c in required_anchor_cols if c not in anchor_full_df.columns]
assert not missing_anchor_cols, {"missing_anchor_columns": missing_anchor_cols}

# gate値は既存を踏襲
PREMERGE_CENTER_ERROR_P95_MAX = 0.25
PREMERGE_LENS_ERROR_DEG_P95_MAX = 12.0
PREMERGE_DELTA_CENTER_ERROR_MAX = 0.15
PREMERGE_DELTA_LENS_ERROR_DEG_MAX = 8.0

residual_csv = stage_10_persist_only_dir / "pred_vs_anchor_pose_residual_arc.csv"
missing_pred_csv = stage_10_persist_only_dir / "pred_vs_anchor_pose_residual_missing_pred_arc.csv"
gate_csv = stage_10_persist_only_dir / "premerge_pose_gate_arc.csv"
route_compare_json = stage_10_persist_only_dir / "premerge_route_compare_summary.json"
route_compare_csv = stage_10_persist_only_dir / "premerge_route_compare_arc.csv"
graph_solution_csv = stage_10_persist_only_dir / "prepose_chunk_graph_solution_arc.csv"   # downstream互換: chunk validation summary
graph_summary_json = stage_10_persist_only_dir / "prepose_chunk_graph_summary.json"        # downstream互換: incremental summary
graph_opt_summary_json = stage_10_persist_only_dir / "prepose_graph_optimization_summary.json"
validation_json = stage_10_persist_only_dir / "premerge_pose_validation.json"
validation_csv = stage_10_persist_only_dir / "premerge_pose_validation.csv"
graph_contract_manifest_path = stage_10_reaccess_dir / "graph_contract_manifest.json"
identity_transform_csv = chunk_manifest_dir / "chunk_global_transforms_arc.csv"

MAT_COLS = [f"t{r}{c}" for r in range(4) for c in range(4)]


def _record_col(df: pd.DataFrame) -> str:
    for c in ["record_index", "frame_index", "global_index", "index"]:
        if c in df.columns:
            return c
    raise AssertionError({"reason": "record index column not found", "columns": df.columns.tolist()})


def _safe_int(v):
    try:
        return int(v)
    except Exception:
        return None


def _normalize(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float64)
    n = np.linalg.norm(v)
    if n <= 1e-12:
        return np.zeros_like(v)
    return v / n


def _angle_deg(a: np.ndarray, b: np.ndarray) -> float:
    a = _normalize(a)
    b = _normalize(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom <= 1e-12:
        return float("nan")
    cosv = np.clip(float(np.dot(a, b)), -1.0, 1.0)
    return float(np.degrees(np.arccos(cosv)))


def _p95(series) -> float:
    arr = pd.Series(series).dropna().to_numpy(dtype=np.float64)
    if len(arr) == 0:
        return float("nan")
    return float(np.percentile(arr, 95))


def _max_abs(series) -> float:
    arr = pd.Series(series).dropna().to_numpy(dtype=np.float64)
    if len(arr) == 0:
        return float("nan")
    return float(np.max(np.abs(arr)))


def _ensure_pose_batch(arr: np.ndarray) -> np.ndarray:
    arr = np.asarray(arr, dtype=np.float64)
    if arr.ndim == 2:
        arr = arr[None, ...]
    if arr.shape[-2:] == (3, 4):
        out = np.repeat(np.eye(4, dtype=np.float64)[None, ...], arr.shape[0], axis=0)
        out[:, :3, :] = arr
        return out
    if arr.shape[-2:] == (4, 4):
        return arr
    raise AssertionError({"reason": "unexpected_pose_shape", "shape": tuple(arr.shape)})


def _w2c_to_c2w_batch(w2c_batch: np.ndarray) -> np.ndarray:
    out = []
    for M in _ensure_pose_batch(w2c_batch):
        out.append(np.linalg.inv(M))
    return np.stack(out, axis=0)


def _poses_to_center_lens(c2w_batch: np.ndarray):
    centers = c2w_batch[:, :3, 3]
    lens = -c2w_batch[:, :3, 2]
    lens = np.stack([_normalize(v) for v in lens], axis=0)
    return centers, lens


def _resolve_pred_path(item_row: pd.Series) -> Path | None:
    candidates = []

    for col in [
        "pred_extrinsics_path",
        "pred_extrinsics_npy",
        "chunk_pred_extrinsics_path",
        "output_pred_extrinsics_path",
    ]:
        if col in item_row.index and pd.notna(item_row[col]) and str(item_row[col]).strip():
            candidates.append(Path(str(item_row[col]).strip()))

    chunk_name = str(item_row.get("chunk_name", "")).strip()
    batch_name = str(item_row.get("batch_name", "")).strip()

    if "batch_work_dir" in item_row.index and pd.notna(item_row["batch_work_dir"]) and str(item_row["batch_work_dir"]).strip():
        batch_work_dir = Path(str(item_row["batch_work_dir"]).strip())
        if batch_work_dir.name == chunk_name or batch_work_dir.name.startswith(f"{chunk_name}_"):
            candidates.append(batch_work_dir / "pred_extrinsics.npy")
            batch_work_dir = batch_work_dir.parent
        if chunk_name:
            candidates.append(batch_work_dir / chunk_name / "pred_extrinsics.npy")
            candidates.extend(sorted(batch_work_dir.glob(f"{chunk_name}*/pred_extrinsics.npy")))
        candidates.append(batch_work_dir / "pred_extrinsics.npy")
        candidates.extend(sorted(batch_work_dir.glob("chunk_*/pred_extrinsics.npy")))

    if "chunk_out_dir" in item_row.index and pd.notna(item_row["chunk_out_dir"]) and str(item_row["chunk_out_dir"]).strip():
        chunk_out_dir = Path(str(item_row["chunk_out_dir"]).strip())
        candidates.insert(0, chunk_out_dir / "pred_extrinsics.npy")
        if chunk_out_dir.exists():
            candidates.extend(sorted(chunk_out_dir.glob("*/pred_extrinsics.npy")))

    if chunk_name:
        candidates.append(chunk_runs_dir / chunk_name / "pred_extrinsics.npy")
        if batch_name:
            candidates.append(chunk_runs_dir / batch_name / chunk_name / "pred_extrinsics.npy")
            candidates.extend(sorted((chunk_runs_dir / batch_name).glob(f"{chunk_name}*/pred_extrinsics.npy")))
        candidates.extend(sorted(chunk_runs_dir.glob(f"batch_*/{chunk_name}/pred_extrinsics.npy")))
        candidates.extend(sorted(chunk_runs_dir.glob(f"batch_*/{chunk_name}*/pred_extrinsics.npy")))
        candidates.extend(sorted(chunk_runs_dir.glob(f"**/{chunk_name}*/pred_extrinsics.npy")))

    if not run_status_df.empty:
        rs = run_status_df.loc[run_status_df["chunk_name"].astype(str) == chunk_name].copy()
        if "batch_name" in run_status_df.columns and batch_name:
            rs2 = rs.loc[rs["batch_name"].astype(str) == batch_name].copy()
            if len(rs2):
                rs = rs2
        if len(rs):
            out_dir = Path(str(rs.iloc[-1]["out_dir"]))
            candidates.insert(0, out_dir / "pred_extrinsics.npy")

    seen = set()
    uniq = []
    for c in candidates:
        s = str(c)
        if s not in seen:
            uniq.append(c)
            seen.add(s)

    for c in uniq:
        if c.exists():
            return c
    return None


def _resolve_chunk_csv(item_row: pd.Series, pred_path: Path | None) -> Path | None:
    candidates = []

    for col in ["runtime_chunk_csv", "chunk_csv", "chunk_input_csv"]:
        if col in item_row.index and pd.notna(item_row[col]) and str(item_row[col]).strip():
            candidates.append(Path(str(item_row[col]).strip()))

    chunk_name = str(item_row.get("chunk_name", "")).strip()
    batch_name = str(item_row.get("batch_name", "")).strip()

    if pred_path is not None:
        candidates.append(pred_path.parent / "chunk_input_frames.csv")
        candidates.append(pred_path.parent / "_runtime" / "chunk_input_seeded.csv")
        candidates.extend(sorted(pred_path.parent.glob("chunk_input_frames*.csv")))
        candidates.extend(sorted((pred_path.parent / "_runtime").glob("chunk_input_seeded*.csv")))

    if "chunk_out_dir" in item_row.index and pd.notna(item_row["chunk_out_dir"]) and str(item_row["chunk_out_dir"]).strip():
        chunk_out_dir = Path(str(item_row["chunk_out_dir"]).strip())
        candidates.append(chunk_out_dir / "chunk_input_frames.csv")
        candidates.append(chunk_out_dir / "_runtime" / "chunk_input_seeded.csv")
        candidates.extend(sorted(chunk_out_dir.glob("chunk_input_frames*.csv")))
        candidates.extend(sorted((chunk_out_dir / "_runtime").glob("chunk_input_seeded*.csv")))

    if not run_status_df.empty:
        rs = run_status_df.loc[run_status_df["chunk_name"].astype(str) == chunk_name].copy()
        if "batch_name" in run_status_df.columns and batch_name:
            rs2 = rs.loc[rs["batch_name"].astype(str) == batch_name].copy()
            if len(rs2):
                rs = rs2
        if len(rs):
            if "runtime_chunk_csv" in rs.columns and pd.notna(rs.iloc[-1]["runtime_chunk_csv"]):
                candidates.insert(0, Path(str(rs.iloc[-1]["runtime_chunk_csv"])))

    seen = set()
    uniq = []
    for c in candidates:
        s = str(c)
        if s not in seen:
            uniq.append(c)
            seen.add(s)

    for c in uniq:
        if c.exists():
            return c
    return None


def _load_chunk_pose_df(item_row: pd.Series) -> pd.DataFrame:
    pred_path = _resolve_pred_path(item_row)
    chunk_csv_path = _resolve_chunk_csv(item_row, pred_path)

    chunk_name = str(item_row.get("chunk_name", ""))
    if pred_path is None:
        return pd.DataFrame(columns=[
            "chunk_name", "record_index", "chunk_local_index",
            "pred_cx_world", "pred_cy_world", "pred_cz_world",
            "pred_lens_x", "pred_lens_y", "pred_lens_z",
            "is_output_range", "is_adopt_range",
        ])

    assert chunk_csv_path is not None and chunk_csv_path.exists(), {
        "chunk_name": chunk_name,
        "reason": "chunk_csv_not_found",
        "pred_path": str(pred_path),
    }

    chunk_df = pd.read_csv(chunk_csv_path)
    rec_col = _record_col(chunk_df)
    pred_w2c = _ensure_pose_batch(np.load(pred_path))
    assert len(chunk_df) == len(pred_w2c), {
        "chunk_name": chunk_name,
        "reason": "row_count_mismatch",
        "chunk_rows": int(len(chunk_df)),
        "pred_rows": int(len(pred_w2c)),
        "chunk_csv": str(chunk_csv_path),
        "pred_path": str(pred_path),
    }

    c2w = _w2c_to_c2w_batch(pred_w2c)
    centers, lens = _poses_to_center_lens(c2w)

    if "is_output_range" not in chunk_df.columns:
        chunk_df["is_output_range"] = False
    if "is_adopt_range" not in chunk_df.columns:
        chunk_df["is_adopt_range"] = False

    out = pd.DataFrame({
        "chunk_name": chunk_name,
        "record_index": chunk_df[rec_col].astype(int).to_numpy(),
        "chunk_local_index": np.arange(len(chunk_df), dtype=int),
        "pred_cx_world": centers[:, 0],
        "pred_cy_world": centers[:, 1],
        "pred_cz_world": centers[:, 2],
        "pred_lens_x": lens[:, 0],
        "pred_lens_y": lens[:, 1],
        "pred_lens_z": lens[:, 2],
        "pred_path": str(pred_path),
        "chunk_csv_path": str(chunk_csv_path),
        "is_output_range": chunk_df["is_output_range"].astype(bool).to_numpy(),
        "is_adopt_range": chunk_df["is_adopt_range"].astype(bool).to_numpy(),
    })

    if "seed_pose_applied" in chunk_df.columns:
        out["seed_pose_applied"] = chunk_df["seed_pose_applied"].astype(bool).to_numpy()
    else:
        out["seed_pose_applied"] = False

    return out


items_eval_df = items_df.copy()

if not run_status_df.empty and {"chunk_name", "batch_name", "out_dir"}.issubset(run_status_df.columns):
    merge_cols = ["chunk_name", "batch_name"]
    rs_cols = [c for c in ["chunk_name", "batch_name", "status", "returncode", "outputs_exist", "out_dir", "runtime_chunk_csv", "seeded_overlap_count"] if c in run_status_df.columns]
    items_eval_df = items_eval_df.merge(
        run_status_df[rs_cols].drop_duplicates(subset=merge_cols, keep="last"),
        on=merge_cols,
        how="left",
        suffixes=("", "_run"),
    )

if not seed_trace_df.empty and "chunk_name" in seed_trace_df.columns:
    st_cols = [c for c in ["chunk_name", "seeded_overlap_count", "chunk_step", "overlap_size", "adopt_size", "pose_pipeline_mode"] if c in seed_trace_df.columns]
    items_eval_df = items_eval_df.merge(
        seed_trace_df[st_cols].drop_duplicates(subset=["chunk_name"], keep="last"),
        on="chunk_name",
        how="left",
        suffixes=("", "_seed"),
    )

chunk_pose_rows = []
missing_chunk_rows = []

for _, item_row in items_eval_df.iterrows():
    chunk_name = str(item_row.get("chunk_name", ""))
    pred_path = _resolve_pred_path(item_row)
    if pred_path is None:
        missing_chunk_rows.append({
            "chunk_name": chunk_name,
            "reason": "pred_extrinsics_not_found",
        })
        continue

    pose_df = _load_chunk_pose_df(item_row)
    if pose_df.empty:
        missing_chunk_rows.append({
            "chunk_name": chunk_name,
            "reason": "pose_df_empty",
            "pred_path": str(pred_path),
        })
        continue

    pose_df["chunk_id"] = _safe_int(item_row["chunk_id"]) if "chunk_id" in item_row.index else None
    pose_df["batch_name"] = str(item_row.get("batch_name", ""))
    pose_df["seeded_overlap_count"] = int(item_row["seeded_overlap_count"]) if pd.notna(item_row.get("seeded_overlap_count")) else 0
    chunk_pose_rows.append(pose_df)

all_chunk_pose_df = pd.concat(chunk_pose_rows, ignore_index=True) if chunk_pose_rows else pd.DataFrame()

anchor_eval_df = anchor_full_df[[
    "record_index",
    "cx_world", "cy_world", "cz_world",
    "anchor_lens_x", "anchor_lens_y", "anchor_lens_z",
]].copy()
anchor_eval_df["record_index"] = anchor_eval_df["record_index"].astype(int)
anchor_eval_df = anchor_eval_df.sort_values("record_index", kind="stable").reset_index(drop=True)

if all_chunk_pose_df.empty:
    raise AssertionError({"reason": "no_chunk_pose_loaded", "missing_chunk_rows": missing_chunk_rows[:10]})

all_chunk_pose_df = all_chunk_pose_df.sort_values(
    [c for c in ["chunk_id", "batch_name", "chunk_name", "chunk_local_index"] if c in all_chunk_pose_df.columns],
    kind="stable",
).reset_index(drop=True)

# 評価対象は output range のみ
eval_pose_df = all_chunk_pose_df.loc[all_chunk_pose_df["is_output_range"].fillna(False)].copy()

# global pred は adopt優先、その次に output range 最後勝ち
adopt_pose_df = eval_pose_df.loc[eval_pose_df["is_adopt_range"].fillna(False)].copy()

if len(adopt_pose_df):
    global_pred_df = (
        adopt_pose_df
        .drop_duplicates(subset=["record_index"], keep="last")
        .sort_values("record_index", kind="stable")
        .reset_index(drop=True)
    )
else:
    global_pred_df = (
        eval_pose_df
        .drop_duplicates(subset=["record_index"], keep="last")
        .sort_values("record_index", kind="stable")
        .reset_index(drop=True)
    )

target_record_indices = sorted(eval_pose_df["record_index"].astype(int).unique().tolist())

target_anchor_df = anchor_eval_df.loc[
    anchor_eval_df["record_index"].astype(int).isin(target_record_indices)
].copy()

residual_df = global_pred_df.merge(target_anchor_df, on="record_index", how="left")

residual_df["center_error_m"] = np.sqrt(
    (residual_df["pred_cx_world"] - residual_df["cx_world"]) ** 2 +
    (residual_df["pred_cy_world"] - residual_df["cy_world"]) ** 2 +
    (residual_df["pred_cz_world"] - residual_df["cz_world"]) ** 2
)

residual_df["lens_error_deg"] = [
    _angle_deg(
        np.array([px, py, pz], dtype=np.float64),
        np.array([ax, ay, az], dtype=np.float64),
    )
    for px, py, pz, ax, ay, az in zip(
        residual_df["pred_lens_x"], residual_df["pred_lens_y"], residual_df["pred_lens_z"],
        residual_df["anchor_lens_x"], residual_df["anchor_lens_y"], residual_df["anchor_lens_z"],
    )
]

residual_df["pred_exists"] = True
residual_df.to_csv(residual_csv, index=False, encoding="utf-8")

missing_pred_df = target_anchor_df.loc[
    ~target_anchor_df["record_index"].isin(global_pred_df["record_index"].astype(int))
].copy()
missing_pred_df["reason"] = "target_output_record_index_not_in_global_pred"
missing_pred_df.to_csv(missing_pred_csv, index=False, encoding="utf-8")

route_rows = []
if len(residual_df) >= 2:
    r = residual_df.sort_values("record_index", kind="stable").reset_index(drop=True)
    for i in range(1, len(r)):
        prev_row = r.iloc[i - 1]
        curr_row = r.iloc[i]

        pred_delta = np.array([
            curr_row["pred_cx_world"] - prev_row["pred_cx_world"],
            curr_row["pred_cy_world"] - prev_row["pred_cy_world"],
            curr_row["pred_cz_world"] - prev_row["pred_cz_world"],
        ], dtype=np.float64)
        anchor_delta = np.array([
            curr_row["cx_world"] - prev_row["cx_world"],
            curr_row["cy_world"] - prev_row["cy_world"],
            curr_row["cz_world"] - prev_row["cz_world"],
        ], dtype=np.float64)

        delta_center_error_m = float(np.linalg.norm(pred_delta - anchor_delta))

        prev_pred_lens = np.array([prev_row["pred_lens_x"], prev_row["pred_lens_y"], prev_row["pred_lens_z"]], dtype=np.float64)
        curr_pred_lens = np.array([curr_row["pred_lens_x"], curr_row["pred_lens_y"], curr_row["pred_lens_z"]], dtype=np.float64)
        prev_anchor_lens = np.array([prev_row["anchor_lens_x"], prev_row["anchor_lens_y"], prev_row["anchor_lens_z"]], dtype=np.float64)
        curr_anchor_lens = np.array([curr_row["anchor_lens_x"], curr_row["anchor_lens_y"], curr_row["anchor_lens_z"]], dtype=np.float64)

        pred_lens_delta_deg = _angle_deg(prev_pred_lens, curr_pred_lens)
        anchor_lens_delta_deg = _angle_deg(prev_anchor_lens, curr_anchor_lens)
        delta_lens_error_deg = float(abs(pred_lens_delta_deg - anchor_lens_delta_deg))

        route_rows.append({
            "prev_record_index": int(prev_row["record_index"]),
            "record_index": int(curr_row["record_index"]),
            "delta_center_error_m": delta_center_error_m,
            "pred_lens_delta_deg": pred_lens_delta_deg,
            "anchor_lens_delta_deg": anchor_lens_delta_deg,
            "delta_lens_error_deg": delta_lens_error_deg,
            "pred_chunk_name": str(curr_row["chunk_name"]),
            "pred_chunk_id": _safe_int(curr_row["chunk_id"]) if "chunk_id" in curr_row else None,
        })

route_compare_df = pd.DataFrame(route_rows)
route_compare_df.to_csv(route_compare_csv, index=False, encoding="utf-8")

chunk_gate_rows = []
for _, item_row in items_eval_df.iterrows():
    chunk_name = str(item_row.get("chunk_name", ""))
    chunk_id = _safe_int(item_row["chunk_id"]) if "chunk_id" in item_row.index else None

    chunk_eval_rows = residual_df.loc[residual_df["chunk_name"].astype(str) == chunk_name].copy()
    if len(chunk_eval_rows) == 0:
        chunk_gate_rows.append({
            "chunk_id": chunk_id,
            "chunk_name": chunk_name,
            "status": "missing",
            "record_count": 0,
            "seeded_overlap_count": int(item_row["seeded_overlap_count"]) if pd.notna(item_row.get("seeded_overlap_count")) else 0,
            "center_error_p95_m": np.nan,
            "lens_error_p95_deg": np.nan,
            "delta_center_error_max_m": np.nan,
            "delta_lens_error_max_deg": np.nan,
            "hard_fail": True,
            "anchor_warning": False,
            **{c: np.nan for c in MAT_COLS},
        })
        continue

    chunk_route_rows = route_compare_df.loc[route_compare_df["pred_chunk_name"].astype(str) == chunk_name].copy()
    center_error_p95_m = _p95(chunk_eval_rows["center_error_m"])
    lens_error_p95_deg = _p95(chunk_eval_rows["lens_error_deg"])
    delta_center_error_max_m = _max_abs(chunk_route_rows["delta_center_error_m"])
    delta_lens_error_max_deg = _max_abs(chunk_route_rows["delta_lens_error_deg"])

    hard_fail = (
        (pd.notna(center_error_p95_m) and center_error_p95_m > PREMERGE_CENTER_ERROR_P95_MAX)
        or (pd.notna(lens_error_p95_deg) and lens_error_p95_deg > PREMERGE_LENS_ERROR_DEG_P95_MAX)
    )
    anchor_warning = (
        (pd.notna(delta_center_error_max_m) and delta_center_error_max_m > PREMERGE_DELTA_CENTER_ERROR_MAX)
        or (pd.notna(delta_lens_error_max_deg) and delta_lens_error_max_deg > PREMERGE_DELTA_LENS_ERROR_DEG_MAX)
    )

    row = {
        "chunk_id": chunk_id,
        "chunk_name": chunk_name,
        "status": "ok" if not hard_fail else "hard_fail",
        "record_count": int(len(chunk_eval_rows)),
        "seeded_overlap_count": int(item_row["seeded_overlap_count"]) if pd.notna(item_row.get("seeded_overlap_count")) else 0,
        "center_error_p95_m": center_error_p95_m,
        "lens_error_p95_deg": lens_error_p95_deg,
        "delta_center_error_max_m": delta_center_error_max_m,
        "delta_lens_error_max_deg": delta_lens_error_max_deg,
        "hard_fail": bool(hard_fail),
        "anchor_warning": bool(anchor_warning),
    }
    I = np.eye(4, dtype=np.float64)
    for r in range(4):
        for c in range(4):
            row[f"t{r}{c}"] = float(I[r, c])
    chunk_gate_rows.append(row)

gate_df = pd.DataFrame(chunk_gate_rows)
gate_df.to_csv(gate_csv, index=False, encoding="utf-8")
gate_df.to_csv(validation_csv, index=False, encoding="utf-8")
gate_df.to_csv(graph_solution_csv, index=False, encoding="utf-8")  # downstream互換: identity列つき

identity_rows = []
for _, item_row in items_eval_df.iterrows():
    chunk_name = str(item_row.get("chunk_name", ""))
    row = {"chunk_name": chunk_name}
    I = np.eye(4, dtype=np.float64)
    for r in range(4):
        for c in range(4):
            row[f"t{r}{c}"] = float(I[r, c])
    identity_rows.append(row)
identity_df = pd.DataFrame(identity_rows)
identity_df.to_csv(identity_transform_csv, index=False, encoding="utf-8")

route_compare_summary = {
    "route_label": "continuous-gs-v07-chunk18-step6-context12-output6-adopt6-incremental",
    "selected_route_counts": [int(len(route_compare_df))],
    "preferred_route_label": "incremental_seeded_global_pose",
    "evaluation_scope": "output_range_only",
    "context_size": 12,
    "output_size": 6,
    "adopt_size": 6,
    "delta_center_error_max_m": _max_abs(route_compare_df["delta_center_error_m"]) if len(route_compare_df) else float("nan"),
    "delta_lens_error_max_deg": _max_abs(route_compare_df["delta_lens_error_deg"]) if len(route_compare_df) else float("nan"),
}
save_json(route_compare_json, route_compare_summary)

hard_fail_count = int(gate_df["hard_fail"].fillna(False).astype(bool).sum()) if len(gate_df) else 0
anchor_warning_count = int(gate_df["anchor_warning"].fillna(False).astype(bool).sum()) if len(gate_df) else 0
tested_chunk_count = int(len(gate_df))
missing_pred_count = int(len(missing_pred_df))

if hard_fail_count > 0:
    status = "hard_fail"
elif anchor_warning_count > 0:
    status = "warning"
else:
    status = "ok"

validation = {
    "status": status,
    "route": "continuous-gs-v07-chunk18-step6-context12-output6-adopt6-incremental",
    "preferred_route_label": "incremental_seeded_global_pose",
    "evaluation_scope": "output_range_only",
    "context_size": 12,
    "output_size": 6,
    "adopt_size": 6,
    "selected_route_counts": [int(len(route_compare_df))],
    "preferred_fallback_used_count": 0,
    "tested_chunk_count": tested_chunk_count,
    "hard_fail_count": hard_fail_count,
    "anchor_warning_count": anchor_warning_count,
    "missing_pred_count": missing_pred_count,
    "global_pred_record_count": int(len(global_pred_df)),
    "target_output_record_count": int(len(target_anchor_df)),
    "center_error_p95_m": _p95(residual_df["center_error_m"]) if len(residual_df) else float("nan"),
    "lens_error_p95_deg": _p95(residual_df["lens_error_deg"]) if len(residual_df) else float("nan"),
    "delta_center_error_max_m": _max_abs(route_compare_df["delta_center_error_m"]) if len(route_compare_df) else float("nan"),
    "delta_lens_error_max_deg": _max_abs(route_compare_df["delta_lens_error_deg"]) if len(route_compare_df) else float("nan"),
    "artifacts": {
        "residual_csv": str(residual_csv),
        "missing_pred_csv": str(missing_pred_csv),
        "gate_csv": str(gate_csv),
        "route_compare_csv": str(route_compare_csv),
        "graph_solution_csv_compat": str(graph_solution_csv),
        "identity_transform_csv": str(identity_transform_csv),
    },
}
save_json(validation_json, validation)

graph_summary = {
    "mode": "incremental_validation_only",
    "graph_mainflow_removed": True,
    "graph_edges_used": False,
    "graph_solution_csv_semantics": "chunk_validation_summary_with_identity_columns",
    "chunk_global_transforms_semantics": "identity_transforms_for_downstream_compat",
    "evaluation_scope": "output_range_only",
    "context_size": 12,
    "output_size": 6,
    "adopt_size": 6,
    "tested_chunk_count": tested_chunk_count,
    "status": status,
}
save_json(graph_summary_json, graph_summary)
save_json(graph_opt_summary_json, {
    "mode": "not_applicable",
    "reason": "sim3_graph_mainflow_removed",
    "status": status,
})
save_json(graph_contract_manifest_path, {
    "stage": "#10-1",
    "status": status,
    "canonical_root": str(stage_10_persist_only_dir),
    "canonical_artifacts": {
        "premerge_pose_validation_json": str(validation_json),
        "premerge_pose_validation_csv": str(validation_csv),
        "prepose_chunk_graph_solution_csv": str(graph_solution_csv),
        "prepose_chunk_graph_summary_json": str(graph_summary_json),
        "premerge_route_compare_summary_json": str(route_compare_json),
        "premerge_route_compare_csv": str(route_compare_csv),
        "pred_vs_anchor_pose_residual_csv": str(residual_csv),
        "pred_vs_anchor_pose_residual_missing_pred_csv": str(missing_pred_csv),
        "premerge_pose_gate_csv": str(gate_csv),
        "prepose_graph_optimization_summary_json": str(graph_opt_summary_json),
        "chunk_global_transforms_csv": str(identity_transform_csv),
    },
})

missing_chunk_df = pd.DataFrame(missing_chunk_rows)
if len(missing_chunk_df):
    display(missing_chunk_df.head(20))

print(json.dumps(validation, indent=2, ensure_ascii=False))
display(gate_df.head(20))
display(route_compare_df.head(20))
display(residual_df.head(20))

display_stage_summary(
    "10-1",
    "incremental premerge validation and compatibility artifacts",
    outputs=[
        {"item": "validation_json", "path": str(validation_json)},
        {"item": "gate_csv", "path": str(gate_csv)},
        {"item": "route_compare_csv", "path": str(route_compare_csv)},
        {"item": "residual_csv", "path": str(residual_csv)},
        {"item": "graph_solution_csv_compat", "path": str(graph_solution_csv)},
        {"item": "identity_transform_csv", "path": str(identity_transform_csv)},
        {"item": "graph_contract_manifest", "path": str(graph_contract_manifest_path)},
    ],
)

items_df = pd.read_csv(batch_execution_items_path)
display(items_df[["chunk_id", "chunk_name", "batch_name", "batch_work_dir"]].head(20))
```

#No: #10-2
前: #10-1
次: #11-1

# 10 Global Prepose Graph And Gate

この markdown cell は `#10-2` の prepose graph review gate を説明する。graph artifact を review 用 summary へ整え、merge 前確認面を作る。

```python
#10-2

ctx = load_ctx()

probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
merged_dir = Path(ctx.get("merged_dir", str(pipeline_root / "merged")))
merged_dir.mkdir(parents=True, exist_ok=True)

final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_diagnostics_dir.mkdir(parents=True, exist_ok=True)

validation_json = merged_dir / "premerge_pose_validation.json"
route_compare_json = merged_dir / "premerge_route_compare_summary.json"
route_compare_csv = merged_dir / "premerge_route_compare_arc.csv"
graph_solution_csv = merged_dir / "prepose_chunk_graph_solution_arc.csv"   # compat: chunk validation summary
graph_summary_json = merged_dir / "prepose_chunk_graph_summary.json"
batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"

required_paths = [
    validation_json,
    route_compare_json,
    route_compare_csv,
    graph_solution_csv,
    graph_summary_json,
    batch_execution_items_path,
]
missing_paths = [str(path) for path in required_paths if not path.exists()]
assert not missing_paths, {"reason": "missing_incremental_validation_artifacts", "missing_paths": missing_paths}

validation = load_json(validation_json)
route_compare_summary = load_json(route_compare_json)
graph_summary = load_json(graph_summary_json)

validation_df = pd.read_csv(graph_solution_csv) if graph_solution_csv.stat().st_size > 0 else pd.DataFrame()
route_compare_df = pd.read_csv(route_compare_csv) if route_compare_csv.stat().st_size > 0 else pd.DataFrame()

status = str(validation.get("status", "missing"))
selected_route_counts = validation.get("selected_route_counts", route_compare_summary.get("selected_route_counts", []))
preferred_route_label = str(validation.get("preferred_route_label", route_compare_summary.get("preferred_route_label", "")))
preferred_fallback_used_count = int(validation.get("preferred_fallback_used_count", 0))

review_summary = {
    "status": status,
    "route": "continuous-gs-v07-chunk18-step6-context12-output6-adopt6-incremental-review",
    "preferred_route_label": preferred_route_label,
    "selected_route_counts": selected_route_counts,
    "preferred_fallback_used_count": preferred_fallback_used_count,
    "tested_chunk_count": int(validation.get("tested_chunk_count", len(validation_df))),
    "hard_fail_count": int(validation.get("hard_fail_count", 0)),
    "anchor_warning_count": int(validation.get("anchor_warning_count", 0)),
    "missing_pred_count": int(validation.get("missing_pred_count", 0)),
    "target_output_record_count": int(validation.get("target_output_record_count", 0)),
    "global_pred_record_count": int(validation.get("global_pred_record_count", 0)),
    "evaluation_scope": "output_range_only",
    "context_size": 12,
    "output_size": 6,
    "adopt_size": 6,
    "graph_mainflow_removed": bool(graph_summary.get("graph_mainflow_removed", True)),
    "graph_edges_used": bool(graph_summary.get("graph_edges_used", False)),
    "route_compare_csv": str(route_compare_csv),
    "chunk_validation_summary_csv": str(graph_solution_csv),
    "incremental_validation_summary_json": str(graph_summary_json),
    "premerge_pose_validation_json": str(validation_json),
}
save_json(final_outputs_diagnostics_dir / "prepose_graph_gate_review.json", review_summary)

artifact_index = {
    "route_compare_csv": str(route_compare_csv),
    "chunk_validation_summary_csv": str(graph_solution_csv),
    "premerge_pose_validation_json": str(validation_json),
    "incremental_validation_summary_json": str(graph_summary_json),
}
save_json(final_outputs_diagnostics_dir / "premerge_validation_artifact_index.json", artifact_index)

print(json.dumps(review_summary, indent=2, ensure_ascii=False))
print(json.dumps(validation, indent=2, ensure_ascii=False))

if len(validation_df):
    display(validation_df)
if len(route_compare_df):
    display(route_compare_df.head(50))

display_stage_summary(
    "10-2",
    "incremental validation review",
    outputs=[
        {"item": "review_summary_json", "path": str(final_outputs_diagnostics_dir / "prepose_graph_gate_review.json")},
        {"item": "artifact_index_json", "path": str(final_outputs_diagnostics_dir / "premerge_validation_artifact_index.json")},
        {"item": "chunk_validation_summary_csv", "path": str(graph_solution_csv)},
        {"item": "route_compare_csv", "path": str(route_compare_csv)},
        {"item": "validation_json", "path": str(validation_json)},
    ],
)
```

#No: #11-1
前: #10-2
次: #11-2

# 11 Merge And Review

この markdown cell は `#11-1` の merge を説明する。graph で固定した chunk-to-world を使って chunk を合成し、final output を保存する。

```python
#11-1
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
persist_root = Path(ctx.get("persist_root", probe_root))
modeling_session_id = ctx["modeling_session_id"]
manifest_dir = Path(ctx["manifest_dir"])
final_outputs_dir = Path(ctx["final_outputs_dir"])
final_outputs_merged_dir = Path(ctx["final_outputs_merged_dir"])
final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_manifests_dir = Path(ctx["final_outputs_manifests_dir"])
final_outputs_chunk_evidence_dir = Path(ctx["final_outputs_chunk_evidence_dir"])

pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
anchor_dir = persist_root / "01_anchor"
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
graph_reaccess_dir = Path(ctx.get("stage_10_reaccess_dir", str(final_outputs_dir / "#10-1" / "re_access")))
graph_persist_only_dir = Path(ctx.get("stage_10_persist_only_dir", str(final_outputs_dir / "#10-1" / "persist_only")))
merge_reaccess_dir = Path(ctx.get("stage_11_reaccess_dir", str(final_outputs_dir / "#11-1" / "re_access")))
merge_persist_only_dir = Path(ctx.get("stage_11_persist_only_dir", str(final_outputs_dir / "#11-1" / "persist_only")))
final_outputs_merged_dir = merge_persist_only_dir / "merged"
final_outputs_diagnostics_dir = merge_persist_only_dir / "diagnostics"
final_outputs_manifests_dir = merge_persist_only_dir / "manifests"
final_outputs_chunk_evidence_dir = merge_persist_only_dir / "chunk_evidence"
merged_dir = final_outputs_merged_dir
stage_11_2_dir = merge_reaccess_dir / "11_2_handoff"
stage_11_3_dir = merge_reaccess_dir / "11_3_handoff"
stage_11_2_manifest_path = stage_11_2_dir / "11_2_handoff_manifest.json"
stage_11_3_manifest_path = stage_11_3_dir / "11_3_handoff_manifest.json"
stage_access_index_path = merge_reaccess_dir / "stage_access_index.json"
merge_resume_state_path = merge_reaccess_dir / "merge_resume_state.json"
for p in [
    final_outputs_dir,
    graph_reaccess_dir,
    graph_persist_only_dir,
    merge_reaccess_dir,
    merge_persist_only_dir,
    final_outputs_merged_dir,
    final_outputs_diagnostics_dir,
    final_outputs_manifests_dir,
    final_outputs_chunk_evidence_dir,
    stage_11_2_dir,
    stage_11_3_dir,
]:
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
        "STEP": 6,
        "CONTEXT_SIZE": 12,
        "OUTPUT_SIZE": 6,
        "ADOPT_SIZE": 6,
        "CHUNKS_PER_BATCH": 2,
        "GLOBAL_CAMERA_SOURCE": "extrinsics_w2c_arc.npy",
        "TARGET_CHUNK_MODE": "selected_chunk_ids_1based",
        "TARGET_CHUNK_IDS_1BASED": [6, 7],
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
INFER_GS = bool(config_snapshot.get("INFER_GS", config.get("INFER_GS", True)))
batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"

TRANSFORM_SCALE_MIN = 0.8
TRANSFORM_SCALE_MAX = 1.3
TRANSFORM_CENTER_RMSE_MAX = 0.15
TRANSFORM_ROT_DIR_MAX = 0.20
ROUTE_ARCORE = "arcore_anchor_baseline"
ROUTE_DA3 = "da3_predicted_primary"
PREFERRED_ROUTE_LABEL = ROUTE_DA3
LOCAL_EXTRINSIC_MODE = "c2w"
LOCAL_CAMERA_BASIS = np.eye(4, dtype=np.float32)
LOCAL_CAMERA_BASIS[:3, :3] = np.array([
    [0.0, 1.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.0, 0.0, -1.0],
], dtype=np.float32)

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
    target_mode = str(config.get("TARGET_CHUNK_MODE", "selected_chunk_ids_1based"))
    if target_mode == "full_set":
        target_chunks_df = base_df.copy().reset_index(drop=True)
    elif target_mode == "selected_chunk_ids_1based":
        valid_chunk_ids = set(base_df["chunk_id"].astype(int).tolist())
        selected_chunk_ids = sorted({int(x) - 1 for x in config.get("TARGET_CHUNK_IDS_1BASED", []) if int(x) >= 1})
        selected_chunk_ids = [x for x in selected_chunk_ids if x in valid_chunk_ids]
        assert selected_chunk_ids, {
            "reason": "selected target chunk ids resolved empty",
            "selected_chunk_ids_1based": config.get("TARGET_CHUNK_IDS_1BASED", []),
            "valid_chunk_ids_0based": sorted(valid_chunk_ids),
        }
        target_chunks_df = base_df.loc[base_df["chunk_id"].astype(int).isin(selected_chunk_ids)].copy()
        target_chunks_df = target_chunks_df.sort_values("chunk_id", kind="stable").reset_index(drop=True)
    elif config.get("USE_TARGET_CHUNK_WINDOW", False):
        start_0 = max(0, int(config.get("TARGET_CHUNK_WINDOW_START_1BASED", 1)) - 1)
        end_0 = min(start_0 + int(config.get("TARGET_CHUNK_WINDOW_COUNT", 3)), len(base_df))
        target_chunks_df = base_df.iloc[start_0:end_0].copy().reset_index(drop=True)
    else:
        raise AssertionError({"reason": "unsupported target chunk mode", "target_mode": target_mode})
    target_chunks_df.to_csv(target_path, index=False, encoding="utf-8")
    return target_chunks_df

def resolve_chunk_output_dir(chunk_name: str) -> Path:
    direct = chunk_runs_dir / chunk_name
    if (direct / "pred_extrinsics.npy").exists() and (direct / "chunk_input_frames.csv").exists():
        return direct

    nested_candidates = sorted({
        p.parent
        for p in chunk_runs_dir.glob(f"batch_*/{chunk_name}/_SUCCESS.json")
    } | {
        p.parent
        for p in chunk_runs_dir.glob(f"batch_*/{chunk_name}/pred_extrinsics.npy")
    } | {
        p.parent
        for p in chunk_runs_dir.glob(f"batch_*/{chunk_name}/chunk_input_frames.csv")
    })
    for candidate in nested_candidates:
        if (candidate / "pred_extrinsics.npy").exists() and (candidate / "chunk_input_frames.csv").exists():
            return candidate

    raise AssertionError({
        "chunk_name": chunk_name,
        "missing_dir": str(direct),
        "reason": "run #7-5 before #14-1",
        "searched_nested_under": str(chunk_runs_dir),
    })

def resolve_chunk_input_dir(chunk_name: str) -> Path:
    return resolve_chunk_output_dir(chunk_name)

all_chunks_df = pd.read_csv(chunk_manifest_dir / "chunk_index_all.csv")
target_chunks_df = ensure_target_chunk_manifest()
completed_chunk_names = []
pred_ready_chunk_names = []
ply_ready_chunk_names = []
for chunk_name in target_chunks_df["chunk_name"].astype(str).tolist():
    try:
        out_dir = resolve_chunk_output_dir(chunk_name)
    except AssertionError:
        continue
    if (out_dir / "_SUCCESS.json").exists():
        completed_chunk_names.append(chunk_name)
    if (out_dir / "pred_extrinsics.npy").exists():
        pred_ready_chunk_names.append(chunk_name)
    if (out_dir / "gs_ply" / "0000.ply").exists():
        ply_ready_chunk_names.append(chunk_name)

completed_chunk_names = sorted(set(completed_chunk_names))
pred_ready_chunk_names = sorted(set(pred_ready_chunk_names))
ply_ready_chunk_names = sorted(set(ply_ready_chunk_names))
completed_chunks_df = target_chunks_df[target_chunks_df["chunk_name"].isin(completed_chunk_names)].copy()
pred_ready_target_chunk_names = sorted(set(pred_ready_chunk_names) & set(target_chunks_df["chunk_name"].tolist()))
ply_ready_target_chunk_names = sorted(set(ply_ready_chunk_names) & set(target_chunks_df["chunk_name"].tolist()))

batch_summaries = sorted({
    str(p) for p in chunk_runs_dir.glob("batch_*/batch_summary.json")
})
summary_rows = [json.loads(Path(p).read_text(encoding="utf-8")) for p in batch_summaries]
all_batch_summary_path = final_outputs_diagnostics_dir / "all_batch_summary_arc.json"
all_batch_summary_path.write_text(json.dumps(summary_rows, indent=2, ensure_ascii=False), encoding="utf-8")
merge_summary_path = final_outputs_diagnostics_dir / "merge_summary.json"
premerge_pose_validation_path = graph_persist_only_dir / "premerge_pose_validation.json"

if not premerge_pose_validation_path.exists():
    merge_summary = {
        "route": "continuous-gs-v07-chunk18-context12-output6-adopt6-merge",
        "status": "skipped",
        "reason": "premerge_pose_validation_required",
        "premerge_pose_validation_path": str(premerge_pose_validation_path),
        "all_batch_summary_path": str(all_batch_summary_path),
    }
    merge_summary_path.write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
    raise AssertionError("run #13-1 pre-merge pose gate before #14-1 merge")

premerge_pose_validation = json.loads(premerge_pose_validation_path.read_text(encoding="utf-8"))
premerge_route_compare_path = graph_persist_only_dir / "premerge_route_compare_summary.json"
prepose_chunk_graph_solution_path = graph_persist_only_dir / "prepose_chunk_graph_solution_arc.csv"
prepose_chunk_graph_summary_path = graph_persist_only_dir / "prepose_chunk_graph_summary.json"
premerge_validation_csv_path = graph_persist_only_dir / "premerge_pose_validation.csv"
allowed_premerge_status = {"ok", "warning"}
if str(premerge_pose_validation.get("status")) not in allowed_premerge_status:
    merge_summary = {
        "route": "continuous-gs-v07-chunk18-context12-output6-adopt6-merge",
        "status": "skipped",
        "reason": "premerge_pose_validation_failed",
        "premerge_pose_validation_path": str(premerge_pose_validation_path),
        "premerge_route_compare_path": str(premerge_route_compare_path) if premerge_route_compare_path.exists() else None,
        "prepose_chunk_graph_solution_path": str(prepose_chunk_graph_solution_path) if prepose_chunk_graph_solution_path.exists() else None,
        "hard_fail_count": int(premerge_pose_validation.get("hard_fail_count", 0)),
        "failed_chunks": premerge_pose_validation.get("failed_chunks", []),
        "all_batch_summary_path": str(all_batch_summary_path),
    }
    merge_summary_path.write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
    raise AssertionError(premerge_pose_validation)

if REQUIRE_ALL_CHUNKS and len(completed_chunks_df) < len(target_chunks_df):
    merge_summary = {
        "route": "continuous-gs-v07-chunk18-context12-output6-adopt6-merge",
        "status": "skipped",
        "reason": "waiting_for_all_chunks",
        "completed_chunk_count": int(len(completed_chunks_df)),
        "pred_ready_chunk_count": int(len(pred_ready_target_chunk_names)),
        "ply_ready_chunk_count": int(len(ply_ready_target_chunk_names)),
        "all_chunk_count": int(len(target_chunks_df)),
        "all_batch_summary_path": str(all_batch_summary_path),
    }
    merge_summary_path.write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
elif INFER_GS and len(ply_ready_target_chunk_names) < len(target_chunks_df):
    merge_summary = {
        "route": "continuous-gs-v07-chunk18-context12-output6-adopt6-merge",
        "status": "skipped",
        "reason": "gaussian_chunk_outputs_missing",
        "completed_chunk_count": int(len(completed_chunks_df)),
        "pred_ready_chunk_count": int(len(pred_ready_target_chunk_names)),
        "ply_ready_chunk_count": int(len(ply_ready_target_chunk_names)),
        "all_chunk_count": int(len(target_chunks_df)),
        "infer_gs": bool(INFER_GS),
        "all_batch_summary_path": str(all_batch_summary_path),
    }
    merge_summary_path.write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
else:
    global_centers_df = pd.read_csv(anchor_dir / "camera_center_matrix_arc.csv")
    global_camera_matrix_df = pd.read_csv(anchor_dir / "camera_matrix_full_arc.csv")
    global_anchor_df = pd.read_csv(anchor_dir / "camera_anchor_full_arc.csv")
    premerge_validation_df = (
        pd.read_csv(premerge_validation_csv_path)
        if premerge_validation_csv_path.exists() and premerge_validation_csv_path.stat().st_size > 0
        else pd.DataFrame()
    )
    prepose_graph_solution_df = (
        pd.read_csv(prepose_chunk_graph_solution_path)
        if prepose_chunk_graph_solution_path.exists() and prepose_chunk_graph_solution_path.stat().st_size > 0
        else pd.DataFrame()
    )
    selected_route_by_chunk = dict(zip(
        premerge_validation_df["chunk_name"].astype(str),
        premerge_validation_df["route_label"].astype(str),
    )) if len(premerge_validation_df) else {}
    prepose_graph_solution_by_chunk = {
        str(row["chunk_name"]): row.to_dict()
        for _, row in prepose_graph_solution_df.iterrows()
    } if len(prepose_graph_solution_df) else {}
    input_manifest_path = manifest_dir / "da3_input_manifest.csv"
    assert input_manifest_path.exists(), input_manifest_path
    input_manifest_df = pd.read_csv(input_manifest_path)
    if "cx_world" not in global_anchor_df.columns and "cam_cx" in global_anchor_df.columns:
        global_anchor_df["cx_world"] = global_anchor_df["cam_cx"]
        global_anchor_df["cy_world"] = global_anchor_df["cam_cy"]
        global_anchor_df["cz_world"] = global_anchor_df["cam_cz"]
    if "anchor_lens_x" not in global_anchor_df.columns and "lens_x" in global_anchor_df.columns:
        global_anchor_df["anchor_lens_x"] = global_anchor_df["lens_x"]
        global_anchor_df["anchor_lens_y"] = global_anchor_df["lens_y"]
        global_anchor_df["anchor_lens_z"] = global_anchor_df["lens_z"]
    if "anchor_up_x" not in global_anchor_df.columns and "up_x" in global_anchor_df.columns:
        global_anchor_df["anchor_up_x"] = global_anchor_df["up_x"]
        global_anchor_df["anchor_up_y"] = global_anchor_df["up_y"]
        global_anchor_df["anchor_up_z"] = global_anchor_df["up_z"]
    if "record_index" not in global_camera_matrix_df.columns and {"sequence_index", "record_index"}.issubset(global_anchor_df.columns):
        global_camera_matrix_df = global_camera_matrix_df.merge(
            global_anchor_df[["sequence_index", "record_index"]].drop_duplicates(),
            on="sequence_index",
            how="left",
            validate="many_to_one",
        )
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
        m_cols = [f"m{i}{j}" for i in range(4) for j in range(4)]
        w2c_cols = [f"w2c_{i}{j}" for i in range(4) for j in range(4)]
        use_m_cols = all(c in df.columns for c in m_cols)
        use_w2c_cols = all(c in df.columns for c in w2c_cols)
        assert use_m_cols or use_w2c_cols, {
            "reason": "camera matrix cols not found",
            "available_columns": df.columns.tolist(),
        }
        for row in df.itertuples(index=False):
            if use_m_cols:
                M = np.array([getattr(row, c) for c in m_cols], dtype=np.float32).reshape(4, 4)
                out[int(row.record_index)] = M
            else:
                w2c = np.array([getattr(row, c) for c in w2c_cols], dtype=np.float32).reshape(4, 4)
                out[int(row.record_index)] = np.linalg.inv(w2c).astype(np.float32)
        return out

    def normalize_rows(arr: np.ndarray, eps: float = 1e-12) -> np.ndarray:
        arr = np.asarray(arr, dtype=np.float64)
        arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
        norm = np.linalg.norm(arr, axis=1, keepdims=True)
        return arr / np.maximum(norm, eps)

    def summarize_split_metrics(values: np.ndarray, overlap_mask: np.ndarray, prefix: str) -> dict:
        values = np.asarray(values, dtype=np.float64)
        overlap_mask = np.asarray(overlap_mask, dtype=bool)
        nonoverlap_mask = ~overlap_mask

        def pack(mask: np.ndarray, label: str) -> dict:
            count = int(mask.sum())
            base = {
                f"{prefix}_{label}_count": count,
                f"{prefix}_{label}_mean": None,
                f"{prefix}_{label}_p95": None,
                f"{prefix}_{label}_max": None,
            }
            if count <= 0:
                return base
            subset = values[mask]
            base[f"{prefix}_{label}_mean"] = float(subset.mean())
            base[f"{prefix}_{label}_p95"] = float(np.quantile(subset, 0.95))
            base[f"{prefix}_{label}_max"] = float(subset.max())
            return base

        out = {}
        out.update(pack(overlap_mask, "overlap"))
        out.update(pack(nonoverlap_mask, "nonoverlap"))
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
            raw = to_4x4(ext).astype(np.float32)
            if LOCAL_EXTRINSIC_MODE == "c2w":
                c2w = raw
            elif LOCAL_EXTRINSIC_MODE == "w2c":
                c2w = np.linalg.inv(raw).astype(np.float32)
            else:
                raise AssertionError({
                    "reason": "unsupported_local_extrinsic_mode",
                    "LOCAL_EXTRINSIC_MODE": LOCAL_EXTRINSIC_MODE,
                })
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

    def transform_c2w_list(c2w_list, T):
        out = []
        for c2w in c2w_list:
            M = np.asarray(c2w, dtype=np.float64).copy()
            M[:3, :3] = T[:3, :3] @ M[:3, :3]
            M[:3, 3] = T[:3, :3] @ M[:3, 3] + T[:3, 3]
            out.append(M.astype(np.float32))
        return out


    def c2w_to_w2c(c2w: np.ndarray) -> np.ndarray:
        return np.linalg.inv(np.asarray(c2w, dtype=np.float64)).astype(np.float32)


    def pose_row_from_c2w(chunk_name: str, local_index: int, chunk_row: pd.Series, c2w: np.ndarray) -> dict:
        c2w = np.asarray(c2w, dtype=np.float32)
        w2c = c2w_to_w2c(c2w)
        center = c2w[:3, 3]
        lens = lens_direction_from_c2w(c2w)
        up = up_direction_from_c2w(c2w)
        row = {
            "chunk_name": str(chunk_name),
            "local_index": int(local_index),
            "record_index": int(chunk_row["record_index"]) if "record_index" in chunk_row.index and pd.notna(chunk_row["record_index"]) else None,
            "sequence_index": int(chunk_row["sequence_index"]) if "sequence_index" in chunk_row.index and pd.notna(chunk_row["sequence_index"]) else None,
            "frame_timestamp_ns": int(chunk_row["frame_timestamp_ns"]) if "frame_timestamp_ns" in chunk_row.index and pd.notna(chunk_row["frame_timestamp_ns"]) else None,
            "capture_timestamp_ns": int(chunk_row["capture_timestamp_ns"]) if "capture_timestamp_ns" in chunk_row.index and pd.notna(chunk_row["capture_timestamp_ns"]) else None,
            "image_file_name": str(chunk_row["image_file_name"]) if "image_file_name" in chunk_row.index and pd.notna(chunk_row["image_file_name"]) else None,
            "image_path": str(chunk_row["image_path"]) if "image_path" in chunk_row.index and pd.notna(chunk_row["image_path"]) else None,
            "cx_world": float(center[0]),
            "cy_world": float(center[1]),
            "cz_world": float(center[2]),
            "anchor_lens_x": float(lens[0]),
            "anchor_lens_y": float(lens[1]),
            "anchor_lens_z": float(lens[2]),
            "anchor_up_x": float(up[0]),
            "anchor_up_y": float(up[1]),
            "anchor_up_z": float(up[2]),
        }
        for r in range(4):
            for c in range(4):
                row[f"m{r}{c}"] = float(c2w[r, c])
                row[f"w2c_{r}{c}"] = float(w2c[r, c])
        return row


    def dedupe_integrated_pose_df(df: pd.DataFrame) -> pd.DataFrame:
        if len(df) == 0:
            return df.copy()
        out = df.copy()
        order_cols = [c for c in ["record_index", "sequence_index", "frame_timestamp_ns", "chunk_name", "local_index"] if c in out.columns]
        if order_cols:
            out = out.sort_values(order_cols, kind="stable")
        if "record_index" in out.columns and out["record_index"].notna().any():
            out = out.drop_duplicates(["record_index"], keep="first")
        elif "sequence_index" in out.columns and out["sequence_index"].notna().any():
            out = out.drop_duplicates(["sequence_index"], keep="first")
        elif "frame_timestamp_ns" in out.columns and out["frame_timestamp_ns"].notna().any():
            out = out.drop_duplicates(["frame_timestamp_ns"], keep="first")
        return out.reset_index(drop=True)

    def has_detailed_prepose_solution(solution: dict | None) -> bool:
        if not solution:
            return False
        required = [
            "route_label",
            "route_source",
            "scale",
            "rotation_det",
            "center_rmse",
            "rotation_dir_residual",
        ]
        return all(k in solution and pd.notna(solution[k]) for k in required)

    def summarize_route_candidate(chunk_name: str, route_label: str, route_source: str, route_overlap_record_count: int, overlap_record_indices: list[int], transformed_rows, anchor_rows, align_diag: dict) -> dict:
        pred_center = np.stack([m[:3, 3] for m in transformed_rows], axis=0)
        pred_lens = np.stack([lens_direction_from_c2w(m) for m in transformed_rows], axis=0)
        anchor_center = anchor_rows[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32)
        anchor_lens = anchor_rows[["anchor_lens_x", "anchor_lens_y", "anchor_lens_z"]].to_numpy(dtype=np.float32)
        record_indices = anchor_rows["record_index"].astype(int).to_numpy()
        overlap_index_set = {int(x) for x in overlap_record_indices}
        overlap_mask = np.array([int(x) in overlap_index_set for x in record_indices], dtype=bool)
        center_error = np.linalg.norm(pred_center - anchor_center, axis=1)
        lens_error_deg = np.degrees(np.arccos(np.clip(np.sum(normalize_rows(pred_lens) * normalize_rows(anchor_lens), axis=1), -1.0, 1.0)))
        out = {
            "chunk_name": chunk_name,
            "route_label": route_label,
            "route_source": route_source,
            "route_overlap_record_count": int(route_overlap_record_count),
            "route_overlap_local_count": int(overlap_mask.sum()),
            "route_nonoverlap_local_count": int((~overlap_mask).sum()),
            "scale": float(align_diag["scale"]),
            "rotation_det": float(align_diag["rotation_det"]),
            "center_rmse": float(align_diag["center_rmse"]),
            "rotation_dir_residual": float(align_diag["rotation_dir_residual"]),
            "positive_similarity_ok": bool(align_diag["positive_similarity_ok"]),
            "scale_in_range_ok": bool(align_diag["scale_in_range_ok"]),
            "center_rmse_ok": bool(align_diag["center_rmse_ok"]),
            "rotation_dir_ok": bool(align_diag["rotation_dir_ok"]),
            "hard_fail": bool(align_diag["hard_fail"]),
            "center_error_mean": float(center_error.mean()),
            "center_error_p95": float(np.quantile(center_error, 0.95)),
            "lens_error_deg_mean": float(lens_error_deg.mean()),
            "lens_error_deg_p95": float(np.quantile(lens_error_deg, 0.95)),
        }
        out.update(summarize_split_metrics(center_error, overlap_mask, "center_error"))
        out.update(summarize_split_metrics(lens_error_deg, overlap_mask, "lens_error_deg"))
        return out

    def select_route_candidate(chunk_name: str, candidate_rows: list[dict], requested_route_label: str) -> tuple[dict, bool]:
        by_label = {c["route_label"]: c for c in candidate_rows}
        requested = by_label.get(requested_route_label)
        preferred = by_label.get(PREFERRED_ROUTE_LABEL)
        baseline = by_label.get(ROUTE_ARCORE)
        if requested is not None and not requested["hard_fail"]:
            selected = requested
        elif preferred is not None and not preferred["hard_fail"]:
            selected = preferred
        elif baseline is not None and not baseline["hard_fail"]:
            selected = baseline
        elif requested is not None:
            selected = requested
        elif preferred is not None:
            selected = preferred
        elif baseline is not None:
            selected = baseline
        else:
            raise AssertionError({"chunk_name": chunk_name, "reason": "no route candidates"})
        fallback_used = bool(selected["route_label"] != requested_route_label)
        return selected, fallback_used

    global_camera_map = c2w_rows_to_map(global_camera_matrix_df)
    if "qc_blur_ok" not in input_manifest_df.columns:
        input_manifest_df["qc_blur_ok"] = False
    if "blur_score" not in input_manifest_df.columns:
        input_manifest_df["blur_score"] = 0.0
    global_frame_meta_df = global_anchor_df.merge(
        input_manifest_df[["record_index", "qc_blur_ok", "blur_score"]],
        on="record_index",
        how="left",
    )
    if "qc_blur_ok" not in global_frame_meta_df.columns:
        qc_blur_candidates = [c for c in ["qc_blur_ok_x", "qc_blur_ok_y"] if c in global_frame_meta_df.columns]
        if qc_blur_candidates:
            global_frame_meta_df["qc_blur_ok"] = global_frame_meta_df[qc_blur_candidates].bfill(axis=1).iloc[:, 0]
    if "blur_score" not in global_frame_meta_df.columns:
        blur_score_candidates = [c for c in ["blur_score_x", "blur_score_y"] if c in global_frame_meta_df.columns]
        if blur_score_candidates:
            global_frame_meta_df["blur_score"] = global_frame_meta_df[blur_score_candidates].bfill(axis=1).iloc[:, 0]
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
    experimental_world_pose_map = {}
    route_compare_rows = []
    integrated_pose_rows = []
    previous_selected_chunk_name = None
    previous_selected_T = None

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

        anchor_join_cols = ["record_index", "image_file_name", "image_path", "frame_timestamp_ns", "capture_timestamp_ns"]
        anchor_value_cols = ["cx_world", "cy_world", "cz_world", "anchor_lens_x", "anchor_lens_y", "anchor_lens_z", "anchor_up_x", "anchor_up_y", "anchor_up_z"]
        chunk_merge_df = chunk_df.drop(columns=[c for c in anchor_value_cols if c in chunk_df.columns], errors="ignore")
        anchor_merge_df = global_anchor_df[anchor_join_cols + anchor_value_cols].copy()
        merged = chunk_merge_df.merge(
            anchor_merge_df,
            on=anchor_join_cols,
            how="left",
            validate="one_to_one",
        )
        assert len(merged) == len(chunk_df), {"chunk_name": row.chunk_name, "merged_len": len(merged), "chunk_len": len(chunk_df)}
        assert not merged[anchor_value_cols].isnull().any().any(), f"global anchor missing: {row.chunk_name}"
        global_c2w_list = [build_anchor_c2w(global_camera_map[int(rec.record_index)], rec) for rec in merged.itertuples(index=False)]

        prepose_solution = prepose_graph_solution_by_chunk.get(str(row.chunk_name))
        if has_detailed_prepose_solution(prepose_solution):
            requested_route_label = str(prepose_solution.get("requested_route_label", prepose_solution.get("route_label", PREFERRED_ROUTE_LABEL)))
            selected_candidate = dict(prepose_solution)
            fallback_used = bool(prepose_solution.get("fallback_used", False))
            preferred_fallback_used = bool(prepose_solution.get("preferred_fallback_used", False))
            graph_parent_chunk_name = prepose_solution.get("graph_parent_chunk_name")
            T_c_to_w0 = np.array(
                [float(prepose_solution[f"t{r}{c}"]) for r in range(4) for c in range(4)],
                dtype=np.float32,
            ).reshape(4, 4)
            align_diag = {
                "scale": float(prepose_solution["scale"]),
                "rotation_det": float(prepose_solution["rotation_det"]),
                "center_rmse": float(prepose_solution["center_rmse"]),
                "rotation_dir_residual": float(prepose_solution["rotation_dir_residual"]),
                "positive_similarity_ok": bool(prepose_solution["positive_similarity_ok"]),
                "scale_in_range_ok": bool(prepose_solution["scale_in_range_ok"]),
                "center_rmse_ok": bool(prepose_solution["center_rmse_ok"]),
                "rotation_dir_ok": bool(prepose_solution["rotation_dir_ok"]),
                "hard_fail": bool(prepose_solution.get("align_hard_fail", prepose_solution.get("hard_fail", False))),
            }
            selected_world_rows = transform_c2w_list(local_c2w_list, T_c_to_w0)
            route_compare_rows.append({
                "chunk_name": str(row.chunk_name),
                "graph_parent_chunk_name": graph_parent_chunk_name,
                "route_label": str(prepose_solution["route_label"]),
                "requested_route_label": requested_route_label,
                "preferred_route_label": PREFERRED_ROUTE_LABEL,
                "fallback_used": fallback_used,
                "preferred_fallback_used": preferred_fallback_used,
                "route_source": str(prepose_solution["route_source"]),
                "route_overlap_record_count": int(prepose_solution.get("route_overlap_record_count", 0)),
                "route_overlap_local_count": int(prepose_solution.get("route_overlap_local_count", 0)),
                "route_nonoverlap_local_count": int(prepose_solution.get("route_nonoverlap_local_count", 0)),
                "center_rmse": float(prepose_solution["center_rmse"]),
                "rotation_dir_residual": float(prepose_solution["rotation_dir_residual"]),
                "center_error_p95": float(prepose_solution["center_error_p95"]),
                "lens_error_deg_p95": float(prepose_solution["lens_error_deg_p95"]),
                "center_error_overlap_p95": prepose_solution.get("center_error_overlap_p95"),
                "center_error_nonoverlap_p95": prepose_solution.get("center_error_nonoverlap_p95"),
                "lens_error_deg_overlap_p95": prepose_solution.get("lens_error_deg_overlap_p95"),
                "lens_error_deg_nonoverlap_p95": prepose_solution.get("lens_error_deg_nonoverlap_p95"),
                "relative_scale": prepose_solution.get("relative_scale"),
                "relative_translation_norm": prepose_solution.get("relative_translation_norm"),
                "relative_rotation_deg": prepose_solution.get("relative_rotation_deg"),
                "selected_from_prepose_graph": True,
            })
        else:
            graph_parent_chunk_name = previous_selected_chunk_name
            baseline_T, baseline_diag = estimate_pose_aware_similarity(local_c2w_list, global_c2w_list, estimate_scale=True)
            baseline_world_rows = transform_c2w_list(local_c2w_list, baseline_T)
            baseline_candidate = summarize_route_candidate(
                row.chunk_name,
                ROUTE_ARCORE,
                "anchor_full_sequence",
                len(merged),
                merged["record_index"].astype(int).tolist(),
                baseline_world_rows,
                merged,
                baseline_diag,
            )
            route_compare_rows.append(baseline_candidate)

            overlap_local_rows = []
            overlap_world_rows = []
            overlap_record_indices = []
            for idx, record_index in enumerate(merged["record_index"].astype(int).tolist()):
                if record_index in experimental_world_pose_map:
                    overlap_local_rows.append(local_c2w_list[idx])
                    overlap_world_rows.append(experimental_world_pose_map[record_index])
                    overlap_record_indices.append(int(record_index))

            if overlap_world_rows:
                experimental_source = "predicted_overlap"
                experimental_overlap_record_count = len(overlap_world_rows)
                if len(overlap_world_rows) >= 2:
                    experimental_T, experimental_diag = estimate_pose_aware_similarity(overlap_local_rows, overlap_world_rows, estimate_scale=True)
                else:
                    experimental_T = baseline_T.copy()
                    experimental_diag = dict(baseline_diag)
                    experimental_source = "predicted_overlap_seeded_single_record"
            else:
                experimental_source = "seed_from_arcore_baseline"
                experimental_overlap_record_count = 0
                experimental_T = baseline_T.copy()
                experimental_diag = dict(baseline_diag)

            experimental_world_rows = transform_c2w_list(local_c2w_list, experimental_T)
            experimental_candidate = summarize_route_candidate(
                row.chunk_name,
                ROUTE_DA3,
                experimental_source,
                experimental_overlap_record_count,
                overlap_record_indices,
                experimental_world_rows,
                merged,
                experimental_diag,
            )
            route_compare_rows.append(experimental_candidate)

            requested_route_label = str(selected_route_by_chunk.get(row.chunk_name, PREFERRED_ROUTE_LABEL))
            selected_candidate, fallback_used = select_route_candidate(
                row.chunk_name,
                [baseline_candidate, experimental_candidate],
                requested_route_label,
            )
            preferred_fallback_used = bool(selected_candidate["route_label"] != PREFERRED_ROUTE_LABEL)
            selected_world_rows = experimental_world_rows if selected_candidate["route_label"] == ROUTE_DA3 else baseline_world_rows
            align_diag = experimental_diag if selected_candidate["route_label"] == ROUTE_DA3 else baseline_diag
            T_c_to_w0 = experimental_T if selected_candidate["route_label"] == ROUTE_DA3 else baseline_T

        for record_index, world_pose in zip(merged["record_index"].astype(int).tolist(), selected_world_rows):
            experimental_world_pose_map[int(record_index)] = world_pose

        relative_transform = summarize_relative_transform(previous_selected_T, T_c_to_w0)

        T_path = chunk_manifest_dir / f"{row.chunk_name}_to_w0.npy"
        np.save(T_path, T_c_to_w0)
        transform_rows.append({
            "chunk_name": row.chunk_name,
            "frame_count": int(len(chunk_df)),
            "transform_path": str(T_path),
            "graph_parent_chunk_name": graph_parent_chunk_name,
            "route_label": str(selected_candidate["route_label"]),
            "requested_route_label": requested_route_label,
            "preferred_route_label": PREFERRED_ROUTE_LABEL,
            "fallback_used": bool(fallback_used),
            "preferred_fallback_used": preferred_fallback_used,
            "route_source": str(selected_candidate["route_source"]),
            "route_overlap_record_count": int(selected_candidate["route_overlap_record_count"]),
            "route_overlap_local_count": int(selected_candidate.get("route_overlap_local_count", 0)),
            "route_nonoverlap_local_count": int(selected_candidate.get("route_nonoverlap_local_count", 0)),
            "local_extrinsic_mode": LOCAL_EXTRINSIC_MODE,
            "local_camera_basis": "perm_yxz_sign_ppn",
            "scale": float(align_diag["scale"]),
            "rotation_det": float(align_diag["rotation_det"]),
            "center_rmse": float(align_diag["center_rmse"]),
            "rotation_dir_residual": float(align_diag["rotation_dir_residual"]),
            "relative_scale": float(relative_transform["relative_scale"]),
            "relative_translation_norm": float(relative_transform["relative_translation_norm"]),
            "relative_rotation_deg": float(relative_transform["relative_rotation_deg"]),
            "positive_similarity_ok": bool(align_diag["positive_similarity_ok"]),
            "scale_in_range_ok": bool(align_diag["scale_in_range_ok"]),
            "center_rmse_ok": bool(align_diag["center_rmse_ok"]),
            "rotation_dir_ok": bool(align_diag["rotation_dir_ok"]),
            "hard_fail": bool(align_diag["hard_fail"]),
            "center_error_p95": float(selected_candidate["center_error_p95"]),
            "lens_error_deg_p95": float(selected_candidate["lens_error_deg_p95"]),
            "center_error_overlap_p95": selected_candidate.get("center_error_overlap_p95"),
            "center_error_nonoverlap_p95": selected_candidate.get("center_error_nonoverlap_p95"),
            "lens_error_deg_overlap_p95": selected_candidate.get("lens_error_deg_overlap_p95"),
            "lens_error_deg_nonoverlap_p95": selected_candidate.get("lens_error_deg_nonoverlap_p95"),
        })
        assert not align_diag["hard_fail"], {
            "chunk_name": row.chunk_name,
            "reason": "invalid_pose_similarity",
            "selected_route_label": selected_candidate["route_label"],
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
            "route_label": str(selected_candidate["route_label"]),
            "transform_warning": transform_warning,
            "keep_zero_chunk": keep_zero_chunk,
            "fallback_used": bool(fallback_used),
            "preferred_fallback_used": preferred_fallback_used,
        })
        keep_rows.append({
            "chunk_name": row.chunk_name,
            "route_label": str(selected_candidate["route_label"]),
            "requested_route_label": requested_route_label,
            "fallback_used": bool(fallback_used),
            "preferred_fallback_used": preferred_fallback_used,
            "kept_vertices": int(len(df)),
            "owner_record_unique_count": int(assignment_df["owner_record_index"].nunique()),
            "owner_candidate_mode": str(assignment_df["owner_candidate_mode"].iloc[0]),
            "owner_record_min": int(assignment_df["owner_record_index"].min()),
            "owner_record_max": int(assignment_df["owner_record_index"].max()),
            "owner_blur_ok_ratio": float(assignment_df["owner_blur_ok"].mean()),
            "owner_score_mean": float(assignment_df["owner_score"].mean()),
        })
        assert not keep_zero_chunk, {"chunk_name": row.chunk_name, "reason": "keep_zero_chunk"}
        previous_selected_chunk_name = str(row.chunk_name)
        previous_selected_T = T_c_to_w0.copy()

        if glb_path.exists():
            scene = load_scene_any(glb_path)
            for gname, geom in iter_baked_scene_geometry(scene):
                geom2 = geom.copy() if hasattr(geom, "copy") else geom
                if hasattr(geom2, "apply_transform"):
                    geom2.apply_transform(T_c_to_w0)
                master_scene.add_geometry(geom2, node_name=f"{row.chunk_name}_{gname}")


transform_df = pd.DataFrame(transform_rows)
transform_df.to_csv(chunk_manifest_dir / "chunk_global_transforms_arc.csv", index=False, encoding="utf-8")

integrated_pose_df = dedupe_integrated_pose_df(pd.DataFrame(integrated_pose_rows))
merged_camera_pose_csv = final_outputs_diagnostics_dir / "merged_camera_pose_arc.csv"
merged_camera_matrix_csv = final_outputs_diagnostics_dir / "merged_camera_matrix_arc.csv"
merged_camera_c2w_npy = final_outputs_diagnostics_dir / "merged_camera_c2w_arc.npy"
merged_camera_w2c_npy = final_outputs_diagnostics_dir / "merged_extrinsics_w2c_arc.npy"
ngl_bundle_dir = final_outputs_merged_dir / "ngl_camera_bundle"
ngl_bundle_manifest_dir = ngl_bundle_dir / "manifests"
ngl_bundle_manifest_dir.mkdir(parents=True, exist_ok=True)
ngl_input_manifest_path = ngl_bundle_manifest_dir / "da3_input_manifest.csv"
ngl_intrinsics_path = ngl_bundle_manifest_dir / "intrinsics.npy"
ngl_extrinsics_path = ngl_bundle_manifest_dir / "extrinsics_w2c_arc.npy"
ngl_pose_summary_path = ngl_bundle_dir / "ngl_pose_bundle_summary.json"

if len(integrated_pose_df):
    integrated_pose_df.to_csv(merged_camera_pose_csv, index=False, encoding="utf-8")
    mat_cols = ["chunk_name", "record_index", "sequence_index", "frame_timestamp_ns", "capture_timestamp_ns", "image_file_name", "image_path"] + [f"m{r}{c}" for r in range(4) for c in range(4)] + [f"w2c_{r}{c}" for r in range(4) for c in range(4)]
    integrated_pose_df[[c for c in mat_cols if c in integrated_pose_df.columns]].to_csv(merged_camera_matrix_csv, index=False, encoding="utf-8")
    c2w_arr = integrated_pose_df[[f"m{r}{c}" for r in range(4) for c in range(4)]].to_numpy(dtype=np.float32).reshape(-1, 4, 4)
    w2c_arr = integrated_pose_df[[f"w2c_{r}{c}" for r in range(4) for c in range(4)]].to_numpy(dtype=np.float32).reshape(-1, 4, 4)
    np.save(merged_camera_c2w_npy, c2w_arr)
    np.save(merged_camera_w2c_npy, w2c_arr)

    if "record_index" in integrated_pose_df.columns and integrated_pose_df["record_index"].notna().any() and "record_index" in input_manifest_df.columns:
        ngl_manifest_df = integrated_pose_df[["record_index"]].dropna().copy()
        ngl_manifest_df["record_index"] = ngl_manifest_df["record_index"].astype(int)
        ngl_manifest_df = ngl_manifest_df.merge(input_manifest_df, on="record_index", how="left", validate="one_to_one")
        if "sequence_index" in integrated_pose_df.columns:
            seq_map_df = integrated_pose_df[[c for c in ["record_index", "sequence_index"] if c in integrated_pose_df.columns]].drop_duplicates("record_index")
            ngl_manifest_df = ngl_manifest_df.merge(seq_map_df, on="record_index", how="left")
        if "sequence_index" in ngl_manifest_df.columns and ngl_manifest_df["sequence_index"].notna().any():
            ngl_manifest_df = ngl_manifest_df.sort_values(["sequence_index", "record_index"], kind="stable")
        else:
            ngl_manifest_df = ngl_manifest_df.sort_values(["record_index"], kind="stable")
    else:
        ngl_manifest_df = input_manifest_df.copy().iloc[:len(integrated_pose_df)].reset_index(drop=True)
    ngl_manifest_df.to_csv(ngl_input_manifest_path, index=False, encoding="utf-8")
    if (manifest_dir / "intrinsics.npy").exists():
        shutil.copy2(manifest_dir / "intrinsics.npy", ngl_intrinsics_path)
    np.save(ngl_extrinsics_path, w2c_arr)
    ngl_pose_bundle_summary = {
        "status": "ok",
        "pose_row_count": int(len(integrated_pose_df)),
        "ngl_bundle_dir": str(ngl_bundle_dir),
        "da3_input_manifest_csv": str(ngl_input_manifest_path),
        "intrinsics_npy": str(ngl_intrinsics_path) if ngl_intrinsics_path.exists() else None,
        "extrinsics_w2c_npy": str(ngl_extrinsics_path),
        "merged_camera_pose_csv": str(merged_camera_pose_csv),
        "merged_camera_matrix_csv": str(merged_camera_matrix_csv),
        "merged_camera_c2w_npy": str(merged_camera_c2w_npy),
        "merged_camera_w2c_npy": str(merged_camera_w2c_npy),
    }
else:
    pd.DataFrame(columns=["chunk_name", "record_index", "sequence_index"]).to_csv(merged_camera_pose_csv, index=False, encoding="utf-8")
    pd.DataFrame().to_csv(merged_camera_matrix_csv, index=False, encoding="utf-8")
    ngl_pose_bundle_summary = {
        "status": "skipped",
        "reason": "integrated_pose_rows_empty",
        "ngl_bundle_dir": str(ngl_bundle_dir),
        "merged_camera_pose_csv": str(merged_camera_pose_csv),
        "merged_camera_matrix_csv": str(merged_camera_matrix_csv),
    }
    save_json(ngl_pose_summary_path, ngl_pose_bundle_summary)

    route_compare_df = pd.DataFrame(route_compare_rows)
    route_compare_path = final_outputs_diagnostics_dir / "merge_route_compare_arc.csv"
    route_compare_df.to_csv(route_compare_path, index=False, encoding="utf-8")

    keep_df = pd.DataFrame(keep_rows)
    keep_summary_path = final_outputs_diagnostics_dir / "chunk_keep_summary_arc.csv"
    keep_df.to_csv(keep_summary_path, index=False, encoding="utf-8")
    transform_quality_path = final_outputs_diagnostics_dir / "chunk_transform_quality_arc.csv"
    transform_df.to_csv(transform_quality_path, index=False, encoding="utf-8")

    if owner_hist_rows:
        pd.concat(owner_hist_rows, ignore_index=True).to_csv(final_outputs_diagnostics_dir / "owner_record_histogram_arc.csv", index=False, encoding="utf-8")
    if chunk_assign_rows:
        pd.concat(chunk_assign_rows, ignore_index=True).to_csv(final_outputs_diagnostics_dir / "chunk_assignment_summary_arc.csv", index=False, encoding="utf-8")

    warning_summary = {
        "transform_warning_count": int(sum(bool(x["transform_warning"]) for x in warning_rows)),
        "keep_zero_chunk_count": int(sum(bool(x["keep_zero_chunk"]) for x in warning_rows)),
        "fallback_used_count": int(sum(bool(x["fallback_used"]) for x in warning_rows)),
        "preferred_fallback_used_count": int(sum(bool(x.get("preferred_fallback_used")) for x in warning_rows)),
        "rows": warning_rows,
    }
    (final_outputs_diagnostics_dir / "merge_warning_summary_arc.json").write_text(json.dumps(warning_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    merged_ply_path = merged_dir / "merged_gs_arc.ply"
    if all_vertices:
        merged_vertices = np.concatenate(all_vertices, axis=0)
        PlyData([PlyElement.describe(merged_vertices, "vertex")], text=False).write(str(merged_ply_path))

    merged_glb_path = final_outputs_merged_dir / "merged_scene_arc.glb"
    if len(master_scene.geometry) > 0:
        master_scene.export(str(merged_glb_path))

    stage_11_2_entries = [
        {"label": "merged_gs_arc.ply", "path": str(merged_ply_path)},
        {"label": "chunk_global_transforms_arc.csv", "path": str(chunk_manifest_dir / "chunk_global_transforms_arc.csv")},
        {"label": "merge_route_compare_arc.csv", "path": str(route_compare_path)},
        {"label": "chunk_keep_summary_arc.csv", "path": str(keep_summary_path)},
        {"label": "chunk_transform_quality_arc.csv", "path": str(transform_quality_path)},
        {"label": "owner_record_histogram_arc.csv", "path": str(final_outputs_diagnostics_dir / "owner_record_histogram_arc.csv")},
        {"label": "chunk_assignment_summary_arc.csv", "path": str(final_outputs_diagnostics_dir / "chunk_assignment_summary_arc.csv")},
        {"label": "merge_warning_summary_arc.json", "path": str(final_outputs_diagnostics_dir / "merge_warning_summary_arc.json")},
        {"label": "all_batch_summary_arc.json", "path": str(all_batch_summary_path)},
        {"label": "merged_camera_pose_arc.csv", "path": str(merged_camera_pose_csv)},
        {"label": "merged_camera_matrix_arc.csv", "path": str(merged_camera_matrix_csv)},
        {"label": "merged_camera_c2w_arc.npy", "path": str(merged_camera_c2w_npy)},
        {"label": "merged_extrinsics_w2c_arc.npy", "path": str(merged_camera_w2c_npy)},
        {"label": "ngl_pose_bundle_summary.json", "path": str(ngl_bundle_dir / "ngl_pose_bundle_summary.json")},
    ]
    stage_11_2_entries = [entry for entry in stage_11_2_entries if Path(entry["path"]).exists()]
    stage_11_2_manifest = {
        "stage": "#11-2",
        "handoff_role": "review_inputs",
        "canonical_root": str(merge_persist_only_dir),
        "entries": stage_11_2_entries,
    }
    stage_11_2_manifest_path.write_text(json.dumps(stage_11_2_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    merge_resume_state = {
        "route": "continuous-gs-v07-chunk18-context12-output6-adopt6-merge",
        "stage": "11-2-complete",
        "completed_chunk_count": int(len(completed_chunks_df)),
        "all_chunk_count": int(len(target_chunks_df)),
        "stage_11_2_dir": str(stage_11_2_dir),
        "stage_11_2_manifest_path": str(stage_11_2_manifest_path),
        "merged_ply_path": str(merged_ply_path) if merged_ply_path.exists() else None,
    }
    merge_resume_state_path.write_text(json.dumps(merge_resume_state, indent=2, ensure_ascii=False), encoding="utf-8")

    stage_11_3_entries = list(stage_11_2_entries)
    if merged_glb_path.exists():
        stage_11_3_entries.append({"label": "merged_scene_arc.glb", "path": str(merged_glb_path)})
    stage_11_3_entries.append({"label": "merge_resume_state.json", "path": str(merge_resume_state_path)})
    stage_11_3_manifest = {
        "stage": "#11-3",
        "handoff_role": "bundle_and_resume_inputs",
        "canonical_root": str(merge_persist_only_dir),
        "entries": stage_11_3_entries,
    }
    stage_11_3_manifest_path.write_text(json.dumps(stage_11_3_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    merge_resume_state.update({
        "stage": "11-3-complete",
        "stage_11_3_dir": str(stage_11_3_dir),
        "stage_11_3_manifest_path": str(stage_11_3_manifest_path),
        "merged_glb_path": str(merged_glb_path) if merged_glb_path.exists() else None,
    })
    merge_resume_state_path.write_text(json.dumps(merge_resume_state, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest_copy_plan = [
        (input_manifest_path, final_outputs_manifests_dir / "da3_input_manifest.csv"),
        (anchor_dir / "camera_center_matrix_arc.csv", final_outputs_manifests_dir / "camera_center_matrix_arc.csv"),
        (anchor_dir / "camera_matrix_full_arc.csv", final_outputs_manifests_dir / "camera_matrix_full_arc.csv"),
        (anchor_dir / "camera_anchor_full_arc.csv", final_outputs_manifests_dir / "camera_anchor_full_arc.csv"),
        (chunk_manifest_dir / "chunk_index_all.csv", final_outputs_manifests_dir / "chunk_index_all.csv"),
        (chunk_manifest_dir / "batch_plan.csv", final_outputs_manifests_dir / "batch_plan.csv"),
    ]
    final_output_files = []
    for src, dst in manifest_copy_plan:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            final_output_files.append({
                "label": dst.name,
                "source_path": str(src),
                "drive_path": str(dst),
            })
    for path in [
        merged_ply_path,
        merged_glb_path,
        route_compare_path,
        keep_summary_path,
        transform_quality_path,
        final_outputs_diagnostics_dir / "owner_record_histogram_arc.csv",
        final_outputs_diagnostics_dir / "chunk_assignment_summary_arc.csv",
        final_outputs_diagnostics_dir / "merge_warning_summary_arc.json",
        all_batch_summary_path,
        merged_camera_pose_csv,
        merged_camera_matrix_csv,
        merged_camera_c2w_npy,
        merged_camera_w2c_npy,
        ngl_bundle_dir / "ngl_pose_bundle_summary.json",
        merge_resume_state_path,
    ]:
        if Path(path).exists():
            final_output_files.append({
                "label": Path(path).name,
                "source_path": str(path),
                "drive_path": str(path),
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
        "stage_11_2_manifest_path": str(stage_11_2_manifest_path),
        "stage_11_3_manifest_path": str(stage_11_3_manifest_path),
        "chunk_evidence_dirs": sorted([str(p) for p in final_outputs_chunk_evidence_dir.glob("*") if p.is_dir()]),
        "file_count": int(len(final_output_files)),
        "files": final_output_files,
    }
    (final_outputs_dir / "final_output_manifest_arc.json").write_text(json.dumps(final_output_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    stage_access_index_path.write_text(json.dumps({
        "stage": "#11-1",
        "canonical_root": str(merge_persist_only_dir),
        "stage_11_2_manifest_path": str(stage_11_2_manifest_path),
        "stage_11_3_manifest_path": str(stage_11_3_manifest_path),
        "merge_resume_state_path": str(merge_resume_state_path),
        "final_output_manifest_path": str(final_outputs_dir / "final_output_manifest_arc.json"),
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    if not all_vertices and not INFER_GS:
        merge_reason = "infer_gs_disabled"
    elif not all_vertices and len(ply_ready_target_chunk_names) == 0:
        merge_reason = "gaussian_chunk_outputs_missing"
    else:
        merge_reason = None if all_vertices else "no kept vertices"

    selected_route_counts = (
        transform_df.groupby("route_label", as_index=False).size().rename(columns={"size": "chunk_count"}).to_dict(orient="records")
        if len(transform_df)
        else []
    )
    fallback_used_count = int(transform_df["fallback_used"].fillna(False).astype(bool).sum()) if len(transform_df) else 0
    preferred_fallback_used_count = int(transform_df["preferred_fallback_used"].fillna(False).astype(bool).sum()) if len(transform_df) else 0

    merge_summary = {
        "route": "continuous-gs-v07-chunk18-context12-output6-adopt6-merge",
        "status": "ok" if all_vertices else "skipped",
        "reason": merge_reason,
        "completed_chunk_count": int(len(completed_chunks_df)),
        "pred_ready_chunk_count": int(len(pred_ready_target_chunk_names)),
        "ply_ready_chunk_count": int(len(ply_ready_target_chunk_names)),
        "all_chunk_count": int(len(target_chunks_df)),
        "infer_gs": bool(INFER_GS),
        "merged_ply_path": str(merged_ply_path) if merged_ply_path.exists() else None,
        "merged_glb_path": str(merged_glb_path) if merged_glb_path.exists() else None,
        "chunk_global_transforms_path": str(chunk_manifest_dir / "chunk_global_transforms_arc.csv"),
        "merge_route_compare_path": str(route_compare_path),
        "prepose_chunk_graph_solution_path": str(prepose_chunk_graph_solution_path) if prepose_chunk_graph_solution_path.exists() else None,
                "prepose_chunk_graph_summary_path": str(prepose_chunk_graph_summary_path) if prepose_chunk_graph_summary_path.exists() else None,
        "chunk_keep_summary_path": str(keep_summary_path),
        "chunk_transform_quality_path": str(transform_quality_path),
        "owner_record_histogram_path": str(final_outputs_diagnostics_dir / "owner_record_histogram_arc.csv"),
        "chunk_assignment_summary_path": str(final_outputs_diagnostics_dir / "chunk_assignment_summary_arc.csv"),
        "merge_warning_summary_path": str(final_outputs_diagnostics_dir / "merge_warning_summary_arc.json"),
        "all_batch_summary_path": str(all_batch_summary_path),
        "merged_camera_pose_path": str(merged_camera_pose_csv),
        "merged_camera_matrix_path": str(merged_camera_matrix_csv),
        "merged_camera_c2w_path": str(merged_camera_c2w_npy),
        "merged_extrinsics_w2c_path": str(merged_camera_w2c_npy),
        "ngl_pose_bundle_summary_path": str(ngl_bundle_dir / "ngl_pose_bundle_summary.json"),
        "preferred_route_label": PREFERRED_ROUTE_LABEL,
        "selected_route_counts": selected_route_counts,
        "fallback_used_count": fallback_used_count,
        "preferred_fallback_used_count": preferred_fallback_used_count,
        "final_outputs_dir": str(final_outputs_dir),
        "final_output_manifest_path": str(final_outputs_dir / "final_output_manifest_arc.json"),
        "bundle_summary": bundle_summary,
    }
    merge_summary_path.write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
    display_stage_summary(
        "11-1",
        "merge",
        inputs=[
            {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
            {"item": "camera_anchor_full", "path": str(anchor_dir / "camera_anchor_full_arc.csv")},
            {"item": "da3_input_manifest", "path": str(input_manifest_path)},
        ],
        outputs=[
            {"item": "merge_summary", "path": str(merge_summary_path)},
            {"item": "merged_gs", "path": str(merged_ply_path)},
            {"item": "merged_scene_glb", "path": str(merged_glb_path)},
            {"item": "final_output_manifest", "path": str(final_outputs_dir / "final_output_manifest_arc.json")},
            {"item": "chunk_global_transforms", "path": str(chunk_manifest_dir / "chunk_global_transforms_arc.csv")},
            {"item": "merge_route_compare", "path": str(route_compare_path)},
            {"item": "chunk_keep_summary", "path": str(keep_summary_path)},
            {"item": "chunk_transform_quality", "path": str(transform_quality_path)},
            {"item": "merged_camera_pose", "path": str(merged_camera_pose_csv)},
            {"item": "merged_extrinsics_w2c", "path": str(merged_camera_w2c_npy)},
            {"item": "ngl_pose_bundle_summary", "path": str(ngl_bundle_dir / "ngl_pose_bundle_summary.json")},
        ],
        notes=[
            {"item": "completed_chunk_count", "value": int(len(completed_chunks_df))},
            {"item": "status", "value": merge_summary["status"]},
            {"item": "fallback_used_count", "value": fallback_used_count},
            {"item": "preferred_fallback_used_count", "value": preferred_fallback_used_count},
            {"item": "premerge_status", "value": str(premerge_pose_validation.get("status"))},
            {"item": "ngl_pose_rows", "value": int(len(integrated_pose_df))},
        ],
    )
```

#No: #11-2
前: #11-1
次: 終了

# 11 Merge And Review

この markdown cell は `#11-2` の merge review visualization を説明する。full anchor、chunk、merged trajectory を並べて review できる可視化を生成する。

```python
#11-2
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ctx = load_ctx()
probe_root = Path(ctx["probe_root"])
persist_root = Path(ctx.get("persist_root", probe_root))
pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
merged_dir = Path(ctx.get("merged_dir", str(pipeline_root / "merged")))
merged_dir.mkdir(parents=True, exist_ok=True)
anchor_dir = persist_root / "01_anchor"

anchor_path = anchor_dir / "camera_anchor_full_arc.csv"
graph_solution_path = merged_dir / "prepose_chunk_graph_solution_arc.csv"
transform_path = chunk_manifest_dir / "chunk_global_transforms_arc.csv"
merged_camera_pose_path = merged_dir / "merged_camera_pose_arc.csv"
batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
merge_summary_path = merged_dir / "merge_summary.json"

required = [anchor_path, batch_execution_items_path]
missing = [str(p) for p in required if not p.exists()]
assert not missing, {"missing_required": missing}

anchor_df = pd.read_csv(anchor_path)
items_df = pd.read_csv(batch_execution_items_path)
merge_summary = load_json(merge_summary_path) if merge_summary_path.exists() else {}

transform_df = pd.read_csv(graph_solution_path) if graph_solution_path.exists() else (pd.read_csv(transform_path) if transform_path.exists() else pd.DataFrame())


def _resolve_center_cols(df: pd.DataFrame):
    for cols in [
        ("cx_world", "cy_world", "cz_world"),
        ("cam_cx", "cam_cy", "cam_cz"),
        ("cx", "cy", "cz"),
        ("camera_center_x", "camera_center_y", "camera_center_z"),
        ("tx", "ty", "tz"),
    ]:
        if all(c in df.columns for c in cols):
            return cols
    raise AssertionError({"reason": "center columns not found", "columns": df.columns.tolist()})


def _resolve_dir_cols(df: pd.DataFrame):
    for cols in [
        ("anchor_lens_x", "anchor_lens_y", "anchor_lens_z"),
        ("lens_x", "lens_y", "lens_z"),
        ("forward_x", "forward_y", "forward_z"),
        ("dir_x", "dir_y", "dir_z"),
    ]:
        if all(c in df.columns for c in cols):
            return cols
    return None


def _load_transform_map(df: pd.DataFrame) -> dict:
    if df is None or len(df) == 0 or "chunk_name" not in df.columns:
        return {}
    mat_cols = [f"t{r}{c}" for r in range(4) for c in range(4)]
    if not set(mat_cols).issubset(df.columns):
        return {}
    out = {}
    for row in df.itertuples(index=False):
        M = np.eye(4, dtype=np.float32)
        for r in range(4):
            for c in range(4):
                M[r, c] = float(getattr(row, f"t{r}{c}"))
        out[str(row.chunk_name)] = M
    return out


def _resolve_chunk_output_dir(chunk_name: str) -> Path | None:
    direct = chunk_runs_dir / chunk_name
    if direct.exists():
        return direct
    hits = sorted(chunk_runs_dir.glob(f"batch_*/{chunk_name}"))
    return hits[0] if hits else None


def _sample_indices(n: int, k: int = 12) -> np.ndarray:
    if n <= 0:
        return np.array([], dtype=int)
    if n <= k:
        return np.arange(n, dtype=int)
    return np.unique(np.linspace(0, n - 1, num=k, dtype=int))


def _py_bool(value) -> bool:
    return bool(value)


def _poses_to_centers_dirs(c2w: np.ndarray):
    centers = c2w[:, :3, 3]
    lens = -c2w[:, :3, 2]
    norms = np.linalg.norm(lens, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)
    lens = lens / norms
    return centers, lens

anchor_center_cols = _resolve_center_cols(anchor_df)
anchor_dir_cols = _resolve_dir_cols(anchor_df)
anchor_view_df = anchor_df.copy()
if "sequence_index" in anchor_view_df.columns:
    anchor_view_df = anchor_view_df.sort_values("sequence_index", kind="stable").reset_index(drop=True)
elif "frame_timestamp_ns" in anchor_view_df.columns:
    anchor_view_df = anchor_view_df.sort_values("frame_timestamp_ns", kind="stable").reset_index(drop=True)
anchor_centers = anchor_view_df[list(anchor_center_cols)].to_numpy(dtype=float)
anchor_dirs = anchor_view_df[list(anchor_dir_cols)].to_numpy(dtype=float) if anchor_dir_cols is not None else None

transform_map = _load_transform_map(transform_df)
chunk_rows = []
chunk_plot_items = []
merged_pose_rows = []

item_cols = [c for c in ["chunk_id", "batch_index", "chunk_name", "chunk_csv"] if c in items_df.columns]
if item_cols:
    items_unique_df = items_df[item_cols].drop_duplicates().sort_values([c for c in ["chunk_id", "batch_index", "chunk_name"] if c in item_cols], kind="stable")
else:
    items_unique_df = items_df[["chunk_name", "chunk_csv"]].drop_duplicates()

for row in items_unique_df.itertuples(index=False):
    chunk_name = str(row.chunk_name)
    chunk_csv = Path(row.chunk_csv)
    if not chunk_csv.exists():
        continue
    out_dir = _resolve_chunk_output_dir(chunk_name)
    if out_dir is None:
        continue
    pred_path = out_dir / "pred_extrinsics.npy"
    if not pred_path.exists():
        continue
    local_df = pd.read_csv(chunk_csv)
    pred = to_4x4_batch(np.load(pred_path))
    if len(local_df) != pred.shape[0]:
        n = min(len(local_df), pred.shape[0])
        local_df = local_df.iloc[:n].copy()
        pred = pred[:n]
    T = transform_map.get(chunk_name, np.eye(4, dtype=np.float32))
    world = np.einsum("ij,njk->nik", T, pred)
    centers, lens = _poses_to_centers_dirs(world)
    sample_idx = _sample_indices(len(centers), 10)
    chunk_plot_items.append({
        "chunk_name": chunk_name,
        "centers": centers,
        "lens": lens,
        "sample_idx": sample_idx,
    })
    record_index_col = "record_index" if "record_index" in local_df.columns else None
    sequence_col = "sequence_index" if "sequence_index" in local_df.columns else None
    for i in range(len(local_df)):
        chunk_rows.append({
            "chunk_name": chunk_name,
            "local_index": int(i),
            "record_index": int(local_df.iloc[i][record_index_col]) if record_index_col else None,
            "sequence_index": int(local_df.iloc[i][sequence_col]) if sequence_col else None,
            "cx": float(centers[i,0]),
            "cy": float(centers[i,1]),
            "cz": float(centers[i,2]),
            "lens_x": float(lens[i,0]),
            "lens_y": float(lens[i,1]),
            "lens_z": float(lens[i,2]),
        })
        merged_pose_rows.append({
            "chunk_name": chunk_name,
            "record_index": int(local_df.iloc[i][record_index_col]) if record_index_col else None,
            "sequence_index": int(local_df.iloc[i][sequence_col]) if sequence_col else None,
            "cx": float(centers[i,0]),
            "cy": float(centers[i,1]),
            "cz": float(centers[i,2]),
            "lens_x": float(lens[i,0]),
            "lens_y": float(lens[i,1]),
            "lens_z": float(lens[i,2]),
        })

chunk_pose_review_csv = merged_dir / "chunk_pose_review_arc.csv"
pd.DataFrame(chunk_rows).to_csv(chunk_pose_review_csv, index=False, encoding="utf-8")

merged_pose_csv = merged_dir / "merged_pose_review_arc.csv"
if merged_camera_pose_path.exists() and merged_camera_pose_path.stat().st_size > 0:
    merged_df = pd.read_csv(merged_camera_pose_path)
    rename_map = {
        "cx_world": "cx",
        "cy_world": "cy",
        "cz_world": "cz",
        "anchor_lens_x": "lens_x",
        "anchor_lens_y": "lens_y",
        "anchor_lens_z": "lens_z",
    }
    merged_df = merged_df.rename(columns={k: v for k, v in rename_map.items() if k in merged_df.columns})
    keep_cols = [c for c in ["chunk_name", "record_index", "sequence_index", "cx", "cy", "cz", "lens_x", "lens_y", "lens_z"] if c in merged_df.columns]
    merged_df = merged_df[keep_cols].copy()
else:
    merged_df = pd.DataFrame(merged_pose_rows)
    if len(merged_df):
        if merged_df["record_index"].notna().any():
            merged_df = merged_df.sort_values(["record_index", "chunk_name"], kind="stable").drop_duplicates(["record_index"], keep="first")
        elif merged_df["sequence_index"].notna().any():
            merged_df = merged_df.sort_values(["sequence_index", "chunk_name"], kind="stable").drop_duplicates(["sequence_index"], keep="first")
        merged_df = merged_df.reset_index(drop=True)
merged_df.to_csv(merged_pose_csv, index=False, encoding="utf-8")

fig = make_subplots(
    rows=1,
    cols=3,
    specs=[[{"type": "scene"}, {"type": "scene"}, {"type": "scene"}]],
    subplot_titles=("full anchor", "chunks globalized", "merged trajectory"),
)

# panel 1: full anchor
fig.add_trace(go.Scatter3d(
    x=anchor_centers[:,0], y=anchor_centers[:,1], z=anchor_centers[:,2],
    mode="lines+markers", name="full_anchor", marker=dict(size=2),
    line=dict(width=4), showlegend=True,
), row=1, col=1)
if anchor_dirs is not None and len(anchor_centers):
    sample_idx = _sample_indices(len(anchor_centers), 12)
    for i in sample_idx:
        p = anchor_centers[i]
        d = anchor_dirs[i]
        fig.add_trace(go.Scatter3d(
            x=[p[0], p[0] + d[0] * 0.2],
            y=[p[1], p[1] + d[1] * 0.2],
            z=[p[2], p[2] + d[2] * 0.2],
            mode="lines", name="full_anchor_dir" if i == sample_idx[0] else None,
            showlegend=_py_bool(i == sample_idx[0]),
        ), row=1, col=1)

# panel 2: each chunk
for item in chunk_plot_items:
    centers = item["centers"]
    fig.add_trace(go.Scatter3d(
        x=centers[:,0], y=centers[:,1], z=centers[:,2],
        mode="lines+markers", name=item["chunk_name"], marker=dict(size=2), line=dict(width=4),
    ), row=1, col=2)
    for i in item["sample_idx"]:
        p = centers[i]
        d = item["lens"][i]
        fig.add_trace(go.Scatter3d(
            x=[p[0], p[0] + d[0] * 0.2],
            y=[p[1], p[1] + d[1] * 0.2],
            z=[p[2], p[2] + d[2] * 0.2],
            mode="lines", showlegend=False,
        ), row=1, col=2)

# panel 3: merged trajectory
if len(merged_df):
    fig.add_trace(go.Scatter3d(
        x=merged_df["cx"], y=merged_df["cy"], z=merged_df["cz"],
        mode="lines+markers", name="merged_pose", marker=dict(size=2), line=dict(width=5),
    ), row=1, col=3)
    for i in _sample_indices(len(merged_df), 12):
        p = merged_df.loc[i, ["cx", "cy", "cz"]].to_numpy(dtype=float)
        d = merged_df.loc[i, ["lens_x", "lens_y", "lens_z"]].to_numpy(dtype=float)
        fig.add_trace(go.Scatter3d(
            x=[p[0], p[0] + d[0] * 0.2],
            y=[p[1], p[1] + d[1] * 0.2],
            z=[p[2], p[2] + d[2] * 0.2],
            mode="lines", showlegend=False,
        ), row=1, col=3)

for scene_name in ["scene", "scene2", "scene3"]:
    fig.update_layout(**{scene_name: dict(aspectmode="data")})
fig.update_layout(height=700, width=1800, title="full anchor / chunk / merged pose review")

review_html = merged_dir / "premerge_pose_review_panel.html"
fig.write_html(str(review_html), include_plotlyjs="cdn")

review_summary = {
    "status": "ok",
    "merge_status": merge_summary.get("status"),
    "full_anchor_rows": int(len(anchor_df)),
    "chunk_review_rows": int(len(chunk_rows)),
    "merged_review_rows": int(len(merged_df)),
    "review_html": str(review_html),
    "chunk_pose_review_csv": str(chunk_pose_review_csv),
    "merged_pose_review_csv": str(merged_pose_csv),
    "transform_source": str(graph_solution_path if graph_solution_path.exists() else transform_path),
    "merged_camera_pose_source": str(merged_camera_pose_path) if merged_camera_pose_path.exists() else None,
}
save_json(merged_dir / "premerge_pose_review_summary.json", review_summary)
print(json.dumps(review_summary, indent=2, ensure_ascii=False))
display_stage_summary(
    "11-2",
    "merge review visualization",
    inputs=[
        {"item": "camera_anchor_full", "path": str(anchor_path)},
        {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
        {"item": "chunk_global_transforms_or_graph_solution", "path": str(graph_solution_path if graph_solution_path.exists() else transform_path)},
        {"item": "merge_summary", "path": str(merge_summary_path)},
    ],
    outputs=[
        {"item": "chunk_pose_review", "path": str(chunk_pose_review_csv)},
        {"item": "merged_pose_review", "path": str(merged_pose_csv)},
        {"item": "premerge_pose_review_panel", "path": str(review_html)},
        {"item": "premerge_pose_review_summary", "path": str(merged_dir / "premerge_pose_review_summary.json")},
        {"item": "merged_camera_pose", "path": str(merged_camera_pose_path)},
    ],
    notes=[
        {"item": "chunk_count", "value": int(len(chunk_plot_items))},
        {"item": "merged_review_rows", "value": int(len(merged_df))},
    ],
)
```
