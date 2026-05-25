# ✅ Always Do Patterns — OCI Logging

## 1. Separate Log Groups by Compliance Domain

```hcl
# Minimum viable log group separation for production
resource "oci_logging_log_group" "app_logs" {
  compartment_id = var.app_compartment_ocid
  display_name   = "app-service-logs"
  description    = "Custom application logs — API service tier"
  defined_tags   = { "operations.environment" = "prod", "operations.owner" = "api-team" }
}

resource "oci_logging_log_group" "infra_logs" {
  compartment_id = var.app_compartment_ocid
  display_name   = "infra-platform-logs"
  description    = "Service logs: LB access, API Gateway, VCN flow"
  defined_tags   = { "operations.environment" = "prod", "operations.owner" = "platform-team" }
}

resource "oci_logging_log_group" "security_logs" {
  compartment_id = var.security_compartment_ocid
  display_name   = "security-audit-logs"
  description    = "Compliance scope — Connector Hub uses _Audit sentinel for audit events"
  defined_tags   = { "operations.environment" = "prod", "operations.owner" = "security-team" }
}
```

**Recommended taxonomy**:
```
compartment: <app>
├── app-service-logs     → Custom logs (application tier) — developers can read
├── infra-platform-logs  → Service logs (LB, API GW, VCN flow) — platform team only
└── db-audit-logs        → Service logs (DB audit) — security team only

compartment: security
└── security-audit-logs  → Connector Hub _Audit sentinel target
```

---

## 2. Set `retention_duration` Explicitly at Creation Time

```hcl
# Operational logs — 90-day minimum for production
resource "oci_logging_log" "api_access_log" {
  display_name       = "api-service-access"
  log_group_id       = oci_logging_log_group.app_logs.id
  log_type           = "CUSTOM"
  is_enabled         = var.logging_enabled
  retention_duration = 90  # Set at creation — retroactive increase does NOT recover deleted data
}

# Compliance/security logs — 180 days (max) + mandatory archival pipeline
resource "oci_logging_log" "vcn_flow_log" {
  display_name       = "vcn-flow-logs-prod"
  log_group_id       = oci_logging_log_group.infra_logs.id
  log_type           = "SERVICE"
  is_enabled         = var.logging_enabled
  retention_duration = 180  # Maximum — pair with Connector Hub → Object Storage
  depends_on         = [oci_sch_service_connector.vcn_flow_archiver]  # Archival FIRST
  configuration {
    source {
      category    = "reject"   # See Never Do #5 before using "all"
      resource    = oci_core_subnet.app_subnet.id
      service     = "flowlogs"
      source_type = "OCISERVICE"
    }
  }
}
```

---

## 3. Deploy UMA via Dynamic Group Association

```hcl
# Step 1: Dynamic group at tenancy level (not compartment)
resource "oci_identity_dynamic_group" "app_instances" {
  compartment_id = var.tenancy_ocid
  name           = "prod-app-instances"
  description    = "All compute instances in the production app compartment"
  matching_rule  = "ALL {instance.compartment.id = '${var.app_compartment_ocid}'}"
}

# Step 2: IAM policy — write-only (instances ship logs, cannot read)
resource "oci_identity_policy" "instance_logging" {
  compartment_id = var.tenancy_ocid
  name           = "prod-instance-logging-policy"
  statements = [
    "allow dynamic-group prod-app-instances to use log-content in compartment prod-app"
  ]
}

# Step 3: UMA configuration associated with the dynamic group
resource "oci_logging_unified_agent_configuration" "app_log_collector" {
  compartment_id = var.app_compartment_ocid
  display_name   = "app-log-collector-prod"
  is_enabled     = true

  group_association {
    group_list = [oci_identity_dynamic_group.app_instances.id]
  }

  service_configuration {
    configuration_type = "LOGGING"
    sources {
      name        = "app-json-logs"
      source_type = "LOG_TAIL"
      paths       = ["/var/log/app/*.log", "/var/log/app/*.json"]
      parser {
        parser_type = "JSON"
      }
    }
    destination {
      log_object_id = oci_logging_log.api_access_log.id
    }
  }
}
```

---

## 4. Control `is_enabled` via Variable

```hcl
variable "logging_enabled" {
  description = "Enable log collection. Set false only for dev/test environments."
  type        = bool
  default     = true  # Production default: always true
}

resource "oci_logging_log" "example" {
  display_name       = "api-service-access"
  log_group_id       = oci_logging_log_group.app_logs.id
  log_type           = "CUSTOM"
  is_enabled         = var.logging_enabled  # Never hardcode false for prod
  retention_duration = 90
}
```

---

## 5. Enable Operational Metrics on All Production UMA Configurations

```hcl
service_configuration {
  configuration_type = "LOGGING"

  sources {
    name        = "app-logs"
    source_type = "LOG_TAIL"
    paths       = ["/var/log/app/app.log"]
    parser { parser_type = "JSON" }
  }

  destination {
    log_object_id = oci_logging_log.api_access_log.id

    operational_metrics_configuration {
      source {
        type = "UMA_METRICS"
        record_input {
          namespace      = "oci_logging_agent_health"
          resource_group = "prod-app-agents"
        }
      }
      destination {
        compartment_id = var.app_compartment_ocid
      }
    }
  }
}
# Create OCI Monitoring alarm on oci_logging_agent_health namespace:
# metric: BufferQueueLength — alert when > threshold indicates log shipping failure
```

---

## 6. Archival Pipeline Before High-Volume Service Logs (Terraform Order)

```hcl
# 1. Archive bucket first
resource "oci_objectstorage_bucket" "vcn_flow_archive" {
  name           = "prod-vcn-flow-archive"
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  compartment_id = var.security_compartment_ocid
  versioning     = "Enabled"
}

# 2. Connector Hub archival connector second
resource "oci_sch_service_connector" "vcn_flow_archiver" {
  depends_on     = [oci_objectstorage_bucket.vcn_flow_archive]
  compartment_id = var.app_compartment_ocid
  display_name   = "vcn-flow-log-archiver"
  source {
    kind = "logging"
    log_sources {
      compartment_id = var.app_compartment_ocid
      log_group_id   = oci_logging_log_group.infra_logs.id
      log_id         = oci_logging_log.vcn_flow_log.id
    }
  }
  target {
    kind               = "objectStorage"
    bucket             = oci_objectstorage_bucket.vcn_flow_archive.name
    object_name_prefix = "vcn-flow-logs/prod/"
  }
}

# 3. Enable the service log AFTER archival is confirmed
resource "oci_logging_log" "vcn_flow_log" {
  depends_on         = [oci_sch_service_connector.vcn_flow_archiver]
  log_type           = "SERVICE"
  is_enabled         = true
  retention_duration = 180
  # ... source configuration
}
```

---

## 7. Three-Tier IAM Policy for Log Access

```hcl
# Production log access — least privilege, three tiers
resource "oci_identity_policy" "logging_access" {
  compartment_id = var.tenancy_ocid
  name           = "prod-logging-access-policy"
  statements = [
    # Tier 1: Instances — write-only (ship logs, cannot read)
    "allow dynamic-group prod-app-instances to use log-content in compartment prod-app",

    # Tier 2: SRE team — read log data for investigation (compartment-scoped)
    "allow group platform-sre to read log-content in compartment prod-app",
    "allow group platform-sre to read logging-family in compartment prod-app",

    # Tier 3: IaC pipeline — manage log resources only (NOT log data)
    "allow group terraform-pipeline to manage logging-family in compartment prod-app",
    # Note: "manage logging-family" does NOT grant read log-content — safe for IaC

    # Security team — audit log group in dedicated compartment
    "allow group security-auditors to read log-content in compartment security",
    "allow group security-auditors to read logging-family in compartment security"
  ]
}
```

**IAM verb reference:**
- `use log-content` → write logs (for instances/UMA)
- `read log-content` → read log data (for operators/SIEM)
- `manage logging-family` → create/update/delete log groups and logs (for IaC)
- `manage log-content` → **avoid** unless log deletion is explicitly required
