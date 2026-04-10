from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

DB_ROOT = Path(__file__).resolve().parents[3]
DEVS_ROOT = DB_ROOT / "--devs"
COLAB_DIR = DEVS_ROOT / "--products" / "prj-kisaragi_0002" / "colab"
SOURCE_DIR = COLAB_DIR / "da3_optpose_sources"
MANIFEST_PATH = SOURCE_DIR / "cell_manifest.json"
MARKDOWN_MANIFEST_PATH = SOURCE_DIR / "markdown_manifest.json"
RUNBOOK_MD = COLAB_DIR / "da3_ngl_optpose_RB.md"
RUNBOOK_IPYNB = COLAB_DIR / "da3_ngl_optpose_RB.ipynb"
AGENTS_PATH = COLAB_DIR / "agents.md"
HAUB_PATH = DEVS_ROOT / "--tgpce-map" / "prj-kisaragi_0002" / "hi-ai-unified-blueprint.md"
SYNC_SCRIPT = SOURCE_DIR / "sync_da3_optpose_sources.py"
INVENTORY_SCRIPT = SOURCE_DIR / "build_optpose_inventory.py"
INVENTORY_PATH = COLAB_DIR / "da3_ngl_optpose_source_inventory.md"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class Da3OptposeSourcesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sync = load_module(SYNC_SCRIPT, "da3_optpose_sync")
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.markdown_manifest = json.loads(MARKDOWN_MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.notebook = json.loads(RUNBOOK_IPYNB.read_text(encoding="utf-8"))
        cls.markdown = RUNBOOK_MD.read_text(encoding="utf-8")
        cls.agents = AGENTS_PATH.read_text(encoding="utf-8")
        cls.haub = HAUB_PATH.read_text(encoding="utf-8")
        cls.inventory = INVENTORY_PATH.read_text(encoding="utf-8")

    def test_manifest_covers_all_tokenized_code_cells(self) -> None:
        notebook_tokens = []
        notebook_markdown_cells = 0
        for cell in self.notebook["cells"]:
            if cell.get("cell_type") == "markdown":
                notebook_markdown_cells += 1
                continue
            if cell.get("cell_type") != "code":
                continue
            src = "".join(cell.get("source", []))
            stripped = src.lstrip()
            if stripped.startswith("#"):
                notebook_tokens.append(stripped.splitlines()[0].strip())
        self.assertEqual([entry["token"] for entry in self.manifest], notebook_tokens)
        self.assertEqual(notebook_markdown_cells, len(self.markdown_manifest))

    def test_markdown_cells_match_manifest(self) -> None:
        markdown_cells = [cell for cell in self.notebook["cells"] if cell.get("cell_type") == "markdown"]
        self.assertEqual(len(markdown_cells), len(self.markdown_manifest))
        for entry, cell in zip(self.markdown_manifest, markdown_cells):
            source = (SOURCE_DIR / entry["source_file"]).read_text(encoding="utf-8")
            actual = "".join(cell.get("source", []))
            self.assertEqual(source.replace("\r\n", "\n"), actual.replace("\r\n", "\n"), entry["leading_token"])
            self.assertTrue(source.startswith(f"#No: {entry['target_ref']}"))
            self.assertIn(f"前: {entry['prev_ref']}", source)
            self.assertIn(f"次: {entry['next_ref']}", source)

    def test_pair_matches_manifest_sources(self) -> None:
        for entry in self.manifest:
            source = (SOURCE_DIR / entry["source_file"]).read_text(encoding="utf-8")
            cell = self.sync.find_code_cell(self.notebook, entry["token"])
            actual = "".join(cell.get("source", []))
            self.assertEqual(source.replace("\r\n", "\n"), actual.replace("\r\n", "\n"), entry["token"])
            block = re.search(rf"```python\n{re.escape(source.rstrip())}\n```", self.markdown, re.S)
            self.assertIsNotNone(block, entry["token"])

    def test_shared_helpers_are_split_and_reused(self) -> None:
        helper_source = (SOURCE_DIR / "cells" / "06_02.py").read_text(encoding="utf-8")
        path_source = (SOURCE_DIR / "cells" / "03_01.py").read_text(encoding="utf-8")
        tree_init_source = (SOURCE_DIR / "cells" / "04_01.py").read_text(encoding="utf-8")
        managed_source = (SOURCE_DIR / "cells" / "04_02.py").read_text(encoding="utf-8")
        matching_source = (SOURCE_DIR / "cells" / "09_01.py").read_text(encoding="utf-8")
        graph_source = (SOURCE_DIR / "cells" / "10_01.py").read_text(encoding="utf-8")
        review_source = (SOURCE_DIR / "cells" / "11_02.py").read_text(encoding="utf-8")
        self.assertIn("def estimate_pose_aware_similarity(", helper_source)
        self.assertIn("def transform_c2w_list(", helper_source)
        self.assertNotIn("def estimate_pose_aware_similarity(", matching_source)
        self.assertNotIn("def estimate_pose_aware_similarity(", graph_source)
        self.assertNotIn("def to_4x4_batch(", review_source)
        self.assertIn("estimate_pose_aware_similarity(", matching_source)
        self.assertIn("estimate_pose_aware_similarity(", graph_source)
        self.assertIn("to_4x4_batch(", review_source)
        self.assertIn("from scipy.optimize import least_squares", graph_source)
        self.assertIn("from scipy.spatial.transform import Rotation as SciRot", graph_source)
        self.assertIn("GRAPH_ANCHOR_FRAME_TRANSLATION_WEIGHT", graph_source)
        self.assertIn("GRAPH_ANCHOR_NONOVERLAP_FRAME_WEIGHT", graph_source)
        self.assertIn("graph_node_measurements", graph_source)
        self.assertIn("def recompute_solution_metrics(", graph_source)
        self.assertIn("validation_df = graph_solution_df.copy()", graph_source)
        self.assertIn('and not preferred_anchor_warning', graph_source)
        self.assertIn("def _py_bool(value) -> bool:", review_source)
        self.assertIn("showlegend=_py_bool(i == sample_idx[0])", review_source)
        self.assertIn('tree_schema_version = "2.0.0"', path_source)
        self.assertIn('run_root = validation_runs_dir / run_id', path_source)
        self.assertIn('compatibility_aliases = {', path_source)
        self.assertIn('def ensure_tree_pointer(pointer_path: Path, target_path: Path)', tree_init_source)
        self.assertIn('root_manifest.json', tree_init_source)
        self.assertNotIn('legacy_source_pipeline_slug', tree_init_source)
        self.assertIn("'managed_dirs': {k: str(v) for k, v in managed_dirs.items()}", managed_source)
        self.assertIn("managed_dirs = {\n    '02_records':", managed_source)

    def test_docs_reference_optpose_pair(self) -> None:
        self.assertIn("da3_ngl_optpose_RB.md", self.agents)
        self.assertIn("da3_optpose_sources/", self.agents)
        self.assertIn("da3_ngl_optpose_RB.md", self.haub)
        self.assertIn("da3_ngl_optpose_source_inventory.md", self.haub)
        self.assertIn("## Function And Class Inventory", self.inventory)
        self.assertIn("## Variable Inventory", self.inventory)
        for entry in self.manifest:
            self.assertIn(entry["docs_id"], self.inventory)

    def test_sync_and_inventory_scripts_run(self) -> None:
        subprocess.run([sys.executable, str(SYNC_SCRIPT)], check=True, cwd=DB_ROOT.parent)
        subprocess.run([sys.executable, str(INVENTORY_SCRIPT)], check=True, cwd=DB_ROOT.parent)
        self.assertTrue(RUNBOOK_MD.exists())
        self.assertTrue(RUNBOOK_IPYNB.exists())
        self.assertTrue(INVENTORY_PATH.exists())


if __name__ == "__main__":
    unittest.main()
