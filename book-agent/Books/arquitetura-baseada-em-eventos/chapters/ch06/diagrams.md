## Diagrams — Event Sourcing — State as a Sequence of Events

### side-by-side comparison. Left panel "State-Oriented": a single Account row with balance=500 being overwritten by an UPDATE, with prior values shown crossed out and labeled "lost". Right panel "Event-Sourced": an append-only list of events (AccountOpened, MoneyDeposited +1000, MoneyWithdrawn -500) with a derived balance=500 shown as computed, not stored. Flowchart/comparison style.

The diagram contrasts the two storage philosophies side by side: the state-oriented model overwrites previous values on each UPDATE, permanently destroying history, while the event-sourced model appends immutable facts and derives the current balance on demand. This contrast is the core trade-off of the chapter — convenience of direct reads versus an unforgeable history.

```mermaid
flowchart LR
    subgraph STATE["State-Oriented Storage"]
        direction TB
        S1["balance = 200 — LOST"]
        S2["balance = 700 — LOST"]
        S3["balance = 500 (current)"]
        S1 --"UPDATE overwrites"--> S2
        S2 --"UPDATE overwrites"--> S3
    end

    subgraph EVENT["Event-Sourced Storage"]
        direction TB
        E1["AccountOpened"]
        E2["MoneyDeposited +1000"]
        E3["MoneyWithdrawn -500"]
        E4["balance = 500 (computed)"]
        E1 --> E2 --> E3 --> E4
    end

    STATE --- EVENT
```

---

### sequence diagram of a write. Command handler loads events for stream, calls rehydrate to fold them into an aggregate, invokes a command method (withdraw) which validates the invariant and returns a new MoneyWithdrawn event, then appends that event to the store at expectedVersion+1. Show the concurrency check on append.

This sequence diagram traces the full lifecycle of a write command in an event-sourced system, from stream loading through aggregate rehydration, invariant validation, and optimistic-concurrency-controlled append. It makes visible exactly where validation lives (command method) and where the unique-constraint concurrency guard fires (the append step).

```mermaid
sequenceDiagram
    participant CH as Command Handler
    participant ES as Event Store
    participant AG as Aggregate

    CH->>ES: Load stream (acc-123)
    ES-->>CH: Events v1..v7
    CH->>AG: rehydrate(events)
    AG-->>CH: Aggregate state (version=7)
    CH->>AG: withdraw(300)
    AG-->>CH: MoneyWithdrawn event
    CH->>ES: Append event (expectedVersion=7)
    alt Version 8 is free
        ES-->>CH: OK — written as version 8
    else Version 8 already taken
        ES-->>CH: Conflict — unique constraint violation
        CH->>CH: Retry with fresh load
    end
```

---

### decision flowchart for adopting Event Sourcing. Questions: Is a complete audit trail a hard requirement (regulatory/financial)? Do you need temporal queries or to reconstruct past states? Is the domain rich in behavior rather than simple CRUD? Can the team absorb schema-versioning and eventual-consistency complexity? Route "yes to the first three and the last" to "Event Sourcing is justified" and route CRUD-shaped or team-unready cases to "Prefer state storage / CQRS-lite".

This decision flowchart guides architects through the four qualifying questions before committing to Event Sourcing, routing toward adoption only when all four conditions hold and toward lighter alternatives otherwise. It operationalizes the blunt guidance in the prose: adopt Event Sourcing where history is the product, not where it is a novelty.

```mermaid
flowchart TD
    Q1{"Audit trail is a\nhard requirement?\n(regulatory / financial)"}
    Q2{"Need temporal queries\nor past state reconstruction?"}
    Q3{"Domain is behavior-rich\nrather than simple CRUD?"}
    Q4{"Team can absorb schema\nversioning and eventual consistency?"}
    YES["Event Sourcing Justified"]
    NO["Prefer State Storage\nor CQRS-Lite"]

    Q1 -->|Yes| Q2
    Q1 -->|No| NO
    Q2 -->|Yes| Q3
    Q2 -->|No| NO
    Q3 -->|Yes| Q4
    Q3 -->|No| NO
    Q4 -->|Yes| YES
    Q4 -->|No| NO
```

---
