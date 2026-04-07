#9-2
from pathlib import Path
import json
import pandas as pd

ctx = load_ctx()
manifest_dir = Path(ctx['manifest_dir'])
managed_dirs = json.loads(Path('/content/runbook_managed_dirs.json').read_text(encoding='utf-8'))
record_dir = Path(managed_dirs['02_records'])
record_dir.mkdir(parents=True, exist_ok=True)
anchor_diag = pd.read_csv(Path(managed_dirs['01_anchor']) / 'full_anchor_pose_diag_arc.csv')
anchor_keep_cols = [c for c in ['sequence_index','roll_deg','pitch_deg','yaw_deg','delta_roll_deg','delta_pitch_deg','delta_yaw_deg','delta_pos','delta2_pos','delta2_rot'] if c in anchor_diag.columns]
anchor_join = anchor_diag[anchor_keep_cols].copy() if anchor_keep_cols else pd.DataFrame()

p = manifest_dir / 'da3_input_manifest.csv'
assert p.exists(), p
df = pd.read_csv(p)
ts_col = next((c for c in ['frame_timestamp_ns','timestamp_ns','timestamp'] if c in df.columns), None)
df = append_sequence_columns(df, ts_col or 'frame_timestamp_ns')
if not anchor_join.empty and 'sequence_index' in df.columns:
    df = df.merge(anchor_join, on='sequence_index', how='left', suffixes=('', '_anchor'))
df['is_time_adjacent_valid'] = True
df.to_csv(p, index=False, encoding='utf-8')
df.to_csv(record_dir / 'record_manifest.csv', index=False, encoding='utf-8')
print({'updated_manifest': str(p), 'rows': len(df)})
display_stage_summary(
    "9-2",
    "record manifest refresh",
    inputs=[
        {"item": "da3_input_manifest", "path": str(p)},
        {"item": "full_anchor_pose_diag", "path": str(Path(managed_dirs['01_anchor']) / 'full_anchor_pose_diag_arc.csv')},
    ],
    outputs=[
        {"item": "record_manifest", "path": str(record_dir / 'record_manifest.csv')},
        {"item": "da3_input_manifest_updated", "path": str(p)},
    ],
    notes=[
        {"item": "rows", "value": int(len(df))},
    ],
)
