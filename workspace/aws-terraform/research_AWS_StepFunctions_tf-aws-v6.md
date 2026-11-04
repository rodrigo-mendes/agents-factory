# Research — AWS Step Functions with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `stepfunctions`, P4 fan-out, flat — no sub-agents).
> Regional service: every in-scope resource takes optional `region` (F5); it is not a global service (F14).
> Resource docs taken from upstream raw markdown (F12). Coverage checklist only, NOT a source:
> `workspace/terraform/research_AWS_StepFunctions_aws-v6.x.md` (6.47.0 / Terraform 1.7, EOL).

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"` (1.17.0 stable but not the target) | F1, F2 |
| hashicorp/aws | latest 6.70.0; constraint `version = "~> 6.69"`; no 7.x | F3 |
| Withdrawn | 6.57.0 — never pin | F4 |
| Root vs reusable modules | root `~>`, modules `>=` | F6 |
| Identity-based import | needs Terraform >= 1.12.0 (satisfied) | F11 |
| Step Functions service quotas relevant to IaC | definition max 1 MB (hard); 1,000 published versions and 100 aliases per state machine; names <= 80 chars | [7] |

## 2. Provider 6.x changes for Step Functions

- **6.0.0 upgrade guide (F13):** no entry mentions `aws_sfn_*` or Step Functions — no removed/renamed arguments in scope. [4]
- **Enhanced Region Support:** `aws_sfn_state_machine`, `aws_sfn_alias`, `aws_sfn_activity` and data source `aws_sfn_state_machine_versions` all document optional `region` (F5). Import into another region with `<arn>@<region>` per F5. [1][2][3][5]
- **CHANGELOG 6.48.0 → 6.70.0** [6]:
  - 6.55.0 (2026-07-15): New List Resource `aws_sfn_state_machine` (#48840).
  - No other `sfn` entries found in 6.48.0–6.54.0 or 6.56.0–6.70.0/Unreleased; no breaking changes in scope. (Coverage limit L1: the CHANGELOG was read in 100k-char chunks; 6.55.0 enhancement list was truncated in one chunk.)

## 3. `aws_sfn_state_machine` [1]

Required: `definition` (ASL JSON string), `role_arn`.

| Argument | Notes |
|---|---|
| `name` / `name_prefix` | Optional; `[0-9A-Za-z_-]`; random name generated if omitted; `name_prefix` conflicts with `name`. AWS: <= 80 chars, unique per account+Region [7] |
| `type` | `STANDARD` (default) or `EXPRESS`. AWS: all versions of a state machine share the same type [9]. Replacement on change in Terraform (M1) |
| `publish` | "Set to true to publish a version of the state machine during creation. Default: false." Exposes `state_machine_version_arn` |
| `logging_configuration` | `level` = `ALL`/`ERROR`/`FATAL`/`OFF` (default `OFF`), `include_execution_data` (bool), `log_destination` = CloudWatch log group ARN that **must end with `:*`**; role needs logging IAM (§7) |
| `tracing_configuration` | `enabled = true` turns on X-Ray; role needs X-Ray IAM (§7) |
| `encryption_configuration` | `type` (Required: `AWS_OWNED_KEY` or `CUSTOMER_MANAGED_KMS_KEY`), `kms_key_id` (alias, alias ARN, key ID or key ARN; ARN required cross-account), `kms_data_key_reuse_period_seconds` (CMK only; AWS range 60–900 s, default 300 [10]) |
| `tags` | `tags_all` includes provider `default_tags` |
| `region` | F5 |

- Attributes: `id` = `arn`, `creation_date`, `state_machine_version_arn`, `status` (`ACTIVE`/`DELETING`), `tags_all`.
- No `description`, `version_description` or `revision_id` argument is documented on the page (2026-10-23).
- **Definition substitutions:** the Terraform resource has **no** `definition_substitutions` argument (that is a CloudFormation/SAM concept) — substitute with `templatefile()` or `jsonencode()` (verified by absence on [1]; `templatefile`/`jsonencode` are core Terraform functions [17]).
- Timeouts: create 5m, update 1m, delete 5m.
- Import: identity `{ arn = "<state machine ARN>" }` (TF >= 1.12), `import { id = "<arn>" }` (TF >= 1.5), or `terraform import aws_sfn_state_machine.x <arn>`.
- Notes on page: logging → see AWS guide; encryption → see "Data at rest encryption". The `encryption_configuration` description contains an unfilled "[TBD]" placeholder (doc defect; L2).
- 6.55.0 list resource (`list` block / `terraform query`) available for discovery [6].

### Definition authoring and change behavior
- `jsonencode({...})` keeps the ASL in HCL with native references; `templatefile("x.asl.json", {...})` keeps ASL as a file editable in Workflow Studio. Both produce the required JSON string. Choice is a team convention, not an AWS/HashiCorp rule (M2).
- A `definition` change is applied via AWS `UpdateStateMachine` (definition, role, tracing and logging are mutable per revision [9]); Terraform documents an `update` timeout, consistent with in-place update (M3). With `publish = true` the doc only promises a version **at creation** (U1: whether later updates publish a new version).
- In-flight Standard executions keep the revision they started with; unversioned starts use the latest revision [9]. For controlled rollout, publish versions and front them with `aws_sfn_alias`.
- Whitespace/key-order normalization causing perpetual diffs: not documented (U2).

## 4. `aws_sfn_alias` [2]

- Required: `name`, `routing_configuration` (one or more blocks: `state_machine_version_arn`, `weight`). Optional: `description`, `region`.
- AWS rules [11]: an alias points to **up to two** versions; aliases point only to versions (not to other aliases or unpublished revisions); weights must total 100; max 100 aliases per state machine [7].
- Attributes: `arn` (`<state-machine-arn>:<alias>`), `creation_date`.
- Timeouts: create/update/delete 30m.
- Import: identity `{ arn }`, `import { id = "<alias arn>" }`, or `terraform import aws_sfn_alias.x <arn>`.
- Version ARNs come from `aws_sfn_state_machine.x.state_machine_version_arn` (publish = true) or data source `aws_sfn_state_machine_versions` (`statemachine_arn` → `statemachine_versions` list) [5].

## 5. `aws_sfn_activity` [3]

- Required: `name`. Optional: `encryption_configuration`, `tags`, `region`.
- `encryption_configuration.type` documented as `AWS_KMS_KEY` or `CUSTOMER_MANAGED_KMS_KEY` (differs from AWS `AWS_OWNED_KEY` [10]; M4); `kms_key_id`, `kms_data_key_reuse_period_seconds`.
- AWS: activity configuration is **immutable**; changing encryption requires a new activity (CloudFormation: Replacement) [10]. Terraform forces-new on change is therefore expected (M5).
- Attributes: `id`/`arn`, `name`, `creation_date`, `tags_all`. Import by ARN (identity `{ arn }`, `import` block, CLI).
- Workers: AWS recommends >= 100 open `GetActivityTask` polls per activity ARN in production [8].

## 6. Integrations and ASL essentials (AWS docs only)

- Patterns [12]: Request Response (default), Run a Job (`.sync`), Wait for Callback (`.waitForTaskToken`). **Express supports only Request Response**; Standard supports `.sync`/`.waitForTaskToken` where the service table says so. Lambda, SQS, SNS, EventBridge, API Gateway: callback yes, `.sync` no; Step Functions, ECS, EKS, Bedrock: both; DynamoDB optimized: Request Response only. AWS SDK integrations: no `.sync`, callback on Standard.
- Lambda optimized [13]: `"Resource": "arn:aws:states:::lambda:invoke"` (callback: `lambda:invoke.waitForTaskToken`); result nested under `Payload`; `InvocationType: Event` for async. IAM `lambda:InvokeFunction` on function ARN; when using a `Qualifier`/version/alias, include it or `:*` — unqualified ARN alone gives Access Denied.
- `.sync` within the same account uses EventBridge events + polling; needs extra IAM (managed rules) [12].
- Task tokens must come from principals in the same account [12]. Use `HeartbeatSeconds` with callbacks; set `TimeoutSeconds` on Task states (ASL has no default timeout) [8].
- Retry [14]: `ErrorEquals` (required), `IntervalSeconds` (default 1), `MaxAttempts` (default 3; 0 = never), `BackoffRate` (default 2.0), `MaxDelaySeconds`, `JitterStrategy` (`FULL`/`NONE`, default `NONE`). Catch: `ErrorEquals`, `Next` (required), `ResultPath`. `States.ALL` must be alone and last; it does not catch `States.DataLimitExceeded` or `States.Runtime`. `States.TaskFailed` matches all except `States.Timeout`.
- Lambda transient errors: retry `Lambda.ServiceException`, `Lambda.AWSLambdaException`, `Lambda.SdkClientException`, `Lambda.ClientExecutionTimeoutException` (example: interval 2, attempts 6, backoff 2) [8].
- Limits [7][15]: 256 KiB payload per state/task/execution (use S3 ARNs for larger [8]); Standard max 1 year + 25,000 history events; Express max 5 minutes; Inline Map up to 40 concurrent iterations; Distributed Map up to 10,000 parallel child executions; 1 MB definition; 1 MB request.
- Triggers: EventBridge Scheduler templated target `StartExecution` with state machine ARN; scheduler role needs `states:StartExecution` [16]. (EventBridge rule targets are covered by the EventBridge unit — cross-reference.)

## 7. IAM execution role pattern

- Trust: principal `states.amazonaws.com`, action `sts:AssumeRole`; AWS recommends confused-deputy conditions `aws:SourceArn` (`arn:aws:states:<region>:<acct>:stateMachine:*`) and `aws:SourceAccount` [18]. The IAM role itself is global (F14 — no `region`).
- Logging (Standard and Express when created via API/Terraform): `logs:CreateLogDelivery`, `logs:CreateLogStream`, `logs:GetLogDelivery`, `logs:UpdateLogDelivery`, `logs:DeleteLogDelivery`, `logs:ListLogDeliveries`, `logs:PutLogEvents`, `logs:PutResourcePolicy`, `logs:DescribeResourcePolicies`, `logs:DescribeLogGroups` on `Resource = "*"` (these actions do not support resource scoping) [19].
- CloudWatch Logs resource policy: Step Functions updates it on create/update; 5,120-char limit and **10 resource policies per Region per account** — prefix log groups with `/aws/vendedlogs/states` to avoid the size limit [8][19]. No separate `aws_cloudwatch_log_resource_policy` is required by the docs (U3 for cross-account).
- X-Ray: `xray:PutTraceSegments`, `xray:PutTelemetryRecords`, `xray:GetSamplingRules`, `xray:GetSamplingTargets` on `*`. No X-Ray for Distributed Map child executions [20].
- CMK: execution role needs `kms:Decrypt` + `kms:GenerateDataKey` (Sync Express: `kms:Decrypt`), scoped with `kms:EncryptionContext:aws:states:stateMachineArn` (activities: `aws:states:activityArn`). Deploying principal needs `kms:DescribeKey` + `kms:GenerateDataKey`. With CMK + logging: key policy allows `delivery.logs.amazonaws.com` `kms:Decrypt`; role needs `kms:GenerateDataKey` with `kms:EncryptionContext:SourceArn = arn:aws:logs:...`. Do **not** put `kms:ViaService` on the execution role (can break executions) [10].
- Key disabled/deleted → running executions fail; deleted key = data unrecoverable. CMK-encrypted workflows omit input/output from EventBridge status events [10].
- Service permissions (Lambda/SQS/SNS/DynamoDB): grant the specific action on the specific ARN — console-generated templates do this [13][18]; `.sync` needs additional events/describe permissions [12].

## 8. AWS guidance

### Best practices [8]
- Nest Express (idempotent, high-rate) inside Standard (non-idempotent, long-running); Express only if < 5 min, at-least-once acceptable, no `.sync`/`.waitForTaskToken`.
- Set `TimeoutSeconds`/`HeartbeatSeconds`; pass S3 ARNs instead of > 256 KiB payloads; avoid 25,000-event history via Distributed Map or child executions; retry Lambda transient exceptions; >= 100 activity pollers; `/aws/vendedlogs/` log group prefix; tag state machines and activities (tag-based authorization applies to executions).
- Express workflows have no execution history in Step Functions — logging is the only history; CloudWatch Logs delivery is best effort [19].

### Security Hub CSPM controls [21]
| ID | Title | Severity | Resource | Notes |
|---|---|---|---|---|
| StepFunctions.1 | State machines should have logging turned on | Medium | `AWS::StepFunctions::StateMachine` | Config rule `step-functions-state-machine-logging-enabled`; optional `logLevel` param (`ALL`/`ERROR`/`FATAL`) |
| StepFunctions.2 | Activities should be tagged | Low | `AWS::StepFunctions::Activity` | `requiredTagKeys` (up to 6) |

No Security Hub control for state machine CMK encryption or X-Ray was listed on 2026-10-23.

## 9. Legacy checklist — claims found wrong or unverified

| Legacy claim | Finding |
|---|---|
| `aws_sfn_state_machine_version` resource exists ("new v6 resource") | **Wrong** — raw doc 404; versions come from `publish = true` and data source `aws_sfn_state_machine_versions` [1][5] |
| Alias example with two `aws_sfn_state_machine_version` resources | **Wrong** (depends on the nonexistent resource) |
| `required_version >= 1.7`, `version ~> 6.0`, S3 `dynamodb_table` locking | Outdated — F1/F3/F7 (`use_lockfile`) |
| Logging IAM policy list | Incomplete — omits `logs:CreateLogStream` [19] |
| KMS key policy grants `delivery.logs.amazonaws.com` Encrypt/GenerateDataKey* | Broader than AWS doc, which requires only `kms:Decrypt` for that principal [10] |
| "Explicit `delivery.logs` trust policy" on the role | Wrong framing — role trust is `states.amazonaws.com`; `delivery.logs` appears only in the KMS key policy [10][18] |
| `/aws/vendedlogs/states` prefix | Correct [8] |
| "Weighted canary" via alias | Correct, max 2 versions, weights total 100 [11] |
| Secrets in ASL anti-pattern source `docs.aws.amazon.com/security/` | Not a specific source (unverified) |

## 10. Unverified / medium-confidence / limits

- **M1** `type` change forces replacement in Terraform — AWS says type is shared by all versions and one summary of [1] said "cannot be changed after creation"; exact ForceNew not quoted (medium confidence).
- **M2** jsonencode vs templatefile choice is convention (medium confidence).
- **M3** `definition`/`role_arn`/logging/tracing changes are in-place updates (inferred from [9] + update timeout) (medium confidence).
- **M4** Activity `type` enum `AWS_KMS_KEY` in provider doc vs AWS `AWS_OWNED_KEY` — possible doc error; test before use (medium confidence).
- **M5** Activity attributes force replacement (AWS immutability [10]) (medium confidence).
- **U1** Whether `publish = true` publishes a new version on each update (unverified).
- **U2** Perpetual-diff behavior for definition formatting (unverified).
- **U3** Cross-account log destinations / explicit log resource policy needs (unverified).
- **L1** CHANGELOG read in chunks; 6.55.0 section partially truncated.
- **L2** `encryption_configuration` provider doc contains "[TBD]".
- **L3** Distributed Map, JSONata, HTTP Task, redrive not covered in depth.

## 11. Security note

No prompt-injection or instruction-like text was observed in any fetched page.

## Source Bibliography

All accessed 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_alias.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_activity.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/sfn_state_machine_versions.html.markdown (and 404 for r/sfn_state_machine_version.html.markdown)
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
7. https://docs.aws.amazon.com/step-functions/latest/dg/service-quotas.html
8. https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html
9. https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machine-version.html
10. https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html
11. https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machine-alias.html
12. https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html
13. https://docs.aws.amazon.com/step-functions/latest/dg/connect-lambda.html
14. https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html
15. https://docs.aws.amazon.com/step-functions/latest/dg/state-map-inline.html
16. https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-targets-templated.html
17. https://developer.hashicorp.com/terraform/language/functions/templatefile (cited, not re-fetched — standard core function; medium confidence)
18. https://docs.aws.amazon.com/step-functions/latest/dg/procedure-create-iam-role.html
19. https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html
20. https://docs.aws.amazon.com/step-functions/latest/dg/concepts-xray-tracing.html
21. https://docs.aws.amazon.com/securityhub/latest/userguide/stepfunctions-controls.html
