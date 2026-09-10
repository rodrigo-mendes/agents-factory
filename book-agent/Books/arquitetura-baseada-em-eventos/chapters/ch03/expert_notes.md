## Expert Review — Topologies and Messaging Infrastructure
Reviewer profile: Senior practitioner, 10+ years, cloud-native microservices and corporate distributed systems
Date: 2026-09-01

---

### Publish/Subscribe, Partitions, and Consumer Groups

> **Expert Note:** The prose correctly states that ordering is guaranteed only within a partition and that the partition key should keep causally related events together. What is not said — and what routinely causes production incidents — is the hot-partition problem: if a small number of keys (a high-volume merchant ID, a viral product) accounts for a large share of events, those partitions receive disproportionate write pressure and lag accumulates on the consumers assigned to them while other partitions sit idle. The naive fix of switching to a composite key (e.g., `merchantId + orderId`) restores distribution but breaks the causal ordering guarantee across orders for that merchant. Teams must profile key cardinality before going live. When true hot-key situations are unavoidable, a common mitigation is key salting with a bounded random suffix (e.g., `orderId-0` through `orderId-N`) combined with a merge step, accepting that ordering is coordinated in the consumer rather than guaranteed by the broker.

**Integration level:** inline callout
**Priority:** high

---

### Publish/Subscribe, Partitions, and Consumer Groups

> **Expert Note:** The prose explains consumer groups clearly but does not flag the rebalancing hazard. In Kafka's original eager rebalancing protocol, every time a consumer joins, leaves, or crashes, the entire group stops processing and reassigns all partitions — a stop-the-world pause that can range from seconds to tens of seconds depending on session timeouts and partition count. Under `at-least-once` delivery this window also produces duplicates, because in-flight records are re-delivered to newly assigned consumers. Kafka 2.4 introduced Incremental Cooperative Rebalancing (the `CooperativeStickyAssignor` assignment strategy), which transfers only the partitions that must move, leaving the rest actively consumed. This is not the default in many client versions, so production deployments should explicitly configure `partition.assignment.strategy=CooperativeStickyAssignor` and tune `session.timeout.ms` and `heartbeat.interval.ms` deliberately. Ignoring this is a common source of mystery lag spikes during routine deployments.

**Integration level:** inline callout
**Priority:** high

---

### Retention, Replay, and Reprocessing

> **Expert Note:** Replay is the log's most powerful capability, but it introduces a failure mode the prose does not cover: schema evolution. Events written months or years ago carry older schema versions. When a consumer is reset to offset zero and processes that history, its current deserializer must be backward-compatible with every schema version it will encounter, not just the current one. Without a schema registry (Confluent Schema Registry or AWS Glue Schema Registry) enforcing a compatibility policy (typically BACKWARD or FULL), a reprocessing job will fail partway through history on the first breaking schema change — usually discovered in a high-pressure incident recovery window. The practical rule: treat schema registry enrollment and compatibility enforcement as a prerequisite to enabling replay in production, not an afterthought.

**Integration level:** inline callout
**Priority:** high

---

### Choreography Versus Orchestration

> **Expert Note:** The prose frames the choice as system-wide, but the most resilient production architectures apply both models simultaneously at different granularity levels. The canonical pattern: use orchestration inside a bounded context (a saga process manager owns multi-step workflows within the Payment domain) and use choreography between bounded contexts (Payment publishes `PaymentCaptured`; Fulfillment subscribes without knowing that Payment exists). This aligns with DDD's autonomous bounded-context principle and prevents the orchestrator from accumulating cross-domain knowledge that collapses the boundary. Teams that miss this often build a "god orchestrator" that ends up knowing about every service, recreating the coupling they were trying to eliminate.

**Integration level:** collapsed block
**Priority:** medium

---

### Broker Topology Versus Mediator Topology

> **Expert Note:** The prose correctly identifies the mediator as a potential bottleneck, but in practice the more dangerous production risk is blast radius, not throughput. Modern workflow engines (AWS Step Functions, Temporal, Conductor) scale horizontally and are rarely CPU- or throughput-limited. The real danger is that a bug in the orchestrator's business logic, or a bad deployment that corrupts workflow state, simultaneously affects every in-flight instance of every workflow type managed by that orchestrator. Teams mitigate this with workflow versioning (Temporal's versioning API, Step Functions state machine versions), strict canary deployment of orchestrator changes, and separation of workflow definitions by domain boundary so a defect in Order workflows cannot corrupt Payment workflows.

**Integration level:** collapsed block
**Priority:** medium

---

### Distributed Log Versus Queue

> **Expert Note:** The binary framing of log versus queue, while pedagogically useful, understates how much the boundary has shifted. RabbitMQ 3.9 (2021) introduced Streams, a durable, append-only, replayable log abstraction built into the broker, with consumer offset tracking semantics nearly identical to Kafka. Teams evaluating RabbitMQ for new EDA workloads should assess Streams before dismissing it as a queue-only tool. The meaningful differentiators between Kafka and RabbitMQ Streams at this point are ecosystem maturity, Kafka's richer partition-level parallelism controls, and the managed-service landscape (MSK, Confluent Cloud), not the fundamental replay capability.

**Integration level:** collapsed block
**Priority:** medium

---

### Retention, Replay, and Reprocessing

> **Expert Note:** The prose accurately defines log compaction as keeping the latest event per key forever, which is correct. The nuance worth adding is that log-compacted topics are incompatible with full event sourcing. Event sourcing requires every event for an entity, not just the latest value; compaction discards intermediate events, which means you can derive current state but cannot reconstruct the audit trail or time-travel queries. Log compaction is appropriate for changelog topics (CDC, KTable materialization) and not for event-sourced aggregates, where infinite retention or external event store archival (DynamoDB, EventStoreDB) is the correct strategy. Teams that enable compaction on an event-sourced topic discover the data loss only when they attempt a full replay.

**Integration level:** collapsed block
**Priority:** medium

---

### Choreography Versus Orchestration

> **Expert Note:** The "roughly four steps" heuristic for switching from choreography to orchestration is a useful starting signal, but step count is a proxy for the real criterion: whether the process has observable, ownable failure modes requiring compensating transactions. A three-step choreography with complex distributed compensation (partial refunds, inventory re-reservations) is far more dangerous to leave in choreography than a six-step orchestration with simple idempotent rollback. In practice, the trigger for introducing an orchestrator is the moment the team cannot answer "what happens to this order if step 2 succeeds but step 3 times out?" with a clear, testable answer from reading a single artefact.

**Integration level:** file only
**Priority:** low

---

## Summary
- Total notes: 8
- High priority (inline callout): 3
- Medium priority (collapsed block): 4
- Low priority (file only): 1

**Top 3 notes to integrate:**
1. [Publish/Subscribe, Partitions, and Consumer Groups] Hot-partition problem with naive key choice and mitigation via key salting
2. [Publish/Subscribe, Partitions, and Consumer Groups] Consumer group rebalancing stop-the-world pauses and CooperativeStickyAssignor opt-in
3. [Retention, Replay, and Reprocessing] Schema evolution as a prerequisite gating condition for replay in production
