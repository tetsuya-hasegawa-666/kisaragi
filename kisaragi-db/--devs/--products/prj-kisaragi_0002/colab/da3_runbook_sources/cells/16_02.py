#16-2
from pathlib import Path
import json
import pandas as pd

ctx = load_ctx()
pipeline_root = Path(ctx['probe_root']) / ctx.get('pipeline_slug', 'da3_ngl_batch_v01')
merged_dir = Path(ctx.get('merged_dir', str(pipeline_root / 'merged')))
cleanup_plan_path = merged_dir / 'cleanup_plan.json'
assert cleanup_plan_path.exists(), cleanup_plan_path
cleanup_plan = json.loads(cleanup_plan_path.read_text(encoding='utf-8'))
rows=[]
for item in cleanup_plan.get('delete_candidates', []):
    rows.append({
        'action': 'delete',
        'path': item['path'],
        'kind': item.get('kind',''),
        'reason': item.get('reason',''),
        'size_bytes': item.get('size_bytes',0),
    })
for item in cleanup_plan.get('kept_groups', []):
    rows.append({
        'action': 'keep',
        'path': item['path'],
        'kind': item.get('kind','keep'),
        'reason': item.get('reason', item.get('label','keep_group')),
        'size_bytes': item.get('size_bytes',0),
    })
cleanup_csv = merged_dir / 'cleanup_inventory_review_v02.csv'
pd.DataFrame(rows).to_csv(cleanup_csv, index=False, encoding='utf-8')
print({'cleanup_inventory_review_csv': str(cleanup_csv), 'row_count': len(rows)})
display_stage_summary(
    "16-2",
    "cleanup inventory review csv",
    inputs=[
        {"item": "cleanup_plan", "path": str(cleanup_plan_path)},
    ],
    outputs=[
        {"item": "cleanup_inventory_review_v02", "path": str(cleanup_csv)},
    ],
    notes=[
        {"item": "row_count", "value": int(len(rows))},
    ],
)
