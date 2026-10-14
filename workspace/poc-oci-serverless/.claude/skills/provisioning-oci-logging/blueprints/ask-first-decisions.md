# Ask First Decisions — OCI Logging (Terraform oracle/oci ~> 8.15)

## Decision 1: LOGGING vs. MONITORING `configuration_type`

**Ask**: "Are you collecting log files from disk, or scraping Prometheus metrics from Kubernetes pods?"

| Option | Optimizes | Sacrifices | Use Case |
|---|---|---|---|
| `LOGGING` | Log collection & forwarding | No metrics output | File tail, syslog, Windows Event Log, CUSTOM_PLUGIN |
| `MONITORING` | Prometheus metric scraping | No log file collection | OKE pod metric scraping → OCI Monitoring |

**Rule**: A single `oci_logging_unified_agent_configuration` resource cannot mix both types. Create two separate resources if both are needed.

```hcl
# LOGGING — file collection
service_configuration {
  configuration_type = "LOGGING"
  sources {
    source_type = "LOG_TAIL"
    paths       = ["/var/log/app/*.log"]
    # ...
  }
}

# MONITORING — Kubernetes pod metric scraping
service_configuration {
  configuration_type = "MONITORING"
  application_configurations {
    source_type = "KUBERNETES"
    # ...
  }
}
```

---

## Decision 2: Per-Environment Log Groups vs. Shared Log Group

**Ask**: "Do different environments need separate IAM policies or Connector Hub routing?"

| Option | Optimizes | Sacrifices | OCI Quota |
|---|---|---|---|
| Per-env groups | Strict IAM isolation, simple Connector Hub | Resource count | 50 groups/compartment (soft limit) |
| Shared group | Resource efficiency | Cross-env blast radius, complex filter | 50 groups/compartment |

**Guidance**:
- **Per-env groups**: production, regulated workloads, separate team access, distinct Connector Hub pipelines
- **Shared group**: dev/staging only, single-team small projects

```hcl
# Per-env: one group per environment
resource "oci_logging_log_group" "app_logs" {
  for_each       = toset(["dev", "staging", "prod"])
  display_name   = "${var.app_name}-${each.key}-app-logs"
  compartment_id = var.compartment_id
  freeform_tags  = merge(local.common_tags, { "environment" = each.key })
}
```

---

## Decision 3: State Backend — Local vs. OCI Object Storage vs. ORM

**Ask**: "Is this a single-cloud OCI deployment? How many team members will run Terraform?"

| Option | Optimizes | Sacrifices | Locking |
|---|---|---|---|
| Local | Simplicity | No sharing, no locking | None |
| OCI Object Storage (HTTP backend) | OCI-native, no cost | No built-in locking | None (workflow-level controls needed) |
| OCI Resource Manager (ORM) | Built-in locking, IAM, audit | ORM stack deployment model | Built-in |
| HCP Terraform | SaaS ease, VCS hooks | Cost, vendor lock | Built-in |

**Guidance**: ORM preferred for OCI-first teams. OCI Object Storage viable for existing Terraform pipelines with CI/CD approval gates preventing concurrent applies.

```hcl
# OCI Object Storage backend (no native locking)
backend "http" {
  # address      = "https://objectstorage.<region>.oraclecloud.com/p/<PAR>/n/<ns>/b/<bucket>/o/tfstate"
  # update_method = "PUT"
}

# ORM: no backend block — state managed automatically by ORM
```

---

## Decision 4: Parser Type for UMA Sources

**Ask**: "What format do application logs use? (JSON, Apache combined, Java multi-line, container CRI, custom?)"

| Parser | Best For | Pitfall |
|---|---|---|
| `JSON` | Structured app logs (12-factor) | Silently fails on non-JSON lines |
| `CRI` | OKE / Kubernetes container logs | Requires `is_merge_cri_fields = true` |
| `GROK` | Apache, Nginx, common formats | Requires grok pattern knowledge |
| `MULTILINE` | Java stack traces | Requires `format_firstline` anchor |
| `REGEXP` | Single-line custom pattern | Verbose regex; runtime compile error |
| `NONE` | Raw forwarding, downstream parses | No field extraction |
| `OPENMETRICS` | Prometheus endpoint scraping | Only for metrics → OCI Monitoring |

```hcl
# JSON (modern app logs)
parser { parser_type = "JSON" }

# CRI (OKE containers)
parser {
  parser_type         = "CRI"
  is_merge_cri_fields = true
}

# MULTILINE (Java stack traces)
parser {
  parser_type       = "MULTILINE"
  format_firstline  = "/^\\d{4}-\\d{2}-\\d{2}/"
  format            = ["/^(?<time>\\S+) (?<level>\\S+) (?<message>.*)$/"]
}
```

---

## Decision 5: `count` vs. `for_each` for Multiple Log Resources

**Ask**: "Will the set of log sources grow or change over time? Could the list order change?"

| Option | Optimizes | Pitfall |
|---|---|---|
| `count` | Simple conditional (0 or 1) | Index reordering causes resource recreation → log data loss |
| `for_each` | Stable map keys | More verbose; map key appears in state references |

**Rule**: Always use `for_each` with a map for multiple logs of the same type. `count` is acceptable only for single conditional resources (exists or not).

```hcl
variable "service_logs" {
  type = map(object({
    service  = string
    resource = string
    category = string
  }))
}

resource "oci_logging_log" "service" {
  for_each = var.service_logs

  display_name       = each.key
  log_group_id       = oci_logging_log_group.infra_logs.id
  log_type           = "SERVICE"
  is_enabled         = true
  retention_duration = var.log_retention_days

  configuration {
    source {
      source_type = "OCISERVICE"
      service     = each.value.service
      resource    = each.value.resource
      category    = each.value.category
    }
  }
}

# count: acceptable only for conditional single resource
resource "oci_logging_log" "lb_access" {
  count = var.load_balancer_ocid != "" ? 1 : 0
  # ...
}
```
