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
    batch_work_dir = chunk_runs_dir / batch_name / chunk_name
    chunk_csv_path = chunk_manifest_dir / f"{chunk_name}.csv"

    execution_rows.append({
        "chunk_id": int(chunk_id),
        "chunk_name": chunk_name,
        "batch_index": int(batch_index),
        "batch_name": batch_name,
        "batch_work_dir": str(batch_work_dir),
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
