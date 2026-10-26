## Integration Patterns

### Streaming ↔ OCI Functions (Detached Mode Destination)

**Purpose**: Functions in detached mode publish execution results (success/failure) to a Stream for async processing.

```hcl
# Stream to receive async Function results (OCI Provider v6.x+)
resource "oci_streaming_stream" "function_results" {
  name               = "stream-fn-results-${var.environment}"
  partitions         = 3
  retention_in_hours = 48
  stream_pool_id     = oci_streaming_stream_pool.this.id
  freeform_tags      = var.tags
}

# Function with detached mode → success destination = stream
resource "oci_functions_function" "batch_processor" {
  application_id     = var.application_id
  display_name       = "batch-processor"
  image              = var.function_image
  memory_in_mbs      = 512
  timeout_in_seconds = 300

  detached_mode_timeout_in_seconds = 900

  success_destination {
    kind      = "STREAM"
    stream_id = oci_streaming_stream.function_results.id
  }

  failure_destination {
    kind     = "NOTIFICATION"
    topic_id = var.error_topic_ocid
  }

  freeform_tags = var.tags
}
```

---

### Streaming ↔ Service Connector Hub

**Purpose**: Service Connector Hub reads from a Stream and invokes a Function for continuous event processing.

```hcl
# Service Connector Hub: Stream → Function (OCI Provider v6.x+)
resource "oci_sch_service_connector" "stream_to_function" {
  compartment_id = var.compartment_ocid
  display_name   = "sch-stream-to-fn-${var.environment}"

  source {
    kind = "streaming"
    cursor {
      kind = "TRIM_HORIZON"
    }
    stream_id = oci_streaming_stream.events.id
  }

  target {
    kind        = "functions"
    function_id = var.processor_function_id
  }

  freeform_tags = var.tags
}
```

---

### Streaming ↔ IAM (Dynamic Group Policies)

**Purpose**: IAM policies granting Functions permission to produce/consume from Streams.

```hcl
# IAM Policy for Functions to push/pull from Streams (OCI Provider v6.x+)
resource "oci_identity_policy" "streaming" {
  compartment_id = var.tenancy_ocid
  name           = "policy-streaming-${var.project_name}-${var.environment}"
  description    = "Allow Functions to produce/consume from Streams"

  statements = [
    "Allow dynamic-group ${var.functions_dynamic_group_name} to use stream-push in compartment ${var.compartment_name}",
    "Allow dynamic-group ${var.functions_dynamic_group_name} to use stream-pull in compartment ${var.compartment_name}",
    # Required if using customer-managed encryption key
    "Allow service streaming to use keys in compartment ${var.compartment_name} where target.key.id = '${var.kms_key_ocid}'",
  ]
}
```

---

### Streaming ↔ Network (NSG Rules for Kafka)

**Purpose**: NSG rules enabling Kafka protocol (port 9092) communication between Functions and private Stream Pool.

```hcl
# NSG for Streaming private endpoint (OCI Provider v6.x+)
resource "oci_core_network_security_group" "streaming" {
  compartment_id = var.compartment_ocid
  vcn_id         = var.vcn_id
  display_name   = "nsg-streaming-${var.environment}"
  freeform_tags  = var.tags
}

# Ingress: Allow Kafka (9092) from Functions NSG
resource "oci_core_network_security_group_security_rule" "streaming_ingress_kafka" {
  network_security_group_id = oci_core_network_security_group.streaming.id
  direction                 = "INGRESS"
  protocol                  = "6"  # TCP
  source                    = var.nsg_functions_id
  source_type               = "NETWORK_SECURITY_GROUP"
  description               = "Allow Kafka from Functions"
  stateless                 = false

  tcp_options {
    destination_port_range {
      min = 9092
      max = 9092
    }
  }
}

# Egress: Allow Functions to reach Streaming NSG on 9092
resource "oci_core_network_security_group_security_rule" "functions_egress_streaming" {
  network_security_group_id = var.nsg_functions_id
  direction                 = "EGRESS"
  protocol                  = "6"  # TCP
  destination               = oci_core_network_security_group.streaming.id
  destination_type          = "NETWORK_SECURITY_GROUP"
  description               = "Allow Kafka egress to Streaming"
  stateless                 = false

  tcp_options {
    destination_port_range {
      min = 9092
      max = 9092
    }
  }
}
```

---

### Streaming ↔ OCI Events (Event Rule → Stream)

**Purpose**: OCI Events rules capture service-level events and publish to a Stream for audit/processing.

```hcl
# OCI Events rule → publish to Stream (OCI Provider v6.x+)
resource "oci_events_rule" "audit_to_stream" {
  compartment_id = var.compartment_ocid
  display_name   = "rule-audit-to-stream-${var.environment}"
  is_enabled     = true

  condition = jsonencode({
    eventType = [
      "com.oraclecloud.functions.function.invoke",
      "com.oraclecloud.apigateway.createdeployment"
    ]
  })

  actions {
    actions {
      action_type = "OSS"  # OCI Streaming Service
      is_enabled  = true
      stream_id   = oci_streaming_stream.audit.id
    }
  }

  freeform_tags = var.tags
}
```

---

