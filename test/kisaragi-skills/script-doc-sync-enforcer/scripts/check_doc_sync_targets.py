from __future__ import annotations

from pathlib import Path


def suggest_doc_targets(changed_paths: list[str]) -> dict:
    text = " ".join(changed_paths).lower()
    suggestions = ["project-truth-core.md", "realtime-compass-and-status.md"]
    if "colab" in text or "runbook" in text or ".ipynb" in text:
        suggestions.extend(["design contract", "source inventory"])
    if "agents.md" in text or "ag" in text:
        suggestions.extend(["AGENTS.md", "AGENTSmd-RH.md"])
    return {"changed_paths": changed_paths, "suggestions": suggestions}


if __name__ == "__main__":
    print(suggest_doc_targets(["colab/da3_ngl_increpose_RB.ipynb"]))




