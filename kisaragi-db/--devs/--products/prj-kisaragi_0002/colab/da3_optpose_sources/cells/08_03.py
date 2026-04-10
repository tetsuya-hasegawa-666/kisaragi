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
