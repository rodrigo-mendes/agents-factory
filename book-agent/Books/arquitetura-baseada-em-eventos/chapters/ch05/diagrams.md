## Diagrams — CQRS — Separating Reads and Writes

### side-by-side comparison (two-column) showing a normalized write model — Order, OrderLine, Product, Customer tables with foreign keys — versus a denormalized read model — a single flat CustomerOrderView document with embedded line items and precomputed lifetime value. Label the arrow between them "projection".

The write model (left) keeps data normalized across four tables to enforce invariants and prevent anomalies; the read model (right) flattens those tables into a single document pre-optimized for the query screen. The "projection" arrow between them represents the event-driven process that continuously derives the read shape from write-side events — this is the structural core of CQRS.

```mermaid
flowchart LR
    subgraph WriteModel["Write Model (Normalized)"]
        direction TB
        CU[Customer\n- customerId PK\n- name\n- email]
        OR[Order\n- orderId PK\n- customerId FK\n- createdAt]
        OL[OrderLine\n- lineId PK\n- orderId FK\n- productId FK\n- qty]
        PR[Product\n- productId PK\n- name\n- thumbnailUrl]
        CU -->|1 : N| OR
        OR -->|1 : N| OL
        OL -->|N : 1| PR
    end

    WriteModel -->|projection| ReadModel

    subgraph ReadModel["Read Model (Denormalized)"]
        direction TB
        COV["CustomerOrderView\n────────────────────\n customerId\n orderId\n productNames\n productThumbnails\n shippingStatus\n orderTotal\n lifetimeValue (precomputed)"]
    end
```

---

### flowchart showing the command path (Command -> Command Handler -> Write Store) emitting an event onto an event bus, then two independent projection consumers reading from the bus and writing into two different read stores (a SQL read model for order history, an Elasticsearch index for product search). Query requests hit the read stores directly, bypassing the write store.

This diagram shows how events produced by the command path fan out to purpose-built projections, each maintaining its own read store optimized for a specific query pattern. It illustrates why CQRS allows the read and write sides to use different storage engines and scale independently.

```mermaid
flowchart TD
    CMD[Command] --> CH[Command Handler]
    CH --> WS[(Write Store\nRelational DB)]
    CH --> EB[Event Bus]

    EB --> P1[Projection\nOrder History]
    EB --> P2[Projection\nProduct Search]

    P1 --> RS1[(SQL Read Model\nOrder History)]
    P2 --> RS2[(Elasticsearch Index\nProduct Search)]

    Q1[Query: Order History] --> RS1
    Q2[Query: Product Search] --> RS2
```

---

### sequence diagram showing a client sending a command, the write store committing and publishing an event, the client immediately issuing a query that returns stale data, then the projection applying the event, then a second query returning fresh data. Annotate the gap between commit and projection as "eventual consistency window / replication lag".

This sequence diagram makes the eventual-consistency cost of CQRS visible: a query issued immediately after a successful command can return stale data because the projection has not yet processed the event. Understanding this window — and the business tolerance for it — is the key design decision when adopting CQRS.

```mermaid
sequenceDiagram
    participant C as Client
    participant WS as Write Store
    participant EB as Event Bus
    participant PR as Projection
    participant RS as Read Store

    C->>WS: Command (CancelOrder)
    WS-->>EB: Publish OrderCancelled event
    WS-->>C: Acknowledgement (success)

    C->>RS: Query (GetOrderStatus)
    RS-->>C: Stale response — order still Active

    Note over EB,RS: eventual consistency window / replication lag

    EB->>PR: Deliver OrderCancelled event
    PR->>RS: Upsert read model (status = Cancelled)

    C->>RS: Query (GetOrderStatus)
    RS-->>C: Fresh response — order Cancelled
```

---
