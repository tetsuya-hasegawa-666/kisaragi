from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent.parent
        / "--products"
        / "prj-kisaragi_0002"
        / "python"
    ),
)

from modeling_colab_tool import build_notebook, import_results


class ModelingColabToolTest(unittest.TestCase):
    def test_build_notebook_writes_colab_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            job_request = root / "colab_job_request.json"
            selected_route = root / "selected_route.json"
            output_dir = root / "colab"

            job_request.write_text(
                json.dumps(
                    {
                        "sessionId": "session-colab",
                        "defaultRouteId": "route-colmap40-global-splatfacto",
                        "requiredUploadArtifacts": ["video.mp4", "session_package.json"],
                        "resultArtifacts": ["benchmark_summary.json", "space_quality.json"],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            selected_route.write_text(
                json.dumps(
                    {
                        "selectedRouteId": "route-colmap40-global-splatfacto",
                        "selectedRoute": {"mapper": "global"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            written = build_notebook(job_request, selected_route, output_dir)

            notebook_path = output_dir / "trajectreview_colmap4_splatfacto_colab.ipynb"
            upload_manifest_path = output_dir / "upload_manifest.json"
            self.assertEqual([notebook_path, upload_manifest_path], written)
            notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
            notebook_text = json.dumps(notebook, ensure_ascii=False)
            self.assertIn("session_root", notebook_text)
            self.assertIn("global_mapper", notebook_text)
            self.assertIn("missing inputs", notebook_text)
            self.assertIn("ns-train", notebook_text)
            self.assertIn("splatfacto", notebook_text)
            upload_manifest = json.loads(upload_manifest_path.read_text(encoding="utf-8"))
            self.assertIn("recommendedSessionRoot", upload_manifest)

    def test_import_results_writes_reviewing_handoff_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            remote_dir = root / "remote"
            output_dir = root / "imported"
            remote_dir.mkdir()
            (remote_dir / "remote_summary.json").write_text(
                json.dumps(
                    {
                        "sessionId": "session-colab",
                        "routeId": "route-colmap40-global-splatfacto",
                        "status": "completed",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (remote_dir / "route_metrics.json").write_text(
                json.dumps(
                    {
                        "spaceQuality": "0.88",
                        "trajectoryQuality": "0.74",
                        "registeredImageRatio": 0.91,
                        "reprojectionErrorPx": 0.63,
                        "workerPathCount": 2,
                        "attentionPoints": [{"timeRange": "00:12-00:20", "reason": "worker-02 の橋渡し区間"}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            written = import_results(remote_dir, output_dir)

            self.assertEqual(4, len(written))
            handoff = json.loads((output_dir / "modeling_handoff_manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(handoff["readyForReviewing"])
            self.assertEqual("route-colmap40-global-splatfacto", handoff["selectedRouteId"])


if __name__ == "__main__":
    unittest.main()
