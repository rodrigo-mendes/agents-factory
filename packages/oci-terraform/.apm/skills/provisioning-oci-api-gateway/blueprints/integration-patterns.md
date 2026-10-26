## Integration Patterns

### API Gateway ↔ OCI Functions

**Compatibility**: OCI Provider v6.x+ | Functions in same region and tenancy

```hcl
# ✅ Complete integration: Function as API Gateway backend (OCI Provider v6.x+)
resource "oci_functions_application" "this" {
  compartment_id = var.compartment_ocid
  display_name   = var.application_name
  subnet_ids     = [var.subnet_private_id]

  config = {
    "LOG_LEVEL"    = "INFO"
    "SERVICE_NAME" = var.application_name
  }
}

resource "oci_functions_function" "this" {
  application_id     = oci_functions_application.this.id
  display_name       = var.function_name
  image              = var.function_image
  memory_in_mbs      = var.memory_in_mbs
  timeout_in_seconds = var.timeout_in_seconds

  provisioned_concurrency_config {
    strategy = var.provisioned_concurrency > 0 ? "CONSTANT" : "NONE"
    count    = var.provisioned_concurrency > 0 ? var.provisioned_concurrency : null
  }
}

# Route → Function backend
resource "oci_apigateway_deployment" "this" {
  specification {
    routes {
      path    = "/api/{path*}"
      methods = ["GET", "POST", "PUT", "DELETE"]
      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = oci_functions_function.this.id
      }
    }
  }
}
```

**Common Issues**:
- **502 Bad Gateway**: Missing IAM policy `use fn-invocation` — see [provisioning-oci-iam](../../provisioning-oci-iam/SKILL.md)
- **Cold starts**: 2-5s for Java Functions — mitigate with `provisioned_concurrency`
- **Timeout**: Function max 300s; API Gateway must match or exceed Function timeout

**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingoraclefunctionsbackend.htm

---

### API Gateway ↔ VCN (Network)

**Pattern**: API Gateway in public subnet; Functions in private subnet; NSGs control inter-tier communication.

```hcl
# ✅ Network segmentation for API Gateway + Functions (OCI Provider v6.x+)

# NSG: API Gateway — only HTTPS inbound from internet
resource "oci_core_network_security_group_security_rule" "apigw_ingress_443" {
  network_security_group_id = oci_core_network_security_group.apigw.id
  direction                 = "INGRESS"
  protocol                  = "6"  # TCP
  source                    = "0.0.0.0/0"
  source_type               = "CIDR_BLOCK"
  description               = "HTTPS from internet"

  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}

# NSG: Functions — only from API Gateway NSG
resource "oci_core_network_security_group_security_rule" "functions_ingress" {
  network_security_group_id = oci_core_network_security_group.functions.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = oci_core_network_security_group.apigw.id
  source_type               = "NETWORK_SECURITY_GROUP"
  description               = "Traffic from API Gateway NSG only"

  tcp_options {
    destination_port_range {
      min = 1
      max = 65535
    }
  }
}
```

**Required Gateways**:
- **Internet Gateway**: Required for public API Gateway subnet
- **NAT Gateway**: Required for Functions private subnet egress (image pull, external API calls)
- **Service Gateway**: Required for Functions to access OCI services (Object Storage, Vault) without internet

**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/networksecuritygroups.htm — see also [designing-oci-networking](../../designing-oci-networking/SKILL.md)

---

### API Gateway ↔ OCI Logging & Monitoring

**Pattern**: Service Logs for access/execution; Monitoring Alarms for anomaly detection.

```hcl
# ✅ Observability stack for API Gateway (OCI Provider v6.x+)
resource "oci_logging_log_group" "this" {
  compartment_id = var.compartment_ocid
  display_name   = "lg-${var.project_name}-${var.environment}"
}

resource "oci_logging_log" "apigw_access" {
  display_name = "log-apigw-access-${var.environment}"
  log_group_id = oci_logging_log_group.this.id
  log_type     = "SERVICE"
  is_enabled   = true

  configuration {
    compartment_id = var.compartment_ocid
    source {
      category    = "access"
      resource    = var.api_deployment_id
      service     = "apigateway"
      source_type = "OCISERVICE"
    }
  }
}

# Alarm: High 5xx error rate
resource "oci_monitoring_alarm" "apigw_5xx" {
  compartment_id   = var.compartment_ocid
  display_name     = "alarm-apigw-5xx-${var.environment}"
  is_enabled       = true
  namespace        = "oci_apigateway"
  # Use a dimensão httpStatusCategory="5xx" — o regex httpStatusCode=~"5.." NÃO casa no MQL do OCI.
  query            = "HttpResponses[1m]{httpStatusCategory = \"5xx\"}.count() > 10"
  severity         = "CRITICAL"
  pending_duration = "PT5M"
  destinations     = [oci_ons_notification_topic.alerts.id]
  message_format   = "ONS_OPTIMIZED"
}
```

**Common Issues**:
- **log_type** must be `"SERVICE"` (not `"CUSTOM"`) for API Gateway logs
- **category** must be exactly `"access"` or `"execution"` for apigateway service
- Alarm queries use **MQL syntax** — validate before apply

**Source**: https://docs.oracle.com/en-us/iaas/Content/Logging/Concepts/loggingoverview.htm | https://docs.oracle.com/en-us/iaas/Content/Monitoring/Concepts/monitoringoverview.htm

---

