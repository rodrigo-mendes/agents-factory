---
kind: work-order
id: wo-<nn>-review
from: building-quarkus-aws-saas
to: quarkus-code-reviewer        # Stripe tasks: two work-orders, sequential: stripe-advisor FIRST, then this one only after the advisor's review is `approved`
change: <change-id>
task: <task-id>                  # SAME task as the code work-order (keeps review_rounds per task)
refs: [wo-<nn>-code]             # requirements/ADRs and the code work-order only; never a `result-*` record
requirements: [R1]
status: pending
createdAt: <ISO 8601 UTC>
---

## Scope

Independent read-only review (step I7), round <n>. Use review id `review-<nn>` (next free number).

## Skills

- refactoring-quarkus-java (reviewer checklist)
- <every skill the code work-order listed; their Never-Do items apply>

## Requirements

- R1: <requirement text> - scenarios: <names>.

## Constraints

- Files to review (repo-relative): `<path>`, `<path>`. ADR directory: `openspec/specs/architecture/adr/`
  (only `accepted` counts). An ADR violation is always HIGH.
- Ask-First items the code work-order settled (copy verbatim, e.g. `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)` when integrating-quarkus-langchain4j-v1-15 is listed).
- Do not pass the author's reasoning or the `result-*` record; the reviewer judges artefacts.
- Stripe task: every review record of a Stripe task (the wrapped `stripe-advisor` notes and the
  `quarkus-code-reviewer` record) gets `role: stripe` in its frontmatter (the profile then routes `changes-requested` to `stripe-integrator`).
- Stripe task order: `stripe-advisor` reviews first; `quarkus-code-reviewer` runs only after the advisor's
  review is `approved`. Any `changes-requested` returns to `stripe-integrator` before the other review runs.
  Each `changes-requested` is one `review_rounds` round (review records with that outcome per task); a
  project may raise `limits.review_rounds` for Stripe tasks in `openspec/handoff-profile.yaml`.

## Acceptance criteria

- [ ] Review record returned with `outcome` and `round: <n>`; every finding has `file:line` and evidence.
- [ ] Traceability matrix requirement -> scenario -> test present.
