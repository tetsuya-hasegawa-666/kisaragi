#10-1

from pathlib import Path
import json
import pandas as pd
import numpy as np

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
config_snapshot = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8")) if Path("/content/config_snapshot.json").exists() else {}

manifest_dir = Path(ctx["manifest_dir"])
persist_root = Path(ctx.get("persist_root", manifest_dir.parent))
pipeline_slug = ctx.get("pipeline_slug", config_snapshot.get("PIPELINE_SLUG", "da3_ngl_batch_v01"))
pipeline_root = persist_root / pipeline_slug
chunk_manifest_dir = pipeline_root / "manifests"

chunk_index_all_path = chunk_manifest_dir / "chunk_index_all.csv"
assert chunk_index_all_path.exists(), chunk_index_all_path

chunk_index_df = pd.read_csv(chunk_index_all_path)
assert not chunk_index_df.empty, chunk_index_all_path
assert "chunk_name" in chunk_index_df.columns, chunk_index_df.columns.tolist()
assert "chunk_csv" in chunk_index_df.columns, chunk_index_df.columns.tolist()

rows = []

for row in chunk_index_df.itertuples(index=False):
    chunk_name = row.chunk_name
    chunk_csv = Path(row.chunk_csv)
    assert chunk_csv.exists(), {"chunk_name": chunk_name, "missing_chunk_csv": str(chunk_csv)}

    chunk_df = pd.read_csv(chunk_csv)
    assert not chunk_df.empty, {"chunk_name": chunk_name, "reason": "empty chunk csv"}

    # sequence_index がなければ record_index / timestamp で代用
    if "sequence_index" in chunk_df.columns:
        seq = chunk_df["sequence_index"].astype(int).to_numpy()
    elif "record_index" in chunk_df.columns:
        seq = chunk_df["record_index"].astype(int).to_numpy()
    else:
        raise AssertionError({"chunk_name": chunk_name, "reason": "sequence_index/record_index not found", "columns": chunk_df.columns.tolist()})

    is_monotonic = bool(np.all(np.diff(seq) > 0)) if len(seq) >= 2 else True
    has_duplicate_sequence = bool(pd.Series(seq).duplicated().any())
    bad_gap_count = int(np.sum(np.diff(seq) != 1)) if len(seq) >= 2 else 0

    rows.append({
        "chunk_id": int(row.chunk_id) if "chunk_id" in chunk_index_df.columns else None,
        "chunk_name": chunk_name,
        "row_count": int(len(chunk_df)),
        "sequence_min": int(seq.min()) if len(seq) else None,
        "sequence_max": int(seq.max()) if len(seq) else None,
        "is_monotonic": is_monotonic,
        "has_duplicate_sequence": has_duplicate_sequence,
        "bad_gap_count": bad_gap_count,
        "chunk_csv": str(chunk_csv),
    })

precheck_df = pd.DataFrame(rows)
precheck_path = chunk_manifest_dir / "batch_chunk_sequence_precheck.csv"
precheck_df.to_csv(precheck_path, index=False, encoding="utf-8")

bad_chunk_count = int(
    ((~precheck_df["is_monotonic"]) | (precheck_df["has_duplicate_sequence"]) | (precheck_df["bad_gap_count"] > 0)).sum()
)

print(precheck_df.head())
print({
    "precheck_csv": str(precheck_path),
    "bad_chunk_count": bad_chunk_count,
    "chunk_count": int(len(precheck_df)),
})
display_stage_summary(
    "10-1",
    "batch chunk sequence precheck",
    inputs=[
        {"item": "chunk_index_all", "path": str(chunk_index_all_path)},
    ],
    outputs=[
        {"item": "batch_chunk_sequence_precheck", "path": str(precheck_path)},
    ],
    notes=[
        {"item": "bad_chunk_count", "value": int(bad_chunk_count)},
        {"item": "chunk_count", "value": int(len(precheck_df))},
    ],
)
