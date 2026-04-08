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
        self.assertIn("HAUB", self.contract)
        self.assertIn("reference directory", self.contract)
        self.assertIn("## Function And Class Inventory", self.inventory)
        self.assertIn("## Variable Inventory", self.inventory)
        self.assertIn("DA3 script 一覧表", self.haub)
        self.assertIn("reference directories", self.haub)
        self.assertIn("main outputs / handoff", self.haub)
        self.assertIn("key data names", self.haub)
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
        self.assertIn('"TARGET_CHUNK_IDS_1BASED": [6, 7]', config_source)
        self.assertIn('"BATCH_SIZE": 2', config_source)
        self.assertIn('"INFER_GS": True', config_source)
        self.assertIn('"DEVICE": "cuda"', config_source)
        self.assertIn('"EXPORT_FORMAT": "npz-glb-gs_ply-gs_video"', config_source)
        self.assertIn('target_mode == "selected_chunk_ids_1based"', plan_source)
        self.assertIn('"target_policy": target_policy', plan_source)
        self.assertIn('"target_chunk_ids_1based": target_ids_1based', plan_source)
        self.assertIn('BATCH_SIZE = int(config_snapshot.get("BATCH_SIZE", 2))', plan_source)
        self.assertIn('target_mode == "selected_chunk_ids_1based"', merge_source)

    def test_fresh_run_resets_probe_root_at_tree_init(self) -> None:
        tree_init_source = (SOURCE_DIR / "cells" / "04_01.py").read_text(encoding="utf-8")
        self.assertIn('reset_before_run = bool(config.get("RESET_TARGET_OUTPUTS_BEFORE_RUN", True))', tree_init_source)
        self.assertIn("shutil.rmtree(probe_root_resolved)", tree_init_source)
        self.assertIn('"reset_target_outputs_before_run": reset_before_run', tree_init_source)

    def test_premerge_pose_gate_contract_is_produced_and_consumed(self) -> None:
        full_anchor_source = (SOURCE_DIR / "cells" / "07_02.py").read_text(encoding="utf-8")
        validation_source = (SOURCE_DIR / "cells" / "13_01.py").read_text(encoding="utf-8")
        preflight_source = (SOURCE_DIR / "cells" / "12_01.py").read_text(encoding="utf-8")
        run_batches_source = (SOURCE_DIR / "cells" / "12_03.py").read_text(encoding="utf-8")
        merge_source = (SOURCE_DIR / "cells" / "14_01.py").read_text(encoding="utf-8")
        markdown_source = (SOURCE_DIR / "markdown" / "13_01.md").read_text(encoding="utf-8")
        probe_dead_copy = (SOURCE_DIR / "cells" / "13_02.py-extrated.md").read_text(encoding="utf-8")
        split_dead_copy = (SOURCE_DIR / "cells" / "13_03.py-extrated.md").read_text(encoding="utf-8")
        raw_dead_copy = (SOURCE_DIR / "cells" / "13_04.py-extrated.md").read_text(encoding="utf-8")
        arcore_dead_copy = (SOURCE_DIR / "cells" / "13_05.py-extrated.md").read_text(encoding="utf-8")
        join_dead_copy = (SOURCE_DIR / "cells" / "13_06.py-extrated.md").read_text(encoding="utf-8")
        self.assertIn('"record_index": manifest_df["record_index"].astype(int)', full_anchor_source)
        self.assertIn('camera_anchor_full_df["cx_world"] = camera_centers[:, 0]', full_anchor_source)
        self.assertIn('camera_anchor_full_df["anchor_lens_x"] = lens_vecs[:, 0]', full_anchor_source)
        self.assertIn('camera_anchor_full_df["anchor_up_x"] = up_vecs[:, 0]', full_anchor_source)
        self.assertIn('Path("/content/runbook_batch_preflight_status.json")', preflight_source)
        self.assertIn('"route": "da3_record_sequence_anchor_batch_plan_execution_preflight"', preflight_source)
        self.assertIn('DEVICE = str(config_snapshot.get("DEVICE", "cuda")).strip().lower()', run_batches_source)
        self.assertIn('assert DEVICE in {"auto", "cuda", "cpu"}', run_batches_source)
        self.assertIn('if INFER_GS and "gs_ply" not in EXPORT_FORMAT:', run_batches_source)
        self.assertIn('EXPORT_FORMAT = "npz-glb-gs_ply-gs_video"', run_batches_source)
        self.assertIn('stdout_txt.open("w", encoding="utf-8")', run_batches_source)
        self.assertIn('proc = subprocess.Popen(', run_batches_source)
        self.assertIn('returncode = int(proc.wait())', run_batches_source)
        self.assertIn('"gs_ply_saved": bool((out_dir / "gs_ply" / "0000.ply").exists())', (SOURCE_DIR / "cells" / "12_chunk_wrapper.py").read_text(encoding="utf-8"))
        self.assertIn('validation_json = merged_dir / "premerge_pose_validation.json"', validation_source)
        self.assertIn('anchor_dir = persist_root / "01_anchor"', validation_source)
        self.assertIn('camera_anchor_full_path = anchor_dir / "camera_anchor_full_arc.csv"', validation_source)
        self.assertIn('LOCAL_EXTRINSIC_MODE = "c2w"', validation_source)
        self.assertIn('LOCAL_CAMERA_BASIS[:3, :3] = np.array([', validation_source)
        self.assertIn('anchor_df = chunk_df.merge(', validation_source)
        self.assertIn('T_c_to_w0, align_diag = estimate_pose_aware_similarity(local_rows, global_rows)', validation_source)
        self.assertIn('transformed_rows = transform_c2w_list(local_rows, T_c_to_w0)', validation_source)
        self.assertIn('"local_extrinsic_mode": LOCAL_EXTRINSIC_MODE', validation_source)
        self.assertIn('"local_camera_basis": "perm_yxz_sign_ppn"', validation_source)
        self.assertIn('"transform_scale_mean"', validation_source)
        self.assertIn('"hard_fail_count": int(len(hard_fail_df))', validation_source)
        self.assertIn('save_json(final_outputs_diagnostics_dir / "premerge_pose_validation.json", summary)', validation_source)
        self.assertIn("dead copy", probe_dead_copy)
        self.assertIn("#13-2", probe_dead_copy)
        self.assertIn("best_positive_candidates", probe_dead_copy)
        self.assertIn("dead copy", split_dead_copy)
        self.assertIn("#13-3", split_dead_copy)
        self.assertIn('"forward_error_deg_p95"', split_dead_copy)
        self.assertIn("dead copy", raw_dead_copy)
        self.assertIn("#13-4", raw_dead_copy)
        self.assertIn('"sample_count_per_chunk_max": 5', raw_dead_copy)
        self.assertIn("dead copy", arcore_dead_copy)
        self.assertIn("#13-5", arcore_dead_copy)
        self.assertIn('ortho_up_abs_error_deg', arcore_dead_copy)
        self.assertIn("dead copy", join_dead_copy)
        self.assertIn("#13-6", join_dead_copy)
        self.assertIn('join_ready_csv = merged_dir / "premerge_pose_join_ready.csv"', join_dead_copy)
        self.assertIn('premerge_pose_validation_path = merged_dir / "premerge_pose_validation.json"', merge_source)
        self.assertIn('anchor_dir = persist_root / "01_anchor"', merge_source)
        self.assertIn('global_camera_matrix_df = pd.read_csv(anchor_dir / "camera_matrix_full_arc.csv")', merge_source)
        self.assertIn('global_anchor_df["cx_world"] = global_anchor_df["cam_cx"]', merge_source)
        self.assertIn('if "qc_blur_ok" not in input_manifest_df.columns:', merge_source)
        self.assertIn('input_manifest_df["qc_blur_ok"] = False', merge_source)
        self.assertIn('input_manifest_df["blur_score"] = 0.0', merge_source)
        self.assertIn('qc_blur_candidates = [c for c in ["qc_blur_ok_x", "qc_blur_ok_y"] if c in global_frame_meta_df.columns]', merge_source)
        self.assertIn('blur_score_candidates = [c for c in ["blur_score_x", "blur_score_y"] if c in global_frame_meta_df.columns]', merge_source)
        self.assertNotIn('run #13-2 pre-merge pose probe before #14-1 merge', merge_source)
        self.assertNotIn('run #13-3 pre-merge pose split probe before #14-1 merge', merge_source)
        self.assertNotIn('run #13-4 pre-merge raw orientation inspection before #14-1 merge', merge_source)
        self.assertNotIn('run #13-5 arcore anchor trajectory validation before #14-1 merge', merge_source)
        self.assertNotIn('run #13-6 pre-merge join-ready data build before #14-1 merge', merge_source)
        self.assertIn('batch_execution_items_path = chunk_manifest_dir / "batch_execution_items.csv"', merge_source)
        self.assertIn('TRANSFORM_SCALE_MIN = 0.8', merge_source)
        self.assertIn('TRANSFORM_CENTER_RMSE_MAX = 0.15', merge_source)
        self.assertIn('TRANSFORM_ROT_DIR_MAX = 0.20', merge_source)
        self.assertIn('INFER_GS = bool(config_snapshot.get("INFER_GS", config.get("INFER_GS", True)))', merge_source)
        self.assertIn('def resolve_chunk_output_dir(chunk_name: str) -> Path:', merge_source)
        self.assertIn('chunk_runs_dir.glob(f"batch_*/{chunk_name}/_SUCCESS.json")', merge_source)
        self.assertIn('pred_ready_chunk_count', merge_source)
        self.assertIn('reason": "gaussian_chunk_outputs_missing"', merge_source)
        self.assertIn('merge_reason = "infer_gs_disabled"', merge_source)
        self.assertIn('w2c_cols = [f"w2c_{i}{j}" for i in range(4) for j in range(4)]', merge_source)
        self.assertIn('out[int(row.record_index)] = np.linalg.inv(w2c).astype(np.float32)', merge_source)
        self.assertIn('LOCAL_EXTRINSIC_MODE = "c2w"', merge_source)
        self.assertIn('LOCAL_CAMERA_BASIS = np.eye(4, dtype=np.float32)', merge_source)
        self.assertIn('if LOCAL_EXTRINSIC_MODE == "c2w":', merge_source)
        self.assertIn('"local_extrinsic_mode": LOCAL_EXTRINSIC_MODE', merge_source)
        self.assertIn('run #13-1 pre-merge pose gate before #14-1 merge', merge_source)
        self.assertIn("premerge_pose_validation.json", markdown_source)
        self.assertIn("`c2w + perm_yxz_sign_ppn`", markdown_source)
        self.assertIn("`c2w + perm_yxz_sign_ppn`", (SOURCE_DIR / "markdown" / "14_01.md").read_text(encoding="utf-8"))
        self.assertIn("`center_rmse <= 0.15`", (SOURCE_DIR / "markdown" / "14_01.md").read_text(encoding="utf-8"))
        self.assertIn("`rotation_dir_residual <= 0.20`", (SOURCE_DIR / "markdown" / "14_01.md").read_text(encoding="utf-8"))
        self.assertNotIn("`#13-2`", markdown_source)
        self.assertNotIn("`#13-3`", markdown_source)
        self.assertNotIn("`#13-4`", markdown_source)
        self.assertNotIn("`#13-5`", markdown_source)
        self.assertNotIn("`#13-6`", markdown_source)

    def test_sync_and_inventory_scripts_run(self) -> None:
        subprocess.run([sys.executable, str(SYNC_SCRIPT)], check=True, cwd=DB_ROOT.parent)
        subprocess.run([sys.executable, str(INVENTORY_SCRIPT)], check=True, cwd=DB_ROOT.parent)
        self.assertTrue(INVENTORY_PATH.exists())


if __name__ == "__main__":
    unittest.main()
