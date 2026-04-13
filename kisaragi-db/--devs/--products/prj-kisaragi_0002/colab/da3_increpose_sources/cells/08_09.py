#8-9

from pathlib import Path
import json
import subprocess
import pandas as pd
import numpy as np

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))

probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "runtime_workspace")
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
chunk_runs_dir.mkdir(parents=True, exist_ok=True)

final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_diagnostics_dir.mkdir(parents=True, exist_ok=True)

wrapper_path = Path("/content/Depth-Anything-3/run_da3_chunk_local.py")
assert wrapper_path.exists(), wrapper_path

chunk_execution_plan_path = chunk_manifest_dir / "chunk_execution_plan.csv"
batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
assert chunk_execution_plan_path.exists(), chunk_execution_plan_path

items_df = pd.read_csv(chunk_execution_plan_path)
if "is_target" in items_df.columns:
    items_df = items_df.loc[items_df["is_target"].fillna(False)].copy()
assert not items_df.empty, chunk_execution_plan_path
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

all_batch_summary_json = pipeline_root / "all_batch_summary_arc.json"
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
        {"item": "chunk_execution_plan", "path": str(chunk_execution_plan_path)},
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
