#5-1
from pathlib import Path
import inspect
import subprocess
import sys

repo_root = Path("/content/Depth-Anything-3")
repo_url = "https://github.com/ByteDance-Seed/Depth-Anything-3.git"
src_root = repo_root / "src"

if not repo_root.exists():
    subprocess.run(["git", "clone", "--depth", "1", repo_url, str(repo_root)], check=True)
else:
    print("repo already exists:", repo_root)

subprocess.run([
    "python", "-m", "pip", "install", "--quiet",
    "addict", "evo", "moviepy==1.0.3", "pygame", "pycolmap", "plyfile", "trimesh", "gsplat", "e3nn"
], check=True)

assert repo_root.exists(), repo_root
assert src_root.exists(), src_root
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from depth_anything_3.api import DepthAnything3
import gsplat
import e3nn

print("repo_exists", repo_root.exists(), repo_root)
print("dependency_install_ok")
print("depth_anything_3_import_ok", DepthAnything3)
print("gsplat_version", getattr(gsplat, "__version__", "unknown"))
print("e3nn_version", getattr(e3nn, "__version__", "unknown"))
print("inference_sig", inspect.signature(DepthAnything3.inference))
