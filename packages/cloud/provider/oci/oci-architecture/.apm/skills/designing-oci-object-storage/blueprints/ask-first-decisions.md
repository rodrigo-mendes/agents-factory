# Ask First Decisions — OCI Object Storage

Three architectural crossroads that require business context before implementation. Present options with tradeoffs and wait for user decision — never assume.

---

## Decision 1: Storage Tier Strategy

**Ask before implementing**: "What is the expected data access frequency, and will any object need to be accessed within 31 days of upload?"

> ⚠️ `storage_tier` on the bucket is **immutable after creation**. Wrong tier selection requires `terraform destroy` + recreate with full data migration.

| Option | Terraform Config | Storage Cost | Access Cost | Best When |
|--------|-----------------|--------------|-------------|-----------|
| **Standard (fixed)** | `storage_tier = "Standard"` | ~$0.0255/GB/mo | None | Access > 1x/month, operational data |
| **Auto-Tiering** | `auto_tiering = "InfrequentAccess"` | Blended (Standard + IA) | Per-GB retrieval on IA reads | Unpredictable access patterns, mixed warm/cold objects |
| **Lifecycle → IA** | Lifecycle rule `INFREQUENT_ACCESS` | ~$0.0102/GB/mo after transition | Per-GB retrieval | Predictable aging (e.g., logs > 30 days) |
| **Archive (bucket)** | `storage_tier = "Archive"` | ~$0.0026/GB/mo | Restore + retrieval fees | Cold backups, compliance data > 90 days, no ad-hoc access |
| **Lifecycle → Archive** | Lifecycle rule `ARCHIVE` | Gradual reduction as objects age | Restore latency + fees | Mixed operational + archival in same bucket |

**Cost note**: InfrequentAccess has a **31-day minimum storage duration** per object — deleting before 31 days still incurs the full minimum charge. Archive has a **90-day minimum**. Verify current pricing at https://www.oracle.com/cloud/price-list/#pricing-storage.

**Terraform examples**:

```hcl
# Option A: Standard (fixed, immutable)
resource "oci_objectstorage_bucket" "standard" {
  storage_tier = "Standard"
  auto_tiering = "Disabled"
  # ...
}

# Option B: Auto-tiering on Standard bucket
resource "oci_objectstorage_bucket" "auto_tiered" {
  storage_tier = "Standard"
  auto_tiering = "InfrequentAccess"  # Disabled for Archive-tier buckets
  # ...
}

# Option C: Archive tier (immutable after creation)
resource "oci_objectstorage_bucket" "archive" {
  storage_tier = "Archive"
  auto_tiering = "Disabled"  # Incompatible with Archive
  # ...
}
```

---

## Decision 2: Data Protection Mechanism

**Ask before implementing**: "Is the requirement accidental-change recovery, regulatory immutability (WORM), or regional disaster recovery — or a combination?"

| Option | OCI Feature | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| **Versioning** | `versioning = "Enabled"` | Accidental overwrite/delete recovery | Storage cost (all versions retained), lifecycle complexity | Application assets, config objects, ML datasets |
| **Retention Rules** | `retention_rules {}` with locked duration | WORM compliance, tamper-proof records | Flexibility (locked rules cannot be shortened or removed) | Financial/healthcare audit logs, compliance records |
| **Cross-Region Replication** | `oci_objectstorage_replication_policy` | Regional DR, geographic redundancy | Async lag (eventual consistency), destination is read-only | DR targets, data residency compliance |
| **All Three** | Combined | Maximum protection | Complexity, 2x storage cost for replication | Production buckets with compliance + DR requirements |

**Terraform examples**:

```hcl
# Versioning — once Enabled, can only be Suspended (never returns to Disabled)
resource "oci_objectstorage_bucket" "versioned" {
  versioning = "Enabled"
  # ...
}

# Locked retention rule (test in staging BEFORE applying — cannot be shortened after locking)
resource "oci_objectstorage_bucket" "compliance" {
  # ...
}

resource "oci_objectstorage_object" "retention" {
  # Use OCI Console or CLI — Terraform support for retention rules is via SDK calls
}

# CLI: add time-based retention rule
# oci os retention-rule create \
#   --namespace <ns> --bucket-name <bucket> \
#   --duration '{"timeAmount": 7, "timeUnit": "YEARS"}' \
#   --time-rule-locked <ISO8601_date>  # Locks the rule at this date

# Cross-region replication — destination bucket must be pre-created
resource "oci_objectstorage_replication_policy" "dr" {
  bucket            = oci_objectstorage_bucket.primary.name
  namespace         = data.oci_objectstorage_namespace.ns.namespace
  name              = "dr-replication"
  destination_region_name = var.dr_region
  destination_bucket_name = var.dr_bucket_name
}
```

**Critical constraints**:
- Versioning: once `Enabled`, cannot return to `Disabled` — only `Suspended`. Plan irreversibility before enabling in production.
- Retention rules: locked rules cannot be shortened or removed until the duration elapses. Test lock in staging first.
- Replication: destination bucket `is_read_only = true` while policy is active. Replication does not copy existing objects — only post-policy-creation writes.

---

## Decision 3: Unauthenticated Access Pattern

**Ask before implementing**: "Who needs access — OCI compute/functions, internal human users, time-bounded external partners, or global end-users?"

| Requester Type | Option | Config | Best When |
|----------------|--------|--------|-----------|
| OCI compute/functions | IAM Dynamic Group + Instance Principal | `allow dynamic-group <DG> to manage objects in compartment <C>` | OCI-to-OCI access, no credentials in code |
| Internal human users | IAM User/Group Policy | `allow group Developers to use objects in compartment dev-workloads` | Human operator access, CI/CD with API keys |
| External partner (time-bound) | Pre-Authenticated Request (PAR) | `access_type = "ObjectRead"` + explicit `time_expires` | Third-party upload/download links |
| Global end-users (read-only) | OCI CDN over private bucket | CDN origin → private bucket via IAM service principal | High-traffic public media, static assets |
| Intentionally public dataset | Public Bucket | `access_type = "ObjectRead"` | Only when data is explicitly non-sensitive |

**PAR creation** (CLI — full URI shown only once, store in OCI Vault immediately):
```bash
# Minimum-scope PAR: single object, read-only, short expiry
oci os preauth-request create \
  --namespace <ns> \
  --bucket-name <bucket> \
  --name "partner-download-$(date +%Y%m%d)" \
  --access-type "ObjectRead" \
  --object-name "reports/q1-2024.pdf" \
  --time-expires "$(date -u -v+7d '+%Y-%m-%dT%H:%M:%SZ')"
# IMMEDIATELY store the returned access-uri in OCI Vault — it cannot be retrieved again
```

**Dynamic Group for Instance Principal** (no credentials in application code):
```hcl
resource "oci_identity_dynamic_group" "compute_dg" {
  compartment_id = var.tenancy_ocid
  name           = "compute-bucket-access"
  description    = "Compute instances that need Object Storage access"
  matching_rule  = "instance.compartment.id = '${var.app_compartment_ocid}'"
}

resource "oci_identity_policy" "compute_storage" {
  compartment_id = var.app_compartment_ocid
  name           = "compute-storage-access"
  description    = "Allow compute to read/write app bucket"
  statements = [
    "allow dynamic-group compute-bucket-access to manage objects in compartment app-workloads where target.bucket.name = '${var.bucket_name}'"
  ]
}
```
