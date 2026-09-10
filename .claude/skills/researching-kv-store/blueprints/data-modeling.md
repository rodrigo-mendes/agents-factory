# Key-Value Data Modeling

For persistent key-value stores used as primary datastore. Cross-type principles: [shared modeling-principles](../../templates/platform-research/data-modeling-principles.md).

---

## Key Design Principles

```
Namespace keys hierarchically:
  Good: user:1234:profile, order:5678:items, session:abc:data
  Bad:  data, temp, x, u1234 (unclear, collision-prone)

Encode entity type + identity + attribute:
  <entity-type>:<entity-id>:<attribute>

Key length:
  Keep short — each key has memory overhead (per-key metadata)
  But not so short that keys become ambiguous

Composite keys for range scans (ordered KV like RocksDB/TiKV):
  <tenant>:<entity>:<timestamp> enables prefix range queries
  Order matters — most-selective prefix first
```

---

## Value Structure Selection

For structured KV stores (Redis-style), choose the value type by access pattern:

| Structure | Use Case | Access Pattern |
|---|---|---|
| String / bytes | Single value, counter, serialized object | GET/SET, atomic INCR |
| Hash / map | Object with fields (avoid full-object deserialization) | Field-level get/set |
| List | Queue, timeline, bounded history | Push/pop from ends, range |
| Set | Unique membership, tags | Add, membership test, set operations |
| Sorted set | Leaderboard, priority queue, time-ordered index | Range by score/rank |
| Stream / log | Append-only event log with consumer groups | Append, range read |

For opaque-byte KV stores (RocksDB, LMDB), the value is application-serialized — choose the serialization format (Protobuf, MessagePack, JSON) based on size and evolution needs.

---

## TTL Strategy (Primary Datastore)

Unlike caches, a primary KV datastore uses TTL only when expiration is a **business requirement**:

- Session data with a defined lifetime
- Rate-limit / quota counters that reset on a window
- Temporary tokens (password reset, email verification)

Never use TTL as an eviction crutch for a primary datastore — if you need eviction, the data is a cache (`researching-cache-store`).

---

## Access-Pattern-First Design

```
1. List all access patterns (from WORKLOAD_PROFILE)
2. For each: what is the lookup key? point lookup or range scan?
3. Design keys so the primary access pattern is a direct key lookup (O(1))
4. For secondary access patterns:
   - Ordered KV (RocksDB/TiKV): design composite key prefix for range scan
   - Redis: maintain a secondary index (sorted set of IDs by attribute)
5. Denormalize where a single logical read should be a single key fetch
```

---

## Secondary Index Patterns

KV stores lack native secondary indexes (except some). Application-maintained patterns:

| Pattern | How | Trade-off |
|---|---|---|
| Index key (Redis) | Sorted set / set mapping attribute → entity IDs | Extra write per index; must keep in sync |
| Composite key range (ordered KV) | Encode indexed attribute in key prefix | Only works for range/prefix queries |
| Duplicate data per query | Store the entity under multiple keys | Storage cost; write amplification |

Rule: every secondary index is application-maintained — document the write path that keeps it consistent.

---

## KV Data Modeling Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Generic / ambiguous keys | Collisions; unreadable | Namespaced hierarchical keys |
| Large serialized blobs as single value | Memory fragmentation; slow ops | Split into hash fields or object storage + reference |
| Storing relational data with app-side joins | N+1 key lookups | Denormalize for the read pattern |
| Unbounded key growth (per-event keys, no bound) | Memory exhaustion | Aggregate; bound cardinality; archive old data |
| Secondary index not updated transactionally with data | Index drift | Update index in the same write path (transaction / Lua script) |
