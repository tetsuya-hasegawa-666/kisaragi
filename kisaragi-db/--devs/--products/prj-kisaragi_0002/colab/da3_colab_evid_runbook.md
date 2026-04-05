# DA3 Colab Evid Runbook

## 文書の役割

- `Colab` modeling の canonical runbook とする。
- canonical input は `session_manifest.json`、`frame_record.jsonl`、`trajectreview/image` または `trajectreview/images` とする。
- `frame_pose_index.csv` は診断用、`arcore_pose.jsonl` は fallback とする。
- canonical route は `MRL-10 record-native DA3 route` とし、`proof route` と `production route` を分離する。
- `1 record = image + pose + intrinsics + timestamp` の構造を `Colab` 側で壊さないことを最優先とする。

## Route Policy

- `proof route`
  - QC 通過後の subset を使って短く壊れ方を見る。
  - 既定では `baseline thinning` 後の先頭 `24` frame までを使う。
- `production route`
  - QC 通過した全 record を主対象にする。
  - 固定枚数 cap は置かない。
  - thinning は `skip reason` を残す時だけ許可する。
- record-native canonical route では常に
  - `image[]`
  - `intrinsics[N,3,3]`
  - `extrinsics_w2c[N,4,4]`
  を manifest として生成する。
- `DA3Metric-Large` は現行 upstream 制約により image-only 推論とし、`intrinsics` / `extrinsics_w2c` は world projection と評価証跡に使う。
- `Giant` proof living route は `DA3NESTED-GIANT-LARGE-1.1`、`da3_estimated pose`、`debug_gs_readback` bundle を canonical とする。

## Orientation Policy

- canonical image は `correcting` 側で `90度右回転` 済みの upright JPEG を受け取る前提とする。
- `Colab` 側は image pixel を再回転しない。
- `Block 1` では、実画像の `width` / `height` と `frame_record.jsonl` の `imageIntrinsics` を照合し、すでに upright ならそのまま使う。
- legacy session のように intrinsics だけ raw 向きで `width` / `height` が swap している時は、`90度右回転` の式で `fx` / `fy` / `cx` / `cy` を canonical upright 基準へ補正する。
- 上記の判定結果は `input_frame_manifest.csv`、`k_resize_check.csv`、`orientation_summary.json` に残す。

## Bundle Naming Policy

- `correcting` 側の canonical zip 名は `trajectreview/correcting/trajectreview-correcting-session-YYYYMMDD-HHMMSS.zip` とする。
- `modeling` 側の Drive 正本保存先は、`1 correcting session = 1 modeling directory` とし、`MyDrive/trajectreview/modeling/<modeling_session_id>_<route_slug>/` だけを使う。
- `Colab` runbook では `selected input` の `session_id` が `trajectreview-correcting-session-*` なら、Drive 正本 directory 名に使う `modeling_session_id` を `trajectreview-modeling-session-*` へ置き換えて使う。
- download 用 zip は Drive 上へ重複保存せず、必要時だけ `/content/<modeling_session_id>_<model_slug>_...zip` を作る。
- binary `gs_ply` は text viewer で文字化けするため、runbook は header、property stats、focus stats、`xyz_only.ply` を `debug_gs_visible_copy/` と bundle zip に同梱する。

## 実行順

1. `準備確認 1-4`
2. `install`
3. `MRL-10 Block 1`
4. `MRL-10 Block 2`
5. 必要時のみ `MRL-10 Block 3`
6. 必要時のみ `MRL-10 Block 4`
7. 必要時のみ `MRL-10 Block 5` を `RUN_BATCH_INDEX` を変えながら繰り返す
   - 例: `0`, `1`, `2`, `3` ...
   - 1 回の `Block 5` で `3chunk` だけ処理する
   - ただし `1chunk = 18frame`、`chunk overlap = 6frame`、各 chunk の再構成責務は基本 `後半 12frame` とする
8. 最後に `MRL-10 Block 6`

## 準備確認

### #1 準備確認 1

```python
#1
import os
from pathlib import Path
import torch
from google.colab import drive

drive.mount("/content/drive", force_remount=True)

print("cwd", os.getcwd())
print("cuda_available", torch.cuda.is_available())
print("drive_exists", Path("/content/drive").exists())
print("mydrive_exists", Path("/content/drive/MyDrive").exists())
print("shortcut_root_exists", Path("/content/drive/.shortcut-targets-by-id").exists())
```

### #2 準備確認 2

```python
#2
from pathlib import Path
import json
import shutil
import zipfile

# ===== 固定定数 =====
OAI_SHORTCUT_ID = "1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_"
SHORTCUT_ROOT = Path(f"/content/drive/.shortcut-targets-by-id/{OAI_SHORTCUT_ID}")

# 探索対象は raw correcting と既存 modeling の両方
RAW_SCAN_ROOTS = [
    SHORTCUT_ROOT / "trajectreview" / "correcting",
    Path("/content/drive/MyDrive/trajectreview/correcting"),
]

# 保存先は modeling
RESULTS_ROOT_CANDIDATES = [
    Path("/content/drive/MyDrive/trajectreview/modeling"),
    SHORTCUT_ROOT / "trajectreview" / "modeling",
]

RESULTS_ROOT = next((p for p in RESULTS_ROOT_CANDIDATES if p.exists()), RESULTS_ROOT_CANDIDATES[0])
RESULTS_ROOT.mkdir(parents=True, exist_ok=True)

EXTRACT_ROOT = Path("/content/trajectreview_input")
RUNBOOK_CANDIDATE_DOC = Path("/content/runbook_drive_candidates.json")
RUNBOOK_SELECTED_DOC = Path("/content/runbook_selected_input.json")
RUNBOOK_PATHS_DOC = Path("/content/runbook_paths.json")

def infer_session_id(path: Path) -> str:
    return path.stem if path.suffix.lower() == ".zip" else path.name

def scan_candidates(scan_roots):
    zip_map = {}
    dir_map = {}

    for root in scan_roots:
        if not root.exists():
            continue

        for zip_path in sorted(root.rglob("*.zip")):
            stat = zip_path.stat()
            key = (infer_session_id(zip_path), stat.st_size)
            zip_map[key] = {
                "kind": "zip",
                "session_id": infer_session_id(zip_path),
                "label": f"{infer_session_id(zip_path)} [zip]",
                "path": str(zip_path),
                "size_bytes": stat.st_size,
            }

        for manifest_path in sorted(root.rglob("session_manifest.json")):
            session_dir = manifest_path.parent
            dir_map[infer_session_id(session_dir)] = {
                "kind": "dir",
                "session_id": infer_session_id(session_dir),
                "label": f"{infer_session_id(session_dir)} [dir]",
                "path": str(session_dir),
            }

    return sorted(
        list(zip_map.values()) + list(dir_map.values()),
        key=lambda x: (x["session_id"], x["kind"], x["path"]),
    )

def scan_modeling_candidates(results_root: Path):
    rows = []
    if not results_root.exists():
        return rows
    for p in sorted(results_root.iterdir(), key=lambda x: x.name):
        if not p.is_dir():
            continue
        if not p.name.startswith("trajectreview-modeling-session-"):
            continue
        pipeline_root = p / "continuous_gs_v06_chunk18_overlap6_adopt12"
        rows.append({
            "kind": "modeling_dir",
            "source_family": "modeling",
            "session_id": p.name,
            "label": f"{p.name} [modeling]",
            "path": str(p),
            "has_chunk_pipeline": bool(pipeline_root.exists()),
            "has_chunk_runs": bool((pipeline_root / "chunk_runs").exists()),
        })
    return rows

def reset_extract_root():
    if EXTRACT_ROOT.exists():
        shutil.rmtree(EXTRACT_ROOT)
    EXTRACT_ROOT.mkdir(parents=True, exist_ok=True)

def extract_selected_input(selected_path: Path, selected_kind: str):
    reset_extract_root()
    if selected_kind == "zip":
        with zipfile.ZipFile(selected_path, "r") as zf:
            zf.extractall(EXTRACT_ROOT)
    else:
        shutil.copytree(selected_path, EXTRACT_ROOT / selected_path.name)

def pick_best_raw_root(base: Path) -> Path:
    manifest_hits = sorted(base.rglob("session_manifest.json"))
    if manifest_hits:
        root = manifest_hits[0].parent
        if root.name != "trajectreview" and (root / "trajectreview").exists():
            return root / "trajectreview"
        return root

    package_hits = sorted(base.rglob("session_package.json"))
    if package_hits:
        pkg_parent = package_hits[0].parent
        root = pkg_parent.parent if pkg_parent.name == "trajectreview" else pkg_parent
        if root.name != "trajectreview" and (root / "trajectreview").exists():
            return root / "trajectreview"
        return root

    frame_hits = sorted(list(base.rglob("frame_record.jsonl")) + list(base.rglob("arcore_pose.jsonl")))
    image_dir_hits = sorted([p for p in base.rglob("*") if p.is_dir() and p.name in {"images", "image"}])
    candidate_roots = []

    for p in frame_hits:
        candidate_roots.append(p.parent)
        if (p.parent / "trajectreview").exists():
            candidate_roots.append(p.parent / "trajectreview")

    for p in image_dir_hits:
        candidate_roots.append(p.parent)
        if (p.parent / "trajectreview").exists():
            candidate_roots.append(p.parent / "trajectreview")

    for c in candidate_roots:
        if c.name == "trajectreview":
            return c

    if candidate_roots:
        root = candidate_roots[0]
        if root.name != "trajectreview" and (root / "trajectreview").exists():
            return root / "trajectreview"
        return root

    dirs = [p for p in base.iterdir() if p.is_dir()]
    if len(dirs) == 1:
        only = dirs[0]
        if (only / "trajectreview").exists():
            return only / "trajectreview"
        return only

    raise AssertionError(f"raw session root not found under {base}")

def resolve_and_validate_paths(selected_doc: dict):
    selected_path = Path(selected_doc["path"])
    selected_kind = selected_doc["kind"]
    session_id = selected_doc["session_id"]

    assert selected_path.exists(), f"selected input missing: {selected_path}"

    extract_selected_input(selected_path, selected_kind)

    session_root = pick_best_raw_root(EXTRACT_ROOT)
    if session_root.name != "trajectreview" and (session_root / "trajectreview").exists():
        session_root = session_root / "trajectreview"
    session_outer = session_root.parent if session_root.name == "trajectreview" else session_root

    image_dir_candidates = [
        session_root / "images",
        session_root / "image",
        session_outer / "images",
        session_outer / "image",
        session_outer / "trajectreview" / "images",
        session_outer / "trajectreview" / "image",
    ]
    valid_image_dirs = []
    for p in image_dir_candidates:
        if not p.exists():
            continue
        image_count = (
            len(list(p.glob("*.jpg"))) +
            len(list(p.glob("*.jpeg"))) +
            len(list(p.glob("*.png"))) +
            len(list(p.glob("*.JPG"))) +
            len(list(p.glob("*.JPEG"))) +
            len(list(p.glob("*.PNG")))
        )
        valid_image_dirs.append((p, image_count))
    assert valid_image_dirs, {"image_dir_candidates": [str(p) for p in image_dir_candidates]}
    valid_image_dirs = sorted(valid_image_dirs, key=lambda x: (-x[1], len(str(x[0]))))
    images_dir = valid_image_dirs[0][0]

    frame_record_candidates = [
        session_outer / "frame_record.jsonl",
        session_root / "frame_record.jsonl",
        session_root / "arcore_pose.jsonl",
        session_outer / "arcore_pose.jsonl",
        session_outer / "trajectreview" / "frame_record.jsonl",
        session_outer / "trajectreview" / "arcore_pose.jsonl",
    ]
    frame_record_path = next((p for p in frame_record_candidates if p.exists()), None)
    assert frame_record_path is not None, {"frame_record_candidates": [str(p) for p in frame_record_candidates]}

    probe_root = RESULTS_ROOT / modeling_session_id
    proof_metric_dir = probe_root / "proof_metriclarge"
    prod_metric_dir = probe_root / "prod_metriclarge"
    proof_giant_dir = probe_root / "proof_giant"
    world_dir = probe_root / "world_fusion_v01"
    manifest_dir = probe_root / "manifests"
    final_outputs_dir = probe_root / "final_outputs"
    final_outputs_merged_dir = final_outputs_dir / "merged"
    final_outputs_diagnostics_dir = final_outputs_dir / "diagnostics"
    final_outputs_manifests_dir = final_outputs_dir / "manifests"
    final_outputs_chunk_evidence_dir = final_outputs_dir / "chunk_evidence"

    for p in [
        probe_root,
        proof_metric_dir,
        prod_metric_dir,
        proof_giant_dir,
        world_dir,
        manifest_dir,
        final_outputs_dir,
        final_outputs_merged_dir,
        final_outputs_diagnostics_dir,
        final_outputs_manifests_dir,
        final_outputs_chunk_evidence_dir,
    ]:
        p.mkdir(parents=True, exist_ok=True)

    return {
        "session_id": session_id,
        "selected_kind": selected_kind,
        "source_family": selected_doc.get("source_family", "correcting"),
        "selected_path": str(selected_path),
        "results_root": str(RESULTS_ROOT),
        "results_root_visibility": "google_drive_mydrive_visible",
        "extract_root": str(EXTRACT_ROOT),
        "probe_root": str(probe_root),
        "manifest_dir": str(manifest_dir),
        "proof_metric_dir": str(proof_metric_dir),
        "prod_metric_dir": str(prod_metric_dir),
        "proof_giant_dir": str(proof_giant_dir),
        "world_dir": str(world_dir),
        "final_outputs_dir": str(final_outputs_dir),
        "final_outputs_merged_dir": str(final_outputs_merged_dir),
        "final_outputs_diagnostics_dir": str(final_outputs_diagnostics_dir),
        "final_outputs_manifests_dir": str(final_outputs_manifests_dir),
        "final_outputs_chunk_evidence_dir": str(final_outputs_chunk_evidence_dir),
        "images_dir": str(images_dir),
        "images_dir_file_count": int(valid_image_dirs[0][1]),
        "image_dir_candidates_ranked": [{"path": str(p), "image_count": int(c)} for p, c in valid_image_dirs],
        "frame_record_path": str(frame_record_path),
        "session_root": str(session_root),
        "session_outer": str(session_outer),
        "input_mode": "raw_session",
    }

def resolve_modeling_probe_paths(selected_doc: dict):
    selected_path = Path(selected_doc["path"])
    assert selected_path.exists(), f"selected modeling directory missing: {selected_path}"
    pipeline_root = selected_path / "continuous_gs_v06_chunk18_overlap6_adopt12"
    manifest_dir = selected_path / "manifests"
    required_paths = [
        pipeline_root,
        pipeline_root / "global_pose_bootstrap" / "camera_matrix_full.csv",
        pipeline_root / "global_pose_bootstrap" / "camera_center_matrix.csv",
        pipeline_root / "manifests" / "chunk_index_all.csv",
        pipeline_root / "chunk_runs",
        manifest_dir / "da3_input_manifest_prod.csv",
    ]
    for p in required_paths:
        assert p.exists(), f"modeling probe_root missing required path: {p}"

    return {
        "session_id": selected_doc["session_id"],
        "selected_kind": selected_doc["kind"],
        "source_family": "modeling",
        "selected_path": str(selected_path),
        "results_root": str(RESULTS_ROOT),
        "results_root_visibility": "google_drive_mydrive_visible",
        "probe_root": str(selected_path),
        "pipeline_root": str(pipeline_root),
        "manifest_dir": str(manifest_dir),
        "proof_metric_dir": str(selected_path / "proof_metriclarge"),
        "prod_metric_dir": str(selected_path / "prod_metriclarge"),
        "proof_giant_dir": str(selected_path / "proof_giant"),
        "world_dir": str(selected_path / "world_fusion_v01"),
        "final_outputs_dir": str(selected_path / "final_outputs"),
        "final_outputs_merged_dir": str(selected_path / "final_outputs" / "merged"),
        "final_outputs_diagnostics_dir": str(selected_path / "final_outputs" / "diagnostics"),
        "final_outputs_manifests_dir": str(selected_path / "final_outputs" / "manifests"),
        "final_outputs_chunk_evidence_dir": str(selected_path / "final_outputs" / "chunk_evidence"),
        "chunk_runs_dir": str(pipeline_root / "chunk_runs"),
        "input_mode": "existing_modeling_probe_root",
    }

def build_context_doc_from_paths(paths: dict) -> dict:
    probe_root = Path(paths["probe_root"])
    session_root = Path(paths["session_root"]) if "session_root" in paths else probe_root
    frame_pose_index_path = Path(paths["frame_pose_index_path"]) if "frame_pose_index_path" in paths else (session_root / "frame_pose_index.csv")
    selected_path = Path(paths["selected_path"])
    session_id = paths["session_id"]
    selected_kind = paths["selected_kind"]
    results_root = Path(paths["results_root"])
    route_slug = "da3_record_route_v01"
    modeling_session_id = session_id.replace("trajectreview-correcting-session-", "trajectreview-modeling-session-", 1) if session_id.startswith("trajectreview-correcting-session-") else session_id
    if selected_kind == "modeling_dir":
        modeling_session_id = probe_root.name
    return {
        "session_id": session_id,
        "modeling_session_id": modeling_session_id,
        "selected_kind": selected_kind,
        "selected_path": str(selected_path),
        "results_root": str(results_root),
        "results_root_visibility": paths.get("results_root_visibility", "google_drive_mydrive_visible"),
        "route_slug": route_slug,
        "probe_root_name": probe_root.name,
        "session_outer": str(Path(paths["session_outer"])) if "session_outer" in paths else str(probe_root),
        "session_root": str(session_root),
        "images_dir": str(Path(paths["images_dir"])) if "images_dir" in paths else "",
        "frame_record_path": str(Path(paths["frame_record_path"])) if "frame_record_path" in paths else "",
        "frame_pose_index_path": str(frame_pose_index_path),
        "probe_root": str(probe_root),
        "proof_metric_dir": str(Path(paths["proof_metric_dir"])),
        "prod_metric_dir": str(Path(paths["prod_metric_dir"])),
        "proof_giant_dir": str(Path(paths["proof_giant_dir"])),
        "world_dir": str(Path(paths["world_dir"])),
        "manifest_dir": str(Path(paths["manifest_dir"])),
        "merged_dir": str(Path(paths["merged_dir"])) if "merged_dir" in paths else str(probe_root / "continuous_gs_v06_chunk18_overlap6_adopt12" / "merged"),
        "final_outputs_dir": str(Path(paths["final_outputs_dir"])),
        "final_outputs_merged_dir": str(Path(paths["final_outputs_merged_dir"])),
        "final_outputs_diagnostics_dir": str(Path(paths["final_outputs_diagnostics_dir"])),
        "final_outputs_manifests_dir": str(Path(paths["final_outputs_manifests_dir"])),
        "final_outputs_chunk_evidence_dir": str(Path(paths["final_outputs_chunk_evidence_dir"])),
        "add_suffix": paths.get("add_suffix", ""),
        "resume_mode": "existing_probe_root" if selected_kind == "modeling_dir" else "",
        "pipeline_root": paths.get("pipeline_root", str(probe_root / "continuous_gs_v06_chunk18_overlap6_adopt12")),
        "chunk_runs_dir": paths.get("chunk_runs_dir", ""),
        "input_mode": paths.get("input_mode", ""),
    }

candidate_doc = {
    "results_root": str(RESULTS_ROOT),
    "results_root_visibility": "google_drive_mydrive_visible",
    "scan_roots": [str(p) for p in RAW_SCAN_ROOTS] + [str(RESULTS_ROOT)],
    "candidate_count": 0,
    "candidates": scan_candidates(RAW_SCAN_ROOTS) + scan_modeling_candidates(RESULTS_ROOT),
}
candidate_doc["candidate_count"] = len(candidate_doc["candidates"])
RUNBOOK_CANDIDATE_DOC.write_text(json.dumps(candidate_doc, indent=2, ensure_ascii=False), encoding="utf-8")
print("RUNBOOK_CANDIDATE_DOC", RUNBOOK_CANDIDATE_DOC)
print("RESULTS_ROOT", RESULTS_ROOT)
print("candidate_count", candidate_doc["candidate_count"])
for idx, item in enumerate(candidate_doc["candidates"]):
    print(f"[{idx}] {item['label']}: {item['path']}")
```

### #3 準備確認 3

```python
#3
from pathlib import Path
import json
import ipywidgets as widgets
from IPython.display import display

candidate_doc = json.loads(Path("/content/runbook_drive_candidates.json").read_text(encoding="utf-8"))
selected_doc_path = RUNBOOK_SELECTED_DOC if "RUNBOOK_SELECTED_DOC" in globals() else Path("/content/runbook_selected_input.json")
options = [(f"[{idx}] {item['label']}", idx) for idx, item in enumerate(candidate_doc["candidates"])]
dropdown = widgets.Dropdown(options=options, description="input", layout=widgets.Layout(width="95%"))
button = widgets.Button(description="selected input を保存", button_style="success")
output = widgets.Output()

def on_click(_):
    selected = candidate_doc["candidates"][dropdown.value]
    selected_doc = {
        "selected_index": dropdown.value,
        "kind": selected["kind"],
        "source_family": selected.get("source_family", "correcting" if selected["kind"] in {"zip", "dir"} else "modeling"),
        "session_id": selected["session_id"],
        "label": selected["label"],
        "path": selected["path"],
        "results_root": candidate_doc["results_root"],
    }
    selected_doc_path.write_text(json.dumps(selected_doc, indent=2, ensure_ascii=False), encoding="utf-8")
    with output:
        output.clear_output()
        print(json.dumps(selected_doc, indent=2, ensure_ascii=False))
        print("selected_exists", Path(selected["path"]).exists())

button.on_click(on_click)
display(dropdown, button, output)
```

- `#3` で `... [zip]` または `... [dir]` を選んだ時は `correcting` の raw input として扱う。
- `#3` で `... [modeling]` を選んだ時は、既存 chunk ありの `probe_root` として扱う。

### #4 準備確認 4

```python
#4
from pathlib import Path
import json

assert "resolve_and_validate_paths" in globals(), "#2 を先に実行して helper を定義してください"
assert "RUNBOOK_PATHS_DOC" in globals(), "#2 を先に実行して RUNBOOK_PATHS_DOC を定義してください"
if "build_context_doc_from_paths" not in globals():
    def build_context_doc_from_paths(paths: dict) -> dict:
        probe_root = Path(paths["probe_root"])
        session_root = Path(paths["session_root"]) if "session_root" in paths else probe_root
        frame_pose_index_path = Path(paths["frame_pose_index_path"]) if "frame_pose_index_path" in paths else (session_root / "frame_pose_index.csv")
        selected_path = Path(paths["selected_path"])
        session_id = paths["session_id"]
        selected_kind = paths["selected_kind"]
        results_root = Path(paths["results_root"])
        route_slug = "da3_record_route_v01"
        modeling_session_id = session_id.replace("trajectreview-correcting-session-", "trajectreview-modeling-session-", 1) if session_id.startswith("trajectreview-correcting-session-") else session_id
        if selected_kind == "modeling_dir":
            modeling_session_id = probe_root.name
        return {
            "session_id": session_id,
            "modeling_session_id": modeling_session_id,
            "selected_kind": selected_kind,
            "selected_path": str(selected_path),
            "results_root": str(results_root),
            "results_root_visibility": paths.get("results_root_visibility", "google_drive_mydrive_visible"),
            "route_slug": route_slug,
            "probe_root_name": probe_root.name,
            "session_outer": str(Path(paths["session_outer"])) if "session_outer" in paths else str(probe_root),
            "session_root": str(session_root),
            "images_dir": str(Path(paths["images_dir"])) if "images_dir" in paths else "",
            "frame_record_path": str(Path(paths["frame_record_path"])) if "frame_record_path" in paths else "",
            "frame_pose_index_path": str(frame_pose_index_path),
            "probe_root": str(probe_root),
            "proof_metric_dir": str(Path(paths["proof_metric_dir"])),
            "prod_metric_dir": str(Path(paths["prod_metric_dir"])),
            "proof_giant_dir": str(Path(paths["proof_giant_dir"])),
            "world_dir": str(Path(paths["world_dir"])),
            "manifest_dir": str(Path(paths["manifest_dir"])),
            "merged_dir": str(Path(paths["merged_dir"])) if "merged_dir" in paths else str(probe_root / "continuous_gs_v06_chunk18_overlap6_adopt12" / "merged"),
            "final_outputs_dir": str(Path(paths["final_outputs_dir"])),
            "final_outputs_merged_dir": str(Path(paths["final_outputs_merged_dir"])),
            "final_outputs_diagnostics_dir": str(Path(paths["final_outputs_diagnostics_dir"])),
            "final_outputs_manifests_dir": str(Path(paths["final_outputs_manifests_dir"])),
            "final_outputs_chunk_evidence_dir": str(Path(paths["final_outputs_chunk_evidence_dir"])),
            "add_suffix": paths.get("add_suffix", ""),
            "resume_mode": "existing_probe_root" if selected_kind == "modeling_dir" else "",
            "pipeline_root": paths.get("pipeline_root", str(probe_root / "continuous_gs_v06_chunk18_overlap6_adopt12")),
            "chunk_runs_dir": paths.get("chunk_runs_dir", ""),
            "input_mode": paths.get("input_mode", ""),
        }
selected_doc = json.loads(RUNBOOK_SELECTED_DOC.read_text(encoding="utf-8")) if "RUNBOOK_SELECTED_DOC" in globals() else json.loads(Path("/content/runbook_selected_input.json").read_text(encoding="utf-8"))
if selected_doc.get("source_family") == "modeling" or selected_doc.get("kind") == "modeling_dir":
    paths = resolve_modeling_probe_paths(selected_doc)
else:
    paths = resolve_and_validate_paths(selected_doc)
RUNBOOK_PATHS_DOC.write_text(json.dumps(paths, indent=2, ensure_ascii=False), encoding="utf-8")
context_doc = build_context_doc_from_paths(paths)
Path("/content/runbook_session_context.json").write_text(json.dumps(context_doc, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(paths, indent=2, ensure_ascii=False))
print("# runbook_session_context")
print(json.dumps(context_doc, indent=2, ensure_ascii=False))
```

## #5 install

```python
#5
from pathlib import Path
import inspect
import shutil
import subprocess
import sys

repo_root = Path("/content/Depth-Anything-3")
if repo_root.exists():
    shutil.rmtree(repo_root)
subprocess.run(["git", "clone", "https://github.com/ByteDance-Seed/Depth-Anything-3.git", str(repo_root)], check=True)

subprocess.run([
    "python", "-m", "pip", "install", "--quiet",
    "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile", "trimesh", "gsplat", "e3nn"
], check=True)

src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from depth_anything_3.api import DepthAnything3
import gsplat
import e3nn

print("repo_exists", repo_root.exists(), repo_root)
print("dependency_install_ok")
print("depth_anything_3_import_ok", DepthAnything3)
print("gsplat_version", getattr(gsplat, "__version__", "unknown"))
print("e3nn_version", getattr(e3nn, "__version__", "unknown"))
print("inference_sig", inspect.signature(DepthAnything3.inference))
```

## MRL-10 record-native DA3 route

### 再利用方法

- 既存 `probe_root` を再利用して merge 系だけをやり直す場合でも、runtime 初期化と path cache 生成のため `#1` から `#4` は必須とする。
- `#3` では `correcting` と `modeling` を明示的に選べる。`correcting` を選んだ時は raw input 扱い、`modeling` を選んだ時は既存 chunk ありの `probe_root` 扱いとする。
- 既存 modeling data を使う最短順は `#1 -> #2 -> #3 -> #4 -> #6-1b -> #10-5 -> #11` とする。必要なら `#6-1a` で候補一覧を再表示してよい。
- `correcting` を選んだ時は raw session 前提なので、通常どおり前段から全工程を進める。
- cleanup が必要な時だけ `#12` と `#13` を続ける。

### #6-1 正規化 + context pack

```python
#6-1
from pathlib import Path
import json

paths = json.loads(Path("/content/runbook_paths.json").read_text(encoding="utf-8"))
selected_path = Path(paths["selected_path"])
selected_kind = paths["selected_kind"]
session_id = paths["session_id"]
results_root = Path(paths["results_root"])
assert str(results_root).startswith("/content/drive/MyDrive/"), results_root
results_root.mkdir(parents=True, exist_ok=True)
session_root = Path(paths["session_root"])
session_outer = Path(paths["session_outer"])
images_dir = Path(paths["images_dir"])
frame_record_path = Path(paths["frame_record_path"])
frame_pose_index_path = session_root / "frame_pose_index.csv"
route_slug = "da3_record_route_v01"
modeling_session_id = session_id.replace("trajectreview-correcting-session-", "trajectreview-modeling-session-", 1) if session_id.startswith("trajectreview-correcting-session-") else f"trajectreview-modeling-session-{session_id}"
probe_root_name = modeling_session_id
probe_root = Path(paths["probe_root"])
merged_dir = probe_root / "continuous_gs_v06_chunk18_overlap6_adopt12" / "merged"
proof_metric_dir = Path(paths["proof_metric_dir"])
prod_metric_dir = Path(paths["prod_metric_dir"])
proof_giant_dir = Path(paths["proof_giant_dir"])
world_dir = Path(paths["world_dir"])
manifest_dir = Path(paths["manifest_dir"])
final_outputs_dir = Path(paths["final_outputs_dir"])
final_outputs_merged_dir = Path(paths["final_outputs_merged_dir"])
final_outputs_diagnostics_dir = Path(paths["final_outputs_diagnostics_dir"])
final_outputs_manifests_dir = Path(paths["final_outputs_manifests_dir"])
final_outputs_chunk_evidence_dir = Path(paths["final_outputs_chunk_evidence_dir"])

for p in [
    probe_root,
    proof_metric_dir,
    prod_metric_dir,
    proof_giant_dir,
    world_dir,
    manifest_dir,
    final_outputs_dir,
    final_outputs_merged_dir,
    final_outputs_diagnostics_dir,
    final_outputs_manifests_dir,
    final_outputs_chunk_evidence_dir,
]:
    p.mkdir(parents=True, exist_ok=True)

context_doc = {
    "session_id": session_id,
    "modeling_session_id": modeling_session_id,
    "selected_kind": selected_kind,
    "selected_path": str(selected_path),
    "results_root": str(results_root),
    "results_root_visibility": "google_drive_mydrive_visible",
    "route_slug": route_slug,
    "probe_root_name": probe_root_name,
    "session_outer": str(session_outer),
    "session_root": str(session_root),
    "images_dir": str(images_dir),
    "frame_record_path": str(frame_record_path),
    "frame_pose_index_path": str(frame_pose_index_path),
    "probe_root": str(probe_root),
    "proof_metric_dir": str(proof_metric_dir),
    "prod_metric_dir": str(prod_metric_dir),
    "proof_giant_dir": str(proof_giant_dir),
    "world_dir": str(world_dir),
    "manifest_dir": str(manifest_dir),
    "merged_dir": str(merged_dir),
    "final_outputs_dir": str(final_outputs_dir),
    "final_outputs_merged_dir": str(final_outputs_merged_dir),
    "final_outputs_diagnostics_dir": str(final_outputs_diagnostics_dir),
    "final_outputs_manifests_dir": str(final_outputs_manifests_dir),
    "final_outputs_chunk_evidence_dir": str(final_outputs_chunk_evidence_dir),
    "add_suffix": "",
}
Path("/content/runbook_session_context.json").write_text(json.dumps(context_doc, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(context_doc, indent=2, ensure_ascii=False))
```

### #6-1b 既存 probe_root 参照で再開

- すでに Drive 上に `probe_root` があり、chunk 実行結果や manifest を再利用して `#10-5` または `#11` から再開したい時はこの cell を使う。
- ただし再開時も `#1` から `#4` は省略せず先に実行し、Drive mount、selected input、`runbook_paths.json` をそろえる。
- `EXISTING_PROBE_ROOT` には `continuous_gs_v06_chunk18_overlap6_adopt12/` を含む既存 root を入れる。
- この cell は既存 tree を読み、`runbook_session_context.json` だけを再生成する。未作成 route の `#6-1` と同じ親番の再開枝番とする。
- canonical な top directory 名は modeling session 名そのもの、たとえば `trajectreview-modeling-session-20260403_gl11_c18ov6ad12` とする。
- 既存 data を読んで追加生成する時の出力先は、既存物へ上書きせず `_add**` suffix を付けた directory / file へ分離する。連番は `01` から始め、未使用の最小番号を採る。

```python
#6-1a
from pathlib import Path
import json

RUNBOOK_PATHS_DOC = Path("/content/runbook_paths.json")
assert RUNBOOK_PATHS_DOC.exists(), "再開でも #2 -> #3 -> #4 を先に実行して /content/runbook_paths.json を作成してください"
paths = json.loads(RUNBOOK_PATHS_DOC.read_text(encoding="utf-8"))
results_root = Path(paths["results_root"])
assert str(results_root).startswith("/content/drive/MyDrive/"), results_root
assert results_root.exists(), results_root

candidates = sorted(
    [p for p in results_root.iterdir() if p.is_dir() and p.name.startswith("trajectreview-modeling-session-")],
    key=lambda p: p.name,
)
assert candidates, f"no modeling directories found under {results_root}"

selected_modeling_path = Path(paths["selected_path"]) if paths.get("selected_kind") == "modeling_dir" else None
selected_modeling_name = selected_modeling_path.name if selected_modeling_path is not None else ""

rows = [
    {
        "index": i,
        "name": p.name,
        "path": str(p),
        "selected_by_block3": bool(p.name == selected_modeling_name),
    }
    for i, p in enumerate(candidates)
]
Path("/content/runbook_existing_probe_roots.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({
    "results_root": str(results_root),
    "candidate_count": len(rows),
    "candidates": rows,
}, indent=2, ensure_ascii=False))
```

```python
#6-1b
from pathlib import Path
import json

SELECT_MODELING_INDEX = 0
SELECT_MODELING_NAME = ""

RUNBOOK_PATHS_DOC = Path("/content/runbook_paths.json")
assert RUNBOOK_PATHS_DOC.exists(), "再開でも #2 -> #3 -> #4 を先に実行して /content/runbook_paths.json を作成してください"
paths = json.loads(RUNBOOK_PATHS_DOC.read_text(encoding="utf-8"))
results_root = Path(paths["results_root"])
candidate_cache_path = Path("/content/runbook_existing_probe_roots.json")
if candidate_cache_path.exists():
    candidates = json.loads(candidate_cache_path.read_text(encoding="utf-8"))
else:
    candidates = [
        {"index": i, "name": p.name, "path": str(p)}
        for i, p in enumerate(sorted(
            [p for p in results_root.iterdir() if p.is_dir() and p.name.startswith("trajectreview-modeling-session-")],
            key=lambda p: p.name,
        ))
    ]
assert candidates, f"no modeling directories found under {results_root}"

selected_modeling_path = Path(paths["selected_path"]) if paths.get("selected_kind") == "modeling_dir" else None
if selected_modeling_path is not None and selected_modeling_path.exists() and not SELECT_MODELING_NAME:
    matched = [row for row in candidates if Path(row["path"]) == selected_modeling_path]
    if matched:
        SELECT_MODELING_INDEX = int(matched[0]["index"])

if SELECT_MODELING_NAME:
    matched = [row for row in candidates if row["name"] == SELECT_MODELING_NAME]
    assert matched, {"SELECT_MODELING_NAME": SELECT_MODELING_NAME, "candidates": candidates}
    selected_row = matched[0]
else:
    matched = [row for row in candidates if int(row["index"]) == int(SELECT_MODELING_INDEX)]
    assert matched, {"SELECT_MODELING_INDEX": SELECT_MODELING_INDEX, "candidates": candidates}
    selected_row = matched[0]

EXISTING_PROBE_ROOT = Path(selected_row["path"])
assert str(EXISTING_PROBE_ROOT).startswith("/content/drive/MyDrive/"), EXISTING_PROBE_ROOT
assert EXISTING_PROBE_ROOT.exists(), EXISTING_PROBE_ROOT

def resolve_next_add_path(parent: Path, stem: str) -> tuple[Path, str]:
    n = 1
    while True:
        suffix = f"_add{n:02d}"
        candidate = parent / f"{stem}{suffix}"
        if not candidate.exists():
            return candidate, suffix
        n += 1

pipeline_root = EXISTING_PROBE_ROOT / "continuous_gs_v06_chunk18_overlap6_adopt12"
global_pose_dir = pipeline_root / "global_pose_bootstrap"
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"

required_paths = [
    pipeline_root,
    global_pose_dir / "camera_matrix_full.csv",
    global_pose_dir / "camera_center_matrix.csv",
    chunk_manifest_dir / "chunk_index_all.csv",
    chunk_manifest_dir / "da3_input_manifest_prod.csv",
]
for p in required_paths:
    assert p.exists(), f"missing required path: {p}"

selected_path = Path(paths["selected_path"])
selected_kind = paths["selected_kind"]
session_id = paths["session_id"]
assert str(results_root).startswith("/content/drive/MyDrive/"), results_root
session_root = Path(paths["session_root"])
session_outer = Path(paths["session_outer"])
images_dir = Path(paths["images_dir"])
frame_record_path = Path(paths["frame_record_path"])
frame_pose_index_path = session_root / "frame_pose_index.csv"
route_slug = "da3_record_route_v01"
modeling_session_id = EXISTING_PROBE_ROOT.name
probe_root_name = EXISTING_PROBE_ROOT.name
probe_root = EXISTING_PROBE_ROOT
proof_metric_dir = probe_root / "proof_metriclarge"
prod_metric_dir = probe_root / "prod_metriclarge"
proof_giant_dir = probe_root / "proof_giant"
world_dir = probe_root / "world_fusion_v01"
manifest_dir = probe_root / "manifests"
final_outputs_dir, add_suffix = resolve_next_add_path(probe_root, "final_outputs")
final_outputs_merged_dir = final_outputs_dir / "merged"
final_outputs_diagnostics_dir = final_outputs_dir / "diagnostics"
final_outputs_manifests_dir = final_outputs_dir / "manifests"
final_outputs_chunk_evidence_dir = final_outputs_dir / "chunk_evidence"
merged_dir, merged_add_suffix = resolve_next_add_path(pipeline_root, "merged")
assert add_suffix == merged_add_suffix, {"final_outputs_add_suffix": add_suffix, "merged_add_suffix": merged_add_suffix}

for p in [
    final_outputs_dir,
    final_outputs_merged_dir,
    final_outputs_diagnostics_dir,
    final_outputs_manifests_dir,
    final_outputs_chunk_evidence_dir,
]:
    p.mkdir(parents=True, exist_ok=True)

context_doc = {
    "session_id": session_id,
    "modeling_session_id": modeling_session_id,
    "selected_kind": selected_kind,
    "selected_path": str(selected_path),
    "results_root": str(results_root),
    "results_root_visibility": "google_drive_mydrive_visible",
    "route_slug": route_slug,
    "probe_root_name": probe_root_name,
    "session_outer": str(session_outer),
    "session_root": str(session_root),
    "images_dir": str(images_dir),
    "frame_record_path": str(frame_record_path),
    "frame_pose_index_path": str(frame_pose_index_path),
    "probe_root": str(probe_root),
    "proof_metric_dir": str(proof_metric_dir),
    "prod_metric_dir": str(prod_metric_dir),
    "proof_giant_dir": str(proof_giant_dir),
    "world_dir": str(world_dir),
    "manifest_dir": str(manifest_dir),
    "final_outputs_dir": str(final_outputs_dir),
    "final_outputs_merged_dir": str(final_outputs_merged_dir),
    "final_outputs_diagnostics_dir": str(final_outputs_diagnostics_dir),
    "final_outputs_manifests_dir": str(final_outputs_manifests_dir),
    "final_outputs_chunk_evidence_dir": str(final_outputs_chunk_evidence_dir),
    "merged_dir": str(merged_dir),
    "add_suffix": add_suffix,
    "resume_mode": "existing_probe_root",
    "pipeline_root": str(pipeline_root),
    "chunk_runs_dir": str(chunk_runs_dir),
    "source_probe_root": str(EXISTING_PROBE_ROOT),
}
Path("/content/runbook_session_context.json").write_text(json.dumps(context_doc, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(context_doc, indent=2, ensure_ascii=False))
```

### #6-2 QC と manifest 化

```python
#6-2
from pathlib import Path
import csv
import json

import imageio.v3 as iio
import numpy as np
import pandas as pd
from PIL import Image

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
images_dir = Path(ctx["images_dir"])
frame_record_path = Path(ctx["frame_record_path"])
frame_pose_index_path = Path(ctx["frame_pose_index_path"])
manifest_dir = Path(ctx["manifest_dir"])

CANONICAL_ORIENTATION_POLICY = "upright_rot90cw_from_correcting"
BLUR_THRESHOLD = 8.0

with frame_record_path.open("r", encoding="utf-8") as f:
    frame_records = [json.loads(line) for line in f if line.strip()]

frame_pose_df = pd.read_csv(frame_pose_index_path) if frame_pose_index_path.exists() else pd.DataFrame()
image_name_by_record_index = {}
if len(frame_pose_df) > 0:
    image_name_col = next((c for c in ["image_file_name", "imageFileName", "frame_name"] if c in frame_pose_df.columns), None)
    record_index_col = next((c for c in ["pose_record_index", "record_index"] if c in frame_pose_df.columns), None)
    if image_name_col is not None and record_index_col is not None:
        tmp = frame_pose_df[[record_index_col, image_name_col]].copy()
        tmp = tmp.dropna()
        tmp[image_name_col] = tmp[image_name_col].astype(str).str.strip()
        tmp = tmp.loc[tmp[image_name_col] != ""]
        image_name_by_record_index = {
            int(getattr(row, record_index_col)): getattr(row, image_name_col)
            for row in tmp.itertuples(index=False)
        }
    elif "frame_index" in frame_pose_df.columns:
        sorted_image_names = sorted([
            *[p.name for p in images_dir.glob("*.jpg")],
            *[p.name for p in images_dir.glob("*.jpeg")],
            *[p.name for p in images_dir.glob("*.png")],
            *[p.name for p in images_dir.glob("*.JPG")],
            *[p.name for p in images_dir.glob("*.JPEG")],
            *[p.name for p in images_dir.glob("*.PNG")],
        ])
        record_index_col = next((c for c in ["pose_record_index", "record_index"] if c in frame_pose_df.columns), None)
        if record_index_col is not None:
            for row in frame_pose_df.itertuples(index=False):
                frame_idx = int(getattr(row, "frame_index"))
                if 0 <= frame_idx < len(sorted_image_names):
                    image_name_by_record_index[int(getattr(row, record_index_col))] = sorted_image_names[frame_idx]

def ranked_image_dirs(primary_dir: Path, frame_record_path: Path):
    session_outer = frame_record_path.parent
    session_root = session_outer / "trajectreview" if (session_outer / "trajectreview").exists() else session_outer
    candidates = [
        primary_dir,
        session_root / "images",
        session_root / "image",
        session_outer / "images",
        session_outer / "image",
        session_outer / "trajectreview" / "images",
        session_outer / "trajectreview" / "image",
    ]
    ranked = []
    seen = set()
    for p in candidates:
        key = str(p)
        if key in seen or not p.exists():
            continue
        seen.add(key)
        image_count = (
            len(list(p.glob("*.jpg"))) +
            len(list(p.glob("*.jpeg"))) +
            len(list(p.glob("*.png"))) +
            len(list(p.glob("*.JPG"))) +
            len(list(p.glob("*.JPEG"))) +
            len(list(p.glob("*.PNG")))
        )
        ranked.append((p, image_count))
    return sorted(ranked, key=lambda x: (-x[1], len(str(x[0]))))

def lap_var(image_path: Path) -> float:
    img = iio.imread(image_path)
    if img.ndim == 3:
        gray = img[..., :3].mean(axis=2).astype(np.float32)
    else:
        gray = img.astype(np.float32)
    gx = gray[:, 1:] - gray[:, :-1]
    gy = gray[1:, :] - gray[:-1, :]
    return float(np.var(gx) + np.var(gy))

def read_actual_wh(image_path: Path):
    with Image.open(image_path) as img:
        width, height = img.size
    return int(width), int(height)

def normalize_intrinsics_to_upright(intr, actual_width: int, actual_height: int):
    fx = intr.get("fx")
    fy = intr.get("fy")
    cx = intr.get("cx")
    cy = intr.get("cy")
    intr_width = intr.get("width")
    intr_height = intr.get("height")

    if None in [fx, fy, cx, cy, intr_width, intr_height]:
        return {
            "intrinsics_case": "missing_intrinsics",
            "rotation_applied_deg": None,
            "fx_canonical": None,
            "fy_canonical": None,
            "cx_canonical": None,
            "cy_canonical": None,
            "width_canonical": None,
            "height_canonical": None,
        }

    fx = float(fx)
    fy = float(fy)
    cx = float(cx)
    cy = float(cy)
    intr_width = int(intr_width)
    intr_height = int(intr_height)

    if intr_width == actual_width and intr_height == actual_height:
        return {
            "intrinsics_case": "already_upright",
            "rotation_applied_deg": 0,
            "fx_canonical": fx,
            "fy_canonical": fy,
            "cx_canonical": cx,
            "cy_canonical": cy,
            "width_canonical": actual_width,
            "height_canonical": actual_height,
        }

    if intr_width == actual_height and intr_height == actual_width:
        return {
            "intrinsics_case": "rot90cw_intrinsics_fixed",
            "rotation_applied_deg": 90,
            "fx_canonical": fy,
            "fy_canonical": fx,
            "cx_canonical": float(intr_height - 1) - cy,
            "cy_canonical": cx,
            "width_canonical": actual_width,
            "height_canonical": actual_height,
        }

    return {
        "intrinsics_case": "dimension_mismatch",
        "rotation_applied_deg": None,
        "fx_canonical": None,
        "fy_canonical": None,
        "cx_canonical": None,
        "cy_canonical": None,
        "width_canonical": None,
        "height_canonical": None,
    }

image_dir_ranking = ranked_image_dirs(images_dir, frame_record_path)
resolved_images_dir = image_dir_ranking[0][0]
rows = []
for rec in sorted(frame_records, key=lambda x: int(x.get("frameTimestampNs", 0))):
    image_name = str(rec.get("imageFileName", "") or "").strip()
    if not image_name:
        record_index = rec.get("recordIndex")
        if record_index is not None:
            image_name = str(image_name_by_record_index.get(int(record_index), "")).strip()
    image_path = resolved_images_dir / image_name if image_name else None
    image_exists = bool(image_name) and image_path.exists()
    intr = rec.get("imageIntrinsics") or {}
    pose = rec.get("pose") or {}
    blur_score = lap_var(image_path) if image_exists else None
    actual_width = None
    actual_height = None
    intr_norm = {
        "intrinsics_case": "image_missing",
        "rotation_applied_deg": None,
        "fx_canonical": None,
        "fy_canonical": None,
        "cx_canonical": None,
        "cy_canonical": None,
        "width_canonical": None,
        "height_canonical": None,
    }
    if image_exists:
        actual_width, actual_height = read_actual_wh(image_path)
        intr_norm = normalize_intrinsics_to_upright(intr, actual_width, actual_height)
    rows.append({
        "session_id": rec.get("sessionId"),
        "record_index": rec.get("recordIndex"),
        "frame_timestamp_ns": rec.get("frameTimestampNs"),
        "capture_timestamp_ns": rec.get("captureTimestampNs"),
        "tracking_state": rec.get("trackingState"),
        "image_file_name": image_name,
        "image_path": str(image_path) if image_path else "",
        "resolved_images_dir": str(resolved_images_dir),
        "image_name_source": "frame_record" if str(rec.get("imageFileName", "") or "").strip() else "frame_pose_index_fallback",
        "image_exists": image_exists,
        "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
        "actual_width": actual_width,
        "actual_height": actual_height,
        "fx": intr.get("fx"),
        "fy": intr.get("fy"),
        "cx": intr.get("cx"),
        "cy": intr.get("cy"),
        "width": intr.get("width"),
        "height": intr.get("height"),
        "intrinsics_case": intr_norm["intrinsics_case"],
        "rotation_applied_deg": intr_norm["rotation_applied_deg"],
        "fx_canonical": intr_norm["fx_canonical"],
        "fy_canonical": intr_norm["fy_canonical"],
        "cx_canonical": intr_norm["cx_canonical"],
        "cy_canonical": intr_norm["cy_canonical"],
        "width_canonical": intr_norm["width_canonical"],
        "height_canonical": intr_norm["height_canonical"],
        "tx": pose.get("tx"),
        "ty": pose.get("ty"),
        "tz": pose.get("tz"),
        "qx": pose.get("qx"),
        "qy": pose.get("qy"),
        "qz": pose.get("qz"),
        "qw": pose.get("qw"),
        "blur_score": blur_score,
    })

manifest_df = pd.DataFrame(rows)
manifest_df.to_csv(manifest_dir / "input_frame_manifest.csv", index=False, encoding="utf-8")

qc_df = manifest_df.copy()
qc_df["qc_tracking_ok"] = qc_df["tracking_state"].fillna("") == "TRACKING"
qc_df["qc_image_ok"] = qc_df["image_exists"].fillna(False)
qc_df["qc_orientation_ok"] = qc_df["intrinsics_case"].isin(["already_upright", "rot90cw_intrinsics_fixed"])
qc_df["qc_intrinsics_ok"] = qc_df[["fx_canonical", "fy_canonical", "cx_canonical", "cy_canonical", "width_canonical", "height_canonical"]].notna().all(axis=1)
qc_df["qc_pose_ok"] = qc_df[["tx", "ty", "tz", "qx", "qy", "qz", "qw"]].notna().all(axis=1)
qc_df["blur_score"] = pd.to_numeric(qc_df["blur_score"], errors="coerce")
qc_df["qc_blur_ok"] = qc_df["blur_score"].fillna(0.0).ge(BLUR_THRESHOLD).infer_objects(copy=False)
qc_df["qc_pass"] = qc_df[["qc_tracking_ok", "qc_image_ok", "qc_orientation_ok", "qc_intrinsics_ok", "qc_pose_ok"]].all(axis=1)
qc_df["skip_reason"] = ""
qc_df.loc[~qc_df["qc_tracking_ok"], "skip_reason"] = "tracking_not_ok"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_image_ok"], "skip_reason"] = "image_missing"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_orientation_ok"], "skip_reason"] = "orientation_mismatch"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_intrinsics_ok"], "skip_reason"] = "intrinsics_missing"
qc_df.loc[qc_df["skip_reason"].eq("") & ~qc_df["qc_pose_ok"], "skip_reason"] = "pose_missing"
qc_df.to_csv(manifest_dir / "input_frame_qc.csv", index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)

def quat_to_rot(qx, qy, qz, qw):
    xx, yy, zz = qx*qx, qy*qy, qz*qz
    xy, xz, yz = qx*qy, qx*qz, qy*qz
    wx, wy, wz = qw*qx, qw*qy, qw*qz
    return np.array([
        [1 - 2*(yy + zz), 2*(xy - wz), 2*(xz + wy)],
        [2*(xy + wz), 1 - 2*(xx + zz), 2*(yz - wx)],
        [2*(xz - wy), 2*(yz + wx), 1 - 2*(xx + yy)],
    ], dtype=np.float32)

def pose_to_w2c(row):
    R_c2w = quat_to_rot(float(row.qx), float(row.qy), float(row.qz), float(row.qw))
    t_c2w = np.array([float(row.tx), float(row.ty), float(row.tz)], dtype=np.float32)
    R_w2c = R_c2w.T
    t_w2c = -R_w2c @ t_c2w
    out = np.eye(4, dtype=np.float32)
    out[:3, :3] = R_w2c
    out[:3, 3] = t_w2c
    return out

def build_K(row):
    return np.array([
        [float(row.fx_canonical), 0.0, float(row.cx_canonical)],
        [0.0, float(row.fy_canonical), float(row.cy_canonical)],
        [0.0, 0.0, 1.0],
    ], dtype=np.float32)

adopt_df = qc_df.loc[qc_df["qc_pass"]].copy().sort_values("frame_timestamp_ns").reset_index(drop=True)
if len(adopt_df) < 2:
    fail_counts = {
        "frame_record_count": int(len(qc_df)),
        "qc_pass_count": int(len(adopt_df)),
        "tracking_not_ok": int((~qc_df["qc_tracking_ok"]).sum()),
        "image_missing": int((~qc_df["qc_image_ok"]).sum()),
        "orientation_mismatch": int((~qc_df["qc_orientation_ok"]).sum()),
        "intrinsics_missing": int((~qc_df["qc_intrinsics_ok"]).sum()),
        "pose_missing": int((~qc_df["qc_pose_ok"]).sum()),
        "blur_low_diag_only": int((~qc_df["qc_blur_ok"]).sum()),
        "skip_reason_counts": qc_df["skip_reason"].value_counts(dropna=False).to_dict(),
    }
    (manifest_dir / "qc_failure_summary.json").write_text(json.dumps(fail_counts, indent=2, ensure_ascii=False), encoding="utf-8")
    raise AssertionError(fail_counts)

adopted_rows = []
last_t = None
last_R = None
for row in adopt_df.itertuples(index=False):
    t = np.array([float(row.tx), float(row.ty), float(row.tz)], dtype=np.float32)
    R = quat_to_rot(float(row.qx), float(row.qy), float(row.qz), float(row.qw))
    baseline = None if last_t is None else float(np.linalg.norm(t - last_t))
    rot_delta = None if last_R is None else float(np.degrees(np.arccos(np.clip((np.trace(last_R.T @ R) - 1.0) / 2.0, -1.0, 1.0))))
    geometric_adopt = last_t is None or (baseline >= 0.05) or (rot_delta is not None and rot_delta >= 3.0)
    blur_boost = bool(row.qc_blur_ok) if pd.notna(row.qc_blur_ok) else False
    adopt = geometric_adopt or (last_t is None and blur_boost)
    adopted_rows.append({
        **row._asdict(),
        "baseline_from_prev_adopted_m": baseline,
        "rotation_from_prev_adopted_deg": rot_delta,
        "geometric_adopt": geometric_adopt,
        "prod_adopted": adopt,
        "prod_skip_reason": "" if adopt else "baseline_small",
    })
    if adopt:
        last_t = t
        last_R = R

prod_df = pd.DataFrame(adopted_rows)
prod_df.to_csv(manifest_dir / "pose_conversion_check.csv", index=False, encoding="utf-8")

prod_selected = prod_df.loc[prod_df["prod_adopted"]].copy().reset_index(drop=True)
proof_selected = prod_selected.head(min(24, len(prod_selected))).copy()
assert len(proof_selected) >= 2, {"proof_selected": len(proof_selected)}

for name, df in [("proof", proof_selected), ("prod", prod_selected)]:
    Ks = np.stack([build_K(row) for row in df.itertuples(index=False)], axis=0)
    exts = np.stack([pose_to_w2c(row) for row in df.itertuples(index=False)], axis=0)
    np.save(manifest_dir / f"intrinsics_{name}.npy", Ks)
    np.save(manifest_dir / f"extrinsics_w2c_{name}.npy", exts)
    df.to_csv(manifest_dir / f"da3_input_manifest_{name}.csv", index=False, encoding="utf-8")

k_check = prod_selected[[
    "image_file_name",
    "canonical_orientation_policy",
    "intrinsics_case",
    "rotation_applied_deg",
    "width",
    "height",
    "actual_width",
    "actual_height",
    "width_canonical",
    "height_canonical",
    "fx",
    "fy",
    "cx",
    "cy",
    "fx_canonical",
    "fy_canonical",
    "cx_canonical",
    "cy_canonical",
]].copy()
k_check["resize_mode"] = "native"
k_check.to_csv(manifest_dir / "k_resize_check.csv", index=False, encoding="utf-8")

orientation_summary = {
    "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
    "already_upright_count": int((manifest_df["intrinsics_case"] == "already_upright").sum()),
    "rot90cw_intrinsics_fixed_count": int((manifest_df["intrinsics_case"] == "rot90cw_intrinsics_fixed").sum()),
    "dimension_mismatch_count": int((manifest_df["intrinsics_case"] == "dimension_mismatch").sum()),
    "image_missing_count": int((manifest_df["intrinsics_case"] == "image_missing").sum()),
}
(manifest_dir / "orientation_summary.json").write_text(json.dumps(orientation_summary, indent=2, ensure_ascii=False), encoding="utf-8")

summary = {
    "frame_record_count": int(len(manifest_df)),
    "qc_pass_count": int(len(adopt_df)),
    "qc_skip_count": int((~qc_df["qc_pass"]).sum()),
    "resolved_images_dir": str(resolved_images_dir),
    "resolved_images_dir_file_count": int(image_dir_ranking[0][1]),
    "frame_pose_index_path": str(frame_pose_index_path),
    "frame_pose_fallback_mapping_count": int(len(image_name_by_record_index)),
    "prod_selected_count": int(len(prod_selected)),
    "proof_selected_count": int(len(proof_selected)),
    "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
    "proof_intrinsics_path": str(manifest_dir / "intrinsics_proof.npy"),
    "proof_extrinsics_path": str(manifest_dir / "extrinsics_w2c_proof.npy"),
    "prod_intrinsics_path": str(manifest_dir / "intrinsics_prod.npy"),
    "prod_extrinsics_path": str(manifest_dir / "extrinsics_w2c_prod.npy"),
    "orientation_summary_path": str(manifest_dir / "orientation_summary.json"),
}
(manifest_dir / "qc_summary.json").write_text(json.dumps({
    "frame_record_count": summary["frame_record_count"],
    "qc_pass_count": summary["qc_pass_count"],
    "qc_skip_count": summary["qc_skip_count"],
    "frame_record_path": str(frame_record_path),
    "images_dir": str(images_dir),
    "canonical_orientation_policy": CANONICAL_ORIENTATION_POLICY,
}, indent=2, ensure_ascii=False), encoding="utf-8")
(manifest_dir / "da3_input_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
```

### #7 MetricLarge proof + production + world export

```python
#7
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import torch
from PIL import Image
ctx_path = Path("/content/runbook_session_context.json")
assert ctx_path.exists(), ctx_path
ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
manifest_dir = Path(ctx["manifest_dir"])
proof_metric_dir = Path(ctx["proof_metric_dir"])
prod_metric_dir = Path(ctx["prod_metric_dir"])
world_dir = Path(ctx["world_dir"])
final_outputs_dir = Path(ctx["final_outputs_dir"])
final_outputs_merged_dir = Path(ctx["final_outputs_merged_dir"])
final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_manifests_dir = Path(ctx["final_outputs_manifests_dir"])
final_outputs_chunk_evidence_dir = Path(ctx["final_outputs_chunk_evidence_dir"])

repo_root = Path("/content/Depth-Anything-3")
src_root = repo_root / "src"
assert repo_root.exists(), repo_root
assert src_root.exists(), src_root
assert (src_root / "depth_anything_3" / "api.py").exists(), src_root / "depth_anything_3" / "api.py"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))
for name in list(sys.modules.keys()):
    if name.startswith("depth_anything_3"):
        del sys.modules[name]

from depth_anything_3.api import DepthAnything3

required_dirs = [manifest_dir, proof_metric_dir, prod_metric_dir, world_dir]
for p in required_dirs:
    p.mkdir(parents=True, exist_ok=True)

required_files = {
    "proof_manifest": manifest_dir / "da3_input_manifest_proof.csv",
    "prod_manifest": manifest_dir / "da3_input_manifest_prod.csv",
    "proof_intrinsics": manifest_dir / "intrinsics_proof.npy",
    "proof_extrinsics": manifest_dir / "extrinsics_w2c_proof.npy",
    "prod_intrinsics": manifest_dir / "intrinsics_prod.npy",
    "prod_extrinsics": manifest_dir / "extrinsics_w2c_prod.npy",
}
for key, path in required_files.items():
    assert path.exists(), {key: str(path)}

proof_df = pd.read_csv(required_files["proof_manifest"])
prod_df = pd.read_csv(required_files["prod_manifest"])
assert not proof_df.empty, "proof manifest empty"
assert not prod_df.empty, "prod manifest empty"

required_columns = {
    "image_path",
    "image_file_name",
    "canonical_orientation_policy",
    "intrinsics_case",
}
assert required_columns.issubset(proof_df.columns), {
    "missing_in_proof": sorted(required_columns - set(proof_df.columns))
}
assert required_columns.issubset(prod_df.columns), {
    "missing_in_prod": sorted(required_columns - set(prod_df.columns))
}

proof_images = proof_df["image_path"].tolist()
prod_images = prod_df["image_path"].tolist()
assert len(proof_images) >= 2, {"proof_image_count": len(proof_images)}
assert len(prod_images) >= 2, {"prod_image_count": len(prod_images)}

for label, image_paths in [("proof", proof_images), ("prod", prod_images)]:
    missing = [p for p in image_paths if not Path(p).exists()]
    assert not missing, {f"{label}_missing_images_head": missing[:10], f"{label}_missing_count": len(missing)}

proof_intrinsics = np.load(required_files["proof_intrinsics"])
proof_extrinsics = np.load(required_files["proof_extrinsics"])
prod_intrinsics = np.load(required_files["prod_intrinsics"])
prod_extrinsics = np.load(required_files["prod_extrinsics"])

assert proof_intrinsics.shape == (len(proof_df), 3, 3), {
    "proof_intrinsics_shape": tuple(proof_intrinsics.shape),
    "proof_count": len(proof_df),
}
assert proof_extrinsics.shape[0] == len(proof_df), {
    "proof_extrinsics_shape": tuple(proof_extrinsics.shape),
    "proof_count": len(proof_df),
}
assert prod_intrinsics.shape == (len(prod_df), 3, 3), {
    "prod_intrinsics_shape": tuple(prod_intrinsics.shape),
    "prod_count": len(prod_df),
}
assert prod_extrinsics.shape[0] == len(prod_df), {
    "prod_extrinsics_shape": tuple(prod_extrinsics.shape),
    "prod_count": len(prod_df),
}

preflight = {
    "ctx_path": str(ctx_path),
    "repo_root": str(repo_root),
    "manifest_dir": str(manifest_dir),
    "proof_metric_dir": str(proof_metric_dir),
    "prod_metric_dir": str(prod_metric_dir),
    "world_dir": str(world_dir),
    "proof_image_count": len(proof_images),
    "prod_image_count": len(prod_images),
    "proof_intrinsics_shape": list(proof_intrinsics.shape),
    "proof_extrinsics_shape": list(proof_extrinsics.shape),
    "prod_intrinsics_shape": list(prod_intrinsics.shape),
    "prod_extrinsics_shape": list(prod_extrinsics.shape),
}
(manifest_dir / "metriclarge_block2_preflight.json").write_text(json.dumps(preflight, indent=2, ensure_ascii=False), encoding="utf-8")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = DepthAnything3.from_pretrained("depth-anything/DA3METRIC-LARGE").to(device=device)
proof_prediction = model.inference(
    image=proof_images,
    infer_gs=False,
    process_res=504,
    export_dir=str(proof_metric_dir),
    export_format="mini_npz-depth_vis",
)
prod_prediction = model.inference(
    image=prod_images,
    infer_gs=False,
    process_res=504,
    export_dir=str(prod_metric_dir),
    export_format="mini_npz-depth_vis",
)

depths = np.asarray(prod_prediction.depth)
assert depths is not None and len(depths) == len(prod_df), {
    "depth_count": None if depths is None else len(depths),
    "prod_selected_count": len(prod_df),
}
assert np.isfinite(prod_intrinsics).all(), "prod intrinsics has non-finite value"
assert np.isfinite(prod_extrinsics).all(), "prod extrinsics has non-finite value"

all_points = []
per_frame = []
skipped_frames = []
stride = 24
for idx, row in enumerate(prod_df.itertuples(index=False)):
    depth = np.asarray(depths[idx]).astype(np.float32)
    K = prod_intrinsics[idx]
    w2c = prod_extrinsics[idx]
    c2w = np.linalg.inv(w2c)
    h, w = depth.shape
    grid_y, grid_x = np.mgrid[0:h:stride, 0:w:stride]
    z = depth[grid_y, grid_x]
    valid = np.isfinite(z) & (z > 0.0)
    if not np.any(valid):
        skipped_frames.append({"image_file_name": row.image_file_name, "reason": "no_valid_depth"})
        continue
    px = grid_x[valid].astype(np.float32)
    py = grid_y[valid].astype(np.float32)
    zz = z[valid].astype(np.float32)
    x = (px - K[0, 2]) * zz / K[0, 0]
    y = (py - K[1, 2]) * zz / K[1, 1]
    cam = np.stack([x, y, zz], axis=-1)
    cam_h = np.concatenate([cam, np.ones((len(cam), 1), dtype=np.float32)], axis=1)
    world = (c2w @ cam_h.T).T[:, :3]
    all_points.append(world)
    per_frame.append({"image_file_name": row.image_file_name, "point_count": int(len(world))})

assert all_points, "no world points generated"
merged = np.concatenate(all_points, axis=0).astype(np.float32)
np.save(world_dir / "world_points_multiframe.npy", merged)

with (world_dir / "world_points_multiframe.ply").open("w", encoding="utf-8") as f:
    f.write("ply\nformat ascii 1.0\n")
    f.write(f"element vertex {len(merged)}\n")
    f.write("property float x\nproperty float y\nproperty float z\n")
    f.write("end_header\n")
    for p in merged:
        f.write(f"{p[0]} {p[1]} {p[2]}\n")

sample = merged[::4] if len(merged) > 4000 else merged
mins = sample.min(axis=0)
maxs = sample.max(axis=0)
norm = (sample - mins) / np.maximum(maxs - mins, 1e-6)
preview = np.zeros((800, 800, 3), dtype=np.uint8)
px = np.clip((norm[:, 0] * 799).astype(int), 0, 799)
py = np.clip((norm[:, 1] * 799).astype(int), 0, 799)
preview[799 - py, px] = 255
Image.fromarray(preview).save(world_dir / "world_points_multiframe_preview.png")

proof_summary = {
    "route": "MetricLarge-proof",
    "image_count": len(proof_images),
    "proof_metric_dir": str(proof_metric_dir),
    "prediction_type": str(type(proof_prediction).__name__),
    "da3_camera_input_mode": "image_only",
    "canonical_orientation_policy": str(proof_df["canonical_orientation_policy"].iloc[0]),
    "intrinsics_case_counts": proof_df["intrinsics_case"].value_counts().to_dict(),
}
prod_summary = {
    "route": "MetricLarge-production",
    "image_count": len(prod_images),
    "prod_metric_dir": str(prod_metric_dir),
    "prediction_type": str(type(prod_prediction).__name__),
    "da3_camera_input_mode": "image_only",
    "canonical_orientation_policy": str(prod_df["canonical_orientation_policy"].iloc[0]),
    "intrinsics_case_counts": prod_df["intrinsics_case"].value_counts().to_dict(),
}
world_summary = {
    "route": "MetricLarge-production-world",
    "processed_frames": len(per_frame),
    "skipped_frames": skipped_frames,
    "total_points": int(len(merged)),
    "stride": stride,
    "depth_source": "prod_prediction.depth",
    "world_projection_input_mode": "frame_record_intrinsics_and_pose",
    "canonical_orientation_policy": str(prod_df["canonical_orientation_policy"].iloc[0]),
    "npy_path": str(world_dir / "world_points_multiframe.npy"),
    "ply_path": str(world_dir / "world_points_multiframe.ply"),
}
(proof_metric_dir / "export_summary.json").write_text(json.dumps(proof_summary, indent=2, ensure_ascii=False), encoding="utf-8")
(prod_metric_dir / "export_summary.json").write_text(json.dumps(prod_summary, indent=2, ensure_ascii=False), encoding="utf-8")
(world_dir / "export_summary.json").write_text(json.dumps(world_summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({
    "preflight_path": str(manifest_dir / "metriclarge_block2_preflight.json"),
    "proof_image_count": proof_summary["image_count"],
    "prod_image_count": prod_summary["image_count"],
    "processed_frames": world_summary["processed_frames"],
    "total_points": world_summary["total_points"],
    "world_dir": str(world_dir),
}, indent=2, ensure_ascii=False))
```

### #8 Global camera matrix + batch plan

```python
#8
from pathlib import Path
import json
import math

import numpy as np
import pandas as pd

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
manifest_dir = Path(ctx["manifest_dir"])
probe_root = Path(ctx["probe_root"])

pipeline_root = probe_root / "continuous_gs_v06_chunk18_overlap6_adopt12"
global_pose_dir = pipeline_root / "global_pose_bootstrap"
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
merged_dir = pipeline_root / "merged"

for p in [pipeline_root, global_pose_dir, chunk_manifest_dir, chunk_runs_dir, merged_dir]:
    p.mkdir(parents=True, exist_ok=True)

MODEL_ID = "depth-anything/DA3NESTED-GIANT-LARGE-1.1"
BUNDLE_MODEL_SLUG = "".join(ch.lower() for ch in MODEL_ID.split("/")[-1] if ch.isalnum()).replace("da3nested", "")
PROCESS_RES = 504
CHUNK_SIZE = 18
STEP = 12
ADOPT_SIZE = 12
CHUNKS_PER_BATCH = 3

config = {
    "MODEL_ID": MODEL_ID,
    "BUNDLE_MODEL_SLUG": BUNDLE_MODEL_SLUG,
    "PROCESS_RES": PROCESS_RES,
    "CHUNK_SIZE": CHUNK_SIZE,
    "STEP": STEP,
    "ADOPT_SIZE": ADOPT_SIZE,
    "CHUNKS_PER_BATCH": CHUNKS_PER_BATCH,
    "GLOBAL_CAMERA_SOURCE": "extrinsics_w2c_prod.npy",
}
(pipeline_root / "pipeline_config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

prod_df = pd.read_csv(manifest_dir / "da3_input_manifest_prod.csv").reset_index(drop=True)
assert len(prod_df) >= 2, {"prod_frame_count": len(prod_df)}
prod_extrinsics_path = manifest_dir / "extrinsics_w2c_prod.npy"
assert prod_extrinsics_path.exists(), prod_extrinsics_path
prod_extrinsics = np.load(prod_extrinsics_path).astype(np.float32)
assert prod_extrinsics.shape[0] == len(prod_df), {
    "prod_extrinsics_shape": tuple(prod_extrinsics.shape),
    "prod_frame_count": len(prod_df),
}

def to_4x4(ext):
    ext = np.asarray(ext).astype(np.float32)
    if ext.shape == (4, 4):
        return ext
    if ext.shape == (3, 4):
        M = np.eye(4, dtype=np.float32)
        M[:3, :] = ext
        return M
    raise ValueError(f"unexpected extrinsic shape: {ext.shape}")

chunks = []
start_pos = 0
chunk_id = 0
while start_pos < len(prod_df):
    end_pos = min(start_pos + CHUNK_SIZE, len(prod_df))
    chunk_df = prod_df.iloc[start_pos:end_pos].copy().reset_index(drop=True)
    if len(chunk_df) < 2:
        break

    chunk_name = f"chunk_{chunk_id:04d}_{start_pos:05d}_{end_pos-1:05d}"
    chunk_df["chunk_local_index"] = range(len(chunk_df))
    adopt_local_start = max(0, len(chunk_df) - min(ADOPT_SIZE, len(chunk_df)))
    adopt_local_end = len(chunk_df) - 1
    chunk_df["is_adopted_region"] = chunk_df["chunk_local_index"] >= adopt_local_start

    chunk_csv = chunk_manifest_dir / f"{chunk_name}.csv"
    chunk_df.to_csv(chunk_csv, index=False, encoding="utf-8")

    chunks.append({
        "chunk_id": int(chunk_id),
        "chunk_name": chunk_name,
        "global_start": int(start_pos),
        "global_end": int(end_pos - 1),
        "frame_count": int(len(chunk_df)),
        "adopt_local_start": int(adopt_local_start),
        "adopt_local_end": int(adopt_local_end),
        "chunk_csv": str(chunk_csv),
    })

    if end_pos == len(prod_df):
        break
    start_pos += STEP
    chunk_id += 1

all_chunks_df = pd.DataFrame(chunks)
assert len(all_chunks_df) >= 1, "no chunks generated"
all_chunks_df.to_csv(chunk_manifest_dir / "chunk_index_all.csv", index=False, encoding="utf-8")
all_chunks_df.to_csv(chunk_manifest_dir / "chunk_index_target.csv", index=False, encoding="utf-8")

batch_rows = []
batch_count = math.ceil(len(all_chunks_df) / CHUNKS_PER_BATCH)
for batch_index in range(batch_count):
    s = batch_index * CHUNKS_PER_BATCH
    e = min(s + CHUNKS_PER_BATCH, len(all_chunks_df))
    batch_rows.append({
        "batch_index": batch_index,
        "chunk_from": s,
        "chunk_to": e - 1,
        "chunk_count": e - s,
        "chunk_names": "|".join(all_chunks_df.iloc[s:e]["chunk_name"].tolist()),
    })
batch_plan_df = pd.DataFrame(batch_rows)
batch_plan_df.to_csv(chunk_manifest_dir / "batch_plan.csv", index=False, encoding="utf-8")

bootstrap_df = prod_df.copy()
bootstrap_df.to_csv(global_pose_dir / "bootstrap_input_frames.csv", index=False, encoding="utf-8")

rows = []
pose_rows = []
for i, row in enumerate(bootstrap_df.itertuples(index=False)):
    w2c = to_4x4(prod_extrinsics[i])
    c2w = np.linalg.inv(w2c)
    center = c2w[:3, 3]
    rows.append({
        "bootstrap_index": i,
        "record_index": int(row.record_index),
        "image_file_name": row.image_file_name,
        "image_path": row.image_path,
        "cx_world": float(center[0]),
        "cy_world": float(center[1]),
        "cz_world": float(center[2]),
    })
    pose_rows.append({
        "bootstrap_index": i,
        "record_index": int(row.record_index),
        "image_file_name": row.image_file_name,
        "m00": float(c2w[0, 0]), "m01": float(c2w[0, 1]), "m02": float(c2w[0, 2]), "m03": float(c2w[0, 3]),
        "m10": float(c2w[1, 0]), "m11": float(c2w[1, 1]), "m12": float(c2w[1, 2]), "m13": float(c2w[1, 3]),
        "m20": float(c2w[2, 0]), "m21": float(c2w[2, 1]), "m22": float(c2w[2, 2]), "m23": float(c2w[2, 3]),
        "m30": float(c2w[3, 0]), "m31": float(c2w[3, 1]), "m32": float(c2w[3, 2]), "m33": float(c2w[3, 3]),
    })

camera_centers_df = pd.DataFrame(rows)
camera_centers_df.to_csv(global_pose_dir / "camera_center_matrix.csv", index=False, encoding="utf-8")

camera_matrix_df = pd.DataFrame(pose_rows)
camera_matrix_df.to_csv(global_pose_dir / "camera_matrix_full.csv", index=False, encoding="utf-8")

summary = {
    "route": "continuous-gs-v06-chunk18-overlap6-adopt12-global-camera-matrix",
    "global_camera_source": "extrinsics_w2c_prod.npy",
    "bootstrap_frame_count": int(len(bootstrap_df)),
    "chunk_count": int(len(all_chunks_df)),
    "batch_count": int(batch_count),
    "global_pose_dir": str(global_pose_dir),
    "bundle_model_slug": BUNDLE_MODEL_SLUG,
    "prod_extrinsics_path": str(prod_extrinsics_path),
    "chunk_index_all_path": str(chunk_manifest_dir / "chunk_index_all.csv"),
    "batch_plan_path": str(chunk_manifest_dir / "batch_plan.csv"),
}
(global_pose_dir / "export_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
print("\n# batch_plan")
print(batch_plan_df.to_string(index=False))
```

### #9 chunk helper for 18frame / overlap6 / adopt12

- この helper は `Block 3` の `camera_matrix_full.csv` と各 chunk の `pred_extrinsics.npy` を合わせて pose-aware alignment を解く。
- chunk merge の keep 判定は `PCA 1軸帯` ではなく `owner_record_index` ベースで行う。
- 各 vertex は global frame center 近傍 `top-k` に対し `distance + direction + blur_penalty + index_penalty` で owner を決め、owner が当該 chunk の `is_adopted_region=True` record に属する時だけ keep する。
- 生成物は `vertex_assignment_summary.csv`、`owner_record_histogram.csv`、`chunk_assignment_summary.csv`、`merge_warning_summary.csv`、`chunk_transform_quality.csv` として `pipeline_root` 配下へ保存され、`Block 6` bundle に自動同梱される。

```python
#9
from pathlib import Path
import gc
import json
import sys
import shutil

import numpy as np
import pandas as pd
import torch
import trimesh
from plyfile import PlyData, PlyElement
from scipy.spatial import cKDTree

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
probe_root = Path(ctx["probe_root"])
manifest_dir = Path(ctx["manifest_dir"])

pipeline_root = probe_root / "continuous_gs_v06_chunk18_overlap6_adopt12"
global_pose_dir = pipeline_root / "global_pose_bootstrap"
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
merged_dir = pipeline_root / "merged"

config = json.loads((pipeline_root / "pipeline_config.json").read_text(encoding="utf-8"))
MODEL_ID = config["MODEL_ID"]
PROCESS_RES = config["PROCESS_RES"]
CHUNKS_PER_BATCH = config["CHUNKS_PER_BATCH"]

target_chunks_df = pd.read_csv(chunk_manifest_dir / "chunk_index_target.csv")
batch_plan_df = pd.read_csv(chunk_manifest_dir / "batch_plan.csv")
global_centers_df = pd.read_csv(global_pose_dir / "camera_center_matrix.csv")
global_camera_matrix_df = pd.read_csv(global_pose_dir / "camera_matrix_full.csv")
prod_manifest_df = pd.read_csv(manifest_dir / "da3_input_manifest_prod.csv")

OWNER_TOPK = 6
OWNER_W_DIST = 1.0
OWNER_W_DIR = 0.35
OWNER_W_BLUR = 0.25
OWNER_W_INDEX = 0.02
OWNER_RECORD_MARGIN = 6
TRANSFORM_CENTER_RMSE_WARN = 0.25
TRANSFORM_ROT_DIR_WARN = 0.25
TRANSFORM_SCALE_MIN = 0.8
TRANSFORM_SCALE_MAX = 1.3
TRANSFORM_CENTER_RMSE_MAX = 0.05
TRANSFORM_ROT_DIR_MAX = 0.05

LOCAL_CAMERA_BASIS = np.eye(4, dtype=np.float32)
LOCAL_CAMERA_BASIS[:3, :3] = np.array([
    [0.0, 1.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.0, 0.0, -1.0],
], dtype=np.float32)

print("# batch_plan")
print(batch_plan_df.to_string(index=False))

def to_4x4(ext):
    ext = np.asarray(ext).astype(np.float32)
    if ext.shape == (4, 4):
        return ext
    if ext.shape == (3, 4):
        M = np.eye(4, dtype=np.float32)
        M[:3, :] = ext
        return M
    raise ValueError(f"unexpected extrinsic shape: {ext.shape}")

def camera_centers_from_extrinsics(extrinsics):
    centers = []
    for ext in extrinsics:
        w2c = to_4x4(ext)
        c2w = np.linalg.inv(w2c)
        centers.append(c2w[:3, 3])
    return np.stack(centers, axis=0)

def c2w_rows_to_map(df: pd.DataFrame):
    out = {}
    cols = [f"m{i}{j}" for i in range(4) for j in range(4)]
    for row in df.itertuples(index=False):
        M = np.array([getattr(row, c) for c in cols], dtype=np.float32).reshape(4, 4)
        out[int(row.record_index)] = M
    return out

def optical_axis_from_c2w(c2w: np.ndarray):
    axis = np.asarray(c2w[:3, 2], dtype=np.float32)
    norm = float(np.linalg.norm(axis))
    return axis / max(norm, 1e-12)

def c2w_list_from_extrinsics(extrinsics):
    mats = []
    for ext in extrinsics:
        c2w = np.linalg.inv(to_4x4(ext)).astype(np.float32)
        mats.append((c2w @ LOCAL_CAMERA_BASIS).astype(np.float32))
    return mats

def estimate_pose_aware_similarity(local_c2w_list, global_c2w_list, estimate_scale=True):
    assert len(local_c2w_list) == len(global_c2w_list) >= 2, {"local_len": len(local_c2w_list), "global_len": len(global_c2w_list)}

    src_dirs = []
    dst_dirs = []
    src_centers = []
    dst_centers = []
    for local_c2w, global_c2w in zip(local_c2w_list, global_c2w_list):
        src_dirs.extend([local_c2w[:3, 0], local_c2w[:3, 1], local_c2w[:3, 2]])
        dst_dirs.extend([global_c2w[:3, 0], global_c2w[:3, 1], global_c2w[:3, 2]])
        src_centers.append(local_c2w[:3, 3])
        dst_centers.append(global_c2w[:3, 3])

    src_dirs = np.asarray(src_dirs, dtype=np.float64)
    dst_dirs = np.asarray(dst_dirs, dtype=np.float64)
    src_centers = np.asarray(src_centers, dtype=np.float64)
    dst_centers = np.asarray(dst_centers, dtype=np.float64)

    H = dst_dirs.T @ src_dirs
    U, _, Vt = np.linalg.svd(H)
    S = np.eye(3, dtype=np.float64)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[-1, -1] = -1.0
    R = U @ S @ Vt

    src_mean = src_centers.mean(axis=0)
    dst_mean = dst_centers.mean(axis=0)
    src_c = src_centers - src_mean
    dst_c = dst_centers - dst_mean
    src_rot = (R @ src_c.T).T

    if estimate_scale:
        denom = float(np.sum(src_rot ** 2))
        numer = float(np.sum(dst_c * src_rot))
        scale = numer / max(denom, 1e-12)
    else:
        scale = 1.0

    t = dst_mean - scale * (R @ src_mean)
    pred = (scale * (R @ src_centers.T)).T + t
    center_rmse = float(np.sqrt(np.mean(np.sum((pred - dst_centers) ** 2, axis=1))))
    rot_residual = float(np.mean(np.linalg.norm((R @ src_dirs.T).T - dst_dirs, axis=1)))

    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = scale * R
    T[:3, 3] = t
    diag = {
        "scale": float(scale),
        "rotation_det": float(np.linalg.det(R)),
        "center_rmse": center_rmse,
        "rotation_dir_residual": rot_residual,
        "positive_similarity_ok": bool(scale > 0.0),
        "scale_in_range_ok": bool(TRANSFORM_SCALE_MIN <= scale <= TRANSFORM_SCALE_MAX),
        "center_rmse_ok": bool(center_rmse <= TRANSFORM_CENTER_RMSE_MAX),
        "rotation_dir_ok": bool(rot_residual <= TRANSFORM_ROT_DIR_MAX),
    }
    diag["hard_fail"] = bool(
        (scale <= 0.0)
        or (scale < TRANSFORM_SCALE_MIN)
        or (scale > TRANSFORM_SCALE_MAX)
        or (center_rmse > TRANSFORM_CENTER_RMSE_MAX)
        or (rot_residual > TRANSFORM_ROT_DIR_MAX)
    )
    return T.astype(np.float32), diag

def load_scene_any(path: Path):
    loaded = trimesh.load(str(path), force="scene")
    if isinstance(loaded, trimesh.Scene):
        return loaded
    scene = trimesh.Scene()
    if hasattr(loaded, "geometry"):
        for name, geom in loaded.geometry.items():
            scene.add_geometry(geom, node_name=name)
    else:
        scene.add_geometry(loaded)
    return scene

global_camera_map = c2w_rows_to_map(global_camera_matrix_df)
global_frame_meta_df = global_centers_df.merge(
    prod_manifest_df[["record_index", "qc_blur_ok", "blur_score"]],
    on="record_index",
    how="left",
)
global_frame_meta_df["opt_x"] = global_frame_meta_df["record_index"].map(lambda x: float(optical_axis_from_c2w(global_camera_map[int(x)])[0]))
global_frame_meta_df["opt_y"] = global_frame_meta_df["record_index"].map(lambda x: float(optical_axis_from_c2w(global_camera_map[int(x)])[1]))
global_frame_meta_df["opt_z"] = global_frame_meta_df["record_index"].map(lambda x: float(optical_axis_from_c2w(global_camera_map[int(x)])[2]))
global_frame_meta_df["qc_blur_ok"] = global_frame_meta_df["qc_blur_ok"].fillna(False).astype(bool)
global_frame_meta_df["blur_score"] = global_frame_meta_df["blur_score"].fillna(0.0)
global_frame_meta_df = global_frame_meta_df.sort_values("record_index").reset_index(drop=True)
global_center_tree = cKDTree(global_frame_meta_df[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32))

def assign_vertex_owners(xyz_w: np.ndarray, chunk_df: pd.DataFrame):
    chunk_record_df = global_frame_meta_df.loc[
        global_frame_meta_df["record_index"].isin(chunk_df["record_index"].astype(int).tolist())
    ].copy()
    record_min = int(chunk_df["record_index"].min())
    record_max = int(chunk_df["record_index"].max())
    candidate_mode = "chunk_only"
    candidate_df = chunk_record_df
    if len(candidate_df) < 2:
        candidate_mode = "chunk_with_margin"
        candidate_df = global_frame_meta_df.loc[
            global_frame_meta_df["record_index"].between(record_min - OWNER_RECORD_MARGIN, record_max + OWNER_RECORD_MARGIN)
        ].copy()
    if len(candidate_df) < 2:
        candidate_mode = "global_fallback"
        candidate_df = global_frame_meta_df.copy()
    candidate_tree = cKDTree(candidate_df[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32))

    k = min(OWNER_TOPK, len(candidate_df))
    dists, idxs = candidate_tree.query(xyz_w, k=k)
    if k == 1:
        dists = dists[:, None]
        idxs = idxs[:, None]

    candidate_meta = candidate_df.iloc[idxs.reshape(-1)].reset_index(drop=True)
    candidate_centers = candidate_meta[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32).reshape(len(xyz_w), k, 3)
    candidate_axes = candidate_meta[["opt_x", "opt_y", "opt_z"]].to_numpy(dtype=np.float32).reshape(len(xyz_w), k, 3)
    candidate_blur_ok = candidate_meta["qc_blur_ok"].to_numpy(dtype=bool).reshape(len(xyz_w), k)
    candidate_records = candidate_meta["record_index"].to_numpy(dtype=np.int64).reshape(len(xyz_w), k)

    view_vec = xyz_w[:, None, :] - candidate_centers
    view_norm = np.linalg.norm(view_vec, axis=2, keepdims=True)
    view_dir = view_vec / np.maximum(view_norm, 1e-12)
    dir_cos = np.sum(view_dir * candidate_axes, axis=2)
    dir_term = 1.0 - np.clip(dir_cos, -1.0, 1.0)
    blur_penalty = np.where(candidate_blur_ok, 0.0, 1.0)

    chunk_record_center = float(chunk_df["record_index"].median())
    chunk_record_span = float(max(chunk_df["record_index"].max() - chunk_df["record_index"].min(), 1))
    index_penalty = np.minimum(np.abs(candidate_records - chunk_record_center) / chunk_record_span, 1.0)

    score = (
        OWNER_W_DIST * np.asarray(dists, dtype=np.float32)
        + OWNER_W_DIR * dir_term.astype(np.float32)
        + OWNER_W_BLUR * blur_penalty.astype(np.float32)
        + OWNER_W_INDEX * index_penalty.astype(np.float32)
    )

    best_local = np.argmin(score, axis=1)
    row_idx = np.arange(len(xyz_w))
    owner_records = candidate_records[row_idx, best_local]
    owner_scores = score[row_idx, best_local]
    owner_dists = np.asarray(dists, dtype=np.float32)[row_idx, best_local]
    owner_dir_cos = dir_cos[row_idx, best_local]
    owner_blur_ok = candidate_blur_ok[row_idx, best_local]

    assignment_df = pd.DataFrame({
        "vertex_index": np.arange(len(xyz_w), dtype=np.int64),
        "owner_record_index": owner_records.astype(np.int64),
        "owner_chunk_name": chunk_df.attrs.get("chunk_name", ""),
        "owner_candidate_mode": candidate_mode,
        "owner_candidate_record_min": int(candidate_df["record_index"].min()),
        "owner_candidate_record_max": int(candidate_df["record_index"].max()),
        "owner_score": owner_scores.astype(np.float32),
        "owner_dist": owner_dists.astype(np.float32),
        "owner_dir_cos": owner_dir_cos.astype(np.float32),
        "owner_blur_ok": owner_blur_ok.astype(bool),
    })
    return assignment_df

def show_batch_plan(run_batch_index: int):
    assert len(batch_plan_df) >= 1, "batch_plan.csv is empty"
    if run_batch_index < 0 or run_batch_index >= len(batch_plan_df):
        print(json.dumps({
            "status": "skip",
            "reason": "batch_out_of_range",
            "run_batch_index": int(run_batch_index),
            "available_batch_count": int(len(batch_plan_df)),
        }, indent=2, ensure_ascii=False))
        return

    row = batch_plan_df.iloc[int(run_batch_index)]
    chunk_names = str(row["chunk_names"]).split("|") if str(row["chunk_names"]).strip() else []
    print("# selected_batch")
    print(json.dumps({
        "run_batch_index": int(run_batch_index),
        "chunk_from": int(row["chunk_from"]),
        "chunk_to": int(row["chunk_to"]),
        "chunk_count": int(row["chunk_count"]),
        "chunk_names": chunk_names,
    }, indent=2, ensure_ascii=False))

def process_batch(run_batch_index: int):
    batch_start = run_batch_index * CHUNKS_PER_BATCH
    batch_end = min(batch_start + CHUNKS_PER_BATCH, len(target_chunks_df))

    show_batch_plan(run_batch_index)

    if batch_start >= len(target_chunks_df):
        print(json.dumps({
            "status": "skip",
            "reason": "batch_out_of_range",
            "run_batch_index": int(run_batch_index),
            "available_batch_count": int((len(target_chunks_df) + CHUNKS_PER_BATCH - 1) // CHUNKS_PER_BATCH),
        }, indent=2, ensure_ascii=False))
        return

    batch_chunks_df = target_chunks_df.iloc[batch_start:batch_end].copy().reset_index(drop=True)
    batch_name = f"batch_{run_batch_index:03d}"
    batch_dir = chunk_runs_dir / batch_name
    batch_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DepthAnything3.from_pretrained(MODEL_ID).to(device=device)

    run_rows = []
    transform_rows = []
    keep_rows = []
    warning_rows = []
    batch_records = []
    batch_scene = trimesh.Scene()

    for row in batch_chunks_df.itertuples(index=False):
        chunk_df = pd.read_csv(row.chunk_csv)
        chunk_df.attrs["chunk_name"] = row.chunk_name
        images = chunk_df["image_path"].tolist()

        out_dir = chunk_runs_dir / row.chunk_name
        done_flag = out_dir / "_SUCCESS.json"

        if done_flag.exists():
            pred_extrinsics = np.load(out_dir / "pred_extrinsics.npy")
            chunk_df = pd.read_csv(out_dir / "chunk_input_frames.csv")
        else:
            if out_dir.exists():
                shutil.rmtree(out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            prediction = model.inference(
                image=images,
                infer_gs=True,
                process_res=PROCESS_RES,
                export_dir=str(out_dir),
                export_format="npz-glb-gs_ply-gs_video",
            )

            pred_intrinsics = getattr(prediction, "intrinsics", None)
            pred_extrinsics = getattr(prediction, "extrinsics", None)

            assert pred_intrinsics is not None, f"intrinsics missing: {row.chunk_name}"
            assert pred_extrinsics is not None, f"extrinsics missing: {row.chunk_name}"

            np.save(out_dir / "pred_intrinsics.npy", np.asarray(pred_intrinsics).astype(np.float32))
            np.save(out_dir / "pred_extrinsics.npy", np.asarray(pred_extrinsics).astype(np.float32))
            chunk_df.to_csv(out_dir / "chunk_input_frames.csv", index=False, encoding="utf-8")
            done_flag.write_text(json.dumps({"chunk_name": row.chunk_name}, indent=2, ensure_ascii=False), encoding="utf-8")

        pred_extrinsics = np.asarray(pred_extrinsics).astype(np.float32)
        local_centers = camera_centers_from_extrinsics(pred_extrinsics)
        local_c2w_list = c2w_list_from_extrinsics(pred_extrinsics)

        merged = chunk_df.merge(
            global_centers_df[["record_index", "cx_world", "cy_world", "cz_world"]],
            on="record_index",
            how="left",
        )
        assert len(merged) == len(chunk_df), {"chunk_name": row.chunk_name, "merged_len": len(merged), "chunk_len": len(chunk_df)}
        global_c2w_list = [global_camera_map[int(record_index)] for record_index in merged["record_index"].tolist()]

        src = local_centers
        dst = merged[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32)
        T_c_to_w0, align_diag = estimate_pose_aware_similarity(local_c2w_list, global_c2w_list, estimate_scale=True)

        T_path = chunk_manifest_dir / f"{row.chunk_name}_to_w0.npy"
        np.save(T_path, T_c_to_w0.astype(np.float32))

        transform_rows.append({
            "chunk_name": row.chunk_name,
            "frame_count": int(len(chunk_df)),
            "transform_path": str(T_path),
            "local_camera_basis": "perm_yxz_sign_ppn",
            "scale": float(align_diag["scale"]),
            "rotation_det": float(align_diag["rotation_det"]),
            "center_rmse": float(align_diag["center_rmse"]),
            "rotation_dir_residual": float(align_diag["rotation_dir_residual"]),
            "positive_similarity_ok": bool(align_diag["positive_similarity_ok"]),
            "scale_in_range_ok": bool(align_diag["scale_in_range_ok"]),
            "center_rmse_ok": bool(align_diag["center_rmse_ok"]),
            "rotation_dir_ok": bool(align_diag["rotation_dir_ok"]),
            "hard_fail": bool(align_diag["hard_fail"]),
        })
        assert not align_diag["hard_fail"], {
            "chunk_name": row.chunk_name,
            "reason": "invalid_pose_similarity",
            "align_diag": align_diag,
        }

        ply_path = out_dir / "gs_ply" / "0000.ply"
        glb_path = out_dir / "scene.glb"

        run_rows.append({
            "batch_name": batch_name,
            "chunk_name": row.chunk_name,
            "frame_count": int(len(chunk_df)),
            "ply_exists": bool(ply_path.exists()),
            "glb_exists": bool(glb_path.exists()),
            "out_dir": str(out_dir),
        })

        if ply_path.exists():
            T = np.load(T_path).astype(np.float32)
            A = T[:3, :3]
            t = T[:3, 3]
            adopted_record_set = set(chunk_df.loc[chunk_df["is_adopted_region"] == True, "record_index"].astype(int).tolist())

            ply = PlyData.read(str(ply_path))
            df = pd.DataFrame(ply["vertex"].data)
            xyz = df[["x", "y", "z"]].to_numpy(dtype=np.float32)

            xyz_w = (A @ xyz.T).T + t
            assignment_df = assign_vertex_owners(xyz_w, chunk_df)
            keep = assignment_df["owner_record_index"].isin(adopted_record_set).to_numpy(dtype=bool)
            assignment_df["kept"] = keep
            assignment_df.to_csv(out_dir / "vertex_assignment_summary.csv", index=False, encoding="utf-8")

            owner_hist_df = assignment_df.groupby("owner_record_index", as_index=False).size().rename(columns={"size": "owner_vertex_count"})
            owner_hist_df.to_csv(out_dir / "owner_record_histogram.csv", index=False, encoding="utf-8")

            chunk_assignment_summary = assignment_df.groupby(["owner_record_index", "owner_blur_ok"], as_index=False).agg(
                owner_vertex_count=("vertex_index", "count"),
                owner_score_mean=("owner_score", "mean"),
                owner_dist_mean=("owner_dist", "mean"),
                owner_dir_cos_mean=("owner_dir_cos", "mean"),
            )
            chunk_assignment_summary.to_csv(out_dir / "chunk_assignment_summary.csv", index=False, encoding="utf-8")

            df["x"] = xyz_w[:, 0]
            df["y"] = xyz_w[:, 1]
            df["z"] = xyz_w[:, 2]
            df = df.loc[keep].copy()

            if len(df) > 0:
                batch_records.append(df.to_records(index=False))

            transform_warning = bool(
                align_diag["center_rmse"] > TRANSFORM_CENTER_RMSE_WARN
                or align_diag["rotation_dir_residual"] > TRANSFORM_ROT_DIR_WARN
            )
            keep_zero_chunk = int(len(df)) == 0
            warning_rows.append({
                "batch_name": batch_name,
                "chunk_name": row.chunk_name,
                "transform_warning": transform_warning,
                "keep_zero_chunk": keep_zero_chunk,
                "fallback_used": False,
            })
            keep_rows.append({
                "batch_name": batch_name,
                "chunk_name": row.chunk_name,
                "kept_vertices": int(len(df)),
                "owner_record_unique_count": int(assignment_df["owner_record_index"].nunique()),
                "owner_candidate_mode": str(assignment_df["owner_candidate_mode"].iloc[0]),
                "owner_record_min": int(assignment_df["owner_record_index"].min()),
                "owner_record_max": int(assignment_df["owner_record_index"].max()),
                "owner_blur_ok_ratio": float(assignment_df["owner_blur_ok"].mean()),
                "owner_score_mean": float(assignment_df["owner_score"].mean()),
            })
            assert not keep_zero_chunk, {"chunk_name": row.chunk_name, "reason": "keep_zero_chunk"}

        if glb_path.exists():
            scene = load_scene_any(glb_path)
            T = np.load(T_path).astype(np.float32)
            for gname, geom in scene.geometry.items():
                geom2 = geom.copy()
                if hasattr(geom2, "apply_transform"):
                    geom2.apply_transform(T)
                batch_scene.add_geometry(geom2, node_name=f"{row.chunk_name}_{gname}")

    run_df = pd.DataFrame(run_rows)
    run_df.to_csv(batch_dir / "chunk_run_summary.csv", index=False, encoding="utf-8")

    transform_df = pd.DataFrame(transform_rows)
    transform_df.to_csv(batch_dir / "chunk_global_transforms.csv", index=False, encoding="utf-8")

    keep_df = pd.DataFrame(keep_rows)
    keep_df.to_csv(batch_dir / "chunk_keep_summary.csv", index=False, encoding="utf-8")

    warning_df = pd.DataFrame(warning_rows)
    warning_df.to_csv(batch_dir / "merge_warning_summary.csv", index=False, encoding="utf-8")
    transform_df.to_csv(batch_dir / "chunk_transform_quality.csv", index=False, encoding="utf-8")

    batch_ply_path = batch_dir / f"{batch_name}_merged_gs.ply"
    if batch_records:
        batch_records_concat = np.concatenate(batch_records, axis=0)
        PlyData([PlyElement.describe(batch_records_concat, "vertex")], text=False).write(str(batch_ply_path))

    batch_glb_path = batch_dir / f"{batch_name}_merged_scene.glb"
    if len(batch_scene.geometry) > 0:
        batch_scene.export(str(batch_glb_path))

    batch_summary = {
        "status": "ok",
        "batch_name": batch_name,
        "run_batch_index": int(run_batch_index),
        "chunk_count": int(len(batch_chunks_df)),
        "chunk_names": batch_chunks_df["chunk_name"].tolist(),
        "batch_ply_path": str(batch_ply_path) if batch_ply_path.exists() else None,
        "batch_glb_path": str(batch_glb_path) if batch_glb_path.exists() else None,
    }
    (batch_dir / "batch_summary.json").write_text(json.dumps(batch_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print(json.dumps(batch_summary, indent=2, ensure_ascii=False))
```

### #10 batch run

- この block は 1 回で `3chunk` だけ処理する。
- 各 chunk は `18frame` を持ち、次 chunk と `6frame` 重なり、再構成責務は基本 `後半 12frame` である。
- `RUN_BATCH_INDEX = 0` は先頭 `3chunk`、`RUN_BATCH_INDEX = 1` は次の `3chunk` を意味する。
- `batch_plan.csv` を見ながら `0`, `1`, `2`, `3` ... と順に実行する。
- 全 batch を回し終わるまでは `Block 6` を実行しない。

```python
#10-1
RUN_BATCH_INDEX = 0
process_batch(RUN_BATCH_INDEX)
```

```python
#10-2
RUN_BATCH_INDEX = 1
process_batch(RUN_BATCH_INDEX)
```

```python
#10-3
RUN_BATCH_INDEX = 2
process_batch(RUN_BATCH_INDEX)
```

```python
#10-4
RUN_BATCH_INDEX = 3
process_batch(RUN_BATCH_INDEX)
```

### #10-5 Pre-merge pose gate

- `#11 merge` の前に、全 chunk を対象に camera-only の pose validation を必ず実行する。
- この cell は `pred_extrinsics.npy` を `w2c` とみなし、local camera basis を `perm_yxz_sign_ppn` へ固定したうえで、global `camera_matrix_full.csv` に対する positive similarity 制約を全 chunk で確認する。
- gate 条件は `scale > 0`、`0.8 <= scale <= 1.3`、`center_rmse <= 0.05`、`rotation_dir_residual <= 0.05` とする。
- 生成物は `merged` または `merged_add**` 配下の `premerge_pose_validation.csv` と `premerge_pose_validation.json`、および `final_outputs/diagnostics/` または `final_outputs_add**/diagnostics/` への copy とする。
- `hard_fail` が 1 件でもあれば、この cell 自体を fail させ、`#11 merge` へ進まない。

```python
#10-5
from pathlib import Path
import json
import numpy as np
import pandas as pd
import shutil

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
probe_root = Path(ctx["probe_root"])
final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])

pipeline_root = probe_root / "continuous_gs_v06_chunk18_overlap6_adopt12"
global_pose_dir = pipeline_root / "global_pose_bootstrap"
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
merged_dir = Path(ctx.get("merged_dir", str(pipeline_root / "merged")))
merged_dir.mkdir(parents=True, exist_ok=True)
final_outputs_diagnostics_dir.mkdir(parents=True, exist_ok=True)

TRANSFORM_SCALE_MIN = 0.8
TRANSFORM_SCALE_MAX = 1.3
TRANSFORM_CENTER_RMSE_MAX = 0.05
TRANSFORM_ROT_DIR_MAX = 0.05
LOCAL_CAMERA_BASIS = np.eye(4, dtype=np.float32)
LOCAL_CAMERA_BASIS[:3, :3] = np.array([
    [0.0, 1.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.0, 0.0, -1.0],
], dtype=np.float32)

def to_4x4(ext):
    ext = np.asarray(ext).astype(np.float32)
    if ext.shape == (4, 4):
        return ext
    if ext.shape == (3, 4):
        M = np.eye(4, dtype=np.float32)
        M[:3, :] = ext
        return M
    raise ValueError(f"unexpected extrinsic shape: {ext.shape}")

def c2w_rows_to_map(df: pd.DataFrame):
    out = {}
    cols = [f"m{i}{j}" for i in range(4) for j in range(4)]
    for row in df.itertuples(index=False):
        M = np.array([getattr(row, c) for c in cols], dtype=np.float32).reshape(4, 4)
        out[int(row.record_index)] = M
    return out

def c2w_list_from_extrinsics(extrinsics):
    mats = []
    for ext in extrinsics:
        c2w = np.linalg.inv(to_4x4(ext)).astype(np.float32)
        mats.append((c2w @ LOCAL_CAMERA_BASIS).astype(np.float32))
    return mats

def estimate_pose_aware_similarity(local_c2w_list, global_c2w_list, estimate_scale=True):
    assert len(local_c2w_list) == len(global_c2w_list) >= 2
    src_dirs, dst_dirs, src_centers, dst_centers = [], [], [], []
    for local_c2w, global_c2w in zip(local_c2w_list, global_c2w_list):
        src_dirs.extend([local_c2w[:3, 0], local_c2w[:3, 1], local_c2w[:3, 2]])
        dst_dirs.extend([global_c2w[:3, 0], global_c2w[:3, 1], global_c2w[:3, 2]])
        src_centers.append(local_c2w[:3, 3])
        dst_centers.append(global_c2w[:3, 3])
    src_dirs = np.asarray(src_dirs, dtype=np.float64)
    dst_dirs = np.asarray(dst_dirs, dtype=np.float64)
    src_centers = np.asarray(src_centers, dtype=np.float64)
    dst_centers = np.asarray(dst_centers, dtype=np.float64)
    H = dst_dirs.T @ src_dirs
    U, _, Vt = np.linalg.svd(H)
    S = np.eye(3, dtype=np.float64)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[-1, -1] = -1.0
    R = U @ S @ Vt
    src_mean = src_centers.mean(axis=0)
    dst_mean = dst_centers.mean(axis=0)
    src_c = src_centers - src_mean
    dst_c = dst_centers - dst_mean
    src_rot = (R @ src_c.T).T
    if estimate_scale:
        denom = float(np.sum(src_rot ** 2))
        numer = float(np.sum(dst_c * src_rot))
        scale = numer / max(denom, 1e-12)
    else:
        scale = 1.0
    t = dst_mean - scale * (R @ src_mean)
    pred = (scale * (R @ src_centers.T)).T + t
    center_rmse = float(np.sqrt(np.mean(np.sum((pred - dst_centers) ** 2, axis=1))))
    rot_residual = float(np.mean(np.linalg.norm((R @ src_dirs.T).T - dst_dirs, axis=1)))
    return {
        "scale": float(scale),
        "rotation_det": float(np.linalg.det(R)),
        "center_rmse": center_rmse,
        "rotation_dir_residual": rot_residual,
    }

global_camera_matrix_df = pd.read_csv(global_pose_dir / "camera_matrix_full.csv")
global_camera_map = c2w_rows_to_map(global_camera_matrix_df)
all_chunks_df = pd.read_csv(chunk_manifest_dir / "chunk_index_all.csv")

rows = []
for row in all_chunks_df.itertuples(index=False):
    chunk_dir = chunk_runs_dir / row.chunk_name
    pred_path = chunk_dir / "pred_extrinsics.npy"
    frames_path = chunk_dir / "chunk_input_frames.csv"
    assert pred_path.exists(), f"pred_extrinsics missing: {row.chunk_name}"
    assert frames_path.exists(), f"chunk_input_frames missing: {row.chunk_name}"
    pred_extrinsics = np.load(pred_path)
    chunk_frames_df = pd.read_csv(frames_path)
    local_c2w_list = c2w_list_from_extrinsics(pred_extrinsics)
    global_c2w_list = [global_camera_map[int(record_index)] for record_index in chunk_frames_df["record_index"].tolist()]
    diag = estimate_pose_aware_similarity(local_c2w_list, global_c2w_list, estimate_scale=True)
    scale = float(diag["scale"])
    center_rmse = float(diag["center_rmse"])
    rot = float(diag["rotation_dir_residual"])
    hard_fail = bool(
        (scale <= 0.0)
        or (scale < TRANSFORM_SCALE_MIN)
        or (scale > TRANSFORM_SCALE_MAX)
        or (center_rmse > TRANSFORM_CENTER_RMSE_MAX)
        or (rot > TRANSFORM_ROT_DIR_MAX)
    )
    rows.append({
        "chunk_name": row.chunk_name,
        "frame_count": int(len(chunk_frames_df)),
        "local_camera_basis": "perm_yxz_sign_ppn",
        "interpretation": "w2c",
        "scale": scale,
        "rotation_det": float(diag["rotation_det"]),
        "center_rmse": center_rmse,
        "rotation_dir_residual": rot,
        "positive_similarity_ok": bool(scale > 0.0),
        "scale_in_range_ok": bool(TRANSFORM_SCALE_MIN <= scale <= TRANSFORM_SCALE_MAX),
        "center_rmse_ok": bool(center_rmse <= TRANSFORM_CENTER_RMSE_MAX),
        "rotation_dir_ok": bool(rot <= TRANSFORM_ROT_DIR_MAX),
        "hard_fail": hard_fail,
    })

validation_df = pd.DataFrame(rows).sort_values("chunk_name").reset_index(drop=True)
validation_csv_path = merged_dir / "premerge_pose_validation.csv"
validation_json_path = merged_dir / "premerge_pose_validation.json"
validation_df.to_csv(validation_csv_path, index=False, encoding="utf-8")
hard_fail_df = validation_df[validation_df["hard_fail"]].copy()
summary = {
    "status": "ok" if hard_fail_df.empty else "fail",
    "route": "continuous-gs-v06-chunk18-overlap6-adopt12-premerge-pose-gate",
    "local_camera_basis": "perm_yxz_sign_ppn",
    "interpretation": "w2c",
    "thresholds": {
        "scale_min": TRANSFORM_SCALE_MIN,
        "scale_max": TRANSFORM_SCALE_MAX,
        "center_rmse_max": TRANSFORM_CENTER_RMSE_MAX,
        "rotation_dir_max": TRANSFORM_ROT_DIR_MAX,
    },
    "tested_chunk_count": int(len(validation_df)),
    "hard_fail_count": int(len(hard_fail_df)),
    "csv_path": str(validation_csv_path),
    "failed_chunks": hard_fail_df[["chunk_name", "scale", "center_rmse", "rotation_dir_residual"]].to_dict(orient="records"),
}
validation_json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
shutil.copy2(validation_csv_path, final_outputs_diagnostics_dir / "premerge_pose_validation.csv")
shutil.copy2(validation_json_path, final_outputs_diagnostics_dir / "premerge_pose_validation.json")
print(json.dumps(summary, indent=2, ensure_ascii=False))
assert hard_fail_df.empty, hard_fail_df[["chunk_name", "scale", "center_rmse", "rotation_dir_residual"]].to_dict(orient="records")
```

### #11 Final rebuild merge + bundle

- final merge でも `Block 4` と同じ owner_record 判定を使う。`PCA 1軸帯 keep` と terminal の `all keep fallback` は使わない。
- `keep_zero_chunk` は warning ではなく hard error とし、owner-based merge が崩れた chunk を見逃さない。
- `#11` の前に `#10-5 pre-merge pose gate` を必ず通し、`merged` または `merged_add**` 配下の `premerge_pose_validation.json` の `status == ok` を満たした時だけ merge を許可する。
- `MAKE_DRIVE_BUNDLE = True` の時も、Drive 上で新しい複製 directory は作らない。Drive 正本は最初から `probe_root` 配下だけに集約し、bundle summary にはその root を `drive_visible_dir` として残す。
- download 用 zip は `/content/...zip` にだけ作り、必要なら browser download を行う。したがって `vertex_assignment_summary.csv`、`chunk_assignment_summary.csv`、`owner_record_histogram.csv`、`merge_warning_summary.json`、`chunk_transform_quality.csv` は Drive 正本 `probe_root` と local zip の両方で見られる。
- `probe_root/final_outputs/` は `#6-1` の時点で先に作り、`#11` で確定出力と最低限の付随情報を必ずここへ保存する。download や local zip が失敗しても Drive 側の最終 tree は残る。
- `#11` は現状 1 cell でも、`#11-2 gs_ply merge` 相当の成果物を `probe_root/final_outputs/stage_11_2/` へ、`#11-3 glb merge` 相当の成果物を `probe_root/final_outputs/stage_11_3/` へ保存する。これにより runtime 切断後も Drive 側 artifact から途中再開できる。
- `#11-2` 相当では `merged_gs.ply`、`chunk_global_transforms.csv`、`chunk_keep_summary.csv`、`chunk_transform_quality.csv`、`owner_record_histogram.csv`、`chunk_assignment_summary.csv`、`merge_warning_summary.json` を Drive 側へ保存する。
- `#11-3` 相当では、上記に加えて `merged_scene.glb` と `merge_resume_state.json` を Drive 側へ保存し、後段はその resume state と stage artifact だけを読んで再開できる構成にする。
- cleanup 後も merge 根拠を再確認できるよう、`final_outputs/chunk_evidence/<chunk_name>/` に `vertex_assignment_summary.csv`、`chunk_input_frames.csv`、`pred_extrinsics.npy`、`pred_intrinsics.npy` を残す。
- cleanup は `#12 inventory` と `#13 apply` に分離する。`#12` は全 block を対象に「保持対象」と「削除候補」を一覧化し、`#13` はその一覧を読んで yes 入力時だけ削除する。

```python
#11
from pathlib import Path
import json
import shutil
import os

import numpy as np
import pandas as pd
import trimesh
from plyfile import PlyData, PlyElement
from scipy.spatial import cKDTree

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
probe_root = Path(ctx["probe_root"])
results_root = Path(ctx["results_root"])
modeling_session_id = ctx["modeling_session_id"]
manifest_dir = Path(ctx["manifest_dir"])
final_outputs_dir = Path(ctx["final_outputs_dir"])
final_outputs_merged_dir = Path(ctx["final_outputs_merged_dir"])
final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_manifests_dir = Path(ctx["final_outputs_manifests_dir"])
final_outputs_chunk_evidence_dir = Path(ctx["final_outputs_chunk_evidence_dir"])

pipeline_root = probe_root / "continuous_gs_v06_chunk18_overlap6_adopt12"
global_pose_dir = pipeline_root / "global_pose_bootstrap"
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
merged_dir = Path(ctx.get("merged_dir", str(pipeline_root / "merged")))
merged_dir.mkdir(parents=True, exist_ok=True)
stage_11_2_dir = final_outputs_dir / "stage_11_2"
stage_11_3_dir = final_outputs_dir / "stage_11_3"
for p in [final_outputs_dir, final_outputs_merged_dir, final_outputs_diagnostics_dir, final_outputs_manifests_dir, final_outputs_chunk_evidence_dir, stage_11_2_dir, stage_11_3_dir]:
    p.mkdir(parents=True, exist_ok=True)

config_path = pipeline_root / "pipeline_config.json"
if config_path.exists():
    config = json.loads(config_path.read_text(encoding="utf-8"))
else:
    config = {
        "MODEL_ID": "depth-anything/DA3NESTED-GIANT-LARGE-1.1",
        "BUNDLE_MODEL_SLUG": "giantlarge11",
        "PROCESS_RES": 504,
        "CHUNK_SIZE": 18,
        "STEP": 12,
        "ADOPT_SIZE": 12,
        "CHUNKS_PER_BATCH": 3,
        "GLOBAL_CAMERA_SOURCE": "extrinsics_w2c_prod.npy",
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
BUNDLE_MODEL_SLUG = config["BUNDLE_MODEL_SLUG"]
REQUIRE_ALL_CHUNKS = True
MAKE_DRIVE_BUNDLE = True
MAKE_LOCAL_BUNDLE_ZIP = True
DOWNLOAD_LOCAL_BUNDLE = True

chunk_index_all_path = chunk_manifest_dir / "chunk_index_all.csv"
if chunk_index_all_path.exists():
    all_chunks_df = pd.read_csv(chunk_index_all_path)
else:
    inferred_chunk_names = sorted({
        p.parent.name
        for p in chunk_runs_dir.glob("*/_SUCCESS.json")
    } | {
        p.parent.parent.name
        for p in chunk_runs_dir.glob("*/gs_ply/0000.ply")
    } | {
        p.parent.parent.name
        for p in chunk_runs_dir.glob("*/gs_video/0000_extend.mp4")
    })
    all_chunks_df = pd.DataFrame([
        {
            "chunk_id": i,
            "chunk_name": name,
            "global_start": None,
            "global_end": None,
            "frame_count": None,
            "adopt_local_start": None,
            "adopt_local_end": None,
            "chunk_csv": None,
        }
        for i, name in enumerate(inferred_chunk_names)
    ])
    chunk_manifest_dir.mkdir(parents=True, exist_ok=True)
    all_chunks_df.to_csv(chunk_index_all_path, index=False, encoding="utf-8")

completed_chunk_names = sorted({
    p.parent.name
    for p in chunk_runs_dir.glob("*/_SUCCESS.json")
})
ply_ready_chunk_names = sorted({
    p.parent.name
    for p in chunk_runs_dir.glob("*/gs_ply/0000.ply")
})
completed_chunks_df = all_chunks_df[all_chunks_df["chunk_name"].isin(completed_chunk_names)].copy()

batch_summaries = sorted(chunk_runs_dir.glob("batch_*/batch_summary.json"))
summary_rows = [json.loads(p.read_text(encoding="utf-8")) for p in batch_summaries]
(merged_dir / "all_batch_summary.json").write_text(json.dumps(summary_rows, indent=2, ensure_ascii=False), encoding="utf-8")
premerge_pose_validation_path = merged_dir / "premerge_pose_validation.json"

if not premerge_pose_validation_path.exists():
    merge_summary = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "status": "skipped",
        "reason": "premerge_pose_validation_required",
        "premerge_pose_validation_path": str(premerge_pose_validation_path),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary.json"),
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
    raise AssertionError("run #10-5 pre-merge pose gate before #11 merge")

premerge_pose_validation = json.loads(premerge_pose_validation_path.read_text(encoding="utf-8"))
if premerge_pose_validation.get("status") != "ok":
    merge_summary = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "status": "skipped",
        "reason": "premerge_pose_validation_failed",
        "premerge_pose_validation_path": str(premerge_pose_validation_path),
        "hard_fail_count": int(premerge_pose_validation.get("hard_fail_count", 0)),
        "failed_chunks": premerge_pose_validation.get("failed_chunks", []),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary.json"),
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
    raise AssertionError(premerge_pose_validation)

if REQUIRE_ALL_CHUNKS and len(completed_chunks_df) < len(all_chunks_df):
    merge_summary = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "status": "skipped",
        "reason": "waiting_for_all_chunks",
        "completed_chunk_count": int(len(completed_chunks_df)),
        "ply_ready_chunk_count": int(len(ply_ready_chunk_names)),
        "all_chunk_count": int(len(all_chunks_df)),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary.json"),
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
else:
    global_centers_df = pd.read_csv(global_pose_dir / "camera_center_matrix.csv")
    global_camera_matrix_df = pd.read_csv(global_pose_dir / "camera_matrix_full.csv")
    prod_manifest_df = pd.read_csv(manifest_dir / "da3_input_manifest_prod.csv")
    OWNER_TOPK = 6
    OWNER_W_DIST = 1.0
    OWNER_W_DIR = 0.35
    OWNER_W_BLUR = 0.25
    OWNER_W_INDEX = 0.02
    OWNER_RECORD_MARGIN = 6
    TRANSFORM_CENTER_RMSE_WARN = 0.25
    TRANSFORM_ROT_DIR_WARN = 0.25

    def load_scene_any(path: Path):
        loaded = trimesh.load(str(path), force="scene")
        if isinstance(loaded, trimesh.Scene):
            return loaded
        scene = trimesh.Scene()
        if hasattr(loaded, "geometry"):
            for name, geom in loaded.geometry.items():
                scene.add_geometry(geom, node_name=name)
        else:
            scene.add_geometry(loaded)
        return scene

    def to_4x4(ext):
        ext = np.asarray(ext).astype(np.float32)
        if ext.shape == (4, 4):
            return ext
        if ext.shape == (3, 4):
            M = np.eye(4, dtype=np.float32)
            M[:3, :] = ext
            return M
        raise ValueError(f"unexpected extrinsic shape: {ext.shape}")

    def c2w_rows_to_map(df: pd.DataFrame):
        out = {}
        cols = [f"m{i}{j}" for i in range(4) for j in range(4)]
        for row in df.itertuples(index=False):
            M = np.array([getattr(row, c) for c in cols], dtype=np.float32).reshape(4, 4)
            out[int(row.record_index)] = M
        return out

    def optical_axis_from_c2w(c2w: np.ndarray):
        axis = np.asarray(c2w[:3, 2], dtype=np.float32)
        norm = float(np.linalg.norm(axis))
        return axis / max(norm, 1e-12)

    def c2w_list_from_extrinsics(extrinsics):
        mats = []
        for ext in extrinsics:
            c2w = np.linalg.inv(to_4x4(ext)).astype(np.float32)
            mats.append((c2w @ LOCAL_CAMERA_BASIS).astype(np.float32))
        return mats

    def estimate_pose_aware_similarity(local_c2w_list, global_c2w_list, estimate_scale=True):
        assert len(local_c2w_list) == len(global_c2w_list) >= 2, {"local_len": len(local_c2w_list), "global_len": len(global_c2w_list)}

        src_dirs = []
        dst_dirs = []
        src_centers = []
        dst_centers = []
        for local_c2w, global_c2w in zip(local_c2w_list, global_c2w_list):
            src_dirs.extend([local_c2w[:3, 0], local_c2w[:3, 1], local_c2w[:3, 2]])
            dst_dirs.extend([global_c2w[:3, 0], global_c2w[:3, 1], global_c2w[:3, 2]])
            src_centers.append(local_c2w[:3, 3])
            dst_centers.append(global_c2w[:3, 3])

        src_dirs = np.asarray(src_dirs, dtype=np.float64)
        dst_dirs = np.asarray(dst_dirs, dtype=np.float64)
        src_centers = np.asarray(src_centers, dtype=np.float64)
        dst_centers = np.asarray(dst_centers, dtype=np.float64)

        H = dst_dirs.T @ src_dirs
        U, _, Vt = np.linalg.svd(H)
        S = np.eye(3, dtype=np.float64)
        if np.linalg.det(U) * np.linalg.det(Vt) < 0:
            S[-1, -1] = -1.0
        R = U @ S @ Vt

        src_mean = src_centers.mean(axis=0)
        dst_mean = dst_centers.mean(axis=0)
        src_c = src_centers - src_mean
        dst_c = dst_centers - dst_mean
        src_rot = (R @ src_c.T).T

        if estimate_scale:
            denom = float(np.sum(src_rot ** 2))
            numer = float(np.sum(dst_c * src_rot))
            scale = numer / max(denom, 1e-12)
        else:
            scale = 1.0

        t = dst_mean - scale * (R @ src_mean)
        pred = (scale * (R @ src_centers.T)).T + t
        center_rmse = float(np.sqrt(np.mean(np.sum((pred - dst_centers) ** 2, axis=1))))
        rot_residual = float(np.mean(np.linalg.norm((R @ src_dirs.T).T - dst_dirs, axis=1)))

        T = np.eye(4, dtype=np.float64)
        T[:3, :3] = scale * R
        T[:3, 3] = t
        diag = {
            "scale": float(scale),
            "rotation_det": float(np.linalg.det(R)),
            "center_rmse": center_rmse,
            "rotation_dir_residual": rot_residual,
            "positive_similarity_ok": bool(scale > 0.0),
            "scale_in_range_ok": bool(TRANSFORM_SCALE_MIN <= scale <= TRANSFORM_SCALE_MAX),
            "center_rmse_ok": bool(center_rmse <= TRANSFORM_CENTER_RMSE_MAX),
            "rotation_dir_ok": bool(rot_residual <= TRANSFORM_ROT_DIR_MAX),
        }
        diag["hard_fail"] = bool(
            (scale <= 0.0)
            or (scale < TRANSFORM_SCALE_MIN)
            or (scale > TRANSFORM_SCALE_MAX)
            or (center_rmse > TRANSFORM_CENTER_RMSE_MAX)
            or (rot_residual > TRANSFORM_ROT_DIR_MAX)
        )
        return T.astype(np.float32), diag

    global_camera_map = c2w_rows_to_map(global_camera_matrix_df)
    global_frame_meta_df = global_centers_df.merge(
        prod_manifest_df[["record_index", "qc_blur_ok", "blur_score"]],
        on="record_index",
        how="left",
    )
    global_frame_meta_df["opt_x"] = global_frame_meta_df["record_index"].map(lambda x: float(optical_axis_from_c2w(global_camera_map[int(x)])[0]))
    global_frame_meta_df["opt_y"] = global_frame_meta_df["record_index"].map(lambda x: float(optical_axis_from_c2w(global_camera_map[int(x)])[1]))
    global_frame_meta_df["opt_z"] = global_frame_meta_df["record_index"].map(lambda x: float(optical_axis_from_c2w(global_camera_map[int(x)])[2]))
    global_frame_meta_df["qc_blur_ok"] = global_frame_meta_df["qc_blur_ok"].fillna(False).astype(bool)
    global_frame_meta_df["blur_score"] = global_frame_meta_df["blur_score"].fillna(0.0)
    global_frame_meta_df = global_frame_meta_df.sort_values("record_index").reset_index(drop=True)
    global_center_tree = cKDTree(global_frame_meta_df[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32))

    def assign_vertex_owners(xyz_w: np.ndarray, chunk_df: pd.DataFrame):
        chunk_record_df = global_frame_meta_df.loc[
            global_frame_meta_df["record_index"].isin(chunk_df["record_index"].astype(int).tolist())
        ].copy()
        record_min = int(chunk_df["record_index"].min())
        record_max = int(chunk_df["record_index"].max())
        candidate_mode = "chunk_only"
        candidate_df = chunk_record_df
        if len(candidate_df) < 2:
            candidate_mode = "chunk_with_margin"
            candidate_df = global_frame_meta_df.loc[
                global_frame_meta_df["record_index"].between(record_min - OWNER_RECORD_MARGIN, record_max + OWNER_RECORD_MARGIN)
            ].copy()
        if len(candidate_df) < 2:
            candidate_mode = "global_fallback"
            candidate_df = global_frame_meta_df.copy()
        candidate_tree = cKDTree(candidate_df[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32))

        k = min(OWNER_TOPK, len(candidate_df))
        dists, idxs = candidate_tree.query(xyz_w, k=k)
        if k == 1:
            dists = dists[:, None]
            idxs = idxs[:, None]

        candidate_meta = candidate_df.iloc[idxs.reshape(-1)].reset_index(drop=True)
        candidate_centers = candidate_meta[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32).reshape(len(xyz_w), k, 3)
        candidate_axes = candidate_meta[["opt_x", "opt_y", "opt_z"]].to_numpy(dtype=np.float32).reshape(len(xyz_w), k, 3)
        candidate_blur_ok = candidate_meta["qc_blur_ok"].to_numpy(dtype=bool).reshape(len(xyz_w), k)
        candidate_records = candidate_meta["record_index"].to_numpy(dtype=np.int64).reshape(len(xyz_w), k)

        view_vec = xyz_w[:, None, :] - candidate_centers
        view_norm = np.linalg.norm(view_vec, axis=2, keepdims=True)
        view_dir = view_vec / np.maximum(view_norm, 1e-12)
        dir_cos = np.sum(view_dir * candidate_axes, axis=2)
        dir_term = 1.0 - np.clip(dir_cos, -1.0, 1.0)
        blur_penalty = np.where(candidate_blur_ok, 0.0, 1.0)

        chunk_record_center = float(chunk_df["record_index"].median())
        chunk_record_span = float(max(chunk_df["record_index"].max() - chunk_df["record_index"].min(), 1))
        index_penalty = np.minimum(np.abs(candidate_records - chunk_record_center) / chunk_record_span, 1.0)

        score = (
            OWNER_W_DIST * np.asarray(dists, dtype=np.float32)
            + OWNER_W_DIR * dir_term.astype(np.float32)
            + OWNER_W_BLUR * blur_penalty.astype(np.float32)
            + OWNER_W_INDEX * index_penalty.astype(np.float32)
        )

        best_local = np.argmin(score, axis=1)
        row_idx = np.arange(len(xyz_w))
        return pd.DataFrame({
            "vertex_index": np.arange(len(xyz_w), dtype=np.int64),
            "owner_record_index": candidate_records[row_idx, best_local].astype(np.int64),
            "owner_candidate_mode": candidate_mode,
            "owner_candidate_record_min": int(candidate_df["record_index"].min()),
            "owner_candidate_record_max": int(candidate_df["record_index"].max()),
            "owner_score": score[row_idx, best_local].astype(np.float32),
            "owner_dist": np.asarray(dists, dtype=np.float32)[row_idx, best_local].astype(np.float32),
            "owner_dir_cos": dir_cos[row_idx, best_local].astype(np.float32),
            "owner_blur_ok": candidate_blur_ok[row_idx, best_local].astype(bool),
        })

    transform_rows = []
    keep_rows = []
    warning_rows = []
    all_vertices = []
    dtype_ref = None
    master_scene = trimesh.Scene()
    owner_hist_rows = []
    chunk_assign_rows = []

    for row in completed_chunks_df.itertuples(index=False):
        out_dir = chunk_runs_dir / row.chunk_name
        ply_path = out_dir / "gs_ply" / "0000.ply"
        pred_ext_path = out_dir / "pred_extrinsics.npy"
        chunk_input_path = out_dir / "chunk_input_frames.csv"
        glb_path = out_dir / "scene.glb"
        if not (ply_path.exists() and pred_ext_path.exists() and chunk_input_path.exists()):
            continue

        chunk_df = pd.read_csv(chunk_input_path)
        pred_extrinsics = np.load(pred_ext_path)
        chunk_df.attrs["chunk_name"] = row.chunk_name

        local_c2w_list = c2w_list_from_extrinsics(pred_extrinsics)
        local_centers = np.stack([m[:3, 3] for m in local_c2w_list], axis=0).astype(np.float32)

        merged = chunk_df.merge(
            global_centers_df[["record_index", "cx_world", "cy_world", "cz_world"]],
            on="record_index",
            how="left",
        )
        assert not merged[["cx_world", "cy_world", "cz_world"]].isnull().any().any(), f"global center missing: {row.chunk_name}"
        global_c2w_list = [global_camera_map[int(record_index)] for record_index in merged["record_index"].tolist()]

        T_c_to_w0, align_diag = estimate_pose_aware_similarity(local_c2w_list, global_c2w_list, estimate_scale=True)

        T_path = chunk_manifest_dir / f"{row.chunk_name}_to_w0.npy"
        np.save(T_path, T_c_to_w0)
        transform_rows.append({
            "chunk_name": row.chunk_name,
            "frame_count": int(len(chunk_df)),
            "transform_path": str(T_path),
            "local_camera_basis": "perm_yxz_sign_ppn",
            "scale": float(align_diag["scale"]),
            "rotation_det": float(align_diag["rotation_det"]),
            "center_rmse": float(align_diag["center_rmse"]),
            "rotation_dir_residual": float(align_diag["rotation_dir_residual"]),
            "positive_similarity_ok": bool(align_diag["positive_similarity_ok"]),
            "scale_in_range_ok": bool(align_diag["scale_in_range_ok"]),
            "center_rmse_ok": bool(align_diag["center_rmse_ok"]),
            "rotation_dir_ok": bool(align_diag["rotation_dir_ok"]),
            "hard_fail": bool(align_diag["hard_fail"]),
        })
        assert not align_diag["hard_fail"], {
            "chunk_name": row.chunk_name,
            "reason": "invalid_pose_similarity",
            "align_diag": align_diag,
        }

        adopted_record_set = set(chunk_df.loc[chunk_df["is_adopted_region"] == True, "record_index"].astype(int).tolist())

        ply = PlyData.read(str(ply_path))
        df = pd.DataFrame(ply["vertex"].data)
        xyz = df[["x", "y", "z"]].to_numpy(dtype=np.float32)

        A = T_c_to_w0[:3, :3].astype(np.float32)
        t32 = T_c_to_w0[:3, 3].astype(np.float32)
        xyz_w = (A @ xyz.T).T + t32
        assignment_df = assign_vertex_owners(xyz_w, chunk_df)
        assignment_df["chunk_name"] = row.chunk_name
        keep = assignment_df["owner_record_index"].isin(adopted_record_set).to_numpy(dtype=bool)
        assignment_df["kept"] = keep
        assignment_df.to_csv(out_dir / "vertex_assignment_summary.csv", index=False, encoding="utf-8")

        chunk_evidence_dir = final_outputs_chunk_evidence_dir / row.chunk_name
        chunk_evidence_dir.mkdir(parents=True, exist_ok=True)
        chunk_evidence_copy_plan = [
            (out_dir / "vertex_assignment_summary.csv", chunk_evidence_dir / "vertex_assignment_summary.csv"),
            (out_dir / "chunk_input_frames.csv", chunk_evidence_dir / "chunk_input_frames.csv"),
            (out_dir / "pred_extrinsics.npy", chunk_evidence_dir / "pred_extrinsics.npy"),
            (out_dir / "pred_intrinsics.npy", chunk_evidence_dir / "pred_intrinsics.npy"),
        ]
        for src, dst in chunk_evidence_copy_plan:
            if src.exists():
                shutil.copy2(src, dst)

        owner_hist = assignment_df.groupby("owner_record_index", as_index=False).size().rename(columns={"size": "owner_vertex_count"})
        owner_hist["chunk_name"] = row.chunk_name
        owner_hist_rows.append(owner_hist)

        chunk_assign = assignment_df.groupby(["owner_record_index", "owner_blur_ok"], as_index=False).agg(
            owner_vertex_count=("vertex_index", "count"),
            owner_score_mean=("owner_score", "mean"),
            owner_dist_mean=("owner_dist", "mean"),
            owner_dir_cos_mean=("owner_dir_cos", "mean"),
        )
        chunk_assign["chunk_name"] = row.chunk_name
        chunk_assign_rows.append(chunk_assign)

        df["x"] = xyz_w[:, 0]
        df["y"] = xyz_w[:, 1]
        df["z"] = xyz_w[:, 2]
        df = df.loc[keep].copy()

        if len(df) > 0:
            records = df.to_records(index=False)
            if dtype_ref is None:
                dtype_ref = records.dtype
            else:
                records = records.astype(dtype_ref, copy=False)
            all_vertices.append(records)

        transform_warning = bool(
            align_diag["center_rmse"] > TRANSFORM_CENTER_RMSE_WARN
            or align_diag["rotation_dir_residual"] > TRANSFORM_ROT_DIR_WARN
        )
        keep_zero_chunk = int(len(df)) == 0
        warning_rows.append({
            "chunk_name": row.chunk_name,
            "transform_warning": transform_warning,
            "keep_zero_chunk": keep_zero_chunk,
            "fallback_used": False,
        })
        keep_rows.append({
            "chunk_name": row.chunk_name,
            "kept_vertices": int(len(df)),
            "owner_record_unique_count": int(assignment_df["owner_record_index"].nunique()),
            "owner_candidate_mode": str(assignment_df["owner_candidate_mode"].iloc[0]),
            "owner_record_min": int(assignment_df["owner_record_index"].min()),
            "owner_record_max": int(assignment_df["owner_record_index"].max()),
            "owner_blur_ok_ratio": float(assignment_df["owner_blur_ok"].mean()),
            "owner_score_mean": float(assignment_df["owner_score"].mean()),
        })
        assert not keep_zero_chunk, {"chunk_name": row.chunk_name, "reason": "keep_zero_chunk"}

        if glb_path.exists():
            scene = load_scene_any(glb_path)
            for gname, geom in scene.geometry.items():
                geom2 = geom.copy()
                if hasattr(geom2, "apply_transform"):
                    geom2.apply_transform(T_c_to_w0)
                master_scene.add_geometry(geom2, node_name=f"{row.chunk_name}_{gname}")

    transform_df = pd.DataFrame(transform_rows)
    transform_df.to_csv(chunk_manifest_dir / "chunk_global_transforms.csv", index=False, encoding="utf-8")

    keep_df = pd.DataFrame(keep_rows)
    keep_summary_path = merged_dir / "chunk_keep_summary.csv"
    keep_df.to_csv(keep_summary_path, index=False, encoding="utf-8")
    transform_quality_path = merged_dir / "chunk_transform_quality.csv"
    transform_df.to_csv(transform_quality_path, index=False, encoding="utf-8")

    if owner_hist_rows:
        pd.concat(owner_hist_rows, ignore_index=True).to_csv(merged_dir / "owner_record_histogram.csv", index=False, encoding="utf-8")
    if chunk_assign_rows:
        pd.concat(chunk_assign_rows, ignore_index=True).to_csv(merged_dir / "chunk_assignment_summary.csv", index=False, encoding="utf-8")

    warning_summary = {
        "transform_warning_count": int(sum(bool(x["transform_warning"]) for x in warning_rows)),
        "keep_zero_chunk_count": int(sum(bool(x["keep_zero_chunk"]) for x in warning_rows)),
        "fallback_used_count": 0,
        "rows": warning_rows,
    }
    (merged_dir / "merge_warning_summary.json").write_text(json.dumps(warning_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    merged_ply_path = merged_dir / "merged_gs.ply"
    if all_vertices:
        merged_vertices = np.concatenate(all_vertices, axis=0)
        PlyData([PlyElement.describe(merged_vertices, "vertex")], text=False).write(str(merged_ply_path))

    stage_11_2_copy_plan = [
        (merged_ply_path, stage_11_2_dir / "merged_gs.ply"),
        (chunk_manifest_dir / "chunk_global_transforms.csv", stage_11_2_dir / "chunk_global_transforms.csv"),
        (keep_summary_path, stage_11_2_dir / "chunk_keep_summary.csv"),
        (transform_quality_path, stage_11_2_dir / "chunk_transform_quality.csv"),
        (merged_dir / "owner_record_histogram.csv", stage_11_2_dir / "owner_record_histogram.csv"),
        (merged_dir / "chunk_assignment_summary.csv", stage_11_2_dir / "chunk_assignment_summary.csv"),
        (merged_dir / "merge_warning_summary.json", stage_11_2_dir / "merge_warning_summary.json"),
        (merged_dir / "all_batch_summary.json", stage_11_2_dir / "all_batch_summary.json"),
    ]
    stage_11_2_files = []
    for src, dst in stage_11_2_copy_plan:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            stage_11_2_files.append(str(dst))
    merge_resume_state = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "stage": "11-2-complete",
        "completed_chunk_count": int(len(completed_chunks_df)),
        "all_chunk_count": int(len(all_chunks_df)),
        "stage_11_2_dir": str(stage_11_2_dir),
        "stage_11_2_files": stage_11_2_files,
        "merged_ply_path": str(merged_ply_path) if merged_ply_path.exists() else None,
    }
    (final_outputs_diagnostics_dir / "merge_resume_state.json").write_text(json.dumps(merge_resume_state, indent=2, ensure_ascii=False), encoding="utf-8")

    merged_glb_path = merged_dir / "merged_scene.glb"
    if len(master_scene.geometry) > 0:
        master_scene.export(str(merged_glb_path))

    for src in stage_11_2_dir.glob("*"):
        if src.is_file():
            shutil.copy2(src, stage_11_3_dir / src.name)
    if merged_glb_path.exists():
        shutil.copy2(merged_glb_path, stage_11_3_dir / "merged_scene.glb")
    merge_resume_state.update({
        "stage": "11-3-complete",
        "stage_11_3_dir": str(stage_11_3_dir),
        "merged_glb_path": str(merged_glb_path) if merged_glb_path.exists() else None,
    })
    (final_outputs_diagnostics_dir / "merge_resume_state.json").write_text(json.dumps(merge_resume_state, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(final_outputs_diagnostics_dir / "merge_resume_state.json", stage_11_3_dir / "merge_resume_state.json")

    final_output_copy_plan = [
        (merged_ply_path, final_outputs_merged_dir / "merged_gs.ply"),
        (merged_glb_path, final_outputs_merged_dir / "merged_scene.glb"),
        (chunk_manifest_dir / "chunk_global_transforms.csv", final_outputs_diagnostics_dir / "chunk_global_transforms.csv"),
        (keep_summary_path, final_outputs_diagnostics_dir / "chunk_keep_summary.csv"),
        (transform_quality_path, final_outputs_diagnostics_dir / "chunk_transform_quality.csv"),
        (merged_dir / "owner_record_histogram.csv", final_outputs_diagnostics_dir / "owner_record_histogram.csv"),
        (merged_dir / "chunk_assignment_summary.csv", final_outputs_diagnostics_dir / "chunk_assignment_summary.csv"),
        (merged_dir / "merge_warning_summary.json", final_outputs_diagnostics_dir / "merge_warning_summary.json"),
        (merged_dir / "all_batch_summary.json", final_outputs_diagnostics_dir / "all_batch_summary.json"),
        (manifest_dir / "da3_input_manifest_prod.csv", final_outputs_manifests_dir / "da3_input_manifest_prod.csv"),
        (global_pose_dir / "camera_center_matrix.csv", final_outputs_manifests_dir / "camera_center_matrix.csv"),
        (global_pose_dir / "camera_matrix_full.csv", final_outputs_manifests_dir / "camera_matrix_full.csv"),
        (chunk_manifest_dir / "chunk_index_all.csv", final_outputs_manifests_dir / "chunk_index_all.csv"),
        (chunk_manifest_dir / "batch_plan.csv", final_outputs_manifests_dir / "batch_plan.csv"),
    ]
    final_output_files = []
    for src, dst in final_output_copy_plan:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            final_output_files.append({
                "label": dst.name,
                "source_path": str(src),
                "drive_path": str(dst),
            })

    bundle_summary = {
        "status": "skipped",
        "reason": "MAKE_DRIVE_BUNDLE is False",
    }

    if MAKE_DRIVE_BUNDLE:
        local_bundle_base = f"{modeling_session_id}_{BUNDLE_MODEL_SLUG}_continuousgsv06chunk18ov6ad12"
        local_bundle_zip = Path("/content") / f"{local_bundle_base}.zip"

        if local_bundle_zip.exists():
            local_bundle_zip.unlink()

        bundle_summary = {
            "status": "ok",
            "drive_visible_dir": str(probe_root),
            "drive_pipeline_root": str(pipeline_root),
            "drive_results_root": str(results_root),
        }

        if MAKE_LOCAL_BUNDLE_ZIP:
            shutil.make_archive(str(local_bundle_zip.with_suffix("")), "zip", root_dir=str(probe_root))
            bundle_summary["local_bundle_zip"] = str(local_bundle_zip)

        if DOWNLOAD_LOCAL_BUNDLE and MAKE_LOCAL_BUNDLE_ZIP:
            from google.colab import files
            assert local_bundle_zip.exists(), local_bundle_zip
            files.download(str(local_bundle_zip))
            bundle_summary["download_requested"] = True
            bundle_summary["manual_download_hint"] = f"from google.colab import files; files.download(r'{local_bundle_zip}')"
            print("# manual_download_hint")
            print(bundle_summary["manual_download_hint"])

    final_output_manifest = {
        "status": "ok" if final_output_files else "partial",
        "drive_visible_dir": str(probe_root),
        "final_outputs_dir": str(final_outputs_dir),
        "final_outputs_merged_dir": str(final_outputs_merged_dir),
        "final_outputs_diagnostics_dir": str(final_outputs_diagnostics_dir),
        "final_outputs_manifests_dir": str(final_outputs_manifests_dir),
        "final_outputs_chunk_evidence_dir": str(final_outputs_chunk_evidence_dir),
        "stage_11_2_dir": str(stage_11_2_dir),
        "stage_11_3_dir": str(stage_11_3_dir),
        "chunk_evidence_dirs": sorted([str(p) for p in final_outputs_chunk_evidence_dir.glob("*") if p.is_dir()]),
        "file_count": int(len(final_output_files)),
        "files": final_output_files,
    }
    (final_outputs_dir / "final_output_manifest.json").write_text(json.dumps(final_output_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    merge_summary = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "status": "ok" if all_vertices else "skipped",
        "reason": None if all_vertices else "no kept vertices",
        "completed_chunk_count": int(len(completed_chunks_df)),
        "all_chunk_count": int(len(all_chunks_df)),
        "merged_ply_path": str(merged_ply_path) if merged_ply_path.exists() else None,
        "merged_glb_path": str(merged_glb_path) if merged_glb_path.exists() else None,
        "chunk_global_transforms_path": str(chunk_manifest_dir / "chunk_global_transforms.csv"),
        "chunk_keep_summary_path": str(keep_summary_path),
        "chunk_transform_quality_path": str(transform_quality_path),
        "owner_record_histogram_path": str(merged_dir / "owner_record_histogram.csv"),
        "chunk_assignment_summary_path": str(merged_dir / "chunk_assignment_summary.csv"),
        "merge_warning_summary_path": str(merged_dir / "merge_warning_summary.json"),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary.json"),
        "final_outputs_dir": str(final_outputs_dir),
        "final_output_manifest_path": str(final_outputs_dir / "final_output_manifest.json"),
        "bundle_summary": bundle_summary,
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(merged_dir / "merge_summary.json", final_outputs_diagnostics_dir / "merge_summary.json")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))

```

### #12 Cleanup inventory

- `#12` は `#1` から `#11` までの生成物を対象に、Drive 正本として保持するものと、merge 完了後に削除候補へ回せる不可視生成物を一覧化する。
- `#12` 自体は削除しない。`cleanup_plan.json` を作って、admin が内容を見てから `#13` で適用する
- 全 block 対象の cleanup inventory
- cleanup_plan.json を作る
- 何を残し、何を消せるかを一覧表示

```python
#12
from pathlib import Path
import json
import os

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
probe_root = Path(ctx["probe_root"])
results_root = Path(ctx["results_root"])
manifest_dir = Path(ctx["manifest_dir"])
proof_metric_dir = Path(ctx["proof_metric_dir"])
prod_metric_dir = Path(ctx["prod_metric_dir"])
proof_giant_dir = Path(ctx["proof_giant_dir"])
world_dir = Path(ctx["world_dir"])

pipeline_root = probe_root / "continuous_gs_v06_chunk18_overlap6_adopt12"
global_pose_dir = pipeline_root / "global_pose_bootstrap"
chunk_manifest_dir = pipeline_root / "manifests"
chunk_runs_dir = pipeline_root / "chunk_runs"
merged_dir = Path(ctx.get("merged_dir", str(pipeline_root / "merged")))
merge_summary_path = merged_dir / "merge_summary.json"

def path_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return int(path.stat().st_size)
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            fp = Path(root) / name
            try:
                total += int(fp.stat().st_size)
            except FileNotFoundError:
                pass
    return int(total)

merge_summary = json.loads(merge_summary_path.read_text(encoding="utf-8")) if merge_summary_path.exists() else {}
merge_ok = bool(merge_summary.get("status") == "ok")

kept_groups = [
    {"block": "#6", "label": "manifest_dir", "path": str(manifest_dir)},
    {"block": "#6", "label": "final_outputs_dir", "path": str(final_outputs_dir)},
    {"block": "#6", "label": "final_outputs_merged_dir", "path": str(final_outputs_merged_dir)},
    {"block": "#6", "label": "final_outputs_diagnostics_dir", "path": str(final_outputs_diagnostics_dir)},
    {"block": "#6", "label": "final_outputs_manifests_dir", "path": str(final_outputs_manifests_dir)},
    {"block": "#6", "label": "final_outputs_chunk_evidence_dir", "path": str(final_outputs_chunk_evidence_dir)},
    {"block": "#7", "label": "proof_metric_dir", "path": str(proof_metric_dir)},
    {"block": "#7", "label": "prod_metric_dir", "path": str(prod_metric_dir)},
    {"block": "#7", "label": "world_dir", "path": str(world_dir)},
    {"block": "#8", "label": "global_pose_dir", "path": str(global_pose_dir)},
    {"block": "#8", "label": "chunk_manifest_dir", "path": str(chunk_manifest_dir)},
    {"block": "#11", "label": "merged_dir", "path": str(merged_dir)},
    {"block": "#11", "label": "proof_giant_dir", "path": str(proof_giant_dir)},
]

delete_candidates = []
if chunk_runs_dir.exists() and merge_ok:
    delete_candidates.append({
        "block": "#10",
        "path": str(chunk_runs_dir),
        "kind": "drive_dir",
        "reason": "chunk intermediate gs outputs already merged",
        "size_bytes": path_size_bytes(chunk_runs_dir),
    })

local_tmp_candidates = [
    ("#2", Path("/content/runbook_selected_input.json"), "local_tmp", "selected input pointer"),
    ("#4", Path("/content/runbook_paths.json"), "local_tmp", "resolved path cache"),
    ("#5", Path("/content/runbook_session_context.json"), "local_tmp", "session context cache"),
    ("#5", Path("/content/trajectreview_input"), "local_tmp", "extracted input workspace"),
]
local_bundle_zip = merge_summary.get("bundle_summary", {}).get("local_bundle_zip")
if local_bundle_zip:
    local_tmp_candidates.append(("#11", Path(local_bundle_zip), "local_tmp", "download-only local bundle zip"))

for block_no, p, kind, reason in local_tmp_candidates:
    if p.exists():
        delete_candidates.append({
            "block": block_no,
            "path": str(p),
            "kind": kind,
            "reason": reason,
            "size_bytes": path_size_bytes(p),
        })

cleanup_plan = {
    "drive_visible_dir": str(probe_root),
    "drive_final_outputs_dir": str(final_outputs_dir),
    "results_root": str(results_root),
    "merge_status": merge_summary.get("status"),
    "kept_groups": kept_groups,
    "delete_candidate_count": int(len(delete_candidates)),
    "delete_candidate_total_bytes": int(sum(x["size_bytes"] for x in delete_candidates)),
    "delete_candidates": delete_candidates,
}
(merged_dir / "cleanup_plan.json").write_text(json.dumps(cleanup_plan, indent=2, ensure_ascii=False), encoding="utf-8")
Path(final_outputs_diagnostics_dir).mkdir(parents=True, exist_ok=True)
(final_outputs_diagnostics_dir / "cleanup_plan.json").write_text(json.dumps(cleanup_plan, indent=2, ensure_ascii=False), encoding="utf-8")
print("# cleanup_plan")
print(json.dumps(cleanup_plan, indent=2, ensure_ascii=False))
```

### #13 Cleanup apply

- `#13` は `#12` が作った `cleanup_plan.json` を読んで、yes の時だけ削除する。
- `#13` は `probe_root` 配下の正本 directory を削除しない。削除するのは `delete_candidates` に載った不可視生成物だけである。
- cleanup_plan.json を読んで
- yes の時だけ削除実行

```python
#13
from pathlib import Path
import json
import shutil

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
probe_root = Path(ctx["probe_root"])
final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
pipeline_root = probe_root / "continuous_gs_v06_chunk18_overlap6_adopt12"
merged_dir = Path(ctx.get("merged_dir", str(pipeline_root / "merged")))
cleanup_plan_path = merged_dir / "cleanup_plan.json"
assert cleanup_plan_path.exists(), cleanup_plan_path

cleanup_plan = json.loads(cleanup_plan_path.read_text(encoding="utf-8"))
print("# cleanup_plan_reloaded")
print(json.dumps(cleanup_plan, indent=2, ensure_ascii=False))

answer = input("Delete cleanup_plan delete_candidates now? type yes to delete: ").strip().lower()

deleted = []
if answer == "yes":
    for item in cleanup_plan["delete_candidates"]:
        p = Path(item["path"])
        if not p.exists():
            continue
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        deleted.append(item)
    cleanup_result = {
        "status": "ok",
        "reason": "user_confirmed",
        "deleted": deleted,
    }
else:
    cleanup_result = {
        "status": "skipped",
        "reason": "user_declined",
        "deleted": [],
    }

(merged_dir / "cleanup_result.json").write_text(json.dumps(cleanup_result, indent=2, ensure_ascii=False), encoding="utf-8")
Path(final_outputs_diagnostics_dir).mkdir(parents=True, exist_ok=True)
(final_outputs_diagnostics_dir / "cleanup_result.json").write_text(json.dumps(cleanup_result, indent=2, ensure_ascii=False), encoding="utf-8")
print("# cleanup_result")
print(json.dumps(cleanup_result, indent=2, ensure_ascii=False))
```
