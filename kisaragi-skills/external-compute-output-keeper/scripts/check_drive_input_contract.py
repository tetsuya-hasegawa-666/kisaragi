from __future__ import annotations

from pathlib import Path


def check_drive_input_contract(mount_root: str, selected_input: str) -> dict:
    mount = Path(mount_root)
    target = Path(selected_input)
    return {
        "mount_exists": mount.exists(),
        "selected_input_exists": target.exists(),
        "selected_input_is_dir": target.is_dir(),
        "selected_input_is_file": target.is_file(),
    }


if __name__ == "__main__":
    print(check_drive_input_contract("/content/drive", "/content/drive/MyDrive"))
