from __future__ import annotations


def suggest_evidence_targets(has_admin_step_change: bool = False) -> dict:
    targets = ["codex-mrl-test-evidence.md", "--testlogs/"]
    if has_admin_step_change:
        targets.append("admin-mrl-test-method.md")
    return {"evidence_targets": targets}


if __name__ == "__main__":
    print(suggest_evidence_targets(False))
