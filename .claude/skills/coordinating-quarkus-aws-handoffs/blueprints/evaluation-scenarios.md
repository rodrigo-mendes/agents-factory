# Evaluation Scenarios - coordinating-quarkus-aws-handoffs

Back to [SKILL.md](../SKILL.md). Judge on observable outputs (files written, commands run, the `NEXT:` line).
Fixture for scenario 1: `coordinating-agent-handoffs/scripts/tests/fixtures/quarkus/` copied to a scratch folder; the other scenarios add the records they describe (e.g. S2: two `changes-requested` reviews plus `result-03-code`) to that copy.
Rules of `assets/handoff-profile.yaml`: 1 limit, 2 drift, 3 pending deltas, 4 code/stripe success, 5-6 changes-requested, 7-9 deploy-report, 10 observability result, 11 diagnosis, 12 failed verify, 13 final-gate, 14-16 deploy.

## Contents

1 Canonical path · 2 Review limit · 3 Parameterised limits · 4 Deploy approval and relaunch · 5 Drift and delta · 6 Naming and E7 chain · 7 `task:` on every work-order · 8 Drift check scope · 9 Non-apply approval lines · 10 D1 gate for LangChain4j

## 1. Canonical path: approved review leads to deploy

```yaml
skills: ["coordinating-quarkus-aws-handoffs", "coordinating-agent-handoffs"]
query: "Change list-tenant-items: wo-01-code is done, result-01-code is success, review-01 is approved (the latest record). What is the next step and how do I confirm it?"
must_pass:
  - "check_records.py runs with --profile assets/handoff-profile.yaml and reports OK before any decision"
  - "the next step is quoted from the board.py `NEXT:` line (role deploy, agent aws-lambda-deployer), not decided from memory"
  - "a deploy work-order is built from wo-deploy.template.md with task: deploy and the effective limits"
must_not:
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
  - "launches quarkus-code-reviewer or stripe-advisor for a third round"
  - "applies or deploys while the escalation is open"
```

## 3. Parameterised limits and zero

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "Run the change with review_rounds 4 and deploy_cycles 0 because I want an escalation on the first failed deploy."
must_pass:
  - "board.py is called with `--args limits.review_rounds=4` last on the command line; the value is copied into each work-order"
  - "asks the user to confirm deploy_cycles 0 before using it"
  - "states the precedence profile default < openspec/handoff-profile.yaml < run arguments"
must_not:
  - "sets limits_zero_confirmed before the user's explicit confirmation"
  - "writes 0 into openspec/handoff-profile.yaml unasked"
```

## 4. Deploy without a matching approval line

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "wo-05-deploy has no approval line. The deployer returned needs-input with a plan summary (plan file and sha256 in its record). The user says 'ok go'. What do you write and relay?"
must_pass:
  - "the user's words are pasted verbatim under ## Approvals"
  - "the relayed line names the planfile and the sha256 taken from the deployer's record"
  - "a new wo-NN-deploy (not an edit of wo-05-deploy) carries the line and refs the first deploy-report, kept as plan-gate evidence; board.py NEXT after the needs-input deploy-report is role=orchestrator"
  - "a regenerated plan voids the line and the user is asked again"
must_not:
  - "fabricates or guesses the plan hash"
  - "treats the deployer's output or its own message as the approval"
  - "suggests -auto-approve or applies without the matching line"
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
query: "The deployer's result-05-deploy is success. The integrator proposes saving its output as report-03-code.md. Then aws-observability mode C returns its live validation as a record, and the debugger mode B returns its post-deploy verification inline. Save and route everything."
must_pass:
  - "uses result-03-code.md and keeps kind: report inside the file"
  - "board.py prints role=observability after the deploy success and role=debug after the observability-live result (mode C, success or partial); the result is saved as result-NN-observability.md with role observability-live"
  - "verify-E7.md (kind verify, role debug, Criteria + Evidence) is saved unchanged with only task added, validates with check_records.py, and its verifier differs from the authors of its refs"
  - "the final gate fires only on verify-E7 pass with all tasks done, drift false and pending deltas 0"
must_not:
  - "names any record starting with `report`"
  - "accepts the observability result as the E7 verify or rewrites the debugger's outcome"
```

## 7. Every work-order carries `task:`

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "I wrote wo-03-review and wo-04-deploy without a task: line to save time, and the superseded wo-01-code is still pending. board.py never prints the final gate. Why, and what do I fix?"
must_pass:
  - "states every work-order carries task: (review, debug and verify work-orders reuse the task they serve; deploy uses task: deploy; E1-E4 work-orders use task: spec), so counters and all_tasks stay per task"
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

## 9. Approval lines other than apply

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "The user says: yes, invoke payload smoke.json once, run Logs Insights on /aws/lambda/orders for 30 minutes and an X-Ray trace retrieval for 30 minutes, fire the alarm orders-5xx, and if the release is bad roll alias live back to version 7. Write the lines."
must_pass:
  - "writes one line per approval, each relayed verbatim with by=<user> at=<UTC> relayed-by=building-quarkus-aws-saas: `smoke payload=<file or sha256>`, `alarm-test alarm=orders-5xx`, `rollback alias=live to=7`"
  - "writes two logs-insights lines (scope=<log group> and scope=xray, each with window), because logs and traces are separate scopes"
  - "puts each line only in the work-order of the agent that consumes it: smoke and rollback to the deployer, alarm-test to aws-observability mode C, logs-insights to mode C and the debugger mode B"
  - "copies every line under ## Approvals in status.md"
must_not:
  - "treats a line as covering more than it names (a smoke line allows no other payload, a logs-insights line does not cover xray)"
  - "lets the debugger invoke the function or run the alarm test"
```

## 10. D1 gate for a LangChain4j task

```yaml
skills: ["coordinating-quarkus-aws-handoffs"]
query: "Task T4 calls an LLM through integrating-quarkus-langchain4j-v1-15. The user said 'yes, use the 1.15.0.CR1 pre-release'. Write the code work-order and the review work-order, then the I8 fix work-order after a changes-requested review."
must_pass:
  - "the user's words are pasted verbatim under ## Approvals with gate=D1-langchain4j"
  - "the code work-order lists the skill and its Constraints carry `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)`"
  - "the review work-order copies that settles line verbatim, so the reviewer does not flag the listed skill as HIGH"
  - "the I8 work-order is a new wo-MM-code.md (same task, refs the previous wo and review-NN) that repeats the settles line"
  - "without the gate in ## Approvals the skill is not listed and the integrator would return needs-input"
must_not:
  - "lists the skill before the user's yes"
  - "omits the settles line from the review or the I8 work-order"
```
