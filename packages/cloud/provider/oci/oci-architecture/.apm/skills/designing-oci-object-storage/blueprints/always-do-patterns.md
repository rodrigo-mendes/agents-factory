# Always Do Patterns — OCI Object Storage

Six mandatory patterns for every OCI Object Storage bucket provisioning task.

---

## 1. Explicit `access_type = "NoPublicAccess"` Declaration

**Why**: Buckets default to `NoPublicAccess` but IaC without the explicit declaration is misread by reviewers and can expose buckets during Terraform state drift scenarios.

```hcl
resource "oci_objectstorage_bucket" "example" {
  compartment_id = var.compartment_id
  name           = var.bucket_name
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  access_type    = "NoPublicAccess"  # ALWAYS explicit — never rely on default
}
```

**Verify**:
```bash
oci os bucket get --namespace <ns> --bucket-name <bucket> \
  --query 'data."public-access-type"'
# Expected: "NoPublicAccess"
```

---

## 2. Customer-Managed Encryption Key (CMEK) for Regulated Data

**Why**: Oracle-managed encryption (SSE-Oracle, AES-256) is applied by default but does not satisfy BYOK requirements for HIPAA, PCI-DSS, or GDPR-governed workloads. Key rotation must be scheduled in OCI Vault.

```hcl
resource "oci_objectstorage_bucket" "regulated" {
  compartment_id = var.compartment_id
  name           = var.bucket_name
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  access_type    = "NoPublicAccess"
  kms_key_id     = oci_kms_key.data_key.id  # Must be ACTIVE state with ENCRYPT+DECRYPT
}
```

**Key rotation policy** (add to vault key resource):
```hcl
resource "oci_kms_key" "data_key" {
  compartment_id      = var.compartment_id
  display_name        = "${var.bucket_name}-key"
  management_endpoint = var.vault_management_endpoint

  key_shape {
    algorithm = "AES"
    length    = 32
  }
}
```

**Verify**:
```bash
oci os bucket get --namespace <ns> --bucket-name <bucket> \
  --query 'data."kms-key-id"'
# Expected: non-null OCID

oci kms management key get --key-id <key_ocid> \
  --endpoint <vault_mgmt_endpoint> \
  --query 'data."lifecycle-state"'
# Expected: "ENABLED"
```

⚠️ **Caution**: Key pending-deletion period minimum is 7 days (set to 30 days for production). Accidental key deletion renders the bucket permanently inaccessible.

---

## 3. Service Gateway for Private Subnet Object Storage Access

**Why**: NAT Gateway bills per-GB egress and routes traffic through public internet paths. Service Gateway provides a free private path on Oracle's backbone.

```hcl
# Service Gateway — one per VCN
resource "oci_core_service_gateway" "sgw" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.main.id
  display_name   = "sgw-${var.vcn_name}"

  services {
    service_id = data.oci_core_services.all_oci_services.services[0].id
    # Use "All <Region> Services In Oracle Services Network"
  }
}

# Route rule in private subnet route table
resource "oci_core_route_table" "private" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.main.id

  route_rules {
    network_entity_id = oci_core_service_gateway.sgw.id
    destination       = data.oci_core_services.all_oci_services.services[0].cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
  }
}
```

**Verify** (from private subnet compute):
```bash
curl -I https://objectstorage.<region>.oraclecloud.com
# Expected: HTTP 200 or 401 — NOT a timeout
# Confirm in VCN Flow Logs: destination matches OCI service CIDR, not 0.0.0.0/0
```

---

## 4. Object Lifecycle Policy with ABORT Rule for Multipart Uploads

**Why**: Uncommitted multipart upload parts are billed at Standard tier rates indefinitely without an ABORT rule. Set `time_amount` higher than the maximum expected upload duration for your largest objects.

```hcl
resource "oci_objectstorage_object_lifecycle_policy" "bucket_policy" {
  bucket    = oci_objectstorage_bucket.example.name
  namespace = data.oci_objectstorage_namespace.ns.namespace

  rules {
    name        = "abort-incomplete-multipart-uploads"
    action      = "ABORT"
    is_enabled  = true
    target      = "multipart-uploads"
    time_amount = 7       # Set > maximum expected upload duration
    time_unit   = "DAYS"
  }
}
```

**For versioned buckets**, add this rule alongside the ABORT rule:
```hcl
  rules {
    name        = "delete-old-versions"
    action      = "DELETE"
    is_enabled  = true
    target      = "previous-object-versions"
    time_amount = 30
    time_unit   = "DAYS"
  }
```

**Verify**:
```bash
oci os multipart list --namespace <ns> --bucket-name <bucket>
# Expected: empty or all uploads younger than time_amount
```

---

## 5. `object_events_enabled = true` for Processing Pipelines

**Why**: Polling-based detection of new objects creates latency and wastes API call budget. OCI Events push-based notifications are free and decouple uploaders from consumers.

```hcl
resource "oci_objectstorage_bucket" "pipeline_source" {
  compartment_id      = var.compartment_id
  name                = var.bucket_name
  namespace           = data.oci_objectstorage_namespace.ns.namespace
  access_type         = "NoPublicAccess"
  object_events_enabled = true
}

# OCI Events rule routing to OCI Functions
resource "oci_events_rule" "on_object_create" {
  compartment_id = var.compartment_id
  display_name   = "on-upload-${var.bucket_name}"
  is_enabled     = true

  condition = jsonencode({
    eventType  = ["com.oraclecloud.objectstorage.createobject"]
    data       = { bucketName = [var.bucket_name] }
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

**Verify**:
```bash
oci os bucket get --namespace <ns> --bucket-name <bucket> \
  --query 'data."object-events-enabled"'
# Expected: true
```

⚠️ **Design for at-least-once delivery** — OCI Events does not guarantee strict ordering or exactly-once delivery. Function consumers must be idempotent.

---

## 6. Defined Tags for Cost Allocation and Governance

**Why**: Untagged buckets cannot be attributed to cost centers in OCI Cost Analysis. Cloud Guard flags untagged resources as governance violations.

```hcl
resource "oci_objectstorage_bucket" "example" {
  compartment_id = var.compartment_id
  name           = var.bucket_name
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  access_type    = "NoPublicAccess"

  defined_tags = {
    "Operations.Environment"        = var.environment          # prod | staging | dev
    "Operations.Application"        = var.application_name
    "Operations.DataClassification" = var.data_classification  # public | internal | confidential | restricted
    "Finance.CostCenter"            = var.cost_center
  }
}
```

**Enforce via OCI Tag Defaults** on the compartment to auto-apply required tags to all new buckets:
```bash
oci iam tag-default create \
  --compartment-id <compartment_ocid> \
  --tag-definition-id <tag_def_ocid> \
  --value "prod" \
  --is-required true
```

**Verify**: OCI Cost Analysis → filter by `tag key = Operations.Application`. Cloud Guard → 0 untagged bucket findings.
