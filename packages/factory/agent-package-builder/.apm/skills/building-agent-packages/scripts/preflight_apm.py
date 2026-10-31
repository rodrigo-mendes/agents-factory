#!/usr/bin/env python3
"""Read-only checks before `apm install` (stdlib only). Run from the repo root in P5 (rehearsal)
and P8. It never runs apm and never fixes anything: it names the problem and the recovery step.
Usage: preflight_apm.py [--slug <slug>] [--package <pkg>[,<pkg>]] [--log <slug_dir>] [--execution N]
  --slug     your own run, so its .run.lock is not reported as a concurrent run
  --package  the packages your run edits (default: the slug); changed .claude files are grouped by
             owning package (apm.lock.yaml, then packages/) and only files owned by others block
  --log   append a PREFLIGHT event with the summary to that execution
Exit 1 when a BLOCK is found (concurrent run, uncommitted .claude/lock changes, broken root apm.yml)."""
import glob
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_lib as sl  # noqa: E402

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
    own_pkgs = (args[args.index('--package') + 1] if '--package' in args else (own or '')).split(',')
    block, warn, info = [], [], []

    for lock in glob.glob('workspace/*/execution-*/.run.lock') + glob.glob('workspace/.shared.lock'):
        slug = lock.replace(os.sep, '/').split('/')[1]
        if slug == '.shared.lock':  # its first word is the slug that holds it
            slug = (open(lock, encoding='utf-8').read().split() or ['?'])[0]
        if slug != own:
            block.append(f'another run holds {lock} ({open(lock, encoding="utf-8").read().strip()}): '
                         'wait for it, or ask the user; never install over a live run')

    # --ignore-cr-at-eol: a CRLF-only difference is reported below, not as a change of content
    dirty = git('diff', '--ignore-cr-at-eol', '--name-only', '--', '.claude')
    untracked = git('ls-files', '--others', '--exclude-standard', '--', '.claude')
    mine = set(own_pkgs)
    by_owner = {}
    owners = sl.lock_owners()
    for f in dirty + untracked:
        by_owner.setdefault(sl.owner_of(f, owners), []).append(f)
    unmanaged = [f for f in glob.glob('.claude/skills/**/*', recursive=True)
                 if os.path.isfile(f) and '__pycache__' not in f
                 and f.replace(os.sep, '/') not in owners and sl.owner_of(f, owners) in mine]
    if unmanaged:
        skills = sorted({f.replace(os.sep, '/').split('/')[2] for f in unmanaged})
        block.append(f'{len(unmanaged)} files of your package exist in .claude/ but are not in apm.lock.yaml '
                     f'(e.g. {unmanaged[0]}): apm refuses to update such "unmanaged" files once they change. '
                     f'Delete .claude/skills/{{{",".join(skills)}}} (generated; packages/ and git have them) and reinstall')
    for owner, files in sorted(by_owner.items()):
        line = (f'{len(files)} changed/new .claude files owned by {owner} (e.g. {files[0]})')
        if owner in mine:
            warn.append(line + ': yours; the install will overwrite them with packages/ (expected)')
        else:
            block.append(line + ': not yours; find who changed them (another run, a hand edit) '
                         'before installing; save them with `git stash push -- <files>` if needed')
    if git('diff', '--ignore-cr-at-eol', '--name-only', '--', 'apm.lock.yaml'):
        (warn if mine else block).append('apm.lock.yaml has uncommitted changes: expected only after '
                                         "your own install; otherwise another run's install is pending")

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
    for src in glob.glob('packages/**/.apm/skills/*/**/*', recursive=True):
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
