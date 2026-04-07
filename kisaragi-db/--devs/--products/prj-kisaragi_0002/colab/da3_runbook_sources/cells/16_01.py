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
