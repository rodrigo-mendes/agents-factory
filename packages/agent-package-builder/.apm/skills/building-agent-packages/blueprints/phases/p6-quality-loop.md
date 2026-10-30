# P6 Quality loop (rounds=N, default 3)

Back to [SKILL.md](../../SKILL.md). Rules: [triage and stop](../policy/triage-and-stop-rules.md).

**Source-first testing (always):** every round reviews the package SOURCE `packages/<pkg>/.apm/` (plus its `README.md` and `apm.yml`), never the generated `.claude/`, and writes reports only under `workspace/<slug>/execution-<N>/rounds/`. Do not wait for the full `apm install`: P6 starts as soon as P5 passes `verify_package.py` and the scoped install (`scripts/scoped_install.py`, seconds); the full root install runs only in P8. Whether `.claude/` matches the source is checked once, mechanically, in P8 step 3. Why: the Windows install takes 12-40 min and the reviewers only need the package's own files (decided in the github-actions-cicd run, 2026-10-30).

Round k (VALIDATE, TEST and AUDIT run in parallel, at most 4 agents at a time; all three only read the source, so none waits for another):
1. VALIDATE skills (groups <= 5) and the package (agents, rules, command, README, apm.yml), from the source.
2. TEST each skill's evaluation scenarios from the source; the evaluator loads the skill's SKILL.md into its own context and judges it, never by spawning agents (flat fan-out).
3. AUDIT the package source `packages/<pkg>/.apm/`; the auditor applies the scope, flow and engine lenses one after another in its own context (no lens agents) and writes the consensus itself.
For every reviewer launched, first run `state_event.py ... round-start round-<k> <validate|test|audit> <target>`: it writes `<kind>__<target>.running`, so the dashboard shows `running` and `check_state.py` does not report the pending report as missing (it does if P6 is closed while a marker has no report). Delete the marker when the report lands.
4. CONSOLIDATE: the three results live in `execution-<N>/rounds/round-<k>/<validate|test|audit>__<target>.md`; write `scoreboard.md` (score per skill, with the previous round's score as baseline); re-check each HIGH against the file; every confirmed HIGH/MEDIUM becomes `finding add` (keep the F-id in the fix brief), and next round's validator gets the open F-ids to confirm FIXED or REOPENED; `state_event.py ... event P6 ROUND_DONE "round-<k> HIGH=<n>"`.
5. Mark `unit <unit> VALIDATED --score <s>` only for a skill with 0 HIGH and its scenarios passing this round; a skill that will not get there is `DEFERRED` with a `--note`.
6. Exit criteria met -> leave the loop. Else if k < N -> FIX ([fix brief](../worker-briefs/fix-cycle.md)) -> round k+1. Else leave with leftovers.
7. Regression -> stop, show the diff.

A finding REOPENED twice is not sent to another fix round: ask the user, record `decide --gate none --who user` citing the F-id (or mark it DEFERRED with `--note`). Round k+1 re-reviews only changed skills plus open F-ids. Starting a round beyond `max_rounds` of the brief is a new question to the user, recorded as a decision citing `max_rounds`. `check_state.py` must pass before leaving P6 (every unit VALIDATED, DEFERRED or DROPPED). `rounds: 0` skips the loop only after explicit user confirmation.

**Gate:** none; leftovers become the G3 decision list.
