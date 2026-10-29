#!/usr/bin/env python3
"""Consistency checks for one execution (stdlib only, read-only). Exit 1 on any problem.
Usage: check_state.py <slug_dir> [--execution N]
Checks: phase order and done-without-start, gates required before the phases they unlock,
units left behind after P6, round reports missing a kind or misnamed, event codes, environment
snapshot after P0, PREFLIGHT before P8, findings reopened twice without a decision, HIGH findings
open at G3/P9, sources read more than 12 months ago (and a warning for injected pages)."""
import datetime
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_lib as sl  # noqa: E402

CODES = set(sl.CODES)
# gate -> first phase it unlocks. P7 is optional (only when a family fact changed).
GATE_BEFORE = {'G1': 'P3', 'G2': 'P4', 'G3': 'P9'}
OPTIONAL = {'P7'}


def main():
    args = sys.argv[1:]
    n = args[args.index('--execution') + 1] if '--execution' in args else None
    ex = sl.resolve(args[0], n)
    if not ex:
        print('no execution folder (legacy layout?)')
        sys.exit(1)
    s = sl.load(ex)
    problems = []
    warnings = []
    started = [p for p in sl.PHASES if p in s['phases']]
    for p in started:
        i = sl.PHASES.index(p)
        for q in sl.PHASES[:i]:
            if q not in OPTIONAL and s['phases'].get(q, {}).get('status') != 'done':
                problems.append(f'{p} started but {q} is not done')
                break
    for g, p in GATE_BEFORE.items():
        if p in s['phases'] and g not in s['gates']:
            problems.append(f'{p} started without {g} recorded in state/gates/{g}.md')
    if s['phases'].get('P6', {}).get('status') == 'done':
        for k, v in s['units'].items():
            if v['state'] not in ('VALIDATED', 'DEFERRED', 'DROPPED'):
                problems.append(f'unit {k} is {v["state"]} after P6 done (VALIDATED/DEFERRED/DROPPED)')
        if not s['rounds']:
            problems.append('P6 done with no rounds/ folder')
    for k, v in s['rounds'].items():
        if not re.fullmatch(r'round-\d+', k):
            problems.append(f'round folder {k} not named round-<k>')
        for kind, ok in v['kinds'].items():
            if not ok:
                problems.append(f'{k}: no {kind}__<target>.md report')
        for b in v['bad_names']:
            problems.append(f'{k}: {b} not named <validate|test|audit>__<target>.md')
    for i, l in enumerate(s['events'], 1):
        parts = [x.strip() for x in l.split('|')]
        if len(parts) != 5 or parts[3] not in CODES:
            problems.append(f'events.log line {i} malformed: {l[:80]}')
    if s['phases'].get('P0', {}).get('status') == 'done' and \
            not os.path.isfile(os.path.join(ex, 'state', 'environment.md')):
        problems.append('P0 done without state/environment.md (run snapshot_env.py --write)')
    codes = [l.split('|')[3].strip() for l in s['events'] if l.count('|') == 4]
    if 'P8' in s['phases'] and 'PREFLIGHT' not in codes:
        problems.append('P8 started without a PREFLIGHT event (run preflight_apm.py before apm install)')
    findings = sl.register(ex, 'findings')
    decided = ' '.join(r[5] + ' ' + r[6] for rs in sl.register(ex, 'decisions').values() for r in rs)
    for i, rs in findings.items():
        last = rs[-1]
        if sum(1 for x in rs if x[2] == 'REOPENED') >= 2 and last[2] != 'FIXED' and i not in decided:
            problems.append(f'{i} reopened twice: ask the user and record a decision citing {i}')
        if ('P9' in s['phases'] or 'G3' in s['gates']) and last[3] == 'HIGH' \
                and last[2] in ('OPEN', 'REOPENED'):
            problems.append(f'{i} HIGH still {last[2]} at G3/P9 (fix it or mark DEFERRED with a note)')
    today = datetime.date.today()
    for url, rs in sl.register(ex, 'sources').items():
        try:
            age = (today - datetime.date.fromisoformat(rs[-1][2])).days
        except ValueError:
            problems.append(f'source {url}: bad read date {rs[-1][2]}')
            continue
        if age > 365:
            problems.append(f'source {url} read {age} days before today (> 12 months): re-read it')
        if rs[-1][4] == 'yes':
            warnings.append(f'source {url} carried injected instructions; confirm nothing acted on them')
    slug = os.path.dirname(os.path.abspath(ex))
    max_rounds, budget = sl.brief_budget(slug)
    if max_rounds and len(s['rounds']) > max_rounds and 'max_rounds' not in decided:
        problems.append(f'{len(s["rounds"])} rounds > max_rounds {max_rounds} without a decision citing max_rounds')
    spent = sum(int(r[3]) for r in sl.rows(os.path.join(ex, 'state', 'metrics.md'))
                if r[2] == 'actual' and r[3].isdigit())
    if budget and spent > budget and 'token_budget' not in decided:
        problems.append(f'actual {spent} tokens > token_budget {budget} without a decision citing token_budget')
    if 'P4' in s['phases'] and not budget:
        warnings.append('P4 started with token_budget 0 in PACKAGE_BRIEF.md (set it from the P3 estimate at G2)')
    plan = os.path.join(ex, 'plan', 'commit-plan.json')
    touched = list(sl.register(ex, 'shared-touch'))
    if touched and ('G3' in s['gates'] or 'P9' in s['phases']):
        try:
            planned = {p.replace(os.sep, '/') for g in json.load(open(plan, encoding='utf-8'))
                       for p in g.get('paths', [])}
        except (OSError, ValueError):
            planned = set()
            problems.append('shared files were touched but plan/commit-plan.json is missing or invalid')
        for p in touched:
            if planned and not any(p == q or p.startswith(q.rstrip('/') + '/') for q in planned):
                problems.append(f'shared file {p} touched but not in plan/commit-plan.json (G3 must show it)')
    if 'P9' in s['phases'] and 'SHARED_LOCK' not in codes:
        problems.append('P9 started without the shared lock (state_event.py ... shared-lock)')
    if sl.current_phase(s) == 'DONE':
        if codes.count('SHARED_LOCK') > codes.count('SHARED_UNLOCK'):
            problems.append('shared lock not released after P9 (shared-unlock)')
        if not sl.register(ex, 'retro'):
            warnings.append('run finished with no retro rows: record at least one lesson')
    advanced = [k for k, v in s['units'].items() if v['state'] != 'PLANNED']
    bd = os.path.join(ex, 'briefs')
    if advanced and not (os.path.isdir(bd) and os.listdir(bd)):
        warnings.append('units moved past PLANNED but briefs/ is empty: save every worker brief')
    if os.path.isfile(os.path.join(ex, '.run.lock')) and sl.current_phase(s) == 'DONE':
        problems.append('.run.lock still present after P9 done')
    print(f'{ex}: current phase {sl.current_phase(s)}, {len(s["units"])} units, '
          f'{len(s["rounds"])} rounds')
    for w in warnings:
        print('  warning:', w)
    print('PROBLEMS:' if problems else 'OK, no problems')
    for p in problems:
        print('  -', p)
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
