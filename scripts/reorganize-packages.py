#!/usr/bin/env python3
"""
Move the flat packages/<pkg> folders into family folders (packages/<family>[/<sub>]/<pkg>) and fix
every reference to them. Dry run by default; pass --apply to change the tree.

What it does, in order:
  1. `git mv packages/<pkg> packages/<new>/<pkg>` for every entry of FAMILY.
  2. Rewrites every `path: ../<pkg>` in packages/**/apm.yml (and the apm.yml snippets in package
     READMEs) to the relative path from the package's NEW location.
  3. Rewrites `./packages/<pkg>` in the root apm.yml and `packages/<pkg>` in every tracked text file
     outside .claude/ (generated), apm.lock.yaml (generated) and workspace/ (historical outputs).
  4. Fails if any `path:` in a packages/**/apm.yml does not resolve to an existing folder.

Runs before `apm install --target claude`, which regenerates .claude/ and apm.lock.yaml.

Verified before writing this (2026-10-31, APM 0.35.0): nested packages whose apm.yml files cite the
same dependency with different relative texts (e.g. ../../../delivery/protocol/handoff-core and
../../../../delivery/protocol/handoff-core) install and pass `apm audit --ci`; the "ambiguous
resolved_by" failure documented in the root apm.yml comes from listing a transitive package
directly in the ROOT manifest, which this script does not do.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PKGS = REPO / "packages"

FAMILY = {
    "factory-core": "factory",
    "research-core": "factory",
    "researching-frameworks": "factory",
    "researching-platform": "factory",
    "artifact-authoring": "factory",
    "agent-package-builder": "factory",
    "auditing": "harness-quality",
    "validating": "harness-quality",
    "evaluating": "harness-quality",
    "book-writing": "content-generation",
    "solution-architecture": "architecture",
    "terraform": "cloud/terraform",
    "aws-terraform": "cloud/terraform",
    "oci-terraform": "cloud/terraform",
    "aws-skills": "cloud/provider/aws",
    "aws-architect": "cloud/provider/aws",
    "aws-lambda": "cloud/provider/aws",
    "aws-observability": "cloud/provider/aws",
    "oci-core": "cloud/provider/oci",
    "oci-functions-java": "cloud/provider/oci",
    "oci-observability": "cloud/provider/oci",
    "oci-architecture": "cloud/provider/oci",
    "handoff-core": "delivery/protocol",
    "openspec-core": "delivery/specs",
    "openspec-github": "delivery/specs",
    "github-core": "delivery/github",
    "github-actions-cicd": "delivery/github",
    "quarkus-core": "java/quarkus",
    "quarkus-aws": "java/quarkus",
    "quarkus-langchain4j": "java/quarkus",
    "camel-quarkus-skills": "java/quarkus",
    "camel-quarkus-integrator": "java/quarkus",
    "langchain4j": "java/libs",
    "stripe-java": "java/libs",
    "nextjs-frontend": "frontend/react",
    "ui-design": "frontend/react",
    "vercel-frontend": "third-party",
    "aws-saas-serverless-quarkus-react-nextjs": "saas",
}

TEXT_EXT = {".md", ".py", ".yml", ".yaml", ".json", ".txt", ".sh", ".ps1"}
SKIP_PREFIXES = (".claude/", "workspace/", "apm_modules/")
SKIP_FILES = {"apm.lock.yaml", "scripts/reorganize-packages.py"}

NAMES = "|".join(sorted(map(re.escape, FAMILY), key=len, reverse=True))
# `packages/<pkg>` not already inside a family folder: packages/ must not be preceded by a word char
# or dash, and <pkg> must end at a non-name char.
PKG_REF = re.compile(rf"(?<![\w-])(\.?/?)packages/({NAMES})(?![\w-])")
DEP_PATH = re.compile(rf"(path:\s*)\.\./({NAMES})(?![\w-])")


def new_dir(pkg: str) -> str:
    return f"{FAMILY[pkg]}/{pkg}"


def rel(from_pkg: str, to_pkg: str) -> str:
    return os.path.relpath(new_dir(to_pkg), new_dir(from_pkg)).replace(os.sep, "/")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True,
                          text=True, encoding="utf-8").stdout


def rewrite(path: Path, fn, apply: bool) -> int:
    with open(path, encoding="utf-8", newline="") as fh:  # keep the file's own line endings
        text = fh.read()
    new, _ = fn(text)
    # count only real changes: a same-family `../x` is rewritten to the same text (idempotent reruns)
    n = sum(1 for a, b in zip(text.splitlines(), new.splitlines()) if a != b)
    if n and apply:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new)
    return n


def main() -> int:
    apply = "--apply" in sys.argv
    # Resumable: a package is either still flat (old) or already moved (new).
    old = lambda p: (PKGS / p / "apm.yml").is_file()
    moved = lambda p: (PKGS / new_dir(p) / "apm.yml").is_file()
    missing = [p for p in FAMILY if not old(p) and not moved(p)]
    on_disk = sorted(d.name for d in PKGS.iterdir() if (d / "apm.yml").is_file())
    unmapped = [p for p in on_disk if p not in FAMILY]
    if missing or unmapped:
        print(f"REFUSED: missing={missing} unmapped={unmapped} (FAMILY is out of date)")
        return 1

    # 1. move (a folder locked by another process is reported and the run stops before rewriting)
    locked = []
    for pkg in FAMILY:
        if not old(pkg):
            continue
        print(f"mv packages/{pkg} -> packages/{new_dir(pkg)}")
        if apply:
            (PKGS / FAMILY[pkg]).mkdir(parents=True, exist_ok=True)
            try:
                git("mv", f"packages/{pkg}", f"packages/{new_dir(pkg)}")
            except subprocess.CalledProcessError as e:
                locked.append(f"{pkg}: {e.stderr.strip()}")
    if locked:
        print("NOT MOVED (close whatever holds these folders, then rerun with --apply):\n  "
              + "\n  ".join(locked))
        return 1

    # 2. dependency paths in each package's apm.yml and in README snippets of that package
    total = 0
    for pkg in FAMILY:
        root = PKGS / (new_dir(pkg) if moved(pkg) else pkg)
        for f in [root / "apm.yml", root / "README.md"]:
            if not f.is_file():
                continue
            n = rewrite(f, lambda t, pkg=pkg: DEP_PATH.subn(lambda m: m.group(1) + rel(pkg, m.group(2)), t), apply)
            if n:
                print(f"  {n:3d} dep path(s)  {f.relative_to(REPO).as_posix()}")
                total += n

    # 3. packages/<pkg> references in tracked text files
    files = git("ls-files").splitlines()
    for f in files:
        if f in SKIP_FILES or f.startswith(SKIP_PREFIXES) or Path(f).suffix.lower() not in TEXT_EXT:
            continue
        p = REPO / f
        if not p.is_file():
            continue
        n = rewrite(p, lambda t: PKG_REF.subn(lambda m: f"{m.group(1)}packages/{new_dir(m.group(2))}", t), apply)
        if n:
            print(f"  {n:3d} ref(s)       {f}")
            total += n
    print(f"{total} reference(s) {'rewritten' if apply else 'to rewrite'}")

    # 4. every dependency path must resolve
    if apply:
        bad = []
        for yml in PKGS.rglob("apm.yml"):
            # local dependencies only: `- path: ../x` list items (not comments, not git `path:` subfolders)
            for m in re.finditer(r"^\s*- path:\s*(\.\.?/\S+)", yml.read_text(encoding="utf-8"), re.M):
                if not (yml.parent / m.group(1)).resolve().joinpath("apm.yml").is_file():
                    bad.append(f"{yml.relative_to(REPO).as_posix()}: {m.group(1)}")
        for m in re.finditer(r"path:\s*(\./packages/\S+)", (REPO / "apm.yml").read_text(encoding="utf-8")):
            if not (REPO / m.group(1) / "apm.yml").is_file():
                bad.append(f"apm.yml: {m.group(1)}")
        if bad:
            print("UNRESOLVED:\n  " + "\n  ".join(bad))
            return 1
        print("OK every apm.yml path resolves")
    else:
        print("(dry run; add --apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
