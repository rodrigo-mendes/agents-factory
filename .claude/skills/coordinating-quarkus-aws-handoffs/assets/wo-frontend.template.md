---
kind: work-order
id: wo-<nn>-frontend
from: building-aws-saas-serverless-quarkus-react-nextjs
to: nextjs-frontend-integrator
change: <change-id>
task: <task-id>                  # T1, T2 ...
refs: []                         # [verify-E3b, verify-E4-<flow>, <wo of the contract task>]; fix round: [<previous wo id>, review-<nn>]
requirements: [R1, R2]
status: pending
createdAt: <ISO 8601 UTC>
---

## Functionality

Plain sentences: what the logged-in user sees and can do on this screen, including empty state, error, 401 and 403.

## Diagram

Sequence from `changes/<id>/design/<flow>.md` (section 3) and the wireframe from `openspec/specs/design/wireframes/<screen>.md` (ASCII, with R* marks and the states).

## Scope

One front task = one screen or one shared component set. Target path: `frontend/`. Static export only (no SSR, Server Actions, API routes).
Steps I0-I6 and I9 (I8 + I9 with a review). Output: code + `result-<nn>-frontend.md` (shape of `assets/result-code.template.md`; `role: frontend` is derived from the agent; build line: `pnpm install --frozen-lockfile && lint && test && build`, with the sha256 of `out/`).

## Inputs

- Wireframe: `openspec/specs/design/wireframes/<screen>.md`
- Design system: `openspec/specs/design/design-system.md`
- Contract: `openspec/specs/architecture/contracts/<name>.md`

## Skills

- react-best-practices - composition-patterns - building-components - web-design-guidelines - next-dev-loop (list only the Vercel skills this screen needs)

## Requirements

- R1: <requirement text> - scenarios: <names>, one component test each (`R1_<scenario>`).

## Applicable ADRs

- `architecture/adr/<NNN>-static-export.md`, `design/adr/<NNN>-design-system-base.md`, `design/adr/<NNN>-theming-dark-mode.md` - <what each forces>. A violation of any ADR of the three folders is HIGH.

## Constraints

- Call only endpoints of the contract; the 4 screen states; 401 -> login, 403 -> "no permission"; accessibility level of the design ADR; check both themes.
- No secrets in the bundle; only public env vars (`NEXT_PUBLIC_*`) named in this work-order.

## Limits

- build_attempts: <effective value> - review_rounds: <effective value> - coverage_min: <effective value>   (source: profile | override | args)

## Acceptance criteria

- [ ] One test per scenario, named `R<n>_<scenario>`.
- [ ] lint, test and build green; `out/` generated; `portable.py dirhash out` reported.
- [ ] Only contract endpoints are called.
- [ ] Review order: `nextjs-code-reviewer` first, `ui-design-reviewer` (visual fidelity) after the first is `approved`; both review records carry `role: frontend` (REQUIRED: it sends `changes-requested` back to `nextjs-frontend-integrator`).
- [ ] Result record valid, with `spec_impact` and `## Spec impact`.
