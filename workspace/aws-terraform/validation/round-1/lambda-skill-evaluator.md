# Evaluation Report: provisioning-aws-lambda-v6 (round 1)

Method: no subagents. Each response was written by the evaluator using only SKILL.md and its blueprints (always-do-*, never-do-*, unverified-and-risks), then judged. Skill dir: packages/aws-terraform/.apm/skills/provisioning-aws-lambda-v6/. Provenance of the responses: they are evaluator-simulated, not captured runtime output.

## Summary

| Scenario | must_pass | must_not OK | Verdict |
|---|---|---|---|
| 1 SQS-triggered function | 7/7 | 3/3 | PASS |
| 2 Function URL NONE | 5/5 | 2/2 | PASS |
| 3 Computed maximum_concurrency | 3/3 | 2/2 | PASS |
| 4 Stale runtime claims | 4/4 | 3/3 | PASS |
| 5 VPC + role cleanup | 4/4 | 2/2 | PASS |

Overall: 5/5 scenarios PASS. must_pass 23/23, must_not 12/12.

## Scenario 1 - Canonical SQS function

Simulated response: the terraform block (`required_version = "~> 1.16"`, `version = "~> 6.69"`), the IAM role fragment, `aws_cloudwatch_log_group` "/aws/lambda/orders-fn", the Zip function, and the SQS mapping. Fragments are from always-do-function.md §1-3 and always-do-events-layers.md §12. Every `# example` value is labelled.

- PASS: constraints. Evidence: always-do-function.md §1 gives `required_version = "~> 1.16"` and `version = "~> 6.69"`.
- PASS: one code source plus handler and runtime. Evidence: `filename = "build/orders.zip"`, `handler = "app.handler"`, `runtime = "python3.14"`.
- PASS: trust policy `lambda.amazonaws.com`/`sts:AssumeRole` and the three logs actions (§2).
- PASS: log group plus `logging_config { log_format = "JSON" ... }` (§3).
- PASS: `function_response_types = ["ReportBatchItemFailures"]` (§12).
- PASS: no `starting_position` (§12, never-do-events §1).
- PASS: values marked with `# example`.
- must_not OK: one code source only. `maximum_concurrency = 10`, which is at least 2. No registry.terraform.io citations; L4 says registry pages are unreadable and raw markdown is used.

Note: the skill's role fragment has no SQS consume permissions (`sqs:ReceiveMessage` and so on). A real SQS mapping needs them. The skill points to the sqs skill but never says so for the role. This is not a criterion, only a content gap.

## Scenario 2 - Function URL NONE

Simulated response: states that `authorization_type` is required (`AWS_IAM` or `NONE`). With NONE the provider adds `lambda:InvokeFunctionUrl` and `lambda:InvokeFunction` at create, and those policies are not removed from AWS on destroy. It then asks, "Is public access intended, and who cleans up the permissions?" (SKILL.md Ask First). It mentions Lambda.1, "Function policies should prohibit public access (Critical)", and suggests `AWS_IAM` as the alternative. The response defaults to nothing and awaits confirmation.

- PASS x5. Evidence: always-do-invocation.md §10 and the Ask First "Function URL NONE" row. Lambda.1 comes from the Quick Reference.
- must_not OK x2: no claim that destroy cleans up, and NONE is not chosen without asking.

Ambiguity: the criterion "Mentions Lambda.1 as a related control" is only weakly sourced. The skill never links Lambda.1 to Function URLs. Lambda.1 appears only in the Quick Reference, in always-do §9 (S3 permission) and in never-do-access §2. The link is inferred from the title "public access". The criterion passes but is an inference. Suggested fix: add one sentence in always-do-invocation §10 or the Ask First row, such as "Lambda.1 (public access) is the related control". If the research never confirmed it applies to URL auth NONE, say so.

## Scenario 3 - Computed maximum_concurrency

Simulated response: rejects `min(var.reserved_concurrent_executions, 1000)`. With the default -1 the result is -1, and any computed value can be below 2, so the provider rejects it. `maximum_concurrency` is SQS-only. Values above 1000 need a quota request. Use a fixed value such as 10, or validate `>= 2` in a variable validation (never-do-events §2).

- PASS x3. Evidence: never-do-events §2, "A computed value such as `min(var.reserved, 1000)` can fall below 2 (or equal -1)".
- must_not OK x2: min() is not accepted, and no Kinesis or DynamoDB use is suggested.

Ambiguity: "or a validated value" is only implied. The skill shows a fixed value and never shows a `validation {}` block. The criterion still passes through the "fixed" branch.

## Scenario 4 - Stale runtimes

Simulated response: runtime support is time-sensitive and was read 2026-10-23 from the Lambda runtimes page. `dotnet8` deprecates 2026-11-10, so it is not a safe permanent value, and `python3.10` deprecates 2026-10-31. `java11` stays supported until 2027-06-30 and `java11.al2023` is listed as supported to 2029, so it is not approaching EOL; it is a bad ban target. It will not hard-code an allow-list. It asks, "Which runtime, and who maintains the allow-list as dates change?"

- PASS x4. Evidence: unverified-and-risks.md "Version-lifetime risk" (the table and the paragraph after it) and the SKILL.md Ask First "Runtime choice" row.
- must_not OK x3: dotnet8 is not allowed, java11 is not called near-EOL, and python3.10 is not called long-term safe.

Caveat: the "supported to 2029" figure for `java11.al2023` appears only in the paragraph in unverified-and-risks.md. The table does not show it. It is sourced to the runtimes page, so it passes. SKILL.md itself does not contain the java11 facts; a model reading only SKILL.md would miss them. Suggested fix: add a java11 sentence to the SKILL.md Runtime choice row or Version Context.

## Scenario 5 - VPC and role cleanup

Simulated response: the role and the VPC policy attachment stay until the function is destroyed, because deleting the role before ENI deletion prevents cleanup. Removing the VPC config can take up to 20 minutes to delete the ENI. The response splits the request: attach `vpc_config` now, keep the role, and remove the old role only after the function is destroyed (or after the ENI is confirmed gone). `subnet_ids` spans at least 2 AZs (Lambda.5). Only `vpc_config` is used, never with `capacity_provider_config`.

- PASS x4. Evidence: always-do-function-config §5, never-do-access-provider §1, SKILL.md Never Do rows 2 and 11.
- must_not OK x2.

Ambiguity or criterion issue: "remove the old execution role" can mean swapping to a new role. The skill covers only "role removed while the function still has vpc_config". It does not say whether the old role may be deleted after the function is repointed to a new role and the ENI has been cleaned up. The criterion "Keeps the role until the function is destroyed" is stricter than the research supports. Suggested fix: reword it to "Does not delete the role in the same change as VPC config removal, and says to wait until the ENI is gone". Alternatively, add a note to the skill about role swaps.

## Fixes needed (short)

1. Scenario 2: link Lambda.1 to Function URL NONE in the skill, or mark the link as inferred (criterion weakly sourced).
2. Scenario 4: put the java11 / java11.al2023 facts into SKILL.md (they live only in unverified-and-risks.md).
3. Scenario 5: reword the criterion about keeping the role "until the function is destroyed". It does not cover role swaps.
4. Scenario 3 (minor): add a variable `validation {}` example, since the criterion says "validated value".
5. Scenario 1 (content gap, not a criterion): add the SQS consume permissions to the role guidance, or an explicit pointer to the sqs skill.

No skill-behavior failures. No must_not violations. No criteria demand advice the research never gives, apart from the weak Lambda.1 link and the role-swap wording noted above.
