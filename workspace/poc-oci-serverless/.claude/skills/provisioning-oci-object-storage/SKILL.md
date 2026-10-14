---
name: provisioning-oci-object-storage
description: "Provisions OCI Object Storage buckets using Terraform OCI Provider ~> 8.0 (oracle/oci). Use when writing Terraform HCL for bucket creation, lifecycle policies, CMEK encryption, IAM access control, event-driven pipelines, or remote state backend configuration on OCI."
---

## Version Context

**Technology**: Terraform OCI Provider (`oracle/oci`)
**Target version**: `~> 8.0` (8.15.0 — released 2026-05-20)
**Terraform version**: `>= 1.9`
**OCI API**: Object Storage v20160918 (stable)
**Support status**: Active

**Important changes in 8.x**:
- Full `auto_tiering` support (`InfrequentAccess`) as first-class bucket property
- Complete lifecycle policy `target` support: `objects`, `previous-object-versions`, `multipart-uploads`
- OCI S3-compatible backend requires non-standard flags (`skip_region_validation`, `force_path_style = true`) and a Customer Secret Key — not an API key
- Instance Principal and Resource Principal as production-grade auth (no API keys in application code)

**Deprecated**: None in 8.x.

⚠️ **CRITICAL — Agent Warning**:
This skill targets Terraform OCI Provider `~> 8.0`. Reject patterns from `7.x` or earlier. Do not apply AWS S3 backend patterns — OCI S3-compatible backend has unique configuration requirements.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 8 mandatory patterns with Terraform HCL
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 4 architectural crossroads with tradeoff matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 7 anti-patterns with ❌ wrong / ✅ correct examples
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Event-driven, data lake, log archival, CDN patterns
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge, and misuse test cases
- **[Verification Loop](#verification-loop)** — OCI CLI validation commands
- **[Quick Reference](#quick-reference)** — Limits and critical values at a glance
- **[External Resources](#external-resources)** — Official OCI documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with Terraform HCL and OCI CLI examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns** (all 8 required — this domain is Complex tier):
- **Terraform provider constraint `~> 8.0` + OCI S3-compatible backend** — Pin provider to `oracle/oci ~> 8.0`; declare `terraform >= 1.9`; OCI S3 backend requires `skip_region_validation`, `skip_credentials_validation`, `force_path_style = true`, and a Customer Secret Key (not an API key).
- **Namespace data source in every module** — Always retrieve via `data.oci_objectstorage_namespace.ns`; hardcoding the namespace string breaks cross-tenancy deployments (DR, test, staging).
- **Explicit `access_type = "NoPublicAccess"`** — Declare explicitly in every `oci_objectstorage_bucket` resource; implicit default is not sufficient to prevent IaC drift-based exposure.
- **CMEK via OCI Vault for regulated data** — Set `kms_key_id` to an ACTIVE Vault master key for any bucket holding HIPAA, PCI-DSS, or GDPR-classified data; Oracle-managed keys (SSE-Oracle) do not satisfy BYOK requirements.
- **Service Gateway for private subnet access** — Route all compute/Function → Object Storage traffic through Service Gateway; NAT Gateway bills per-GB egress and exposes data paths to internet routing.
- **Lifecycle policy with ABORT rule and `depends_on`** — Every bucket needs an `oci_objectstorage_object_lifecycle_policy` with `action = "ABORT"` targeting `multipart-uploads` (7 days); add `depends_on = [oci_objectstorage_bucket.main]` — this resource uses `CreateOrReplace` semantics, always declare ALL rules in one resource.
- **`object_events_enabled = true` for processing pipelines** — Enable on any bucket that feeds a downstream pipeline; polling-based detection is inefficient and creates latency. Design consumers for at-least-once delivery.
- **Defined tags with `merge()` and `ignore_changes` for system tags** — Apply `environment`, `application`, `data-classification`, `cost-center` defined tags; use `ignore_changes = [defined_tags["Oracle-Tags.CreatedBy"]]` to prevent perpetual plan drift.

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Decision points** (ask before implementing):
- **Storage tier strategy** — Standard (fixed) vs. Auto-Tiering vs. Lifecycle-to-IA vs. Archive vs. Lifecycle-to-Archive; bucket `storage_tier` is **immutable after creation** — wrong choice requires destroy/recreate.
- **Data protection mechanism** — Versioning vs. Retention Rules vs. Cross-Region Replication; ask whether the requirement is accidental-change recovery, regulatory immutability (WORM), or regional DR.
- **Unauthenticated access pattern** — PAR vs. OCI CDN vs. IAM Dynamic Group vs. Public Bucket; never use `access_type = "ObjectRead"` for sensitive data.
- **Multi-environment state isolation** — Separate backends per env (hard isolation) vs. Terraform Workspaces (shared state bucket) vs. OCI Resource Manager (built-in locking); note OCI S3 backend has no native state locking — concurrent applies can corrupt state.

### 🚫 Never Do

For complete anti-patterns with side-by-side code, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Prohibited patterns**:
- **PAR with `AnyObjectReadWrite` and far-future `time_expires`** — CRITICAL: grants unrestricted bucket write access with no revocation path except explicit PAR deletion by ID.
- **Wildcard IAM policy (`in tenancy`) without resource conditions** — CRITICAL: grants full CRUD to all buckets in all compartments; scope to minimum compartment + bucket conditions.
- **Versioned bucket without lifecycle rule on `previous-object-versions`** — HIGH: unbounded version history accumulates silently; always pair `versioning = "Enabled"` with a DELETE rule on previous-object-versions.
- **Hardcoded OCI namespace string** — HIGH: namespace is tenancy-specific; hardcoding breaks cross-tenancy reuse (DR, test, staging); always use `data.oci_objectstorage_namespace.ns.namespace`.
- **`oci_objectstorage_object_lifecycle_policy` with incomplete rules** — HIGH: `CreateOrReplace` semantics silently delete all rules not declared in the Terraform resource; always declare ALL rules in one resource block.
- **Object Storage as session state or inter-service message queue** — HIGH: 50–200 ms per-object API latency is incompatible with session SLAs; no atomic compare-and-swap; use OCI Cache (Redis) or OCI Queue instead.
- **`access_type = "ObjectRead"` for non-public data** — CRITICAL: makes all objects freely downloadable to any internet user; future uploads are immediately exposed.

---

## Integration Patterns

For complete integration code, see [Integration Patterns](./blueprints/integration-patterns.md).

**Supported integrations**:
- **Object Storage ↔ OCI Events + Functions** — Event-driven processing pipeline (upload triggers virus scan / thumbnail generation / ETL)
- **Object Storage ↔ OCI Data Flow (Apache Spark)** — Data lake with Hive-style prefix partitioning and OCI Data Catalog
- **Object Storage ↔ OCI Connector Hub** — Centralized log archival (OCI Logging / Audit → Archive-tier bucket with CMEK + retention rules)
- **Object Storage ↔ OCI CDN** — Private-origin static asset delivery (bucket stays private; CDN provides public edge caching)

**Common problems**:
- **Problem**: Replication destination bucket is not writable after policy deletion → **Solution**: Confirm `is_read_only = false` after `oci os replication delete-replication-policy`; propagation may take 1–2 minutes.
- **Problem**: Object events not firing → **Solution**: Verify `object_events_enabled = true` on the bucket AND that an OCI Events rule exists matching `com.oraclecloud.objectstorage.createobject`.
- **Problem**: Function cannot access Object Storage in private subnet → **Solution**: Verify Service Gateway exists, route table has OCI service CIDR rule, and NSG allows egress TCP 443 to the OCI service CIDR.

---

## Verification Loop

Run after every Terraform apply or bucket configuration change:

### 1. Access Control Check
```bash
oci os bucket get \
  --namespace $(oci os ns get --query 'data' --raw-output) \
  --bucket-name <BUCKET_NAME> \
  --query 'data.{"access":\"public-access-type\","kms":"kms-key-id","events":"object-events-enabled","versioning":"versioning"}'
# Expected: access = "NoPublicAccess", kms = <ocid> or null, events = true/false per design
```

### 2. Lifecycle Policy Validation
```bash
oci os object-lifecycle-policy get \
  --namespace $(oci os ns get --query 'data' --raw-output) \
  --bucket-name <BUCKET_NAME>
# Expected: rules array includes at minimum an ABORT rule targeting "multipart-uploads"
```

### 3. Orphaned Multipart Upload Audit
```bash
oci os multipart list \
  --namespace $(oci os ns get --query 'data' --raw-output) \
  --bucket-name <BUCKET_NAME>
# Expected: empty data array, or all uploads within the ABORT window
```

### 4. Cloud Guard Security Posture
```bash
# No CLI equivalent — check in OCI Console:
# Cloud Guard → Problems → Resource Type: Bucket
# Expected: 0 HIGH/CRITICAL findings
```

**Troubleshooting**:
- `BucketNotFound` → verify namespace is correct (`oci os ns get`)
- `AuthorizationFailed` → IAM policy missing `read buckets` or `inspect object-family` for the calling principal
- `kms-key-id = null` on a regulated bucket → add `kms_key_id` in Terraform and re-apply; existing objects retain previous encryption (copy-to-self required to re-encrypt)

---

## Quick Reference

**Essential CLI commands**:
```bash
oci os ns get                                                    # Get namespace
oci os bucket list --compartment-id <ocid> --all                # List all buckets
oci os bucket get --namespace <ns> --bucket-name <name>          # Get bucket details
oci os preauth-request list --namespace <ns> --bucket-name <name> # List PARs
oci os replication list-replication-policies --namespace <ns> --bucket-name <name>
```

**Critical limits**:

| Resource | Limit | Scope |
|----------|-------|-------|
| Object size (PutObject) | 50 GiB | Per object |
| Object size (multipart) | 10 TiB | Per object |
| Retention rules per bucket | 100 | Per bucket |
| Pre-Authenticated Requests | No hard limit | Per bucket |
| InfrequentAccess minimum duration | 31 days | Per object |
| Archive minimum duration | 90 days | Per object |
| Archive restore SLA | 1 hour | Per restore request |
| OCI Audit retention | 90 days | Per tenancy |

---

## External Resources

### Official Documentation
- [OCI Object Storage Overview](https://docs.oracle.com/en-us/iaas/Content/Object/home.htm) (verified 2026-07-26)
- [Bucket API Reference](https://docs.oracle.com/iaas/api/#/en/objectstorage/latest/Bucket) (verified 2026-07-26)
- [Storage Tiers](https://docs.oracle.com/en-us/iaas/Content/Object/Concepts/understandingstoragetiers.htm) (verified 2026-07-26)
- [Object Lifecycle Policies](https://docs.oracle.com/iaas/api/#/en/objectstorage/latest/ObjectLifecyclePolicy) (verified 2026-07-26)
- [Pre-Authenticated Requests](https://docs.oracle.com/iaas/api/#/en/objectstorage/latest/PreauthenticatedRequest) (verified 2026-07-26)
- [Replication](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/usingreplication.htm) (verified 2026-07-26)
- [Versioning](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/usingversioning.htm) (verified 2026-07-26)
- [Retention Rules](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/usingretentionrules.htm) (verified 2026-07-26)

### Security & Best Practices
- [Object Storage Security Guide](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/objectstorage_security.htm) (verified 2026-07-26)
- [IAM Policy Reference for Object Storage](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/objectstoragepolicyreference.htm) (verified 2026-07-26)
- [OCI Vault Key Management](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm) (verified 2026-07-26)
- [Service Gateway](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/servicegateway.htm) (verified 2026-07-26)
- [Cloud Guard Overview](https://docs.oracle.com/en-us/iaas/Content/CloudGuard/Concepts/cloudguardoverview.htm) (verified 2026-07-26)

### Terraform Resource
- [oci_objectstorage_bucket](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/objectstorage_bucket) (verified 2026-07-26)
- [oci_objectstorage_object_lifecycle_policy](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/objectstorage_object_lifecycle_policy) (verified 2026-07-26)
