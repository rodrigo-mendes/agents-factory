#!/usr/bin/env python3
"""Run right after EVERY `apm install` (stdlib only; repo root). The apm.yml post-install hooks did
not fire in a real install, so this applies the two repo-root fixups explicitly and then proves the
damage is gone. Usage: after_install.py [--package <pkg>[,<pkg>]] [--log <slug_dir>] [--execution N]
Steps: scripts/restore-rule-metadata.py, scripts/fix-cross-package-links.py, then checks:
  - no .claude/rules/*.md without name:/description: frontmatter
  - no markdown link into apm_modules/ under .claude/
  - every .claude change left (ignoring CRLF) is owned by --package; others are listed by owner
Exit 1 when a fixup fails or residue remains."""
import glob
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_lib as sl  # noqa: E402

FIXUPS = ('scripts/restore-rule-metadata.py', 'scripts/fix-cross-package-links.py')


def main():
    args = sys.argv[1:]
    mine = set((args[args.index('--package') + 1] if '--package' in args else '').split(',')) - {''}
    problems, notes = [], []
    for f in FIXUPS:
        if not os.path.isfile(f):
            problems.append(f'{f} not found: run from the repo root')
            continue
        r = subprocess.run([sys.executable, f], capture_output=True, text=True, encoding='utf-8',
                           errors='replace')
        last = (r.stdout.strip().splitlines() or ['(no output)'])[-1]
        print(f'{f}: {last}')
        if r.returncode:
            problems.append(f'{f} exited {r.returncode}: {r.stderr.strip()[:200]}')
    for rule in glob.glob('.claude/rules/*.md'):
        head = open(rule, encoding='utf-8').read(600)
        if not re.match(r'---\r?\n', head) or not re.search(r'^name:', head, re.M) \
                or not re.search(r'^description:', head, re.M):
            problems.append(f'{rule} lacks name:/description: frontmatter after the fixup')
    for md in glob.glob('.claude/**/*.md', recursive=True):
        if 'apm_modules/' in open(md, encoding='utf-8', errors='replace').read():
            if re.search(r'\]\([^)]*apm_modules/', open(md, encoding='utf-8', errors='replace').read()):
                problems.append(f'{md} still links into apm_modules/')
    owners = sl.lock_owners()
    deleted = subprocess.run(['git', 'ls-files', '--deleted', '--', '.claude'],
                             capture_output=True, text=True).stdout.split()
    if deleted:
        problems.append(f'the install deleted {len(deleted)} committed .claude files (e.g. {deleted[0]}); '
                        'a remote dependency failed to resolve ("recovery incomplete"). Restore them with '
                        '`git ls-files --deleted -- .claude` | `git restore --source=HEAD` and do not commit the lock as is')
    head = subprocess.run(['git', 'show', 'HEAD:apm.lock.yaml'], capture_output=True, text=True,
                          encoding='utf-8', errors='replace').stdout
    head_owners, cur = {}, None
    for line in head.splitlines():
        m = re.match(r'^- repo_url:\s*(\S+)', line)
        if m:
            cur = m.group(1).replace('_local/', '')
        elif cur and re.match(r'^  - \.claude/', line):
            head_owners.setdefault(cur, 0)
            head_owners[cur] += 1
    now_owners = {}
    for o in owners.values():
        now_owners[o] = now_owners.get(o, 0) + 1
    for pkg, n in sorted(head_owners.items()):
        if pkg not in mine and now_owners.get(pkg, 0) < n:
            problems.append(f'apm.lock.yaml lost deployed entries of {pkg} ({n} -> {now_owners.get(pkg, 0)}): '
                            'keep the HEAD lock and replace only your package blocks (dependencies entry and '
                            'its deployments: entries)')
    r = subprocess.run(['git', 'diff', '--ignore-cr-at-eol', '--name-only', '--diff-filter=AM', '--', '.claude'],
                       capture_output=True, text=True)
    foreign = {}
    for f in r.stdout.split():
        o = sl.owner_of(f, owners)
        if o not in mine:
            foreign.setdefault(o, []).append(f)
    for o, fs in sorted(foreign.items()):
        problems.append(f'{len(fs)} .claude files of {o} changed by this install (e.g. {fs[0]}): '
                        'not your package; show the diff to the user, do not commit them with yours')
    summary = f'{len(problems)} problem(s) after install'
    print('PROBLEMS:' if problems else 'OK, fixups applied and no residue', f'({summary})')
    for p in problems:
        print('  -', p)
    if '--log' in args:
        import state_event as se
        ex = se.resolve(args[args.index('--log') + 1],
                        args[args.index('--execution') + 1] if '--execution' in args else None)
        se.log(ex, 'P8', 'after_install', 'INCIDENT' if problems else 'NOTE', summary)
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
