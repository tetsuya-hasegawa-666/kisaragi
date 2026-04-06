from __future__ import annotations

import argparse
import json
from pathlib import Path


def split_markdown_to_cells(text: str) -> list[dict]:
    cells: list[dict] = []
    markdown_buffer: list[str] = []
    code_buffer: list[str] = []
    in_code = False

    for line in text.splitlines(keepends=True):
        if line.startswith("```"):
            if in_code:
                cells.append(
                    {
                        "cell_type": "code",
                        "metadata": {},
                        "execution_count": None,
                        "outputs": [],
                        "source": code_buffer.copy(),
                    }
                )
                code_buffer.clear()
                in_code = False
            else:
                if markdown_buffer and any(part.strip() for part in markdown_buffer):
                    cells.append(
                        {
                            "cell_type": "markdown",
                            "metadata": {},
                            "source": markdown_buffer.copy(),
                        }
                    )
                markdown_buffer.clear()
                in_code = True
            continue

        if in_code:
            code_buffer.append(line)
        else:
            markdown_buffer.append(line)

    if code_buffer and any(part.strip() for part in code_buffer):
        cells.append(
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": code_buffer.copy(),
            }
        )
    if markdown_buffer and any(part.strip() for part in markdown_buffer):
        cells.append(
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": markdown_buffer.copy(),
            }
        )
    return cells


def build_notebook(md_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8")
    return {
        "cells": split_markdown_to_cells(text),
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown_files", nargs="+", type=Path)
    args = parser.parse_args()

    for md_path in args.markdown_files:
        ipynb_path = md_path.with_suffix(".ipynb")
        notebook = build_notebook(md_path)
        ipynb_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"markdown": str(md_path), "ipynb": str(ipynb_path), "cells": len(notebook["cells"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
