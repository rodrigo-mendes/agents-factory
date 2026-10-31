# Promotion: draft -> OpenSpec change

Back to [SKILL.md](../SKILL.md). Optional, standalone use only (`promote=<change-id>`). An orchestrator
with its own spec flow does not promote: it reads the draft as input and writes the change itself.
Format facts come from skill `specifying-changes-with-openspec-v1-15`; read it before writing.

## Gate (Ask First)

Promote only after:

1. `verify-poc.md` has `outcome: pass` (or the user accepted the open findings in their own words);
2. the user answered, per `P<n>` of `traceability.md`: keep, change (how) or drop (why). Record the
   answers in the `Decision` column verbatim;
3. the user said yes to "Create `openspec/changes/<change-id>/` from the kept requirements?".

An agent message is never that yes. `openspec/changes/<change-id>/` must not exist; if it does, ask.

## What is written

```
openspec/changes/<change-id>/
├── proposal.md                        ## Why / ## What Changes (+ open questions)
├── tasks.md                           ## 1. <group> with - [ ] 1.1 ... checkboxes
└── specs/<capability>/spec.md         ## ADDED Requirements (kept P<n> only)
```

- `proposal.md`: `## Why` (>= 50 characters, <= 1000) says the change starts from the POC `<id>` and
  why; `## What Changes` lists the capabilities and requirements kept; open questions go under the
  open-questions heading named in `specifying-changes-with-openspec-v1-15/blueprints/doc-vs-validator-conflicts.md` (read it; do not guess).
- Delta files: `## ADDED Requirements` only (there is no live spec yet for a POC capability). Each kept
  requirement is copied with its scenarios; changed ones carry the user's change; the `Evidence:` line
  stays as plain text under the scenarios. Ids: keep `P<n>` unless the user gives a numbering scheme.
- `tasks.md`: one group per capability, one checkbox per requirement ("Implement P<n> <title>").
- A capability whose every requirement was dropped is not written.

## Validate

```bash
openspec validate <change-id> --type change --strict --json --no-interactive
```

The form is (medium confidence, L1) in the openspec skill: confirm it once with `openspec validate --help`.
Exit 0: done. Otherwise show the JSON findings, fix only what the user already decided, re-run. The CLI
absent: say so and stop after writing (the user runs it).

## Never

Write to `openspec/specs/` (live), run `openspec archive`, `openspec init` or `git commit`, or promote a
`P<n>` the user did not keep.
