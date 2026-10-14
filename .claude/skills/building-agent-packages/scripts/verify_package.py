#!/usr/bin/env python3
"""Mechanical checks for an APM package (stdlib only, read-only).
Usage: verify_package.py <package_dir>   e.g. packages/camel-quarkus-integrator
Checks apm.yml, skill/agent/rule frontmatter, dependency paths, skill names referenced in prose,
and local markdown links. Exit 1 when any problem is found."""
import os
import re
import sys

pkg = sys.argv[1].rstrip('/')
apm = os.path.join(pkg, '.apm')
problems = []


def fm(path):
    t = open(path, encoding='utf-8').read()
    m = re.match(r'---\n(.*?)\n---\n', t, re.S)
    return (m.group(1) if m else None), t


def key(block, k):
    m = re.search(r'^' + k + r':\s*(.*)$', block or '', re.M)
    return m.group(1).strip() if m else None


if not os.path.isfile(os.path.join(pkg, 'apm.yml')):
    problems.append('missing apm.yml')
else:
    y = open(os.path.join(pkg, 'apm.yml'), encoding='utf-8').read()
    for dep in re.findall(r'-\s*path:\s*(\S+)', y):
        if not os.path.isdir(os.path.normpath(os.path.join(pkg, dep))):
            problems.append(f'apm.yml dependency path missing: {dep}')

skills = {}
sd = os.path.join(apm, 'skills')
if os.path.isdir(sd):
    for n in sorted(os.listdir(sd)):
        f = os.path.join(sd, n, 'SKILL.md')
        if not os.path.isfile(f):
            problems.append(f'skill {n}: no SKILL.md')
            continue
        b, t = fm(f)
        skills[n] = t
        if key(b, 'name') != n:
            problems.append(f'skill {n}: name != folder')
        d = key(b, 'description') or ''
        if 'Use when' not in d and not d.startswith('>'):
            problems.append(f'skill {n}: description lacks "Use when"')
        if len(t.splitlines()) >= 500:
            problems.append(f'skill {n}: >= 500 lines')

agents = {}
ad = os.path.join(apm, 'agents')
if os.path.isdir(ad):
    for f in sorted(os.listdir(ad)):
        b, t = fm(os.path.join(ad, f))
        agents[f] = t
        for k in ('name', 'description', 'tools'):
            if not key(b, k):
                problems.append(f'agent {f}: missing {k}')

idir = os.path.join(apm, 'instructions')
if os.path.isdir(idir):
    for f in sorted(os.listdir(idir)):
        b, _ = fm(os.path.join(idir, f))
        for k in ('name', 'description'):
            if not key(b, k):
                problems.append(f'rule {f}: missing {k}')
        if not (key(b, 'applyTo') or key(b, 'paths')):
            problems.append(f'rule {f}: no applyTo/paths')

# every skill-looking name referenced in prose must exist in this package or the repo
repo_skills = set()
for root in ('packages',):
    for r, ds, fs in os.walk(root):
        if r.replace(os.sep, '/').endswith('/.apm/skills'):
            repo_skills.update(ds)
for n, t in list(skills.items()) + list(agents.items()):
    for ref in set(re.findall(r'`((?:developing|integrating|structuring|building)-[a-z0-9-]+)`', t)):
        if ref not in repo_skills:
            problems.append(f'{n}: references unknown skill {ref}')

for r, _, fs in os.walk(pkg):
    for f in fs:
        if not f.endswith('.md'):
            continue
        p = os.path.join(r, f)
        t = open(p, encoding='utf-8').read()
        if t.startswith('\ufeff'):
            problems.append(f'BOM in {os.path.relpath(p, pkg)}')
        for mm in re.finditer(r'\]\((?!http|#|mailto)([^)\s#]+)', t):
            tgt = os.path.normpath(os.path.join(os.path.dirname(p), mm.group(1)))
            if not os.path.exists(tgt):
                problems.append(f'broken link {os.path.relpath(p, pkg)} -> {mm.group(1)}')

print(f'{pkg}: {len(skills)} skills, {len(agents)} agents, '
      f'{len(os.listdir(idir)) if os.path.isdir(idir) else 0} rules')
print('PROBLEMS:' if problems else 'OK, no problems')
for p in problems:
    print('  -', p)
sys.exit(1 if problems else 0)
