#4-2
from pathlib import Path
import json

ctx = json.loads(Path('/content/runbook_session_context.json').read_text(encoding='utf-8'))
probe_root = Path(ctx['probe_root'])
managed_dirs = {
    '00_config': probe_root / '00_config',
    '01_anchor': probe_root / '01_anchor',
    '02_records': probe_root / '02_records',
    '03_batch_plan': probe_root / '03_batch_plan',
    '04_batch_runs': probe_root / '04_batch_runs',
    '05_merge': probe_root / '05_merge',
    '06_cleanup': probe_root / '06_cleanup',
    'other': probe_root / 'other',
}
for p in managed_dirs.values():
    p.mkdir(parents=True, exist_ok=True)
Path('/content/runbook_managed_dirs.json').write_text(json.dumps({k:str(v) for k,v in managed_dirs.items()}, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({k:str(v) for k,v in managed_dirs.items()}, indent=2, ensure_ascii=False))
