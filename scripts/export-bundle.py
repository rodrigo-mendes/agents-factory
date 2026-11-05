#!/usr/bin/env python3
"""
Export a sales bundle (packages/bundles/<name>/) as the COMPILED TARGET DIRECTORY that APM produces,
filtered, as a folder (SkillHQ) and a zip (Agensi). Dry run by default; --apply writes to --out.

    python scripts/export-bundle.py stripe-for-java              # dry run: what would go in
    python scripts/export-bundle.py stripe-for-java --apply      # folder + zip in dist/
    python scripts/export-bundle.py --all --apply                # every bundle
    options: --target claude   --out dist   --work C:/tmp/ax   --keep (keep the sandbox)

Per bundle:
  1. install ONLY the bundle in a fresh sandbox per attempt (`apm install --target <t>`, up to 5 attempts:
     Windows file locks on apm_modules/ are intermittent). Sandbox paths are kept SHORT (C:/tmp/ax/<6 hex>)
     because apm_modules/ nests deep paths and long names hit Windows MAX_PATH. The sandbox lives on a short path: the 8.3 user Temp path
     made APM fail in testing (2026-10-31).
  2. run the two post-install fixups against the sandbox (`--root`).
  3. read what was compiled from the sandbox apm.lock.yaml `deployments:` (path + owning package).
  4. filter: drop files not owned by a local package or owned by packages/third-party/ (Vercel);
     drop the skills in NEVER_EXPORT; apply packages/bundles/<name>/export.yml if present;
     then run the sensitive-data detectors (scripts/export_detectors.py) -- any finding BLOCKS the bundle
     and is listed in <out>/<bundle>/BLOCKED.txt.
  5. write <out>/<bundle>/<target>/ (the filtered compiled dir + README.md) and <out>/<bundle>-<target>.zip
     (same content, deterministic: sorted entries, fixed timestamps).

export.yml (optional, next to the bundle apm.yml; APM ignores it):
    agents: [name, ...] | all       skills: [name, ...] | cited | all       rules: [...] | cited | all
    include: [skills/x, agents/y.md, rules/z.md]       exclude: [...]      (`*` wildcards allowed)
`cited` = names written in backticks in the selected agents. Missing fields default to `all`.
"""
import datetime
import fnmatch
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_detectors as det  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
BUNDLES = REPO / "packages" / "bundles"
TARGET_DIRS = {"claude": ".claude"}
ATTEMPTS = 5  # Windows locks on apm_modules/ are intermittent; each retry starts clean after a pause
NEVER_EXPORT = {"skills/integrating-oracle-rms-webhooks"}  # a client's integration, not a product
VERCEL_PREREQS = [
    "https://github.com/vercel-labs/agent-skills",
    "https://github.com/vercel/next.js (skills folder)",
]
ZIP_TIME = (1980, 1, 1, 0, 0, 0)


# ---------------------------------------------------------------------------- small YAML subset
def read_simple_yaml(path: Path) -> dict:
    """Enough YAML for export.yml and the bundle apm.yml header: scalars, `>-` folded text,
    inline [a, b] lists and `- item` lists. Comments are ignored."""
    data, key, folded = {}, None, False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = re.sub(r"\s+#.*$", "", raw) if not raw.lstrip().startswith("- path:") else raw
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if folded and line.startswith("  ") and not line.lstrip().startswith("- "):
            data[key] = (data[key] + " " + line.strip()).strip()
            continue
        folded = False
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val in (">-", ">", "|", "|-"):
                data[key], folded = "", True
            elif val.startswith("[") and val.endswith("]"):
                data[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            elif val == "":
                data[key] = []
            else:
                data[key] = val.strip("'\"")
            continue
        m = re.match(r"^\s+-\s+(.+)$", line)
        if m and isinstance(data.get(key), list):
            data[key].append(m.group(1).strip().strip("'\""))
    return data


def tdir_of(target: str) -> str:
    return TARGET_DIRS.get(target, f".{target}")


# ---------------------------------------------------------------------------- sandbox install
def new_sandbox(bundle: str, target: str, work: Path, attempt: int) -> Path:
    """A fresh, never-reused directory per attempt. Windows can keep a half-deleted apm_modules/ locked
    for a while, so reusing (or wiping) a sandbox makes every retry fail the same way."""
    # short on purpose: apm_modules/ nests deep paths and long bundle names pushed them past Windows
    # MAX_PATH (260), which made every attempt of the long-named bundles fail (2026-10-31)
    tag = hashlib.sha1(f"{bundle}{target}{time.time()}".encode()).hexdigest()[:6]
    sandbox = work / f"{tag}{attempt}"
    sandbox.mkdir(parents=True)
    (sandbox / "BUNDLE").write_text(f"{bundle} {target}\n", encoding="utf-8")  # which bundle this dir is
    (sandbox / "apm.yml").write_text(
        "name: export-sandbox\nversion: 0.0.0\ndescription: throwaway export install, never committed\n"
        "author: export\nlicense: MIT\ndependencies:\n  apm:\n"
        f"    - path: {(BUNDLES / bundle).as_posix()}\n  mcp: []\nincludes: auto\nscripts: {{}}\n",
        encoding="utf-8", newline="\n")
    subprocess.run(["git", "init", "-q", "."], cwd=sandbox, capture_output=True)
    return sandbox


def discard(sandbox: Path, work: Path):
    """Best-effort removal; a locked leftover is harmless because sandboxes are never reused."""
    if sandbox.parent == work:
        shutil.rmtree(sandbox, ignore_errors=True)


def install_env() -> dict:
    """The user's git may have core.autocrlf=true (Windows default): the clone of a pinned upstream repo
    (vercel-labs/agent-browser) then fails with "local changes would be overwritten by checkout".
    Override it for this process only (GIT_CONFIG_* env, git >= 2.31); the global config is untouched."""
    env = dict(os.environ)
    n = int(env.get("GIT_CONFIG_COUNT", "0") or 0)
    env.update({"GIT_CONFIG_COUNT": str(n + 1), f"GIT_CONFIG_KEY_{n}": "core.autocrlf",
                f"GIT_CONFIG_VALUE_{n}": "false"})
    return env


def install(bundle: str, target: str, work: Path) -> tuple[Path, str]:
    apm = shutil.which("apm")
    if not apm:
        return work, "apm CLI not found on PATH"
    reason = "install failed"
    for attempt in range(1, ATTEMPTS + 1):
        sandbox = new_sandbox(bundle, target, work, attempt)
        p = subprocess.run([apm, "install", "--target", target], cwd=sandbox, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", env=install_env())
        out = (p.stdout or "") + (p.stderr or "")
        if p.returncode == 0 and "Installed" in out:
            for fix in ("restore-rule-metadata.py", "fix-cross-package-links.py"):
                subprocess.run([sys.executable, str(REPO / "scripts" / fix), "--root", str(sandbox)],
                               capture_output=True, text=True)
            return sandbox, ""
        # the useful line is the first error, not the generic "no changes were committed" at the end
        flat = " ".join(out.split())
        if "Another APM operation" in flat:
            # global lock in ~/.apm: another `apm install` (any repo) is running; retrying here is pointless
            return work, "outra operação do APM está rodando (lock global em ~/.apm); rode uma de cada vez"
        m = re.search(r"\[x\][^\[]*?(?:WinError \d+[^\]]*?\]?|Access is denied|not empty)[^\[]{0,120}", flat)
        reason = m.group(0)[:200] if m else (out.strip().splitlines()[-1] if out.strip() else str(p.returncode))
        print(f"    install attempt {attempt}/{ATTEMPTS} failed: {reason}")
        discard(sandbox, work)
        time.sleep(5 * attempt)
    return work, reason


def deployments(sandbox: Path) -> list[tuple[str, str]]:
    """[(deployed path, owner)] for every deployed FILE in the sandbox lock."""
    text = (sandbox / "apm.lock.yaml").read_text(encoding="utf-8")
    text = text.split("\ndeployments:\n", 1)[1] if "\ndeployments:\n" in text else ""
    out = []
    for entry in re.split(r"\n- ", "\n" + text)[1:]:
        value = re.search(r"(?m)^\s*value:\s*(.+)$", entry)
        owner = re.search(r"(?m)^\s*active_owner:\s*(.+)$", entry)
        if value and (sandbox / value.group(1).strip()).is_file():
            out.append((value.group(1).strip(), owner.group(1).strip() if owner else ""))
    return out


# ---------------------------------------------------------------------------- selection
def kind_and_name(rel: str, tdir: str) -> tuple[str, str]:
    """('skills', name) / ('agents', name) / ('rules', name) / ('other', rel) for a deployed path."""
    parts = rel.split("/")
    if len(parts) >= 3 and parts[0] == tdir and parts[1] in ("skills", "agents", "rules"):
        name = parts[2] if parts[1] == "skills" else re.sub(r"\.md$", "", parts[2])
        return parts[1], name
    return "other", rel


def is_local_product(owner: str) -> bool:
    o = owner.replace("\\", "/")
    return o.startswith("local:") and "/packages/" in o and "/packages/third-party/" not in o


def select(files, sandbox: Path, tdir: str, spec: dict):
    """Apply NEVER_EXPORT and export.yml. Returns (kept files, dropped vercel count)."""
    vercel = sum(1 for _, o in files if not is_local_product(o))
    files = [(r, o) for r, o in files if is_local_product(o)]
    names = {"skills": set(), "agents": set(), "rules": set()}
    for r, _ in files:
        k, n = kind_and_name(r, tdir)
        if k in names:
            names[k].add(n)

    def wanted(field, cited):
        v = spec.get(field, "all")
        if v == "all":
            return names[field]
        if v == "cited":
            return names[field] & cited
        return names[field] & set(v)

    agents = wanted("agents", set())
    cited = set()
    for a in agents:
        cited |= set(re.findall(r"`([a-z0-9][a-z0-9-]+)`", (sandbox / tdir / "agents" / f"{a}.md")
                                .read_text(encoding="utf-8")))
    keep = {"skills": wanted("skills", cited), "agents": agents, "rules": wanted("rules", cited)}
    if spec.get("rules") == "cited":
        # the base rules every artifact relies on (frontmatter and naming schemas) always ship
        keep["rules"] |= {n for n in names["rules"]
                          if n in ("skill-frontmatter", "agent-frontmatter", "rules-frontmatter",
                                   "naming-conventions", "skill-structure")}
    include = list(spec.get("include", []) or [])
    exclude = list(spec.get("exclude", []) or []) + sorted(NEVER_EXPORT)

    def matches(patterns, k, n):  # `skills/x`, `agents/y.md`, `rules/z.md`; `*` wildcards allowed
        keys = (f"{k}/{n}", f"{k}/{n}.md")
        return any(fnmatch.fnmatchcase(key, p) for p in patterns for key in keys)

    kept = []
    for r, o in files:
        k, n = kind_and_name(r, tdir)
        if matches(exclude, k, n):
            continue
        if k == "other" or n in keep.get(k, set()) or matches(include, k, n):
            kept.append((r, o))
    return kept, vercel


# ---------------------------------------------------------------------------- output
# ---------------------------------------------------------------------------- usage manuals (docs/)
KINDS = ("skills", "agents", "rules")
MAX_LISTED = 12  # names shown per kind in the "not included" banner
INSTALL_NOTE = ("This package is part of the bundle you received. Copy the bundle's `.claude/` folder into "
                "your project (see the bundle README). No other install step is needed.")
MARKER_LINE = re.compile(r"^<!-- (?:BEGIN|END) GENERATED:[a-z-]+ -->[ \t]*\n?", re.M)
LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)\)")
CONTENT_ROW = re.compile(r"^\| (command|inline orchestrator|knowledge skill|agent(?: \([a-z]+\))?|rule) \| "
                         r"\[`/?([^`]+)`\]\([^)]*\) \|")
AGENT_ROW = re.compile(r"^\| \[`([^`]+)`\]\([^)]*\) \|")


def package_dir_of(owner: str):
    """Folder of the local package that owns a deployed file (lock `active_owner`), or None."""
    o = owner.replace("\\", "/")
    if "/packages/" not in o:
        return None
    parts = [p for p in o.split("/packages/", 1)[1].split("#")[0].split("/") if p]
    for n in range(len(parts), 0, -1):
        cand = REPO.joinpath("packages", *parts[:n])
        if (cand / "apm.yml").is_file():
            return cand
    return None


def own_names(pkg_dir: Path) -> dict:
    """Names of every skill, agent and rule a package defines, as they are deployed."""
    names = {k: set() for k in KINDS}
    skills = pkg_dir / ".apm" / "skills"
    if skills.is_dir():
        names["skills"] = {p.name for p in skills.iterdir() if (p / "SKILL.md").is_file()}
    agents = pkg_dir / ".apm" / "agents"
    for f in agents.glob("*.md") if agents.is_dir() else []:
        m = re.search(r"(?m)^name:\s*(\S+)", f.read_text(encoding="utf-8"))
        names["agents"].add(m.group(1).strip("\"'") if m else re.sub(r"\.agent$", "", f.stem))
    rules = pkg_dir / ".apm" / "instructions"
    for f in rules.glob("*.md") if rules.is_dir() else []:
        names["rules"].add(re.sub(r"\.instructions$", "", f.stem))
    return names


def rewrite_links(text: str, src_dir: Path, local: dict) -> str:
    """Links to another included package manual become local; every other relative link becomes plain
    text (repo paths do not exist in the export). URLs, mail links and in-page anchors stay."""
    def sub(m):
        bang, label, target = m.group(1), m.group(2), m.group(3)
        if target.startswith("#") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
            return m.group(0)
        path, _, frag = target.partition("#")
        resolved = (src_dir / path).resolve() if path else None
        if resolved is not None and resolved.name == "README.md" and resolved.parent in local:
            return f"[{label}]({local[resolved.parent]}" + (f"#{frag}" if frag else "") + ")"
        return "" if bang else label
    return LINK_RE.sub(sub, text)


def transform_block(text: str, block_id: str, fn) -> str:
    pattern = re.compile(rf"(<!-- BEGIN GENERATED:{re.escape(block_id)} -->\n)(.*?)(\n?<!-- END GENERATED:{re.escape(block_id)} -->)",
                         re.DOTALL)
    return pattern.sub(lambda m: m.group(1) + fn(m.group(2)) + m.group(3), text, count=1)


def filter_generated(text: str, kept: dict) -> str:
    """Keep only what the bundle ships: replace the install block, drop table rows of excluded items and
    the dependency lines that describe the repository."""
    def contents(body):
        out = []
        for line in body.splitlines():
            if line.startswith(("**Depends on:**", "**Used by:**")):
                continue
            m = CONTENT_ROW.match(line)
            if m:
                kind = "skills" if m.group(1) in ("command", "inline orchestrator", "knowledge skill") else \
                    "agents" if m.group(1).startswith("agent") else "rules"
                if m.group(2) not in kept[kind]:
                    continue
            out.append(line)
        return "\n".join(out)

    def agents_ref(body):
        out = []
        for line in body.splitlines():
            m = AGENT_ROW.match(line)
            if m and m.group(1) not in kept["agents"]:
                continue
            out.append(line)
        return "\n".join(out)

    text = transform_block(text, "installation", lambda _: INSTALL_NOTE)
    text = transform_block(text, "contents", contents)
    return transform_block(text, "agents-reference", agents_ref)


def not_included_banner(own: dict, kept: dict):
    missing = {k: sorted(own[k] - kept[k]) for k in KINDS if own[k] - kept[k]}
    if not missing:
        return ""
    parts = []
    for k, names in missing.items():
        shown = ", ".join(f"`{n}`" for n in names[:MAX_LISTED])
        more = f" and {len(names) - MAX_LISTED} more" if len(names) > MAX_LISTED else ""
        parts.append(f"{k} {shown}{more}")
    return ("> **This bundle includes only part of this package.** Not included: " + "; ".join(parts) +
            ". Anything below that refers to them does not apply to this bundle.\n\n")


def build_docs(kept_files, tdir: str, bundle: str, meta: dict):
    """{file name under docs/: text} for the packages that own at least one exported file."""
    owned = {}
    for rel, owner in kept_files:
        pkg = package_dir_of(owner)
        kind, name = kind_and_name(rel, tdir)
        if pkg is not None and kind in KINDS:
            owned.setdefault(pkg, {k: set() for k in KINDS})[kind].add(name)
    local = {pkg: f"{pkg.name}.md" for pkg in owned}
    docs = {}
    for pkg, kept in sorted(owned.items(), key=lambda kv: kv[0].name):
        readme_path = pkg / "README.md"
        if not readme_path.is_file():
            continue
        text = readme_path.read_text(encoding="utf-8")
        text = filter_generated(text, kept)
        text = rewrite_links(text, pkg, local)
        text = MARKER_LINE.sub("", text)
        head, _, rest = text.partition("\n")  # keep the title line first, then the banner
        docs[f"{pkg.name}.md"] = head + "\n\n" + not_included_banner(own_names(pkg), kept) + rest.lstrip("\n")
    if docs:
        index = [f"# {bundle.replace('-', ' ').title()}: documentation", "", meta.get("description", ""), "",
                 "Usage manuals for the packages in this bundle. Each one covers installation, quick start, "
                 "usage scenarios, the command or skill reference, agents and limits.", ""]
        index += [f"- [{name[:-3]}]({name})" for name in sorted(docs)]
        docs["README.md"] = "\n".join(index) + "\n"
    return docs


def scan_docs(docs: dict):
    """Detector findings for the doc files, in the same shape as the findings for exported files."""
    return [(f"docs/{name}", n, d, m, line.strip())
            for name, text in docs.items()
            for n, line in enumerate(text.splitlines(), 1)
            for d, m in det.scan_text(line)]


def readme(meta: dict, bundle: str, counts: dict, lists: dict, vercel: bool, tdir: str, docs=None) -> str:
    title = bundle.replace("-", " ").title()
    lines = [f"# {title}  ·  v{meta.get('version', '1.0.0')}  ·  {datetime.date.today().isoformat()}", "",
             meta.get("description", ""), "", "## Contents"]
    for k in ("skills", "agents", "rules"):
        if counts[k]:
            lines.append(f"- {counts[k]} {k}: " + ", ".join(sorted(lists[k])))
    lines += ["", "## Install",
              f"Copy the `{tdir}/` folder into the root of your project (merge it with an existing one).",
              "Restart your agent so it picks up the new skills, agents and rules."]
    if docs:
        lines += ["", "## Documentation",
                  "The `docs/` folder holds the usage manual of each package in this bundle (it sits next to "
                  f"`{tdir}/`, outside it, so your agent does not load it). Start with [docs/README.md](docs/README.md):"]
        lines += [f"- [{name[:-3]}](docs/{name})" for name in sorted(docs) if name != "README.md"]
    if vercel:
        lines += ["", "## Free prerequisites",
                  "Some skills in this bundle build on the official Vercel skills, which are free and are "
                  "not included here. Install them from:"] + [f"- {u}" for u in VERCEL_PREREQS]
    return "\n".join(lines) + "\n"


def write_zip(src: Path, dest: Path):
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(p for p in src.rglob("*") if p.is_file()):
            info = zipfile.ZipInfo(f.relative_to(src).as_posix(), ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, f.read_bytes())


def export(bundle: str, target: str, out: Path, work: Path, apply: bool, keep_sandbox: bool) -> str:
    tdir = tdir_of(target)
    meta = read_simple_yaml(BUNDLES / bundle / "apm.yml")
    spec = read_simple_yaml(BUNDLES / bundle / "export.yml") if (BUNDLES / bundle / "export.yml").is_file() else {}
    sandbox, err = install(bundle, target, work)
    if err:
        print(f"⚠️  {bundle:32s} INSTALL FAILED — {err}")
        return "failed"
    kept, vercel = select(deployments(sandbox), sandbox, tdir, spec)
    lists = {"skills": set(), "agents": set(), "rules": set()}
    for r, _ in kept:
        k, n = kind_and_name(r, tdir)
        if k in lists:
            lists[k].add(n)
    counts = {k: len(v) for k, v in lists.items()}
    docs = build_docs(kept, tdir, bundle, meta)
    findings = [(r, *f) for r, _ in kept for f in det.scan_file(sandbox / r)] + scan_docs(docs)
    bdir = out / bundle
    if findings:
        files = len({f[0] for f in findings})
        print(f"⛔ {bundle:32s} BLOQUEADO — {len(findings)} ocorrência(s) em {files} arquivo(s)")
        for r, n, d, m, line in findings[:6]:
            print(f"     [{d}] {r}:{n}  {m}")
        if apply:
            bdir.mkdir(parents=True, exist_ok=True)
            (bdir / "BLOCKED.txt").write_text(
                "".join(f"[{d}] {r}:{n}  {m}  |  {line}\n" for r, n, d, m, line in findings), encoding="utf-8")
            print(f"     lista completa: {(bdir / 'BLOCKED.txt').relative_to(REPO) if bdir.is_relative_to(REPO) else bdir}")
        status = "blocked"
    else:
        summary = ", ".join(f"{counts[k]} {k}" for k in ("skills", "agents", "rules"))
        summary += f", {max(len(docs) - 1, 0)} manual(s) in docs/"
        extra = f"; {vercel} arquivo(s) da Vercel fora" if vercel else ""
        if apply:
            dest = bdir / target
            if dest.exists():
                shutil.rmtree(dest)
            for r, _ in kept:
                (dest / r).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(sandbox / r, dest / r)
            for name, text in docs.items():
                (dest / "docs").mkdir(parents=True, exist_ok=True)
                (dest / "docs" / name).write_text(text, encoding="utf-8", newline="\n")
            (dest / "README.md").write_text(readme(meta, bundle, counts, lists, bool(vercel), tdir, docs),
                                            encoding="utf-8", newline="\n")
            (bdir / "BLOCKED.txt").unlink(missing_ok=True)
            zpath = out / f"{bundle}-{target}.zip"
            write_zip(dest, zpath)
            digest = hashlib.sha256(zpath.read_bytes()).hexdigest()[:12]
            print(f"✅ {bundle:32s} OK — {summary}{extra}; zip {zpath.stat().st_size // 1024} KB sha256 {digest}")
        else:
            print(f"✅ {bundle:32s} OK — {summary}{extra} (simulação: nada gravado)")
        status = "ok"
    if not keep_sandbox:
        discard(sandbox, work)
    return status


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:]

    def opt(name, default):
        return args[args.index(name) + 1] if name in args else default

    target = opt("--target", "claude")
    out = Path(opt("--out", str(REPO / "dist"))).resolve()
    work = Path(opt("--work", "C:/tmp/ax" if os.name == "nt" else "/tmp/ax")).resolve()
    apply, keep = "--apply" in args, "--keep" in args
    values = {opt(o, None) for o in ("--target", "--out", "--work")}
    names = [a for a in args if not a.startswith("--") and a not in values]
    all_bundles = sorted(d.name for d in BUNDLES.iterdir() if (d / "apm.yml").is_file())
    if "--all" in args:
        names = all_bundles
    unknown = [n for n in names if n not in all_bundles]
    if not names or unknown:
        print(__doc__ if not names else f"unknown bundle(s): {unknown}\navailable: {', '.join(all_bundles)}")
        return 2
    work.mkdir(parents=True, exist_ok=True)
    if apply:
        out.mkdir(parents=True, exist_ok=True)
    results = {n: export(n, target, out, work, apply, keep) for n in names}
    ok = sum(1 for v in results.values() if v == "ok")
    print(f"\n{ok}/{len(results)} bundle(s) OK; "
          f"{sum(1 for v in results.values() if v == 'blocked')} bloqueado(s); "
          f"{sum(1 for v in results.values() if v == 'failed')} com falha de instalação")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
