#!/usr/bin/env python3
"""Print real artifact counts (never trust documented numbers). Read-only.
Usage: check_counts.py [repo_root]   then compare against CLAUDE.md / README.md / docs.
Prints the real counts from .claude/ and packages/, then every documented count line in the
project docs (English and Portuguese wording) so a mismatch is visible at a glance."""
import re
import sys
from pathlib import Path

DOCS = ['CLAUDE.md', 'README.md', 'docs/visao-geral.md', 'docs/README.md',
        'docs/capacidades/README.md', 'docs/capacidades/skills.md', 'docs/manual/README.md']
COUNT = re.compile(r'\b[0-9]+ (skills|agents|subagents|subagentes|rules|regras|packages|pacotes'
                   r'|commands|comandos)\b', re.IGNORECASE)
MAX_LINES = 60

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
skills = [d for d in (root / '.claude/skills').glob('*/') if d.is_dir()]
commands = sum(1 for d in skills if (d / 'SKILL.md').is_file()
               and 'disable-model-invocation: true' in (d / 'SKILL.md').read_text(encoding='utf-8'))
print(f'skills   (.claude/skills):   {len(skills)}  ({commands} commands, {len(skills) - commands} knowledge)')
print(f'agents   (.claude/agents):   {len(list((root / ".claude/agents").glob("*.md")))}')
print(f'rules    (.claude/rules):    {len(list((root / ".claude/rules").glob("*.md")))}')
print(f'packages (packages/*/apm.yml): {len(list((root / "packages").glob("*/apm.yml")))}')
print('--- documented counts to compare ---')
shown = 0
for rel in DOCS:
    path = root / rel
    if not path.is_file():
        continue
    for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if COUNT.search(line) and shown < MAX_LINES:
            print(f'{rel}:{n}:{line.strip()[:160]}')
            shown += 1
