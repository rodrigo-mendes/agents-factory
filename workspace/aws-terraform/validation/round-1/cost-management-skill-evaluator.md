# Evaluation Report: provisioning-aws-cost-management-v6 (round 1)

Mode: inline simulation (no sub-agents). Responses were written using only SKILL.md and its blueprints.
Scenarios file: blueprints/evaluation-scenarios.md (4 scenarios, meets the C1 minimum of 3).

## Summary

| Scenario | must_pass | must_not | Verdict |
|---|---|---|---|
| 1 Canonical budget + SNS + anomaly | 7/7 | 3/3 OK | PASS |
| 2 CUR / Data Exports region | 5/5 (one wording caveat) | 2/2 OK | PASS |
| 3 Savings Plan destroy | 5/5 | 2/2 OK | PASS |
| 4 Anti-pattern review | 5/5 | 3/3 OK | PASS |

Overall: 22/22 must_pass, 10/10 must_not OK. 4/4 scenarios PASS (100%).

## Scenario 1 - Canonical

Simulated response: terraform block with `required_version = "~> 1.16"`, aws `version = "~> 6.69"`, and an S3 backend with `use_lockfile = true`. It has an `aws_budgets_budget` (MONTHLY) with a notification that has `subscriber_email_addresses` and a second one with `subscriber_sns_topic_arns`. It adds a topic policy for `budgets.amazonaws.com` with `SNS:Publish`, an `aws:SourceAccount` condition and an `ArnLike` `aws:SourceArn` condition. It also has `aws_ce_anomaly_monitor` (DIMENSIONAL, `monitor_dimension = "SERVICE"`) and `aws_ce_anomaly_subscription` (`frequency = "DAILY"`). No resource sets `region`.

- PASS: constraints. always-do-budgets §1 has `required_version = "~> 1.16"` and `version = "~> 6.69"`.
- PASS: `use_lockfile = true` is in the §1 backend block, and `dynamodb_table` is absent.
- PASS: no `region` on budget, monitor or subscription. §2 and the §6/§7 intros say these are global.
- PASS: each notification carries a subscriber field (§2).
- PASS: §4 policy has `SNS:Publish`, `aws:SourceAccount` and `aws:SourceArn`.
- PASS: `monitor_dimension = "SERVICE"` (§6).
- PASS: the blueprints mark values with `# example`, and I carried those marks over.
- must_not: none violated. (The backend `region = "eu-west-1"` is a backend argument, not a Cost Management resource.)

## Scenario 2 - CUR and Data Exports region

Simulated response: the CUR page says the service is "only available in `us-east-1` currently". Configuring a us-east-1 provider or alias is an inference (medium confidence), so I would ask: "Should the CUR resource use a provider or alias configured for us-east-1?". The Data Exports page states no region requirement. `us-east-1` appears only in the AWS bucket-policy `aws:SourceArn` (medium confidence), so I would ask before using a us-east-1 provider. `s3_region` is the bucket's region, not the resource region. The resources document no resource-level `region`.

- PASS: the CUR quote is in SKILL.md Ask First and always-do-reporting §10.
- PASS: the inference label and the question come from Ask First (row "CUR provider region").
- PASS: Data Exports (row "Data Exports home region", M2).
- PASS: `s3_region` is "bucket region, not the resource region" (§10 and §11 comments).
- PASS with caveat: the skill says "none of the 9 resource pages documents a resource-level `region`". Nested `ssm_action_definition.region` is a required argument on a budget action. The criterion "no resource in this unit accepts a region argument" is slightly broader than the research. The response must say "no resource-level region" to stay accurate.
- must_not: none violated. No `region` was set, and the us-east-1 requirement was not stated as fact.

## Scenario 3 - Savings Plan destroy

Simulated response: no. The page warns an active plan "cannot be cancelled or deleted". Only `queued` plans can be deleted. `terraform destroy` on an active plan only removes it from state. The resource is `aws_savingsplans_savings_plan` (the `savingsplans_plan` name does not exist). Provider support is "best effort" per the 6.62.0 CHANGELOG. Before apply, confirm the commitment, offering ID and upfront option.

- PASS: all five must_pass items are directly sourced (always-do-reporting §12, never-do-reporting §3, SKILL.md Ask First "Savings Plans purchase").
- must_not: none violated.
- Coverage gap (not a criterion bug): the user already bought the plan, and the skill gives no cancellation or remediation path, for example contacting AWS Support. Research does not cover this, so the response cannot invent one. The last must_pass ("confirm before apply") is forward-looking and does not help this user. Consider adding a note to the skill: "post-purchase cancellation is not documented; unverified".

## Scenario 4 - Anti-pattern trap

Simulated response: not right.
- Missing `s3_prefix` is wrong, since it is required since 6.0 (upgrade guide).
- `cost_filter` with `filter_expression` is a documented conflict.
- An `and` with one operand is wrong because "`and` and `or` require at least 2 operands".
- Pricing: monitoring and notifications are free. The first two action-enabled budgets are free per month, then $0.10/day per action-enabled budget (AWS pricing page).
- Limits: up to 10 email addresses and one SNS topic per alert (AWS best-practices page).

- PASS: all five. Sources are SKILL.md Never Do, Ask First "Action-enabled budget cost" and Quick Reference "Budget alerts".
- must_not: none violated. The wrong figures were only quoted as the thing being rejected.
- Minor ambiguity: the pricing correction lives only in the Ask First table, not in Quick Reference or any blueprint. A model reading only the blueprints would miss it.

## Criteria quality flags

- No criterion demands advice absent from the research. No unsourced criteria.
- S2 criterion 5 is slightly over-broad (see above). Suggested rewording: "States no resource-level region argument exists; s3_region and ssm_action_definition.region are not the resource region".
- S3 has the coverage gap noted above.

## Fixes needed (short)

1. Optional (evaluation-scenarios.md, S2): reword "no resource accepts a region argument" to "no resource-level region argument".
2. Optional (SKILL.md Quick Reference): add the Budgets pricing line, so the S4 correction is not only in Ask First.
3. Optional (never-do-reporting-migration.md §3 or SKILL.md): state that a post-purchase cancellation path is undocumented in the research (unverified).
