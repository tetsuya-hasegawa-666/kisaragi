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
pipeline_slug = config.get("PIPELINE_SLUG", "runtime_workspace")
legacy_source_pipeline_slug = "continuous_gs_v07_chunk18_step6_adopt6_incremental"
modeling_session_id = session_id.replace("trajectreview-correcting-session-", "trajectreview-modeling-session-", 1) if session_id.startswith("trajectreview-correcting-session-") else f"trajectreview-modeling-session-{session_id}"
probe_root_name = modeling_session_id
probe_root = Path(paths["probe_root"])
pipeline_root = probe_root / pipeline_slug
da3_nested_dir = Path(paths["da3_nested_dir"])
da3_nested_gs_dir = Path(paths["da3_nested_gs_dir"])
world_dir = Path(paths["world_dir"])
manifest_dir = Path(paths["manifest_dir"])
final_outputs_dir = Path(paths["final_outputs_dir"])
final_outputs_diagnostics_dir = Path(paths["final_outputs_diagnostics_dir"])
final_outputs_chunk_evidence_dir = Path(paths["final_outputs_chunk_evidence_dir"])
stage_10_dir = Path(paths["stage_10_dir"])
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
    final_outputs_diagnostics_dir,
    final_outputs_chunk_evidence_dir,
    stage_10_dir,
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
    "final_outputs_dir": str(final_outputs_dir),
    "final_outputs_diagnostics_dir": str(final_outputs_diagnostics_dir),
    "final_outputs_chunk_evidence_dir": str(final_outputs_chunk_evidence_dir),
    "stage_10_dir": str(stage_10_dir),
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
