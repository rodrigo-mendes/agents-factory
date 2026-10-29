# Unverified items and risks

Back to [SKILL.md](../SKILL.md). Authoring date 2026-10-28. Register: **5 unverified (U1-U5)**,
**0 irresolvable (I)**, **3 medium confidence (M1-M3)** and **3 coverage limits (L1-L3)**, 11 items in
total. Tags `(unverified)` / `(medium confidence)` in other files of this skill point here by id.

## Contents

- Version-lifetime risk
- Unverified (U1-U5)
- Irresolvable from documentation (I)
- Medium confidence (M1-M3)
- Coverage limits (L1-L3)
- Tag to register mapping
- Source Bibliography

## Version-lifetime risk

| Risk | Effect | Mitigation |
|---|---|---|
| Protocol v1 of `coordinating-agent-handoffs` is being widened (deploy-report and diagnosis-report accept the four outcomes) | The profile no longer carries a `values:` override; a script older than the widened protocol rejects `partial` / `needs-input` | Run the Verification Loop with the installed `handoff-core`; update the package pair together |
| The agent definitions change (the observability and debugger agents are being aligned) | `agent-alignment.md` rows go stale | Re-read the agent files and re-check rows A5, A6, A10 |
| OpenSpec 1.15.0 formats; no 1.15.1+ as of 2026-10-28 | `handoff/` and ADR placement may need a change | See the OpenSpec skill and U2, U3 |
| Claude Code hook and subagent write-guard behaviour can change | The `Stop` hook note and the `result-*` naming reason go stale | Re-check the hooks reference before installing a hook (U1); keep `result-*` (U5) |

## Unverified

| Id | Item | Consequence | Mitigation |
|---|---|---|---|
| U1 | Claude Code `Stop` hook behaviour: that only exit code 2 blocks, whether stdout of a non-blocking hook is shown, and whether APM `hooks:` can ship it. Taken over from the generic drift-hook page, not re-verified. | A drift warning may be invisible or may block a turn | Keep `\|\| true`; install only after the user's confirmation; re-check the hooks reference first |
| U2 | `openspec archive` moving or ignoring a non-standard `handoff/` folder inside the change folder. | Records could be lost or fail validation at archive | Run `openspec validate` before; inspect the archived folder after the first archive; copy `handoff/` out first if in doubt |
| U3 | `openspec validate` tolerating `openspec/specs/architecture/adr/` (a folder without `spec.md`) under `specs/`. | Validation noise or failure | Test on a scratch project; fall back to `openspec/adr/` and edit `spec.adr_dir` in the profile |
| U4 | The profile and scripts ran only on fixtures (2026-10-28: `check_records.py` exit 0, `board.py` ended the E7 chain at `final-gate`), not yet on a real project change. | A rule interaction not covered by the fixtures could remain | Run the Verification Loop and the fixture commands of the SKILL before first use |
| U5 | A subagent write guard on file names starting with `report` (known from the user's decision and the generic protocol register U2, not from a dated official Anthropic page). | If the guard is narrower, `result-*` is still safe | Keep `result-*`; never test the guard |

The `role` frontmatter field is no longer an unverified item: `record-kinds.md` of `coordinating-agent-handoffs` documents it ("overrides the role derived from `from`"). The Stripe and observability routing built on it is covered by fixtures only (U4).

## Irresolvable from documentation (I)

Count: 0. No open question of this profile is unanswerable from the sources read.

## Medium confidence

| Id | Item | Consequence | Mitigation |
|---|---|---|---|
| M1 | The E7 acceptance chain of family rule 15 (observability result routed to the debugger, `verify-E7.md` from the debugger as the final-gate record) is the factory's design, not an external standard. | A debugger verdict could be accepted without an independent pillar check | The debugger's mode B repeats the pillar checks read-only; the user sees `status.md` before the final gate |
| M2 | Counting `build_attempts` as failed/partial **reports** while the integrator also counts attempts inside a run (A2 of agent alignment). | Up to `limit x limit` builds before the board alone escalates | Orchestrator escalates on `failed` with `build_attempts >=` the work-order limit |
| M3 | Default values (3/2/2/2/2, `coverage_min` 80) are design defaults awaiting the user's final choice at gate G1, not sourced thresholds. | Too tight or too loose for the project | Override per project or per run; they are parameters |

## Coverage limits (L)

Count: 3.

- L1: the profile does not enforce that `spec_impact` agrees with the `## Spec impact` text; the orchestrator checks by hand (agent alignment A1).
- L2: the profile does not enforce which agent of the `reviewer` role runs; the work-order type and the sequential Stripe order (advisor first, then `quarkus-code-reviewer` after `approved`) are orchestrator discipline.
- L3: `review_rounds` counts review records with outcome `changes-requested` per task, so a Stripe task consumes rounds from both reviewers; a project may raise `limits.review_rounds` through `openspec/handoff-profile.yaml`.

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) Stop hook warning behaviour | [openspec-integration.md](./openspec-integration.md) | U1 |
| (unverified) `handoff/` travels through archive | [openspec-integration.md](./openspec-integration.md) | U2 |
| (unverified) ADR folder under `openspec/specs/architecture/` | [openspec-integration.md](./openspec-integration.md) | U3 |
| (unverified) scripts on a real change (fixtures only so far) | SKILL.md Verification Loop | U4 |
| (unverified) `report*` name guard | SKILL.md Never Do (naming convention only); this register | U5 |
| (medium confidence) E7 chain: debugger verify as gate record | SKILL.md stage map; agent-alignment A6, A10 | M1 |
| (medium confidence) two build-attempt counters | agent-alignment A2 | M2 |
| (medium confidence) default limits and coverage | SKILL.md Limits | M3 |
| spec_impact consistency checked by hand | agent-alignment A1 | L1 |
| reviewer agent choice and Stripe sequence | agent-alignment (Routing details) | L2 |
| `review_rounds` counted per `changes-requested` record | agent-alignment (Routing details); wo-review template | L3 |

## Source Bibliography

- Shipped: skills `coordinating-agent-handoffs` (SKILL.md, `blueprints/profile-format.md`, `blueprints/record-kinds.md`, `blueprints/protocol.md`, `scripts/`) and `specifying-changes-with-openspec-v1-15`.
- Factory provenance, not shipped (read 2026-10-28; do not cite in runtime briefs). Generic protocol source: `packages/handoff-core/.apm/skills/coordinating-agent-handoffs/`.
- Agent definitions (factory provenance, not shipped): `packages/quarkus-aws/.apm/agents/`, `packages/aws-lambda/.apm/agents/`, `packages/aws-observability/.apm/agents/aws-observability.agent.md`, `packages/handoff-core/.apm/agents/spec-synchronizer.agent.md`, `packages/stripe-java/.apm/agents/`, `packages/aws-architect/.apm/agents/`, `packages/terraform/.apm/agents/aws-terraform-engineer.agent.md`.
- Family decisions (factory provenance, not shipped): `workspace/quarkus-aws-saas/_family_rules_v3.40.md`, rules 13-15 (dated 2026-10-28).
- No external web source: the profile is the factory's own design.
