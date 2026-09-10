# Event-Driven Architecture
### CQRS, Event Sourcing, Trade-offs and Pitfalls for Senior Architects

## Chapter 1: Foundations of Event-Driven Architecture
**Objective:** Establish what an event is and why the asynchronous, distributed style of Event-Driven Architecture solves problems the request-response model cannot.
**Description:** The chapter defines an event as an immutable fact of the past and contrasts the temporal coupling of the synchronous model with the decoupling of event-driven communication. It situates EDA in the context of corporate distributed systems and cloud-native microservices, delineating when it adds value and when it is over-engineering.
**Key Concepts:**
- Event as immutable fact versus command and message
- Temporal, spatial, and flow coupling
- Request-response model versus asynchronous communication
- Notification, event-carried state transfer, and the four event styles (Fowler)
- Decision criteria: when to adopt and when to avoid

## Chapter 2: Modeling Events as Domain Facts
**Objective:** Teach how to design events that express meaningful business facts, avoiding the pitfall of publishing technical noise as if it were a domain event.
**Description:** The chapter applies Domain-Driven Design and Event Storming to the discovery and design of domain events. It differentiates domain events from integration events, discusses granularity, past-tense naming, and the bounded-context boundary that events cross.
**Key Concepts:**
- Domain events versus integration events
- Event Storming as a discovery technique
- Bounded contexts and event contracts between teams
- Granularity and event naming conventions
- Technical noise as a modeling anti-pattern

## Chapter 3: Topologies and Messaging Infrastructure
**Objective:** Compare broker and mediator topologies and choreography versus orchestration models, mapping them to the most widely used messaging technologies.
**Description:** The chapter examines how events flow between producers and consumers through brokers, distinguishing the distributed log model from the traditional queue model. It analyzes pub/sub, partitions, consumer groups, and the trade-offs among Apache Kafka, RabbitMQ, and cloud-managed services.
**Key Concepts:**
- Broker topology versus mediator topology
- Choreography versus orchestration
- Distributed log versus queue (Kafka vs. RabbitMQ vs. SNS/SQS)
- Publish/subscribe, partitions, and consumer groups
- Retention, replay, and reprocessing

## Chapter 4: Delivery Guarantees and Idempotency
**Objective:** Explain the delivery guarantees available in distributed systems and show how to build idempotent consumers under at-least-once delivery.
**Description:** The chapter demystifies at-most-once, at-least-once, and exactly-once semantics, exposing why the latter is frequently misunderstood. It details consumer idempotency, deduplication, message ordering, and the Transactional Outbox pattern for reliable publishing.
**Key Concepts:**
- At-most-once, at-least-once, and exactly-once semantics
- Consumer idempotency and deduplication keys
- Message ordering and partitioning
- Transactional Outbox pattern and the dual-write problem
- Dead-letter queues and retry policies

## Chapter 5: CQRS — Separating Reads and Writes
**Objective:** Present Command Query Responsibility Segregation as a solution to the shape mismatch between write and read models, with clear adoption criteria.
**Description:** The chapter separates the command path from the query path and shows how to build event-sourced read models. It discusses projections, consistency between the write side and read side, and warns against adopting CQRS where a simple CRUD would suffice.
**Key Concepts:**
- The shape-mismatch problem
- Command and query separation
- Read models and event-driven projections
- Consistency between write side and read side
- When CQRS is over-engineering

## Chapter 6: Event Sourcing — State as a Sequence of Events
**Objective:** Teach how to persist state as an immutable log of events and reconstruct current state by replay, weighing the costs of this decision.
**Description:** The chapter addresses the truth-and-history problem: instead of storing the current state, every fact that produced it is stored. It details the event store, aggregate reconstruction, snapshots for performance, and the long-term consequences of adopting Event Sourcing.
**Key Concepts:**
- The truth-and-history problem
- Event store and append-only log
- State reconstruction and aggregates
- Snapshots and replay optimization
- Long-term costs and design constraints

## Chapter 7: Consistency, Sagas, and Long-Running Processes
**Objective:** Show how to coordinate transactions that span multiple services using sagas, accepting eventual consistency instead of distributed transactions.
**Description:** The chapter addresses the practical impossibility of distributed ACID transactions and presents sagas as an alternative. It compares choreographed and orchestrated sagas, details compensating actions, and discusses how to reason about eventual consistency in long-running business processes.
**Key Concepts:**
- Eventual consistency versus strong consistency
- Choreographed versus orchestrated sagas
- Compensating transactions and semantic rollback
- Process managers and state machines
- CAP theorem applied to event flows

## Chapter 8: Schema Evolution and Event Versioning
**Objective:** Provide strategies for evolving event contracts without breaking existing consumers over time.
**Description:** Because persisted events live indefinitely, their schemas must evolve with discipline. The chapter covers schema registry, backward and forward compatibility, upcasting of old events, and governance policies for inter-team contracts.
**Key Concepts:**
- Backward and forward compatibility
- Schema registry and formats (Avro, JSON Schema, Protobuf)
- Upcasting and versioning of persisted events
- Contracts, consumer-driven contracts, and governance
- Absence of a compatibility policy as a pitfall

## Chapter 9: Observability, Debugging, and Operations
**Objective:** Equip the architect with techniques for observing, debugging, and operating event-driven systems where the control flow is implicit.
**Description:** Tracing the cause of an effect is difficult when producers and consumers are decoupled. The chapter covers distributed tracing, correlation and causation IDs, consumer lag metrics, and failure-handling strategies including dead-letter queues and safe reprocessing.
**Key Concepts:**
- Distributed tracing and correlation/causation IDs
- Lag, throughput, and consumer health metrics
- Debugging asynchronous event flows
- Dead-letter queues and operational reprocessing
- Poison messages and containment strategies

## Chapter 10: Real-World Cases, Trade-offs, and Pitfalls
**Objective:** Consolidate the book with real-world case studies, a decision map of trade-offs, and a catalog of the most common pitfalls in adopting event-driven architectures.
**Description:** The chapter revisits the book's patterns through real fintech and e-commerce cases, showing architectural decisions and their consequences. It presents an anti-pattern catalog, criteria for migrating to and from Event Sourcing, and a guide to when not to use each pattern.
**Key Concepts:**
- Case studies in fintech and e-commerce
- Anti-pattern catalog and recurring pitfalls
- Premature adoption of ES, CQRS, and Saga combined
- Migrating to and from Event Sourcing
- Decision framework: when not to use each pattern
