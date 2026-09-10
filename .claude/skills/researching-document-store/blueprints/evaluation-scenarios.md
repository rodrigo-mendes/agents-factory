# Evaluation Scenarios — researching-document-store

Cross-vendor coverage required: at least one MongoDB scenario AND at least one non-MongoDB scenario (Couchbase or RavenDB).

---

## Scenario 1 — MongoDB on Kubernetes

**Input**:
```
/researching-document-store MongoDB 7.0 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Recommends Percona Operator for MongoDB or MongoDB Community/Enterprise Operator
- Documents 16MB BSON document size limit
- Recommends 3-member replica set minimum for production
- Documents write concern `w: majority` and read concern for critical data
- Documents oplog window sizing
- Data Modeling section: embed vs reference, ESR index rule, unbounded array anti-pattern
- Backup: Percona Backup for MongoDB (pbm) / mongodump
- References `blueprints/references/mongodb-7.0.md`

**must_not**:
- Recommend standalone deployment for production
- Omit the 16MB document size limit
- Present embedding as universally preferable without trade-offs

---

## Scenario 2 — Couchbase on VM

**Input**:
```
/researching-document-store Couchbase 7.6 deployment=vm depth=standard
```

**must_pass**:
- Uses Couchbase terminology: bucket, scope, collection, vBucket (1024 vBuckets), Data/Index/Query/Search services, N1QL/SQL++
- Documents Couchbase's multi-dimensional scaling (separate service nodes)
- Documents Cross Datacenter Replication (XDCR)
- Recommends Couchbase Autonomous Operator for K8s
- References `blueprints/references/couchbase-7.6.md`

**must_not**:
- Use MongoDB terminology (replica set, oplog, BSON) for Couchbase
- Reference mongodump / pbm for Couchbase (uses cbbackupmgr)
- Apply MongoDB's 16MB limit to Couchbase (different limit: 20MB)

---

## Scenario 3 — Data Modeling Focus

**Input**:
```
/researching-document-store MongoDB 7.0 (workload: e-commerce orders with line items and customer data)
```

**must_pass**:
- Recommends embedding line items in the order document (accessed together, bounded)
- Recommends referencing customer (accessed independently; extended reference pattern for cached display fields)
- Warns against unbounded arrays (e.g., all orders embedded in customer)
- Applies ESR rule to compound indexes

---

## Scenario 4 — Misuse: Relational Workload

**Input**:
```
/researching-document-store MongoDB 7.0 (workload: complex multi-table JOINs and ACID across entities)
```

**must_pass**:
- Notes that heavy multi-entity JOINs and cross-entity ACID are better served by an RDBMS
- Suggests `researching-rdbms` if the workload is fundamentally relational
- If staying with MongoDB, documents the `$lookup` cost and multi-document transaction limits
