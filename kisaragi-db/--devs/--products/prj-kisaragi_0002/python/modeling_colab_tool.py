from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_notebook_document(job_request: dict[str, Any], selected_route: dict[str, Any]) -> dict[str, Any]:
    selected = selected_route["selectedRoute"]
    route_id = selected_route["selectedRouteId"]
    session_id = job_request["sessionId"]
    notebook_cells = [
        markdown_cell(
            "# trajectreview modeling notebook\n"
            "この notebook は `DA3NESTED-GIANT-LARGE-1.1` の official API / CLI 基準で、sequence-anchor first の modeling を行う。"
        ),
        code_cell(
            "CONFIG = {\n"
            f"    'session_root': '/content/drive/MyDrive/trajectreview/input/{session_id}',\n"
            "    'work_root': '/content/trajectreview',\n"
            "    'result_root': '/content/drive/MyDrive/trajectreview/results',\n"
            "}\n"
            "CONFIG"
        ),
        code_cell(
            "from google.colab import drive\n"
            "drive.mount('/content/drive')"
        ),
        code_cell(
            "from pathlib import Path\n"
            "import json\n"
            "\n"
            "session_root = Path(CONFIG['session_root'])\n"
            "session_package = json.loads((session_root / 'session_package.json').read_text(encoding='utf-8'))\n"
            "camera_calibration = json.loads((session_root / 'camera_calibration_summary.json').read_text(encoding='utf-8'))\n"
            "session_id = session_package['sessionId']\n"
            "selected_route_path = session_root / 'selected_route.json'\n"
            "job_request_path = session_root / 'colab_job_request.json'\n"
            f"route_id = '{route_id}'\n"
            f"sampling_profile = '{selected['samplingProfile']}'\n"
            f"intrinsics_mode = '{selected['intrinsicsMode']}'\n"
            "if selected_route_path.exists():\n"
            "    selected_route = json.loads(selected_route_path.read_text(encoding='utf-8'))\n"
            "    route_id = selected_route.get('selectedRouteId', route_id)\n"
            "    selected_payload = selected_route.get('selectedRoute', {})\n"
            "    sampling_profile = selected_payload.get('samplingProfile', sampling_profile)\n"
            "    intrinsics_mode = selected_payload.get('intrinsicsMode', intrinsics_mode)\n"
            "elif job_request_path.exists():\n"
            "    job_request = json.loads(job_request_path.read_text(encoding='utf-8'))\n"
            "    route_id = job_request.get('defaultRouteId', route_id)\n"
            "images_source = session_root / 'trajectreview' / 'image'\n"
            "required = [\n"
            "    session_root / 'video.mp4',\n"
            "    session_root / 'session_package.json',\n"
            "    session_root / 'frame_pose_index.csv',\n"
            "    session_root / 'camera_calibration_summary.json',\n"
            "    session_root / 'sensor_quality.json',\n"
            "    session_root / 'space_handoff_manifest.json',\n"
            "    images_source,\n"
            "]\n"
            "missing = [str(path) for path in required if not path.exists()]\n"
            "if missing:\n"
            "    raise FileNotFoundError(f'missing inputs: {missing}')\n"
            "camera_calibration.get('imageIntrinsicsCoverageRatio'), camera_calibration.get('lensDistortionCoverageRatio')\n"
            "session_root, session_id, route_id, sampling_profile, intrinsics_mode"
        ),
        code_cell(
            "import subprocess\n"
            "\n"
            "def run(cmd: list[str]) -> None:\n"
            "    print('RUN', ' '.join(cmd))\n"
            "    subprocess.run(cmd, check=True)\n"
            "\n"
            "run(['bash', '-lc', 'apt-get update'])\n"
            "run(['bash', '-lc', 'apt-get install -y ffmpeg git'])\n"
            "run(['python', '-m', 'pip', 'install', '--upgrade', 'pip'])\n"
            "run(['git', 'clone', 'https://github.com/ByteDance-Seed/depth-anything-3.git'])\n"
            "run(['python', '-m', 'pip', 'install', '-e', './depth-anything-3'])"
        ),
        code_cell(
            "from pathlib import Path\n"
            "work_root = Path(CONFIG['work_root'])\n"
            "images_dir = work_root / 'image'\n"
            "da3_export_dir = work_root / 'da3_output'\n"
            "export_dir = Path(CONFIG['result_root']) / session_id / route_id\n"
            "for directory in [work_root, images_dir, da3_export_dir, export_dir]:\n"
            "    directory.mkdir(parents=True, exist_ok=True)"
        ),
        code_cell(
            "import shutil\n"
            "for image_path in images_source.iterdir():\n"
            "    if image_path.is_file():\n"
            "        shutil.copy2(image_path, images_dir / image_path.name)\n"
            "print({'copied_images': len(list(images_dir.iterdir()))})"
        ),
        code_cell(
            "stride = 2 if sampling_profile == '5fps' else 1\n"
            "sampled_dir = work_root / 'sampled_images'\n"
            "sampled_dir.mkdir(parents=True, exist_ok=True)\n"
            "for index, image_path in enumerate(sorted(images_dir.iterdir())):\n"
            "    if image_path.is_file() and index % stride == 0:\n"
            "        shutil.copy2(image_path, sampled_dir / image_path.name)\n"
            "print({'sampled_images': len(list(sampled_dir.iterdir())), 'sampling_profile': sampling_profile})"
        ),
        code_cell(
            "run([\n"
            "    'da3', 'auto', str(sampled_dir),\n"
            "    '--export-format', 'ply',\n"
            "    '--export-dir', str(da3_export_dir),\n"
            "    '--model-dir', 'depth-anything/DA3NESTED-GIANT-LARGE-1.1',\n"
        "])"
        ),
        code_cell(
            "summary = {\n"
            "    'sessionId': session_id,\n"
            "    'routeId': route_id,\n"
            "    'samplingProfile': sampling_profile,\n"
            "    'intrinsicsMode': intrinsics_mode,\n"
            "    'status': 'completed',\n"
            "}\n"
            "(export_dir / 'remote_summary.json').write_text(__import__('json').dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')"
        ),
    ]
    return {
        "cells": notebook_cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.10",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def markdown_cell(text: str) -> dict[str, Any]:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code_cell(text: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


def build_notebook(job_request_path: Path, selected_route_path: Path, output_dir: Path) -> list[Path]:
    ensure_directory(output_dir)
    job_request = load_json(job_request_path)
    selected_route = load_json(selected_route_path)
    notebook = build_notebook_document(job_request, selected_route)
    notebook_path = output_dir / "trajectreview_da3nested_giant_large_colab.ipynb"
    upload_manifest_path = output_dir / "upload_manifest.json"
    notebook_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8")
    upload_manifest = {
        "sessionId": job_request["sessionId"],
        "recommendedSessionRoot": f"/content/drive/MyDrive/trajectreview/input/{job_request['sessionId']}",
        "defaultRouteId": job_request["defaultRouteId"],
        "requiredUploadArtifacts": job_request["requiredUploadArtifacts"],
        "resultArtifacts": job_request["resultArtifacts"],
    }
    upload_manifest_path.write_text(json.dumps(upload_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return [notebook_path, upload_manifest_path]


def import_results(remote_dir: Path, output_dir: Path) -> list[Path]:
    ensure_directory(output_dir)
    summary = load_json(remote_dir / "remote_summary.json")
    route_metrics = load_json(remote_dir / "route_metrics.json")
    written: list[Path] = []
    outputs = {
        "space_quality.json": {
            "sessionId": summary["sessionId"],
            "routeId": summary["routeId"],
            "spaceQuality": route_metrics["spaceQuality"],
            "registeredImageRatio": route_metrics["registeredImageRatio"],
            "reprojectionErrorPx": route_metrics["reprojectionErrorPx"],
        },
        "trajectory_quality.json": {
            "sessionId": summary["sessionId"],
            "routeId": summary["routeId"],
            "trajectoryQuality": route_metrics["trajectoryQuality"],
            "workerPathCount": route_metrics.get("workerPathCount", 1),
        },
        "attention_seed.json": {
            "sessionId": summary["sessionId"],
            "routeId": summary["routeId"],
            "attentionPoints": route_metrics.get("attentionPoints", []),
        },
        "modeling_handoff_manifest.json": {
            "sessionId": summary["sessionId"],
            "selectedRouteId": summary["routeId"],
            "readyForReviewing": summary["status"] == "completed",
            "nextAction": "reviewing app で実 ReviewArtifact を開く" if summary["status"] == "completed" else "modeling route を再実行する",
        },
    }
    for filename, payload in outputs.items():
        path = output_dir / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build-notebook")
    build_parser.add_argument("--job-request", type=Path, required=True)
    build_parser.add_argument("--selected-route", type=Path, required=True)
    build_parser.add_argument("--output", type=Path, required=True)

    import_parser = subparsers.add_parser("import-results")
    import_parser.add_argument("--remote-dir", type=Path, required=True)
    import_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "build-notebook":
        written = build_notebook(args.job_request, args.selected_route, args.output)
    else:
        written = import_results(args.remote_dir, args.output)

    print(json.dumps({"written": [str(path) for path in written]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
