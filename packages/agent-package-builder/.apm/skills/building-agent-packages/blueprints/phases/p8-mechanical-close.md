# P8 Mechanical close (no AI judgement)

Back to [SKILL.md](../../SKILL.md).

1. `scripts/verify_skill.py` on every new skill; `scripts/verify_package.py` on the package.
2. `apm install --target claude`, then `python3 scripts/restore-rule-metadata.py` and `python3 scripts/fix-cross-package-links.py`.
3. Compare `packages/` with `.claude/` for the new artifacts (identical copies).
4. `scripts/check_counts.sh`; fix every documented count (CLAUDE.md, README.md, docs/visao-geral.md, docs/capacidades/*, docs/manual/README.md) from the real numbers.
5. `git status` for stray or foreign changes; BOM/CRLF check; no `.github/`.
6. Ask for the second `apm install --frozen` + `git diff --exit-code` on `.claude/` to prove no drift.

**Done when:** every command exits 0 and counts match `ls`. **Gate:** next is G3.
