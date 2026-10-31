#!/usr/bin/env python3
"""Normalize uncertainty tags to plain parentheses: **(unverified)** -> (unverified),
[unverified] -> (unverified), same for (medium confidence). Idempotent.
Usage: normalize_tags.py <dir> [--write]   (dry run unless --write)"""
import os
import re
import sys

root = sys.argv[1]
write = '--write' in sys.argv
pats = [(re.compile(r'\*\*\((unverified|medium confidence)\)\*\*'), r'(\1)'),
        (re.compile(r'\[(unverified|medium confidence)\]'), r'(\1)')]
changed = 0
for r, _, fs in os.walk(root):
    for f in fs:
        if not f.endswith('.md'):
            continue
        p = os.path.join(r, f)
        t = open(p, encoding='utf-8').read()
        n = t
        for rx, rep in pats:
            n = rx.sub(rep, n)
        if n != t:
            changed += 1
            print(('rewrote ' if write else 'would rewrite ') + p)
            if write:
                open(p, 'w', encoding='utf-8').write(n)
print(f'{changed} file(s) {"changed" if write else "to change"}')
