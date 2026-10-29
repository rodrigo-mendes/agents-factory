---
kind: spec-delta
id: spec-delta-<nn>
from: <sync-agent>
to: <orchestrator-agent>
change: <change-id>          # profile scope_key: `change` or `capability`
refs: [<report-id-that-diverged>]
requirements: [R1]
status: proposed             # proposed | accepted | rejected | revise
createdAt: <ISO 8601 UTC>
---

<!-- Delta sections follow the OpenSpec format; see ../../specifying-changes-with-openspec-v1-15/SKILL.md.
     Keep only the sections that apply. A MODIFIED requirement repeats the COMPLETE requirement
     (sentence + every scenario), not a diff. Target file once accepted:
     <change dir>/specs/<capability>/spec.md -->

## MODIFIED Requirements

### Requirement: <existing requirement header>
The system SHALL <complete requirement sentence>.

#### Scenario: <name>
- **WHEN** <condition>
- **THEN** <expected result>

## ADDED Requirements

### Requirement: <new requirement header>
The system SHALL <requirement sentence>.

#### Scenario: <name>
- **WHEN** <condition>
- **THEN** <expected result>

## Files

- `<every drifted path this delta covers, one per line>`

## Questions

- <Open question for the user, e.g. "Is limit 50 a business rule or only technical?">  Write "none" when there are no questions.
