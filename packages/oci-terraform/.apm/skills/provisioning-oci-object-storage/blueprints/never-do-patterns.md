# Never Do Patterns — OCI Object Storage

Seven prohibited patterns with side-by-side ❌ wrong / ✅ correct examples.

---

## Anti-Pattern 1: PAR with Excessive Scope and No Expiry Rotation

**Risk Level**: CRITICAL
**Why**: A PAR with `AnyObjectReadWrite` and a far-future `time_expires` grants unrestricted write access to the entire bucket. There is no mechanism to invalidate a PAR URL — only explicit deletion by `par_id` revokes it. If the `par_id` was not retained, the PAR is irrevocable until expiry.

❌ **Wrong**:
```bash
oci os preauth-request create \
  --namespace <ns> \
  --bucket-name <bucket> \
  --name "partner-access" \
  --access-type "AnyObjectReadWrite" \
  --time-expires "2099-12-31T23:59:59Z"  # Far-future, bucket-wide, write access
```

✅ **Correct**:
```bash
# Minimum scope: single object, read-only, short expiry window
oci os preauth-request create \
  --namespace <ns> \
  --bucket-name <bucket> \
  --name "partner-download-$(date +%Y%m%d)" \
  --access-type "ObjectRead" \
  --object-name "reports/q1-2024.pdf" \
  --time-expires "$(date -u -v+7d '+%Y-%m-%dT%H:%M:%SZ')"

# Store par_id and access-uri in OCI Vault IMMEDIATELY after creation
# To revoke before expiry:
oci os preauth-request delete \
  --namespace <ns> --bucket-name <bucket> --par-id <par_id>
```

**Blast radius if violated**: Full bucket data exfiltration, unauthorized object injection, potential bucket erasure, compliance violation.

---

## Anti-Pattern 2: Wildcard IAM Policy Without Resource Conditions

**Risk Level**: CRITICAL
**Why**: `manage object-family in tenancy` grants full CRUD to all buckets and objects in all compartments in the tenancy — enabling accidental or malicious cross-environment data destruction.

❌ **Wrong**:
```hcl
resource "oci_identity_policy" "developers" {
  statements = [
    "allow group Developers to manage object-family in tenancy"
    # Grants full control over ALL buckets in ALL compartments
  ]
}
```

✅ **Correct**:
```hcl
resource "oci_identity_policy" "developers" {
  statements = [
    # Scope to minimum compartment + verb + optional bucket condition
    "allow group Developers to use objects in compartment dev-workloads where target.bucket.name = 'app-assets-dev'",
    # For CI/CD that needs bucket listing only:
    "allow group CI-Pipeline to inspect buckets in compartment dev-workloads"
  ]
}
```

**IAM verb hierarchy** (least to most permissive):
- `inspect` — list bucket names and metadata; no object access
- `read` — GetObject, HeadObject, ListObjects
- `use` — read + write; cannot delete buckets or delete objects
- `manage` — full CRUD including bucket delete and object delete

**Blast radius if violated**: Cross-environment data deletion, data breach, compliance violation.

---

## Anti-Pattern 3: Versioned Bucket Without Lifecycle Rules on Previous-Object-Versions

**Risk Level**: HIGH
**Why**: Versioning preserves every overwritten or deleted object indefinitely. Without a DELETE rule on `previous-object-versions`, high-churn buckets accumulate 10–100x expected storage cost silently.

❌ **Wrong**:
```hcl
resource "oci_objectstorage_bucket" "versioned" {
  versioning = "Enabled"
  # No lifecycle policy — previous versions accumulate forever
}
```

✅ **Correct**:
```hcl
resource "oci_objectstorage_bucket" "versioned" {
  versioning = "Enabled"
}

resource "oci_objectstorage_object_lifecycle_policy" "versioned_policy" {
  bucket    = oci_objectstorage_bucket.versioned.name
  namespace = data.oci_objectstorage_namespace.ns.namespace

  rules {
    name        = "delete-old-versions"
    action      = "DELETE"
    is_enabled  = true
    target      = "previous-object-versions"
    time_amount = 30  # Retain previous versions 30 days for recovery window
    time_unit   = "DAYS"
  }

  rules {
    name        = "abort-stale-multipart"
    action      = "ABORT"
    is_enabled  = true
    target      = "multipart-uploads"
    time_amount = 7
    time_unit   = "DAYS"
  }
}
```

**Detection**:
```bash
# Check for versioned buckets without lifecycle policy
VERSIONING=$(oci os bucket get --namespace <ns> --bucket-name <bucket> --query 'data.versioning' --raw-output)
POLICY=$(oci os object-lifecycle-policy get --namespace <ns> --bucket-name <bucket> 2>&1)
# If VERSIONING = "Enabled" and POLICY shows empty rules array → anti-pattern present
```

---

## Anti-Pattern 4: Object Storage as Session State or Message Queue

**Risk Level**: HIGH
**Why**: Object Storage per-request latency is 50–200 ms — incompatible with session read SLAs (< 5 ms). There are no atomic compare-and-swap operations; concurrent read-modify-write patterns cause silent data loss (last-writer-wins). At > 100 requests/sec, API call costs exceed dedicated services.

❌ **Wrong**:
```python
# Using Object Storage as a session store — NEVER do this
import oci

object_storage = oci.object_storage.ObjectStorageClient(config)

def get_session(session_id: str) -> dict:
    # 50-200ms latency per call — breaks session SLAs
    response = object_storage.get_object(namespace, "sessions-bucket", session_id)
    return json.loads(response.data.content)

def set_session(session_id: str, data: dict):
    # No atomic write — race conditions in concurrent requests
    object_storage.put_object(namespace, "sessions-bucket", session_id, json.dumps(data))
```

✅ **Correct alternatives by use case**:

| Use Case | Correct OCI Service |
|----------|-------------------|
| Session state | OCI Cache (Redis-compatible, < 1 ms) |
| Task queues | OCI Queue |
| Event streams / fan-out | OCI Streaming |
| Distributed locks | OCI Cache (SETNX) or OCI NoSQL (conditional writes) |
| Application secrets/config | OCI Vault (secrets) |

```python
# Correct: OCI Cache (Redis-compatible) for session state
import redis

cache = redis.Redis(host=OCI_CACHE_ENDPOINT, port=6380, ssl=True)

def get_session(session_id: str) -> dict:
    data = cache.get(f"session:{session_id}")  # < 1 ms
    return json.loads(data) if data else {}

def set_session(session_id: str, data: dict, ttl_seconds: int = 3600):
    cache.setex(f"session:{session_id}", ttl_seconds, json.dumps(data))
```

---

## Anti-Pattern 5: Public Bucket for Non-Public Data

**Risk Level**: CRITICAL
**Why**: `access_type = "ObjectRead"` makes all objects in the bucket freely downloadable by any internet user. All future uploads — even accidental ones by authorized users — are immediately exposed without authentication.

❌ **Wrong**:
```hcl
resource "oci_objectstorage_bucket" "assets" {
  access_type = "ObjectRead"  # CRITICAL: exposes ALL objects publicly
  # Any sensitive file uploaded here is immediately world-readable
}
```

✅ **Correct** (private bucket + CDN origin for public delivery):
```hcl
# Bucket stays private
resource "oci_objectstorage_bucket" "assets" {
  access_type = "NoPublicAccess"  # Always explicit
}

# IAM policy: grant OCI CDN service principal read access
resource "oci_identity_policy" "cdn_read" {
  statements = [
    "allow service cdn to read objects in compartment ${var.compartment_name} where target.bucket.name = '${var.bucket_name}'"
  ]
}
# OCI CDN serves objects publicly; bucket remains private
```

**Detection**:
```bash
oci os bucket list --compartment-id <compartment_ocid> --all \
  --query 'data[?"public-access-type" != `"NoPublicAccess"`].name'
# Expected: empty array — any output indicates exposed buckets
```

**Cloud Guard**: "Bucket is publicly accessible" detector rule — HIGH severity. Enable at tenancy root and configure OCI Notifications alert routing.

---

## Anti-Pattern 6: Hardcoded OCI Namespace String

**Risk Level**: HIGH
**Why**: The OCI namespace is tenancy-specific and immutable. Hardcoding it makes modules non-portable and causes `terraform apply` failures in DR, test, or partner tenancies — breaking environment parity.

❌ **Wrong**:
```hcl
resource "oci_objectstorage_bucket" "bad" {
  namespace = "axbcdxxxxxx"  # Hardcoded — unique to one tenancy
  name      = var.bucket_name
  # ...
}
```

✅ **Correct**:
```hcl
data "oci_objectstorage_namespace" "ns" {
  compartment_id = var.compartment_id
}

resource "oci_objectstorage_bucket" "correct" {
  namespace = data.oci_objectstorage_namespace.ns.namespace
  name      = var.bucket_name
  # ...
}
```

**Blast radius if violated**: Module reuse across tenancies fails at plan time; DR drills fail; cross-tenancy CI/CD pipelines break silently.

---

## Anti-Pattern 7: Lifecycle Policy Resource With Incomplete Rule Set (Silent Rule Deletion)

**Risk Level**: HIGH
**Why**: `oci_objectstorage_object_lifecycle_policy` uses `CreateOrReplaceObjectLifecyclePolicy` semantics — the entire policy is replaced (not merged) on each `apply`. A resource declaring only one rule silently deletes all other rules on the next apply.

❌ **Wrong**:
```hcl
# Adding a new ABORT rule — this silently DELETES the existing DELETE rule
resource "oci_objectstorage_object_lifecycle_policy" "bad" {
  bucket    = oci_objectstorage_bucket.main.name
  namespace = data.oci_objectstorage_namespace.ns.namespace

  rules {
    name        = "abort-multipart-uploads"
    action      = "ABORT"
    is_enabled  = true
    target      = "multipart-uploads"
    time_amount = 7
    time_unit   = "DAYS"
  }
  # Any previously applied DELETE rule on previous-object-versions is now GONE
}
```

✅ **Correct** — always declare ALL rules in a single resource; use `dynamic "rules"` for conditional rules:
```hcl
resource "oci_objectstorage_object_lifecycle_policy" "correct" {
  bucket    = oci_objectstorage_bucket.main.name
  namespace = data.oci_objectstorage_namespace.ns.namespace

  rules {
    name        = "abort-incomplete-multipart-uploads"
    action      = "ABORT"
    is_enabled  = true
    target      = "multipart-uploads"
    time_amount = 7
    time_unit   = "DAYS"
  }

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

**Blast radius if violated**: Silent deletion of cost-control rules (orphaned multipart parts accumulate), retention rules (compliance gap), version cleanup rules (unbounded storage cost).
