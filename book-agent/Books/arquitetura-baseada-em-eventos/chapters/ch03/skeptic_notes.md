## Skeptical Review — Topologies and Messaging Infrastructure
Reviewer profile: Rigorous technical skeptic
Date: 2026-09-01

---

### Retention, Replay, and Reprocessing

> **Critical Note:** The prose states that log compaction "keeps the latest event per key forever" and presents it as a retention option alongside time-based or size-based policies — but this conflates two incompatible goals. Log compaction is a compaction strategy that actively deletes all intermediate events for a given key, retaining only the most recent value. A team that enables compaction on a topic and later attempts full replay to rebuild a projection will silently receive a truncated history: every intermediate state transition for each entity is gone. The phrase "keeps the latest event per key forever" is technically accurate for the surviving record, but it implies durability of history rather than destruction of it. For a chapter whose entire argument for choosing a log over a queue rests on replay and reprocessing, recommending compaction without a hard warning about what it erases directly undermines the chapter's core thesis.

**Severity:** blocking
**Suggested fix:** Add an explicit callout that log compaction is incompatible with event-history replay. Reserve it for changelog use cases (maintaining current state per key, as in Kafka Streams materialized views or KTables), and flag that event-sourced systems should use time-based or size-based retention with infinite or very long windows, never compaction on fact-carrying topics.

---

### Retention, Replay, and Reprocessing

> **Critical Note:** The prose correctly states that reprocessing "demands that consumers be idempotent, because replayed events will be seen again" — but idempotency in the consumer's own data writes is only one layer of the problem. Any consumer that triggers external side effects during processing (sending an email, calling a payment gateway, invoking a webhook, publishing a notification to an external system) will re-execute those side effects on replay unless they are independently deduped at the external boundary. This failure mode is extremely common and causes real production incidents: replaying six months of `OrderPlaced` events re-sends confirmation emails to customers and re-charges payment methods. The prose defers all idempotency detail to Chapter 4, but senior engineers reading this chapter need at least a one-sentence warning that external side effects are a separate, harder problem than idempotent storage writes.

**Severity:** important
**Suggested fix:** Add a sentence distinguishing idempotent local writes (covered in Chapter 4) from idempotent external side effects (require deduplication tokens at the external API boundary or suppression flags during reprocessing runs). A single sentence of foreshadowing prevents teams from assuming "idempotent consumer" fully covers the replay safety problem.

---

### Retention, Replay, and Reprocessing

> **Critical Note:** The chapter argues strongly for replay and reprocessing as the log's decisive advantage, but never addresses schema evolution — arguably the biggest operational risk in long-lived logs. If a topic retains events for two years, consumers performing full replay will encounter events serialized under schemas that predate multiple breaking changes. Avro, Protobuf, and JSON Schema all have compatibility rules, but enforcing them, maintaining a schema registry, and writing consumer deserializers that handle both old and new shapes is non-trivial. A team that deploys a new consumer, resets to offset zero, and hits a three-year-old event in a deprecated Avro schema will get a deserialization exception and a stalled consumer group. For an audience of senior architects, treating replay as straightforward while omitting schema evolution is a significant gap.

**Severity:** important
**Suggested fix:** Add a brief paragraph noting that durable retention obligates a schema evolution strategy (schema registry with backward/forward compatibility rules, or a versioned envelope). Reference this as a prerequisite for making replay operationally safe rather than just theoretically possible.

---

### Broker Topology Versus Mediator Topology

> **Critical Note:** The prose opens with "every event-driven system falls into one of two structural patterns" and then builds the entire topology framework on the broker/mediator binary. In practice, large production systems routinely combine both: domain events flow over a broker while cross-domain sagas are orchestrated via a mediator, often within the same deployment. Presenting the choice as mutually exclusive at the system level leads architects toward a false either/or decision at architecture time, when the real question is "which topology per process boundary?" The binary framing is pedagogically convenient but actively misleading for senior practitioners designing systems with heterogeneous workflows.

**Severity:** important
**Suggested fix:** Change the framing from "every system falls into one of two" to "each workflow or process boundary can be classified as one of two." Add one sentence acknowledging that most non-trivial systems combine both, often with broker topology at the domain boundary and mediator topology for cross-domain sagas, and that the choice is made per process, not per system.

---

### Choreography Versus Orchestration

> **Critical Note:** The prose offers "switch to orchestration the moment the process exceeds roughly four steps" as an opinionated but actionable threshold. This number has no empirical basis and is highly context-dependent. Two-step flows with external payment systems and regulatory compensation requirements often demand a mediator; eight-step internal data pipelines with fully autonomous services and mature observability can operate safely as choreography. The relevant variables are not step count but: whether compensation is required (sagas), whether the process has a business owner who needs an audit trail, what observability tooling is in place, and whether services are autonomously deployable. Presenting a step count as the decision threshold will cause teams to misclassify their workflows.

**Severity:** important
**Suggested fix:** Replace the four-step rule with a multi-factor checklist: compensation logic required, external audit trail needed, process has a single business owner, or team lacks distributed tracing. Any one of those factors warrants an orchestrator regardless of step count. The step count can remain as a rough signal, not a threshold.

---

### Choreography Versus Orchestration

> **Critical Note:** The comparison table lists choreography's coupling as "Lowest" without qualification. This is true at the deployment and runtime level but misleading at the data contract level. In choreography, every consumer must understand the schema of every upstream event it subscribes to; a breaking schema change in `OrderPlaced` can silently break three independent consumers simultaneously with no compile-time or deploy-time signal. Orchestration localizes schema coupling to the orchestrator-participant boundary, which is narrower and easier to version. For a senior audience that manages schema evolution, presenting choreography as categorically lower coupling can lead to underinvesting in event schema governance.

**Severity:** minor
**Suggested fix:** Add a table footnote or inline qualifier: "Lowest runtime coupling, but schema coupling is distributed across all subscribers — event schema governance is non-optional in choreography."

---

### Distributed Log Versus Queue

> **Critical Note:** The prose states that in a traditional message queue "once acknowledged, the message is gone." For Amazon SQS, this is a significant oversimplification: SQS standard queues retain messages for 1 to 14 days regardless of consumption, dead-letter queues capture failed messages for independent analysis and retry, and SQS FIFO queues provide deduplication within a five-minute window. RabbitMQ has persistent queues, dead-letter exchanges, and lazy queues that can buffer millions of messages to disk. These are not full replay capabilities, but they are not "message is gone on acknowledge" either. The oversimplification could lead teams to dismiss queue-based systems prematurely or fail to leverage retention features that do exist.

**Severity:** minor
**Suggested fix:** Qualify the statement: "A queue does not retain messages for arbitrary replay — once a consumer acknowledges a message, it is removed from active delivery — but configurable retention windows and dead-letter queues exist in both SQS and RabbitMQ for operational recovery, not architectural replay."

---

## Summary
- Total notes: 7
- Blocking (inline callout): 1
- Important (collapsed): 4
- Minor (file only): 2

**Top 3 items requiring attention:**

1. [Retention, Replay, and Reprocessing] Log compaction silently destroys intermediate event history — directly contradicts the chapter's core argument for replay
2. [Retention, Replay, and Reprocessing] External side effects during replay are not idempotency-safe through consumer-level deduplication alone — a production incident waiting to happen
3. [Broker Topology Versus Mediator Topology] Binary "one of two patterns" framing misrepresents how real systems combine both topologies per process boundary
