#!/usr/bin/env python3
"""Print remote hashes for main/dev/stg."""
import subprocess

for branch in ["main", "dev", "stg"]:
    command = ["git", "rev-parse", f"origin/{branch}"]
    try:
        output = subprocess.check_output(command, text=True).strip()
    except Exception:
        output = "N/A"
    print(f"{branch}: {output}")
