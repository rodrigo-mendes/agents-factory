# Evaluation Scenarios — researching-platform-software (Orchestrator)

Tests **routing correctness only** — this skill delegates research to siblings. Content-level evaluation lives in each sibling's own `evaluation-scenarios.md`.

---

## Scenario 1 — Unambiguous Route

**Input**:
```
/researching-platform-software Kafka 3.7
```

**must_pass**:
- First line of response begins with `Routing "Kafka 3.7" → researching-streaming-broker`
- Invokes the sibling via `Skill({ skill: "researching-streaming-broker", ... })` OR unambiguously instructs the user to run `/researching-streaming-broker Kafka 3.7`
- Does NOT produce any research output in its own response body (no §Executive Summary, no config tables, no glossary)
- Passes all extra args (deployment, depth, iterations) through unchanged

**must_not**:
- Emit a research document
- Route Kafka to any sibling other than `researching-streaming-broker`
- Add default values not specified by the user (e.g., inject `depth=exhaustive` if omitted — pass through as-is)

---

## Scenario 2 — Ambiguous Route (Redis)

**Input**:
```
/researching-platform-software Redis 7.2
```

**must_pass**:
- Detects Redis as ambiguous and asks which role: cache-store / kv-store / coordination-analog
- Presents the 3 options with a short description each
- Does NOT proceed with a default route without confirmation
- After user answers "cache" → routes to `researching-cache-store`
- After user answers "kv" → routes to `researching-kv-store`
- After user answers "coordination" → routes to `researching-coordination-service`

**must_not**:
- Assume Redis is a cache without asking
- Route Redis to `researching-kv-store` silently just because Redis has persistence options
- Produce research output in this skill

---

## Scenario 3 — Ambiguous with Explicit Disambiguator

**Input**:
```
/researching-platform-software Redis 7.2 datastore-type=kv
```

**must_pass**:
- Reads the explicit `datastore-type=kv` disambiguator
- Routes directly to `researching-kv-store` without asking
- Passes `Redis 7.2` (and any other args) to the sibling

**must_not**:
- Ask for disambiguation when it was already provided
- Route to `researching-cache-store` (would ignore the user's explicit choice)

---

## Scenario 4 — Unknown Platform

**Input**:
```
/researching-platform-software Aerospike 7.0
```

**must_pass**:
- Does NOT invent a route
- Responds with the list of all 14 sibling skills and short descriptions
- Suggests top 2 candidates based on the platform name (Aerospike is a NoSQL K/V + document hybrid — plausible candidates: `researching-kv-store`, `researching-document-store`)
- Asks the user which sibling to route to OR proposes adding a row to `routing-decision-tree.md`

**must_not**:
- Guess a sibling silently
- Route to the "closest name match" without asking
- Refuse to help ("platform not supported") — offer the candidates

---

## Scenario 5 — Category-Crossing (PostgreSQL + pgvector)

**Input A**:
```
/researching-platform-software PostgreSQL 16
```

**must_pass**:
- Routes to `researching-rdbms` as default
- MAY note in the response that PostgreSQL can also be used as time-series (TimescaleDB) or vector store (pgvector), and offer to route to those siblings if that's the primary use case

**Input B**:
```
/researching-platform-software pgvector 0.7
```

**must_pass**:
- Routes to `researching-vector-store`
- Notes that pgvector is a PostgreSQL extension and the RDBMS operational concerns still apply — recommends also consulting `researching-rdbms` for base PostgreSQL operations

**Input C**:
```
/researching-platform-software TimescaleDB 2.14
```

**must_pass**:
- Routes to `researching-timeseries-db`
- Same note about RDBMS base + extension pattern

---

## Scenario 6 — Alias Handling

**Input**:
```
/researching-platform-software es 8.13
```

**must_pass**:
- Recognizes `es` as an alias for Elasticsearch (per `routing-decision-tree.md`)
- Routes to `researching-search-engine`

**Input**:
```
/researching-platform-software mongo 7.0
```

**must_pass**:
- Recognizes `mongo` as an alias for MongoDB
- Routes to `researching-document-store`

**must_not**:
- Fail to match because of case or the vendor prefix (`apache`, `hashicorp`) — matching is case-insensitive and strips known vendor prefixes
