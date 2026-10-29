---
kind: work-order
id: wo-<nn>-stripe
from: building-quarkus-aws-saas
to: stripe-integrator
change: <change-id>
task: <task-id>                  # T1, T2 ...
refs: []                         # for a fix round: [<previous wo id>, review-<nn>]
requirements: [R1]
status: pending                  # pending | in-progress | done | blocked | cancelled
createdAt: <ISO 8601 UTC>
---

## Scope

One Stripe task = one webhook endpoint, checkout/session flow or billing call. Target project path: `<path>`.
Output: code + `result-<nn>-stripe.md` (kind `report`, from `assets/result-code.template.md`, with
`spec_impact` and `## Spec impact`). Review follows by `stripe-advisor` (and `quarkus-code-reviewer` for the Quarkus side).

## Skills

- integrating-stripe-quarkus-v3-40 (and the Stripe Java skills this work-order names)
- The Quarkus skills the endpoint needs (see roles-and-skills.md): developing-quarkus-amazon-lambda-http-v3-40,
  securing-quarkus-lambda-cognito-v3-40 when authenticated; refactoring-quarkus-java (always, for I4/I5)

## Requirements

- R1: <requirement text copied from the spec> - scenarios: <names>, one test each.

## Applicable ADRs

- `openspec/specs/architecture/adr/<NNN>-<title>.md` - <what it forces or forbids: webhook secret storage, idempotency store, API version>.

## Constraints

- Raw webhook body stays intact for signature verification; webhook secret and API keys only from the
  secret store named in the ADR, never in code, logs or records; Stripe API version pinned as the skill states.
- Idempotency keys on every mutating call; no real Stripe calls in tests (test-mode fixtures only).
- Ask-First items of the Stripe skill that this work-order settles: <item -> decision>.

## I-steps

Same steps and evidence as `wo-code.template.md` (I0-I6, I8 with a review record, I9 close).

## Limits

- build_attempts: <effective value>   (source: profile | override | args)
- review_rounds: <effective value>
- coverage_min: <effective value>

## Acceptance criteria

- [ ] Every scenario has a passing, traceable test; webhook signature failure and replay are covered.
- [ ] `mvn -q verify` green; coverage of new classes >= coverage_min.
- [ ] Result record valid (`result-<nn>-stripe.md`), with `spec_impact` and `## Spec impact`.
