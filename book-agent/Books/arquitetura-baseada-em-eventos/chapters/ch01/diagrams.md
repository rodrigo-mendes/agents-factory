## Diagrams — Foundations of Event-Driven Architecture

### A side-by-side comparison (flowchart) contrasting a command flow — one sender arrow to one receiver labeled "expects execution, can be rejected" — versus an event flow — one producer fanning out to three independent consumers labeled "announces a fact, expects nothing".

Commands and events differ fundamentally in intent and coupling: a command targets one specific receiver and demands a response, while an event broadcasts a fact to any number of independent consumers who may or may not exist at publish time. Understanding this contrast is the first step to avoiding the design mistake of publishing commands disguised as events.

```mermaid
flowchart TD
    subgraph CMD["Command Flow"]
        Sender["Sender"] -->|"Do this"| Receiver["Receiver"]
        Receiver -.->|"Executed or Rejected"| Sender
    end

    subgraph EVT["Event Flow"]
        Producer["Producer"] -->|"This happened"| ConsumerA["Consumer A"]
        Producer --> ConsumerB["Consumer B"]
        Producer --> ConsumerC["Consumer C"]
    end
```

---

### A sequence diagram contrasting two scenarios. Top: synchronous chain of five services where a failure at service 4 propagates a timeout back to the client. Bottom: the same actors communicating through a broker, where service 4 being down leaves messages buffered and the client already acknowledged.

This diagram makes the availability cost of synchronous chains concrete: a single failing service cascades timeouts all the way back to the caller, whereas a broker-mediated async flow absorbs the failure by buffering messages, allowing the client to receive an acknowledgment immediately and the healthy consumers to continue processing independently.

```mermaid
flowchart TD
    subgraph SYNC["Scenario A — Synchronous Chain: failure propagates"]
        C1[Client] --> SV1[Service 1]
        SV1 --> SV2[Service 2]
        SV2 --> SV3[Service 3]
        SV3 --> SV4["Service 4 — DOWN"]
        SV4 -.->|Timeout| SV3
        SV3 -.->|Timeout| SV2
        SV2 -.->|Timeout| SV1
        SV1 -.->|Timeout| C1
    end

    subgraph ASYNC["Scenario B — Async via Broker: failure buffered"]
        C2[Client] -->|Publish event| BR[Broker]
        BR -->|ACK — immediate| C2
        BR --> B1[Service 1]
        BR --> B2[Service 2]
        BR --> B3[Service 3]
        BR -.->|Messages buffered| B4["Service 4 — DOWN"]
    end
```

---
