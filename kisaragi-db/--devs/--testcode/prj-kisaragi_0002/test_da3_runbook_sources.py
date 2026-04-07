from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

VENDOR_PYTHON = Path(__file__).resolve().parents[4] / "_vendor" / "python"
if VENDOR_PYTHON.exists():
    sys.path.insert(0, str(VENDOR_PYTHON))

import numpy as np

DB_ROOT = Path(__file__).resolve().parents[3]
DEVS_ROOT = DB_ROOT / "--devs"
COLAB_DIR = DEVS_ROOT / "--products" / "prj-kisaragi_0002" / "colab"
SOURCE_DIR = COLAB_DIR / "da3_runbook_sources"
MANIFEST_PATH = SOURCE_DIR / "cell_manifest.json"
MARKDOWN_MANIFEST_PATH = SOURCE_DIR / "markdown_manifest.json"
RUNBOOK_MD = COLAB_DIR / "da3_ngl_runbook.md"
RUNBOOK_IPYNB = COLAB_DIR / "da3_ngl_runbook.ipynb"
HAUB_PATH = DEVS_ROOT / "--tgpce-map" / "prj-kisaragi_0002" / "hi-ai-unified-blueprint.md"
DESIGN_CONTRACT_PATH = COLAB_DIR / "da3_ngl_runbook_design_contract.md"
SYNC_SCRIPT = SOURCE_DIR / "sync_da3_runbook_sources.py"
INVENTORY_SCRIPT = SOURCE_DIR / "build_inventory.py"
INVENTORY_PATH = COLAB_DIR / "da3_ngl_runbook_source_inventory.md"
SHARED_HELPERS = SOURCE_DIR / "cells" / "06_shared_helpers.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class Da3RunbookSourcesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sync = load_module(SYNC_SCRIPT, "da3_sync")
        cls.shared = load_module(SHARED_HELPERS, "da3_shared_helpers")
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.markdown_manifest = json.loads(MARKDOWN_MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.notebook = json.loads(RUNBOOK_IPYNB.read_text(encoding="utf-8"))
        cls.markdown = RUNBOOK_MD.read_text(encoding="utf-8")
        cls.haub = HAUB_PATH.read_text(encoding="utf-8")
        cls.contract = DESIGN_CONTRACT_PATH.read_text(encoding="utf-8")
        cls.inventory = INVENTORY_PATH.read_text(encoding="utf-8") if INVENTORY_PATH.exists() else ""

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
        self.assertEqual(sorted(notebook_tokens), sorted(entry["token"] for entry in self.manifest))
        self.assertEqual(notebook_markdown_cells, len(self.markdown_manifest))

    def test_markdown_cells_match_markdown_manifest(self) -> None:
        markdown_cells = [cell for cell in self.notebook["cells"] if cell.get("cell_type") == "markdown"]
        self.assertEqual(len(markdown_cells), len(self.markdown_manifest))
        for entry, cell in zip(self.markdown_manifest, markdown_cells):
            source = (SOURCE_DIR / entry["source_file"]).read_text(encoding="utf-8")
            actual = "".join(cell.get("source", []))
            self.assertEqual(source.replace("\r\n", "\n"), actual.replace("\r\n", "\n"), entry["leading_token"])
            self.assertTrue(source.startswith(f"#No: {entry['target_ref']}"))
            self.assertIn(f"前: {entry['prev_ref']}", source)
            self.assertIn(f"次: {entry['next_ref']}", source)
            self.assertIn(source.strip(), self.markdown)

    def test_pair_matches_manifest_sources(self) -> None:
        for entry in self.manifest:
            source = (SOURCE_DIR / entry["source_file"]).read_text(encoding="utf-8")
            expected = (
                self.sync.render_wrapper_cell(entry["token"], source)
                if entry["kind"] == "wrapper_body"
                else source
            )
            cell = self.sync.find_code_cell(self.notebook, entry["token"])
            actual = "".join(cell.get("source", []))
            self.assertEqual(expected.replace("\r\n", "\n"), actual.replace("\r\n", "\n"), entry["token"])

            pattern = re.compile(rf"```python\n[ \t]*{re.escape(entry['token'])}.*?```", re.S)
            match = pattern.search(self.markdown)
            self.assertIsNotNone(match, entry["token"])
            self.assertEqual(
                f"```python\n{expected.rstrip()}\n```",
                match.group(0).replace("\r\n", "\n"),
                entry["token"],
            )

    def test_docs_ids_are_tracked_in_docs(self) -> None:
        self.assertIn("cell_manifest.json", self.contract)
        self.assertIn("da3_ngl_runbook_source_inventory.md", self.contract)
        self.assertIn("## Function And Class Inventory", self.inventory)
        self.assertIn("## Variable Inventory", self.inventory)
        for entry in self.manifest:
            docs_id = entry["docs_id"]
            self.assertIn(docs_id, self.haub, docs_id)
            self.assertIn(docs_id, self.inventory, docs_id)

    def test_wrapper_markdown_preserves_backslash_sequences(self) -> None:
        pattern = re.compile(r"```python\n[ \t]*#12-2.*?```", re.S)
        match = pattern.search(self.markdown)
        self.assertIsNotNone(match, "#12-2")
        block = match.group(0)
        self.assertIn('lstrip("\\n")', block)

    def test_shared_helpers_basics(self) -> None:
        self.assertTrue(hasattr(self.shared, "load_ctx"))
        self.assertTrue(hasattr(self.shared, "save_json"))
        self.assertTrue(hasattr(self.shared, "append_sequence_columns"))
        self.assertTrue(hasattr(self.shared, "display_stage_summary"))

        df = self.shared.append_sequence_columns(
            self.shared.pd.DataFrame(
                [
                    {"frame_timestamp_ns": 30, "value": "c"},
                    {"frame_timestamp_ns": 10, "value": "a"},
                    {"frame_timestamp_ns": 20, "value": "b"},
                ]
            ),
            "frame_timestamp_ns",
        )
        self.assertEqual([0, 1, 2], df["sequence_index"].tolist())
        self.assertEqual(["a", "b", "c"], df["value"].tolist())

    def test_anchor_qc_uses_centered_roll_and_count_aliases(self) -> None:
        source = (SOURCE_DIR / "cells" / "08_01.py").read_text(encoding="utf-8")
        self.assertIn("ANCHOR_QC_WARN_ABS_ROLL_CENTERED_DEG", source)
        self.assertIn('df["roll_deg_centered"]', source)
        self.assertIn('"fail_count": int(len(fail_df))', source)
        self.assertIn('"warn_count": int(len(warn_df))', source)

    def test_target_chunk_policy_is_config_driven_and_consistent(self) -> None:
        config_source = (SOURCE_DIR / "cells" / "02_01.py").read_text(encoding="utf-8")
        plan_source = (SOURCE_DIR / "cells" / "09_04.py").read_text(encoding="utf-8")
        merge_source = (SOURCE_DIR / "cells" / "14_01.py").read_text(encoding="utf-8")
        self.assertIn('"TARGET_CHUNK_MODE": "selected_chunk_ids_1based"', config_source)
        self.assertIn('"TARGET_CHUNK_IDS_1BASED": [6, 7, 8, 9, 10, 11]', config_source)
        self.assertIn('target_mode == "selected_chunk_ids_1based"', plan_source)
        self.assertIn('"target_policy": target_policy', plan_source)
        self.assertIn('"target_chunk_ids_1based": target_ids_1based', plan_source)
        self.assertIn('target_mode == "selected_chunk_ids_1based"', merge_source)

    def test_fresh_run_resets_probe_root_at_tree_init(self) -> None:
        tree_init_source = (SOURCE_DIR / "cells" / "04_01.py").read_text(encoding="utf-8")
        self.assertIn('reset_before_run = bool(config.get("RESET_TARGET_OUTPUTS_BEFORE_RUN", True))', tree_init_source)
        self.assertIn("shutil.rmtree(probe_root_resolved)", tree_init_source)
        self.assertIn('"reset_target_outputs_before_run": reset_before_run', tree_init_source)

    def test_sync_and_inventory_scripts_run(self) -> None:
        subprocess.run([sys.executable, str(SYNC_SCRIPT)], check=True, cwd=DB_ROOT.parent)
        subprocess.run([sys.executable, str(INVENTORY_SCRIPT)], check=True, cwd=DB_ROOT.parent)
        self.assertTrue(INVENTORY_PATH.exists())


if __name__ == "__main__":
    unittest.main()
