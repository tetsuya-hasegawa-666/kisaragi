from __future__ import annotations

import ast
import json
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
COLAB_DIR = THIS_DIR.parent
MANIFEST_PATH = THIS_DIR / "cell_manifest.json"
MARKDOWN_MANIFEST_PATH = THIS_DIR / "markdown_manifest.json"
INVENTORY_PATH = COLAB_DIR / "da3_ngl_runbook_source_inventory.md"


def load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def top_level_symbols(source: str) -> tuple[list[str], list[str]]:
    tree = ast.parse(source)
    functions: list[str] = []
    variables: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            functions.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    variables.append(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            variables.append(node.target.id)
    return functions, variables


def render_inventory() -> str:
    cell_rows = [
        "| token | source_file | kind | heading | functions | top_level_variables | docs_id |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    function_rows = [
        "| name | token | heading | docs_id |",
        "| --- | --- | --- | --- |",
    ]
    variable_rows = [
        "| name | token | heading | docs_id |",
        "| --- | --- | --- | --- |",
    ]

    for entry in load_json(MANIFEST_PATH):
        source = (THIS_DIR / entry["source_file"]).read_text(encoding="utf-8")
        functions, variables = top_level_symbols(source)
        cell_rows.append(
            f"| {entry['token']} | `{entry['source_file']}` | `{entry['kind']}` | {entry['heading']} | {', '.join(functions) if functions else '-'} | {', '.join(variables[:12]) if variables else '-'} | `{entry['docs_id']}` |"
        )
        for name in functions:
            function_rows.append(f"| {name} | {entry['token']} | {entry['heading']} | `{entry['docs_id']}` |")
        for name in variables:
            variable_rows.append(f"| {name} | {entry['token']} | {entry['heading']} | `{entry['docs_id']}` |")

    markdown_rows = [
        "| leading_token | source_file | target_ref | prev_ref | next_ref | heading |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in load_json(MARKDOWN_MANIFEST_PATH):
        markdown_rows.append(
            f"| {entry['leading_token']} | `{entry['source_file']}` | {entry['target_ref']} | {entry['prev_ref']} | {entry['next_ref']} | {entry['heading']} |"
        )

    return "\n".join(
        [
            "# da3_ngl_prepose_RB source inventory",
            "",
            "この文書は `da3_runbook_sources/cell_manifest.json` と `da3_runbook_sources/markdown_manifest.json` を正として、canonical pair `da3_ngl_prepose_RB.md` / `da3_ngl_prepose_RB.ipynb` の code / markdown source 一覧を示す。",
            "",
            "## Cell Inventory",
            "",
            *cell_rows,
            "",
            "## Markdown Inventory",
            "",
            *markdown_rows,
            "",
            "## Function And Class Inventory",
            "",
            *function_rows,
            "",
            "## Variable Inventory",
            "",
            *variable_rows,
            "",
        ]
    )


def main() -> None:
    INVENTORY_PATH.write_text(render_inventory(), encoding="utf-8")


if __name__ == "__main__":
    main()
