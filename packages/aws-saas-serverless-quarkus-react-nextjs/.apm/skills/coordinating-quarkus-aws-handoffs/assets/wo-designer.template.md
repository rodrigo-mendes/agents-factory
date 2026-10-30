---
kind: work-order
id: wo-<nn>-designer
from: building-aws-saas-serverless-quarkus-react-nextjs
to: ui-ux-designer
change: <change-id>
task: spec                       # E1-E4 work-orders use task: spec
refs: []                         # E3b: [verify-E3]; a fix round: [<previous wo id>, verify-<stage>]
requirements: [R1]               # E3b: the R* of the screens
status: pending
createdAt: <ISO 8601 UTC>
---

## Scope

Stage: E2b (design system and design ADRs) | E3b (wireframes and navigation). Design only, no code.
Output: files + `result-<nn>-designer.md` (kind `report`, outcome `success|partial|failed|needs-input`).
- E2b: `openspec/specs/design/design-system.md` (light/dark colors with computed contrast, type, spacing, radii, base components with states, accessibility rules) and ADRs in `openspec/specs/design/adr/`.
- E3b: `openspec/specs/design/wireframes/<screen>.md` (ASCII wireframe, R* marks, states: empty, loading, error, no permission) and `design/navigation.md`.

## Skills

- web-design-guidelines, building-components (and the Vercel skills the work-order names)

## Requirements

- R1: <requirement text> - screens: <names>.

## Applicable ADRs

- `design/adr/<NNN>-...`, `architecture/adr/<NNN>-...` (e.g. static export) - <what each forces>.

## Constraints

- Interview answers on brand, audience, accessibility level, dark mode, languages: `<verify-E1 path>`.
- Static export only (no SSR): screens cannot depend on a server render.

## Limits

- review_rounds: <effective value>   (source: profile | override | args)

## Acceptance criteria

- [ ] Every screen state exists; every R* with a UI effect appears on a wireframe.
- [ ] ADRs use `assets/adr.template.md` with `area: design`, status `proposed`.
- [ ] Result record valid; the independent reviewer is `ui-design-reviewer` (verify-E2b / verify-E3b).
