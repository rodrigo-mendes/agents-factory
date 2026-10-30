# Unverified items and risks

Back to [SKILL.md](../SKILL.md). Authoring date 2026-10-28; revised for the Next.js + GitHub Actions flow (20 roles, pipeline records, three ADR folders). Register: **6 unverified (U1-U6)**,
**0 irresolvable (I)**, **4 medium confidence (M1-M4)** and **4 coverage limits (L1-L4)**, 14 items in
total. Tags `(unverified)` / `(medium confidence)` in other files of this skill point here by id.

## Contents

- Version-lifetime risk
- Unverified (U1-U6)
- Irresolvable from documentation (I)
- Medium confidence (M1-M4)
- Coverage limits (L1-L4)
- Tag to register mapping
- Source Bibliography

## Version-lifetime risk

| Risk | Effect | Mitigation |
|---|---|---|
| Protocol v1 of `coordinating-agent-handoffs` is being widened (deploy-report and diagnosis-report accept the four outcomes) | The profile no longer carries a `values:` override; a script older than the widened protocol rejects `partial` / `needs-input` | Run the Verification Loop with the installed `handoff-core`; update the package pair together |
| The agent definitions change (the observability and debugger agents are being aligned; the new design, front-end and reviewer agents are authored separately) | `agent-alignment.md` rows go stale | Re-read the agent files and re-check rows A6, A10, A14-A16 |
| Reused agents of `github-actions-cicd` (`cicd-pipeline-engineer`, `cicd-pipeline-reviewer`) know nothing about this profile | Their output may lack protocol frontmatter | The orchestrator wraps it (A14, A15) |
| OpenSpec 1.15.0 formats; no 1.15.1+ as of 2026-10-28 | `handoff/` and ADR placement may need a change | See the OpenSpec skill and U2, U3 |
| Claude Code hook and subagent write-guard behaviour can change | The `Stop` hook note and the `result-*` naming reason go stale | Re-check the hooks reference before installing a hook (U1); keep `result-*` (U5) |

## Unverified

| Id | Item | Consequence | Mitigation |
|---|---|---|---|
| U1 | Claude Code `Stop` hook behaviour: that only exit code 2 blocks, whether stdout of a non-blocking hook is shown, and whether APM `hooks:` can ship it. Taken over from the generic drift-hook page, not re-verified. | A drift warning may be invisible or may block a turn | Keep `\|\| true`; install only after the user's confirmation; re-check the hooks reference first |
| U2 | `openspec archive` moving or ignoring a non-standard `handoff/` folder inside the change folder. | Records could be lost or fail validation at archive | Run `openspec validate` before; inspect the archived folder after the first archive; copy `handoff/` out first if in doubt |
| U3 | `openspec validate` tolerating `openspec/specs/{architecture,design,infrastructure}/` and their `adr/` subfolders (folders that may be read as capabilities or lack `spec.md`) under `specs/`, and `changes/<id>/design/` next to the official `design.md`. | Validation noise or failure | Test on a scratch project; if it complains, give each folder a minimal `spec.md` in OpenSpec format, or move the ADR folders and edit `spec.adr_dir` in the profile |
| U4 | The profile and scripts ran only on fixtures (the 2026-10-28 chain, and the 31 throwaway cases of the next-action table of this revision, one per row), not yet on a real project change. | A rule interaction not covered by the fixtures could remain | Run the Verification Loop and the fixture commands of the SKILL before first use |
| U5 | A subagent write guard on file names starting with `report` (known from the user's decision and the generic protocol register U2, not from a dated official Anthropic page). | If the guard is narrower, `result-*` is still safe | Keep `result-*`; never test the guard |
| U6 | That the new and reused agents emit (or can be wrapped into) the records of A14-A16, and that `gh pr checks` / `gh run view` output is enough to fill `result-NN-pipeline.md`; not verified against a real GitHub run. | A record may need wrapping or a field may be missing | The orchestrator wraps and marks no `success` it cannot support; re-check on the first real run |

The `role` frontmatter field is no longer an unverified item: `record-kinds.md` of `coordinating-agent-handoffs` documents it ("overrides the role derived from `from`"). The Stripe and observability routing built on it is covered by fixtures only (U4).

## Irresolvable from documentation (I)

Count: 0. No open question of this profile is unanswerable from the sources read.

## Medium confidence

| Id | Item | Consequence | Mitigation |
|---|---|---|---|
| M1 | The E7 acceptance chain of family rule 15 (observability result routed to the debugger, `verify-E7.md` from the debugger as the final-gate record) is the factory's design, not an external standard. | A debugger verdict could be accepted without an independent pillar check | The debugger's mode B repeats the pillar checks read-only; the user sees `status.md` before the final gate |
| M2 | Counting `build_attempts` as failed/partial **reports** while the integrator also counts attempts inside a run (A2 of agent alignment); the design authors are not counted at all. | Up to `limit x limit` builds before the board alone escalates; a design loop is escalated by hand | Orchestrator escalates on `failed` with `build_attempts >=` the work-order limit and after the second failed verify of a design stage |
| M4 | `deploy_cycles` counts only failed CD runs (`pipeline-cd` + `failed`); a `partial` CD run or an observability/debug failure after a green run is not a cycle, and the board cannot tell dev from prod runs. | A prod failure shares the counter with dev failures | The orchestrator reads `environment` in the pipeline record; raise or reset through an answered escalation |
| M3 | Default values (3/2/2/2/2, `coverage_min` 80) are design defaults awaiting the user's final choice at gate G1, not sourced thresholds. | Too tight or too loose for the project | Override per project or per run; they are parameters |

## Coverage limits (L)

Count: 4.

- L1: the profile does not enforce that `spec_impact` agrees with the `## Spec impact` text; the orchestrator checks by hand (agent alignment A1).
- L2: the profile does not enforce which agent of the `reviewer` role runs (six agents share it); the work-order type, the `role:` on each review and the sequential order of two-reviewer tasks (hold) are orchestrator discipline.
- L3: `review_rounds` counts review records with outcome `changes-requested` per task, so a two-reviewer task consumes rounds from both reviewers; a project may raise `limits.review_rounds` through `openspec/handoff-profile.yaml`.
- L4: `all_tasks: done` over a final `verify` of the debugger can fire `NEXT: final-gate` before `verify-E7-site` exists when the change has a front end; the board cannot know whether a front exists. E9 re-checks every required verify (the orchestrator does this by hand).

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) Stop hook warning behaviour | [openspec-integration.md](./openspec-integration.md) | U1 |
| (unverified) `handoff/` travels through archive | [openspec-integration.md](./openspec-integration.md) | U2 |
| (unverified) the three spec/ADR folders under `openspec/specs/` | [openspec-integration.md](./openspec-integration.md) | U3 |
| (unverified) scripts on a real change (fixtures only so far) | SKILL.md Verification Loop | U4 |
| (unverified) `report*` name guard | SKILL.md Never Do (naming convention only); this register | U5 |
| (medium confidence) E7 chain: debugger verify as gate record | SKILL.md stage map; agent-alignment A6, A10 | M1 |
| (medium confidence) two build-attempt counters, design authors uncounted | agent-alignment A2 | M2 |
| (medium confidence) `deploy_cycles` counts failed CD runs only | SKILL.md Limits | M4 |
| (unverified) agents and `gh` output vs the pipeline and author records | agent-alignment A14-A16 | U6 |
| (medium confidence) default limits and coverage | SKILL.md Limits | M3 |
| spec_impact consistency checked by hand | agent-alignment A1 | L1 |
| reviewer agent choice and two-reviewer sequence | agent-alignment (Routing details) | L2 |
| `review_rounds` counted per `changes-requested` record | agent-alignment (Routing details); wo-review template | L3 |
| final-gate can precede the site verify | agent-alignment (Routing details) | L4 |

## Source Bibliography

- Shipped: skills `coordinating-agent-handoffs` (SKILL.md, `blueprints/profile-format.md`, `blueprints/record-kinds.md`, `blueprints/protocol.md`, `scripts/`) and `specifying-changes-with-openspec-v1-15`.
- Factory provenance, not shipped (read 2026-10-28; do not cite in runtime briefs). Generic protocol source: `packages/handoff-core/.apm/skills/coordinating-agent-handoffs/`.
- Agent definitions (factory provenance, not shipped): `packages/quarkus-aws/.apm/agents/`, `packages/aws-lambda/.apm/agents/` (the deployer is no longer part of this flow), `packages/github-actions-cicd` (cicd agents), `packages/aws-observability/.apm/agents/aws-observability.agent.md`, `packages/handoff-core/.apm/agents/spec-synchronizer.agent.md`, `packages/stripe-java/.apm/agents/`, `packages/aws-architect/.apm/agents/`, `packages/terraform/.apm/agents/aws-terraform-engineer.agent.md`.
- Family decisions (factory provenance, not shipped): `workspace/quarkus-aws-saas/_family_rules_v3.40.md`, rules 13-15 (dated 2026-10-28).
- No external web source: the profile is the factory's own design.
