---
name: coordinating-quarkus-aws-handoffs
description: "Quarkus/AWS + Next.js SaaS profile of the generic handoff protocol v1: 20 roles and agents, record names, orchestrator-mediated flow, limits, user gates (merge, bootstrap, prod), pipeline records, stage verify records. Use when a team agent or the orchestrator reads or writes a handoff record. Not for OCI."
---

# Coordinating Quarkus/AWS Handoffs

Thin **profile** over `coordinating-agent-handoffs` (**protocol v1**, package `handoff-core`). Record
kinds, handshake, scripts (`check_records.py`, `board.py`, `detect_drift.py`) and rules live there;
this skill adds only what is specific to the Quarkus-on-Lambda + Next.js SaaS team. It does not restate
OpenSpec formats: see `specifying-changes-with-openspec-v1-15`.

## Version Context

| Item | Value | Source |
|---|---|---|
| Handoff protocol | v1, mode `orchestrated` | `coordinating-agent-handoffs` (package `handoff-core`) |
| Spec format | `spec.kind: openspec` (OpenSpec 1.15 formats) | `specifying-changes-with-openspec-v1-15` |
| Target team | Quarkus 3.40 / AWS Lambda back end, Next.js static export on S3 + CloudFront, deploy by GitHub Actions; roles map to the agents below | factory design, no external page |
| Defaults (limits, `coverage_min`) | design defaults, not external facts; the project or the run may override them (see Limits) | factory design, no external page |

## Quick Navigation

- Profile read by the scripts: [assets/handoff-profile.yaml](./assets/handoff-profile.yaml)
- [Roles and skills per work-order](./blueprints/roles-and-skills.md)
- [OpenSpec integration](./blueprints/openspec-integration.md) - where files live (3 ADR folders), archive, gate
- [Agent alignment](./blueprints/agent-alignment.md) - what each agent really emits vs this profile
- [Blueprints & Guardrails](#blueprints--guardrails) | [Quick Reference](#quick-reference) | [Verification Loop](#verification-loop)
- [User gates and approval lines](./blueprints/approval-lines.md)
- [Always-do](./blueprints/always-do-patterns.md), [never-do](./blueprints/never-do-patterns.md),
  [unverified and risks](./blueprints/unverified-and-risks.md),
  [evaluation scenarios](./blueprints/evaluation-scenarios.md)
- Templates (`assets/`), design: [wo-solution-architect](./assets/wo-solution-architect.template.md),
  [wo-infrastructure-architect](./assets/wo-infrastructure-architect.template.md), [wo-designer](./assets/wo-designer.template.md),
  [adr](./assets/adr.template.md) (`area:` architecture | design | infrastructure).
  Build: [wo-code](./assets/wo-code.template.md), [wo-ai](./assets/wo-ai.template.md), [wo-stripe](./assets/wo-stripe.template.md),
  [wo-frontend](./assets/wo-frontend.template.md), [wo-infra](./assets/wo-infra.template.md), [wo-cicd](./assets/wo-cicd.template.md),
  [wo-observability](./assets/wo-observability.template.md), [result-code](./assets/result-code.template.md) (shape of every author result).
  Review and live: [wo-review](./assets/wo-review.template.md) (variants table), [review](./assets/review.template.md),
  [result-pipeline](./assets/result-pipeline.template.md), [wo-debug](./assets/wo-debug.template.md),
  [diagnosis-report](./assets/diagnosis-report.template.md), [escalation](./assets/escalation.template.md).
  Work-orders for `solution-reviewer`, `infrastructure-reviewer`, `design-reviewer`, `site-verify` and `sync` use the generic
  `work-order.template.md` of `coordinating-agent-handoffs/assets/` (`to: <agent>`, `id: wo-NN-<role>`, `task: spec` or `E7`); the verifiers return
  `verify-<stage>` records (generic `verify.template.md`). Other kinds (`spec-delta`, `status`) also use the generic templates.
  The deploy work-order and deploy-report templates left this flow: the deploy is the GitHub Actions run (`aws-lambda-deployer` is not part of it).

## Blueprints & Guardrails

### ✅ Always Do
- Load `coordinating-agent-handoffs`, then this profile, before writing or reading any record.
- Name files `wo-NN-<role>.md`, `result-NN-<role>.md` (roles: `solution-architect`, `infrastructure-architect`, `designer`, `code`, `ai`, `stripe`, `frontend`, `infra`, `observability`, `cicd`; the pipeline is `result-NN-pipeline.md`), `review-NN.md`, `diagnosis-NN.md`, `spec-delta-NN.md`, `verify-<stage>.md` (relaunch: `verify-<stage>-<nn>.md`).
- Run the three scripts after every record; act on `NEXT:`; copy effective limits into work-orders.
- Put `## Spec impact` (and `spec_impact:`) in every author result (design, code, front, infra, cicd, pipeline).
- Put `role:` in the frontmatter where the table below says so; the board reads it before `from`.
- Details: [always-do](./blueprints/always-do-patterns.md).

### ⚠️ Ask First
- Any limit set to `0`; a limit above 5; relaxing `coverage_min` below 80 (ask the user, via the orchestrator).
- Enabling the Stop drift hook or a project-wide `--include-worktree` check outside a run (per-run use in E6-E9 is mandatory, not Ask First).
- Accepting a spec-delta that conflicts with an accepted ADR (of any of the three folders): needs a new ADR first.
- Any alarm-firing test (`approval: alarm-test`). The debugger never invokes the function; the real invoke is the `_smoke-test` job of the pipeline.
- A GitHub plan Free variant (weaker approval path) and the pre-release `integrating-quarkus-langchain4j-v1-15` (D1).

### 🚫 Never Do
Full table: [never-do](./blueprints/never-do-patterns.md).

| Do not | Do instead |
|---|---|
| Name a record other than by the convention | `result-NN-<role>.md`; `kind: report` stays inside (guard rationale: register U5) |
| Let the author verify a stage | A `verify` record from another agent, a script or the user |
| Launch any agent to apply, deploy, push, merge or trigger a workflow | The pipeline deploys after the merge; the orchestrator only reads the run (`gh`, read-only) and writes `result-NN-pipeline.md` |
| Record `pipeline-ci` / `pipeline-cd` without `role:` | `role: pipeline-ci` or `role: pipeline-cd` in the frontmatter (else the board derives `orchestrator`) |
| Retry past a limit | `NEXT: escalate` -> escalation record |
| Edit the live spec, ADRs or code from a sync agent | `spec-delta` / new ADR through the user |
| Hand-edit `status.md` outside `## Approvals` | Re-run `board.py` |

## Where records live

Root: `openspec/changes/<change-id>/handoff/` in the **target project** (never in the factory).
Archiving a change moves the whole folder with the change. `status.md` is generated by `board.py`;
only its `## Approvals` section is hand-written (by the orchestrator, from the user's own words).

## Roles and who reads/writes what

20 roles. The orchestrator is the project manager; it is the only one that talks to the user and the only one that launches agents.

| Role | Agent | Reads | Writes |
|---|---|---|---|
| orchestrator | `building-aws-saas-serverless-quarkus-react-nextjs` (inline skill) | everything, `status.md` | work-orders, escalations, saved inline records, pipeline records, `## Approvals` |
| solution-architect | `solution-architect` (Opus) | `wo-NN-solution-architect`, interview verify, specs, ADRs | `architecture/` spec, contracts, ADRs (E2a); `design/<flow>.md` + `design.md` index (E4); `result-NN-solution-architect.md` |
| solution-reviewer | `solution-architecture-reviewer` | its work-order, the files and ADRs | `verify-E2a.md`, `verify-E4-<flow>.md`, `verify-E4-index.md` (inline; orchestrator saves) |
| infrastructure-architect | `aws-infrastructure-architect` (Opus) | `wo-NN-infrastructure-architect`, E2a files | `infrastructure/` spec + ADRs (E2c), `infra-design.md` (E4); `result-NN-infrastructure-architect.md` |
| infrastructure-reviewer | `aws-architect-reviewer` | its work-order, the files and ADRs | `verify-E2c.md`, `verify-E4-infra.md` (inline) |
| designer | `ui-ux-designer` | `wo-NN-designer`, interview verify, E3 spec | design system + ADRs (E2b), wireframes + navigation (E3b); returned inline (no Write tool); the manager saves the files and `result-NN-designer.md` with `saved-by` |
| design-reviewer | `ui-design-reviewer` | its work-order, files, ADRs, front code (visual) | `verify-E2b.md`, `verify-E3b.md` (inline); visual review of the front: `review-NN.md` with `role: frontend` |
| code | `quarkus-lambda-integrator` | `wo-NN-code`, review | code + `result-NN-code.md` |
| ai | `quarkus-lambda-integrator` (same agent as `code`) | `wo-NN-ai`, review | code + `result-NN-ai.md`; put `role: ai` in the records (the first listed role of an agent wins, so without it the board shows `code`) |
| stripe | `stripe-integrator` | `wo-NN-stripe` | code + `result-NN-stripe.md` |
| frontend | `nextjs-frontend-integrator` | `wo-NN-frontend`, wireframe, design system, contract | `frontend/` code + `result-NN-frontend.md` |
| cicd | `cicd-pipeline-engineer` | `wo-NN-cicd` | `.github/**` + `result-NN-cicd.md` (with the `user-must-add` list) |
| reviewer | `quarkus-code-reviewer`, `stripe-advisor`, `langchain4j-reviewer`, `nextjs-code-reviewer`, `terraform-code-reviewer`, `cicd-pipeline-reviewer` | `wo-NN-review`, code, ADRs | `review-NN.md` (inline; orchestrator saves; `role:` per the [wo-review variants](./assets/wo-review.template.md)) |
| infra | `aws-terraform-engineer` | `wo-NN-infra` | HCL + `result-NN-infra.md` |
| observability | `aws-observability` | `wo-NN-observability`, specs, pipeline record | Terraform (mode B) or live validation (mode C) + `result-NN-observability.md` (kind `report`; mode C adds `role: observability-live`, mode A `role: observability-review`) |
| pipeline-ci, pipeline-cd | none: the GitHub Actions run (the roles point to the orchestrator, which records the run) | `gh pr checks`, `gh run view` (read-only) | `result-NN-pipeline.md` with `role: pipeline-ci` or `pipeline-cd`, `run_url` |
| site-verify | `static-site-verifier` | `wo-NN-site-verify`, pipeline record, `out/` sha256 | `verify-E7-site.md` (inline) |
| debug | `aws-lambda-debugger` | `wo-NN-debug`, pipeline and observability results | `diagnosis-NN.md` (mode A), `verify-E7.md` (mode B; gap-acceptance relaunch: `verify-E7-<nn>`) (inline) |
| sync | `spec-synchronizer` | `wo-NN-sync`, drift, specs, ADRs, results | `verify-E1.md`, `verify-E3.md`, `verify-E5.md`, `spec-delta-NN.md` (inline) |

Where a role value in the profile is the orchestrator (`pipeline-ci`, `pipeline-cd`) or an agent shared with another role (`ai`),
the record carries an explicit `role:`. Agents without a Write tool (reviewers, debugger, synchronizer, site verifier, advisor,
architect reviewers) return the record inline; the orchestrator saves it unchanged except the normalisations in
[agent alignment](./blueprints/agent-alignment.md). Only the orchestrator launches agents. Models: `solution-architect` and
`aws-infrastructure-architect` run on Opus, every other agent on Sonnet (set by the orchestrator, not by this profile).

## Stage map (E1-E9) and the records it produces

| Stage | Records | Verifier (never the author) |
|---|---|---|
| E1 interview | `status.md` approvals, `verify-E1.md` | `spec-synchronizer` (review mode) + user |
| E2a solution architecture | ADRs `area: architecture`, `result-NN-solution-architect`, `verify-E2a.md` | `solution-architecture-reviewer` + `check_records.py` |
| E2b design system | ADRs `area: design`, `result-NN-designer`, `verify-E2b.md` | `ui-design-reviewer` |
| E2c infrastructure | ADRs `area: infrastructure`, `result-NN-infrastructure-architect`, `result-NN-observability` (mode A, `role: observability-review`), `verify-E2c.md` | `aws-architect-reviewer`; one E2 approval of the user over the three fronts |
| E3 functional spec | `verify-E3.md` | `spec-synchronizer` + user |
| E3b wireframes | `result-NN-designer`, `verify-E3b.md` | `ui-design-reviewer` + user approval |
| E4 change designs | `verify-E4-<flow>.md` (one per design), `verify-E4-index.md` (every R* owned by exactly one design), `verify-E4-infra.md` | `solution-architecture-reviewer`, `aws-architect-reviewer` |
| E5 tasks | `verify-E5.md` (R* -> tasks coverage) + `tasks.md` + the task table of `status.md` | `spec-synchronizer` + script (`board.py`) + user |
| E6 per task (I0-I9) | `wo-NN-<role>` -> `result-NN-<role>` -> `wo-NN-review` -> `review-NN` (-> fix `wo` -> ...); no verify record, the approved `review-NN` closes the task | per task type (see the variants table of `wo-review`); the orchestrator re-runs the build itself |
| E7 PR, pipeline, observability | `result-NN-pipeline` (CI, role `pipeline-ci`) -> user merge (`gate=E7-merge`) -> `result-NN-pipeline` (CD, role `pipeline-cd`) -> `wo-NN-observability` (mode C) -> `result-NN-observability` (`role: observability-live`, routes to `debug`) -> `wo-NN-debug` (mode B) -> `verify-E7.md` -> `verify-E7-site.md` when the change has a front; on failure `diagnosis-NN.md` | `aws-lambda-debugger` (mode B), `static-site-verifier`; producer `aws-observability` never verifies |
| E8 sync code to spec | `spec-delta-NN.md` | user accepts, rejects or answers |
| E9 gate | `status.md` | `check_records.py` + `detect_drift.py` + `board.py` |

Acceptance criteria per stage live in the stage blueprints of `building-aws-saas-serverless-quarkus-react-nextjs` (same
package): [E1](../building-aws-saas-serverless-quarkus-react-nextjs/blueprints/e1-interview.md),
[E2](../building-aws-saas-serverless-quarkus-react-nextjs/blueprints/e2-architecture-and-adrs.md),
[E3](../building-aws-saas-serverless-quarkus-react-nextjs/blueprints/e3-functional-spec.md),
[E3b](../building-aws-saas-serverless-quarkus-react-nextjs/blueprints/e3b-ui-design.md),
[E4-E5](../building-aws-saas-serverless-quarkus-react-nextjs/blueprints/e4-e5-design-and-tasks.md),
[E6](../building-aws-saas-serverless-quarkus-react-nextjs/blueprints/e6-implementation-cycle.md),
[E7](../building-aws-saas-serverless-quarkus-react-nextjs/blueprints/e7-deploy-and-observability.md),
[E8](../building-aws-saas-serverless-quarkus-react-nextjs/blueprints/e8-reverse-sync.md),
[E9](../building-aws-saas-serverless-quarkus-react-nextjs/blueprints/e9-archive-gate.md). Each becomes the `## Criteria` list of
its `verify-<stage>` record (`[x]` met, `[ ]` not met, with reason). Stage ids: `E1`, `E2a`, `E2b`, `E2c`, `E3`, `E3b`,
`E4-<flow>`, `E4-index`, `E4-infra`, `E5`, `E7`, `E7-site`.

## Limits (parameters, never an agent's memory)

Default values are the factory's own design choice (medium confidence, see
[unverified and risks](./blueprints/unverified-and-risks.md) M3), not sourced thresholds.

| Parameter | Default | Loop |
|---|---|---|
| `limits.build_attempts` | 3 | failed or partial author results per task, roles `code`, `ai`, `stripe`, `frontend`, `infra`, `observability`, `cicd` (see agent alignment A2) |
| `limits.review_rounds` | 2 | `changes-requested` reviews per task |
| `limits.deploy_cycles` | 2 | failed CD runs (`result-NN-pipeline`, role `pipeline-cd`, outcome `failed`), per change; a failed CI run is a fix in E6, not a cycle |
| `limits.delta_revisions` | 2 | spec-delta `revise`, per change |
| `limits.record_rejections` | 2 | `check_records.py` failing on the same record |
| `quality.coverage_min` | 80 | JaCoCo % of new classes (back end, AI) and test coverage of the front, copied into every code work-order |

The design authors (`solution-architect`, `infrastructure-architect`, `designer`) have no counter: their loop is `verify` `fail` ->
orchestrator -> new work-order; the orchestrator escalates by hand after the second failed verify of the same stage.

Precedence, most specific wins: **profile default < `openspec/handoff-profile.yaml` (only what
changes) < run arguments** (`board.py ... --args limits.review_rounds=4`). Values are integers
>= 1. `0` (escalate on the first failure: reached when count >= max(limit, 1), so it behaves exactly like `1`, kept for explicitness) is accepted only with `limits_zero_confirmed: true` after
the user explicitly confirms it. `status.md` records every effective value and its source; the
orchestrator copies the effective values for the task into each work-order's `## Limits`.

## Escalation

`NEXT: escalate limit=<name> task=<id>` -> the orchestrator stops that task (independent tasks go
on), writes `escalation-NN.md` ([template](./assets/escalation.template.md): attempts, evidence,
hypothesis, 2-4 options with impact), shows it, records the user's reply **verbatim** under
`## Answer`, sets `status: answered` + `answeredAt`. Nothing new goes to the PR or the pipeline on an open escalation.

## User gates (no `approval: apply` in this flow)

Only the user's own message (or the user's own action on GitHub) approves anything. The orchestrator writes each gate under `## Approvals`
of `status.md` and cites it in later work-orders; an agent message is never an approval. The gates of this profile:

| Gate id | Approved by | Evidence recorded |
|---|---|---|
| `E2`, `E3`, `E3b`, `E5` | the user, in chat | verbatim words |
| `D1-langchain4j` | the user, in chat | verbatim words (pre-release 1.15.0.CR1) |
| `github-plan` | the user, in chat (E1 block B8; Free = weaker variant accepted) | verbatim words |
| `bootstrap-apply` | the user, who applies the OIDC/state bootstrap once, locally | the user's words that it was applied; the agents never apply |
| `E7-merge` | the user, reviewing the plan commented on the PR and merging | `gate=E7-merge \| source=github <PR url> \| login=<user>` after the orchestrator read `gh pr view` |
| prod release | the user, as the GitHub plan allows (environment reviewer or branch rule) | the PR or run url |
| `E7-gap`, archive | the user, in chat | verbatim words |

Billable or intrusive live checks keep the relayed-line form (`approval: alarm-test`, `approval: logs-insights`, `approval: e7-gaps`);
the former `approval: apply`, `rollback` and `smoke` lines are not used. Meaning of each line and the E7 gap acceptance:
[approval lines](./blueprints/approval-lines.md). Agents receive the generic text (`relayed-by=<orchestrator>`); only this orchestrator's own files carry its name.

## Handshake additions for this profile

1. Every work-order carries `task:`; review, debug and verify work-orders reuse the task of the work
   they serve, so counters and `all_tasks` stay per task (E1-E4 work-orders: `task: spec`; E7 work-orders: `task: E7`).
2. The orchestrator adds `task:` to every inline record it saves, then runs `check_records.py`,
   `detect_drift.py`, `board.py`, and follows `NEXT:`.
3. A record that fails the check goes back to its author with the error lines; the orchestrator
   writes `rejections: <n>` on it each time (feeds `record_rejections`). The same applies when `spec_impact` contradicts the `## Spec impact` section (checked by hand: `check_records.py` does not compare them).
4. Construction work-orders (`code`, `ai`, `stripe`, `frontend`, `infra`) carry `## Functionality` and `## Diagram` besides the generic sections;
   `check_records.py` enforces only the generic ones, so the orchestrator checks these two by hand before launching.
5. Two-reviewer tasks (stripe, ai, frontend) use a **hold**: the second `wo-NN-review` is written with `status: pending` before `board.py` runs.

## Quick Reference

| Need | Where |
|---|---|
| Which skills go in a work-order | [roles-and-skills](./blueprints/roles-and-skills.md) |
| Why a record is rejected | [agent alignment](./blueprints/agent-alignment.md) |
| Where ADRs and deltas live | [openspec integration](./blueprints/openspec-integration.md) |
| Which `role:` a review or pipeline record needs | [wo-review](./assets/wo-review.template.md) variants, [result-pipeline](./assets/result-pipeline.template.md) |

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
