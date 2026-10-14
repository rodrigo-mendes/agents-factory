---
name: monitoring-oci-apm-dashboards
description: "Configures OCI Management Dashboards with Application Performance Monitoring (APM) for unified observability across Java microservices, browser RUM, and synthetic monitors. Use when creating APM domains, instrumenting Java agents, securing dashboard IAM policies, building APM QL widgets, or configuring trace sampling and OpenTelemetry ingestion on OCI."
---

## Function

Specialist in OCI unified observability — connecting APM domains, Java agent instrumentation, Management Dashboard design, and IAM security for production microservices on Oracle Cloud Infrastructure.

---

## Version Context

**Technology**: OCI Management Dashboards & Application Performance Monitoring (APM)
**Target version**: OCI Best Practices Framework 2024 (APM GA)
**Release date**: 2024
**Support status**: Active

**Important changes in this version**:
- Native OpenTelemetry (OTel/OTLP) ingestion endpoint — no vendor shim required
- Unified Dashboard Filters — global variables propagate to APM and Monitoring widgets simultaneously
- Dedicated Vantage Points — private VCN-hosted synthetic monitors for internal workloads
- JSON Dashboard Export/Import — dashboard-as-code portability across compartments

**Deprecated**: None active in 2024 edition.

⚠️ **Version Lock**: This skill targets OCI BPF 2024 + APM GA. Reject pre-GA APM agent paths or legacy dashboard API shapes.

---

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — APM domain setup, key vaulting, IAM, agent config, filters
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — widget data source, vantage point type, trace sampling strategy
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — hardcoded OCIDs, key leakage, unparameterized SQL, over-permissive IAM
- **[Verification Loop](#verification-loop)** — OCI CLI audit commands
- **[Quick Reference](#quick-reference)** — IAM policy templates, key APM QL queries
- **[External Resources](#external-resources)** — Official OCI documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For full IAM policies, Agent.properties config, and APM QL examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns** (Standard tier — 5 patterns):

- **Isolated APM Domain per environment** — Provision separate APM Domains for dev/staging/prod within their respective compartments. Shared domains allow dev ingestion spikes to exhaust production capacity and pollute alert thresholds.
- **Private Data Keys in OCI Vault via Instance Principal** — Never hardcode Private Data Keys in `Agent.properties` or environment variables. Store them in OCI Vault; retrieve at runtime using Instance Principal authentication from an IAM Dynamic Group.
- **IAM RBAC: `use` vs `manage` for dashboards** — Grant `use management-dashboards` to consumers (read + filter) and `manage management-dashboards` to SRE groups only. Individual IAM users must not receive `manage` in production compartments.
- **Global dashboard filters on every widget** — All APM QL and OCI Monitoring widgets must inherit global `Compartment`, `ApmDomain`, and `TimeRange` filter variables. Hardcoded OCIDs break dashboard portability and cause silent staleness.
- **APM Java Agent injected via `-javaagent` JVM flag** — Configure the agent through `Agent.properties` (or environment variables `OCI_APM_PRIVATE_KEY` / `OCI_APM_UPLOAD_ENDPOINT`). Do not instrument JDBC or HTTP manually when the agent auto-instruments.

### ⚠️ Ask First

For tradeoff matrices with example queries and cost profiles, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Decision points** (Standard tier — 3 decisions):

- **Widget data source: APM QL vs OCI Monitoring metrics** — APM QL (Trace Explorer) offers span-level granularity but has higher execution cost and slower rendering. OCI Monitoring metrics render fast and are ideal for SLA dashboards. Ask: "Is this dashboard for executive SLA reporting or SRE diagnostic triage?"
- **Synthetic vantage points: Public vs Dedicated (VCN-hosted)** — Public Vantage Points test internet-facing endpoints from OCI PoPs. Dedicated Vantage Points install inside your VCN to test private APIs unreachable from the internet. Ask: "Does the target endpoint require VPN or private subnet access?"
- **Trace retention: Full ingestion vs sampling + Dynamic Metric Generation** — Full ingestion preserves all spans for deep diagnostics but costs scale linearly with request volume. Sampling with Dynamic Metric Generation converts high-cardinality traces into compact OCI Monitoring metrics. Ask: "What is the monthly trace volume estimate and the retention SLA?"

### 🚫 Never Do

For wrong/correct code side-by-side examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Prohibited patterns** (Standard tier — 4 anti-patterns):

- **Hardcode APM Domain OCIDs or absolute time windows in widget queries** — Widgets become non-portable, break on domain recreation, and fetch unbounded historical data. RISK: HIGH. Use `${apm_domain_id}` and `${time_range}` dashboard variables instead.
- **Expose Private APM Data Keys in client-side browser code** — Private Keys have server write permissions; browser exposure allows telemetry injection and metrics poisoning by third parties. RISK: CRITICAL. Use Public Data Keys for RUM Browser Agent only.
- **Execute unparameterized SQL in APM-traced JDBC paths** — The APM Java Agent captures raw `dbStatement` span attributes. Unparameterized SQL containing PII (names, emails, SSNs) is stored in plaintext in APM trace storage. RISK: CRITICAL. Enforce `PreparedStatement` + Agent obfuscation filters.
- **Grant `manage management-dashboards` to individual IAM users in production** — Individual grants bypass group rotation hygiene, survive team changes, and cannot be audited via group membership reports. RISK: HIGH. Grant only to IAM Groups, never to individual users.

---

## Integration Patterns

For complete integration code with imports and configs, see [Always Do Patterns](./blueprints/always-do-patterns.md#integration-patterns).

**OCI APM ↔ OCI Management Dashboard**
- APM QL queries saved from Trace Explorer are embedded as dashboard widgets; link via global `ApmDomain` filter.

**OCI APM ↔ OCI Vault (Private Key Security)**
- Dynamic Group grants `use secret-family` on specific secret; Instance Principal retrieves key at agent startup without static credentials.

**OCI APM ↔ OCI Monitoring (Alerting)**
- Dynamic Metric Generation rules inside APM Domain emit trace-derived metrics into OCI Monitoring namespace; OCI Alarms fire on metric thresholds and route to OCI Notifications.

**OCI APM ↔ OpenTelemetry (OTLP)**
- Any OTel SDK points to the APM domain OTLP endpoint. No OCI-specific library required — only `OTEL_EXPORTER_OTLP_ENDPOINT` and `OTEL_EXPORTER_OTLP_HEADERS` (with the Private Data Key).

**Common problems**:
- **Widgets show "No data"** → Verify APM Domain filter is inherited and the domain has active trace ingestion (check Agent logs for HTTP 200 on upload endpoint).
- **Agent.properties key rejected** → Confirm key type: server-side requires **Private** key, not Public key.
- **OTLP spans not appearing** → Check `OTEL_EXPORTER_OTLP_ENDPOINT` ends with `/20200101/observations/public-span` (APM OTLP path), not the root domain URL.

---

## Verification Loop

Execute after each APM or dashboard configuration change:

### 1. Verify APM Domain ingestion is active
```bash
rtk oci apm-control-plane apm-domain list \
  --compartment-id <compartment_ocid> \
  --query "data[*].{Name:\"name\", Status:\"lifecycle-state\", Endpoint:\"data-upload-endpoint\"}"
# Expected: lifecycle-state = ACTIVE | Exit code: 0
```

### 2. Audit IAM policies for dashboard RBAC
```bash
rtk oci iam policy list \
  --compartment-id <root_compartment_ocid> \
  --query "data[*].statements" | grep "management-dashboards"
# Expected: Only group references (no individual user grants) | Exit code: 0
```

### 3. Confirm Dynamic Group covers compute nodes
```bash
rtk oci iam dynamic-group list \
  --query "data[*].{Name:name, Rule:\"matching-rule\"}"
# Expected: APMAgentsGroup rule matches production compartment OCID | Exit code: 0
```

### 4. Detect hardcoded OCIDs in dashboard widgets
```bash
rtk oci management-dashboard dashboard get \
  --dashboard-id <dashboard_ocid> \
  --query "data.widgets[*].queries" | grep "ocid1\."
# Expected: No output (all OCIDs replaced by filter variables) | Exit code: 0
```

**Troubleshooting**:
- `NotAuthorizedOrNotFound` on APM API → Instance Principal Dynamic Group rule does not match the compute instance's compartment.
- `400 Bad Request` on agent upload → Mismatched key type (Public key used for server-side agent).
- Dashboard filter not propagating → Widget parameter not mapped to global filter variable; open widget editor and enable "Inherit Global APM Domain Filter".

---

## Quick Reference

**Critical APM QL queries** (paste into Trace Explorer, save to dashboard):
```sql
-- Average latency per service
show spans | group by serviceName | select avg(duration) as 'Avg ms' | order by avg(duration) desc

-- Error rate per service
show traces | where error = true | group by serviceName | select count(*) as 'Failures'

-- Slowest DB statements
show spans | where dbStatement is not null | group by dbStatement | select avg(duration) | order by avg(duration) desc | limit 5
```

**Minimal IAM policy set**:
```
allow group ObservabilityConsumers to use management-dashboards in compartment <ProdCompartment>
allow group ObservabilityEngineers to manage management-dashboards in compartment <ProdCompartment>
allow dynamic-group APMAgentsGroup to use secret-family in compartment <ProdCompartment> where target.secret.name = 'APM_Private_Key'
```

**Critical limits**:

| Resource | Limit | Scope |
|----------|-------|-------|
| APM Domain Data Keys | Max 2 per domain (Public + Private) | Per domain |
| Dashboard global filters | Unlimited | Per dashboard |
| APM QL `limit` clause | Max 1000 rows | Per query execution |
| Dedicated Vantage Points | Subject to OCI service limits | Per tenancy |

---

## External Resources

### Official Documentation
- [OCI APM Overview](https://docs.oracle.com/en-us/iaas/Content/APM/home.htm)
- [APM Domains & Data Keys](https://docs.oracle.com/en-us/iaas/Content/APM/Concepts/apmdomains.htm)
- [APM Java Agent Installation](https://docs.oracle.com/en-us/iaas/Content/APM/Tasks/installjavaagent.htm)
- [APM Query Language (APM QL)](https://docs.oracle.com/en-us/iaas/Content/APM/Tasks/apm_ql.htm)
- [Trace Explorer](https://docs.oracle.com/en-us/iaas/Content/APM/Tasks/traceexplorer.htm)
- [Synthetic Monitoring & Vantage Points](https://docs.oracle.com/en-us/iaas/Content/APM/Tasks/syntheticmonitoring.htm)
- [OCI Browser Agent (RUM)](https://docs.oracle.com/en-us/iaas/Content/APM/Tasks/browseragent.htm)
- [OpenTelemetry with OCI APM](https://docs.oracle.com/en-us/iaas/Content/APM/Tasks/opentelemetry.htm)

### Management Dashboards
- [OCI Management Dashboards Overview](https://docs.oracle.com/en-us/iaas/Content/observability/dashboards.htm)
- [Creating & Editing Dashboards](https://docs.oracle.com/en-us/iaas/Content/observability/dashboards_create.htm)
- [Dashboard Filters](https://docs.oracle.com/en-us/iaas/Content/observability/dashboards_filters.htm)
- [Dashboard Export/Import (JSON)](https://docs.oracle.com/en-us/iaas/Content/observability/dashboards_export_import.htm)
- [Dashboard IAM Policies](https://docs.oracle.com/en-us/iaas/Content/observability/dashboards_iam.htm)

### Research Basis
- [OCI APM & Management Dashboards Research 2024](../../../StoryBeat/OCI/research_cloud_OCI_Observability-Architecture_Management-Dashboards-APM-2024.md)
