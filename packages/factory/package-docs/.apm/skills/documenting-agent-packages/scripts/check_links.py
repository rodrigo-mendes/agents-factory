#!/usr/bin/env python3
"""
Check every relative link and #anchor in the manuals and docs pages.

Looks at: the root README.md, every .md file under the docs folder, and every package and bundle README
(folders named .apm are skipped). Code blocks and inline code are ignored, so examples such as
`![x](assets/y.png)` are not treated as links. Anchors follow the GitHub rule: lower case, punctuation
removed, spaces turned into hyphens, repeated headings numbered -1, -2.

Usage:
    python check_links.py --root <repo>              # check the default set of files
    python check_links.py --root <repo> FILE [FILE]  # check only these files

Exit codes: 0 every link and anchor resolves, 1 at least one is broken.
Stdlib only. Layout comes from <repo>/docs-catalog.json (see docs_catalog.py).
"""
import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import docs_catalog as catalog  # noqa: E402

LINK = re.compile(r"\]\(([^)\s]+)\)")
HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$", re.M)


def strip_fences(text: str) -> str:
    """Drop fenced code blocks. Only lines that START with ``` open or close a fence, so a ``` written
    inside a table cell or a sentence does not confuse the pairing."""
    out, inside = [], False
    for line in text.splitlines():
        if re.match(r"^\s*```", line):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


def prose(text: str) -> str:
    return re.sub(r"`[^`\n]*`", "``", strip_fences(text))


def slugs(text: str) -> set:
    seen, found = {}, set()
    for m in HEADING.finditer(strip_fences(text)):
        heading = re.sub(r"`", "", m.group(1))
        heading = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
        slug = re.sub(r"[^\w\- ]", "", heading.lower(), flags=re.UNICODE).replace(" ", "-")
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        found.add(slug if n == 0 else f"{slug}-{n}")
    return found


def check_file(path: Path, cache: dict) -> list:
    """Problems in one file, each a plain sentence naming the link."""
    problems = []
    shown = path.relative_to(catalog.ROOT).as_posix() if path.is_relative_to(catalog.ROOT) else path.as_posix()
    for m in LINK.finditer(prose(path.read_text(encoding="utf-8"))):
        target = m.group(1)
        if target.startswith(("http", "mailto", "<")):
            continue
        rel, _, frag = target.partition("#")
        dest = (path.parent / rel).resolve() if rel else path.resolve()
        if not dest.exists():
            problems.append(f"{shown}: the link '{target}' points to a file that does not exist.")
            continue
        if frag and dest.suffix == ".md":
            if dest not in cache:
                cache[dest] = slugs(dest.read_text(encoding="utf-8"))
            if frag not in cache[dest]:
                problems.append(f"{shown}: the link '{target}' points to a heading that does not exist.")
    return problems


def default_files() -> list:
    root = catalog.ROOT
    files = [root / "README.md"] if (root / "README.md").is_file() else []
    docs = root / catalog.CONFIG["docs_dir"]
    files += sorted(docs.rglob("*.md")) if docs.is_dir() else []
    pkgs = root / catalog.CONFIG["packages_dir"]
    files += [p for p in sorted(pkgs.rglob("README.md")) if ".apm" not in p.parts] if pkgs.is_dir() else []
    return files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="repository to check (default: current folder)")
    ap.add_argument("files", nargs="*", help="check only these files")
    args = ap.parse_args(argv)
    catalog.configure(Path(args.root))
    files = [Path(f).resolve() for f in args.files] if args.files else default_files()
    cache, problems = {}, []
    for f in files:
        problems += check_file(f, cache)
    print(f"{len(files)} files checked, {len(problems)} broken link(s).")
    for p in problems[:60]:
        print(f"  - {p}")
    if len(problems) > 60:
        print(f"  ... and {len(problems) - 60} more")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
