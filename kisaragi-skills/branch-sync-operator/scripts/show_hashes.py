#!/usr/bin/env python3
"""Print remote hashes for main/dev/stg."""
import subprocess
for b in ['main','dev','stg']:
    cmd=['git','rev-parse',f'origin/{b}']
    try:
        out=subprocess.check_output(cmd, text=True).strip()
    except Exception:
        out='N/A'
    print(f'{b}: {out}')
