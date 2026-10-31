# Unverified Register, Risks and Bibliography

Authored 2026-10-28. Back to [SKILL.md](../SKILL.md). This skill is a profile over repo-internal protocol
files, not over an external product; there is no AWS or OCI documentation page behind it, so no web
source is cited. Register: **1 unverified (U1)**, **0 irresolvable (I)**, **0 medium confidence (M)**,
**2 coverage limits (L1-L2)**. The statement that overwritten records make limit counters meaningless is
High: it is made by the generic protocol page cited below.

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable from documentation](#irresolvable-from-documentation-i)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- The profile follows protocol v1 of `coordinating-agent-handoffs`. A protocol v2 (new record kinds or
  profile keys) needs a new profile.
- The file-name rule (no name starting with `report`) reflects a Claude Code subagent write guard observed
  in this repo (U1); if that guard changes, the rule can be relaxed, not before.
- The roster is the OCI agent family of 2026-10-28; a new agent needs a roster row and a record name.

## Unverified items

Count: 1.

- U1 (unverified): a Claude Code subagent write guard on file names starting with `report`, observed in this
  repo and stated by the generic protocol register; no dated official page was read. Handling: keep the
  `result-<role>.md` naming convention; never test the guard; relax only if it is shown to be gone.

The earlier item about how the scripts count `build_attempts` and `deploy_cycles` is closed: the generic
protocol (skill `coordinating-agent-handoffs`, blueprint `protocol.md`) says "A profile may declare that a
family overwrites records per cycle (OCI legacy); then counters that depend on history (limits) are not
meaningful"; this family overwrites records per cycle.

## Irresolvable from documentation (I)

Count: 0. No open question of this profile is unanswerable from the sources read.

## Medium-confidence items

Count: 0.

## Coverage limits

| ID | Limit |
|---|---|
| L1 | The generic skill, its scripts and `profile-format.md` live in another package and are referenced by skill name |
| L2 | No live run of an OCI agent chain; the scenarios are static expectations for `skill-evaluator` |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| Limit counters are not cycle counts (High, cited from the generic protocol; no tag needed) | SKILL.md Ask First and Never Do; never-do F3; handoff-protocol rule 8; evaluation scenario 3 | none (cited, High) |
| `(unverified)` subagent write guard on `report*` names | SKILL.md Never Do and Quick Reference; never-do F1; handoff-protocol file-name rule; result template | U1 |
| Generic skill read by name only | SKILL.md Version Context | L1 |
| Scenarios are static, no live run | evaluation-scenarios.md | L2 |

## Source Bibliography

Repo-internal inputs, read 2026-10-28; none is an external page.

| ID | Input | Used for |
|---|---|---|
| In1 | `assets/handoff-profile.yaml` of this skill | roles, record names, limits, `next:` rules |
| In2 | `blueprints/handoff-protocol.md` of this skill | roster, layout, handshake, lifecycle |
| In3 | skill `coordinating-agent-handoffs` (protocol v1): `blueprints/protocol.md`, `blueprints/record-kinds.md`, `scripts/check_records.py` | record kinds, overwritten-records statement, createdAt check, scripts |
| In4 | factory provenance, not shipped: the validation reports of this family under `workspace/` | the findings behind this version |
