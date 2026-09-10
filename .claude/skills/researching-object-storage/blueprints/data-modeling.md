# Object Storage Data Modeling

For S3-compatible object storage. Cross-type principles: [shared modeling-principles](../../templates/platform-research/data-modeling-principles.md).

---

## Bucket Design

```
Naming convention: <project>-<environment>-<data-type>
  Example: myapp-prod-user-uploads

One bucket per:
  - Security boundary (different access policies)
  - Lifecycle policy (different retention)
  - Data class (uploads vs backups vs logs vs artifacts)

Avoid: one giant bucket for everything (cannot apply differentiated policy)
```

---

## Key (Object Path) Design

```
Structure keys for lifecycle + listing efficiency:
  <entity-type>/<YYYY>/<MM>/<DD>/<entity-id>/<filename>

Benefits:
  - Time-based lifecycle rules match a date prefix
  - Prefix-scoped listing (list one day's objects)
  - Natural sharding by prefix

Hot-prefix avoidance (high write rate):
  Bad:  2024/01/15/...  (all today's writes hit one prefix range)
  Good: <hash-prefix>/2024/01/15/...  (distributes writes)
```

---

## Lifecycle Rules

| Phase | Age | Action |
|---|---|---|
| Active | 0–30 days | Standard tier |
| Warm | 30–90 days | Transition / compress |
| Cold | 90 days–1 year | Archive tier |
| Expired | > retention | Delete (if allowed) |

Define lifecycle at bucket creation. Consider legal/compliance retention (object lock / WORM) where required.

---

## Object Size Strategy

```
Many small objects (<1KB each):
  Problem: per-object overhead; list latency; poor erasure-coding efficiency
  Fix: aggregate into archives (tar, parquet, log bundles) before storing

Few large objects (GB+):
  Use multipart upload for reliability and parallelism
  Set appropriate part size (e.g., 64-128MB parts)
```

---

## Versioning & Immutability

- **Versioning**: keeps prior versions on overwrite/delete — protects against accidental loss but accumulates storage (pair with lifecycle to expire old versions)
- **Object lock (WORM)**: prevents deletion for a retention period — compliance use cases
- **Immutability principle**: treat objects as write-once; model updates as new objects + version, not in-place mutation

---

## Access Patterns

| Pattern | Design |
|---|---|
| Public read (CDN origin) | Bucket policy for public read on a specific prefix; front with CDN |
| Time-limited private access | Presigned URLs with expiry |
| Application-only access | IAM/policy-scoped credentials; no public access |
| Cross-account/tenant | Separate buckets or prefix-scoped policies + deny ListBucket across tenants |

---

## Object Storage Data Modeling Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| One bucket for all data classes | Cannot differentiate policy/lifecycle | Bucket per security/lifecycle boundary |
| Mutable-object workload | Version accumulation | Database for mutable data |
| No lifecycle | Unbounded cost | Lifecycle per bucket at creation |
| Millions of tiny objects | Overhead; poor EC | Aggregate into archives |
| Hot date-only prefix | Uneven write distribution | Hash component early in key |
| Predictable keys for sensitive objects | Enumeration | Opaque keys + deny ListBucket |
