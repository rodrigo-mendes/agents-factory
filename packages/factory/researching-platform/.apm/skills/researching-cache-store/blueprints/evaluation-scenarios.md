# Evaluation Scenarios — researching-cache-store

Cross-vendor coverage required: at least one Redis scenario AND at least one non-Redis scenario (Memcached, KeyDB, or Dragonfly).

---

## Scenario 1 — Redis as Session Cache on VM

**Input**:
```
/researching-cache-store Redis 7.2 deployment=vm depth=standard
```

**must_pass**:
- Confirms Redis is deployed as cache (not primary datastore); references note the distinction with `researching-kv-store`
- Documents `maxmemory-policy: allkeys-lru` as cache-appropriate (NOT `noeviction`, which is for primary datastore)
- Includes `requirepass` (or ACL for 7.x) as mandatory in Security section
- Cache hit ratio KPI documented with alert threshold
- Cache stampede mitigation pattern present (probabilistic expiration or single-flight lock)
- References `blueprints/references/redis-7.2.md` for pinned values

**must_not**:
- Recommend `appendonly yes` + `noeviction` (that's the primary-datastore config; belongs in `researching-kv-store`)
- Omit auth configuration

---

## Scenario 2 — Memcached on Kubernetes

**Input**:
```
/researching-cache-store Memcached 1.6 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Uses Memcached terminology: slabs, items, LRU, expiration, `-m` (memory limit), `-c` (connections)
- Notes Memcached has NO native persistence (differs from Redis)
- Documents SASL auth (available since Memcached 1.5.14) — enabled with `-S` flag
- Includes Memcached-specific stats: `get_hits`, `get_misses`, `evictions`, `curr_items`, `bytes`
- Documents twemproxy or mcrouter as sharding proxy patterns
- References `blueprints/references/memcached-1.6.md`

**must_not**:
- Reference AOF/RDB (Redis-specific persistence) as Memcached options
- Recommend `requirepass` (Redis directive) for Memcached
- Include Redis Cluster hash-slot concept for Memcached

---

## Scenario 3 — Dragonfly Cross-Compat Test

**Input**:
```
/researching-cache-store Dragonfly 1.14 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Notes Dragonfly is Redis-protocol compatible (client libraries reuse) but has different internals (multi-threaded, no VM fork)
- Documents Dragonfly-specific advantages: memory efficiency, multi-threaded, no COW fork
- Uses Dragonfly's own config keys (--maxmemory, --cache_mode, --hz) — cites their docs
- References `blueprints/references/dragonfly-1.14.md`

**must_not**:
- Copy-paste Redis 7.2 config as if fully applicable — flag Dragonfly-specific differences
- Assume all Redis modules work on Dragonfly (some don't)

---

## Scenario 4 — Misuse: Primary Datastore Intent

**Input**:
```
/researching-cache-store Redis 7.2 (workload: never lose customer session data)
```

**must_pass**:
- Detects the intent conflict: "never lose data" is not a cache pattern
- Routes to `researching-kv-store` OR asks the user: "This describes a primary datastore, not a cache. Do you want researching-kv-store instead?"

**must_not**:
- Silently recommend AOF + noeviction under this skill (violates the cache-store scope)

---

## Scenario 5 — TTL Discipline Check

**Input**:
```
/researching-cache-store Redis 7.2 (workload: API response cache, no TTL specified)
```

**must_pass**:
- Insists on TTL policy in the output
- Provides a TTL selection framework based on data change frequency
- Warns that missing TTL turns cache into infinite-growth memory hog
