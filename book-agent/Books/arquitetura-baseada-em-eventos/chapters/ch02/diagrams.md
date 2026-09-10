## Diagrams — Modeling Events as Domain Facts

### flowchart showing a domain event produced inside Context A, passing through a translation/anti-corruption boundary that transforms it into an integration event, which is then consumed by Context B; label the boundary as the bounded-context edge

A domain event produced inside a bounded context must be translated into an integration event before it crosses the context boundary; this seam preserves each team's freedom to refactor their internal model independently.

```mermaid
flowchart LR
    subgraph CA["Context A (Producer)"]
        DE["Domain Event\n— OrderAggregateUpdated —"]
        TL["Translation Layer"]
        IE["Integration Event\n— OrderPlaced —"]
        DE --> TL --> IE
    end
    subgraph CB["Context B (Consumer)"]
        ACL["Anti-Corruption Layer"]
        CBM["Internal Model"]
        ACL --> CBM
    end
    IE -->|"Bounded-Context Edge"| ACL
```

---

### sequence-style timeline of an Event Storming wall showing past-tense domain events left to right, with commands, aggregates, and a policy note, and a highlighted boundary where the ubiquitous language changes

An Event Storming timeline maps business facts in past tense from left to right, surfacing commands, aggregates, and policies; the point where the ubiquitous language shifts marks a bounded-context boundary and signals a candidate integration event.

```mermaid
flowchart LR
    subgraph SALES["Sales Context"]
        CMD1["Command: Place Order"]
        EV1["Event: Order Placed"]
        EV2["Event: Payment Authorized"]
        AGG1["Aggregate: Order"]
        POL1["Policy: When Payment Authorized"]
        CMD1 --> EV1 --> EV2 --> AGG1 --> POL1
    end
    subgraph SHIPPING["Shipping Context"]
        EV3["Event: Order Shipped"]
        AGG2["Aggregate: Shipment"]
        EV3 --> AGG2
    end
    POL1 -->|"Language Boundary"| EV3
```

---

### comparison chart contrasting a clean stream of business-meaningful events against a noisy stream polluted with persistence and infrastructure events, showing how consumers lose signal in the noisy case

Mixing technical noise into domain topics floods consumers with irrelevant signals, making it impossible to distinguish real business facts from implementation artifacts; keeping domain topics clean preserves the stream as a reliable business ledger.

```mermaid
flowchart TD
    subgraph CLEAN["Clean Stream — Business Events"]
        CE1["OrderPlaced"]
        CE2["PaymentCaptured"]
        CE3["OrderShipped"]
        CC["Consumer — Clear Signal"]
        CE1 --> CE2 --> CE3 --> CC
    end
    subgraph NOISY["Noisy Stream — Mixed Events"]
        NE1["OrderPlaced"]
        NE2["EntitySaved"]
        NE3["CacheEvicted"]
        NE4["RowUpdated"]
        NE5["PaymentCaptured"]
        NC["Consumer — Signal Lost"]
        NE1 --> NE2 --> NE3 --> NE4 --> NE5 --> NC
    end
```

---
