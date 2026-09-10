## Skeptical Review — Real-World Cases, Trade-offs, and Pitfalls
Reviewer profile: Rigorous technical skeptic
Date: 2026-09-01

---

### Migrating to and from Event Sourcing

> ⚠️ **Critical Note:** Step 3 of the migration guide states "Old history before the cutover is lost, and that is acceptable." This assertion is directly contradicted by the fintech ledger case study introduced just two sections earlier, where the primary driver is auditability and the stated requirement is that "every balance must be explainable." Regulators (PCI-DSS, SOX, FCA, BACEN) routinely demand multi-year transaction history, and a migration strategy that discards pre-cutover state would be non-compliant in precisely the domain the chapter uses as its canonical success story. A senior architect reading this in a regulated industry context may follow this advice and produce a legally non-compliant migration plan.

**Severity:** blocking
**Suggested fix:** Qualify the statement explicitly: "Discarding pre-cutover history is acceptable for non-regulated domains. In regulated contexts (fintech, healthcare, insurance), the legacy state must be preserved — either by retaining the legacy database as a read-only compliance archive, migrating historical records as synthetic events with source provenance metadata, or obtaining explicit regulatory sign-off that the Initialized snapshot satisfies audit requirements."

---

### Case Studies in Fintech and E-commerce

> ⚠️ **Critical Note:** The prose claims Event Sourcing is "the cheapest way to meet" the auditability requirement of a fintech ledger, with no comparison against alternatives. Append-only audit log tables (a separate audit_log table that is INSERT-only and NEVER updated), Change Data Capture (CDC) with Debezium writing to an immutable sink, and purpose-built audit services (AWS CloudTrail-style) all satisfy the same auditability requirement at a fraction of the operational complexity. For many teams, an append-only audit table is the cheapest and most maintainable solution. Presenting Event Sourcing as the default-correct answer to "you need auditability" is the very over-adoption trap the chapter warns against.

**Severity:** important
**Suggested fix:** Replace "the cheapest way" with "one compelling way" and add one sentence enumerating the lighter-weight alternatives: "If the requirement is auditability alone without temporal query or state replay, an append-only audit log or CDC pipeline may achieve the same guarantee at significantly lower complexity cost."

---

### Case Studies in Fintech and E-commerce

> ⚠️ **Critical Note:** The e-commerce checkout section presents distributed ACID as "impractical" as a universal claim, without acknowledging that modern globally-distributed databases (Google Spanner, CockroachDB, YugabyteDB, AWS Aurora Global Database with serializable isolation) do provide distributed ACID semantics. For a target audience of senior architects, dismissing distributed ACID categorically may produce over-reliance on sagas even in cases where a strongly-consistent database satisfying all services' requirements is the simpler and safer choice.

**Severity:** important
**Suggested fix:** Narrow the claim to its actual scope: "A distributed ACID transaction across services that own separate data stores and separate deployment units is impractical in the general case. If the services can share a single strongly-consistent database cluster, standard ACID transactions may remain viable and should be preferred."

---

### Anti-Pattern Catalog and Recurring Pitfalls

> ⚠️ **Critical Note:** The anti-pattern for "Assuming exactly-once delivery" states that "under at-least-once delivery — the realistic default — duplicates are guaranteed." The word "guaranteed" is technically wrong: at-least-once delivery means a message will be delivered at least once, which makes duplicates possible and likely under failure conditions, but not guaranteed in every execution. Saying they are guaranteed implies every single message will arrive more than once, which is false and could lead engineers to add unnecessary deduplication overhead on low-volume, low-failure paths while the real lesson — that idempotency must be designed in regardless of observed duplicate rate — is sound.

**Severity:** important
**Suggested fix:** Replace "duplicates are guaranteed" with "duplicates are an expected and unavoidable occurrence under failure conditions." Retain the conclusion that non-idempotent consumers are a time bomb — that recommendation is correct.

---

### Case Studies in Fintech and E-commerce

> ⚠️ **Critical Note:** The shopping cart is described as "disposable by nature," implicitly endorsing the decision not to event-source it. While discouraging event-sourcing the cart is correct advice, characterizing carts as disposable is an oversimplification that does not match real-world e-commerce requirements. Abandoned cart recovery, GDPR right-to-erasure auditing over cart contents, tax-jurisdiction snapshotting, and wishlist/save-for-later features all require durable, queryable cart state. The framing may lead readers to under-invest in cart persistence design under the assumption it is inherently throwaway.

**Severity:** important
**Suggested fix:** Replace "the shopping cart, which is disposable by nature" with "the shopping cart, whose state is short-lived and whose contents need not be reconstructed historically." Add a one-sentence clarification: "Cart state must still be persisted durably for abandoned-cart recovery and regulatory purposes — the point is that its history is not a business requirement."

---

### Migrating to and from Event Sourcing

> ⚠️ **Critical Note:** The exit from Event Sourcing is described as "straightforward" because "current state is always derivable." This glosses over three significant failure modes that senior practitioners regularly encounter: (1) projection bugs that have silently accumulated incorrect state over thousands of replays, meaning the "final" projection may not reflect reality; (2) event store volume — a system with hundreds of millions of events may take hours or days to replay into a final snapshot, making a clean cutover operationally complex; and (3) incomplete or corrupt event streams where gaps or deserialization failures mean the current state is not fully derivable. Calling the exit "straightforward" understates the due diligence required.

**Severity:** important
**Suggested fix:** Qualify the exit procedure: "The exit is conceptually clean, because state is derivable from events — but practitioners should validate projection correctness by cross-checking against known business invariants before treating the final snapshot as authoritative, and plan for the replay duration if event volumes are large."

---

### Decision Framework: When Not to Use Each Pattern

> ⚠️ **Critical Note:** The decision table instructs architects to prefer "Orchestration with a process manager" over choreography whenever "the process has many steps and needs central visibility." This conflates the two concerns. Distributed tracing (OpenTelemetry, AWS X-Ray, Jaeger) provides central observability over choreographed flows without introducing the tight coupling and single point of failure that a process manager brings. Many steps alone is not a valid trigger for orchestration — it becomes valid when the business logic requires centralized decision-making or compensating logic that is unsafe to distribute. Reducing the choice to step count may cause teams to introduce orchestration overhead unnecessarily.

**Severity:** minor
**Suggested fix:** Refine the condition from "The process has many steps and needs central visibility" to "The process has many steps with complex conditional branching, or requires central authority to decide on compensation." Add a note: "Observability over choreographed flows is achievable with distributed tracing and correlation IDs without requiring orchestration."

---

### Premature Adoption of ES, CQRS, and Saga Combined

> ⚠️ **Critical Note:** The prose states that a junior engineer "cannot add a field without touching an event schema, a projection, an upcaster, and possibly a saga step." While the complexity warning is valid, the upcaster requirement is only true for breaking schema changes. With schema registries (Confluent Schema Registry, AWS Glue Schema Registry) and backward-compatible evolution rules (adding a nullable field in Avro or Protobuf), new fields can be added without writing upcasters at all. The example conflates all schema changes with breaking schema changes, which may cause readers to overestimate the ongoing maintenance cost and either avoid Event Sourcing when it genuinely fits, or miscommunicate the risk to stakeholders.

**Severity:** minor
**Suggested fix:** Qualify the claim: "A junior engineer cannot safely make a breaking schema change — removing a field, renaming a field, or changing a type — without touching a projection, an upcaster, and possibly a saga step. Non-breaking additions are manageable with a schema registry enforcing compatibility rules, but even those additions propagate through projections when business logic changes."

---

## Summary
- Total notes: 8
- Blocking (inline callout): 1
- Important (collapsed): 5
- Minor (file only): 2

**Top 3 items requiring attention:**

1. [Migrating to and from Event Sourcing] "Old history before the cutover is lost, and that is acceptable" — directly contradicts the fintech auditability requirement and is non-compliant guidance for regulated industries.
2. [Case Studies in Fintech and E-commerce] Event Sourcing described as "the cheapest way" to meet auditability — lighter-weight alternatives (append-only audit log, CDC) are ignored, perpetuating the exact over-adoption bias the chapter warns against.
3. [Anti-Pattern Catalog and Recurring Pitfalls] "Duplicates are guaranteed" — technically incorrect phrasing that could cause unnecessary engineering overhead and distracts from the correct lesson (design for idempotency regardless of observed rate).
