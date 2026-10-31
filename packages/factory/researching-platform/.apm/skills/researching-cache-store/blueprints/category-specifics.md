# Cache Store — Neutral Category Specifics

Patterns for in-memory ephemeral caches. Vendor-specific config keys and commands live in `references/<vendor>-<version>.md`.

---

## Cache Patterns (Vendor-Neutral)

### Cache-Aside (Lazy Loading)

```
Read path:
  1. Application reads from cache
  2. Cache miss → read from source of truth (DB)
  3. Write value to cache with TTL
  4. Return value

Write path:
  1. Application writes to DB
  2. Invalidate (or update) the cache entry

Trade-off: cache is optional; cold miss penalty acceptable
Use when: read-heavy; cache absence should not break the app
```

### Write-Through

```
Write path:
  1. Application writes to cache
  2. Cache synchronously writes to DB
  3. Ack to application only when both complete

Trade-off: strong consistency; higher write latency
Use when: cache absence would degrade reads significantly; DB writes are the bottleneck
```

### Write-Behind (Write-Back)

```
Write path:
  1. Application writes to cache
  2. Ack immediately
  3. Cache asynchronously flushes batches to DB

Trade-off: fast writes; potential data loss window
Use when: write throughput > DB capacity; brief inconsistency acceptable
```

### Refresh-Ahead

```
Read path:
  1. Application reads from cache
  2. If TTL is within refresh window (e.g., < 20% remaining) → async trigger refresh
  3. Return current cached value

Trade-off: extra background load; near-zero cache-miss latency
Use when: predictable hot keys; miss penalty unacceptable
```

---

## TTL Discipline

Every cache entry must have an explicit TTL rationale:

| TTL Class | Range | Use Case |
|---|---|---|
| Short (1–60s) | Sub-minute | Rate-limit counters, in-flight lookups |
| Medium (1–60min) | Minutes | User session, API response cache |
| Long (1–24h) | Hours | Reference data (country list, feature flags) |
| Very long (days) | Days | Rarely-changing catalog data with explicit invalidation on change |
| No TTL (dangerous) | ∞ | Never in a pure cache — always set TTL |

**Rule**: derive TTL from data change frequency + acceptable staleness window, not from arbitrary defaults.

---

## Eviction Policy Choice

When cache reaches memory limit, one of these policies triggers (vendor names differ):

| Policy | Behavior | Best For |
|---|---|---|
| LRU (Least Recently Used) | Evict entries not accessed recently | General-purpose caching |
| LFU (Least Frequently Used) | Evict entries with lowest access count | Long-tail access patterns; hot keys stay |
| Random | Evict random entry | Lowest overhead; when access patterns are uniform |
| TTL-only | Evict entries closest to TTL expiry | Predictable eviction; requires TTL on every key |
| No-eviction | Refuse new writes when full | ONLY appropriate for primary datastore mode (use `researching-kv-store`) |

**Trap**: some platforms default to `noeviction` — in cache mode, this means writes fail silently instead of evicting old entries. Always explicitly set a cache-appropriate eviction policy.

---

## Cache Stampede Mitigation

Problem: popular key expires → many concurrent misses → DB overwhelmed.

Neutral solutions:

1. **Probabilistic early expiration** — some fraction of requests treat the key as expired early to refresh it before the actual TTL
2. **Single-flight lock** — first miss acquires a lock; other requests wait for the first to populate
3. **Two-level TTL** — hard TTL and soft TTL; between soft and hard, return stale + trigger async refresh (stale-while-revalidate)
4. **Warmup on deploy** — pre-populate hot keys before serving traffic

---

## Neutral KPIs

| Metric | Purpose | Alert When |
|---|---|---|
| Cache hit ratio | Health signal | < workload's baseline (e.g., < 0.9 for high-read workload) |
| Evictions per second | Memory pressure | Sustained non-zero when TTL should be draining |
| Memory usage / max memory | Capacity | > 0.85 approaching limit |
| Connected clients | Connection pool health | approaching maxclients limit |
| Command latency p99 | Query health | > single-digit ms for in-memory cache |
| Replication lag (if applicable) | Replica health | > threshold (single-digit seconds) |

---

## HA Considerations for Caches

Cache HA is often **less critical** than for primary datastores because a cache miss is recoverable (fetch from source of truth). Options:

1. **No HA** — single instance; on failure, all traffic falls through to backend; acceptable if backend can handle the load
2. **Failover pair** — primary + replica; automatic failover; cache warm on failover if replica served as read-only shadow
3. **Cluster mode** — sharded across nodes; each shard has replicas; failure of one shard loses only that portion of keys

**Design principle**: size the backend datastore to handle full cache-miss traffic during cache outage. If it cannot, the "cache" has become load-bearing and requires HA + persistence — reconsider as primary datastore (`researching-kv-store`).

---

## Universal Anti-Patterns (Caches)

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| No TTL on cache entries | Stale data indefinitely; memory fills | Every entry gets TTL matched to data change rate |
| Cache without auth on network-accessible port | Anyone on network can flush / read | Enable auth per vendor reference card; restrict bind address |
| Assuming cache = primary datastore | On eviction, data is gone permanently | Route to `researching-kv-store` if data must survive eviction |
| Treating cache miss as an error | Overwhelms source of truth on cold start | Design app to gracefully handle miss; measure miss rate |
| Storing large objects (>1MB) in cache | Memory fragmentation; slow serialization | Store reference in cache, fetch full object from object storage |
| `KEYS *` (or equivalent full-scan) in production | Blocks single-threaded caches for seconds | Use vendor's cursor-based scan (SCAN in Redis, stats slabs in Memcached) |

---

## Ecosystem Adjacencies

Neutral list of adjacent tools (vendor-specific names in reference cards):

- Client-side connection pooler (Jedis pool, aiomcache, etc.)
- Server-side proxy / router (Twemproxy, KeyDB active-replica, Redis Cluster proxy)
- Cache warmup / prefetch tooling
- Monitoring exporters (Prometheus exporter per vendor)
- Backup/snapshot tooling (if persistence is used)
