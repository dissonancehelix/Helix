#!/usr/bin/env python3
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
STAGING = ROOT / "staging"
KB = ROOT / "kb"


def main():
    files = list(STAGING.glob("*.json"))

    if not files:
        print("staging/ is empty — nothing to promote.")
        sys.exit(0)

    copied = []
    for src in files:
        dst = KB / src.name
        shutil.copy2(src, dst)
        copied.append(dst)

    result = subprocess.run(
        [sys.executable, str(ROOT / "core" / "validate.py")],
        cwd=str(ROOT)
    )

    if result.returncode != 0:
        for dst in copied:
            dst.unlink(missing_ok=True)
        sys.exit(1)

    for src in files:
        src.unlink()

    sys.exit(0)


if __name__ == "__main__":
    main()
