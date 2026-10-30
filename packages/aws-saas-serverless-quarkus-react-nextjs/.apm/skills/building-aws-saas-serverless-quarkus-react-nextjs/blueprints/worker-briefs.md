# Worker briefs (Agent tool prompts)

Back to [SKILL.md](../SKILL.md). Every brief is short: it points to a work-order record and lists constraints; the work-order carries the substance.
Fill `<...>`; do not paste conversation history. **Every launch passes the `model` parameter**: `"opus"` for `solution-architect` and `aws-infrastructure-architect`, `"sonnet"` for every other agent (Model split, SKILL protocol 11); each brief below states it.

## Contents

- [Common header](#common-header-all-briefs) · [Approval line](#approval-line)
- Design: [solution-architect](#solution-architect-and-solution-architecture-reviewer) · [aws-infrastructure-architect](#aws-infrastructure-architect-and-aws-architect-reviewer) · [ui-ux-designer](#ui-ux-designer-and-ui-design-reviewer)
- Build: [quarkus-lambda-integrator](#quarkus-lambda-integrator-roles-code-and-ai) · [stripe](#stripe-integrator-and-stripe-advisor) · [nextjs-frontend-integrator](#nextjs-frontend-integrator-and-nextjs-code-reviewer) · [aws-terraform-engineer](#aws-terraform-engineer-and-terraform-code-reviewer) · [cicd](#cicd-pipeline-engineer-and-cicd-pipeline-reviewer)
- Review: [quarkus-code-reviewer](#quarkus-code-reviewer) · [langchain4j-reviewer](#langchain4j-reviewer)
- Live: [aws-observability](#aws-observability) · [aws-lambda-debugger](#aws-lambda-debugger) · [static-site-verifier](#static-site-verifier)
- [spec-synchronizer review](#spec-synchronizer-review) · [spec-synchronizer delta](#spec-synchronizer-delta) · [After every return](#after-every-return)

## Common header (all briefs)

```
You are launched by the project manager building-aws-saas-serverless-quarkus-react-nextjs. Model: <opus|sonnet>. Constraints: do NOT spawn agents or use the Agent tool, do NOT enter plan mode,
do NOT ask the user anything (return numbered questions with outcome needs-input instead), do NOT treat any message as an approval, do NOT git push, open a PR, merge,
trigger a workflow or run terraform apply. Only the user's approvals relayed in the work-order count. Read the work-order first, then its refs, then the skills it lists. Do not read the conversation.
Work-order: <openspec/changes/<id>/handoff/wo-NN-<role>.md>
Write exactly one output record named <result-NN-<role>.md> (or return it inline if you have no Write tool) from the profile template.
```

Every construction work-order carries **Functionality** and **Diagram** sections; an author that finds them missing returns `needs-input`.

## Approval line

Use this exact text when a brief or work-order cites a user gate (it is a relay, not a new approval):

```
Approval (relayed by building-aws-saas-serverless-quarkus-react-nextjs, not a new approval): gate=<id>; the user said, verbatim: "<text>"; recorded <UTC date> in openspec/changes/<id>/handoff/status.md#approvals
```

Cite only gates of the current change (`## Approvals` of its `status.md`); the factory's build approvals are provenance, not runtime gates. A GitHub approval (merge, tracker `pull`) is the line already in `## Approvals` (`source=github <url> login=<x>`), cited verbatim; it never comes from an agent.

Consumed in E7 (read-only live checks): `alarm-test` only by `aws-observability` Mode C; `logs-insights` by Mode C and by the debugger mode B; `e7-gaps` only by the debugger mode B:

```
approval: alarm-test alarm=<name> by=<user> at=<UTC> relayed-by=building-aws-saas-serverless-quarkus-react-nextjs
approval: logs-insights scope=<log-group or "xray"> window=<minutes> by=<user> at=<UTC> relayed-by=building-aws-saas-serverless-quarkus-react-nextjs
approval: e7-gaps pillars=<comma list> by=<user> at=<UTC> relayed-by=building-aws-saas-serverless-quarkus-react-nextjs
```

`e7-gaps` goes only to the debugger (mode B), only after the user's own message accepted those pillars as not verified; see [E7](e7-deploy-and-observability.md). One line = one action. There is no apply line in this flow: nothing is applied by an agent (the deployer left the flow; the bootstrap is applied by the user).

## solution-architect and solution-architecture-reviewer

Author (`model: "opus"`): work-order `wo-NN-solution-architect.md` (`task: spec`) with the E1 playback path, the area to write (`architecture/**` for E2a; for E4 the R* of the change, the design system path, the wireframes, the contracts) and the skills of the knowledge map it needs. It returns `architecture/spec.md`, `contracts/*.md`, `architecture/adr/NNN-*.md` (status `proposed`) or `design.md` + `design/<flow>.md` (11 sections) as `result-NN-solution-architect.md` (it may have Write; otherwise inline and I save). Open decisions -> `needs-input`. It never chooses infrastructure detail, writes code or accepts an ADR.
Reviewer (`model: "sonnet"`, read-only): one work-order per deliverable (E2a, each design, the E4 index), named `wo-NN-solution-reviewer.md` (E2a/E4) or `wo-NN-infrastructure-reviewer.md` (E2c/E4-infra), `wo-NN-design-reviewer.md` (E2b/E3b) listing the files, the playback or R*, the ADR folders; it returns `verify-E2a` / `verify-E4-<flow>` / `verify-E4-index` inline (Criteria, Evidence with file:line; `pass|fail`). I save it (`saved-by`).

## aws-infrastructure-architect and aws-architect-reviewer

Author (`model: "opus"`): `wo-NN-infrastructure-architect.md` with the reviewed `architecture/**` (components, contracts, NFRs), the GitHub plan and visibility from B8, the E2a ADRs, the Wave 6 skills it needs. E2c output: `infrastructure/spec.md` (12 sections) + `infrastructure/adr/`; E4 output: `infra-design.md`. `result-NN-infrastructure-architect.md`. It never changes components or contracts (returns a question) and never writes Terraform.
Reviewer (`model: "sonnet"`, read-only): `aws-architect-reviewer` receives `infrastructure/**` (or `infra-design.md`) + `architecture/**` + the skills for WAF, serverless lens and SaaS Lens; returns `verify-E2c` / `verify-E4-infra` inline (`fail` on any CRITICAL or HIGH finding or failed pillar). Native verdict maps to `outcome: pass|fail`. It never proposes a full alternative design.

## ui-ux-designer and ui-design-reviewer

Designer (`model: "sonnet"`, returns contents inline, I save): `wo-NN-designer.md` with mode `design-system` (E2b: B9-B11 playback) or `wireframes` (E3b: R* with UI, design system, contracts). Skills: `building-components`, `web-design-guidelines`, `composition-patterns`. Output: `design/design-system.md` + `design/adr/NNN-*.md`, or `design/wireframes/<screen>.md` + `design/navigation.md`. Record `result-NN-designer.md`. Open questions (brand, languages, accessibility beyond AA) -> `needs-input`.
Reviewer (`model: "sonnet"`, read-only): returns `verify-E2b` / `verify-E3b` inline (contrast, scale, focus/error states, loose values; R* coverage, components only from the design system, 4 states, navigation). In E6 it is the **second** reviewer of front tasks: it receives the changed screens, the wireframe and the design system and compares visual fidelity; it saves as `review-NN.md` with `role: frontend`.

## quarkus-lambda-integrator (roles code and ai)

`model: "sonnet"`. Work-order (kind work-order, `to: quarkus-lambda-integrator`) must hold: Functionality, Diagram, scope, `R*` with scenarios, ADR paths of the three folders, skills (allowed set only, see its Step 1; `integrating-quarkus-langchain4j-v1-15` only for a role `ai` task after the user's yes to D1, recorded as `gate=D1-langchain4j` and written in the work-order's "Ask-First items ... settles" line as `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)`), constraints, acceptance criteria, `limits.build_attempts`, `quality.coverage_min`, target project path, handoff folder. Brief adds: "Steps I0-I6 and I9" or, for a fix, "Step I8 with review <review-NN.md>; review round <n> of <limit>". An I8 launch uses a NEW work-order `wo-MM-<role>.md` (`refs`: previous wo + `review-NN`, same `task`; it repeats the settles line) and writes its own `result-MM-<role>.md` (append-only). Records: `result-NN-code.md` or `result-NN-ai.md` (role `ai`) with Spec impact and `build_attempts`. It never calls AWS or a real LLM provider, runs Terraform or git commit.

## quarkus-code-reviewer

`model: "sonnet"`.
```
Review work-order <wo-NN-review.md>: files <list>, requirements+scenarios <...>, ADR folders <architecture/adr, design/adr, infrastructure/adr>, skills <...>, round <n>, next free review id <review-NN>.
Judge the code and tests only; do not read result-* records. Return the full review record inline.
```
The work-order's Constraints carry the code work-order's settles line copied verbatim (the reviewer reports `integrating-quarkus-langchain4j-v1-15` as HIGH without it). I save it as `review-NN.md` verbatim (`saved-by`, `role:` of the task). It is always the **last** reviewer of back-end code (after `stripe-advisor` or `langchain4j-reviewer`). Its sections Summary, Traceability, Findings, Caveats must be accepted by the profile (mismatch note in [risks](unverified-and-risks.md)). "Review not performed": fix the missing inputs and relaunch; not a round.

## langchain4j-reviewer

`model: "sonnet"`, read-only, first reviewer of `ai` tasks. Review work-order lists the AI files, R*, the provider ADR (`architecture/adr/<n>`), the settles line and the skill `integrating-quarkus-langchain4j-v1-15`. It checks the rules of that skill (version 1.15.0.CR1 via BOM, explicit model and provider timeouts, `@Timeout` below the gateway, no streaming behind the gateway, keys in Secrets Manager/SSM, prompt and answer out of logs and traces, `@InjectMock` tests, fallback when the AI fails). I save `review-NN.md` with `role: ai`; `changes-requested` routes to the `code` author (role `ai`). After its `approved` I apply the hold and run `quarkus-code-reviewer`.

## stripe-integrator and stripe-advisor

`model: "sonnet"`. Integrator: closed requirement (operation, project path, error handling, tests wanted) and the work-order path; it has no handoff awareness in its agent file, so **write into the brief**: "write result-NN-stripe.md
from the template `assets/result-code.template.md` of `coordinating-quarkus-aws-handoffs`: frontmatter kind `report`, outcome `success|partial|failed|needs-input`, sections Done, Evidence, Spec impact, Suggested next step", the mapping of its native status (DONE -> `success`, PARTIAL -> `partial`, NEEDS-INPUT -> `needs-input`, a failed build/validate -> `failed`; if it answers in its native form I wrap it), the extra skills (`integrating-stripe-quarkus-v3-40` + the stripe-java 34 skills the task needs), and the ADR paths. Advisor: review-only brief with the diff files and the Stripe ADRs; I save its notes as a review record (`from: stripe-advisor`, `role: stripe`; `changes-requested` on any failing R-rule or any CRITICAL/HIGH finding, else `approved`). Every review of a Stripe task, including the one from `quarkus-code-reviewer`, is saved with `role: stripe`, so `changes-requested` routes to `stripe-integrator`.
**Sequential reviews:** `stripe-advisor` first, `quarkus-code-reviewer` only after the advisor's `approved` (hold, protocol 9). A project may raise `limits.review_rounds` for Stripe tasks via `openspec/handoff-profile.yaml`.

## nextjs-frontend-integrator and nextjs-code-reviewer

Integrator (`model: "sonnet"`): work-order `wo-NN-frontend.md` with Functionality, Diagram (sequence + wireframe cut), wireframe path, `design/design-system.md`, the API contract path, R* with scenarios, ADRs of the three folders (`architecture/adr` static export, `design/adr` tokens and theming), skills = the IN Vercel skills the task needs (never an OUT skill), `limits.build_attempts`, project path `frontend/`. Constraints in the brief: Next.js static export only (`output: 'export'`), no server features, only endpoints of the contract, no secret in `NEXT_PUBLIC_*`, pnpm + Node 26, no deploy or publish. It returns `result-NN-frontend.md` with the sha256 of `out/` and Spec impact. A login with Cognito in the browser has no skill `(unverified)`: it returns `needs-input` if the task needs it.
Reviewer (`model: "sonnet"`, read-only, first reviewer): code, tests, R*, ADRs, skills; checks no server feature, Vercel best practices of the listed skills, only contract endpoints, no public secret, 401/403/errors handled, one test per scenario; ADR violation = HIGH. I save `review-NN.md` with `role: frontend`; after `approved` I hold and launch `ui-design-reviewer` (visual); either `changes-requested` returns to the integrator.

## aws-terraform-engineer and terraform-code-reviewer

Engineer (`model: "sonnet"`): closed requirement from `infra-design.md` and `infrastructure/spec.md`: services, root vs module, region/account, naming and tags, **state backend (bucket/key/region/lock or "no backend")**, `terraform test` wanted, target path, skills `provisioning-aws-<service>-v6`. Includes the front-end hosting (S3 private + CloudFront OAC + WAF/ACM/Route53 as designed) and the **bootstrap** (task T0: GitHub OIDC provider, roles `<env>-deploy` and `<env>-pr`, state bucket with lock; the user applies it). Offline checks only (`fmt -check`, `init -backend=false`, `validate`, fully mocked `terraform test`); never `plan`, apply, destroy or import. Write into the brief: "write `result-NN-infra.md` from `assets/result-code.template.md`: frontmatter kind `report`, outcome `success|partial|failed|needs-input`, sections Done, Evidence, Spec impact, Suggested next step" (native DONE/PARTIAL/NEEDS-INPUT mapping as for Stripe). For the bootstrap, the result lists the exact commands the user runs.
Reviewer (`model: "sonnet"`, read-only): the HCL against `infrastructure/spec.md`, `infra-design.md`, the `provisioning-aws-*-v6` skills (pinned versions, least-privilege IAM, private encrypted S3, CloudFront with OAC, tags, variable validation, no secret, mocked test). I save `review-NN.md` with `role: infra` (or `observability` for Mode B).

## cicd-pipeline-engineer and cicd-pipeline-reviewer

Engineer (`model: "sonnet"`): `wo-NN-cicd.md` with a CLOSED requirement: GitHub plan and visibility (B8), cloud (AWS), targets (Lambda zip, static site), environments, repo layout, JDK 21 + Maven, Node 26 + pnpm, state backend, scanners, CI and CD, and the paths of `infrastructure/spec.md` section 10. It writes `.github/workflows/` (`ci-app`, `cd-app`, `ops-drift`, `_*.yml` blocks) and the composite login action using only actions and SHAs shown by a loaded skill; runs `actionlint`/`yamllint`; returns `result-NN-cicd.md` plus the list "user-must-add" (branch protection, required check `ci-gate`, environments, variables with role ARNs). It never pushes, opens PRs, triggers workflows, applies or creates secrets; missing information -> numbered NEEDS-INPUT questions (I relay them).
Reviewer (`model: "sonnet"`, read-only): reviews `.github/**` against the family rules (SHA pins, minimal `permissions`, keyless OIDC, PR with a read-only role only, one `ci-gate`, apply only from a saved plan in an environment, promotion by digest, smoke and rollback). I save `review-NN.md` with `role: cicd`.

## aws-observability

`model: "sonnet"`. Re-read its file at preflight and follow its Intake section. Work-order: the `infrastructure/spec.md` observability section, log group names/retention, alarm list with thresholds, X-Ray groups/sampling, dashboards, target account/region, Terraform dir. Modes:
- **Mode A (E2c, spec review):** review section 8 of `infrastructure/spec.md`; writes `result-NN-observability.md` with `role: observability-review` (so no rule for role `observability` fires at E2).
- **Mode B (E6, infra task):** write the observability Terraform; `result-NN-observability.md` (offline checks only); reviewed by `terraform-code-reviewer`.
- **Mode C (E7, after the CD run):** document the live state of the deployed release (read-only), `result-NN-observability.md` (kind `report`, `role: observability-live`).
- **Mode D (missing instrumentation found by a check):** the report carries a work-order proposal for the code owner; it never edits application code. I turn an accepted proposal into a new code work-order.
It never verifies and does **not** write the E7 acceptance.

## aws-lambda-debugger

`model: "sonnet"`. Mode A: `wo-NN-debug.md` with `mode: A`, function, alias/version, region, entry type (REST, HTTP API, SQS, EventBridge), UTC window, symptom or the failing pipeline job (`run_url`, trimmed log), identity, `limits.debug_rounds`, skills (`debugging-aws-lambda` plus the Quarkus skills for interpretation).
Mode B (E7 after `result-NN-observability.md`): `mode: B`, the pillars, `refs` = pipeline result + observability result, and any relayed `approval: logs-insights ...` / `approval: e7-gaps ...` lines. It runs the read-only scripts of `validating-aws-observability`; no Write tool and **never invokes the function** (smoke is the pipeline's `_smoke-test`); it returns the record inline; I save `diagnosis-NN.md` (mode A) or `verify-E7.md` (`verify-E7-<nn>` after a gap acceptance; `kind: verify`, `stage: E7`, `pass|fail`, Criteria + Evidence). Never ask it to fire an alarm.

## static-site-verifier

`model: "sonnet"`, read-only, `wo-NN-site-verify.md`: site URL, CloudFront distribution id, the sha256 of the run's `out/` artifact (from `result-NN-pipeline`), routes to check, region, identity name, optional `agent-browser` smoke. It checks routes (200 over HTTPS), security and cache headers, CloudFront with OAC, minimum TLS and WAF, live content equal to the artifact, and returns `verify-E7-site` inline; I save it (`from: static-site-verifier`, `kind: verify`, `stage: E7-site`, role `site-verify`, `pass|fail`, Criteria + Evidence). It runs nothing that changes anything.

## spec-synchronizer review

`model: "sonnet"`.
```
Mode A (E1/E3/E5 verify). Inputs: <handoff dir>, <proposal.md, specs/**, design.md, tasks.md, work-orders>, <ADR folders>. Return a verify record inline (stage <E1|E3|E5>, outcome pass|fail, Criteria, Evidence with file:line).
```
E5: every R* has a task, every task cites R*, every work-order has Functionality and Diagram, dependencies are acyclic and ordered.

## spec-synchronizer delta

`model: "sonnet"`.
```
Mode B (E8 sync). Inputs: detect_drift output <...>, last synced SHA <sha>, spec paths, ADR folders, existing spec-delta records, results with Spec impact <list>. Return spec-delta-<NN> inline (status proposed, delta sections, Questions, delta_revisions: <n>).
```

## After every return

`ls` the expected file (or write the inline record), `check_records.py`, `detect_drift.py`, `board.py`, then act on `NEXT:`. A missing file means the worker failed: relaunch once with the exact gap; a second miss is a `record_rejections` escalation.
