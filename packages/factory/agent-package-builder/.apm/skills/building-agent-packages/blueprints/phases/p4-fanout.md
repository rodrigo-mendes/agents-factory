# P4 Fan-out

Back to [SKILL.md](../../SKILL.md).

Batches of at most 4 units. Every brief is saved to `execution-<N>/briefs/<phase>-<unit>-<role>.md` before it is sent, and includes the `brief` rows of the retro table (the dashboard section "Lessons for the next briefs"). Per batch:
1. Research: one researcher per unit in a single message (flat, depth 1; no investigators).
2. `ls` every research file; re-send once for missing/truncated ones.
3. Author: one author per unit in a single message, writing to `packages/<package>/.apm/skills/`.
4. `scripts/verify_skill.py` per unit; one fix brief per failure, then recheck.
5. `scripts/normalize_tags.py packages/<package> --write`; record each transition with `scripts/state_event.py workspace/<slug> unit <unit> RESEARCHED|AUTHORED|VERIFIED`.
6. Close the batch: `metric <unit> actual` per unit; any mistake seen in two units becomes `retro add --kind brief --text "..."` so the next batch's briefs carry it. If `BUDGET EXCEEDED` is printed, stop and ask the user.
7. `apm install` is not run here (see [shared files](../policy/shared-files.md)).

In `from-research` mode skip step 1 for COMPLETE research files.

**Done when:** all units VERIFIED. **Gate:** none.
