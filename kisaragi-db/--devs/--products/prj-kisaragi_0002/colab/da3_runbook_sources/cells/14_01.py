#14-1
from pathlib import Path
import json
import shutil
import os
import subprocess
import sys

import numpy as np
import pandas as pd

missing_merge_deps = []
for module_name, package_name in [
    ("trimesh", "trimesh"),
    ("plyfile", "plyfile"),
    ("scipy", "scipy"),
]:
    try:
        __import__(module_name)
    except ModuleNotFoundError:
        missing_merge_deps.append(package_name)

if missing_merge_deps:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet", *missing_merge_deps],
        check=True,
    )

import trimesh
from plyfile import PlyData, PlyElement
from scipy.spatial import cKDTree

batch_preflight_status_path = Path("/content/runbook_batch_preflight_status.json")
if not batch_preflight_status_path.exists():
    print("# warning: batch execution preflight was not run; continued by self-heal path")

ctx = json.loads(Path("/content/runbook_session_context.json").read_text(encoding="utf-8"))
probe_root = Path(ctx["probe_root"])
results_root = Path(ctx["results_root"])
persist_root = Path(ctx.get("persist_root", probe_root))
modeling_session_id = ctx["modeling_session_id"]
manifest_dir = Path(ctx["manifest_dir"])
final_outputs_dir = Path(ctx["final_outputs_dir"])
final_outputs_merged_dir = Path(ctx["final_outputs_merged_dir"])
final_outputs_diagnostics_dir = Path(ctx["final_outputs_diagnostics_dir"])
final_outputs_manifests_dir = Path(ctx["final_outputs_manifests_dir"])
final_outputs_chunk_evidence_dir = Path(ctx["final_outputs_chunk_evidence_dir"])

pipeline_root = probe_root / ctx.get("pipeline_slug", "da3_ngl_batch_v01")
anchor_dir = persist_root / "01_anchor"
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
        "BUNDLE_MODEL_SLUG": "nestedgiantlarge11",
        "PROCESS_RES": 504,
        "CHUNK_SIZE": 18,
        "STEP": 12,
        "ADOPT_SIZE": 12,
        "CHUNKS_PER_BATCH": 2,
        "GLOBAL_CAMERA_SOURCE": "extrinsics_w2c_arc.npy",
        "TARGET_CHUNK_MODE": "selected_chunk_ids_1based",
        "TARGET_CHUNK_IDS_1BASED": [6, 7],
        "USE_TARGET_CHUNK_WINDOW": False,
        "TARGET_CHUNK_WINDOW_START_1BASED": 1,
        "TARGET_CHUNK_WINDOW_COUNT": 0,
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
BUNDLE_MODEL_SLUG = config["BUNDLE_MODEL_SLUG"]
REQUIRE_ALL_CHUNKS = True
config_snapshot = json.loads(Path("/content/config_snapshot.json").read_text(encoding="utf-8")) if Path("/content/config_snapshot.json").exists() else {}
MAKE_DRIVE_BUNDLE = bool(config_snapshot.get("MAKE_DRIVE_BUNDLE", False))
INFER_GS = bool(config_snapshot.get("INFER_GS", config.get("INFER_GS", True)))
batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"

TRANSFORM_SCALE_MIN = 0.8
TRANSFORM_SCALE_MAX = 1.3
TRANSFORM_CENTER_RMSE_MAX = 0.15
TRANSFORM_ROT_DIR_MAX = 0.20
ROUTE_ARCORE = "arcore_anchor_baseline"
ROUTE_DA3 = "da3_predicted_primary"
PREFERRED_ROUTE_LABEL = ROUTE_DA3
LOCAL_EXTRINSIC_MODE = "c2w"
LOCAL_CAMERA_BASIS = np.eye(4, dtype=np.float32)
LOCAL_CAMERA_BASIS[:3, :3] = np.array([
    [0.0, 1.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.0, 0.0, -1.0],
], dtype=np.float32)

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

def ensure_target_chunk_manifest():
    target_path = chunk_manifest_dir / "chunk_index_target.csv"
    if target_path.exists():
        return pd.read_csv(target_path)
    all_path = chunk_manifest_dir / "chunk_index_all.csv"
    assert all_path.exists(), all_path
    base_df = pd.read_csv(all_path)
    target_mode = str(config.get("TARGET_CHUNK_MODE", "selected_chunk_ids_1based"))
    if target_mode == "full_set":
        target_chunks_df = base_df.copy().reset_index(drop=True)
    elif target_mode == "selected_chunk_ids_1based":
        valid_chunk_ids = set(base_df["chunk_id"].astype(int).tolist())
        selected_chunk_ids = sorted({int(x) - 1 for x in config.get("TARGET_CHUNK_IDS_1BASED", []) if int(x) >= 1})
        selected_chunk_ids = [x for x in selected_chunk_ids if x in valid_chunk_ids]
        assert selected_chunk_ids, {
            "reason": "selected target chunk ids resolved empty",
            "selected_chunk_ids_1based": config.get("TARGET_CHUNK_IDS_1BASED", []),
            "valid_chunk_ids_0based": sorted(valid_chunk_ids),
        }
        target_chunks_df = base_df.loc[base_df["chunk_id"].astype(int).isin(selected_chunk_ids)].copy()
        target_chunks_df = target_chunks_df.sort_values("chunk_id", kind="stable").reset_index(drop=True)
    elif config.get("USE_TARGET_CHUNK_WINDOW", False):
        start_0 = max(0, int(config.get("TARGET_CHUNK_WINDOW_START_1BASED", 1)) - 1)
        end_0 = min(start_0 + int(config.get("TARGET_CHUNK_WINDOW_COUNT", 3)), len(base_df))
        target_chunks_df = base_df.iloc[start_0:end_0].copy().reset_index(drop=True)
    else:
        raise AssertionError({"reason": "unsupported target chunk mode", "target_mode": target_mode})
    target_chunks_df.to_csv(target_path, index=False, encoding="utf-8")
    return target_chunks_df

def resolve_chunk_output_dir(chunk_name: str) -> Path:
    direct = chunk_runs_dir / chunk_name
    if (direct / "pred_extrinsics.npy").exists() and (direct / "chunk_input_frames.csv").exists():
        return direct

    nested_candidates = sorted({
        p.parent
        for p in chunk_runs_dir.glob(f"batch_*/{chunk_name}/_SUCCESS.json")
    } | {
        p.parent
        for p in chunk_runs_dir.glob(f"batch_*/{chunk_name}/pred_extrinsics.npy")
    } | {
        p.parent
        for p in chunk_runs_dir.glob(f"batch_*/{chunk_name}/chunk_input_frames.csv")
    })
    for candidate in nested_candidates:
        if (candidate / "pred_extrinsics.npy").exists() and (candidate / "chunk_input_frames.csv").exists():
            return candidate

    raise AssertionError({
        "chunk_name": chunk_name,
        "missing_dir": str(direct),
        "reason": "run #12-3 before #14-1",
        "searched_nested_under": str(chunk_runs_dir),
    })

def resolve_chunk_input_dir(chunk_name: str) -> Path:
    return resolve_chunk_output_dir(chunk_name)

all_chunks_df = pd.read_csv(chunk_manifest_dir / "chunk_index_all.csv")
target_chunks_df = ensure_target_chunk_manifest()
completed_chunk_names = []
pred_ready_chunk_names = []
ply_ready_chunk_names = []
for chunk_name in target_chunks_df["chunk_name"].astype(str).tolist():
    try:
        out_dir = resolve_chunk_output_dir(chunk_name)
    except AssertionError:
        continue
    if (out_dir / "_SUCCESS.json").exists():
        completed_chunk_names.append(chunk_name)
    if (out_dir / "pred_extrinsics.npy").exists():
        pred_ready_chunk_names.append(chunk_name)
    if (out_dir / "gs_ply" / "0000.ply").exists():
        ply_ready_chunk_names.append(chunk_name)

completed_chunk_names = sorted(set(completed_chunk_names))
pred_ready_chunk_names = sorted(set(pred_ready_chunk_names))
ply_ready_chunk_names = sorted(set(ply_ready_chunk_names))
completed_chunks_df = target_chunks_df[target_chunks_df["chunk_name"].isin(completed_chunk_names)].copy()
pred_ready_target_chunk_names = sorted(set(pred_ready_chunk_names) & set(target_chunks_df["chunk_name"].tolist()))
ply_ready_target_chunk_names = sorted(set(ply_ready_chunk_names) & set(target_chunks_df["chunk_name"].tolist()))

batch_summaries = sorted({
    str(p) for p in chunk_runs_dir.glob("batch_*/batch_summary.json")
})
summary_rows = [json.loads(Path(p).read_text(encoding="utf-8")) for p in batch_summaries]
(merged_dir / "all_batch_summary_arc.json").write_text(json.dumps(summary_rows, indent=2, ensure_ascii=False), encoding="utf-8")
premerge_pose_validation_path = merged_dir / "premerge_pose_validation.json"

if not premerge_pose_validation_path.exists():
    merge_summary = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "status": "skipped",
        "reason": "premerge_pose_validation_required",
        "premerge_pose_validation_path": str(premerge_pose_validation_path),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary_arc.json"),
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
    raise AssertionError("run #13-1 pre-merge pose gate before #14-1 merge")

premerge_pose_validation = json.loads(premerge_pose_validation_path.read_text(encoding="utf-8"))
premerge_route_compare_path = merged_dir / "premerge_route_compare_summary.json"
prepose_chunk_graph_solution_path = merged_dir / "prepose_chunk_graph_solution_arc.csv"
prepose_chunk_graph_edges_path = merged_dir / "prepose_chunk_graph_edges_arc.csv"
prepose_chunk_graph_summary_path = merged_dir / "prepose_chunk_graph_summary.json"
if premerge_pose_validation.get("status") != "ok":
    merge_summary = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "status": "skipped",
        "reason": "premerge_pose_validation_failed",
        "premerge_pose_validation_path": str(premerge_pose_validation_path),
        "premerge_route_compare_path": str(premerge_route_compare_path) if premerge_route_compare_path.exists() else None,
        "prepose_chunk_graph_solution_path": str(prepose_chunk_graph_solution_path) if prepose_chunk_graph_solution_path.exists() else None,
        "hard_fail_count": int(premerge_pose_validation.get("hard_fail_count", 0)),
        "failed_chunks": premerge_pose_validation.get("failed_chunks", []),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary_arc.json"),
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
    raise AssertionError(premerge_pose_validation)

if REQUIRE_ALL_CHUNKS and len(completed_chunks_df) < len(target_chunks_df):
    merge_summary = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "status": "skipped",
        "reason": "waiting_for_all_chunks",
        "completed_chunk_count": int(len(completed_chunks_df)),
        "pred_ready_chunk_count": int(len(pred_ready_target_chunk_names)),
        "ply_ready_chunk_count": int(len(ply_ready_target_chunk_names)),
        "all_chunk_count": int(len(target_chunks_df)),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary_arc.json"),
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
elif INFER_GS and len(ply_ready_target_chunk_names) < len(target_chunks_df):
    merge_summary = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "status": "skipped",
        "reason": "gaussian_chunk_outputs_missing",
        "completed_chunk_count": int(len(completed_chunks_df)),
        "pred_ready_chunk_count": int(len(pred_ready_target_chunk_names)),
        "ply_ready_chunk_count": int(len(ply_ready_target_chunk_names)),
        "all_chunk_count": int(len(target_chunks_df)),
        "infer_gs": bool(INFER_GS),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary_arc.json"),
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
else:
    global_centers_df = pd.read_csv(anchor_dir / "camera_center_matrix_arc.csv")
    global_camera_matrix_df = pd.read_csv(anchor_dir / "camera_matrix_full_arc.csv")
    global_anchor_df = pd.read_csv(anchor_dir / "camera_anchor_full_arc.csv")
    premerge_validation_df = pd.read_csv(merged_dir / "premerge_pose_validation.csv")
    prepose_graph_solution_df = (
        pd.read_csv(prepose_chunk_graph_solution_path)
        if prepose_chunk_graph_solution_path.exists() and prepose_chunk_graph_solution_path.stat().st_size > 0
        else pd.DataFrame()
    )
    selected_route_by_chunk = dict(zip(
        premerge_validation_df["chunk_name"].astype(str),
        premerge_validation_df["route_label"].astype(str),
    )) if len(premerge_validation_df) else {}
    prepose_graph_solution_by_chunk = {
        str(row["chunk_name"]): row.to_dict()
        for _, row in prepose_graph_solution_df.iterrows()
    } if len(prepose_graph_solution_df) else {}
    input_manifest_path = manifest_dir / "da3_input_manifest.csv"
    assert input_manifest_path.exists(), input_manifest_path
    input_manifest_df = pd.read_csv(input_manifest_path)
    if "cx_world" not in global_anchor_df.columns and "cam_cx" in global_anchor_df.columns:
        global_anchor_df["cx_world"] = global_anchor_df["cam_cx"]
        global_anchor_df["cy_world"] = global_anchor_df["cam_cy"]
        global_anchor_df["cz_world"] = global_anchor_df["cam_cz"]
    if "anchor_lens_x" not in global_anchor_df.columns and "lens_x" in global_anchor_df.columns:
        global_anchor_df["anchor_lens_x"] = global_anchor_df["lens_x"]
        global_anchor_df["anchor_lens_y"] = global_anchor_df["lens_y"]
        global_anchor_df["anchor_lens_z"] = global_anchor_df["lens_z"]
    if "anchor_up_x" not in global_anchor_df.columns and "up_x" in global_anchor_df.columns:
        global_anchor_df["anchor_up_x"] = global_anchor_df["up_x"]
        global_anchor_df["anchor_up_y"] = global_anchor_df["up_y"]
        global_anchor_df["anchor_up_z"] = global_anchor_df["up_z"]
    if "record_index" not in global_camera_matrix_df.columns and {"sequence_index", "record_index"}.issubset(global_anchor_df.columns):
        global_camera_matrix_df = global_camera_matrix_df.merge(
            global_anchor_df[["sequence_index", "record_index"]].drop_duplicates(),
            on="sequence_index",
            how="left",
            validate="many_to_one",
        )
    assert global_anchor_df["record_index"].is_unique, "global anchor record_index must be unique"
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

    def iter_baked_scene_geometry(scene: trimesh.Scene):
        dumped = None
        if hasattr(scene, "dump"):
            try:
                dumped = scene.dump(concatenate=False)
            except TypeError:
                dumped = scene.dump()
        if isinstance(dumped, (list, tuple)) and len(dumped) > 0:
            for idx, geom in enumerate(dumped):
                if geom is None:
                    continue
                if hasattr(geom, "copy"):
                    geom = geom.copy()
                yield f"dump_{idx:04d}", geom
            return
        for gname, geom in scene.geometry.items():
            geom2 = geom.copy() if hasattr(geom, "copy") else geom
            yield str(gname), geom2

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
        m_cols = [f"m{i}{j}" for i in range(4) for j in range(4)]
        w2c_cols = [f"w2c_{i}{j}" for i in range(4) for j in range(4)]
        use_m_cols = all(c in df.columns for c in m_cols)
        use_w2c_cols = all(c in df.columns for c in w2c_cols)
        assert use_m_cols or use_w2c_cols, {
            "reason": "camera matrix cols not found",
            "available_columns": df.columns.tolist(),
        }
        for row in df.itertuples(index=False):
            if use_m_cols:
                M = np.array([getattr(row, c) for c in m_cols], dtype=np.float32).reshape(4, 4)
                out[int(row.record_index)] = M
            else:
                w2c = np.array([getattr(row, c) for c in w2c_cols], dtype=np.float32).reshape(4, 4)
                out[int(row.record_index)] = np.linalg.inv(w2c).astype(np.float32)
        return out

    def normalize_rows(arr: np.ndarray, eps: float = 1e-12) -> np.ndarray:
        arr = np.asarray(arr, dtype=np.float64)
        arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
        norm = np.linalg.norm(arr, axis=1, keepdims=True)
        return arr / np.maximum(norm, eps)

    def summarize_split_metrics(values: np.ndarray, overlap_mask: np.ndarray, prefix: str) -> dict:
        values = np.asarray(values, dtype=np.float64)
        overlap_mask = np.asarray(overlap_mask, dtype=bool)
        nonoverlap_mask = ~overlap_mask

        def pack(mask: np.ndarray, label: str) -> dict:
            count = int(mask.sum())
            base = {
                f"{prefix}_{label}_count": count,
                f"{prefix}_{label}_mean": None,
                f"{prefix}_{label}_p95": None,
                f"{prefix}_{label}_max": None,
            }
            if count <= 0:
                return base
            subset = values[mask]
            base[f"{prefix}_{label}_mean"] = float(subset.mean())
            base[f"{prefix}_{label}_p95"] = float(np.quantile(subset, 0.95))
            base[f"{prefix}_{label}_max"] = float(subset.max())
            return base

        out = {}
        out.update(pack(overlap_mask, "overlap"))
        out.update(pack(nonoverlap_mask, "nonoverlap"))
        return out

    def lens_direction_from_c2w(c2w: np.ndarray):
        axis = -np.asarray(c2w[:3, 2], dtype=np.float32)
        norm = float(np.linalg.norm(axis))
        return axis / max(norm, 1e-12)

    def up_direction_from_c2w(c2w: np.ndarray):
        axis = -np.asarray(c2w[:3, 1], dtype=np.float32)
        norm = float(np.linalg.norm(axis))
        return axis / max(norm, 1e-12)

    def normalize_vec(vec: np.ndarray, fallback: np.ndarray):
        vec = np.asarray(vec, dtype=np.float32)
        norm = float(np.linalg.norm(vec))
        if norm <= 1e-12:
            fallback = np.asarray(fallback, dtype=np.float32)
            fallback_norm = float(np.linalg.norm(fallback))
            assert fallback_norm > 1e-12, "fallback vector must be non-zero"
            return fallback / fallback_norm
        return vec / norm

    def build_anchor_c2w(fallback_c2w: np.ndarray, rec) -> np.ndarray:
        M = np.asarray(fallback_c2w, dtype=np.float32).copy()
        center = np.array([float(rec.cx_world), float(rec.cy_world), float(rec.cz_world)], dtype=np.float32)
        anchor_lens = normalize_vec(
            np.array([float(rec.anchor_lens_x), float(rec.anchor_lens_y), float(rec.anchor_lens_z)], dtype=np.float32),
            lens_direction_from_c2w(M),
        )
        anchor_up = normalize_vec(
            np.array([float(rec.anchor_up_x), float(rec.anchor_up_y), float(rec.anchor_up_z)], dtype=np.float32),
            up_direction_from_c2w(M),
        )
        z_col = normalize_vec(-anchor_lens, M[:3, 2])
        x_seed = np.cross(-anchor_up, z_col)
        x_col = normalize_vec(x_seed, M[:3, 0])
        y_col = normalize_vec(np.cross(z_col, x_col), M[:3, 1])
        if float(np.dot(y_col, -anchor_up)) < 0.0:
            x_col = -x_col
            y_col = -y_col
        M[:3, 0] = x_col
        M[:3, 1] = y_col
        M[:3, 2] = z_col
        M[:3, 3] = center
        return M

    def c2w_list_from_extrinsics(extrinsics):
        mats = []
        for ext in extrinsics:
            raw = to_4x4(ext).astype(np.float32)
            if LOCAL_EXTRINSIC_MODE == "c2w":
                c2w = raw
            elif LOCAL_EXTRINSIC_MODE == "w2c":
                c2w = np.linalg.inv(raw).astype(np.float32)
            else:
                raise AssertionError({
                    "reason": "unsupported_local_extrinsic_mode",
                    "LOCAL_EXTRINSIC_MODE": LOCAL_EXTRINSIC_MODE,
                })
            mats.append((c2w @ LOCAL_CAMERA_BASIS).astype(np.float32))
        return mats

    def estimate_pose_aware_similarity(local_c2w_list, global_c2w_list, estimate_scale=True):
        assert len(local_c2w_list) == len(global_c2w_list) >= 2, {"local_len": len(local_c2w_list), "global_len": len(global_c2w_list)}

        src_dirs = []
        dst_dirs = []
        src_centers = []
        dst_centers = []
        for local_c2w, global_c2w in zip(local_c2w_list, global_c2w_list):
            src_dirs.append(lens_direction_from_c2w(local_c2w))
            src_dirs.append(up_direction_from_c2w(local_c2w))
            dst_dirs.append(lens_direction_from_c2w(global_c2w))
            dst_dirs.append(up_direction_from_c2w(global_c2w))
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

    def transform_c2w_list(c2w_list, T):
        out = []
        for c2w in c2w_list:
            M = np.asarray(c2w, dtype=np.float64).copy()
            M[:3, :3] = T[:3, :3] @ M[:3, :3]
            M[:3, 3] = T[:3, :3] @ M[:3, 3] + T[:3, 3]
            out.append(M.astype(np.float32))
        return out

    def summarize_route_candidate(chunk_name: str, route_label: str, route_source: str, route_overlap_record_count: int, overlap_record_indices: list[int], transformed_rows, anchor_rows, align_diag: dict) -> dict:
        pred_center = np.stack([m[:3, 3] for m in transformed_rows], axis=0)
        pred_lens = np.stack([lens_direction_from_c2w(m) for m in transformed_rows], axis=0)
        anchor_center = anchor_rows[["cx_world", "cy_world", "cz_world"]].to_numpy(dtype=np.float32)
        anchor_lens = anchor_rows[["anchor_lens_x", "anchor_lens_y", "anchor_lens_z"]].to_numpy(dtype=np.float32)
        record_indices = anchor_rows["record_index"].astype(int).to_numpy()
        overlap_index_set = {int(x) for x in overlap_record_indices}
        overlap_mask = np.array([int(x) in overlap_index_set for x in record_indices], dtype=bool)
        center_error = np.linalg.norm(pred_center - anchor_center, axis=1)
        lens_error_deg = np.degrees(np.arccos(np.clip(np.sum(normalize_rows(pred_lens) * normalize_rows(anchor_lens), axis=1), -1.0, 1.0)))
        out = {
            "chunk_name": chunk_name,
            "route_label": route_label,
            "route_source": route_source,
            "route_overlap_record_count": int(route_overlap_record_count),
            "route_overlap_local_count": int(overlap_mask.sum()),
            "route_nonoverlap_local_count": int((~overlap_mask).sum()),
            "scale": float(align_diag["scale"]),
            "rotation_det": float(align_diag["rotation_det"]),
            "center_rmse": float(align_diag["center_rmse"]),
            "rotation_dir_residual": float(align_diag["rotation_dir_residual"]),
            "positive_similarity_ok": bool(align_diag["positive_similarity_ok"]),
            "scale_in_range_ok": bool(align_diag["scale_in_range_ok"]),
            "center_rmse_ok": bool(align_diag["center_rmse_ok"]),
            "rotation_dir_ok": bool(align_diag["rotation_dir_ok"]),
            "hard_fail": bool(align_diag["hard_fail"]),
            "center_error_mean": float(center_error.mean()),
            "center_error_p95": float(np.quantile(center_error, 0.95)),
            "lens_error_deg_mean": float(lens_error_deg.mean()),
            "lens_error_deg_p95": float(np.quantile(lens_error_deg, 0.95)),
        }
        out.update(summarize_split_metrics(center_error, overlap_mask, "center_error"))
        out.update(summarize_split_metrics(lens_error_deg, overlap_mask, "lens_error_deg"))
        return out

    def select_route_candidate(chunk_name: str, candidate_rows: list[dict], requested_route_label: str) -> tuple[dict, bool]:
        by_label = {c["route_label"]: c for c in candidate_rows}
        requested = by_label.get(requested_route_label)
        preferred = by_label.get(PREFERRED_ROUTE_LABEL)
        baseline = by_label.get(ROUTE_ARCORE)
        if requested is not None and not requested["hard_fail"]:
            selected = requested
        elif preferred is not None and not preferred["hard_fail"]:
            selected = preferred
        elif baseline is not None and not baseline["hard_fail"]:
            selected = baseline
        elif requested is not None:
            selected = requested
        elif preferred is not None:
            selected = preferred
        elif baseline is not None:
            selected = baseline
        else:
            raise AssertionError({"chunk_name": chunk_name, "reason": "no route candidates"})
        fallback_used = bool(selected["route_label"] != requested_route_label)
        return selected, fallback_used

    global_camera_map = c2w_rows_to_map(global_camera_matrix_df)
    if "qc_blur_ok" not in input_manifest_df.columns:
        input_manifest_df["qc_blur_ok"] = False
    if "blur_score" not in input_manifest_df.columns:
        input_manifest_df["blur_score"] = 0.0
    global_frame_meta_df = global_anchor_df.merge(
        input_manifest_df[["record_index", "qc_blur_ok", "blur_score"]],
        on="record_index",
        how="left",
    )
    if "qc_blur_ok" not in global_frame_meta_df.columns:
        qc_blur_candidates = [c for c in ["qc_blur_ok_x", "qc_blur_ok_y"] if c in global_frame_meta_df.columns]
        if qc_blur_candidates:
            global_frame_meta_df["qc_blur_ok"] = global_frame_meta_df[qc_blur_candidates].bfill(axis=1).iloc[:, 0]
    if "blur_score" not in global_frame_meta_df.columns:
        blur_score_candidates = [c for c in ["blur_score_x", "blur_score_y"] if c in global_frame_meta_df.columns]
        if blur_score_candidates:
            global_frame_meta_df["blur_score"] = global_frame_meta_df[blur_score_candidates].bfill(axis=1).iloc[:, 0]
    global_frame_meta_df["lens_x"] = global_frame_meta_df["anchor_lens_x"].astype(float)
    global_frame_meta_df["lens_y"] = global_frame_meta_df["anchor_lens_y"].astype(float)
    global_frame_meta_df["lens_z"] = global_frame_meta_df["anchor_lens_z"].astype(float)
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
        candidate_axes = candidate_meta[["lens_x", "lens_y", "lens_z"]].to_numpy(dtype=np.float32).reshape(len(xyz_w), k, 3)
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
    experimental_world_pose_map = {}
    route_compare_rows = []
    previous_selected_chunk_name = None
    previous_selected_T = None

    for row in completed_chunks_df.itertuples(index=False):
        out_dir = chunk_runs_dir / row.chunk_name
        input_dir = resolve_chunk_input_dir(row.chunk_name)
        ply_path = input_dir / "gs_ply" / "0000.ply"
        pred_ext_path = input_dir / "pred_extrinsics.npy"
        chunk_input_path = input_dir / "chunk_input_frames.csv"
        glb_path = input_dir / "scene.glb"
        if not (ply_path.exists() and pred_ext_path.exists() and chunk_input_path.exists()):
            continue

        out_dir.mkdir(parents=True, exist_ok=True)

        chunk_df = pd.read_csv(chunk_input_path)
        pred_extrinsics = np.load(pred_ext_path)
        chunk_df.attrs["chunk_name"] = row.chunk_name
        assert chunk_df["record_index"].is_unique, f"duplicate record_index in chunk_input_frames: {row.chunk_name}"
        assert pred_extrinsics.shape[0] == len(chunk_df), {"chunk_name": row.chunk_name, "pred_len": int(pred_extrinsics.shape[0]), "chunk_len": int(len(chunk_df))}

        local_c2w_list = c2w_list_from_extrinsics(pred_extrinsics)

        merged = chunk_df.merge(
            global_anchor_df,
            on=["record_index", "image_file_name", "image_path", "frame_timestamp_ns", "capture_timestamp_ns"],
            how="left",
            validate="one_to_one",
        )
        assert len(merged) == len(chunk_df), {"chunk_name": row.chunk_name, "merged_len": len(merged), "chunk_len": len(chunk_df)}
        assert not merged[["cx_world", "cy_world", "cz_world", "anchor_lens_x", "anchor_lens_y", "anchor_lens_z", "anchor_up_x", "anchor_up_y", "anchor_up_z"]].isnull().any().any(), f"global anchor missing: {row.chunk_name}"
        global_c2w_list = [build_anchor_c2w(global_camera_map[int(rec.record_index)], rec) for rec in merged.itertuples(index=False)]

        prepose_solution = prepose_graph_solution_by_chunk.get(str(row.chunk_name))
        if prepose_solution is not None:
            requested_route_label = str(prepose_solution.get("requested_route_label", prepose_solution.get("route_label", PREFERRED_ROUTE_LABEL)))
            selected_candidate = dict(prepose_solution)
            fallback_used = bool(prepose_solution.get("fallback_used", False))
            preferred_fallback_used = bool(prepose_solution.get("preferred_fallback_used", False))
            graph_parent_chunk_name = prepose_solution.get("graph_parent_chunk_name")
            T_c_to_w0 = np.array(
                [float(prepose_solution[f"t{r}{c}"]) for r in range(4) for c in range(4)],
                dtype=np.float32,
            ).reshape(4, 4)
            align_diag = {
                "scale": float(prepose_solution["scale"]),
                "rotation_det": float(prepose_solution["rotation_det"]),
                "center_rmse": float(prepose_solution["center_rmse"]),
                "rotation_dir_residual": float(prepose_solution["rotation_dir_residual"]),
                "positive_similarity_ok": bool(prepose_solution["positive_similarity_ok"]),
                "scale_in_range_ok": bool(prepose_solution["scale_in_range_ok"]),
                "center_rmse_ok": bool(prepose_solution["center_rmse_ok"]),
                "rotation_dir_ok": bool(prepose_solution["rotation_dir_ok"]),
                "hard_fail": bool(prepose_solution.get("align_hard_fail", prepose_solution.get("hard_fail", False))),
            }
            selected_world_rows = transform_c2w_list(local_c2w_list, T_c_to_w0)
            route_compare_rows.append({
                "chunk_name": str(row.chunk_name),
                "graph_parent_chunk_name": graph_parent_chunk_name,
                "route_label": str(prepose_solution["route_label"]),
                "requested_route_label": requested_route_label,
                "preferred_route_label": PREFERRED_ROUTE_LABEL,
                "fallback_used": fallback_used,
                "preferred_fallback_used": preferred_fallback_used,
                "route_source": str(prepose_solution["route_source"]),
                "route_overlap_record_count": int(prepose_solution.get("route_overlap_record_count", 0)),
                "route_overlap_local_count": int(prepose_solution.get("route_overlap_local_count", 0)),
                "route_nonoverlap_local_count": int(prepose_solution.get("route_nonoverlap_local_count", 0)),
                "center_rmse": float(prepose_solution["center_rmse"]),
                "rotation_dir_residual": float(prepose_solution["rotation_dir_residual"]),
                "center_error_p95": float(prepose_solution["center_error_p95"]),
                "lens_error_deg_p95": float(prepose_solution["lens_error_deg_p95"]),
                "center_error_overlap_p95": prepose_solution.get("center_error_overlap_p95"),
                "center_error_nonoverlap_p95": prepose_solution.get("center_error_nonoverlap_p95"),
                "lens_error_deg_overlap_p95": prepose_solution.get("lens_error_deg_overlap_p95"),
                "lens_error_deg_nonoverlap_p95": prepose_solution.get("lens_error_deg_nonoverlap_p95"),
                "relative_scale": prepose_solution.get("relative_scale"),
                "relative_translation_norm": prepose_solution.get("relative_translation_norm"),
                "relative_rotation_deg": prepose_solution.get("relative_rotation_deg"),
                "selected_from_prepose_graph": True,
            })
        else:
            graph_parent_chunk_name = previous_selected_chunk_name
            baseline_T, baseline_diag = estimate_pose_aware_similarity(local_c2w_list, global_c2w_list, estimate_scale=True)
            baseline_world_rows = transform_c2w_list(local_c2w_list, baseline_T)
            baseline_candidate = summarize_route_candidate(
                row.chunk_name,
                ROUTE_ARCORE,
                "anchor_full_sequence",
                len(merged),
                merged["record_index"].astype(int).tolist(),
                baseline_world_rows,
                merged,
                baseline_diag,
            )
            route_compare_rows.append(baseline_candidate)

            overlap_local_rows = []
            overlap_world_rows = []
            overlap_record_indices = []
            for idx, record_index in enumerate(merged["record_index"].astype(int).tolist()):
                if record_index in experimental_world_pose_map:
                    overlap_local_rows.append(local_c2w_list[idx])
                    overlap_world_rows.append(experimental_world_pose_map[record_index])
                    overlap_record_indices.append(int(record_index))

            if overlap_world_rows:
                experimental_source = "predicted_overlap"
                experimental_overlap_record_count = len(overlap_world_rows)
                if len(overlap_world_rows) >= 2:
                    experimental_T, experimental_diag = estimate_pose_aware_similarity(overlap_local_rows, overlap_world_rows, estimate_scale=True)
                else:
                    experimental_T = baseline_T.copy()
                    experimental_diag = dict(baseline_diag)
                    experimental_source = "predicted_overlap_seeded_single_record"
            else:
                experimental_source = "seed_from_arcore_baseline"
                experimental_overlap_record_count = 0
                experimental_T = baseline_T.copy()
                experimental_diag = dict(baseline_diag)

            experimental_world_rows = transform_c2w_list(local_c2w_list, experimental_T)
            experimental_candidate = summarize_route_candidate(
                row.chunk_name,
                ROUTE_DA3,
                experimental_source,
                experimental_overlap_record_count,
                overlap_record_indices,
                experimental_world_rows,
                merged,
                experimental_diag,
            )
            route_compare_rows.append(experimental_candidate)

            requested_route_label = str(selected_route_by_chunk.get(row.chunk_name, PREFERRED_ROUTE_LABEL))
            selected_candidate, fallback_used = select_route_candidate(
                row.chunk_name,
                [baseline_candidate, experimental_candidate],
                requested_route_label,
            )
            preferred_fallback_used = bool(selected_candidate["route_label"] != PREFERRED_ROUTE_LABEL)
            selected_world_rows = experimental_world_rows if selected_candidate["route_label"] == ROUTE_DA3 else baseline_world_rows
            align_diag = experimental_diag if selected_candidate["route_label"] == ROUTE_DA3 else baseline_diag
            T_c_to_w0 = experimental_T if selected_candidate["route_label"] == ROUTE_DA3 else baseline_T

        for record_index, world_pose in zip(merged["record_index"].astype(int).tolist(), selected_world_rows):
            experimental_world_pose_map[int(record_index)] = world_pose

        relative_transform = summarize_relative_transform(previous_selected_T, T_c_to_w0)

        T_path = chunk_manifest_dir / f"{row.chunk_name}_to_w0.npy"
        np.save(T_path, T_c_to_w0)
        transform_rows.append({
            "chunk_name": row.chunk_name,
            "frame_count": int(len(chunk_df)),
            "transform_path": str(T_path),
            "graph_parent_chunk_name": graph_parent_chunk_name,
            "route_label": str(selected_candidate["route_label"]),
            "requested_route_label": requested_route_label,
            "preferred_route_label": PREFERRED_ROUTE_LABEL,
            "fallback_used": bool(fallback_used),
            "preferred_fallback_used": preferred_fallback_used,
            "route_source": str(selected_candidate["route_source"]),
            "route_overlap_record_count": int(selected_candidate["route_overlap_record_count"]),
            "route_overlap_local_count": int(selected_candidate.get("route_overlap_local_count", 0)),
            "route_nonoverlap_local_count": int(selected_candidate.get("route_nonoverlap_local_count", 0)),
            "local_extrinsic_mode": LOCAL_EXTRINSIC_MODE,
            "local_camera_basis": "perm_yxz_sign_ppn",
            "scale": float(align_diag["scale"]),
            "rotation_det": float(align_diag["rotation_det"]),
            "center_rmse": float(align_diag["center_rmse"]),
            "rotation_dir_residual": float(align_diag["rotation_dir_residual"]),
            "relative_scale": float(relative_transform["relative_scale"]),
            "relative_translation_norm": float(relative_transform["relative_translation_norm"]),
            "relative_rotation_deg": float(relative_transform["relative_rotation_deg"]),
            "positive_similarity_ok": bool(align_diag["positive_similarity_ok"]),
            "scale_in_range_ok": bool(align_diag["scale_in_range_ok"]),
            "center_rmse_ok": bool(align_diag["center_rmse_ok"]),
            "rotation_dir_ok": bool(align_diag["rotation_dir_ok"]),
            "hard_fail": bool(align_diag["hard_fail"]),
            "center_error_p95": float(selected_candidate["center_error_p95"]),
            "lens_error_deg_p95": float(selected_candidate["lens_error_deg_p95"]),
            "center_error_overlap_p95": selected_candidate.get("center_error_overlap_p95"),
            "center_error_nonoverlap_p95": selected_candidate.get("center_error_nonoverlap_p95"),
            "lens_error_deg_overlap_p95": selected_candidate.get("lens_error_deg_overlap_p95"),
            "lens_error_deg_nonoverlap_p95": selected_candidate.get("lens_error_deg_nonoverlap_p95"),
        })
        assert not align_diag["hard_fail"], {
            "chunk_name": row.chunk_name,
            "reason": "invalid_pose_similarity",
            "selected_route_label": selected_candidate["route_label"],
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
            "route_label": str(selected_candidate["route_label"]),
            "transform_warning": transform_warning,
            "keep_zero_chunk": keep_zero_chunk,
            "fallback_used": bool(fallback_used),
            "preferred_fallback_used": preferred_fallback_used,
        })
        keep_rows.append({
            "chunk_name": row.chunk_name,
            "route_label": str(selected_candidate["route_label"]),
            "requested_route_label": requested_route_label,
            "fallback_used": bool(fallback_used),
            "preferred_fallback_used": preferred_fallback_used,
            "kept_vertices": int(len(df)),
            "owner_record_unique_count": int(assignment_df["owner_record_index"].nunique()),
            "owner_candidate_mode": str(assignment_df["owner_candidate_mode"].iloc[0]),
            "owner_record_min": int(assignment_df["owner_record_index"].min()),
            "owner_record_max": int(assignment_df["owner_record_index"].max()),
            "owner_blur_ok_ratio": float(assignment_df["owner_blur_ok"].mean()),
            "owner_score_mean": float(assignment_df["owner_score"].mean()),
        })
        assert not keep_zero_chunk, {"chunk_name": row.chunk_name, "reason": "keep_zero_chunk"}
        previous_selected_chunk_name = str(row.chunk_name)
        previous_selected_T = T_c_to_w0.copy()

        if glb_path.exists():
            scene = load_scene_any(glb_path)
            for gname, geom in iter_baked_scene_geometry(scene):
                geom2 = geom.copy() if hasattr(geom, "copy") else geom
                if hasattr(geom2, "apply_transform"):
                    geom2.apply_transform(T_c_to_w0)
                master_scene.add_geometry(geom2, node_name=f"{row.chunk_name}_{gname}")

    transform_df = pd.DataFrame(transform_rows)
    transform_df.to_csv(chunk_manifest_dir / "chunk_global_transforms_arc.csv", index=False, encoding="utf-8")
    route_compare_df = pd.DataFrame(route_compare_rows)
    route_compare_path = merged_dir / "merge_route_compare_arc.csv"
    route_compare_df.to_csv(route_compare_path, index=False, encoding="utf-8")

    keep_df = pd.DataFrame(keep_rows)
    keep_summary_path = merged_dir / "chunk_keep_summary_arc.csv"
    keep_df.to_csv(keep_summary_path, index=False, encoding="utf-8")
    transform_quality_path = merged_dir / "chunk_transform_quality_arc.csv"
    transform_df.to_csv(transform_quality_path, index=False, encoding="utf-8")

    if owner_hist_rows:
        pd.concat(owner_hist_rows, ignore_index=True).to_csv(merged_dir / "owner_record_histogram_arc.csv", index=False, encoding="utf-8")
    if chunk_assign_rows:
        pd.concat(chunk_assign_rows, ignore_index=True).to_csv(merged_dir / "chunk_assignment_summary_arc.csv", index=False, encoding="utf-8")

    warning_summary = {
        "transform_warning_count": int(sum(bool(x["transform_warning"]) for x in warning_rows)),
        "keep_zero_chunk_count": int(sum(bool(x["keep_zero_chunk"]) for x in warning_rows)),
        "fallback_used_count": int(sum(bool(x["fallback_used"]) for x in warning_rows)),
        "preferred_fallback_used_count": int(sum(bool(x.get("preferred_fallback_used")) for x in warning_rows)),
        "rows": warning_rows,
    }
    (merged_dir / "merge_warning_summary_arc.json").write_text(json.dumps(warning_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    merged_ply_path = merged_dir / "merged_gs_arc.ply"
    if all_vertices:
        merged_vertices = np.concatenate(all_vertices, axis=0)
        PlyData([PlyElement.describe(merged_vertices, "vertex")], text=False).write(str(merged_ply_path))

    stage_11_2_copy_plan = [
        (merged_ply_path, stage_11_2_dir / "merged_gs_arc.ply"),
        (chunk_manifest_dir / "chunk_global_transforms_arc.csv", stage_11_2_dir / "chunk_global_transforms_arc.csv"),
        (route_compare_path, stage_11_2_dir / "merge_route_compare_arc.csv"),
        (keep_summary_path, stage_11_2_dir / "chunk_keep_summary_arc.csv"),
        (transform_quality_path, stage_11_2_dir / "chunk_transform_quality_arc.csv"),
        (merged_dir / "owner_record_histogram_arc.csv", stage_11_2_dir / "owner_record_histogram_arc.csv"),
        (merged_dir / "chunk_assignment_summary_arc.csv", stage_11_2_dir / "chunk_assignment_summary_arc.csv"),
        (merged_dir / "merge_warning_summary_arc.json", stage_11_2_dir / "merge_warning_summary_arc.json"),
        (merged_dir / "all_batch_summary_arc.json", stage_11_2_dir / "all_batch_summary_arc.json"),
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
        "all_chunk_count": int(len(target_chunks_df)),
        "stage_11_2_dir": str(stage_11_2_dir),
        "stage_11_2_files": stage_11_2_files,
        "merged_ply_path": str(merged_ply_path) if merged_ply_path.exists() else None,
    }
    (final_outputs_diagnostics_dir / "merge_resume_state.json").write_text(json.dumps(merge_resume_state, indent=2, ensure_ascii=False), encoding="utf-8")

    merged_glb_path = merged_dir / "merged_scene_arc.glb"
    if len(master_scene.geometry) > 0:
        master_scene.export(str(merged_glb_path))

    for src in stage_11_2_dir.glob("*"):
        if src.is_file():
            shutil.copy2(src, stage_11_3_dir / src.name)
    if merged_glb_path.exists():
        shutil.copy2(merged_glb_path, stage_11_3_dir / "merged_scene_arc.glb")
    merge_resume_state.update({
        "stage": "11-3-complete",
        "stage_11_3_dir": str(stage_11_3_dir),
        "merged_glb_path": str(merged_glb_path) if merged_glb_path.exists() else None,
    })
    (final_outputs_diagnostics_dir / "merge_resume_state.json").write_text(json.dumps(merge_resume_state, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(final_outputs_diagnostics_dir / "merge_resume_state.json", stage_11_3_dir / "merge_resume_state.json")

    final_output_copy_plan = [
        (merged_ply_path, final_outputs_merged_dir / "merged_gs_arc.ply"),
        (merged_glb_path, final_outputs_merged_dir / "merged_scene_arc.glb"),
        (chunk_manifest_dir / "chunk_global_transforms_arc.csv", final_outputs_diagnostics_dir / "chunk_global_transforms_arc.csv"),
        (route_compare_path, final_outputs_diagnostics_dir / "merge_route_compare_arc.csv"),
        (keep_summary_path, final_outputs_diagnostics_dir / "chunk_keep_summary_arc.csv"),
        (transform_quality_path, final_outputs_diagnostics_dir / "chunk_transform_quality_arc.csv"),
        (merged_dir / "owner_record_histogram_arc.csv", final_outputs_diagnostics_dir / "owner_record_histogram_arc.csv"),
        (merged_dir / "chunk_assignment_summary_arc.csv", final_outputs_diagnostics_dir / "chunk_assignment_summary_arc.csv"),
        (merged_dir / "merge_warning_summary_arc.json", final_outputs_diagnostics_dir / "merge_warning_summary_arc.json"),
        (merged_dir / "all_batch_summary_arc.json", final_outputs_diagnostics_dir / "all_batch_summary_arc.json"),
        (input_manifest_path, final_outputs_manifests_dir / "da3_input_manifest.csv"),
        (anchor_dir / "camera_center_matrix_arc.csv", final_outputs_manifests_dir / "camera_center_matrix_arc.csv"),
        (anchor_dir / "camera_matrix_full_arc.csv", final_outputs_manifests_dir / "camera_matrix_full_arc.csv"),
        (anchor_dir / "camera_anchor_full_arc.csv", final_outputs_manifests_dir / "camera_anchor_full_arc.csv"),
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
        "status": "drive_only",
        "reason": "drive_outputs_ready_local_bundle_is_separate_stage",
    }

    if MAKE_DRIVE_BUNDLE:
        bundle_summary = {
            "status": "drive_only",
            "drive_visible_dir": str(probe_root),
            "drive_pipeline_root": str(pipeline_root),
            "drive_results_root": str(results_root),
            "local_bundle_stage": "#11-1",
            "download_requested": False,
        }

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
    (final_outputs_dir / "final_output_manifest_arc.json").write_text(json.dumps(final_output_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    if not all_vertices and not INFER_GS:
        merge_reason = "infer_gs_disabled"
    elif not all_vertices and len(ply_ready_target_chunk_names) == 0:
        merge_reason = "gaussian_chunk_outputs_missing"
    else:
        merge_reason = None if all_vertices else "no kept vertices"

    selected_route_counts = (
        transform_df.groupby("route_label", as_index=False).size().rename(columns={"size": "chunk_count"}).to_dict(orient="records")
        if len(transform_df)
        else []
    )
    fallback_used_count = int(transform_df["fallback_used"].fillna(False).astype(bool).sum()) if len(transform_df) else 0
    preferred_fallback_used_count = int(transform_df["preferred_fallback_used"].fillna(False).astype(bool).sum()) if len(transform_df) else 0

    merge_summary = {
        "route": "continuous-gs-v06-chunk18-overlap6-adopt12-merge",
        "status": "ok" if all_vertices else "skipped",
        "reason": merge_reason,
        "completed_chunk_count": int(len(completed_chunks_df)),
        "pred_ready_chunk_count": int(len(pred_ready_target_chunk_names)),
        "ply_ready_chunk_count": int(len(ply_ready_target_chunk_names)),
        "all_chunk_count": int(len(target_chunks_df)),
        "infer_gs": bool(INFER_GS),
        "merged_ply_path": str(merged_ply_path) if merged_ply_path.exists() else None,
        "merged_glb_path": str(merged_glb_path) if merged_glb_path.exists() else None,
        "chunk_global_transforms_path": str(chunk_manifest_dir / "chunk_global_transforms_arc.csv"),
        "merge_route_compare_path": str(route_compare_path),
        "prepose_chunk_graph_solution_path": str(prepose_chunk_graph_solution_path) if prepose_chunk_graph_solution_path.exists() else None,
        "prepose_chunk_graph_edges_path": str(prepose_chunk_graph_edges_path) if prepose_chunk_graph_edges_path.exists() else None,
        "prepose_chunk_graph_summary_path": str(prepose_chunk_graph_summary_path) if prepose_chunk_graph_summary_path.exists() else None,
        "chunk_keep_summary_path": str(keep_summary_path),
        "chunk_transform_quality_path": str(transform_quality_path),
        "owner_record_histogram_path": str(merged_dir / "owner_record_histogram_arc.csv"),
        "chunk_assignment_summary_path": str(merged_dir / "chunk_assignment_summary_arc.csv"),
        "merge_warning_summary_path": str(merged_dir / "merge_warning_summary_arc.json"),
        "all_batch_summary_path": str(merged_dir / "all_batch_summary_arc.json"),
        "preferred_route_label": PREFERRED_ROUTE_LABEL,
        "selected_route_counts": selected_route_counts,
        "fallback_used_count": fallback_used_count,
        "preferred_fallback_used_count": preferred_fallback_used_count,
        "final_outputs_dir": str(final_outputs_dir),
        "final_output_manifest_path": str(final_outputs_dir / "final_output_manifest_arc.json"),
        "bundle_summary": bundle_summary,
    }
    (merged_dir / "merge_summary.json").write_text(json.dumps(merge_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(merged_dir / "merge_summary.json", final_outputs_diagnostics_dir / "merge_summary.json")
    print(json.dumps(merge_summary, indent=2, ensure_ascii=False))
    display_stage_summary(
        "14-1",
        "merge",
        inputs=[
            {"item": "batch_execution_items", "path": str(batch_execution_items_path)},
            {"item": "camera_anchor_full", "path": str(anchor_dir / "camera_anchor_full_arc.csv")},
            {"item": "da3_input_manifest", "path": str(input_manifest_path)},
        ],
        outputs=[
            {"item": "merge_summary", "path": str(merged_dir / "merge_summary.json")},
            {"item": "merged_gs", "path": str(merged_ply_path)},
            {"item": "merged_scene_glb", "path": str(merged_glb_path)},
            {"item": "final_output_manifest", "path": str(final_outputs_dir / "final_output_manifest_arc.json")},
            {"item": "chunk_global_transforms", "path": str(chunk_manifest_dir / "chunk_global_transforms_arc.csv")},
            {"item": "merge_route_compare", "path": str(route_compare_path)},
            {"item": "chunk_keep_summary", "path": str(keep_summary_path)},
            {"item": "chunk_transform_quality", "path": str(transform_quality_path)},
        ],
        notes=[
            {"item": "completed_chunk_count", "value": int(len(completed_chunks_df))},
            {"item": "status", "value": merge_summary["status"]},
            {"item": "fallback_used_count", "value": fallback_used_count},
            {"item": "preferred_fallback_used_count", "value": preferred_fallback_used_count},
        ],
    )
