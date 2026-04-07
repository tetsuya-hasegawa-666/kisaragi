import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

REPO_ROOT = Path("/content/Depth-Anything-3")
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from depth_anything_3.api import DepthAnything3


def _resolve_device(device_arg: str) -> str:
    if device_arg and device_arg != "auto":
        return device_arg
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _pick_pred_array(prediction, attr_names):
    for name in attr_names:
        if hasattr(prediction, name):
            v = getattr(prediction, name)
            if v is None:
                continue
            try:
                arr = np.asarray(v)
                return arr
            except Exception:
                pass
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk-csv", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--model-id", required=True)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--process-res", type=int, default=504)
    ap.add_argument("--process-res-method", default="upper_bound_resize")
    ap.add_argument("--export-format", default="mini_npz")
    ap.add_argument("--infer-gs", action="store_true")
    ap.add_argument("--align-to-input-ext-scale", action="store_true")
    ap.add_argument("--show-cameras", action="store_true")
    ap.add_argument("--conf-thresh-percentile", type=float, default=40.0)
    ap.add_argument("--num-max-points", type=int, default=1_000_000)
    args = ap.parse_args()

    chunk_csv = Path(args.chunk_csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(chunk_csv)
    assert len(df) >= 2, {"chunk_csv": str(chunk_csv), "reason": "need at least 2 frames"}

    required_cols = ["image_path", "fx_canonical", "fy_canonical", "cx_canonical", "cy_canonical"]
    missing = [c for c in required_cols if c not in df.columns]
    assert not missing, {"chunk_csv": str(chunk_csv), "missing_required_columns": missing}

    image_paths = df["image_path"].astype(str).tolist()
    missing_images = [p for p in image_paths if not Path(p).exists()]
    assert not missing_images, {"missing_images_count": len(missing_images), "sample": missing_images[:10]}

    if not {"tx", "ty", "tz", "qx", "qy", "qz", "qw"}.issubset(df.columns):
        raise AssertionError({"reason": "pose quaternion/translation columns missing", "columns": df.columns.tolist()})

    # notebook側で既に extrinsics_w2c_arc.npy を整備している想定だが、
    # chunk csv だけからも走れるように tx/ty/tz + qx/qy/qz/qw からは再構成しない。
    # 代わりに chunk csv に extrinsics 参照列が無い場合は、w2c は使わず image-only API にフォールバックする。
    use_pose_conditioning = False
    extrinsics = None

    if {"w2c_00","w2c_01","w2c_02","w2c_03","w2c_10","w2c_11","w2c_12","w2c_13","w2c_20","w2c_21","w2c_22","w2c_23","w2c_30","w2c_31","w2c_32","w2c_33"}.issubset(df.columns):
        mats = []
        for r in df.itertuples(index=False):
            M = np.array([
                [r.w2c_00, r.w2c_01, r.w2c_02, r.w2c_03],
                [r.w2c_10, r.w2c_11, r.w2c_12, r.w2c_13],
                [r.w2c_20, r.w2c_21, r.w2c_22, r.w2c_23],
                [r.w2c_30, r.w2c_31, r.w2c_32, r.w2c_33],
            ], dtype=np.float32)
            mats.append(M)
        extrinsics = np.stack(mats, axis=0)
        use_pose_conditioning = True
    elif {"extrinsics_path", "chunk_local_index"}.issubset(df.columns):
        # 予備: 外部npyへの参照があればそれを使えるようにする余地
        pass

    intrinsics = []
    for r in df.itertuples(index=False):
        K = np.array([
            [float(r.fx_canonical), 0.0, float(r.cx_canonical)],
            [0.0, float(r.fy_canonical), float(r.cy_canonical)],
            [0.0, 0.0, 1.0],
        ], dtype=np.float32)
        intrinsics.append(K)
    intrinsics = np.stack(intrinsics, axis=0)

    device = _resolve_device(args.device)
    model = DepthAnything3.from_pretrained(args.model_id)
    model = model.to(device)

    inference_kwargs = dict(
        image=image_paths,
        intrinsics=intrinsics,
        process_res=args.process_res,
        process_res_method=args.process_res_method,
        export_dir=str(out_dir),
        export_format=args.export_format,
        conf_thresh_percentile=args.conf_thresh_percentile,
        num_max_points=args.num_max_points,
        show_cameras=bool(args.show_cameras),
    )

    if use_pose_conditioning:
        inference_kwargs["extrinsics"] = extrinsics
        inference_kwargs["align_to_input_ext_scale"] = bool(args.align_to_input_ext_scale)

    if args.infer_gs:
        inference_kwargs["infer_gs"] = True

    prediction = model.inference(**inference_kwargs)

    # pred_extrinsics / pred_intrinsics を後段互換で保存
    pred_ext = _pick_pred_array(prediction, ["extrinsics", "pred_extrinsics", "camera_extrinsics"])
    pred_ixt = _pick_pred_array(prediction, ["intrinsics", "pred_intrinsics", "camera_intrinsics"])

    # API docs によれば align_to_input_ext_scale=True の場合、返る extrinsics は入力 extrinsics に置換される。
    # 後段互換のため、pose conditioning時に pred_ext が拾えなければ入力 extrinsics を保存する。
    if pred_ext is None and extrinsics is not None:
        pred_ext = extrinsics
    if pred_ixt is None:
        pred_ixt = intrinsics

    if pred_ext is not None:
        np.save(out_dir / "pred_extrinsics.npy", np.asarray(pred_ext, dtype=np.float32))
    if pred_ixt is not None:
        np.save(out_dir / "pred_intrinsics.npy", np.asarray(pred_ixt, dtype=np.float32))

    df.to_csv(out_dir / "chunk_input_frames.csv", index=False, encoding="utf-8")

    summary = {
        "status": "ok",
        "chunk_csv": str(chunk_csv),
        "out_dir": str(out_dir),
        "model_id": args.model_id,
        "device": device,
        "frame_count": int(len(df)),
        "use_pose_conditioning": bool(use_pose_conditioning),
        "align_to_input_ext_scale": bool(args.align_to_input_ext_scale),
        "infer_gs": bool(args.infer_gs),
        "pred_extrinsics_saved": bool((out_dir / "pred_extrinsics.npy").exists()),
        "pred_intrinsics_saved": bool((out_dir / "pred_intrinsics.npy").exists()),
    }
    (out_dir / "_SUCCESS.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
