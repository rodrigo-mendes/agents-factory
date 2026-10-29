#!/usr/bin/env python3
"""Snapshot of the build environment (stdlib only). Changes nothing on the system: it only reads
versions and settings; the sandbox probe runs `git init` in a temp folder it deletes afterwards.
Usage: snapshot_env.py [--write <slug_dir> --phase P0|P5|P8] [--execution N]
Without --write it prints the Markdown section; with --write it appends it to
<execution>/state/environment.md and logs an ENV event. Run it in P0 and again before P8."""
import datetime
import locale
import os
import platform
import shutil
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
TOOLS = (('apm', '--version'), ('git', '--version'), ('gh', '--version'), ('jq', '--version'),
         ('terraform', 'version'), ('mvn', '-v'), ('java', '-version'), ('docker', '--version'),
         ('node', '--version'))
HEADER = """# Environment snapshots

Written only by `scripts/snapshot_env.py --write`. One section per snapshot (P0, and again before
P8). Compare the two: a difference explains a failure before it becomes an incident.
"""


def run(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=cwd,
                           encoding='utf-8', errors='replace')
        out = (r.stdout or r.stderr).strip().splitlines()
        return r.returncode, out[0][:100] if out else ''
    except (OSError, subprocess.TimeoutExpired) as e:
        return -1, type(e).__name__


def git_init_allowed():
    d = tempfile.mkdtemp(prefix='apb-probe-')
    try:
        rc, _ = run(['git', 'init', '-q', d])
        return 'yes' if rc == 0 and os.path.isdir(os.path.join(d, '.git')) else 'no'
    finally:
        shutil.rmtree(d, ignore_errors=True)


def snapshot(phase):
    rows = [('platform', f'{platform.system()} {platform.release()}'),
            ('python', sys.version.split()[0]),
            ('stdout encoding', sys.stdout.encoding),
            ('preferred encoding', locale.getpreferredencoding(False)),
            ('PYTHONIOENCODING', os.environ.get('PYTHONIOENCODING', '(unset)'))]
    for tool, flag in TOOLS:
        path = shutil.which(tool)
        rows.append((tool, run([path, flag])[1] or 'present' if path else 'NOT FOUND'))
    rows.append(('git core.autocrlf', run(['git', 'config', '--get', 'core.autocrlf'])[1] or '(unset)'))
    rows.append(('.gitattributes', 'present' if os.path.isfile('.gitattributes') else 'absent'))
    rows.append(('git init in a temp folder (sandbox)', git_init_allowed()))
    ts = datetime.datetime.now().replace(microsecond=0).isoformat()
    body = '\n'.join(f'| {k} | {v.replace("|", "/")} |' for k, v in rows)
    return f'\n## {phase} — {ts}\n\n| Item | Value |\n|---|---|\n{body}\n', rows


def main():
    args = sys.argv[1:]
    phase = args[args.index('--phase') + 1] if '--phase' in args else 'manual'
    text, rows = snapshot(phase)
    if '--write' not in args:
        print(text)
        return
    import state_event as se
    slug = args[args.index('--write') + 1]
    ex = se.resolve(slug, args[args.index('--execution') + 1] if '--execution' in args else None)
    path = os.path.join(ex, 'state', 'environment.md')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with se.FileLock(path):
        new = not os.path.isfile(path)
        with open(path, 'a', encoding='utf-8', newline='\n') as f:
            f.write((HEADER if new else '') + text)
    missing = [k for k, v in rows if v == 'NOT FOUND']
    se.log(ex, phase, 'snapshot_env', 'ENV',
           f'snapshot written; missing tools: {", ".join(missing) or "none"}; '
           f'git init in sandbox: {rows[-1][1]}')
    print(f'OK {path}')


if __name__ == '__main__':
    main()
