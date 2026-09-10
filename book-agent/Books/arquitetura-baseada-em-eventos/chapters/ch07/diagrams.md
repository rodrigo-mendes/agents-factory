## Diagrams — Consistency, Sagas, and Long-Running Processes

### sequence diagram contrasting strong consistency (single locked transaction across Order, Payment, Inventory committing together) versus eventual consistency (three independent local commits over time, with a visible inconsistency window between them)

Two-phase commit forces all participants to lock and commit atomically, creating a single all-or-nothing window; a saga lets each service commit locally in sequence, accepting a visible inconsistency window between steps that closes as events propagate forward.

```mermaid
sequenceDiagram
    participant C as Client
    participant O as Order Service
    participant P as Payment Service
    participant I as Inventory Service

    Note over C,I: Strong Consistency — 2PC (all-or-nothing)
    C->>O: PlaceOrder
    O->>P: PREPARE (lock held)
    O->>I: PREPARE (lock held)
    P-->>O: VOTE YES
    I-->>O: VOTE YES
    O->>P: COMMIT
    O->>I: COMMIT
    O-->>C: Order Confirmed

    Note over C,I: Eventual Consistency — Saga (independent commits)
    C->>O: PlaceOrder
    O-->>C: Order Accepted (local commit)
    O-)P: OrderPlaced event
    Note over P: inconsistency window
    P->>P: Commit locally
    P-)I: PaymentCaptured event
    Note over I: inconsistency window
    I->>I: Commit locally
```

---

### side-by-side comparison — left panel choreographed saga as a chain of services each reacting to the previous event with no center; right panel orchestrated saga with a central orchestrator issuing commands and receiving replies from Payment, Inventory, Shipping

Choreography wires services together through a chain of reactive events with no single coordinator, while orchestration places all process logic in one explicit orchestrator that issues commands and awaits replies — understanding this trade-off determines how visible and maintainable the saga flow will be as complexity grows.

```mermaid
flowchart TD
    subgraph CHOREO["Choreographed Saga (no center)"]
        direction LR
        OS[Order Service] -->|OrderPlaced| PS1[Payment Service]
        PS1 -->|PaymentCaptured| IS1[Inventory Service]
        IS1 -->|StockReserved| SS1[Shipping Service]
    end

    subgraph ORCH["Orchestrated Saga (explicit coordinator)"]
        direction LR
        ORC[Order Orchestrator]
        ORC -->|CapturePayment| PS2[Payment Service]
        PS2 -->|PaymentCaptured| ORC
        ORC -->|ReserveStock| IS2[Inventory Service]
        IS2 -->|StockReserved| ORC
        ORC -->|CreateShipment| SS2[Shipping Service]
        SS2 -->|ShipmentCreated| ORC
    end
```

---

### state machine (state diagram) for an order saga with states Started, AwaitingPayment, AwaitingStock, AwaitingShipment, Completed, Compensating, Cancelled, showing the happy-path transitions on success events and the compensation transitions on failure/timeout events

This state machine captures every observable state of an in-flight order saga and makes both the happy path and compensation paths explicit transitions — persisting this state on each transition is what allows the process manager to survive crashes and resume without orphaning in-flight orders.

```mermaid
stateDiagram-v2
    [*] --> Started
    Started --> AwaitingPayment: CapturePayment sent
    AwaitingPayment --> AwaitingStock: PaymentCaptured
    AwaitingPayment --> Compensating: PaymentFailed / Timeout
    AwaitingStock --> AwaitingShipment: StockReserved
    AwaitingStock --> Compensating: StockFailed / Timeout
    AwaitingShipment --> Completed: ShipmentCreated
    AwaitingShipment --> Compensating: ShipmentFailed / Timeout
    Compensating --> Cancelled: AllCompensated
    Completed --> [*]
    Cancelled --> [*]
```

---

### flowchart showing the CAP decision for a cross-service business operation — partition detected → branch: choose Consistency (block, fail the operation, 2PC/CP) versus choose Availability (commit locally, converge later via saga/AP), annotating each branch with its business consequence

When a network partition occurs, the system must choose between blocking the operation to preserve consistency (CP — the 2PC path) or committing locally to stay available and converging later (AP — the saga path), and this diagram makes explicit that sagas are not a workaround but a deliberate architectural choice with predictable business consequences.

```mermaid
flowchart TD
    A[Cross-Service Business Operation] --> B{Network Partition Detected?}
    B -->|No| N[Proceed Normally]
    B -->|Yes| D{CAP Choice}
    D -->|Choose Consistency - CP| E[Block — Wait for All Participants]
    E --> F[2PC Coordinator Holds Locks]
    F --> G[Operation Fails\nData remains consistent\nBusiness request rejected]
    D -->|Choose Availability - AP| H[Commit Locally per Service]
    H --> I[Each Service Stays Available\nSaga Continues]
    I --> J[Eventual Convergence\nvia Events and Compensations\nBusiness request accepted]
```
