#!/usr/bin/env python3
"""Migrate a legacy workspace (no execution-<N>/ folder) to execution-0 (stdlib only).
Non-destructive: legacy files (PIPELINE_STATE.md, validation/, research, family files, plans) stay
where they are, because skills and agents cite those paths. It only ADDS execution-0/ and LATEST.
Usage: migrate_state.py <slug_dir> [--apply]     dry run by default (prints what it would record)
Reconstruction rules (every row says `migrate_state` as actor and "reconstructed" in its note):
  gates      Approvals rows named G1/G2/G3 (G3-A, G3 (commit plan)... merge into one gate file);
             an empty row whose approval appears in the Log becomes a gate quoting the log line
  decisions  every other Approvals row (pre-G1, intake, review, P6-F1, ...) -> who=user
  units      Units table rows with a State column (unknown states become PLANNED with a note)
  phases     P0..max phase named in the Log/header; the last one is done only when the Log shows
             commits applied or DONE
  events     INIT, one DISCREPANCY per contradiction found (header phase vs log), NOTE for legacy
             validation folders"""
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_event as se  # noqa: E402
import state_lib as sl  # noqa: E402

ACTOR = 'migrate_state'


def section(text, title):
    m = re.search(r'^## ' + title + r'.*?$(.*?)(?=^## |\Z)', text, re.M | re.S)
    return m.group(1) if m else ''


def table(block):
    lines = [l for l in block.splitlines() if l.startswith('|')]
    if len(lines) < 2:
        return [], []
    split = lambda l: [c.strip() for c in l.strip().strip('|').split('|')]
    return split(lines[0]), [split(l) for l in lines[2:]]


def kebab(s):
    s = re.sub(r'[`*()\[\]]', '', s).strip().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:60] or 'unit'


def plan(slug):
    st = os.path.join(slug, 'PIPELINE_STATE.md')
    text = open(st, encoding='utf-8').read() if os.path.isfile(st) else ''
    log = section(text, 'Log') + ''.join(section(text, t) for t in (r'20\d\d-',))
    actions = {'gates': {}, 'decisions': [], 'units': [], 'phases': [], 'events': []}
    if not text:
        actions['events'].append(('DISCREPANCY', 'no PIPELINE_STATE.md: state reconstructed from disk only; '
                                  'phases and gates unknown, ask the user before resuming'))
    head, rows = table(section(text, 'Approvals'))
    for r in rows:
        if len(r) < 4 or not r[0]:
            continue
        gate, date, scope, words = r[0], r[1], r[2], r[3]
        m = re.match(r'(G[123])\b', gate)
        if m and words:
            g = actions['gates'].setdefault(m.group(1), {'date': date, 'scope': [], 'words': []})
            g['scope'].append(f'{gate}: {scope}')
            g['words'].append(words)
        elif m:
            hit = re.search(r'^.*\b' + m.group(1) + r'\b[^\n]*approv[^\n]*$', text, re.M | re.I)
            if hit and m.group(1) not in actions['gates']:
                actions['gates'][m.group(1)] = {'date': date or '(from log)',
                                                'scope': [f'{gate}: reconstructed from log'],
                                                'words': [f'(not recorded in the table; log line) {hit.group(0).strip()[:300]}']}
                actions['events'].append(('DISCREPANCY', f'{m.group(1)} row empty in Approvals but approved in the log'))
        elif scope or words:
            actions['decisions'].append((f'{gate}: {scope}', words or '(no words recorded)'))
    head, rows = table(section(text, 'Units'))
    if head:
        si = next((i for i, h in enumerate(head) if h.lower() == 'state'), None)
        ni = next((i for i, h in enumerate(head) if 'skill' in h.lower()), 0)
        for r in rows:
            if not r or not r[0]:
                continue
            name = r[ni] if ni < len(r) and re.fullmatch(r'`?[a-z0-9-]+`?', r[ni] or '') else r[0]
            raw = r[si] if si is not None and si < len(r) else ''
            state = next((s for s in reversed(sl.STATES + ('DEFERRED', 'DROPPED')) if s in raw.upper()), None)
            actions['units'].append((kebab(name), state or 'PLANNED',
                                     f'reconstructed; legacy state cell: {raw[:80] or "(none)"}'))
    header = re.search(r'^current_phase:\s*(.*)$', text, re.M)
    header = header.group(1).strip() if header else ''
    nums = [int(x) for x in re.findall(r'\bP([0-9])\b', log + ' ' + header)]
    top = max(nums) if nums else None
    finished = re.search(r'commit(s)? (applied|groups|[0-9a-f]{7})|\bDONE\b|committed', log, re.I) is not None
    if top is not None:
        for k in range(top + 1):
            actions['phases'].append((f'P{k}', k < top or finished))
        hm = re.match(r'P([0-9])', header)
        if hm and int(hm.group(1)) != top:
            actions['events'].append(('DISCREPANCY', f'header said current_phase {header[:60]} but the log reaches P{top}'))
    vd = os.path.join(slug, 'validation')
    if os.path.isdir(vd):
        actions['events'].append(('NOTE', 'legacy round reports kept in place: ' +
                                  ', '.join(sorted(os.listdir(vd)))[:180]))
    return actions


def apply(slug, a):
    ex = os.path.join(slug, 'execution-0')
    for sub in ('state/phases', 'state/gates', 'state/units', 'rounds', 'plan', 'briefs'):
        os.makedirs(os.path.join(ex, sub), exist_ok=True)
    se.log(ex, 'P0', ACTOR, 'INIT', 'execution-0 migrated from the legacy layout (legacy files untouched)')
    for p, done in a['phases']:
        path = os.path.join(ex, 'state', 'phases', f'{p}.md')
        se.append(path, f'| {se.now()} | start | {ACTOR} | reconstructed from legacy log |',
                  se.template('PHASE.template.md', phase=p))
        if done:
            se.append(path, f'| {se.now()} | done | {ACTOR} | reconstructed from legacy log |')
    for g, v in sorted(a['gates'].items()):
        with open(os.path.join(ex, 'state', 'gates', f'{g}.md'), 'x', encoding='utf-8', newline='\n') as f:
            f.write(se.template('GATE.template.md', gate=g, date=v['date'], actor=ACTOR,
                                scope='RECONSTRUCTED from legacy PIPELINE_STATE.md — ' + ' ; '.join(v['scope']),
                                words=' / '.join(v['words'])))
    for text, words in a['decisions']:
        se.reg_append(ex, 'decisions', [None, 'none', 'user', ACTOR, text, f'verbatim (legacy): {words}'])
    for name, state, note in a['units']:
        se.append(os.path.join(ex, 'state', 'units', f'{name}.md'),
                  f'| {se.now()} | {state} |  |  | {ACTOR} | {se.clean(note)} |',
                  se.template('UNIT.template.md', unit=name))
    with open(os.path.join(ex, 'state', 'environment.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# Environment snapshots\n\nNot recorded: legacy run migrated by migrate_state.py. '
                'Take a snapshot (snapshot_env.py --write) before resuming.\n')
    for code, text in a['events']:
        se.log(ex, '-', ACTOR, code, text)
    with open(os.path.join(slug, 'LATEST'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('execution-0\n')
    return ex


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    slug = args[0].rstrip('/' + os.sep)
    if any(re.fullmatch(r'execution-\d+', d) for d in os.listdir(slug)):
        print(f'SKIP {slug}: already has execution-<N> folders')
        return
    if not os.path.isfile(os.path.join(slug, 'PACKAGE_BRIEF.md')):
        print(f'SKIP {slug}: no PACKAGE_BRIEF.md (not a building-agent-packages run)')
        return
    a = plan(slug)
    print(f'{slug}: {len(a["phases"])} phases, gates {sorted(a["gates"]) or "none"}, '
          f'{len(a["decisions"])} decisions, {len(a["units"])} units, {len(a["events"])} events')
    for code, text in a['events']:
        print(f'  {code}: {text}')
    if '--apply' not in args:
        print('  (dry run; add --apply to write execution-0/ and LATEST)')
        return
    print(f'  OK {apply(slug, a)}')


if __name__ == '__main__':
    main()
