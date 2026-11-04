# Evaluation Report: provisioning-aws-eventbridge-v6 (round 1)

Method: no sub-agents. I answered each scenario myself using only SKILL.md and its 9 linked blueprints, then judged the answer against the criteria.

Skill path: `packages/aws-terraform/.apm/skills/provisioning-aws-eventbridge-v6/`

## Summary

| Scenario | must_pass | must_not OK | Verdict |
|---|---|---|---|
| 1 Canonical bus/rule/Lambda/DLQ | 8/8 | 4/4 | PASS |
| 2 Nightly schedule (Madrid) | 4/4 | 3/3 | PASS |
| 3 Policy + permission on one bus | 4/4 | 2/2 | PASS |
| 4 Anti-pattern review | 5/5 | 4/4 | PASS |

Overall: 21/21 must_pass (100%), 13/13 must_not OK. Verdict: 4/4 scenarios PASS.

## Scenario 1: Canonical

The response is the skill's foundation §1, §2 and rules §3-§4 patterns assembled into one set of Terraform. It is marked FRAGMENT because the Lambda, SQS and KMS resources are defined elsewhere. All names are marked `# example`.

must_pass:
- PASS: `required_version = "~> 1.16"` and `version = "~> 6.69"` (always-do-foundation §1).
- PASS: `use_lockfile = true`, no `dynamodb_table` (foundation §1).
- PASS: rule and target both set `event_bus_name = aws_cloudwatch_event_bus.orders.name` (rules §3-§4).
- PASS: `state = "ENABLED"` (rules §3).
- PASS: `source` and `"detail-type"` in the `event_pattern` (rules §3).
- PASS: standard SQS queue in the same Region, with the note "the queue policy must be granted manually" (rules §4 prose). The skill gives no queue-policy HCL, so I pointed to the AWS DLQ page instead.
- PASS: `aws_lambda_permission` with `principal = "events.amazonaws.com"` (rules §4).
- PASS: `# example` markers and the `# FRAGMENT` header are present in the blueprint (rules §3-§4).

must_not: all OK (no `is_enabled`, no FIFO queue, Lambda permission present, no Logs target and no `role_arn`).

## Scenario 2: Scheduling

Response summary:
- Recommend `aws_scheduler_schedule`. AWS calls scheduled rules "a legacy feature" (SKILL.md Ask First, Always Do, scheduler §6).
- Show `cron(0 2 * * ? *)` with `schedule_expression_timezone = "Europe/Madrid"` and `flexible_time_window { mode = "OFF" }`.
- Show `target { arn, role_arn }`.
- State that scheduled rules are UTC+0 only and default-bus only.
- Ask "Scheduler (recommended) or scheduled rule?".

must_pass: 4/4 PASS. All of this is quoted from scheduler §6 and the Ask First row.

must_not: all OK.
- `role_arn` is present in the Scheduler target.
- No `schedule_expression` on a custom-bus rule. I quoted the WRONG example only as a rejected one.
- I did not say scheduled rules are removed. The skill says "legacy" and recommends Scheduler.

## Scenario 3: Misuse rejection

Response summary:
- No. The policy resource "is incompatible with the EventBridge permission resource and will overwrite permissions" (never-do-bus-and-rules §1, SKILL.md Never Do).
- Pick one resource per bus.
- Ask: "Policy document or permission resources for this bus? Which accounts or organization?"
- `principal = "*"` is allowed on the permission resource only with an `aws:PrincipalOrgID` condition.

must_pass: 4/4 PASS.

must_not: both OK. Both resources are rejected, and `*` is not called fine unconditionally.

## Scenario 4: Anti-pattern review

Response summary, all from the Never Do table and never-do blueprints:
- `is_enabled` is deprecated, not removed. Use `state`.
- `input`, `input_path` and `input_transformer` are mutually exclusive. Use exactly one.
- A FIFO queue is not allowed as a DLQ. Use a standard SQS queue in the same Region.
- `dynamodb_table` is deprecated. Use `use_lockfile = true`.
- I mentioned no Security Hub control.

must_pass: 5/5 PASS. must_not: 4/4 OK.

## Flags: criterion and skill issues (no failures)

1. **S4 must_not "Mention a Security Hub control that is not on the current EventBridge controls page" is ambiguous.** The query is unrelated to Security Hub. The criterion only tests for hallucination, and it passes trivially unless the model volunteers controls. The skill carries only EventBridge.2, .3 and .4, which are all on the page. The criterion needs the intent stated: "if a Security Hub control is cited, it must be one of EventBridge.2-.4."
2. **S1 must_pass 6 "notes the queue policy must be granted manually" is only weakly supported by example code.** The skill has the prose note but no queue-policy HCL (rules §4: "not shown here"). A model asked to "generate Terraform" has nothing to copy. This is a skill gap, not a criterion bug. Suggestion: add a minimal `aws_sqs_queue_policy` fragment in always-do-rules-targets.md §4, sourced from the DLQ page.
3. **Never-do-targets §2 labels the WRONG example "input + input_path".** The S4 query uses `input + input_transformer`. The rule text covers all three, so the scenario passes, but a matching example would be clearer.
4. **S3 must_not on `principal = "*"`** is supported only by the Ask First row. The permission page itself was not quoted in a blueprint. It is sourced, so it is not a criterion bug.
5. **S2 must_pass 4 is an either/or** ("asks the user to choose OR recommends Scheduler"). It is lenient, but both behaviors are in the skill.

## Fixes needed (short)

- Optional: add a DLQ queue-policy HCL fragment to `blueprints/always-do-rules-targets.md` §4 (see item 2).
- Optional: add an `input + input_transformer` WRONG example to `blueprints/never-do-targets.md` §2 (see item 3).
- Optional: reword the S4 Security Hub must_not in `blueprints/evaluation-scenarios.md` (see item 1).
- No blocking fixes.
