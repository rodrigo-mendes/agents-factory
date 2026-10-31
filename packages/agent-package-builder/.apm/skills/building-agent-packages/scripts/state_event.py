#!/usr/bin/env python3
"""The only writer of execution state (stdlib only). Every call appends; nothing is rewritten.
Usage: state_event.py <slug_dir> <command> [args] [--execution N] [--actor NAME]
  init [--inherit]                    create execution-<N+1>, point LATEST at it
  phase <P0..P9> start|done [--note T]
  gate <G1|G2|G3> --scope T --words T write-once; refuses when the gate file exists
  unit <name> <STATE> [--score S] [--tokens N] [--note T]
  event <PHASE> <CODE> <text>         free log line with a closed event code
  lock | unlock [--stale]             one session per execution (.run.lock)
  finding add --sev HIGH|MEDIUM|LOW --round R --target T --text X     -> prints F-<nnn>
  finding <F-nnn> FIXED|WONTFIX|DEFERRED|REOPENED --round R [--note X]
  defer add --owner O --trigger T --text X                           -> prints D-<nnn>
  defer <D-nnn> RESUMED|CLOSED [--note X]
  decide --gate G1|G2|G3|none --who user|orchestrator --text X --reason Y -> DEC-<nnn>
  source <url> --read-on YYYY-MM-DD --official yes|no [--injection yes|no] --used-by X
  metric <scope> estimate|actual --tokens N [--minutes M] [--note X]  (scope: unit, phase or run)
  retro add --kind brief|known-failure|lesson --target T --text X     -> prints R-<nnn>
  touch <repo-path> [--note X]          record a change to a file other runs also own
  shared-lock | shared-unlock [--stale] repo-wide lock (workspace/.shared.lock) for P8/P9
  round-start <round-k> <validate|test|audit> <target>  mark a reviewer as launched (writes
                                      rounds/<round-k>/<kind>__<target>.running; the report replaces it)
  score <pilot|round-k> <target> --kind validate|test|audit --score S [--high N --medium N --low N]
        [--pass P --total T] [--note X]   one row per review report (state/scores.md)
  render                              regenerate PIPELINE_STATE.md (and each round's scoreboard.md)
Every successful write re-renders the dashboard; add --no-render to batch many writes, then `render`.
Layout and formats: blueprints/state-layout.md. Exit 1 on any refused write."""
import datetime
import os
import re
import shutil
import socket
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_lib as sl  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), 'assets')
PHASES = [f'P{i}' for i in range(10)]
GATES = ('G1', 'G2', 'G3')
STATES = ('PLANNED', 'RESEARCHED', 'AUTHORED', 'VERIFIED', 'VALIDATED')
SIDE_STATES = ('DEFERRED', 'DROPPED')
CODES = sl.CODES
STALE_HOURS = 12


def die(msg):
    print('REFUSED:', msg)
    sys.exit(1)


def opt(args, name, default=None):
    if name in args:
        i = args.index(name)
        if i + 1 >= len(args):
            die(f'{name} needs a value')
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return default


def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def clean(t):
    return ' '.join(str(t).split()).replace('|', '/')[:200]


class FileLock:
    """Cross-process lock: O_EXCL create of <path>.lck, retried for up to 10 s."""

    def __init__(self, path):
        self.lck = path + '.lck'

    def __enter__(self):
        for _ in range(200):
            try:
                os.close(os.open(self.lck, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return self
            except FileExistsError:
                time.sleep(0.05)
        die(f'could not lock {self.lck} (remove it if no writer is running)')

    def __exit__(self, *a):
        os.remove(self.lck)


def append(path, line, header=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with FileLock(path):
        new = not os.path.isfile(path)
        with open(path, 'a', encoding='utf-8', newline='\n') as f:
            if new and header:
                f.write(header)
            f.write(line + '\n')


def template(name, **kv):
    t = open(os.path.join(ASSETS, name), encoding='utf-8').read()
    for k, v in kv.items():
        t = t.replace('<' + k + '>', v)
    return t


def executions(slug):
    return sorted((int(m.group(1)) for d in os.listdir(slug)
                   if (m := re.fullmatch(r'execution-(\d+)', d))), key=int)


def resolve(slug, n):
    if n is None:
        lp = os.path.join(slug, 'LATEST')
        if not os.path.isfile(lp):
            die('no LATEST; run init first')
        n = open(lp, encoding='utf-8').read().strip().removeprefix('execution-')
    ex = os.path.join(slug, f'execution-{n}')
    if not os.path.isdir(ex):
        die(f'{ex} does not exist')
    return ex


def log(ex, phase, actor, code, text):
    if code not in CODES:
        die(f'event code {code} not in {CODES}')
    append(os.path.join(ex, 'state', 'events.log'),
           f'{now()} | {phase} | {clean(actor)} | {code} | {clean(text)}')


def last_row(path):  # same row rule as state_lib.rows
    if not os.path.isfile(path):
        return None
    rows = [l for l in open(path, encoding='utf-8').read().splitlines()
            if l.startswith('| 20')]
    return [c.strip() for c in rows[-1].strip('|').split('|')] if rows else None


def cmd_init(slug, args, actor):
    os.makedirs(slug, exist_ok=True)
    nums = executions(slug)
    n = (nums[-1] + 1) if nums else 1
    ex = os.path.join(slug, f'execution-{n}')
    for sub in ('state/phases', 'state/gates', 'state/units', 'rounds', 'plan', 'briefs'):
        os.makedirs(os.path.join(ex, sub), exist_ok=True)
    name = os.path.basename(os.path.abspath(slug))
    for src, dst in (('PACKAGE_BRIEF.template.md', 'PACKAGE_BRIEF.md'),
                     ('FAMILY_FACTS.template.md', '_family_facts.md'),
                     ('FAMILY_RULES.template.md', '_family_rules.md')):
        if not os.path.exists(os.path.join(slug, dst)):
            shutil.copyfile(os.path.join(ASSETS, src), os.path.join(slug, dst))
    inherited = []
    if '--inherit' in args and nums:
        prev = os.path.join(slug, f'execution-{nums[-1]}')
        for reg in ('findings', 'deferred', 'decisions'):
            regs = sl.register(prev, reg)
            keep = sl.live_ids(prev, reg) if reg in sl.LIVE else list(regs)
            path = os.path.join(ex, 'state', f'{reg}.md')
            for i in keep:  # full history of each carried ID, so the repeat count survives
                for row in regs[i]:
                    append(path, '| ' + ' | '.join(row) + ' |', template(sl.REGISTERS[reg][0]))
            if keep:
                inherited.append(f'{reg}:{len(keep)}')
    with open(os.path.join(slug, 'LATEST'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'execution-{n}\n')
    log(ex, 'P0', actor, 'INIT', f'{name} execution-{n} created; inherited: {inherited or "none"}')
    print(f'OK {ex}')


def cmd_phase(ex, args, actor):
    if len(args) < 2 or args[0] not in PHASES or args[1] not in ('start', 'done'):
        die('usage: phase <P0..P9> start|done [--note T]')
    p, status = args[0], args[1]
    note = opt(args, '--note', '')
    path = os.path.join(ex, 'state', 'phases', f'{p}.md')
    last = last_row(path)
    if status == 'done' and (not last or last[1] != 'start'):
        die(f'{p} done without a prior start')
    append(path, f'| {now()} | {status} | {clean(actor)} | {clean(note)} |',
           template('PHASE.template.md', phase=p))
    log(ex, p, actor, 'PHASE_START' if status == 'start' else 'PHASE_DONE', note or status)
    print(f'OK {p} {status}')


def cmd_gate(ex, args, actor):
    if not args or args[0] not in GATES:
        die('usage: gate <G1|G2|G3> --scope T --words T')
    g = args.pop(0)
    scope, words = opt(args, '--scope'), opt(args, '--words')
    if not scope or not words:
        die('--scope and --words (the verbatim user answer) are both required')
    path = os.path.join(ex, 'state', 'gates', f'{g}.md')
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        die(f'{g} already recorded (write-once); log a DISCREPANCY event instead')
    with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
        f.write(template('GATE.template.md', gate=g, date=now(), actor=actor,
                         scope=scope.strip(), words=words.strip()))
    log(ex, {'G1': 'P2', 'G2': 'P3', 'G3': 'P8'}[g], actor, 'GATE', f'{g} approved: {scope}')
    print(f'OK {g}')


def cmd_unit(ex, args, actor):
    if len(args) < 2:
        die('usage: unit <name> <STATE> [--score S] [--tokens N] [--note T]')
    score, tokens, note = opt(args, '--score', ''), opt(args, '--tokens', ''), opt(args, '--note', '')
    name, state = args[0], args[1]
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', name):
        die('unit name must be kebab-case')
    if state not in STATES + SIDE_STATES:
        die(f'state {state} not in {STATES + SIDE_STATES}')
    path = os.path.join(ex, 'state', 'units', f'{name}.md')
    last = last_row(path)
    if last and state in STATES and last[1] in STATES:
        if STATES.index(state) < STATES.index(last[1]) and not note:
            die(f'{name}: {last[1]} -> {state} goes backwards; give --note with the reason')
    append(path, f'| {now()} | {state} | {clean(score)} | {clean(tokens)} | {clean(actor)} | {clean(note)} |',
           template('UNIT.template.md', unit=name))
    log(ex, '-', actor, 'UNIT_STATE', f'{name} -> {state}' + (f' score={score}' if score else ''))
    print(f'OK {name} {state}')


def cmd_round_start(ex, args, actor):
    if len(args) != 3 or not re.fullmatch(r'round-\d+', args[0]) or args[1] not in sl.ROUND_KINDS \
            or not re.fullmatch(r'[a-z0-9][a-z0-9.-]*', args[2]):
        die('usage: round-start <round-k> <validate|test|audit> <target>')
    d = os.path.join(ex, 'rounds', args[0])
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f'{args[1]}__{args[2]}.running'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(f'{now()} | {actor}\n')
    log(ex, 'P6', actor, 'ROUND_START', f'{args[0]} {args[1]}__{args[2]} running')
    print(f'OK {args[0]} {args[1]}__{args[2]} running')


def cmd_score(ex, args, actor):
    kind, score = opt(args, '--kind'), opt(args, '--score')
    nums = {k: opt(args, f'--{k}', '') for k in ('high', 'medium', 'low', 'pass', 'total')}
    note = opt(args, '--note', '')
    usage = ('usage: score <pilot|round-k> <target> --kind validate|test|audit --score S '
             '[--high N --medium N --low N] [--pass P --total T] [--note X]')
    if len(args) != 2 or not re.fullmatch(r'pilot|round-\d+', args[0]) or kind not in sl.ROUND_KINDS \
            or not re.fullmatch(r'[a-z0-9][a-z0-9.-]*', args[1]):
        die(usage)
    try:
        s = float(score)
    except (TypeError, ValueError):
        die('--score must be a number')
    if not 0 <= s <= (10 if kind == 'audit' else 100):
        die('--score out of range (0-100; audit 0-10)')
    if any(v and not v.isdigit() for v in nums.values()):
        die('--high/--medium/--low/--pass/--total must be whole numbers')
    if nums['pass'] and nums['total'] and int(nums['pass']) > int(nums['total']):
        die('--pass cannot exceed --total')
    path = os.path.join(ex, 'state', 'scores.md')
    append(path, f'| {now()} | ' + ' | '.join(clean(c) for c in [
        args[0], args[1], kind, f'{s:g}', nums['high'], nums['medium'], nums['low'],
        nums['pass'], nums['total'], actor, note]) + ' |', template('SCORES.template.md'))
    log(ex, 'P6' if args[0] != 'pilot' else 'P3', actor, 'NOTE', f'score {args[0]} {kind} {args[1]} {s:g}')
    print(f'OK score {args[0]} {kind} {args[1]} {s:g}')


def cmd_render(ex, args, actor):
    print(render(ex, 'render') or 'OK rendered')


def render(ex, by):
    """Regenerate the dashboard; never fails the write that triggered it."""
    try:
        p = subprocess.run([sys.executable, os.path.join(HERE, 'render_state.py'), os.path.dirname(ex),
                            '--execution', os.path.basename(ex).removeprefix('execution-'), '--by', by],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if p.returncode:
            print('WARN dashboard not rendered:', (p.stdout + p.stderr).strip()[-200:], file=sys.stderr)
        return p.stdout.strip()
    except OSError as e:
        print('WARN dashboard not rendered:', e, file=sys.stderr)
        return ''


def cmd_event(ex, args, actor):
    if len(args) < 3:
        die('usage: event <PHASE> <CODE> <text>')
    log(ex, args[0], actor, args[1], ' '.join(args[2:]))
    print('OK event')


def cmd_lock(ex, args, actor, release):
    path = os.path.join(ex, '.run.lock')
    if release:
        if not os.path.isfile(path):
            die('no lock to release')
        info = open(path, encoding='utf-8').read().split()
        started = datetime.datetime.fromisoformat(info[2]) if len(info) > 2 else None
        age = (datetime.datetime.now() - started).total_seconds() / 3600 if started else 0
        if '--stale' in args and age < STALE_HOURS:
            die(f'lock is {age:.1f} h old (< {STALE_HOURS} h); not stale')
        os.remove(path)
        log(ex, '-', actor, 'UNLOCK', ('stale ' if '--stale' in args else '') + ' '.join(info))
        print('OK unlocked')
        return
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        die('execution locked by: ' + open(path, encoding='utf-8').read().strip()
            + f' (unlock, or unlock --stale after {STALE_HOURS} h)')
    with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'{os.getpid()} {socket.gethostname()} {now()}\n')
    log(ex, '-', actor, 'LOCK', f'pid {os.getpid()}')
    print('OK locked')


def next_id(ex, reg, prefix):
    ids = [int(m.group(1)) for i in sl.register(ex, reg)
           if (m := re.fullmatch(prefix + r'-(\d+)', i))]
    return f'{prefix}-{(max(ids) + 1 if ids else 1):03d}'


def reg_append(ex, reg, cells):
    path = os.path.join(ex, 'state', f'{reg}.md')
    with FileLock(path + '.id'):  # id allocation and write are one critical section
        if cells[0] is None:
            cells[0] = next_id(ex, reg, {'findings': 'F', 'deferred': 'D', 'decisions': 'DEC',
                                         'retro': 'R'}[reg])
        append(path, f'| {now()} | ' + ' | '.join(clean(c) for c in cells) + ' |',
               template(sl.REGISTERS[reg][0]))
    return cells[0]


def cmd_finding(ex, args, actor):
    if args and args[0] == 'add':
        sev, rnd, tgt, text = (opt(args, k) for k in ('--sev', '--round', '--target', '--text'))
        if sev not in ('HIGH', 'MEDIUM', 'LOW') or not (rnd and tgt and text):
            die('finding add needs --sev HIGH|MEDIUM|LOW --round --target --text')
        fid = reg_append(ex, 'findings', [None, 'OPEN', sev, rnd, tgt, actor, text])
        log(ex, 'P6', actor, 'FINDING', f'{fid} OPEN {sev} {tgt}')
        print(f'OK {fid}')
        return
    if len(args) < 2 or args[1] not in ('FIXED', 'WONTFIX', 'DEFERRED', 'REOPENED'):
        die('usage: finding <F-nnn> FIXED|WONTFIX|DEFERRED|REOPENED --round R [--note X]')
    fid, status = args[0], args[1]
    rnd, note = opt(args, '--round', ''), opt(args, '--note', '')
    hist = sl.register(ex, 'findings').get(fid)
    if not hist:
        die(f'{fid} unknown')
    first = hist[0]
    if status in ('WONTFIX', 'DEFERRED') and not note:
        die(f'{status} needs --note with the reason (it goes to the G3 decision list)')
    reg_append(ex, 'findings', [fid, status, first[3], rnd or first[4], first[5], actor,
                                note or first[7]])
    reopened = sum(1 for x in hist if x[2] == 'REOPENED') + (status == 'REOPENED')
    log(ex, 'P6', actor, 'FINDING', f'{fid} {status}')
    if reopened >= 2:
        print(f'ESCALATE: {fid} reopened {reopened} times; ask the user instead of another fix round')
    print(f'OK {fid} {status}')


def cmd_defer(ex, args, actor):
    if args and args[0] == 'add':
        owner, trig, text = (opt(args, k) for k in ('--owner', '--trigger', '--text'))
        if not (owner and trig and text):
            die('defer add needs --owner --trigger --text')
        did = reg_append(ex, 'deferred', [None, 'OPEN', owner, trig, actor, text])
        log(ex, '-', actor, 'DEFER', f'{did} {text}')
        print(f'OK {did}')
        return
    if len(args) < 2 or args[1] not in ('RESUMED', 'CLOSED'):
        die('usage: defer <D-nnn> RESUMED|CLOSED [--note X]')
    hist = sl.register(ex, 'deferred').get(args[0])
    if not hist:
        die(f'{args[0]} unknown')
    f = hist[0]
    reg_append(ex, 'deferred', [args[0], args[1], f[3], f[4], actor, opt(args, '--note', '') or f[6]])
    log(ex, '-', actor, 'DEFER', f'{args[0]} {args[1]}')
    print(f'OK {args[0]} {args[1]}')


def cmd_decide(ex, args, actor):
    gate, who, text, reason = (opt(args, k) for k in ('--gate', '--who', '--text', '--reason'))
    if gate not in GATES + ('none',) or who not in ('user', 'orchestrator') or not (text and reason):
        die('decide needs --gate G1|G2|G3|none --who user|orchestrator --text --reason')
    if who == 'user' and gate != 'none' and \
            not os.path.isfile(os.path.join(ex, 'state', 'gates', f'{gate}.md')):
        die(f'a user decision at {gate} needs the {gate} gate recorded first (verbatim words)')
    did = reg_append(ex, 'decisions', [None, gate, who, actor, text, reason])
    log(ex, '-', actor, 'DECISION', f'{did} {text}')
    print(f'OK {did}')


def cmd_source(ex, args, actor):
    read_on, official = opt(args, '--read-on'), opt(args, '--official')
    inj, used = opt(args, '--injection', 'no'), opt(args, '--used-by', '')
    if not args or not re.fullmatch(r'https?://\S+', args[0]):
        die('usage: source <url> --read-on YYYY-MM-DD --official yes|no [--injection yes|no] --used-by X')
    try:
        datetime.date.fromisoformat(read_on or '')
    except ValueError:
        die('--read-on must be YYYY-MM-DD')
    if official not in ('yes', 'no') or inj not in ('yes', 'no'):
        die('--official and --injection take yes|no')
    reg_append(ex, 'sources', [args[0], read_on, official, inj, actor, used])
    log(ex, '-', actor, 'SOURCE', args[0] + (' INJECTION SUSPECTED' if inj == 'yes' else ''))
    print('OK source')


def cmd_metric(ex, args, actor):
    tokens, minutes, note = opt(args, '--tokens'), opt(args, '--minutes', ''), opt(args, '--note', '')
    if len(args) < 2 or args[1] not in ('estimate', 'actual') or not (tokens or '').isdigit():
        die('usage: metric <scope> estimate|actual --tokens N [--minutes M] [--note X]')
    if minutes and not minutes.replace('.', '', 1).isdigit():
        die('--minutes must be a number')
    reg_append(ex, 'metrics', [args[0], args[1], tokens, minutes, actor, note])
    log(ex, '-', actor, 'METRIC', f'{args[0]} {args[1]} {tokens} tokens')
    slug = os.path.dirname(ex)
    _, budget = sl.brief_budget(slug)
    if budget and args[1] == 'actual':
        spent = sum(int(r[3]) for r in sl.rows(os.path.join(ex, 'state', 'metrics.md'))
                    if r[2] == 'actual' and r[3].isdigit())
        if spent > budget:
            log(ex, '-', actor, 'BUDGET', f'actual {spent} > token_budget {budget}')
            print(f'BUDGET EXCEEDED: {spent} > {budget}; stop and ask the user before the next step')
    print(f'OK metric {args[0]} {args[1]}')


def cmd_retro(ex, args, actor):
    kind, target, text = opt(args, '--kind'), opt(args, '--target', '-'), opt(args, '--text')
    if not args or args[0] != 'add' or kind not in ('brief', 'known-failure', 'lesson') or not text:
        die('usage: retro add --kind brief|known-failure|lesson --target T --text X')
    rid = reg_append(ex, 'retro', [None, kind, target, actor, text])
    log(ex, '-', actor, 'RETRO', f'{rid} {kind}: {text}')
    print(f'OK {rid}')


def blob_hash(path):
    head = subprocess.run(['git', 'rev-parse', f'HEAD:{path}'], capture_output=True, text=True)
    # git hash-object applies the same filters (autocrlf) as the HEAD blob, so equal means unchanged
    obj = subprocess.run(['git', 'hash-object', path], capture_output=True, text=True)
    now = obj.stdout.strip()[:12] if os.path.isfile(path) and obj.returncode == 0 else 'deleted'
    return (head.stdout.strip()[:12] if head.returncode == 0 else 'new'), now


def cmd_touch(ex, args, actor):
    if not args:
        die('usage: touch <repo-path> [--note X]  (run from the repo root)')
    note = opt(args, '--note', '')
    path = args[0].replace(os.sep, '/')
    if not (os.path.exists(path) or blob_hash(path)[0] != 'new'):
        die(f'{path} neither exists nor is tracked: run from the repo root')
    if not path.startswith(sl.SHARED_FILES) and not path.startswith('packages/'):
        die(f'{path} is not a shared file; only {sl.SHARED_FILES} or another package are recorded')
    head, now_h = blob_hash(path)
    reg_append(ex, 'shared-touch', [path, head, now_h, actor, note])
    log(ex, '-', actor, 'TOUCH', f'{path} {head} -> {now_h}')
    print(f'OK touch {path}')


def cmd_shared_lock(ex, args, actor, release):
    path = sl.SHARED_LOCK
    me = os.path.basename(os.path.dirname(os.path.abspath(ex)))
    if release:
        if not os.path.isfile(path):
            die('no shared lock to release')
        info = open(path, encoding='utf-8').read().split()
        if info and info[0] != me and '--stale' not in args:
            die(f'shared lock belongs to {info[0]}, not {me}')
        started = datetime.datetime.fromisoformat(info[3]) if len(info) > 3 else None
        age = (datetime.datetime.now() - started).total_seconds() / 3600 if started else 0
        if '--stale' in args and age < STALE_HOURS:
            die(f'shared lock is {age:.1f} h old (< {STALE_HOURS} h); not stale')
        os.remove(path)
        log(ex, '-', actor, 'SHARED_UNLOCK', ('stale ' if '--stale' in args else '') + ' '.join(info))
        print('OK shared lock released')
        return
    if not os.path.isdir('workspace'):
        die('run from the repo root (workspace/ not found)')
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        die('shared files locked by: ' + open(path, encoding='utf-8').read().strip())
    with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'{me} {os.getpid()} {socket.gethostname()} {now()}\n')
    log(ex, '-', actor, 'SHARED_LOCK', me)
    print('OK shared lock taken')


def main():
    args = sys.argv[1:]
    actor = opt(args, '--actor', 'orchestrator')
    n = opt(args, '--execution')
    no_render = '--no-render' in args
    if no_render:
        args.remove('--no-render')
    if len(args) < 2:
        print(__doc__)
        sys.exit(2)
    slug, cmd, rest = args[0], args[1], args[2:]
    if cmd == 'init':
        return cmd_init(slug, rest, actor)
    ex = resolve(slug, n)
    if cmd == 'render':
        return cmd_render(ex, rest, actor)
    handlers = {'phase': cmd_phase, 'gate': cmd_gate, 'unit': cmd_unit, 'event': cmd_event,
                'finding': cmd_finding, 'defer': cmd_defer, 'decide': cmd_decide,
                'source': cmd_source, 'metric': cmd_metric, 'retro': cmd_retro,
                'touch': cmd_touch, 'round-start': cmd_round_start, 'score': cmd_score}
    if cmd in handlers:
        handlers[cmd](ex, rest, actor)
    elif cmd in ('lock', 'unlock'):
        cmd_lock(ex, rest, actor, cmd == 'unlock')
    elif cmd in ('shared-lock', 'shared-unlock'):
        cmd_shared_lock(ex, rest, actor, cmd == 'shared-unlock')
    else:
        die(f'unknown command {cmd}')
    if not no_render:  # refused writes exit in die() before this line, so only real writes render
        render(ex, 'state_event')


if __name__ == '__main__':
    main()
