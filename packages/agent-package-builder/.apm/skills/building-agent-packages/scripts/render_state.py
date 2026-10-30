#!/usr/bin/env python3
"""Render the PIPELINE_STATE.md dashboard of one execution from state/ and rounds/ (stdlib only).
Idempotent: same inputs, byte-identical output. Writes only <execution>/PIPELINE_STATE.md.
Usage: render_state.py <slug_dir> [--execution N] [--stdout] [--by state_event|watch|render_state]
The Health section (locks, watcher, check_state result, update stamp) is the only time-dependent part."""
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_lib as sl  # noqa: E402

TEMPLATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'assets', 'PIPELINE_STATE.template.md')


def table(head, body):
    if not body:
        return '_none yet_'
    return '\n'.join(['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
                     + ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in body])


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def latest_by_target(scores, kind):
    """{target: score row} = the newest round that scored this target with this kind."""
    out = {}
    for r in scores:
        if r['kind'] == kind and num(r['score']) is not None:
            out[r['target']] = r
    return out


def scoreboard_panel(scores):
    """Target x round matrix of validate (audit for `audit`) scores, with delta and REGRESSION."""
    if not scores:
        return '_no scores yet (record one per report with `state_event.py ... score`)_'
    rounds = []
    for r in scores:
        if r['round'] not in rounds:
            rounds.append(r['round'])
    cell, tests = {}, latest_by_target(scores, 'test')
    for r in scores:
        if r['kind'] in ('validate', 'audit') and (r['kind'] == 'audit') == (r['target'] == 'audit'):
            sev = ' '.join(f'{r[k]}{k[0].upper()}' for k in ('high', 'medium') if r[k])
            cell[(r['target'], r['round'])] = (num(r['score']), f'{r["score"]}' + (f' ({sev})' if sev else ''))
    targets = sorted({t for t, _ in cell} | set(tests), key=lambda t: (t in ('package', 'audit'), t == 'audit', t))
    body = []
    for t in targets:
        seen = [cell[(t, k)][0] for k in rounds if (t, k) in cell and cell[(t, k)][0] is not None]
        delta = ''
        if len(seen) >= 2:
            d = seen[-1] - seen[-2]
            delta = f'**REGRESSION {d:+g}**' if d < 0 else f'{d:+g}'
        tr = tests.get(t)
        scen = f'{tr["pass"]}/{tr["total"]}' if tr and tr['total'] else '-'
        high = next((cell_row['high'] for cell_row in reversed(scores)
                     if cell_row['target'] == t and cell_row['high'] != ''), '')
        body.append([t, *(cell.get((t, k), (None, '-'))[1] for k in rounds), delta or '-', scen, high or '-'])
    return table(['Target', *rounds, 'Δ', 'Scenarios', 'HIGH'], body) + \
        '\n\nAudit is 0-10; every other score is 0-100 (`100 - 6/HIGH - 2.5/MEDIUM - 0.5/LOW`). ' \
        'A negative Δ is a stop rule of P6: show the diff to the user.'


def exit_panel(ex, scores):
    """P6 exit criteria from scores.md + findings.md (limits in state_lib.EXIT)."""
    if not scores:
        return '_no scores yet_'
    findings = sl.register(ex, 'findings')
    high = [i for i in sl.live_ids(ex, 'findings') if findings[i][0][3] == 'HIGH']
    val = latest_by_target(scores, 'validate')
    skills = {t: num(r['score']) for t, r in val.items() if t not in ('package', 'audit')}
    low = sorted(f'{t} ({s:g})' for t, s in skills.items() if s < sl.EXIT['skill_min'])
    pkg = num(val['package']['score']) / 10 if 'package' in val else None
    aud = latest_by_target(scores, 'audit').get('audit')
    aud = num(aud['score']) if aud else None
    tests = latest_by_target(scores, 'test').values()
    p = sum(int(r['pass']) for r in tests if r['pass'].isdigit())
    t = sum(int(r['total']) for r in tests if r['total'].isdigit())
    failing = sorted(f'{r["target"]} {r["pass"]}/{r["total"]}' for r in tests
                     if r['total'].isdigit() and r['pass'] != r['total'])
    rows_ = [
        (not high, '0 HIGH open', f'{len(high)} open' + (f' ({", ".join(high)})' if high else '')),
        (bool(skills) and not low, f'every skill >= {sl.EXIT["skill_min"]:g}',
         f'{len(low)} below: {", ".join(low)}' if low else f'{len(skills)} skills scored'),
        (pkg is not None and pkg >= sl.EXIT['package_min'], f'package >= {sl.EXIT["package_min"]:g}/10',
         f'{pkg:g}/10' if pkg is not None else 'not scored'),
        (aud is not None and aud >= sl.EXIT['audit_min'], f'audit >= {sl.EXIT["audit_min"]:g}/10',
         f'{aud:g}/10' if aud is not None else 'not scored'),
        (t > 0 and p == t, '100% scenarios pass', f'{p}/{t}' + (f' (failing: {", ".join(failing)})' if failing else '')),
    ]
    met = sum(1 for ok, _, _ in rows_ if ok)
    return '\n'.join(f'- [{"x" if ok else " "}] {name}: {why}' for ok, name, why in rows_) + \
        f'\n\n**{met}/5 met** · ' + ('exit P6' if met == 5 else 'loop continues (or leftovers go to G3)')


def findings_panel(ex):
    findings = sl.register(ex, 'findings')
    if not findings:
        return '_none yet_'
    by_round, by_target = {}, {}
    for fid, rs in findings.items():
        sev, rnd, tgt, status = rs[0][3], rs[0][4], rs[0][5], rs[-1][2]
        b = by_round.setdefault(rnd, {})
        b[(sev, status)] = b.get((sev, status), 0) + 1
        if status in sl.LIVE['findings']:
            bt = by_target.setdefault(tgt, {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0})
            bt[sev] += 1
    statuses = ('OPEN', 'REOPENED', 'DEFERRED', 'FIXED', 'WONTFIX')
    rk = lambda k: (0 if not re.search(r'\d', k) else 1, int(re.sub(r'\D', '', k) or 0), k)
    t1 = table(['Opened in', 'Severity', *statuses],
               [[r, sev, *(by_round[r].get((sev, s), 0) or '-' for s in statuses)]
                for r in sorted(by_round, key=rk) for sev in ('HIGH', 'MEDIUM', 'LOW')
                if any(by_round[r].get((sev, s)) for s in statuses)])
    t2 = table(['Target (open)', 'HIGH', 'MEDIUM', 'LOW'],
               [[k, v['HIGH'] or '-', v['MEDIUM'] or '-', v['LOW'] or '-']
                for k, v in sorted(by_target.items(), key=lambda kv: (-kv[1]['HIGH'], -kv[1]['MEDIUM'], kv[0]))])
    return t1 + '\n\n' + t2


def bar(frac, width=20):
    frac = max(0.0, min(frac, 1.0))
    full = round(frac * width)
    return '█' * full + '░' * (width - full)


def progress_panel(ex, slug, s, metrics):
    max_rounds, budget = sl.brief_budget(slug)
    spent = sum(int(r[3]) for r in metrics if r[2] == 'actual' and r[3].isdigit())
    lines = []
    if budget:
        lines.append(f'- Tokens: `{bar(spent / budget)}` {spent / 1e6:.2f}M / {budget / 1e6:.2f}M '
                     f'({100 * spent / budget:.0f}%)' + (' · **BUDGET EXCEEDED**' if spent > budget else ''))
    else:
        lines.append(f'- Tokens: {spent / 1e6:.2f}M spent · `token_budget` not set in PACKAGE_BRIEF.md')
    per_round = {}
    for r in metrics:
        if r[2] == 'actual' and re.fullmatch(r'round-\d+', r[1]) and r[3].isdigit():
            per_round[r[1]] = per_round.get(r[1], 0) + int(r[3])
    done = len(s['rounds'])
    rl = f'- Rounds: {done}' + (f' / {max_rounds} (max_rounds)' if max_rounds else '')
    if per_round:
        avg = sum(per_round.values()) / len(per_round)
        rl += f' · avg/round {avg / 1e6:.2f}M (from `metric round-<k>`)'
        if max_rounds and budget:
            left = max(max_rounds - done, 0)
            proj = spent + avg * min(left, 2)
            rl += f' · projection +{min(left, 2)} rounds: {proj / 1e6:.2f}M ' + \
                  ('(fits)' if proj <= budget else '(**over budget**: ask the user)')
    else:
        rl += ' · no per-round cost yet (record `metric round-<k> actual`)'
    lines.append(rl)
    states = {}
    for u in s['units'].values():
        states[u['state']] = states.get(u['state'], 0) + 1
    total = len(s['units'])
    v = states.get('VALIDATED', 0)
    lines.append(f'- Units: `{bar(v / total if total else 0)}` {v}/{total} VALIDATED · '
                 + ' · '.join(f'{n} {k}' for k, n in sorted(states.items()) if k != 'VALIDATED'))
    return '\n'.join(lines)


def health_panel(ex, s, by):
    import datetime
    import subprocess
    nowdt = datetime.datetime.now()
    out = []
    running = []
    for k, v in s['rounds'].items():
        for f in v['files']:
            if f.endswith('.running'):
                started = open(os.path.join(ex, 'rounds', k, f), encoding='utf-8').read().split('|')[0].strip()
                running.append(f'{k}/{f[:-8]} since {started}')
    out.append(['Reviewers running', ', '.join(running) or 'none'])
    lp = os.path.join(ex, '.run.lock')
    if os.path.isfile(lp):
        info = open(lp, encoding='utf-8').read().split()
        out.append(['Run lock', f'pid {info[0]} on {info[1]} since {info[2]}' if len(info) > 2 else 'held'])
    else:
        out.append(['Run lock', 'none (run finished or not started)'])
    sp = sl.SHARED_LOCK
    if os.path.isfile(sp):
        info = open(sp, encoding='utf-8').read().split()
        age = ''
        try:
            age_h = (nowdt - datetime.datetime.fromisoformat(info[-1])).total_seconds() / 3600
            age = f' · **{age_h:.0f} h old: stale, ask the user**' if age_h >= 12 else ''
        except (ValueError, IndexError):
            pass
        out.append(['Shared lock', f'held by {info[0]} since {info[-1]}{age}'])
    else:
        out.append(['Shared lock', 'free'])
    hb = os.path.join(ex, '.watch.heartbeat')
    if os.path.isfile(hb):
        parts = open(hb, encoding='utf-8').read().split()
        interval = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 300
        try:
            last = datetime.datetime.fromisoformat(parts[0])
            alive = (nowdt - last).total_seconds() <= 2 * interval + 5
        except (ValueError, IndexError):
            last, alive = None, False
        out.append(['Watcher (5-min refresh)', f'alive, every {interval}s' if alive else
                    f'**stopped** (last tick {parts[0] if parts else "?"}): restart `watch_state.py`'])
    else:
        out.append(['Watcher (5-min refresh)', 'not started (`watch_state.py`, started in P0)'])
    drift = sl.builder_drift()
    out.append(['Builder scripts in .claude/', f'**stale vs source**: {", ".join(drift)} (run scripts from '
                'packages/; fixed by the P8 install)' if drift else 'match source'])
    nxt = next((g for g in sl.GATES if g not in s['gates']), None)
    out.append(['Next gate', {'G1': 'G1 at the end of P2', 'G2': 'G2 at the end of P3 (pilot)',
                              'G3': 'G3 at the end of P8'}.get(nxt, 'G4 (push) - always the user')])
    try:
        p = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'check_state.py'),
                            os.path.dirname(ex), '--execution', os.path.basename(ex).removeprefix('execution-')],
                           capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
        probs = [l.strip()[2:] for l in p.stdout.splitlines() if l.strip().startswith('- ')]
        out.append(['check_state.py', 'OK' if p.returncode == 0 else f'**{len(probs)} problem(s)**: ' + '; '.join(probs[:3])])
    except (OSError, subprocess.TimeoutExpired) as e:
        out.append(['check_state.py', f'not run: {e}'])
    stamp = nowdt.replace(microsecond=0).isoformat()
    return table(['Check', 'Status'], out) + f'\n\n_Updated {stamp} by {by}._'


def round_scoreboards(ex, scores):
    """Write rounds/<k>/scoreboard.md from scores.md (only when the content changes)."""
    for k in {r['round'] for r in scores if r['round'] != 'pilot'}:
        d = os.path.join(ex, 'rounds', k)
        if not os.path.isdir(d):
            continue
        rs = [r for r in scores if r['round'] == k]
        body = table(['Target', 'Kind', 'Score', 'HIGH', 'MEDIUM', 'LOW', 'Pass', 'Total', 'Note'],
                     [[r['target'], r['kind'], r['score'], r['high'] or '-', r['medium'] or '-',
                       r['low'] or '-', r['pass'] or '-', r['total'] or '-', r['note'] or '-'] for r in rs])
        text = (f'# Scoreboard - {k}\n\n> GENERATED by `scripts/render_state.py` from `state/scores.md`. '
                f'Do not edit: record scores with `state_event.py ... score`.\n\n{body}\n\n'
                f'## Across rounds\n\n{scoreboard_panel(scores)}\n')
        p = os.path.join(d, 'scoreboard.md')
        if not os.path.isfile(p) or open(p, encoding='utf-8').read() != text:
            write_atomic(p, text)


def write_atomic(path, text):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    os.replace(tmp, path)


def main():
    args = sys.argv[1:]
    by = args[args.index('--by') + 1] if '--by' in args else 'render_state'
    n = args[args.index('--execution') + 1] if '--execution' in args else None
    slug = args[0]
    ex = sl.resolve(slug, n)
    if not ex:
        print('no execution folder (legacy layout?): run state_event.py init, or migrate_state.py')
        sys.exit(1)
    s = sl.load(ex)
    cur = sl.current_phase(s)
    units = s['units']
    validated = sum(1 for u in units.values() if u['state'] == 'VALIDATED')
    summary = '\n'.join([
        f'- **Current phase:** {cur}',
        f'- **Units:** {len(units)} ({validated} VALIDATED)',
        f'- **Gates recorded:** {", ".join(sorted(s["gates"])) or "none"}',
        f'- **Rounds:** {len(s["rounds"])}',
        f'- **Findings open:** {len(sl.live_ids(ex, "findings"))} · **Deferred open:** '
        f'{len(sl.live_ids(ex, "deferred"))} · **Decisions:** {len(sl.register(ex, "decisions"))} · '
        f'**Sources:** {len(sl.register(ex, "sources"))}',
        f'- **Events:** {len(s["events"])}'])
    phases = table(['Phase', 'Status', 'Started', 'Done', 'Note', 'File'],
                   [[p, v['status'], v['started'], v['done'], v['note'],
                     f'[{p}](state/phases/{p}.md)'] for p, v in s['phases'].items()])
    gates = table(['Gate', 'Date', 'Scope approved', 'User words'],
                  [[g, v['date'], v['scope'], v['words']] for g, v in sorted(s['gates'].items())])
    unit_t = table(['Unit', 'State', 'Last score', 'Transitions', 'File'],
                   [[k, v['state'], v['score'], v['history'], f'[{k}](state/units/{k}.md)']
                    for k, v in units.items()])
    rounds = table(['Round', 'Validate', 'Test', 'Audit', 'Files', 'Scoreboard'],
                   [[k, *('yes' if v['kinds'][x] is True else 'running' if v['kinds'][x] == 'running' else '**missing**'
                            for x in sl.ROUND_KINDS),
                     len(v['files']),
                     f'[scoreboard](rounds/{k}/scoreboard.md)' if 'scoreboard.md' in v['files'] else '-']
                    for k, v in s['rounds'].items()])
    arts = []
    arts += [['research', f'../{rel}'] for rel, _ in sl.research_files(slug)]
    for f in ('environment.md', 'findings.md', 'deferred.md', 'decisions.md', 'sources.md'):
        if os.path.isfile(os.path.join(ex, 'state', f)):
            arts.append(['state', f'state/{f}'])
    for sub in ('plan', 'briefs'):
        d = os.path.join(ex, sub)
        arts += [[sub, f'{sub}/{f}'] for f in sorted(os.listdir(d))] if os.path.isdir(d) else []
    artifacts = table(['Kind', 'Path'], arts)
    opened = [[p, 'phase started, not done'] for p, v in s['phases'].items()
              if v['status'] != 'done' and p != cur]
    if 'P6' in s['phases'] and s['phases']['P6']['status'] == 'done':
        opened += [[k, f'unit still {v["state"]} after P6'] for k, v in units.items()
                   if v['state'] not in ('VALIDATED', 'DEFERRED', 'DROPPED')]
    findings = sl.register(ex, 'findings')
    for i in sl.live_ids(ex, 'findings'):
        last = findings[i][-1]
        reopen = sum(1 for x in findings[i] if x[2] == 'REOPENED')
        opened.append([f'[{i}](state/findings.md)', f'{last[3]} {last[2]} on {last[5]}: {last[7]}'
                       + (f' (reopened {reopen}x: ask the user)' if reopen >= 2 else '')])
    deferred = sl.register(ex, 'deferred')
    for i in sl.live_ids(ex, 'deferred'):
        last = deferred[i][-1]
        opened.append([f'[{i}](state/deferred.md)', f'deferred, owner {last[3]}, resume when {last[4]}: {last[6]}'])
    for url, rs in sl.register(ex, 'sources').items():
        if rs[-1][4] == 'yes':
            opened.append([url, 'fetched page carried injected instructions (treated as data)'])
    open_t = table(['Item', 'Why'], opened)
    metrics = sl.rows(os.path.join(ex, 'state', 'metrics.md'))
    tot = {}
    for r in metrics:
        k = tot.setdefault(r[1], {'estimate': 0, 'actual': 0})
        k[r[2]] += int(r[3]) if r[3].isdigit() else 0
    max_rounds, budget = sl.brief_budget(slug)
    spent = sum(v['actual'] for v in tot.values())
    cost = table(['Scope', 'Estimate (tokens)', 'Actual (tokens)'],
                 [[k, v['estimate'], v['actual']] for k, v in sorted(tot.items())])
    cost += (f'\n\nBudget: {spent} of {budget} tokens' if budget else '\n\nBudget: not set in PACKAGE_BRIEF.md') \
        + (f' · max_rounds {max_rounds}' if max_rounds else '')
    shared = table(['Path', 'HEAD', 'Now', 'Note'],
                   [[p, rs[-1][2], rs[-1][3], rs[-1][5]]
                    for p, rs in sorted(sl.register(ex, 'shared-touch').items())])
    retro = table(['ID', 'Kind', 'Target', 'Text'],
                  [[i, rs[-1][2], rs[-1][3], rs[-1][5]] for i, rs in sl.register(ex, 'retro').items()])
    log = '\n'.join(f'- `{l}`' for l in s['events'][-20:]) or '_none yet_'
    scores = sl.scores(ex)
    round_scoreboards(ex, scores)
    t = open(TEMPLATE, encoding='utf-8').read()
    for k, v in (('slug', os.path.basename(os.path.abspath(slug))),
                 ('execution', os.path.basename(ex)), ('summary', summary), ('phases', phases),
                 ('gates', gates), ('units', unit_t), ('rounds', rounds),
                 ('artifacts', artifacts), ('open', open_t), ('log', log), ('cost', cost),
                 ('shared', shared), ('retro', retro), ('scoreboard', scoreboard_panel(scores)),
                 ('exit', exit_panel(ex, scores)), ('findings', findings_panel(ex)),
                 ('progress', progress_panel(ex, slug, s, metrics)), ('health', health_panel(ex, s, by))):
        t = t.replace('<' + k + '>', v)
    if '--stdout' in args:
        print(t)
        return
    write_atomic(os.path.join(ex, 'PIPELINE_STATE.md'), t)
    print(f'OK {os.path.join(ex, "PIPELINE_STATE.md")} (current phase {cur})')


if __name__ == '__main__':
    main()
