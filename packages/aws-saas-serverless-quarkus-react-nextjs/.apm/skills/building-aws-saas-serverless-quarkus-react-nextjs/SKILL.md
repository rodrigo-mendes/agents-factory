---
name: building-aws-saas-serverless-quarkus-react-nextjs
description: "Project manager for spec-driven development of a SaaS on AWS: Quarkus 3.40 Lambdas, Next.js static export on S3+CloudFront, AI in Lambdas, GitHub Actions deploy. Interview, specs, designs, agent team via handoff records. Use when building or evolving a change end to end. Not for Quarkus 4, Camel, SAM/CDK, ECS or SSR."
---

# Building an AWS serverless SaaS (Quarkus + React/Next.js) - project manager

> Project manager only: it holds workflow, gates and protocols. It never designs and never writes code. Every technical fact
> lives in the knowledge skills (see [knowledge map](blueprints/knowledge-map.md)); never restate it from memory. Runs **inline** in
> the main conversation: subagents cannot spawn subagents, so only this skill launches agents (Agent tool) and only this skill talks to the user.

## Overview

Chain: **E1 interview -> E2 (a solution, b design, c infrastructure) -> E3 functional spec -> E3b wireframes -> E4 designs + infra design ->
E5 tasks -> E6 implementation cycle (I0-I9) -> E7 PR + CI + merge + CD + verification -> E8 reverse sync -> E9 archive gate.**
Each passage has acceptance criteria and an **independent verifier**: whoever produces never verifies, and **every deliverable has its own
reviewer, different from its author** (matrix below). Spec format and CLI: OpenSpec (format + CLI only: no `/opsx:*` commands). The `openspec/`
layout (functional specs, the three decision areas `architecture/`, `design/`, `infrastructure/`, multiple designs per change) is the factory
convention in the rule `openspec-project-layout` (package `openspec-core`). Handoff: protocol `coordinating-agent-handoffs`, profile
`coordinating-quarkus-aws-handoffs`. Records: `wo-NN-<role>.md`, `result-NN-<role>.md`, `review-NN.md`, `verify-<stage>.md`; names starting with `report` are avoided (write guard observed `(unverified)`, register U5).

Gates of each run are the user's answers recorded in `## Approvals` of that change's `status.md`; the factory build approvals are provenance only (see [unverified and risks](blueprints/unverified-and-risks.md#source-bibliography)).

## Version Context

| Item | Value | Confidence | Source |
|---|---|---|---|
| Quarkus | 3.40 LTS (released 2026-09-30, community support to 2027-09-30); Quarkus 4 out of scope | High | https://quarkus.io/releases |
| quarkus-amazon-services (Quarkiverse) | 3.23.0 built on Quarkus 3.40.0; pairing with 3.40.1.1 | High (parent POM); pairing with patch 3.40.1.1 (medium confidence) (M1) | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom |
| OpenSpec | 1.15.0 (format + CLI) | High | https://github.com/Fission-AI/OpenSpec/releases |
| Handoff protocol | v1 (factory's own) | High | `coordinating-agent-handoffs` |
| LangChain4j on Quarkus | `integrating-quarkus-langchain4j-v1-15` (package `quarkus-langchain4j`): quarkus-langchain4j 1.15.0.CR1, **pre-release-locked**; the default AI path, adoption is Ask First D1; Lambdas only | Pre-release only (I2) | https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-core/maven-metadata.xml |
| Front end | Next.js static export (`output: 'export'`) + React on S3 + CloudFront; pnpm + Node 26 (skill `building-nextjs-github-actions-v16-4`); no server features | Per the Vercel and CI/CD skills (see [knowledge map](blueprints/knowledge-map.md#wave-4---frontend-next-static-export-on-s3--cloudfront)) | skills of `vercel-frontend`, `github-actions-cicd` |

Not suffixed `-v3-40`: workflow skill, updated in place. Tags `(unverified)` / `(medium confidence)` in the knowledge skills stay attached when relayed.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails) | [Preflight](#preflight) | [Arguments](#arguments-and-limits) | [Phases](#phases-and-gates) | [Deliverable matrix](#deliverable--author--independent-reviewer) | [Protocols](#protocols) | [Team](#team) | [Quick Reference](#quick-reference) | [Verification Loop](#verification-loop)
- Phases: [E1](blueprints/e1-interview.md) · [E2](blueprints/e2-architecture-and-adrs.md) · [E3](blueprints/e3-functional-spec.md) · [E3b](blueprints/e3b-ui-design.md) · [E4-E5](blueprints/e4-e5-design-and-tasks.md) · [E6](blueprints/e6-implementation-cycle.md) · [E7](blueprints/e7-deploy-and-observability.md) · [E8](blueprints/e8-reverse-sync.md) · [E9](blueprints/e9-archive-gate.md)
- [Knowledge map](blueprints/knowledge-map.md) · [Worker briefs](blueprints/worker-briefs.md) · [Always-do](blueprints/always-do-patterns.md) · [Never-do](blueprints/never-do-patterns.md) · [Unverified and risks](blueprints/unverified-and-risks.md) · [Evaluation scenarios](blueprints/evaluation-scenarios.md) · [Tracker (optional)](blueprints/tracker-github-projects.md)

## Blueprints & Guardrails

### ✅ Always Do

- Run the [preflight](#preflight) first; stop with the exact missing list if an agent, skill, tool or `model:` is wrong.
- Run `check_records.py`, then `detect_drift.py`, then `board.py` after **every** record; act only on `NEXT:`.
- Record each gate answer verbatim under `## Approvals` of `status.md`, and cite it in the brief.
- Ask at most 10 questions per round; end every interview block with a playback the user confirms.
- Launch every agent with the explicit `model` of the [Model split](#protocols) (protocol 11).
- Reverify every agent claim of green builds yourself (`mvn -q verify`, `pnpm build && pnpm test`, `terraform validate`, `actionlint`) before accepting a task.
- Read pipeline state only with read-only `gh` commands (`gh pr checks`, `gh run view`) and write it as `result-NN-pipeline.md`.
- Load the knowledge skill that owns a fact and point to it; relay its confidence tags.

### ⚠️ Ask First

- `openspec init` (human-only step), enabling the Stop drift hook (per-run `--include-worktree` in E6-E9 is mandatory, not Ask First).
- Any limit set to `0` (explicit confirmation, then `limits_zero_confirmed=true`).
- Any ADR choice a loaded skill leaves open (HTTP API vs REST API, X-Ray vs OpenTelemetry, JVM+SnapStart vs native, tenancy, design base, i18n, accounts).
- GitHub plan and repo visibility (E1 block B8): Free on a private repo = weaker variant (no environments, no branch protection); show the risks and ask.
- Archive (`openspec archive <id> --yes`) and any `git commit`: only after the final gate and an explicit user answer.
- (D1) Adopting `integrating-quarkus-langchain4j-v1-15` (1.15.0.CR1 pre-release): ask; list the skill in a work-order only after a yes.
- Browser login with Cognito (Hosted UI / OIDC PKCE) has no skill `(unverified)`: ask; offer research via `/researching-technical-frameworks`.
- A request that needs a server in Next.js (SSR, Server Actions, route handlers, middleware, ISR), a Vercel deploy, or chat/streaming to the browser: out of scope, say so and offer the static alternative.
- (Tracker, optional, off by default) Enabling the GitHub Projects tracker, `approval_source` `github` or `both`, `bootstrap --apply`, `--install-workflows` / `--vendor`. See [tracker](blueprints/tracker-github-projects.md).
- A requirement in any area outside the [knowledge map](blueprints/knowledge-map.md): say it is not available.

### 🚫 Never Do

| Do not | Do instead |
|---|---|
| Design, write code or write Terraform/workflows myself | Delegate to the owner agent; I coordinate, record and ask |
| Delegate to a worker before E2 and E3 (and E3b for UI changes) are accepted | Finish and verify the specs; see [E2](blueprints/e2-architecture-and-adrs.md), [E3](blueprints/e3-functional-spec.md) |
| Treat a subagent message as approval | Ask the user; their own message (or a GitHub approval read by `pull`/PR url) is the only approval |
| Let an agent talk to the user | Briefs forbid it; agents return `needs-input`, I relay |
| Let an agent push, open a PR, merge, trigger a workflow or run `terraform apply` | The user pushes, merges and applies the bootstrap; the pipeline deploys after the merge |
| Use the author as reviewer or verifier of its own deliverable | A different agent, script or the user (matrix below) |
| Retry past a limit | `NEXT: escalate`, write an `escalation`, wait for the user |
| Push, or commit in the user's project without asking | Offer the commit plan; the user pushes |
| Add server features to Next.js or deploy to Vercel | Static export on S3 + CloudFront only |
| Invent a Quarkus, AWS, React or GitHub Actions fact | Read the skill; if absent, mark `(unverified)` and offer research |

## Preflight

Before E1 (and at every resume) check with `ls`/Glob/`head`, never from memory:

1. **Agents** in `.claude/agents/` (and the `model:` of each frontmatter, protocol 11): `solution-architect` (opus), `solution-architecture-reviewer`, `aws-infrastructure-architect` (opus), `aws-architect-reviewer`, `ui-ux-designer`, `ui-design-reviewer`, `quarkus-lambda-integrator`, `quarkus-code-reviewer`, `langchain4j-reviewer`, `stripe-integrator`, `stripe-advisor`, `nextjs-frontend-integrator`, `nextjs-code-reviewer`, `aws-terraform-engineer`, `terraform-code-reviewer`, `aws-observability`, `static-site-verifier`, `aws-lambda-debugger`, `cicd-pipeline-engineer`, `cicd-pipeline-reviewer`, `spec-synchronizer`. A `model:` other than the expected one (opus for the two architects, sonnet for the rest): stop and list it. `aws-lambda-deployer` and `aws-architect` are not part of this flow.
2. **Skills**: `coordinating-agent-handoffs` (with `scripts/`), `coordinating-quarkus-aws-handoffs` (with `assets/handoff-profile.yaml`), `specifying-changes-with-openspec-v1-15`, the Vercel skills of the IN list and the `github-actions-cicd` skills listed in the [knowledge map](blueprints/knowledge-map.md), plus the ones it lists for the current wave.
3. **Tools**: `python --version` (3.8+), `openspec --version` (1.15.0 expected; absent -> ask the user to install it), `git status`, `gh --version` and `gh auth status` (read-only checks of CI/CD runs), `node --version` and `pnpm --version` (front-end tasks; Node 26 + pnpm per the CI skill; absent -> report, never install).
4. **Project state**: `openspec/` exists (if not, ask the user to run `openspec init --tools none`); `openspec/specs/architecture/spec.md` present means a later change (E1 asks only the affected blocks).
5. **Drift baseline**: `status.md` has `lastSyncedSha` (set by the E5 baseline, `gate=E5-baseline`, see [E4-E5](blueprints/e4-e5-design-and-tasks.md#e5-drift-baseline-after-the-approval-before-the-first-work-order)); from E5 on, `detect_drift.py` exit 1 with it missing means run the baseline first.
6. **Handoff folder and status.md**: once the change id is known (E1), create `openspec/changes/<id>/handoff/` and run `board.py` once so `status.md` exists before the first `## Approvals` line.
7. **Tracker (optional, only when enabled)**: `gh --version` >= 2.94.0, skill `syncing-openspec-with-github-projects` present. See [tracker](blueprints/tracker-github-projects.md).

## Arguments and limits

Arguments after the command: `change=<kebab-id>` (resume or name the change), `limits.<name>=<int>`, `quality.coverage_min=<int>`.
Limits: `build_attempts`, `review_rounds`, `deploy_cycles`, `delta_revisions`, `record_rejections`.
Precedence (most specific wins): installed profile < project `openspec/handoff-profile.yaml` < run arguments. Pass run
arguments to `board.py --args ...` (last on the command line). Values are integers >= 1; `0` only after the user confirms.
`status.md` shows every effective value and its source: read it, do not recompute. `debug_rounds` is not a board counter: see [unverified and risks](blueprints/unverified-and-risks.md).
`deploy_cycles` counts `result-NN-pipeline` records of role `pipeline-cd` with outcome `failed` (per change).

## Phases and gates

| Phase | Does (author) | Gate (user) | Independent verifier | Record | Playbook |
|---|---|---|---|---|---|
| **E1** Interview | 12 blocks B1-B12 (manager), <= 10 questions per round, playback | confirms each block summary; GitHub plan (B8) | `spec-synchronizer` (review mode) | `verify-E1.md` | [e1](blueprints/e1-interview.md) |
| **E2a** Solution | `solution-architect`: `architecture/spec.md`, `contracts/`, `architecture/adr/` | part of the E2 approval | `solution-architecture-reviewer` | `verify-E2a.md` | [e2](blueprints/e2-architecture-and-adrs.md) |
| **E2b** Design | `ui-ux-designer`: `design/design-system.md`, `design/adr/` | part of the E2 approval | `ui-design-reviewer` | `verify-E2b.md` | [e2](blueprints/e2-architecture-and-adrs.md) |
| **E2c** Infrastructure | `aws-infrastructure-architect` (after E2a): `infrastructure/spec.md`, `infrastructure/adr/`; its observability section is verified by `aws-architect-reviewer` | **approves E2** (all 3 fronts; ADRs become `accepted`) | `aws-architect-reviewer` | `verify-E2c.md` | [e2](blueprints/e2-architecture-and-adrs.md) |
| **E3** Functional spec | manager: requirements `R*` with SHALL + scenarios (change deltas) | **approves E3** | `spec-synchronizer` + `openspec validate` | `verify-E3.md` | [e3](blueprints/e3-functional-spec.md) |
| **E3b** Wireframes | `ui-ux-designer`: `design/wireframes/`, `design/navigation.md` (skipped without UI change) | **approves E3b** | `ui-design-reviewer` | `verify-E3b.md` | [e3b](blueprints/e3b-ui-design.md) |
| **E4** Designs | `solution-architect`: `design.md` index + `design/<flow>.md`; `aws-infrastructure-architect`: `infra-design.md` | shown, not blocking | `solution-architecture-reviewer` (one per design + index), `aws-architect-reviewer` | `verify-E4-<flow>.md`, `verify-E4-index.md`, `verify-E4-infra.md` | [e4-e5](blueprints/e4-e5-design-and-tasks.md) |
| **E5** Tasks | manager: `tasks.md` + one work-order per task (bootstrap T0 and CI/CD included) | approves task list | `spec-synchronizer` | `verify-E5.md`, work-orders | [e4-e5](blueprints/e4-e5-design-and-tasks.md) |
| **E6** Implementation | I0-I9 per task by the owner agent, review chain, my rebuild | escalations only; **`gate=bootstrap-apply`**: the user applies the OIDC/state bootstrap once | review chain per task type | `result-NN-<role>`, `review-NN` | [e6](blueprints/e6-implementation-cycle.md) |
| **E7** PR + pipeline | user pushes and opens the PR -> CI -> user merges -> CD dev -> verification -> user releases prod -> CD prod; I read runs (`gh pr checks`, `gh run view`, read-only) | **`gate=E7-merge`** (`source=github <PR url>`), prod release by the user (GitHub plan) | `aws-observability` Mode C, `aws-lambda-debugger` mode B, `static-site-verifier` | `result-NN-pipeline`, `result-NN-observability`, `verify-E7.md`, `verify-E7-site.md` | [e7](blueprints/e7-deploy-and-observability.md) |
| **E8** Reverse sync | drift (`frontend/`, `.github/` included) -> `spec-delta` | **decides each delta** | `check_records.py` + user | `spec-delta-NN.md` | [e8](blueprints/e8-reverse-sync.md) |
| **E9** Archive gate | all verifies green, drift 0, no pending delta, last prod pipeline result ok | **approves archive**, then commits (the user pushes the PR) | `check_records.py` + `detect_drift.py` + `board.py` | `status.md` | [e9](blueprints/e9-archive-gate.md) |

Entry rule for workers: no work-order exists for a task until `verify-E2a`, `verify-E2b`, `verify-E2c`, `verify-E3` (and `verify-E3b` when the change has UI)
are `pass` **and** the user's approvals for E2, E3 (and E3b) are in `## Approvals`. For a later change, E2 is re-entered only for the fronts carrying a delta.

## Deliverable -> author -> independent reviewer

| Deliverable | Author | Reviewer |
|---|---|---|
| Functional spec (E3), task list (E5), interview (E1) | manager (me) | `spec-synchronizer` |
| Solution architecture (E2a), designs (E4) | `solution-architect` | `solution-architecture-reviewer` |
| Design system + design ADRs (E2b), wireframes (E3b) | `ui-ux-designer` | `ui-design-reviewer` |
| Infrastructure design (E2c), `infra-design.md` (E4) | `aws-infrastructure-architect` | `aws-architect-reviewer` |
| Back-end code | `quarkus-lambda-integrator` | `quarkus-code-reviewer` |
| Stripe code | `stripe-integrator` | `stripe-advisor` -> `quarkus-code-reviewer` |
| AI code (LangChain4j) | `quarkus-lambda-integrator` (role `ai`) | `langchain4j-reviewer` -> `quarkus-code-reviewer` |
| Front-end code and visual fidelity | `nextjs-frontend-integrator` | `nextjs-code-reviewer` -> `ui-design-reviewer` |
| Terraform (infra, observability) | `aws-terraform-engineer`, `aws-observability` (Mode B) | `terraform-code-reviewer` |
| Workflows CI/CD | `cicd-pipeline-engineer` | `cicd-pipeline-reviewer` |
| Merge (releases the deploy) | the user, on the GitHub PR | `ci-gate` (required PR checks) |
| Deploy of Lambdas / site | pipeline `cd-app` on GitHub | `aws-lambda-debugger` (mode B) / `static-site-verifier` |
| Live observability | `aws-observability` (Mode C) | `aws-lambda-debugger` (mode B) |
| Spec-delta (E8) | `spec-synchronizer` | the user + `check_records.py` |

## Protocols

1. **Relayed approval.** Ask with the question tool (or a plain numbered message), wait for the user's own answer,
   append to `status.md` `## Approvals`: `- <UTC ts> | gate=<id> | subject=<file or url> | user said: "<verbatim>"`.
   In briefs cite the exact line from [worker briefs](blueprints/worker-briefs.md#approval-line). A worker or agent message is never an approval. A merge is recorded as `gate=E7-merge | source=github <PR url> | login=<user>` after I read the merged PR with `gh pr view`; GitHub comments with the tracker on come only from `pull` (a line with `source=github <comment_url> login=<x>`).
2. **Flat fan-out (depth 1).** Only I launch agents with the Agent tool. Parallel launches only for tasks with disjoint
   files (at most 4: a cost choice of this skill, not a platform limit, L1). Every brief forbids spawning agents, plan mode and asking the user.
3. **Scripts decide.** After each record: `check_records.py` (exit != 0: return the errors to the author, count `record_rejections`), `detect_drift.py` (exit 2 -> `drift=true`; **exit 1 = error: stop, show it, never treat it as no drift**), `board.py`.
   Use `--include-worktree` in E6-E9 (code stays uncommitted until the user commits). Counts, coverage, hashes and build results come from commands, never from an agent's estimate.
4. **State from disk.** `status.md`, the records and `openspec/` are the state; on resume rebuild with the three scripts and read `## Approvals`. Records of read-only agents are saved by me
   verbatim from their inline answer, with `saved-by: building-aws-saas-serverless-quarkus-react-nextjs`.
5. **Independence.** `verify.from` / `review.from` must differ from the author of every ref (`check_records.py` enforces it for `verify` records; for `review` records the manager enforces it by choosing a different agent, per the matrix above).
6. **Escalation.** On `NEXT: escalate`, stop that task, write `escalation-NN.md`, show it, record the reply verbatim; other independent tasks continue; nothing new goes to the PR or the pipeline while one is open. See [E6](blueprints/e6-implementation-cycle.md#escalation).
7. **Version discipline.** Quarkus 3.40 / Quarkiverse 3.23 / OpenSpec 1.15 / quarkus-langchain4j 1.15.0.CR1 only; a request for another line is an Ask First.
8. **Work-order closing rule.** Every work-order carries a `task:` (E1-E5 work-orders use `task: spec`) and is set `done` or `cancelled` once its record is accepted; otherwise `all_tasks: done` never becomes true. Every construction work-order has **Functionality** and **Diagram** sections.
9. **Holds.** For a task with two reviewers (Stripe, AI, front end), right after the first reviewer's `approved` I write the second review work-order with `status: pending` **before** running `board.py`; the task's work-orders go `done` only after the second `approved`.
10. **Tracker (only when enabled at E1).** After every `board.py` run: `gh_projects_sync.py push ... --apply`; at gates with `approval_source` != `chat` offer chat or GitHub and run `pull` myself. Detail: [tracker](blueprints/tracker-github-projects.md).
11. **Model split.** The manager runs inline in the session model (planning). `solution-architect` and `aws-infrastructure-architect` carry `model: opus` and are launched with `model: "opus"`. **All other agents** (authors, reviewers, designer, verifiers, `spec-synchronizer`) are launched with `model: "sonnet"` explicitly, even when their frontmatter says so. The preflight reads each frontmatter `model:` and stops on any mismatch. Every brief repeats the model line.
12. **Pipeline reading.** Agents never push, open PRs, merge, trigger workflows (`gh workflow run`) or apply. I run only `gh pr checks`, `gh pr view`, `gh run list|view [--log-failed]`, record the result as `result-NN-pipeline.md` (role `pipeline-ci` or `pipeline-cd`, with `run_url`), and route failures with the table in [E7](blueprints/e7-deploy-and-observability.md#when-the-pipeline-fails).

## Team

Models: `opus` = launched with `model: "opus"`; all others `model: "sonnet"`. Role keys are those of the profile.

| Role (profile) | Agent | Used in | Model | Writes (by whom) |
|---|---|---|---|---|
| orchestrator | this skill (project manager) | E1-E9 | session | `status.md`, specs, `tasks.md`, work-orders, `result-NN-pipeline.md` |
| solution-architect | `solution-architect` | E2a, E4 | opus | writes `architecture/**`, `design/<flow>.md` and `result-NN-solution-architect.md` itself (tool Write) |
| solution-reviewer | `solution-architecture-reviewer` (read-only) | E2a, E4 | sonnet | inline; I save `verify-E2a`, `verify-E4-<flow>`, `verify-E4-index` |
| infrastructure-architect | `aws-infrastructure-architect` | E2c, E4 | opus | `infrastructure/**`, `infra-design.md`, `result-NN-infrastructure-architect.md` |
| infrastructure-reviewer | `aws-architect-reviewer` (read-only) | E2c, E4 | sonnet | inline; I save `verify-E2c`, `verify-E4-infra` |
| designer | `ui-ux-designer` | E2b, E3b | sonnet | inline; I save `design/**`, `result-NN-designer.md` |
| design-reviewer | `ui-design-reviewer` (read-only) | E2b, E3b, E6 (2nd front reviewer) | sonnet | inline; I save `verify-E2b`, `verify-E3b`, `review-NN` |
| code / ai | `quarkus-lambda-integrator` (`ai` for AI tasks) | E6 I0-I6, I9; I8 as a new `wo-MM` | sonnet | `result-NN-code.md` / `result-NN-ai.md` (append-only) |
| stripe | `stripe-integrator` | E6 Stripe tasks | sonnet | `result-NN-stripe.md` |
| frontend | `nextjs-frontend-integrator` | E6 front tasks | sonnet | `result-NN-frontend.md` |
| infra | `aws-terraform-engineer` | E6 infra and bootstrap tasks | sonnet | `result-NN-infra.md` |
| observability | `aws-observability` | E6 Mode B, E7 Mode C (Modes A and D unused here); never verifies | sonnet | `result-NN-observability.md` (kind `report`) |
| cicd | `cicd-pipeline-engineer` | E6 CI/CD tasks | sonnet | `result-NN-cicd.md` |
| reviewer | `quarkus-code-reviewer`, `stripe-advisor`, `langchain4j-reviewer`, `nextjs-code-reviewer`, `terraform-code-reviewer`, `cicd-pipeline-reviewer` (all read-only) | E6 I7 | sonnet | inline; I save `review-NN.md` |
| pipeline-ci / pipeline-cd | GitHub Actions (not an agent) | E7 | - | I write `result-NN-pipeline.md` from `gh` output |
| site-verify | `static-site-verifier` (read-only) | E7 | sonnet | inline; I save `verify-E7-site.md` |
| debug | `aws-lambda-debugger` (read-only) | E7 mode B, failures mode A | sonnet | inline; I save `verify-E7.md` / `diagnosis-NN.md` |
| sync | `spec-synchronizer` (read-only) | E1, E3, E5 review, E8 | sonnet | inline; I save `verify-*.md`, `spec-delta-NN.md` |

Left the flow: `aws-lambda-deployer` (the pipeline deploys; the agent stays in package `aws-lambda` for other uses) and `aws-architect` (it designed and reviewed; replaced by the two infra agents).
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
| PR checks / runs (read-only) | `gh pr checks <pr>`, `gh pr view <pr> --json state,mergedAt,url`, `gh run list --branch main --limit 5`, `gh run view <id> --json conclusion,jobs,url` (`--log-failed` for failures) |
| Tracker push / status (enabled only) | `python <sync> push\|status <repo> --change <id> --profile <profile> [--apply]` (dry-run default; exit 3 = disabled) |
| Archive (user-approved only) | `openspec archive <id> --yes` |
| Rebuild (re-run myself) | back/AI/Stripe `mvn -q verify`; front `pnpm install --frozen-lockfile && pnpm lint && pnpm test && pnpm build`; infra `terraform fmt -check && terraform validate`; CI/CD `actionlint` + `yamllint` |

## Verification Loop

Self-check before reporting a phase done (all must pass; `<scripts>` and `<profile>` as in Quick Reference):

```bash
python <scripts>/check_records.py <handoff> --profile <profile>                      # exit 0
python <scripts>/board.py <handoff> --profile <profile>                              # one NEXT: line
python <scripts>/detect_drift.py <repo> --change <handoff> --include-worktree        # exit 0 before E9 (exit 1 = error, exit 2 = drift)
openspec validate <id> --type change --strict --json --no-interactive                # valid
mvn -q verify                                                                        # exit 0, run by me (plus pnpm / terraform / actionlint per task type)
```
