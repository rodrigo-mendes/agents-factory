---
name: observing-aws-cloudwatch
description: "Architects and validates AWS observability stacks using Amazon CloudWatch (metrics, logs, alarms, traces, Application Signals, cross-account monitoring, OTLP/PromQL). Encodes production guardrails: log retention policy, alarm missing-data treatment, M-out-of-N evaluation, EMF for serverless metrics, and OpenTelemetry standardization. Use when designing or reviewing a CloudWatch-based observability architecture, configuring production alarms, selecting log classes, or migrating instrumentation to OpenTelemetry on AWS."
---

## Function
Specialist in cloud observability architecture for Amazon CloudWatch — aligned to the AWS Well-Architected Operational Excellence pillar.

## Version Context

**Technology**: Amazon CloudWatch (AWS managed service)
**Target version**: Current edition — 2026; currency threshold 2027-07
**Support status**: Active (AWS-managed, continuously updated)

**Key capabilities in this edition**:
- Native OTLP endpoints (metrics, logs, traces) + PromQL via CloudWatch Query Studio + PromQL alarms
- Application Signals: auto-instrumented APM + SLOs/error budgets (no code changes required)
- Log alarms: alarm directly on a scheduled Logs Insights query (M-out-of-N)
- CloudWatch Logs classes: Standard / Infrequent Access / Archive Instant Access
- Cross-account observability via AWS Organizations (OAM)

⚠️ **Version Lock**: Targets 2026 CloudWatch edition. Re-verify after 2027-07 at:
https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatsNew.html

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 5 mandatory patterns: retention, alarms, centralization, EMF, OTel
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 4 decision matrices: metric model, log class, resolution, visualization
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 5 anti-patterns with ❌ wrong / ✅ correct code and CLI detection
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 test cases: standard, edge, misuse
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands
- **[Quick Reference](#quick-reference)** — Limits table + essential CLI
- **[External Resources](#external-resources)** — Official documentation

---

## Blueprints & Guardrails

### ✅ Always Do

See [Always Do Patterns](./blueprints/always-do-patterns.md) for full CLI examples and IaC snippets.

- **Set explicit log-group retention** — Default is infinite (unbounded cost + compliance liability). Define retention per data class (e.g. 30–90 days Standard for operational; 1–7 years Infrequent Access for audit). Enforce via IaC and an AWS Config rule so no log group is created with `retentionInDays == null`.

- **Alarm on sustained breaches: M-out-of-N + explicit TreatMissingData** — Set `period >= metric resolution`, `DatapointsToAlarm` (e.g. 3-of-3), and an explicit `TreatMissingData` policy per alarm. Roll noisy alarms into a composite alarm; page on-call only on the composite.

- **Centralize observability into a dedicated monitoring account** — In multi-account orgs, link source accounts via OAM with AWS Organizations auto-linking. Constraint: cross-account composite alarms are unsupported; `ANOMALY_DETECTION_BAND`, `INSIGHT_RULE`, and `SERVICE_QUOTA` math functions are unsupported cross-account.

- **Publish custom metrics via EMF in serverless/containers** — Prefer Embedded Metric Format over synchronous `PutMetricData` to eliminate request-path latency and get correlated logs + metrics in one write. Keep dimension combinations bounded (each unique set = one billed metric).

- **Standardize instrumentation on OpenTelemetry (OTLP)** — CloudWatch exposes native OTLP endpoints; same OTel SDK targets CloudWatch and any third-party backend. Choose one query model per team (Metrics Insights vs PromQL) and document it.

### ⚠️ Ask First

See [Ask First Decisions](./blueprints/ask-first-decisions.md) for full option matrices and cost profiles.

- **Traditional CloudWatch metrics vs OTLP metrics** — Ask: does the team standardize on Metrics Insights or PromQL? Is multi-backend portability required? (Traditional = 30 dimensions, deep AWS integration, Metrics Insights; OTLP = 150 labels, PromQL, portable)

- **Log class per log group** — Ask: how often is each group queried? What is the retention/compliance requirement? (Standard = full features; Infrequent Access = lower cost, reduced features; Archive Instant Access = long-term storage)

- **Standard (1-min) vs high-resolution (1s) metrics** — Ask: does sub-minute detection materially change the response (autoscaling, SLO breach)? High-res alarms (10s/30s) incur a higher billing tier (`HighResAlarmMonitorUsage`).

- **Native CloudWatch dashboards vs Amazon Managed Grafana** — Ask: must visualization span multiple telemetry sources or backends? Yes → prefer Managed Grafana. AWS-native ops only → native dashboards suffice and avoid a second managed service.

### 🚫 Never Do

See [Never Do Patterns](./blueprints/never-do-patterns.md) for ❌/✅ side-by-side code and CLI detection queries.

| Anti-Pattern | Risk | ✅ Correct Alternative |
|---|---|---|
| Log group with default (never-expire) retention | HIGH | Explicit `retentionInDays` on every log group; enforce via IaC + Config rule |
| Latency alarm with `Statistic: Average` | MEDIUM | Use `p95` or `p99` extended statistic aligned to the SLO |
| Critical alarm without explicit `TreatMissingData` | HIGH | Set `breaching` (no heartbeat = down) or `notBreaching` (legitimately idle) — document intent |
| Every metric alarm wired directly to on-call SNS | MEDIUM | Keep metric alarms for context; page only on a composite alarm |
| High-cardinality value (`RequestId`, `UserId`) as a metric dimension | MEDIUM | Put identifiers in EMF structured log fields; keep dimensions low-cardinality |

---

## Integration Patterns

- **CloudWatch ↔ Application Signals / X-Ray** — Application Signals auto-instruments APM golden signals (latency, error rate, request rate) with SLOs and error budgets. Pairs with X-Ray Transaction Search for trace correlation.

- **CloudWatch ↔ Amazon SNS** — Alarm state transitions trigger SNS topics; route composite alarm → SNS → on-call, Systems Manager OpsItems, or Lambda remediation.

- **CloudWatch ↔ AWS Organizations (OAM)** — Monitoring account creates OAM sink; source accounts create OAM links. Auto-link all org accounts via Organizations to avoid manual per-account setup.

- **CloudWatch ↔ Amazon Managed Grafana / AMP** — Scale-out visualization for high-cardinality or multi-source scenarios; offload Prometheus-native workloads to Amazon Managed Service for Prometheus (AMP) as volume grows.

**Common problems**:
- **Cross-account composite alarm fails** → Composite alarms must reside in the same account as their member alarms; restructure to intra-account rollups.
- **`ANOMALY_DETECTION_BAND` fails in monitoring account** → Create the alarm in the source account; this math function is not supported cross-account.
- **p99 alarm stays `INSUFFICIENT_DATA`** → Alarm `period` is shorter than the metric's native resolution; set `period >= native resolution` (e.g. ≥300s for 5-min EC2 basic monitoring).
- **EMF metrics not extracted** → Verify `_aws.CloudWatchMetrics[].Namespace` key exists in the JSON log event body.

---

## Verification Loop

Run after any CloudWatch configuration change:

### 1. Log Retention Compliance
```bash
aws logs describe-log-groups \
  --query 'logGroups[?retentionInDays==`null`].logGroupName'
# Expected: [] — no log group with infinite retention
```

### 2. Alarm Health
```bash
# Alarms missing explicit missing-data handling
aws cloudwatch describe-alarms \
  --query 'MetricAlarms[?TreatMissingData==`missing`].[AlarmName]'
# Expected: []

# Latency alarms using Average statistic (should be 0)
aws cloudwatch describe-alarms \
  --query 'MetricAlarms[?contains(MetricName,`Latency`) && Statistic==`Average`].[AlarmName]'
# Expected: []
```

### 3. Cross-Account Observability
```bash
aws oam list-sinks   # Monitoring account — must show configured sink
aws oam list-links   # Source accounts — must show active link to monitoring account
```

### 4. EMF Metric Extraction
```bash
aws cloudwatch list-metrics --namespace "MyApp/Prod"
# Expected: metric names matching EMF definitions appear within ~2 min of log ingestion
```

**Troubleshooting**:
- `INSUFFICIENT_DATA` on new alarm → `period` shorter than metric resolution; increase to match or exceed native resolution
- EMF metrics absent → Check `_aws` JSON envelope structure is valid in log events
- Cross-account metrics not visible → Verify OAM link in source account + IAM trust in monitoring account

---

## Quick Reference

**Essential CLI**:
```bash
# Find log groups with no retention
aws logs describe-log-groups --query 'logGroups[?retentionInDays==`null`].logGroupName'

# Set retention on a log group
aws logs put-retention-policy --log-group-name /app/prod --retention-in-days 30

# List alarms with key config
aws cloudwatch describe-alarms \
  --query 'MetricAlarms[].[AlarmName,TreatMissingData,EvaluationPeriods,DatapointsToAlarm]'

# Verify OAM sinks (monitoring account)
aws oam list-sinks

# List metrics in a custom namespace
aws cloudwatch list-metrics --namespace "MyApp/Prod"
```

**Critical limits**:

| Resource | Limit | Scope |
|----------|-------|-------|
| Dimensions per traditional metric | 30 | Per metric |
| Labels per OTLP metric | 150 | Per metric |
| Standard resolution | 1 min | AWS-vended and custom |
| High-resolution | 1 sec | Custom metrics only |
| Log retention range | 1 day – 10 years | Per log group; default = infinite |
| Metric data auto-expiry | 15 months | After last data point |
| Max alarm evaluation window | 7 days (period ≥ 1h) / 1 day (shorter) | Per alarm |

---

## External Resources

### Official AWS Documentation (accessed 2026-07-31)
- [What is Amazon CloudWatch?](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html)
- [CloudWatch metrics concepts](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html) — Namespaces, dimensions, resolution, statistics, percentiles, periods, OTel metrics
- [Using CloudWatch alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html) — Types, states, missing data, composite alarms
- [CloudWatch Logs concepts](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Concepts.html) — Retention, log classes, metric/subscription filters
- [CloudWatch billing and cost optimization](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_billing.html)
- [Well-Architected: AWS Observability Tools](https://docs.aws.amazon.com/wellarchitected/latest/management-and-governance-guide/aws-observability-tools.html)
- [Publish custom metrics (PutMetricData / EMF)](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html)
- [Send metrics using OpenTelemetry](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OpenTelemetry-Sections.html)

### Best Practices
- [AWS Observability Best Practices — CloudWatch recipes](https://aws-observability.github.io/observability-best-practices/recipes/cw/) — Community-curated, AWS-maintained (accessed 2026-07-31)
- [EKS Observability Best Practices](https://docs.aws.amazon.com/prescriptive-guidance/latest/amazon-eks-observability-best-practices/introduction.html) — AWS Prescriptive Guidance (accessed 2026-07-31)

### Research Base
- Source research: `StoryBeats/docs/research_cloud_AWS_Observability-CloudWatch_2026.md` — dated 2026-07-31
