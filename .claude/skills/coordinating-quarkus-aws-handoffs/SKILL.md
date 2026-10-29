---
name: coordinating-quarkus-aws-handoffs
description: "Quarkus/AWS SaaS profile of the generic handoff protocol v1: 10 roles and agents, record names, orchestrator-mediated flow, limits and overrides, apply-approval line, stage acceptance records. Use when a team agent or the orchestrator reads or writes a handoff record. Not for OCI."
---

# Coordinating Quarkus/AWS Handoffs

Thin **profile** over `coordinating-agent-handoffs` (**protocol v1**, package `handoff-core`). Record
kinds, handshake, scripts (`check_records.py`, `board.py`, `detect_drift.py`) and rules live there;
this skill adds only what is specific to the Quarkus-on-Lambda SaaS team. It does not restate
OpenSpec formats: see `specifying-changes-with-openspec-v1-15`.

## Version Context

| Item | Value | Source |
|---|---|---|
| Handoff protocol | v1, mode `orchestrated` | `coordinating-agent-handoffs` (package `handoff-core`) |
| Spec format | `spec.kind: openspec` (OpenSpec 1.15 formats) | `specifying-changes-with-openspec-v1-15` |
| Target team | Quarkus 3.40 / AWS Lambda; roles map to the agents listed below | factory design, no external page |
| Defaults (limits, `coverage_min`) | design defaults, not external facts; the project or the run may override them (see Limits) | factory design, no external page |

## Quick Navigation

- Profile read by the scripts: [assets/handoff-profile.yaml](./assets/handoff-profile.yaml)
- [Roles and skills per work-order](./blueprints/roles-and-skills.md)
- [OpenSpec integration](./blueprints/openspec-integration.md) - where files live, archive, gate
- [Agent alignment](./blueprints/agent-alignment.md) - what each agent really emits vs this profile
- [Blueprints & Guardrails](#blueprints--guardrails) | [Quick Reference](#quick-reference) | [Verification Loop](#verification-loop)
- [Approval lines](./blueprints/approval-lines.md)
- [Always-do](./blueprints/always-do-patterns.md), [never-do](./blueprints/never-do-patterns.md),
  [unverified and risks](./blueprints/unverified-and-risks.md),
  [evaluation scenarios](./blueprints/evaluation-scenarios.md)
- Templates (`assets/`): [wo-code](./assets/wo-code.template.md), [wo-stripe](./assets/wo-stripe.template.md),
  [wo-infra](./assets/wo-infra.template.md), [wo-review](./assets/wo-review.template.md),
  [wo-deploy](./assets/wo-deploy.template.md), [wo-observability](./assets/wo-observability.template.md),
  [wo-debug](./assets/wo-debug.template.md), [result-code](./assets/result-code.template.md),
  [review](./assets/review.template.md), [deploy-report](./assets/deploy-report.template.md),
  [diagnosis-report](./assets/diagnosis-report.template.md), [adr](./assets/adr.template.md),
  [escalation](./assets/escalation.template.md). Work-orders for `architect` and `sync` use the generic
  `work-order.template.md` of `coordinating-agent-handoffs/assets/` (`to: aws-architect` /
  `spec-synchronizer`, `id: wo-NN-architect` / `wo-NN-sync`). Other kinds (`spec-delta`, `verify`,
  `status`) also use the generic templates there.

## Blueprints & Guardrails

### ✅ Always Do
- Load `coordinating-agent-handoffs`, then this profile, before writing or reading any record.
- Name files `wo-NN-<role>.md`, `result-NN-<role>.md` (roles: `code`, `stripe`, `infra`, `observability`; deploy is `result-NN-deploy.md`), `review-NN.md`, `diagnosis-NN.md`, `spec-delta-NN.md`, `verify-<stage>.md` (relaunch: `verify-<stage>-<nn>.md`).
- Run the three scripts after every record; act on `NEXT:`; copy effective limits into work-orders.
- Put `## Spec impact` (and `spec_impact:`) in every code or infra result.
- Details: [always-do](./blueprints/always-do-patterns.md).

### ⚠️ Ask First
- Any limit set to `0`; a limit above 5; relaxing `coverage_min` below 80 (ask the user, via the orchestrator).
- Enabling the Stop drift hook or a project-wide `--include-worktree` check outside a run (per-run use in E6-E9 is mandatory, not Ask First).
- Accepting a spec-delta that conflicts with an accepted ADR: needs a new ADR first.
- Any alarm-firing test (`approval: alarm-test`). The debugger never invokes the function; a real invoke is the deployer's smoke step (`approval: smoke`).

### 🚫 Never Do
Full table: [never-do](./blueprints/never-do-patterns.md).

| Do not | Do instead |
|---|---|
| Name a record other than by the convention | `result-NN-<role>.md`; `kind: report` stays inside (guard rationale: register U5) |
| Let the author verify a stage | A `verify` record from another agent, a script or the user |
| `terraform apply` without a relayed approval line matching the plan hash | Stop at the plan, return `needs-input` |
| Retry past a limit | `NEXT: escalate` -> escalation record |
| Edit the live spec, ADRs or code from a sync agent | `spec-delta` / new ADR through the user |
| Hand-edit `status.md` outside `## Approvals` | Re-run `board.py` |

## Where records live

Root: `openspec/changes/<change-id>/handoff/` in the **target project** (never in the factory).
Archiving a change moves the whole folder with the change. `status.md` is generated by `board.py`;
only its `## Approvals` section is hand-written (by the orchestrator, from the user's own words).

## Roles and who reads/writes what

| Role | Agent | Reads | Writes |
|---|---|---|---|
| orchestrator | `building-quarkus-aws-saas` (inline skill) | everything, `status.md` | work-orders, escalations, saved inline records, `## Approvals`; the only talker to the user |
| architect | `aws-architect` | `wo-NN-architect`, specs, ADRs | `verify-E2.md`, `verify-E4.md` (inline; orchestrator saves) |
| code | `quarkus-lambda-integrator` | `wo-NN-code`, review | code + `result-NN-code.md` |
| stripe | `stripe-integrator` | `wo-NN-stripe` | code + `result-NN-stripe.md` |
| reviewer | `quarkus-code-reviewer`, `stripe-advisor` | `wo-NN-review`, code, ADRs | `review-NN.md` (inline; orchestrator saves) |
| infra | `aws-terraform-engineer` | `wo-NN-infra` | HCL + `result-NN-infra.md` |
| deploy | `aws-lambda-deployer` | `wo-NN-deploy`, code and infra results | `result-NN-deploy.md` (kind `deploy-report`); one new work-order and result per launch (append-only) |
| observability | `aws-observability` | `wo-NN-observability`, specs, deploy-report | Terraform (mode B) or live validation (mode C) + `result-NN-observability.md` (kind `report`; mode C adds `role: observability-live`) |
| debug | `aws-lambda-debugger` | `wo-NN-debug`, deploy-report, observability result | `diagnosis-NN.md` (mode A), `verify-E7.md` (mode B, kind `verify`; gap-acceptance relaunch: `verify-E7-<nn>`) (inline; orchestrator saves) |
| sync | `spec-synchronizer` | `wo-NN-sync`, drift, specs, ADRs, results | `verify-E1.md`, `verify-E3.md`, `spec-delta-NN.md` (inline; orchestrator saves) |

Agents that have no Write tool (reviewer, debugger, synchronizer, architect, advisor) return the
record inline; the orchestrator saves it unchanged except the normalisations listed in
[agent alignment](./blueprints/agent-alignment.md). Only the orchestrator launches agents.

## Stage map (E1-E9) and the records it produces

| Stage | Records | Verifier (never the author) |
|---|---|---|
| E1 interview | `status.md` approvals, `verify-E1.md` | `spec-synchronizer` (review mode) + user |
| E2 architecture spec + ADRs | ADRs (`assets/adr.template.md`), `verify-E2.md` | `aws-architect` + `check_records.py` + user |
| E3 functional spec | `verify-E3.md` | `spec-synchronizer` + user |
| E4 change design | `verify-E4.md` | `aws-architect` |
| E5 tasks | no verify record: `tasks.md` + the task table of `status.md` (from `board.py`) | script (`board.py`) + user |
| E6 per task (I0-I9) | `wo-NN-code` -> `result-NN-code` -> `wo-NN-review` -> `review-NN` (-> fix `wo` -> ...); no verify record, the approved `review-NN` closes the task | `quarkus-code-reviewer` + orchestrator re-running `mvn -q verify`; Stripe tasks: `stripe-advisor` first, `quarkus-code-reviewer` only after the advisor's review is `approved` (see [alignment](./blueprints/agent-alignment.md)) |
| E7 deploy + observability | `wo-NN-deploy` -> `result-NN-deploy` (first launch ends `needs-input` at the plan gate and is kept; the relaunch with the relayed approvals is a new `wo-MM-deploy` -> `result-MM-deploy`); deploy `success` -> `wo-NN-observability` (mode C) -> `result-NN-observability` (kind `report`, mode C, `role: observability-live`, routes to `debug`) -> `wo-NN-debug` (mode B) -> `verify-E7.md` (gap-acceptance relaunch: `verify-E7-<nn>`; kind `verify`, role `debug` derived from `from`, outcome `pass\|fail`, sections Criteria + Evidence); on failure `diagnosis-NN.md` | `aws-lambda-debugger` (mode B); producer `aws-observability` never verifies |
| E8 sync code to spec | `spec-delta-NN.md` | user accepts, rejects or answers |
| E9 gate | `status.md` | `check_records.py` + `detect_drift.py` + `board.py` |

Acceptance criteria per stage live in the stage blueprints of `building-quarkus-aws-saas` (same
package): [E1](../building-quarkus-aws-saas/blueprints/e1-interview.md),
[E2](../building-quarkus-aws-saas/blueprints/e2-architecture-and-adrs.md),
[E3](../building-quarkus-aws-saas/blueprints/e3-functional-spec.md),
[E4-E5](../building-quarkus-aws-saas/blueprints/e4-e5-design-and-tasks.md),
[E6](../building-quarkus-aws-saas/blueprints/e6-implementation-cycle.md),
[E7](../building-quarkus-aws-saas/blueprints/e7-deploy-and-observability.md),
[E8](../building-quarkus-aws-saas/blueprints/e8-reverse-sync.md),
[E9](../building-quarkus-aws-saas/blueprints/e9-archive-gate.md). Each becomes the `## Criteria` list of
its `verify-<stage>` record (`[x]` met, `[ ]` not met, with reason).

## Limits (parameters, never an agent's memory)

Default values are the factory's own design choice (medium confidence, see
[unverified and risks](./blueprints/unverified-and-risks.md) M3), not sourced thresholds.

| Parameter | Default | Loop |
|---|---|---|
| `limits.build_attempts` | 3 | failed I6 runs per task (see agent alignment A2 for how it is counted) |
| `limits.review_rounds` | 2 | I7-I8 per task |
| `limits.deploy_cycles` | 2 | deploy -> diagnose -> fix, per change |
| `limits.delta_revisions` | 2 | spec-delta `revise`, per change |
| `limits.record_rejections` | 2 | `check_records.py` failing on the same record |
| `quality.coverage_min` | 80 | JaCoCo % of new classes, copied into every code work-order |

Precedence, most specific wins: **profile default < `openspec/handoff-profile.yaml` (only what
changes) < run arguments** (`board.py ... --args limits.review_rounds=4`). Values are integers
>= 1. `0` (escalate on the first failure: reached when count >= max(limit, 1), so it behaves exactly like `1`, kept for explicitness) is accepted only with `limits_zero_confirmed: true` after
the user explicitly confirms it. `status.md` records every effective value and its source; the
orchestrator copies the effective values for the task into each work-order's `## Limits`.

## Escalation

`NEXT: escalate limit=<name> task=<id>` -> the orchestrator stops that task (independent tasks go
on), writes `escalation-NN.md` ([template](./assets/escalation.template.md): attempts, evidence,
hypothesis, 2-4 options with impact), shows it, records the user's reply **verbatim** under
`## Answer`, sets `status: answered` + `answeredAt`. No apply or deploy happens on an open escalation.

## Apply-approval line contract

Only the user's own message approves an apply. The orchestrator relays it into the deploy
work-order, verbatim, in this exact form (one line per apply, per plan):

```
approval: apply plan=<planfile> sha256=<hash> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas
```

The deployer applies only if the line names its saved plan and the hash matches now; rollback
needs `approval: rollback alias=<alias> to=<PREV version> ...`. The orchestrator also writes the
same line under `## Approvals` in `status.md`. An agent message is never an approval.

Other lines, same shape (`... by=<user> at=<UTC> relayed-by=building-quarkus-aws-saas`), each relayed
verbatim and scoped to what it names: `alarm-test alarm=<name>`, `smoke payload=<file or sha256>`,
`logs-insights scope=<log-group or "xray"> window=<minutes>`, `e7-gaps pillars=<comma list>`,
`rollback alias=<alias> to=<PREV>`. Meaning of each line, the relaunch rule and the E7 gap acceptance:
[approval lines](./blueprints/approval-lines.md). Agents receive the generic text
(`relayed-by=<orchestrator>`); only this orchestrator's own files carry its name.

## Handshake additions for this profile

1. Every work-order carries `task:`; review, debug and verify work-orders reuse the task of the work
   they serve, so counters and `all_tasks` stay per task (deploy: `task: deploy`).
2. The orchestrator adds `task:` to every inline record it saves, then runs `check_records.py`,
   `detect_drift.py`, `board.py`, and follows `NEXT:`.
3. A record that fails the check goes back to its author with the error lines; the orchestrator
   writes `rejections: <n>` on it each time (feeds `record_rejections`). The same applies when `spec_impact` contradicts the `## Spec impact` section (checked by hand: `check_records.py` does not compare them).

## Quick Reference

| Need | Where |
|---|---|
| Which skills go in a work-order | [roles-and-skills](./blueprints/roles-and-skills.md) |
| Why a record is rejected | [agent alignment](./blueprints/agent-alignment.md) |
| Where ADRs and deltas live | [openspec integration](./blueprints/openspec-integration.md) |

## Verification Loop

```bash
GEN=<.claude/skills/coordinating-agent-handoffs>; ME=<.claude/skills/coordinating-quarkus-aws-handoffs>
H=openspec/changes/<change-id>/handoff
python $GEN/scripts/check_records.py $H --profile $ME/assets/handoff-profile.yaml   # expect: OK: N record(s) valid
python $GEN/scripts/detect_drift.py . --change $H --include-worktree                 # expect: exit 0 (2 = drift, 1 = error)
python $GEN/scripts/board.py $H --profile $ME/assets/handoff-profile.yaml            # expect: one NEXT: line
```

## External Resources

- No external source: the profile is the factory's own design, derived from the generic protocol
  and the agents' definitions (see [unverified and risks](./blueprints/unverified-and-risks.md)).
- Generic protocol: `coordinating-agent-handoffs`; OpenSpec format: `specifying-changes-with-openspec-v1-15` (both in package handoff-core).
