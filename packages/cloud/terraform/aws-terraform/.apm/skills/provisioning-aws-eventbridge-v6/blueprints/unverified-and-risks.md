# Unverified Claims and Risks — hashicorp/aws 6.x EventBridge

Each source carries its own read date (bibliography below). See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x**: latest is 6.70.0; the skill targets `~> 6.69`. Re-verify when starting new work.
  Source: https://releases.hashicorp.com/terraform-provider-aws/ (read 2026-10-23)
- **Terraform 1.17.0** is stable since 2026-10-21; this skill targets `~> 1.16` (newest 1.16.x is 1.16.7, 2026-10-22).
  Source: https://releases.hashicorp.com/terraform/ (read 2026-10-23); https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md (read 2026-10-22)
- **6.57.0 is withdrawn** from GitHub and the Registry. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- **v7**: the upgrade guide says `s3_us_east_1_regional_endpoint` "will be removed in `v7.0.0`"; no 7.x release exists. When v7 ships, create a new skill `provisioning-aws-eventbridge-v7`.
  Source (read 2026-10-23): https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Connection page has inconsistencies (placement of `connectivity_parameters` vs `invocation_connectivity_parameters`; `http_method` described as a password) | (unverified) — `auth_parameters` contents omitted from the skill; read the current page |
| U2 | `aws_cloudwatch_event_endpoint` arguments (replication for Security Hub EventBridge.4) — page not read | (unverified) — endpoint resource not covered |
| U4 | Archive retention: the page says only that omitting `retention_days` keeps events indefinitely | (unverified) — omit `retention_days` for indefinite retention |
| U5 | Whether AWS service events are delivered only to the default bus | (unverified) — not stated by any page read |
| U6 | That the API destination endpoint must start with https — known only from an AWS console page, not the provider page | (unverified) |
| U7 | Rule-target retry numeric limits are not on the provider page (see L1) | (unverified) |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | `target_id` uniqueness scope — inferred from the import format `bus/rule/target_id` | (medium confidence) |
| M2 | `aws_lambda_permission.source_arn` = rule ARN — mapped from the AWS Lambda sample (principal `events.amazonaws.com`, condition `AWS:SourceArn` = rule ARN) | (medium confidence) |
| M3 | SNS topic policy with `aws:SourceArn` — the AWS sample shows `sns:Publish` for `events.amazonaws.com` without a SourceArn condition | (medium confidence) |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | Rule-target retry numeric limits are not on the provider page; the AWS defaults (24 h / 185) and the Scheduler limits (60–86400 s, 0–185) are documented separately; identical limits for rule targets are not verified |
| L2 | Data sources (`aws_cloudwatch_event_bus`, `_connection`, `_source`) and `aws_cloudwatch_event_endpoint` are not covered |
| L3 | `aws_pipes_pipe` is covered briefly by design |
| L4 | The AWS scheduled-rules page `eb-scheduled-rules.html` returned only a title; the legacy-rule page was used instead |
| L5 | Registry pages are JS-only; raw `main` branch docs were used and may run slightly ahead of 6.70.0 |

## Tag to register mapping

| Tag text | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Ask First — Archive retention row | U4 |
| (unverified) | SKILL.md Ask First — Connection authentication row | U1 |
| (unverified) | always-do-scheduler-integrations.md §5 — connection inconsistencies | U1 |
| (unverified) | always-do-scheduler-integrations.md §5 — https endpoint | U6 |
| (unverified) | SKILL.md Ask First — Events from AWS services on a custom bus row | U5 |
| (unverified) | SKILL.md Ask First — Global endpoints row | U2 |
| (unverified) | SKILL.md Ask First — Rule-target retry limits row | U7 |
| (medium confidence) | never-do-targets.md §4 — comment in the CORRECT block | M2 |
| (medium confidence) | SKILL.md Ask First — Target ID scope row | M1 |
| (medium confidence) | SKILL.md Ask First — SNS and Lambda resource policies row (two tags) | M2, M3 |
| (medium confidence) | always-do-rules-targets.md §4 — comment above `source_arn` | M2 |

## Source Bibliography

Read dates: all items were read 2026-10-23, except the Terraform 1.17 CHANGELOG (item 27), read 2026-10-22.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — no EventBridge items in 6.0.0
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_rule.html.markdown — `state`, `is_enabled`, default-bus schedules
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_bus.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_bus_policy.html.markdown — incompatible with permission resource
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_permission.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_target.html.markdown — `role_arn`, input exclusivity, Lambda/SNS permissions
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_archive.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_connection.html.markdown
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_api_destination.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/scheduler_schedule.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/scheduler_schedule_group.html.markdown
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/pipes_pipe.html.markdown
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — 6.54.0, 6.66.0, 6.57.0 withdrawn
14. https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html
15. https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html
16. https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html
17. https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html — scheduled rules legacy, Scheduler recommended; console page that states https for endpoints (U6)
18. https://docs.aws.amazon.com/securityhub/latest/userguide/eventbridge-controls.html
19. https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rules-best-practices.html
20. https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-patterns-best-practices.html
21. https://releases.hashicorp.com/terraform/ — 1.16.6, 1.17.0
22. https://releases.hashicorp.com/terraform-provider-aws/ — 6.70.0 latest
23. https://developer.hashicorp.com/terraform/language/backend/s3 — `use_lockfile`; `dynamodb_table` deprecated
24. https://developer.hashicorp.com/terraform/language/expressions/version-constraints
25. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown — optional `region`
26. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown — identity import needs Terraform ≥ 1.12.0
27. https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md — 1.17.0 stable (read 2026-10-22)
