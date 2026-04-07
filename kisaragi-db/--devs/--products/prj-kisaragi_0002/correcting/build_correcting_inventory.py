from __future__ import annotations

import json
import re
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = THIS_DIR / "correcting_script_manifest.json"
INVENTORY_PATH = THIS_DIR / "correcting_script_source_inventory.md"

KOTLIN_SYMBOL_RE = re.compile(
    r"^\s*(?:data\s+class|sealed\s+class|enum\s+class|class|object|interface)\s+([A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)
KOTLIN_FUN_RE = re.compile(r"^\s*fun\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
POWERSHELL_FUN_RE = re.compile(r"^\s*function\s+([A-Za-z_][A-Za-z0-9_-]*)", re.MULTILINE)


def load_manifest() -> list[dict]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def unique_in_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def source_symbols(source_file: str) -> list[str]:
    path = THIS_DIR / source_file
    source = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".kt", ".java"}:
        return unique_in_order(KOTLIN_SYMBOL_RE.findall(source) + KOTLIN_FUN_RE.findall(source))
    if suffix == ".ps1":
        return unique_in_order(POWERSHELL_FUN_RE.findall(source))
    return []


def render_inventory() -> str:
    source_rows = [
        "| token | source_file | kind | heading | role | key functions / classes | key data names | reference directories | main outputs / handoff | docs_id |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    function_rows = [
        "| name | token | heading | docs_id |",
        "| --- | --- | --- | --- |",
    ]
    variable_rows = [
        "| name | token | heading | docs_id |",
        "| --- | --- | --- | --- |",
    ]

    for entry in load_manifest():
        symbols = source_symbols(entry["source_file"])
        key_data_names = entry.get("key_data_names", [])
        reference_directories = entry.get("reference_directories", [])
        main_outputs = entry.get("main_outputs_handoff", [])
        source_rows.append(
            "| {token} | `{source_file}` | `{kind}` | {heading} | {role} | {symbols} | {data_names} | {directories} | {outputs} | `{docs_id}` |".format(
                token=entry["token"],
                source_file=entry["source_file"],
                kind=entry["kind"],
                heading=entry["heading"],
                role=entry["role"],
                symbols=", ".join(symbols) if symbols else "-",
                data_names=", ".join(key_data_names) if key_data_names else "-",
                directories=", ".join(reference_directories) if reference_directories else "-",
                outputs=", ".join(main_outputs) if main_outputs else "-",
                docs_id=entry["docs_id"],
            )
        )
        for symbol in symbols:
            function_rows.append(
                f"| {symbol} | {entry['token']} | {entry['heading']} | `{entry['docs_id']}` |"
            )
        for name in key_data_names:
            variable_rows.append(
                f"| {name} | {entry['token']} | {entry['heading']} | `{entry['docs_id']}` |"
            )

    return "\n".join(
        [
            "# correcting script source inventory",
            "",
            "この文書は `correcting_script_manifest.json` を正として、`correcting` の local product script / source inventory を示す。",
            "",
            "- 目的は、`HAUB` の correct 用一覧表から local product 側の実体へ迷わず降りることである。",
            "- `correcting` 側は最適化前でも現状のまま記載し、後段で責務再編する時は manifest と同時に更新する。",
            "- 詳細列は `role`、`key data names`、`reference directories`、`main outputs / handoff` を固定し、`modeling` 側の inventory 思想と揃える。",
            "",
            "## Source Inventory",
            "",
            *source_rows,
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
