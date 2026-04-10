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
