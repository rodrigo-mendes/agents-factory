# ⚠️ Ask First Decisions — OCI Logging

## Decision 1: Log Ingestion Method

**Ask**: "Does the application currently write logs to disk files, or emit logs programmatically?"

| Option | Source Type | Best When | Constraint |
|--------|-------------|-----------|------------|
| UMA `LOG_TAIL` | `LOG_TAIL` source in UMA config | Existing apps writing to log files; no code changes tolerated | Oracle Cloud Agent must be installed and Logging plugin enabled |
| OCI SDK PutLogs | Direct API `POST /20200531/logs/{logId}/actions/push` | Greenfield apps; OCI Functions; Container Instances | Requires IAM resource principal (instance principal or Functions principal) |
| `CUSTOM_PLUGIN` | Fluentd plugin config | TCP/UDP syslog, HTTP log receivers, proprietary protocols | Requires Fluentd plugin expertise; no OCI Console validation |
| `WINDOWS_EVENT_LOG` | Windows channel names | Windows compute (IIS, AD, .NET services) | Windows-only; Oracle Cloud Agent required |

**File-based → UMA LOG_TAIL (no code changes needed):**
```hcl
sources {
  name        = "app-log-tail"
  source_type = "LOG_TAIL"
  paths       = ["/var/log/app/*.log"]
  advanced_options {
    is_read_from_head = true  # Set true on initial deployment to catch existing data
  }
  parser { parser_type = "JSON" }
}
```

**Programmatic / Functions → Direct SDK:**
```python
from oci.loggingingestion import LoggingClient
from oci.loggingingestion.models import PutLogsDetails, LogEntryBatch, LogEntry
import datetime, uuid

client = LoggingClient(config={}, signer=oci.auth.signers.InstancePrincipalsSecurityTokenSigner())
client.put_logs(
    log_id="<log-ocid>",
    put_logs_details=PutLogsDetails(
        specversion="1.0",
        log_entry_batches=[LogEntryBatch(
            entries=[LogEntry(id=str(uuid.uuid4()), data='{"level":"INFO","msg":"hello"}', time=datetime.datetime.utcnow())],
            source="my-function",
            type="com.myapp.log"
        )]
    )
)
```

---

## Decision 2: UMA Parser Type

**Ask**: "What format does the application write log lines in — structured JSON, fixed-format text, or multi-line?"

| Format | `parser_type` | When | Notes |
|--------|---------------|------|-------|
| Structured JSON | `JSON` | App emits `{"level":"INFO","msg":"..."}` | Zero config; all fields searchable |
| Fixed-format with known structure | `GROK` | Apache/nginx-style, custom fixed format | Named capture groups; requires pattern authoring |
| Simple fixed-format | `REGEXP` | Known structure, no Grok expertise | Regex capture groups only |
| Java stack traces / multi-line errors | `MULTILINE_GROK` | Python tracebacks, SQL error blocks | Requires `multi_line_start_regexp` |
| Kubernetes CRI format (OKE) | `CRI` | OKE worker node `/var/log/pods/**/*.log` | Supports `nested_parser` for inner JSON |
| Prometheus metrics endpoint | `OPENMETRICS` | MONITORING config type only | Emits to OCI Monitoring, not OCI Logging |
| Raw blob | `NONE` | **Never in production** — see Never Do #2 | |

**JSON (preferred for greenfield):**
```hcl
parser {
  parser_type = "JSON"
  time_type   = "STRING"
  time_format = "%Y-%m-%dT%H:%M:%S.%LZ"
}
```

**GROK (for structured text like Apache access logs):**
```hcl
parser {
  parser_type = "GROK"
  patterns {
    name    = "access-log"
    pattern = "%{COMBINEDAPACHELOG}"
  }
}
```

**MULTILINE_GROK (for Java exception traces):**
```hcl
parser {
  parser_type             = "MULTILINE_GROK"
  multi_line_start_regexp = "^\\d{4}-\\d{2}-\\d{2}"
  patterns {
    name    = "java-exception"
    pattern = "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}"
  }
}
```

---

## Decision 3: Retention Beyond 180 Days

**Ask**: "Will archived log data ever need to be searched, or is it purely produce-on-demand for regulatory compliance?"

| Option | Services | Cost | Search | Best When |
|--------|---------|------|--------|-----------|
| Connector Hub → Object Storage | Connector Hub + Object Storage + Retention Rules | $$ | No native search (use Data Flow) | Audit-only, WORM compliance (SOC2, PCI, HIPAA) |
| Connector Hub → Logging Analytics | Connector Hub + Logging Analytics | $$$ | Full KQL + ML anomaly detection | Active SOC, ongoing threat hunting |
| Dual pipeline | Both Object Storage (archive) + Logging Analytics (search) | $$$+ | Archive + active search | Enterprise SOC with both compliance and operational needs |
| Object Storage → Archive Storage | Object Storage Lifecycle Policy | $-$$ (lowest storage, high retrieval) | Hours retrieval latency | 7+ year cold archives |

**Object Storage WORM pipeline (compliance-first, lowest cost):**
```hcl
resource "oci_objectstorage_bucket" "log_archive" {
  name           = "prod-log-archive-immutable"
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  compartment_id = var.security_compartment_ocid
  versioning     = "Enabled"
  kms_key_id     = oci_kms_key.log_archive_cmk.id
}
# Note: Lock Retention Rules immediately after creation — locked rules cannot be shortened
# oci os retention-rule create --bucket-name prod-log-archive-immutable --time-amount 365 --time-unit DAYS
```

---

## Decision 4: Service Log Enablement Strategy

**Ask**: "What are the daily log volume estimates for each service and what is the per-service retention budget?"

**Recommended enablement priority:**

| OCI Service | Log Category | Priority | Volume | Action Before Enable |
|-------------|-------------|----------|--------|---------------------|
| VCN Flow Logs (perimeter subnet) | `all` | CRITICAL | HIGH | Deploy archival pipeline first |
| VCN Flow Logs (app subnets) | `reject` | CRITICAL | MEDIUM | Deploy archival pipeline first |
| Load Balancer | `access` + `error` | HIGH | MEDIUM-HIGH | Estimate daily volume |
| API Gateway | `execution` | HIGH | HIGH | Estimate daily volume |
| Bastion | `access` | HIGH | LOW | Standard 180-day retention |
| WAF | `access` | HIGH | HIGH | Deploy archival pipeline first |
| Autonomous DB | `oci_autonomous_db_data_safe_audit` | CRITICAL | LOW | 180-day + archival |
| OKE | `kube-apiserver` | MEDIUM | MEDIUM | Estimate per cluster |
| Object Storage | `read`, `write` | MEDIUM | **VERY HIGH** if busy bucket | Volume assessment mandatory |
| Functions | `function-invocation` | MEDIUM | MEDIUM | Standard retention |

**Volume estimation before enabling Object Storage logs:**
```bash
# Check recent bucket request metrics to estimate log volume before enabling
oci monitoring metric-data summarize-metrics-data \
  --compartment-id <ocid> \
  --namespace oci_objectstorage \
  --query-text 'AllRequests[1d].sum()' \
  --start-time "$(date -u -v-7d +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```
