---
kind: work-order
id: wo-<nn>-code
from: building-aws-saas-serverless-quarkus-react-nextjs
to: quarkus-lambda-integrator    # back-end only; Stripe: wo-stripe; AI: wo-ai; front: wo-frontend
change: <change-id>
task: <task-id>                  # T1, T2 ...
refs: []                         # for I8: [<previous wo id>, review-<nn>]
requirements: [R1]
status: pending                  # pending | in-progress | done | blocked | cancelled
createdAt: <ISO 8601 UTC>
---

## Functionality

Plain sentences: what the user gets from this endpoint or consumer, including the error cases.

## Diagram

Sequence copied from `changes/<id>/design/<flow>.md` (section 3).

## Scope

One task = one endpoint or one event consumer. Target project path: `<path>`. Handoff folder: `<path>`.
Steps: I0-I6 and I9 (or I8 + I9 when `refs` holds a review record).

## Skills

Load only these (see roles-and-skills.md of the profile for the choice per task type):

- developing-quarkus-amazon-lambda-v3-40 (and the others the task needs)
- refactoring-quarkus-java (always, for I4/I5)

## Requirements

- R1: <requirement text copied from the spec> - scenarios: <scenario names>, one test each, named
  after the scenario (e.g. `R1_otherTenant_returns403`).

## Applicable ADRs

- `architecture/adr/<NNN>-<title>.md`, `infrastructure/adr/<NNN>-<title>.md` (and `design/adr/...` when it applies) - <one line: what each forces or forbids>.
  Only `accepted` ADRs; a conflict with a loaded skill's Never-Do is returned as a question.

## Constraints

- Forbidden approaches (from ADRs and skills), Lambda timeout and downstream timeout budget, tenant
  identity only from verified token claims, no real AWS calls in tests, no secrets in logs.
- Ask-First items of the listed skills that this work-order settles: <item -> decision>. For `integrating-quarkus-langchain4j-v1-15` write `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)`; the user's yes is recorded under `## Approvals` as `gate=D1-langchain4j` (verbatim words).

## I-steps

| Step | Expected evidence in the result |
|---|---|
| I0 Plan | short plan (classes, packages, tests) |
| I1 Tests first | scenario -> test list, tests failing for the right reason |
| I2 Minimal implementation | tests green |
| I3 Refinement | edge cases, validation, error mapping, timeouts, idempotency; a test each |
| I4 Clean code | rule checklist |
| I5 Refactor | before/after (classes, methods > 40 lines), behaviour identical |
| I6 Verify | `mvn -q verify`, JaCoCo, `function.zip` build, offline only |
| I8 Fix | only with a review record: HIGH fixed, MEDIUM fixed or justified |
| I9 Close | `result-<nn>-code.md` with `## Spec impact` |

## Limits

- build_attempts: <effective value>   (source: profile | override | args)
- review_rounds: <effective value>
- coverage_min: <effective value>

## Acceptance criteria

- [ ] Every scenario of the linked requirements has a passing, traceable test.
- [ ] `mvn -q verify` green; coverage of new classes >= coverage_min; `function.zip` built.
- [ ] No HIGH finding open (including ADR violations); MEDIUMs fixed or justified.
- [ ] Result record valid, with `spec_impact` and `## Spec impact`.
