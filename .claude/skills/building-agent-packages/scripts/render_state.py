#!/usr/bin/env python3
"""Render the PIPELINE_STATE.md dashboard of one execution from state/ and rounds/ (stdlib only).
Idempotent: same inputs, byte-identical output. Writes only <execution>/PIPELINE_STATE.md.
Usage: render_state.py <slug_dir> [--execution N] [--stdout]"""
import os
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


def main():
    args = sys.argv[1:]
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
                   [[k, *('yes' if v['kinds'][x] else '**missing**' for x in sl.ROUND_KINDS),
                     len(v['files']),
                     f'[scoreboard](rounds/{k}/scoreboard.md)' if 'scoreboard.md' in v['files'] else '-']
                    for k, v in s['rounds'].items()])
    arts = []
    for f in sorted(os.listdir(slug)):
        if f.startswith('research_') and f.endswith('.md'):
            arts.append(['research', f'../{f}'])
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
    t = open(TEMPLATE, encoding='utf-8').read()
    for k, v in (('slug', os.path.basename(os.path.abspath(slug))),
                 ('execution', os.path.basename(ex)), ('summary', summary), ('phases', phases),
                 ('gates', gates), ('units', unit_t), ('rounds', rounds),
                 ('artifacts', artifacts), ('open', open_t), ('log', log), ('cost', cost),
                 ('shared', shared), ('retro', retro)):
        t = t.replace('<' + k + '>', v)
    if '--stdout' in args:
        print(t)
        return
    with open(os.path.join(ex, 'PIPELINE_STATE.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(t)
    print(f'OK {os.path.join(ex, "PIPELINE_STATE.md")} (current phase {cur})')


if __name__ == '__main__':
    main()
