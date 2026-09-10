## Expert Review — Schema Evolution and Event Versioning
Reviewer profile: Senior practitioner, 10+ years, cloud-native microservices / corporate distributed systems
Date: 2026-09-01

---

### Backward and Forward Compatibility

> **Expert Note:** The prose states that full compatibility is "the target most mature registries default to." This is inaccurate and should be corrected before publication. Confluent Schema Registry — the de facto industry standard — defaults to **BACKWARD** compatibility, not FULL. AWS Glue Schema Registry also defaults to BACKWARD_ALL. FULL compatibility is an opt-in choice, not a default, precisely because it prohibits field removal and imposes constraints many teams cannot meet early in a product's lifecycle. Shipping the claim as written will cause practitioners to mis-configure registries, then be confused when the real defaults contradict the book.

**Integration level:** inline callout
**Priority:** high

---

### Schema Registry and Formats (Avro, JSON Schema, Protobuf)

> **Expert Note:** The prose explains that producers tag events with a schema ID, but omits the wire-format detail that makes this interoperable in practice. The Confluent wire format — now a de facto standard adopted by AWS MSK, Confluent Cloud, and most Kafka-adjacent tooling — is: `0x00` (magic byte) + 4-byte big-endian schema ID + serialized payload. Any non-Kafka consumer (an HTTP webhook bridge, a CDC pipeline, a legacy Java consumer) must understand this framing before it can even begin deserialization. Teams that treat the schema ID as an internal detail discover this the hard way when they onboard their first external or polyglot consumer. Architects should document this wire contract explicitly and test deserialization from at least one non-JVM client before go-live.

**Integration level:** collapsed block
**Priority:** medium

---

### Schema Registry and Formats (Avro, JSON Schema, Protobuf)

> **Expert Note:** The schema registry is mentioned as a build-time gate but its operational risk as a runtime dependency is not addressed. In production, every consumer performs a cache-miss lookup to the registry on first contact with a new schema ID. If the registry is unavailable, a consumer that has not yet cached that schema will fail to deserialize. The standard mitigation is a **local on-disk schema cache** that survives registry downtime — Confluent's Java client supports this via `SchemaRegistryClient` cache configuration, but it is not on by default. Teams that deploy the registry as a single instance without HA, or that do not seed the local cache before deploying consumers, treat a routine registry restart as a production incident. Treat the registry with the same availability SLA as the broker itself.

**Integration level:** collapsed block
**Priority:** medium

---

### Upcasting and Versioning of Persisted Events

> **Expert Note:** At production scale, an upcaster chain interacts dangerously with Event Sourcing aggregate reconstruction. Replaying a stream of 500k events through even two upcasters per event adds meaningful CPU and wall-clock time during cold restarts or aggregate rebuilds from scratch. The standard mitigation — **aggregate snapshots** — must be co-designed with the upcasting strategy: a snapshot stores a fully-upcasted, current-version aggregate state, so replays only process events *since* the last snapshot. If snapshotting is added as an afterthought after the upcaster chain is already in place, teams discover that old snapshots may themselves need versioning and upcasting, creating a recursive problem. Both versioning and snapshotting should be designed together from the start, not sequentially.

**Integration level:** collapsed block
**Priority:** medium

---

### Contracts, Consumer-Driven Contracts, and Governance

> **Expert Note:** The prose describes consumer-driven contracts conceptually but does not name the tooling, which matters for practitioners. **Pact** (pact.io) is the dominant open-source implementation: consumers write Pact files expressing the interactions they depend on, a **Pact Broker** (or PactFlow for SaaS) stores them, and the producer's CI pipeline runs `can-i-deploy` against the broker before any release. The critical production discipline that the prose does not mention is **pending pacts and WIP pacts** — Pact's mechanism for introducing new consumer contracts without immediately blocking the producer's build during the initial negotiation period. Without this mechanism, onboarding a new consumer becomes a coordinated freeze across both teams. Senior architects evaluating CDC should specifically assess whether their chosen tool supports this graduated rollout mode.

**Integration level:** collapsed block
**Priority:** medium

---

### Contracts, Consumer-Driven Contracts, and Governance

> **Expert Note:** The prose recommends "metric-backed deprecation" before retiring old schema versions, which is the right principle, but the measurement gap in practice is worth naming explicitly. Schema registry metrics tell you whether a schema *version* is being registered or fetched — they do not tell you whether a specific *field* within that version is being used by downstream consumers. A consumer might fetch schema v3 while only reading the `orderId` field and ignoring `couponCode`. If `couponCode` is the field you want to remove, fetch counts give you false confidence. The safest metric is **consumer-side field-level telemetry**: instrumented deserialization that logs which fields are accessed per consumer group. Few teams implement this, but those who have gone through a painful field removal incident almost always add it afterward.

**Integration level:** collapsed block
**Priority:** medium

---

### The Missing-Policy Pitfall

> **Expert Note:** The prose correctly identifies the absence of a declared policy as the most damaging mistake, but does not distinguish between two failure modes that require different remediation. The first is a greenfield team with no registry at all — the fix is straightforward: stand up a registry, pick BACKWARD, enforce it. The second, more painful case is a running system where events have been shipped for months without a registry, and a registry is now being retrofitted. In this case, the initial schema registration must be treated as a **compatibility baseline** audit, not a simple import: every existing schema must be manually reviewed before being registered, because the registry's first compatibility check will be against whatever you declare as v1. Teams that bulk-import existing schemas without review often discover that their "stable" schemas already contain patterns (undocumented required fields, implicit type coercions) that would fail a BACKWARD check, requiring immediate remediation of live consumers before the registry can be enforced.

**Integration level:** inline callout
**Priority:** high

---

### Backward and Forward Compatibility

> **Expert Note:** The prose covers what changes are safe and unsafe, but does not name the **Tolerant Reader** pattern — the consumer-side discipline that is the practical implementation of forward compatibility. A tolerant reader deserializes only the fields it explicitly needs and discards everything else without error, rather than failing on unrecognized or missing fields. This is the complementary discipline to additive-only producer changes: the producer adds fields safely only if consumers are written to tolerate them. In practice, many deserialization frameworks (especially Jackson with `FAIL_ON_UNKNOWN_PROPERTIES` defaulting to false in recent versions, or Avro's schema projection) implement this automatically, but teams using strict validation libraries or hand-written parsers must enforce it explicitly in code review. Naming the pattern gives teams a vocabulary to use in standards documents and review checklists.

**Integration level:** collapsed block
**Priority:** medium

---

## Summary
- Total notes: 8
- High priority (inline callout): 2
- Medium priority (collapsed block): 6
- Low priority (file only): 0

**Top 3 notes to integrate:**

1. [Backward and Forward Compatibility] Factual correction — registry defaults are BACKWARD, not FULL; Confluent and AWS Glue both confirm this
2. [The Missing-Policy Pitfall] Retrofitting a registry onto a running system is a distinct and more dangerous failure mode requiring a baseline audit, not just enforcement enablement
3. [Upcasting and Versioning of Persisted Events] Upcaster chains must be co-designed with aggregate snapshots from day one — adding snapshots after the fact creates a recursive versioning problem
