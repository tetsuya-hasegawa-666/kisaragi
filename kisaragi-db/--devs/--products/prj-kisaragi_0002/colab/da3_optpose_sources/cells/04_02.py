#4-2
from pathlib import Path
import json

ctx = json.loads(Path('/content/runbook_session_context.json').read_text(encoding='utf-8'))
probe_root = Path(ctx['probe_root'])
run_root = Path(ctx['run_root'])

canonical_dirs = {
    'run_root': run_root,
    'run_config_snapshot': Path(ctx['run_config_snapshot_dir']),
    'runtime_extract': Path(ctx['runtime_extract_dir']),
    'runtime_model': Path(ctx['runtime_model_dir']),
    'runtime_cleanup': Path(ctx['runtime_cleanup_dir']),
    'validation_anchor': Path(ctx['compatibility_aliases']['01_anchor']).resolve() if Path(ctx['compatibility_aliases']['01_anchor']).exists() else Path(ctx['validation_root']) / 'runs' / Path(ctx['run_id']) / '10_validation' / 'anchor',
    'validation_records': Path(ctx['compatibility_aliases']['02_records']).resolve() if Path(ctx['compatibility_aliases']['02_records']).exists() else Path(ctx['validation_root']) / 'runs' / Path(ctx['run_id']) / '10_validation' / 'records',
    'validation_batch_plan': Path(ctx['compatibility_aliases']['03_batch_plan']).resolve() if Path(ctx['compatibility_aliases']['03_batch_plan']).exists() else Path(ctx['validation_root']) / 'runs' / Path(ctx['run_id']) / '10_validation' / 'batch_plan',
    'validation_chunk_runs': Path(ctx['chunk_runs_dir']),
    'validation_merged': Path(ctx['merged_dir']),
    'validation_manifests': Path(ctx['chunk_manifest_dir']),
    'validation_reviews': Path(ctx['run_validation_dir']) / 'reviews',
    'delivery_end_user_current': Path(ctx['final_outputs_merged_dir']),
    'delivery_technical_reference_current': Path(ctx['final_outputs_manifests_dir']),
    'delivery_operator_private_current': Path(ctx['final_outputs_chunk_evidence_dir']),
}

managed_dirs = {
    '02_records': canonical_dirs['validation_records'],
}

compatibility_aliases = {k: Path(v) for k, v in ctx.get('compatibility_aliases', {}).items()}
for p in list(canonical_dirs.values()) + list(managed_dirs.values()) + list(compatibility_aliases.values()):
    p.mkdir(parents=True, exist_ok=True)

doc = {
    'probe_root': str(probe_root),
    'run_root': str(run_root),
    'tree_schema_version': str(ctx['tree_schema_version']),
    'canonical_dirs': {k: str(v) for k, v in canonical_dirs.items()},
    'managed_dirs': {k: str(v) for k, v in managed_dirs.items()},
    'compatibility_aliases': {k: str(v) for k, v in compatibility_aliases.items()},
}
Path('/content/runbook_managed_dirs.json').write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(doc, indent=2, ensure_ascii=False))
