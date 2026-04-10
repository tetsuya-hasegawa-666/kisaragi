#8-2
from pathlib import Path
import json
import pandas as pd

ctx = load_ctx()
manifest_dir = Path(ctx['manifest_dir'])
managed_dirs = json.loads(Path('/content/runbook_managed_dirs.json').read_text(encoding='utf-8'))
record_dir = Path(managed_dirs['02_records'])
record_dir.mkdir(parents=True, exist_ok=True)

p = manifest_dir / 'da3_input_manifest.csv'
assert p.exists(), p
df = pd.read_csv(p)
ts_col = next((c for c in ['frame_timestamp_ns','timestamp_ns','timestamp'] if c in df.columns), None)
df = append_sequence_columns(df, ts_col or 'frame_timestamp_ns')
df['is_time_adjacent_valid'] = True
df.to_csv(p, index=False, encoding='utf-8')
df.to_csv(record_dir / 'record_manifest.csv', index=False, encoding='utf-8')
print({'updated_manifest': str(p), 'rows': len(df)})
display_stage_summary(
    "8-2",
    "record manifest refresh",
    inputs=[
        {"item": "da3_input_manifest", "path": str(p)},
    ],
    outputs=[
        {"item": "record_manifest", "path": str(record_dir / 'record_manifest.csv')},
        {"item": "da3_input_manifest_updated", "path": str(p)},
    ],
    notes=[
        {"item": "rows", "value": int(len(df))},
        {"item": "anchor_derived_join", "value": False},
    ],
)
