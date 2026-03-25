from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PRODUCT_ROOT = ROOT / "--products" / "prj-reviework"
PYTHON_ROOT = PRODUCT_ROOT / "python"

sys.path.insert(0, str(PYTHON_ROOT))

from review_contracts import build_stage_handoff_contracts


class RevieworkProjectContractsTest(unittest.TestCase):
    def test_project_files_do_not_reference_other_projects(self) -> None:
        project_dirs = [
            ROOT / "--plans" / "prj-reviework",
            ROOT / "--products" / "prj-reviework",
            ROOT / "--project-truth" / "prj-reviework",
            ROOT / "--state" / "prj-reviework",
            ROOT / "--testcode" / "prj-reviework",
        ]
        allowed = {"prj-reviework"}
        forbidden_hits: list[str] = []

        for directory in project_dirs:
            for path in directory.rglob("*"):
                if path.is_dir() or "__pycache__" in path.parts or ".gradle" in path.parts:
                    continue
                if path.suffix in {".pyc", ".lock", ".jar"}:
                    continue
                text = path.read_text(encoding="utf-8")
                for token in set(part for part in text.split() if part.startswith("prj-")):
                    normalized = token.strip("`'\",:()[]{}")
                    if normalized.startswith("prj-") and normalized not in allowed:
                        forbidden_hits.append(f"{path}: {normalized}")

        self.assertEqual([], forbidden_hits)

    def test_output_routing_uses_exsams_and_testlogs(self) -> None:
        build_file = (PRODUCT_ROOT / "build.gradle.kts").read_text(encoding="utf-8")
        app_build_file = (PRODUCT_ROOT / "app" / "build.gradle.kts").read_text(encoding="utf-8")
        android_script = (PRODUCT_ROOT / "scripts" / "run_android_unit_tests.ps1").read_text(encoding="utf-8")
        python_script = (PRODUCT_ROOT / "scripts" / "run_python_tests.ps1").read_text(encoding="utf-8")

        self.assertIn("--exsams/prj-reviework", build_file)
        self.assertNotIn("--trial-data", build_file)
        self.assertIn("--testlogs/prj-reviework", app_build_file)
        self.assertIn("--exsams/prj-reviework", app_build_file)
        self.assertNotIn("--trial-data", app_build_file)
        self.assertIn("--testlogs\\prj-reviework", android_script)
        self.assertIn("--exsams\\prj-reviework", android_script)
        self.assertNotIn("--trial-data", android_script)
        self.assertIn("--testlogs\\prj-reviework", python_script)
        self.assertIn("--exsams\\prj-reviework", python_script)
        self.assertNotIn("--trial-data", python_script)

    def test_stage_handoff_contract_covers_all_four_stages(self) -> None:
        contracts = build_stage_handoff_contracts()
        project_truth = (ROOT / "--project-truth" / "prj-reviework" / "project-truth.md").read_text(encoding="utf-8")

        self.assertEqual(
            ["InputPackaging", "SpaceReconstruction", "TrajectoryReconstruction", "AssemblyAndViewer"],
            [contract.stage_name for contract in contracts],
        )
        for contract in contracts:
            self.assertTrue(contract.input_contracts)
            self.assertTrue(contract.output_contracts)
            self.assertTrue(contract.handoff_conditions)
            self.assertIn(contract.stage_name, project_truth)
            for output_name in contract.output_contracts:
                self.assertIn(output_name, project_truth)


if __name__ == "__main__":
    unittest.main()
