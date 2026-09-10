## Expert Review — CQRS — Separating Reads and Writes
Reviewer profile: Senior practitioner, 10+ years, cloud-native microservices / corporate distributed systems
Date: 2026-09-01

---

### Read Models and Event-Driven Projections

> **Expert Note:** The prose correctly presents read-model rebuildability as a practical advantage, but omits the operational cost that surprises every team the first time they exercise it in production. Replaying millions of events through a projection is not instantaneous — a mature event log can contain hundreds of millions of events, and a naive single-threaded replay can take hours or days. Production-grade systems handle this with snapshot checkpoints (periodic materialized snapshots of the projection state at a given event position), partitioned parallel replay across event-stream segments, and a "shadow projection" strategy: the new projection is built on the side while the old one continues serving traffic, and traffic is cut over only when the shadow reaches the live position. Teams that treat "just replay from the beginning" as a cost-free escape hatch discover the hard way that it is a maintenance operation requiring planning, capacity, and a tested runbook.

**Integration level:** inline callout
**Priority:** high

---

### Read Models and Event-Driven Projections

> **Expert Note:** Projection versioning is the quietly dangerous part of long-running CQRS systems. When a projection's logic changes — a new computed field, a renamed column, a changed aggregation — the read model built under the old logic is invalidated. The industry pattern is to version projections explicitly (e.g., `CustomerOrderView_v1`, `CustomerOrderView_v2`), run both simultaneously until the new version fully catches up, then atomically swap the query service's read target and decommission the old version. Frameworks such as Axon Framework and EventStoreDB provide projection versioning primitives; rolling your own requires a projection registry and a controlled replay harness. Teams that skip this discipline end up with silent data drift as they patch projections in place without rebuilding — a read model that no longer faithfully represents the event stream.

**Integration level:** collapsed block
**Priority:** medium

---

### Consistency Between Write Side and Read Side

> **Expert Note:** The "version / token check" row in the consistency table understates how this pattern is implemented at scale. The correct production form is a **causal consistency token**: the command handler returns an opaque token encoding the event sequence position (e.g., a global offset in Kafka, a stream revision in EventStoreDB). The client passes that token on its next read; the query service blocks or retries internally until the projection's watermark has advanced past the token, then responds. This provides read-your-own-writes without ever touching the write model. AWS AppSync, Confluent's ksqlDB, and EventStoreDB all expose variants of this under names like "read-at-revision" or "after-position." The key production nuance is that the query service must expose a "not yet" response code (HTTP 202 Accepted or a structured retry-after payload) rather than silently returning stale data — otherwise the client cannot distinguish "the system caught up" from "the projection is lagging."

**Integration level:** inline callout
**Priority:** high

---

### Command and Query Separation

> **Expert Note:** A common design conflict surfaces when UX teams assume the command path should return rich, post-mutation state — the updated order, the new account balance. The correct CQRS contract is stricter: the command handler returns synchronous **validation errors and failure codes** (the user must know immediately if their intent was rejected), but on success returns only an identifier or causal token — never the mutated read shape. Returning query-side data from the command path reintroduces the coupling CQRS was designed to sever and forces the command handler to query the read model or re-read the write store. Teams that blur this boundary end up with a "command-query hybrid" that inherits the complexity of both models without the scaling benefit of either.

**Integration level:** collapsed block
**Priority:** medium

---

### Read Models and Event-Driven Projections

> **Expert Note:** Projection idempotency keys deserve more precision than "event ID or per-view version." In broker-based systems (Kafka, Kinesis), the temptation is to use the broker's partition offset as the idempotency key. This is fragile: offsets can be reassigned after topic compaction, partition rebalancing, or topic recreation during disaster recovery. The robust choice is the **domain event's own UUID or aggregate version**, which is stable across infrastructure changes. Concretely, the projection table should carry a `last_applied_event_id` column; an upsert is only executed when the incoming event ID differs. This makes the projection resilient to broker infrastructure events that the team controls separately from domain semantics.

**Integration level:** collapsed block
**Priority:** medium

---

### When CQRS Is Over-Engineering

> **Expert Note:** In practice, the safest adoption path is incremental rather than upfront. A team that introduces CQRS from day one on an untested domain almost always over-applies it — the bounded contexts are speculative, the query shapes are unknown, and the projections that get built end up mirroring the write model anyway. The field-validated approach is to start with a shared model under a read replica, instrument query patterns, identify the two or three read shapes that genuinely diverge from the write model under real load, and extract only those into projections. This "migrate from pain" path is dramatically less risky than designing CQRS upfront, and it keeps most of the codebase in the simpler CRUD regime until real evidence justifies the cost.

**Integration level:** collapsed block
**Priority:** medium

---

### When CQRS Is Over-Engineering

> **Expert Note:** The prose's warning signs are solid, but one failure mode common in microservices-heavy corporate environments is missing: cross-stream projections. When domain aggregates are partitioned too finely — separate services for Order, OrderLine, and Fulfillment — projections for UI screens must join events from multiple streams. This is effectively a distributed join, and it introduces a secondary consistency hazard: the projection for a CustomerOrderView may receive OrderPlaced from stream A before the correlated FulfillmentScheduled from stream B, requiring buffering, timeout logic, and compensating logic for events that never arrive. At that point the projection is no longer a simple consumer but a stateful correlation engine. This is a strong signal that the bounded contexts were drawn incorrectly rather than that CQRS should be extended to handle the complexity.

**Integration level:** collapsed block
**Priority:** medium

---

### Command and Query Separation

> **Expert Note:** A pattern that masquerades as CQRS in many corporate codebases is "poor man's CQRS": a single database where read paths use views, stored procedures, or indexed covering queries instead of a physically separate read model, with no event-driven projection. This provides modest query optimization but none of the structural benefits — the two sides share the same schema migration lifecycle, the same storage engine, and the same transactional lock contention under load. It is sometimes the correct intermediate step, but teams that call it CQRS misjudge how far they are from the pattern's actual scaling and rebuildability benefits.

**Integration level:** file only
**Priority:** low

---

## Summary
- Total notes: 8
- High priority (inline callout): 2
- Medium priority (collapsed block): 5
- Low priority (file only): 1

**Top 3 notes to integrate:**
1. [Read Models and Event-Driven Projections] Projection replay at production scale — snapshot checkpoints, parallel replay, shadow projection strategy
2. [Consistency Between Write Side and Read Side] Causal consistency token pattern — the correct production implementation of version/token read-your-writes
3. [Read Models and Event-Driven Projections] Projection idempotency keys — domain event UUID vs. broker offset, and why offsets are fragile
