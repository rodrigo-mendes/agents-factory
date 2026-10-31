#!/usr/bin/env python3
"""Re-render the PIPELINE_STATE.md dashboard every N seconds while a run is active (stdlib only).

Catches what changes outside state_event.py: a reviewer's report landing in rounds/ (its `.running`
marker disappears), lock ages, the watcher heartbeat itself. state_event.py already re-renders after
every write; this covers the gaps between writes.

Usage: watch_state.py <slug_dir> [--execution N] [--interval 300] [--once]
Started in P0 right after `state_event.py <slug> lock`, in the background; restarted after a resume.
Writes only <execution>/.watch.heartbeat ("<iso time> <interval>") and, via render_state.py, the
dashboard. Exits 0 by itself when the execution has no .run.lock (unlocked at P9 or never locked)
or when P9 is done, so no orphan process is left behind.
"""
import datetime
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_lib as sl  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def active(ex):
    if not os.path.isfile(os.path.join(ex, '.run.lock')):
        return False, 'no .run.lock'
    if sl.load(ex)['phases'].get('P9', {}).get('status') == 'done':
        return False, 'P9 done'
    return True, ''


def tick(ex, interval):
    with open(os.path.join(ex, '.watch.heartbeat'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'{datetime.datetime.now().replace(microsecond=0).isoformat()} {interval}\n')
    p = subprocess.run([sys.executable, os.path.join(HERE, 'render_state.py'), os.path.dirname(ex),
                        '--execution', os.path.basename(ex).removeprefix('execution-'), '--by', 'watch'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode:
        print('WARN render failed:', (p.stdout + p.stderr).strip()[-200:], flush=True)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(2)
    interval = int(a[a.index('--interval') + 1]) if '--interval' in a else 300
    n = a[a.index('--execution') + 1] if '--execution' in a else None
    ex = sl.resolve(a[0], n)
    if not ex:
        sys.exit(f'no execution folder under {a[0]}')
    print(f'watching {ex} every {interval}s (stops when the run is unlocked or P9 is done)', flush=True)
    while True:
        ok, why = active(ex)
        if not ok:
            print(f'stopped: {why}', flush=True)
            hb = os.path.join(ex, '.watch.heartbeat')
            if os.path.isfile(hb):
                os.remove(hb)
            return
        tick(ex, interval)
        if '--once' in a:
            return
        time.sleep(interval)


if __name__ == '__main__':
    main()
