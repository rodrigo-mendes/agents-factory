# E3 - Functional spec (what the system does)

Back to [SKILL.md](../SKILL.md). Format and CLI facts belong to skill `specifying-changes-with-openspec-v1-15`; read it (SKILL.md and
`blueprints/delta-format-and-archive.md`) before writing. Do not restate them from memory.

## Where

| Item | Path |
|---|---|
| Live functional spec | `openspec/specs/<capability>/spec.md` (one per capability, e.g. `items`, `billing`) |
| Change deltas | `openspec/changes/<id>/specs/<capability>/spec.md` |
| Proposal / design / tasks | `openspec/changes/<id>/{proposal.md,design.md,tasks.md}` |

New capabilities use `## ADDED Requirements`; changes use `## MODIFIED Requirements` (the **entire** requirement block with all scenarios);
removals carry `**Reason**` and `**Migration**`; renames use FROM/TO. Scenarios are exactly `#### Scenario:` with `- **WHEN**` / `- **THEN**` bullets
(wrong heading depth fails silently, per the openspec skill). Where docs and validator conflict, follow the openspec skill's
`doc-vs-validator-conflicts` blueprint.

## Authoring (orchestrator, from B2-B4 and B8)

1. One requirement per behaviour, header `### Requirement: R<n> <title>`, text with `SHALL`/`MUST`. IDs are **project-global, increasing, never reused**
   (convention of this skill; recorded in `requirements:` of every record).
2. Each requirement: >= 1 happy scenario **and** >= 1 negative scenario (wrong tenant, missing role, invalid input, limit reached).
3. Each requirement linked to the architecture component that serves it (in E4) and consistent with the accepted ADRs; if a requirement
   contradicts an ADR, stop: the user decides via a new ADR in E2.
4. Actors from B2; business rules from B4 as requirements, not prose.
5. No technology in functional requirements (no "DynamoDB", "Lambda"): that is E2.

## Acceptance (E3 accepted)

All of:

1. Every requirement has an ID and `SHALL`/`MUST`.
2. Every requirement has >= 1 happy and >= 1 negative scenario.
3. Every requirement maps to an E2 component and has no ADR conflict.
4. No blocking open question.
5. `openspec validate <id> --type change --strict --json --no-interactive` exits 0 (read its JSON; if it disagrees with the docs, the validator wins; cite both).
6. `spec-synchronizer` (mode A) returns `pass`: testability, gaps, contradictions, ADR conflicts. Saved as `verify-E3.md`.
7. The user approves (verbatim, `gate=E3`).

Verifier is never the author: I write, `spec-synchronizer` + validator check, the user approves. `check_records.py` checks the record format of `verify-E3.md`.

## When review fails

Show the findings with file:line. Fix the spec yourself (only for the items the user already decided) or ask the missing question in a new interview round (max 10).
Never edit scenarios to make a review pass without the user's confirmation of the behaviour.

## Hand-off to design

With `verify-E2` and `verify-E3` both `pass` and both user approvals in `## Approvals`, proceed to [E4-E5](e4-e5-design-and-tasks.md). Before that, no work-order may exist.
