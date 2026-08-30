#!/bin/bash
# Apply Windows compatibility patches to the installed swebench package.
#
# swebench 2.1.8 has three bugs when running the evaluation harness on
# Windows. These patches fix them in-place inside site-packages.
#
# Usage:
#   bash patches/swebench/apply_windows_patches.sh <python-executable>
# Example:
#   bash patches/swebench/apply_windows_patches.sh D:/Apps/python/python.exe
#
# Re-run safely: patches are idempotent (they check before applying).

set -euo pipefail

PYTHON="${1:?Usage: $0 <python-executable>}"

"$PYTHON" - << 'PYEOF'
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.find_spec("swebench")
if spec is None:
    print("ERROR: swebench not installed for", sys.executable)
    sys.exit(1)
pkg_root = Path(spec.origin).parent
print(f"swebench package: {pkg_root}")


def patch_file(rel_path: str, old: str, new: str, label: str) -> None:
    path = pkg_root / rel_path
    text = path.read_text(encoding="utf-8")
    if new in text:
        print(f"  [skip] {label} (already applied)")
        return
    if old not in text:
        print(f"  [FAIL] {label}: pattern not found — swebench version mismatch?")
        sys.exit(1)
    path.write_text(text.replace(old, new), encoding="utf-8")
    print(f"  [ok]   {label}")


# --- Patch 1: copy_to_container must treat dst as a POSIX path ---
# On Windows, Path("/eval.sh") is a WindowsPath whose string form uses
# backslashes: f"tar -xf {dst}.tar -C {dst.parent}" becomes
# "tar -xf \eval.sh.tar -C \" — the trailing backslash makes shlex
# raise "No escaped character" and every instance errors out.
patch_file(
    "harness/docker_utils.py",
    old='''    # Check if destination path is valid
    if os.path.dirname(dst) == "":
        raise ValueError(
            f"Destination path parent directory cannot be empty!, dst: {dst}"
        )''',
    new='''    # Windows fix: dst must be treated as a POSIX path (container path).
    # On Windows, Path('/eval.sh') is a WindowsPath whose string form uses
    # backslashes, producing 'tar -xf \\\\eval.sh.tar -C \\\\' which shlex
    # rejects with 'No escaped character'.
    dst = PurePosixPath(dst)
    # Check if destination path is valid
    if os.path.dirname(dst) == "":
        raise ValueError(
            f"Destination path parent directory cannot be empty!, dst: {dst}"
        )''',
    label="copy_to_container: PurePosixPath for container destinations",
)

# Patch 1b: import PurePosixPath
docker_utils = pkg_root / "harness/docker_utils.py"
text = docker_utils.read_text(encoding="utf-8")
if "from pathlib import Path, PurePosixPath" not in text:
    if "from pathlib import Path" in text:
        docker_utils.write_text(
            text.replace("from pathlib import Path", "from pathlib import Path, PurePosixPath", 1),
            encoding="utf-8",
        )
        print("  [ok]   docker_utils: import PurePosixPath")
    else:
        print("  [FAIL] docker_utils: no 'from pathlib import Path' import found")
        sys.exit(1)
else:
    print("  [skip] docker_utils: import PurePosixPath (already applied)")

# --- Patch 2: eval.sh must be written with LF line endings ---
# Windows text mode writes CRLF; bash inside the container then sees
# "conda activate testbed\r" and fails with "No such file or directory".
patch_file(
    "harness/run_evaluation.py",
    old='        eval_file.write_text(test_spec.eval_script)',
    new='        eval_file.write_text(test_spec.eval_script, newline=chr(10))',
    label="run_evaluation: write eval.sh with LF endings",
)

# --- Patch 3: patch.diff must be written with LF line endings ---
# Same CRLF problem: git apply inside the container rejects the patch
# with "trailing whitespace" / "patch does not apply".
patch_file(
    "harness/run_evaluation.py",
    old='        patch_file.write_text(pred[KEY_PREDICTION] or "")',
    new='        patch_file.write_text(pred[KEY_PREDICTION] or "", newline=chr(10))',
    label="run_evaluation: write patch.diff with LF endings",
)

print("\nAll swebench Windows patches applied successfully.")
PYEOF
