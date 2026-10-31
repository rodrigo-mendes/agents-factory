#!/usr/bin/env python3
"""
Restore name: and description: on deployed .claude/rules/*.md files.

Confirmed bug (APM CLI v0.31.0, verified via a local spike install on
2026-09-25): the applyTo: -> paths: transform for the `claude` deploy target
drops every OTHER frontmatter field — name: and description: vanish, even
though the same source file deploys to .github/instructions/*.instructions.md
with all fields intact. `apm audit` does not catch this (it only flags
hidden-Unicode, not missing fields).

This breaks .claude/rules/skill-frontmatter.md's own schema, which lists
`name` as required and unique. Runtime behavior isn't affected -- Claude
Code's paths: mechanism doesn't need name/description to fire -- but every
rule loses its identity and its human-readable purpose.

Fix: after install, re-read name/description from the package source
(packages/**/.apm/instructions/*.instructions.md) and patch them back into
the matching deployed file, keyed by filename stem.

Wired up as a `lifecycle: post-install:` command in the root apm.yml. Needs
`apm lifecycle trust` once per clone before it runs.

If a future APM release fixes this upstream, this script becomes a no-op
(the second write will match what's already there) and can be deleted.
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGES = REPO_ROOT / "packages"  # sources always come from this repo


def deploy_root() -> Path:
    """`--root <dir>` patches <dir>/.claude/rules (e.g. an export sandbox); default: this repo."""
    if "--root" in sys.argv:
        return Path(sys.argv[sys.argv.index("--root") + 1]).resolve()
    return REPO_ROOT


ROOT = deploy_root()
DEPLOYED_RULES = ROOT / ".claude" / "rules"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def read_frontmatter(path: Path) -> tuple[str, str, str]:
    """Return (raw_frontmatter, body, full_text)."""
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return "", text, text
    return m.group(1), text[m.end():], text


def find_source(stem: str) -> Path | None:
    # packages/<family>[/<sub>]/<pkg>/.apm/... since the family reorganization (2026-10-31)
    matches = list(PACKAGES.glob(f"**/.apm/instructions/{stem}.instructions.md"))
    return matches[0] if matches else None


def main() -> int:
    if not DEPLOYED_RULES.is_dir():
        print("[restore-rule-metadata] .claude/rules/ not found -- nothing to do")
        return 0

    patched = 0
    for deployed in sorted(DEPLOYED_RULES.glob("*.md")):
        stem = deployed.stem
        source = find_source(stem)
        if source is None:
            print(f"[restore-rule-metadata] no source match for {deployed.name} -- skipped")
            continue

        src_front, _, _ = read_frontmatter(source)
        name_m = re.search(r'^name:\s*(.+)$', src_front, re.MULTILINE)
        desc_m = re.search(r'^description:\s*(.+)$', src_front, re.MULTILINE)
        if not name_m:
            print(f"[restore-rule-metadata] source {source.name} has no name: -- skipped")
            continue

        dep_front, dep_body, dep_full = read_frontmatter(deployed)
        if re.search(r'^name:', dep_front, re.MULTILINE):
            continue  # already has it -- APM fixed upstream, or already patched

        prefix_lines = [f"name: {name_m.group(1).strip()}"]
        if desc_m:
            prefix_lines.append(f"description: {desc_m.group(1).strip()}")
        new_front = "\n".join(prefix_lines) + "\n" + dep_front
        deployed.write_text(f"---\n{new_front}\n---\n{dep_body}", encoding="utf-8", newline="\n")
        patched += 1
        print(f"[restore-rule-metadata] patched {deployed.relative_to(ROOT)}")

    print(f"[restore-rule-metadata] done -- {patched} file(s) patched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
