"""Scoped install rehearsal: install ONE package (plus its local dependencies) into a throwaway
sandbox and prove that what `apm install` deploys equals the package source (stdlib only).

Why: the full root `apm install` takes 12-40 min on Windows and, when a remote dependency fails,
deletes committed `.claude/` files and drops other packages from the lock. The sandbox install
touches neither the root `apm.yml`, the lock nor `.claude/`, and takes seconds.

Usage (from the repo root):
  python scoped_install.py --package <pkg> [--slug <slug>] [--keep]

  --package  folder name under packages/
  --slug     workspace/<slug> of the running pipeline: logs a NOTE/INCIDENT event to its state
  --keep     keep workspace/.sbx after the run (default: delete it)

The sandbox lives at workspace/.sbx on purpose: a deeper folder pushed copied paths past the
Windows 260-character limit (WinError 3) in the github-actions-cicd run (2026-10-30).
Exit 0 when the install succeeds and every skill, agent and rule matches the source; 1 otherwise.
"""
import argparse
import filecmp
import os
import re
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join('workspace', '.sbx')
MAX_PATH = 260


def run_install(sandbox):
    apm = shutil.which('apm')
    if not apm:
        return 1, 'apm CLI not found on PATH'
    out = ''
    for attempt in (1, 2):  # the first attempt can fail on a stale staging copy; one retry
        p = subprocess.run([apm, 'install', '--target', 'claude'], cwd=sandbox,
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        out = (p.stdout or '') + (p.stderr or '')
        if p.returncode == 0 and 'Installed' in out:
            return 0, out
        print(f'attempt {attempt} failed:', out.strip().splitlines()[-1:] if out.strip() else p.returncode)
    return 1, out


def tree_diff(src, dst):
    """Files that differ or are missing between two directory trees."""
    problems = []
    c = filecmp.dircmp(src, dst)
    problems += [f'missing in deploy: {os.path.join(src, x)}' for x in c.left_only]
    problems += [f'extra in deploy: {os.path.join(dst, x)}' for x in c.right_only]
    _, mismatch, errors = filecmp.cmpfiles(src, dst, c.common_files, shallow=False)
    problems += [f'differs: {os.path.join(dst, x)}' for x in mismatch + errors]
    for sub in c.common_dirs:
        problems += tree_diff(os.path.join(src, sub), os.path.join(dst, sub))
    return problems


def split_globs(s):
    """Split an applyTo value on commas outside braces: `a.{yml,yaml},b` -> ['a.{yml,yaml}', 'b'] (as APM does)."""
    out, depth, cur = [], 0, ''
    for ch in s:
        depth += ch == '{'
        depth -= ch == '}'
        if ch == ',' and depth == 0:
            out.append(cur.strip())
            cur = ''
        else:
            cur += ch
    return [g for g in out + [cur.strip()] if g]


def compare(pkg_apm, claude):
    problems, counts = [], {'skills': 0, 'agents': 0, 'rules': 0}
    sk = os.path.join(pkg_apm, 'skills')
    for name in sorted(os.listdir(sk)) if os.path.isdir(sk) else []:
        counts['skills'] += 1
        dst = os.path.join(claude, 'skills', name)
        problems += [f'skill not deployed: {name}'] if not os.path.isdir(dst) else \
            tree_diff(os.path.join(sk, name), dst)
    ag = os.path.join(pkg_apm, 'agents')
    for f in sorted(os.listdir(ag)) if os.path.isdir(ag) else []:
        counts['agents'] += 1
        dst = os.path.join(claude, 'agents', f.replace('.agent.md', '.md'))
        if not os.path.isfile(dst):
            problems.append(f'agent not deployed: {f}')
        elif not filecmp.cmp(os.path.join(ag, f), dst, shallow=False):
            problems.append(f'agent differs: {dst}')
    ins = os.path.join(pkg_apm, 'instructions')
    for f in sorted(os.listdir(ins)) if os.path.isdir(ins) else []:
        counts['rules'] += 1
        dst = os.path.join(claude, 'rules', f.replace('.instructions.md', '.md'))
        if not os.path.isfile(dst):
            problems.append(f'rule not deployed: {f}')
            continue
        src_t = open(os.path.join(ins, f), encoding='utf-8').read()
        dst_t = open(dst, encoding='utf-8').read()
        m = re.search(r'^applyTo:\s*"?([^"\n]+)"?', src_t, re.M)
        globs = split_globs(m.group(1)) if m else []
        for g in globs:  # applyTo must reappear as paths: entries
            if f'"{g}"' not in dst_t and f"- {g}" not in dst_t:
                problems.append(f'rule {dst}: applyTo glob {g} missing from paths:')
        body = lambda t: t.split('---', 2)[-1].strip()  # noqa: E731
        if body(src_t) != body(dst_t):
            problems.append(f'rule body differs: {dst}')
    return problems, counts


def longest_root_path(pkg_apm, repo):
    """Longest path the package will have once deployed into the root .claude/ (MAX_PATH guard)."""
    m = 0
    for r, _, files in os.walk(os.path.join(pkg_apm, 'skills')):
        for x in files:
            rel = os.path.relpath(os.path.join(r, x), pkg_apm)
            m = max(m, len(os.path.join(repo, '.claude', rel)))
    return m


def log(slug, code, text):
    if slug:
        subprocess.run([sys.executable, os.path.join(HERE, 'state_event.py'),
                        os.path.join('workspace', slug), 'event', 'P5', code, text[:200]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--package', required=True)
    ap.add_argument('--slug')
    ap.add_argument('--keep', action='store_true')
    a = ap.parse_args()
    repo = os.getcwd()
    pkg_apm = os.path.join('packages', a.package, '.apm')
    if not os.path.isfile(os.path.join('packages', a.package, 'apm.yml')):
        sys.exit(f'packages/{a.package}/apm.yml not found (run from the repo root)')
    if os.path.isdir(SANDBOX):
        shutil.rmtree(SANDBOX)
    os.makedirs(SANDBOX)
    with open(os.path.join(SANDBOX, 'apm.yml'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(f'name: scoped-install-sandbox\nversion: 0.0.0\n'
                 f'description: Throwaway scoped install of packages/{a.package}; never committed.\n'
                 f'author: agents-factory\nlicense: MIT\ndependencies:\n  apm:\n'
                 f'    - path: ../../packages/{a.package}\n  mcp: []\nincludes: auto\nscripts: {{}}\n')
    rc, out = run_install(SANDBOX)
    if rc:
        print('PROBLEMS:\n  - scoped apm install failed:', out.strip().splitlines()[-3:])
        log(a.slug, 'INCIDENT', f'scoped install of {a.package} failed')
        sys.exit(1)
    problems, counts = compare(pkg_apm, os.path.join(SANDBOX, '.claude'))
    longest = longest_root_path(pkg_apm, repo)
    if longest >= MAX_PATH:
        problems.append(f'deployed path length {longest} >= {MAX_PATH} (Windows MAX_PATH)')
    print(f'{a.package}: {counts["skills"]} skills, {counts["agents"]} agents, {counts["rules"]} rules '
          f'deployed in sandbox; longest root path {longest}')
    if not a.keep:
        shutil.rmtree(SANDBOX, ignore_errors=True)
    if problems:
        print('PROBLEMS:')
        for p in problems:
            print('  -', p)
        log(a.slug, 'INCIDENT', f'scoped install of {a.package}: {len(problems)} mismatch(es)')
        sys.exit(1)
    print('OK, deploy matches source')
    log(a.slug, 'NOTE', f'scoped install of {a.package} OK: {counts["skills"]} skills, '
                        f'{counts["agents"]} agents, {counts["rules"]} rules match source')


if __name__ == '__main__':
    main()
