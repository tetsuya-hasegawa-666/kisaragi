from __future__ import annotations

import importlib.util
import json
import py_compile
import re
import subprocess
import sys
import unittest
from pathlib import Path

DB_ROOT = Path(__file__).resolve().parents[3]
DEVS_ROOT = DB_ROOT / "--devs"
COLAB_DIR = DEVS_ROOT / "--products" / "prj-kisaragi_0002" / "colab"
SOURCE_DIR = COLAB_DIR / "da3_increpose_sources"
MANIFEST_PATH = SOURCE_DIR / "cell_manifest.json"
MARKDOWN_MANIFEST_PATH = SOURCE_DIR / "markdown_manifest.json"
RUNBOOK_MD = COLAB_DIR / "da3_ngl_increpose_RB.md"
RUNBOOK_IPYNB = COLAB_DIR / "da3_ngl_increpose_RB.ipynb"
AGENTS_PATH = COLAB_DIR / "agents.md"
HAUB_PATH = DEVS_ROOT / "--tgpce-map" / "prj-kisaragi_0002" / "hi-ai-unified-blueprint.md"
PROJECT_TRUTH_PATH = DEVS_ROOT / "--tgpce-map" / "prj-kisaragi_0002" / "project-truth.md"
RESUME_PATH = DEVS_ROOT / "--tgpce-map" / "prj-kisaragi_0002" / "resume-startup-plan.md"
DESIGN_CONTRACT_PATH = COLAB_DIR / "da3_ngl_runbook_design_contract.md"
SYNC_SCRIPT = SOURCE_DIR / "sync_da3_increpose_sources.py"
INVENTORY_SCRIPT = SOURCE_DIR / "build_increpose_inventory.py"
INVENTORY_PATH = COLAB_DIR / "da3_ngl_increpose_source_inventory.md"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class Da3IncreposeSourcesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sync = load_module(SYNC_SCRIPT, "da3_increpose_sync")
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.markdown_manifest = json.loads(MARKDOWN_MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.notebook = json.loads(RUNBOOK_IPYNB.read_text(encoding="utf-8"))
        cls.markdown = RUNBOOK_MD.read_text(encoding="utf-8")
        cls.inventory = INVENTORY_PATH.read_text(encoding="utf-8") if INVENTORY_PATH.exists() else ""
        cls.agents = AGENTS_PATH.read_text(encoding="utf-8")
        cls.haub = HAUB_PATH.read_text(encoding="utf-8")
        cls.project_truth = PROJECT_TRUTH_PATH.read_text(encoding="utf-8")
        cls.resume = RESUME_PATH.read_text(encoding="utf-8")
        cls.contract = DESIGN_CONTRACT_PATH.read_text(encoding="utf-8")

    def test_manifest_covers_notebook_cells(self) -> None:
        notebook_tokens = []
        markdown_count = 0
        for cell in self.notebook["cells"]:
            if cell.get("cell_type") == "markdown":
                markdown_count += 1
                continue
            if cell.get("cell_type") != "code":
                continue
            src = "".join(cell.get("source", []))
            stripped = src.lstrip()
            if stripped.startswith("#"):
                notebook_tokens.append(stripped.splitlines()[0].strip())
        self.assertEqual([entry["token"] for entry in self.manifest], notebook_tokens)
        self.assertEqual(markdown_count, len(self.markdown_manifest))

    def test_markdown_and_code_sources_match_pair(self) -> None:
        markdown_cells = [cell for cell in self.notebook["cells"] if cell.get("cell_type") == "markdown"]
        self.assertEqual(len(markdown_cells), len(self.markdown_manifest))
        for entry, cell in zip(self.markdown_manifest, markdown_cells):
            source = (SOURCE_DIR / entry["source_file"]).read_text(encoding="utf-8")
            actual = "".join(cell.get("source", []))
            self.assertEqual(source.replace("\r\n", "\n"), actual.replace("\r\n", "\n"), entry["leading_token"])
            self.assertIn(source.strip(), self.markdown)
        for entry in self.manifest:
            source = (SOURCE_DIR / entry["source_file"]).read_text(encoding="utf-8")
            cell = self.sync.find_code_cell(self.notebook, entry["token"])
            actual = "".join(cell.get("source", []))
            self.assertEqual(source.replace("\r\n", "\n"), actual.replace("\r\n", "\n"), entry["token"])
            self.assertRegex(self.markdown, rf"```python\n{re.escape(source.rstrip())}\n```")

    def test_incremental_pose_contract_is_explicit(self) -> None:
        config_source = (SOURCE_DIR / "cells" / "02_01.py").read_text(encoding="utf-8")
        chunk_build_source = (SOURCE_DIR / "cells" / "08_03.py").read_text(encoding="utf-8")
        precheck_source = (SOURCE_DIR / "cells" / "08_04.py").read_text(encoding="utf-8")
        target_resolve_source = (SOURCE_DIR / "cells" / "08_05.py").read_text(encoding="utf-8")
        exec_source = (SOURCE_DIR / "cells" / "08_09.py").read_text(encoding="utf-8")
        graph_source = (SOURCE_DIR / "cells" / "10_01.py").read_text(encoding="utf-8")
        merge_source = (SOURCE_DIR / "cells" / "11_01.py").read_text(encoding="utf-8")
        self.assertIn('"POSE_PIPELINE_MODE": "sliding_window_incremental_seeded"', config_source)
        self.assertIn('"CONTEXT_SIZE": 12', config_source)
        self.assertIn('"OUTPUT_SIZE": 6', config_source)
        self.assertIn('"OVERLAP_SIZE": 12', config_source)
        self.assertIn('"SEED_USE_PREV_POSE": True', config_source)
        self.assertIn('chunk_csv_path = chunk_manifest_dir / f"{chunk_name}.csv"', chunk_build_source)
        self.assertIn('chunk_index_all_path = chunk_manifest_dir / "chunk_index_all.csv"', chunk_build_source)
        self.assertIn('batch_work_dir = chunk_runs_dir / batch_name', chunk_build_source)
        self.assertIn('chunk_out_dir = batch_work_dir / chunk_name', chunk_build_source)
        self.assertIn('batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"', precheck_source)
        self.assertIn('chunk_input_manifest_path = chunk_manifest_dir / "chunk_input_manifest_arc.csv"', precheck_source)
        self.assertIn('source_label = "batch_execution_items"', precheck_source)
        self.assertIn("def build_target_chunk_and_batch_plan():", target_resolve_source)
        self.assertIn('batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"', target_resolve_source)
        self.assertIn('fallback_chunk_target_path = chunk_manifest_dir / "chunk_index_target.csv"', target_resolve_source)
        self.assertIn('fallback_batch_plan_path = chunk_manifest_dir / "batch_plan.csv"', target_resolve_source)
        self.assertIn('if batch_work_dir.name == chunk_name:', exec_source)
        self.assertIn('if "chunk_out_dir" in item_row.index', exec_source)
        self.assertIn('out_dir = batch_work_dir / chunk_name', exec_source)
        self.assertIn('runtime_dir = out_dir / "_runtime"', exec_source)
        self.assertIn('"batch_work_dir": str(batch_work_dir)', exec_source)
        self.assertIn('"out_dir": str(out_dir)', exec_source)
        self.assertIn("def apply_incremental_seed_to_chunk_df(", exec_source)
        self.assertIn("def update_accepted_pose_map_from_chunk(", exec_source)
        self.assertIn("seed_pose_by_record_index: dict[int, np.ndarray] = {}", exec_source)
        self.assertIn('seed_trace_path = final_outputs_diagnostics_dir / "incremental_seed_trace_arc.csv"', exec_source)
        self.assertIn('"route": "sliding_window_incremental_seeded"', exec_source)
        self.assertIn("run_status_path = final_outputs_diagnostics_dir / \"batch_run_status_arc.csv\"", graph_source)
        self.assertIn("seed_trace_path = final_outputs_diagnostics_dir / \"incremental_seed_trace_arc.csv\"", graph_source)
        self.assertIn('if batch_work_dir.name == chunk_name:', graph_source)
        self.assertIn('if "chunk_out_dir" in item_row.index', graph_source)
        self.assertIn("graph_solution_csv = merged_dir / \"prepose_chunk_graph_solution_arc.csv\"", graph_source)
        self.assertIn("identity_transform_csv = chunk_manifest_dir / \"chunk_global_transforms_arc.csv\"", graph_source)
        self.assertIn("merged_camera_pose_csv", merge_source)
        self.assertIn("ngl_extrinsics_path", merge_source)

    def test_docs_reference_increpose_canonical_pair(self) -> None:
        self.assertIn("da3_ngl_increpose_RB", self.agents)
        self.assertIn("da3_increpose_sources/", self.agents)
        self.assertIn("da3_ngl_increpose_RB", self.haub)
        self.assertIn("da3_ngl_increpose_source_inventory.md", self.haub)
        self.assertIn("da3_ngl_increpose_RB", self.project_truth)
        self.assertIn("da3_ngl_increpose_RB", self.resume)
        self.assertIn("da3_ngl_increpose_RB", self.contract)
        self.assertIn("incremental predicted chunk route", self.haub)
        self.assertIn("sliding_window_incremental_seeded", self.haub)
        self.assertIn("### Increpose Path Handoff Matrix", self.haub)
        self.assertIn("PATH-I10", self.haub)
        self.assertIn("pipeline_root/chunk_runs/<batch_name>/<chunk_name>/pred_extrinsics.npy", self.haub)
        self.assertIn("## Function And Class Inventory", self.inventory)
        self.assertIn("## Variable Inventory", self.inventory)
        for entry in self.manifest:
            self.assertIn(entry["docs_id"], self.inventory)

    def test_sync_inventory_and_sources_compile(self) -> None:
        subprocess.run([sys.executable, str(SYNC_SCRIPT)], check=True, cwd=DB_ROOT.parent)
        subprocess.run([sys.executable, str(INVENTORY_SCRIPT)], check=True, cwd=DB_ROOT.parent)
        self.assertTrue(RUNBOOK_MD.exists())
        self.assertTrue(RUNBOOK_IPYNB.exists())
        self.assertTrue(INVENTORY_PATH.exists())
        for entry in self.manifest:
            py_compile.compile(str(SOURCE_DIR / entry["source_file"]), doraise=True)


if __name__ == "__main__":
    unittest.main()
