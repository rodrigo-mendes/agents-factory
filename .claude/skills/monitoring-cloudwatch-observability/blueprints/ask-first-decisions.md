# Ask First Decisions — monitoring-cloudwatch-observability

Full decision matrices (4). Summary in [../SKILL.md](../SKILL.md).
Source: research_cloud_AWS_CloudWatch_Observability_2026.md (research date 2026-08-30; official AWS docs accessed 2026-08-30).

---

## Decision 1 — Observability instrumentation strategy

**Ask**: "Does this application need to send telemetry to more than one monitoring backend now or within 18 months, or is there an existing non-AWS APM contract?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| CloudWatch Native (CloudWatch Agent, PutMetricData, Logs; X-Ray SDK only for existing apps) | Simplicity, AWS-managed, no collector | Portability; tied to CloudWatch/X-Ray APIs | AWS-only team, minimal operational overhead |
| ADOT (Collector, SDK layers, CloudWatch OTLP endpoint) | Vendor neutrality; instrument once, many backends | Collector infrastructure to run; more complex pipeline | Multi-backend needs or future non-AWS APM |
| Third-party APM via Metric Streams + Firehose | Rich pre-built dashboards, AI-assisted correlation | APM subscription on top of AWS; data leaves the account | Existing APM contract |

**Cost**: Native lowest; ADOT low plus collector compute; third-party highest.
**Lock-in**: Native high; ADOT low (OTel standard); third-party moderate.
**Architect instruction**: yes to multi-backend or existing contract means ADOT or Metric Streams; otherwise CloudWatch Native with ADOT as the instrumentation path.

Sources: [ADOT](https://docs.aws.amazon.com/xray/latest/devguide/xray-services-adot.html); [Metric Streams](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Metric-Streams.html) (2026-08-30)

---

## Decision 2 — Custom metrics ingestion strategy

**Ask**: "Is the compute ephemeral/serverless, and must metric values correlate with the log that produced them?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| PutMetricData API | Explicit publish, no log dependency | Synchronous hot-path call; needs `cloudwatch:PutMetricData` | Batch reporting from non-ephemeral services |
| Embedded Metric Format (EMF) | Async emission; log + metric correlation; only `logs:PutLogEvents` needed | Pays log and metric charges; cardinality explosion risk; at-least-once (duplicates possible) | Lambda/container workloads |
| Metric Filters | No code change; works on existing logs | Pattern-based only; not retroactive | Apps that cannot be modified |
| Metric Streams | Near-real-time push to S3/Firehose | Outbound only; not an ingestion path | Export to third-party APM or data lake |

**Cost**: PutMetricData per call + per metric/month; EMF log ingestion + per metric/month; Metric Filters log ingestion only; Metric Streams per metric update.
**Lock-in**: PutMetricData/EMF medium; Metric Filters and Streams low.
**Architect instruction**: ephemeral compute plus correlation means EMF; unmodifiable logs mean Metric Filters; export means Metric Streams.

Sources: [EMF](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html); [Metric filters](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html) (2026-08-30)

---

## Decision 3 — Log analytics backend strategy

**Ask**: "Is the primary use case (a) incident response with alarm correlation, (b) compliance archival with ad-hoc SQL, or (c) full-text search and rich dashboards?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| CloudWatch Logs + Logs Insights | Operational queries, live tail, alarm integration, EMF correlation | Cost at scale; query concurrency limits | (a) Troubleshooting, short retention, high query rate |
| CloudWatch Logs + S3 export + Athena | Cheap long-term storage, SQL | Async export; no live alarm integration | (b) Archival, batch analytics |
| CloudWatch Logs + Firehose + OpenSearch | Full-text search, OpenSearch Dashboards, near-real-time | Extra domain cost and complexity | (c) Full-text search |

**Cost**: Logs Insights $0.005/GB scanned for API-initiated queries (console queries free); S3 export cheapest at scale; OpenSearch highest TCO.
**Lock-in**: all use CloudWatch Logs for ingestion; analytics backends are replaceable.

Source: [Analyzing log data with Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html) (2026-08-30)

---

## Decision 4 — Distributed tracing strategy

**Ask**: "Do you need SLO management and automatic topology discovery, or must traces go to a non-AWS backend or an unsupported language?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| X-Ray SDK | Direct AWS integration, service map | Maintenance mode; OTel migration needs code changes | Existing apps already on the SDK (plan migration) |
| Application Signals | Auto-discovery, SLI/SLO, application map; zero-code for Java, Python, Node.js, .NET | Service discovery up to 10 min; SLI evaluation up to 15 min | Production SLO management |
| ADOT with manual OTel SDK | Vendor neutral; Lambda managed layers | Collector to operate | Multi-tool/multi-cloud or unsupported language |

**Cost**: X-Ray SDK = X-Ray trace pricing; Application Signals = $1.50 per million signals + X-Ray; ADOT = collector compute + X-Ray.
**Lock-in**: X-Ray SDK high; Application Signals medium (ADOT underneath); ADOT low.

Source: [Application Signals](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Monitoring-Sections.html) (2026-08-30)
