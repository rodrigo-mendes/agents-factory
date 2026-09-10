# Object Storage — Neutral Category Specifics

Patterns for S3-compatible object storage. Vendor-specific config keys, EC profiles, and CLI live in `references/<vendor>-<version>.md`.

---

## Object Storage Model (Neutral)

| Concept | What to research per engine |
|---|---|
| Bucket | Top-level container; naming rules; per-bucket policy |
| Object | Immutable blob + metadata; key (path-like but flat) |
| Durability | Erasure coding (K+M) vs replication factor |
| Healing | Automatic repair of missing shards/replicas |
| Lifecycle | Automatic transition / expiration rules |
| S3 compatibility | Which S3 API operations are supported |

---

## Durability: Erasure Coding vs Replication (Neutral)

| Mechanism | How | Storage Overhead | Survives |
|---|---|---|---|
| Replication (N copies) | Store N full copies | N× | N-1 node losses |
| Erasure coding (K+M) | K data shards + M parity shards | (K+M)/K× | M shard/node losses |

Erasure coding is more storage-efficient at scale (e.g., EC 8+4 = 1.5× overhead survives 4 losses vs 3× replication surviving 2). The reference card gives the vendor's EC profile config and minimum node count.

---

## Write Quorum (Neutral)

- A write must reach a minimum number of shards/replicas before it's acknowledged
- If insufficient nodes are available, writes block or fail (fail-safe, not silent loss)
- Document the write-quorum requirement and behavior when nodes are down

---

## Bucket & Key Layout (Neutral)

Object storage has a flat namespace; keys simulate directories via prefixes:

```
Key structure: <entity-type>/<YYYY>/<MM>/<DD>/<entity-id>/<filename>
  → enables time-based lifecycle rules and prefix-scoped listing

Prefix distribution:
  - Avoid a single hot prefix for high-write workloads (e.g., date-only prefix sends all
    of today's writes to the same prefix range)
  - For high write rates, add a hash/random component early in the key
```

---

## Lifecycle Management (Neutral)

| Phase | Age | Action |
|---|---|---|
| Active | 0–30 days | Standard tier |
| Warm | 30–90 days | Transition to cheaper tier / compress |
| Cold | 90 days–1 year | Archive tier |
| Expired | > retention | Delete (if policy allows) |

Define lifecycle rules per bucket at creation — never leave storage to grow unbounded.

---

## S3 API Compatibility (Neutral)

Every engine in this family targets S3 API compatibility, but coverage varies:

- Document which S3 operations `TARGET_VERSION` supports (multipart upload, versioning, object lock, select, etc.)
- Document SDK compatibility (AWS SDK v2, boto3, s3cmd) tested against the engine
- Note any operations NOT supported — the reference card is authoritative

---

## HA Topologies (Neutral)

1. **Distributed erasure-coded cluster** — shards across nodes; automatic healing (MinIO distributed, Ceph)
2. **Multi-site replication** — active-active bucket sync across sites for DR
3. **Single node** — dev/test only; no durability against node loss

Document minimum node count for the chosen EC profile.

---

## Neutral KPIs

| Metric | Purpose | Alert When |
|---|---|---|
| Available capacity | Storage headroom | approaching limit |
| Object/request rate (GET/PUT/LIST) | Throughput baseline | anomaly |
| Request latency p99 | Performance | > SLA |
| Healing / rebuild status | Durability health | rebuild backlog after node loss |
| Failed requests (4xx/5xx) | Error signal | spike |
| Node/disk health | Cluster health | any offline |
| Replication lag (multi-site) | DR health | > threshold |

---

## Universal Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Object storage as mutable database | Version accumulation; wrong access pattern | Database for mutable data; object storage for blobs |
| No lifecycle policy | Unbounded cost | Lifecycle rules per bucket |
| Public bucket without justification | Data exposure | Private by default; presigned URLs |
| Millions of tiny objects | List overhead; poor EC efficiency | Aggregate into archives |
| Predictable keys for sensitive data | Enumeration attack | Opaque keys + deny ListBucket |
| Hot prefix for high write rate | Uneven load distribution | Hash component early in key |

---

## §Data Modeling

Full guidance: [data-modeling.md](./data-modeling.md). Cross-type principles: [shared modeling-principles](../../templates/platform-research/data-modeling-principles.md).

---

## Ecosystem Adjacencies (neutral; names in reference cards)

- S3-compatible CLI / SDK (aws-cli, mc, s3cmd, rclone)
- Backup / sync tooling (rclone, Velero for K8s PVC)
- Multi-site replication tooling
- Monitoring exporters (Prometheus per vendor)
- Gateway / access proxy
