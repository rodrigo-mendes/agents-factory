# Ask First Decisions — logging-oci-java-functions

Present options to the user and wait for a decision before generating code. Four architectural crossroads.

---

## Decision 1: Java Logging Framework

**Question**: "Does the project already use Log4j2? What is the cold-start SLA?"

| Option | Structured JSON | Cold-Start Added | JAR Size | CVE History | Recommend When |
|--------|----------------|------------------|----------|-------------|----------------|
| **JUL (java.util.logging)** | Custom `Formatter` subclass | 0 ms | 0 KB | None | Minimal deps; hard cold-start SLA |
| **SLF4J 2.0.16 + Logback 1.5.18** | `logstash-logback-encoder:8.0` | +15–25 ms | ~800 KB | Low | Default choice — best JSON, MDC, easy config |
| **SLF4J 2.0.16 + Log4j2 2.24.x** | `log4j2-layout-template-json` | +20–35 ms | ~1.5 MB | Log4Shell CVE-2021-44228 (fixed ≥2.17.1) | Team already on Log4j2 — verify no transitive dep < 2.17.1 |
| **SLF4J + slf4j-simple** | No JSON support | +5 ms | ~100 KB | None | Dev/test only — never production |

**Agent guidance**:
1. "Does the project already use Log4j2?" → Yes → use Log4j2 2.24.x; run `mvn dependency:tree | grep log4j` before proceeding
2. "Is cold-start latency a hard SLA (< 500 ms)?" → Consider JUL with custom JSON Formatter
3. "No existing logging dependency?" → Use SLF4J + Logback (recommended default)

**Log4j2 — critical note**: If chosen, verify no transitive dependency pulls in < 2.17.1. Explicitly declare in `<dependencyManagement>`:
```xml
<dependency>
    <groupId>org.apache.logging.log4j</groupId>
    <artifactId>log4j-bom</artifactId>
    <version>2.24.3</version>
    <type>pom</type>
    <scope>import</scope>
</dependency>
```

---

## Decision 2: Log Delivery Strategy

**Question**: "What is the required log retention period? Is there an audit compliance requirement (PCI, SOC2, GDPR)?"

| Option | IAM Required | Retention Max | Structured Query | Complexity |
|--------|-------------|---------------|-----------------|------------|
| **stdout capture only** | OCI Log resource on app | 180 days | OCI Logging search + MQL | Low — zero code |
| **SDK PutLogs only** | `use log-content` on log group | 180 days | OCI Logging search | High — SDK setup |
| **stdout + SDK PutLogs** | Both above | 180 days (per log group) | Both streams | Very High |
| **stdout → Connector Hub → Log Analytics** | Connector Hub + LA | Unlimited | Full-text, ML anomaly | High setup; no function code change |

**Agent guidance**:
1. "Is retention beyond 180 days needed?" → stdout → Connector Hub → OCI Logging Analytics
2. "Are logs audit-critical (PCI/SOC2/HIPAA)?" → SDK PutLogs to a separate high-retention log group
3. "Is the goal simple operational visibility?" → stdout capture only (zero extra code)
4. "Real-time alerting on log content?" → stdout + OCI Alarm on MQL log search query

---

## Decision 3: PutLogs Batching Strategy

**Question**: "How many log entries does the function generate per invocation?"

| Option | API Calls | Latency Added | Risk | Use When |
|--------|-----------|---------------|------|----------|
| **Per-event** | 1 per log line | +20–50 ms each | Timeout exhaustion under volume | < 3 entries/invoke (avoid) |
| **Batch at end of invocation** | 1 | +20–50 ms once | None | Standard — recommended for most functions |
| **Periodic flush within invocation** | N (bounded) | Bounded | Partial batch if function times out early | Long-running batch functions only |

**Default**: Always recommend **batch at end of invocation** — collect `List<LogEntry>` during the handler, issue one `putLogs` call in the `finally` block before returning.

---

## Decision 4: Log Group Organization

**Question**: "What is the compliance tier? Do developers have read access to production logs?"

| Option | Retention Control | IAM Scoping | Compliance | Complexity |
|--------|-----------------|-------------|------------|------------|
| **Single log group** | One `retention_duration` | Same group for all | Basic | Low |
| **Separate operational + audit groups** | Independent per-group | Different IAM policies; restrict developer access to audit group | PCI/SOC2/HIPAA | Medium |

**Terraform** (separate groups pattern):
```hcl
resource "oci_logging_log_group" "fn_operational" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.app_name}-operational-logs"
}

resource "oci_logging_log_group" "fn_audit" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.app_name}-audit-logs"
}

resource "oci_logging_log" "fn_operational_log" {
  log_group_id       = oci_logging_log_group.fn_operational.id
  log_type           = "SERVICE"
  retention_duration = 30
  configuration {
    source {
      category    = "invoke"
      resource    = oci_functions_application.app.id
      service     = "functions"
      source_type = "OCISERVICE"
    }
    compartment_id = var.compartment_ocid
  }
  is_enabled = true
}

resource "oci_logging_log" "fn_audit_log" {
  display_name       = "${var.app_name}-audit-log"
  log_group_id       = oci_logging_log_group.fn_audit.id
  log_type           = "CUSTOM"
  retention_duration = 90   # longer retention for audit
  is_enabled         = true
}
```

**IAM note**: Apply a separate policy to deny developers `read log-content` on the audit log group.
