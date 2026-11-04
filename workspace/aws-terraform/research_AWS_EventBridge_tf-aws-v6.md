# Research — AWS EventBridge with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `eventbridge`, flat fan-out, no sub-agents).
> Registry pages render JS-only (F12); upstream raw markdown in `hashicorp/terraform-provider-aws` (`main`) is the authoritative resource-doc source.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_EventBridge_aws-v6.x.md` (6.47.0, Terraform 1.7 — EOL).
> Every URL below was read on 2026-10-23 unless a family fact (F#) is cited.

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"` (1.17.0 stable but NOT the target) | F1, F2 |
| hashicorp/aws | latest 6.70.0; constraint `version = "~> 6.69"`; no 7.x | F3 |
| Withdrawn | 6.57.0 — never pin | F4 |
| Region | EventBridge, Scheduler and Pipes are **regional**: every in-scope resource documents optional `region` (default provider region); change forces replacement; import `id@region` | F5; resource pages [2]–[12] |
| Identity import | `identity` blocks need Terraform ≥ 1.12.0 (satisfied by 1.16) | F11 |
| Naming | Every page: "EventBridge was formerly known as CloudWatch Events. The functionality is identical." → resource prefix stays `aws_cloudwatch_event_*` | [2]–[8] |

Constraint block: identical to the pilot (`~> 1.16`, `hashicorp/aws ~> 6.69`) — F1/F3/F6.

## 2. Provider 6.x changes for EventBridge

**6.0.0 upgrade guide (F13, [1])**: no item mentions `aws_cloudwatch_event_*`, `aws_scheduler_*` or `aws_pipes_pipe`. The only nearby section is "CloudWatch Evidently Deprecation" (`aws_evidently_*`), which is a different service. → No 6.0.0 breaking changes in scope.

- `aws_cloudwatch_event_rule.is_enabled` is still **Deprecated (not removed)** at `main`; use `state`; the two conflict [2].

**CHANGELOG 6.48.0 → 6.70.0** [13] (all versions checked, in three windows; 6.55.0 header confirmed):
- **6.54.0 (2026-07-08)**: Resource Identity added to `aws_cloudwatch_event_api_destination`, `_archive`, `_bus`, `_bus_policy`, `_connection`, `_endpoint`, `_permission` (#48819); `aws_scheduler_schedule` gains resource identity + becomes a **list resource** (#48828).
- **6.66.0 (2026-09-21)**: `aws_pipes_pipe` fix: unset `server_root_ca_certificate` is no longer sent as an empty string, which had made `UpdatePipe` fail (#40116).
- No other entries in 6.48.0–6.70.0 for the scoped resources (none for `aws_cloudwatch_event_rule`/`_target`). No breaking changes.

## 3. aws_cloudwatch_event_bus [3]

- Required: `name`. Custom bus names can't contain `/`. For a partner bus, `name` must match `event_source_name`.
- Optional: `description`, `event_source_name`, `kms_key_identifier` (CMK: key ARN, KeyId, alias, or alias ARN), `dead_letter_config { arn }` (SQS), `log_config { include_detail = NONE|FULL, level = OFF|ERROR|INFO|TRACE }`, `tags`, `region`.
- The page gives no defaults except `region`. No WARNING blocks.
- Import: `name` (also works for a partner source name); identity `{ name }` (+ optional `account_id`, `region`).
- Bus DLQ: AWS documents bus-level DLQs for capturing errors when events are encrypted with a CMK. Queue policy `aws:SourceArn` = the bus ARN; the queue must be in the same Region [15].

## 4. aws_cloudwatch_event_bus_policy [4] and aws_cloudwatch_event_permission [5]

- Bus policy: `policy` (required JSON), `event_bus_name` (optional, defaults to `default`). Import: `event_bus_name`; identity `{ event_bus_name }`.
- Permission: `principal` (required; 12-digit account or `*`), `statement_id` (required), `action` (default `events:PutEvents`), `condition { key = "aws:PrincipalOrgID", type = "StringEquals", value }` (these are the only valid key/type), `event_bus_name` (default `default`). Import: `event_bus_name/statement_id`; identity `{ statement_id }`.
- **NOTE (both pages, verbatim)**: "The EventBridge bus policy resource (`aws_cloudwatch_event_bus_policy`) is incompatible with the EventBridge permission resource (`aws_cloudwatch_event_permission`) and will overwrite permissions." → pick one per bus.
- Use `principal = "*"` only together with `condition` on `aws:PrincipalOrgID` [5].

## 5. aws_cloudwatch_event_rule [2]

- No argument is strictly required, but **at least one of `schedule_expression` or `event_pattern`** must be set.
- `name` / `name_prefix` (conflict with each other; `name_prefix` ≤ 38 chars); random name if neither is set.
- `event_bus_name`: name or ARN; defaults to `default`.
- `event_pattern`: JSON. Size limit is 2048 by default, and can be raised to 4096 characters through a service-quota request.
- `schedule_expression`: cron/rate. **Works only on the default event bus.**
- `state`: `ENABLED` (default) | `DISABLED` | `ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS`. The last value can't be combined with `schedule_expression`.
- `is_enabled`: deprecated (default `true`), conflicts with `state`.
- `role_arn` (role used for target invocation), `force_destroy` (default `false`; allows deleting AWS-managed rules), `description`, `tags`.
- Import: `event_bus_name/rule_name` (bus omitted → `default`); identity `{ name }` + optional `account_id`, `region`.

## 6. aws_cloudwatch_event_target [6]

- Required: `arn`, `rule`. Optional: `event_bus_name` (default `default`; must match the rule's bus), `target_id` (random if omitted), `force_destroy`, `region`.
- `role_arn`: **required** for `ecs_target`, and for targets that are EC2 instances, Kinesis data streams, Step Functions state machines, or an event bus in another account/Region.
- Input: `input` (JSON), `input_path` (JSONPath) and `input_transformer` are **mutually exclusive**. In `input_transformer`, `input_template` is required and must be valid JSON, escaped for both JSON and Terraform. `input_paths` allows ≤ 100 pairs, uses dot notation (no brackets), and keys can't start with "AWS".
- `dead_letter_config { arn }` (SQS). `retry_policy { maximum_event_age_in_seconds, maximum_retry_attempts }`; the provider page lists no limits.
- `sqs_target { message_group_id }` (FIFO).
- `ecs_target`:
  - `task_definition_arn` is required.
  - `launch_type` is `EC2|EXTERNAL|FARGATE`. Omit it when `capacity_provider_strategy` is set.
  - `network_configuration` is required for FARGATE (`assign_public_ip` default `false`).
  - `task_count` default 1; `platform_version` is FARGATE only; `propagate_tags` accepts only `TASK_DEFINITION`.
  - Up to 5 `ordered_placement_strategy` and up to 10 `placement_constraint` blocks.
- `batch_target`: `job_definition` and `job_name` required; `array_size` 2–10,000; `job_attempts` 1–10.
- `http_target`: `header_parameters`, `path_parameter_values`, `query_string_parameters` (for API Gateway / API destinations).
- `run_command_targets` (≤ 5): `key` = `tag:<key>` or `InstanceIds`, plus `values`.
- Also available: `kinesis_target { partition_key_path }`, `redshift_target` (`database` required), `sagemaker_pipeline_target`, `appsync_target { graphql_operation }`.
- `target_id` uniqueness: the import/identity key is `event_bus_name/rule/target_id`, so a target ID identifies one target within one rule on one bus (medium confidence — inferred from the import format; the page does not state the uniqueness scope; M1).
- Import: `event_bus_name/rule-name/target-id` (bus omitted → `default`); identity `{ event_bus_name, rule, target_id }`.
- **NOTE (verbatim gist)**: to invoke a Lambda function or SNS topic you must set permissions with `aws_lambda_permission` or `aws_sns_topic_policy`.

## 7. Target permissions [14]

- **CloudWatch Logs** targets use resource-based policies; **do not set `role_arn`** on them ("Important" box). The logs policy grants `events.amazonaws.com` and `delivery.logs.amazonaws.com` the actions `logs:CreateLogStream` and `logs:PutLogEvents`.
- **Lambda / SNS / SQS** accept either an IAM execution role (`lambda:InvokeFunction` / `sns:Publish` / `sqs:SendMessage`) or a resource-based policy. "If no execution role is configured, EventBridge uses resource-based policies on the target resource."
- **Kinesis** streams use identity-based policies, i.e. a role (matches the provider `role_arn` requirement [6]).
- Lambda sample: principal `events.amazonaws.com`, condition `AWS:SourceArn` = rule ARN. In Terraform this maps to `aws_lambda_permission { principal = "events.amazonaws.com", source_arn = aws_cloudwatch_event_rule.x.arn }`. The mapping is an inference (medium confidence, M2).
- SQS sample: `sqs:SendMessage` with `ArnEquals aws:SourceArn`. The rule ARN on a custom bus has the form `rule/<bus-name>/<rule-name>`; on the default bus it is `rule/<rule-name>`.
- SNS sample (AWS doc): `sns:Publish` for `events.amazonaws.com` **without** a SourceArn condition. Adding `aws:SourceArn` is consistent with the SQS/Lambda samples but is not shown for SNS (M3).
- API Gateway: `execute-api:Invoke` with `aws:SourceArn` = rule ARN.
- Pipes "does not support resource-based policies".

## 8. Retries and dead-letter queues [15][16]

- Default retry: **24 hours and up to 185 attempts**, with exponential backoff and jitter. After retries are exhausted, "the event is dropped" [16]. The legacy claim is confirmed.
- Some errors are **not retried** (missing permissions, target no longer exists, invalid address / DNS failure). These go straight to the DLQ if one is set [15].
- DLQ must be a **standard SQS queue (FIFO not supported)** in the **same Region** as the rule [15].
- Because Terraform uses the API (`PutTargets`), the queue policy must be granted manually (the console does this automatically) [15].
- DLQ messages carry `RULE_ARN`, `TARGET_ARN`, `ERROR_CODE`, `ERROR_MESSAGE`, `EXHAUSTED_RETRY_CONDITION`, `RETRY_ATTEMPTS`. Metrics: `InvocationsSentToDLQ`, `InvocationsFailedToBeSentToDLQ`.

## 9. aws_cloudwatch_event_archive [7]

- Required: `name` (≤ 48 chars), `event_source_arn` (bus ARN).
- Optional: `description`, `event_pattern` (if omitted, all events are archived), `kms_key_identifier` (CMK), `retention_days`. If `retention_days` is omitted, events are archived **indefinitely**.
- Import: `name`; identity `{ name }`.

## 10. aws_cloudwatch_event_connection [8] / aws_cloudwatch_event_api_destination [9]

- Connection: `authorization_type` (`API_KEY|BASIC|OAUTH_CLIENT_CREDENTIALS`), `auth_parameters` (max 1: `api_key`, `basic`, `oauth`, `invocation_http_parameters`, `connectivity_parameters`), `invocation_connectivity_parameters { resource_parameters { resource_configuration_arn } }` (private API via VPC Lattice), `kms_key_identifier`. Exports `arn` and `secret_arn`.
- Secrets (api key value, basic password, OAuth client id/secret, and parameters with `is_value_secret = true`) are stored in **Secrets Manager** by the service.
- The connection page has inconsistencies (placement of `connectivity_parameters` vs `invocation_connectivity_parameters`; `http_method` described as a password) — U1.
- Import: `name`.
- API destination: `name` (required, ≤ 64 chars, `[A-Za-z0-9._-]`, unique per account), `invocation_endpoint` (required; `*` path wildcards), `http_method` (required), `connection_arn` (required), `invocation_rate_limit_per_second` (default **300**, > 0), `description` (≤ 512 chars). Import: `name`.
- The AWS console docs say the endpoint "must start with **https**" [17].

## 11. EventBridge Scheduler: aws_scheduler_schedule [10] / aws_scheduler_schedule_group [11]

- **AWS position** [17]: "Scheduled rules are a legacy feature of EventBridge … We recommend that you use Scheduler to invoke targets on a schedule."
  - Scheduled rules use UTC+0 only, with a minimum precision of one minute.
  - "You can only create scheduled rules using the default event bus."
- Schedule required arguments: `flexible_time_window { mode = OFF|FLEXIBLE, maximum_window_in_minutes 1–1440 }`, `schedule_expression`, `target { arn, role_arn }` (`role_arn` is **required** — Scheduler always uses an execution role).
- Schedule optional arguments:
  - `schedule_expression_timezone` (default `UTC`), `state` (`ENABLED` default), `start_date`/`end_date` (UTC; ignored for one-time schedules).
  - `group_name` (default `default`, **forces new**), `name`/`name_prefix` (forces new), `kms_key_arn` (CMK).
  - `action_after_completion` (`NONE` default | `DELETE`), `description`.
- Target block:
  - `retry_policy`: `maximum_event_age_in_seconds` 60–86400 (default 86400), `maximum_retry_attempts` 0–185 (default 185).
  - `dead_letter_config { arn }` (SQS), `input`.
  - Templated target parameter blocks: `ecs_parameters`, `eventbridge_parameters` (`detail_type` and `source` required), `kinesis_parameters` (`partition_key`), `sagemaker_pipeline_parameters`, `sqs_parameters { message_group_id }`.
  - Universal targets: `arn = "arn:aws:scheduler:::aws-sdk:<service>:<apiAction>"` with the payload in `input`.
- Schedule import: `group_name/name`; identity `{ group_name, name }`. List resource since 6.54.0 [13].
- Schedule group: optional `name`/`name_prefix` (forces new), `tags`; timeouts create 5m / delete 5m. Import: `name`.

## 12. aws_pipes_pipe (brief) [12]

- Required: `role_arn`, `source`, `target`.
- Optional: `desired_state` `RUNNING|STOPPED` (the page states no default), `source_parameters` (incl. `filter_criteria`), `enrichment` / `enrichment_parameters`, `target_parameters`.
- `kms_key_identifier`: if omitted, data is encrypted with an AWS owned key.
- `log_configuration { level = OFF|ERROR|INFO|TRACE; destinations: CloudWatch Logs / Firehose / S3 }`.
- Timeouts 30m (create/update/delete). Import: `name`. 6.66.0 bug fix (§2).

## 13. AWS guidance

**Security Hub CSPM EventBridge controls** [18]:

| ID | Title | Severity | Resource | Terraform lever |
|---|---|---|---|---|
| EventBridge.2 | Event buses should be tagged (`requiredTagKeys`, ≤ 6, no default) | Low | `AWS::Events::EventBus` | `tags` / provider `default_tags` |
| EventBridge.3 | Custom event buses should have a resource-based policy attached | Low | `AWS::Events::EventBus` | `aws_cloudwatch_event_bus_policy` |
| EventBridge.4 | Global endpoints should have event replication enabled | Medium | `AWS::Events::Endpoint` | `aws_cloudwatch_event_endpoint` `replication_config` (U2 — endpoint resource page not read) |

- **No EventBridge.1 appears on the current page.** The brief's "EventBridge.1 …" could not be confirmed; it is assumed retired or never published (U3).
- EventBridge.4 note: failover needs a custom bus with the same name, in the same account, in each Region.

**Best practices (rules)** [19]:
- One target per rule. Up to 5 are allowed, but duplicating the rule is recommended.
- Use resource policies for cross-account/Region rule ownership.
- Monitor `TriggeredRules`, `ThrottledRules` and `IngestionToInvocationStartLatency`. Sustained latency over 30 s may indicate disruption or throttling.

**Best practices (event patterns)** [20]:
- Avoid infinite loops: match only the "bad state" events, not every change.
- Always filter on `source` + `detail-type`. Add `account`/`region` to limit cross-account/Region matches. For CloudTrail events, filter on `eventName`.
- Use `$or` and content filters (prefix/suffix/numeric).
- Validate patterns with the Sandbox or `aws events test-event-pattern`.
- Use budgets to catch runaway charges.

## 14. Legacy-file check (`research_AWS_EventBridge_aws-v6.x.md`)

- Confirmed: `is_enabled` deprecated → `state`; scheduled rules only on the default bus; bus policy vs permission conflict; Lambda permission needed; 24 h / 185 retries; `retention_days` omitted (legacy says `= 0`) = indefinite. The `0` value semantics are unverified (U4).
- **Wrong (outdated)**: "Production Remote State (S3 + DynamoDB)". DynamoDB locking is deprecated; use `use_lockfile = true` (F7).
- **Unverified**: "AWS-native service events are only delivered to the default bus" — not confirmed in pages read (U5).
- **Incomplete**: the schedule example ("cron only works on default bus") omits the AWS recommendation that scheduled rules are legacy and Scheduler is preferred [17].
- **Constraint references**: the legacy 6.47.0 / Terraform 1.7 pins are superseded by F1/F3.

## 15. Unverified / medium-confidence / limits

- U1 Connection page internal inconsistencies (§10) — verify against the AWS `CreateConnection` API before authoring.
- U2 `aws_cloudwatch_event_endpoint` arguments (replication) — page not read.
- U3 EventBridge.1 control — absent from the official page.
- U4 Meaning of `retention_days = 0` on archives.
- U5 AWS service events delivered only to the default bus.
- M1 `target_id` uniqueness scope (from the import format).
- M2 `aws_lambda_permission.source_arn` = rule ARN mapping.
- M3 SNS topic policy with `aws:SourceArn` (AWS sample omits the condition).
- L1 Target retry-policy numeric limits are not on the provider page; they come from the AWS target docs (24 h / 185 defaults) and the Scheduler page (60–86400, 0–185). Rule-target limits are not verified as identical (L1).
- L2 Data sources (`aws_cloudwatch_event_bus`, `_connection`, `_source`) and `aws_cloudwatch_event_endpoint` are not covered.
- L3 `aws_pipes_pipe` covered briefly by design.
- L4 The scheduled-rules page `eb-scheduled-rules.html` returned only a title; the legacy-rule page [17] was used instead.

## 16. Security note

None. No prompt-injection or instruction-like text was observed in fetched pages. The AWS SNS permission page links a third-party "JSON to string converter" (tools.knowledgewalls.com); it is ignored and not a source.

## Source Bibliography

All read 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_rule.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_bus.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_bus_policy.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_permission.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_target.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_archive.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_connection.html.markdown
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_api_destination.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/scheduler_schedule.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/scheduler_schedule_group.html.markdown
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/pipes_pipe.html.markdown
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
14. https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html
15. https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html
16. https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html
17. https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html
18. https://docs.aws.amazon.com/securityhub/latest/userguide/eventbridge-controls.html
19. https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rules-best-practices.html
20. https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-patterns-best-practices.html
21. https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-scheduled-rules.html (returned title only — L4)
