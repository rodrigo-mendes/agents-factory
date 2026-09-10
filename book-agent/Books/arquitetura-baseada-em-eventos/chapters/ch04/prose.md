# Chapter 4: Delivery Guarantees and Idempotency

## Opening Problem Statement

Chapter 3 ended with a promise and a warning. The distributed log lets you replay history — reprocess millions of past events to rebuild a read model or fix a bug. But replay only works if reprocessing the same event twice produces the same result as processing it once. That property is called **idempotency**, and without it, replay corrupts data instead of repairing it.

This is not an edge case. Under the most common delivery guarantee in production systems, **every consumer will eventually receive a duplicate**. A network timeout, a broker retry, a consumer crash after processing but before acknowledging — any of these produces a message the consumer has already seen. If your handler charges a credit card, sends an email, or decrements inventory, a duplicate is a real financial or reputational loss.

Senior engineers frequently reach for a comforting escape hatch: "exactly-once delivery." They assume a broker feature or a cloud service flag makes the problem disappear. It does not. This chapter demystifies the three delivery semantics, explains precisely why exactly-once is the most misunderstood term in distributed systems, and gives you the concrete patterns — deduplication keys, the Transactional Outbox, dead-letter queues — that make correctness achievable. The goal is that duplicates stop being a threat and become a non-event.

## At-Most-Once, At-Least-Once, and Exactly-Once Semantics

A **delivery guarantee** describes what the messaging system promises about how many times a consumer observes each message. There are three levels, and the difference between them comes down to *when* the consumer acknowledges receipt.

An **acknowledgment** (ack) is the signal a consumer sends back to the broker to say "I am done with this message; you may stop tracking it." The ordering of *process* and *ack* determines the guarantee.

- **At-most-once**: ack first, then process. If the consumer crashes after acking but before finishing, the message is lost. Zero or one delivery. Fast, lossy, acceptable only for disposable data like metrics samples or non-critical telemetry.
- **At-least-once**: process first, then ack. If the consumer crashes after processing but before acking, the broker redelivers. One or more deliveries. Never loses a message, but guarantees duplicates. This is the default in Kafka, SQS, and RabbitMQ.
- **Exactly-once**: the holy grail — one delivery, no loss, no duplication.

[DIAGRAM: sequence diagram contrasting at-most-once (ack before process, crash loses message) and at-least-once (process before ack, crash triggers redelivery and duplicate) — show the broker, consumer, and the crash point in each]

The table below is the mental model to keep.

[CODE: comparison table as data — three rows (at-most-once, at-least-once, exactly-once) with columns: ack ordering, on crash, duplicates possible, message loss possible, typical use case]

Now for the misunderstanding. **True exactly-once delivery over a network is impossible.** This follows from the Two Generals Problem: two parties communicating over an unreliable channel can never both be certain the other received the final message. A sender that gets no ack cannot distinguish "message lost" from "ack lost," so it must either resend (risking a duplicate) or give up (risking loss). No protocol escapes this.

What vendors sell as "exactly-once" is really **exactly-once *processing***, not delivery. The message may be *delivered* many times, but the system produces the *effect* only once. Kafka's exactly-once semantics work this way: they combine at-least-once delivery with idempotent producers and transactional writes that are scoped **within Kafka** — a read-process-write loop whose output is another Kafka topic. The moment your side effect leaves that boundary — a database, a payment gateway, an email — Kafka's transaction cannot cover it. You are back to at-least-once, and correctness becomes *your* responsibility.

The opinionated takeaway: **design every consumer for at-least-once.** Treat exactly-once as a marketing term for a narrow, broker-internal optimization. If your architecture depends on messages never duplicating, it is already broken.

## Consumer Idempotency and Deduplication Keys

An operation is **idempotent** when applying it multiple times yields the same result as applying it once. Setting a value (`status = SHIPPED`) is naturally idempotent. Incrementing a value (`balance = balance - 10`) is not — run it twice and you have double-charged.

Since duplicates are guaranteed, the consumer must detect and discard them. The tool is a **deduplication key**: a stable, unique identifier carried by the event that lets the consumer recognize a message it has already handled. The producer must generate this key once and attach it to the event; never derive it from arrival time or a random value at the consumer.

Two patterns dominate.

**1. The idempotency check (dedup store).** Before processing, the consumer checks whether the key already exists in a store of processed IDs. If present, it acks and skips. If absent, it processes and records the key. This works for side effects that cannot be made naturally idempotent, such as calling an external payment API.

[CODE: idempotent consumer handler in Java — accept message, extract dedup key (event ID), attempt conditional insert of the key into a processed-events table; on unique-constraint violation skip as duplicate, otherwise perform the side effect; comment the critical race window]

There is a subtle race. If the consumer records the key *before* the side effect and then crashes, the redelivered message will be skipped and the side effect never happens — silent loss. If it records the key *after* the side effect and crashes in between, the redelivery reprocesses — a duplicate. The clean solution is to make the dedup record and the business write **atomic**, committed in the same local database transaction. We return to this idea with the Outbox.

**2. Natural idempotency via upsert.** When the side effect is a database write you control, model it so that reapplying it is harmless. An **upsert** keyed by the event's identifier — insert if new, overwrite if present — makes reprocessing safe by construction. This is why event-carried state transfer (Chapter 1) pairs so well with idempotent consumers: the event contains the full new state, and the consumer simply writes it.

Pro Tip: prefer natural idempotency over a dedup store whenever the domain allows it. A dedup store adds a lookup, a write, and a retention policy — you must eventually expire old keys or the table grows without bound. An upsert carries none of that operational weight.

## Message Ordering and Partitioning

Idempotency handles *duplicates*. It does not handle *out-of-order* arrival, and the two are easy to conflate. Recall from Chapter 3 that a distributed log guarantees order **only within a partition**, selected by the **partition key**. Across partitions, all bets are off.

This matters because many business operations are order-sensitive. Consider three events for one account: `AccountOpened`, `Deposited`, `Withdrawn`. Process the withdrawal before the deposit and you may reject a valid transaction. The fix is to route all events for a given entity to the same partition by using a stable partition key — here, the account ID. Same key, same partition, guaranteed order.

[DIAGRAM: flowchart showing a producer partitioning events by accountId — three accounts fanning into three partitions, each partition preserving per-account order, while a single consumer group competes across partitions]

But ordering has a cost, and it is the tension every architect must weigh:

- A **narrow** partition key (few distinct values) preserves order across large groups of events but concentrates load on few partitions, capping parallelism.
- A **wide** partition key (many distinct values, like a per-entity ID) spreads load and maximizes throughput but only guarantees order within each tiny group.

There is no ordering *across* keys. Pick the key at the granularity where order actually matters to the business — usually the aggregate (the account, the order, the shipment), not the whole system.

A defensive complement is **version-aware idempotency**. Stamp each event with a monotonically increasing version per entity. The consumer stores the last version it applied and rejects any event whose version is less than or equal to what it has already seen. This makes the consumer robust to both duplicates *and* stale out-of-order redeliveries in one mechanism.

[CODE: pseudocode for version-aware consumer — read stored version for entity, compare to incoming event version, apply and advance only if incoming > stored, otherwise discard]

Opinionated guidance: do not attempt to impose global ordering across your whole event stream. It destroys the scalability that made you choose a log in the first place. Order per aggregate; tolerate disorder everywhere else.

## The Transactional Outbox Pattern and the Dual-Write Problem

Everything so far protects the *consumer*. But the *producer* has its own failure mode, and it is one of the most common sources of silent data loss in event-driven systems: the **dual-write problem**.

A service usually needs to do two things when handling a command: update its own database and publish an event. These are two separate systems — a database and a broker — with no shared transaction. Four sequences are possible, and two of them are corrupt:

1. Write DB, publish event — both succeed. Correct.
2. Write DB, then crash before publishing — state changed, but no event. Consumers never learn. **Lost event.**
3. Publish event, then crash before writing DB — consumers act on a fact that never became true. **Phantom event.**
4. Neither happens. Correct (nothing changed).

You cannot make two independent systems commit atomically without a distributed transaction, and distributed transactions (two-phase commit) are exactly what we abandon in cloud-native architectures for their cost and fragility.

[DIAGRAM: flowchart of the dual-write problem — service writes to DB, then a crash prevents the broker publish, leaving DB and broker inconsistent; annotate the failure gap]

The **Transactional Outbox** pattern solves this elegantly. Instead of writing to the database *and* the broker, the service writes to the database *only*. In the **same local transaction** that updates the business tables, it also inserts the event into an **outbox table** in that same database. Because it is one transaction over one database, it is atomic: either both the state change and the outbox row commit, or neither does. The dual-write problem disappears.

A separate process then reads unpublished rows from the outbox and publishes them to the broker, marking each as sent. This process operates **at-least-once** — if it crashes after publishing but before marking a row, it republishes on restart. Which is exactly why consumers must be idempotent. The Outbox does not eliminate duplicates; it guarantees *no loss*, and pushes deduplication to the consumer, where we already built defenses for it.

[CODE: Transactional Outbox — a single database transaction inserting both the business record (order) and an outbox row (serialized event with a unique event ID); show the commit boundary explicitly]

Two mechanisms drive the outbox relay. **Polling** queries the table on an interval — simple, portable, but adds latency and database load. **Change Data Capture (CDC)** tails the database transaction log (via tools like Debezium) and streams new outbox rows to the broker in near-real time, with no polling overhead. CDC is the more scalable choice for high-volume systems; polling is perfectly adequate for most.

Pro Tip: the event ID written into the outbox row is the same deduplication key the consumer uses. Design the two together. The producer's Outbox and the consumer's dedup check are two halves of one end-to-end correctness contract.

## Dead-Letter Queues and Retry Policies

Idempotency and the Outbox assume messages eventually succeed. Some never will. A malformed payload, a permanent schema mismatch, or a business rule that always rejects the message creates a **poison message** — one that fails no matter how many times it is retried. Under at-least-once, a naive broker redelivers it forever, blocking the partition or starving the consumer. This is a self-inflicted outage.

The containment tool is a **dead-letter queue (DLQ)**: a separate queue where messages are moved after exhausting their retry budget. The DLQ isolates the poison message so the healthy stream keeps flowing, and preserves the failed message for inspection and manual reprocessing rather than discarding it.

A sound **retry policy** distinguishes two failure classes:

- **Transient failures** — a timeout, a throttled dependency, a brief network blip. These deserve retries, ideally with **exponential backoff** (increasing delays: 1s, 2s, 4s, 8s) and **jitter** (randomization) to avoid a thundering herd of synchronized retries hammering a recovering service.
- **Permanent failures** — a validation error, an unparseable message. Retrying is pointless; route these to the DLQ immediately. Wasting a retry budget on a message that can never succeed only delays the inevitable.

[CODE: retry policy configuration as pseudocode — max attempts, exponential backoff with jitter for transient errors, immediate dead-letter routing for a non-retryable validation exception]

Set a **maximum receive count** — the number of delivery attempts before the message is dead-lettered. In SQS this is a native redrive policy; in Kafka it is typically implemented with retry topics and a final DLQ topic. Choose the count deliberately: too low and transient blips lose messages to the DLQ; too high and a poison message churns for minutes before quarantine.

Critically, the DLQ is not a garbage can. A message landing there is an **operational signal** demanding an alert. Chapter 9 treats DLQ monitoring and safe reprocessing in depth; for now, the rule is simple: **an unwatched DLQ is a silent data loss buffer.** Every message that enters it represents a business fact your system failed to honor.

## Key Takeaways

- **At-least-once is the realistic default.** True exactly-once *delivery* is impossible over a network (Two Generals); what vendors sell is exactly-once *processing*, scoped inside the broker and void the moment a side effect touches an external system.
- **Duplicates are guaranteed, so consumers must be idempotent.** Use natural idempotency (upserts keyed by event ID) where the domain allows, and a deduplication-key store where side effects are external.
- **Order is a partition-scoped guarantee.** Route order-sensitive events for one aggregate to one partition via a stable partition key, and use per-entity version numbers to reject stale or duplicate deliveries.
- **The Transactional Outbox defeats the dual-write problem** by committing the state change and the event atomically to one database, then relaying to the broker at-least-once — which is why the consumer's idempotency is non-negotiable.
- **Dead-letter queues contain poison messages.** Retry transient failures with exponential backoff and jitter; dead-letter permanent failures immediately; and alert on every DLQ arrival.

## What's Next

With reliable delivery and idempotent processing established, Chapter 5 turns to structure — introducing CQRS to separate the write path from the read path and resolve the shape mismatch between how data is stored and how it is queried.
