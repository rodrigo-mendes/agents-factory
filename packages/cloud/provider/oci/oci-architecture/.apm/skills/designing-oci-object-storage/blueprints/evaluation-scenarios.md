# Evaluation Scenarios — designing-oci-object-storage

## Scenario 1: Canonical — Storage Tier Selection

```json
{
  "skills": ["designing-oci-object-storage"],
  "query": "We need to store application logs on OCI Object Storage. Logs are queried frequently for the first 30 days, occasionally for 31–90 days, and almost never after 90 days. We want to minimize cost. What storage tier strategy should we use?",
  "expected_behavior": [
    "Does NOT recommend Auto-Tiering for this pattern — Auto-Tiering transitions between Standard and InfrequentAccess only; it does not transition to Archive",
    "Recommends Standard tier bucket with a lifecycle policy: transition to InfrequentAccess at 31 days, transition to Archive at 91 days",
    "Warns that bucket storage_tier is IMMUTABLE after creation — standard bucket + lifecycle rules is the correct approach, not an Archive-tier bucket from the start",
    "Notes that InfrequentAccess has a 31-day minimum storage duration (objects deleted or transitioned before 31 days are billed for 31 days)",
    "Notes that Archive has a 90-day minimum storage duration and a 1-hour restore SLA",
    "Asks whether restore latency is acceptable for the 90+ day tier before finalising the Archive recommendation"
  ]
}
```

## Scenario 2: Canonical — Versioning vs Retention Rules vs Replication

```json
{
  "skills": ["designing-oci-object-storage"],
  "query": "We store financial reports in an OCI Object Storage bucket. Requirements: (a) recover from accidental deletion or overwrite within 90 days, (b) keep records for 7 years with WORM guarantees for audit, (c) have a copy in another OCI region for DR. Which data protection mechanism covers each requirement?",
  "expected_behavior": [
    "Maps (a) to versioning: previous-object-versions allow restore; pairs versioning with a lifecycle DELETE rule on previous-object-versions to bound storage growth",
    "Maps (b) to a locked retention rule with duration = 7 YEARS; warns that time-rule-locked makes the rule irrevocable until the duration elapses per object — must be tested in staging before applying to production",
    "Maps (c) to oci_objectstorage_replication_policy pointing to a pre-created destination bucket in the DR region; notes replication is asynchronous (RPO > 0) and warns that for zero-RPO the application must dual-write",
    "Notes that versioning + locked retention rule + replication can coexist on the same bucket",
    "Does NOT recommend using PAR or CDN for any of these requirements — they are access patterns, not data protection mechanisms"
  ]
}
```

## Scenario 3: Edge — PAR vs OCI CDN vs Public Bucket for Unauthenticated Access

```json
{
  "skills": ["designing-oci-object-storage"],
  "query": "We host a static marketing website on OCI Object Storage. Assets must be publicly readable. A developer suggests setting access_type = 'ObjectRead' on the bucket. Is that appropriate?",
  "expected_behavior": [
    "Accepts access_type = 'ObjectRead' only if ALL objects in the bucket are intentionally public and non-sensitive — marketing assets with no PII qualify",
    "Warns that any future upload to the bucket is immediately publicly readable with no per-object access control; recommends confirming that the bucket will never hold sensitive data",
    "Recommends OCI CDN as the preferred pattern for public static sites: bucket stays private (NoPublicAccess), CDN provides edge caching and the public-facing URL, reducing origin egress costs",
    "Notes that PAR is not appropriate for a full public website — PARs are per-object or per-prefix URLs and are not a CDN replacement",
    "Asks whether caching, custom domain, or geo-distribution requirements exist — if yes, OCI CDN is clearly the better choice",
    "Flags access_type = 'ObjectRead' for non-public data as the Never Do pattern in the skill"
  ]
}
```

## Scenario 4: Edge — Event-Driven Pipeline with Object Storage

```json
{
  "skills": ["designing-oci-object-storage"],
  "query": "An OCI Function needs to process every file uploaded to a bucket (virus scan + ETL). A developer proposes polling the bucket on a timer every 5 minutes. Should we approve this design?",
  "expected_behavior": [
    "Rejects polling: 5-minute polling introduces up to 5-minute processing latency, wastes compute, and creates unnecessary OCI CLI/SDK API calls against the Object Storage list endpoint",
    "Recommends event-driven: set object_events_enabled = true on the bucket, create an OCI Events rule matching com.oraclecloud.objectstorage.createobject, route to OCI Functions",
    "Notes that the Function consumer must be designed for at-least-once delivery (OCI Events guarantees at-least-once, not exactly-once) — ETL must be idempotent",
    "Recommends a separate destination bucket for processed output to prevent the output write from triggering another event loop",
    "Asks whether the function needs to handle createobject only or also overwriteobject and multipart-upload events"
  ]
}
```

## Scenario 5: Misuse — Object Storage as Session Cache or Message Queue

```json
{
  "skills": ["designing-oci-object-storage"],
  "query": "A team wants to use Object Storage as a shared session store between OCI Function instances (write session on login, read on each request) and also as a work-item queue (writers put objects, readers list and delete). Should we approve?",
  "expected_behavior": [
    "Rejects Object Storage as session store: per-object API latency is 50–200 ms — incompatible with typical < 10 ms session read SLAs; recommends OCI Cache (Redis-compatible) for sub-millisecond session access",
    "Rejects Object Storage as a message queue: no atomic compare-and-swap, no visibility timeout, no dead-letter support; concurrent readers listing and deleting the same object leads to race conditions and lost work items; recommends OCI Queue or OCI Streaming",
    "Notes that Object Storage list operations are eventually consistent — a reader may not immediately see an object written by another instance",
    "Flags both patterns as Never Do in the skill: Anti-Pattern 3 (Object Storage as session state or message queue)",
    "Does NOT suggest 'it could work with retry logic' — the fundamental latency and consistency model makes it structurally unsuitable for both use cases"
  ]
}
```
