#17-1
import json
import shutil
import pandas as pd

ctx = load_ctx()
probe_root = Path(ctx['probe_root'])
pipeline_root = probe_root / ctx.get('pipeline_slug', 'da3_ngl_batch_v01')
merged_dir = Path(ctx.get('merged_dir', str(pipeline_root / 'merged')))
cleanup_plan_path = merged_dir / 'cleanup_plan.json'
cleanup_csv_path = merged_dir / 'cleanup_inventory_review_v02.csv'
assert cleanup_plan_path.exists(), cleanup_plan_path
assert cleanup_csv_path.exists(), cleanup_csv_path

cleanup_plan = json.loads(cleanup_plan_path.read_text(encoding='utf-8'))
review_df = pd.read_csv(cleanup_csv_path)
review_df['action'] = review_df['action'].astype(str).str.strip().str.lower()
reviewed_paths = set(review_df['path'].astype(str))
other_dir = probe_root / 'other'
other_dir.mkdir(parents=True, exist_ok=True)

deleted = []
moved_to_other = []
kept = []

for row in review_df.itertuples(index=False):
    p = Path(row.path)
    action = str(row.action).strip().lower()
    if action == 'delete' and p.exists():
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        deleted.append(str(p))
    elif action in {'keep', 'other'}:
        kept.append(str(p))

for item in cleanup_plan.get('delete_candidates', []):
    src = Path(item['path'])
    if str(src) in reviewed_paths or not src.exists():
        continue
    dst = other_dir / src.name
    n = 1
    while dst.exists():
        dst = other_dir / f'{src.stem}_mv{n:02d}{src.suffix}'
        n += 1
    shutil.move(str(src), str(dst))
    moved_to_other.append({'src': str(src), 'dst': str(dst)})

cleanup_result = {
    'status': 'ok',
    'deleted': deleted,
    'moved_to_other': moved_to_other,
    'kept': kept,
}
(merged_dir / 'cleanup_apply_log.json').write_text(json.dumps(cleanup_result, indent=2, ensure_ascii=False), encoding='utf-8')
pd.DataFrame(
    [{'action': 'deleted', 'path': p} for p in deleted]
    + [{'action': 'moved_to_other', 'path': x['src'], 'dst': x['dst']} for x in moved_to_other]
    + [{'action': 'kept', 'path': p} for p in kept]
).to_csv(merged_dir / 'cleanup_apply_log.csv', index=False, encoding='utf-8')
print(json.dumps(cleanup_result, indent=2, ensure_ascii=False))
display_stage_summary(
    "17-1",
    "cleanup apply",
    inputs=[
        {"item": "cleanup_plan", "path": str(cleanup_plan_path)},
        {"item": "cleanup_inventory_review_v02", "path": str(cleanup_csv_path)},
    ],
    outputs=[
        {"item": "cleanup_apply_log_json", "path": str(merged_dir / 'cleanup_apply_log.json')},
        {"item": "cleanup_apply_log_csv", "path": str(merged_dir / 'cleanup_apply_log.csv')},
    ],
    notes=[
        {"item": "deleted_count", "value": int(len(deleted))},
        {"item": "moved_to_other_count", "value": int(len(moved_to_other))},
    ],
)
