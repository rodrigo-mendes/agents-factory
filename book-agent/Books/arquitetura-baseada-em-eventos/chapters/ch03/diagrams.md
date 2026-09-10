## Diagrams — Topologies and Messaging Infrastructure

### Two side-by-side flowcharts. Left labeled "Broker Topology": an event flows to a broker, and three services independently subscribe and react, each publishing further events with no central node. Right labeled "Mediator Topology": a triggering event enters a central Mediator, which issues numbered commands 1-2-3 to three services in sequence and receives replies.

This diagram contrasts the two fundamental EDA structural patterns: Broker Topology, where control flow is emergent and no single node owns the process, versus Mediator Topology, where a central coordinator drives each step in a deliberate sequence. Understanding the contrast is the prerequisite for making the topology choice a defensible architectural decision.

```mermaid
flowchart LR
    subgraph BT["Broker Topology"]
        direction TD
        E1[Incoming Event] --> BR[(Broker)]
        BR --> SA[Service A]
        BR --> SB[Service B]
        BR --> SC[Service C]
        SA --> EA[New Event]
        SB --> EB[New Event]
        SC --> EC[New Event]
    end

    subgraph MT["Mediator Topology"]
        direction TD
        TE[Trigger Event] --> MD[Mediator]
        MD -->|"1 - Command"| PA[Service A]
        MD -->|"2 - Command"| PB[Service B]
        MD -->|"3 - Command"| PC[Service C]
        PA -.->|Reply| MD
        PB -.->|Reply| MD
        PC -.->|Reply| MD
    end
```

---

### Two contrasting diagrams. Top labeled "Queue": a producer sends messages into a queue; two competing consumers each pull different messages, and consumed messages disappear from the queue. Bottom labeled "Distributed Log": a producer appends events 0-1-2-3-4-5 to an ordered log; two independent consumer groups each maintain their own offset pointer at different positions, and no events are removed on consumption.

This diagram illustrates the single most consequential infrastructure distinction in event-driven systems: a queue destroys messages on consumption, enabling competing-consumers work distribution, while a distributed log retains the ordered event sequence, enabling independent consumer groups to read at their own pace, rewind, and replay.

```mermaid
flowchart TD
    subgraph QUEUE["Queue Model"]
        direction LR
        PQ[Producer] --> Q[(Queue)]
        Q -->|"Message A"| CA[Consumer A]
        Q -->|"Message B"| CB[Consumer B]
        CA --> DA["Message A — deleted"]
        CB --> DB["Message B — deleted"]
    end

    subgraph LOG["Distributed Log Model"]
        direction LR
        PL[Producer] --> LS["Log  0  1  2  3  4  5"]
        LS --> G1["Consumer Group 1\nOffset: 4"]
        LS --> G2["Consumer Group 2\nOffset: 1"]
    end
```

---

### A decision flowchart guiding technology selection. Start: "Is the message a durable fact multiple consumers may replay?" Yes leads to "Distributed log (Kafka / managed streaming)". No leads to "Is it transient work to distribute?" which leads to "Queue (RabbitMQ / SQS)". A side branch: "Need simple fan-out of notifications?" leads to "Pub/sub (SNS) fanning into per-consumer SQS queues".

This flowchart turns the chapter's conceptual distinctions into an actionable decision tree, guiding practitioners from the nature of the message to the appropriate technology archetype. It frames technology selection as a mapping exercise rather than a popularity contest.

```mermaid
flowchart TD
    START([Start]) --> Q1{"Durable fact that multiple\nconsumers may replay?"}
    Q1 -->|Yes| LOG["Distributed Log\nKafka / Managed Streaming"]
    Q1 -->|No| Q2{"Transient work item\nto distribute once?"}
    Q2 -->|Yes| QUEUE["Queue\nRabbitMQ / Amazon SQS"]
    Q2 -->|No| Q3{"Simple fan-out\nof notifications?"}
    Q3 -->|Yes| FANOUT["Pub/Sub — Amazon SNS\nfanning into per-consumer SQS queues"]
    Q3 -->|No| REVIEW["Re-examine message semantics"]
```

---
