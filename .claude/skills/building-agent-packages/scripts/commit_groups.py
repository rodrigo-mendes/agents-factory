#!/usr/bin/env python3
"""Stage and commit explicit path groups, refusing anything outside the group.
Usage: commit_groups.py <plan.json> [--apply]
plan.json: [{"message": "...", "paths": ["packages/x/", "docs/y.md"]}, ...]
Dry run by default: prints what each group would stage. With --apply, runs `git reset -q`, then
for each group `git add -- <paths>`, verifies `git diff --cached --name-only` is inside the
group's paths (exit 1 and unstage otherwise), then commits with the message. Never pushes."""
import json
import subprocess
import sys


def git(*a):
    return subprocess.run(['git', *a], capture_output=True, text=True, check=True).stdout


def inside(f, paths):
    return any(f == p.rstrip('/') or f.startswith(p.rstrip('/') + '/') for p in paths)


plan = json.load(open(sys.argv[1], encoding='utf-8'))
apply = '--apply' in sys.argv
ok = True
for i, g in enumerate(plan, 1):
    paths = g['paths']
    if apply:
        git('reset', '-q')
        git('add', '--', *paths)
        staged = [f for f in git('diff', '--cached', '--name-only').splitlines() if f]
    else:
        status = git('status', '--porcelain', '--', *paths).splitlines()
        staged = [l[3:] for l in status]
    stray = [f for f in staged if not inside(f, paths)]
    print(f'group {i}: {len(staged)} file(s) — {g["message"].splitlines()[0]}')
    if stray:
        print('  REFUSED, files outside group:', *stray, sep='\n   ')
        ok = False
        if apply:
            git('reset', '-q')
        break
    if not staged:
        print('  nothing to commit, skipped')
        continue
    if apply:
        git('commit', '-q', '-m', g['message'])
        print('  committed', git('rev-parse', '--short', 'HEAD').strip())
if apply:
    git('reset', '-q')
sys.exit(0 if ok else 1)
