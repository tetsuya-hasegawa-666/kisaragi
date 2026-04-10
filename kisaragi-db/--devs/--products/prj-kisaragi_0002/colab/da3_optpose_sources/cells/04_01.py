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
