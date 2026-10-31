# E3 - Functional spec (what the system does)

Back to [SKILL.md](../SKILL.md). Format and CLI facts belong to skill `specifying-changes-with-openspec-v1-15`; read it (SKILL.md and
`blueprints/delta-format-and-archive.md`) before writing. Do not restate them from memory.

## Where

| Item | Path |
|---|---|
| Live functional spec | `openspec/specs/<capability>/spec.md` (one per capability, e.g. `items`, `billing`) |
| Change deltas | `openspec/changes/<id>/specs/<capability>/spec.md` |
| Proposal / design index / tasks | `openspec/changes/<id>/{proposal.md,design.md,tasks.md}` (`design.md` is the index of `design/<flow>.md`, see [E4](e4-e5-design-and-tasks.md); layout in rule `openspec-project-layout`) |

New capabilities use `## ADDED Requirements`; changes use `## MODIFIED Requirements` (the **entire** requirement block with all scenarios);
removals carry `**Reason**` and `**Migration**`; renames use FROM/TO. Scenarios are exactly `#### Scenario:` with `- **WHEN**` / `- **THEN**` bullets
(wrong heading depth fails silently, per the openspec skill). Where docs and validator conflict, follow the openspec skill's
`doc-vs-validator-conflicts` blueprint.

## Authoring (manager, from B2-B4, B8, B9)

1. One requirement per behaviour, header `### Requirement: R<n> <title>`, text with `SHALL`/`MUST`. IDs are **project-global, increasing, never reused**
   (convention of this skill; recorded in `requirements:` of every record).
2. Each requirement: >= 1 happy scenario **and** >= 1 negative scenario (wrong tenant, missing role, invalid input, limit reached).
3. Each requirement linked to the architecture component that serves it (in E4) and consistent with the accepted ADRs of the three folders (`architecture/adr`, `design/adr`, `infrastructure/adr`); if a requirement
   contradicts an ADR, stop: the user decides via a new ADR in the owning E2 front.
4. Actors from B2; business rules from B4 as requirements, not prose.
5. No technology in functional requirements (no "DynamoDB", "Lambda", "Next.js"): that is E2. UI behaviour is stated as user-visible behaviour; screens come in E3b.

## Acceptance (E3 accepted)

All of:

1. Every requirement has an ID and `SHALL`/`MUST`.
2. Every requirement has >= 1 happy and >= 1 negative scenario.
3. Every requirement maps to an E2a component and has no ADR conflict (any of the three folders).
4. No blocking open question.
5. `openspec validate <id> --type change --strict --json --no-interactive` exits 0 (read its JSON; if it disagrees with the docs, the validator wins; cite both).
6. `spec-synchronizer` (mode A) returns `pass`: testability, gaps, contradictions, ADR conflicts. Saved as `verify-E3.md`.
7. The user approves (verbatim, `gate=E3`).

Verifier is never the author: I write, `spec-synchronizer` + validator check, the user approves. `check_records.py` checks the record format of `verify-E3.md`.

## When review fails

Show the findings with file:line. Fix the spec yourself (only for the items the user already decided) or ask the missing question in a new interview round (max 10).
Never edit scenarios to make a review pass without the user's confirmation of the behaviour.

## Hand-off to design

With `verify-E2a`, `verify-E2b`, `verify-E2c` and `verify-E3` all `pass` and the user approvals of E2 and E3 in `## Approvals`: a change with UI goes to [E3b wireframes](e3b-ui-design.md) first (gate E3b), then to [E4-E5](e4-e5-design-and-tasks.md); a change without UI goes straight to E4. Before that, no construction work-order may exist.
