# Ask First Decisions — OCI APM & Management Dashboards

Architectural crossroads requiring user context before proceeding. Present the full tradeoff matrix, then ask the decision question before generating configuration.

---

## Decision 1: Widget Data Source — APM QL vs OCI Monitoring Metrics

**Ask**: "Is this dashboard for executive SLA reporting or SRE diagnostic triage?"

### Tradeoff Matrix

| Dimension | APM QL (Trace Explorer) | OCI Monitoring Metrics |
|-----------|------------------------|------------------------|
| **Granularity** | Span-level attributes, DB statements, user sessions, operation names | Aggregated time-series (avg, p95, count) |
| **Rendering speed** | Slow (query-on-demand across trace storage) | Fast (pre-aggregated metric store) |
| **Cost** | Higher — priced per GB of trace storage scanned | Lower — priced per metric data point |
| **Alerting** | Cannot directly alarm on APM QL queries | Native OCI Alarms integration |
| **Retention** | Configurable trace retention (days) | 90 days raw, longer with Monitoring |
| **Best for** | SRE triage dashboards, SQL bottleneck analysis, error root-cause | Executive SLAs, auto-scaling triggers, budget dashboards |

### Recommendation

Use **OCI Monitoring metrics** (including APM-generated dynamic metrics) for always-on, executive-facing dashboards. Use **APM QL** for dedicated diagnostic workspaces opened during active incidents.

### Example: APM QL widget (Trace Explorer → Save to Dashboard)
```sql
-- Response time breakdown by service (use in SRE diagnostic dashboard)
show spans
| group by serviceName, operationName
| select avg(duration) as 'Avg ms', percentile(duration, 99) as 'P99 ms', count(*) as 'Requests'
| order by percentile(duration, 99) desc
| limit 20
```

### Example: OCI Monitoring MQL widget (use in SLA/executive dashboard)
```
# HTTP success rate (use APM Dynamic Metric if configured)
ApmRequestCount[5m]{httpResponseStatusCode = "2xx"}.sum() /
ApmRequestCount[5m].sum() * 100
```

---

## Decision 2: Synthetic Vantage Points — Public vs Dedicated (VCN-hosted)

**Ask**: "Does the monitored endpoint require private network access (VPN, private subnet, internal load balancer)?"

### Tradeoff Matrix

| Dimension | Public Vantage Points | Dedicated Vantage Points |
|-----------|----------------------|--------------------------|
| **Target endpoints** | Internet-facing only (public IPs/DNS) | Private + internet (VCN-internal) |
| **Setup complexity** | Zero — select from OCI PoP list | Requires installing agent in your VCN subnet |
| **Customization** | OCI-managed PoP locations | Any compute shape, any VCN subnet |
| **Cost** | Included with APM domain (usage-based) | Compute instance cost for the vantage point VM |
| **Latency realism** | Simulates external user experience | Simulates internal service-to-service calls |
| **Best for** | SaaS/public APIs, CDN validation, global latency monitoring | Back-office APIs, microservice-to-microservice, database health probes |

### Dedicated Vantage Point installation (OCI Compute inside VCN)
```bash
# On a compute instance inside your private VCN subnet:
# 1. Download the Dedicated Vantage Point installer from APM Console
#    (Observability & Management → APM → Administration → Vantage Points → Add Dedicated)
# 2. Run installer with your APM domain details
bash dvp-installer.sh \
  --apm-domain-id ocid1.apmdomain.oc1..prod \
  --private-data-key "$OCI_APM_PRIVATE_KEY" \
  --upload-endpoint "$OCI_APM_UPLOAD_ENDPOINT" \
  --display-name "internal-vpc-monitor"
```

### Synthetic monitor creation (OCI CLI)
```bash
# Create an HTTP monitor on a public vantage point
rtk oci apm-synthetics monitor create \
  --apm-domain-id <apm_domain_ocid> \
  --display-name "API-Health-Check" \
  --monitor-type REST \
  --repeat-interval-in-seconds 60 \
  --vantage-points '[{"name": "OraclePublic-us-ashburn-1"}]' \
  --configuration '{"requestMethod": "GET", "reqAuthenticationScheme": "NONE"}' \
  --target "https://api.myapp.com/health"
```

---

## Decision 3: Trace Retention — Full Ingestion vs Sampling + Dynamic Metric Generation

**Ask**: "What is the estimated monthly span volume and the minimum retention SLA for individual request traces?"

### Tradeoff Matrix

| Dimension | Full Trace Ingestion | Sampling + Dynamic Metrics |
|-----------|---------------------|---------------------------|
| **Diagnostic fidelity** | Every request traceable | Only sampled % of requests traceable |
| **Cost** | Linear with request volume — can grow unexpectedly | Bounded by sampling rate + fixed metric cost |
| **SLA trend data** | Available via APM QL aggregation | Available via OCI Monitoring (metric-based) |
| **Error coverage** | 100% of errors captured | Configure 100% sampling for errors, reduce for success |
| **Rollout complexity** | None — default behavior | Requires configuring Trace Ingest Rules in APM admin |
| **Best for** | Low/medium volume (<5M spans/month), compliance trace audit | High-volume (>50M spans/month), cost-sensitive production |

### Recommended sampling rules (configure in APM Domain → Administration → Trace Ingest Rules)

| Rule | Sample Rate | Rationale |
|------|-------------|-----------|
| HTTP 5xx errors | 100% | Full visibility into failures |
| HTTP 4xx errors | 100% | Catch client-side issues |
| HTTP 2xx (normal traffic) | 10% | Cost control, statistically valid |
| Database spans (slow: >500ms) | 100% | Full capture of performance outliers |

### Enable Dynamic Metric Generation (APM Console)
```
Observability & Management → APM → Administration → [select domain]
→ Dynamic Metric Generation → Enable
```
This converts span data into OCI Monitoring metrics (`ApmRequestCount`, `ApmResponseTime`, `ApmErrorRate`) that persist beyond the trace retention window and support OCI Alarms.
