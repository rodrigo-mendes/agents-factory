#!/usr/bin/env python3
"""Mechanical checks for a hybrid knowledge skill (stdlib only, read-only).
Usage: verify_skill.py <skill_dir>   Exit 1 when any problem is found."""
import os
import re
import sys

d = sys.argv[1]
name = os.path.basename(d.rstrip('/'))
problems = []


def slug(h):
    h = h.strip().lower()
    h = re.sub(r'[^\w\- ]', '', h, flags=re.U)
    return h.replace(' ', '-')


skill = os.path.join(d, 'SKILL.md')
text = open(skill, encoding='utf-8').read()
lines = text.splitlines()
print(f'{name}: SKILL.md {len(lines)} lines')
if len(lines) >= 500:
    problems.append('SKILL.md >= 500 lines')

m = re.match(r'---\n(.*?)\n---\n', text, re.S)
if not m:
    problems.append('no frontmatter')
else:
    fm = m.group(1)
    keys = re.findall(r'^([a-zA-Z_-]+):', fm, re.M)
    if sorted(keys) != ['description', 'name']:
        problems.append(f'frontmatter keys: {keys}')
    nm = re.search(r'^name:\s*(.+)$', fm, re.M)
    if nm and nm.group(1).strip() != name:
        problems.append('name != folder')
    desc = re.search(r'^description:\s*"(.*)"\s*$', fm, re.M)
    if not desc:
        problems.append('description not a quoted single line')
    else:
        dd = desc.group(1)
        print(f'  description {len(dd)} chars')
        if len(dd) >= 300:
            problems.append('description >= 300')
        if 'Use when' not in dd:
            problems.append('description lacks "Use when"')

for h in ('## Version Context', '## Quick Navigation', '## Blueprints & Guardrails',
          '### ✅ Always Do', '### ⚠️ Ask First', '### 🚫 Never Do', '## Quick Reference'):
    if h not in text:
        problems.append(f'missing heading {h}')

bp = os.path.join(d, 'blueprints')
for f in ('evaluation-scenarios.md', 'unverified-and-risks.md', 'always-do-patterns.md',
          'never-do-patterns.md'):
    if not os.path.isfile(os.path.join(bp, f)):
        problems.append(f'missing blueprint {f}')
ur = os.path.join(bp, 'unverified-and-risks.md')
if os.path.isfile(ur):
    t = open(ur, encoding='utf-8').read()
    for h in ('Version-lifetime risk', 'Source Bibliography'):
        if not re.search(r'^#+\s*' + re.escape(h), t, re.M | re.I):
            problems.append(f'unverified-and-risks lacks heading {h}')
ev = os.path.join(bp, 'evaluation-scenarios.md')
if os.path.isfile(ev):
    n = len(re.findall(r'^#+\s*(Scenario|Escenario)', open(ev, encoding='utf-8').read(), re.M | re.I))
    print(f'  eval scenarios headings: {n}')

for root, _, fs in os.walk(d):
    for f in fs:
        if not f.endswith('.md'):
            continue
        p = os.path.join(root, f)
        t = open(p, encoding='utf-8').read()
        if t.startswith('\ufeff'):
            problems.append(f'BOM in {f}')
        n_lines = len(t.splitlines())
        if f != 'SKILL.md' and n_lines > 160:
            problems.append(f'{f} has {n_lines} lines (> 160)')
        for mm in re.finditer(r'\]\((\.?/?[^)\s#]*)(#[^)\s]*)?\)', t):
            tgt, anc = mm.group(1), mm.group(2)
            if tgt.startswith('http'):
                continue
            fp = p if tgt == '' else os.path.normpath(os.path.join(os.path.dirname(p), tgt))
            if not os.path.isfile(fp):
                problems.append(f'MISSING FILE {os.path.relpath(p, d)} -> {tgt}')
                continue
            if anc:
                heads = [slug(re.sub(r'^#+\s*', '', l)) for l in
                         open(fp, encoding='utf-8').read().splitlines() if l.startswith('#')]
                if anc[1:] not in heads:
                    problems.append(f'MISSING ANCHOR {os.path.relpath(p, d)} -> {tgt}{anc}')
        for pat, label in ((r'/Users/|/home/|C:\\\\', 'absolute path'), (r'\.github/', '.github'),
                           (r'days? (old|ago)|weeks? old', 'relative date'),
                           (r'write_to_file', 'write_to_file')):
            if re.search(pat, t):
                problems.append(f'{label} in {os.path.relpath(p, d)}')

print('PROBLEMS:' if problems else 'OK, no problems')
for p in problems:
    print('  -', p)
sys.exit(1 if problems else 0)
