# Research — AWS CloudWatch (Logs + Alarms + Dashboards) with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-14**. Status: **COMPLETE** (unit `cloudwatch`, P4 fan-out, flat — no sub-agents).
> Resource docs come from the upstream raw markdown in `hashicorp/terraform-provider-aws` (`main`), because Registry pages render JS-only (F12).
> Coverage checklist only (not a source): `workspace/terraform/research_AWS_CloudWatch_aws-v6.x.md` (6.47.0, Terraform 1.7, EOL). Claims from it that turned out wrong are listed in §8.
> Shared facts are cited by ID from `workspace/aws-terraform/_family_facts_v6.md` (F1–F13) and were not re-researched.

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | 1.16.6 latest; target `required_version = "~> 1.16"` | F1 |
| Terraform pre-release | 1.17.0-rc2. Do not target it. | F2 |
| hashicorp/aws | 6.69.0 latest; target `version = "~> 6.69"`; 7.x not released | F3 |
| Withdrawn | 6.57.0. Never pin it. | F4 |
| Per-resource `region` | Every in-scope resource has an optional `region` argument (confirmed on each page below). Changing it forces replacement. | F5 |
| Identity import | Every in-scope resource documents an `identity` import block. It needs Terraform ≥ 1.12.0, which 1.16 satisfies. | F11 + resource pages [3–16] |
| Constraint style | Root modules use `~>`; reusable modules set only `>=` | F6 |

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

## 2. Provider 6.x changes for CloudWatch

**6.0.0 breaking changes** (F13, upgrade guide [2]). The guide lists **no** items for `aws_cloudwatch_log_*`, `aws_cloudwatch_metric_alarm`, `aws_cloudwatch_composite_alarm` or `aws_cloudwatch_dashboard`. These CloudWatch-adjacent items are listed:
- `aws_flow_log`: `log_group_name` removed. Use `log_destination` instead. (This is covered by the VPC unit.)
- `aws_bedrock_model_invocation_logging_configuration`: `logging_config.cloudwatch_config` changed to a list of nested blocks, e.g. `logging_config[0].cloudwatch_config[0].log_group_name`.
- CloudWatch Evidently (`aws_evidently_feature|launch|project|segment`) is deprecated and will be removed in a future major release. AWS ended Evidently support on 2025-10-17.

**CHANGELOG 6.48.0 → 6.69.0, in-scope resources** [1]. No BREAKING entries were found.

| Version | Type | Entry | PR |
|---|---|---|---|
| 6.48.0, 6.49.0, 6.51.0, 6.54.0 | — | No `aws_cloudwatch_*` entries | — |
| 6.50.0 | New resource + list resource | `aws_cloudwatch_log_s3_table_integration_source` | #48190 |
| 6.50.0 | Bug fix | `aws_cloudwatch_log_subscription_filter`: retries IAM eventual-consistency `ValidationException` on Create/Update | #48255 |
| 6.52.0 | Enhancement | Resource Identity for `aws_cloudwatch_log_account_policy`, `_log_anomaly_detector`, `_log_data_protection_policy`, `_log_delivery`, `_log_delivery_destination`, `_log_delivery_destination_policy`, `_log_delivery_source`, `_log_destination`, `_log_destination_policy`, `_log_index_policy`, `_log_resource_policy`, `_log_stream`, `_query_definition` (the last one also gains `arn`) | #48502 |
| 6.52.0 | Bug fix | `aws_cloudwatch_log_delivery`: a mutex around create/update/delete prevents `ConflictException` | #48158 |
| 6.52.0 | Bug fix | `aws_cloudwatch_log_delivery`: fixes the "invalid for the destination type" error when `s3_delivery_configuration` is unchanged | #46123 |
| 6.53.0 | Enhancement | Resource Identity for `aws_cloudwatch_composite_alarm`, `_dashboard`, `_metric_stream`, `_contributor_insight_rule`, `_contributor_managed_insight_rule` | #48679 |
| 6.53.0 | Bug fix | `aws_cloudwatch_contributor_managed_insight_rule`: `resource_arn`, `tags`, `template_name` now ForceNew | #48679 |
| 6.55.0 | New list resource | `aws_cloudwatch_log_stream` | #48878 |
| 6.56.0 | Enhancement | `aws_cloudwatch_log_subscription_filter`: `@source.log` is now a valid `emit_system_fields` value | #48956 |
| 6.62.0 | Bug fix | `aws_cloudwatch_log_resource_policy`: fixes the import-by-identity error with resource scope | #49614 |
| 6.64.0 | Enhancement | `aws_cloudwatch_metric_alarm`: `warm_up_configuration` block | #49873 |
| 6.69.0 | Enhancement | `aws_cloudwatch_metric_alarm`: `evaluation_window` (wall-clock windows) | #50373 |
| 6.69.0 | New resource | `aws_cloudwatch_resource_metrics_configuration` (out of scope, noted only) | #50254 |
| 6.69.0 | Enhancement | `aws_cloudwatch_otel_enrichment`: `include_filter` / `exclude_filter` (out of scope) | #50390 |

Out of scope and excluded: `aws_cloudwatch_event_*` (EventBridge), and `aws_cloudwatchomni_domain` / `aws_cloudwatchomni_space` (6.69.0).

## 3. CloudWatch Logs resources

Source for each resource: `https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/<name>.html.markdown`, fetched 2026-10-14.

### aws_cloudwatch_log_group [3]
- **No required arguments.** If `name` is omitted, a random name is generated. `name` and `name_prefix` force a new resource and conflict with each other.
- `retention_in_days` accepts **0, 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653**. `0` means events never expire.
- With `log_group_class = "DELIVERY"`, `retention_in_days` is **ignored and forced to 2**.
- What happens when `retention_in_days` is omitted is not stated on the TF page. AWS says: "By default, log data is stored in CloudWatch Logs indefinitely" [21]. **Always set it.**
- `log_group_class` accepts `STANDARD`, `INFREQUENT_ACCESS` or `DELIVERY`. AWS: "After a log group is created, its log class can't be changed" [20]. The TF page does not say whether changing the argument forces replacement (M1).
- `kms_key_id`: ARN of the KMS key. Once the key is disassociated, newly ingested data is not encrypted with it. Previously ingested data stays encrypted, and reading it still requires permissions on that key.
- `skip_destroy`: when `true`, destroy removes the log group from state only. The log group and its logs are kept.
- `deletion_protection_enabled`: default `false`. To turn it off you must **explicitly set `false`**; removing the argument is not enough. AWS rejects deletion of a protected log group with `ValidationException` ("Disable deletion protection first") [22].
- Attributes: `arn` with the trailing `:*` stripped (append `:*` yourself where a service needs it), and `tags_all`.
- Import: by `name`. Identity import uses `name` (plus optional `account_id`/`region`).
- No standalone NOTE/WARNING blocks on the page.

### aws_cloudwatch_log_stream [4]
- Required: `name` (≤ 512 chars, no `:`) and `log_group_name`. Attribute: `arn`.
- Import: `log-group:stream`. Identity: `log_group_name` + `name`.
- List resource since 6.55.0; identity since 6.52.0.

### aws_cloudwatch_log_metric_filter [5]
- Required: `name`, `pattern`, `log_group_name`, and a `metric_transformation` block with `name`, `namespace`, `value`.
- `metric_transformation` optional fields:
  - `default_value` **conflicts with** `dimensions`.
  - `dimensions` allows up to 3.
  - `unit` defaults to `None` when omitted.
- `apply_on_transformed_logs` default `false`. Valid only on log groups with an active log transformer.
- Import: `log-group:filter-name`.
- Metric filters are **not supported on Infrequent Access** log groups [20].

### aws_cloudwatch_log_subscription_filter [6]
- Required: `name`, `log_group_name`, `filter_pattern` (`""` matches all events), `destination_arn`.
- The TF page names only "Kinesis stream or Lambda" for `destination_arn`. AWS also documents Firehose and OpenSearch [23] (M2).
- `role_arn` rules:
  - Kinesis: provide it.
  - Lambda: **omit it** and grant access with `aws_lambda_permission`.
  - Cross-account logical destination: not required.
- `distribution` accepts `Random` or `ByLogStream` and applies to Kinesis only. Default is grouping by log stream.
- `emit_system_fields` accepts `@aws.account`, `@aws.region`, `@source.log` (6.56.0). Set `[]` to clear it.
- `apply_on_transformed_logs` default `false`.
- Import: `log_group_name|name` (pipe separator, unlike the other log resources).
- AWS facts [23]:
  - Up to **5** subscription filters per log group.
  - One account-level subscription filter per Region.
  - Standard log class only.
  - At-least-once delivery.
  - Retryable errors are retried for up to 24 h. On non-retryable errors (e.g. `AccessDeniedException`) the filter is disabled for up to 10 min and logs are **skipped** during that time.
- **Recursion risk** [24]: do not subscribe log groups that are part of the delivery workflow (Lambda, Step Functions, Fargate, VPC flow logs). For account policies, exclude them with `selection_criteria`.
- **Confused deputy** [25]: use `aws:SourceArn` (preferred, full ARN) and/or `aws:SourceAccount` in the trust/resource policies of Kinesis/Firehose destinations.

### aws_cloudwatch_log_resource_policy [7]
- Required: `policy_document` (JSON, "up to 5120 characters" per the TF page).
- Set exactly one of `policy_name` or `resource_arn`:
  - `policy_name` (account scope): limited to **10 per region**.
  - `resource_arn` (resource scope): **one policy per log group ARN**.
- Exports `id`, `policy_scope` (`ACCOUNT` | `RESOURCE`) and `revision_id` (resource scope only).
- The examples use principals `es.amazonaws.com` and `route53.amazonaws.com` (`/aws/route53/*`). The page shows no `aws:SourceArn` condition, but add one per [25].
- The AWS vended-logs page says the log-group-level resource policy maximum is **51,200 bytes**, and recommends a `/aws/vendedlogs/*` prefix wildcard [26]. This conflicts with the TF "5120 characters" (M3).
- Import: by policy name or resource ARN. Identity-import bug with resource scope fixed in 6.62.0.

### aws_cloudwatch_log_data_protection_policy [8]
- Required: `log_group_name`, `policy_document` (JSON with `Name`, `Version` "2021-06-01", `Statement[]` of `Sid` / `DataIdentifier[]` / `Operation`). `Operation` is either `Audit.FindingsDestination` (CloudWatchLogs, Firehose or S3) or `Deidentify.MaskConfig {}`.
- Import: by `log_group_name`.
- AWS facts [27]:
  - One log-group-level policy per log group; the limit is 30,720 chars.
  - Account and log-group policies both apply.
  - Data is masked at all egress points (Logs Insights, metric filters, subscription filters). Only principals with `logs:Unmask` see the raw data.
  - **Data ingested before the policy is not masked.**
  - Supported on Standard and Infrequent Access.
  - Emits the `LogEventsWithFindings` metric (AWS/Logs, free), which you can alarm on.

### aws_cloudwatch_log_account_policy [9]
- Required: `policy_name`, `policy_document`, and `policy_type` (`DATA_PROTECTION_POLICY` | `SUBSCRIPTION_FILTER_POLICY` | `FIELD_INDEX_POLICY` | `TRANSFORMER_POLICY`).
- `scope` defaults to and only accepts `ALL`.
- `selection_criteria` (subscription filter policies only) allows only `LogGroupName NOT IN [...]`.
- **Only one account policy per `policy_type`.**
- Import: `policy_name:policy_type`.

### Vended-log delivery: aws_cloudwatch_log_delivery_source / _destination / _destination_policy / _delivery [10–13]
- The model is source → destination → delivery, which pairs exactly one source with one destination [28].
- **Source** [10]:
  - Required: `name`, `log_type`, `resource_arn`.
  - `log_type` depends on the service: e.g. Bedrock `APPLICATION_LOGS`; AgentCore `APPLICATION_LOGS|TRACES|USAGE_LOGS`; CloudFront `ACCESS_LOGS`; IAM Identity Center `ERROR_LOGS`; WorkMail `*_LOGS`.
  - Exports `arn` and `service`.
  - Import: by `name`.
- **Destination** [11]:
  - Required: `name`.
  - `output_format` accepts `json|plain|w3c|raw|parquet`.
  - `delivery_destination_type` accepts `S3|CWL|FH|XRAY`. Computed from `destination_resource_arn` except for X-Ray, where you must set `XRAY` and omit the configuration block.
  - `delivery_destination_configuration.destination_resource_arn` is required whenever the block is set.
  - Import: by `name`.
- **Destination policy** [12]:
  - Required: `delivery_destination_name`, `delivery_destination_policy`.
  - Needed for cross-account delivery, which supports only S3 and Firehose destinations [28].
- **Delivery** [13]:
  - Required: `delivery_source_name`, `delivery_destination_arn`.
  - Optional: `field_delimiter` (plain/w3c/raw only), `record_fields`, and `s3_delivery_configuration { enable_hive_compatible_path, suffix_path }`. Do not put the AWS-managed `AWSLogs/{account}/...` prefix in `suffix_path`.
  - Import: by delivery `id`.
- A CWL destination needs a log group resource policy for `delivery.logs.amazonaws.com` (`logs:CreateLogStream`, `logs:PutLogEvents`) with `aws:SourceAccount` + `aws:SourceArn` conditions [26].
- AWS: removing delivery resources after deleting the source resource is the customer's job [28]. Vended delivery to S3/Firehose still incurs CloudWatch delivery charges [29].

## 4. Alarms and dashboards

### aws_cloudwatch_metric_alarm [14]
- Required: `alarm_name`. The page lists the remaining fields as optional, but some are conditionally required:
  - `evaluation_periods` for traditional alarms.
  - `threshold` for static-threshold alarms.
  - `evaluation_interval` together with `evaluation_criteria`.
- `comparison_operator`:
  - Standard: `GreaterThanOrEqualToThreshold`, `GreaterThanThreshold`, `LessThanThreshold`, `LessThanOrEqualToThreshold`.
  - Anomaly detection only: `LessThanLowerOrGreaterThanUpperThreshold`, `LessThanLowerThreshold`, `GreaterThanUpperThreshold`.
- `period` and `evaluation_interval` accept 10, 20, 30 or any multiple of 60.
- `statistic` accepts `SampleCount|Average|Sum|Minimum|Maximum`. `extended_statistic` takes p0.0–p100.
- **NOTE**: `statistic` and `extended_statistic` cannot both be set.
- **NOTE**: with any `metric_query`, do not set `metric_name`, `namespace`, `period` or `statistic`. Without `metric_query`, all of them are required (`extended_statistic` may replace `statistic`).
- **`treat_missing_data`** accepts `missing|ignore|breaching|notBreaching`. **Default `missing`**.
- `evaluate_low_sample_count_percentiles` accepts `ignore|evaluate` (omitted behaves like `evaluate`).
- `actions_enabled` default `true`. `datapoints_to_alarm` has no stated default.
- **Metric math** (`metric_query`, up to 20 blocks):
  - `id`: starts with a lowercase letter; letters, digits and `_` only.
  - **Exactly one** query has `return_data = true`.
  - Each query has **either** `metric` **or** `expression`, not both.
  - `metric` requires `metric_name`, `namespace`, `period`, `stat`.
  - `period`: multiples of 60, or 1/5/10/20/30 for high resolution.
  - `account_id` enables cross-account alarms.
- `threshold_metric_id` must match the `ANOMALY_DETECTION_BAND` id. Do not combine it with `threshold`.
- **PromQL alarms**: `evaluation_criteria { promql_criteria { query, pending_period, recovery_period } }`, with periods in the range 0–86400 s.
  - Cannot be combined with traditional metric alarm parameters.
  - Requires `evaluation_interval`.
  - Applies to metrics ingested through the CloudWatch OTLP endpoint [17].
- `evaluation_window { wall_clock_window { timezone } }` (6.69.0):
  - Only for `period` 60, 300, 3600, 86400 or 604800.
  - Timezone defaults to UTC; only IANA names observe DST.
  - Not supported with `evaluation_criteria`.
- `warm_up_configuration { warm_up_period_duration_in_minutes (1–2880), only_start_evaluating_after_warm_up_period_ends (default false) }` (6.64.0). It applies once, at creation.
- Import: by `alarm_name`. Identity: `alarm_name`.

### aws_cloudwatch_composite_alarm [15]
- Required: `alarm_name` (unique per region) and `alarm_rule` (≤ 10,240 chars, **no leading or trailing whitespace**).
- `alarm_actions`, `ok_actions`, `insufficient_data_actions`: up to 5 ARNs each.
- `actions_enabled` default `true`, and **changing it forces a new resource**.
- `actions_suppressor { alarm, extension_period, wait_period }`: all three are required inside the block.
- Up to 50 tags.
- **NOTE**: an alarm cannot be destroyed while composite alarms depend on it. On update this can create a cycle, because Terraform tries to destroy alarms before it updates the rule. Mitigations: `depends_on`, referencing alarms by name, two-stage updates.
- Import: by `alarm_name`. Identity since 6.53.0.
- AWS [17]:
  - Composite alarms can notify SNS or create investigations/OpsItems/incidents, but **cannot run EC2 or Auto Scaling actions**.
  - Cross-account composite alarms are not supported.

### aws_cloudwatch_dashboard [16]
- Required: `dashboard_name`, `dashboard_body` (JSON, typically from `jsonencode()`; widgets have `type`, `x`, `y`, `width`, `height`, `properties`). Exports `dashboard_arn`.
- Import: by name. Identity since 6.53.0.

### AWS alarm behaviour [17][18]
- Actions fire only on a state change (Auto Scaling actions repeat every minute).
- CloudWatch does **not validate** that action targets exist.
- Maximum evaluation span (`period` × `evaluation_periods`) is 7 days when period ≥ 3600 s, otherwise 1 day. Alarm history is kept for 30 days.
- Missing data [18]:
  - The default `missing` goes to INSUFFICIENT_DATA only when all points in the evaluation range are missing.
  - Use `breaching` for continuously-reporting metrics (e.g. rollback alarms).
  - Use `notBreaching` for error-only metrics (e.g. DynamoDB `ThrottledRequests`).
  - `AWS/DynamoDB` alarms default to ignoring missing data.
  - For EC2 stop/terminate/reboot/recover actions AWS recommends `missing` and acting only on ALARM.

## 5. AWS guidance — encryption, retention, classes

- **Encryption** [19]:
  - Log data is **always encrypted** at rest with server-side AES-256-GCM by default. KMS is an optional alternative.
  - Use **symmetric keys only**.
  - The key policy grants `logs.<region>.amazonaws.com` the actions `kms:Encrypt`, `kms:Decrypt`, `kms:ReEncrypt*`, `kms:GenerateDataKey*`, `kms:Describe*`. Scope it with an `ArnEquals`/`ArnLike` condition on `kms:EncryptionContext:aws:logs:arn` = `arn:aws:logs:<region>:<account>:log-group:<name>`.
  - The caller needs `kms:DescribeKey`, ideally scoped with `kms:ViaService`.
  - Associating or disassociating a key takes up to 5 minutes.
  - Revoking access to, disabling or deleting the key makes the data unreadable.
  - AWS recommends **a separate KMS key per encrypted log group**.
- **Retention** [21]:
  - Default is indefinite.
  - Expired events are deleted up to ~72 h after they expire, and stop accruing storage cost once they are marked for deletion.
  - A log group can have up to 50 tags.
- **Log classes** [20]:
  - Standard and Infrequent Access differ **only in ingestion price**; storage and Insights charges are the same.
  - Infrequent Access lacks subscription filters, metric filters, Live Tail, anomaly detection, field indexing, EMF, Container/Lambda Insights ingestion and GetLogEvents/FilterLogEvents.
  - The `DELIVERY` class is "only for delivering AWS Lambda logs" to S3/Firehose, with a fixed 2-day retention and no Insights.

## 6. Security Hub CSPM — CloudWatch controls [30]

| Control | Severity | Requirement / Config rule | Terraform lever |
|---|---|---|---|
| CloudWatch.1–14 | Low | CIS metric filter + alarm for: root usage (1), unauthorized API calls (2), console sign-in without MFA (3), IAM policy changes (4), CloudTrail config changes (5), console auth failures (6), CMK disable/delete (7), S3 bucket policy changes (8), Config changes (9), SG changes (10), NACL changes (11), network gateways (12), route tables (13), VPC changes (14). Custom Security Hub rules. | `aws_cloudwatch_log_metric_filter` on the CloudTrail log group + `aws_cloudwatch_metric_alarm` + SNS |
| CloudWatch.15 | High | Alarms have specified actions. `cloudwatch-alarm-action-check`. `alarmActionRequired=true` is fixed; `okActionRequired` and `insufficientDataActionRequired` default false. | `alarm_actions` on every **metric** alarm |
| CloudWatch.16 | Medium | Log group retention ≥ `minRetentionTime`, default **365** (allowed 365, 400, 545, 731, 1827, 3653). `cw-loggroup-retention-period-check`. | `retention_in_days >= 365`, or `0` (see below) |
| CloudWatch.17 | High | Alarm actions activated. `cloudwatch-alarm-action-enabled-check`. | keep `actions_enabled = true` |

- CloudWatch.15/17 evaluate **metric** alarms. They produce FAILED findings when the metric alarm lacks actions, *even if* a parent composite alarm has them. Silencing child alarms and alerting only from the composite therefore fails CloudWatch.15.
- The Config rule treats "Never expire" (`retention_in_days = 0`) as **COMPLIANT** [31].
- The Security Hub CloudWatch page lists no control for log-group KMS encryption (L3).

## 7. Unverified / medium-confidence items and coverage limits

- U1: CIS benchmark versions mapped to CloudWatch.1–14 were not extracted per control.
- M1: whether a `log_group_class` change in TF plans a replacement. AWS says the class is immutable [20]; the TF page is silent.
- M2: Firehose as `destination_arn`. AWS supports it [23]; the TF page names only Kinesis/Lambda. The Firehose `role_arn` requirement is inferred (same as Kinesis).
- M3: resource policy size. TF says 5120 chars; AWS says 51,200 bytes for log-group-level policies [26]. Treat 5120 as the safe bound for account-scope policies.
- M4: verbatim NOTE wording. WebFetch paraphrases; the substance was confirmed on the raw markdown.
- L1: raw `main` docs may run slightly ahead of 6.69.0 (F12).
- L2: the CHANGELOG was read in 100k-character chunks. 6.48.0–6.69.0 were all covered, and the 6.54.0 boundary was rechecked separately.
- L3: no Security Hub control for KMS on log groups was found on the CloudWatch controls page, and other service pages were not checked.
- L4: out of scope and not researched: `aws_cloudwatch_metric_stream`, `_query_definition`, `_log_destination*`, `_log_anomaly_detector`, `_log_transformer`, `_log_index_policy`, `_contributor_*`, `_otel_enrichment`, `_resource_metrics_configuration`.

## 8. Legacy-file claims found wrong or imprecise

`workspace/terraform/research_AWS_CloudWatch_aws-v6.x.md`:
1. "AWS-managed CMK (the default) …". **Wrong.** The default is CloudWatch Logs server-side AES-256-GCM encryption, not an AWS-managed KMS key [19].
2. `DELIVERY` class "for AWS service delivery logs (VPC Flow, S3, CloudTrail via log delivery API)". **Wrong.** AWS limits it to AWS Lambda logs going to S3/Firehose [20].
3. `INFREQUENT_ACCESS` "~50% cheaper … limited Insights". **Imprecise.** Only ingestion is priced lower. The legacy file also omits that metric filters and subscription filters are unsupported on this class [20].
4. Composite pattern with empty child `alarm_actions` ("fire at composite"). This **fails Security Hub CloudWatch.15 (High)** [30].
5. `alarm_rule = <<-EOT … EOT` heredoc. A heredoc keeps a trailing newline, but the TF docs forbid leading/trailing whitespace [15]. Use `trimspace()` or a one-line string.
6. Terraform 1.7 / `~> 6.0` / S3 `dynamodb_table` locking. Superseded by F1, F3 and F7 (`use_lockfile = true`).
7. KMS key policy actions `kms:GenerateDataKey` / `kms:DescribeKey`. AWS uses `kms:GenerateDataKey*` / `kms:Describe*` [19] (minor).
8. Its module-level retention validation list omits 0, 1096, 2192, 2557, 2922 and 3288 [3].

## 9. Security note

- No prompt-injection or instruction-like content was seen in any fetched page.

## Source Bibliography

All fetched 2026-10-14.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_group.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_stream.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_metric_filter.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_subscription_filter.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_resource_policy.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_data_protection_policy.html.markdown
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_account_policy.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_delivery_source.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_delivery_destination.html.markdown
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_delivery_destination_policy.html.markdown
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_log_delivery.html.markdown
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_metric_alarm.html.markdown
15. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_composite_alarm.html.markdown
16. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_dashboard.html.markdown
17. https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html
18. https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/alarms-and-missing-data.html
19. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/encrypt-log-data-kms.html
20. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Log_Classes.html
21. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html
22. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/protecting-log-groups-from-deletion.html
23. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions.html
24. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions-recursion-prevention.html
25. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions-confused-deputy.html
26. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AWS-logs-infrastructure-V2-CloudWatchLogs.html
27. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html
28. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AWS-vended-logs-permissions-V2.html
29. https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AWS-logs-and-resource-policy.html
30. https://docs.aws.amazon.com/securityhub/latest/userguide/cloudwatch-controls.html
31. https://docs.aws.amazon.com/config/latest/developerguide/cw-loggroup-retention-period-check.html
