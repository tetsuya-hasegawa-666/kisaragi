from __future__ import annotations

import argparse
import json
import re
import textwrap
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
COLAB_DIR = THIS_DIR.parent
RUNBOOK_MD = COLAB_DIR / "da3_ngl_runbook.md"
RUNBOOK_IPYNB = COLAB_DIR / "da3_ngl_runbook.ipynb"
MANIFEST_PATH = THIS_DIR / "cell_manifest.json"
MARKDOWN_MANIFEST_PATH = THIS_DIR / "markdown_manifest.json"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.replace("\r\n", "\n"), encoding="utf-8")


def source_lines(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n")
    if not normalized.endswith("\n"):
        normalized += "\n"
    return normalized.splitlines(keepends=True)


def load_manifest() -> list[dict]:
    return json.loads(read_text(MANIFEST_PATH))


def load_markdown_manifest() -> list[dict]:
    return json.loads(read_text(MARKDOWN_MANIFEST_PATH))


def find_code_cell(nb: dict, token: str) -> dict:
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        if src.lstrip().startswith(token):
            return cell
    raise ValueError(f"cell not found: {token}")


def notebook_template() -> dict:
    if RUNBOOK_IPYNB.exists():
        return json.loads(read_text(RUNBOOK_IPYNB))
    return {
        "cells": [],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def replace_markdown_code_block(markdown: str, token: str, new_source: str) -> str:
    pattern = re.compile(rf"```python\n[ \t]*{re.escape(token)}.*?```", re.S)
    replacement = f"```python\n{new_source.rstrip()}\n```"
    new_markdown, count = pattern.subn(lambda _: replacement, markdown, count=1)
    if count != 1:
        raise ValueError(f"markdown code block not found or duplicated: {token}")
    return new_markdown


def extract_wrapper_body(cell_source: str) -> str:
    m = re.search(r"wrapper_code = r'''(.*?)'''", cell_source, re.S)
    if not m:
        raise ValueError("wrapper_code block not found")
    body = textwrap.dedent(m.group(1)).lstrip("\n")
    return body.rstrip() + "\n"


def render_wrapper_cell(token: str, wrapper_body: str) -> str:
    inner = textwrap.dedent(wrapper_body).rstrip("\n")
    return (
        f"{token}\n\n"
        "from pathlib import Path\n"
        "import textwrap\n\n"
        'repo_root = Path("/content/Depth-Anything-3")\n'
        'src_root = repo_root / "src"\n'
        "assert repo_root.exists(), repo_root\n"
        "assert src_root.exists(), src_root\n\n"
        'wrapper_path = repo_root / "run_da3_chunk_local.py"\n\n'
        "wrapper_code = r'''\n"
        f"{inner}\n"
        "'''\n\n"
        'wrapper_path.write_text(textwrap.dedent(wrapper_code).lstrip("\\n"), encoding="utf-8")\n'
        'print({"wrapper_path": str(wrapper_path), "size_bytes": wrapper_path.stat().st_size})\n'
        "display_stage_summary(\n"
        f'    "{token.lstrip("#")}",\n'
        '    "write chunk runner wrapper",\n'
        "    outputs=[\n"
        '        {"item": "wrapper_path", "path": str(wrapper_path)},\n'
        "    ],\n"
        ")\n"
    )


def extract_current_sources(force: bool) -> None:
    manifest = load_manifest()
    markdown_manifest = load_markdown_manifest()
    nb = json.loads(read_text(RUNBOOK_IPYNB))
    markdown_cells = [cell for cell in nb.get("cells", []) if cell.get("cell_type") == "markdown"]

    if len(markdown_cells) != len(markdown_manifest):
        raise ValueError(
            {
                "reason": "markdown cell count mismatch",
                "notebook_markdown_cells": len(markdown_cells),
                "markdown_manifest_entries": len(markdown_manifest),
            }
        )

    for entry, cell in zip(markdown_manifest, markdown_cells):
        path = THIS_DIR / entry["source_file"]
        if path.exists() and not force:
            continue
        write_text(path, "".join(cell.get("source", [])))

    for entry in manifest:
        path = THIS_DIR / entry["source_file"]
        if path.exists() and not force:
            continue
        cell = find_code_cell(nb, entry["token"])
        cell_source = "".join(cell.get("source", []))
        if entry["kind"] == "wrapper_body":
            write_text(path, extract_wrapper_body(cell_source))
        else:
            write_text(path, cell_source)


def sync_sources() -> None:
    manifest = load_manifest()
    markdown_manifest = load_markdown_manifest()
    nb = notebook_template()
    notebook_cells: list[dict] = []
    markdown_parts: list[str] = []
    markdown_by_token = {entry["leading_token"]: entry for entry in markdown_manifest}

    for entry in manifest:
        md_entry = markdown_by_token.get(entry["token"])
        if md_entry is not None:
            md_source = read_text(THIS_DIR / md_entry["source_file"])
            notebook_cells.append(
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": source_lines(md_source),
                }
            )
            markdown_parts.append(md_source.rstrip())

        path = THIS_DIR / entry["source_file"]
        source = read_text(path)
        rendered = render_wrapper_cell(entry["token"], source) if entry["kind"] == "wrapper_body" else source
        notebook_cells.append(
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": source_lines(rendered),
            }
        )
        markdown_parts.append(f"```python\n{rendered.rstrip()}\n```")

    nb["cells"] = notebook_cells
    write_text(RUNBOOK_MD, "\n\n".join(markdown_parts).rstrip() + "\n")
    write_text(RUNBOOK_IPYNB, json.dumps(nb, ensure_ascii=False, indent=1) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract-current", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.extract_current:
        extract_current_sources(force=args.force)
    else:
        sync_sources()


if __name__ == "__main__":
    main()
