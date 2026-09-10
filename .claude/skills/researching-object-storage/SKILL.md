---
name: researching-object-storage
description: "Researches self-managed S3-compatible object storage (MinIO, Ceph RGW, SeaweedFS, GarageHQ) into a hallucination-proof, version-absolute knowledge base covering installation, erasure-coding/replication HA, backup, upgrade, hardening, observability, and bucket/object data modeling (layout, lifecycle, S3 compatibility). Use when researching object storage the team will install and operate itself (not managed services like Amazon S3)."
argument-hint: "<platform> <version> [deployment=bare-metal|vm|container-compose|kubernetes-operator|hybrid] [depth=exhaustive] [iterations=5] (e.g. MinIO 2024 deployment=kubernetes-operator)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# Object Storage Research

## INPUT VARIABLES

- `PLATFORM_SOFTWARE`: MinIO | Ceph RGW | SeaweedFS | GarageHQ
- `TARGET_VERSION`: exact version (date-based for MinIO, semver for others)
- `DEPLOYMENT_MODEL`, `RESEARCH_DEPTH`, `MAX_ITERATIONS`: standard passthrough

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)**
- **[Category Specifics](./blueprints/category-specifics.md)** — Neutral object storage patterns (EC, buckets, lifecycle)
- **[Data Modeling](./blueprints/data-modeling.md)** — Bucket/key layout, lifecycle, S3 compatibility
- **[Reference Card Template](../../templates/platform-research/reference-card-template.md)** — Skeleton every per-vendor card follows (worked example: reference-card-example-kafka-3.7.md)
- **[Reference Cards](./blueprints/references/)**
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**
- **[Shared Output Template](../../templates/platform-research/output-format-base.md)**
- **[Shared Research Scope](../../templates/platform-research/research-scope-operations.md)**
- **[Shared Modeling Principles](../../templates/platform-research/data-modeling-principles.md)**

## Blueprints & Guardrails

### ✅ Always Do

- **Document the durability mechanism** — erasure coding (EC:K+M) vs replication — and how many node/disk failures it survives
- **Bucket layout + lifecycle rules from day one** — object storage grows unbounded without lifecycle
- **State S3 API compatibility level** — which operations are supported for `TARGET_VERSION`
- **Default to private buckets** — public exposure requires explicit justification
- **Label configs by `DEPLOYMENT_MODEL`**

### ⚠️ Ask First

- **Durability profile** — EC ratio (e.g., 4+2 vs 8+4) depends on node count and failure tolerance
- **Multi-site replication** — active-active vs DR-only
- **Workload** — many small objects vs few large objects (impacts EC efficiency)
- **`DEPLOYMENT_MODEL`** if unspecified

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Object storage as a mutable database | Objects are write-once; updates create versions that accumulate | Use a database for mutable data; object storage for immutable blobs |
| No lifecycle policy | Unbounded storage cost | Lifecycle rules per bucket at creation |
| Public bucket without justification | Data exposure | Private by default; presigned URLs for time-limited access |
| Millions of tiny objects (<1KB) | List overhead; poor EC efficiency | Aggregate into archives (tar/parquet) |
| Predictable keys for sensitive objects | Enumeration attack | Opaque/random keys + deny ListBucket |

## Research Scope

Shared: **[research-scope-operations.md](../../templates/platform-research/research-scope-operations.md)** §1–§12.

Object-storage-specific: **[category-specifics.md](./blueprints/category-specifics.md)**.

## Output Format

Base: **[output-format-base.md](../../templates/platform-research/output-format-base.md)**.

Save as `research_platform_{{PLATFORM_SOFTWARE}}_v{{TARGET_VERSION}}.md` in `StoryBeat/docs/`.

Conditional sections:
- **§K8s Kubernetes Deployment Blueprint** — when `DEPLOYMENT_MODEL=kubernetes-operator`
- **§Data Modeling** — always (bucket/key layout) — see [data-modeling.md](./blueprints/data-modeling.md)

## External Resources

| Engine | Primary Docs | K8s Operator | Release Notes |
|---|---|---|---|
| MinIO | min.io/docs | MinIO Operator | github.com/minio/minio/releases |
| Ceph (RGW) | docs.ceph.com | Rook (Ceph Operator) | docs.ceph.com/en/latest/releases |
| SeaweedFS | github.com/seaweedfs/seaweedfs/wiki | SeaweedFS Operator / Helm | github.com/seaweedfs/seaweedfs/releases |
| GarageHQ | garagehq.deuxfleurs.fr/documentation | Garage Helm | git.deuxfleurs.fr/Deuxfleurs/garage/releases |
