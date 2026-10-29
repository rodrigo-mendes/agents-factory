#!/usr/bin/env python3
"""Read-only checks before `apm install` (stdlib only). Run from the repo root in P5 (rehearsal)
and P8. It never runs apm and never fixes anything: it names the problem and the recovery step.
Usage: preflight_apm.py [--slug <slug>] [--log <slug_dir>] [--execution N]
  --slug  your own run, so its .run.lock is not reported as a concurrent run
  --log   append a PREFLIGHT event with the summary to that execution
Exit 1 when a BLOCK is found (concurrent run, uncommitted .claude/lock changes, broken root apm.yml)."""
import glob
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
DEP = re.compile(r'^\s*-\s*(path|git):\s*(\S+)', re.M)


def git(*a):
    r = subprocess.run(['git', *a], capture_output=True, text=True, encoding='utf-8', errors='replace')
    return [l for l in r.stdout.splitlines() if l.strip()]


def deps(apm_file):
    text = open(apm_file, encoding='utf-8').read()
    text = '\n'.join(l for l in text.splitlines() if not l.lstrip().startswith('#'))
    return DEP.findall(text)


def main():
    args = sys.argv[1:]
    own = args[args.index('--slug') + 1] if '--slug' in args else None
    block, warn, info = [], [], []

    for lock in glob.glob('workspace/*/execution-*/.run.lock') + glob.glob('workspace/.shared.lock'):
        slug = lock.replace(os.sep, '/').split('/')[1]
        if slug == '.shared.lock':  # its first word is the slug that holds it
            slug = (open(lock, encoding='utf-8').read().split() or ['?'])[0]
        if slug != own:
            block.append(f'another run holds {lock} ({open(lock, encoding="utf-8").read().strip()}): '
                         'wait for it, or ask the user; never install over a live run')

    dirty = git('diff', '--name-only', '--', '.claude', 'apm.lock.yaml')
    untracked = git('ls-files', '--others', '--exclude-standard', '--', '.claude')
    if dirty or untracked:
        block.append(f'{len(dirty)} modified + {len(untracked)} untracked files in .claude/ or '
                     f'apm.lock.yaml (e.g. {(dirty + untracked)[0]}): identify the owner; save yours '
                     'with `git stash push -- .claude apm.lock.yaml` before installing')

    if not os.path.isfile('apm.yml'):
        block.append('no apm.yml in the current folder: run from the repo root')
    else:
        root = deps('apm.yml')
        if git('diff', '--name-only', '--', 'apm.yml'):
            warn.append('apm.yml has uncommitted changes (`git diff apm.yml`): confirm every added '
                        'package belongs to this run before installing')
        listed = {os.path.normpath(v) for k, v in root if k == 'path'}
        for k, v in root:
            if k == 'git':
                warn.append(f'remote dependency {v}: install needs network; a hang here is not your package')
            elif not os.path.isfile(os.path.join(v, 'apm.yml')):
                block.append(f'root apm.yml lists {v}, which has no apm.yml')
        for v in sorted(listed):
            sub = os.path.join(v, 'apm.yml')
            if not os.path.isfile(sub):
                continue
            for k, d in deps(sub):
                if k == 'path':
                    t = os.path.normpath(os.path.join(v, d))
                    if t in listed:
                        block.append(f'{t} is listed in the root apm.yml and also reached through {v}: '
                                     'remove the direct entry (audit fails with "ambiguous resolved_by")')

    if git('config', '--get', 'core.autocrlf') == ['true'] and not os.path.isfile('.gitattributes'):
        warn.append('core.autocrlf=true and no .gitattributes: APM may see CRLF-only copies as user-edited')

    crlf, drift = [], 0
    for src in glob.glob('packages/*/.apm/skills/*/**/*', recursive=True):
        if not os.path.isfile(src):
            continue
        rel = src.replace(os.sep, '/').split('/.apm/', 1)[1]
        dst = '.claude/' + rel
        if not os.path.isfile(dst):
            continue
        a, b = open(src, 'rb').read(), open(dst, 'rb').read()
        if a != b:
            if a.replace(b'\r\n', b'\n') == b.replace(b'\r\n', b'\n'):
                crlf.append(dst)
            else:
                drift += 1
    if crlf:
        warn.append(f'{len(crlf)} deployed files differ from the source only by CRLF (e.g. {crlf[0]}): '
                    'APM refuses them as "modified since deployment"; restore them from git first')
    if drift:
        info.append(f'{drift} deployed skill files differ from packages/ (expected for packages edited '
                    'in this run; anything else was changed by hand or by another run)')

    for label, items in (('BLOCK', block), ('WARN', warn), ('INFO', info)):
        for i in items:
            print(f'{label}: {i}')
    summary = f'{len(block)} block, {len(warn)} warn, {len(info)} info'
    print('OK, nothing blocks apm install' if not block else 'BLOCKED: do not run apm install yet',
          f'({summary}). Recovery steps: blueprints/known-failures.md')
    if '--log' in args:
        import state_event as se
        slug = args[args.index('--log') + 1]
        ex = se.resolve(slug, args[args.index('--execution') + 1] if '--execution' in args else None)
        se.log(ex, 'P8', 'preflight_apm', 'PREFLIGHT', summary + ('; ' + block[0] if block else ''))
    sys.exit(1 if block else 0)


if __name__ == '__main__':
    main()
