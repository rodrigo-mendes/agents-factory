#!/usr/bin/env python3
"""
Check package and bundle manuals: their structure, their readability basics, and that every manual exists.

Every problem is written as a plain sentence that says what is wrong and how to fix it, so the person or
agent that reads it can act without opening this script.

Usage:
    python check_manual.py --root <repo> --file <README>   # one manual
    python check_manual.py --root <repo> --all             # every manual, plus the presence checks
    python check_manual.py --root <repo> --hook post-edit  # Claude Code PostToolUse hook (JSON on stdin)
    python check_manual.py --root <repo> --hook stop       # Claude Code Stop / SubagentStop hook
    add --skip-stale to --hook stop or --all when the generated tables are filled later (for example
    inside a writer agent, which must not run the generator)

Exit codes: 0 fine, 2 at least one problem (message on stderr, which Claude Code feeds back to Claude).
Warnings (for example numbers typed by hand in prose) are printed but never change the exit code.
Stdlib only. Layout comes from <repo>/docs-catalog.json (see docs_catalog.py).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_links as links  # noqa: E402
import docs_catalog as catalog  # noqa: E402

MIN_INTRO_CHARS = 60
COUNT_IN_PROSE = re.compile(r"\b\d+ (skills|agents|subagents|rules|packages|commands)\b", re.I)


def shown(path: Path) -> str:
    return path.relative_to(catalog.ROOT).as_posix() if path.is_relative_to(catalog.ROOT) else path.as_posix()


def section_body(text: str, heading_regex: str):
    """Body of the level-2 section whose heading matches, up to the next level-2 heading, or None."""
    m = re.search(heading_regex, text, re.M)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def intro_of(text: str) -> str:
    """Prose between the title and the first level-2 heading, without quotes, markers and blank lines."""
    lines = text.split("\n", 1)[1] if "\n" in text else ""
    head = re.split(r"^## ", lines, maxsplit=1, flags=re.M)[0]
    keep = [ln for ln in head.splitlines() if ln.strip() and not ln.startswith((">", "<!--"))]
    return " ".join(keep)


def check_markers(text: str, name: str) -> list:
    problems = []
    for block in re.findall(r"<!-- BEGIN GENERATED:([a-z-]+) -->", text):
        begin = text.find(f"<!-- BEGIN GENERATED:{block} -->")
        end = text.find(f"<!-- END GENERATED:{block} -->", begin)
        if end == -1:
            problems.append(f"{name}: the generated block '{block}' has a BEGIN marker but no END marker after it. "
                            f"Restore the END marker line exactly.")
    return problems


def check_package_manual(pkg, path: Path):
    text = path.read_text(encoding="utf-8")
    name, errors, warnings = shown(path), [], []
    if not text.startswith("# "):
        errors.append(f"{name}: the first line must be the title, '# {pkg.name}'.")
    if len(intro_of(text)) < MIN_INTRO_CHARS:
        errors.append(f"{name}: there is no opening paragraph. Under the title, say in two or three plain "
                      f"sentences what the package is, who it is for and when you need it.")
    positions = []
    for key, rx in catalog.REQUIRED_HEADINGS:
        m = re.search(rx, text, re.M)
        if not m:
            errors.append(f"{name}: the section for '{key}' is missing. Add a level-2 heading for it "
                          f"(see the manual template).")
        else:
            positions.append((m.start(), key))
    if positions != sorted(positions):
        warnings.append(f"{name}: the required sections are not in the usual order.")
    errors += check_markers(text, name)
    quick = section_body(text, r"^## .*Quick Start.*$")
    if quick is not None and "```" not in quick:
        errors.append(f"{name}: the Quick Start has no example. Show the shortest real invocation in a code block.")
    scenarios = section_body(text, r"^## .*Usage Scenarios.*$")
    if scenarios is not None:
        parts = re.split(r"^### ", scenarios, flags=re.M)[1:]
        if not parts:
            errors.append(f"{name}: Usage Scenarios has no scenario. Add '### Scenario 1 - ...' subsections.")
        if parts and "```" not in scenarios:
            errors.append(f"{name}: none of the scenarios has an example. Show at least the exact invocation in a code block.")
        for part in parts:
            if "```" not in part:  # chaining and misuse scenarios may be prose, so this only warns
                warnings.append(f"{name}: the scenario '{part.splitlines()[0][:60]}' has no code block; "
                                f"add the invocation if there is one.")
    for s in pkg.skills:
        if s.kind == "knowledge":
            continue
        shown_name = f"/{s.name}" if s.kind == "command" else s.name
        body = catalog.section_of(text, s.name)
        if body is None:
            errors.append(f"{name}: '{shown_name}' has no section. Add a heading that is exactly "
                          f"### `{shown_name}` with nothing after it, so the link #{s.name} works.")
            continue
        if "```" not in body:
            errors.append(f"{name}: the section of '{shown_name}' has no Syntax block (a fenced code block).")
        params = catalog.hint_params(s.argument_hint)
        if params and not re.search(r"\|\s*(Parameter|Argument)", body, re.I):
            errors.append(f"{name}: the section of '{shown_name}' has no parameter table "
                          f"(a table whose header starts with Parameter).")
        missing = [k for k in params if k not in catalog.table_text(body)]
        if missing:
            errors.append(f"{name}: the section of '{shown_name}' does not document: {', '.join(missing)}.")
    typed = COUNT_IN_PROSE.findall(re.sub(r"<!-- BEGIN.*?END GENERATED:[a-z-]+ -->", "", links.prose(text), flags=re.S))
    if typed:
        warnings.append(f"{name}: numbers of {', '.join(sorted(set(t.lower() for t in typed)))} are typed in the prose; "
                        f"they go stale. Put counts in a generated block instead.")
    errors += links.check_file(path, {})
    return errors, warnings


def check_bundle_readme(bundle, path: Path):
    text = path.read_text(encoding="utf-8")
    name, errors = shown(path), []
    if len(intro_of(text)) < MIN_INTRO_CHARS:
        errors.append(f"{name}: there is no opening paragraph describing the bundle.")
    if "<!-- BEGIN GENERATED:contents -->" not in text:
        errors.append(f"{name}: the generated 'contents' block is missing.")
    by_name = {p.name: p for p in catalog.discover_packages()}
    for dep in bundle.packages:
        pkg = by_name.get(dep)
        if pkg and catalog.rel_link(bundle.dir, pkg.dir / "README.md") not in text:
            errors.append(f"{name}: it does not link to the manual of '{dep}'.")
    errors += check_markers(text, name) + links.check_file(path, {})
    return errors


def classify(path: Path):
    path = path.resolve()
    for pkg in catalog.discover_packages():
        if (pkg.dir / "README.md").resolve() == path:
            return "package", pkg
    for b in catalog.discover_bundles():
        if (b.dir / "README.md").resolve() == path:
            return "bundle", b
    return None, None


def check_one(path: Path):
    kind, owner = classify(path)
    if kind == "package":
        return check_package_manual(owner, path)
    if kind == "bundle":
        return check_bundle_readme(owner, path), []
    return [], []


def check_presence(skip_stale: bool) -> list:
    """Every manual and every required page exists and is linked; generated tables are current."""
    errors, packages, bundles = [], catalog.discover_packages(), catalog.discover_bundles()
    for pkg in packages:
        if not (pkg.dir / "README.md").is_file():
            errors.append(f"{shown(pkg.dir)}: the package has no README.md manual. Write one from the template.")
    for b in bundles:
        if not (b.dir / "README.md").is_file():
            errors.append(f"{shown(b.dir)}: the bundle has no README.md. Write one from the bundle template.")
    for page in catalog.CONFIG["required_pages"]:
        if not (catalog.ROOT / page).is_file():
            errors.append(f"{page}: this required docs page does not exist.")
    index_file = next((rel for rel, ids in catalog.CONFIG["generated_targets"].items() if "entry-points" in ids), None)
    index_text = (catalog.ROOT / index_file).read_text(encoding="utf-8") if index_file and (catalog.ROOT / index_file).is_file() else ""
    guide_dir = catalog.ROOT / catalog.CONFIG["guide_pages_dir"]
    guides = "\n".join(p.read_text(encoding="utf-8") for p in sorted(guide_dir.glob("*.md"))
                       if p.name != "README.md") if guide_dir.is_dir() else ""
    for pkg in packages:
        entries = [s for s in pkg.skills if s.kind != "knowledge"]
        if not entries:
            continue
        for s in entries:
            if index_file and f"README.md#{s.name})" not in index_text:
                errors.append(f"{index_file}: '{s.name}' is not in the entry-point index. Run docs_catalog.py to regenerate it.")
        if guides and f"{pkg.rel}/README.md" not in guides:
            errors.append(f"{catalog.CONFIG['guide_pages_dir']}: no guide page links to the manual of '{pkg.name}', "
                          f"which has commands.")
    if not skip_stale:
        stale, _ = catalog.process_blocks(packages, bundles, write=False)
        errors += [f"{s}: this generated table is out of date. Run docs_catalog.py --root . to refresh it." for s in stale]
    return errors


def changed_manuals() -> list:
    """Package and bundle READMEs that are modified or new in the working tree."""
    try:
        out = subprocess.run(["git", "status", "--porcelain", "-uall"], cwd=catalog.ROOT, capture_output=True,
                             text=True, encoding="utf-8", errors="replace").stdout
    except OSError:
        return []
    paths = [catalog.ROOT / line[3:].split(" -> ")[-1].strip().strip('"') for line in out.splitlines() if len(line) > 3]
    return [p for p in paths if p.name == "README.md" and p.is_file() and classify(p)[0]]


def report(errors: list, warnings: list, header: str) -> int:
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if errors:
        print(header, file=sys.stderr)
        for e in errors[:40]:
            print(f"  - {e}", file=sys.stderr)
        if len(errors) > 40:
            print(f"  ... and {len(errors) - 40} more", file=sys.stderr)
        return 2
    return 0


def read_hook_input() -> dict:
    try:
        return json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    except (ValueError, OSError):
        return {}


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="repository to check (default: current folder)")
    ap.add_argument("--file", help="check one README")
    ap.add_argument("--all", action="store_true", help="check every manual and the presence of all of them")
    ap.add_argument("--hook", choices=["post-edit", "stop"], help="run as a Claude Code hook (JSON on stdin)")
    ap.add_argument("--skip-stale", action="store_true", help="do not fail on generated tables that are out of date")
    args = ap.parse_args(argv)
    catalog.configure(Path(args.root))

    if args.hook == "post-edit":
        data = read_hook_input()
        file_path = (data.get("tool_input") or {}).get("file_path")
        if not file_path:
            return 0
        path = Path(file_path)
        if not path.is_file() or classify(path)[0] is None:
            return 0  # not a manual: nothing to check, and no delay for normal editing
        errors, warnings = check_one(path)
        return report(errors, warnings, "This manual has problems. Fix them before going on:")

    if args.hook == "stop":
        data = read_hook_input()
        if data.get("stop_hook_active"):
            return 0  # already continuing because of this hook: never loop
        errors = check_presence(args.skip_stale)
        warnings = []
        for path in changed_manuals():
            e, w = check_one(path)
            errors += e
            warnings += w
        return report(errors, warnings, "The documentation is not finished. Fix these before you stop:")

    if args.file:
        errors, warnings = check_one(Path(args.file))
        if classify(Path(args.file))[0] is None:
            print(f"{args.file} is not a package or bundle README of this repository.", file=sys.stderr)
            return 2
        return report(errors, warnings, f"{args.file} has problems:")

    if args.all:
        errors, warnings = check_presence(args.skip_stale), []
        for pkg in catalog.discover_packages():
            if (pkg.dir / "README.md").is_file():
                e, w = check_package_manual(pkg, pkg.dir / "README.md")
                errors += e
                warnings += w
        for b in catalog.discover_bundles():
            if (b.dir / "README.md").is_file():
                errors += check_bundle_readme(b, b.dir / "README.md")
        rc = report(errors, warnings, "The documentation has problems:")
        if rc == 0:
            print("All manuals are present and well formed.")
        return rc

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
