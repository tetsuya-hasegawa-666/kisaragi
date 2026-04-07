#10-2
from pathlib import Path
import json
import pandas as pd

ctx = load_ctx()
pipeline_root = Path(ctx['probe_root']) / ctx.get('pipeline_slug', 'da3_ngl_batch_v01')
chunk_manifest_dir = pipeline_root / 'manifests'
idx_df = pd.read_csv(chunk_manifest_dir / 'chunk_sequence_anchor_index.csv')
rows=[]
for row in idx_df.itertuples(index=False):
    cdf = pd.read_csv(Path(row.chunk_csv_ext))
    miss = cdf.loc[cdf['adjacent_edge_valid'] & ((cdf['adjacent_edge_dst_sequence_index'] - cdf['adjacent_edge_src_sequence_index']) != 1)].copy() if 'adjacent_edge_valid' in cdf.columns else pd.DataFrame()
    rows.append({'chunk_name': row.chunk_name, 'missing_or_bad_edge_count': int(len(miss))})
edge_df = pd.DataFrame(rows)
out = chunk_manifest_dir / 'adjacent_edge_validation.csv'
edge_df.to_csv(out, index=False, encoding='utf-8')
display(edge_df)
display_stage_summary(
    "10-2",
    "adjacent edge validation",
    inputs=[
        {"item": "chunk_sequence_anchor_index", "path": str(chunk_manifest_dir / 'chunk_sequence_anchor_index.csv')},
    ],
    outputs=[
        {"item": "adjacent_edge_validation", "path": str(out)},
    ],
    notes=[
        {"item": "chunk_count", "value": int(len(edge_df))},
    ],
)
