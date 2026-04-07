#6-1
from pathlib import Path
import json, math, shutil
import numpy as np
import pandas as pd
from IPython.display import Markdown, display

RUNBOOK_CTX_PATH = Path('/content/runbook_session_context.json')


def load_ctx() -> dict:
    return json.loads(RUNBOOK_CTX_PATH.read_text(encoding='utf-8'))


def save_json(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')


def append_sequence_columns(df: pd.DataFrame, timestamp_col: str = 'frame_timestamp_ns') -> pd.DataFrame:
    out = df.copy()
    if timestamp_col in out.columns:
        out = out.sort_values(timestamp_col, kind='stable').reset_index(drop=True)
    else:
        out = out.reset_index(drop=True)
    out['sequence_index'] = np.arange(len(out), dtype=np.int64)
    out['prev_sequence_index'] = out['sequence_index'] - 1
    out['next_sequence_index'] = out['sequence_index'] + 1
    out.loc[out['sequence_index'] == 0, 'prev_sequence_index'] = -1
    out.loc[out['sequence_index'] == len(out) - 1, 'next_sequence_index'] = -1
    return out


def rotmat_to_rpy_deg(R: np.ndarray):
    sy = math.sqrt(float(R[0,0] * R[0,0] + R[1,0] * R[1,0]))
    singular = sy < 1e-6
    if not singular:
        roll = math.degrees(math.atan2(float(R[2,1]), float(R[2,2])))
        pitch = math.degrees(math.atan2(float(-R[2,0]), sy))
        yaw = math.degrees(math.atan2(float(R[1,0]), float(R[0,0])))
    else:
        roll = math.degrees(math.atan2(float(-R[1,2]), float(R[1,1])))
        pitch = math.degrees(math.atan2(float(-R[2,0]), sy))
        yaw = 0.0
    return roll, pitch, yaw


def _summary_rows(items, kind: str):
    rows = []
    for item in (items or []):
        if isinstance(item, (str, Path)):
            item = {"item": Path(item).name, "path": str(item)}
        row = dict(item)
        row.setdefault("kind", kind)
        if "item" not in row:
            row["item"] = row.pop("label", row.pop("name", ""))
        path_value = row.get("path")
        if path_value:
            p = Path(path_value)
            row.setdefault("exists", p.exists())
            row.setdefault("is_dir", p.exists() and p.is_dir())
            if p.exists() and p.is_file():
                row.setdefault("bytes", int(p.stat().st_size))
        rows.append(row)
    return rows


def display_stage_summary(stage_no: str, title: str, inputs=None, outputs=None, notes=None):
    display(Markdown(f"### {stage_no} summary"))
    if notes:
        display(pd.DataFrame(_summary_rows(notes, "note")))
    if inputs:
        display(pd.DataFrame(_summary_rows(inputs, "input")))
    if outputs:
        display(pd.DataFrame(_summary_rows(outputs, "output")))
