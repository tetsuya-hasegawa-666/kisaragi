from __future__ import annotations

import argparse
import json
from pathlib import Path


def _norm(path: Path) -> str:
    return str(path.resolve())


def _project_code_from_path(path: Path) -> str | None:
    for part in path.parts:
        if part.startswith("prj-kisaragi_"):
            return part
    return None


def _shared_docs(workspace_root: Path) -> list[Path]:
    return [workspace_root / "AGENTS.md"]


def _project_docs(workspace_root: Path, project_code: str) -> list[Path]:
    tgpce = workspace_root / "kisaragi-db" / "--devs" / "--tgpce-map" / project_code
    docs = [
        tgpce / "project-truth.md",
        tgpce / "hi-ai-unified-blueprint.md",
    ]
    return [p for p in docs if p.exists()]


def _extra_review_docs(workspace_root: Path, project_code: str, touched: list[Path]) -> list[Path]:
    tgpce = workspace_root / "kisaragi-db" / "--devs" / "--tgpce-map" / project_code
    extras: list[Path] = []
    touched_strs = {_norm(p) for p in touched}

    def add(path: Path) -> None:
        if path.exists():
            extras.append(path)

    for path in touched:
        p = _norm(path)
        if "\\kisaragi-db\\--devs\\--products\\" in p or "\\kisaragi-db\\--devs\\--testcode\\" in p:
            add(tgpce / "resume-startup-plan.md")
            add(tgpce / "codex-mrl-test-evidence.md")
        if "\\kisaragi-db\\--devs\\--tgpce-map\\" in p:
            add(tgpce / "resume-startup-plan.md")
        if "\\kisaragi-skills\\" in p:
            add(workspace_root / "kisaragi-skills" / "agents.md")
            add(workspace_root / "AGENTSmd-RH.md")

    unique: list[Path] = []
    seen = set()
    for path in extras:
        s = _norm(path)
        if s not in seen and s not in touched_strs:
            unique.append(path)
            seen.add(s)
    return unique


def build_report(workspace_root: Path, touched: list[Path]) -> dict:
    touched = [p.resolve() for p in touched]
    report = {
        "workspace_root": _norm(workspace_root),
        "touched_paths": [_norm(p) for p in touched],
        "must_read_before": [],
        "should_review_after": [],
        "likely_update_targets": [],
        "notes": [],
    }

    must: list[Path] = _shared_docs(workspace_root)
    after: list[Path] = []
    update_targets: list[Path] = []

    project_codes = sorted({code for p in touched if (code := _project_code_from_path(p))})
    for code in project_codes:
        docs = _project_docs(workspace_root, code)
        must.extend(docs)
        after.extend(docs)
        update_targets.extend(_extra_review_docs(workspace_root, code, touched))

    for path in touched:
        text = _norm(path)
        if "\\sharedlogs_" in text:
            report["notes"].append(
                f"{text}: shared worklog。正本ではないので AGENTS.md / project-truth.md / hi-ai-unified-blueprint.md 側の反映要否を別途確認する"
            )
        if "\\kisaragi-skills\\" in text:
            must.append(workspace_root / "kisaragi-skills" / "agents.md")
            after.append(workspace_root / "kisaragi-skills" / "agents.md")
        if text.endswith("\\AGENTS.md"):
            must.append(workspace_root / "AGENTSmd-RH.md")
            after.append(workspace_root / "AGENTSmd-RH.md")

    def uniq(paths: list[Path]) -> list[str]:
        out: list[str] = []
        seen = set()
        for path in paths:
            if not path.exists():
                continue
            s = _norm(path)
            if s not in seen:
                out.append(s)
                seen.add(s)
        return out

    report["must_read_before"] = uniq(must)
    report["should_review_after"] = uniq(after)
    report["likely_update_targets"] = uniq(update_targets)
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace-root", type=Path, required=True)
    ap.add_argument("--path", action="append", default=[])
    args = ap.parse_args()

    workspace_root = args.workspace_root.resolve()
    touched = [Path(p).resolve() for p in args.path]
    report = build_report(workspace_root, touched)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
