# P7 Fact sweep

Back to [SKILL.md](../../SKILL.md).

Runs whenever a row of `_family_facts` changed (in P3, P6 or by user decision).
1. `grep -rn` the old value across `packages/<package>/` and `workspace/<slug>/`.
2. One fix brief per affected skill listing exact lines.
3. Re-run `scripts/verify_skill.py` on each; log the sweep.

**Done when:** grep for the old value returns only intentional mentions (e.g. a migration baseline).
