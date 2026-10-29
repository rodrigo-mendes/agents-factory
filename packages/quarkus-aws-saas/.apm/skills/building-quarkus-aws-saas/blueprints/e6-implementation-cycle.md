# E6 - Implementation cycle I0-I9 (per task)

Back to [SKILL.md](../SKILL.md). Author and reviewer are always different agents; the reviewer never sees the author's reasoning.

## Steps and who runs them

| Step | What | Evidence | Runner |
|---|---|---|---|
| I0 Prepare | read work-order, requirements, scenarios, ADRs, skills; short plan | "Plan" | integrator (1 launch covers I0-I6) |
| I1 Tests first | each scenario -> >= 1 test with traceable name (`R1_otherTenant_returns403`); tests fail for the right reason | scenario -> test list | integrator |
| I2 Minimal implementation | smallest code that passes | green tests | integrator |
| I3 Refinement | edge cases, validation, error -> HTTP mapping, tenant isolation from token claims, downstream timeouts below Lambda timeout, idempotency; a test per item | cases added | integrator |
| I4 Clean code | `refactoring-quarkus-java` + rule `quarkus-clean-code` | rule checklist | integrator |
| I5 Refactor | extract collaborators, records; identical behaviour | before/after | integrator |
| I6 Verify | `mvn -q verify`, JaCoCo for new classes >= `coverage_min`, `function.zip` build, no new warnings; offline only | command output | integrator, **then me** (re-run) |
| I7 Review | diff vs rule, Never-Do of listed skills, accepted ADRs (violation = HIGH), scenario -> test traceability | `review-NN.md` | `quarkus-code-reviewer` (+ `stripe-advisor` for Stripe) |
| I8 Fix | HIGH always, MEDIUM fixed or justified; back to I6 | resolved findings | integrator on a NEW work-order `wo-MM-code.md` (`refs`: previous wo + `review-NN`; same `task`) |
| I9 Close | result with "Spec impact" | `result-NN-code.md` (an I8 launch writes its own `result-MM-code.md`) | integrator |

Stripe tasks: `stripe-integrator` runs I0-I9 (mismatch note in [risks](unverified-and-risks.md)); reviewers: `quarkus-code-reviewer` **and** `stripe-advisor`.
Design change inside a task -> also `aws-architect`.

## Orchestrator loop for one task

1. Write `wo-NN-code.md`; `check_records.py`; launch the integrator (brief in [worker briefs](worker-briefs.md#quarkus-lambda-integrator)).
2. When it returns: confirm the record file exists (`ls`), run `check_records.py`. Exit != 0: return the error lines to the same agent (counts toward `record_rejections`).
3. Re-run `mvn -q verify` in the project myself. Red but the report says green -> the report is wrong: treat as `failed`, quote both outputs in the next brief or the escalation.
4. `detect_drift.py`, then `board.py`; follow `NEXT:`. Agents leave their code **uncommitted until E9**, so plain `detect_drift.py` sees only commits: add `--include-worktree` (mandatory in every run during E6-E9, not Ask First) to see the working tree; without it uncommitted edits are invisible and the check is vacuous (register L5). Exit 1 is an error (show it; if `lastSyncedSha` is missing run the [E5 baseline](e4-e5-design-and-tasks.md#e5-drift-baseline-after-the-approval-before-the-first-work-order)), never "no drift".
   - `result ... success` -> reviewer: write `wo-NN-review.md` (files from the diff, `R*` and scenarios, ADR paths, skills, round, next free review `NN`), launch **without** passing the result record or any author reasoning (the reviewer must not read `result-*`; list only code, tests, requirements, ADRs).
   - Save the reviewer's inline record as `review-NN.md` verbatim (`saved-by`). `approved` -> set the task's work-orders (code, review) `done` once the record is accepted.
   - **Stripe task:** after `stripe-advisor`'s `approved`, write the `quarkus-code-reviewer` review work-order with `status: pending` **before** running `board.py`; set the task's work-orders `done` only after the second reviewer's `approved` (else `review approved + all_tasks: done` routes to deploy early).
   - **Stripe task:** `changes-requested` goes to a NEW `wo-MM-stripe.md` (`stripe-integrator`, next free number, same `task`, `refs`: previous wo + `review-NN`), as in [worker briefs](worker-briefs.md#stripe-integrator-and-stripe-advisor).
   - Other tasks: `changes-requested` -> I8 on a NEW work-order `wo-MM-code.md` (next free number, same `task`, `refs`: previous wo + `review-NN`); the integrator writes its own `result-MM-code.md` (records are append-only, never overwrite `result-NN-code.md`); then I6 again, then a new review round. Set the superseded work-order `done`/`cancelled`.
   - `outcome: failed|partial|needs-input` -> relay questions to the user (needs-input) or retry per limits; `NEXT: escalate` -> [escalation](#escalation).
5. Task done when: every scenario has a green test, my `mvn -q verify` is green, coverage >= `coverage_min`, `function.zip` built, no open HIGH, MEDIUMs resolved or justified in the record, report has "Spec impact".

## Counters and limits (read from `status.md`)

| Loop | Parameter | Default | At the limit |
|---|---|---|---|
| I1-I6 tests/build green | `limits.build_attempts` | 3 per task | escalate |
| I7-I8 review -> fix | `limits.review_rounds` | 2 | escalate |
| `check_records.py` fails on the same record | `limits.record_rejections` | 2 | escalate |

Never count in your head; the board counts from records (`result` with `failed|partial`, `review` with `changes-requested`).

## Escalation

On `NEXT: escalate`: stop only that task; write `escalation-NN.md` from the template (attempts with what each tried, persisting error with evidence = command output
or `file:line`, hypothesis, 2-4 options with impact such as relaxing a requirement, new ADR, different approach, accept risk). Show it, ask the user, store the reply
verbatim under `## Answer`, set `status: answered` + `answeredAt`; counters restart. Other independent tasks keep going.

## Spec impact intake

Read "Spec impact" of every `result-*`: `Divergences`/`Ambiguities` non-empty => `spec_impact` must not be `none` (if it is, return the record to its author like a `check_records.py` failure and increment `rejections`); drift handled in [E8](e8-reverse-sync.md) at the next `NEXT: sync`
(do not wait for the end of the change if the divergence changes a requirement).

## Acceptance of the task (checked by scripts + reviewer, not by the author)

`check_records.py` exit 0; `review` latest `approved`; my own `mvn -q verify` exit 0; the task's work-orders are set `done` (closing rule, SKILL.md Protocol 8) and `board.py` marks the task `done`. Only then dependent tasks start.
