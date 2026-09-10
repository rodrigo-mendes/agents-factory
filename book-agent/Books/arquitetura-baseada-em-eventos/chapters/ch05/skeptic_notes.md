## Skeptical Review — CQRS: Separating Reads and Writes
Reviewer profile: Rigorous technical skeptic
Date: 2026-09-01

---

### Command and Query Separation

> ⚠️ **Critical Note:** The prose states categorically that "the query path never touches the authoritative write store," yet Section "Consistency Between Write Side and Read Side" correctly advises to "keep the invariant-critical reads close to the write model." These two statements directly contradict each other. A senior architect reading Chapter 5 in sequence will internalize an absolute rule in the first section, then encounter a carve-out three sections later without acknowledgment that it reverses the earlier rule. This ambiguity can cause misapplication: teams may implement a strict "never read from the write store" policy and then be unable to serve the strongly-consistent reads their domain actually requires without a full rework.

**Severity:** blocking
**Suggested fix:** Remove the word "never" from the query-path description in Command and Query Separation and qualify the statement: "In the general case the query path reads from purpose-built read models; Section X identifies the exception for strongly-consistent, invariant-critical queries that legitimately stay on the write store." This acknowledges the hybrid reality from the outset and removes the contradiction.

---

### Read Models and Event-Driven Projections

> ⚠️ **Critical Note:** The prose says "Write a new projection, replay history through it, and you have a fully-populated read model without a risky data migration." This is true only when the event history is short, the event schemas have been kept stable, and projections do not depend on external state. In production systems: (1) events published years ago may carry different field names, missing fields, or obsolete semantics — requiring versioned upcasters before replay is correct; (2) replaying billions of events takes hours to days, which may be operationally unacceptable; (3) projections that call external services (pricing APIs, enrichment services) at projection time cannot be faithfully reconstructed because that external state may have changed or been decommissioned. Presenting rebuildability as an unqualified strength misleads the target audience about real operational costs.

**Severity:** important
**Suggested fix:** Add a paragraph after the "disposable and rebuildable" claim that scopes the guarantee: rebuildability holds when events carry self-contained, version-stable payloads and projections are pure functions of the event stream. Flag event schema evolution (and the need for upcasters), replay throughput limits at scale, and the anti-pattern of projections with external side effects as conditions that undermine the guarantee.

---

### Consistency Between Write Side and Read Side

> ⚠️ **Critical Note:** The prose characterizes replication lag as "milliseconds usually, seconds under load" — framing it as a narrow, recoverable window. This omits the failure-mode scenario that shapes SLA design: a crashed projection consumer, a poison-pill event causing repeated reprocessing, or a Kafka consumer-group rebalance can stall a projection for minutes or hours, not seconds. For a senior audience designing production SLAs and alerting strategies, the failure-mode tail matters more than the happy-path average. Quoting only the happy-path latency invites under-engineering of monitoring, dead-letter handling, and consumer health alerting.

**Severity:** important
**Suggested fix:** Extend the lag characterization to include the failure tail: "milliseconds in the steady state, seconds under load — but a stalled or crash-looping projection consumer can pause updates for minutes to hours, making projection-lag monitoring and alerting a first-class operational concern, not an afterthought."

---

### Command and Query Separation

> ⚠️ **Critical Note:** "The command path returns almost nothing to the caller; frequently just an acknowledgement or an identifier" is presented as an architectural fact rather than a contested design choice. Returning only an ID forces a mandatory second round-trip to retrieve the created or updated resource — a real latency and UX cost, especially over high-latency mobile or international connections. Many widely-deployed CQRS systems (including those built on Axon, MediatR, and similar frameworks) routinely return a result DTO from command handlers without violating CQRS semantics. The prose does not acknowledge this as a trade-off; it reads as a prescription.

**Severity:** important
**Suggested fix:** Reframe the statement as a common convention rather than a rule: "A common convention is to return only an identifier or acknowledgement from the command path; some teams return a lightweight result DTO to avoid an extra round-trip. Either is valid — the principle is that the command handler must not read from the query-side read model to compose its response."

---

### The Shape-Mismatch Problem

> ⚠️ **Critical Note:** "The naive fix is to keep bolting indexes and read replicas onto the single model. That buys time but not escape." This frames read replicas and materialized views as merely a stopgap, implying they are inadequate long-term solutions. For a significant class of real systems — moderate read/write ratios, bounded query diversity, predictable access patterns — a well-maintained read replica with a materialized view is a fully adequate permanent solution, not a stepping stone to CQRS. The prose does not acknowledge this, potentially pushing architects toward unnecessary complexity when the boring solution would suffice. This is in tension with the chapter's own "When CQRS Is Over-Engineering" section, which argues exactly the opposite.

**Severity:** important
**Suggested fix:** Qualify the claim: "For systems with diverse, unpredictable, or divergent query shapes, indexes and read replicas buy time but not escape. For systems with a stable, bounded set of queries, a carefully maintained read replica with a materialized view is often the correct permanent answer and should be evaluated before adopting CQRS."

---

### Command and Query Separation

> ⚠️ **Critical Note:** "Read traffic in most corporate systems dwarfs write traffic by an order of magnitude" is stated as a universal premise for the independent-scaling benefit. While this holds for typical OLTP applications with heavy reporting, it does not hold for write-heavy domains: IoT telemetry ingestion, financial tick data, audit and compliance logging, sensor pipelines, and content moderation queues are all corporate systems where writes dominate or balance reads. For a senior audience building across domains, accepting this as a universal axiom may lead them to cite a benefit that does not exist in their specific context.

**Severity:** minor
**Suggested fix:** Add a qualifier: "In most OLTP corporate systems, read traffic dwarfs write traffic by an order of magnitude — validating the independent-scaling benefit. Verify this ratio for your domain before treating it as given; write-heavy workloads such as IoT ingestion or financial tick data do not share this profile."

---

### The Shape-Mismatch Problem

> ⚠️ **Critical Note:** "The write side wants normalization" conflates a relational database modeling practice with a general architectural property of the write model. Many production write models are not relational at all: aggregate-per-document stores (MongoDB, DynamoDB) store the entire aggregate as a single document, which is denormalized by design; Event Sourcing (introduced next chapter) stores a stream of events, not a normalized table. For senior architects familiar with non-relational write stores, the framing that "write = normalized relational tables" introduces an implicit assumption that may not hold in their context and narrows the conceptual applicability of the shape-mismatch problem.

**Severity:** minor
**Suggested fix:** Replace "The write side wants normalization" with "The write side wants a structure optimized for enforcing invariants — typically normalized in a relational store, but potentially a single aggregate document or an event stream in other storage engines." This keeps the conceptual point without overfitting it to the relational case.

---

### Consistency Between Write Side and Read Side

> ⚠️ **Critical Note:** The "read-your-writes routing" mitigation — "Route a user's reads to the write model briefly after their command" — lists "reintroduces write-side read load" as its only cost. A more significant and often overlooked cost is that the write model and the query-path read model expose different shapes: the write model stores a normalized aggregate while the read model returns a denormalized DTO. If the routing layer must return the same DTO regardless of which store it consults, it must re-implement the projection logic inline — partially defeating the CQRS separation and duplicating business logic that can drift over time.

**Severity:** minor
**Suggested fix:** Add a second caveat to the read-your-writes routing row: "also requires the write store to produce the same response shape as the read model, or the client must handle two different DTO contracts — reintroducing coupling you aimed to eliminate."

---

## Summary
- Total notes: 8
- Blocking (inline callout): 1
- Important (collapsed): 4
- Minor (file only): 3

**Top 3 items requiring attention:**
1. [Command and Query Separation] Internal contradiction — "query path never touches write store" vs. "keep invariant-critical reads close to the write model" — blocking inconsistency that inverts the pattern's own guidance.
2. [Read Models and Event-Driven Projections] Replay rebuildability presented as unconditional — event schema evolution, replay throughput at scale, and side-effecting projections all undermine the guarantee without any caveat.
3. [Consistency Between Write Side and Read Side] Replication lag characterized by happy-path numbers only — failure-mode tail (minutes to hours from stalled consumers) is the operationally relevant figure for SLA and alerting design.
