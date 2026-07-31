---
Full_Name: "Amazon CloudWatch — Observability & Monitoring Architecture"
Cloud_Provider: "AWS"
Architecture_Domain: "Observability / Monitoring (Amazon CloudWatch)"
Target_Edition: "Amazon CloudWatch (current, 2026) — aligned to AWS Well-Architected Operational Excellence pillar"
Architecture_Context: "General AWS production workloads (unspecified by requester; patterns generalized for cloud architects and tech leads)"
Official_Source_URL: "https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-07-31"
Currency_Threshold: "2027-07 — re-verify all patterns and pricing/feature claims after this date"
---

# Amazon CloudWatch — Observability Architecture Research

> Scope note: the requester passed only `aws cloud watch` with no `ARCHITECTURE_CONTEXT`. Per the
> skill's Ask-First rule, workload-specific compliance and cost prescriptions are **not** assumed;
> patterns below are generalized for AWS production workloads. If a specific context (e.g. multi-tenant
> SaaS, financial services, IoT) is required, re-run with that context to tighten the Ask-First section.

## Executive Summary

Amazon CloudWatch is AWS's native monitoring and observability service for AWS resources and the
applications running on them, in real time. It is not a single feature but a suite spanning three
telemetry signals — **metrics**, **logs**, and **traces** — plus higher-order capabilities:
alarms, dashboards, Application Signals (APM), Synthetics, RUM, Service Level Objectives (SLOs),
Container/Lambda/Database Insights, cross-account observability, and network monitoring. Within the
AWS Well-Architected Framework it is the primary tooling for the **Operational Excellence** pillar
(and contributes to Reliability and Performance Efficiency), per the Management & Governance guide.
[Source: What is CloudWatch, accessed 2026-07-31]

The most consequential recent evolution in the current (2026) edition is **native OpenTelemetry (OTLP)
support**: CloudWatch now exposes native OTLP endpoints for metrics, logs, and traces, adds a second
metrics data model (metric name + up to 150 labels, with gauge/sum/histogram/exponential-histogram
types) queried via **PromQL** in **CloudWatch Query Studio**, and supports **PromQL-based alarms**.
This sits alongside — not replacing — traditional CloudWatch metrics (namespace + up to 30 dimensions,
queried via GetMetricStatistics / Metrics Insights). Other notable current-edition capabilities:
**Application Signals** (auto-instrumented APM + SLOs), **log alarms** (alarm directly on a Logs
Insights query on a schedule), **CloudWatch Logs log classes** (Standard / Infrequent Access /
Archive Instant Access) for cost tiering, and **cross-account observability** linked via AWS
Organizations. [Source: CloudWatch metrics concepts + What is CloudWatch, accessed 2026-07-31]

The three most critical architecture guardrails for any production workload: (1) **set an explicit
log-group retention policy** — CloudWatch Logs retains data forever by default, which is an unbounded
cost and compliance liability; (2) **alarm on the signals that matter with correct missing-data
treatment and M-out-of-N evaluation** — alarms only act on sustained state changes, and misconfigured
missing-data handling produces false confidence; (3) **centralize observability** via cross-account
observability into a dedicated monitoring account rather than logging into per-workload silos.

## Cloud Architecture Glossary

```
Term: Metric
Definition: A time-ordered set of data points published to CloudWatch; the fundamental CloudWatch concept. Uniquely defined by name + namespace + zero or more dimensions. Region-scoped; cannot be deleted; auto-expires after 15 months with no new data.
Provider Docs Section: CloudWatch metrics concepts → Metrics
Architect Usage: Model each thing you monitor as a metric; choose dimensions deliberately because each unique dimension combination is billed and stored as a separate metric.
Common Confusion: Confused with OpenTelemetry metrics (different data model — labels not dimensions).
```
```
Term: Namespace
Definition: A container for CloudWatch metrics; metrics in different namespaces are isolated so unrelated apps are not aggregated together. AWS services use AWS/{service} (e.g. AWS/EC2). No default namespace — you must specify one per data point.
Provider Docs Section: CloudWatch metrics concepts → Namespaces
Architect Usage: Give custom application metrics a stable, versioned namespace (e.g. MyApp/Prod) to keep them queryable and isolated from AWS-vended metrics.
Common Confusion: Confused with dimensions; namespace is the top-level container, dimensions are name/value pairs inside it.
```
```
Term: Dimension
Definition: A name/value pair that is part of a metric's identity; up to 30 per traditional metric. Each unique combination is treated as a separate metric.
Provider Docs Section: CloudWatch metrics concepts → Dimensions
Architect Usage: Use dimensions to slice (e.g. InstanceId, Environment); note CloudWatch does NOT aggregate across dimensions for custom metrics — plan the combinations you will actually query.
Common Confusion: Confused with OpenTelemetry labels (up to 150, different semantics).
```
```
Term: Resolution (Standard vs High)
Definition: Standard resolution = 1-minute granularity (default for AWS-vended metrics). High resolution = 1-second granularity (custom metrics only), readable at 1/5/10/30s or multiples of 60s.
Provider Docs Section: CloudWatch metrics concepts → Resolution
Architect Usage: Use high resolution only for sub-minute-critical signals (e.g. latency spikes); every PutMetricData call is billed and high-res alarms (10s/30s) cost more.
Common Confusion: Assuming AWS-vended metrics can be high-resolution — they are standard by default; EC2 "detailed monitoring" is still 1-minute, not sub-minute.
```
```
Term: Statistic / Statistic set
Definition: Statistics are aggregations (Average, Minimum, Maximum, Sum, SampleCount, percentiles, trimmed mean) over a period. A statistic set is a pre-aggregated datum (Min/Max/Sum/SampleCount) you publish instead of raw points for high-frequency data.
Provider Docs Section: CloudWatch metrics concepts → Statistics / Aggregation
Architect Usage: Publish statistic sets for high-volume signals (e.g. per-request latency aggregated once per minute) to cut PutMetricData cost; but percentiles require raw points (or specific stat-set equalities).
Common Confusion: Expecting percentile statistics from statistic sets — generally unavailable unless Min=Max or SampleCount=1.
```
```
Term: Percentile (e.g. p95, p99)
Definition: Relative standing of a value in a dataset; p95 means 95% of data is below it. Supported as an alarm statistic for select services (API Gateway, ALB, EC2, ELB, Kinesis, Lambda, RDS) and for custom metrics with raw points. Not available when any value is negative.
Provider Docs Section: CloudWatch metrics concepts → Percentiles
Architect Usage: Alarm on p95/p99 latency rather than Average (hides spikes) or Maximum (single outlier skews).
Common Confusion: Assuming percentiles work on statistic-set-published metrics.
```
```
Term: Period / Evaluation period
Definition: Period = length of time for one statistic aggregation (1, 5, 10, 30, or any multiple of 60 seconds; default 60). Evaluation periods = how many consecutive periods the alarm inspects before concluding.
Provider Docs Section: CloudWatch metrics concepts → Periods
Architect Usage: Set alarm period >= the metric's resolution (e.g. >=300s for EC2 basic monitoring). Max evaluation window: 7 days for period >=1h, 1 day for shorter periods.
Common Confusion: Setting a 60s period alarm on a 5-minute basic-monitoring metric → chronic INSUFFICIENT_DATA.
```
```
Term: Alarm (metric / composite / PromQL / log)
Definition: Metric alarm watches one metric or a math expression against a threshold over N periods. Composite alarm combines other alarms via a rule expression (reduces noise). PromQL alarm evaluates an OTLP/PromQL instant query. Log alarm evaluates a scheduled Logs Insights query with M-out-of-N.
Provider Docs Section: Using CloudWatch alarms
Architect Usage: Use composite alarms to suppress noise (page only when a rollup condition holds); note composite alarms cannot perform EC2/Auto Scaling actions.
Common Confusion: Expecting an alarm to fire on transient breaches — alarms only act on sustained state changes across the evaluation window.
```
```
Term: Alarm state (OK / ALARM / INSUFFICIENT_DATA)
Definition: The three alarm states. Actions fire only on state change (exception: Auto Scaling actions re-fire each minute while in state). Missing data is treated per a configurable policy (missing / notBreaching / breaching / ignore).
Provider Docs Section: Using CloudWatch alarms + Configuring how alarms treat missing data
Architect Usage: Explicitly configure missing-data treatment; INSUFFICIENT_DATA can mean "resource idle," not "healthy."
Common Confusion: Reading INSUFFICIENT_DATA as a failure — e.g. a detached EBS volume legitimately stops sending data.
```
```
Term: Log event / Log stream / Log group
Definition: Log event = one activity record. Log stream = sequence of events from the same source. Log group = collection of streams sharing one retention policy and settings.
Provider Docs Section: CloudWatch Logs concepts
Architect Usage: Model retention and access control at the log-group level; one stream per source instance/function.
Common Confusion: Assuming logs expire by default — they never expire unless you set retention.
```
```
Term: Log class (Standard / Infrequent Access / Archive Instant Access)
Definition: Storage/ingestion tiers for CloudWatch Logs. Standard = full-feature, frequent access. Infrequent Access = lower-cost, reduced-feature tier for rarely queried logs. Archive Instant Access = long-term storage tier.
Provider Docs Section: CloudWatch Logs concepts + CloudWatch billing (TimedStorage-IA / -AIA UsageTypes)
Architect Usage: Route compliance/audit logs you rarely query to Infrequent Access; keep operational logs Standard.
Common Confusion: Assuming feature parity — IA log class has reduced capabilities.
```
```
Term: Metric filter vs Subscription filter
Definition: Metric filter extracts numeric values from log events into a CloudWatch metric (for alarms/dashboards). Subscription filter streams matching log events in real time to Lambda, Firehose, Kinesis, or S3.
Provider Docs Section: CloudWatch Logs → MonitoringLogData / Subscriptions
Architect Usage: Use metric filters to alert on error-string counts; use subscription filters to fan logs out to a data lake or SIEM.
Common Confusion: Using a metric filter when you actually need to move raw log data (that's a subscription filter).
```
```
Term: Embedded Metric Format (EMF)
Definition: A structured log format that lets you publish high-cardinality custom metrics by writing them into log events; CloudWatch extracts metrics from the embedded JSON asynchronously.
Provider Docs Section: Publish custom metrics (PutMetricData / EMF)
Architect Usage: Prefer EMF over synchronous PutMetricData in Lambda/containers to avoid API latency and get logs + metrics in one write.
Common Confusion: Confusing EMF (metrics-via-logs) with plain structured logging.
```
```
Term: Application Signals
Definition: Auto-instrumented APM that detects and monitors app KPIs (latency, error rate, request rate) without code changes, with curated dashboards and native SLO tracking.
Provider Docs Section: What is CloudWatch → APM
Architect Usage: Enable for services needing golden-signal monitoring without manual OTel wiring; pair with SLOs + error budgets.
Common Confusion: Confusing it with X-Ray (tracing) — Application Signals sits above and can use X-Ray/Transaction Search.
```
```
Term: Cross-account observability
Definition: A central monitoring account views metrics, logs, and traces from linked source accounts; enables cross-account dashboards and alarms. Linked individually or automatically via AWS Organizations.
Provider Docs Section: What is CloudWatch → Cross-account monitoring
Architect Usage: The default topology for any multi-account landing zone — one monitoring account, source accounts linked via Organizations.
Common Confusion: Cross-account composite alarms are NOT supported; some math functions (ANOMALY_DETECTION_BAND, INSIGHT_RULE, SERVICE_QUOTA) are not supported cross-account.
```
```
Term: OpenTelemetry (OTLP) metrics / PromQL / Query Studio
Definition: Native OTLP ingestion for metrics/logs/traces; OTLP metrics use metric-name + up to 150 labels and gauge/sum/histogram types, queried in PromQL via CloudWatch Query Studio; supports PromQL alarms. Retention up to 15 months.
Provider Docs Section: CloudWatch metrics concepts → OpenTelemetry metrics
Architect Usage: Standardize instrumentation on OTel to keep portability across CloudWatch and third-party backends; use PromQL for OTel-native teams.
Common Confusion: Mixing the two data models in one query — traditional metrics use Metrics Insights/GetMetricStatistics, OTLP metrics use PromQL/Query Studio.
```

## Architecture Guardrails

### ✅ Mandatory Patterns

**Set explicit log-group retention (never rely on the default)**
- Pillar Alignment: Operational Excellence + Cost Optimization
- Why: CloudWatch Logs data **never expires by default**; retention is configurable per log group from 1 day to 10 years. Unbounded retention is both a cost driver (TimedStorage-ByteHrs) and a compliance liability.
- AWS Services: Amazon CloudWatch Logs (log groups, retention policy, log classes)
- Architecture Decision: Define a retention standard per data class (e.g. operational 30–90 days Standard; audit/compliance 1–7 years Infrequent Access or Archive Instant Access). Enforce via IaC and an AWS Config / Organizations control so no log group is created with default (never-expire) retention.
- Verification: `aws logs describe-log-groups --query 'logGroups[?retentionInDays==null].logGroupName'` → expect empty. Console: Logs → each log group shows an explicit "Retention" value, not "Never expire."
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Concepts.html (accessed 2026-07-31)

**Alarm on sustained breaches with correct missing-data treatment and M-out-of-N**
- Pillar Alignment: Operational Excellence + Reliability
- Why: Alarms act only on sustained state changes across the evaluation window; missing data can be silently misread. Configuring evaluation periods (M out of N) and missing-data policy is mandatory to avoid both alert fatigue and blind spots.
- AWS Services: Amazon CloudWatch alarms (metric / composite / PromQL / log alarms), Amazon SNS for notification
- Architecture Decision: For each critical signal set period >= metric resolution, choose evaluation periods (e.g. 3 of 3), and explicitly set treat-missing-data (missing / notBreaching / breaching / ignore) based on whether "no data" means "healthy" or "broken." Roll multiple noisy alarms into a composite alarm and page only on the composite.
- Verification: `aws cloudwatch describe-alarms` → confirm each alarm has an explicit `TreatMissingData` and sensible `EvaluationPeriods`/`DatapointsToAlarm`. Console alarm shows "Treat missing data as …".
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html + cloudwatch_concepts.html → Periods (accessed 2026-07-31)

**Centralize observability into a dedicated monitoring account**
- Pillar Alignment: Operational Excellence + Security
- Why: In a multi-account org, per-workload monitoring silos prevent cross-account root-cause analysis. CloudWatch cross-account observability provides a central account to view metrics, logs, and traces from all source accounts.
- AWS Services: CloudWatch cross-account observability, AWS Organizations (automatic linking), cross-account dashboards and alarms
- Architecture Decision: Designate a monitoring account; link source accounts automatically via AWS Organizations. Build cross-account dashboards there. Note constraints: cross-account **composite** alarms are unsupported, and ANOMALY_DETECTION_BAND / INSIGHT_RULE / SERVICE_QUOTA math functions are unsupported cross-account.
- Verification: In the monitoring account, CloudWatch → Settings shows linked source accounts; metrics/logs from source accounts are visible. `aws oam list-sinks` / `aws oam list-links`.
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html → Cross-account monitoring (accessed 2026-07-31)

**Publish custom metrics via EMF, not synchronous PutMetricData, in serverless/containers**
- Pillar Alignment: Performance Efficiency + Cost Optimization
- Why: Synchronous PutMetricData adds request latency and per-call cost; Embedded Metric Format writes metrics as structured log events, letting CloudWatch extract them asynchronously and giving you correlated logs + metrics in one write.
- AWS Services: CloudWatch Logs (EMF), CloudWatch Metrics
- Architecture Decision: Instrument Lambda/ECS/EKS workloads with an EMF library (or OTel) rather than calling PutMetricData in the request path. Keep dimension cardinality bounded (each unique combination is a separate billed metric).
- Verification: Log events contain the `_aws` EMF envelope; extracted metrics appear in the target namespace. Confirm no synchronous PutMetricData in hot paths via code review.
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html (referenced from metrics concepts, accessed 2026-07-31)

**Standardize instrumentation on OpenTelemetry (OTLP) for portability**
- Pillar Alignment: Operational Excellence
- Why: CloudWatch now exposes native OTLP endpoints for metrics, logs, and traces with no proprietary agent or format conversion — the same instrumentation can target CloudWatch and third-party backends, and lets you query app + AWS infra telemetry together (PromQL in Query Studio).
- AWS Services: CloudWatch OTLP endpoints, CloudWatch Query Studio (PromQL), PromQL alarms; optionally AWS Distro for OpenTelemetry (ADOT), Amazon Managed Service for Prometheus, Amazon Managed Grafana
- Architecture Decision: Emit telemetry through an OTel SDK/collector to CloudWatch OTLP; reserve traditional PutMetricData/EMF for cases needing the traditional dimension model. Choose one query model per team (Metrics Insights vs PromQL) to avoid cross-model confusion.
- Verification: OTLP metrics visible in Query Studio via PromQL; label count <=150 per metric.
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html → OpenTelemetry support + cloudwatch_concepts.html → OpenTelemetry metrics (accessed 2026-07-31)

### ⚠️ Architectural Decisions

**Traditional CloudWatch metrics vs OpenTelemetry (OTLP) metrics**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Traditional metrics | CloudWatch Metrics (PutMetricData / EMF) | Deep AWS-service integration, Metrics Insights, anomaly detection band | Only 30 dimensions; AWS-specific model | Monitoring AWS-vended metrics and existing CloudWatch-native stacks |
  | OpenTelemetry metrics | CloudWatch OTLP endpoint + PromQL / Query Studio | Portability, up to 150 labels, histogram types, PromQL | Newer surface; different query/alarm tooling | Multi-backend strategy, OTel-standardized orgs, Prometheus-native teams |

- Cost Profile: Traditional custom metrics billed per metric (MetricMonitorUsage) + per PutMetricData request; OTLP billed by observations (OTEL:Values) and ingestion bytes (OTEL:Bytes) + PromQL samples scanned. Order-of-magnitude comparison only — validate against current CloudWatch pricing.
- Lock-in Assessment: OTLP maximizes portability (open standard, same instrumentation to other backends); traditional metrics are AWS-specific.
- Architect Instruction: "Ask which query model the operating team standardizes on (Metrics Insights vs PromQL) and whether multi-backend portability is a requirement, before choosing the metric ingestion path."
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html → OpenTelemetry metrics (accessed 2026-07-31)

**Log class selection: Standard vs Infrequent Access vs Archive Instant Access**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Standard | CloudWatch Logs Standard class | Full feature set, frequent query, Live Tail, Insights | Highest ingestion/storage cost | Operational logs queried often, real-time troubleshooting |
  | Infrequent Access | CloudWatch Logs IA class | Lower ingestion/storage cost | Reduced feature set | Compliance/audit logs rarely queried |
  | Archive Instant Access | CloudWatch Logs AIA storage tier | Lowest long-term storage cost | Archive-oriented access | Long-retention records kept for audit, seldom read |

- Cost Profile: Distinct UsageTypes — DataProcessing-Bytes (Standard ingest) vs DataProcessingIA-Bytes (IA ingest); TimedStorage-ByteHrs vs TimedStorage-IA-ByteHrs vs TimedStorage-AIA-ByteHrs (storage). Query billed separately (DataScanned-Bytes).
- Lock-in Assessment: Low — all classes are CloudWatch Logs; consider S3 export (subscription/delivery) for cheapest long-term retention if query latency is acceptable.
- Architect Instruction: "Ask how often each log group is actually queried and what the retention/compliance requirement is, then assign log class per group rather than defaulting everything to Standard."
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_billing.html (accessed 2026-07-31)

**Standard vs high-resolution metrics and alarms**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Standard (1-min) | CloudWatch Metrics/Alarms | Lower cost, sufficient for most | No sub-minute visibility | Most production signals |
  | High-resolution (1s) | High-res custom metrics + 10s/30s alarms | Sub-minute detection | Higher PutMetricData + higher-charge high-res alarms | Latency-critical spikes, rapid autoscaling triggers |

- Cost Profile: High-res alarms (10s/30s) billed at HighResAlarmMonitorUsage (higher than AlarmMonitorUsage); each high-res PutMetricData call is charged.
- Lock-in Assessment: N/A (config choice, not lock-in).
- Architect Instruction: "Ask whether sub-minute detection materially changes the response (e.g. autoscaling, SLO breach) before paying for high resolution."
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html → Resolution + Alarms (accessed 2026-07-31)

**Native CloudWatch dashboards vs Amazon Managed Grafana for visualization**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | CloudWatch Dashboards | CloudWatch | Zero infra, curated automatic dashboards, cross-account/Region share | Fewer visualization options; per-dashboard pricing | AWS-native ops, quick setup |
  | Amazon Managed Grafana | Amazon Managed Grafana | Rich viz, multi-source (CloudWatch, AMP/Prometheus, X-Ray), SSO | Additional managed service to operate | Correlating metrics+logs+traces at scale across sources |

- Cost Profile: CloudWatch dashboards billed per dashboard (DashboardsUsageHour-Basic <=50 metrics vs DashboardsUsageHour >50). Managed Grafana billed per active user/license.
- Lock-in Assessment: Grafana (open-source-based) reduces viz lock-in; CloudWatch dashboards are AWS-specific.
- Architect Instruction: "Ask whether visualization must span multiple telemetry sources/backends; if yes, prefer Amazon Managed Grafana over native dashboards."
- Source: https://docs.aws.amazon.com/wellarchitected/latest/management-and-governance-guide/aws-observability-tools.html + cloudwatch_billing.html (accessed 2026-07-31)

### 🚫 Anti-Patterns

**Leaving log groups on default (never-expire) retention**
- Risk Level: HIGH
- Why: Cost Optimization + Compliance. Default retention is infinite; storage cost (TimedStorage-ByteHrs) grows unbounded and undeleted PII/audit data becomes a compliance exposure.
- ❌ Wrong: A CloudWatch Logs log group created with no `retentionInDays` set (console shows "Never expire").
- ✅ Correct: Every log group has an explicit retention (e.g. 30 days Standard for app logs; 1–7 years Infrequent Access for audit logs), enforced via IaC + an Organizations/Config rule.
- Detection: `aws logs describe-log-groups --query 'logGroups[?retentionInDays==null]'` → must be empty. AWS Config managed rule for log-group retention.
- Impact: Cost overrun + Compliance violation.
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Concepts.html (accessed 2026-07-31)

**Alarming on Average latency instead of a percentile**
- Risk Level: MEDIUM
- Why: Reliability + Performance Efficiency. Average hides tail latency; a healthy-looking average can mask p99 breaches that violate SLOs.
- ❌ Wrong: A metric alarm on `AWS/ApplicationELB TargetResponseTime` with statistic `Average` threshold 200ms.
- ✅ Correct: A metric alarm on the same metric with statistic `p99` (or `p95`) threshold aligned to the SLO, with 3-of-3 evaluation periods.
- Detection: `aws cloudwatch describe-alarms` → flag latency alarms whose `Statistic`/`ExtendedStatistic` is Average. Review against SLO definitions.
- Impact: Undetected SLO/latency degradation (silent user-facing outage).
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html → Percentiles (accessed 2026-07-31)

**Ignoring or defaulting missing-data treatment on critical alarms**
- Risk Level: HIGH
- Why: Reliability. If "no data" from a broken/idle resource is treated as `notBreaching`, the alarm stays OK and the outage is invisible; if treated as `breaching` for a legitimately idle resource, it pages needlessly.
- ❌ Wrong: A production health alarm left on default missing-data handling with no explicit `TreatMissingData`, silently sitting in INSUFFICIENT_DATA.
- ✅ Correct: Explicitly set `TreatMissingData` per intent — `breaching` for "no heartbeat = down," `notBreaching` for legitimately idle resources (e.g. a detached EBS volume) — and document the choice.
- Detection: `aws cloudwatch describe-alarms --query 'MetricAlarms[?TreatMissingData==`missing`]'` → review each for intent.
- Impact: Service outage undetected OR alert fatigue.
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html → missing data (accessed 2026-07-31)

**Alert-per-metric with no composite rollup (alarm noise)**
- Risk Level: MEDIUM
- Why: Operational Excellence. Paging on dozens of individual metric alarms produces fatigue and drowns real incidents.
- ❌ Wrong: 20 individual metric alarms all wired to the same on-call SNS topic, each paging independently.
- ✅ Correct: Keep the 20 metric alarms for context but page only on a **composite alarm** whose rule expression fires when the meaningful combination breaches (e.g. error-rate AND latency).
- Detection: Count alarms with SNS notify actions vs composite alarms; a high ratio of direct-paging metric alarms signals missing rollups.
- Impact: Alert fatigue → missed real incidents.
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html → composite alarms (accessed 2026-07-31)

**Unbounded custom-metric dimension cardinality**
- Risk Level: MEDIUM
- Why: Cost Optimization. Each unique dimension (or OTel label) combination is a distinct billed metric; putting high-cardinality values (user IDs, request IDs) in dimensions explodes metric count and cost.
- ❌ Wrong: Publishing a custom metric with a `RequestId` or `UserId` dimension via PutMetricData.
- ✅ Correct: Keep dimensions bounded/low-cardinality (Environment, Service, InstanceId); put high-cardinality identifiers in structured logs (EMF fields / Logs Insights), not metric dimensions.
- Detection: `aws cloudwatch list-metrics --namespace <ns>` growing without bound; Cost Explorer MetricMonitorUsage spike.
- Impact: Cost overrun.
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html → Dimensions + cloudwatch_billing.html (accessed 2026-07-31)

## Cloud-Native Design Patterns

**Three-signal observability (metrics + logs + traces) with correlation**
- Category: Communication / Resilience
- Problem: Fragmented telemetry prevents fast root-cause analysis across a distributed system.
- Solution on AWS: Metrics via CloudWatch Metrics/OTLP; logs via CloudWatch Logs (log groups, Logs Insights); traces via AWS X-Ray / Application Signals Transaction Search. Correlate in CloudWatch (or Amazon Managed Grafana) and alarm on golden signals through Application Signals SLOs.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Coverage | End-to-end request visibility | Ingestion + storage across three signals |
  | MTTR | Faster root-cause via correlation | Instrumentation effort (mitigated by Application Signals auto-instrumentation) |

- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html → APM (accessed 2026-07-31)

**Log-derived metrics and log alarms**
- Category: Scalability / Communication
- Problem: Need to alert on conditions expressed in log content (error strings, patterns) without a pre-existing metric.
- Solution on AWS: Use a **metric filter** to convert a log pattern into a CloudWatch metric and alarm on it; or use a **log alarm** that runs a scheduled Logs Insights query and evaluates M-out-of-N results. Use **log anomaly detection** to surface unusual patterns automatically.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Flexibility | Alert on arbitrary log content | Logs Insights query cost (DataScanned-Bytes) for log alarms |
  | Latency | Metric filter = near-real-time; log alarm = scheduled | Metric filters need a pattern defined up front |

- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html → log alarms + What is CloudWatch → Logs (accessed 2026-07-31)

## Security Architecture

**Audit trail + centralized logging baseline**
- Security Domain: Detection
- AWS Services: AWS CloudTrail (API event history), CloudWatch Logs (centralized log integration), CloudWatch cross-account observability, optionally Amazon OpenSearch Service / Amazon Managed Grafana for analysis
- Architecture: Per Well-Architected M&G guidance, CloudTrail records control-plane API activity (Control Tower stores control-plane logs centrally); CloudWatch integrates AWS service, resource, and application logs; a central monitoring account aggregates across accounts. Add CloudWatch Logs **data protection** (DataProtection-Bytes) to detect/mask sensitive data in logs.
- Compliance Alignment: Supports Operational Excellence + Security pillar detective controls (structure only — not legal advice; SOC2/HIPAA/PCI-DSS scope is organization-specific — see Ask-First).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/management-and-governance-guide/aws-observability-tools.html (accessed 2026-07-31)

## Operational Patterns

**Observability stack (AWS-native)**
- Operational Domain: Observability
- AWS Services: CloudWatch (Metrics, Logs, Alarms, Dashboards), CloudWatch Application Signals + SLOs, CloudWatch Synthetics (canaries), CloudWatch RUM (real-user monitoring), AWS X-Ray (traces), Container/Lambda/Database Insights, Internet Monitor + Network Flow Monitor (network), Amazon Managed Grafana / Amazon Managed Service for Prometheus (scale-out viz/metrics)
- Architecture: Emit metrics/logs/traces (OTLP or native) → CloudWatch; auto-instrument golden signals with Application Signals; define SLOs with error budgets; proactively probe endpoints with Synthetics canaries; measure real-user experience with RUM; alarm on composite conditions → SNS → on-call / Systems Manager OpsItems / CloudWatch investigations.
- Cost Profile: Medium–High; primary drivers are log ingestion/storage (DataProcessing-Bytes, TimedStorage-ByteHrs) and custom/high-res metrics (MetricMonitorUsage, HighResAlarmMonitorUsage).
- Automation: Automate alarm→SNS→remediation and Auto Scaling; keep runbook decisions (scale vs investigate) as human decision points.
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html + cloudwatch_billing.html (accessed 2026-07-31)

**Proactive endpoint & network monitoring**
- Operational Domain: Observability / HA
- AWS Services: CloudWatch Synthetics (canaries), CloudWatch RUM, Internet Monitor, Network Flow Monitor, Network Synthetic Monitor (Direct Connect)
- Architecture: Canaries run scripted probes against endpoints/APIs to catch availability/perf degradation before users; Internet Monitor analyzes VPC flow logs for internet-path issues; Network Flow Monitor uses lightweight agents to surface packet loss/latency and a Network Health Indicator.
- Cost Profile: Low–Medium (per-canary run, per-monitor).
- Automation: Alarm on canary failures and NHI; route to on-call.
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html → APM + Network monitoring (accessed 2026-07-31)

## Reference Architectures

**Centralized multi-account observability (monitoring account)**
- AWS Source: CloudWatch cross-account observability + Well-Architected M&G guide
- Context: Multi-account AWS Organization / landing zone.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Ingestion | CloudWatch Metrics/Logs, X-Ray, OTLP endpoints | Collect metrics, logs, traces per source account |
  | Linking | CloudWatch cross-account observability + AWS Organizations | Auto-link source accounts to a central sink |
  | Aggregation | Monitoring account (CloudWatch) | Cross-account metrics/logs/traces, cross-account dashboards |
  | Alerting | CloudWatch alarms + Amazon SNS + Systems Manager | Cross-account alarms (note: composite cross-account unsupported) |
  | Analysis/Viz | Amazon Managed Grafana / OpenSearch / Amazon Managed Service for Prometheus | Correlate and visualize at scale |
  | Audit | AWS CloudTrail (centralized via Control Tower) | Control-plane audit trail |

- Key Decisions: Which accounts link automatically vs individually; where composite alarms live (must be intra-account); Grafana vs native dashboards.
- Scaling Path: Add source accounts via Organizations auto-linking; offload high-cardinality metrics to Amazon Managed Service for Prometheus + Grafana as volume grows.
- Cost Baseline: Medium–High; centralized-metrics ingestion billed (CentralizedBytes) plus per-account log/metric costs.
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html → Cross-account monitoring + M&G guide (accessed 2026-07-31)

## Service Equivalence Map

CloudWatch is AWS's answer to the observability service class. Cross-provider equivalents (see the
skill blueprint for the full table; equivalence ≠ feature parity):

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| Metrics/Monitoring | Amazon CloudWatch (Metrics, Alarms, Dashboards) | Cloud Monitoring | Azure Monitor (Metrics) | OCI Monitoring |
| Logging | Amazon CloudWatch Logs | Cloud Logging | Azure Monitor Logs / Log Analytics | OCI Logging / Logging Analytics |
| Tracing | AWS X-Ray | Cloud Trace | Application Insights (distributed tracing) | OCI APM (traces) |
| APM | CloudWatch Application Signals | Cloud Trace + Cloud Profiler | Application Insights | OCI Application Performance Monitoring |
| Synthetic monitoring | CloudWatch Synthetics (canaries) | Uptime Checks | Availability Tests (App Insights) | OCI APM Synthetic Monitoring |
| Real-user monitoring | CloudWatch RUM | (Firebase/GA-based) | Application Insights (browser SDK) | OCI APM RUM |
| Managed Prometheus | Amazon Managed Service for Prometheus | Google Cloud Managed Service for Prometheus | Azure Monitor managed service for Prometheus | (OCI + open-source Prometheus) |
| Managed Grafana | Amazon Managed Grafana | (self-managed / Cloud Monitoring dashboards) | Azure Managed Grafana | (self-managed) |

> ⚠️ Equivalence does NOT mean feature parity. Validate limits, pricing, and regional availability
> against current provider docs before any multi-cloud decision.

## Provider Differentiators

- **Native OTLP + PromQL + Query Studio**: CloudWatch ingests OpenTelemetry metrics/logs/traces natively (no proprietary agent) and lets you query OTel metrics with PromQL alongside AWS infra telemetry — reducing lock-in while keeping AWS-native depth.
- **Application Signals**: auto-instrumented APM with built-in SLOs/error budgets and curated dashboards, minimal setup.
- **Cross-account observability via Organizations**: first-class central-monitoring-account model with automatic linking.
- **Curated automatic dashboards + solutions catalog**: pre-built dashboards/alarms/agent configs for JVM, NVIDIA GPU, Kafka, Tomcat, NGINX.
- Caveat: cross-account composite alarms and some math functions (ANOMALY_DETECTION_BAND, INSIGHT_RULE, SERVICE_QUOTA) are unsupported cross-account.

## Scenario Coverage

**Standard Case**: Single- or multi-account AWS workload needing golden-signal monitoring.
- Approach: Enable Application Signals for APM + SLOs; set explicit log retention + log classes; alarm on p95/p99 with composite rollups → SNS; centralize into a monitoring account.
- Key Decisions: metric model (traditional vs OTLP), log class per group, dashboard tool (native vs Grafana).

**Edge Case**: Sub-minute latency-critical or high-cardinality telemetry at scale.
- Approach: Use high-resolution metrics + 10s/30s alarms only where response changes; offload high-cardinality/Prometheus workloads to Amazon Managed Service for Prometheus + Amazon Managed Grafana; keep identifiers in logs (EMF), not dimensions.

**Anti-Pattern Case**: Request to "just turn on all CloudWatch features" or log everything forever with no retention/cost plan.
- Clarification: Ask for the workload's SLOs, query frequency per log group, retention/compliance requirement, and multi-account topology before enabling features — otherwise cost and alert-noise anti-patterns are guaranteed.

## Source Bibliography

### Primary Sources (official AWS documentation — all accessed 2026-07-31)
- What is Amazon CloudWatch? — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html
- CloudWatch metrics concepts (namespaces, dimensions, resolution, statistics, percentiles, periods, aggregation, OTel metrics, alarms) — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html
- Using Amazon CloudWatch alarms (metric/composite/PromQL/log alarms, states, missing data) — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html
- CloudWatch Logs concepts (log events/streams/groups, retention, log classes, metric/subscription filters) — https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatch_Logs_Concepts.html
- Analyzing, optimizing, and reducing CloudWatch costs (UsageTypes, log classes, alarm/metric/dashboard cost) — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_billing.html
- Well-Architected Management & Governance guide — AWS observability tools — https://docs.aws.amazon.com/wellarchitected/latest/management-and-governance-guide/aws-observability-tools.html

### Validation / Secondary Sources
- AWS Observability Best Practices — CloudWatch recipes (community-curated, AWS-maintained) — https://aws-observability.github.io/observability-best-practices/recipes/cw/ (accessed 2026-07-31)
- AWS Prescriptive Guidance — EKS observability best practices — https://docs.aws.amazon.com/prescriptive-guidance/latest/amazon-eks-observability-best-practices/introduction.html (accessed 2026-07-31)

### Referenced but not deep-read (for downstream skill authoring)
- Publish custom metrics (PutMetricData / EMF) — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html
- Configuring how CloudWatch alarms treat missing data — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/alarms-and-missing-data.html
- Send metrics using OpenTelemetry — https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OpenTelemetry-Sections.html

## Agent Operation Notes (confidence for downstream skill authoring)

- High confidence (autonomous): concepts (metrics/namespaces/dimensions/resolution/statistics/percentiles/periods), retention behavior and ranges, alarm types/states/missing-data, log classes, cross-account model, OTLP/PromQL support — all sourced from official docs dated within currency window.
- Medium confidence (verify before prescribing): exact pricing and cost-optimization magnitudes (pricing not read directly — only UsageType structure); Application Signals / Query Studio feature depth (surfaces described at overview level).
- Low confidence (must ask user): compliance-specific controls (SOC2/HIPAA/PCI-DSS/GDPR), organization billing/reserved-capacity decisions, and any workload-specific ARCHITECTURE_CONTEXT — none were provided.
- Unverified / gaps: no page was read for Synthetics/RUM/Container Insights internals beyond the overview; treat their detailed patterns as unverified until their dedicated docs are consulted.
```
