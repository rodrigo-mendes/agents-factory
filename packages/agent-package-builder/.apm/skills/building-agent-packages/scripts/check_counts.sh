#!/usr/bin/env bash
# Print real artifact counts (never trust documented numbers). Read-only.
# Usage: check_counts.sh [repo_root]   then compare against CLAUDE.md / README.md / docs.
set -euo pipefail
cd "${1:-.}"
echo "skills   (.claude/skills):   $(ls -d .claude/skills/*/ 2>/dev/null | wc -l | tr -d ' ')"
echo "agents   (.claude/agents):   $(ls .claude/agents/*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "rules    (.claude/rules):    $(ls .claude/rules/*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "packages (packages/*/apm.yml): $(ls packages/*/apm.yml 2>/dev/null | wc -l | tr -d ' ')"
echo "--- documented counts to compare (grep) ---"
grep -rnE '\b[0-9]+ (skills|agents|rules|packages|commands|subagents)\b' CLAUDE.md README.md docs/visao-geral.md 2>/dev/null | head -20 || true
