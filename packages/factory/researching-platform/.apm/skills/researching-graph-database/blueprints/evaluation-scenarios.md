# Evaluation Scenarios — researching-graph-database

Cross-vendor coverage required: at least one Neo4j scenario AND at least one non-Neo4j scenario (JanusGraph, ArangoDB, or Nebula).

---

## Scenario 1 — Neo4j on Kubernetes

**Input**:
```
/researching-graph-database Neo4j 5.20 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Documents Causal Cluster: core servers (Raft) + read replicas; causal consistency via bookmarks
- Recommends 3 core servers minimum for production
- Documents page cache sizing (`dbms.memory.pagecache.size`) as the key performance lever, separate from heap
- Data Modeling: node/edge granularity, property placement, super-node mitigation, indexed anchor lookup
- Bounded variable-length paths
- References `blueprints/references/neo4j-5.20.md`

**must_not**:
- Recommend unbounded traversals
- Omit index on anchor properties
- Confuse heap with page cache tuning

---

## Scenario 2 — JanusGraph (pluggable backend)

**Input**:
```
/researching-graph-database JanusGraph 1.0 deployment=vm depth=standard
```

**must_pass**:
- Documents JanusGraph as a graph layer over a pluggable storage backend (Cassandra/HBase/BerkeleyDB) + index backend (Elasticsearch/Solr/Lucene)
- Notes HA is inherited from the storage backend — cross-references `researching-wide-column-store` for Cassandra backend operations
- Uses Gremlin (TinkerPop) as the query language
- References `blueprints/references/janusgraph-1.0.md`

**must_not**:
- Describe JanusGraph as having native index-free adjacency like Neo4j (it's backend-dependent)
- Use Cypher (Neo4j language) for JanusGraph
- Omit the storage + index backend dependency

---

## Scenario 3 — ArangoDB (multi-model)

**Input**:
```
/researching-graph-database ArangoDB 3.12 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Notes ArangoDB is multi-model (document + graph + key-value) with AQL query language
- Documents cluster topology: Coordinators + DB-Servers + Agents (Agency = Raft-based config)
- Recommends ArangoDB Kubernetes Operator
- References `blueprints/references/arangodb-3.12.md`

**must_not**:
- Use Cypher or Gremlin (ArangoDB uses AQL)
- Describe it as graph-only

---

## Scenario 4 — Misuse: Aggregation Workload

**Input**:
```
/researching-graph-database Neo4j 5.20 (workload: daily revenue aggregation across 100M transactions)
```

**must_pass**:
- Flags that heavy tabular aggregation is not a graph strength
- Suggests `researching-rdbms` or `researching-columnar-analytics` for the aggregation workload
- If relationships matter, suggests keeping graph for traversal + separate store for analytics
