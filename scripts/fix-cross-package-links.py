#!/usr/bin/env python3
"""
Defensive fixup for markdown links that APM's install-time link resolution
can rewrite into apm_modules/ paths.

Root cause found and fixed (2026-09-25): this repo's root apm.yml originally
declared a DIRECT dependency on packages/factory-core and packages/research-
core *as well as* every package that already depended on them transitively
(e.g. researching-frameworks -> ../factory-core). APM resolved the same
physical package via two different textual paths (./packages/factory-core
from root vs ../factory-core from a sibling), and `apm audit --ci` correctly
rejected this as "ambiguous resolved_by". As a side effect, the ambiguity
also confused APM's markdown-link rewriting: within-package links (e.g. an
agent linking to a skill in its own package) got rewritten into
`apm_modules/_local/<package>/.apm/...` instead of staying deploy-relative.

Fix applied: apm.yml's root dependency list no longer lists factory-core/
research-core directly -- they resolve transitively through the packages
that need them, with exactly one resolution path each. Verified this alone
resolves both the audit failure AND the link corruption (0 mismatches in a
byte-for-byte comparison of every deployed skill/agent against its package
source, on a fully clean install).

This script is kept as a defensive no-op safety net -- if a future change
reintroduces an ambiguous dependency graph (a new package added twice, a
path typo, etc.), this catches the resulting link corruption without anyone
needing to re-diagnose it. It should print "0 link(s) fixed" in the normal
case; if it ever prints more than that, treat it as a signal to re-check the
dependency graph in apm.yml and every packages/*/apm.yml for a duplicate
path to the same package.

Wired up as a `lifecycle: post-install:` command in the root apm.yml
(after restore-rule-metadata.py) and explicitly in CI (see
.github/workflows/apm.yml) since lifecycle did not auto-fire in testing.
"""
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_DIR = REPO_ROOT / ".claude"

# Matches: apm_modules/_local/<pkg-or-hash>/.apm/(agents|skills)/<rest>
BROKEN_LINK_RE = re.compile(
    r"(?:\.\./)*apm_modules/_local/[^/]+/\.apm/(agents|skills)/([^)\]\s]+)"
)


def target_path_under_claude(kind: str, rest: str) -> Path:
    if kind == "agents":
        # rest looks like "<name>.agent.md" (or "<name>.agent.md#anchor")
        name = rest.split("#")[0]
        anchor = rest[len(name):]
        stem = re.sub(r"\.agent\.md$", "", name)
        return CLAUDE_DIR / "agents" / f"{stem}.md{anchor}"
    else:  # skills
        return CLAUDE_DIR / "skills" / rest


def fix_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")

    def repl(m: re.Match) -> str:
        kind, rest = m.group(1), m.group(2)
        target = target_path_under_claude(kind, rest)
        target_no_anchor = Path(str(target).split("#")[0])
        anchor = str(target)[len(str(target_no_anchor)):]
        rel = os.path.relpath(target_no_anchor, start=path.parent)
        return rel + anchor

    new_text, n = BROKEN_LINK_RE.subn(repl, text)
    if n:
        path.write_text(new_text, encoding="utf-8")
    return n


def main() -> int:
    if not CLAUDE_DIR.is_dir():
        print("[fix-cross-package-links] .claude/ not found -- nothing to do")
        return 0

    total_files = 0
    total_fixes = 0
    candidates = list((CLAUDE_DIR / "agents").glob("*.md")) if (CLAUDE_DIR / "agents").is_dir() else []
    if (CLAUDE_DIR / "skills").is_dir():
        candidates += list((CLAUDE_DIR / "skills").rglob("*.md"))

    for f in candidates:
        n = fix_file(f)
        if n:
            total_files += 1
            total_fixes += n
            print(f"[fix-cross-package-links] fixed {n} link(s) in {f.relative_to(REPO_ROOT)}")

    print(f"[fix-cross-package-links] done -- {total_fixes} link(s) fixed across {total_files} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
