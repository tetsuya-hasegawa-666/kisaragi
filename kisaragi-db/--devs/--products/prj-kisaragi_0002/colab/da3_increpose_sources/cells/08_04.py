#8-4

from pathlib import Path
import pandas as pd
import numpy as np

ctx = load_ctx()
probe_root = Path(ctx["probe_root"])
pipeline_root = probe_root / ctx.get("pipeline_slug", "runtime_workspace")
chunk_manifest_dir = pipeline_root / "manifests"

chunk_execution_plan_path = chunk_manifest_dir / "chunk_execution_plan.csv"
batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"
chunk_input_manifest_path = chunk_manifest_dir / "chunk_input_manifest_arc.csv"
chunk_index_all_path = chunk_manifest_dir / "chunk_index_all.csv"

if chunk_execution_plan_path.exists():
    chunk_index_df = pd.read_csv(chunk_execution_plan_path)
    source_label = "chunk_execution_plan"
elif batch_execution_items_path.exists():
    chunk_index_df = pd.read_csv(batch_execution_items_path)
    source_label = "batch_execution_items"
elif chunk_index_all_path.exists():
    chunk_index_df = pd.read_csv(chunk_index_all_path)
    source_label = "chunk_index_all"
else:
    raise AssertionError({
        "missing_required_manifest": [
            str(chunk_execution_plan_path),
            str(batch_execution_items_path),
            str(chunk_index_all_path),
        ]
    })

assert not chunk_index_df.empty, {"source_label": source_label, "chunk_manifest_dir": str(chunk_manifest_dir)}
assert "chunk_name" in chunk_index_df.columns, chunk_index_df.columns.tolist()

input_manifest_df = pd.read_csv(chunk_input_manifest_path) if chunk_input_manifest_path.exists() else pd.DataFrame()

rows = []

for row in chunk_index_df.itertuples(index=False):
    chunk_name = row.chunk_name
    chunk_csv_value = getattr(row, "chunk_csv", "")
    chunk_csv = Path(str(chunk_csv_value)) if str(chunk_csv_value).strip() else (chunk_manifest_dir / f"{chunk_name}.csv")
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
        "record_index_min": int(chunk_df["record_index"].min()) if "record_index" in chunk_df.columns and len(chunk_df) else None,
        "record_index_max": int(chunk_df["record_index"].max()) if "record_index" in chunk_df.columns and len(chunk_df) else None,
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
    "source_label": source_label,
    "chunk_input_manifest_rows": int(len(input_manifest_df)),
})
display_stage_summary(
    "8-4",
    "batch chunk sequence precheck",
    inputs=[
        {"item": source_label, "path": str(chunk_execution_plan_path if source_label == "chunk_execution_plan" else (batch_execution_items_path if source_label == "batch_execution_items" else chunk_index_all_path))},
        {"item": "chunk_input_manifest_arc", "path": str(chunk_input_manifest_path)},
    ],
    outputs=[
        {"item": "batch_chunk_sequence_precheck", "path": str(precheck_path)},
    ],
    notes=[
        {"item": "bad_chunk_count", "value": int(bad_chunk_count)},
        {"item": "chunk_count", "value": int(len(precheck_df))},
        {"item": "source_label", "value": source_label},
    ],
)
