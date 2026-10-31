# E3b - Wireframes

Back to [SKILL.md](../SKILL.md). Runs after E3 is accepted and before E4. Author `ui-ux-designer` (sonnet), reviewer `ui-design-reviewer` (sonnet), gate = the user. The designer returns the file contents inline (it only reads); I save them under `openspec/specs/design/` and as `result-NN-designer.md`.

## When

Any change that creates or alters a screen (requirements `R*` with UI). A change with no UI skips E3b: write the reason in `status.md` and the E3b gate is not asked. Entry: `verify-E2b` pass and `verify-E3` pass with both approvals recorded.

## Work-order (`wo-NN-designer.md`, mode wireframes)

Inputs: the E3 requirements with scenarios, `design/design-system.md`, `design/adr/`, the contracts (`architecture/contracts/`) the screens consume, B9-B11 playback. Sections Functionality (what the user gains) and Diagram (journey between screens) are mandatory like in every construction-type work-order.
Skills: `building-components`, `web-design-guidelines`, `composition-patterns`. Launch with `model: "sonnet"`.

## Output format

| File | Content |
|---|---|
| `design/wireframes/<screen>.md` | one screen per file, ASCII layout using only components of the design system; the `R*` of each element next to it; the 4 states: empty, loading, error, no permission (plus the dark-mode note if the theming ADR requires it) |
| `design/navigation.md` | screen map: entry points, transitions, redirects (401 -> login, 403 -> no-permission screen), no dead ends |

Example of the layout style:

```
┌────────────────────────────────────┐
│ [Logo]        Items      [Avatar v] │
├────────────────────────────────────┤
│ [Search........]  [+ New item]  R2 │
│ ┌────────┬──────────┬────────────┐ │
│ │ Name   │ Category │ Actions    │ │ R1
│ └────────┴──────────┴────────────┘ │
└────────────────────────────────────┘
states: empty · loading · error · no permission
```

## Review and acceptance

`ui-design-reviewer` checks: every `R*` with UI appears on a screen; only design-system components; the 4 states on every screen; navigation without dead ends; contrast and focus per the design system. It returns `verify-E3b` (`pass|fail`, Criteria, Evidence) inline; I save it.
On `fail`: new `wo-MM-designer.md` with the findings (the old work-order is set `done`/`cancelled`), re-review; `review_rounds`-style limits apply through the profile.
Gate: I show the screens and the navigation map to the user in plain words; the user approves (verbatim, `gate=E3b`). Front tasks in E6 cite the wireframe path in their work-order Inputs and the wireframe cut in Diagram.
