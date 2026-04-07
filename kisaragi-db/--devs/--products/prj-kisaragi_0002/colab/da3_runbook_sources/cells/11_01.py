#11-1

from pathlib import Path
import json
import pandas as pd

ctx = load_ctx()
manifest_dir = Path(ctx["probe_root"]) / ctx.get("pipeline_slug", "da3_ngl_batch_v01") / "manifests"

batch_plan_df = pd.read_csv(manifest_dir / "batch_plan.csv")
chunk_all_df = pd.read_csv(manifest_dir / "chunk_index_all.csv")
chunk_target_df = pd.read_csv(manifest_dir / "chunk_index_target.csv")

display(batch_plan_df)
display(chunk_all_df[[c for c in ["chunk_id","chunk_name"] if c in chunk_all_df.columns]].head(10))
display(chunk_all_df[[c for c in ["chunk_id","chunk_name"] if c in chunk_all_df.columns]].tail(10))
display(chunk_target_df[[c for c in chunk_target_df.columns if c in ["chunk_id","chunk_name"]]])
display_stage_summary(
    "11-1",
    "run preparation preview",
    inputs=[
        {"item": "batch_plan", "path": str(manifest_dir / "batch_plan.csv")},
        {"item": "chunk_index_all", "path": str(manifest_dir / "chunk_index_all.csv")},
        {"item": "chunk_index_target", "path": str(manifest_dir / "chunk_index_target.csv")},
    ],
    outputs=[],
    notes=[
        {"item": "batch_count", "value": int(len(batch_plan_df))},
        {"item": "all_chunk_count", "value": int(len(chunk_all_df))},
        {"item": "target_chunk_count", "value": int(len(chunk_target_df))},
    ],
)
