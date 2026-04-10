from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROBE_PATH = Path(__file__).resolve().parent / "da3_increpose_path_contract_probe.py"


class Da3IncreposePathContractProbeTest(unittest.TestCase):
    def test_probe_reports_no_haub_contract_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "da3_increpose_path_contract_report.json"
            subprocess.run(
                [sys.executable, str(PROBE_PATH), "--report-json", str(report_path)],
                check=True,
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual([], report["critical_rule_failures"])
        self.assertEqual([], report["haub_contract_failures"])
        self.assertGreaterEqual(report["haub_handoff_contract_count"], 10)

        critical = report["critical_artifacts"]
        for key in [
            "batch_execution_items.csv",
            "chunk_index_all.csv",
            "chunk_index_target.csv",
            "batch_plan.csv",
            "execution_target_chunks.csv",
            "execution_target_batch_plan.csv",
            "batch_run_status_arc.csv",
            "incremental_seed_trace_arc.csv",
            "pred_extrinsics.npy",
            "chunk_input_frames.csv",
            "premerge_pose_validation.json",
            "prepose_chunk_graph_solution_arc.csv",
            "chunk_global_transforms_arc.csv",
        ]:
            self.assertIn(key, critical)
            self.assertTrue(
                critical[key]["writes"] or critical[key]["reads"],
                key,
            )

        self.assertTrue(critical["pred_extrinsics.npy"]["writes"])
        self.assertTrue(critical["pred_extrinsics.npy"]["reads"])
        self.assertTrue(critical["chunk_input_frames.csv"]["writes"])
        self.assertTrue(critical["chunk_input_frames.csv"]["reads"])


if __name__ == "__main__":
    unittest.main()
