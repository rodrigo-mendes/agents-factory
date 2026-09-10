# Evaluation Scenarios — researching-object-storage

Cross-vendor coverage required: at least one MinIO scenario AND at least one non-MinIO scenario (Ceph, SeaweedFS, or GarageHQ).

---

## Scenario 1 — MinIO on Kubernetes

**Input**:
```
/researching-object-storage MinIO 2024 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Recommends MinIO Operator
- Documents erasure coding (EC:K+M) with minimum 4 nodes; healing on node return
- Documents write quorum behavior
- Bucket layout + lifecycle rules; versioning + object lock
- S3 API compatibility level
- Security: private by default; restrict console; TLS
- References `blueprints/references/minio-2024.md`

**must_not**:
- Recommend object storage as a mutable database
- Omit lifecycle policy
- Default to public buckets

---

## Scenario 2 — Ceph RGW (RADOS Gateway)

**Input**:
```
/researching-object-storage Ceph RGW 18 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Documents Ceph's layered architecture: RADOS (object store) + OSDs + MON + MGR + RGW (S3 gateway)
- Recommends Rook operator for Kubernetes
- Documents CRUSH map for data placement; replication vs erasure-coded pools
- Notes Ceph is a broader storage platform (block + file + object); RGW is the object interface
- References `blueprints/references/ceph-rgw-18.md`

**must_not**:
- Describe Ceph as a single-purpose object store (it's multi-protocol)
- Use MinIO's env-var config model for Ceph
- Omit the OSD/MON/MGR components

---

## Scenario 3 — SeaweedFS (small-file optimized)

**Input**:
```
/researching-object-storage SeaweedFS 3.6 deployment=vm depth=standard
```

**must_pass**:
- Documents SeaweedFS's architecture: master + volume servers + filer; optimized for many small files (Haystack-inspired)
- Notes its strength for small-file workloads (differs from MinIO/Ceph)
- Documents replication settings (e.g., 001, 010, 100 replication codes)
- References `blueprints/references/seaweedfs-3.6.md`

**must_not**:
- Apply MinIO erasure-coding config as-is
- Omit the master/volume/filer separation

---

## Scenario 4 — Misuse: Database Workload

**Input**:
```
/researching-object-storage MinIO 2024 (workload: frequently updated records with queries by field)
```

**must_pass**:
- Flags that frequently-updated queryable records is a database workload, not object storage
- Recommends the appropriate database sibling (`researching-rdbms` / `researching-document-store`)
- Clarifies object storage is for immutable blobs, not mutable queryable records
