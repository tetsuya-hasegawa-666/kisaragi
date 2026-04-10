from __future__ import annotations

import argparse
import ast
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DB_ROOT = Path(__file__).resolve().parents[3]
DEVS_ROOT = DB_ROOT / "--devs"
COLAB_DIR = DEVS_ROOT / "--products" / "prj-kisaragi_0002" / "colab"
SOURCE_DIR = COLAB_DIR / "da3_increpose_sources"
MANIFEST_PATH = SOURCE_DIR / "cell_manifest.json"
HAUB_PATH = DEVS_ROOT / "--tgpce-map" / "prj-kisaragi_0002" / "hi-ai-unified-blueprint.md"

MANUAL_EXTERNAL_KEYS = {
    "test_only_target_chunk_with_batch.csv",
    "test_only_target_batch_plan.csv",
    "target_chunk_with_batch.csv",
    "target_batch_plan.csv",
    "frame_record.csv",
    "pose_landmarker_world.csv",
    "frames_pose.csv",
}

CRITICAL_ARTIFACT_KEYS = {
    "batch_execution_items.csv",
    "chunk_input_manifest_arc.csv",
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
    "merged_camera_pose_arc.csv",
}

HAUB_HOFF_HEADING = "### Increpose Path Handoff Matrix"


@dataclass
class PathRef:
    token: str
    source_file: str
    line: int
    mode: str
    path_template: str
    artifact_key: str
    via: str


def _is_python_blob(text: str) -> bool:
    return "import " in text and ("def main" in text or "argparse" in text or "Path(" in text)


def _join_path(lhs: str, rhs: str) -> str:
    left = lhs.rstrip("/")
    right = rhs.lstrip("/")
    if not left:
        return right
    if not right:
        return left
    return f"{left}/{right}"


class PathContractCollector(ast.NodeVisitor):
    def __init__(self, token: str, source_file: str) -> None:
        self.token = token
        self.source_file = source_file
        self.env: dict[str, str] = {}
        self.refs: list[PathRef] = []
        self.directory_defs: dict[str, str] = {}
        self.embedded_sources: list[tuple[str, str]] = []

    def render(self, node: ast.AST | None) -> str:
        if node is None:
            return ""
        if isinstance(node, ast.Name):
            return self.env.get(node.id, f"<{node.id}>")
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return node.value.replace("\\", "/")
            if node.value is None:
                return ""
            return str(node.value)
        if isinstance(node, ast.Call):
            func_name = self._func_name(node.func)
            if func_name in {"Path", "str"} and node.args:
                return self.render(node.args[0])
            if func_name == "next":
                return "<next()>"
            return f"<call:{func_name}>"
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return _join_path(self.render(node.left), self.render(node.right))
        if isinstance(node, ast.JoinedStr):
            parts: list[str] = []
            for value in node.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    parts.append(value.value.replace("\\", "/"))
                elif isinstance(value, ast.FormattedValue):
                    parts.append("{" + self.render(value.value) + "}")
            return "".join(parts)
        if isinstance(node, ast.Attribute):
            return f"{self.render(node.value)}.{node.attr}"
        if isinstance(node, ast.Subscript):
            base = self.render(node.value)
            index = self.render(node.slice)
            return f"{base}[{index}]"
        if isinstance(node, ast.Tuple):
            return ",".join(self.render(x) for x in node.elts)
        if isinstance(node, ast.List):
            return ",".join(self.render(x) for x in node.elts)
        return f"<{node.__class__.__name__}>"

    def _func_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            left = self._func_name(node.value)
            return f"{left}.{node.attr}" if left else node.attr
        return ""

    def _artifact_key(self, template: str) -> str:
        norm = template.replace("\\", "/")
        if norm.startswith("/content/"):
            return norm
        parts = [p for p in norm.split("/") if p]
        literal_parts = [p for p in parts if "{" not in p and not p.startswith("<")]
        if not literal_parts:
            return norm
        if len(literal_parts) >= 2 and "." in literal_parts[-1]:
            tail2 = "/".join(literal_parts[-2:])
            if literal_parts[-2] in {"manifests", "merged", "diagnostics", "_runtime", "07matching", "gs_ply", "gs_video"}:
                return tail2
        return literal_parts[-1]

    def _record_ref(self, mode: str, path_node: ast.AST | None, node: ast.AST, via: str) -> None:
        template = self.render(path_node)
        if not template:
            return
        self.refs.append(
            PathRef(
                token=self.token,
                source_file=self.source_file,
                line=getattr(node, "lineno", 0),
                mode=mode,
                path_template=template,
                artifact_key=self._artifact_key(template),
                via=via,
            )
        )

    def visit_Assign(self, node: ast.Assign) -> Any:
        rendered = self.render(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.env[target.id] = rendered
                if target.id.endswith("_dir"):
                    self.directory_defs[target.id] = rendered
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str) and _is_python_blob(node.value.value):
                    self.embedded_sources.append((f"{self.token}:{target.id}", node.value.value))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        func_name = self._func_name(node.func)

        if func_name.endswith(".to_csv") and node.args:
            self._record_ref("write", node.args[0], node, func_name)
        elif func_name == "np.save" and node.args:
            self._record_ref("write", node.args[0], node, func_name)
        elif func_name == "save_json" and node.args:
            self._record_ref("write", node.args[0], node, func_name)
        elif func_name.endswith(".write_text"):
            base = node.func.value if isinstance(node.func, ast.Attribute) else None
            self._record_ref("write", base, node, func_name)
        elif func_name.endswith(".write_html"):
            base = node.func.value if isinstance(node.func, ast.Attribute) else None
            self._record_ref("write", base, node, func_name)
        elif func_name.endswith(".mkdir"):
            base = node.func.value if isinstance(node.func, ast.Attribute) else None
            self._record_ref("mkdir", base, node, func_name)
        elif func_name == "pd.read_csv" and node.args:
            self._record_ref("read", node.args[0], node, func_name)
        elif func_name == "np.load" and node.args:
            self._record_ref("read", node.args[0], node, func_name)
        elif func_name == "load_json" and node.args:
            self._record_ref("read", node.args[0], node, func_name)
        elif func_name.endswith(".read_text"):
            base = node.func.value if isinstance(node.func, ast.Attribute) else None
            self._record_ref("read", base, node, func_name)
        elif func_name.endswith(".exists"):
            base = node.func.value if isinstance(node.func, ast.Attribute) else None
            self._record_ref("probe", base, node, func_name)
        elif func_name.endswith(".glob") and node.args:
            base = node.func.value if isinstance(node.func, ast.Attribute) else None
            glob_expr = _join_path(self.render(base), self.render(node.args[0]))
            fake = ast.Constant(glob_expr)
            self._record_ref("probe", fake, node, func_name)

        self.generic_visit(node)


def _load_cell_entries() -> list[dict[str, Any]]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _parse_pipe_row(line: str) -> list[str]:
    return [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]


def _load_haub_handoff_contracts() -> list[dict[str, str]]:
    text = HAUB_PATH.read_text(encoding="utf-8")
    if HAUB_HOFF_HEADING not in text:
        return []
    section = text.split(HAUB_HOFF_HEADING, 1)[1]
    lines = section.splitlines()
    table_lines = [line for line in lines if line.strip().startswith("|")]
    if len(table_lines) < 3:
        return []
    headers = _parse_pipe_row(table_lines[0])
    rows = []
    for line in table_lines[2:]:
        cells = _parse_pipe_row(line)
        if len(cells) != len(headers):
            break
        rows.append(dict(zip(headers, cells)))
    return rows


def _collect_from_source(token: str, source_file: str, source_text: str) -> tuple[list[PathRef], dict[str, str], list[tuple[str, str]]]:
    tree = ast.parse(source_text, filename=source_file)
    collector = PathContractCollector(token=token, source_file=source_file)
    collector.visit(tree)
    return collector.refs, collector.directory_defs, collector.embedded_sources


def _managed_ref(ref: PathRef) -> bool:
    template = ref.path_template
    if template.startswith("/content/"):
        return False
    managed_markers = [
        "<probe_root>",
        "<pipeline_root>",
        "<chunk_manifest_dir>",
        "<chunk_runs_dir>",
        "<merged_dir>",
        "<manifest_dir>",
        "<anchor_dir>",
        "<final_outputs_dir>",
        "<final_outputs_diagnostics_dir>",
        "<final_outputs_manifests_dir>",
        "<final_outputs_chunk_evidence_dir>",
        "<batch_work_dir>",
        "<out_dir>",
        "final_outputs",
        "chunk_runs",
        "manifests",
        "01_anchor",
        "merged",
    ]
    return any(marker in template for marker in managed_markers)


def build_report() -> dict[str, Any]:
    entries = _load_cell_entries()
    haub_contracts = _load_haub_handoff_contracts()
    all_refs: list[PathRef] = []
    directory_defs: dict[str, dict[str, str]] = {}
    source_text_by_token: dict[str, str] = {}

    for entry in entries:
        source_file = entry["source_file"]
        source_path = SOURCE_DIR / source_file
        source_text = source_path.read_text(encoding="utf-8")
        source_text_by_token[entry["token"]] = source_text
        refs, dirs, embedded_sources = _collect_from_source(entry["token"], source_file, source_text)
        all_refs.extend(refs)
        for name, template in dirs.items():
            directory_defs[f"{entry['token']}:{name}"] = {"token": entry["token"], "source_file": source_file, "path_template": template}
        for embedded_token, embedded_text in embedded_sources:
            source_text_by_token[embedded_token] = embedded_text
            emb_refs, emb_dirs, _ = _collect_from_source(embedded_token, source_file, embedded_text)
            all_refs.extend(emb_refs)
            for name, template in emb_dirs.items():
                directory_defs[f"{embedded_token}:{name}"] = {"token": embedded_token, "source_file": source_file, "path_template": template}

    artifact_map: dict[str, dict[str, Any]] = defaultdict(lambda: {"writes": [], "reads": [], "probes": [], "mkdirs": []})
    for ref in all_refs:
        bucket = artifact_map[ref.artifact_key]
        if ref.mode == "write":
            bucket["writes"].append(asdict(ref))
        elif ref.mode == "read":
            bucket["reads"].append(asdict(ref))
        elif ref.mode == "mkdir":
            bucket["mkdirs"].append(asdict(ref))
        else:
            bucket["probes"].append(asdict(ref))

    missing_reads = []
    for artifact_key, bucket in sorted(artifact_map.items()):
        if artifact_key in MANUAL_EXTERNAL_KEYS:
            continue
        if artifact_key.startswith("/content/"):
            continue
        if bucket["reads"] and not bucket["writes"]:
            managed_reads = [r for r in bucket["reads"] if _managed_ref(PathRef(**r))]
            if managed_reads:
                missing_reads.append({"artifact_key": artifact_key, "reads": managed_reads})

    critical_rule_failures = []
    pred_writer_lines = [
        ref for ref in all_refs
        if ref.mode == "write" and ref.artifact_key == "pred_extrinsics.npy"
    ]
    if not any(ref.token == "#8-8:wrapper_code" and ref.path_template.endswith('/pred_extrinsics.npy') for ref in pred_writer_lines):
        critical_rule_failures.append({
            "rule": "wrapper_writes_pred_extrinsics",
            "detail": "embedded wrapper in #8-8 does not expose pred_extrinsics.npy writer",
        })

    exec_source = (SOURCE_DIR / "cells" / "08_09.py").read_text(encoding="utf-8")
    if 'out_dir = batch_work_dir / chunk_name' not in exec_source:
        critical_rule_failures.append({
            "rule": "chunk_outputs_are_chunk_scoped",
            "detail": "#8-9 must write to batch_work_dir / chunk_name",
        })
    if 'runtime_dir = out_dir / "_runtime"' not in exec_source:
        critical_rule_failures.append({
            "rule": "runtime_seed_csv_is_chunk_scoped",
            "detail": "#8-9 runtime dir must be under out_dir / _runtime",
        })

    def token_has_artifact_text(token: str, artifact_key: str) -> bool:
        return artifact_key in source_text_by_token.get(token, "")

    for contract in haub_contracts:
        artifact_key = contract["artifact_key"]
        canonical_path = contract["canonical path / pattern"]
        producer_tokens = [x.strip() for x in contract["producer token"].split(",") if x.strip()]
        consumer_tokens = [x.strip() for x in contract["consumer token"].split(",") if x.strip()]
        bucket = artifact_map[artifact_key]

        for token in producer_tokens:
            if any(ref["mode"] == "write" and ref["token"].startswith(token) for ref in bucket["writes"]):
                continue
            if token_has_artifact_text(token, artifact_key):
                bucket["writes"].append({
                    "token": token,
                    "source_file": "<haub-contract>",
                    "line": 0,
                    "mode": "write",
                    "path_template": canonical_path,
                    "artifact_key": artifact_key,
                    "via": "haub_declared_producer",
                })

        for token in consumer_tokens:
            has_consumer = any(
                ref["mode"] in {"read", "probe"} and ref["token"].startswith(token)
                for ref in bucket["reads"] + bucket["probes"]
            )
            if has_consumer:
                continue
            if token_has_artifact_text(token, artifact_key):
                bucket["reads"].append({
                    "token": token,
                    "source_file": "<haub-contract>",
                    "line": 0,
                    "mode": "read",
                    "path_template": canonical_path,
                    "artifact_key": artifact_key,
                    "via": "haub_declared_consumer",
                })

    critical_artifacts = {
        key: artifact_map.get(key, {"writes": [], "reads": [], "probes": [], "mkdirs": []})
        for key in sorted(CRITICAL_ARTIFACT_KEYS)
    }

    haub_contract_failures = []
    for contract in haub_contracts:
        artifact_key = contract["artifact_key"]
        producer_tokens = [x.strip() for x in contract["producer token"].split(",") if x.strip()]
        consumer_tokens = [x.strip() for x in contract["consumer token"].split(",") if x.strip()]
        canonical_path = contract["canonical path / pattern"]
        refs_for_key = [
            ref for ref in all_refs
            if ref.artifact_key == artifact_key or artifact_key in ref.path_template
        ]
        for token in producer_tokens:
            if not any(ref.mode == "write" and ref.token.startswith(token) for ref in refs_for_key) and not token_has_artifact_text(token, artifact_key):
                haub_contract_failures.append({
                    "contract_id": contract["contract_id"],
                    "artifact_key": artifact_key,
                    "type": "missing_producer",
                    "token": token,
                    "canonical_path": canonical_path,
                })
        for token in consumer_tokens:
            if not any(ref.mode in {"read", "probe"} and ref.token.startswith(token) for ref in refs_for_key) and not token_has_artifact_text(token, artifact_key):
                haub_contract_failures.append({
                    "contract_id": contract["contract_id"],
                    "artifact_key": artifact_key,
                    "type": "missing_consumer",
                    "token": token,
                    "canonical_path": canonical_path,
                })

    return {
        "source_dir": str(SOURCE_DIR),
        "cell_count": len(entries),
        "haub_handoff_contract_count": len(haub_contracts),
        "directory_defs": directory_defs,
        "artifact_map": artifact_map,
        "managed_reads_without_writers": missing_reads,
        "critical_artifacts": critical_artifacts,
        "critical_rule_failures": critical_rule_failures,
        "haub_contract_failures": haub_contract_failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-json", type=Path, default=None)
    args = parser.parse_args()

    report = build_report()
    if args.report_json is not None:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
