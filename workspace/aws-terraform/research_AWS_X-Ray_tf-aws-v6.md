# Research — AWS X-Ray with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `x-ray`, flat fan-out, no sub-agents).
> Regional service: every in-scope resource documents the optional `region` argument (F5); X-Ray is
> not in the F14 global list.
> Registry pages render JS-only (F12) — upstream raw markdown on `main` is the resource-doc source.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_X-Ray_aws-v6.x.md`
> (6.47.0, Terraform 1.7 — EOL). Claims from it found wrong are listed in §9.

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"`; 1.16.7 newest 1.16.x | F1, F19 |
| Terraform 1.17.0 | Stable, NOT the target | F2 |
| hashicorp/aws | latest 6.70.0 (2026-10-21); constraint `~> 6.69`; no 7.x | F3, F18 |
| Withdrawn | 6.57.0 — never pin | F4 |
| Identity-based import | needs Terraform ≥ 1.12.0 (documented on all three X-Ray pages) | F11; [1][2][3] |
| X-Ray SDK/Daemon | **Maintenance mode since February 25th, 2026** — security fixes only, "will not receive new feature enhancements" | [7][8] |

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

Root modules use `~>`, reusable modules `>=` only (F6). S3 backend: `use_lockfile = true`;
`dynamodb_table` deprecated (F7) — the legacy file's `dynamodb_table` backend is outdated.

## 2. Provider 6.x changes for X-Ray

- **6.0.0 upgrade guide (F13, F17):** no mention of X-Ray or any `aws_xray_*` resource [4] (2026-10-23).
  The only 6.0-wide change that applies is Enhanced Region Support: optional `region` on every
  X-Ray resource (F5).
- **CHANGELOG 6.48.0 → 6.70.0:** no `aws_xray_*` entries found [5] (2026-10-23; read in two chunks
  covering 6.71.0-Unreleased back to 6.40.0).
- **Context (before range), 6.46.0 (May 20, 2026)** [5]: new resources `aws_xray_indexing_rule`,
  `aws_xray_trace_segment_destination`; Resource Identity added to `aws_xray_sampling_rule` and
  `aws_xray_resource_policy`; `aws_xray_resource_policy.policy_name` now ForceNew.
  These three extra resources are outside this unit's scope (L1).

## 3. `aws_xray_sampling_rule` [1]

| Argument | Req. | Notes (provider doc [1] + AWS API constraints [9]) |
|---|---|---|
| `rule_name` | **Optional** (provider) | API: 1–32 chars; "Specify a rule by either name or ARN, but not both" [9]. Also the resource `id` and the import ID |
| `priority` | Required | API range 1–9999 [9]; services evaluate in ascending order and use the first match [6] |
| `reservoir_size` | Required | ≥ 0; requests/second before the fixed rate; applies to all services using the rule collectively [6][9] |
| `fixed_rate` | Required | Double 0–1 [9] (console shows 0–100 %, JSON/API 0–1 [6]) |
| `host` | Required | max 64 [9] |
| `http_method` | Required | max 10 [9] |
| `url_path` | Required | max 128 [9] |
| `service_name` | Required | max 64; API Gateway uses `{api-name}/{stage}` [6][9] |
| `service_type` | Required | max 64; e.g. `AWS::APIGateway::Stage`, `AWS::StepFunctions::StateMachine`, `AWS::EC2::Instance` [6] |
| `resource_arn` | Required | max 500; X-Ray SDK only uses rules with `*`; API Gateway = stage ARN [6][9] |
| `version` | Required | "version of the sampling rule format (`1`)" [1][9] |
| `attributes` | Optional | map, max 5 entries, key/value 1–32 chars [9]; **X-Ray SDK ignores rules that specify attributes**; API Gateway matches original request headers [6] |
| `tags` | Optional | merges with `default_tags`; quota 50 tags per rule [10] |
| `region` | Optional | F5 |

- String fields accept wildcards `*` (zero or more) and `?` (single char) [6].
- Exported: `arn`, `id` (= rule name), `tags_all` [1].
- Import: identity `{ rule_name }` (+ optional `account_id`, `region`) on TF ≥ 1.12; `id = <rule_name>`
  on TF ≥ 1.5; CLI `terraform import aws_xray_sampling_rule.x <rule_name>` [1].
- **Uniqueness of priority:** AWS docs define the range and ascending evaluation [6][9] but the
  pages read do not state that priorities must be unique or what happens on ties (U1). Treat unique
  priorities as a defensive convention, not an AWS-documented constraint.
- **Immutable fields:** the Step Functions guide states "Some parts of existing sampling rules,
  such as the name and priority, cannot be changed. Instead, add or clone an existing rule" [12].
  Whether the provider marks `priority` ForceNew is not stated on [1] (M1).
- **SamplingRateBoost** (MaxRate, CooldownWindowMinutes — anomaly-driven boost) exists in the API [6][9];
  the provider page [1] lists no corresponding argument (L2).
- **Parent-based sampling:** "the sampling decision is made only once, typically by the first
  X-Ray-enabled service" — a rule for a downstream service called by an upstream service "will
  likely never be applied"; put rules on the root service [6].
- X-Ray applies rules best-effort; effective rate converges over time [6].

### Default rule [11]
`RuleName "Default"`, ARN `…:sampling-rule/Default`, **Priority 10000**, `ReservoirSize 1`,
`FixedRate 0.05`, all match fields `*`, `Version 1`. "It is the lowest priority rule and cannot be
deleted. You can, however, change the rate and reservoir size with UpdateSamplingRule" [11].
Same default ("first request each second, and five percent of any additional requests") on [6][12].
Managing the Default rule with `aws_xray_sampling_rule` (create = already exists, destroy = cannot
delete) is not documented on [1] (U2).

### Limits [10]
| Quota | Default | Adjustable |
|---|---|---|
| Custom sampling rules **per region** | 25 | Yes (L-8C0C998A) |
| Tags per custom sampling rule | 50 | No |
| Groups in an account (per Region) | 25 | No |
| Tags per group | 50 | No |
| Segment document size | 64 KB | No |
| Segments per second | 2,600 | No |
| Indexed annotations per trace | 50 | No |
| Trace & service graph retention | 30 days | No |
| Trace data modification period | 7 days | No |
| Trace document size | 100 KB lower / 500 KB dynamic upper | No |

## 4. `aws_xray_group` [2]

- Required: `group_name`, `filter_expression`. Optional: `insights_configuration { insights_enabled (required), notifications_enabled (optional) }`, `tags`, `region`.
- Exported: `arn`, `id` (= ARN), `tags_all`. Import by **ARN** (identity `{ arn }` TF ≥ 1.12; `id` TF ≥ 1.5; CLI) [2].
- AWS: group name max **32 chars**, alphanumeric and dashes, case sensitive; groups cannot be
  renamed; the **Default** group cannot be deleted [13].
- "Updating a group's filter expression doesn't change data that's already recorded … can result in
  a merged graph … To avoid this, delete a current group and create a new one" [13].
- Matching-trace metrics are published to CloudWatch every minute; groups are billed by retrieved
  traces matching the filter [13].
- Group ARNs include a generated unique ID (`group/<name>/<id>`) — use wildcard in IAM `CreateGroup` policies [14].
- Insights notifications go to EventBridge, which "does not currently support customer managed keys" [15].

## 5. `aws_xray_encryption_config` [3]

- Required `type`: `KMS` (own key) or `NONE` ("default encryption"). Optional `key_id` (KMS key ARN), `region`.
- `id` = region name; import by region name (identity `{ region }` TF ≥ 1.12) [3].
- **NOTE** [3]: "Removing this resource from Terraform does not change the encryption configuration in X-Ray."
- Region-level singleton: one config per account per region (follows from id = region; M2).
- AWS [15][11]: X-Ray **always** encrypts at rest. Options: default encryption (free), AWS managed
  key `aws/xray` (pay for use; audit in CloudTrail), customer managed key (pay storage + use; manage
  access/rotation). API accepts alias, key ID or ARN; status `UPDATING` → `ACTIVE`. Set `NONE` to
  return to default encryption. **Asymmetric KMS keys not supported.** Existing data is not
  re-encrypted. If X-Ray loses access to the key (e.g. key disabled) "it stops storing data".
  Caller needs user-level access to the CMK to configure it and view traces [15].
- Cross-account CMK: enter full key ARN in console [15].

## 6. Enabling tracing on other services — cross-references only

| Service | Terraform knob | AWS page statements | Owning skill |
|---|---|---|---|
| Lambda | `aws_lambda_function.tracing_config { mode = "Active" \| "PassThrough" }` | Active: Lambda sends traces **for sampled requests** (upstream header decides); default without Active is PassThrough, which forwards the header but does not send traces; sampling 1 req/s + 5 %, **not configurable**; tracing mode cannot change on a published version; not supported with MSK/self-managed Kafka/Amazon MQ/DocumentDB ESMs; execution role needs `xray:PutTraceSegments`, `xray:PutTelemetryRecords` (in `AWSXRayDaemonWriteAccess`) [16] | provisioning-aws-lambda-v6 |
| API Gateway | `aws_api_gateway_stage.xray_tracing_enabled = true` | "X-Ray only supports tracing for REST APIs through API Gateway"; all endpoint types; uses X-Ray sampling rules; redeploy after enabling; HTTP-integration URL paths can exceed the 10,000-node trace-map limit [17] | provisioning-aws-api-gateway-v6 |
| Step Functions | `aws_sfn_state_machine.tracing_configuration { enabled = true }` | Role needs `xray:PutTraceSegments`, `PutTelemetryRecords`, `GetSamplingRules`, `GetSamplingTargets`; no X-Ray for Distributed Map child executions; 100 KiB guaranteed trace size [12] | provisioning-aws-step-functions-v6 |

Exact Terraform argument shapes are owned by the sibling skills (their research files cite the provider pages).

## 7. IAM, instrumentation and 2026 changes

- **`AWSXRayDaemonWriteAccess`** [14]: `xray:PutTraceSegments`, `PutTelemetryRecords`,
  `GetSamplingRules`, `GetSamplingTargets`, `GetSamplingStatisticSummaries` on `*`. Other managed
  policies: `AWSXrayReadOnlyAccess`, `AWSXrayFullAccess` (`xray:*`), `AWSXrayCrossAccountSharingConfiguration` [14].
- Resource-level permissions only for `Create/Get/Update/DeleteGroup` and
  `Create/Update/DeleteSamplingRule`; everything else needs `"*"`. Sampling-rule ARN = name (no ID) [14].
- Tag-based access control on groups/rules via `aws:RequestTag` / `aws:ResourceTag` [14].
- **SDK/Daemon maintenance mode since 2026-02-25** [7][8]; AWS: "X-Ray is transitioning to
  OpenTelemetry (OTel) as its primary instrumentation standard" and recommends OpenTelemetry SDKs /
  ADOT for instrumentation and the OpenTelemetry Collector / CloudWatch agent for collection, for new
  **and** existing applications [7]. Full migration = replace SDK usage and replace the daemon [7].
- CloudWatch agent ≥ 1.300025.0 can collect OTel traces; collectors need `xray:PutTraceSegments` [7].
- Lambda: recommended AWS Lambda Layer for OpenTelemetry (Application Signals); for tracing only set
  `OTEL_AWS_APPLICATION_SIGNALS_ENABLED=false`; or the ADOT managed layer [7].
- Spans convert to X-Ray segments; CloudWatch console experience unchanged [7].
- No 2026 change to the **default sampling rule** was found on official pages (values in §3 stand).
- Sampling rules and groups are now also configurable in the CloudWatch console (Settings → X-Ray traces) [6][13].

## 8. AWS guidance — best practices and Security Hub

Security Hub: **no `XRay.*` controls** in the controls reference (2026-10-23, both page chunks
read) [18]. Related controls:

| ID | Title | Severity | Terraform mapping |
|---|---|---|---|
| APIGateway.3 | API Gateway REST API stages should have AWS X-Ray tracing enabled | LOW | `xray_tracing_enabled = true` (sibling) |
| Lambda.7 | Lambda functions should have AWS X-Ray active tracing enabled | LOW | `tracing_config { mode = "Active" }` (sibling) |

No Step Functions X-Ray control listed [18].

Best practices (as stated on AWS pages):
1. Define sampling rules centrally in the service rather than local JSON (avoids summed reservoirs, no redeploy) [6].
2. Put rules on root/entry services (parent-based sampling) [6].
3. Use a CMK when you must manage access/rotation; `aws/xray` when you only need CloudTrail audit [15]; never asymmetric; keep the key enabled or X-Ray stops storing data [15].
4. Start with managed policies, move to least privilege; scope group/sampling-rule actions by ARN [14].
5. Adopt OpenTelemetry/ADOT for new and existing apps [7][8].
6. Lower default rule rate where volume is high (example: rate 1 %, reservoir 0) [11].

## 9. Unverified / medium confidence / limits / legacy errors

- U1 Unique priority required / tie behaviour — not stated on AWS pages read.
- U2 Terraform handling of the `Default` sampling rule — not documented on [1].
- U3 KMS key-policy statements needed for `xray.amazonaws.com` (legacy example) — not verified.
- M1 `priority`/`rule_name` immutability in AWS [12]; provider ForceNew behaviour not stated.
- M2 Encryption config is a per-region singleton (inferred from id = region).
- L1 `aws_xray_indexing_rule`, `aws_xray_trace_segment_destination`, `aws_xray_resource_policy` not researched (out of brief scope; exist since 6.46.0 [5]).
- L2 SamplingRateBoost not exposed per provider doc [1] at read time.
- L3 Data sources (none checked); CloudWatch Application Signals provisioning out of scope.

**Legacy-file claims found wrong:**
- "Default encryption `NONE` uses AWS-managed keys" — wrong: `NONE` = default encryption; the AWS managed key `aws/xray` is a `KMS` choice [15][11].
- "Lambda `Active` always creates a trace segment regardless of sampling" — wrong: traces for sampled requests only; sampling not configurable [16].
- "25 custom rules per account" — AWS: 25 **per region**, adjustable [10].
- `required_version >= 1.7`, `~> 6.0`, `dynamodb_table` locking — superseded (F1, F3, F7).
- Error rule using `attributes = { "http.status" = "5??" }` — attributes are ignored by the X-Ray SDK and API Gateway matches request headers [6]; the example is not supported by docs.
- "HTTP API traces via Lambda integration" — X-Ray traces only REST APIs through API Gateway [17].
- Legacy treats `rule_name` as required; provider marks it Optional [1].

## 10. Security note

No prompt-injection or instruction-like text observed in fetched pages.

## Source Bibliography

All accessed 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_sampling_rule.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_group.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_encryption_config.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
6. https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html
7. https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html
8. https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html
9. https://docs.aws.amazon.com/xray/latest/api/API_SamplingRule.html
10. https://docs.aws.amazon.com/general/latest/gr/xray.html
11. https://docs.aws.amazon.com/xray/latest/devguide/xray-api-configuration.html
12. https://docs.aws.amazon.com/step-functions/latest/dg/concepts-xray-tracing.html
13. https://docs.aws.amazon.com/xray/latest/devguide/xray-console-groups.html
14. https://docs.aws.amazon.com/xray/latest/devguide/security_iam_id-based-policy-examples.html
15. https://docs.aws.amazon.com/xray/latest/devguide/xray-console-encryption.html
16. https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html
17. https://docs.aws.amazon.com/xray/latest/devguide/xray-services-apigateway.html
18. https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-controls-reference.html
