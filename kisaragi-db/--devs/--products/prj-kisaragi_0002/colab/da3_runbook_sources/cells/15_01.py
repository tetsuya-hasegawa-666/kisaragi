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
