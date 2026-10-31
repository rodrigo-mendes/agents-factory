#!/usr/bin/env python3
"""Reconstruct pipeline state from disk (stdlib only, READ-ONLY). Works with or without
PIPELINE_STATE.md; the disk always wins over the recorded state.
Usage: inspect_workspace.py <workspace_dir> [--packages packages] [--execution N] [--json]
With execution-N folders (new layout) the state comes from state_lib (LATEST unless --execution);
without them the workspace is reported as legacy (execution-0, read-only).
Per research file: COMPLETE | PARTIAL. Per skill: OK | INCOMPLETE | CORRUPT | UNCHECKED
(OK = verify_skill.py passes; UNCHECKED = not a hybrid knowledge skill). Also reports validation rounds, family files, recorded phase."""
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_lib as sl  # noqa: E402

ws = sys.argv[1].rstrip('/' + os.sep)
pk = sys.argv[sys.argv.index('--packages') + 1] if '--packages' in sys.argv else 'packages'
here = os.path.dirname(os.path.abspath(__file__))
verify = os.path.join(here, 'verify_skill.py')
out = {'workspace': ws, 'research': {}, 'skills': {}, 'family': [], 'rounds': {}, 'recorded': None,
       'execution': None}

for rel, f in sl.research_files(ws) if os.path.isdir(ws) else []:  # research/ first, legacy root next
    t = open(os.path.join(ws, rel), encoding='utf-8').read()
    done = bool(re.search(r'^#+\s*.*(Source Bibliography|Bibliography|Sources)', t, re.M | re.I)) \
        and len(t.splitlines()) > 60
    out['research'][rel] = 'COMPLETE' if done else 'PARTIAL'
for f in sorted(os.listdir(ws)) if os.path.isdir(ws) else []:
    if f.startswith('_family_'):
        out['family'].append(f)
vd = os.path.join(ws, 'validation')
if os.path.isdir(vd):
    for r in sorted(os.listdir(vd)):
        if os.path.isdir(os.path.join(vd, r)):
            parts = os.listdir(os.path.join(vd, r))
            out['rounds'][r] = {k: any(k in x.lower() for x in parts)
                                for k in ('validate', 'test', 'audit')}
ex = sl.resolve(ws, sys.argv[sys.argv.index('--execution') + 1] if '--execution' in sys.argv else None)
st = os.path.join(ws, 'PIPELINE_STATE.md')
if ex:
    s = sl.load(ex)
    out['execution'] = os.path.basename(ex)
    out['recorded'] = sl.current_phase(s)
    out['rounds'] = {k: v['kinds'] for k, v in s['rounds'].items()}
    out['units'] = {k: v['state'] for k, v in s['units'].items()}
    out['gates'] = sorted(s['gates'])
elif os.path.isfile(st):
    m = re.search(r'^current_phase:\s*(\S+)', open(st, encoding='utf-8').read(), re.M)
    out['recorded'] = m.group(1) if m else 'unparseable'

for root, dirs, _ in os.walk(pk):
    if root.replace(os.sep, '/').endswith('/.apm/skills'):
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
    print(f'workspace {ws}  layout: {out["execution"] or "legacy (execution-0, read-only)"}  '
          f'recorded phase: {out["recorded"] or "none (state reconstructed from disk)"}')
    for k, v in out.get('units', {}).items():
        print(f'  unit     {v:10} {k}')
    if out['execution']:
        print(f'  gates: {", ".join(out["gates"]) or "none"}')
    for k, v in out['research'].items():
        print(f'  research {v:9} {k}')
    print(f'  family files: {", ".join(out["family"]) or "none"}')
    for k, v in sorted(out['skills'].items()):
        print(f'  skill    {v:10} {k}')
    for k, v in out['rounds'].items():
        print(f'  {k}: {v}')
