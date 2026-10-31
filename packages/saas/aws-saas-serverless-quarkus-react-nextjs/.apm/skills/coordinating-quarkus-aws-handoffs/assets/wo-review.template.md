---
kind: work-order
id: wo-<nn>-review
from: building-aws-saas-serverless-quarkus-react-nextjs
to: quarkus-code-reviewer        # reviewer per task type, see the variants table below
change: <change-id>
role: <author role>              # the role the review record must carry (variants table); omit for plain `code`
task: <task-id>                  # SAME task as the authoring work-order (keeps review_rounds per task)
refs: [wo-<nn>-code]             # requirements/ADRs and the code work-order only; never a `result-*` record
requirements: [R1]
status: pending
createdAt: <ISO 8601 UTC>
---

## Scope

Independent read-only review (step I7), round <n>. Use review id `review-<nn>` (next free number).

## Variants (one work-order per reviewer; the reviewer never sees the reasoning of the author)

| Task type | Reviewers in order (each only after the previous is `approved`) | `role:` on every review record | `changes-requested` returns to |
|---|---|---|---|
| back (`code`) | `quarkus-code-reviewer` | omit | `quarkus-lambda-integrator` |
| stripe | `stripe-advisor`, `quarkus-code-reviewer` | `stripe` | `stripe-integrator` |
| ai | `langchain4j-reviewer`, `quarkus-code-reviewer` | `ai` | `quarkus-lambda-integrator` |
| frontend | `nextjs-code-reviewer` (code), `ui-design-reviewer` (visual fidelity vs wireframe and design system) | `frontend` (both) | `nextjs-frontend-integrator` |
| infra | `terraform-code-reviewer` | `infra` | `aws-terraform-engineer` |
| observability (mode B) | `terraform-code-reviewer` | `observability` | `aws-observability` |
| cicd | `cicd-pipeline-reviewer` | `cicd` | `cicd-pipeline-engineer` |

**Hold:** when the first reviewer of a two-reviewer task approves, write the second `wo-<nn>-review` with `status: pending` (same `task`) BEFORE running `board.py`; set the work-orders of the task `done` only after the last `approved`. Design deliveries (E2a/E2b/E2c, E3b, E4) are not reviews: their reviewers return `verify-<stage>` records.

## Skills

- refactoring-quarkus-java (reviewer checklist; back-end and AI)
- front: the Vercel skills of the front work-order (their Never-Do items are the criteria); terraform: the `provisioning-aws-<service>-v6` of the task; cicd: the github-actions-cicd skills of the work-order
- <every skill the code work-order listed; their Never-Do items apply>

## Requirements

- R1: <requirement text> - scenarios: <names>.

## Constraints

- Files to review (repo-relative): `<path>`, `<path>`. ADR directories: `openspec/specs/architecture/adr/`, `openspec/specs/design/adr/`,
  `openspec/specs/infrastructure/adr/` (only `accepted` counts). A violation of an ADR of ANY of the three is always HIGH.
- Ask-First items the code work-order settled (copy verbatim, e.g. `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)` when integrating-quarkus-langchain4j-v1-15 is listed).
- Do not pass the author's reasoning or the `result-*` record; the reviewer judges artefacts.
- Tasks with two reviewers (stripe, ai, frontend): every review record carries the `role:` of the table, so the profile routes
  `changes-requested` to the right author. Any `changes-requested` returns to the author before the other review runs.
  Each `changes-requested` is one `review_rounds` round (review records with that outcome per task); a
  project may raise `limits.review_rounds` in `openspec/handoff-profile.yaml`.

## Acceptance criteria

- [ ] Review record returned with `outcome` and `round: <n>`; every finding has `file:line` and evidence.
- [ ] Traceability matrix requirement -> scenario -> test present.
