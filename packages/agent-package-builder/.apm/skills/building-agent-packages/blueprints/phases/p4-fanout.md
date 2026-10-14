# P4 Fan-out

Back to [SKILL.md](../../SKILL.md).

Batches of at most 4 units. Per batch:
1. Research: one researcher per unit in a single message (flat, depth 1; no investigators).
2. `ls` every research file; re-send once for missing/truncated ones.
3. Author: one author per unit in a single message, writing to `packages/<package>/.apm/skills/`.
4. `scripts/verify_skill.py` per unit; one fix brief per failure, then recheck.
5. `scripts/normalize_tags.py <package> --write`; update PIPELINE_STATE (RESEARCHED -> AUTHORED -> VERIFIED).
6. `apm install --target claude` once per batch is optional; mandatory in P8.

In `from-research` mode skip step 1 for COMPLETE research files.

**Done when:** all units VERIFIED. **Gate:** none.
