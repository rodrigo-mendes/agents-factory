#!/usr/bin/env python3
"""
Wrapper kept at the old path so the documented commands keep working:

    python scripts/gen-docs-catalog.py                   # rewrite the generated blocks
    python scripts/gen-docs-catalog.py --check           # exit 1 if any block is stale
    python scripts/gen-docs-catalog.py --check-manuals   # manual coverage; exit 1 on gaps

The code lives in the documenting-agent-packages skill (packages/factory/package-docs). This wrapper runs it
for this repository, adding `--root <this repo>` unless you pass your own. Stdlib only.
"""
import runpy
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = (REPO / "packages" / "factory" / "package-docs" / ".apm" / "skills"
                 / "documenting-agent-packages" / "scripts")
TARGET = SKILL_SCRIPTS / "docs_catalog.py"

if __name__ == "__main__":
    if not TARGET.is_file():
        sys.exit(f"documenting-agent-packages is not at {TARGET}; restore packages/factory/package-docs.")
    args = sys.argv[1:]
    if "--root" not in args:
        args = ["--root", str(REPO)] + args
    sys.argv = [str(TARGET)] + args
    sys.path.insert(0, str(SKILL_SCRIPTS))
    runpy.run_path(str(TARGET), run_name="__main__")
