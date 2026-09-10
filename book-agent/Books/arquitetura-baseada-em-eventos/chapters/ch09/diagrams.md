## Diagrams — Observability, Debugging, and Operations

### A sequence diagram showing an OrderPlaced event flowing from an API gateway through a broker to a Payment consumer, which publishes PaymentCaptured, which flows to an Email consumer. Each hop carries the same correlation_id, and each new event's causation_id points to the previous event. Trace spans link across each broker hop.

This diagram shows how a single correlation ID threads through every service in an asynchronous flow while causation IDs preserve the parent-child relationship at each hop. It illustrates why both IDs are necessary: correlation groups the whole transaction, and causation rebuilds the exact causal order, enabling distributed tracing across broker hops via span links.

```mermaid
sequenceDiagram
    participant GW as API Gateway
    participant BR as Broker
    participant PAY as Payment Service
    participant EMAIL as Email Service

    GW->>BR: OrderPlaced<br/>msg_id=M1, corr=C1, cause=—
    Note over GW,BR: Trace Span S1

    BR->>PAY: OrderPlaced<br/>msg_id=M1, corr=C1, cause=—
    Note over BR,PAY: Span S2 (linked to S1)

    PAY->>BR: PaymentCaptured<br/>msg_id=M2, corr=C1, cause=M1
    Note over PAY,BR: Trace Span S3

    BR->>EMAIL: PaymentCaptured<br/>msg_id=M2, corr=C1, cause=M1
    Note over BR,EMAIL: Span S4 (linked to S3)

    EMAIL-->>BR: Ack (EmailSent)
    Note over EMAIL,BR: Span S4 ends
```

---

### A flowchart decision tree for diagnosing rising consumer lag. Branches on throughput near zero (stuck consumer, check poison message) versus throughput high (scale out or optimize), and on whether lag drains during off-peak.

This decision tree gives on-call engineers a structured path from a rising-lag alert to a concrete action, distinguishing the two fundamentally different failure modes — a consumer that is overwhelmed versus one that is completely stuck — because the remediation for each is different and applying the wrong fix wastes critical incident time.

```mermaid
flowchart TD
    A[Rising Consumer Lag Detected] --> B{Throughput near zero?}

    B -->|Yes - consumer stuck| C[Suspect poison message]
    C --> D[Inspect DLQ for failed messages]
    D --> E[Apply bounded retries + DLQ routing]
    E --> F[Partition unblocked — lag resumes draining]

    B -->|No - throughput is high| G{Does lag drain during off-peak?}
    G -->|Yes - bursty traffic| H[Normal burst pattern]
    H --> I[Verify peak lag fully drains]
    G -->|No - lag keeps climbing| J[Consumer slower than producer]
    J --> K{Handler optimization feasible?}
    K -->|Yes| L[Optimize consumer handler]
    K -->|No| M[Scale out consumer instances]
```

---

### A flowchart of the reprocessing workflow — DLQ alert fires, engineer inspects message and root cause, deploys fix, verifies consumer idempotency, then replays messages in throttled batches back to the source topic, monitoring lag during replay.

This flowchart captures the safe reprocessing procedure that prevents operators from triggering secondary outages when draining a DLQ. It emphasizes the mandatory order of operations — fix first, verify idempotency, then replay in controlled batches — because skipping any step can turn a recovery into a second incident.

```mermaid
flowchart TD
    A[DLQ Alert: depth gt 0] --> B[Inspect DLQ messages]
    B --> C[Identify root cause]
    C --> D[Deploy fix to consumer]
    D --> E{Consumer idempotent?}

    E -->|No| F[Implement idempotency guard]
    F --> G[Replay messages in throttled batches]
    E -->|Yes| G

    G --> H[Preserve original corr_id and cause_id]
    H --> I[Monitor consumer lag during replay]
    I --> J{Lag stable or decreasing?}

    J -->|Yes| K[Continue replay until DLQ empty]
    K --> L[Incident resolved]
    J -->|No| M[Pause replay]
    M --> N[Investigate downstream health]
    N --> G
```

---
