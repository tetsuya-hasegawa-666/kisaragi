from __future__ import annotations

import json
import locale
import os
import subprocess
import sys


def run_command(command: list[str]) -> dict[str, object]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "error": str(exc)}

    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout_preview": completed.stdout[:120],
        "stderr_preview": completed.stderr[:120],
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    report = {
        "python_stdout_encoding": getattr(sys.stdout, "encoding", None),
        "preferred_encoding": locale.getpreferredencoding(False),
        "python_utf8_mode": getattr(sys.flags, "utf8_mode", 0),
        "powershell_output_encoding": os.environ.get("PYTHONIOENCODING", ""),
        "git_version": run_command(["git", "--version"]),
        "git_utf8_sample": run_command(["git", "status", "--short"]),
    }

    report["runtime_utf8_safe"] = (
        str(report["python_stdout_encoding"]).lower().startswith("utf")
        or str(report["preferred_encoding"]).lower().startswith("utf")
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
