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
    "CHUNK_STEP": 12,
    "ADOPT_SIZE": 12,
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
}
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
from datetime import datetime, timezone
import re

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


def slugify_name(value: str, fallback: str = "optpose") -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", str(value or "")).strip("_").lower()
    return text[:32] if text else fallback

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
    tree_schema_version = "2.0.0"
    purpose_slug = slugify_name(CONFIG_SNAPSHOT.get("PROJECT_SLUG", "optpose"))
    run_timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    run_id = f"run_{run_timestamp_utc}_{purpose_slug}"

    runtime_root = probe_root / "00_runtime"
    validation_root = probe_root / "10_validation"
    validation_runs_dir = validation_root / "runs"
    run_root = validation_runs_dir / run_id
    run_runtime_dir = run_root / "00_runtime"
    run_validation_dir = run_root / "10_validation"
    run_logs_dir = run_root / "logs"
    run_config_snapshot_dir = run_root / "config_snapshot"
    validation_current_alias = validation_root / "current"
    validation_latest_alias = validation_runs_dir / "latest"

    runtime_extract_dir = run_runtime_dir / "extract_root"
    runtime_model_dir = run_runtime_dir / "model_runtime"
    runtime_cleanup_dir = run_runtime_dir / "cleanup_review"
    validation_anchor_dir = run_validation_dir / "anchor"
    validation_records_dir = run_validation_dir / "records"
    validation_batch_plan_dir = run_validation_dir / "batch_plan"
    validation_chunk_runs_dir = run_validation_dir / "chunk_runs"
    validation_merged_dir = run_validation_dir / "merged"
    validation_manifest_dir = run_validation_dir / "manifests"
    validation_review_dir = run_validation_dir / "reviews"
    validation_other_dir = run_validation_dir / "other"

    delivery_root = probe_root / "20_delivery"
    delivery_releases_dir = delivery_root / "releases"
    delivery_end_user_dir = delivery_root / "end_user"
    delivery_technical_reference_dir = delivery_root / "technical_reference"
    delivery_operator_private_dir = delivery_root / "operator_private"
    delivery_release_latest_alias = delivery_releases_dir / "latest"
    delivery_release_stable_alias = delivery_releases_dir / "stable"

    final_outputs_dir = delivery_root
    final_outputs_merged_dir = delivery_end_user_dir / "current"
    final_outputs_diagnostics_dir = delivery_technical_reference_dir / "current" / "diagnostics"
    final_outputs_manifests_dir = delivery_technical_reference_dir / "current" / "manifests"
    final_outputs_chunk_evidence_dir = delivery_operator_private_dir / "current" / "chunk_evidence"

    pipeline_root = probe_root / PIPELINE_SLUG
    pipeline_manifest_dir = pipeline_root / "manifests"
    pipeline_chunk_runs_dir = pipeline_root / "chunk_runs"
    pipeline_merged_dir = pipeline_root / "merged"

    da3_nested_dir = runtime_model_dir / "da3_nested_giant_large"
    da3_nested_gs_dir = runtime_model_dir / "da3_nested_gs"
    world_dir = runtime_model_dir / "world_fusion_v01"
    manifest_dir = validation_manifest_dir

    legacy_root = probe_root / "legacy"
    migration_root = probe_root / "migration"
    archive_root = probe_root / "99_archive"

    compatibility_aliases = {
        "00_config": str(probe_root / "00_config"),
        "01_anchor": str(probe_root / "01_anchor"),
        "02_records": str(probe_root / "02_records"),
        "03_batch_plan": str(probe_root / "03_batch_plan"),
        "04_batch_runs": str(probe_root / "04_batch_runs"),
        "05_merge": str(probe_root / "05_merge"),
        "06_cleanup": str(probe_root / "06_cleanup"),
        "other": str(probe_root / "other"),
        "pipeline_manifests": str(pipeline_manifest_dir),
        "pipeline_chunk_runs": str(pipeline_chunk_runs_dir),
        "pipeline_merged": str(pipeline_merged_dir),
    }

    for p in [
        probe_root,
        runtime_root,
        validation_root,
        validation_runs_dir,
        run_root,
        run_runtime_dir,
        run_validation_dir,
        run_logs_dir,
        run_config_snapshot_dir,
        runtime_extract_dir,
        runtime_model_dir,
        runtime_cleanup_dir,
        validation_anchor_dir,
        validation_records_dir,
        validation_batch_plan_dir,
        validation_chunk_runs_dir,
        validation_merged_dir,
        validation_manifest_dir,
        validation_review_dir,
        validation_other_dir,
        delivery_root,
        delivery_releases_dir,
        delivery_end_user_dir,
        delivery_technical_reference_dir,
        delivery_operator_private_dir,
        final_outputs_merged_dir,
        final_outputs_diagnostics_dir,
        final_outputs_manifests_dir,
        final_outputs_chunk_evidence_dir,
        pipeline_root,
        legacy_root,
        migration_root,
        archive_root,
        da3_nested_dir,
        da3_nested_gs_dir,
        world_dir,
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
        "tree_schema_version": tree_schema_version,
        "run_id": run_id,
        "run_timestamp_utc": run_timestamp_utc,
        "probe_root": str(probe_root),
        "runtime_root": str(runtime_root),
        "validation_root": str(validation_root),
        "validation_runs_dir": str(validation_runs_dir),
        "validation_current_alias": str(validation_current_alias),
        "validation_latest_alias": str(validation_latest_alias),
        "run_root": str(run_root),
        "run_runtime_dir": str(run_runtime_dir),
        "run_validation_dir": str(run_validation_dir),
        "run_logs_dir": str(run_logs_dir),
        "run_config_snapshot_dir": str(run_config_snapshot_dir),
        "manifest_dir": str(manifest_dir),
        "da3_nested_dir": str(da3_nested_dir),
        "da3_nested_gs_dir": str(da3_nested_gs_dir),
        "world_dir": str(world_dir),
        "pipeline_root": str(pipeline_root),
        "pipeline_manifest_dir": str(pipeline_manifest_dir),
        "pipeline_chunk_runs_dir": str(pipeline_chunk_runs_dir),
        "pipeline_merged_dir": str(pipeline_merged_dir),
        "final_outputs_dir": str(final_outputs_dir),
        "final_outputs_merged_dir": str(final_outputs_merged_dir),
        "final_outputs_diagnostics_dir": str(final_outputs_diagnostics_dir),
        "final_outputs_manifests_dir": str(final_outputs_manifests_dir),
        "final_outputs_chunk_evidence_dir": str(final_outputs_chunk_evidence_dir),
        "delivery_root": str(delivery_root),
        "delivery_releases_dir": str(delivery_releases_dir),
        "delivery_release_latest_alias": str(delivery_release_latest_alias),
        "delivery_release_stable_alias": str(delivery_release_stable_alias),
        "delivery_end_user_dir": str(delivery_end_user_dir),
        "delivery_technical_reference_dir": str(delivery_technical_reference_dir),
        "delivery_operator_private_dir": str(delivery_operator_private_dir),
        "legacy_root": str(legacy_root),
        "migration_root": str(migration_root),
        "archive_root": str(archive_root),
        "validation_anchor_dir": str(validation_anchor_dir),
        "validation_records_dir": str(validation_records_dir),
        "validation_batch_plan_dir": str(validation_batch_plan_dir),
        "validation_chunk_runs_dir": str(validation_chunk_runs_dir),
        "validation_merged_dir": str(validation_merged_dir),
        "validation_manifest_dir": str(validation_manifest_dir),
        "validation_review_dir": str(validation_review_dir),
        "validation_other_dir": str(validation_other_dir),
        "runtime_extract_dir": str(runtime_extract_dir),
        "runtime_model_dir": str(runtime_model_dir),
        "runtime_cleanup_dir": str(runtime_cleanup_dir),
        "compatibility_aliases": compatibility_aliases,
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

- root は `immutable run / release 実体 + current/latest pointer + tree schema version` で管理する
- 実際の validation 出力は `10_validation/runs/<run_id>/` 配下へ置く
- 旧 path は compatibility alias として残し、今通っている notebook 実行を壊さない

```python
#4-1
from pathlib import Path
import json
import shutil
import hashlib
from datetime import datetime, timezone

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
modeling_session_id = session_id.replace("trajectreview-correcting-session-", "trajectreview-modeling-session-", 1) if session_id.startswith("trajectreview-correcting-session-") else f"trajectreview-modeling-session-{session_id}"
probe_root_name = modeling_session_id
probe_root = Path(paths["probe_root"])
tree_schema_version = str(paths["tree_schema_version"])
run_id = str(paths["run_id"])
run_timestamp_utc = str(paths["run_timestamp_utc"])
runtime_root = Path(paths["runtime_root"])
validation_root = Path(paths["validation_root"])
validation_runs_dir = Path(paths["validation_runs_dir"])
validation_current_alias = Path(paths["validation_current_alias"])
validation_latest_alias = Path(paths["validation_latest_alias"])
run_root = Path(paths["run_root"])
run_runtime_dir = Path(paths["run_runtime_dir"])
run_validation_dir = Path(paths["run_validation_dir"])
run_logs_dir = Path(paths["run_logs_dir"])
run_config_snapshot_dir = Path(paths["run_config_snapshot_dir"])
pipeline_root = Path(paths["pipeline_root"])
chunk_manifest_dir = Path(paths["pipeline_manifest_dir"])
chunk_runs_dir = Path(paths["pipeline_chunk_runs_dir"])
merged_dir = Path(paths["pipeline_merged_dir"])
da3_nested_dir = Path(paths["da3_nested_dir"])
da3_nested_gs_dir = Path(paths["da3_nested_gs_dir"])
world_dir = Path(paths["world_dir"])
manifest_dir = Path(paths["manifest_dir"])
final_outputs_dir = Path(paths["final_outputs_dir"])
final_outputs_merged_dir = Path(paths["final_outputs_merged_dir"])
final_outputs_diagnostics_dir = Path(paths["final_outputs_diagnostics_dir"])
final_outputs_manifests_dir = Path(paths["final_outputs_manifests_dir"])
final_outputs_chunk_evidence_dir = Path(paths["final_outputs_chunk_evidence_dir"])
delivery_root = Path(paths["delivery_root"])
delivery_releases_dir = Path(paths["delivery_releases_dir"])
delivery_release_latest_alias = Path(paths["delivery_release_latest_alias"])
delivery_release_stable_alias = Path(paths["delivery_release_stable_alias"])
delivery_end_user_dir = Path(paths["delivery_end_user_dir"])
delivery_technical_reference_dir = Path(paths["delivery_technical_reference_dir"])
delivery_operator_private_dir = Path(paths["delivery_operator_private_dir"])
legacy_root = Path(paths["legacy_root"])
migration_root = Path(paths["migration_root"])
archive_root = Path(paths["archive_root"])
validation_anchor_dir = Path(paths["validation_anchor_dir"])
validation_records_dir = Path(paths["validation_records_dir"])
validation_batch_plan_dir = Path(paths["validation_batch_plan_dir"])
validation_chunk_runs_dir = Path(paths["validation_chunk_runs_dir"])
validation_merged_dir = Path(paths["validation_merged_dir"])
validation_manifest_dir = Path(paths["validation_manifest_dir"])
validation_review_dir = Path(paths["validation_review_dir"])
validation_other_dir = Path(paths["validation_other_dir"])
runtime_extract_dir = Path(paths["runtime_extract_dir"])
runtime_model_dir = Path(paths["runtime_model_dir"])
runtime_cleanup_dir = Path(paths["runtime_cleanup_dir"])
compatibility_aliases = {k: Path(v) for k, v in paths.get("compatibility_aliases", {}).items()}


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def ensure_tree_pointer(pointer_path: Path, target_path: Path) -> dict:
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.mkdir(parents=True, exist_ok=True)
    if pointer_path.exists() or pointer_path.is_symlink():
        try:
            if pointer_path.is_symlink() and pointer_path.resolve() == target_path.resolve():
                return {"pointer": str(pointer_path), "target": str(target_path), "status": "already_linked"}
        except FileNotFoundError:
            pass
        if pointer_path.is_symlink():
            pointer_path.unlink()
        elif pointer_path.is_dir():
            existing_items = list(pointer_path.iterdir())
            if existing_items:
                return {"pointer": str(pointer_path), "target": str(target_path), "status": "existing_directory_kept"}
            pointer_path.rmdir()
        else:
            pointer_path.unlink()
    try:
        pointer_path.symlink_to(target_path, target_is_directory=True)
        return {"pointer": str(pointer_path), "target": str(target_path), "status": "symlink_created"}
    except OSError:
        pointer_path.mkdir(parents=True, exist_ok=True)
        write_json(pointer_path / "alias_target.json", {
            "pointer": str(pointer_path),
            "target": str(target_path),
            "status": "directory_fallback",
        })
        return {"pointer": str(pointer_path), "target": str(target_path), "status": "directory_fallback"}

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
    runtime_root,
    validation_root,
    validation_runs_dir,
    run_root,
    run_runtime_dir,
    run_validation_dir,
    run_logs_dir,
    run_config_snapshot_dir,
    runtime_extract_dir,
    runtime_model_dir,
    runtime_cleanup_dir,
    validation_anchor_dir,
    validation_records_dir,
    validation_batch_plan_dir,
    validation_chunk_runs_dir,
    validation_merged_dir,
    validation_manifest_dir,
    validation_review_dir,
    validation_other_dir,
    pipeline_root,
    chunk_manifest_dir,
    chunk_runs_dir,
    merged_dir,
    da3_nested_dir,
    da3_nested_gs_dir,
    world_dir,
    delivery_root,
    delivery_releases_dir,
    delivery_end_user_dir,
    delivery_technical_reference_dir,
    delivery_operator_private_dir,
    final_outputs_dir,
    final_outputs_merged_dir,
    final_outputs_diagnostics_dir,
    final_outputs_manifests_dir,
    final_outputs_chunk_evidence_dir,
    legacy_root,
    migration_root,
    archive_root,
]:
    p.mkdir(parents=True, exist_ok=True)

config_snapshot_path = Path("/content/config_snapshot.json")
config_hash = hashlib.sha256(config_snapshot_path.read_bytes()).hexdigest() if config_snapshot_path.exists() else None
if config_snapshot_path.exists():
    shutil.copy2(config_snapshot_path, run_config_snapshot_dir / "config_snapshot.json")

pointer_logs = [
    ensure_tree_pointer(validation_latest_alias, run_root),
    ensure_tree_pointer(validation_current_alias, run_root),
]
for alias_name, alias_path in compatibility_aliases.items():
    target_map = {
        "00_config": run_config_snapshot_dir,
        "01_anchor": validation_anchor_dir,
        "02_records": validation_records_dir,
        "03_batch_plan": validation_batch_plan_dir,
        "04_batch_runs": validation_chunk_runs_dir,
        "05_merge": validation_merged_dir,
        "06_cleanup": runtime_cleanup_dir,
        "other": validation_other_dir,
        "pipeline_manifests": validation_manifest_dir,
        "pipeline_chunk_runs": validation_chunk_runs_dir,
        "pipeline_merged": validation_merged_dir,
    }
    target = target_map.get(alias_name)
    if target is not None:
        pointer_logs.append(ensure_tree_pointer(alias_path, target))

write_json(probe_root / "root_manifest.json", {
    "tree_schema_version": tree_schema_version,
    "active_run_id": run_id,
    "active_release_id": None,
    "pipeline_slug": pipeline_slug,
    "route_slug": route_slug,
})
write_json(run_root / "run_manifest.json", {
    "run_id": run_id,
    "created_at_utc": run_timestamp_utc,
    "session_id": session_id,
    "modeling_session_id": modeling_session_id,
    "purpose": route_slug,
    "input_id": session_id,
    "config_hash": config_hash,
    "tree_schema_version": tree_schema_version,
})
write_json(run_root / "status.json", {
    "state": "running",
    "updated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
})
write_json(run_root / "lineage.json", {
    "parent_run_id": None,
    "selected_path": str(selected_path),
    "selected_kind": selected_kind,
    "release_ids": [],
})
for bundle_dir, bundle_name, origin_stage, lifecycle, audience in [
    (validation_manifest_dir, "manifests", "run_init", "validation", "internal"),
    (validation_chunk_runs_dir, "chunk_runs", "chunk_execution", "validation", "internal"),
    (validation_merged_dir, "merged", "merge", "validation", "internal"),
    (final_outputs_merged_dir, "end_user_current", "delivery", "delivery", "end_user"),
    (final_outputs_manifests_dir, "technical_reference_current", "delivery", "delivery", "technical_reference"),
    (final_outputs_chunk_evidence_dir, "operator_private_current", "delivery", "delivery", "operator_private"),
]:
    write_json(bundle_dir / "bundle_manifest.json", {
        "bundle_name": bundle_name,
        "origin_stage": origin_stage,
        "lifecycle": lifecycle,
        "audience": audience,
        "schema_version": tree_schema_version,
    })
write_json(migration_root / f"migration_{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}.json", {
    "tree_schema_version": tree_schema_version,
    "run_id": run_id,
    "pointer_logs": pointer_logs,
    "compatibility_aliases": {k: str(v) for k, v in compatibility_aliases.items()},
})

context_doc = {
    "session_id": session_id,
    "modeling_session_id": modeling_session_id,
    "selected_kind": selected_kind,
    "selected_path": str(selected_path),
    "results_root": str(results_root),
    "results_root_visibility": "google_drive_mydrive_visible",
    "route_slug": route_slug,
    "pipeline_slug": pipeline_slug,
    "tree_schema_version": tree_schema_version,
    "run_id": run_id,
    "run_timestamp_utc": run_timestamp_utc,
    "probe_root_name": probe_root_name,
    "session_outer": str(session_outer),
    "session_root": str(session_root),
    "images_dir": str(images_dir),
    "frame_record_path": str(frame_record_path),
    "frame_pose_index_path": str(frame_pose_index_path),
    "probe_root": str(probe_root),
    "runtime_root": str(runtime_root),
    "validation_root": str(validation_root),
    "validation_runs_dir": str(validation_runs_dir),
    "validation_current_alias": str(validation_current_alias),
    "validation_latest_alias": str(validation_latest_alias),
    "run_root": str(run_root),
    "run_runtime_dir": str(run_runtime_dir),
    "run_validation_dir": str(run_validation_dir),
    "run_logs_dir": str(run_logs_dir),
    "run_config_snapshot_dir": str(run_config_snapshot_dir),
    "da3_nested_dir": str(da3_nested_dir),
    "da3_nested_gs_dir": str(da3_nested_gs_dir),
    "world_dir": str(world_dir),
    "manifest_dir": str(manifest_dir),
    "merged_dir": str(merged_dir),
    "chunk_manifest_dir": str(chunk_manifest_dir),
    "chunk_runs_dir": str(chunk_runs_dir),
    "delivery_root": str(delivery_root),
    "delivery_releases_dir": str(delivery_releases_dir),
    "delivery_release_latest_alias": str(delivery_release_latest_alias),
    "delivery_release_stable_alias": str(delivery_release_stable_alias),
    "delivery_end_user_dir": str(delivery_end_user_dir),
    "delivery_technical_reference_dir": str(delivery_technical_reference_dir),
    "delivery_operator_private_dir": str(delivery_operator_private_dir),
    "final_outputs_dir": str(final_outputs_dir),
    "final_outputs_merged_dir": str(final_outputs_merged_dir),
    "final_outputs_diagnostics_dir": str(final_outputs_diagnostics_dir),
    "final_outputs_manifests_dir": str(final_outputs_manifests_dir),
    "final_outputs_chunk_evidence_dir": str(final_outputs_chunk_evidence_dir),
    "legacy_root": str(legacy_root),
    "migration_root": str(migration_root),
    "archive_root": str(archive_root),
    "pointer_logs": pointer_logs,
    "compatibility_aliases": {k: str(v) for k, v in compatibility_aliases.items()},
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

- canonical dir は `run_root` と `10_validation` / `20_delivery` 系へ整理する
- `managed_dirs` は現行 script が実際に使う key だけへ絞る
- 旧 tree 名は `compatibility_aliases` として保持し、既存 cell の参照を壊さない

```python
#4-2
from pathlib import Path
import json

ctx = json.loads(Path('/content/runbook_session_context.json').read_text(encoding='utf-8'))
probe_root = Path(ctx['probe_root'])
run_root = Path(ctx['run_root'])

canonical_dirs = {
    'run_root': run_root,
    'run_config_snapshot': Path(ctx['run_config_snapshot_dir']),
    'runtime_extract': Path(ctx['runtime_extract_dir']),
    'runtime_model': Path(ctx['runtime_model_dir']),
    'runtime_cleanup': Path(ctx['runtime_cleanup_dir']),
    'validation_anchor': Path(ctx['compatibility_aliases']['01_anchor']).resolve() if Path(ctx['compatibility_aliases']['01_anchor']).exists() else Path(ctx['validation_root']) / 'runs' / Path(ctx['run_id']) / '10_validation' / 'anchor',
    'validation_records': Path(ctx['compatibility_aliases']['02_records']).resolve() if Path(ctx['compatibility_aliases']['02_records']).exists() else Path(ctx['validation_root']) / 'runs' / Path(ctx['run_id']) / '10_validation' / 'records',
    'validation_batch_plan': Path(ctx['compatibility_aliases']['03_batch_plan']).resolve() if Path(ctx['compatibility_aliases']['03_batch_plan']).exists() else Path(ctx['validation_root']) / 'runs' / Path(ctx['run_id']) / '10_validation' / 'batch_plan',
    'validation_chunk_runs': Path(ctx['chunk_runs_dir']),
    'validation_merged': Path(ctx['merged_dir']),
    'validation_manifests': Path(ctx['chunk_manifest_dir']),
    'validation_reviews': Path(ctx['run_validation_dir']) / 'reviews',
    'delivery_end_user_current': Path(ctx['final_outputs_merged_dir']),
    'delivery_technical_reference_current': Path(ctx['final_outputs_manifests_dir']),
    'delivery_operator_private_current': Path(ctx['final_outputs_chunk_evidence_dir']),
}

managed_dirs = {
    '02_records': canonical_dirs['validation_records'],
}

compatibility_aliases = {k: Path(v) for k, v in ctx.get('compatibility_aliases', {}).items()}
for p in list(canonical_dirs.values()) + list(managed_dirs.values()) + list(compatibility_aliases.values()):
    p.mkdir(parents=True, exist_ok=True)

doc = {
    'probe_root': str(probe_root),
    'run_root': str(run_root),
    'tree_schema_version': str(ctx['tree_schema_version']),
    'canonical_dirs': {k: str(v) for k, v in canonical_dirs.items()},
    'managed_dirs': {k: str(v) for k, v in managed_dirs.items()},
    'compatibility_aliases': {k: str(v) for k, v in compatibility_aliases.items()},
}
Path('/content/runbook_managed_dirs.json').write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(doc, indent=2, ensure_ascii=False))
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

この markdown cell は `#8-3` の chunk/batch plan build を説明する。record manifest から chunk index、target chunk、batch plan を生成する。

```python
#8-3

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
BATCH_SIZE = int(config_snapshot.get("BATCH_SIZE", 2))

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
    "TARGET_CHUNK_MODE": str(config_snapshot.get("TARGET_CHUNK_MODE", "selected_chunk_ids_1based")),
    "TARGET_CHUNK_IDS_1BASED": list(config_snapshot.get("TARGET_CHUNK_IDS_1BASED", [6, 7])),
    "USE_TARGET_CHUNK_WINDOW": bool(config_snapshot.get("USE_TARGET_CHUNK_WINDOW", False)),
    "TARGET_CHUNK_WINDOW_START_1BASED": int(config_snapshot.get("TARGET_CHUNK_WINDOW_START_1BASED", 1)),
    "TARGET_CHUNK_WINDOW_COUNT": int(config_snapshot.get("TARGET_CHUNK_WINDOW_COUNT", 0)),
    "TARGET_POLICY": "config_driven_target_selection",
    "TEST_EXECUTION_LIMITER_LOCATION": "#11-3 legacy override only",
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

# ----- canonical target = config で選ぶ -----
target_mode = str(config.get("TARGET_CHUNK_MODE", "selected_chunk_ids_1based"))
target_ids_1based = [int(x) for x in config.get("TARGET_CHUNK_IDS_1BASED", [])]

if target_mode == "full_set":
    target_chunks_df = all_chunks_df.copy().reset_index(drop=True)
    target_policy = "full_set"
elif target_mode == "selected_chunk_ids_1based":
    valid_chunk_ids = set(all_chunks_df["chunk_id"].astype(int).tolist())
    selected_chunk_ids = sorted({int(x) - 1 for x in target_ids_1based if int(x) >= 1})
    selected_chunk_ids = [x for x in selected_chunk_ids if x in valid_chunk_ids]
    assert selected_chunk_ids, {
        "reason": "selected target chunk ids resolved empty",
        "target_ids_1based": target_ids_1based,
        "valid_chunk_ids_0based": sorted(valid_chunk_ids),
    }
    target_chunks_df = all_chunks_df.loc[all_chunks_df["chunk_id"].astype(int).isin(selected_chunk_ids)].copy()
    target_chunks_df = target_chunks_df.sort_values("chunk_id", kind="stable").reset_index(drop=True)
    target_policy = "selected_chunk_ids_1based"
elif bool(config.get("USE_TARGET_CHUNK_WINDOW", False)):
    start_0 = max(0, int(config.get("TARGET_CHUNK_WINDOW_START_1BASED", 1)) - 1)
    count = int(config.get("TARGET_CHUNK_WINDOW_COUNT", 0))
    assert count > 0, {"reason": "TARGET_CHUNK_WINDOW_COUNT must be > 0 when window mode is enabled", "count": count}
    end_0 = min(start_0 + count, len(all_chunks_df))
    target_chunks_df = all_chunks_df.iloc[start_0:end_0].copy().reset_index(drop=True)
    assert not target_chunks_df.empty, {"reason": "window target resolved empty", "start_0": start_0, "end_0": end_0}
    target_policy = "window_1based"
else:
    raise AssertionError({"reason": "unsupported target chunk mode", "target_mode": target_mode})

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


# ----- anchor 由来の派生 manifest は #7 anchor 構築後に実装する -----
# TODO(after #7):
# - camera_anchor_full_arc.csv を record_index で各 chunk に結合する
# - chunk_xxx_sequence_anchor.csv を生成する
# - chunk_sequence_anchor_index.csv を生成する

run_manifest = {
    "route": "da3_record_batch_plan_config_target",
    "pipeline_root": str(pipeline_root),
    "chunk_manifest_dir": str(chunk_manifest_dir),
    "batch_runs_dir": str(batch_runs_dir),
    "merged_dir": str(merged_dir),
    "da3_input_manifest_path": str(chunk_manifest_dir / "da3_input_manifest.csv"),
    "chunk_index_all_path": str(chunk_manifest_dir / "chunk_index_all.csv"),
    "target_chunk_with_batch_path": str(chunk_manifest_dir / "target_chunk_with_batch.csv"),
    "batch_plan_path": str(chunk_manifest_dir / "batch_plan.csv"),
    "config_path": str(chunk_manifest_dir / "da3_batch_config.json"),
}
print(run_manifest)

display_stage_summary(
    "8-3",
    "record manifest and chunk plan build",
    inputs=[
        {"item": "da3_input_manifest", "path": str(chunk_manifest_dir / "da3_input_manifest.csv")},
    ],
    outputs=[
        {"item": "chunk_index_all", "path": str(chunk_manifest_dir / "chunk_index_all.csv")},
        {"item": "target_chunk_with_batch", "path": str(chunk_manifest_dir / "target_chunk_with_batch.csv")},
        {"item": "batch_plan", "path": str(chunk_manifest_dir / "batch_plan.csv")},
        {"item": "da3_batch_config", "path": str(chunk_manifest_dir / "da3_batch_config.json")},
    ],
    notes=[
        {"item": "anchor_derived_manifest_deferred_to_stage7", "value": True},
    ],
)
```

#No: #8-4
前: #8-3
次: #8-5

# 8 Chunk Run Preparation And Execution

この markdown cell は `#8-4` の batch chunk sequence precheck を説明する。chunk 内 sequence の連続性と gap を診断する。

```python
#8-4

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
    "8-4",
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

#No: #8-5
前: #8-4
次: #8-6

# 8 Chunk Run Preparation And Execution

この markdown cell は `#8-5` の execution target resolve を説明する。target chunk と batch plan の正本を解決し、後段実行対象を固定する。

```python
#8-5

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
    "execution_chunk_names_all": execution_chunks_df[chunk_name_col].astype(str).tolist(),
    "execution_batch_names": execution_batch_plan_df["batch_name"].astype(str).tolist(),
    "execution_chunk_out": str(execution_chunk_out),
    "execution_batch_out": str(execution_batch_out),
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

この markdown cell は `#8-9` の batch 実行を説明する。target chunk を batch 単位で実行し、predicted pose artifact を残す。

```python
#8-9

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

if INFER_GS and "gs_ply" not in EXPORT_FORMAT:
    EXPORT_FORMAT = "npz-glb-gs_ply-gs_video"

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
            "export_format": EXPORT_FORMAT,
            "infer_gs": bool(INFER_GS),
            "command": " ".join(cmd),
            "out_dir": str(out_dir),
        })
        continue

    with stdout_txt.open("w", encoding="utf-8") as stdout_fh, stderr_txt.open("w", encoding="utf-8") as stderr_fh:
        proc = subprocess.Popen(
            cmd,
            stdout=stdout_fh,
            stderr=stderr_fh,
            text=True,
            cwd="/content/Depth-Anything-3",
        )
        returncode = int(proc.wait())

    outputs_exist = (out_dir / "pred_extrinsics.npy").exists()

    if returncode == 0 and outputs_exist:
        status = "ok"
    else:
        status = "failed"
        failed_json = out_dir / "_FAILED.json"
        failed_json.write_text(json.dumps({
            "status": "failed",
            "returncode": returncode,
            "command": cmd,
            "stdout_path": str(stdout_txt),
            "stderr_path": str(stderr_txt),
            "outputs_exist": outputs_exist,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    rows.append({
        "batch_name": batch_name,
        "chunk_name": chunk_name,
        "status": status,
        "returncode": returncode,
        "outputs_exist": bool(outputs_exist),
        "export_format": EXPORT_FORMAT,
        "infer_gs": bool(INFER_GS),
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
    "8-9",
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

- overlap 由来の relative transform だけでなく、anchor residual を graph optimization へ混ぜる
- overlap 内でだけ合って non-overlap で drift する route は warning として検出する
- preferred route が warning の時は baseline route へ fallback し、採用 route を gate 出力へ残す

```python
#10-1

from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as SciRot

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

anchor_dir = persist_root / "01_anchor"
camera_anchor_full_path = anchor_dir / "camera_anchor_full_arc.csv"

batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
assert batch_execution_items_path.exists(), batch_execution_items_path
assert camera_anchor_full_path.exists(), camera_anchor_full_path

items_df = pd.read_csv(batch_execution_items_path)
assert not items_df.empty, batch_execution_items_path
sort_cols = [c for c in ["chunk_id", "batch_index", "batch_name", "chunk_name"] if c in items_df.columns]
if sort_cols:
    items_df = items_df.sort_values(sort_cols, kind="stable").reset_index(drop=True)

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
    "anchor_up_x", "anchor_up_y", "anchor_up_z",
]
missing_anchor_cols = [c for c in required_anchor_cols if c not in anchor_full_df.columns]
assert not missing_anchor_cols, {"missing_anchor_columns": missing_anchor_cols}

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

PREMERGE_CENTER_ERROR_P95_MAX = 0.25
PREMERGE_LENS_ERROR_DEG_P95_MAX = 12.0
PREMERGE_DELTA_CENTER_ERROR_MAX = 0.15
PREMERGE_DELTA_LENS_ERROR_DEG_MAX = 8.0
TRANSFORM_SCALE_MIN = 0.8
TRANSFORM_SCALE_MAX = 1.3
TRANSFORM_CENTER_RMSE_MAX = 0.15
TRANSFORM_ROT_DIR_MAX = 0.20


SIM3_GRAPH_OPTIMIZATION = True
GRAPH_OPT_MAX_NFEV = 400
GRAPH_PRIOR_WEIGHT = 0.05
GRAPH_EDGE_TRANSLATION_WEIGHT = 1.0
GRAPH_EDGE_ROTATION_WEIGHT = 0.35
GRAPH_EDGE_SCALE_WEIGHT = 0.20
GRAPH_ANCHOR_WEIGHT = 0.02
GRAPH_ANCHOR_ROT_WEIGHT = 0.01
GRAPH_ANCHOR_FRAME_TRANSLATION_WEIGHT = 0.60
GRAPH_ANCHOR_FRAME_DIRECTION_WEIGHT = 0.45
GRAPH_ANCHOR_OVERLAP_FRAME_WEIGHT = 0.20
GRAPH_ANCHOR_NONOVERLAP_FRAME_WEIGHT = 1.00

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

def normalize_vec(vec: np.ndarray, fallback: np.ndarray) -> np.ndarray:
    vec = np.asarray(vec, dtype=np.float64)
    norm = float(np.linalg.norm(vec))
    if norm <= 1e-12:
        fallback = np.asarray(fallback, dtype=np.float64)
        fallback_norm = float(np.linalg.norm(fallback))
        assert fallback_norm > 1e-12, "fallback vector must be non-zero"
        return fallback / fallback_norm
    return vec / norm


def build_anchor_c2w_list(anchor_df: pd.DataFrame) -> list[np.ndarray]:
    mats = []
    for rec in anchor_df.itertuples(index=False):
        center = np.array([float(rec.cx_world), float(rec.cy_world), float(rec.cz_world)], dtype=np.float64)
        anchor_lens = normalize_vec(
            np.array([float(rec.anchor_lens_x), float(rec.anchor_lens_y), float(rec.anchor_lens_z)], dtype=np.float64),
            np.array([0.0, 0.0, -1.0], dtype=np.float64),
        )
        anchor_up = normalize_vec(
            np.array([float(rec.anchor_up_x), float(rec.anchor_up_y), float(rec.anchor_up_z)], dtype=np.float64),
            np.array([0.0, -1.0, 0.0], dtype=np.float64),
        )
        z_col = normalize_vec(-anchor_lens, np.array([0.0, 0.0, 1.0], dtype=np.float64))
        x_seed = np.cross(-anchor_up, z_col)
        x_col = normalize_vec(x_seed, np.array([1.0, 0.0, 0.0], dtype=np.float64))
        y_col = normalize_vec(np.cross(z_col, x_col), np.array([0.0, 1.0, 0.0], dtype=np.float64))
        if float(np.dot(y_col, -anchor_up)) < 0.0:
            x_col = -x_col
            y_col = -y_col
        M = np.eye(4, dtype=np.float32)
        M[:3, 0] = x_col.astype(np.float32)
        M[:3, 1] = y_col.astype(np.float32)
        M[:3, 2] = z_col.astype(np.float32)
        M[:3, 3] = center.astype(np.float32)
        mats.append(M)
    return mats


def local_c2w_list(pred_extrinsics: np.ndarray) -> list[np.ndarray]:
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


def transform_c2w_list(c2w_rows: list[np.ndarray], T: np.ndarray) -> list[np.ndarray]:
    out = []
    for c2w in c2w_rows:
        M = np.asarray(c2w, dtype=np.float64).copy()
        M[:3, :3] = T[:3, :3] @ M[:3, :3]
        M[:3, 3] = T[:3, :3] @ M[:3, 3] + T[:3, 3]
        out.append(M.astype(np.float32))
    return out


def summarize_candidate(
    *,
    batch_name: str,
    chunk_name: str,
    route_label: str,
    route_source: str,
    route_overlap_record_count: int,
    overlap_record_indices: list[int],
    transformed_rows: list[np.ndarray],
    anchor_df: pd.DataFrame,
    align_diag: dict,
) -> tuple[dict, pd.DataFrame]:
    n = len(transformed_rows)
    pred_center = np.stack([m[:3, 3] for m in transformed_rows], axis=0)
    pred_lens = np.stack([lens_direction_from_c2w(m) for m in transformed_rows], axis=0)
    anchor_center = anchor_df[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=float)
    anchor_lens = anchor_df[["anchor_lens_x", "anchor_lens_y", "anchor_lens_z"]].to_numpy(dtype=float)
    record_indices = anchor_df["record_index"].astype(int).to_numpy()
    overlap_index_set = {int(x) for x in overlap_record_indices}
    overlap_mask = np.array([int(x) in overlap_index_set for x in record_indices], dtype=bool)

    center_error = np.linalg.norm(pred_center - anchor_center, axis=1)
    lens_error_deg = angle_deg(pred_lens, anchor_lens)
    delta_center_error = np.zeros(n, dtype=float)
    delta_lens_error_deg = np.zeros(n, dtype=float)
    if n >= 2:
        delta_center_error[1:] = np.abs(np.diff(center_error))
        delta_lens_error_deg[1:] = np.abs(np.diff(lens_error_deg))

    residual_df = pd.DataFrame({
        "batch_name": batch_name,
        "chunk_name": chunk_name,
        "route_label": route_label,
        "route_source": route_source,
        "route_overlap_record_count": int(route_overlap_record_count),
        "route_overlap_local_count": int(overlap_mask.sum()),
        "route_nonoverlap_local_count": int((~overlap_mask).sum()),
        "route_overlap_record_indices": ",".join(str(int(x)) for x in sorted(overlap_index_set)),
        "local_index": np.arange(n, dtype=np.int64),
        "record_index": record_indices,
        "sequence_index": anchor_df["sequence_index"].astype(int).to_numpy() if "sequence_index" in anchor_df.columns else np.arange(n, dtype=np.int64),
        "is_overlap_record": overlap_mask.astype(bool),
        "center_error": center_error.astype(float),
        "lens_error_deg": lens_error_deg.astype(float),
        "delta_center_error": delta_center_error.astype(float),
        "delta_lens_error_deg": delta_lens_error_deg.astype(float),
        "local_extrinsic_mode": LOCAL_EXTRINSIC_MODE,
        "local_camera_basis": "perm_yxz_sign_ppn",
        "transform_scale": float(align_diag["scale"]),
        "transform_rotation_det": float(align_diag["rotation_det"]),
        "transform_center_rmse": float(align_diag["center_rmse"]),
        "transform_rotation_dir_residual": float(align_diag["rotation_dir_residual"]),
    })

    center_error_p95 = float(np.quantile(center_error, 0.95))
    lens_error_deg_p95 = float(np.quantile(lens_error_deg, 0.95))
    delta_center_error_max = float(delta_center_error.max())
    delta_lens_error_deg_max = float(delta_lens_error_deg.max())
    center_split = summarize_split_metrics(center_error, overlap_mask, "center_error")
    lens_split = summarize_split_metrics(lens_error_deg, overlap_mask, "lens_error_deg")
    residual_warning = bool(
        (center_error_p95 > PREMERGE_CENTER_ERROR_P95_MAX)
        or (lens_error_deg_p95 > PREMERGE_LENS_ERROR_DEG_P95_MAX)
        or (delta_center_error_max > PREMERGE_DELTA_CENTER_ERROR_MAX)
        or (delta_lens_error_deg_max > PREMERGE_DELTA_LENS_ERROR_DEG_MAX)
    )
    candidate = {
        "batch_name": batch_name,
        "chunk_name": chunk_name,
        "route_label": route_label,
        "route_source": route_source,
        "route_overlap_record_count": int(route_overlap_record_count),
        "route_overlap_local_count": int(overlap_mask.sum()),
        "route_nonoverlap_local_count": int((~overlap_mask).sum()),
        "row_count": int(n),
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
        "center_error_mean": float(center_error.mean()),
        "center_error_p95": center_error_p95,
        "lens_error_deg_mean": float(lens_error_deg.mean()),
        "lens_error_deg_p95": lens_error_deg_p95,
        "delta_center_error_max": delta_center_error_max,
        "delta_lens_error_deg_max": delta_lens_error_deg_max,
        "center_error_p95_ok": bool(center_error_p95 <= PREMERGE_CENTER_ERROR_P95_MAX),
        "lens_error_deg_p95_ok": bool(lens_error_deg_p95 <= PREMERGE_LENS_ERROR_DEG_P95_MAX),
        "delta_center_error_ok": bool(delta_center_error_max <= PREMERGE_DELTA_CENTER_ERROR_MAX),
        "delta_lens_error_deg_ok": bool(delta_lens_error_deg_max <= PREMERGE_DELTA_LENS_ERROR_DEG_MAX),
        "align_hard_fail": bool(align_diag["hard_fail"]),
        "anchor_warning": residual_warning,
        "residual_warning": residual_warning,
        "hard_fail": bool(align_diag["hard_fail"]),
    }
    candidate.update(center_split)
    candidate.update(lens_split)
    return candidate, residual_df


def pick_selected_candidate(candidates: list[dict]) -> tuple[dict, bool]:
    by_label = {c["route_label"]: c for c in candidates}
    preferred = by_label.get(PREFERRED_ROUTE_LABEL)
    baseline = by_label.get(ROUTE_ARCORE)
    preferred_anchor_warning = bool(preferred["anchor_warning"]) if preferred is not None else False
    if (
        preferred is not None
        and not preferred["align_hard_fail"]
        and not preferred_anchor_warning
    ):
        selected = preferred
    elif baseline is not None and not baseline["align_hard_fail"]:
        selected = baseline
    elif preferred is not None:
        selected = preferred
    elif baseline is not None:
        selected = baseline
    else:
        raise AssertionError({"reason": "no route candidates"})
    fallback_used = bool(selected["route_label"] != PREFERRED_ROUTE_LABEL)
    return selected, fallback_used


route_world_pose_map: dict[int, np.ndarray] = {}
candidate_rows = []
selected_rows = []
graph_solution_rows = []
graph_edge_rows = []
residual_frames = []
missing_pred_chunks = []
graph_node_measurements = {}
previous_selected_chunk_name = None
previous_selected_T = None

for row in items_df.itertuples(index=False):
    batch_name = str(row.batch_name)
    chunk_name = str(row.chunk_name)
    batch_work_dir = Path(row.batch_work_dir)

    chunk_anchor_csv_value = getattr(row, "chunk_sequence_anchor_csv", "")
    chunk_anchor_csv = None
    if pd.notna(chunk_anchor_csv_value):
        chunk_anchor_csv_value = str(chunk_anchor_csv_value).strip()
        if chunk_anchor_csv_value:
            chunk_anchor_csv = Path(chunk_anchor_csv_value)

    if chunk_anchor_csv is not None and chunk_anchor_csv.exists():
        chunk_df = pd.read_csv(chunk_anchor_csv)
    else:
        chunk_csv_value = getattr(row, "chunk_csv", "")
        assert pd.notna(chunk_csv_value) and str(chunk_csv_value).strip(), {"chunk_name": chunk_name, "reason": "chunk_csv missing"}
        chunk_csv = Path(str(chunk_csv_value).strip())
        assert chunk_csv.exists(), {"chunk_name": chunk_name, "missing_chunk_csv": str(chunk_csv)}
        chunk_base_df = pd.read_csv(chunk_csv)
        assert not chunk_base_df.empty, {"chunk_name": chunk_name, "reason": "empty chunk csv"}
        assert "record_index" in chunk_base_df.columns, {"chunk_name": chunk_name, "reason": "record_index missing in chunk csv"}

        anchor_cols = [c for c in anchor_full_df.columns if c not in chunk_base_df.columns or c == "record_index"]
        chunk_df = chunk_base_df.merge(
            anchor_full_df[anchor_cols].copy(),
            on="record_index",
            how="left",
            validate="many_to_one",
        )

    assert not chunk_df.empty, {"chunk_name": chunk_name, "reason": "empty anchor csv"}
    assert "record_index" in chunk_df.columns, {"chunk_name": chunk_name, "reason": "record_index missing"}

    pred_candidates = [
        batch_work_dir / chunk_name / "pred_extrinsics.npy",
        chunk_runs_dir / chunk_name / "pred_extrinsics.npy",
        batch_work_dir / f"{chunk_name}_pred_extrinsics.npy",
    ]
    pred_path = next((p for p in pred_candidates if p.exists()), None)
    if pred_path is None:
        missing_pred_chunks.append({"batch_name": batch_name, "chunk_name": chunk_name, "reason": "pred_extrinsics.npy not found yet"})
        continue

    existing_anchor_cols = [c for c in required_anchor_cols if c in chunk_df.columns]
    if set(required_anchor_cols).issubset(set(chunk_df.columns)):
        anchor_df = chunk_df.copy()
    else:
        missing_join_cols = [c for c in required_anchor_cols if c not in chunk_df.columns]
        anchor_df = chunk_df.merge(
            anchor_full_df[["record_index", *[c for c in missing_join_cols if c != "record_index"]]].copy(),
            on="record_index",
            how="left",
            validate="many_to_one",
        )
    assert not anchor_df[[c for c in required_anchor_cols[1:] if c in anchor_df.columns]].isnull().any().any(), {
        "chunk_name": chunk_name,
        "reason": "full anchor join failed",
        "missing_columns": [c for c in required_anchor_cols if c not in anchor_df.columns],
    }
    assert set(required_anchor_cols).issubset(set(anchor_df.columns)), {
        "chunk_name": chunk_name,
        "reason": "required anchor columns missing after normalization",
        "missing_columns": [c for c in required_anchor_cols if c not in anchor_df.columns],
    }

    pred = to_4x4_batch(np.load(pred_path))
    n = min(len(anchor_df), pred.shape[0])
    if n <= 1:
        continue
    pred = pred[:n]
    anchor_df = anchor_df.iloc[:n].copy().reset_index(drop=True)

    local_rows = local_c2w_list(pred)
    global_rows = build_anchor_c2w_list(anchor_df)

    baseline_T, baseline_align = estimate_pose_aware_similarity(
        local_rows,
        global_rows,
        estimate_scale=True,
        scale_min=TRANSFORM_SCALE_MIN,
        scale_max=TRANSFORM_SCALE_MAX,
        center_rmse_max=TRANSFORM_CENTER_RMSE_MAX,
        rotation_dir_max=TRANSFORM_ROT_DIR_MAX,
    )
    baseline_transformed = transform_c2w_list(local_rows, baseline_T)
    baseline_candidate, baseline_residual_df = summarize_candidate(
        batch_name=batch_name,
        chunk_name=chunk_name,
        route_label=ROUTE_ARCORE,
        route_source="anchor_full_sequence",
        route_overlap_record_count=int(n),
        overlap_record_indices=anchor_df["record_index"].astype(int).tolist(),
        transformed_rows=baseline_transformed,
        anchor_df=anchor_df,
        align_diag=baseline_align,
    )
    candidate_rows.append(baseline_candidate)
    residual_frames.append(baseline_residual_df)

    overlap_local_rows = []
    overlap_world_rows = []
    overlap_record_indices = []
    for idx, record_index in enumerate(anchor_df["record_index"].astype(int).tolist()):
        if record_index in route_world_pose_map:
            overlap_local_rows.append(local_rows[idx])
            overlap_world_rows.append(route_world_pose_map[record_index])
            overlap_record_indices.append(int(record_index))

    if overlap_world_rows:
        experimental_source = "predicted_overlap"
        experimental_overlap_record_count = len(overlap_world_rows)
        if len(overlap_world_rows) >= 2:
            experimental_T, experimental_align = estimate_pose_aware_similarity(
                overlap_local_rows,
                overlap_world_rows,
                estimate_scale=True,
                scale_min=TRANSFORM_SCALE_MIN,
                scale_max=TRANSFORM_SCALE_MAX,
                center_rmse_max=TRANSFORM_CENTER_RMSE_MAX,
                rotation_dir_max=TRANSFORM_ROT_DIR_MAX,
            )
        else:
            experimental_T = baseline_T.copy()
            experimental_align = dict(baseline_align)
            experimental_align["center_rmse"] = float(baseline_align["center_rmse"])
            experimental_align["rotation_dir_residual"] = float(baseline_align["rotation_dir_residual"])
            experimental_source = "predicted_overlap_seeded_single_record"
    else:
        experimental_source = "seed_from_arcore_baseline"
        experimental_overlap_record_count = 0
        experimental_T = baseline_T.copy()
        experimental_align = dict(baseline_align)

    experimental_transformed = transform_c2w_list(local_rows, experimental_T)
    experimental_candidate, experimental_residual_df = summarize_candidate(
        batch_name=batch_name,
        chunk_name=chunk_name,
        route_label=ROUTE_DA3,
        route_source=experimental_source,
        route_overlap_record_count=int(experimental_overlap_record_count),
        overlap_record_indices=overlap_record_indices,
        transformed_rows=experimental_transformed,
        anchor_df=anchor_df,
        align_diag=experimental_align,
    )
    candidate_rows.append(experimental_candidate)
    residual_frames.append(experimental_residual_df)

    candidates = [baseline_candidate, experimental_candidate]
    selected_candidate, fallback_used = pick_selected_candidate(candidates)
    selected_candidate = dict(selected_candidate)
    selected_candidate["preferred_route_label"] = PREFERRED_ROUTE_LABEL
    selected_candidate["fallback_used"] = bool(fallback_used)
    selected_candidate["fallback_reason"] = (
        None if not fallback_used else "preferred_route_hard_fail_or_unavailable"
    )

    selected_transformed = experimental_transformed if selected_candidate["route_label"] == ROUTE_DA3 else baseline_transformed
    selected_T = experimental_T if selected_candidate["route_label"] == ROUTE_DA3 else baseline_T
    selected_align = experimental_align if selected_candidate["route_label"] == ROUTE_DA3 else baseline_align
    for record_index, world_pose in zip(anchor_df["record_index"].astype(int).tolist(), selected_transformed):
        route_world_pose_map[int(record_index)] = world_pose

    graph_parent_chunk_name = previous_selected_chunk_name
    relative_transform = summarize_relative_transform(previous_selected_T, selected_T)
    selected_candidate["graph_parent_chunk_name"] = graph_parent_chunk_name
    selected_candidate["relative_scale"] = float(relative_transform["relative_scale"])
    selected_candidate["relative_translation_norm"] = float(relative_transform["relative_translation_norm"])
    selected_candidate["relative_rotation_deg"] = float(relative_transform["relative_rotation_deg"])
    if bool(selected_candidate["fallback_used"]):
        selected_candidate["fallback_reason"] = "preferred_route_warning_or_hard_fail"
    selected_rows.append(selected_candidate)
    graph_node_measurements[chunk_name] = {
        "batch_name": batch_name,
        "chunk_name": chunk_name,
        "local_rows": [m.copy() for m in local_rows],
        "anchor_df": anchor_df.copy(),
        "overlap_record_indices": [int(x) for x in overlap_record_indices],
        "route_source": str(selected_candidate["route_source"]),
    }

    graph_solution_row = {
        "batch_name": batch_name,
        "chunk_name": chunk_name,
        "graph_parent_chunk_name": graph_parent_chunk_name,
        "route_label": str(selected_candidate["route_label"]),
        "requested_route_label": str(selected_candidate["route_label"]),
        "preferred_route_label": PREFERRED_ROUTE_LABEL,
        "fallback_used": bool(fallback_used),
        "preferred_fallback_used": bool(str(selected_candidate["route_label"]) != PREFERRED_ROUTE_LABEL),
        "route_source": str(selected_candidate["route_source"]),
        "route_overlap_record_count": int(selected_candidate["route_overlap_record_count"]),
        "route_overlap_local_count": int(selected_candidate.get("route_overlap_local_count", 0)),
        "route_nonoverlap_local_count": int(selected_candidate.get("route_nonoverlap_local_count", 0)),
        "row_count": int(n),
        "local_extrinsic_mode": LOCAL_EXTRINSIC_MODE,
        "local_camera_basis": "perm_yxz_sign_ppn",
        "scale": float(selected_align["scale"]),
        "rotation_det": float(selected_align["rotation_det"]),
        "center_rmse": float(selected_align["center_rmse"]),
        "rotation_dir_residual": float(selected_align["rotation_dir_residual"]),
        "positive_similarity_ok": bool(selected_align["positive_similarity_ok"]),
        "scale_in_range_ok": bool(selected_align["scale_in_range_ok"]),
        "center_rmse_ok": bool(selected_align["center_rmse_ok"]),
        "rotation_dir_ok": bool(selected_align["rotation_dir_ok"]),
        "align_hard_fail": bool(selected_align["hard_fail"]),
        "residual_hard_fail": bool(selected_candidate["hard_fail"]),
        "hard_fail": bool(selected_candidate["hard_fail"]),
        "center_error_mean": float(selected_candidate["center_error_mean"]),
        "center_error_p95": float(selected_candidate["center_error_p95"]),
        "lens_error_deg_mean": float(selected_candidate["lens_error_deg_mean"]),
        "lens_error_deg_p95": float(selected_candidate["lens_error_deg_p95"]),
        "delta_center_error_max": float(selected_candidate["delta_center_error_max"]),
        "delta_lens_error_deg_max": float(selected_candidate["delta_lens_error_deg_max"]),
        "center_error_overlap_p95": selected_candidate.get("center_error_overlap_p95"),
        "center_error_nonoverlap_p95": selected_candidate.get("center_error_nonoverlap_p95"),
        "lens_error_deg_overlap_p95": selected_candidate.get("lens_error_deg_overlap_p95"),
        "lens_error_deg_nonoverlap_p95": selected_candidate.get("lens_error_deg_nonoverlap_p95"),
        "relative_scale": float(relative_transform["relative_scale"]),
        "relative_translation_norm": float(relative_transform["relative_translation_norm"]),
        "relative_rotation_deg": float(relative_transform["relative_rotation_deg"]),
    }
    for r in range(4):
        for c in range(4):
            graph_solution_row[f"t{r}{c}"] = float(selected_T[r, c])
    graph_solution_rows.append(graph_solution_row)
    graph_edge_rows.append({
        "batch_name": batch_name,
        "chunk_name": chunk_name,
        "graph_parent_chunk_name": graph_parent_chunk_name,
        "route_label": str(selected_candidate["route_label"]),
        "route_source": str(selected_candidate["route_source"]),
        "route_overlap_record_count": int(selected_candidate["route_overlap_record_count"]),
        "route_overlap_local_count": int(selected_candidate.get("route_overlap_local_count", 0)),
        "route_nonoverlap_local_count": int(selected_candidate.get("route_nonoverlap_local_count", 0)),
        "center_error_overlap_p95": selected_candidate.get("center_error_overlap_p95"),
        "center_error_nonoverlap_p95": selected_candidate.get("center_error_nonoverlap_p95"),
        "lens_error_deg_overlap_p95": selected_candidate.get("lens_error_deg_overlap_p95"),
        "lens_error_deg_nonoverlap_p95": selected_candidate.get("lens_error_deg_nonoverlap_p95"),
        "relative_scale": float(relative_transform["relative_scale"]),
        "relative_translation_norm": float(relative_transform["relative_translation_norm"]),
        "relative_rotation_deg": float(relative_transform["relative_rotation_deg"]),
        "center_rmse": float(selected_align["center_rmse"]),
        "rotation_dir_residual": float(selected_align["rotation_dir_residual"]),
        "fallback_used": bool(fallback_used),
        "preferred_fallback_used": bool(str(selected_candidate["route_label"]) != PREFERRED_ROUTE_LABEL),
        "hard_fail": bool(selected_candidate["hard_fail"]),
    })
    previous_selected_chunk_name = chunk_name
    previous_selected_T = selected_T.copy()

candidate_df = pd.DataFrame(candidate_rows)
route_compare_csv = merged_dir / "premerge_route_compare_arc.csv"
candidate_df.to_csv(route_compare_csv, index=False, encoding="utf-8")

residual_df = pd.concat(residual_frames, ignore_index=True) if residual_frames else pd.DataFrame()
residual_csv = chunk_manifest_dir / "pred_vs_anchor_pose_residual.csv"
residual_df.to_csv(residual_csv, index=False, encoding="utf-8")

missing_pred_df = pd.DataFrame(missing_pred_chunks)
missing_pred_csv = chunk_manifest_dir / "pred_vs_anchor_pose_residual_missing_pred.csv"
missing_pred_df.to_csv(missing_pred_csv, index=False, encoding="utf-8")



def sim3_matrix_to_params(T: np.ndarray, allow_scale: bool = True) -> np.ndarray:
    T = np.asarray(T, dtype=np.float64)
    A = T[:3, :3]
    det = float(np.linalg.det(A))
    scale = np.cbrt(abs(det)) if abs(det) > 1e-12 else 1.0
    scale = max(scale, 1e-8)
    Rm = A / scale
    U, _, Vt = np.linalg.svd(Rm)
    Rm = U @ Vt
    if np.linalg.det(Rm) < 0:
        U[:, -1] *= -1.0
        Rm = U @ Vt
    rotvec = SciRot.from_matrix(Rm).as_rotvec()
    t = T[:3, 3].astype(np.float64)
    log_scale = math.log(scale) if allow_scale else 0.0
    return np.concatenate([rotvec, t, np.array([log_scale], dtype=np.float64)])


def params_to_sim3_matrix(params: np.ndarray, allow_scale: bool = True) -> np.ndarray:
    params = np.asarray(params, dtype=np.float64)
    rot = SciRot.from_rotvec(params[:3]).as_matrix()
    t = params[3:6]
    scale = math.exp(float(params[6])) if allow_scale else 1.0
    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = scale * rot
    T[:3, 3] = t
    return T


def invert_sim3(T: np.ndarray) -> np.ndarray:
    T = np.asarray(T, dtype=np.float64)
    A = T[:3, :3]
    t = T[:3, 3]
    A_inv = np.linalg.inv(A)
    out = np.eye(4, dtype=np.float64)
    out[:3, :3] = A_inv
    out[:3, 3] = -(A_inv @ t)
    return out


def compose_sim3(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return np.asarray(A, dtype=np.float64) @ np.asarray(B, dtype=np.float64)


def edge_transform_from_row(row: pd.Series) -> np.ndarray:
    T = np.eye(4, dtype=np.float64)
    for r in range(4):
        for c in range(4):
            key = f"t{r}{c}"
            T[r, c] = float(row[key])
    return T


def sim3_residual_vec(pred: np.ndarray, target: np.ndarray, allow_scale: bool = True) -> np.ndarray:
    pred_p = sim3_matrix_to_params(pred, allow_scale=allow_scale)
    tgt_p = sim3_matrix_to_params(target, allow_scale=allow_scale)
    return pred_p - tgt_p


def refine_graph_solution(
    initial_solution_df: pd.DataFrame,
    edge_df: pd.DataFrame,
    node_measurements: dict[str, dict],
    allow_scale: bool = True,
):
    if len(initial_solution_df) <= 1:
        summary = {
            "optimization_enabled": True,
            "allow_scale": bool(allow_scale),
            "status": "skipped_single_chunk",
            "node_count": int(len(initial_solution_df)),
            "edge_count": int(len(edge_df)),
        }
        return initial_solution_df.copy(), edge_df.copy(), summary

    node_names = initial_solution_df["chunk_name"].astype(str).tolist()
    root_name = str(node_names[0])
    init_map = {str(r.chunk_name): edge_transform_from_row(pd.Series(r._asdict())) for r in initial_solution_df.itertuples(index=False)}
    name_to_idx = {name: i for i, name in enumerate(node_names)}
    opt_names = [name for name in node_names if name != root_name]

    x0 = []
    for name in opt_names:
        x0.append(sim3_matrix_to_params(init_map[name], allow_scale=allow_scale))
    x0 = np.concatenate(x0, axis=0) if x0 else np.zeros((0,), dtype=np.float64)

    def unpack(x: np.ndarray):
        out = {root_name: init_map[root_name].copy()}
        offset = 0
        for name in opt_names:
            out[name] = params_to_sim3_matrix(x[offset:offset+7], allow_scale=allow_scale)
            offset += 7
        return out

    edge_records = []
    for row in edge_df.itertuples(index=False):
        child = str(row.chunk_name)
        parent = str(row.graph_parent_chunk_name) if pd.notna(row.graph_parent_chunk_name) else None
        if not parent or parent == 'nan':
            continue
        T_child = init_map[child]
        T_parent = init_map[parent]
        T_rel = compose_sim3(invert_sim3(T_parent), T_child)
        overlap = float(getattr(row, 'route_overlap_local_count', 0) or 0)
        quality = 1.0 / max(float(getattr(row, 'center_rmse', 0.02) or 0.02), 1e-3)
        weight = max(1.0, min(10.0, overlap + 1.0)) * max(0.5, min(8.0, quality * 0.1))
        edge_records.append((parent, child, T_rel, weight))

    def residual_fn(x: np.ndarray) -> np.ndarray:
        T_map = unpack(x)
        res = []
        for parent, child, T_rel, weight in edge_records:
            pred_rel = compose_sim3(invert_sim3(T_map[parent]), T_map[child])
            rv = sim3_residual_vec(pred_rel, T_rel, allow_scale=allow_scale)
            rv[:3] *= GRAPH_EDGE_ROTATION_WEIGHT
            rv[3:6] *= GRAPH_EDGE_TRANSLATION_WEIGHT
            rv[6] *= GRAPH_EDGE_SCALE_WEIGHT if allow_scale else 0.0
            res.append(math.sqrt(weight) * rv)
        for name in opt_names:
            prior = sim3_residual_vec(T_map[name], init_map[name], allow_scale=allow_scale)
            prior[:3] *= GRAPH_ANCHOR_ROT_WEIGHT
            prior[3:6] *= GRAPH_ANCHOR_WEIGHT
            prior[6] *= GRAPH_ANCHOR_WEIGHT if allow_scale else 0.0
            res.append(GRAPH_PRIOR_WEIGHT * prior)
        for name in opt_names:
            measurement = node_measurements.get(name)
            if measurement is None:
                continue
            transformed_rows = transform_c2w_list(measurement["local_rows"], T_map[name])
            anchor_df = measurement["anchor_df"]
            overlap_index_set = {int(x) for x in measurement["overlap_record_indices"]}
            for idx, (world_pose, anchor_row) in enumerate(zip(transformed_rows, anchor_df.itertuples(index=False))):
                record_index = int(anchor_row.record_index)
                frame_weight = (
                    GRAPH_ANCHOR_OVERLAP_FRAME_WEIGHT
                    if record_index in overlap_index_set
                    else GRAPH_ANCHOR_NONOVERLAP_FRAME_WEIGHT
                )
                pred_center = np.asarray(world_pose[:3, 3], dtype=np.float64)
                anchor_center = np.array(
                    [float(anchor_row.cx_world), float(anchor_row.cy_world), float(anchor_row.cz_world)],
                    dtype=np.float64,
                )
                center_res = (pred_center - anchor_center) * (GRAPH_ANCHOR_FRAME_TRANSLATION_WEIGHT * frame_weight)
                res.append(center_res)

                pred_lens = lens_direction_from_c2w(world_pose).astype(np.float64)
                anchor_lens = normalize_vec(
                    np.array(
                        [float(anchor_row.anchor_lens_x), float(anchor_row.anchor_lens_y), float(anchor_row.anchor_lens_z)],
                        dtype=np.float64,
                    ),
                    np.array([0.0, 0.0, -1.0], dtype=np.float64),
                )
                lens_res = (pred_lens - anchor_lens) * (GRAPH_ANCHOR_FRAME_DIRECTION_WEIGHT * frame_weight)
                res.append(lens_res)
        if not res:
            return np.zeros((0,), dtype=np.float64)
        return np.concatenate(res, axis=0)

    lsq = least_squares(residual_fn, x0, loss='soft_l1', f_scale=1.0, max_nfev=GRAPH_OPT_MAX_NFEV)
    refined_map = unpack(lsq.x)

    refined_solution_df = initial_solution_df.copy()
    refined_solution_df['graph_optimization_enabled'] = True
    refined_solution_df['graph_optimization_allow_scale'] = bool(allow_scale)
    refined_solution_df['graph_optimization_cost'] = float(lsq.cost)
    refined_solution_df['graph_optimization_success'] = bool(lsq.success)
    refined_solution_df['graph_optimization_status'] = int(lsq.status)
    refined_solution_df['graph_optimization_nfev'] = int(lsq.nfev)
    refined_solution_df['graph_optimization_optimality'] = float(lsq.optimality)

    for idx, row in refined_solution_df.iterrows():
        T = refined_map[str(row['chunk_name'])]
        for r in range(4):
            for c in range(4):
                refined_solution_df.at[idx, f't{r}{c}'] = float(T[r, c])

    refined_edges_df = edge_df.copy()
    opt_edge_residuals = []
    for idx, row in refined_edges_df.iterrows():
        child = str(row['chunk_name'])
        parent = row['graph_parent_chunk_name']
        if pd.isna(parent):
            refined_edges_df.at[idx, 'graph_opt_edge_translation_residual'] = 0.0
            refined_edges_df.at[idx, 'graph_opt_edge_rotation_residual_deg'] = 0.0
            refined_edges_df.at[idx, 'graph_opt_edge_log_scale_residual'] = 0.0
            continue
        parent = str(parent)
        pred_rel = compose_sim3(invert_sim3(refined_map[parent]), refined_map[child])
        init_rel = compose_sim3(invert_sim3(init_map[parent]), init_map[child])
        rv = sim3_residual_vec(pred_rel, init_rel, allow_scale=allow_scale)
        trans_res = float(np.linalg.norm(rv[3:6]))
        rot_res_deg = float(np.degrees(np.linalg.norm(rv[:3])))
        scale_res = float(abs(rv[6])) if allow_scale else 0.0
        refined_edges_df.at[idx, 'graph_opt_edge_translation_residual'] = trans_res
        refined_edges_df.at[idx, 'graph_opt_edge_rotation_residual_deg'] = rot_res_deg
        refined_edges_df.at[idx, 'graph_opt_edge_log_scale_residual'] = scale_res
        opt_edge_residuals.append((trans_res, rot_res_deg, scale_res))

    summary = {
        "optimization_enabled": True,
        "allow_scale": bool(allow_scale),
        "status": "ok" if bool(lsq.success) else "warning",
        "success": bool(lsq.success),
        "solver_status": int(lsq.status),
        "message": str(lsq.message),
        "cost": float(lsq.cost),
        "optimality": float(lsq.optimality),
        "nfev": int(lsq.nfev),
        "node_count": int(len(initial_solution_df)),
        "edge_count": int(len(edge_records)),
    }
    if opt_edge_residuals:
        trans_vals = np.asarray([x[0] for x in opt_edge_residuals], dtype=float)
        rot_vals = np.asarray([x[1] for x in opt_edge_residuals], dtype=float)
        scale_vals = np.asarray([x[2] for x in opt_edge_residuals], dtype=float)
        summary.update({
            "edge_translation_residual_mean": float(trans_vals.mean()),
            "edge_translation_residual_p95": float(np.quantile(trans_vals, 0.95)),
            "edge_rotation_residual_deg_mean": float(rot_vals.mean()),
            "edge_rotation_residual_deg_p95": float(np.quantile(rot_vals, 0.95)),
            "edge_log_scale_residual_mean": float(scale_vals.mean()),
            "edge_log_scale_residual_p95": float(np.quantile(scale_vals, 0.95)),
        })
    return refined_solution_df, refined_edges_df, summary


def recompute_solution_metrics(solution_df: pd.DataFrame, node_measurements: dict[str, dict]) -> pd.DataFrame:
    if solution_df.empty:
        return solution_df.copy()
    refreshed_rows = []
    for row in solution_df.itertuples(index=False):
        chunk_name = str(row.chunk_name)
        measurement = node_measurements.get(chunk_name)
        if measurement is None:
            refreshed_rows.append(pd.Series(row._asdict()).to_dict())
            continue
        T = edge_transform_from_row(pd.Series(row._asdict()))
        transformed_rows = transform_c2w_list(measurement["local_rows"], T)
        align_diag = {
            "scale": float(getattr(row, "scale")),
            "rotation_det": float(getattr(row, "rotation_det")),
            "center_rmse": float(getattr(row, "center_rmse")),
            "rotation_dir_residual": float(getattr(row, "rotation_dir_residual")),
            "positive_similarity_ok": bool(getattr(row, "positive_similarity_ok")),
            "scale_in_range_ok": bool(getattr(row, "scale_in_range_ok")),
            "center_rmse_ok": bool(getattr(row, "center_rmse_ok")),
            "rotation_dir_ok": bool(getattr(row, "rotation_dir_ok")),
            "hard_fail": bool(getattr(row, "align_hard_fail", getattr(row, "hard_fail"))),
        }
        refreshed_candidate, _ = summarize_candidate(
            batch_name=str(getattr(row, "batch_name")),
            chunk_name=chunk_name,
            route_label=str(getattr(row, "route_label")),
            route_source=str(getattr(row, "route_source")),
            route_overlap_record_count=int(getattr(row, "route_overlap_record_count")),
            overlap_record_indices=measurement["overlap_record_indices"],
            transformed_rows=transformed_rows,
            anchor_df=measurement["anchor_df"],
            align_diag=align_diag,
        )
        row_dict = pd.Series(row._asdict()).to_dict()
        row_dict.update(refreshed_candidate)
        row_dict["hard_fail"] = bool(row_dict["align_hard_fail"] or row_dict["anchor_warning"])
        refreshed_candidate = row_dict
        refreshed_rows.append(refreshed_candidate)
    return pd.DataFrame(refreshed_rows)

graph_solution_df = pd.DataFrame(graph_solution_rows)
graph_edges_df = pd.DataFrame(graph_edge_rows)

graph_optimization_summary = {
    "optimization_enabled": False,
    "status": "not_run",
    "allow_scale": bool(SIM3_GRAPH_OPTIMIZATION),
}
if len(graph_solution_df):
    graph_solution_df, graph_edges_df, graph_optimization_summary = refine_graph_solution(
        graph_solution_df,
        graph_edges_df,
        graph_node_measurements,
        allow_scale=bool(SIM3_GRAPH_OPTIMIZATION),
    )
    graph_solution_df = recompute_solution_metrics(graph_solution_df, graph_node_measurements)

validation_df = graph_solution_df.copy() if len(graph_solution_df) else pd.DataFrame(selected_rows)
validation_csv = merged_dir / "premerge_pose_validation.csv"
validation_df.to_csv(validation_csv, index=False, encoding="utf-8")

gate_csv = chunk_manifest_dir / "premerge_pose_gate.csv"
validation_df.to_csv(gate_csv, index=False, encoding="utf-8")

graph_solution_csv = merged_dir / "prepose_chunk_graph_solution_arc.csv"
graph_solution_df.to_csv(graph_solution_csv, index=False, encoding="utf-8")

graph_edges_csv = merged_dir / "prepose_chunk_graph_edges_arc.csv"
graph_edges_df.to_csv(graph_edges_csv, index=False, encoding="utf-8")

validation_json = merged_dir / "premerge_pose_validation.json"
route_compare_json = merged_dir / "premerge_route_compare_summary.json"
graph_summary_json = merged_dir / "prepose_chunk_graph_summary.json"
graph_opt_summary_json = merged_dir / "prepose_graph_optimization_summary.json"
hard_fail_df = validation_df[validation_df["hard_fail"]].copy() if len(validation_df) else validation_df.copy()
anchor_warning_df = validation_df[validation_df["anchor_warning"].fillna(False).astype(bool)].copy() if len(validation_df) else validation_df.copy()

if len(validation_df) == 0:
    status = "not_run"
elif len(missing_pred_df) > 0:
    status = "partial"
elif len(hard_fail_df) > 0:
    status = "fail"
elif len(anchor_warning_df) > 0:
    status = "warning"
else:
    status = "ok"

route_counts = (
    validation_df.groupby("route_label", as_index=False).size().rename(columns={"size": "chunk_count"}).to_dict(orient="records")
    if len(validation_df)
    else []
)
fallback_count = int(validation_df["fallback_used"].fillna(False).astype(bool).sum()) if len(validation_df) else 0
route_compare_summary = {
    "status": status,
    "route": "continuous-gs-v06-chunk18-overlap6-adopt12-route-compare",
    "candidate_row_count": int(len(candidate_df)),
    "selected_chunk_count": int(len(validation_df)),
    "selected_route_counts": route_counts,
    "fallback_count": fallback_count,
    "preferred_route_label": PREFERRED_ROUTE_LABEL,
    "route_compare_csv": str(route_compare_csv),
    "prepose_chunk_graph_solution_csv": str(graph_solution_csv),
    "prepose_chunk_graph_edges_csv": str(graph_edges_csv),
    "selected_chunks": validation_df[
        [
            "chunk_name",
            "route_label",
            "route_source",
            "fallback_used",
            "route_overlap_record_count",
            "route_overlap_local_count",
            "route_nonoverlap_local_count",
            "center_error_p95",
            "lens_error_deg_p95",
            "center_error_overlap_p95",
            "center_error_nonoverlap_p95",
            "lens_error_deg_overlap_p95",
            "lens_error_deg_nonoverlap_p95",
            "relative_rotation_deg",
            "relative_translation_norm",
            "relative_scale",
            "center_rmse",
            "rotation_dir_residual",
        ]
    ].to_dict(orient="records") if len(validation_df) else [],
}

graph_summary = {
    "status": status,
    "graph_optimization": graph_optimization_summary,
    "route": "continuous-gs-v06-chunk18-overlap6-adopt12-prepose-graph-build",
    "selected_chunk_count": int(len(graph_solution_df)),
    "preferred_route_label": PREFERRED_ROUTE_LABEL,
    "preferred_fallback_used_count": int(graph_solution_df["preferred_fallback_used"].fillna(False).astype(bool).sum()) if len(graph_solution_df) else 0,
    "graph_solution_csv": str(graph_solution_csv),
    "graph_edges_csv": str(graph_edges_csv),
    "selected_chunks": graph_solution_df[
        [
            "chunk_name",
            "graph_parent_chunk_name",
            "route_label",
            "route_source",
            "fallback_used",
            "preferred_fallback_used",
            "route_overlap_local_count",
            "route_nonoverlap_local_count",
            "center_error_overlap_p95",
            "center_error_nonoverlap_p95",
            "lens_error_deg_overlap_p95",
            "lens_error_deg_nonoverlap_p95",
            "relative_rotation_deg",
            "relative_translation_norm",
            "relative_scale",
            "center_rmse",
            "rotation_dir_residual",
        ]
    ].to_dict(orient="records") if len(graph_solution_df) else [],
}

summary = {
    "status": status,
    "route": "continuous-gs-v06-chunk18-overlap6-adopt12-premerge-pose-gate",
    "residual_row_count": int(len(residual_df)),
    "missing_pred_chunk_count": int(len(missing_pred_df)),
    "gate_chunk_count": int(len(validation_df)),
    "residual_csv": str(residual_csv),
    "missing_pred_csv": str(missing_pred_csv),
    "gate_csv": str(gate_csv),
    "validation_csv": str(validation_csv),
    "route_compare_csv": str(route_compare_csv),
    "route_compare_json": str(route_compare_json),
    "prepose_chunk_graph_solution_csv": str(graph_solution_csv),
    "prepose_chunk_graph_edges_csv": str(graph_edges_csv),
    "prepose_chunk_graph_summary_json": str(graph_summary_json),
    "prepose_graph_optimization_summary_json": str(graph_opt_summary_json),
    "preferred_route_label": PREFERRED_ROUTE_LABEL,
    "thresholds": {
        "center_error_p95_max": PREMERGE_CENTER_ERROR_P95_MAX,
        "lens_error_deg_p95_max": PREMERGE_LENS_ERROR_DEG_P95_MAX,
        "delta_center_error_max": PREMERGE_DELTA_CENTER_ERROR_MAX,
        "delta_lens_error_deg_max": PREMERGE_DELTA_LENS_ERROR_DEG_MAX,
        "transform_scale_min": TRANSFORM_SCALE_MIN,
        "transform_scale_max": TRANSFORM_SCALE_MAX,
        "transform_center_rmse_max": TRANSFORM_CENTER_RMSE_MAX,
        "transform_rotation_dir_residual_max": TRANSFORM_ROT_DIR_MAX,
    },
    "tested_chunk_count": int(len(validation_df)),
    "hard_fail_count": int(len(hard_fail_df)),
    "anchor_warning_count": int(len(anchor_warning_df)),
    "fallback_count": fallback_count,
    "selected_route_counts": route_counts,
    "failed_chunks": hard_fail_df[
        [
            "chunk_name",
            "route_label",
            "center_error_p95",
            "lens_error_deg_p95",
            "delta_center_error_max",
            "delta_lens_error_deg_max",
            "center_rmse",
            "rotation_dir_residual",
        ]
    ].to_dict(orient="records") if len(hard_fail_df) else [],
    "anchor_warning_chunks": validation_df[
        [
            "chunk_name",
            "route_label",
            "route_source",
            "center_error_p95",
            "lens_error_deg_p95",
            "delta_center_error_max",
            "delta_lens_error_deg_max",
        ]
    ].loc[validation_df["anchor_warning"].fillna(False).astype(bool)].to_dict(orient="records") if len(validation_df) else [],
}
if len(validation_df):
    summary["center_error_mean"] = float(validation_df["center_error_mean"].mean())
    summary["center_error_p95"] = float(validation_df["center_error_p95"].quantile(0.95))
    summary["lens_error_deg_mean"] = float(validation_df["lens_error_deg_mean"].mean())
    summary["lens_error_deg_p95"] = float(validation_df["lens_error_deg_p95"].quantile(0.95))
    summary["transform_scale_mean"] = float(validation_df["scale"].mean())
    summary["transform_center_rmse_mean"] = float(validation_df["center_rmse"].mean())
    summary["transform_rotation_dir_residual_mean"] = float(validation_df["rotation_dir_residual"].mean())
    summary["selected_chunks"] = validation_df[
        [
            "chunk_name",
            "route_label",
            "route_source",
            "fallback_used",
            "route_overlap_record_count",
            "route_overlap_local_count",
            "route_nonoverlap_local_count",
            "center_error_p95",
            "lens_error_deg_p95",
            "center_error_overlap_p95",
            "center_error_nonoverlap_p95",
            "lens_error_deg_overlap_p95",
            "lens_error_deg_nonoverlap_p95",
            "relative_rotation_deg",
            "relative_translation_norm",
            "relative_scale",
            "center_rmse",
            "rotation_dir_residual",
        ]
    ].to_dict(orient="records")

save_json(route_compare_json, route_compare_summary)
save_json(graph_summary_json, graph_summary)
save_json(graph_opt_summary_json, graph_optimization_summary)
save_json(validation_json, summary)
save_json(final_outputs_diagnostics_dir / "premerge_route_compare_summary.json", route_compare_summary)
save_json(final_outputs_diagnostics_dir / "prepose_chunk_graph_summary.json", graph_summary)
save_json(final_outputs_diagnostics_dir / "prepose_graph_optimization_summary.json", graph_optimization_summary)
save_json(final_outputs_diagnostics_dir / "premerge_pose_gate_summary.json", summary)
save_json(final_outputs_diagnostics_dir / "batch_residual_summary.json", summary)
save_json(final_outputs_diagnostics_dir / "premerge_pose_validation.json", summary)

print(json.dumps(summary, indent=2, ensure_ascii=False))
if len(validation_df):
    display(validation_df)
if len(candidate_df):
    display(candidate_df)
if len(missing_pred_df):
    display(missing_pred_df.head())
display_stage_summary(
    "10-1",
    "prepose graph build and gate",
    inputs=[
        {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
        {"item": "camera_anchor_full_arc", "path": str(camera_anchor_full_path)},
    ],
    outputs=[
        {"item": "pred_vs_anchor_pose_residual", "path": str(residual_csv)},
        {"item": "pred_vs_anchor_pose_residual_missing_pred", "path": str(missing_pred_csv)},
        {"item": "premerge_pose_gate", "path": str(gate_csv)},
        {"item": "premerge_route_compare_summary", "path": str(route_compare_json)},
        {"item": "prepose_chunk_graph_solution", "path": str(graph_solution_csv)},
        {"item": "prepose_chunk_graph_edges", "path": str(graph_edges_csv)},
        {"item": "prepose_chunk_graph_summary", "path": str(graph_summary_json)},
        {"item": "prepose_graph_optimization_summary", "path": str(graph_opt_summary_json)},
        {"item": "premerge_pose_gate_summary", "path": str(final_outputs_diagnostics_dir / "premerge_pose_gate_summary.json")},
        {"item": "premerge_pose_validation", "path": str(validation_json)},
        {"item": "batch_residual_summary", "path": str(final_outputs_diagnostics_dir / "batch_residual_summary.json")},
    ],
    notes=[
        {"item": "status", "value": status},
        {"item": "preferred_route_label", "value": PREFERRED_ROUTE_LABEL},
        {"item": "missing_pred_chunk_count", "value": int(len(missing_pred_df))},
        {"item": "hard_fail_count", "value": int(len(hard_fail_df))},
        {"item": "anchor_warning_count", "value": int(len(anchor_warning_df))},
        {"item": "fallback_count", "value": fallback_count},
    ],
)

# TODO(from pre-#7 deferred anchor-derived features):
# - #9-2 で行っていた full_anchor_pose_diag_arc.csv の record manifest 結合
# - #9-4 で行っていた camera_anchor_full_arc.csv -> chunk_xxx_sequence_anchor.csv / chunk_sequence_anchor_index.csv 生成
# - #9-5 で行っていた sequence-anchor 派生列 / adjacent edge 派生列の付与
# - #10-2 で行っていた adjacent edge validation
# - #10-3 で行っていた full_anchor_pose_qc_arc.csv を用いた anchor QC summary
# - #11-4 で行っていた anchor pose / anchor QC を含む preflight 拡張
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
graph_solution_csv = merged_dir / "prepose_chunk_graph_solution_arc.csv"
graph_edges_csv = merged_dir / "prepose_chunk_graph_edges_arc.csv"
graph_summary_json = merged_dir / "prepose_chunk_graph_summary.json"
batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"

required_paths = [
    validation_json,
    route_compare_json,
    route_compare_csv,
    graph_solution_csv,
    graph_edges_csv,
    graph_summary_json,
    batch_execution_items_path,
]
missing_paths = [str(path) for path in required_paths if not path.exists()]
assert not missing_paths, {"reason": "missing_prepose_graph_artifacts", "missing_paths": missing_paths}

validation = load_json(validation_json)
route_compare_summary = load_json(route_compare_json)
graph_summary = load_json(graph_summary_json)

validation_df = pd.read_csv(graph_solution_csv)
route_compare_df = pd.read_csv(route_compare_csv)
graph_edges_df = pd.read_csv(graph_edges_csv)

status = str(validation.get("status", "missing"))
selected_route_counts = validation.get("selected_route_counts", route_compare_summary.get("selected_route_counts", []))
preferred_route_label = str(validation.get("preferred_route_label", route_compare_summary.get("preferred_route_label", "")))
preferred_fallback_used_count = int(validation.get("preferred_fallback_used_count", 0))

review_summary = {
    "status": status,
    "route": "continuous-gs-v06-chunk18-overlap6-adopt12-prepose-graph-review",
    "preferred_route_label": preferred_route_label,
    "selected_route_counts": selected_route_counts,
    "preferred_fallback_used_count": preferred_fallback_used_count,
    "tested_chunk_count": int(validation.get("tested_chunk_count", len(validation_df))),
    "hard_fail_count": int(validation.get("hard_fail_count", 0)),
    "anchor_warning_count": int(validation.get("anchor_warning_count", 0)),
    "route_compare_csv": str(route_compare_csv),
    "prepose_chunk_graph_solution_csv": str(graph_solution_csv),
    "prepose_chunk_graph_edges_csv": str(graph_edges_csv),
    "prepose_chunk_graph_summary_json": str(graph_summary_json),
    "premerge_pose_validation_json": str(validation_json),
}
save_json(final_outputs_diagnostics_dir / "prepose_graph_gate_review.json", review_summary)

print(json.dumps(review_summary, indent=2, ensure_ascii=False))
if len(validation_df):
    display(validation_df)
if len(route_compare_df):
    display(route_compare_df)
if len(graph_edges_df):
    display(graph_edges_df)

display_stage_summary(
    "10-2",
    "prepose graph review gate",
    inputs=[
        {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
        {"item": "premerge_pose_validation", "path": str(validation_json)},
        {"item": "premerge_route_compare_summary", "path": str(route_compare_json)},
        {"item": "prepose_chunk_graph_summary", "path": str(graph_summary_json)},
    ],
    outputs=[
        {"item": "premerge_route_compare", "path": str(route_compare_csv)},
        {"item": "prepose_chunk_graph_solution", "path": str(graph_solution_csv)},
        {"item": "prepose_chunk_graph_edges", "path": str(graph_edges_csv)},
        {"item": "prepose_graph_gate_review", "path": str(final_outputs_diagnostics_dir / "prepose_graph_gate_review.json")},
    ],
    notes=[
        {"item": "status", "value": status},
        {"item": "preferred_route_label", "value": preferred_route_label},
        {"item": "preferred_fallback_used_count", "value": preferred_fallback_used_count},
        {"item": "hard_fail_count", "value": int(validation.get("hard_fail_count", 0))},
        {"item": "anchor_warning_count", "value": int(validation.get("anchor_warning_count", 0))},
    ],
)

assert status in {"ok", "warning"}, validation
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
    raise AssertionError("run #13-1 pre-merge pose gate before #14-1 merge")

premerge_pose_validation = json.loads(premerge_pose_validation_path.read_text(encoding="utf-8"))
premerge_route_compare_path = merged_dir / "premerge_route_compare_summary.json"
prepose_chunk_graph_solution_path = merged_dir / "prepose_chunk_graph_solution_arc.csv"
prepose_chunk_graph_edges_path = merged_dir / "prepose_chunk_graph_edges_arc.csv"
prepose_chunk_graph_summary_path = merged_dir / "prepose_chunk_graph_summary.json"
premerge_validation_csv_path = merged_dir / "premerge_pose_validation.csv"
allowed_premerge_status = {"ok", "warning"}
if str(premerge_pose_validation.get("status")) not in allowed_premerge_status:
    merge_summary = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "status": "skipped",
        "reason": "premerge_pose_validation_failed",
        "premerge_pose_validation_path": str(premerge_pose_validation_path),
        "premerge_route_compare_path": str(premerge_route_compare_path) if premerge_route_compare_path.exists() else None,
        "prepose_chunk_graph_solution_path": str(prepose_chunk_graph_solution_path) if prepose_chunk_graph_solution_path.exists() else None,
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
        "pred_ready_chunk_count": int(len(pred_ready_target_chunk_names)),
        "ply_ready_chunk_count": int(len(ply_ready_target_chunk_names)),
        "all_chunk_count": int(len(target_chunks_df)),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary_arc.json"),
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
elif INFER_GS and len(ply_ready_target_chunk_names) < len(target_chunks_df):
    merge_summary = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "status": "skipped",
        "reason": "gaussian_chunk_outputs_missing",
        "completed_chunk_count": int(len(completed_chunks_df)),
        "pred_ready_chunk_count": int(len(pred_ready_target_chunk_names)),
        "ply_ready_chunk_count": int(len(ply_ready_target_chunk_names)),
        "all_chunk_count": int(len(target_chunks_df)),
        "infer_gs": bool(INFER_GS),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary_arc.json"),
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
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

        merged = chunk_df.merge(
            global_anchor_df,
            on=["record_index", "image_file_name", "image_path", "frame_timestamp_ns", "capture_timestamp_ns"],
            how="left",
            validate="one_to_one",
        )
        assert len(merged) == len(chunk_df), {"chunk_name": row.chunk_name, "merged_len": len(merged), "chunk_len": len(chunk_df)}
        assert not merged[["cx_world", "cy_world", "cz_world", "anchor_lens_x", "anchor_lens_y", "anchor_lens_z", "anchor_up_x", "anchor_up_y", "anchor_up_z"]].isnull().any().any(), f"global anchor missing: {row.chunk_name}"
        global_c2w_list = [build_anchor_c2w(global_camera_map[int(rec.record_index)], rec) for rec in merged.itertuples(index=False)]

        prepose_solution = prepose_graph_solution_by_chunk.get(str(row.chunk_name))
        if prepose_solution is not None:
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
merged_camera_pose_csv = merged_dir / "merged_camera_pose_arc.csv"
merged_camera_matrix_csv = merged_dir / "merged_camera_matrix_arc.csv"
merged_camera_c2w_npy = merged_dir / "merged_camera_c2w_arc.npy"
merged_camera_w2c_npy = merged_dir / "merged_extrinsics_w2c_arc.npy"
ngl_bundle_dir = merged_dir / "ngl_camera_bundle"
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
    route_compare_path = merged_dir / "merge_route_compare_arc.csv"
    route_compare_df.to_csv(route_compare_path, index=False, encoding="utf-8")

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
        "fallback_used_count": int(sum(bool(x["fallback_used"]) for x in warning_rows)),
        "preferred_fallback_used_count": int(sum(bool(x.get("preferred_fallback_used")) for x in warning_rows)),
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
        (route_compare_path, stage_11_2_dir / "merge_route_compare_arc.csv"),
        (keep_summary_path, stage_11_2_dir / "chunk_keep_summary_arc.csv"),
        (transform_quality_path, stage_11_2_dir / "chunk_transform_quality_arc.csv"),
        (merged_dir / "owner_record_histogram_arc.csv", stage_11_2_dir / "owner_record_histogram_arc.csv"),
        (merged_dir / "chunk_assignment_summary_arc.csv", stage_11_2_dir / "chunk_assignment_summary_arc.csv"),
        (merged_dir / "merge_warning_summary_arc.json", stage_11_2_dir / "merge_warning_summary_arc.json"),
        (merged_dir / "all_batch_summary_arc.json", stage_11_2_dir / "all_batch_summary_arc.json"),
        (merged_dir / "merged_camera_pose_arc.csv", stage_11_2_dir / "merged_camera_pose_arc.csv"),
        (merged_dir / "merged_camera_matrix_arc.csv", stage_11_2_dir / "merged_camera_matrix_arc.csv"),
        (merged_dir / "merged_camera_c2w_arc.npy", stage_11_2_dir / "merged_camera_c2w_arc.npy"),
        (merged_dir / "merged_extrinsics_w2c_arc.npy", stage_11_2_dir / "merged_extrinsics_w2c_arc.npy"),
        (merged_dir / "ngl_camera_bundle/ngl_pose_bundle_summary.json", stage_11_2_dir / "ngl_pose_bundle_summary.json"),
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
        (route_compare_path, final_outputs_diagnostics_dir / "merge_route_compare_arc.csv"),
        (keep_summary_path, final_outputs_diagnostics_dir / "chunk_keep_summary_arc.csv"),
        (transform_quality_path, final_outputs_diagnostics_dir / "chunk_transform_quality_arc.csv"),
        (merged_dir / "owner_record_histogram_arc.csv", final_outputs_diagnostics_dir / "owner_record_histogram_arc.csv"),
        (merged_dir / "chunk_assignment_summary_arc.csv", final_outputs_diagnostics_dir / "chunk_assignment_summary_arc.csv"),
        (merged_dir / "merge_warning_summary_arc.json", final_outputs_diagnostics_dir / "merge_warning_summary_arc.json"),
        (merged_dir / "all_batch_summary_arc.json", final_outputs_diagnostics_dir / "all_batch_summary_arc.json"),
        (merged_dir / "merged_camera_pose_arc.csv", final_outputs_diagnostics_dir / "merged_camera_pose_arc.csv"),
        (merged_dir / "merged_camera_matrix_arc.csv", final_outputs_diagnostics_dir / "merged_camera_matrix_arc.csv"),
        (merged_dir / "merged_camera_c2w_arc.npy", final_outputs_diagnostics_dir / "merged_camera_c2w_arc.npy"),
        (merged_dir / "merged_extrinsics_w2c_arc.npy", final_outputs_diagnostics_dir / "merged_extrinsics_w2c_arc.npy"),
        (merged_dir / "ngl_camera_bundle/ngl_pose_bundle_summary.json", final_outputs_diagnostics_dir / "ngl_pose_bundle_summary.json"),
        (input_manifest_path, final_outputs_manifests_dir / "da3_input_manifest.csv"),
        (anchor_dir / "camera_center_matrix_arc.csv", final_outputs_manifests_dir / "camera_center_matrix_arc.csv"),
        (anchor_dir / "camera_matrix_full_arc.csv", final_outputs_manifests_dir / "camera_matrix_full_arc.csv"),
        (anchor_dir / "camera_anchor_full_arc.csv", final_outputs_manifests_dir / "camera_anchor_full_arc.csv"),
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
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
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
        "prepose_chunk_graph_edges_path": str(prepose_chunk_graph_edges_path) if prepose_chunk_graph_edges_path.exists() else None,
        "prepose_chunk_graph_summary_path": str(prepose_chunk_graph_summary_path) if prepose_chunk_graph_summary_path.exists() else None,
        "chunk_keep_summary_path": str(keep_summary_path),
        "chunk_transform_quality_path": str(transform_quality_path),
        "owner_record_histogram_path": str(merged_dir / "owner_record_histogram_arc.csv"),
        "chunk_assignment_summary_path": str(merged_dir / "chunk_assignment_summary_arc.csv"),
        "merge_warning_summary_path": str(merged_dir / "merge_warning_summary_arc.json"),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary_arc.json"),
        "merged_camera_pose_path": str(merged_dir / "merged_camera_pose_arc.csv"),
        "merged_camera_matrix_path": str(merged_dir / "merged_camera_matrix_arc.csv"),
        "merged_camera_c2w_path": str(merged_dir / "merged_camera_c2w_arc.npy"),
        "merged_extrinsics_w2c_path": str(merged_dir / "merged_extrinsics_w2c_arc.npy"),
        "ngl_pose_bundle_summary_path": str(merged_dir / "ngl_camera_bundle" / "ngl_pose_bundle_summary.json"),
        "preferred_route_label": PREFERRED_ROUTE_LABEL,
        "selected_route_counts": selected_route_counts,
        "fallback_used_count": fallback_used_count,
        "preferred_fallback_used_count": preferred_fallback_used_count,
        "final_outputs_dir": str(final_outputs_dir),
        "final_output_manifest_path": str(final_outputs_dir / "final_output_manifest_arc.json"),
        "bundle_summary": bundle_summary,
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(merged_dir / "merge_summary.json", final_outputs_diagnostics_dir / "merge_summary.json")
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
            {"item": "merge_summary", "path": str(merged_dir / "merge_summary.json")},
            {"item": "merged_gs", "path": str(merged_ply_path)},
            {"item": "merged_scene_glb", "path": str(merged_glb_path)},
            {"item": "final_output_manifest", "path": str(final_outputs_dir / "final_output_manifest_arc.json")},
            {"item": "chunk_global_transforms", "path": str(chunk_manifest_dir / "chunk_global_transforms_arc.csv")},
            {"item": "merge_route_compare", "path": str(route_compare_path)},
            {"item": "chunk_keep_summary", "path": str(keep_summary_path)},
            {"item": "chunk_transform_quality", "path": str(transform_quality_path)},
            {"item": "merged_camera_pose", "path": str(merged_dir / "merged_camera_pose_arc.csv")},
            {"item": "merged_extrinsics_w2c", "path": str(merged_dir / "merged_extrinsics_w2c_arc.npy")},
            {"item": "ngl_pose_bundle_summary", "path": str(merged_dir / "ngl_camera_bundle" / "ngl_pose_bundle_summary.json")},
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
