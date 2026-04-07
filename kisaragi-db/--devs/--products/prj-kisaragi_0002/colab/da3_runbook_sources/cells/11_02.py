#11-2
from pathlib import Path
import json, os, shutil, subprocess, shlex, math, hashlib
import numpy as np
import pandas as pd

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def load_ctx():
    return load_json("/content/runbook_session_context.json")

def find_first(paths):
    for p in paths:
        p = Path(p)
        if p.exists():
            return p
    return None

def normalize_rows(x, eps=1e-12):
    x = np.asarray(x, dtype=float)
    n = np.linalg.norm(x, axis=1, keepdims=True)
    n = np.maximum(n, eps)
    return x / n

def angle_deg(a, b):
    a = normalize_rows(a)
    b = normalize_rows(b)
    d = np.sum(a * b, axis=1)
    d = np.clip(d, -1.0, 1.0)
    return np.degrees(np.arccos(d))

print("common helpers loaded")
