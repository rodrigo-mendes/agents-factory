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
