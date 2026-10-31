# P8 Mechanical close (no AI judgement)

Back to [SKILL.md](../../SKILL.md).

0. `state_event.py ... shared-lock`, `git fetch`, `git status` ([shared files](../policy/shared-files.md)); foreign changes in shared files -> stop and show them.
1. `scripts/verify_skill.py` on every new skill; `scripts/verify_package.py` on the package.
2. `scripts/snapshot_env.py --write workspace/<slug> --phase P8` and `scripts/preflight_apm.py --slug <slug> --log workspace/<slug>`; on BLOCK stop and show it (never `--force` on your own). Then `apm install --target claude` (12-40 min on Windows with remote dependencies; run it in the background), and right after it, always, `<skill>/scripts/after_install.py --package <pkg> --log workspace/<slug>`: it runs the two repo-root fixups (the apm.yml post-install hooks did not fire in a real install) and fails if a rule lost its frontmatter, a link still points into `apm_modules/`, or files of another package changed. If it reports deleted committed files or a lock that lost other packages' entries: restore the files from HEAD and run `scripts/merge_lock.py --package <pkg> --apply`, then `after_install.py` again.
3. Compare `packages/` with `.claude/` for the new artifacts (identical copies).
4. `scripts/check_counts.py`; fix every documented count (then `touch <file>` for each one changed) (CLAUDE.md, README.md, docs/visao-geral.md, docs/capacidades/*, docs/manual/README.md) from the real numbers.
5. `git status` for stray or foreign changes; BOM/CRLF check; no `.github/`.
6. A failed install is `event P8 INCIDENT` with the command and the first error line, plus the recovery step from [known failures](../known-failures.md); never commit without a regenerated lock.
7. Ask the user for a second `apm install --target claude`, then `python scripts/restore-rule-metadata.py`, `python scripts/fix-cross-package-links.py` and `git diff --exit-code -- .claude` to prove no drift (there is no CI to do it).

**Done when:** every command exits 0 and counts match `ls`. **Gate:** next is G3.
