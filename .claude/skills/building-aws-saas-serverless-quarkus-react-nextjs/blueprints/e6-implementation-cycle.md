# E6 - Implementation cycle I0-I9 (per task)

Back to [SKILL.md](../SKILL.md). Author and reviewer are always different agents; the reviewer never sees the author's reasoning. Every author and reviewer is launched with `model: "sonnet"` (Model split, SKILL protocol 11). I write work-orders and rebuild; I never write code.

## The cycle has 4 stages with one owner each

```
STAGE 1  MANAGER prepares   wo-NN-<role>.md (Functionality, Diagram, R*, scenarios, ADRs of 3 folders, skills, limits); launch the AUTHOR
STAGE 2  AUTHOR builds      I0 Prepare -> I1 Tests -> I2 Minimal -> I3 Refine -> I4 Clean -> I5 Refactor -> I6 Verify -> I9 Close (result-NN-<role>.md)
                            I6 fails: retry (build_attempts); limit reached: stop, the manager escalates
STAGE 3  REVIEWER reviews   I7: only code, requirements, ADRs, skills (never the author's result); review-NN.md approved | changes-requested
                            two reviewers: the 2nd starts only after the 1st approved (hold)
                            changes-requested -> I8: NEW wo-MM-<role> to the author (cites the review) -> I6 -> I9 -> new review (review_rounds)
STAGE 4  MANAGER confirms   reruns the build myself; green -> task accepted; red -> back to the author
```

After each stage I run `check_records.py -> detect_drift.py --include-worktree -> board.py` and follow `NEXT:`.

| Step | What | Evidence | Runner |
|---|---|---|---|
| I0 Prepare | read work-order, requirements, scenarios, ADRs, skills; short plan | "Plan" | author (one launch covers I0-I6) |
| I1 Tests first | each scenario -> >= 1 test with traceable name (`R1_otherTenant_returns403`, `R1_empty_showsEmptyState`); tests fail for the right reason | scenario -> test list | author |
| I2 Minimal implementation | smallest code that passes | green tests | author |
| I3 Refinement | edge cases, validation, error mapping, per-type extras (table below) | cases added | author |
| I4 Clean code | `refactoring-quarkus-java` + rule `quarkus-clean-code` (Java); the front-end rule and skills (front) | checklist | author |
| I5 Refactor | extract collaborators; identical behaviour | before/after | author |
| I6 Verify | build + tests + coverage, offline only (table below) | command output | author, **then me** (rerun) |
| I7 Review | diff vs rules, Never-Do of listed skills, accepted ADRs (violation = HIGH), scenario -> test traceability | `review-NN.md` | reviewer chain |
| I8 Fix | HIGH always, MEDIUM fixed or justified; back to I6 | resolved findings | author on a NEW `wo-MM-<role>.md` (`refs`: previous wo + `review-NN`; same `task`) |
| I9 Close | result with "Spec impact" | `result-NN-<role>.md` (an I8 launch writes its own `result-MM-<role>.md`; append-only) | author |

## Review chain per task type

| Task type (role) | Author | Reviewers in sequence | I6 build, which I rerun |
|---|---|---|---|
| back (`code`) | `quarkus-lambda-integrator` | `quarkus-code-reviewer` | `mvn -q verify` |
| Stripe (`stripe`) | `stripe-integrator` | `stripe-advisor` -> `quarkus-code-reviewer` | `mvn -q verify` |
| AI (`ai`) | `quarkus-lambda-integrator` | `langchain4j-reviewer` -> `quarkus-code-reviewer` | `mvn -q verify` |
| front (`frontend`) | `nextjs-frontend-integrator` | `nextjs-code-reviewer` -> `ui-design-reviewer` (visual fidelity) | `pnpm install --frozen-lockfile && pnpm lint && pnpm test && pnpm build`, hash of `out/` |
| infra / bootstrap (`infra`) | `aws-terraform-engineer` | `terraform-code-reviewer` | `terraform fmt -check`, `init -backend=false`, `validate`, mocked `test` |
| observability (Mode B) | `aws-observability` | `terraform-code-reviewer` | `terraform validate` |
| CI/CD (`cicd`) | `cicd-pipeline-engineer` | `cicd-pipeline-reviewer` | `actionlint`, `yamllint` |

Rule: the **last reviewer of back-end code is always `quarkus-code-reviewer`**. A design change inside a task goes back to the design owner through E4, not to the code author. The front-end build uses pnpm and Node 26 like the CI skill so the local build equals the pipeline's.

## Variants by task type (what changes in each step)

| | back / Stripe | AI | front | infra / observability | CI/CD |
|---|---|---|---|---|---|
| Main input | `design/<flow>.md` + contract | same + provider ADR | wireframe + design system + contract | `infra-design.md` + `infrastructure/spec.md` | `infrastructure/spec.md` section 10 |
| I1 tests | JUnit + mock event server (Stripe: signed test webhook) | `@InjectMock` on the AI service | component test per scenario (4 states) | mocked `terraform test` | grep checks from the skills |
| I3 extras | tenant from token claims, timeouts below Lambda timeout, idempotency (Stripe: signature before effects, idempotency key, dedupe) | explicit model, provider timeout, `@Timeout` below the gateway, fallback, secret in Secrets Manager, prompt and answer out of logs | 4 states, 401/403, a11y, only endpoints of the contract, no server features, no secret in `NEXT_PUBLIC_*` | least-privilege IAM, KMS, tags, variable validation | SHA pins, minimal `permissions`, OIDC without keys, one `ci-gate` |
| I6 extras | JaCoCo >= `coverage_min`, `function.zip` | same | lint, test, build, `out/` hash | validate | actionlint |

## Orchestrator loop for one task

1. Write `wo-NN-<role>.md`; `check_records.py`; launch the author with its model (brief in [worker briefs](worker-briefs.md)).
2. When it returns: confirm the record file exists (`ls`), run `check_records.py`. Exit != 0: return the error lines to the same agent (counts toward `record_rejections`).
3. Rerun the build of the task type myself (table above). Red but the report says green -> the report is wrong: treat as `failed`, quote both outputs in the next brief or the escalation.
4. `detect_drift.py --include-worktree`, then `board.py`; follow `NEXT:` (exit 1 of drift is an error, never "no drift").
   - `result ... success` -> reviewer: write `wo-NN-review.md` (files from the diff, `R*` and scenarios, ADR paths of the 3 folders, skills, round, next free review `NN`), launch **without** the result record or any author reasoning.
   - Save the reviewer's inline record as `review-NN.md` verbatim (`saved-by`; `role:` = the task's role so `changes-requested` routes to the author).
   - **Holds:** with two reviewers, after the first `approved` write the second review work-order with `status: pending` **before** `board.py`; set the task's work-orders `done` only after the second `approved`. Any `changes-requested` goes to the author before the other review runs.
   - `changes-requested` -> I8 on a NEW work-order (next free number, same `task`, `refs`: previous wo + `review-NN`); the author writes its own `result-MM-<role>.md`; then I6, then a new review round. Set the superseded work-order `done`/`cancelled`.
   - `outcome: failed|partial|needs-input` -> relay questions to the user (needs-input) or retry per limits; `NEXT: escalate` -> [escalation](#escalation).
   - All tasks approved (`NEXT: orchestrator`): give the user the commit plan and PR text ([E7](e7-deploy-and-observability.md)); there is no deploy step for an agent.
5. Task done when: every scenario has a green test, my rebuild is green, coverage >= `coverage_min` (Java), no open HIGH, MEDIUMs resolved or justified, "Spec impact" present, and the work-orders are set `done`. Only then dependent tasks start. The bootstrap task is done only after the user applied it (`gate=bootstrap-apply`, `subject=result-NN-infra`) and the next tasks depending on it start after that.

## Counters and limits (read from `status.md`)

| Loop | Parameter | Default | At the limit |
|---|---|---|---|
| I1-I6 build green | `limits.build_attempts` (roles code, ai, stripe, frontend, infra, observability, cicd) | 3 per task | escalate |
| I7-I8 review -> fix | `limits.review_rounds` | 2 | escalate |
| `check_records.py` fails on the same record | `limits.record_rejections` | 2 | escalate |
| CD pipeline failures | `limits.deploy_cycles` (per change) | 2 | escalate |
| spec-delta revisions | `limits.delta_revisions` (per change) | 2 | escalate |

Never count in your head; the board counts from records (`result` with `failed|partial`, `review` with `changes-requested`, `result-NN-pipeline` of role `pipeline-cd` with `failed`).

## Escalation

"Stop and the manager escalates to you" is mechanical: `board.py` counts the records and prints `NEXT: escalate limit=<name> task=<Tn>`.

1. I stop **only that task** (other independent tasks continue) and write `handoff/escalation-NN.md`: task, limit (`2 of 2`), attempts with what each tried, the persisting error (command output or `file:line`), a hypothesis, 2-4 options with impact (e.g. raise a timeout and move the call to SQS; new ADR to accept a response without category; change requirement R3; accept the risk).
2. I show it to the user with a multiple-choice question (the options + "other").
3. The user answers; I store the reply verbatim under `## Answer`, set `status: answered` + `answeredAt`, and append it to `## Approvals`.
4. The counters of that task restart from zero; I write a new work-order following the chosen option (an option that changes a requirement or an ADR goes back to E3 or the owning E2 front for that part).

While an escalation is open nothing new goes to the PR or the pipeline. Limits can be changed per project (`openspec/handoff-profile.yaml`) or per run (`limits.review_rounds=4`).

## Spec impact intake

Read "Spec impact" of every `result-*`: `Divergences`/`Ambiguities` non-empty => `spec_impact` must not be `none` (otherwise return the record to its author like a `check_records.py` failure and increment `rejections`); drift handled in [E8](e8-reverse-sync.md) at the next `NEXT: sync`.

## Acceptance of the task (checked by scripts + reviewers, not by the author)

`check_records.py` exit 0; the latest review of the chain `approved`; my own rebuild exit 0; work-orders set `done` (closing rule, SKILL.md protocol 8) and `board.py` marks the task `done`.
