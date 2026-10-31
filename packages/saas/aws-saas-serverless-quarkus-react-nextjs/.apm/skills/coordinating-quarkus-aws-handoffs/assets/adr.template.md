---
id: <NNN>
title: <title>
area: architecture               # architecture | design | infrastructure (decides the folder)
status: proposed                 # proposed | accepted | superseded by <NNN>; accepted with the E2 approval of the user
author: <solution-architect | ui-ux-designer | aws-infrastructure-architect>
reviewer: <solution-architecture-reviewer | ui-design-reviewer | aws-architect-reviewer>
date: <YYYY-MM-DD>
requirements: [R1]               # requirements affected, or "architecture-wide"
---

# ADR <NNN>: <title>

<!-- Folder by area, numbering per folder (each folder starts at 001):
       architecture   -> openspec/specs/architecture/adr/<NNN>-<title>.md   (author solution-architect)
       design         -> openspec/specs/design/adr/<NNN>-<title>.md         (author ui-ux-designer)
       infrastructure -> openspec/specs/infrastructure/adr/<NNN>-<title>.md (author aws-infrastructure-architect)
     Cite an ADR with its folder: `design/adr/002`. A number is never reused.
     Status moves proposed -> accepted; an accepted ADR is never edited, it is superseded.
     Not a handoff record: check_records.py does not read these folders; the E2 verifier checks the fields.
     Reviewers of E6 treat a violation of an ADR of ANY of the three folders as HIGH. -->

## Context

The problem and the forces (NFR targets with number + unit, constraints from the interview), with links to the requirements `R*` it affects.

## Alternatives

At least two. Each states why it was rejected and cites the skill that supports the argument. Mark the chosen one.

1. <alternative A> - rejected because <reason> (skill: `<skill-name>`).
2. <alternative B> - chosen / rejected because <reason> (skill: `<skill-name>`).

## Decision

One sentence: what was chosen.

## Consequences

- Positive: <...>
- Negative: <...>
- Now forbidden (becomes a reviewer check in I7): <e.g. "no Aurora; no table without PK=TENANT#id"; design: "no component outside the design system">.

## Sources

Skills and official pages used. No source -> mark `(unverified)`.
