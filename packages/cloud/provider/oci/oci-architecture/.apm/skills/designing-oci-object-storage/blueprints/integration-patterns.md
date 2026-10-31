# Integration Patterns — OCI Object Storage

Four cross-service integration patterns with complete Terraform/CLI examples.

---

## Pattern 1: Event-Driven Object Processing Pipeline

**Object Storage ↔ OCI Events ↔ OCI Functions**

Use when: processing must be triggered by object arrival (virus scan, image thumbnail, ETL, ML inference).

**Do NOT use when**: SLA < 200 ms (Functions cold start + event routing adds 200 ms–2 s latency); or same event must fan out to > 10 consumers (use OCI Streaming buffer instead).

```hcl
# Source bucket with events enabled
resource "oci_objectstorage_bucket" "source" {
  compartment_id        = var.compartment_id
  name                  = "uploads-${var.env}"
  namespace             = data.oci_objectstorage_namespace.ns.namespace
  access_type           = "NoPublicAccess"
  object_events_enabled = true
}

# Separate destination bucket — prevents event loops
resource "oci_objectstorage_bucket" "processed" {
  compartment_id        = var.compartment_id
  name                  = "processed-${var.env}"
  namespace             = data.oci_objectstorage_namespace.ns.namespace
  access_type           = "NoPublicAccess"
  object_events_enabled = false
}

# OCI Events rule → Function
resource "oci_events_rule" "on_upload" {
  compartment_id = var.compartment_id
  display_name   = "process-on-upload"
  is_enabled     = true

  condition = jsonencode({
    eventType = ["com.oraclecloud.objectstorage.createobject"]
    data      = { bucketName = [oci_objectstorage_bucket.source.name] }
  })

  actions {
    actions {
      action_type = "FAAS"
      function_id = oci_functions_function.processor.id
      is_enabled  = true
    }
  }
}
```

**Function receives event payload** (metadata only — must fetch object separately):
```python
import io, json, oci
from fdk import response

def handler(ctx, data: io.BytesIO = None):
    event = json.loads(data.getvalue())
    bucket_name = event["data"]["bucketName"]
    object_name = event["data"]["resourceName"]

    # Use Instance Principal — no credentials in code
    signer = oci.auth.signers.get_resource_principals_signer()
    os_client = oci.object_storage.ObjectStorageClient({}, signer=signer)
    namespace = os_client.get_namespace().data

    obj = os_client.get_object(namespace, bucket_name, object_name)
    # Process obj.data.content ...
    return response.Response(ctx, response_data=json.dumps({"status": "ok"}))
```

**Design constraint**: Consumer must be idempotent — at-least-once delivery means the same event may trigger multiple invocations.

---

## Pattern 2: Data Lake with Hive-Style Prefix Partitioning

**Object Storage ↔ OCI Data Flow (Apache Spark) ↔ OCI Data Catalog**

Use when: analytics workloads with time or categorical query predicates; buckets with > 1 million objects.

**Prefix partition convention** (design upfront — reorganization requires full object copy/delete):
```
{dataset}/{year=YYYY}/{month=MM}/{day=DD}/{hour=HH}/{uuid}.parquet
```

```hcl
# Raw landing zone — versioned, short retention
resource "oci_objectstorage_bucket" "raw" {
  name       = "datalake-raw-${var.env}"
  namespace  = data.oci_objectstorage_namespace.ns.namespace
  access_type = "NoPublicAccess"
  versioning = "Enabled"
}

# Processed/curated zone — auto-tiering for mixed access
resource "oci_objectstorage_bucket" "processed" {
  name         = "datalake-processed-${var.env}"
  namespace    = data.oci_objectstorage_namespace.ns.namespace
  access_type  = "NoPublicAccess"
  storage_tier = "Standard"
  auto_tiering = "InfrequentAccess"
}

# Archive zone — lifecycle-transitioned data
resource "oci_objectstorage_bucket" "archive" {
  name         = "datalake-archive-${var.env}"
  namespace    = data.oci_objectstorage_namespace.ns.namespace
  access_type  = "NoPublicAccess"
  storage_tier = "Archive"
}

# Lifecycle: age-based tier transition on processed zone
resource "oci_objectstorage_object_lifecycle_policy" "processed_lifecycle" {
  bucket    = oci_objectstorage_bucket.processed.name
  namespace = data.oci_objectstorage_namespace.ns.namespace

  rules {
    name        = "archive-old-partitions"
    action      = "DELETE"
    is_enabled  = true
    target      = "objects"
    time_amount = 365
    time_unit   = "DAYS"

    object_name_filter {
      inclusion_prefixes = ["events/"]  # Scope to specific datasets
    }
  }

  rules {
    name        = "abort-multipart"
    action      = "ABORT"
    is_enabled  = true
    target      = "multipart-uploads"
    time_amount = 7
    time_unit   = "DAYS"
  }
}
```

**OCI Data Flow (Spark) reading from Object Storage** (uses Instance Principal via Dynamic Group):
```python
# spark_job.py — read partitioned Parquet from OCI Object Storage
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("datalake-query").getOrCreate()

# OCI Object Storage URI format
df = spark.read.parquet(
    "oci://datalake-processed-prod@<namespace>/events/year=2024/month=05/"
)
df.filter("day = '25'").show()
```

---

## Pattern 3: Centralized Log Archival

**OCI Logging / Audit ↔ OCI Connector Hub ↔ Object Storage (Archive + CMEK + Retention)**

Use when: compliance log retention beyond OCI Audit's built-in 90-day window.

```hcl
# Archive-tier bucket with CMEK for compliance log storage
resource "oci_objectstorage_bucket" "log_archive" {
  compartment_id = var.log_compartment_id
  name           = "compliance-logs-${var.env}"
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  access_type    = "NoPublicAccess"
  storage_tier   = "Archive"
  kms_key_id     = oci_kms_key.log_key.id

  defined_tags = {
    "Operations.DataClassification" = "confidential"
    "Operations.Environment"        = var.environment
    "Finance.CostCenter"            = var.cost_center
  }
}

# OCI Connector Hub: OCI Logging → Object Storage
resource "oci_sch_service_connector" "log_archival" {
  compartment_id = var.log_compartment_id
  display_name   = "audit-to-object-storage"
  state          = "ACTIVE"

  source {
    kind = "logging"
    log_sources {
      compartment_id = var.compartment_id
      log_group_id   = var.audit_log_group_id
    }
  }

  target {
    kind                       = "objectStorage"
    bucket                     = oci_objectstorage_bucket.log_archive.name
    namespace                  = data.oci_objectstorage_namespace.ns.namespace
    object_name_prefix         = "audit/{year}/{month}/{day}/"
    batch_rollover_time_in_ms  = 60000   # 60-second batches
    batch_rollover_size_in_mbs = 100
  }
}
```

**Locked retention rule** (via CLI — test in staging before locking; cannot be shortened after):
```bash
# Create 7-year locked retention rule
oci os retention-rule create \
  --namespace <ns> \
  --bucket-name "compliance-logs-prod" \
  --duration '{"timeAmount": 7, "timeUnit": "YEARS"}' \
  --time-rule-locked "2024-07-01T00:00:00Z"
# Once time-rule-locked date passes, rule cannot be removed until 7 years elapse per object
```

---

## Pattern 4: Private-Origin Static Asset Delivery via OCI CDN

**Object Storage (private) ↔ OCI CDN**

Use when: globally distributed static asset delivery (images, JS, CSS) with edge caching; bucket must stay private (no `access_type = "ObjectRead"`).

```hcl
# Bucket stays private — CDN is the only public face
resource "oci_objectstorage_bucket" "cdn_origin" {
  compartment_id = var.compartment_id
  name           = "cdn-assets-${var.env}"
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  access_type    = "NoPublicAccess"  # Private — CDN service principal has read access
}

# IAM policy: OCI CDN service reads from the bucket
resource "oci_identity_policy" "cdn_read" {
  compartment_id = var.compartment_id
  name           = "cdn-origin-read"
  statements = [
    "allow service cdn to read objects in compartment ${var.compartment_name} where target.bucket.name = 'cdn-assets-${var.env}'"
  ]
}
```

**OCI CDN distribution** (configure in OCI Console or via SDK — Terraform resource availability varies by OCI provider version):
- Origin type: Object Storage
- Origin bucket: `cdn-assets-${var.env}`
- Protocol: HTTPS
- Cache TTL: align with asset versioning strategy (e.g., 1 year for fingerprinted assets, 60 seconds for `latest/` prefix assets)

**Cache invalidation**:
```bash
# Invalidate specific path after asset update
oci cdn distribution create-invalidation \
  --distribution-id <ocid> \
  --items '[{"path": "/images/*"}]'
```
