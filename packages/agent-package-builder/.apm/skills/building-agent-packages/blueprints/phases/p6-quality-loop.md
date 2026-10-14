# P6 Quality loop (rounds=N, default 3)

Back to [SKILL.md](../../SKILL.md). Rules: [triage and stop](../policy/triage-and-stop-rules.md).

Before round 1: `apm install --target claude` + the two post-install scripts so the audit sees the generated `.claude/`.

Round k:
1. VALIDATE skills (groups <= 5) and the package.
2. TEST each skill's evaluation scenarios.
3. AUDIT the package in `.claude/` (foreground, alone).
4. CONSOLIDATE: write the three results to `workspace/<slug>/validation/round-<k>/`; compute the scoreboard; re-check each HIGH against the file.
5. Exit criteria met -> leave the loop. Else if k < N -> FIX ([fix brief](../worker-briefs/fix-cycle.md)) -> round k+1. Else leave with leftovers.
6. Regression -> stop, show the diff.

Log each round in PIPELINE_STATE (Quality loop table). `rounds: 0` skips the loop only after explicit user confirmation.

**Gate:** none; leftovers become the G3 decision list.
