## Expert Review — Real-World Cases, Trade-offs, and Pitfalls
Reviewer profile: Senior practitioner, 10+ years, cloud-native microservices and corporate distributed systems
Date: 2026-09-01

---

### Case Studies in Fintech and E-commerce

> **Expert Note:** The fintech ledger example correctly motivates Event Sourcing for auditability, but omits a critical production constraint: as an aggregate accumulates tens of thousands of events — common for active accounts after 2–3 years — replaying the full stream on every read becomes prohibitive. Production Event Sourcing systems at scale universally require a **snapshot strategy**: periodically persisting the projected state as a checkpoint so replay starts from the nearest snapshot rather than event zero. Without snapshotting, read latency for high-frequency aggregates grows linearly with account age and can cross SLA thresholds within months of go-live. Teams that discover this late are forced into an emergency snapshot migration under production load.

**Integration level:** inline callout
**Priority:** high

---

### Case Studies in Fintech and E-commerce

> **Expert Note:** The e-commerce checkout saga section is accurate, but omits a production failure mode worth naming: the **saga rollback storm**. When a late-stage compensation fires at high volume — for example, a shipping service rejects an order after payment has already been captured — the compensating `RefundPayment` and `ReleaseInventory` events arrive at upstream services as a burst. At checkout peaks (Black Friday, flash sales), the compensation burst can overwhelm payment provider rate limits or inventory service capacity, causing a second failure wave that cascades back through the saga. Teams operating at scale add backpressure and exponential-backoff retry budgets specifically for the compensation path, treating it as a separate traffic class from the happy path.

**Integration level:** collapsed block
**Priority:** medium

---

### Anti-Pattern Catalog and Recurring Pitfalls

> **Expert Note:** The "assuming exactly-once delivery" anti-pattern is correctly identified, but there is a specific, recurring misconception that the prose does not address: engineers who enable Kafka's **exactly-once semantics (EOS)** via transactional producers and idempotent consumers believe they have eliminated the idempotency requirement on the consumer side. This is wrong. Kafka EOS guarantees that each message is written to and read from the Kafka log exactly once; it makes no guarantee about the side effects of consumer processing — database writes, downstream HTTP calls, file mutations, or external API invocations are completely outside the EOS scope. A consumer that calls an external payment API or writes to a relational DB is still fully responsible for idempotency. Teams have shipped "EOS-enabled" consumers that double-charge customers because they conflated broker-level deduplication with end-to-end exactly-once processing.

**Integration level:** inline callout
**Priority:** high

---

### Anti-Pattern Catalog and Recurring Pitfalls

> **Expert Note:** The distributed monolith anti-pattern could be made more specific with a concrete organizational trigger teams miss: using a **shared schema registry with synchronized releases**. Teams adopt Confluent Schema Registry or AWS Glue Schema Registry correctly, but then manage all schema versions in a single monorepo with a unified release pipeline — requiring schema owners and all consumer teams to coordinate each release cycle. This recreates the centralized release train of the monolith at the schema layer, even when the services themselves are independently deployable. The tell is a sprint board with "schema freeze" stories blocking unrelated feature work.

**Integration level:** collapsed block
**Priority:** medium

---

### Premature Adoption of ES, CQRS, and Saga Combined

> **Expert Note:** The prose correctly describes the technical taxes of combining all three patterns, but the organizational tax is equally significant and often hits first. In a system with Event Sourcing, CQRS, and sagas all active, a single P1 incident requires an engineer to simultaneously reason across four distinct layers: the event stream (what happened?), the projection state (what did it compute?), the saga state (what step is the process in?), and the compensation log (what was rolled back?). Mean time to diagnose spikes. Teams report that onboarding a new engineer to full-stack debugging in this environment takes 6–9 months rather than the 4–6 weeks typical for a service-based system. The complexity is not just a code problem — it is a hiring constraint and a key-person risk.

**Integration level:** collapsed block
**Priority:** medium

---

### Migrating to and from Event Sourcing

> **Expert Note:** Step 4 in the migration procedure — "run dual-write or shadow projections" — glosses over a critical atomicity problem. Dual-writing to a legacy state database and an event store in the same application transaction is not atomic unless both are in the same ACID boundary, which they typically are not. A crash between the DB write and the event store append leaves the two systems inconsistent. The production-safe approach is the **transactional outbox pattern**: write the event to a local outbox table in the same transaction as the state update, then relay it asynchronously to the event store via CDC (Change Data Capture, e.g., Debezium) or a dedicated relay process. Teams that skip this step discover inconsistencies only under failure injection testing or, worse, during an actual production incident.

**Integration level:** inline callout
**Priority:** high

---

### Migrating to and from Event Sourcing

> **Expert Note:** Step 3 states that "old history before the cutover is lost, and that is acceptable." This claim requires a hard qualification for regulated industries — precisely the fintech context the chapter uses as its primary case study. Under SOX, PCI-DSS, and most banking regulators' data retention requirements, historical transaction state must be auditable for 5–7 years. "Seeding with an Initialized event" satisfies the requirement going forward but does not satisfy backward-looking audits for the pre-migration period. Regulated teams must either (a) migrate historical CRUD records into synthetic events at cutover, (b) retain the legacy system in read-only mode as an archive for the retention window, or (c) export historical state snapshots to a compliant cold store. Treating pre-cutover history as acceptable loss without verifying regulatory obligations is an audit risk, not just a technical trade-off.

**Integration level:** inline callout
**Priority:** high

---

### Decision Framework: When Not to Use Each Pattern

> **Expert Note:** The decision table recommends choreography when "two services need loose, independent coupling," implying a two-service ceiling where orchestration is not yet justified. In practice, the threshold is more a function of **observability** than participant count. Choreography with even three or four services creates an implicit distributed state machine with no single component that knows the overall process state, making incident diagnosis and business-level reporting (e.g., "how many orders are stuck between payment and shipping right now?") extremely difficult. The operational rule of thumb used at scale: if a business stakeholder or SRE needs to ask a cross-service question about process state more than once per quarter, that process needs an orchestrator. Choreography should be reserved for fire-and-forget fan-out where the publisher genuinely does not care what consumers do with the event.

**Integration level:** collapsed block
**Priority:** medium

---

## Summary
- Total notes: 7
- High priority (inline callout): 4
- Medium priority (collapsed block): 3
- Low priority (file only): 0

**Top 3 notes to integrate:**

1. [Case Studies in Fintech and E-commerce] Snapshot strategy requirement at scale — event replay latency grows linearly without checkpointing, and teams hit production SLA violations within months.
2. [Migrating to and from Event Sourcing] Dual-write atomicity trap — the transactional outbox + CDC pattern is the production-safe replacement for naive dual-write during migration.
3. [Migrating to and from Event Sourcing] Regulated-industry correction on "history loss is acceptable" — in fintech/banking, pre-cutover history may be legally non-negotiable, directly contradicting the unqualified claim in Step 3.
