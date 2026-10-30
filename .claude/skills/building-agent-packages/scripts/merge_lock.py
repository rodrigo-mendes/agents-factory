#!/usr/bin/env python3
"""Rebuild apm.lock.yaml as HEAD's lock + ONLY your packages' entries from the lock the last install
wrote (stdlib only; repo root). Use it when the install also rewrote other packages' entries, e.g.
a remote dependency failed to resolve and its deployed files were "cleaned" (after_install.py
reports "apm.lock.yaml lost deployed entries of ...").
Usage: merge_lock.py --package <pkg>[,<pkg>] [--apply]     dry run by default
For each package: its `- repo_url: _local/<pkg>` block under dependencies:, and every
`deployments:` entry whose owners list contains `./packages/<pkg>`, come from the current file;
everything else comes from `git show HEAD:apm.lock.yaml`. Then run after_install.py again."""
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def deps_blocks(t):
    """Text before dependencies' first block, and the list of (repo_url, block text) in file order.
    A repo_url may appear more than once (same package resolved at different depths)."""
    start = t.index('\ndependencies:\n') + len('\ndependencies:\n')
    end = t.index('\ndeployments:\n') + 1
    parts = ['- repo_url:' + p for p in t[start:end].split('- repo_url:')[1:]]
    return t[:start], [(p.split('\n', 1)[0].split(':', 1)[1].strip(), p) for p in parts]


def deployments(t):
    i = t.index('\ndeployments:\n') + len('\ndeployments:\n')
    return ['- kind:' + e for e in t[i:].split('- kind:')[1:]]


def value(e):
    return next((l[9:].strip() for l in e.splitlines() if l.startswith('  value: ')), '')


def main():
    args = sys.argv[1:]
    if '--package' not in args:
        print(__doc__)
        sys.exit(2)
    pkgs = args[args.index('--package') + 1].split(',')
    head = subprocess.run(['git', 'show', 'HEAD:apm.lock.yaml'], capture_output=True, text=True,
                          encoding='utf-8').stdout
    cur = open('apm.lock.yaml', encoding='utf-8').read()
    pre, hblocks = deps_blocks(head)
    _, cblocks = deps_blocks(cur)
    keys = {f'_local/{p}' for p in pkgs}
    new = [b for k, b in cblocks if k in keys]
    if {k for k, _ in cblocks} & keys != keys:
        print(f'REFUSED: {sorted(keys - {k for k, _ in cblocks})} not in the current lock (was the install run?)')
        sys.exit(1)
    blocks, placed = [], False
    for k, b in hblocks:  # your blocks take the place of the first HEAD block of your packages
        if k in keys:
            if not placed:
                blocks += new
                placed = True
            continue
        blocks.append(b)
    if not placed:
        blocks += new
    owned = lambda e: any(f'  - ./packages/{p}\n' in e for p in pkgs)
    keep = [e for e in deployments(head) if not owned(e)]
    mine = [e for e in deployments(cur) if owned(e)]
    ents = sorted(keep + mine, key=value)
    out = pre + ''.join(blocks) + 'deployments:\n' + \
        ''.join(e if e.endswith('\n') else e + '\n' for e in ents)
    print(f'{len(pkgs)} package(s): {sum(1 for e in deployments(head) if owned(e))} -> {len(mine)} '
          f'deployment entries; {len(keep)} other entries kept from HEAD')
    if '--apply' in args:
        open('apm.lock.yaml', 'w', encoding='utf-8', newline='\n').write(out)
        print('OK apm.lock.yaml rewritten; run after_install.py again')
    else:
        print('(dry run; add --apply)')


if __name__ == '__main__':
    main()
