# Chapter 6: Event Sourcing — State as a Sequence of Events

## Opening Problem Statement

Chapter 5 left a loose thread. It showed that read models are disposable — you can throw them away and rebuild them by replaying events. That statement quietly assumed something we never justified: that the events still exist somewhere, in order, forever. If projections are rebuildable from an event log, then that log, and not the read model, is the real source of truth.

This chapter formalizes that idea. **Event Sourcing** is the pattern where the authoritative state of an entity is not a row you update, but the complete, ordered sequence of events that happened to it. You do not store the current balance of an account. You store every deposit and every withdrawal, and you compute the balance when you need it.

For senior architects, the appeal is obvious and the danger is subtle. Event Sourcing gives you a perfect audit trail, temporal queries, and debugging power that traditional systems cannot match. It also imposes constraints that last for the life of the system — schemas you can never fully delete, a mental model your whole team must share, and operational costs that only appear at year three. This chapter teaches both sides honestly.

## The Truth-and-History Problem

Traditional systems have a memory problem: they forget. Consider a classic banking table with a single `balance` column. When a customer withdraws money, you run an `UPDATE` and the previous balance is gone. The database now holds a fact — "the balance is 500" — but it has destroyed the history that produced it.

This is the **truth-and-history problem**: a system that stores only current state can answer *what is true now*, but not *how it became true*. Most of the time nobody asks the second question. Then an auditor, a regulator, or an angry customer does, and the answer is a shrug.

Consider what the update-in-place model throws away every time it runs.

[DIAGRAM: side-by-side comparison. Left panel "State-Oriented": a single Account row with balance=500 being overwritten by an UPDATE, with prior values shown crossed out and labeled "lost". Right panel "Event-Sourced": an append-only list of events (AccountOpened, MoneyDeposited +1000, MoneyWithdrawn -500) with a derived balance=500 shown as computed, not stored. Flowchart/comparison style.]

The state-oriented approach optimizes for the present at the expense of the past. Event Sourcing inverts that priority. It treats each **event** — an immutable fact of the past, exactly as defined in Chapter 1 — as the durable unit of truth. Current state becomes a *derived value*, recomputed on demand from the events.

The consequence is strategic, not just technical. In a state-oriented system, history is an afterthought you bolt on with audit tables and triggers, and those audit tables are always slightly wrong. In an event-sourced system, history *is* the storage model. You cannot have incorrect history, because the history is the only thing you ever wrote. Correctness of the audit trail stops being a feature you maintain and becomes a property of the architecture.

That is the trade the pattern offers: you give up the convenience of reading current state directly, and in return you never lose a fact.

## The Event Store and the Append-Only Log

The database that holds these events is called an **event store**. It is not a general-purpose table you happen to insert into — it is a specialized log with two rules that define the entire pattern.

First, the event store is **append-only**. You may add events to the end. You may never update or delete an event already written. An event records something that happened, and the past does not change. This is the same immutability principle from Chapter 1, now enforced at the persistence layer.

Second, events are grouped into **streams**. A stream is the ordered sequence of all events for one entity — for example, all events for account `acc-123`. The stream is the unit of consistency and the unit of reconstruction.

A minimal event store schema needs only a handful of columns to enforce these rules.

[CODE: SQL DDL for a minimal event store table with columns: stream_id, version (per-stream sequence number), event_type, payload (JSON/JSONB), metadata, global_position, occurred_at. Include a UNIQUE constraint on (stream_id, version) to enforce ordering and optimistic concurrency.]

The `version` column is the quiet hero of that schema. It numbers events within a stream: 1, 2, 3, and so on. The `UNIQUE (stream_id, version)` constraint does two jobs at once. It guarantees a total order inside each stream, and it gives you **optimistic concurrency control** for free.

Here is how the concurrency check works. When a command handler loads a stream, it notes the current highest version — say, 7. It processes the command and tries to append a new event as version 8. If another process already wrote version 8 in the meantime, the unique constraint rejects the insert. The handler knows its decision was based on stale data and retries. No locks, no blocking — just a constraint doing its job.

[CODE: pseudocode for appending events with optimistic concurrency: load stream up to expectedVersion, attempt insert at expectedVersion+1, catch unique-constraint violation and signal a concurrency conflict for retry.]

A word of realism for architects choosing infrastructure. You can build an event store on plain PostgreSQL, and for many corporate systems you should — the operational familiarity is worth more than any specialized feature. Purpose-built stores such as EventStoreDB or Axon Server, or cloud primitives like DynamoDB with a partition-plus-sort-key design, add subscription and projection tooling. But none of them changes the two rules above. Append-only and ordered-by-stream are the whole game.

## State Reconstruction and Aggregates

If you never store current state, how do you get it? You compute it. The process is called **reconstruction** or **rehydration**: you read the stream from the beginning and apply each event, in order, to a fresh in-memory object. That object is the **aggregate** — the consistency boundary from Domain-Driven Design that owns the business rules for one entity.

Reconstruction is a fold. You start with an empty aggregate and, event by event, fold each fact into the aggregate's state.

[CODE: an Account aggregate in Java or C#. Show an apply() method with overloads or a switch per event type (AccountOpened sets id and balance=0, MoneyDeposited adds amount, MoneyWithdrawn subtracts amount) and a static rehydrate(events) that folds a stream into a live aggregate.]

Notice the discipline this enforces. There are exactly two kinds of methods on the aggregate, and confusing them is the most common Event Sourcing bug.

1. **Command methods** (for example, `withdraw`) contain the business rules. They validate invariants — "you cannot withdraw more than the balance" — and, if the rule holds, they *produce a new event*. They decide what should happen.
2. **Apply methods** (for example, `applyMoneyWithdrawn`) contain no business logic at all. They only mutate in-memory state from an event that has *already happened*. They record what did happen.

The rule is absolute: **apply methods must never reject an event or contain validation.** The event is a historical fact. Refusing to apply it during reconstruction would mean refusing to acknowledge the past, and your rebuilt state would silently diverge from reality. All validation lives in command methods, before the event exists.

[DIAGRAM: sequence diagram of a write. Command handler loads events for stream, calls rehydrate to fold them into an aggregate, invokes a command method (withdraw) which validates the invariant and returns a new MoneyWithdrawn event, then appends that event to the store at expectedVersion+1. Show the concurrency check on append.]

This is where Event Sourcing and CQRS from Chapter 5 lock together. The command side reconstructs the aggregate to make a decision and emits an event. That same event feeds the projections that build the read models. One event, written once, serves both truth and query. The event log becomes the single source that CQRS's disposable read models are rebuilt from.

## Snapshots and Replay Optimization

Reconstruction has an obvious flaw, and every skeptic spots it immediately. If an account has 200,000 events accumulated over ten years, must you read and fold all 200,000 events every time someone checks the balance? At that volume, reconstruction turns a millisecond operation into a multi-second one.

The answer is the **snapshot**. A snapshot is a cached copy of the aggregate's state at a specific version — a checkpoint that says "at version 50,000, the balance was 12,340." Reconstruction then changes: load the latest snapshot, then replay only the events that came *after* it.

[CODE: rehydrateFromSnapshot(streamId): load the most recent snapshot for the stream, read only events with version greater than snapshot.version, fold those onto the snapshot state. Show the fallback to full replay when no snapshot exists.]

Two design points separate a working snapshot strategy from a broken one.

- **A snapshot is a derived optimization, never a source of truth.** You must be able to delete every snapshot in the system and rebuild all of them from events alone. If deleting snapshots loses data, you have accidentally reintroduced the state-oriented model you were trying to escape.
- **Snapshot on a cadence, not on every write.** A common policy is one snapshot every *N* events per stream — say, every 100. The number is a tuning knob, not a constant.

The following table frames the trade-off you are actually tuning.

| Snapshot frequency | Replay cost per load | Storage & write overhead | Best fit |
|---|---|---|---|
| Never (pure replay) | Grows without bound | None | Short streams, low event counts |
| Every N events (e.g., 100) | Bounded, small | Moderate | Most production systems |
| Every event | Near zero | High; approaches state storage | Almost never — a code smell |

The last row is worth a **Pro Tip**. If your instinct is to snapshot on every single write, stop. You have rebuilt an update-in-place database with extra steps and worse performance. The point of snapshots is to make replay *acceptable*, not to eliminate it. Reach for snapshots only when measurement proves reconstruction is too slow — and for aggregates with short lifespans and few events, you may never need them at all.

## Long-Term Costs and Design Constraints

Event Sourcing is not a technique you try for a sprint and back out of cleanly. Once real events accumulate, the pattern becomes load-bearing, and its costs are structural. An honest architect weighs them before adopting, not after.

**Events are permanent, so their schemas are permanent.** A row you no longer like can be migrated with an `ALTER TABLE`. An event written in 2024 will still be read during reconstruction in 2030, exactly as it was written. You cannot migrate the past. You accommodate old shapes through versioning and upcasting — the entire subject of Chapter 8 — and that discipline is mandatory, not optional.

**Deletion becomes a real design problem.** Regulations such as GDPR grant a right to erasure, which collides head-on with an append-only, immutable log. You cannot simply delete the events. The standard answer is **crypto-shredding**: encrypt personal data per subject and delete the key to render the data unrecoverable. This must be designed in from the first event, because you cannot retrofit encryption onto facts already written in plaintext.

**Querying current state requires the read side.** Since state is derived, you cannot write a simple `SELECT balance FROM accounts`. You need projections and read models — which is precisely why Event Sourcing and CQRS are so often adopted together. Choosing Event Sourcing effectively commits you to the CQRS read path from Chapter 5.

[DIAGRAM: decision flowchart for adopting Event Sourcing. Questions: Is a complete audit trail a hard requirement (regulatory/financial)? Do you need temporal queries or to reconstruct past states? Is the domain rich in behavior rather than simple CRUD? Can the team absorb schema-versioning and eventual-consistency complexity? Route "yes to the first three and the last" to "Event Sourcing is justified" and route CRUD-shaped or team-unready cases to "Prefer state storage / CQRS-lite".]

The blunt guidance for senior architects: Event Sourcing earns its keep in domains where history is intrinsically valuable — ledgers, trading, insurance, medical records, order lifecycles — and where the business genuinely asks *how did we get here*. For a CRUD-shaped domain whose users never ask about the past, it is over-engineering with a decade-long maintenance tail. Adopt it where the audit trail is the product, not where it is a novelty.

## Key Takeaways

- Event Sourcing stores every state-changing event as immutable fact and derives current state by replay, solving the truth-and-history problem that update-in-place systems create by forgetting the past.
- The **event store** is append-only and organized into per-entity **streams**; a `UNIQUE (stream_id, version)` constraint enforces both ordering and lock-free optimistic concurrency.
- Aggregates are **rehydrated** by folding events in order; command methods validate invariants and emit events, while apply methods only mutate state and must never reject a fact.
- **Snapshots** bound replay cost by checkpointing state every N events, but they are disposable optimizations — never a source of truth, and never taken on every write.
- The costs are permanent schemas, hard deletion (crypto-shredding), and a mandatory read side; adopt Event Sourcing only where history is genuinely valuable to the business.

## What's Next

Chapter 7 confronts what happens when a single business process spans multiple aggregates and services, introducing sagas to coordinate transactions under eventual consistency instead of distributed ACID.
