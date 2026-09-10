# Chapter 3: Topologies and Messaging Infrastructure

## Opening Problem Statement

Chapter 2 taught how to model events as genuine business facts and treat every published event as an owned contract. But a well-modeled event is inert until something moves it from the service that produced it to the services that care. That "something" is your messaging infrastructure, and choosing it is one of the highest-leverage, hardest-to-reverse decisions in an event-driven system. Pick the wrong topology and you will spend the next two years fighting your own middleware: replaying events that cannot be replayed, ordering messages that were never ordered, and debugging a control flow that lives nowhere in your codebase. Senior architects do not get to be vague here. The distinction between a distributed log and a queue is not academic trivia; it dictates whether you can rebuild a read model from scratch, whether a slow consumer blocks a fast one, and whether "add another consumer" is a config change or a redesign. This chapter maps the two topology families, the two coordination models, and the three technology archetypes you will actually meet in production. By the end, you should be able to defend a choice, not just name one.

## Broker Topology Versus Mediator Topology

Every event-driven system falls into one of two structural patterns, and the difference is about where the control flow lives. In a **broker topology**, there is no central coordinator. Each service publishes events and subscribes to the events it needs, then reacts on its own. The business process is an emergent property of many independent reactions. Nobody owns the end-to-end flow; it exists only as the sum of local decisions. This is the pattern that gives EDA its famous decoupling and its equally famous debuggability problem.

In a **mediator topology**, a central component, the **mediator** or **orchestrator**, owns the process. It receives a triggering event, then issues commands to participant services in a deliberate sequence, tracking the state of the workflow as it advances. The mediator knows what step comes next, what to do when a step fails, and when the process is complete. The flow is explicit and lives in one place you can read.

The trade-off is the whole point. Broker topology maximizes decoupling and throughput but scatters the process across services, making it hard to answer "why did this order get stuck?" Mediator topology centralizes visibility and error handling but reintroduces a coordination dependency and a potential bottleneck. Neither is correct in the abstract.

[DIAGRAM: Two side-by-side flowcharts. Left labeled "Broker Topology": an event flows to a broker, and three services independently subscribe and react, each publishing further events with no central node. Right labeled "Mediator Topology": a triggering event enters a central Mediator, which issues numbered commands 1-2-3 to three services in sequence and receives replies.]

A useful heuristic: use broker topology for simple, mostly independent reactions where each subscriber's job is self-contained. Reach for a mediator when the process has real steps, ordering constraints, and compensation logic that someone must own. We will formalize the mediator as a saga process manager in Chapter 7; here it is enough to recognize the structural choice.

## Choreography Versus Orchestration

Broker and mediator are structural terms; **choreography** and **orchestration** are the behavioral coordination models that map onto them. They are frequently used as synonyms for the topologies, and for practical purposes the mapping holds: choreography is how a broker topology coordinates, orchestration is how a mediator topology coordinates.

In **choreography**, each service reacts to events and emits new events without being told to by any central authority. Think of dancers who each know their own steps and cues; the dance emerges from everyone reacting to the music and to each other. There is no conductor. An `OrderPlaced` event triggers the payment service, whose `PaymentCaptured` event triggers the shipping service, and so on. The flow is a chain of reactions.

In **orchestration**, a conductor, the orchestrator, explicitly directs each participant. It sends a "capture payment" command, waits for the result, then sends a "reserve inventory" command. The participants do not need to know about each other at all; they only know how to obey commands and report outcomes.

The tension is visibility versus autonomy. Choreography keeps services maximally independent but hides the process; to understand the whole flow you must trace events across many services. Orchestration makes the process legible and centralizes failure handling but couples participants to the orchestrator and creates a component that must scale and stay available.

| Dimension | Choreography | Orchestration |
|---|---|---|
| Control flow | Distributed, emergent | Centralized, explicit |
| Coupling | Lowest | Higher (to orchestrator) |
| Process visibility | Poor, must be traced | Excellent, lives in one place |
| Failure handling | Each service, locally | Orchestrator owns it |
| Best fit | Few steps, autonomous reactions | Many steps, ordering, compensation |

The opinionated position: default to choreography for small numbers of steps, and switch to orchestration the moment the process exceeds roughly four steps or requires compensation. Junior teams tend to over-orchestrate out of a desire for control; over-decoupled teams choreograph flows so complex that no one can explain them. Both are failure modes.

## Distributed Log Versus Queue

Now to the infrastructure itself. The single most consequential technical distinction in messaging is between a **queue** and a **distributed log**, because it determines what you can and cannot do with events after they are consumed.

A traditional **message queue**, such as RabbitMQ or Amazon SQS, treats a message as a work item to be consumed and destroyed. A producer puts a message on the queue; a consumer takes it off; once acknowledged, the message is gone. Queues excel at distributing work: many competing consumers pull from the same queue, and each message is handled by exactly one of them. This is the **competing consumers** pattern, and it is ideal for task distribution where messages are transient commands to do work.

A **distributed log**, exemplified by Apache Kafka, treats events as an append-only, durable sequence. Consuming an event does not delete it. Each consumer tracks its own position, the **offset**, in the log and reads forward at its own pace. The log retains events for a configured period regardless of who has read them. This changes everything downstream: a new consumer can join and read the entire history from the beginning, and an existing consumer can rewind and reprocess.

[DIAGRAM: Two contrasting diagrams. Top labeled "Queue": a producer sends messages into a queue; two competing consumers each pull different messages, and consumed messages disappear from the queue. Bottom labeled "Distributed Log": a producer appends events 0-1-2-3-4-5 to an ordered log; two independent consumer groups each maintain their own offset pointer at different positions, and no events are removed on consumption.]

The distinction is not "which is better" but "which model fits your need." If the message is a transient command consumed once, a queue is simpler and cheaper. If the event is a durable fact that multiple independent consumers need, now and in the future, and that you may need to replay, the log is the right tool. Notice how this echoes Chapter 2: durable facts want a log; transient work items want a queue.

## Publish/Subscribe, Partitions, and Consumer Groups

Three mechanics make the log model work at scale, and senior engineers must understand all three precisely.

**Publish/subscribe** (pub/sub) means a producer publishes to a **topic** and any number of subscribers receive a copy. This is fan-out: one event, many independent readers. It contrasts with point-to-point queuing, where one message goes to one consumer. In cloud terms, Amazon SNS is a pub/sub fan-out service and SQS is a queue; the common SNS-to-SQS pattern deliberately combines both, using SNS to fan an event out to several SQS queues so each downstream service gets its own private copy to consume at its own pace.

**Partitions** are how a log scales horizontally and preserves order. A topic is split into partitions, and each event is routed to a partition by a **partition key**, typically an entity ID such as `orderId`. Kafka guarantees ordering only within a partition, never across partitions. This is the rule that catches teams off guard: if global ordering matters you are limited to one partition and therefore no parallelism, so you deliberately choose a key that keeps causally related events together while letting unrelated entities spread across partitions for throughput.

[CODE: Pseudocode showing a producer publishing OrderPlaced and OrderShipped events using orderId as the partition key, so all events for the same order land on the same partition and remain ordered, while events for different orders distribute across partitions.]

**Consumer groups** coordinate parallel consumption without duplication. Consumers sharing a group ID split the partitions among themselves; each partition is read by exactly one consumer in the group, giving you competing-consumers parallelism inside the log model. Meanwhile, a different group reading the same topic gets its own full copy of the stream. This is the elegant unification: within a group you get work distribution like a queue, across groups you get fan-out like pub/sub, all from the same durable log.

## Retention, Replay, and Reprocessing

The log's defining superpower is that events persist after consumption, and this is where the log earns its cost. **Retention** is the policy governing how long events are kept, by time (for example, seven days) or by size, or indefinitely via **log compaction**, which keeps the latest event per key forever. Retention is a first-class architectural decision, not a default to accept blindly, because it sets the boundary of what history you can reach.

**Replay** is reading historical events again by resetting a consumer's offset backward. **Reprocessing** is the application of replay: you deploy a new version of a projection, reset its consumer group to offset zero, and rebuild its entire state from history. This capability is what makes Event Sourcing and CQRS practical, and both depend on it in later chapters. With a queue, none of this exists; once a message is acknowledged it is gone, so a bug that corrupts a read model is unrecoverable from the messaging layer.

This single capability is the strongest argument for a log over a queue in fact-oriented systems, and the reason Kafka anchors so many event-driven platforms. But it is not free. Retention costs storage, replay can flood downstream systems if not throttled, and reprocessing demands that consumers be idempotent, because replayed events will be seen again. That idempotency requirement is not optional, and it is exactly the subject of Chapter 4.

With the mechanics established, the technology choice becomes a mapping exercise rather than a popularity contest.

[DIAGRAM: A decision flowchart guiding technology selection. Start: "Is the message a durable fact multiple consumers may replay?" Yes leads to "Distributed log (Kafka / managed streaming)". No leads to "Is it transient work to distribute?" which leads to "Queue (RabbitMQ / SQS)". A side branch: "Need simple fan-out of notifications?" leads to "Pub/sub (SNS) fanning into per-consumer SQS queues".]

## Key Takeaways

- **Topology is a control-flow decision.** Broker topology decouples but scatters the process; mediator topology centralizes visibility at the cost of a coordination dependency. Choreography and orchestration are the behavioral models that map onto them.
- **Queue and log are fundamentally different tools.** A queue destroys messages on consumption and distributes work; a distributed log retains events and lets independent consumers read, rewind, and replay.
- **Partitions preserve order only within a partition.** Choose a partition key that keeps causally related events together; global ordering costs you parallelism.
- **Consumer groups unify queue and pub/sub semantics.** Within a group you get competing-consumers parallelism; across groups you get fan-out, all from one log.
- **Retention and replay are the log's decisive advantage** and the foundation for Event Sourcing and CQRS, but they demand idempotent consumers and deliberate retention policy.

## What's Next

Replay guarantees that consumers will see the same event more than once, so Chapter 4 confronts delivery guarantees head-on and shows how to build idempotent consumers under at-least-once delivery.
