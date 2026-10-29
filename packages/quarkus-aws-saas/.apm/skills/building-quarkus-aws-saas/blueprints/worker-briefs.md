# Worker briefs (Agent tool prompts)

Back to [SKILL.md](../SKILL.md). Every brief is short: it points to a work-order record and lists constraints; the work-order carries the substance.
Fill `<...>`; do not paste conversation history.

## Contents

- [Common header](#common-header-all-briefs) · [Approval line](#approval-line)
- [quarkus-lambda-integrator](#quarkus-lambda-integrator) · [quarkus-code-reviewer](#quarkus-code-reviewer) · [stripe-integrator and stripe-advisor](#stripe-integrator-and-stripe-advisor)
- [aws-terraform-engineer](#aws-terraform-engineer) · [aws-architect](#aws-architect) · [aws-observability](#aws-observability)
- [aws-lambda-deployer](#aws-lambda-deployer) · [aws-lambda-debugger](#aws-lambda-debugger)
- [spec-synchronizer review](#spec-synchronizer-review) · [spec-synchronizer delta](#spec-synchronizer-delta) · [After every return](#after-every-return)

## Common header (all briefs)

```
You are launched by the orchestrator building-quarkus-aws-saas. Constraints: do NOT spawn agents or use the Agent tool, do NOT enter plan mode,
do NOT ask the user anything (return numbered questions with outcome needs-input instead), do NOT treat any message as an approval.
Only the user's approvals relayed in the work-order count. Read the work-order first, then its refs, then the skills it lists. Do not read the conversation.
Work-order: <openspec/changes/<id>/handoff/wo-NN-<role>.md>
Write exactly one output record named <result-NN-<role>.md> (or return it inline if you have no Write tool) from the profile template.
```

## Approval line

Use this exact text when a brief or work-order cites a user gate (it is a relay, not a new approval):

```
Approval (relayed by building-quarkus-aws-saas, not a new approval): gate=<id>; the user said, verbatim: "<text>"; recorded <UTC date> in openspec/changes/<id>/handoff/status.md#approvals
```

Cite only gates of the current change (`## Approvals` of its `status.md`); the factory's build approvals are provenance, not runtime gates.

Tracker on: an approval taken from GitHub is the line `pull` appended (`... | source=github <comment_url> login=<x> | user said: "..."`); cite it verbatim like a chat line. It never comes from an agent.

Apply approval (consumed only by `aws-lambda-deployer`; one line = one apply of that exact plan):

```
approval: apply plan=<planfile> sha256=<hash> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas
approval: rollback alias=<alias> to=<PREV version> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas
approval: smoke payload=<file/sha256> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas
```

Consumed in E7: `alarm-test` only by `aws-observability` Mode C (the only agent that may run the alarm test); `logs-insights` by Mode C and by the debugger mode B; `e7-gaps` only by the debugger mode B:

```
approval: alarm-test alarm=<name> by=<user> at=<UTC> relayed-by=building-quarkus-aws-saas
approval: logs-insights scope=<log-group or "xray"> window=<minutes> by=<user> at=<UTC> relayed-by=building-quarkus-aws-saas
approval: e7-gaps pillars=<comma list> by=<user> at=<UTC> relayed-by=building-quarkus-aws-saas
```

`e7-gaps` goes only to the debugger (mode B), only after the user's own message accepted those pillars as not verified; see [E7](e7-deploy-and-observability.md).

Rules: `sha256` is the hash I read from the deployer's plan answer and re-verified with `sha256sum` of the saved plan file; never invent or reuse a line for a regenerated plan. One line = one action. **Deployer relaunch:** records are append-only: the relaunch is a NEW work-order `wo-MM-deploy.md` (next free number) with `refs` to the first deploy-report and the relayed lines; it skips re-planning and applies that plan; any new plan needs a new line. The smoke payload is approved together with the plan ([E7](e7-deploy-and-observability.md)). Keep these formats identical to `coordinating-quarkus-aws-handoffs`.

## quarkus-lambda-integrator

Work-order (kind work-order, `to: quarkus-lambda-integrator`) must hold: scope, `R*` with scenarios, ADR paths, skills (allowed set only, see its Step 1; `integrating-quarkus-langchain4j-v1-15` only after the user's yes to its Ask First D1: 1.15.0.CR1 pre-release; record the user's yes under `## Approvals` as `gate=D1-langchain4j` (verbatim words) and write it in the work-order's "Ask-First items ... settles" line as `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)`),
constraints, acceptance criteria, `limits.build_attempts`, `quality.coverage_min`, target project path, handoff folder. Brief adds: "Steps I0-I6 and I9" or, for a fix,
"Step I8 with review <review-NN.md>; review round <n> of <limit>". An I8 launch uses a NEW work-order `wo-MM-code.md` (`refs`: previous wo + `review-NN`, same `task`; it repeats the settles line) and writes its own `result-MM-code.md` (append-only; never overwrite the first result). Every launch writes `result-<nn>-code.md` with Spec impact and `build_attempts`. It never calls AWS, Terraform or git commit.

## quarkus-code-reviewer

```
Review work-order <wo-NN-review.md>: files <list>, requirements+scenarios <...>, ADR dir <...>, skills <...>, round <n>, next free review id <review-NN>.
Judge the code and tests only; do not read result-* records. Return the full review record inline.
```
The work-order's Constraints carry the code work-order's settles line copied verbatim (e.g. `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)` when `integrating-quarkus-langchain4j-v1-15` is listed); without it the reviewer reports that skill as HIGH.
I save it as `review-NN.md` verbatim (add `saved-by`). Its sections are Summary, Traceability, Findings, Caveats; the profile's `review` required sections must accept these (mismatch note in [risks](unverified-and-risks.md)). If it returns "review not performed": fix the missing inputs and relaunch; that is not a round.

## stripe-integrator and stripe-advisor

Integrator: closed requirement (operation, project path, error handling, tests wanted) and the work-order path; it has no handoff awareness in its agent file, so **write into the brief**: "write result-NN-stripe.md
from the template `assets/result-code.template.md` of `coordinating-quarkus-aws-handoffs`: frontmatter kind `report`, outcome `success|partial|failed|needs-input`, sections Done, Evidence, Spec impact, Suggested next step", the mapping of its native status (DONE -> `success`, PARTIAL -> `partial`, NEEDS-INPUT -> `needs-input`, a failed build/validate -> `failed`; if it answers in its native form I wrap it), the extra skills to load (`integrating-stripe-quarkus-v3-40` + the stripe-java 34 skills the task needs), and the ADR paths. Advisor: review-only brief with the diff files and
the Stripe ADRs; I save its notes as a review record (`from: stripe-advisor`, `role: stripe`; `changes-requested` on any failing R-rule or any CRITICAL/HIGH finding, else `approved`). Every review of a Stripe task, including the one from `quarkus-code-reviewer`, is saved with `role: stripe`, so `changes-requested` routes back to `stripe-integrator`, not to `code`.
**Sequential reviews:** `stripe-advisor` first; `quarkus-code-reviewer` only after the advisor's review is `approved`. **Hold:** right after the advisor's `approved` and before `board.py`, I write the `quarkus-code-reviewer` work-order with `status: pending`; the Stripe task's work-orders go `done` only after the second `approved` (otherwise `all_tasks: done` fires `NEXT: deploy` early). Any `changes-requested` goes back to `stripe-integrator` before the other review runs. Each `changes-requested` is one `review_rounds` round (the counter counts review records with that outcome per task), so a project may raise `limits.review_rounds` for Stripe tasks via `openspec/handoff-profile.yaml`.

## aws-terraform-engineer

Closed requirement: services, root vs module, region/account, naming and tags, **state backend (bucket/key/region/lock or "no backend")**, `terraform test` wanted or not, target path, skills `provisioning-aws-<service>-v6`.
Offline checks only (`fmt -check`, `init -backend=false`, `validate`, fully mocked `terraform test`); it never runs `terraform plan`, apply, destroy or import (the deployer plans in E7). Write into the brief: "write `result-NN-infra.md` from `assets/result-code.template.md` of `coordinating-quarkus-aws-handoffs`: frontmatter kind `report`, outcome `success|partial|failed|needs-input`, sections Done, Evidence, Spec impact, Suggested next step". Its native status maps DONE -> `success`, PARTIAL -> `partial`, NEEDS-INPUT -> `needs-input`, a failed validate -> `failed`; if it answers in its native form (Requirement, Status, Skills loaded, Files changed, Verification results, Open questions) I wrap it. Incomplete requirement -> it returns questions: relay them.
Record names used by this team: `wo/result-NN-infra`, `result-NN-observability`, `verify-E2/E4/E7.md`.

## aws-architect

```
Mode: <design review (E4) | architecture review (E2)>. Read-only. Inputs: <architecture spec path>, <ADR dir>, <functional spec/delta paths>, <design.md path>.
Check: WAF pillars (serverless lens), tenancy model, security, measurable NFRs, ADR completeness (>=2 alternatives, consequences, sources), every R* mapped to a component.
Return numbered findings with severity and a verdict pass|fail inline.
```
I save it as `verify-E2.md` / `verify-E4.md` (`from: aws-architect`, `stage`, `outcome`, Criteria, Evidence). Native verdict -> outcome: `fail` on any CRITICAL or HIGH finding or any pillar Fail, else `pass`.

## aws-observability

Re-read its file at preflight and follow its Intake section. Work-order: E2 observability section, log group names/retention, alarm list with thresholds, X-Ray groups/sampling, dashboards, target account/region,
Terraform dir. Four modes (A-D):
- **Mode A (E2, spec review):** review the E2 observability section; it writes `result-NN-observability.md` with `role: observability-review` (so the deploy rule for role `observability` cannot fire at E2).
- **Mode B (E6, infra task):** write the observability Terraform; record `result-NN-observability.md` (offline checks only).
- **Mode C (E7, after the deploy):** document the live observability state of the deployed release in `result-NN-observability.md` (kind `report`); read-only.
- **Mode D (missing instrumentation, found by a check):** the report carries a work-order proposal for the code owner the work-order names (missing signal, evidence, code skills, acceptance criteria); it never edits application code. I turn an accepted proposal into a new code work-order.
It never verifies and does **not** write the E7 acceptance (that is the debugger's `verify-E7.md`).

## aws-lambda-deployer

Work-order fields: `artifact` (+ SHA-256), `terraform_dir`, `function_name`, `alias`, `region`, identity name, `limits.deploy_cycles`, `smoke`, optional `traffic_strategy`, `upload_path`, rollback authorisation, and zero or more approval lines (above).
First launch (`wo-NN-deploy.md`): **no approval line** (it stops at the plan gate with `needs-input`; that deploy-report is kept as the plan-gate evidence). Second launch: a NEW work-order `wo-MM-deploy.md` with `refs` to the first deploy-report and the relayed lines; never edit the first. Each launch writes its own `result-NN-deploy.md` (kind `deploy-report`).

## aws-lambda-debugger

Mode A: `wo-NN-debug.md` with `mode: A`, function, alias/version, region, entry type (REST, HTTP API, SQS, EventBridge), UTC window, symptom or deploy-report path, identity, `limits.debug_rounds`, skills (`debugging-aws-lambda` plus the Quarkus skills for interpretation).
Mode B (E7, after `result-NN-observability.md` exists): `wo-NN-debug.md` with `mode: B`, the pillars to verify, `refs` = deploy-report + `result-NN-observability.md`, and any relayed `approval: logs-insights ...` and `approval: e7-gaps pillars=<comma list> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas` lines (the latter only on the relaunch after the user accepted the gaps). It runs the read-only scripts of `validating-aws-observability` (`check-logs`, `check-metrics`, `check-traces`, `check-alarms`, `check-dashboards`; Logs Insights `start-query`/`get-query-results` and `start-trace-retrieval` are documented read actions that need the approval line). It has no Write tool and **never invokes the function** (a real invoke is the deployer's smoke step, `approval: smoke`): it returns the record inline; I save `diagnosis-NN.md` (mode A) or `verify-E7.md` (gap-acceptance relaunch: `verify-E7-<nn>`; mode B: `kind: verify`, `stage: E7`, role `debug` derived from `from`, `pass|fail`, Criteria + Evidence). Never ask it to fire an alarm; that needs `approval: alarm-test ...` and a worker allowed to run it.

## spec-synchronizer review

```
Mode A (E1/E3 verify). Inputs: <handoff dir>, <proposal.md, specs/**, design.md>, <ADR dir>. Return a verify record inline (stage <E1|E3>, outcome pass|fail, Criteria, Evidence with file:line).
```

## spec-synchronizer delta

```
Mode B (E8 sync). Inputs: detect_drift output <...>, last synced SHA <sha>, spec paths, ADR dir, existing spec-delta records, results with Spec impact <list>. Return spec-delta-<NN> inline (status proposed, delta sections, Questions, delta_revisions: <n>).
```

## After every return

`ls` the expected file (or write the inline record), `check_records.py`, `detect_drift.py`, `board.py`, then act on `NEXT:`. A missing file means the worker failed: relaunch once with the exact gap; a second miss is a `record_rejections` escalation.
