"""Shared read-only parsing of an execution folder (stdlib only). Imported by render_state.py,
check_state.py and inspect_workspace.py; never writes."""
import os
import re

PHASES = [f'P{i}' for i in range(10)]
GATES = ('G1', 'G2', 'G3')
STATES = ('PLANNED', 'RESEARCHED', 'AUTHORED', 'VERIFIED', 'VALIDATED')
ROUND_KINDS = ('validate', 'test', 'audit')
ROUND_FILE = re.compile(r'(validate|test|audit)__[a-z0-9][a-z0-9.-]*\.md|scoreboard\.md')


def rows(path):
    """Table rows of an append-only state file (rows start with a timestamp)."""
    if not os.path.isfile(path):
        return []
    return [[c.strip() for c in l.strip().strip('|').split('|')]
            for l in open(path, encoding='utf-8').read().splitlines() if l.startswith('| 20')]


def resolve(slug, n=None):
    """Execution folder for slug: explicit N, else LATEST, else None (legacy layout)."""
    if n is None:
        lp = os.path.join(slug, 'LATEST')
        if not os.path.isfile(lp):
            return None
        n = open(lp, encoding='utf-8').read().strip().replace('execution-', '')
    ex = os.path.join(slug, f'execution-{n}')
    return ex if os.path.isdir(ex) else None


def load(ex):
    st = os.path.join(ex, 'state')
    out = {'phases': {}, 'gates': {}, 'units': {}, 'rounds': {}, 'events': []}
    for p in PHASES:
        r = rows(os.path.join(st, 'phases', f'{p}.md'))
        if r:
            out['phases'][p] = {'status': r[-1][1], 'started': r[0][0],
                                'done': r[-1][0] if r[-1][1] == 'done' else '', 'note': r[-1][3]}
    for g in GATES:
        gp = os.path.join(st, 'gates', f'{g}.md')
        if os.path.isfile(gp):
            t = open(gp, encoding='utf-8').read()
            get = lambda k: (re.search(r'\*\*' + k + r':\*\*\s*(.*)', t) or [None, ''])[1].strip()
            words = re.search(r'^> (.*)$', t, re.M)
            out['gates'][g] = {'date': get('Date'), 'scope': get('Scope approved'),
                               'words': words.group(1).strip() if words else ''}
    ud = os.path.join(st, 'units')
    for f in sorted(os.listdir(ud)) if os.path.isdir(ud) else []:
        r = rows(os.path.join(ud, f))
        if r:
            scores = [x[2] for x in r if x[2]]
            out['units'][f[:-3]] = {'state': r[-1][1], 'score': scores[-1] if scores else '',
                                    'history': len(r)}
    rd = os.path.join(ex, 'rounds')
    for k in sorted(os.listdir(rd), key=lambda s: int(re.sub(r'\D', '', s) or 0)) \
            if os.path.isdir(rd) else []:
        files = sorted(os.listdir(os.path.join(rd, k)))
        out['rounds'][k] = {'files': files,
                            'kinds': {x: any(f.startswith(x + '__') for f in files) for x in ROUND_KINDS},
                            'bad_names': [f for f in files if not ROUND_FILE.fullmatch(f)]}
    ev = os.path.join(st, 'events.log')
    if os.path.isfile(ev):
        out['events'] = [l for l in open(ev, encoding='utf-8').read().splitlines() if l.strip()]
    return out


def current_phase(s):
    """First phase without done, after the last started one; P0 when nothing started."""
    started = [p for p in PHASES if p in s['phases']]
    if not started:
        return 'P0'
    last = started[-1]
    if s['phases'][last]['status'] != 'done':
        return last
    i = PHASES.index(last)
    return PHASES[i + 1] if i + 1 < len(PHASES) else 'DONE'


CODES = ('PHASE_START', 'PHASE_DONE', 'GATE', 'UNIT_STATE', 'ROUND_DONE', 'FIX', 'SWEEP',
         'INCIDENT', 'DEFER', 'DISCREPANCY', 'LOCK', 'UNLOCK', 'INIT', 'NOTE', 'FINDING',
         'DECISION', 'SOURCE', 'ENV', 'PREFLIGHT', 'METRIC', 'RETRO',
         'TOUCH', 'SHARED_LOCK', 'SHARED_UNLOCK', 'BUDGET')
# Registers: append-only tables under state/. Column 1 after the timestamp is the ID, column 2 the
# status (or the register-specific field). The latest row of an ID is its current value.
REGISTERS = {
    'findings': ('FINDINGS.template.md', ('OPEN', 'FIXED', 'WONTFIX', 'DEFERRED', 'REOPENED')),
    'deferred': ('DEFERRED.template.md', ('OPEN', 'RESUMED', 'CLOSED')),
    'decisions': ('DECISIONS.template.md', None),
    'sources': ('SOURCES.template.md', None),
    'metrics': ('METRICS.template.md', None),
    'retro': ('RETRO.template.md', None),
    'shared-touch': ('SHARED_TOUCH.template.md', None),
}
SHARED_LOCK = os.path.join('workspace', '.shared.lock')
SHARED_FILES = ('apm.yml', 'apm.lock.yaml', 'CLAUDE.md', 'README.md', 'docs/', '.claude/', 'scripts/')


def brief_budget(slug):
    """(max_rounds, token_budget) from PACKAGE_BRIEF.md; None when absent or not set."""
    bp = os.path.join(slug, 'PACKAGE_BRIEF.md')
    t = open(bp, encoding='utf-8').read() if os.path.isfile(bp) else ''
    get = lambda k: int(m.group(1)) if (m := re.search(r'^' + k + r':\s*(\d+)', t, re.M)) else None
    return get('max_rounds'), get('token_budget')
LIVE = {'findings': ('OPEN', 'REOPENED', 'DEFERRED'), 'deferred': ('OPEN', 'RESUMED')}


def register(ex, name):
    """{id: [rows in order]} for one register of an execution."""
    out = {}
    for r in rows(os.path.join(ex, 'state', f'{name}.md')):
        if len(r) > 1:
            out.setdefault(r[1], []).append(r)
    return out


def live_ids(ex, name):
    """IDs whose latest status is still open (findings, deferred)."""
    return [i for i, rs in register(ex, name).items() if rs[-1][2] in LIVE.get(name, ())]


def lock_owners(lock='apm.lock.yaml'):
    """{deployed path: package} from the deployed_files lists of apm.lock.yaml (repo root)."""
    owners, cur, in_list = {}, None, False
    if not os.path.isfile(lock):
        return owners
    for line in open(lock, encoding='utf-8'):
        m = re.match(r'^- repo_url:\s*(\S+)', line)
        if m:
            cur, in_list = m.group(1).replace('_local/', ''), False
            continue
        if re.match(r'^  deployed_files:\s*$', line):
            in_list = True
            continue
        if in_list:
            m = re.match(r'^  - (\S+)\s*$', line)
            if m:
                owners[m.group(1)] = cur
            else:
                in_list = False
    return owners


def owner_of(path, owners=None):
    """Package that deploys a .claude/ path: the lock first, then the source tree in packages/."""
    path = path.replace(os.sep, '/')
    owners = lock_owners() if owners is None else owners
    if path in owners:
        return owners[path]
    parts = path.split('/')
    if len(parts) < 3 or parts[0] != '.claude':
        return '?'
    kind, name = parts[1], parts[2]
    pats = {'skills': [f'skills/{name}'],
            'agents': [f'agents/{name[:-3]}.agent.md', f'agents/{name}'],
            'rules': [f'instructions/{name[:-3]}.instructions.md', f'rules/{name}']}.get(kind, [])
    for pkg in sorted(os.listdir('packages')) if os.path.isdir('packages') else []:
        if any(os.path.exists(os.path.join('packages', pkg, '.apm', p)) for p in pats):
            return pkg
    return 'unowned (not in the lock nor in packages/)'
