# Unverified Claims and Risks — hashicorp/aws 6.x CloudWatch

Research date 2026-10-14. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x is the current stable major** as of 2026-10-14 (reference 6.69.0). Re-verify
  when starting new work or after 30 days.
  Source: https://github.com/hashicorp/terraform-provider-aws/releases
- **Terraform 1.16.6** is the current stable CLI. **1.17.0-rc2** exists — do not target it.
  Source: https://releases.hashicorp.com/terraform/
- **6.57.0 is permanently withdrawn** from GitHub and the Registry. Any constraint resolving to it
  fails `terraform init`.
- **v7 is planned** — upgrade guide already documents items "removed in v7.0.0". When v7 ships,
  create a new skill `provisioning-aws-cloudwatch-v7`.
- **CloudWatch Evidently** (`aws_evidently_*`) is deprecated; AWS ended support on 2025-10-17.
  Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | CIS benchmark version mapping per CloudWatch.1–14 control — not extracted per control | (unverified) — use the Security Hub CloudWatch controls page for current CIS mapping |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | `log_group_class` ForceNew behavior — AWS says the class is immutable after creation; the TF provider page does not state whether changing the argument plans a replacement | (medium confidence) — treat any class change as requiring destroy/recreate |
| M2 | Firehose as `destination_arn` on `aws_cloudwatch_log_subscription_filter` — AWS documents Firehose support; the TF page names only Kinesis and Lambda | (medium confidence) — infer same `role_arn` requirement as Kinesis; verify against resource page before using |
| M3 | Resource policy size limit — TF page says "up to 5120 characters"; AWS says 51,200 bytes for log-group-level policies | (medium confidence) — treat 5120 characters as the safe upper bound for account-scope policies; 51,200 bytes applies at the log-group level |
| M4 | Verbatim NOTE wording in TF docs — WebFetch paraphrases; substance confirmed via raw markdown | (medium confidence) — use raw markdown source URLs to verify exact wording before quoting |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | Raw `main` branch docs may run slightly ahead of 6.69.0 |
| L2 | CHANGELOG was read in chunks; 6.48.0–6.69.0 were all covered; 6.54.0 boundary was rechecked separately |
| L3 | No Security Hub control for KMS encryption on log groups was found on the CloudWatch controls page; other service control pages were not checked |
| L4 | Out of scope and not researched: `aws_cloudwatch_metric_stream`, `_query_definition`, `_log_destination`, `_log_destination_policy`, `_log_anomaly_detector`, `_log_transformer`, `_log_index_policy`, `_contributor_insight_rule`, `_contributor_managed_insight_rule`, `_otel_enrichment`, `_resource_metrics_configuration`, `aws_cloudwatch_event_*` (EventBridge) |

## Tag to Register Mapping

| Tag text | Where | Register id |
|---|---|---|
| (unverified) | always-do-alarms.md §5 — CIS benchmark version mapping per control | U1 |
| (medium confidence) | never-do-logs.md §3 — log_group_class ForceNew behavior | M1 |
| (medium confidence) | SKILL.md Quick Reference — log class immutability | M1 |
| (medium confidence) | always-do-security.md §6 — Firehose destination for subscription filter | M2 |
| (medium confidence) | SKILL.md ⚠️ Ask First — subscription filter destination | M2 |

## Source Bibliography

All fetched 2026-10-14. Numbers match the original research bibliography.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — CHANGELOG 6.48.0–6.69.0; Evidently deprecation
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — 6.0.0 breaking changes (none for CW resources in scope)
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_group.html.markdown — retention values; deletion_protection; log_group_class; kms_key_id
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_stream.html.markdown — name ≤ 512 chars; no colon
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_metric_filter.html.markdown — default_value conflicts with dimensions; apply_on_transformed_logs
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_subscription_filter.html.markdown — role_arn rules; distribution; emit_system_fields; recursion risk
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_resource_policy.html.markdown — policy_name vs resource_arn; 5120 char limit
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_data_protection_policy.html.markdown — policy_document structure; Version 2021-06-01
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_account_policy.html.markdown — one policy per type; selection_criteria
10–13. Vended-log delivery resources: `cloudwatch_log_delivery_source`, `_destination`, `_destination_policy`, `_delivery` — pattern: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/<name>.html.markdown
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_metric_alarm.html.markdown — statistic/extended_statistic NOTE; metric_query NOTE; treat_missing_data default; warm_up_configuration; evaluation_window
15. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_composite_alarm.html.markdown — alarm_rule whitespace; actions_enabled ForceNew; dependency cycle warning
16. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_dashboard.html.markdown — dashboard_name; dashboard_body JSON
17. https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html — actions fire on state change; no target validation
18. https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/alarms-and-missing-data.html — treat_missing_data semantics
19. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/encrypt-log-data-kms.html — AES-256-GCM default; symmetric keys only; key policy actions; separate key per group
20. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Log_Classes.html — STANDARD/INFREQUENT_ACCESS/DELIVERY; immutability; IA feature gaps; DELIVERY = Lambda logs only
21. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html — default retention = indefinite; 50 tag limit
22. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/protecting-log-groups-from-deletion.html — ValidationException on protected group deletion
23. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions.html — 5 filters per group; Firehose/OpenSearch destinations; at-least-once delivery
24. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions-recursion-prevention.html — recursion prevention guidance
25. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions-confused-deputy.html — aws:SourceArn/aws:SourceAccount conditions
26. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AWS-logs-infrastructure-V2-CloudWatchLogs.html — CWL destination resource policy; 51,200 byte limit
27. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html — data protection policy; pre-existing data not masked; logs:Unmask
28. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AWS-vended-logs-permissions-V2.html — vended delivery model; cross-account limitations
29. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AWS-logs-and-resource-policy.html — delivery charges apply
30. https://docs.aws.amazon.com/securityhub/latest/userguide/cloudwatch-controls.html — CloudWatch.1–17; .15 metric-alarm independent check; .16 retention; .17 actions_enabled
31. https://docs.aws.amazon.com/config/latest/developerguide/cw-loggroup-retention-period-check.html — retention_in_days = 0 is COMPLIANT for CloudWatch.16
