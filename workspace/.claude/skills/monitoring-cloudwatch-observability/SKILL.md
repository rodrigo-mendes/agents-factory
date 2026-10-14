---
name: monitoring-cloudwatch-observability
description: "Implements AWS CloudWatch full-stack observability for web applications using metrics, logs, traces, alarms, and Application Signals. Use when designing or reviewing the observability layer of an AWS-hosted web application, serverless workload, or multi-account architecture."
---

## Function

Specialist in AWS CloudWatch Observability architecture for web applications on AWS. Covers metrics (Classic and OTel), logs, distributed tracing (ADOT), alarms, dashboards, SLOs, synthetics, real-user monitoring, and cross-account observability as of 2026.

## Version Context

**Technology**: Amazon CloudWatch
**Target version**: AWS CloudWatch 2026 (current stable)
**Research date**: 2026-08-30
**Currency threshold**: 2027-08-30
**Support status**: Active

**Critical 2026 changes**:
- OTel metrics ingestion via CloudWatch OTLP endpoint — GA June 2026. Now a first-class path alongside Classic PutMetricData. Supports PromQL alarms and up to 150 labels per metric (vs. 30 dimensions Classic).
- X-Ray SDK and X-Ray Daemon entered maintenance mode (security fixes only). ADOT is the recommended instrumentation path for new workloads. [Exact maintenance-mode announcement date: UNVERIFIED]
- Log Alarms — new alarm type running Logs Insights queries on a schedule (GA 2026).
- OTel-based Container Insights for EKS (Preview April 2026); EKS Observability Add-on enables Application Signals by default (February 2026).
- CloudWatch Log Analytics unified console (GA June 2026).
- ALB access logs now deliverable directly to CloudWatch Logs.
- GenAI observability (GA October 2025): monitors Amazon Bedrock AgentCore agents with 13 pre-built evaluators.

**Deprecated**:
- X-Ray SDK (language-specific) — maintenance mode; plan migration to ADOT for new workloads.

⚠️ **CRITICAL — Agent Warning**:
This skill targets CloudWatch as of 2026. Do not apply X-Ray SDK patterns for new workloads — use ADOT. The OTel metric model (labels, PromQL) is NOT compatible with Classic metric model (dimensions, Metric Math) — do not mix alarm types across models.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 operational rules (mandatory reading)
- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 8 mandatory patterns with verification commands
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 4 architectural decision matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 7 anti-patterns with detection commands
- **[Integration Patterns](#integration-patterns)** — service composition and common problems
- **[Verification Loop](#verification-loop)** — CLI commands to validate observability posture
- **[Quick Reference](#quick-reference)** — critical limits and CLI essentials
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases for skill validation
- **[External Resources](#external-resources)** — official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For full patterns with verification commands, see [Always Do Patterns](./blueprints/always-do-patterns.md).

- **Set log retention at creation** — Never allow a log group to exist without explicit `RetentionInDays`. Default is "Never Expire" = unbounded cost. Tier: debug 14d, app 90d, access 365d, audit 7yr (2555d). IaC (CloudFormation/CDK) is the enforcement mechanism; no console-only creation.
- **Encrypt log groups with CMK** — Associate a symmetric KMS key at log group creation. Key policy must grant `logs.<region>.amazonaws.com` Encrypt/Decrypt/ReEncrypt*/GenerateDataKey*/Describe* with `kms:EncryptionContext:aws:logs:arn` condition scoped to the specific log group ARN. Asymmetric keys are not supported.
- **Metric alarms wired to SNS for all three state transitions** — Every critical metric (HTTP 5xx rate, P99 latency, queue depth) must have a CloudWatch alarm with SNS actions on ALARM, OK, and INSUFFICIENT_DATA transitions. Dashboards alone do not satisfy OPS04-BP02.
- **Composite alarms per application tier** — Group correlated child alarms with Boolean rule expressions (`AND`/`OR` on child alarm states). Suppress SNS actions on individual child alarms; put the single SNS action on the composite alarm. Prevents alert storms from a single root-cause event.
- **Anomaly detection on variable metrics** — Enable on ALB RequestCount, TargetResponseTime, Lambda Invocations, and application error rate. Start at 2–3 standard deviations. Exclude known deployment windows via `PutAnomalyDetector` API `ExcludedTimeRanges`. Eliminates false positives from daily/weekly traffic patterns.
- **Instrument all tiers with ADOT for distributed tracing** — Use AWS Distro for OpenTelemetry (not X-Ray SDK) on all service tiers. Lambda: enable Active Tracing in the console. ECS/EKS: ADOT Collector as sidecar. Add X-Ray Annotations (max 50/trace) for searchable fields (customerId, tenantId). Absence of tracing is rated HIGH risk by Well-Architected OPS04-BP05.
- **Golden-signals dashboard per tier** — Create one CloudWatch Dashboard per application tier with P50/P95/P99 latency, requests per second, error rate, and saturation widgets. Define dashboards as code (`AWS::CloudWatch::Dashboard`). First 3 dashboards free; $3/month each after.
- **Cross-account observability via OAM for multi-account architectures** — Designate a monitoring account with an OAM sink. Source accounts create OAM links. Use CloudFormation StackSets via AWS Organizations for automatic onboarding. No extra charge for metrics and logs; first X-Ray trace copy free.

### ⚠️ Ask First

For full decision matrices, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **Observability instrumentation strategy** — Ask: "Does this application need to send telemetry to more than one monitoring backend now or within 18 months, or does the organisation have an existing non-AWS APM contract?" Options: CloudWatch Native (lowest cost, highest lock-in) vs. ADOT (OTel standard, multi-backend) vs. Third-party APM via Metric Streams (existing contract).
- **Custom metrics ingestion strategy** — Ask: "Are you instrumenting ephemeral/serverless compute and need to correlate metric values with the log that produced them?" Options: EMF (Lambda/containers, log+metric correlation), PutMetricData API (batch, non-ephemeral), Metric Filters (no-code-change on existing logs), Metric Streams (outbound only — not for ingestion).
- **Log analytics backend strategy** — Ask: "Is the primary use case: (a) operational incident response with alarm correlation, (b) compliance long-term archival with ad-hoc SQL, or (c) full-text search and rich dashboards?" Options: CloudWatch Logs + Insights (a), S3 + Athena (b), OpenSearch via Firehose (c).
- **Distributed tracing strategy** — Ask: "Do you need SLO management and automatic service topology discovery? Or must traces go to a non-AWS backend?" Options: Application Signals (zero-code APM + SLO, Java/Python/Node.js/.NET), ADOT manual OTel SDK (multi-backend or unsupported language), X-Ray SDK (existing apps only — plan migration to ADOT).

### 🚫 Never Do

For full anti-patterns with detection commands, see [Never Do Patterns](./blueprints/never-do-patterns.md).

| Anti-Pattern | Risk | Correct Alternative |
|---|---|---|
| Log group left at Never-Expire retention | CRITICAL — unbounded cost, governance failure | Set `RetentionInDays` at creation in IaC; enforce with AWS Config rule |
| Dashboard-only monitoring without alarms | HIGH — MTTD is unbounded; outages go undetected until a human opens the console | CloudWatch Alarms + Composite Alarms wired to SNS on all state transitions |
| Individual metric alarms all firing SNS with no composite alarms | HIGH — alert fatigue; on-call ignores notifications | Composite alarm per tier with single SNS action; suppress child alarm SNS actions |
| Plaintext secrets or PII in log events | CRITICAL — credential exposure, PCI DSS/GDPR violation | Application-level redaction before logging + CloudWatch Logs data protection policies for PII masking |
| Single-metric CPU-only health alarm | HIGH — misses latency, errors, saturation (OPS04-BP01) | Composite alarm combining latency P99, 5xx error rate, CPU, and memory utilization |
| Multi-service web app with no distributed tracing | HIGH — OPS04-BP05 explicitly rates absence of tracing as HIGH risk | ADOT on all tiers; Lambda Active Tracing; verify service map in CloudWatch ServiceLens |
| PutMetricData with high-cardinality dimensions (userId, requestId) | HIGH — metric count explodes proportionally with user base | Aggregate dimensions only (Environment, Service); use EMF + Logs Insights for per-user analytics |

---

## Integration Patterns

**CloudWatch ↔ AWS Lambda** — Lambda publishes CloudWatch Metrics natively (AWS/Lambda namespace). Enable Lambda Insights extension layer for memory/CPU/cold-start data. Use EMF from the Lambda handler for custom business metrics. Enable Active Tracing for X-Ray integration via ADOT.

**CloudWatch ↔ AWS Application Load Balancer** — ALB publishes to AWS/ApplicationELB namespace automatically. ALB access logs now ship directly to CloudWatch Logs (2026). Use `HTTPCode_Target_5XX_Count` and `TargetResponseTime` as primary alarm metrics. Layer anomaly detection on `RequestCount`.

**CloudWatch ↔ ECS / EKS** — Enable Container Insights enhanced observability (not standard) for task/container-level drill-down. Deploy ADOT Collector as sidecar on ECS; use EKS Observability Add-on for EKS (installs enhanced Container Insights + Application Signals by default as of February 2026). OTel Container Insights for EKS (Preview April 2026) uses OTLP and PromQL.

**CloudWatch ↔ AWS X-Ray** — X-Ray is the trace backend; CloudWatch Application Signals synthesizes SLI/SLO health on top of X-Ray traces. ServiceLens and Application Signals service map require active X-Ray tracing on all tiers. CloudWatch RUM supports X-Ray end-to-end trace propagation from browser through API Gateway and Lambda.

**CloudWatch ↔ Third-Party APM (Datadog, Dynatrace, Splunk, New Relic)** — Use Metric Streams + Amazon Data Firehose to push CloudWatch metrics in near real-time. Output formats: JSON, OpenTelemetry 1.0.0, OTel 0.7.0. Does not support historical backfill. Cannot mix include and exclude filters on the same stream.

**Common problems**:
- **Problem**: Application Signals service not appearing on map → **Solution**: Confirm ADOT instrumentation is active on the service and that at least one request has been traced; service discovery can take up to 10 minutes after first trace.
- **Problem**: Log group cost growing unboundedly → **Solution**: Run `aws logs describe-log-groups --query 'logGroups[?retentionInDays==null].[logGroupName,storedBytes]'`; apply retention policy immediately, then enforce via IaC going forward.
- **Problem**: OTel metric alarms not triggering → **Solution**: PromQL alarms apply only to OTel metrics ingested via the CloudWatch OTLP endpoint; Classic CloudWatch metrics require standard threshold or Metric Math alarms — confirm the metric ingestion path before selecting alarm type.
- **Problem**: EMF metrics unexpectedly expensive → **Solution**: Audit dimension cardinality: each unique dimension combination creates a separately billed custom metric. Replace high-cardinality dimensions (userId, sessionId) with aggregate values.

---

## Verification Loop

Run after designing or modifying the observability layer:

### 1. Log Retention Compliance
```bash
aws logs describe-log-groups \
  --query 'logGroups[?retentionInDays==null].[logGroupName,storedBytes]'
# Expected: empty array []
# Any result = VIOLATION — set RetentionInDays immediately
```

### 2. Log Group KMS Encryption
```bash
aws logs describe-log-groups \
  --query 'logGroups[*].[logGroupName,retentionInDays,kmsKeyId]'
# Expected: kmsKeyId present on all log groups containing sensitive or compliance data
```

### 3. Alarms With Empty Action Arrays
```bash
aws cloudwatch describe-alarms \
  --query 'MetricAlarms[*].[AlarmName,AlarmActions,OKActions,InsufficientDataActions]'
# Expected: no alarms with empty AlarmActions array on critical metrics
```

### 4. Composite Alarms Exist
```bash
aws cloudwatch describe-alarms --alarm-types CompositeAlarm \
  --query 'CompositeAlarms[*].[AlarmName,AlarmRule,AlarmActions]'
# Expected: at least one composite alarm per application tier
# Empty result = alert fatigue risk
```

### 5. Lambda Tracing Mode
```bash
aws lambda list-functions \
  --query 'Functions[*].[FunctionName,TracingConfig.Mode]'
# Expected: all production functions show Mode = Active
# PassThrough = tracing is disabled (OPS04-BP05 violation)
```

### 6. ServiceLens Service Map
```
CloudWatch console > ServiceLens > Service Map
Expected: all application tiers appear as nodes with trace data
Empty map or single node = distributed tracing is absent
```

### 7. Anomaly Detectors
```bash
aws cloudwatch describe-anomaly-detectors
# Expected: detectors exist for ALB RequestCount, TargetResponseTime, Lambda Invocations
```

**Troubleshooting**:
- `AccessDenied` on `oam:ListSinks` → Add `oam:Get*`, `oam:List*` to the operator IAM role.
- Anomaly detector model shows `PENDING_TRAINING` → Allow up to 2 weeks of metric history before the band stabilizes.
- PromQL alarm in `INSUFFICIENT_DATA` → Confirm metrics are being ingested via OTLP endpoint (`/v1/metrics`), not Classic PutMetricData.

---

## Quick Reference

**Essential CLI commands**:
```bash
# Set log retention
aws logs put-retention-policy --log-group-name <name> --retention-in-days 90

# Associate KMS key
aws logs associate-kms-key --log-group-name <name> --kms-key-id <arn>

# Describe composite alarms
aws cloudwatch describe-alarms --alarm-types CompositeAlarm

# List custom metrics (cardinality check)
aws cloudwatch list-metrics --namespace <app-namespace>

# OAM setup (monitoring account)
aws oam list-sinks
aws oam list-attached-links --sink-identifier <sink-arn>
```

**Critical service limits**:

| Resource | Limit | Notes |
|---|---|---|
| Classic metric dimensions | 30 per metric | OTel labels: 150 per metric |
| X-Ray annotations | 50 per trace | Use Metadata for unindexed context |
| Composite alarm cross-account | Not supported | Metric alarms support cross-account |
| SLOs per Region | 250 (adjustable) | 100 per service (adjustable) |
| OAM source accounts per monitoring account | 100,000 | Each source can share with up to 5 monitoring accounts |
| Metric Streams filters per stream | 1,000 include OR exclude | Cannot mix include and exclude on same stream |
| CloudWatch Synthetics canaries | 500 per account per Region | Minimum run frequency: 60 seconds |
| Dashboard cost | $3/month per dashboard | First 3 free |

**Retention tiers** (default recommendation):

| Log type | Retention |
|---|---|
| Debug / trace | 14 days |
| Application logs | 90 days |
| Access logs | 365 days |
| Audit / compliance | 2555 days (7 years) |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/monitoring-cloudwatch-observability/
├── SKILL.md                              ← This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md             ← 8 mandatory patterns with full CLI verification
    ├── ask-first-decisions.md            ← 4 architectural decision matrices with tradeoff tables
    ├── never-do-patterns.md              ← 7 anti-patterns with detection commands
    └── evaluation-scenarios.md           ← 6 test scenarios for skill validation
```

---

## External Resources

### Official Documentation
- [CloudWatch Monitoring — Main Docs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/) — Primary reference (2026-08-30)
- [CloudWatch Logs — Main Docs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/) — Log groups, metric filters, insights (2026-08-30)
- [CloudWatch Concepts (Metrics, Namespaces, Dimensions)](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html) — Foundational terms (2026-08-30)
- [CloudWatch Alarms — Best Practices](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Best-Practice-Alarms.html) — Alarm recommendations (2026-08-30)
- [Application Signals — APM / SLOs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Monitoring-Sections.html) — Auto-instrumented APM (2026-08-30)
- [CloudWatch Cross-Account Observability (OAM)](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Unified-Cross-Account.html) — Multi-account setup (2026-08-30)
- [ADOT — AWS Distro for OpenTelemetry](https://docs.aws.amazon.com/xray/latest/devguide/xray-services-adot.html) — Recommended instrumentation path (2026-08-30)

### Security & Compliance
- [Encrypt Log Data with KMS](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/encrypt-log-data-kms.html) — CMK setup (2026-08-30)
- [CloudWatch Logs Data Protection](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html) — PII masking policies (2026-08-30)
- [Security Hub CloudWatch Controls](https://docs.aws.amazon.com/securityhub/latest/userguide/cloudwatch-controls.html) — CIS/NIST/PCI compliance controls (2026-08-30)
- [IAM for CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/iam-access-control-overview-cwl.html) — Least-privilege reference (2026-08-30)

### Well-Architected Alignment
- [OPS04-BP05 — Distributed Tracing](https://docs.aws.amazon.com/wellarchitected/latest/framework/ops_observability_dist_trace.html) — Explicitly rates absence of tracing as HIGH risk (2026-08-30)
- [Implementing Logging and Monitoring](https://docs.aws.amazon.com/prescriptive-guidance/latest/implementing-logging-monitoring-cloudwatch/application-tracing-xray.html) — AWS Prescriptive Guidance (2026-08-30)
- [AWS Observability ICYMI Jan–May 2026](https://aws.amazon.com/blogs/mt/aws-observability-icymi-jan-may-2026/) — 2026 feature roundup (2026-08-30)
