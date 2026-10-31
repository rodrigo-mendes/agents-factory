# Always Do Patterns — OCI Object Storage

Eight mandatory patterns for every OCI Object Storage bucket provisioning task using Terraform OCI Provider `~> 8.0`.

---

## 1. Terraform Configuration Block with OCI Provider Constraint

**Why**: Pins to the `8.x` series, blocking unreviewed `9.0` breaking changes. `>= 1.9` enables `check` blocks for post-apply assertions. The OCI S3-compatible backend is distinct from AWS S3 — omitting `skip_region_validation` and `force_path_style = true` causes silent `terraform init` failures.

```hcl
terraform {
  required_version = ">= 1.9"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 8.0"
    }
  }

  # OCI Object Storage S3-compatible backend
  # Requires OCI Customer Secret Key (NOT API key) for credentials
  backend "s3" {
    bucket                      = "terraform-state-bucket"
    key                         = "prod/object-storage/terraform.tfstate"
    region                      = "us-ashburn-1"
    endpoint                    = "https://<namespace>.compat.objectstorage.us-ashburn-1.oraclecloud.com"
    skip_region_validation      = true
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    force_path_style            = true
    encrypt                     = true
    # AWS_ACCESS_KEY_ID     → OCI Customer Secret Key: Access Key
    # AWS_SECRET_ACCESS_KEY → OCI Customer Secret Key: Secret Key
  }
}

# Production: Instance Principal (no private keys in code or CI/CD)
provider "oci" {
  region = var.oci_region
  auth   = "InstancePrincipal"
}
```

**Verify**:
```bash
terraform init
# Expected: "Terraform has been successfully initialized!"
terraform version
# Expected: Terraform v1.9.x or higher, + provider oracle/oci v8.x.x
```

⚠️ Customer Secret Key is generated in OCI Console → Profile → Customer Secret Keys. It is distinct from OCI API keys and shown only once — store immediately in OCI Vault.

---

## 2. Namespace Data Source (Required in Every Module)

**Why**: The OCI namespace is a tenancy-scoped, system-assigned string required by every bucket and object API call. Hardcoding it makes modules non-portable across tenancies (DR, test, staging). Always retrieve dynamically.

```hcl
# Required in every module managing Object Storage resources
data "oci_objectstorage_namespace" "ns" {
  compartment_id = var.compartment_id
}

# Use in every dependent resource:
resource "oci_objectstorage_bucket" "main" {
  namespace = data.oci_objectstorage_namespace.ns.namespace
  # ...
}

resource "oci_objectstorage_object_lifecycle_policy" "main" {
  namespace = data.oci_objectstorage_namespace.ns.namespace
  # ...
}
```

**Verify**:
```bash
oci os ns get --query 'data' --raw-output
# Returns the namespace string for the authenticated tenancy
```

---

## 3. Explicit `access_type = "NoPublicAccess"` Declaration

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

## 4. Customer-Managed Encryption Key (CMEK) for Regulated Data

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

## 5. Service Gateway for Private Subnet Object Storage Access

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

## 6. Object Lifecycle Policy with ABORT Rule for Multipart Uploads

**Why**: Uncommitted multipart upload parts are billed at Standard tier rates indefinitely without an ABORT rule. Set `time_amount` higher than the maximum expected upload duration for your largest objects.

> **Critical**: `oci_objectstorage_object_lifecycle_policy` uses `CreateOrReplaceObjectLifecyclePolicy` semantics — every `apply` replaces the entire policy. Always declare ALL rules in a single resource. Use `dynamic "rules"` blocks for conditional rules.

```hcl
resource "oci_objectstorage_object_lifecycle_policy" "main" {
  bucket    = oci_objectstorage_bucket.main.name
  namespace = data.oci_objectstorage_namespace.ns.namespace

  # Rule 1: ABORT orphaned multipart uploads (required on every bucket)
  rules {
    name        = "abort-incomplete-multipart-uploads"
    action      = "ABORT"
    is_enabled  = true
    target      = "multipart-uploads"
    time_amount = 7       # Set > maximum expected upload duration
    time_unit   = "DAYS"
  }

  # Rule 2: Cleanup previous versions (versioned buckets only)
  dynamic "rules" {
    for_each = var.enable_versioning ? [1] : []
    content {
      name        = "delete-previous-versions"
      action      = "DELETE"
      is_enabled  = true
      target      = "previous-object-versions"
      time_amount = 90
      time_unit   = "DAYS"
    }
  }

  depends_on = [oci_objectstorage_bucket.main]
}
```

**Verify**:
```bash
oci os multipart list --namespace <ns> --bucket-name <bucket>
# Expected: empty or all uploads younger than time_amount
oci os object-lifecycle-policy get --namespace <ns> --bucket-name <bucket>
# Expected: rules array includes ABORT rule targeting "multipart-uploads"
```

---

## 7. `object_events_enabled = true` for Processing Pipelines

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

## 8. Defined Tags with `merge()` and `ignore_changes` for System Tags

**Why**: Untagged buckets cannot be attributed to cost centers in OCI Cost Analysis. Cloud Guard flags untagged resources as governance violations. Oracle auto-applies `Oracle-Tags.CreatedBy` and `Oracle-Tags.CreatedOn` on creation — without `ignore_changes`, every `terraform plan` shows perpetual diff.

```hcl
locals {
  common_defined_tags = {
    "${var.tag_namespace}.Environment"  = var.environment
    "${var.tag_namespace}.Application"  = var.application_name
    "${var.tag_namespace}.CostCenter"   = var.cost_center
    "${var.tag_namespace}.DataClass"    = var.data_classification
  }
}

resource "oci_objectstorage_bucket" "main" {
  compartment_id = var.compartment_id
  name           = var.bucket_name
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  access_type    = "NoPublicAccess"

  defined_tags  = merge(local.common_defined_tags, var.extra_defined_tags)
  freeform_tags = { "managed-by" = "terraform", "owner" = var.owner }

  lifecycle {
    prevent_destroy = true  # Require explicit override for production
    ignore_changes  = [defined_tags["Oracle-Tags.CreatedBy"], defined_tags["Oracle-Tags.CreatedOn"]]
  }
}
```

**Verify**: OCI Cost Analysis → filter by tag key `Environment`. Cloud Guard → 0 untagged bucket findings.
