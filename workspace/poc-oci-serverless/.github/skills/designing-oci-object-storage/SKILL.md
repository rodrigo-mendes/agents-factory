---
name: provisioning-oci-object-storage
description: "Provisions OCI Object Storage buckets following Oracle Cloud best practices (API v20160918). Use when designing bucket architecture, configuring lifecycle policies, setting encryption and access controls, or building event-driven and data lake pipelines on OCI Object Storage."
---

## Function
Specialist in OCI Object Storage bucket architecture, security hardening, lifecycle management, and event-driven integration patterns for Oracle Cloud Infrastructure.

## Version Context

**Technology**: Oracle Cloud (OCI) Object Storage
**Target version**: API v20160918 / OCI Best Practices 2024
**Release date**: 2024
**Support status**: Active

**Important changes in this version**:
- Auto-tiering (`auto_tiering = "InfrequentAccess"`) is a first-class bucket property for automatic Standard ↔ InfrequentAccess transitions
- `bucket_scope` attribute (`NAMESPACE` vs `REGION`) for multi-tenancy predictable naming
- No per-object monitoring fee for auto-tiering (unlike AWS S3 Intelligent-Tiering)

**Deprecated**: None in this version.

⚠️ **CRITICAL — Agent Warning**:
This skill targets OCI Object Storage API v20160918. Reject any patterns referencing deprecated S3-compatibility shims or pre-2024 lifecycle rule `target` values.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 6 mandatory patterns with Terraform/CLI code
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 3 architectural crossroads with tradeoff matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 5 anti-patterns with ❌ wrong / ✅ correct examples
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Event-driven, data lake, log archival, CDN patterns
- **[Verification Loop](#verification-loop)** — OCI CLI validation commands
- **[Quick Reference](#quick-reference)** — Limits and critical values at a glance
- **[External Resources](#external-resources)** — Official OCI documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with Terraform HCL and OCI CLI examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns** (all 6 required — this domain is Complex tier):
- **Explicit `access_type = "NoPublicAccess"`** — Declare explicitly in every `oci_objectstorage_bucket` resource; implicit default is not sufficient to prevent IaC drift-based exposure.
- **CMEK via OCI Vault for regulated data** — Set `kms_key_id` to an ACTIVE Vault master key for any bucket holding HIPAA, PCI-DSS, or GDPR-classified data; Oracle-managed keys (SSE-Oracle) do not satisfy BYOK requirements.
- **Service Gateway for private subnet access** — Route all compute/Function → Object Storage traffic through Service Gateway; NAT Gateway bills per-GB egress and exposes data paths to internet routing.
- **Lifecycle policy with ABORT rule for multipart uploads** — Every bucket needs `action = "ABORT"` targeting `multipart-uploads` (recommended: 7 days); without it, orphaned parts accumulate silently at Standard tier rates.
- **`object_events_enabled = true` for processing pipelines** — Enable on any bucket that feeds a downstream pipeline; polling-based detection is inefficient and creates latency. Design consumers for at-least-once delivery.
- **Defined tags for cost allocation** — Apply `environment`, `application`, `data-classification`, and `cost-center` defined tags to every bucket; untagged buckets cannot be attributed in OCI Cost Analysis.

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Decision points** (ask before implementing):
- **Storage tier strategy** — Standard (fixed) vs. Auto-Tiering vs. Lifecycle-to-IA vs. Archive vs. Lifecycle-to-Archive; bucket `storage_tier` is **immutable after creation** — wrong choice requires destroy/recreate.
- **Data protection mechanism** — Versioning vs. Retention Rules vs. Cross-Region Replication; ask whether the requirement is accidental-change recovery, regulatory immutability (WORM), or regional DR.
- **Unauthenticated access pattern** — PAR vs. OCI CDN vs. IAM Dynamic Group vs. Public Bucket; never use `access_type = "ObjectRead"` for sensitive data.

### 🚫 Never Do

For complete anti-patterns with side-by-side code, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Prohibited patterns**:
- **PAR with `AnyObjectReadWrite` and far-future `time_expires`** — CRITICAL: grants unrestricted bucket write access with no revocation path except explicit PAR deletion by ID.
- **Wildcard IAM policy (`in tenancy`) without resource conditions** — CRITICAL: grants full CRUD to all buckets in all compartments; scope to minimum compartment + bucket conditions.
- **Versioned bucket without lifecycle rule on `previous-object-versions`** — HIGH: unbounded version history accumulates silently; always pair `versioning = "Enabled"` with a DELETE rule on previous-object-versions.
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
- [OCI Object Storage Overview](https://docs.oracle.com/en-us/iaas/Content/Object/home.htm)
- [Bucket API Reference](https://docs.oracle.com/iaas/api/#/en/objectstorage/latest/Bucket)
- [Storage Tiers](https://docs.oracle.com/en-us/iaas/Content/Object/Concepts/understandingstoragetiers.htm)
- [Object Lifecycle Policies](https://docs.oracle.com/iaas/api/#/en/objectstorage/latest/ObjectLifecyclePolicy)
- [Pre-Authenticated Requests](https://docs.oracle.com/iaas/api/#/en/objectstorage/latest/PreauthenticatedRequest)
- [Replication](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/usingreplication.htm)
- [Versioning](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/usingversioning.htm)
- [Retention Rules](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/usingretentionrules.htm)

### Security & Best Practices
- [Object Storage Security Guide](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/objectstorage_security.htm)
- [IAM Policy Reference for Object Storage](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/objectstoragepolicyreference.htm)
- [OCI Vault Key Management](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm)
- [Service Gateway](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/servicegateway.htm)
- [Cloud Guard Overview](https://docs.oracle.com/en-us/iaas/Content/CloudGuard/Concepts/cloudguardoverview.htm)

### Terraform Resource
- [oci_objectstorage_bucket](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/objectstorage_bucket)
- [oci_objectstorage_object_lifecycle_policy](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/objectstorage_object_lifecycle_policy)
