## Expert Review — Modeling Events as Domain Facts
Reviewer profile: Senior practitioner, 10+ years, cloud-native microservices / corporate distributed systems
Date: 2026-09-01

---

### Domain Events Versus Integration Events

> **Expert Note:** The translation step from domain event to integration event is not just a modeling discipline — it is a reliability boundary that requires an explicit delivery mechanism. In production systems, the most common failure mode is: domain event is captured in memory or in an application-layer listener, the translation runs synchronously, and the publish to the broker fails or the process crashes between the database commit and the broker write. The industry-standard fix is the **Transactional Outbox pattern**: write the outgoing integration event to an `outbox` table in the same ACID transaction that mutates the aggregate, then relay asynchronously. Without this, the translation boundary that protects your consumers from your schema is itself a source of phantom consistency bugs that are extremely hard to reproduce in test environments.

**Integration level:** inline callout
**Priority:** high

---

### Event Storming as a Discovery Technique

> **Expert Note:** Alberto Brandolini defines three levels of Event Storming — **Big Picture**, **Process Modeling**, and **Software Design** — but most teams run only the first and call it done. The Big Picture session produces the boundary map and pivotal events described in the prose. Process Modeling (a separate, smaller session) is where commands, actors, read models, and policies are refined per sub-process: this is the level that produces the aggregate and command design that feeds directly into code. Stopping at Big Picture leaves a significant translation gap between the workshop wall and the first schema draft, which engineers typically fill by reverting to database-shaped events — the exact anti-pattern Chapter 2 warns against.

**Integration level:** collapsed block
**Priority:** medium

---

### Event Storming as a Discovery Technique

> **Expert Note:** In practice, Event Storming hotspots (red notes) are as often organizational as they are technical. A persistent hotspot where domain experts cannot agree on a term is frequently a signal of **Conway's Law** tension: two teams share ownership of a concept and have evolved different models. Treating these as purely technical modeling problems leads to fragile compromises. The more effective response is to surface the organizational ownership question explicitly — which team owns the definition of this aggregate? — and let that decision drive the bounded-context boundary, rather than searching for a linguistic middle ground that neither team will actually maintain.

**Integration level:** collapsed block
**Priority:** medium

---

### Bounded Contexts and Event Contracts Between Teams

> **Expert Note:** The prose correctly introduces consumer-driven contracts as the mechanism for safely evolving integration events, but the tooling gap is worth naming for practitioners ready to implement it. For asynchronous event systems, **Pact** (pact.io) is the most widely adopted consumer-driven contract testing framework and has first-class support for message contracts as of v4. Schema registry contract enforcement (Confluent Schema Registry with compatibility modes, or AWS Glue Schema Registry) handles structural evolution but not semantic compatibility — Pact covers the latter. A complementary layer is **AsyncAPI 3.0**, now the dominant spec for documenting async event contracts, equivalent to OpenAPI for REST; it integrates with schema registries and feeds discoverability catalogs such as Backstage.

**Integration level:** collapsed block
**Priority:** medium

---

### Bounded Contexts and Event Contracts Between Teams

> **Expert Note:** The prose correctly places the anti-corruption boundary at the context edge, but teams frequently misplace the implementation of it. In an asynchronous event system, the ACL lives **inside the consuming service's event handler or a dedicated transformer process** — not in the broker, not in a shared middleware layer. Attempts to implement a "centralized ACL" at the broker level (via Kafka Streams topology or an ESB-style intermediary) reconstitute the integration hub that event-driven architecture was meant to eliminate, and create a shared-mutable component that every team depends on. Each consumer owns its own translation; that is what keeps them independently deployable.

**Integration level:** inline callout
**Priority:** high

---

### Granularity and Event Naming Conventions

> **Expert Note:** The prose warns against events that are too fine-grained (mutations), but the opposite failure is equally dangerous in production and receives less attention: events that are too coarse create **evolutionary pressure toward kitchen-sink payloads**. As new consumers arrive, each one needs a field the existing event does not carry. The path of least resistance is to keep adding fields to the single coarse event. Within 18 months, `OrderPlaced` carries 60 fields, half of which are null for any given consumer, and the schema has become a de facto shared database across teams. The mitigation is to model at business decision granularity but then deliberately audit which fields each declared consumer actually uses — zero-field consumers are a signal the event boundary is wrong.

**Integration level:** inline callout
**Priority:** high

---

### Granularity and Event Naming Conventions

> **Expert Note:** In shared broker environments (a single Kafka cluster or EventBridge event bus serving multiple teams), flat event names like `OrderPlaced` produce naming collisions as the system scales. Industry practice is to include a **namespace prefix** — typically `<bounded-context>.<EventName>` or `<team>.<EventName>` — either in the topic name, the event type field, or both. CloudEvents spec (CNCF) formalizes this as the `type` attribute, recommended as `<reverse-dns>.<version>.<entity>.<action>` (e.g., `com.acme.orders.v1.OrderPlaced`). Adopting this convention at modeling time costs nothing; retrofitting it after consumers have hardcoded string comparisons against bare names is expensive.

**Integration level:** file only
**Priority:** low

---

### Technical Noise as a Modeling Anti-Pattern

> **Expert Note:** The most common production source of technical noise that practitioners encounter is **Change Data Capture (CDC) pipelines publishing directly to domain topics**. Tools like Debezium capture row-level changes from the database transaction log and emit events such as `INSERT/UPDATE on orders table with column deltas` — which is precisely the `OrderTableRowChanged` anti-pattern the prose describes. The failure mode is that teams treat CDC as the event publishing layer, bypassing domain modeling entirely. The correct architecture is to use CDC as an **outbox relay** (reading from an `outbox` or `domain_events` table written by the application) rather than capturing raw table mutations. If you see Debezium topics named after database tables flowing directly to consumers, you are looking at technical noise at industrial scale.

**Integration level:** inline callout
**Priority:** high

---

## Summary
- Total notes: 8
- High priority (inline callout): 4
- Medium priority (collapsed block): 3
- Low priority (file only): 1

**Top 3 notes to integrate:**

1. [Domain Events Versus Integration Events] Transactional Outbox pattern as the reliability mechanism for the translation boundary — prevents silent event loss between DB commit and broker publish.
2. [Technical Noise as a Modeling Anti-Pattern] CDC tools (Debezium) as the primary industrial-scale vector for technical noise — directly actionable correction for teams using CDC.
3. [Granularity and Event Naming Conventions] Kitchen-sink payload evolution pressure from overly coarse events — a real production trap the prose does not warn against.
