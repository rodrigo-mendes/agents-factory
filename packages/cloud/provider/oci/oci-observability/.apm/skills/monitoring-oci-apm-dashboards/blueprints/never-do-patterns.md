# Never Do Patterns — OCI APM & Management Dashboards

Each anti-pattern shows the ❌ wrong approach and the ✅ correct alternative side-by-side, with detection and blast radius.

---

## Anti-Pattern 1: Hardcode APM Domain OCIDs or Absolute Time Windows in Widget Queries

**Risk Level**: HIGH | **Pillar**: Reliability, Operational Efficiency

### ❌ Wrong — static OCID and time window in APM QL widget
```sql
-- Hardcoded OCID and fixed date
show spans
| where apmDomainId = 'ocid1.apmdomain.oc1.iad.aaaa...xyz'
  and startTime > '2026-07-01T00:00:00Z'
| group by serviceName | select avg(duration)
```

### ✅ Correct — dashboard global variable references
```sql
-- References dashboard filter variables
show spans
| where apmDomainId = '${apm_domain_id}'
  and startTime within ${time_range}
| group by serviceName | select avg(duration)
```

Also confirm each widget has global filter inheritance enabled (widget editor → **Inherit Global APM Domain Filter** ✓).

**Detection**:
```bash
rtk oci management-dashboard dashboard get \
  --dashboard-id <dashboard_ocid> \
  --query "data.widgets[*].queries" | grep "ocid1\."
# Any match means hardcoded OCIDs are present — remediate
```

**Blast radius**: Dashboard breaks silently when APM Domain is recreated, migrated, or when the dashboard is imported into a new compartment. Time-hardcoded queries fetch unbounded historical data, inflating query execution costs.

---

## Anti-Pattern 2: Private APM Data Key in Client-Side Browser Code

**Risk Level**: CRITICAL | **Pillar**: Security

### ❌ Wrong — Private key embedded in browser JavaScript
```html
<script>
  window.apmrum = {
    "serviceName": "my-app",
    "ociDataUploadEndpoint": "https://xxx.apm-agt.oci.oraclecloud.com",
    "dataKey": "PRIVATE_aBcDeFgHiJkLmNoPqRsTuV"  // ← CRITICAL: Private key exposed
  };
</script>
<script async src=".../apmrum.min.js"></script>
```

### ✅ Correct — Public key for browser RUM only
```html
<script>
  window.apmrum = {
    "serviceName": "my-app",
    "ociDataUploadEndpoint": "https://xxx.apm-agt.oci.oraclecloud.com",
    "dataKey": "PUBLIC_aBcDeFgHiJkLmNoPqRsTuV"   // ✓ Public key: write-only, limited permissions
  };
</script>
<script async src=".../apmrum.min.js"></script>
```

Use Private keys exclusively in server-side agents and OTel exporters (retrieving via OCI Vault + Instance Principal — see [Always Do Pattern 2](../blueprints/always-do-patterns.md#pattern-2-private-data-keys-in-oci-vault-via-instance-principal)).

**Detection**: Search frontend repository for APM key patterns:
```bash
grep -r "PRIVATE_" ./frontend/src --include="*.js" --include="*.ts" --include="*.html"
# Any match in client-side paths is CRITICAL — rotate key immediately
```

**Blast radius**: Leaked Private Key allows any external party to inject arbitrary trace spans into your APM domain — corrupting performance metrics, triggering false alerts, and causing alert fatigue that masks real incidents.

---

## Anti-Pattern 3: Unparameterized SQL in APM-Traced JDBC Paths

**Risk Level**: CRITICAL | **Pillar**: Security, Compliance

The APM Java Agent captures the `dbStatement` attribute from JDBC calls. String-concatenated SQL values containing PII are indexed in plaintext in APM trace storage.

### ❌ Wrong — string concatenation in JDBC (PII captured in trace)
```java
// APM agent captures this full SQL string including the literal email value
String sql = "SELECT * FROM users WHERE email = '" + userEmail + "'";
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery(sql);
// Stored in APM trace as: dbStatement = "SELECT * FROM users WHERE email = 'alice@example.com'"
```

### ✅ Correct — parameterized query (parameter value not captured)
```java
// Agent captures only the SQL template, never the parameter value
String sql = "SELECT * FROM users WHERE email = ?";
PreparedStatement pstmt = conn.prepareStatement(sql);
pstmt.setString(1, userEmail);
ResultSet rs = pstmt.executeQuery();
// Stored in APM trace as: dbStatement = "SELECT * FROM users WHERE email = ?"
```

For additional defense-in-depth, configure the APM Java Agent to obfuscate matching field patterns:

```properties
# /opt/oracle/apmagent/config/Agent.properties
# Redact fields matching sensitive patterns before trace storage
com.oracle.apm.agent.sql.obfuscation.enabled=true
com.oracle.apm.agent.sql.obfuscation.patterns=password,creditcard,ssn,email,token
```

**Detection** — search for unparameterized values in existing traces:
```sql
-- Run in APM Trace Explorer; any results require immediate code remediation
show spans
| where dbStatement matches '(?i).*(email|password|ssn|token)\s*=\s*''[^?]'
| select traceId, serviceName, dbStatement
| limit 50
```

**Blast radius**: PII stored in APM trace storage constitutes a GDPR, PCI-DSS, and SOC2 violation. Spans can be viewed by anyone with `use apm-domains` IAM permission. Key rotation does not remove already-stored trace data.

---

## Anti-Pattern 4: `manage management-dashboards` Granted to Individual IAM Users

**Risk Level**: HIGH | **Pillar**: Security

### ❌ Wrong — individual user grant
```
# Bypasses group hygiene — survives team turnover, invisible in membership audits
allow user oracleidentitycloudservice/alice@company.com to manage management-dashboards in compartment ProdCompartment
```

### ✅ Correct — group-level grant only
```
# Auditable via group membership; revoked by removing user from group
allow group ObservabilityEngineers to manage management-dashboards in compartment ProdCompartment
```

**Audit scan**:
```bash
rtk oci iam policy list \
  --compartment-id <root_compartment_ocid> \
  --all \
  --query "data[*].statements[]" | grep -i "allow user.*manage management-dashboards"
# Any match is a violation — convert to group-based grants
```

**Blast radius**: Individual grants survive organizational role changes and are invisible in group membership reports. A user who moves teams retains dashboard write access indefinitely. Malicious or accidental widget modification can silently corrupt production operational visibility.

---

## Anti-Pattern 5: Select a Trace-Level Attribute (`TraceStatus`) in a `show spans` Widget

**Risk Level**: HIGH | **Pillar**: Reliability, Operational Efficiency

APM TQL exposes two different attribute sets: span-level built-ins (`show spans`) and trace-level built-ins (`show traces`). They are NOT interchangeable. A spans widget that references a trace-level attribute fails to render — the query errors and the tile stays blank on an otherwise import-clean dashboard. Confirmed live 2026-07-07: `TraceStatus` in a `show spans` tile returns `attribute TraceStatus ... not found ... Character 63`.

### ❌ Wrong — trace-level `TraceStatus` inside a `show spans` query
```sql
-- Spans tile: TraceStatus is a TRACE attribute → "attribute TraceStatus not found"
show spans ServiceName, OperationName, SpanDuration, TraceStatus
where ServiceName = 'func-event-producer'
```

### ✅ Correct — use span-level status in spans; keep `TraceStatus` in a traces tile
```sql
-- Span-level error signal lives on the span
show spans ServiceName, OperationName, SpanDuration, SpanKind, SpanErrorCount
where ServiceName = 'func-event-producer' and SpanErrorCount > 0

-- Trace-level status belongs in a separate show traces tile
show traces TraceId, OperationName, TraceDuration, TraceStatus
where ServiceName = 'func-event-producer' and TraceStatus = 'ERROR'
```

Split the built-ins by query level:
- **`show spans`**: `ServiceName`, `OperationName`, `SpanDuration`, `SpanKind`, `SpanStatus`, `SpanErrorCount` (+ tags bare, e.g. `peer.service`).
- **`show traces`**: `TraceId`, `OperationName`, `TraceDuration`, `TraceStatus`, `TraceErrorSpans`.

**Detection**:
```bash
# Any TraceStatus/TraceDuration inside a "show spans" apmQuery is the bug
grep -o '"apmQuery": *"show spans[^"]*"' infra/modules/dashboards/dashboards/*.json \
  | grep -E 'TraceStatus|TraceDuration'
# Any match = trace attribute in a span query → blank tile
```

**Blast radius**: The tile imports without error (server-side import validation does not execute TQL) and silently renders nothing at view time. Operators believe error visibility exists when it does not — a masked-signal failure that only surfaces during an incident when the empty tile is needed most.

---

## Anti-Pattern 6: Free-Text Dashboard Parameters Expecting Them to Render as Filter Tiles

**Risk Level**: MEDIUM | **Pillar**: Operational Efficiency

Only OOB `savedSearch`-backed filters (compartment, region, time, apmDomain) render as interactive filter tiles on a Management Dashboard. A `parametersConfig` entry with no `savedSearchId` (a free-text/plain parameter) does NOT draw a filter tile — the value can only be supplied via the URL/API, never typed in the UI. A per-transaction-id drill built as a dashboard text box therefore appears "missing" to users. Confirmed live 2026-07-07.

### ❌ Wrong — free-text `transactionId` param expected to appear as a UI filter box
```json
"parametersConfig": [
  { "name": "transactionId", "valueSourceType": "text" }
]
// No savedSearchId → no filter tile renders → users cannot enter a transaction id
```

### ✅ Correct — only savedSearch-backed OOB filters as tiles; drill by transaction id in Trace Explorer
```json
"parametersConfig": [
  { "savedSearchId": "OOBSS-management-dashboard-compartment-filter", "name": "compartmentId" },
  { "savedSearchId": "OOBSS-management-dashboard-region-filter",      "name": "regionName" },
  { "savedSearchId": "OOBSS-management-dashboard-time-selector-filter","name": "time" },
  { "savedSearchId": "OOBSS-APM-domain-filter",                       "name": "apmDomain" }
]
// Per-transaction-id investigation → APM Trace Explorer (Trace Explorer search by
// transaction.id / TraceId), NOT a dashboard text box.
```

**Detection**:
```bash
# parametersConfig entries without a savedSearchId won't render as tiles
jq '.dashboards[].parametersConfig[]? | select(has("savedSearchId")|not)' \
  infra/modules/dashboards/dashboards/*.json
# Any result = a parameter the UI cannot expose as a filter tile
```

**Blast radius**: Design churn and false "broken dashboard" reports — the parameter exists but is invisible in the UI, so operators assume the drill-down feature failed. Steer per-record investigation (a specific transaction/trace id) to APM Trace Explorer, and reserve dashboard parameters for the OOB savedSearch-backed filters that actually render.
