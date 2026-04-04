from __future__ import annotations

import argparse
import csv
import itertools
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


def to_4x4(ext: np.ndarray) -> np.ndarray:
    ext = np.asarray(ext, dtype=np.float64)
    if ext.shape == (4, 4):
        return ext
    if ext.shape == (3, 4):
        out = np.eye(4, dtype=np.float64)
        out[:3, :] = ext
        return out
    raise ValueError(f"unexpected extrinsic shape: {ext.shape}")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv_rows(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def c2w_rows_to_map(rows: list[dict[str, str]]) -> dict[int, np.ndarray]:
    cols = [f"m{i}{j}" for i in range(4) for j in range(4)]
    out: dict[int, np.ndarray] = {}
    for row in rows:
        out[int(row["record_index"])] = np.array([float(row[c]) for c in cols], dtype=np.float64).reshape(4, 4)
    return out


def estimate_pose_aware_similarity(local_c2w_list: list[np.ndarray], global_c2w_list: list[np.ndarray], estimate_scale: bool = True):
    assert len(local_c2w_list) == len(global_c2w_list) >= 2

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

    h = dst_dirs.T @ src_dirs
    u, _, vt = np.linalg.svd(h)
    s = np.eye(3, dtype=np.float64)
    if np.linalg.det(u) * np.linalg.det(vt) < 0:
        s[-1, -1] = -1.0
    r = u @ s @ vt

    src_mean = src_centers.mean(axis=0)
    dst_mean = dst_centers.mean(axis=0)
    src_c = src_centers - src_mean
    dst_c = dst_centers - dst_mean
    src_rot = (r @ src_c.T).T

    if estimate_scale:
        denom = float(np.sum(src_rot ** 2))
        numer = float(np.sum(dst_c * src_rot))
        scale = numer / max(denom, 1e-12)
    else:
        scale = 1.0

    t = dst_mean - scale * (r @ src_mean)
    pred = (scale * (r @ src_centers.T)).T + t
    center_rmse = float(np.sqrt(np.mean(np.sum((pred - dst_centers) ** 2, axis=1))))
    rot_residual = float(np.mean(np.linalg.norm((r @ src_dirs.T).T - dst_dirs, axis=1)))

    transform = np.eye(4, dtype=np.float64)
    transform[:3, :3] = scale * r
    transform[:3, 3] = t
    return transform, {
        "scale": float(scale),
        "rotation_det": float(np.linalg.det(r)),
        "center_rmse": center_rmse,
        "rotation_dir_residual": rot_residual,
    }


def build_basis_variant_map() -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    axes = ("x", "y", "z")
    for perm in itertools.permutations(range(3)):
        perm_name = "".join(axes[i] for i in perm)
        for signs in itertools.product((-1.0, 1.0), repeat=3):
            sign_name = "".join("n" if s < 0 else "p" for s in signs)
            name = f"perm_{perm_name}_sign_{sign_name}"
            f = np.eye(4, dtype=np.float64)
            f[:3, :3] = 0.0
            for row, col in enumerate(perm):
                f[row, col] = signs[row]
            out[name] = f
    return out


VARIANT_MAP = build_basis_variant_map()


def variant_matrix(name: str) -> np.ndarray:
    return VARIANT_MAP[name]


def candidate_names() -> Iterable[str]:
    return VARIANT_MAP.keys()


def basis_meaning(name: str) -> str:
    parts = name.split("_")
    perm = parts[1]
    signs = parts[3]
    axes = []
    for i, axis in enumerate(perm):
        sign = "+" if signs[i] == "p" else "-"
        axes.append(f"{sign}{axis}")
    return f"x'={axes[0]}, y'={axes[1]}, z'={axes[2]}"


def stars(value: int) -> str:
    return "★" * value + "☆" * (5 - value)


def score_scale(scale: float) -> int:
    if scale <= 0:
        return 0
    delta = abs(scale - 1.0)
    if delta < 0.10:
        return 5
    if delta < 0.20:
        return 4
    if delta < 0.35:
        return 3
    if delta < 0.60:
        return 2
    return 1


def score_center(center_rmse: float) -> int:
    if center_rmse < 0.01:
        return 5
    if center_rmse < 0.03:
        return 4
    if center_rmse < 0.07:
        return 3
    if center_rmse < 0.15:
        return 2
    if center_rmse < 0.25:
        return 1
    return 0


def score_rotation(rot_residual: float) -> int:
    if rot_residual < 0.01:
        return 5
    if rot_residual < 0.03:
        return 4
    if rot_residual < 0.07:
        return 3
    if rot_residual < 0.12:
        return 2
    if rot_residual < 0.20:
        return 1
    return 0


@dataclass
class ProbeResult:
    rank: int
    interpretation: str
    axis_variant: str
    basis_meaning: str
    positive_scale: bool
    scale: float
    rotation_det: float
    center_rmse: float
    rotation_dir_residual: float
    scale_star: str
    center_star: str
    rotation_star: str
    total_star: int


def build_local_c2w_list(pred_extrinsics: np.ndarray, interpretation: str, axis_variant: str) -> list[np.ndarray]:
    mats = []
    flip = variant_matrix(axis_variant)
    for ext in pred_extrinsics:
        ext44 = to_4x4(ext)
        if interpretation == "w2c":
            c2w = np.linalg.inv(ext44)
        elif interpretation == "c2w":
            c2w = ext44
        else:
            raise ValueError(f"unsupported interpretation: {interpretation}")
        mats.append(c2w @ flip)
    return mats


def sort_key(row: ProbeResult):
    return (0 if row.positive_scale else 1, -row.total_star, row.center_rmse, row.rotation_dir_residual, abs(row.scale - 1.0))


def build_probe_result(interpretation: str, axis_variant: str, diag: dict[str, float]) -> ProbeResult:
    s_scale = score_scale(diag["scale"])
    s_center = score_center(diag["center_rmse"])
    s_rot = score_rotation(diag["rotation_dir_residual"])
    return ProbeResult(
        rank=0,
        interpretation=interpretation,
        axis_variant=axis_variant,
        basis_meaning=basis_meaning(axis_variant),
        positive_scale=diag["scale"] > 0.0,
        scale=diag["scale"],
        rotation_det=diag["rotation_det"],
        center_rmse=diag["center_rmse"],
        rotation_dir_residual=diag["rotation_dir_residual"],
        scale_star=stars(s_scale),
        center_star=stars(s_center),
        rotation_star=stars(s_rot),
        total_star=s_scale + s_center + s_rot,
    )


def write_chunk_markdown(path: Path, chunk_name: str, chunk_summary: dict, top_rows: list[ProbeResult]) -> None:
    lines = [
        f"# {chunk_name} pose star table",
        "",
        "## 96候補になる理由",
        "",
        "- interpretation が `2` 通りある。",
        "  - `w2c` とみなす場合",
        "  - `c2w` とみなす場合",
        "- camera basis 候補が `48` 通りある。",
        "  - 軸 permutation `6` 通り",
        "  - 各軸の符号 `2^3 = 8` 通り",
        "- 合計は `2 x 48 = 96` 候補である。",
        "",
        "## 判定メモ",
        "",
        f"- current runbook 相当: `{chunk_summary['current_runbook_candidate']['interpretation']} / {chunk_summary['current_runbook_candidate']['axis_variant']}`",
        f"- best balanced: `{chunk_summary['best_balanced_rot_lt_0_2']['interpretation']} / {chunk_summary['best_balanced_rot_lt_0_2']['axis_variant']}`" if chunk_summary["best_balanced_rot_lt_0_2"] else "- best balanced: なし",
        f"- best by rotation: `{chunk_summary['best_by_rotation']['interpretation']} / {chunk_summary['best_by_rotation']['axis_variant']}`",
        "",
        "## 星取表",
        "",
        "| rank | interpretation | axis_variant | basis | scale | center_rmse | rot_residual | scale | center | rotation | total |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in top_rows:
        lines.append(
            f"| {row.rank} | `{row.interpretation}` | `{row.axis_variant}` | `{row.basis_meaning}` | {row.scale:.6f} | {row.center_rmse:.6f} | {row.rotation_dir_residual:.6f} | {row.scale_star} | {row.center_star} | {row.rotation_star} | {row.total_star} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--chunk-name", default="")
    args = parser.parse_args()

    session_root = args.session_root
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    run_root = session_root / "continuous_gs_v06_chunk18_overlap6_adopt12"
    chunk_runs_dir = run_root / "chunk_runs"
    manifests_dir = run_root / "manifests"
    global_pose_dir = run_root / "global_pose_bootstrap"

    global_camera_map = c2w_rows_to_map(read_csv_rows(global_pose_dir / "camera_matrix_full.csv"))
    chunk_index_rows = read_csv_rows(manifests_dir / "chunk_index_all.csv")
    target_chunk_names = [args.chunk_name] if args.chunk_name else [row["chunk_name"] for row in chunk_index_rows]

    aggregate_rows: list[dict] = []
    aggregate_best_keys: dict[str, int] = {}

    for chunk_name in target_chunk_names:
        chunk_dir = chunk_runs_dir / chunk_name
        pred_extrinsics = np.load(chunk_dir / "pred_extrinsics.npy")
        chunk_frames_rows = read_csv_rows(chunk_dir / "chunk_input_frames.csv")
        global_c2w_list = [global_camera_map[int(row["record_index"])] for row in chunk_frames_rows]

        results: list[ProbeResult] = []
        transforms: dict[str, list[list[float]]] = {}

        for interpretation in ("w2c", "c2w"):
            for axis_variant in candidate_names():
                local_c2w_list = build_local_c2w_list(pred_extrinsics, interpretation, axis_variant)
                transform, diag = estimate_pose_aware_similarity(local_c2w_list, global_c2w_list, estimate_scale=True)
                key = f"{interpretation}:{axis_variant}"
                transforms[key] = transform.tolist()
                results.append(build_probe_result(interpretation, axis_variant, diag))

        results = sorted(results, key=sort_key)
        for i, row in enumerate(results, start=1):
            row.rank = i

        best_center = next((row for row in results if row.positive_scale), None)
        best_rotation = min((row for row in results if row.positive_scale), key=lambda r: (r.rotation_dir_residual, r.center_rmse))
        balanced_pool = [row for row in results if row.positive_scale and row.rotation_dir_residual < 0.2]
        best_balanced = min(balanced_pool, key=lambda r: (-r.total_star, r.center_rmse, r.rotation_dir_residual)) if balanced_pool else None
        current_runbook_candidate = next(row for row in results if row.interpretation == "w2c" and row.axis_variant == "perm_xyz_sign_ppp")

        summary = {
            "chunk_name": chunk_name,
            "session_root": str(session_root),
            "chunk_dir": str(chunk_dir),
            "camera_matrix_full_csv": str(global_pose_dir / "camera_matrix_full.csv"),
            "chunk_input_frames_csv": str(chunk_dir / "chunk_input_frames.csv"),
            "pred_extrinsics_npy": str(chunk_dir / "pred_extrinsics.npy"),
            "candidate_count": len(results),
            "best_by_center_rmse": asdict(best_center) if best_center else None,
            "best_by_rotation": asdict(best_rotation),
            "best_balanced_rot_lt_0_2": asdict(best_balanced) if best_balanced else None,
            "current_runbook_candidate": asdict(current_runbook_candidate),
            "all_candidates_csv": str(output_dir / f"{chunk_name}_pose_candidates.csv"),
            "summary_json": str(output_dir / f"{chunk_name}_pose_summary.json"),
            "transform_json": str(output_dir / f"{chunk_name}_pose_transforms.json"),
            "summary_md": str(output_dir / f"{chunk_name}_pose_star.md"),
        }

        write_csv_rows(
            output_dir / f"{chunk_name}_pose_candidates.csv",
            [asdict(row) for row in results],
            ["rank", "interpretation", "axis_variant", "basis_meaning", "positive_scale", "scale", "rotation_det", "center_rmse", "rotation_dir_residual", "scale_star", "center_star", "rotation_star", "total_star"],
        )
        (output_dir / f"{chunk_name}_pose_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        (output_dir / f"{chunk_name}_pose_transforms.json").write_text(json.dumps(transforms, indent=2, ensure_ascii=False), encoding="utf-8")
        top_rows = results[:12]
        if all(row.axis_variant != current_runbook_candidate.axis_variant or row.interpretation != current_runbook_candidate.interpretation for row in top_rows):
            top_rows = top_rows + [current_runbook_candidate]
        write_chunk_markdown(output_dir / f"{chunk_name}_pose_star.md", chunk_name, summary, top_rows)

        chosen = best_balanced or best_rotation
        chosen_key = f"{chosen.interpretation}:{chosen.axis_variant}"
        aggregate_best_keys[chosen_key] = aggregate_best_keys.get(chosen_key, 0) + 1
        aggregate_rows.append({
            "chunk_name": chunk_name,
            "frame_count": len(chunk_frames_rows),
            "chosen_interpretation": chosen.interpretation,
            "chosen_axis_variant": chosen.axis_variant,
            "chosen_basis_meaning": chosen.basis_meaning,
            "chosen_scale": chosen.scale,
            "chosen_center_rmse": chosen.center_rmse,
            "chosen_rotation_dir_residual": chosen.rotation_dir_residual,
            "runbook_scale": current_runbook_candidate.scale,
            "runbook_center_rmse": current_runbook_candidate.center_rmse,
            "runbook_rotation_dir_residual": current_runbook_candidate.rotation_dir_residual,
        })

    aggregate_rows.sort(key=lambda r: r["chunk_name"])
    write_csv_rows(
        output_dir / "all_chunks_pose_probe_summary.csv",
        aggregate_rows,
        ["chunk_name", "frame_count", "chosen_interpretation", "chosen_axis_variant", "chosen_basis_meaning", "chosen_scale", "chosen_center_rmse", "chosen_rotation_dir_residual", "runbook_scale", "runbook_center_rmse", "runbook_rotation_dir_residual"],
    )

    trend_rows = sorted(
        [{"key": key, "count": count} for key, count in aggregate_best_keys.items()],
        key=lambda r: (-r["count"], r["key"]),
    )
    write_csv_rows(output_dir / "all_chunks_pose_probe_trend.csv", trend_rows, ["key", "count"])

    trend_lines = [
        "# all chunks pose probe",
        "",
        "- source session root: `" + str(session_root) + "`",
        "- tested chunks: `" + str(len(aggregate_rows)) + "`",
        "- candidate count per chunk: `96 = 2 interpretations x 6 permutations x 8 sign flips`",
        "",
        "## chosen trend",
        "",
        "| key | count |",
        "| --- | --- |",
    ]
    for row in trend_rows:
        trend_lines.append(f"| `{row['key']}` | {row['count']} |")
    trend_lines.extend(
        [
            "",
            "## chunk summary",
            "",
            "| chunk | chosen | basis | scale | center_rmse | rot_residual | runbook scale | runbook center | runbook rot |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in aggregate_rows:
        trend_lines.append(
            f"| `{row['chunk_name']}` | `{row['chosen_interpretation']} / {row['chosen_axis_variant']}` | `{row['chosen_basis_meaning']}` | {row['chosen_scale']:.6f} | {row['chosen_center_rmse']:.6f} | {row['chosen_rotation_dir_residual']:.6f} | {row['runbook_scale']:.6f} | {row['runbook_center_rmse']:.6f} | {row['runbook_rotation_dir_residual']:.6f} |"
        )
    (output_dir / "all_chunks_pose_probe.md").write_text("\n".join(trend_lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "tested_chunks": len(aggregate_rows),
        "output_dir": str(output_dir),
        "summary_csv": str(output_dir / "all_chunks_pose_probe_summary.csv"),
        "trend_csv": str(output_dir / "all_chunks_pose_probe_trend.csv"),
        "summary_md": str(output_dir / "all_chunks_pose_probe.md"),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
