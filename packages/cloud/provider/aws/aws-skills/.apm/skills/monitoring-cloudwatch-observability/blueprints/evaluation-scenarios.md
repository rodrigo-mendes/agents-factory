# Evaluation Scenarios — monitoring-cloudwatch-observability

Test cases for `/evaluating-skill-scenarios monitoring-cloudwatch-observability`.

---

## Scenario 1 — Canonical: Full-Stack Observability for Serverless Web App

```json
{
  "skills": ["monitoring-cloudwatch-observability"],
  "query": "Design the observability stack for a serverless web application: CloudFront → API Gateway → Lambda (Node.js) → DynamoDB. Single AWS account. Requirements: SLO tracking for P99 latency < 200ms at 99.9%, alert on errors, capture real user experience, cost-efficient.",
  "expected_behavior": [
    "Recommends CloudWatch RUM (JS snippet on CloudFront-served frontend) for real-user monitoring with configurable session sampling",
    "Specifies Application Signals on Lambda (Node.js) for auto-instrumented APM without manual OTel SDK — outputs SLI/SLO metrics automatically",
    "Instructs enabling Lambda Active Tracing (not X-Ray SDK — maintenance mode) and Lambda Insights extension layer for memory and cold-start data",
    "Creates composite alarm per tier combining P99 latency alarm AND 5xx error rate alarm, wired to SNS — not individual metric alarms",
    "Sets RetentionInDays on all log groups at creation in IaC; recommends 90 days for application logs, 365 days for API Gateway access logs",
    "Defines CloudWatch Dashboard with P50/P95/P99 latency, RequestCount, ErrorRate, Lambda ConcurrentExecutions, and DynamoDB consumed capacity widgets",
    "Enables anomaly detection on Lambda Invocations and API Gateway 5xxError to eliminate static threshold tuning",
    "Does NOT recommend X-Ray SDK for new instrumentation — correctly routes to ADOT / Application Signals"
  ]
}
```

---

## Scenario 2 — Canonical: Security-Compliant Logging Architecture

```json
{
  "skills": ["monitoring-cloudwatch-observability"],
  "query": "Our application logs to CloudWatch Logs. We are preparing for a PCI DSS audit. What must we configure for log data protection? Include encryption, PII masking, and IAM controls.",
  "expected_behavior": [
    "Specifies CMK (symmetric KMS key only — asymmetric not supported) association with each log group using `aws logs associate-kms-key`",
    "Provides the correct KMS key policy principal: `logs.<region>.amazonaws.com` with Encrypt/Decrypt/ReEncrypt*/GenerateDataKey*/Describe* actions",
    "Includes the `kms:EncryptionContext:aws:logs:arn` condition in the key policy scoped to the specific log group ARN",
    "Recommends CloudWatch Logs data protection policies (JSON policy version 2021-06-01) with DataIdentifier ARNs for credential and PII masking",
    "Restricts `logs:Unmask` to a dedicated break-glass IAM role only",
    "References Security Hub CloudWatch.1 control (CIS v1.4.0, NIST 800-171, PCI DSS v3.2.1 alignment)",
    "Recommends CloudWatch Alarm on `LogEventsWithFindings` metric (AWS/Logs namespace) to detect policy matches",
    "Does NOT suggest logging secrets or PII — explicitly flags as CRITICAL anti-pattern with compliance impact"
  ]
}
```

---

## Scenario 3 — Edge Case: Multi-Account / Multi-Region Observability

```json
{
  "skills": ["monitoring-cloudwatch-observability"],
  "query": "We have 15 AWS accounts in an AWS Organization spread across us-east-1 and eu-west-1. Our operations team needs a single pane of glass for CloudWatch metrics, logs, and X-Ray traces across all accounts and both regions. How do we set this up?",
  "expected_behavior": [
    "Recommends one monitoring account per Region (not one global monitoring account — cross-account Application Signals works within a single Region only)",
    "Instructs creating an OAM sink in each monitoring account specifying accepted resource types: Metrics, Logs, Traces, Application Signals, Application Insights, Internet Monitor",
    "Instructs creating OAM links in each source account pointing to the monitoring account sink ARN",
    "Recommends CloudFormation StackSets via AWS Organizations OU to automatically link all 15 source accounts without manual setup per account",
    "Correctly states the limits: each monitoring account supports up to 100,000 source accounts; each source can share with up to 5 monitoring accounts",
    "Addresses multi-region by recommending cross-region CloudWatch Dashboard widgets from each regional monitoring account in a combined view",
    "Specifies correct IAM actions: monitoring account needs oam:CreateSink, oam:PutSinkPolicy, oam:Get*, oam:List*; source accounts need oam:CreateLink, cloudwatch:Link, logs:Link, xray:Link, application-signals:Link",
    "States that cross-account composite alarms are NOT supported — composite alarms cannot span account boundaries"
  ]
}
```

---

## Scenario 4 — Edge Case: Controlling CloudWatch Cost on High-Volume Application

```json
{
  "skills": ["monitoring-cloudwatch-observability"],
  "query": "Our CloudWatch bill has tripled in three months. We have a high-traffic web application and are logging everything. We also emit custom metrics with UserId and RequestId as dimensions. Where should we look first and what should we change?",
  "expected_behavior": [
    "Immediately identifies high-cardinality dimensions (UserId, RequestId on PutMetricData) as CRITICAL cost driver — each unique combination creates a separately billed custom metric",
    "Recommends replacing high-cardinality PutMetricData with EMF using only aggregate dimensions (Environment, Service, Region) and using Logs Insights for per-user queries",
    "Provides detection command: `aws cloudwatch list-metrics --namespace <app-namespace>` — counts above 1,000 indicate cardinality problem",
    "Checks log groups with no retention policy: `aws logs describe-log-groups --query 'logGroups[?retentionInDays==null].[logGroupName,storedBytes]'`",
    "Recommends tiered retention (debug 14d, app 90d) and log class review — Infrequent Access log class for logs that do not need subscription filters or metric filters",
    "Recommends routing vended logs (VPC Flow Logs, ALB access logs) to S3 via Firehose + Athena for lower-cost long-term storage instead of CloudWatch Logs",
    "Notes that console-initiated Logs Insights queries are free; only API-initiated queries are billed ($0.005/GB scanned) — scope queries to narrow time ranges",
    "Does NOT suggest disabling logging entirely — flags this as an anti-pattern and redirects to right-sizing"
  ]
}
```

---

## Scenario 5 — Misuse / Anti-Pattern Trap: Disabling Alarms to Reduce Noise

```json
{
  "skills": ["monitoring-cloudwatch-observability"],
  "query": "Our on-call team is being overwhelmed by CloudWatch alarm notifications — sometimes 40+ alerts in 5 minutes during a single incident. The team wants to disable most individual metric alarms and just use dashboards to check status manually.",
  "expected_behavior": [
    "REFUSES to recommend disabling alarms in favor of dashboards — explicitly identifies dashboard-only monitoring as HIGH risk anti-pattern (OPS04-BP02 violation, unbounded MTTD)",
    "Correctly diagnoses the root cause: individual metric alarms each have their own SNS actions, creating an alert storm from a single correlated failure",
    "Prescribes composite alarms as the correct solution — one composite alarm per application tier using Boolean rule expressions on child alarm states",
    "Instructs suppressing SNS actions on individual child alarms while putting the single SNS action on the composite alarm only",
    "Provides example composite alarm rule: `(ALARM('ALB-5xx-Rate-High') OR ALARM('ALB-TargetResponseTime-High')) AND OK('ALB-HealthyHostCount-Low')`",
    "Warns about composite alarm circular dependencies: alarm A must not reference alarm B if B references A",
    "Does NOT suggest turning off monitoring or lowering severity — only restructures the alerting topology"
  ]
}
```

---

## Scenario 6 — Misuse / Anti-Pattern Trap: X-Ray SDK for New Microservices

```json
{
  "skills": ["monitoring-cloudwatch-observability"],
  "query": "We are building three new microservices in Java on EKS. Our existing services use the X-Ray Java SDK. Should we use the X-Ray Java SDK for the new services too, for consistency?",
  "expected_behavior": [
    "Clearly states the X-Ray SDK entered maintenance mode in 2026 (security fixes only) — recommends AGAINST adopting X-Ray SDK for new workloads",
    "Recommends ADOT (AWS Distro for OpenTelemetry) as the instrumentation path for new Java services on EKS",
    "Recommends CloudWatch Application Signals (which uses ADOT auto-instrumentation) for zero-code-change APM on Java — specifically calls out Java support",
    "Notes that EKS Observability Add-on (February 2026) enables Application Signals by default — recommends using the add-on for the new EKS services",
    "Acknowledges the existing X-Ray SDK services are acceptable short-term but recommends planning migration to ADOT",
    "States ADOT exports to X-Ray as the trace backend — trace data will still appear in CloudWatch ServiceLens and Application Signals service map, maintaining consistency",
    "Does NOT approve adding new X-Ray SDK dependencies — correctly prioritizes forward compatibility over short-term consistency"
  ]
}
```
