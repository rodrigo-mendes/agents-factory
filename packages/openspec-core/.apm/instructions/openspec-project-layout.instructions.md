---
name: openspec-project-layout
description: "Layout of openspec/ for projects that also keep architecture, design and infrastructure decisions: what is official OpenSpec 1.15 and what is a factory convention, who writes and reviews each folder, per-folder ADR numbering and status. Use when creating or editing files under openspec/."
applyTo: "openspec/**"
---

# openspec/ project layout

The skill `specifying-changes-with-openspec-v1-15` is locked to the official OpenSpec 1.15 and
states only sourced facts. This rule adds the **factory convention** on top of it and keeps the two
separate. Agents and orchestrators point here instead of repeating the layout.

## Official OpenSpec 1.15 (source: the skill above)
- `openspec/specs/<capability>/spec.md`: the current truth, one folder per capability.
- `openspec/changes/<id>/` with `proposal.md`, `design.md`, `tasks.md` and
  `specs/<capability>/spec.md` (deltas ADDED, MODIFIED, REMOVED, RENAMED).
- `openspec archive <id> --yes` applies the deltas to `specs/` and moves the change to
  `openspec/changes/archive/`.

## Factory convention (not part of OpenSpec 1.15)
```
openspec/
├── specs/
│   ├── <capability>/spec.md      functional requirements R* (official)
│   ├── architecture/             spec.md, contracts/*.md, adr/NNN-*.md
│   ├── design/                   design-system.md, navigation.md, wireframes/*.md, adr/NNN-*.md
│   └── infrastructure/           spec.md, adr/NNN-*.md
└── changes/<id>/
    ├── proposal.md  tasks.md  specs/<capability>/spec.md   (official)
    ├── design.md                 official file, used as INDEX of the technical designs + traceability
    ├── design/<flow>.md          one technical design per flow (convention)
    ├── infra-design.md           infrastructure of the change (convention)
    └── handoff/                  work-orders, results, reviews, verifies, status.md (convention)
```
- `design.md` is the index; each `design/<flow>.md` has 11 sections and owns its R* (an R* has exactly
  one owner design). Contracts live only in `specs/architecture/contracts/`; designs link to them.
- `openspec validate` may treat `design/` and `infrastructure/` as capabilities or object to extra
  files `(unverified)`. If it does, give each folder a minimal `spec.md` in OpenSpec format and note it
  in the change; do not delete the convention.

## Who writes and reviews
| Part | Author | Reviewer |
|---|---|---|
| `specs/<capability>/spec.md` (via deltas) | project manager (orchestrator) | `spec-synchronizer` |
| `specs/architecture/**` | `solution-architect` | `solution-architecture-reviewer` |
| `specs/design/**` | `ui-ux-designer` | `ui-design-reviewer` |
| `specs/infrastructure/**` | `aws-infrastructure-architect` | `aws-architect-reviewer` |
| `changes/<id>/design.md`, `design/*.md` | `solution-architect` | `solution-architecture-reviewer` |
| `changes/<id>/infra-design.md` | `aws-infrastructure-architect` | `aws-architect-reviewer` |
| `changes/<id>/tasks.md` | project manager | `spec-synchronizer` |

The author never reviews. A designer without a Write tool returns content inline and the manager saves it.

## ADRs
- One `adr/` folder per area (`architecture`, `design`, `infrastructure`), numbering from `001` **per
  folder**. Cite by path: `design/adr/002`.
- Front matter: `id`, `title`, `area`, `status`, `author`, `reviewer`; sections Context,
  Alternatives (>= 2), Decision, Consequences, Sources.
- Status flow: `proposed` -> `accepted` (only after the user approves E2; the manager records it) ->
  `superseded` by a new ADR. Authors never set `accepted`.
- A violation of any accepted ADR, in any folder, is HIGH in reviews.

## Always Do
- Keep the official files in OpenSpec format and the convention files outside the delta mechanism.
- Link instead of copying (contracts, ADRs).

## Ask First
- An ADR that conflicts with an accepted ADR in another folder: ask which one is superseded.
- `openspec validate` rejecting a convention folder or extra file: ask before moving or renaming it (the fallback is a minimal `spec.md` per folder).

## Never Do
- Present the convention folders as official OpenSpec in docs or agent text.
- Number ADRs across folders or edit an `accepted` ADR in place; supersede it.
