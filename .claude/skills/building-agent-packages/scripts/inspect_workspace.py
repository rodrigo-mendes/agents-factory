#!/usr/bin/env python3
"""Reconstruct pipeline state from disk (stdlib only, READ-ONLY). Works with or without
PIPELINE_STATE.md; the disk always wins over the recorded state.
Usage: inspect_workspace.py <workspace_dir> [--packages packages] [--json]
Per research file: COMPLETE | PARTIAL. Per skill: OK | INCOMPLETE | CORRUPT | UNCHECKED
(OK = verify_skill.py passes; UNCHECKED = not a hybrid knowledge skill). Also reports validation rounds, family files, recorded phase."""
import json
import os
import re
import subprocess
import sys

ws = sys.argv[1].rstrip('/')
pk = sys.argv[sys.argv.index('--packages') + 1] if '--packages' in sys.argv else 'packages'
here = os.path.dirname(os.path.abspath(__file__))
verify = os.path.join(here, 'verify_skill.py')
out = {'workspace': ws, 'research': {}, 'skills': {}, 'family': [], 'rounds': {}, 'recorded': None}

for f in sorted(os.listdir(ws)) if os.path.isdir(ws) else []:
    p = os.path.join(ws, f)
    if f.startswith('research_') and f.endswith('.md'):
        t = open(p, encoding='utf-8').read()
        done = bool(re.search(r'^#+\s*.*(Source Bibliography|Bibliography|Sources)', t, re.M | re.I)) \
            and len(t.splitlines()) > 60
        out['research'][f] = 'COMPLETE' if done else 'PARTIAL'
    elif f.startswith('_family_'):
        out['family'].append(f)
vd = os.path.join(ws, 'validation')
if os.path.isdir(vd):
    for r in sorted(os.listdir(vd)):
        if os.path.isdir(os.path.join(vd, r)):
            parts = os.listdir(os.path.join(vd, r))
            out['rounds'][r] = {k: any(k in x for x in parts) for k in ('validate', 'test', 'audit')}
st = os.path.join(ws, 'PIPELINE_STATE.md')
if os.path.isfile(st):
    m = re.search(r'^current_phase:\s*(\S+)', open(st, encoding='utf-8').read(), re.M)
    out['recorded'] = m.group(1) if m else 'unparseable'

for root, dirs, _ in os.walk(pk):
    if root.endswith('/.apm/skills'):
        for n in dirs:
            d = os.path.join(root, n)
            if not os.path.isfile(os.path.join(d, 'SKILL.md')):
                out['skills'][n] = 'CORRUPT'
                continue
            if not os.path.isfile(os.path.join(d, 'blueprints', 'unverified-and-risks.md')):
                out['skills'][n] = 'UNCHECKED'  # not a hybrid knowledge skill (e.g. workflow skill)
                continue
            r = subprocess.run([sys.executable, verify, d], capture_output=True, text=True)
            out['skills'][n] = 'OK' if r.returncode == 0 else 'INCOMPLETE'
        dirs[:] = []

if '--json' in sys.argv:
    print(json.dumps(out, indent=1))
else:
    print(f'workspace {ws}  recorded phase: {out["recorded"] or "none (state reconstructed from disk)"}')
    for k, v in out['research'].items():
        print(f'  research {v:9} {k}')
    print(f'  family files: {", ".join(out["family"]) or "none"}')
    for k, v in sorted(out['skills'].items()):
        print(f'  skill    {v:10} {k}')
    for k, v in out['rounds'].items():
        print(f'  {k}: {v}')
