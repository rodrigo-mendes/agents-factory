# Reference Index — researching-object-storage

Index of the official sources and documentation categories already named in this skill's
[SKILL.md](../../SKILL.md) and blueprints. It adds no new facts.

> **Status:** no per-vendor reference cards (`<vendor>-<version>.md`) exist in this folder yet.
> Create them from the [reference card template](../../../researching-platform-software/blueprints/shared/reference-card-template.md)
> (worked example: [reference-card-example-kafka-3.7.md](../../../researching-platform-software/blueprints/shared/reference-card-example-kafka-3.7.md)).

## Official Sources (from SKILL.md → External Resources)

> Entries are copied verbatim. SKILL.md records no fetch date for any of them, so each is
> **(unverified)** until a dated fetch is recorded in a vendor reference card.

| Engine | Primary Docs | K8s Operator | Release Notes | Status |
|---|---|---|---|---|
| MinIO | min.io/docs | MinIO Operator | github.com/minio/minio/releases | (unverified) |
| Ceph (RGW) | docs.ceph.com | Rook (Ceph Operator) | docs.ceph.com/en/latest/releases | (unverified) |
| SeaweedFS | github.com/seaweedfs/seaweedfs/wiki | SeaweedFS Operator / Helm | github.com/seaweedfs/seaweedfs/releases | (unverified) |
| GarageHQ | garagehq.deuxfleurs.fr/documentation | Garage Helm | git.deuxfleurs.fr/Deuxfleurs/garage/releases | (unverified) |

## Documentation Categories

Categories this skill expects each vendor's docs to cover, taken from the headings of
[category-specifics.md](../category-specifics.md):

- Object Storage Model (Neutral)
- Durability: Erasure Coding vs Replication (Neutral)
- Write Quorum (Neutral)
- Bucket & Key Layout (Neutral)
- Lifecycle Management (Neutral)
- S3 API Compatibility (Neutral)
- HA Topologies (Neutral)
- Neutral KPIs
- Universal Anti-Patterns
- §Data Modeling
- Ecosystem Adjacencies (neutral; names in reference cards)

Data-modeling categories, from [data-modeling.md](../data-modeling.md):

- Bucket Design
- Key (Object Path) Design
- Lifecycle Rules
- Object Size Strategy
- Versioning & Immutability
- Access Patterns
- Object Storage Data Modeling Anti-Patterns

## Shared Sources

- [output-format-base.md](../../../researching-platform-software/blueprints/shared/output-format-base.md) — output skeleton; every claim cites an official docs URL with a date
- [research-scope-operations.md](../../../researching-platform-software/blueprints/shared/research-scope-operations.md) — shared research scope §1–§12
- [deployment-guides/](../../../researching-platform-software/blueprints/shared/deployment-guides/) — per-`DEPLOYMENT_MODEL` playbooks
- [evaluation-scenarios.md](../evaluation-scenarios.md) — behavioral test cases for this skill
