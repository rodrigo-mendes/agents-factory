# Evaluation Scenarios — observing-aws-cloudwatch

> Three test cases to validate that the skill activates correctly.
> Covers: canonical use, edge case, and misuse/anti-pattern trap.

---

## Scenario 1 — Canonical: Multi-Account AWS Production Observability Stack

```json
{
  "skills": ["observing-aws-cloudwatch"],
  "query": "Design a CloudWatch observability stack for a multi-account AWS landing zone with 3 workload accounts. Requirements: golden-signal monitoring for ECS services, structured logs with 90-day retention for operational logs and 3-year retention for compliance/audit logs, and on-call paging for production incidents.",
  "expected_behavior": [
    "Recommends a dedicated monitoring account with an OAM sink and AWS Organizations-based auto-linking for all 3 workload accounts",
    "Specifies explicit retentionInDays on all log groups: 90 days Standard class for operational, ~1095 days Infrequent Access for compliance/audit",
    "Recommends Application Signals for auto-instrumented APM on ECS with SLOs and error budgets",
    "Designs composite alarms to route to on-call SNS only when a meaningful combined condition holds (e.g. error-rate AND latency-p99 both breaching)",
    "Explicitly notes that cross-account composite alarms are unsupported and that member alarms must reside in their source account",
    "Invokes Ask-First on metric model (traditional vs OTLP) and visualization (native dashboards vs Managed Grafana) before prescribing tooling"
  ]
}
```

---

## Scenario 2 — Edge Case: High-Cardinality + Sub-Minute Latency in Lambda

```json
{
  "skills": ["observing-aws-cloudwatch"],
  "query": "A Lambda function processes payments at peak 5000 req/s and must report per-request transaction latency. The team wants 1-second resolution metrics and a 10-second alarm. They plan to add RequestId and UserId as CloudWatch metric dimensions. Is this appropriate?",
  "expected_behavior": [
    "Asks first (Ask-First pattern) whether sub-second detection materially changes the response (autoscaling, fraud detection) before approving high-resolution metrics",
    "Flags RequestId and UserId as HIGH-cardinality dimension values — a Never Do anti-pattern — and refuses to generate that configuration without substituting a correct alternative",
    "Provides the correct EMF pattern: latency as a metric with low-cardinality dimensions (Service, Environment); RequestId/UserId as EMF structured log fields, not dimensions",
    "If high-resolution is confirmed appropriate: recommends EMF over synchronous PutMetricData to avoid request-path latency in the Lambda hot path",
    "Notes that high-res alarms (10s/30s) are billed at HighResAlarmMonitorUsage — a higher tier — and documents this trade-off explicitly",
    "Recommends p99 as the alarm statistic (not Average) for latency"
  ]
}
```

---

## Scenario 3 — Misuse / Anti-Pattern Trap: "Enable Everything, Log Forever"

```json
{
  "skills": ["observing-aws-cloudwatch"],
  "query": "We want to enable all CloudWatch features across our 15 ECS services. Log everything to CloudWatch Logs with Never Expire retention so we never lose data. Set up alarms on every metric and wire them all to our on-call SNS topic.",
  "expected_behavior": [
    "Flags 'Never Expire' retention as a HIGH-risk Never-Do anti-pattern (unbounded cost + compliance liability) and declines to generate that configuration",
    "Proposes an alternative: ask the team for their query frequency and compliance retention requirement per log group before assigning retentionInDays and log class",
    "Flags wiring every metric alarm directly to on-call SNS as a MEDIUM-risk Never-Do anti-pattern (alert fatigue) and refuses to generate that topology",
    "Proposes composite alarms with a meaningful rule expression as the on-call page trigger, keeping individual metric alarms for context only",
    "Invokes Ask-First on metric model (traditional vs OTLP) and visualization before enabling 'all features'",
    "Does NOT generate any configuration with a log group lacking retentionInDays or with metric alarms directly paging on-call without a composite rollup"
  ]
}
```
