# Integration Patterns — Provisioning OCI Object Storage

Terraform provisioning for the four cross-service integrations summarized in `SKILL.md`. All examples use the OCI Provider `~> 8.0` and assume `data.oci_objectstorage_namespace.ns` and `var.compartment_id` are defined.

## Contents

- [Pattern 1: Object Storage ↔ OCI Events + Functions](#pattern-1-object-storage--oci-events--functions)
- [Pattern 2: Object Storage ↔ OCI Data Flow (Apache Spark)](#pattern-2-object-storage--oci-data-flow-apache-spark)
- [Pattern 3: Object Storage ↔ OCI Connector Hub (Log Archival)](#pattern-3-object-storage--oci-connector-hub-log-archival)
- [Pattern 4: Object Storage ↔ OCI CDN](#pattern-4-object-storage--oci-cdn)

---

## Pattern 1: Object Storage ↔ OCI Events + Functions

Event-driven processing pipeline: object upload triggers a Function (virus scan, thumbnail, ETL).

**Use when**: processing must fire on object arrival. **Avoid when**: SLA < 200 ms (Events routing + Function cold start adds latency), or fan-out > 10 consumers (buffer through OCI Streaming instead).

```hcl
# Source bucket — events enabled
resource "oci_objectstorage_bucket" "source" {
  compartment_id        = var.compartment_id
  name                  = "uploads-${var.env}"
  namespace             = data.oci_objectstorage_namespace.ns.namespace
  access_type           = "NoPublicAccess"
  object_events_enabled = true
}

# Destination bucket — events DISABLED to prevent processing loops
resource "oci_objectstorage_bucket" "processed" {
  compartment_id        = var.compartment_id
  name                  = "processed-${var.env}"
  namespace             = data.oci_objectstorage_namespace.ns.namespace
  access_type           = "NoPublicAccess"
  object_events_enabled = false
}

# Events rule → Function target
resource "oci_events_rule" "on_upload" {
  compartment_id = var.compartment_id
  display_name   = "process-on-upload-${var.env}"
  is_enabled     = true
  condition = jsonencode({
    eventType = ["com.oraclecloud.objectstorage.createobject"]
    data      = { additionalDetails = { bucketName = oci_objectstorage_bucket.source.name } }
  })
  actions {
    actions {
      action_type = "FAAS"
      is_enabled  = true
      function_id = var.processor_function_id
    }
  }
}
```

**Gotcha**: `object_events_enabled = true` on the source bucket is required AND the Events rule condition must match `com.oraclecloud.objectstorage.createobject`. Missing either → events never fire.

---

## Pattern 2: Object Storage ↔ OCI Data Flow (Apache Spark)

Data lake with Hive-style prefix partitioning; OCI Data Flow (managed Spark) reads/writes bucket prefixes.

**Use when**: batch analytics over large object sets. **Avoid when**: sub-second query latency is required (use Autonomous DB instead).

```hcl
resource "oci_objectstorage_bucket" "datalake" {
  compartment_id = var.compartment_id
  name           = "datalake-${var.env}"
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  access_type    = "NoPublicAccess"
  storage_tier   = "Standard"
}

# Data Flow application reading Hive-partitioned prefixes (year=/month=/day=)
resource "oci_dataflow_application" "etl" {
  compartment_id = var.compartment_id
  display_name   = "etl-${var.env}"
  driver_shape   = "VM.Standard.E4.Flex"
  executor_shape = "VM.Standard.E4.Flex"
  num_executors  = 2
  language       = "PYTHON"
  spark_version  = "3.5.0"
  file_uri       = "oci://${oci_objectstorage_bucket.datalake.name}@${data.oci_objectstorage_namespace.ns.namespace}/scripts/etl.py"
  driver_shape_config {
    ocpus         = 1
    memory_in_gbs = 16
  }
  executor_shape_config {
    ocpus         = 1
    memory_in_gbs = 16
  }
}
```

**Gotcha**: Data Flow accesses buckets via resource-principal IAM (`allow dynamic-group df-runners to manage objects in compartment ...`), not user keys. Partition prefixes (`year=2026/month=07/`) let Spark prune scans.

---

## Pattern 3: Object Storage ↔ OCI Connector Hub (Log Archival)

Centralized log archival: OCI Logging / Audit → Service Connector Hub → Archive-tier bucket with CMEK and retention.

**Use when**: long-term compliance retention of logs. **Avoid when**: logs are queried frequently (Archive-tier restore takes hours).

```hcl
resource "oci_objectstorage_bucket" "log_archive" {
  compartment_id = var.compartment_id
  name           = "log-archive-${var.env}"
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  access_type    = "NoPublicAccess"
  storage_tier   = "Archive"
  kms_key_id     = var.cmek_key_id   # CMEK for compliance
  retention_rules {
    display_name = "retain-7y"
    duration {
      time_amount = 7
      time_unit   = "YEARS"
    }
  }
}

resource "oci_sch_service_connector" "logs_to_archive" {
  compartment_id = var.compartment_id
  display_name   = "logs-to-archive-${var.env}"
  source {
    kind = "logging"
    log_sources {
      compartment_id = var.compartment_id
      log_group_id   = var.log_group_id
    }
  }
  target {
    kind        = "objectStorage"
    bucket_name = oci_objectstorage_bucket.log_archive.name
    namespace   = data.oci_objectstorage_namespace.ns.namespace
  }
}
```

**Gotcha**: SCH needs `allow any-user to manage objects in compartment ... where all {request.principal.type = 'serviceconnector'}`. Retention rules and CMEK cannot be added to Archive-tier objects retroactively — set at bucket creation.

---

## Pattern 4: Object Storage ↔ OCI CDN

Private-origin static asset delivery: bucket stays private, CDN edge caches content via a pre-authenticated origin.

**Use when**: public static assets need edge caching without exposing the bucket. **Avoid when**: assets are user-specific/private (use per-request PARs instead).

```hcl
resource "oci_objectstorage_bucket" "assets" {
  compartment_id = var.compartment_id
  name           = "static-assets-${var.env}"
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  access_type    = "NoPublicAccess"   # bucket stays private
}

# Long-lived read-only PAR as CDN origin credential
resource "oci_objectstorage_preauthrequest" "cdn_origin" {
  namespace    = data.oci_objectstorage_namespace.ns.namespace
  bucket       = oci_objectstorage_bucket.assets.name
  name         = "cdn-origin-${var.env}"
  access_type  = "AnyObjectRead"
  time_expires = var.par_expiry   # rotate before expiry
}
```

**Gotcha**: Keep `access_type = "NoPublicAccess"` on the bucket — public delivery comes from the CDN edge, not the bucket. The PAR is the only credential the CDN origin should hold; rotate it before `time_expires` or delivery breaks.

---

## Common Problems

- **Replication destination not writable after policy deletion** → confirm `is_read_only = false` after `oci os replication delete-replication-policy`; propagation takes 1–2 minutes.
- **Object events not firing** → verify `object_events_enabled = true` on the bucket AND an Events rule matching `com.oraclecloud.objectstorage.createobject`.
- **Function cannot reach Object Storage in private subnet** → verify Service Gateway exists, route table has the OCI services CIDR, and the NSG allows egress TCP 443 to that CIDR.
