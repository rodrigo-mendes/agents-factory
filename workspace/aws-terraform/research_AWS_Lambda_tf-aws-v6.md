# Research — AWS Lambda with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `lambda`, P4 fan-out, flat — no sub-agents).
> Lambda is a **regional** service: every in-scope resource accepts optional `region` (F5).
> Registry pages are JS-only (F12); upstream raw markdown on `main` is the resource-doc source.
> Coverage checklist only (not a source): `workspace/terraform/research_AWS_Lambda_aws-v6.x.md` (6.47.0, Terraform 1.7 — EOL).
> All URLs below were fetched 2026-10-23 unless they cite a family fact (F#).

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI target | `required_version = "~> 1.16"` (1.17.0 stable but not the target) | F1, F2 |
| hashicorp/aws | latest 6.70.0; constraint `~> 6.69`; no 7.x | F3 |
| Withdrawn | 6.57.0 — never pin | F4 |
| `region` per resource | optional, forces replacement on change, import `id@region` | F5 |
| Identity-based import | requires Terraform ≥ 1.12 (satisfied by 1.16); documented for function, ESM, permission, alias, layer version | F11; [1][2][3][5][6] |

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

Lambda runtime facts (AWS, [14]):
- Supported (non-preview) identifiers: `nodejs24.x`, `nodejs22.x`, `python3.14`, `python3.13`, `python3.12`, `python3.11`, `python3.10`, `java25`, `java21`, `java17.al2023`, `java11.al2023`, `java8.al2023`, `java17`, `java11`, `java8.al2`, `dotnet10`, `dotnet8`, `ruby4.0`, `ruby3.4`, `ruby3.3`, `provided.al2023` (`dotnet9` container-only).
- Preview (not for production, no SLA): `nodejs26.x`, `python3.15` (GA targeted November 2026).
- Imminent deprecations relative to 2026-10-23: `python3.10` 2026-10-31; `dotnet8` and `dotnet9` 2026-11-10. AL2 runtimes (`python3.11`, `java17`, `java11`, `java8.al2`) deprecate 2027-06-30 (Amazon Linux 2 EOL 2026-06-30; patched until then).
- Already deprecated: `provided.al2` (2026-07-31), `nodejs20.x` (2026-04-30), `ruby3.2`, `python3.9`, `nodejs18.x`, `dotnet6`, `python3.8`, `nodejs16.x`, `java8`, `go1.x`, `provided`, and older.
- Deprecation policy: notice ≥ 180 days before (email, Health Dashboard, Trusted Advisor); at deprecation no patches/support and console create/update blocked (CLI/SAM/CFN still allowed); block-create ≥ 30 days after; block-update ≥ 60 days after (many current block dates delayed to 2027-07-29 / 2027-08-31). Rollback to a deprecated runtime may be blocked after block-update. All supported runtimes support `x86_64` and `arm64`.
- Container images: no deprecation notifications; you must rebuild from the latest base image.

## 2. Provider 6.x changes for Lambda

6.0.0 upgrade guide (F13, [9]): **no Lambda items** — no removed/renamed arguments for any `aws_lambda_*` resource. Only the general `region` addition (F5) applies.

CHANGELOG 6.48.0 → 6.70.0 ([8]), Lambda scope — no BREAKING entries:
- 6.48.0 BUG FIX `aws_lambda_alias`: plan drift from transient routing weights after a `function_version` update (#48116); `aws_lambda_provisioned_concurrency_config`: error when updating concurrency together with an alias version change (#48116).
- 6.54.0 New resource + list resource `aws_lambda_function_scaling_config` (#48229); ENHANCEMENT `aws_lambda_function` and `aws_lambda_event_source_mapping` add `use_resource_timeout_for_propagation` (#46405); ESM and `aws_lambda_permission` get configurable resource timeouts, replacing hard-coded eventual-consistency timeouts (#46405).
- 6.61.0 New resources `aws_lambdacore_network_connector` (#49387), `aws_lambdamicrovms_image` (#48950) — adjacent, out of scope.
- 6.63.0 New `aws_lambdamicrovms_microvm` (#48984) and list resources — out of scope.
- 6.64.0 New list resource `aws_lambda_alias` (#49706).
- 6.65.0 New resource + list resource `aws_lambda_resource_policy` (#49866).
- 6.68.0 New data source `aws_lambdamicrovms_image_version` (#50299) — out of scope.
- No Lambda entries in 6.49–6.53, 6.56–6.60, 6.62, 6.66, 6.67, 6.69.x, 6.70.0/Unreleased (see L1).

## 3. aws_lambda_function ([1])

- Required: `function_name`, `role` (execution role ARN). Exactly one code source: `filename` | `s3_bucket` (+ `s3_key`, optional `s3_object_version`) | `image_uri` — mutually conflicting.
- `package_type` default `Zip` (`Zip` | `Image`). `handler` and `runtime` are required when `Zip`. `image_config { command, entry_point, working_directory }` for images.
- `architectures` default `["x86_64"]`; values `x86_64` | `arm64`.
- `memory_size` 128–32768 MB (1 MB steps), default 128. `timeout` 1–900 s, default 3. `ephemeral_storage { size }` 512–10240 MB.
- Change detection: `source_code_hash` is a provider-only synthetic value; "Out-of-band changes to the source code _will not_ be captured" — use `code_sha256` (Base64 SHA-256 of the zip, or image digest for OCI; layers excluded) to catch out-of-band changes.
- `source_kms_key_arn` encrypts the zip package (conflicts with `image_uri`). `kms_key_arn` encrypts environment variables; default = AWS service key.
- `environment { variables = {...} }`.
- NOTE: "Lambda was unable to decrypt the environment variables" usually means the role was recreated — fix by switching the role away and back, or taint and re-apply.
- `vpc_config { subnet_ids, security_group_ids, ipv6_allowed_for_dual_stack (default false) }`; all empty = treated as unset. Mutually exclusive with `capacity_provider_config` (Lambda Managed Instances).
- VPC delete NOTE: subnets/SGs used by Lambda can take up to 45 min to delete; handled automatically by provider ≥ 2.31.0.
- `replace_security_groups_on_destroy` default false; when true, `replacement_security_group_ids` is required (swaps SGs before destroy so the original SG can be deleted).
- `dead_letter_config { target_arn }` — SNS topic or SQS queue.
- `tracing_config { mode }` — `Active` | `PassThrough`.
- `logging_config { log_format (required: Text|JSON), application_log_level (TRACE..FATAL), system_log_level (DEBUG|INFO|WARN), log_group }`. Log-level defaults not stated on the page (U2).
- `layers` — up to 5 layer version ARNs (use `aws_lambda_layer_version.arn`).
- `publish` default false; `qualified_arn`/`qualified_invoke_arn`/`version` reflect the published version. `publish_to = "LATEST_PUBLISHED"` optional.
- `reserved_concurrent_executions` default `-1` (unreserved); `0` disables invocation.
- `snap_start { apply_on = "PublishedVersions" }`; attribute `snap_start.optimization_status`.
- `code_signing_config_arn`; attributes `signing_job_arn`, `signing_profile_version_arn`.
- `skip_destroy` default false — the page text says it retains "the old version of a previously deployed Lambda Layer" (likely a docs copy-paste; M1).
- Newer blocks present on `main`: `durable_config { execution_timeout, retention_period (1–90 d, default 14) }` (delete may take 60 min, limited regions), `tenancy_config { tenant_isolation_mode = "PER_TENANT" }`, `file_system_config { arn, local_mount_path "/mnt/..." }`, `capacity_provider_config`. Exact provider version introducing each not checked (L2).
- `use_resource_timeout_for_propagation` (6.54.0): use resource timeouts instead of the 5-minute default for eventual-consistency retries.
- `tags` override provider `default_tags` on key match; `tags_all` computed.
- Attributes: `arn`, `invoke_arn`, `qualified_invoke_arn`, `response_streaming_invoke_arn`, `version`, `vpc_config.vpc_id`.
- Timeouts: create 10m, update 10m, delete 10m. Import: `function_name`; identity `function_name` (+ `account_id`, `region`).
- Log group: examples create `aws_cloudwatch_log_group` named `/aws/lambda/<function_name>` (one example `retention_in_days = 14`) and set `depends_on` on the function "to ensure the log group exists"; docs do not state it is mandatory (M2). For S3/Firehose log delivery, `logging_config.log_group` points to a `DELIVERY`-class group.
- The word "deprecated" does not appear on the page (no deprecated arguments).

## 4. Invocation, versions and permissions

### aws_lambda_alias ([5])
- Required `function_name`, `function_version` (`$LATEST` or number), `name` (not purely numeric).
- `routing_config { additional_version_weights = { "<ver>" = 0.x } }` — remaining weight stays on `function_version`. Update timeout 15m.
- Import `function_name/alias`; identity `function_name` + `name`.

### aws_lambda_permission ([3])
- Required `action` (e.g. `lambda:InvokeFunction`), `function_name`, `principal`.
- Optional `source_arn`, `source_account` (cross-account, S3, SES), `principal_org_id`, `qualifier`, `statement_id` (generated if omitted) xor `statement_id_prefix`, `event_source_token` (Alexa), `function_url_auth_type` (`AWS_IAM`|`NONE`, only with `lambda:InvokeFunctionUrl`), `invoked_via_function_url` (only with `lambda:InvokeFunction`).
- No NOTE/WARNING blocks; no confused-deputy text on the page. API Gateway example comment: "/* part allows invocation from any stage, method and resource path".
- Configurable timeouts since 6.54.0. Import `function_name/statement_id` or `function_name:qualifier/statement_id`.
- New in 6.65.0: `aws_lambda_resource_policy` (whole-policy management; not fetched — U3).

### aws_lambda_function_url ([4])
- Required `authorization_type` (`AWS_IAM`|`NONE`), `function_name`. Optional `qualifier` (alias or `$LATEST`), `invoke_mode` default `BUFFERED` (`RESPONSE_STREAM`), `cors { allow_credentials, allow_headers, allow_methods, allow_origins, expose_headers, max_age ≤ 86400 }`.
- NOTE: with `NONE`, the provider adds `lambda:InvokeFunctionUrl` and `lambda:InvokeFunction` (InvokedViaFunctionUrl=true) permissions at create; "These policies are NOT removed from AWS when the resource is destroyed."
- Create timeout 10m. Import `function_name` or `function_name/qualifier`.

### aws_lambda_provisioned_concurrency_config ([7])
- Required `function_name`, `provisioned_concurrent_executions` (≥ 1), `qualifier` (version or alias; no `$LATEST` statement on the page). `skip_destroy` default false (dangling, billable if true).
- Timeouts create/update 15m. Import `function_name,qualifier`.

### aws_lambda_function_event_invoke_config ([10])
- Required `function_name` (no qualifier in it). `maximum_retry_attempts` 0–2, default 2; `maximum_event_age_in_seconds` 60–21600; `qualifier`.
- `destination_config { on_success { destination }, on_failure { destination } }` — set at least one, else remove the block ("perpetual differences"). Role needs e.g. `sqs:SendMessage`/`sns:Publish`, otherwise generic `InvalidParameterValueException`.
- Import: name or ARN, optionally `:qualifier`.

## 5. Event sources, layers, code signing

### aws_lambda_event_source_mapping ([2])
- Required `function_name`. `batch_size` default 10 (SQS), 100 (Kinesis, DynamoDB, MQ, MSK). `enabled` default true.
- `maximum_batching_window_in_seconds` 0–300 (streams and SQS standard only).
- `starting_position` `LATEST`|`TRIM_HORIZON`|`AT_TIMESTAMP` (Kinesis only) — must not be set for SQS.
- `function_response_types = ["ReportBatchItemFailures"]` — SQS and streams.
- `scaling_config { maximum_concurrency }` ≥ 2, SQS only; > 1000 needs a quota request.
- `filter_criteria { filter { pattern } }` up to 5 filters, 4096 chars; `kms_key_arn` encrypts filter criteria.
- Stream-only: `bisect_batch_on_function_error` (false), `maximum_retry_attempts` (-1 = forever, max 10000), `maximum_record_age_in_seconds` (-1 or 60–604800), `parallelization_factor` 1–10 (1), `tumbling_window_in_seconds` 1–900.
- `destination_config { on_failure { destination_arn } }` — SQS, SNS, S3 (Kafka only) or `kafka://topic`.
- `provisioned_poller_config { maximum_pollers 1–2000, minimum_pollers 1–200 }` — MSK and self-managed Kafka only (not SQS/Kinesis/DynamoDB).
- `metrics_config { metrics = ["EventCount", ...] }`. `use_resource_timeout_for_propagation` (6.54.0).
- Timeouts create 10m, update 10m, delete 5m. Import: mapping UUID.

### aws_lambda_layer_version ([6])
- Required `layer_name`. `filename` xor `s3_bucket`/`s3_key`/`s3_object_version` (bucket in same region). `compatible_runtimes` (≤ 15), `compatible_architectures`, `source_code_hash`, `license_info`.
- Without `skip_destroy = true`, changing almost any argument deletes the old version and creates a new one. NOTE: `skip_destroy = true` leaves versions as "intentional dangling resources ... may incur extra expense".
- Import: layer version ARN; identity `layer_name` + `version`.

### aws_lambda_code_signing_config ([11])
- Required `allowed_publishers { signing_profile_version_arns }` (≤ 20). `policies { untrusted_artifact_on_deployment }` default `Warn` (`Warn`|`Enforce`). Import: CSC ARN.

## 6. AWS guidance

Execution role ([12][16]):
- Trust policy must allow `lambda.amazonaws.com` `sts:AssumeRole`; avoid calling `sts:AssumeRole` on the role from code.
- `AWSLambdaBasicExecutionRole` grants CloudWatch Logs; logs need `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`. Default group `/aws/lambda/<function-name>`.
- Least privilege: trim before production; IAM Access Analyzer policy generation.

VPC ([13]):
- `AWSLambdaVPCAccessExecutionRole` or custom: `ec2:CreateNetworkInterface`, `DescribeNetworkInterfaces`, `DescribeSubnets`, `DeleteNetworkInterface`, `AssignPrivateIpAddresses`, `UnassignPrivateIpAddresses` on `"*"`. Deployer needs `ec2:DescribeSecurityGroups`, `DescribeSubnets`, `DescribeVpcs`, `GetSecurityGroupsForVpc`.
- Recommended deny statement with `lambda:SourceFunctionArn` so function code cannot call those EC2 APIs.
- Use private subnets; internet needs NAT (public subnet gives no public IP). Dedicated-tenancy VPCs not supported directly.
- Hyperplane ENIs shared per subnet+SG combination (65,000 connections each); function Pending until ready; idle 14 days → `Inactive`.
- Removing VPC config: up to 20 min to delete the ENI. **Deleting the execution role before ENI deletion prevents cleanup** — keep the role (and VPC policy attachment) alive until the function is destroyed.
- IPv6 outbound only with all-dual-stack subnets.
- IAM condition keys `lambda:VpcIds`, `lambda:SubnetIds`, `lambda:SecurityGroupIds` (e.g. enforce VPC-attached functions).

Best practices ([15][17]):
- Init SDK clients outside the handler; idempotent code (ESMs are at-least-once); avoid recursion (set reserved concurrency 0 to stop runaway).
- Tune memory (CPU scales with memory) and timeout via load testing; use reserved concurrency to protect downstream; provisioned concurrency for throttle tolerance.
- SQS: function timeout must not exceed the queue visibility timeout (CreateFunction fails / duplicates on update).
- Enable partial batch response (`ReportBatchItemFailures`); with it Lambda does not scale down polling on failures; an exception fails the whole batch; FIFO: stop at first failure.
- Batching window up to 5 min / 6 MB payload; alarm on Kinesis `IteratorAge`.
- Structured JSON logging; CloudWatch metrics/alarms; GuardDuty Lambda Protection; Security Hub.

Security Hub CSPM Lambda controls ([18]):

| ID | Title | Severity | Config rule |
|---|---|---|---|
| Lambda.1 | Function policies should prohibit public access (fails for S3 invokers without `AWS:SourceAccount`; ignores wildcard/variable conditions) | Critical | lambda-function-public-access-prohibited |
| Lambda.2 | Use supported runtimes (list: dotnet10, dotnet8, java25, java21, java17, java11, java8.al2, java17/11/8.al2023, nodejs24.x, nodejs22.x, python3.14–3.10, ruby4.0, ruby3.4, ruby3.3; `Image` ignored) | Medium | lambda-function-settings-check |
| Lambda.3 | Functions should be in a VPC | Low | lambda-inside-vpc |
| Lambda.5 | VPC functions in ≥ 2 AZs (param `availabilityZones`, default 2) | Medium | lambda-vpc-multi-az-check |
| Lambda.6 | Functions should be tagged (`requiredTagKeys`) | Low | tagged-lambda-function |
| Lambda.7 | X-Ray active tracing enabled (`tracing_config.mode = "Active"`) | Low | lambda-function-xray-enabled |

No Lambda.4 exists on the page. Note: `provided.al2023` is supported by Lambda but absent from the Lambda.2 list (M3).

Terraform mapping: Lambda.1 → always set `source_arn` (+ `source_account` for S3) on `aws_lambda_permission`, avoid `principal = "*"` and function URLs with `NONE` unless intended; Lambda.5 → `vpc_config.subnet_ids` across ≥ 2 AZs; Lambda.7 → `tracing_config { mode = "Active" }` (needs X-Ray write permissions — not fetched, U4).

## 7. Legacy-file corrections (checklist `research_AWS_Lambda_aws-v6.x.md`)

- `required_version = ">= 1.7"` and `version = "~> 6.0"` → use `~> 1.16` / `~> 6.69` (F1, F3).
- Runtime allow-list includes `dotnet8` (deprecates 2026-11-10) and omits `python3.14`, `java25`, `dotnet10`, `ruby4.0`, `java17.al2023` etc. [14].
- Calls `java11` "Approaching EOL" — `java11` (AL2) deprecates 2027-06-30; `java11.al2023` is supported to 2029 [14].
- `maximum_concurrency = min(var.reserved_concurrent_executions, 1000)` can produce values < 2 (or -1), which the provider rejects (must be ≥ 2) [2].
- Registry links used as sources (JS-only; F12).

## 8. Unverified / medium-confidence items and limits

- U1 Whether `snap_start` supports runtimes beyond Java (and `arm64`) — SnapStart AWS page not fetched.
- U2 `application_log_level`/`system_log_level` defaults and JSON-only requirement — the AWS advanced-logging page returned no content; not confirmed.
- U3 `aws_lambda_resource_policy` arguments and its interaction with `aws_lambda_permission` — page not fetched.
- U4 X-Ray IAM permissions for active tracing (`AWSXRayDaemonWriteAccess`) — not fetched.
- U5 Default retention of Lambda-created log groups (commonly "never expire") — not stated on fetched pages.
- M1 `aws_lambda_function.skip_destroy` description text refers to "Lambda Layer" — likely copy-paste; actual semantics (retain function on destroy) not confirmed.
- M2 `depends_on` on the log group is shown in examples only, not stated as required.
- M3 Lambda.2 list omits `provided.al2023`; custom-runtime functions may fail Lambda.2 (inference).
- M4 WebFetch paraphrases; verbatim wording partly reconstructed.
- L1 CHANGELOG read in two 100k-char chunks; 6.55.0 header area was at the chunk boundary (no Lambda entries seen in its visible part).
- L2 Raw `main` docs may run slightly ahead of 6.70.0; provider version for `durable_config`/`tenancy_config`/`capacity_provider_config`/`publish_to` not pinned.
- L3 `aws_lambda_function_scaling_config` (6.54.0) noted but not researched (out of brief scope).

## 9. Security note

- None. No instruction-like or prompt-injection content was observed in fetched pages. (The AWS advanced-logging page returned empty content and the fetch tool filled in from general knowledge; that output was discarded, see U2.)

## Source Bibliography

All fetched 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_event_source_mapping.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_permission.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function_url.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_alias.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_layer_version.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_provisioned_concurrency_config.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function_event_invoke_config.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_code_signing_config.html.markdown
12. https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html
13. https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html
14. https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html
15. https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html
16. https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html
17. https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html
18. https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html
19. https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-advanced.html (returned no usable content)
