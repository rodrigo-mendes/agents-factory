## Skeptical Review — Event Sourcing — State as a Sequence of Events
Reviewer profile: Rigorous technical skeptic
Date: 2026-09-01

---

### The Truth-and-History Problem

> **Critical Note:** The prose states "you cannot have incorrect history, because the history is the only thing you ever wrote" and frames audit-trail correctness as "a property of the architecture." This is a consequential overstatement. Application-layer bugs — emitting a `MoneyWithdrawn` event with the wrong amount, writing to the wrong stream ID, or double-firing a command handler — produce incorrect events that are permanently persisted with the same immutability guarantee as correct ones. The event store enforces append-only and ordering, not domain correctness. A senior engineer who internalizes this claim may dangerously deprioritize command-handler correctness testing and idempotency controls on the grounds that "the store guarantees correctness."

**Severity:** blocking
**Suggested fix:** Replace the absolute claim with a qualified one: the architecture guarantees that every event written is durably preserved exactly as written, eliminating accidental overwrite — but correctness of what is written remains entirely the responsibility of the application. Add a brief callout on the importance of idempotent command handlers and at-least-once delivery guards to prevent duplicate or incorrect events from becoming permanent facts.

---

### The Truth-and-History Problem

> **Critical Note:** The prose states that audit tables built with triggers are "always slightly wrong," presenting this as universal. PostgreSQL's temporal tables, SQL Server's system-versioned temporal tables (ISO SQL:2011), and well-implemented CDC pipelines can produce audit trails with strong durability and correctness properties. The blanket dismissal may read as a rhetorical setup for Event Sourcing rather than a fair technical comparison, which undermines credibility with the senior audience.

**Severity:** minor
**Suggested fix:** Qualify the claim: trigger-based audit tables are *operationally fragile* (bypass mechanisms, bulk-load gaps, DDL changes silently breaking triggers) rather than categorically incorrect. This is still a strong argument for Event Sourcing without overstating the failure mode of the alternative.

---

### The Event Store and the Append-Only Log

> **Critical Note:** The claim "no locks, no blocking — just a constraint doing its job" overstates the benefit of optimistic concurrency under contention. In high-throughput write scenarios on a single aggregate stream — for example, a shared account receiving concurrent payment events — every conflicting writer will retry. Under sustained contention this degrades to effective serialization: all writers spin, reload the stream, reprocess the command, and retry the insert. Retry storms can be worse than a fair queue with a single lock, and the application must bound retries and handle persistent concurrency-conflict errors. This failure mode is invisible on the happy path but material in production.

**Severity:** important
**Suggested fix:** Add a paragraph noting that optimistic concurrency works best when conflicting writers on the same stream are rare. For hot streams, recommend command de-duplication at the handler level, stream partitioning, or explicit locking strategies, and note that unbounded retries must be guarded against with a max-retry count and backoff.

---

### State Reconstruction and Aggregates

> **Critical Note:** The rule "apply methods must never reject an event or contain validation" is described as absolute, but it does not address the forward-compatibility scenario where an aggregate encounters an event type introduced by a newer version of the application that the current code does not recognize. Silently ignoring unknown event types during rehydration can produce subtly wrong in-memory state; hard-failing on unknown types breaks reconstruction entirely. This is a real operational problem during rolling deployments and schema migrations. The absolute framing gives no guidance on how to handle it.

**Severity:** important
**Suggested fix:** Qualify the rule: apply methods must not reject *known* events or apply business validation to them. For unknown or unrecognized event types, state the recommended strategy explicitly — typically, ignore-and-log with a version-awareness check — and reference the schema versioning content in Chapter 8 to signal that this is a formally addressed topic, not an open question.

---

### Snapshots and Replay Optimization

> **Critical Note:** The snapshot strategy discussion omits a critical operational question: who writes the snapshot, and what happens if that write fails? If the command handler writes the snapshot synchronously after appending an event (the common inline approach), a snapshot write failure must not be treated as a command failure — or command processing becomes unreliable. If snapshots are written by an asynchronous background process, there is a window where the snapshot store is stale or empty and full replay is silently required. Neither path is mentioned, and the failure mode of an orphaned or corrupt snapshot (one that references a version that no longer exists in the event store) is not addressed.

**Severity:** important
**Suggested fix:** Add a paragraph on snapshot write semantics: snapshots should be written as best-effort, non-transactional operations that never block or fail the command pipeline. Include a note that the code should always fall back to full replay if a snapshot is missing or its version is not present in the event store, treating the snapshot as an advisory cache rather than a required dependency.

---

### Long-Term Costs and Design Constraints

> **Critical Note:** The prose cites medical records as a canonical domain where Event Sourcing "earns its keep" because history is intrinsically valuable. This is the same domain where HIPAA and GDPR create a right-to-erasure obligation and where data correction (amending a clinical entry) is a routine operational requirement. The immutability of Event Sourcing is in direct tension with both. Crypto-shredding handles GDPR erasure in principle, but clinical correction — where a misdiagnosis event must be amended, not just superseded — requires compensating events and careful read-model logic to surface the corrected state. Presenting medical records as a straightforward fit for Event Sourcing without this caveat could lead a reader to underestimate the regulatory complexity.

**Severity:** important
**Suggested fix:** Qualify the medical records example with a note that regulated domains requiring correction or erasure workflows demand explicit design: compensating events for corrections, crypto-shredding for deletion, and read models that correctly surface only the authoritative current record. Consider substituting financial ledgers and order lifecycle as the cleaner examples, since those domains have the weakest deletion requirements.

---

### Long-Term Costs and Design Constraints

> **Critical Note:** "This must be designed in from the first event, because you cannot retrofit encryption onto facts already written in plaintext." The word "cannot" is too absolute. Re-encryption of historical event payloads is operationally expensive and risky but not impossible — it requires a migration pipeline that reads, decrypts (trivially, since the keys still exist), re-encrypts under the new scheme, and re-writes each event to a new store or updates the payload in place (which technically violates immutability of payload content). The correct message is that retrofitting is *prohibitively costly and architecturally disruptive*, not categorically impossible.

**Severity:** minor
**Suggested fix:** Replace "cannot" with "should never need to" and briefly explain why: the migration cost is high, the operation requires downtime or a shadow store, and a single missed plaintext event invalidates the GDPR compliance argument. This makes the same point more honestly and withstands pushback from a senior reader who knows migration pipelines exist.

---

### Long-Term Costs and Design Constraints

> **Critical Note:** The statement "Choosing Event Sourcing effectively commits you to the CQRS read path" is presented as a hard constraint, but it is a strong practical tendency rather than an architectural law. Purpose-built stores like EventStoreDB support persistent subscriptions and catch-up reads that can serve simple queries without a full CQRS projection layer. Lightweight systems may query snapshots directly for current state. For a senior audience that may be evaluating Event Sourcing without CQRS for a bounded context, the categorical framing may falsely eliminate architecturally valid options.

**Severity:** minor
**Suggested fix:** Soften to: "In practice, Event Sourcing without a CQRS read path creates significant query friction, and most production systems adopt both together. Some purpose-built event stores provide built-in query primitives that reduce this friction, but for complex or high-read-volume domains, dedicated projections remain the standard answer."

---

## Summary
- Total notes: 8
- Blocking (inline callout): 1
- Important (collapsed): 4
- Minor (file only): 3

**Top 3 items requiring attention:**

1. [The Truth-and-History Problem] "You cannot have incorrect history" — architecture guarantees durability, not domain correctness; this conflation could cause practitioners to underinvest in command-handler correctness and idempotency controls.
2. [Long-Term Costs and Design Constraints] Medical records cited as a canonical fit for Event Sourcing without acknowledging that the same domain has the strongest deletion and correction requirements that conflict with immutability.
3. [Snapshots and Replay Optimization] Snapshot write-failure semantics and the corrupt/orphaned snapshot failure mode are entirely absent, leaving a gap that practitioners will encounter in production.
