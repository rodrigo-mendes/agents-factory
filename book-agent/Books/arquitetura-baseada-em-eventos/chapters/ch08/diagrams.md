## Diagrams — Schema Evolution and Event Versioning

### A comparison table rendered as a decision matrix (class/table style) mapping schema changes to compatibility direction. Rows: "Add optional field with default", "Remove optional field", "Add required field (no default)", "Rename field", "Widen type (int->long)", "Narrow type (long->int)", "Change field meaning". Columns: "Backward-safe?", "Forward-safe?", "Full-safe?" with check/cross marks. Include a legend note that renaming = remove + add and is never safe.

This diagram classifies common schema changes into four safety groups, making it immediately clear which operations are safe to ship without consumer coordination. Understanding these groupings is the foundation of disciplined schema evolution: only full-safe changes can be deployed at any time without risk.

```mermaid
flowchart LR
    subgraph FULL["Full-Safe — Backward AND Forward"]
        F1["Add optional field with default"]
        F2["Widen type — int to long"]
    end

    subgraph BACK["Backward-Safe Only\n(new consumer reads old events)"]
        B1["Remove optional field\n(new schema supplies default)"]
    end

    subgraph FWD["Forward-Safe Only\n(old consumer reads new events)"]
        V1["Add required field — no default\n(old consumer ignores unknown fields)"]
    end

    subgraph UNSAFE["Never Safe — Breaks Both Directions"]
        U1["Rename field\n= remove + add — fails both ways"]
        U2["Narrow type — long to int\n(truncation risk)"]
        U3["Change field meaning\n(semantic breakage)"]
    end

    FULL -->|"Safe to ship anytime"| OK(["Deploy freely"])
    BACK -->|"Roll consumers forward first"| WARN(["Coordinate rollout"])
    FWD -->|"Breaks event replays"| WARN2(["Block for Event Sourcing"])
    UNSAFE -->|"Registry must reject"| BLOCK(["Build fails"])
```

---

### Sequence diagram of a schema registry interaction. Actors: Producer, Schema Registry, Broker, Consumer. Flow: (1) Producer submits new schema -> Registry runs compatibility check -> returns schema ID or rejects. (2) Producer serializes event with schema ID, publishes to Broker. (3) Consumer reads message, extracts schema ID, requests schema from Registry (cache miss), Registry returns schema. (4) Consumer deserializes. Show the rejection path as an alternative branch.

This sequence diagram shows how a schema registry converts a code-review policy into a hard build-time gate: incompatible schemas are rejected before a single event reaches the broker. The ID-based wire format is also shown, illustrating how consumers always resolve the exact schema the producer used — eliminating guesswork in deserialization.

```mermaid
sequenceDiagram
    participant P as Producer
    participant SR as Schema Registry
    participant BR as Broker
    participant C as Consumer

    P->>SR: Submit candidate schema
    alt Schema is compatible
        SR-->>P: Return schema ID
        P->>BR: Publish event (schema ID + binary payload)
        C->>BR: Read message
        C->>SR: Fetch schema by ID (cache miss)
        SR-->>C: Return schema definition
        C->>C: Deserialize event using schema
    else Schema violates compatibility rule
        SR-->>P: Reject — compatibility violation
        note over P: Build fails on producer side
    end
```

---

### Flowchart of an upcaster pipeline. Input: raw stored event with version tag. Branch on version: v1 enters upcaster v1->v2, output feeds upcaster v2->v3; v2 enters at v2->v3; v3 passes straight through. All paths converge to "current schema event" delivered to the domain handler. Emphasize that stored bytes are never mutated.

This flowchart illustrates how an upcaster chain promotes any historical event version to the current schema at read time, without ever touching the stored bytes. Each upcaster transforms exactly one version step, keeping individual transformations small, testable, and independently reasoned about — while the domain handler remains unaware that multiple historical formats exist.

```mermaid
flowchart TD
    STORE["Event Store\n(immutable — bytes never changed)"]
    STORE -->|read raw bytes| A["Stored Event + Version Tag"]
    A --> VER{Check version}

    VER -->|v1| U1["Upcaster v1 → v2\nsplit fullName into firstName + lastName"]
    VER -->|v2| U2["Upcaster v2 → v3\nconvert amount float to integer minor units"]
    VER -->|v3| PT["Pass Through\nno transformation needed"]

    U1 --> U2
    U2 --> CURR["Current Schema Event — v3"]
    PT --> CURR

    CURR --> DH["Domain Handler\n(sees only v3 — always)"]
```

---

### Sequence/flow diagram of a consumer-driven contract workflow. Consumer A and Consumer B each publish a contract (expected fields) to a shared contract broker. Producer's CI pipeline pulls all consumer contracts, runs its candidate schema against them, and either passes or fails the build. Contrast a small callout showing the producer-driven direction (schema pushed down) versus consumer-driven (contracts pulled up).

This diagram shows how consumer-driven contracts invert the authority relationship: instead of the producer declaring a schema and pushing it down, each consumer states what it needs and the producer's own CI pipeline is responsible for satisfying all of them. This is the mechanism that catches semantically breaking changes that a schema registry — which has no knowledge of actual consumers — cannot detect.

```mermaid
flowchart TD
    CA["Consumer A\npublishes contract\n(expected fields + types)"]
    CB["Consumer B\npublishes contract\n(expected fields + types)"]

    CA -->|upload| REPO["Shared Contract Repository\n(contract broker)"]
    CB -->|upload| REPO

    REPO -->|pull all contracts| CI["Producer CI Pipeline\n(candidate schema)"]

    CI --> CHK{Candidate schema\nsatisfies all contracts?}
    CHK -->|Yes — all consumers pass| PASS["Build Passes\nProduce deploys safely"]
    CHK -->|No — contract violated| FAIL["Build Fails\nProducer must fix schema\nbefore deployment"]

    subgraph CONTRAST["Direction of Authority"]
        PD["Producer-driven\nschema pushed down to consumers"]
        CDC["Consumer-driven\ncontracts pulled up by producer"]
    end
```

---
