#!/usr/bin/env python3
"""
Generate the catalog blocks of the documentation from the sources in packages/.

Counts, package tables and per-family tables are derived from the files, never typed by hand.
Only text between markers is rewritten:

    <!-- BEGIN GENERATED:<id> -->
    ...
    <!-- END GENERATED:<id> -->

Targets and repository layout come from an optional `docs-catalog.json` at the repository root (see
DEFAULT_CONFIG for the keys and the defaults). Package and bundle READMEs opt in to the per-package
blocks (`contents`, `installation`, `agents-reference`) by carrying their markers.

Usage:
    python docs_catalog.py --root <repo>                  # rewrite the generated blocks
    python docs_catalog.py --root <repo> --check          # exit 1 if any block is stale
    python docs_catalog.py --root <repo> --check-manuals  # coverage matrix; exit 1 on gaps

Stdlib only. Bundles are not packages and are excluded from the counts.
"""
import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Layout of the repository this script documents. Every key can be overridden in <root>/docs-catalog.json.
DEFAULT_CONFIG = {
    "packages_dir": "packages",
    "bundles_dir": "packages/bundles",
    "docs_dir": "docs",
    # Entry points that run inline (no `context: fork`): nothing in their frontmatter marks them.
    "inline_orchestrators": [
        "building-aws-saas-serverless-quarkus-react-nextjs",
        "bootstrapping-spec-from-poc",
        "building-agent-packages",
        "integrating-camel-quarkus",
        "documenting-agent-packages",
    ],
    "generated_targets": {
        "README.md": ["totals"],
        "docs/packages/README.md": ["packages-by-family", "bundles"],
        "docs/entry-points/README.md": ["entry-points"],
        "docs/agents/README.md": ["agents-roster", "agents-tools"],
    },
    "required_pages": [
        "docs/README.md",
        "docs/packages/README.md",
        "docs/entry-points/README.md",
        "docs/agents/README.md",
    ],
    "guide_pages_dir": "docs/entry-points",
}

ROOT = Path.cwd()
CONFIG = dict(DEFAULT_CONFIG)
PACKAGES = ROOT / CONFIG["packages_dir"]
BUNDLES_DIR = ROOT / CONFIG["bundles_dir"]
INLINE_ORCHESTRATORS = set(CONFIG["inline_orchestrators"])
TARGETS = {}


def configure(root: Path) -> None:
    """Point the module at a repository: read its docs-catalog.json (if any) and set the globals."""
    global ROOT, CONFIG, PACKAGES, BUNDLES_DIR, INLINE_ORCHESTRATORS, TARGETS
    ROOT = Path(root).resolve()
    CONFIG = dict(DEFAULT_CONFIG)
    cfg_file = ROOT / "docs-catalog.json"
    if cfg_file.is_file():
        CONFIG.update(json.loads(cfg_file.read_text(encoding="utf-8")))
    PACKAGES = ROOT / CONFIG["packages_dir"]
    BUNDLES_DIR = ROOT / CONFIG["bundles_dir"]
    INLINE_ORCHESTRATORS = set(CONFIG["inline_orchestrators"])
    TARGETS = {ROOT / rel: list(ids) for rel, ids in CONFIG["generated_targets"].items()}


@dataclass
class Skill:
    name: str
    path: Path
    description: str
    kind: str  # command | orchestrator | knowledge
    context: str = ""
    agent: str = ""
    argument_hint: str = ""


@dataclass
class Agent:
    name: str
    path: Path
    description: str
    model: str = ""
    tools: str = ""


@dataclass
class Package:
    name: str
    rel: str  # path relative to packages/
    family: str
    skills: list = field(default_factory=list)
    agents: list = field(default_factory=list)
    rules: list = field(default_factory=list)
    rule_files: list = field(default_factory=list)
    dependencies: list = field(default_factory=list)
    dir: Path = None


def read_frontmatter(path: Path) -> dict:
    """Minimal front-matter reader: scalar keys, folded (>) and quoted values. Lists are ignored."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data, key, buf = {}, None, []

    def flush():
        if key is not None:
            value = " ".join(s.strip() for s in buf if s.strip())
            data[key] = value.strip().strip('"').strip("'")

    for line in text[3:end].splitlines():
        top = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if top:
            flush()
            key, buf = top.group(1), []
            rest = top.group(2)
            if rest not in ("", ">", "|", ">-", "|-"):
                buf.append(rest)
        elif key is not None and line[:1] in (" ", "\t"):
            buf.append(line)
    flush()
    return data


def _dep_name(value: str) -> str:
    return re.sub(r"\.git$", "", value.strip().strip("'\"").rstrip("/").split("/")[-1])


def parse_dependencies(apm_yml: Path) -> list:
    """Names of the `dependencies.apm` entries, as the package folder name.

    Accepted forms: `- ../x`, `- path: ../x`, `- git: <url>`, and the object form where `path:` (the package
    folder inside the repo) and `ref:` follow `- git: <url>` on their own lines. When an entry has a `path`,
    its last segment is the name; otherwise the last segment of the url or plain value."""
    deps, in_deps, in_apm, current = [], False, False, None

    def close():
        if current:
            deps.append(_dep_name(current.get("path") or current.get("git") or current.get("_value", "")))

    for raw in apm_yml.read_text(encoding="utf-8").splitlines():
        line = raw.split(" #", 1)[0].rstrip() if not raw.lstrip().startswith("#") else ""
        if re.match(r"^dependencies:\s*$", line):
            in_deps = True
            continue
        if not in_deps or not line:
            continue
        if not line.startswith(" "):
            break
        key = re.match(r"^\s{1,4}([a-z]+):\s*(\[\])?\s*$", line)
        if key:  # `apm:` or `mcp:` section header
            close()
            current = None
            in_apm = key.group(1) == "apm"
            continue
        if not in_apm:
            continue
        item = re.match(r"^\s*-\s*(?:([a-z]+):\s*)?(\S+)\s*$", line)
        if item:
            close()
            current = {item.group(1): item.group(2)} if item.group(1) else {"_value": item.group(2)}
            continue
        field_ = re.match(r"^\s+([a-z]+):\s*(\S+)\s*$", line)
        if field_ and current is not None:
            current[field_.group(1)] = field_.group(2)
    close()
    return deps


def read_apm_meta(apm_yml: Path) -> dict:
    """name, version and (possibly folded) description of an apm.yml."""
    meta, key, buf = {}, None, []

    def flush():
        if key is not None:
            meta[key] = " ".join(s.strip() for s in buf if s.strip()).strip('"').strip("'")

    for line in apm_yml.read_text(encoding="utf-8").splitlines():
        top = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if top:
            flush()
            key, buf = top.group(1), []
            if top.group(2) not in ("", ">", ">-", "|", "|-"):
                buf.append(top.group(2))
        elif key == "description" and line[:1] in (" ", "\t"):
            buf.append(line)
    flush()
    return meta


def read_export_spec(path: Path) -> dict:
    """Subset of export.yml: scalar fields (agents/skills/rules) and `- item` or `[a, b]` lists."""
    spec, key = {}, None
    if not path.exists():
        return spec
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if m and not line.startswith(" "):
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("["):
                spec[key] = [v.strip() for v in val.strip("[]").split(",") if v.strip()]
            else:
                spec[key] = val if val else []
            continue
        item = re.match(r"^\s*-\s*(\S+)", line)
        if item and key is not None:
            if not isinstance(spec[key], list):
                spec[key] = [spec[key]]
            spec[key].append(item.group(1))
    return spec


def family_of(rel: str) -> str:
    parts = rel.split("/")
    return parts[0] if len(parts) > 1 else "root"


def _md_files(folder: Path, pattern: str):
    return sorted(folder.glob(pattern)) if folder.is_dir() else []


def discover_packages() -> list:
    packages = []
    for apm_yml in sorted(PACKAGES.rglob("apm.yml")):
        rel_dir = apm_yml.parent.relative_to(PACKAGES)
        if ".apm" in rel_dir.parts or apm_yml.parent.resolve().is_relative_to(BUNDLES_DIR.resolve()):
            continue
        rel = rel_dir.as_posix()
        pkg = Package(name=rel_dir.name, rel=rel, family=family_of(rel),
                      dependencies=parse_dependencies(apm_yml))
        apm = apm_yml.parent / ".apm"
        for skill_md in _md_files(apm / "skills", "*/SKILL.md"):
            fm = read_frontmatter(skill_md)
            name = fm.get("name") or skill_md.parent.name
            if fm.get("disable-model-invocation") == "true":
                kind = "command"
            elif name in INLINE_ORCHESTRATORS:
                kind = "orchestrator"
            else:
                kind = "knowledge"
            pkg.skills.append(Skill(name, skill_md, fm.get("description", ""), kind,
                                    fm.get("context", ""), fm.get("agent", ""),
                                    fm.get("argument-hint", "")))
        for agent_md in _md_files(apm / "agents", "*.md"):
            fm = read_frontmatter(agent_md)
            pkg.agents.append(Agent(fm.get("name") or agent_md.stem, agent_md,
                                    fm.get("description", ""), fm.get("model", ""), fm.get("tools", "")))
        for rule_md in _md_files(apm / "instructions", "*.md"):
            pkg.rules.append(rule_md.stem)
            pkg.rule_files.append(rule_md)
        pkg.dir = apm_yml.parent
        packages.append(pkg)
    return packages


KIND_KEYS = {"command": "commands", "orchestrator": "orchestrators", "knowledge": "knowledge"}


def counts(packages: list) -> dict:
    c = {"packages": len(packages), "skills": 0, "commands": 0, "orchestrators": 0,
         "knowledge": 0, "agents": 0, "rules": 0}
    for p in packages:
        c["skills"] += len(p.skills)
        c["agents"] += len(p.agents)
        c["rules"] += len(p.rules)
        for s in p.skills:
            c[KIND_KEYS[s.kind]] += 1
    return c


def render_totals(c: dict) -> str:
    return "\n".join([
        "| Artifact | Count |",
        "|---|---|",
        f"| Packages (APM, `packages/`) | {c['packages']} |",
        f"| Skills (total) | {c['skills']} |",
        f"|  - entry-point commands (`/name`) | {c['commands']} |",
        f"|  - inline orchestrators | {c['orchestrators']} |",
        f"|  - knowledge (auto-invoked) | {c['knowledge']} |",
        f"| Subagents | {c['agents']} |",
        f"| Rules (instructions) | {c['rules']} |",
    ])


def render_packages(packages: list) -> str:
    lines = ["| Package | Skills | Agents | Rules | Depends on |", "|---|---|---|---|---|"]
    for p in packages:
        deps = ", ".join(f"`{d}`" for d in p.dependencies) or "-"
        lines.append(f"| `{p.name}` (`{p.rel}`) | {len(p.skills)} | {len(p.agents)} | {len(p.rules)} | {deps} |")
    return "\n".join(lines)


def render_by_family(packages: list) -> str:
    out, current = [], None
    for p in packages:
        if p.family != current:
            current = p.family
            if out:
                out.append("")
            out += [f"### {current}", "", "| Package | Commands | Orchestrators | Knowledge | Agents | Rules |",
                    "|---|---|---|---|---|---|"]
        cmds = sum(s.kind == "command" for s in p.skills)
        orch = sum(s.kind == "orchestrator" for s in p.skills)
        kn = sum(s.kind == "knowledge" for s in p.skills)
        out.append(f"| `{p.name}` | {cmds} | {orch} | {kn} | {len(p.agents)} | {len(p.rules)} |")
    return "\n".join(out)


def first_sentence(text: str, limit: int = 160) -> str:
    text = " ".join(text.split())
    cut = text.find(". ")
    if cut != -1:
        text = text[:cut + 1]
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|") or "-"


def render_entry_points(packages: list) -> str:
    rows = []
    for p in packages:
        for s in p.skills:
            if s.kind == "knowledge":
                continue
            kind = "command" if s.kind == "command" else "inline orchestrator"
            rows.append((p.rel, p.name, s, kind))
    lines = ["| Entry point | Kind | Package | Runs as | Routes to | Arguments | What it does |",
             "|---|---|---|---|---|---|---|"]
    for rel, pkg, s, kind in rows:
        runs = "fork (subagent)" if s.context == "fork" else "inline in your session"
        routed = f"`{s.agent}`" if s.agent else "-"
        shown = f"/{s.name}" if s.kind == "command" else s.name
        name = f"[`{shown}`](../../packages/{rel}/README.md#{s.name})"
        hint = cell(f"`{s.argument_hint}`") if s.argument_hint else "-"
        lines.append(f"| {name} | {kind} | `{pkg}` | {runs} | {routed} | {hint} | {cell(first_sentence(s.description))} |")
    return "\n".join(lines)


def render_agents_roster(packages: list) -> str:
    routed = {}
    for p in packages:
        for s in p.skills:
            if s.agent:
                routed.setdefault(s.agent, []).append(f"/{s.name}")
    lines = ["| Agent | Package | Model | Started by | What it does |", "|---|---|---|---|---|"]
    for p in packages:
        for a in p.agents:
            cmds = routed.get(a.name, [])
            started = ", ".join(f"`{c}`" for c in cmds[:3]) + (f" +{len(cmds) - 3} more" if len(cmds) > 3 else "")
            lines.append(f"| `{a.name}` | `{p.name}` | {a.model or 'inherit'} | {started or 'other agents or an orchestrator'} "
                         f"| {cell(first_sentence(a.description, 200))} |")
    return "\n".join(lines)


def render_agents_tools(packages: list) -> str:
    tools = ["Read", "Grep", "Glob", "Edit", "Write", "Bash", "WebSearch", "WebFetch", "Agent"]
    lines = ["| Agent | " + " | ".join(tools) + " |", "|---|" + "---|" * len(tools)]
    for p in packages:
        for a in p.agents:
            have = {t.strip() for t in a.tools.split(",")}
            lines.append(f"| `{a.name}` | " + " | ".join("x" if t in have else "" for t in tools) + " |")
    return "\n".join(lines)


def bundle_dependencies() -> dict:
    """Map package name -> bundles (packages/bundles/*) that list it as a dependency."""
    used = {}
    for apm_yml in sorted(BUNDLES_DIR.glob("*/apm.yml")) if BUNDLES_DIR.is_dir() else []:
        for dep in parse_dependencies(apm_yml):
            used.setdefault(dep, []).append(apm_yml.parent.name)
    return used


def render_package_contents(pkg: Package, packages: list, bundles: dict) -> str:
    users = sorted(p.name for p in packages if pkg.name in p.dependencies)
    deps = ", ".join(f"`{d}`" for d in pkg.dependencies) or "none"
    bundle_links = [f"[`{b}`]({rel_link(pkg.dir, BUNDLES_DIR / b / 'README.md')}) (bundle)"
                    for b in bundles.get(pkg.name, [])]
    used = ", ".join([f"`{u}`" for u in users] + bundle_links) or "none"
    lines = [f"**Depends on:** {deps}  ", f"**Used by:** {used}", "",
             "| Type | Name | What it does |", "|---|---|---|"]

    def link(path: Path) -> str:
        return path.relative_to(pkg.dir).as_posix()

    labels = {"command": "command", "orchestrator": "inline orchestrator", "knowledge": "knowledge skill"}
    for s in sorted(pkg.skills, key=lambda x: (["command", "orchestrator", "knowledge"].index(x.kind), x.name)):
        shown = f"/{s.name}" if s.kind == "command" else s.name
        lines.append(f"| {labels[s.kind]} | [`{shown}`]({link(s.path)}) | {cell(first_sentence(s.description))} |")
    for a in pkg.agents:
        model = f" ({a.model})" if a.model else ""
        lines.append(f"| agent{model} | [`{a.name}`]({link(a.path)}) | {cell(first_sentence(a.description))} |")
    for rule_path in pkg.rule_files:
        fm = read_frontmatter(rule_path)
        lines.append(f"| rule | [`{rule_path.stem}`]({link(rule_path)}) | {cell(first_sentence(fm.get('description', '')))} |")
    if len(lines) == 6:
        lines.append("| - | (no skills, agents or rules; see the package notes) | - |")
    return "\n".join(lines)


@dataclass
class Bundle:
    name: str
    dir: Path
    description: str
    packages: list
    spec: dict


def discover_bundles() -> list:
    root = BUNDLES_DIR
    out = []
    for apm_yml in sorted(root.glob("*/apm.yml")) if root.is_dir() else []:
        meta = read_apm_meta(apm_yml)
        out.append(Bundle(apm_yml.parent.name, apm_yml.parent, meta.get("description", ""),
                          parse_dependencies(apm_yml), read_export_spec(apm_yml.parent / "export.yml")))
    return out


def rel_link(src_dir: Path, target: Path) -> str:
    return Path(os.path.relpath(target, src_dir)).as_posix()


def dependency_closure(pkg: Package, by_name: dict) -> list:
    """Every package pulled in by pkg, directly or transitively (names, in discovery order)."""
    seen, queue = [], list(pkg.dependencies)
    while queue:
        dep = queue.pop(0)
        if dep in seen or dep == pkg.name:
            continue
        seen.append(dep)
        if dep in by_name:
            queue.extend(by_name[dep].dependencies)
    return seen


def routed_commands(packages: list) -> dict:
    routed = {}
    for p in packages:
        for s in p.skills:
            if s.agent:
                routed.setdefault(s.agent, []).append(f"/{s.name}")
    return routed


def render_installation(pkg: Package, packages: list, root_direct: set) -> str:
    meta = read_apm_meta(pkg.dir / "apm.yml")
    by_name = {p.name: p for p in packages}
    users = sorted(p.name for p in packages if pkg.name in p.dependencies)
    if pkg.name in root_direct:
        where = "listed directly in the root `apm.yml`"
    elif users:
        where = "installed transitively, through " + ", ".join(f"`{u}`" for u in users)
    else:
        where = "not in the root `apm.yml`; install it on its own or through a bundle"
    also = ", ".join(f"`{d}`" for d in dependency_closure(pkg, by_name)) or "nothing"
    lines = ["| Item | Value |", "|---|---|",
             f"| Package name | `{meta.get('name', pkg.name)}` |",
             f"| Version | `{meta.get('version', '-')}` |",
             f"| Source folder | `packages/{pkg.rel}` |",
             f"| In this repository | {where} |",
             f"| Also installs | {also} |", "",
             "Install it into another project, from that project's folder:", "",
             "```bash",
             f"apm install <path-to-agents-factory>/packages/{pkg.rel} --target claude",
             "```", "",
             "Add `--dry-run` to preview the install. APM writes the skills, agents and rules into "
             "`.claude/`. Change the sources under `.apm/`, never the generated `.claude/`."]
    return "\n".join(lines)


def render_agents_reference(pkg: Package, routed: dict) -> str:
    if not pkg.agents:
        return ("This package has no subagents. Claude loads its skills by description, and agents of "
                "other packages can load them too.")
    lines = ["| Agent | Model | Tools | Can start agents | Started by |", "|---|---|---|---|---|"]
    for a in pkg.agents:
        tools = [t.strip() for t in a.tools.split(",") if t.strip()]
        started = ", ".join(f"`{c}`" for c in routed.get(a.name, [])) or "an orchestrator or another agent"
        lines.append(f"| [`{a.name}`]({rel_link(pkg.dir, a.path)}) | {a.model or 'inherit'} | "
                     f"{', '.join(tools)} | {'yes' if 'Agent' in tools else 'no'} | {started} |")
    return "\n".join(lines)


def render_bundle_contents(b: Bundle, packages: list) -> str:
    by_name = {p.name: p for p in packages}
    direct = [by_name[n] for n in b.packages if n in by_name]
    extra = []
    for p in direct:
        for d in dependency_closure(p, by_name):
            if d in by_name and d not in b.packages and d not in extra:
                extra.append(d)
    installed = direct + [by_name[n] for n in extra]

    def pkg_link(p: Package) -> str:
        return f"[`{p.name}`]({rel_link(b.dir, p.dir / 'README.md')})"

    lines = ["**Packages included:** " + (", ".join(pkg_link(p) for p in direct) or "none")]
    if extra:
        lines.append("**Also installed as dependencies:** " + ", ".join(pkg_link(by_name[n]) for n in extra))
    if b.spec:
        lines += ["", "> **Sold as a subset.** The exported package keeps only what `export.yml` selects. "
                      "The table below lists what the packages provide, so the sold subset is narrower."]
        for key in ("agents", "skills", "rules", "include", "exclude"):
            if key in b.spec:
                value = b.spec[key]
                shown = ", ".join(f"`{x}`" for x in value) if isinstance(value, list) else f"`{value}`"
                lines.append(f"> - {key}: {shown}")
    lines += ["", "| Type | Entry point or agent | Package |", "|---|---|---|"]
    for p in installed:
        readme = rel_link(b.dir, p.dir / "README.md")
        for s in p.skills:
            if s.kind == "knowledge":
                continue
            shown = f"/{s.name}" if s.kind == "command" else s.name
            kind = "command" if s.kind == "command" else "inline orchestrator"
            lines.append(f"| {kind} | [`{shown}`]({readme}#{s.name}) | `{p.name}` |")
        for a in p.agents:
            lines.append(f"| agent | [`{a.name}`]({rel_link(b.dir, a.path)}) | `{p.name}` |")
    knowledge = sum(1 for p in installed for s in p.skills if s.kind == "knowledge")
    lines += ["", f"Plus {knowledge} knowledge skills that Claude loads by description. "
                  "Each package manual lists them."]
    return "\n".join(lines)


def render_bundles_table(bundles: list) -> str:
    lines = ["| Bundle | Packages | Subset export |", "|---|---|---|"]
    for b in bundles:
        link = rel_link(ROOT / CONFIG["docs_dir"] / "packages", b.dir / "README.md")
        packages = ", ".join(f"`{n}`" for n in b.packages) or "-"
        lines.append(f"| [`{b.name}`]({link}) | {packages} | {'yes' if b.spec else 'no'} |")
    return "\n".join(lines)


# --------------------------------------------------------------------------- manual completeness
REQUIRED_HEADINGS = [
    ("Installation", r"^## .*Installation"),
    ("Quick Start", r"^## .*Quick Start"),
    ("Usage Scenarios", r"^## .*Usage Scenarios"),
    ("Reference", r"^## .*(Commands Reference|Skills Reference)"),
    ("Architecture", r"^## .*(Pipeline|Architecture)"),
    ("Agents Reference", r"^## .*Agents Reference"),
    ("Limits", r"^## .*(Limits|Constraints)"),
    ("Related", r"^## .*Related"),
]


def hint_params(hint: str) -> list:
    """`key=` parameters and `--flags` named in an argument-hint (positional words are free text)."""
    keys = set(re.findall(r"(?<![\w.-])([A-Za-z_][\w.-]*)=", hint))
    keys |= set(re.findall(r"(--[A-Za-z][\w-]*)", hint))
    return sorted(keys)


def section_of(text: str, name: str):
    """Body of the level-3/4 heading that is exactly the entry point `name` (`### \\`/name\\``), or None.
    The heading carries nothing else, so its GitHub anchor is simply `#name`."""
    pattern = re.compile(rf"^(#{{3,4}}) +`/?{re.escape(name)}`[ \t]*$", re.M)
    m = pattern.search(text)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(rf"^#{{1,{len(m.group(1))}}} ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def table_text(body: str) -> str:
    """Only the table rows of a section: a parameter counts as documented when it is in a table, not just in the syntax line."""
    return "\n".join(l for l in body.splitlines() if l.lstrip().startswith("|"))


def check_manuals(packages: list, bundles: list):
    problems = []
    have = {key: 0 for key, _ in REQUIRED_HEADINGS}
    entries = documented = 0
    for p in packages:
        readme = p.dir / "README.md"
        text = readme.read_text(encoding="utf-8") if readme.exists() else ""
        for key, rx in REQUIRED_HEADINGS:
            if re.search(rx, text, re.M):
                have[key] += 1
            else:
                problems.append(f"{p.name}: missing section '{key}'")
        for s in p.skills:
            if s.kind == "knowledge":
                continue
            entries += 1
            body = section_of(text, s.name)
            if body is None:
                problems.append(f"{p.name}: no section for {s.name}")
                continue
            issues = []
            if "```" not in body:
                issues.append("no Syntax block")
            params = hint_params(s.argument_hint)
            if params and not re.search(r"\|\s*(Parameter|Argument)", body, re.I):
                issues.append("no parameter table")
            missing = [k for k in params if k not in table_text(body)]
            if missing:
                issues.append("parameters not documented: " + ", ".join(missing))
            if issues:
                problems.append(f"{p.name}: {s.name}: " + "; ".join(issues))
            else:
                documented += 1
    for b in bundles:
        readme = b.dir / "README.md"
        if not readme.exists():
            problems.append(f"bundle {b.name}: README.md missing")
        elif "<!-- BEGIN GENERATED:contents -->" not in readme.read_text(encoding="utf-8"):
            problems.append(f"bundle {b.name}: README.md has no generated contents block")
    return have, entries, documented, problems


def render_blocks(packages: list) -> dict:
    return {"totals": render_totals(counts(packages)),
            "packages": render_packages(packages),
            "packages-by-family": render_by_family(packages),
            "entry-points": render_entry_points(packages),
            "agents-roster": render_agents_roster(packages),
            "agents-tools": render_agents_tools(packages),
            "bundles": render_bundles_table(discover_bundles())}


def replace_block(text: str, block_id: str, body: str):
    pattern = re.compile(
        rf"(<!-- BEGIN GENERATED:{re.escape(block_id)} -->\n)(.*?)\n?(<!-- END GENERATED:{re.escape(block_id)} -->)",
        re.DOTALL)
    if not pattern.search(text):
        return text, False
    return pattern.sub(lambda m: m.group(1) + body + "\n" + m.group(3), text, count=1), True


def process_blocks(packages: list, bundle_list: list, write: bool):
    """Render every generated block and replace it in its file. Returns (stale, skipped): the blocks whose
    text differed (rewritten when `write` is true) and the targets that were missing or had no markers."""
    blocks = render_blocks(packages)
    bundles = bundle_dependencies()
    root_direct = set(parse_dependencies(ROOT / "apm.yml")) if (ROOT / "apm.yml").exists() else set()
    routed = routed_commands(packages)
    targets = dict(TARGETS)
    package_blocks = {}
    for pkg in packages:  # package READMEs opt in to each block by carrying its marker
        readme = pkg.dir / "README.md"
        if not readme.exists():
            continue
        text = readme.read_text(encoding="utf-8")
        wanted = {
            "contents": lambda: render_package_contents(pkg, packages, bundles),
            "installation": lambda: render_installation(pkg, packages, root_direct),
            "agents-reference": lambda: render_agents_reference(pkg, routed),
        }
        ids = [b for b in wanted if f"<!-- BEGIN GENERATED:{b} -->" in text]
        if ids:
            targets[readme] = ids
            package_blocks[readme] = {b: wanted[b]() for b in ids}
    for b in bundle_list:  # bundle READMEs carry the same `contents` marker
        readme = b.dir / "README.md"
        if readme.exists() and "<!-- BEGIN GENERATED:contents -->" in readme.read_text(encoding="utf-8"):
            targets[readme] = ["contents"]
            package_blocks[readme] = {"contents": render_bundle_contents(b, packages)}
    stale, skipped = [], []
    for path, ids in targets.items():
        rel = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()
        if not path.exists():
            skipped.append(f"{rel} (file not found)")
            continue
        original = path.read_text(encoding="utf-8")
        text = original
        for block_id in ids:
            body = package_blocks.get(path, {}).get(block_id) or blocks[block_id]
            text, found = replace_block(text, block_id, body)
            if not found:
                skipped.append(f"{rel} (no markers for '{block_id}')")
            elif text != original:
                stale.append(f"{rel}:{block_id}")
        if write and text != original:
            path.write_text(text, encoding="utf-8", newline="\n")
    return stale, skipped


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="exit 1 if any generated block is stale")
    ap.add_argument("--check-manuals", action="store_true",
                    help="print the manual coverage matrix; exit 1 if a README lacks a required section or "
                         "an entry point lacks a Syntax block and parameter table")
    ap.add_argument("--root", default=".", help="repository to document (default: current folder)")
    args = ap.parse_args(argv)
    configure(Path(args.root))

    packages = discover_packages()
    bundle_list = discover_bundles()
    if args.check_manuals:
        have, entries, documented, problems = check_manuals(packages, bundle_list)
        print(f"Manual coverage ({len(packages)} packages, {len(bundle_list)} bundles)")
        for key, n in have.items():
            print(f"  {key:18s} {n}/{len(packages)}")
        print(f"  {'Entry points':18s} {documented}/{entries} with Syntax block and parameter table")
        for line in problems[:80]:
            print(f"  - {line}")
        if len(problems) > 80:
            print(f"  ... and {len(problems) - 80} more")
        return 1 if problems else 0

    stale, skipped = process_blocks(packages, bundle_list, write=not args.check)

    for s in skipped:
        print(f"skipped: {s}", file=sys.stderr)
    if args.check:
        for s in stale:
            print(f"stale: {s}", file=sys.stderr)
        return 1 if stale else 0
    print(f"updated {len(stale)} block(s)" if stale else "all generated blocks up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
