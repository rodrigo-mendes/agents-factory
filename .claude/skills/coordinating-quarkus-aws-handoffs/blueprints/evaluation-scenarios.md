# Evaluation Scenarios - coordinating-quarkus-aws-handoffs

Back to [SKILL.md](../SKILL.md). Judge on observable outputs (files written, commands run, the `NEXT:` line).
Fixture for scenario 1: `coordinating-agent-handoffs/scripts/tests/fixtures/quarkus/` copied to a scratch folder; the other scenarios add the records they describe (e.g. S2: two `changes-requested` reviews plus `result-03-code`) to that copy.
Rules of `assets/handoff-profile.yaml` (first match wins): 1 limit, 2 drift, 3 pending deltas, 4 design `needs-input`, 5-7 design `success` (solution, infrastructure, designer),
8 author `success` (code, ai, stripe, frontend, infra, observability, cicd) -> reviewer, 9-13 `changes-requested` returns (stripe, frontend, infra, observability, cicd), 14 other `changes-requested` -> code,
15 `pipeline-cd` success -> observability, 16 any other pipeline record -> orchestrator, 17 observability-live -> debug, 18 diagnosis, 19 failed verify,
20-21 final-gate (debugger verify, site verify), 22 approved + all tasks done -> orchestrator (PR hand-off). The numbers shift if a rule is added: read `rule=<n>` from the board, do not hard-code it.

## Contents

1 Canonical path · 2 Review limit · 3 Parameterised limits · 4 Pipeline instead of deploy · 5 Drift and delta · 6 Naming and E7 chain · 7 `task:` on every work-order · 8 Drift check scope · 9 Live-check approval lines · 10 D1 gate for LangChain4j · 11 Design chain and the three ADR folders · 12 Front review loop with a hold · 13 Failed CD run and `deploy_cycles`

## 1. Canonical path: approved review leads to the PR hand-off

```yaml
skills: ["coordinating-quarkus-aws-handoffs", "coordinating-agent-handoffs"]
query: "Change list-tenant-items: wo-01-code is done, result-01-code is success, review-01 is approved (the latest record) and no other task is open. What is the next step and how do I confirm it?"
must_pass:
  - "check_records.py runs with --profile assets/handoff-profile.yaml and reports OK before any decision"
  - "the next step is quoted from the board.py `NEXT:` line (role orchestrator), not decided from memory"
  - "the orchestrator hands the user the commit plan and the PR text; the user pushes and opens the PR; no deploy work-order exists"
must_not:
  - "launches aws-lambda-deployer or any agent to apply, push or deploy"
  - "writes or invents an `approval:` line"
  - "edits `## Approvals` or any other part of status.md by hand"
```

## 2. Edge case: review limit reached wins

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "Task T1 has review-01 and review-02 both changes-requested (defaults). The integrator just wrote a successful result-03-code (the latest record). Who runs next?"
must_pass:
  - "the NEXT line is `escalate limit=review_rounds task=T1 rule=1`, not `role=reviewer`"
  - "escalation-01.md follows assets/escalation.template.md with attempts naming the record ids and 2-4 options with impact"
  - "the user's reply is recorded verbatim under ## Answer with status answered and answeredAt; the task counters then restart"
must_not:
  - "launches a reviewer for a third round"
  - "pushes anything to the PR or the pipeline while the escalation is open"
```

## 3. Parameterised limits and zero

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "Run the change with review_rounds 4 and deploy_cycles 0 because I want an escalation on the first failed CD run."
must_pass:
  - "board.py is called with `--args limits.review_rounds=4` last on the command line; the value is copied into each work-order"
  - "asks the user to confirm deploy_cycles 0 before using it"
  - "states the precedence profile default < openspec/handoff-profile.yaml < run arguments"
must_not:
  - "sets limits_zero_confirmed before the user's explicit confirmation"
  - "writes 0 into openspec/handoff-profile.yaml unasked"
```

## 4. Pipeline instead of deploy: CI, merge, CD

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "All tasks are approved and done. The user pushed the branch and opened PR 12; CI is green. What do you write, what do you ask, and what runs next after the merge?"
must_pass:
  - "reads `gh pr checks 12` (read-only) and writes result-NN-pipeline.md from assets/result-pipeline.template.md with `role: pipeline-ci`, run_url and outcome success; board.py NEXT is role=orchestrator"
  - "asks the user to review the plan commented on the PR and merge; records `gate=E7-merge | source=github <PR url> | login=<user>` only after `gh pr view` shows the PR merged"
  - "reads the cd-app run (`gh run view`) into a second result-NN-pipeline.md with `role: pipeline-cd`; on success board.py prints role=observability (mode C), then role=debug after the observability-live result"
must_not:
  - "records a pipeline result without `role:` (the board would derive orchestrator)"
  - "treats an agent text, or a comment it wrote, as the merge or as an approval"
  - "writes `approval: apply`, `rollback` or `smoke`, or launches the deployer, or runs `gh workflow run`"
```

## 5. Divergence found: drift and delta flow

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "result-02-code (the latest record, outcome success) says Divergences: pagination limit 50 added, but the frontmatter has spec_impact: none. Then the user edits a resource by hand. What do you do?"
must_pass:
  - "returns result-02-code to its author with `rejections: <n>` because spec_impact contradicts ## Spec impact"
  - "after detect_drift.py exit 2, board.py is run with drift=true and prints `NEXT: role=sync agent=spec-synchronizer rule=2`"
  - "the saved spec-delta-NN.md has refs naming the divergent result; the final gate is offered only after the delta is accepted, pending deltas are 0 and drift is false"
must_not:
  - "routes to the reviewer while drift is true"
  - "offers the final gate while pending deltas or drift remain"
```

## 6. Naming, inline records and the E7 chain

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "The CD run of the PR is green. The integrator proposes saving its output as report-03-code.md. Then aws-observability mode C returns its live validation as a record, the debugger mode B returns its post-deploy verification inline and the change has a front end. Save and route everything."
must_pass:
  - "uses result-03-code.md and keeps kind: report inside the file"
  - "board.py prints role=observability after the pipeline-cd success and role=debug after the observability-live result (mode C, success or partial); the result is saved as result-NN-observability.md with role observability-live"
  - "verify-E7.md (kind verify, role debug, Criteria + Evidence) is saved unchanged with only task added, then verify-E7-site.md (from static-site-verifier, stage E7-site); both validate with check_records.py and their verifiers differ from the authors of their refs"
  - "the final gate fires only with all tasks done, drift false and pending deltas 0, and E9 re-checks that both verifies are pass"
must_not:
  - "names any record starting with `report`"
  - "accepts the observability result as the E7 verify or rewrites the debugger's outcome"
```

## 7. Every work-order carries `task:`

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "I wrote wo-03-review and wo-04-debug without a task: line to save time, and the superseded wo-01-code is still pending. board.py never prints the final gate. Why, and what do I fix?"
must_pass:
  - "states every work-order carries task: (review, debug and verify work-orders reuse the task they serve; E1-E4 work-orders use task: spec; E7 work-orders use task: E7), so counters and all_tasks stay per task"
  - "adds the missing task: lines and sets the superseded work-orders done or cancelled, because all_tasks is never true while a work-order stays pending"
  - "re-runs check_records.py, detect_drift.py and board.py and follows the new NEXT: line"
must_not:
  - "edits status.md by hand to force the final gate"
  - "leaves a superseded work-order pending"
```

## 8. Drift check scope during E6-E9

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "In E7 I ran detect_drift.py without --include-worktree and it exited 0, so there is no drift. Can I offer the final gate?"
must_pass:
  - "says a run without --include-worktree sees only commits and agents leave code uncommitted, so it is never proof of no drift during E6-E9"
  - "re-runs `detect_drift.py . --change <handoff dir> --include-worktree` and passes its result (exit 2 = drift) to board.py as drift=true or false"
  - "offers the final gate only when that run exits 0 together with the other gate conditions"
must_not:
  - "treats the commits-only exit 0 as the drift verdict"
  - "treats exit 1 (error) as no drift"
```

## 9. Live-check approval lines (the apply, rollback and smoke lines are gone)

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "The user says: yes, run Logs Insights on /aws/lambda/orders for 30 minutes and an X-Ray trace retrieval for 30 minutes, fire the alarm orders-5xx, and approve applying the plan. Write the lines."
must_pass:
  - "writes two logs-insights lines (scope=<log group> and scope=xray, each with window) and one `alarm-test alarm=orders-5xx` line, each relayed verbatim with by=<user> at=<UTC> relayed-by=building-aws-saas-serverless-quarkus-react-nextjs"
  - "puts each line only in the work-order of the agent that consumes it: alarm-test to aws-observability mode C, logs-insights to mode C and the debugger mode B"
  - "says nothing is applied by an agent in this flow: the plan is approved by the user's review and merge of the PR (`gate=E7-merge`), so it writes no `approval: apply` line"
  - "copies every line under ## Approvals in status.md"
must_not:
  - "treats a line as covering more than it names (a logs-insights line does not cover xray)"
  - "lets the debugger invoke the function or run the alarm test"
  - "writes `approval: apply`, `rollback` or `smoke`"
```

## 10. D1 gate for a LangChain4j task

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "Task T4 calls an LLM through integrating-quarkus-langchain4j-v1-15. The user said 'yes, use the 1.15.0.CR1 pre-release'. Write the AI work-order and the review work-order, then the I8 fix work-order after a changes-requested review."
must_pass:
  - "the user's words are pasted verbatim under ## Approvals with gate=D1-langchain4j"
  - "the AI work-order (from wo-ai.template.md, with Functionality and Diagram, `role: ai`) lists the skill and its Constraints carry `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)`"
  - "the review work-order goes to langchain4j-reviewer first, copies that settles line verbatim and its review record carries `role: ai`; quarkus-code-reviewer runs only after that review is approved (hold)"
  - "the I8 work-order is a new wo-MM-ai.md (same task, refs the previous wo and review-NN) that repeats the settles line"
  - "without the gate in ## Approvals the skill is not listed and the integrator would return needs-input"
must_not:
  - "lists the skill before the user's yes"
  - "omits the settles line from the review or the I8 work-order"
```

## 11. Design chain and the three ADR folders

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "E1 is verified. Run E2: the solution architecture, the design system and the infrastructure. Then the solution-architect returns needs-input asking OpenAI or Bedrock."
must_pass:
  - "three work-orders (wo-NN-solution-architect, wo-NN-designer, wo-NN-infrastructure-architect, the last only after verify-E2a) with task: spec; ADRs from assets/adr.template.md with area architecture | design | infrastructure, numbered per folder, status proposed"
  - "board.py: a solution-architect success -> role=solution-reviewer, an infrastructure-architect success -> role=infrastructure-reviewer, a designer success -> role=design-reviewer; the reviewers return verify-E2a, verify-E2b, verify-E2c (saved inline, authors never verify)"
  - "the needs-input result -> NEXT role=orchestrator; the question goes to the user, the answer is recorded verbatim, and a new work-order follows"
  - "one E2 approval of the user over the three fronts; only then the ADRs become accepted"
must_not:
  - "has an author review its own delivery"
  - "numbers the ADRs of the three areas in one sequence"
  - "starts E6 work-orders before verify-E2a, E2b, E2c and the user's E2 approval"
```

## 12. Front review loop with a hold

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "result-07-frontend is success. nextjs-code-reviewer returns changes-requested (endpoint outside the contract). After the fix, nextjs-code-reviewer approves. Then ui-design-reviewer approves. Route everything."
must_pass:
  - "result-07-frontend success -> NEXT role=reviewer; the review work-order goes to nextjs-code-reviewer; the saved review carries `role: frontend`, so changes-requested -> NEXT role=frontend (nextjs-frontend-integrator)"
  - "the fix is a new wo-MM-frontend.md (same task, refs the previous wo and review-NN) that writes result-MM-frontend.md"
  - "right after the first approved the orchestrator writes the second wo-NN-review (ui-design-reviewer) with status pending BEFORE running board.py, so NEXT does not jump to the PR hand-off"
  - "after the visual review is approved (role: frontend) the task's work-orders are set done and the orchestrator runs the pnpm build and test itself"
must_not:
  - "saves a review without `role: frontend` (the fix would go to the back-end integrator)"
  - "runs the visual review before the code review is approved"
```

## 13. Failed CD run and `deploy_cycles`

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "The cd-app run for dev failed twice (smoke test red the first time, terraform apply error the second). What does the board say and what do you do?"
must_pass:
  - "each run is a separate result-NN-pipeline.md with `role: pipeline-cd`, outcome failed, run_url and the failed job excerpt; the first NEXT is role=orchestrator (route the owner: debugger mode A for a runtime failure, aws-terraform-engineer for an apply error)"
  - "after the second failed record deploy_cycles (2 of 2) is reached: `NEXT: escalate limit=deploy_cycles` and an escalation record with 2-4 options is written; nothing new goes to the PR meanwhile"
  - "a failed CI run (role pipeline-ci) does not count toward deploy_cycles"
must_not:
  - "retries a third run on its own or asks any agent to trigger the workflow"
  - "counts pipeline-ci failures as deploy cycles"
```
