# Graph Data Modeling

For `DATASTORE_TYPE=graph`. Platforms: Neo4j, JanusGraph, ArangoDB (multi-model), Nebula Graph.

---

## When to Use a Graph Database

Graph databases excel when:
- Relationships are first-class (not just foreign keys) — social networks, knowledge graphs, fraud detection
- Traversal queries dominate — "friends of friends", "path between A and B", "impact analysis"
- Relationship attributes matter — weight, timestamp, confidence score stored on the edge itself
- The relationship schema evolves organically — adding new relationship types without schema migration

Graph databases do NOT excel for:
- Tabular aggregations (SUM, GROUP BY across millions of records) → use RDBMS or columnar
- Simple key-value lookup with no relationship traversal → use key-value store
- Full-text search → use Elasticsearch alongside the graph

---

## Node and Relationship Design

### Node Design Rules

```
One label per primary entity type — avoid overusing labels as property values
  Good: (:User), (:Product), (:Category)
  Bad:  (:Entity {type: "User"}) — prevents index usage by label

Labels as facets are acceptable for orthogonal concerns:
  (:User:Admin) — a User who is also an Admin; both labels index-backed

Properties on nodes = attributes of the entity's identity:
  name, email, created_at, status
  Avoid storing large blobs (binary data, large text) in node properties
```

### Relationship Design Rules

```
Relationship types are ALL_CAPS_UNDERSCORE by convention:
  (:User)-[:FOLLOWS]->(:User)
  (:User)-[:PURCHASED]->(:Product)
  (:Product)-[:BELONGS_TO]->(:Category)

Properties on relationships = attributes of the connection itself:
  (:User)-[:PURCHASED {at: datetime(), amount: 29.99, quantity: 2}]->(:Product)
  Not: (:User)-[:PURCHASED]->(:Product {purchased_at: datetime()})  ← wrong: bought_at is about the purchase, not the product

Relationship direction is stored — choose direction that reflects the domain:
  (:User)-[:FOLLOWS]->(:User)     ← directed: A follows B
  (:User)-[:MARRIED_TO]-(:User)   ← undirected: use bidirectional or either direction consistently
  You can query against any direction; direction choice affects readability
```

---

## Cypher Schema Patterns (Neo4j)

### Constraint and Index Setup

```cypher
-- Uniqueness constraint (also creates an index)
CREATE CONSTRAINT user_id_unique FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT product_sku_unique FOR (p:Product) REQUIRE p.sku IS UNIQUE;

-- Range index for inequality/range queries
CREATE INDEX user_created_at FOR (u:User) ON (u.created_at);

-- Full-text index for text search
CREATE FULLTEXT INDEX product_description FOR (p:Product) ON EACH [p.description];

-- Composite index for multi-property lookup
CREATE INDEX user_email_status FOR (u:User) ON (u.email, u.status);
```

### Common Traversal Patterns

```cypher
-- 1. Simple relationship traversal: friends of a user
MATCH (u:User {id: $user_id})-[:FOLLOWS]->(friend:User)
RETURN friend.name, friend.id;

-- 2. Variable-length path: mutual friends (depth 2)
MATCH (u:User {id: $user_id})-[:FOLLOWS*1..2]->(other:User)
WHERE other.id <> $user_id
RETURN DISTINCT other.id, other.name;

-- 3. Shortest path between two nodes
MATCH path = shortestPath(
  (a:User {id: $user_a})-[:FOLLOWS*]-(b:User {id: $user_b})
)
RETURN path, length(path);

-- 4. Pattern matching for fraud detection (ring detection)
MATCH (a:Account)-[:TRANSFERS_TO]->(:Account)-[:TRANSFERS_TO]->(:Account)-[:TRANSFERS_TO]->(a)
RETURN a.id AS suspicious_account;
```

---

## Super-Node Mitigation

```
Detection:
MATCH (n) 
RETURN labels(n)[0] AS label, n.id AS id, count{ (n)--() } AS degree 
ORDER BY degree DESC LIMIT 20;

Super-node threshold: > 10,000 relationships for most graph DBs

Mitigation strategies:

1. Relationship type filtering (always first):
   -- Bad: MATCH (celeb:User)-[:FOLLOWS]->(f) WHERE f.country = 'BR'  (traverses ALL follows first)
   -- Good: MATCH (celeb:User)-[:FOLLOWS {country: 'BR'}]->(f)         (filter on relationship property)

2. Intermediate bucket nodes:
   -- Original: (:Celebrity)-[:POSTED]->(:Post)    (1M+ posts per celebrity)
   -- Bucketed: (:Celebrity)-[:HAS_BUCKET]->(:PostBucket {month: '2024-01'})-[:CONTAINS]->(:Post)

3. Paginated traversal (SKIP/LIMIT):
   MATCH (celeb:User {id: $id})-[:FOLLOWS]->(f)
   RETURN f.id SKIP $offset LIMIT 100;

4. Index-backed property filter before traversal:
   Always ensure the starting node lookup uses an indexed property
```

---

## Graph Modeling Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Using a node as a property (e.g., storing address as string instead of (:Address) node) | Cannot query by address components; no relationship to other entities sharing same address | Model Address as a node connected via [:LIVES_AT] |
| Relationship type as a property (`[:RELATED {type: "FOLLOWS"}]`) | Cannot use relationship type in Cypher WHERE clause efficiently; defeats index-free adjacency | Use distinct relationship types: `[:FOLLOWS]`, `[:BLOCKS]`, `[:MENTIONS]` |
| Traversal without depth bound (`*` or `*1..`) | Queries that might traverse the entire graph | Always bound: `*1..5`; use `shortestPath()` for known path queries |
| Storing large binary data in node properties | Graph store not designed for blobs → memory pressure | Store reference (URL/ID) in node; binary data in object storage |
| One massive graph for all data (no multi-tenancy) | Cross-tenant data visible; query performance degrades | Use separate databases per tenant, or add `tenant_id` property + index + filter every query |
