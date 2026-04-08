#9-4

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

# ----- full anchor のコピー/索引化（#2系生成物の利用） -----
camera_anchor_full_path = anchor_dir / "camera_anchor_full_arc.csv"
assert camera_anchor_full_path.exists(), camera_anchor_full_path

anchor_df = pd.read_csv(camera_anchor_full_path)
assert not anchor_df.empty, camera_anchor_full_path
assert "record_index" in anchor_df.columns, anchor_df.columns.tolist()
assert "sequence_index" in anchor_df.columns, anchor_df.columns.tolist()

chunk_sequence_anchor_index_rows = []

for row in all_chunks_df.itertuples(index=False):
    chunk_csv_path = Path(row.chunk_csv)
    chunk_df = pd.read_csv(chunk_csv_path)
    chunk_anchor_df = chunk_df.merge(
        anchor_df,
        on=["record_index"],
        how="left",
        suffixes=("", "_anchor")
    )
    assert len(chunk_anchor_df) == len(chunk_df), {"chunk_name": row.chunk_name, "reason": "anchor merge row count mismatch"}

    missing_anchor = chunk_anchor_df["sequence_index_anchor"].isna().sum() if "sequence_index_anchor" in chunk_anchor_df.columns else 0
    if "sequence_index_anchor" in chunk_anchor_df.columns:
        chunk_anchor_df = chunk_anchor_df.rename(columns={"sequence_index_anchor": "sequence_index"})
    if "frame_timestamp_ns_anchor" in chunk_anchor_df.columns and "frame_timestamp_ns" not in chunk_anchor_df.columns:
        chunk_anchor_df = chunk_anchor_df.rename(columns={"frame_timestamp_ns_anchor": "frame_timestamp_ns"})

    chunk_anchor_csv = chunk_manifest_dir / f"{row.chunk_name}_sequence_anchor.csv"
    chunk_anchor_df.to_csv(chunk_anchor_csv, index=False, encoding="utf-8")

    chunk_sequence_anchor_index_rows.append({
        "chunk_id": int(row.chunk_id),
        "chunk_name": row.chunk_name,
        "global_start": int(row.global_start),
        "global_end": int(row.global_end),
        "frame_count": int(row.frame_count),
        "chunk_csv": str(chunk_csv_path),
        "chunk_sequence_anchor_csv": str(chunk_anchor_csv),
        "missing_anchor_count": int(missing_anchor),
    })

chunk_sequence_anchor_index_df = pd.DataFrame(chunk_sequence_anchor_index_rows)
chunk_sequence_anchor_index_path = chunk_manifest_dir / "chunk_sequence_anchor_index.csv"
chunk_sequence_anchor_index_df.to_csv(chunk_sequence_anchor_index_path, index=False, encoding="utf-8")

summary = {
    "route": "da3_record_sequence_anchor_batch_plan_config_target",
    "global_camera_source": "manifests/extrinsics_w2c_arc.npy",
    "frame_count": int(len(input_df)),
    "chunk_count": int(len(all_chunks_df)),
    "target_chunk_count": int(len(target_chunks_df)),
    "batch_count": int(batch_count),
    "pipeline_root": str(pipeline_root),
    "anchor_dir": str(anchor_dir),
    "camera_anchor_full_path": str(camera_anchor_full_path),
    "bundle_model_slug": BUNDLE_MODEL_SLUG,
    "input_extrinsics_path": str(extrinsics_path),
    "chunk_index_all_path": str(chunk_index_all_path),
    "chunk_index_target_path": str(chunk_index_target_path),
    "chunk_sequence_anchor_index_path": str(chunk_sequence_anchor_index_path),
    "batch_plan_path": str(batch_plan_path),
    "target_policy": target_policy,
    "target_chunk_mode": target_mode,
    "target_chunk_ids_1based": target_ids_1based,
    "target_chunk_names": target_chunks_df["chunk_name"].astype(str).tolist(),
    "test_execution_limiter_location": "#11-3 legacy override only",
}

(chunk_manifest_dir / "batch_plan_summary.json").write_text(
    json.dumps(summary, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print(json.dumps(summary, indent=2, ensure_ascii=False))
display(batch_plan_df)
display_stage_summary(
    "9-4",
    "batch plan build",
    inputs=[
        {"item": "record_manifest", "path": str(input_manifest_path)},
        {"item": "extrinsics_w2c", "path": str(extrinsics_path)},
        {"item": "camera_anchor_full", "path": str(camera_anchor_full_path)},
    ],
    outputs=[
        {"item": "pipeline_config", "path": str(pipeline_root / "pipeline_config.json")},
        {"item": "chunk_index_all", "path": str(chunk_index_all_path)},
        {"item": "chunk_index_target", "path": str(chunk_index_target_path)},
        {"item": "batch_plan", "path": str(batch_plan_path)},
        {"item": "chunk_sequence_anchor_index", "path": str(chunk_sequence_anchor_index_path)},
        {"item": "batch_plan_summary", "path": str(chunk_manifest_dir / "batch_plan_summary.json")},
    ],
    notes=[
        {"item": "chunk_count", "value": int(len(all_chunks_df))},
        {"item": "batch_count", "value": int(batch_count)},
    ],
)
