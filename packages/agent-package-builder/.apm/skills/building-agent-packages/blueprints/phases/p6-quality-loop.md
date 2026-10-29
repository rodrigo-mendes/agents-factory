# P6 Quality loop (rounds=N, default 3)

Back to [SKILL.md](../../SKILL.md). Rules: [triage and stop](../policy/triage-and-stop-rules.md).

Before round 1: `apm install --target claude` + the two post-install scripts so the audit sees the generated `.claude/`.

Round k:
1. VALIDATE skills (groups <= 5) and the package.
2. TEST each skill's evaluation scenarios.
3. AUDIT the package in `.claude/` (foreground, alone).
4. CONSOLIDATE: the three results live in `execution-<N>/rounds/round-<k>/<validate|test|audit>__<target>.md`; write `scoreboard.md` (score per skill, with the previous round's score as baseline); re-check each HIGH against the file; every confirmed HIGH/MEDIUM becomes `finding add` (keep the F-id in the fix brief), and next round's validator gets the open F-ids to confirm FIXED or REOPENED; `state_event.py ... event P6 ROUND_DONE "round-<k> HIGH=<n>"`.
5. Mark `unit <unit> VALIDATED --score <s>` only for a skill with 0 HIGH and its scenarios passing this round; a skill that will not get there is `DEFERRED` with a `--note`.
6. Exit criteria met -> leave the loop. Else if k < N -> FIX ([fix brief](../worker-briefs/fix-cycle.md)) -> round k+1. Else leave with leftovers.
7. Regression -> stop, show the diff.

A finding REOPENED twice is not sent to another fix round: ask the user, record `decide --gate none --who user` citing the F-id (or mark it DEFERRED with `--note`). Round k+1 re-reviews only changed skills plus open F-ids. Starting a round beyond `max_rounds` of the brief is a new question to the user, recorded as a decision citing `max_rounds`. `check_state.py` must pass before leaving P6 (every unit VALIDATED, DEFERRED or DROPPED). `rounds: 0` skips the loop only after explicit user confirmation.

**Gate:** none; leftovers become the G3 decision list.
