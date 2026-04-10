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
