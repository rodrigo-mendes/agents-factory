## Diagrams — Real-World Cases, Trade-offs, and Pitfalls

### side-by-side comparison (two-column flowchart) showing the fintech ledger flow — event store appending FundsDeposited/Withdrawn events feeding a balance projection — next to the e-commerce checkout saga flow — OrderPlaced triggering inventory, payment, and shipping steps with compensating paths back

These two subgraphs contrast the dominant pattern for each domain: the fintech ledger uses Event Sourcing to build an auditable, immutable history that drives a balance projection, while the e-commerce checkout uses a saga with compensating transactions to coordinate across bounded contexts when any step fails.

```mermaid
flowchart TD
    subgraph Fintech["Fintech Ledger — Event Sourcing"]
        FD[FundsDeposited] --> ES[(Event Store)]
        FW[FundsWithdrawn] --> ES
        TS[TransferSettled] --> ES
        ES --> BP[Balance Projection]
        BP --> AT[Audit Trail]
    end

    subgraph Ecommerce["E-commerce Checkout — Saga"]
        OP[OrderPlaced] --> IR[Reserve Inventory]
        IR --> PA[Authorize Payment]
        PA --> SH[Schedule Shipping]
        PA -->|Payment fails| CI[Compensate: Release Inventory]
        SH -->|Shipping fails| RP[Compensate: Refund Payment]
        RP --> CI
    end
```

---

### a quick-reference table-style flowchart mapping each anti-pattern (symptom) to its root cause and the pattern that prevents it, formatted as a diagnostic decision aid

This diagnostic map surfaces the six most common event-driven anti-patterns, their structural root cause, and the corrective pattern — allowing a team inheriting an unfamiliar system to identify architectural debt before reading business logic.

```mermaid
flowchart LR
    AP1["Symptom: SendEmail event"] -->|Root cause: Command as event| FX1["Fix: Past-tense fact — EmailSent"]
    AP2["Symptom: RowInserted published"] -->|Root cause: Technical noise| FX2["Fix: Business-meaningful events only"]
    AP3["Symptom: Shared schema, lockstep deploy"] -->|Root cause: Distributed monolith| FX3["Fix: Schema registry + compatibility policy"]
    AP4["Symptom: Breaks on duplicate message"] -->|Root cause: Assumes exactly-once| FX4["Fix: Idempotent consumer design"]
    AP5["Symptom: DLQ never actioned"] -->|Root cause: DLQ as landfill| FX5["Fix: Alert on non-empty DLQ"]
    AP6["Symptom: Consumers crash on deploy"] -->|Root cause: No compatibility strategy| FX6["Fix: Schema evolution contracts"]
```

---

### sequence diagram showing migration to Event Sourcing — legacy state DB, seeding the event store with an Initialized event, shadow projection validation against legacy state, then cutover of reads to the projection

This sequence traces the five-stage controlled migration from a state-based system to Event Sourcing — seeding an initial fact, running shadow projections in parallel with the legacy system to validate correctness, and only then switching reads to the new projection and retiring the legacy write path.

```mermaid
sequenceDiagram
    participant App as Application
    participant Legacy as Legacy State DB
    participant ES as Event Store
    participant Proj as Shadow Projection

    App->>Legacy: Read current state
    App->>ES: Append Initialized event (snapshot of current state)

    loop Dual-write phase
        App->>Legacy: Write state change (legacy path)
        App->>ES: Append domain event (new path)
        ES->>Proj: Replay events
        Proj-->>App: Compare projection vs Legacy state
    end

    App->>App: Validation passed — cutover reads to Projection
    App->>Legacy: Retire legacy write path
```

---

### a decision-tree flowchart that starts at "Do I have a concrete requirement?" and branches through auditability, cross-context transactions, read/write shape mismatch, and asynchronous need — routing each answer to the appropriate pattern or to the simpler default

This decision tree operationalizes the book's refusal framework — defaulting always to the simpler option and introducing each pattern only when a named, concrete requirement cannot be met without it.

```mermaid
flowchart TD
    A{Concrete requirement\nidentified?} -->|No| B[Use simpler default\nCRUD / request-response]
    A -->|Yes| C{Audit, replay,\nor temporal query needed?}
    C -->|Yes| D[Event Sourcing]
    C -->|No| E{Process spans multiple\nbounded contexts?}
    E -->|Yes| F{Central visibility\nor complex flow?}
    F -->|Yes| G[Saga + Orchestration\nprocess manager]
    F -->|No| H[Saga + Choreography\nvia events]
    E -->|No| I{Read and write shapes\ngenuinely differ?}
    I -->|Yes| J[CQRS]
    I -->|No| K{Async decoupling\nrequired?}
    K -->|Yes| L[Event-Driven Architecture]
    K -->|No| M[Direct request-response call]
```

---
