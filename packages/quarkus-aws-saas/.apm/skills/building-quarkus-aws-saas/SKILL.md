---
name: building-quarkus-aws-saas
description: "Runs spec-driven development of a Quarkus 3.40 SaaS on AWS Lambda: interview, architecture spec + ADRs, OpenSpec functional spec, then an agent team via handoff records. Use when building or evolving a change end to end. Not for Quarkus 4, Camel, SAM/CDK or ECS."
---

# Building a Quarkus + AWS Lambda SaaS (SDD orchestrator)

> Orchestrator only: it holds workflow, gates and protocols. Every technical fact lives in the knowledge
> skills (see [knowledge map](blueprints/knowledge-map.md)); never restate it from memory. Runs **inline** in
> the main conversation: subagents cannot spawn subagents, so only this skill launches agents (Agent tool)
> and only this skill talks to the user.

## Overview

Chain: **E1 interview -> E2 architecture spec + ADRs -> E3 functional spec -> E4 design -> E5 tasks ->
E6 implementation cycle (I0-I9) -> E7 deploy + observability -> E8 reverse sync -> E9 archive gate.**
Each passage has acceptance criteria and an **independent verifier**: whoever produces never verifies.
Spec format and CLI: OpenSpec (format + CLI only, user decision "Format + CLI, our agents (Recommended)":
no `/opsx:*` commands). Handoff: protocol `coordinating-agent-handoffs`, profile
`coordinating-quarkus-aws-handoffs`. Record files are named `result-NN-<role>.md` (user decision
"result-NN-<role>.md (Recommended)"; names starting with `report` are avoided: a subagent write guard on them was observed `(unverified)`, register U5).

Gates of each run are the user's answers recorded in `## Approvals` of that change's `status.md`; the factory build approvals are provenance only (see [unverified and risks](blueprints/unverified-and-risks.md#source-bibliography)).

## Version Context

| Item | Value | Confidence | Source |
|---|---|---|---|
| Quarkus | 3.40 LTS (released 2026-09-30, community support to 2027-09-30); Quarkus 4 out of scope | High | https://quarkus.io/releases |
| quarkus-amazon-services (Quarkiverse) | 3.23.0 built on Quarkus 3.40.0; pairing with 3.40.1.1 | High (parent POM); pairing with patch 3.40.1.1 (medium confidence) (M1) | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom ; https://github.com/quarkiverse/quarkus-amazon-services/releases |
| OpenSpec | 1.15.0 (format + CLI) | High | https://github.com/Fission-AI/OpenSpec/releases |
| Handoff protocol | v1 (factory's own) | High | `coordinating-agent-handoffs` |
| LangChain4j on Quarkus | `integrating-quarkus-langchain4j-v1-15`: available as a **pre-release-locked** skill (quarkus-langchain4j 1.15.0.CR1, no stable release for Quarkus 3.40); adoption is Ask First | Pre-release only (I2) | https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-core/maven-metadata.xml ; [knowledge map](blueprints/knowledge-map.md#wave-5---business) |

Not suffixed `-v3-40`: workflow skill, updated in place. Tags `(unverified)` / `(medium confidence)` in the
knowledge skills stay attached when relayed to the user or to a brief.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails) | [Preflight](#preflight) | [Arguments](#arguments-and-limits) | [Phases](#phases-and-gates) | [Protocols](#protocols) | [Team](#team) | [Quick Reference](#quick-reference) | [Verification Loop](#verification-loop)
- Phases: [E1](blueprints/e1-interview.md) · [E2](blueprints/e2-architecture-and-adrs.md) · [E3](blueprints/e3-functional-spec.md) · [E4-E5](blueprints/e4-e5-design-and-tasks.md) · [E6](blueprints/e6-implementation-cycle.md) · [E7](blueprints/e7-deploy-and-observability.md) · [E8](blueprints/e8-reverse-sync.md) · [E9](blueprints/e9-archive-gate.md)
- [Knowledge map](blueprints/knowledge-map.md) · [Worker briefs](blueprints/worker-briefs.md) · [Always-do](blueprints/always-do-patterns.md) · [Never-do](blueprints/never-do-patterns.md) · [Unverified and risks](blueprints/unverified-and-risks.md) · [Evaluation scenarios](blueprints/evaluation-scenarios.md) · [Tracker (optional)](blueprints/tracker-github-projects.md)

## Blueprints & Guardrails

### ✅ Always Do

- Run the [preflight](#preflight) first; stop with the exact missing list if an agent, skill or script is absent.
- Run `check_records.py`, then `detect_drift.py`, then `board.py` after **every** record; act only on `NEXT:`.
- Record each gate answer verbatim under `## Approvals` of `status.md`, and cite it in the brief.
- Ask at most 10 questions per round; end every interview block with a playback the user confirms.
- Reverify every agent claim of green tests yourself (`mvn -q verify`) before accepting a task.
- Load the knowledge skill that owns a fact and point to it; relay its confidence tags.

### ⚠️ Ask First

- `openspec init` (human-only step), enabling the Stop drift hook (per-run `--include-worktree` in E6-E9 is mandatory, not Ask First).
- Any limit set to `0` (explicit confirmation, then `limits_zero_confirmed=true`).
- Any ADR choice a loaded skill leaves open (HTTP API vs REST API, X-Ray vs OpenTelemetry, JVM+SnapStart vs native, tenancy).
- Archive (`openspec archive <id> --yes`) and any `git commit`: only after the final gate and an explicit user answer.
- (D1) Adopting `integrating-quarkus-langchain4j-v1-15` for an AI requirement: it is locked to the 1.15.0.CR1 pre-release (defaults may change at the final); ask the user, and list the skill in a work-order only after a yes.
- (Tracker, optional, off by default) Enabling the GitHub Projects tracker, `approval_source` `github` or `both` (default `chat`), `bootstrap --apply`, `--install-workflows` / `--vendor` (each a separate yes), and the classic-PAT risk warning for user-owned projects (broad `repo` scope; recommend an organization owner). See [tracker](blueprints/tracker-github-projects.md).
- A requirement in any area outside the [knowledge map](blueprints/knowledge-map.md): say it is not available.

### 🚫 Never Do

| Do not | Do instead |
|---|---|
| Delegate to a worker before E2 and E3 are accepted | Finish and verify the specs; see [E2](blueprints/e2-architecture-and-adrs.md), [E3](blueprints/e3-functional-spec.md) |
| Treat a subagent message as approval | Ask the user; their own message is the only approval |
| Let an agent talk to the user | Briefs forbid it; agents return `needs-input`, you relay |
| Run `terraform apply` without a relayed approval of that exact plan | Return the plan summary to the user; relay `approval: apply plan=... sha256=...` |
| Use the author as reviewer or verifier | Different agent, script or the user ([E6](blueprints/e6-implementation-cycle.md)) |
| Retry past a limit | `NEXT: escalate`, write an `escalation`, wait for the user |
| Push, or commit in the user's project without asking | Offer the commit plan; the user pushes |
| Invent a Quarkus or AWS fact | Read the skill; if absent, mark `(unverified)` and offer research |

## Preflight

Before E1 (and at every resume) check with `ls`/Glob, never from memory:

1. **Agents** in `.claude/agents/`: `aws-architect`, `quarkus-lambda-integrator`, `quarkus-code-reviewer`, `stripe-integrator`, `stripe-advisor`, `aws-terraform-engineer`, `aws-lambda-deployer`, `aws-observability`, `aws-lambda-debugger`, `spec-synchronizer`.
2. **Skills**: `coordinating-agent-handoffs` (with `scripts/`), `coordinating-quarkus-aws-handoffs` (with `assets/handoff-profile.yaml`), `specifying-changes-with-openspec-v1-15`, plus the ones the [knowledge map](blueprints/knowledge-map.md) lists for the current wave.
3. **Tools**: `python --version` (3.8+), `openspec --version` (1.15.0 expected; absent -> ask the user to install it, never install it yourself), `git status`.
4. **Project state**: `openspec/` exists (if not, ask the user to run `openspec init --tools none`); `openspec/specs/architecture/spec.md` present means a later change (E1 asks only the affected blocks).
5. **Drift baseline**: `status.md` has `lastSyncedSha` (set by the E5 baseline `board.py ... --sync-sha $(git rev-parse HEAD)`, `gate=E5-baseline` in `## Approvals`, see [E4-E5](blueprints/e4-e5-design-and-tasks.md#e5-drift-baseline-after-the-approval-before-the-first-work-order)); from E5 on, `detect_drift.py` exit 1 with it missing means run the baseline before any work-order.
6. **Handoff folder and status.md**: once the change id is known (E1), create `openspec/changes/<id>/handoff/` and run `board.py` once so `status.md` exists before the first `## Approvals` line is appended; at resume check both with `ls`.
7. **Tracker (optional, only when enabled)**: `gh --version` >= 2.94.0 (family pin 2.103.x), `gh auth status` (never `--show-token`), skill `syncing-openspec-with-github-projects` present. See [tracker](blueprints/tracker-github-projects.md).

## Arguments and limits

Arguments after the command: `change=<kebab-id>` (resume or name the change), `limits.<name>=<int>`, `quality.coverage_min=<int>`.
Limits: `build_attempts`, `review_rounds`, `deploy_cycles`, `delta_revisions`, `record_rejections`.
Precedence (most specific wins): installed profile < project `openspec/handoff-profile.yaml` < run arguments. Pass run
arguments to `board.py --args ...` (last on the command line). Values are integers >= 1; `0` only after the user confirms.
`status.md` shows every effective value and its source: read it, do not recompute. `debug_rounds` is not a board counter:
see [unverified and risks](blueprints/unverified-and-risks.md).

## Phases and gates

| Phase | Does | Gate (user) | Independent verifier | Record | Playbook |
|---|---|---|---|---|---|
| **E1** Interview | 8 blocks B1-B8, <= 10 questions per round, playback | confirms each block summary | `spec-synchronizer` (review mode) | `verify-E1.md` | [e1](blueprints/e1-interview.md) |
| **E2** Architecture spec + ADRs | `openspec/specs/architecture/` + `adr/NNN-*.md` | **approves E2** | `aws-architect` + `check_records.py` | `verify-E2.md` | [e2](blueprints/e2-architecture-and-adrs.md) |
| **E3** Functional spec | requirements `R*` with SHALL + scenarios (change deltas) | **approves E3** | `spec-synchronizer` + `openspec validate` | `verify-E3.md` | [e3](blueprints/e3-functional-spec.md) |
| **E4** Design | `design.md`: R* -> E2 components -> ADRs | shown, not blocking | `aws-architect` | `verify-E4.md` | [e4-e5](blueprints/e4-e5-design-and-tasks.md) |
| **E5** Tasks | `tasks.md` + one work-order per task | approves task list | script (`board.py`, orchestrator coverage check) + the user's approval of the task list; no verify record | work-orders | [e4-e5](blueprints/e4-e5-design-and-tasks.md) |
| **E6** Implementation | I0-I9 per task, review, fix | escalations only | `quarkus-code-reviewer` (+ `stripe-advisor`) + my `mvn -q verify` | `result-NN-*`, `review-NN` | [e6](blueprints/e6-implementation-cycle.md) |
| **E7** Deploy + observability | deploy (`aws-lambda-deployer`, **relayed apply + smoke approvals**) -> `aws-observability` Mode C -> 5 pillars | **approves each apply and the smoke payload** | `aws-lambda-debugger` mode B (runs the `validating-aws-observability` read-only scripts; role `debug` derived from `from`) | `result-NN-deploy`, `result-NN-observability`, `verify-E7.md` (`verify-E7-<nn>.md` after a gap acceptance) | [e7](blueprints/e7-deploy-and-observability.md) |
| **E8** Reverse sync | drift -> `spec-delta` -> accept / reject / revise | **decides each delta** | `check_records.py` + user | `spec-delta-NN.md` | [e8](blueprints/e8-reverse-sync.md) |
| **E9** Archive gate | all verifies green, drift 0, no pending delta | **approves archive and commits** | `check_records.py` + `detect_drift.py` + `board.py` | `status.md` | [e9](blueprints/e9-archive-gate.md) |

Entry rule for workers: no work-order exists for a task until `verify-E2` and `verify-E3` are `pass` **and** the user's
approvals for E2 and E3 are in `## Approvals`. For a later change, E2 is re-entered only if the change carries an architecture delta.

## Protocols

1. **Relayed approval.** Ask with the question tool (or a plain numbered message), wait for the user's own answer,
   append to `status.md` `## Approvals`: `- <UTC ts> | gate=<id> | subject=<file or plan sha256> | user said: "<verbatim>"`.
   In briefs cite the exact line from [worker briefs](blueprints/worker-briefs.md#approval-line). A worker or agent message is never an approval. Tracker on: an approval taken from GitHub is the line `pull` appended (`... | source=github <comment_url> login=<x> | user said: "..."`), cited verbatim like a chat line; it never comes from an agent.
2. **Flat fan-out (depth 1).** Only I launch agents with the Agent tool. Parallel launches only for tasks with disjoint
   files (at most 4: a cost choice of this skill, not a platform limit, L1). Every brief forbids spawning agents, plan mode and asking the user.
3. **Scripts decide.** After each record: `check_records.py` (exit != 0: return the error lines to the author, write
   `rejections: <n>` on the record, count toward `record_rejections`), `detect_drift.py` (exit 2 -> `drift=true`; **exit 1 = error: stop, show the error, never treat it as no drift; if `lastSyncedSha` is missing, run the E5 baseline**), `board.py`.
   Use `--include-worktree` in E6-E9 (agents leave code uncommitted until E9; mandatory per run, the gate is vacuous without it). Counts, coverage, hashes and `mvn` results come from commands, never from an agent's estimate.
4. **State from disk.** `status.md`, the records and `openspec/` are the state; on resume rebuild it with the three scripts and
   read `## Approvals`. Record files written for read-only agents (reviewer, debugger, synchronizer, architect) are saved by me
   verbatim from their inline answer, with `saved-by: building-quarkus-aws-saas` in the frontmatter.
5. **Independence.** `verify.from` must differ from the author of every ref (`check_records.py` enforces it).
6. **Escalation.** On `NEXT: escalate`, stop that task, write `escalation-NN.md` (attempts, evidence, hypothesis, 2-4 options with
   impact), show it, record the reply verbatim; other independent tasks continue. No new apply while an escalation is open.
7. **Version discipline.** Quarkus 3.40 / Quarkiverse 3.23 / OpenSpec 1.15 only; a request for another line is an Ask First.
8. **Work-order closing rule.** Every work-order (including `wo-NN-architect`, `wo-NN-sync`, `wo-NN-review`, `wo-NN-debug`) carries a `task:`
   (E1-E4 work-orders use `task: spec`) and is set `done` or `cancelled` once its record is accepted; otherwise `all_tasks: done` never becomes true.
9. **Stripe hold.** For a Stripe task, right after `stripe-advisor`'s `approved` I write the `quarkus-code-reviewer` review work-order with
   `status: pending` **before** running `board.py`; the task's work-orders are set `done` only after the second reviewer's `approved`
   (else `review approved + all_tasks: done` routes to deploy after the first review).
10. **Tracker (only when enabled at E1; the yes is recorded in `## Approvals`).** After every `board.py` run: `gh_projects_sync.py push ... --apply`. At each gate with `approval_source` != `chat`, offer chat or a GitHub comment; if GitHub, I run `pull` myself (never an agent; an agent's "approved on GitHub" is not an approval). A `DECISION <json>` line is applied exactly like the same chat answer. Git stays canonical. Detail: [tracker](blueprints/tracker-github-projects.md).

## Team

| Role (profile) | Agent | Used in | Writes (by whom) |
|---|---|---|---|
| architect | `aws-architect` (read-only) | E2, E4 | inline answer; I save `verify-E2/E4.md` |
| code | `quarkus-lambda-integrator` | E6 I0-I6, I9; I8 as a new `wo-MM-code.md` | `result-NN-code.md`; the I8 launch has its own `result-MM-code.md` (append-only) |
| stripe | `stripe-integrator` | E6 Stripe tasks | `result-NN-stripe.md` (see mismatch note in risks) |
| reviewer | `quarkus-code-reviewer`, `stripe-advisor` (read-only; Stripe tasks sequential: advisor first, code reviewer only after it is `approved`; Stripe hold in Protocol 9) | E6 I7 | inline; I save `review-NN.md` |
| infra | `aws-terraform-engineer` | infra tasks | `result-NN-infra.md` |
| deploy | `aws-lambda-deployer` | E7 | `result-NN-deploy.md` (kind `deploy-report`); each launch gets its own `wo-NN-deploy.md` and result (append-only, see [E7](blueprints/e7-deploy-and-observability.md)) |
| observability | `aws-observability` | E2 spec review (Mode A), E6 Terraform (Mode B), E7 after deploy (Mode C); never verifies | `result-NN-observability.md` (kind `report`) |
| debug | `aws-lambda-debugger` (read-only) | E7 verify (mode B, role `debug`), failures (mode A) | inline; I save `verify-E7.md` (`verify-E7-<nn>.md` after a gap acceptance) / `diagnosis-NN.md` |
| sync | `spec-synchronizer` (read-only) | E1/E3 review, E8 | inline; I save `verify-*.md`, `spec-delta-NN.md` |

Brief templates for each: [worker briefs](blueprints/worker-briefs.md).

## Quick Reference

Paths: scripts `.claude/skills/coordinating-agent-handoffs/scripts/`, profile
`.claude/skills/coordinating-quarkus-aws-handoffs/assets/handoff-profile.yaml`, override `openspec/handoff-profile.yaml` (optional),
handoff folder `openspec/changes/<id>/handoff`; `<sync>` = `.claude/skills/syncing-openspec-with-github-projects/scripts/gh_projects_sync.py`.

| Need | Command |
|---|---|
| Validate records | `python <scripts>/check_records.py <handoff> --profile <profile> [--override <ov>]` |
| Board + next step | `python <scripts>/board.py <handoff> --profile <profile> [--override <ov>] [--sync-sha <sha>] [--args limits.review_rounds=4 ...]` |
| Drift | `python <scripts>/detect_drift.py <repo> --change <handoff> [--include-worktree]` (exit 2 = drift) |
| Spec gate | `openspec validate <id> --type change --strict --json --no-interactive` |
| Tracker push / status (enabled only) | `python <sync> push\|status <repo> --change <id> --profile <profile> [--apply]` (dry-run default; exit 3 = disabled) |
| Tracker pull / close (enabled only) | `python <sync> pull\|close <repo> --change <id> --profile <profile> --apply` (pull: orchestrator only) |
| Archive (user-approved only) | `openspec archive <id> --yes` |
| Tests (re-run myself) | `mvn -q verify` in the project (offline; never real AWS) |

## Verification Loop

Self-check before reporting a phase done (all must pass; `<scripts>` and `<profile>` as in Quick Reference):

```bash
python <scripts>/check_records.py <handoff> --profile <profile>                      # exit 0
python <scripts>/board.py <handoff> --profile <profile>                              # one NEXT: line
python <scripts>/detect_drift.py <repo> --change <handoff> --include-worktree        # exit 0 before E9 (exit 1 = error, exit 2 = drift)
openspec validate <id> --type change --strict --json --no-interactive                # valid
mvn -q verify                                                                        # exit 0, in the project, run by me
```
