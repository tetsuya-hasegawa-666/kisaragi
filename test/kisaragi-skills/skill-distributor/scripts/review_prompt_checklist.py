from __future__ import annotations

import re
from dataclasses import dataclass, asdict


MARK_PATTERN = re.compile(r"//[a-z]")
PROJECT_CODE_PATTERN = re.compile(r"prj-kisaragi_\d{4}")


@dataclass
class PromptReview:
    marks: list[str]
    project_codes: list[str]
    mentions_script: bool
    mentions_notebook: bool
    mentions_runbook: bool
    mentions_external_compute: bool
    mentions_bdd_tdd_gate: bool
    mentions_runtime: bool
    mentions_shared_rule_change: bool


def review_prompt(text: str) -> PromptReview:
    lower = text.lower()
    return PromptReview(
        marks=sorted(set(MARK_PATTERN.findall(text))),
        project_codes=sorted(set(PROJECT_CODE_PATTERN.findall(text))),
        mentions_script="script" in lower,
        mentions_notebook="notebook" in lower or ".ipynb" in lower or "colab" in lower,
        mentions_runbook="runbook" in lower,
        mentions_external_compute=any(
            token in lower for token in ("colab", "remote gpu", "remote notebook", "drive mount")
        ),
        mentions_bdd_tdd_gate=any(token in lower for token in ("bdd", "tdd", "mrl", "gate")),
        mentions_runtime=any(token in lower for token in ("docker", "fastapi", "branch", "runtime")),
        mentions_shared_rule_change=any(
            token in lower for token in ("agents.md", "agentsmd-rh", "shared rule", "shared governance")
        ),
    )


if __name__ == "__main__":
    sample = "//s //d runbook source を更新し、Colab input を見直す"
    print(asdict(review_prompt(sample)))
