#9-5
from pathlib import Path
import json
import pandas as pd

ctx = load_ctx()
probe_root = Path(ctx['probe_root'])
pipeline_root = probe_root / ctx.get('pipeline_slug', 'da3_ngl_batch_v01')
chunk_manifest_dir = pipeline_root / 'manifests'
record_manifest_path = Path(json.loads(Path('/content/runbook_managed_dirs.json').read_text(encoding='utf-8'))['02_records']) / 'record_manifest.csv'
record_df = pd.read_csv(record_manifest_path) if record_manifest_path.exists() else None
if record_df is not None:
    keep_cols = [c for c in ['sequence_index','roll_deg','pitch_deg','yaw_deg','delta_roll_deg','delta_pitch_deg','delta_yaw_deg','delta_pos','delta2_pos','delta2_rot'] if c in record_df.columns]
    join_df = record_df[['image_file_name', *keep_cols]].drop_duplicates() if 'image_file_name' in record_df.columns else record_df[keep_cols + ['sequence_index']].copy()
else:
    join_df = None

chunk_index_path = chunk_manifest_dir / 'chunk_index_all.csv'
assert chunk_index_path.exists(), chunk_index_path
chunk_index_df = pd.read_csv(chunk_index_path)
rows = []
for row in chunk_index_df.itertuples(index=False):
    chunk_csv = Path(getattr(row, 'chunk_csv')) if getattr(row, 'chunk_csv', None) else None
    if chunk_csv is None or not chunk_csv.exists():
        continue
    cdf = pd.read_csv(chunk_csv)
    ts_col = next((c for c in ['frame_timestamp_ns','timestamp_ns','timestamp'] if c in cdf.columns), None)
    cdf = append_sequence_columns(cdf, ts_col or 'frame_timestamp_ns')
    if join_df is not None:
        common = [c for c in ['image_file_name', 'sequence_index'] if c in cdf.columns and c in join_df.columns]
        if common:
            cdf = cdf.merge(join_df, on=common, how='left', suffixes=('', '_record'))
    cdf['adjacent_edge_src_sequence_index'] = cdf['sequence_index']
    cdf['adjacent_edge_dst_sequence_index'] = cdf['sequence_index'].shift(-1).fillna(-1).astype(int)
    cdf['adjacent_edge_valid'] = cdf['adjacent_edge_dst_sequence_index'] >= 0
    cdf['adjacent_pair_role'] = 'interior'
    if len(cdf) > 0:
        cdf.loc[cdf.index[0], 'adjacent_pair_role'] = 'head'
        cdf.loc[cdf.index[-1], 'adjacent_pair_role'] = 'tail'
    ext_path = chunk_csv.with_name(chunk_csv.stem + '_sequence_anchor.csv')
    cdf.to_csv(ext_path, index=False, encoding='utf-8')
    rows.append({'chunk_name': getattr(row, 'chunk_name', chunk_csv.stem), 'chunk_csv_ext': str(ext_path), 'row_count': int(len(cdf))})

out = chunk_manifest_dir / 'chunk_sequence_anchor_index.csv'
pd.DataFrame(rows).to_csv(out, index=False, encoding='utf-8')
print({'chunk_sequence_anchor_index': str(out), 'chunk_count': len(rows)})
display_stage_summary(
    "9-5",
    "chunk sequence anchor index refresh",
    inputs=[
        {"item": "chunk_index_all", "path": str(chunk_index_path)},
        {"item": "record_manifest", "path": str(record_manifest_path)},
    ],
    outputs=[
        {"item": "chunk_sequence_anchor_index", "path": str(out)},
    ],
    notes=[
        {"item": "chunk_count", "value": int(len(rows))},
    ],
)
