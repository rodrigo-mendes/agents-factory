---
name: tracing-aws-xray
description: "Instruments AWS X-Ray distributed tracing with ADOT across Lambda, ECS, API Gateway, and DynamoDB. Use when designing or implementing end-to-end distributed tracing on AWS workloads, migrating from the legacy X-Ray SDK to ADOT, or debugging observability gaps in a microservice architecture."
---

## Function

Specialist in AWS X-Ray distributed tracing, ADOT instrumentation, and CloudWatch observability integration for AWS web applications and microservices — 2026 edition (X-Ray SDK maintenance mode; ADOT mandatory for all new instrumentation).

## Version Context

**Technology**: AWS X-Ray + AWS Distro for OpenTelemetry (ADOT)
**Target version**: X-Ray 2026 / ADOT GA 2026
**Research date**: 2026-08-31
**Support status**: Active — X-Ray SDK and Daemon in maintenance mode since 2026-02-25; full end-of-support 2027-02-25

**Critical 2026 changes**:
- X-Ray SDKs and X-Ray Daemon: maintenance mode (security patches only) from 2026-02-25; full end-of-support 2027-02-25
- ADOT is the only supported instrumentation path for all new services
- CloudWatch Application Signals (GA June 2024): unified APM with SLOs, RUM, trace/log correlation, AI analysis
- Transaction Search (GA November 2024): 100% span ingestion into `aws/spans` CloudWatch Logs log group
- CloudWatch OTel Endpoint: direct OTLP export to X-Ray over HTTP 1.1 (gRPC NOT supported) without a collector process

**Deprecated**:
- X-Ray SDK (Java, Node.js, Python, Go, .NET, Ruby): no new features; security patches only
- X-Ray Daemon: replaced by ADOT Collector or CloudWatch Agent v1.300025.0+

⚠️ **CRITICAL — Agent Warning**:
This skill targets AWS X-Ray 2026 (post-SDK-maintenance-mode). Reject any pattern that instructs using the legacy X-Ray SDK or X-Ray Daemon for net-new services. Do not mix X-Ray SDK patterns with ADOT patterns.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 operational tiers
- **[Integration Patterns](#integration-patterns)** — Compute, async, and multi-account patterns
- **[Verification Loop](#verification-loop)** — CLI validation commands with expected output
- **[Quick Reference](#quick-reference)** — Service quotas, pricing, OTLP limits
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test scenarios
- **[External Resources](#external-resources)** — Official dated sources

---

## Blueprints & Guardrails

### ✅ Always Do

**P1 — Instrument all new services with ADOT, never the legacy X-Ray SDK** — X-Ray SDK is maintenance-mode as of 2026-02-25; no new features will ever be added. Use ADOT Managed Lambda Layer for Lambda; ADOT Collector sidecar for ECS Fargate; CloudWatch Agent v1.300025.0+ for EC2.

**P2 — Enable Active Tracing explicitly on every Lambda function** — Default mode is `PassThrough` (Lambda forwards headers but sends ZERO segments to X-Ray). Must be set to `Active` per function. CLI: `aws lambda update-function-configuration --function-name <fn> --tracing-config Mode=Active`. SAM: `Tracing: Active`. CloudFormation: `TracingConfig.Mode: Active`.

**P3 — Define all sampling rules centrally in the X-Ray console** — Local sampling JSON files cause each fleet instance to run its own independent reservoir, multiplying effective rates across the fleet. Remove all local rule files from SDK and Collector config. Use `aws xray create-sampling-rule` and `aws xray get-sampling-rules` to manage centrally.

**P4 — Propagate trace context through all service boundaries** — Every downstream HTTP call must use an ADOT-instrumented client. Configure both the X-Ray propagator and the W3C Trace Context propagator in ADOT OTel config. For SQS → Lambda, rely on automatic trace linking (do not manually inject trace headers into SQS message attributes). Strip `X-Amzn-Trace-Id` from HTTP responses to prevent end-user visibility into internal trace IDs.

**P5 — Correlate traces with logs via CloudWatch Application Signals** — Enable Application Signals on all production services. Java: inject `trace_id`, `span_id`, `trace_flags` via MDC in `application.yml`. Python: set `OTEL_PYTHON_LOG_CORRELATION=true`. Node.js: configure OTel log instrumentation in the logger (Pino/Winston/Bunyan). Verify: CloudWatch console Trace Map node shows a "View logs" link.

**P6 — Attach only `AWSXRayDaemonWriteAccess` to compute execution roles** — Grants exactly the five required actions: `xray:PutTraceSegments`, `xray:PutTelemetryRecords`, `xray:GetSamplingRules`, `xray:GetSamplingTargets`, `xray:GetSamplingStatisticSummaries`. ECS ADOT task role additionally needs SSM (`ssm:GetParameters`) and CloudWatch Logs permissions. Reserve `AWSXrayFullAccess` for observability administrator roles only.

**P7 — Configure KMS encryption for regulated workloads** — Default AWS-owned encryption provides no CloudTrail audit visibility. Use the AWS managed key (`aws/xray`) for audit-level compliance; use a symmetric CMK for PCI-DSS / HIPAA / GDPR workloads. X-Ray does NOT support asymmetric KMS keys. Verify: `aws xray get-encryption-config`.

**P8 — Use ADOT Collector sidecar for ECS Fargate** — Add `public.ecr.aws/aws-observability/aws-otel-collector:latest` as a sidecar container in the task definition. Application container exports OTel to `http://localhost:4317` (gRPC) or `http://localhost:4318` (HTTP). Set a dedicated `taskRoleArn` (not the task execution role) with X-Ray write + SSM permissions.

### ⚠️ Ask First

**D1 — X-Ray SDK vs ADOT vs Vanilla OTel** — Ask: "Is this a net-new service or an existing X-Ray SDK service?" Net-new: mandate ADOT. Existing: evaluate migration cost and set a deadline before 2027-02-25. Vanilla OTel is appropriate for multi-cloud environments; it does not support X-Ray remote sampling in all languages.

**D2 — Sampled traces (X-Ray) vs Transaction Search (CloudWatch Logs)** — Ask: "Do we need to debug specific individual user requests, or is statistical sampling sufficient?" Transaction Search enables 100% span capture into `aws/spans` but adds CloudWatch Logs ingestion cost on top of X-Ray charges. Enable selectively for customer-facing APIs and compliance use cases requiring full trace retention.

**D3 — Sampling strategy selection** — Ask: "What is the maximum acceptable monthly X-Ray cost?" Use Reservoir + fixed-rate (default) for most workloads. Enable `SamplingRateBoost` for anomaly-driven auto-increase. Use Transaction Search 100% indexing only for routes requiring per-request debugging.

**D4 — Collector choice: ADOT Collector vs Self-managed OTel Collector vs CloudWatch Agent** — Ask: "Is tail sampling required?" If yes, only a self-managed OTel Collector supports it — neither ADOT Collector nor CloudWatch Agent do. Use CloudWatch Agent if already deployed on EC2 to minimize sidecar count. Use ADOT Collector for Lambda managed layers and AWS support SLA.

### 🚫 Never Do

| Anti-Pattern | Risk | Correct Alternative |
|---|---|---|
| **Instrument a net-new service with the legacy X-Ray SDK** | HIGH — dead end at 2027-02-25 | ADOT Managed Lambda Layer (Lambda); ADOT Collector sidecar (ECS) |
| **Set `Reservoir=10000, Rate=1.0` in a local sampling rule file** | HIGH — each instance runs its own reservoir; unbounded cost at scale | Delete local files; define all rules centrally in X-Ray console; health-check routes: `Rate=0` |
| **Store PII or credentials in annotations (`put_annotation`)** | CRITICAL — annotations are indexed and searchable by any IAM principal with `AWSXrayReadOnlyAccess` | Use `put_metadata()` for debug data; use hashed identifiers as annotation values; apply CMK encryption |
| **Use raw HTTP clients without ADOT/X-Ray instrumentation** | HIGH — trace context not forwarded; disconnected service map nodes; sampling decision reset | Wrap all downstream HTTP calls in an ADOT-instrumented AWS SDK client or instrumented HTTP client |
| **Use default AWS-owned encryption for regulated workloads** | MEDIUM-HIGH — no CloudTrail audit visibility; no key revocation path | Configure `aws/xray` managed key (audit) or symmetric CMK (full control); restrict `xray:PutEncryptionConfig` |
| **Attach `AWSXrayFullAccess` (`xray:*`) to compute execution roles** | HIGH — compromised role can read all traces, alter sampling rules, disable encryption | Attach `AWSXRayDaemonWriteAccess` only; `AWSXrayFullAccess` for observability admins only |
| **Enable X-Ray active tracing on an API Gateway HTTP API or WebSocket API** | HIGH — silently produces no traces; feature is unsupported for these API types | Use REST API type for active tracing; or instrument at compute layer (Lambda/ECS) for HTTP API |
| **Deploy Lambda without setting `TracingConfig: Mode: Active`** | HIGH — default PassThrough sends no segments even from instrumented upstream calls | SAM: `Tracing: Active`; CloudFormation: `TracingConfig.Mode: Active`; or enable via console |
| **Export directly to X-Ray OTLP endpoint from ADOT SDK without an explicit sampler** | HIGH — defaults to `parentbased_always_on`; up to 20x cost increase | Set `OTEL_TRACES_SAMPLER=parentbased_traceidratio` + `OTEL_TRACES_SAMPLER_ARG=0.05`, or use ADOT Collector for centralized sampling |

---

## Integration Patterns

**Lambda + ADOT Managed Layer**
- Enable Active Tracing per function. Attach the AWS-managed ADOT Lambda Layer for the target runtime. `AWSXRayDaemonWriteAccess` is auto-added when enabling via console. Container-image Lambda: cannot use Lambda Layers — bake ADOT layer contents into the Docker image; set `AWS_LAMBDA_EXEC_WRAPPER=/opt/otel-instrument`.

**ECS Fargate + ADOT Sidecar**
- Two-container task definition: application (exports OTel to `localhost:4317`) + ADOT Collector sidecar. Dedicated `taskRoleArn` with `AWSXRayDaemonWriteAccess` + `ssm:GetParameters` + CloudWatch Logs write permissions.

**API Gateway REST (entry point)**
- Enable per-stage active tracing via console (Logs/Tracing tab) or CLI. API Gateway auto-injects `X-Amzn-Trace-Id`. Sampling rules applied at the API Gateway stage propagate downstream via parent-based sampling. HTTP APIs and WebSocket APIs are NOT supported.

**SQS → Lambda (async trace linking)**
- X-Ray auto-links producer and consumer traces when ADOT or X-Ray SDK is used on the producer. Do not manually inject trace headers into SQS message attributes. Limits: max 20 linked traces per segment; max 100 links per trace. For high-fanout: configure oversampling mitigation (Java, Node.js, Python, Go, .NET).

**Multi-account (CloudWatch OAM)**
- Configure CloudWatch Observability Access Manager. First monitoring account receives trace copies for free; accounts 2–5 are charged at standard X-Ray pricing to the source account. Filter by account ID in CloudWatch Trace Map. Maximum: 5 monitoring accounts per source account.

**X-Ray Insights + EventBridge incident pipeline**
- Enable Insights per X-Ray Group. Wire EventBridge (`source: aws.xray`, `detail-type: AWS X-Ray Insight Update`) to SNS/Lambda/SQS. EventBridge delivery is best-effort — do not rely on it as the sole alerting mechanism. CMK encryption is NOT supported for EventBridge Insights events.

**Common problems**:
- **Disconnected nodes in service map** → One or more services not forwarding trace context. Confirm ADOT propagators include both X-Ray and W3C Trace Context propagators.
- **Zero Lambda traces** → Function is in PassThrough mode. Run: `aws lambda get-function-configuration --function-name <fn> --query 'TracingConfig.Mode'`.
- **Service map node count near 10,000** → High-cardinality URL path parameters. Switch to query string parameters or POST body for high-cardinality identifiers.
- **ALB not appearing on service map** → Expected behavior. ALB injects `X-Amzn-Trace-Id` header (Root only, no Parent field) but does NOT appear as a service map node and does NOT support native active tracing.

---

## Verification Loop

Run after each instrumentation change:

```bash
# 1. Verify API Gateway REST active tracing
aws apigateway get-stage --rest-api-id <id> --stage-name <stage> \
  --query 'tracingEnabled'
# Expected: true

# 2. Verify Lambda Active tracing mode
aws lambda get-function-configuration --function-name <fn-name> \
  --query 'TracingConfig.Mode'
# Expected: "Active"

# 3. Find Lambda functions still in PassThrough mode
aws lambda list-functions \
  --query 'Functions[?TracingConfig.Mode==`PassThrough`].FunctionName'
# Expected: [] (empty list)

# 4. Verify centralized sampling rules exist
aws xray get-sampling-rules \
  --query 'SamplingRuleRecords[*].SamplingRule.{Name:RuleName,Rate:FixedRate,Reservoir:ReservoirSize}'
# Expected: rules present; no local rule JSON files in SDK/Collector config

# 5. Verify ECS ADOT sidecar is in task definition
aws ecs describe-task-definition --task-definition <name> \
  --query 'taskDefinition.containerDefinitions[*].name'
# Expected: includes "aws-otel-collector" or equivalent sidecar name

# 6. Verify KMS encryption (regulated workloads)
aws xray get-encryption-config --query 'EncryptionConfig.Type'
# Expected: "KMS" for regulated workloads; "NONE" only for dev/non-regulated

# 7. Verify compute role uses least-privilege policy
aws iam list-attached-role-policies --role-name <compute-role> \
  --query 'AttachedPolicies[*].PolicyName'
# Expected: "AWSXRayDaemonWriteAccess" present; "AWSXrayFullAccess" absent
```

**Troubleshooting**:
- `TracingConfig.Mode: PassThrough` → `aws lambda update-function-configuration --function-name <fn> --tracing-config Mode=Active`
- Disconnected service map nodes → Verify ADOT SDK config includes both `xray` and `tracecontext` propagators
- Cost overrun → Audit local sampling rule files; verify collector-less ADOT has explicit sampler env vars set

---

## Quick Reference

**Key CLI commands**:
```bash
aws xray get-sampling-rules                           # List centralized sampling rules
aws xray get-encryption-config                        # Check KMS encryption status
aws xray get-groups                                   # List X-Ray Groups (Insights scope)
aws xray get-insights --group-name <name>            # Check active anomaly Insights
aws lambda list-functions \
  --query 'Functions[?TracingConfig.Mode==`PassThrough`].FunctionName'
```

**Service Quotas** (source: https://docs.aws.amazon.com/general/latest/gr/xray.html, 2026-08-31):

| Resource | Limit | Adjustable |
|----------|-------|------------|
| Custom sampling rules per region | 25 | Yes |
| Groups per account per region | 25 | No |
| Annotations per trace | 50 | No |
| Segment document size | 64 KB | No |
| Segments per second | 2,600 | No |
| Trace data retention | 30 days | No |
| Trace modification window | 7 days | No |
| Service map nodes | 10,000 | No |

**Pricing** (source: https://aws.amazon.com/xray/pricing/, 2026-08-30):
- Free tier: 100K traces recorded + 1M retrieved per month
- Beyond free tier: $5.00/M traces recorded; $0.50/M traces retrieved
- Transaction Search (`aws/spans` log group): CloudWatch Logs ingestion pricing per GB
- ECS ADOT sidecar: container compute cost per task

**CloudWatch OTel Endpoint constraints**:
- HTTP 1.1 only (gRPC NOT supported); SigV4 authentication required
- 5 MB per request; 10,000 spans per request; 200 KB per span
- Timestamps: within ±2h future / 14 days past

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/tracing-aws-xray/
├── SKILL.md                          ← This file (summary + guardrails)
└── blueprints/
    └── evaluation-scenarios.md       ← 6 test scenarios for skill-evaluator
```

---

## External Resources

### Official Documentation (all dated 2026-08-30 or later)
- [X-Ray Developer Guide](https://docs.aws.amazon.com/xray/latest/devguide/aws-xray.html) — Primary reference
- [X-Ray SDK Migration to ADOT](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html) — Mandatory migration guide; deadline 2027-02-25
- [X-Ray Concepts](https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html) — Segments, annotations, sampling, groups, inferred segments
- [Sampling Rules](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html) — Centralized rule configuration
- [X-Ray Encryption](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-encryption.html) — KMS encryption configuration
- [X-Ray Insights](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-insights.html) — Automated anomaly detection
- [Service Quotas](https://docs.aws.amazon.com/general/latest/gr/xray.html) — All hard limits

### Service Integrations
- [Lambda + X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html) — Active vs PassThrough tracing mode
- [ECS Tracing with ADOT](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/trace-data.html) — Official sidecar pattern
- [API Gateway + X-Ray](https://docs.aws.amazon.com/xray/latest/devguide/xray-services-apigateway.html) — REST only; HTTP/WebSocket not supported
- [SQS + X-Ray trace linking](https://docs.aws.amazon.com/xray/latest/devguide/xray-services-sqs.html) — Auto-linking limits
- [IAM — AWSXRayDaemonWriteAccess](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AWSXRayDaemonWriteAccess.html) — Exact policy actions

### Observability Stack
- [CloudWatch Application Signals — Trace/Log Correlation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Application-Signals-TraceLogCorrelation.html) — SLOs, log injection
- [Transaction Search — 100% Span Ingestion](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search-ingesting-spans.html) — `aws/spans` log group
- [CloudWatch OTel Endpoint](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLP-UsingADOT.html) — Direct OTLP export and cost risk
- [X-Ray Pricing](https://aws.amazon.com/xray/pricing/) — Cost model and free tier
