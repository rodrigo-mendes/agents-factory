---
kind: work-order
id: wo-<nn>-solution-architect
from: building-aws-saas-serverless-quarkus-react-nextjs
to: solution-architect
change: <change-id>
task: spec                       # E1-E4 work-orders use task: spec
refs: []                         # E4: [verify-E3b]; a fix round: [<previous wo id>, verify-<stage>]
requirements: [R1]               # E4: the R* the design owns
status: pending                  # pending | in-progress | done | blocked | cancelled
createdAt: <ISO 8601 UTC>
---

## Scope

Stage: E2a (solution architecture) | E4 (one design per flow). Designs the parts of the system and how they talk;
it never picks infrastructure details (accounts, network, modules) and never writes code.
Output: files + `result-<nn>-solution-architect.md` (kind `report`, shape of `assets/result-code.template.md`, outcome
`success|partial|failed|needs-input`; unanswered question -> `needs-input` with numbered questions). The record does not need `role:`.
- E2a: `openspec/specs/architecture/spec.md`, `contracts/*.md`, ADRs in `openspec/specs/architecture/adr/`.
- E4: `openspec/changes/<id>/design/<flow>.md` (one per flow) and the index `design.md`; every R* is owned by exactly one design.

## Skills

- <aws-skills / quarkus skills the question needs, e.g. architecting-aws-saas-multitenant, designing-dynamodb-nosql>

## Requirements

- R1: <requirement text copied from the spec>.

## Applicable ADRs

- `architecture/adr/<NNN>-<title>.md`, `design/adr/<NNN>-<title>.md`, `infrastructure/adr/<NNN>-<title>.md` - <what each forces; only accepted ADRs, or proposed ones of this stage>.

## Constraints

- Inputs: interview answers (verify-E1), `<paths>`. Output paths as above; contracts live only in `architecture/contracts/`.
- A decision that the user must take is a `needs-input` question, never an assumption.

## Limits

- review_rounds: <effective value>   (source: profile | override | args)

## Acceptance criteria

- [ ] Every file of the Scope exists; ADRs use `assets/adr.template.md` with `area: architecture`, status `proposed`.
- [ ] E4: each design has the 11 sections of the plan (scope, traceability, sequences, contracts, data, errors, security, limits, AI, build order, risks); the index lists all designs.
- [ ] Result record valid; the independent reviewer is `solution-architecture-reviewer` (verify-E2a / verify-E4-<flow> / verify-E4-index).
