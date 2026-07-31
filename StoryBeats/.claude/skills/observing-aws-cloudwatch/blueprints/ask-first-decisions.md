# Ask First Decisions — observing-aws-cloudwatch

> Full decision matrices for the 4 architectural crossroads summarized in SKILL.md.
> Source: research_cloud_AWS_Observability-CloudWatch_2026.md (accessed 2026-07-31)

---

## 1. Traditional CloudWatch Metrics vs OpenTelemetry (OTLP) Metrics

**Question to ask**: "Does the team standardize on Metrics Insights or PromQL? Is multi-backend
portability a requirement?"

| Dimension | Traditional Metrics (PutMetricData / EMF) | OTLP Metrics (CloudWatch OTLP endpoint) |
|---|---|---|
| **Data model** | Namespace + up to 30 dimensions | Metric name + up to 150 labels |
| **Metric types** | Gauge (PutMetricData) | Gauge, Sum, Histogram, Exp-Histogram |
| **Query language** | Metrics Insights / GetMetricStatistics | PromQL in CloudWatch Query Studio |
| **Alarm support** | Metric alarms, composite alarms | PromQL alarms |
| **AWS service integration** | Deep (EC2, RDS, Lambda vended metrics use this model) | Separate surface; vended metrics not in OTLP model |
| **Portability** | AWS-specific | Open standard — same instrumentation targets any OTLP backend |
| **Anomaly detection** | ANOMALY_DETECTION_BAND supported | Not supported in PromQL alarms |
| **Best when** | Monitoring AWS-vended metrics + existing CloudWatch stacks | OTel-standardized orgs, Prometheus-native teams, multi-backend strategy |

**Cost profile**:
- Traditional: `MetricMonitorUsage` (per custom metric) + `PutMetricData` API calls
- OTLP: `OTEL:Values` (observations) + `OTEL:Bytes` (ingestion bytes) + PromQL samples scanned

Validate exact pricing at https://aws.amazon.com/cloudwatch/pricing/ before committing.

**Lock-in**: OTLP maximizes portability; traditional metrics are AWS-specific.

**Instruction**: Do not choose the metric ingestion path until the operating team confirms their
query model standard (Metrics Insights vs PromQL) and whether multi-backend portability is a
hard requirement.

---

## 2. Log Class per Log Group: Standard vs Infrequent Access vs Archive Instant Access

**Question to ask**: "How often is each log group actually queried? What is the retention/compliance
requirement?"

| Dimension | Standard | Infrequent Access (IA) | Archive Instant Access (AIA) |
|---|---|---|---|
| **Use case** | Operational logs, real-time troubleshooting | Compliance/audit rarely queried | Long-retention records kept for audit |
| **Feature set** | Full (Live Tail, Insights, metric filters, anomaly detection) | Reduced (no Live Tail, no metric filters) | Archive-oriented access |
| **Ingestion billing** | `DataProcessing-Bytes` | `DataProcessingIA-Bytes` (lower) | AIA ingestion |
| **Storage billing** | `TimedStorage-ByteHrs` | `TimedStorage-IA-ByteHrs` (lower) | `TimedStorage-AIA-ByteHrs` (lowest) |
| **Query billing** | `DataScanned-Bytes` | `DataScanned-Bytes` | `DataScanned-Bytes` |
| **Best when** | Logs queried often; real-time | Logs queried rarely | Minimal query, maximum retention |

**Decision heuristic**:
- Query frequency ≥ weekly → Standard
- Query frequency < weekly, retention ≤ 7 years → Infrequent Access
- Query frequency near-zero, retention > 3 years → Archive Instant Access or export to S3 via subscription filter

**Lock-in assessment**: Low — all classes are CloudWatch Logs. Consider S3 export (subscription
delivery) for cheapest long-term retention when Logs Insights query latency is acceptable.

**Instruction**: Assign log class per log group, not per account. Do not default everything to
Standard; request query frequency and compliance requirements from the workload team first.

---

## 3. Standard (1-min) vs High-Resolution (1s) Metrics and Alarms

**Question to ask**: "Does sub-minute detection materially change the response (autoscaling trigger,
SLO breach, fraud detection)? What is the acceptable alarm cost increase?"

| Dimension | Standard Resolution (1-min) | High Resolution (1s) |
|---|---|---|
| **Granularity** | 1-minute aggregation | 1-second; alarm periods: 10s, 30s, or 60s multiples |
| **AWS-vended metrics** | Available (EC2 detailed monitoring is still 1-min) | Custom metrics only |
| **Alarm billing** | `AlarmMonitorUsage` | `HighResAlarmMonitorUsage` (higher charge) |
| **PutMetricData cost** | Standard rate | Standard rate (same API, higher volume) |
| **Best when** | Most production signals (sufficient for human-response SLOs) | Latency-critical spikes, rapid autoscaling, sub-minute SLO detection |

**Decision rule**: If the response action (scale out, alert on-call, block fraud) happens in < 1
minute, high-resolution adds value. If the response is human-triaged and takes 5+ minutes, standard
resolution is sufficient and cheaper.

**Note**: EC2 "Detailed Monitoring" enables 1-minute (not sub-minute) metrics. True high-resolution
(1s) applies only to custom metrics published via `PutMetricData` with `StorageResolution: 1`.

---

## 4. Native CloudWatch Dashboards vs Amazon Managed Grafana

**Question to ask**: "Does visualization need to span multiple telemetry sources or backends?
How large is the ops team relative to the dashboard count?"

| Dimension | CloudWatch Dashboards | Amazon Managed Grafana |
|---|---|---|
| **Setup complexity** | Zero infra; automatic dashboards for many services | Managed service to operate (workspace, IAM auth, SSO) |
| **Data sources** | CloudWatch only (metrics, logs, alarms, traces) | Multi-source: CloudWatch, AMP/Prometheus, X-Ray, Athena, OpenSearch, etc. |
| **Visualization richness** | Good; limited panel types vs Grafana | Rich (80+ Grafana panel types, plugins) |
| **Cross-account/Region** | Supported (with cross-account observability) | Supported via CloudWatch data source + cross-account |
| **Billing** | Per dashboard (`DashboardsUsageHour-Basic` ≤50 metrics; `DashboardsUsageHour` >50) | Per active user / license |
| **Lock-in** | AWS-specific | Open-source-based, lower viz lock-in |
| **Best when** | AWS-native ops team, quick setup, single CloudWatch data source | Correlating metrics + logs + traces across sources; Prometheus-native teams |

**Instruction**: Ask whether visualization must span multiple telemetry sources/backends. If yes,
prefer Amazon Managed Grafana. If the team only needs CloudWatch data and wants zero additional
managed service overhead, native dashboards suffice.
