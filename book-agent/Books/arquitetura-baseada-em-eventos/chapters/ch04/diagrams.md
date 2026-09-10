## Diagrams — Delivery Guarantees and Idempotency

### sequence diagram contrasting at-most-once (ack before process, crash loses message) and at-least-once (process before ack, crash triggers redelivery and duplicate) — show the broker, consumer, and the crash point in each

These two scenarios illustrate how the ordering of acknowledge versus process determines the delivery guarantee: acking first risks silent message loss on crash, while processing first risks duplication but never loses a message.

```mermaid
sequenceDiagram
    participant B as Broker
    participant C as Consumer

    Note over B,C: Scenario A — At-Most-Once (ack before process)
    B->>C: Deliver message
    C-->>B: ACK sent immediately
    Note over C: CRASH — processing never completes
    Note over B,C: Message LOST — broker already released it

    Note over B,C: Scenario B — At-Least-Once (process before ack)
    B->>C: Deliver message
    Note over C: Process message (side effect applied)
    Note over C: CRASH — ACK never sent
    B->>C: Redeliver message (no ACK received)
    C-->>B: ACK after second processing
    Note over B,C: DUPLICATE — side effect applied twice
```

---

### flowchart showing a producer partitioning events by accountId — three accounts fanning into three partitions, each partition preserving per-account order, while a single consumer group competes across partitions

This diagram shows how routing events by a stable entity key (accountId) concentrates all events for one account onto one partition, preserving intra-account order while allowing parallel consumption across accounts via a consumer group.

```mermaid
flowchart LR
    Acc1[Account A01\nEvents] -->|partitionKey=A01| P0[Partition 0\nordered per A01]
    Acc2[Account A02\nEvents] -->|partitionKey=A02| P1[Partition 1\nordered per A02]
    Acc3[Account A03\nEvents] -->|partitionKey=A03| P2[Partition 2\nordered per A03]

    subgraph CG[Consumer Group]
        C1[Consumer 1]
        C2[Consumer 2]
        C3[Consumer 3]
    end

    P0 --> C1
    P1 --> C2
    P2 --> C3
```

---

### flowchart of the dual-write problem — service writes to DB, then a crash prevents the broker publish, leaving DB and broker inconsistent; annotate the failure gap

This diagram exposes the failure gap that exists when a service must write to two independent systems (database and broker) without a shared transaction: a crash between the two writes leaves state persisted in the database but no event published to consumers, silently corrupting the system's consistency.

```mermaid
flowchart TD
    CMD[Incoming Command] --> SVC[Service]
    SVC --> DBW[1. Write to Database]
    DBW --> DBOK[(DB Updated — Committed)]
    DBOK --> FAILGAP["2. FAILURE GAP\nService crashes here"]
    FAILGAP --> NOPUB["3. Broker Publish — NEVER HAPPENS"]
    NOPUB --> INCON["Inconsistent State\nDB updated, no event emitted\nConsumers never notified"]

    style FAILGAP fill:#cc0000,color:#ffffff,stroke:#990000
    style NOPUB fill:#ff8800,color:#ffffff
    style INCON fill:#cc3300,color:#ffffff
```
