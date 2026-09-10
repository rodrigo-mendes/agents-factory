# Chapter 5: CQRS — Separating Reads and Writes

## Opening Problem Statement

Chapter 4 left the write path in good shape. Events flow at-least-once, consumers are idempotent, and the Transactional Outbox publishes reliably. But a nagging question remains: once those events have reshaped your system's state, how does anyone *read* that state efficiently? A single table optimized to enforce invariants on write is almost never the same table you want to query for a dashboard, a search screen, or a mobile feed. This is the tension **Command Query Responsibility Segregation (CQRS)** was built to resolve.

CQRS is one of the most misunderstood patterns in the event-driven toolkit. Some teams treat it as a mandatory companion to Event Sourcing. Others deploy it reflexively on every microservice and drown in accidental complexity. Neither reflex is correct. CQRS is a targeted answer to a specific structural problem — the mismatch between the shape of data you write and the shape you read. This chapter defines that problem precisely, shows how to separate the two paths, teaches you to build read models from events, confronts the consistency cost honestly, and — most importantly for a senior audience — draws a hard line around when CQRS is simply over-engineering.

## The Shape-Mismatch Problem

Every persistent system serves two fundamentally different jobs. On one side, it accepts changes and must protect business rules — an account cannot be overdrawn, an order cannot ship twice. On the other side, it answers questions — show me this customer's order history, rank products by revenue, list unpaid invoices. These two jobs pull the data model in opposite directions.

The write side wants **normalization**. Normalized tables prevent anomalies, enforce referential integrity, and keep invariants local to one aggregate. The read side wants **denormalization**. A query screen wants everything it needs pre-joined, flattened, and indexed for the exact access pattern it serves. Forcing both jobs onto one schema means neither gets what it needs. This is the **shape-mismatch problem**: the optimal structure for validating a change differs from the optimal structure for answering a question.

Consider a corporate e-commerce order service. The write model is a tidy `Order` aggregate with line items, enforcing that totals reconcile and stock is reserved. Now the business asks for a screen showing, per customer, their last ten orders with product thumbnails, shipping status, and a running lifetime-value figure. Serving that from the normalized write schema means a multi-table join executed on every page load, competing for locks with the very transactions that place orders.

[DIAGRAM: side-by-side comparison (two-column) showing a normalized write model — Order, OrderLine, Product, Customer tables with foreign keys — versus a denormalized read model — a single flat CustomerOrderView document with embedded line items and precomputed lifetime value. Label the arrow between them "projection".]

The naive fix is to keep bolting indexes and read replicas onto the single model. That buys time but not escape. Read-optimized indexes slow writes; heavy reporting queries contend with transactional load; and the schema calcifies because it must satisfy every consumer at once. CQRS proposes a cleaner cut: stop pretending one model can be both. Let the write side stay lean and rule-bound, and derive whatever read shapes you need as separate, purpose-built structures.

## Command and Query Separation

The name says it all. A **command** is an instruction to change state — `PlaceOrder`, `CancelReservation`, `ApplyDiscount`. A **query** is a request to return state without changing it — `GetOrderHistory`, `FindUnpaidInvoices`. CQRS insists that these two responsibilities live in **separate models**, and often in separate infrastructure entirely.

This is a deliberate generalization of the older **Command Query Separation (CQS)** principle, which merely said a single method should either change state or return it, never both. CQRS lifts that idea from the method level to the architectural level: one model handles the command path, a different model handles the query path.

The command path processes an intent, validates it against business rules, and — on success — mutates the authoritative state and emits a domain event. That path returns almost nothing to the caller; frequently just an acknowledgement or an identifier. The query path never touches the authoritative write store. It reads from one or more **read models** built specifically for the questions being asked.

[CODE: two contrasting interfaces in a typed language (e.g., C# or Kotlin). First, a command side — an OrderCommandHandler.Handle(PlaceOrderCommand) that loads the aggregate, enforces invariants, persists, and publishes an OrderPlaced event, returning only an OrderId. Second, a query side — an OrderQueryService.GetCustomerOrders(customerId) that reads directly from a denormalized read store and returns a fully-populated view DTO. No shared model between them.]

Notice what this separation unlocks. The two sides can scale independently — read traffic in most corporate systems dwarfs write traffic by an order of magnitude, so you can add read replicas or query nodes without touching write capacity. They can use different storage engines: a relational store for transactional writes, a document store or search index for reads. And they can evolve on independent schedules, because a new query screen means adding a read model, not migrating the write schema.

The trade-off is equally clear. You now maintain two models and the machinery that keeps them aligned. That machinery is where events re-enter the story, and where the pattern earns or loses its keep.

## Read Models and Event-Driven Projections

How does data cross from the write side to the read side? Through events. Every time the command path commits a change, it emits a domain event — exactly the events Chapter 2 taught you to model and Chapter 4 taught you to deliver reliably. A **projection** is the component that consumes those events and updates a read model to reflect them.

Think of a projection as a small, dedicated consumer with one job: translate a stream of facts into a shape optimized for a specific query. When an `OrderPlaced` event arrives, the projection inserts or updates a row in the `CustomerOrderView`. When `OrderShipped` arrives, it flips the status field. The read model is never written to by hand; it is *derived*, entirely and repeatedly, from the event stream.

[DIAGRAM: flowchart showing the command path (Command -> Command Handler -> Write Store) emitting an event onto an event bus, then two independent projection consumers reading from the bus and writing into two different read stores (a SQL read model for order history, an Elasticsearch index for product search). Query requests hit the read stores directly, bypassing the write store.]

This design has a property that senior architects should savor: read models are **disposable and rebuildable**. Because a projection is a pure function of the event stream, you can delete a read model and reconstruct it by replaying events from the beginning. Need a brand-new query shape for a feature shipping next quarter? Write a new projection, replay history through it, and you have a fully-populated read model without a risky data migration. This rebuildability is the strongest practical argument for pairing CQRS with the event log, and it foreshadows Event Sourcing in Chapter 6.

[CODE: a projection handler that subscribes to OrderPlaced, OrderShipped, and OrderCancelled events and performs upserts into a denormalized read table keyed by customerId. Show idempotent handling using the event ID or a per-view version (calling back to Chapter 4), so redelivered events do not corrupt the read model.]

A word of discipline: projections must be **idempotent**, for exactly the reasons Chapter 4 established. Delivery is at-least-once, so the same `OrderShipped` event may arrive twice. A projection that blindly increments a counter will drift. Use upserts keyed by the aggregate identifier, or track the last-applied event version per view, and duplicates become harmless. Treat the read model as a deterministic replay target, never as a place to accumulate side effects.

## Consistency Between Write Side and Read Side

Here is the fact that decides whether CQRS fits: the read side is **eventually consistent** with the write side. A command commits and its event is published, but the projection processes that event a moment later — milliseconds usually, seconds under load, longer if a consumer is lagging or recovering. During that window, a query can return state that does not yet reflect the change the user just made. This is **replication lag**, and it is not a bug you can eliminate; it is the structural price of separating the models.

The classic symptom is **read-your-own-writes** violation. A user cancels an order, the screen refreshes, and the order still shows as active because the cancellation event hasn't been projected yet. Users experience this as the system "losing" their action. You must design for it deliberately rather than hope it never happens.

The table below lays out the practical mitigations and their costs.

| Technique | How it works | Cost / caveat |
|---|---|---|
| Accept the lag | Show eventual state; add a subtle "processing…" hint in the UI | Simplest; only viable where staleness is tolerable |
| Optimistic UI update | Client renders the expected result locally after a command | UI can diverge from server truth on failure |
| Read-your-writes routing | Route a user's reads to the write model briefly after their command | Reintroduces write-side read load you tried to shed |
| Version / token check | Command returns a version; query waits until the read model reaches it | Adds latency and coordination complexity |

[DIAGRAM: sequence diagram showing a client sending a command, the write store committing and publishing an event, the client immediately issuing a query that returns stale data, then the projection applying the event, then a second query returning fresh data. Annotate the gap between commit and projection as "eventual consistency window / replication lag".]

The governing question is one of **business tolerance**, not technology. Ask, for each query: how stale can this data be before it causes real harm? A product-catalog view can lag by seconds with zero consequence. An account-balance check that gates a withdrawal cannot — and that is a strong signal to keep that specific read on the strongly-consistent write model, even in an otherwise CQRS system. CQRS does not force *every* read onto the eventual-consistency path. Keep the invariant-critical reads close to the write model and reserve projections for the reporting, search, and display workloads that dominate volume but tolerate delay.

## When CQRS Is Over-Engineering

Now the opinionated part, and the reason this chapter exists. CQRS is a specialized tool, not a default architecture. Applied where it is not needed, it manufactures complexity that will haunt the team for years. A senior architect's job is to recognize the difference before writing the first line of code.

CQRS is **over-engineering** when your read and write models have essentially the same shape. If a straightforward CRUD entity — a customer profile, a configuration record, a reference table — is written and read through nearly identical structures, there is no shape mismatch to solve. Splitting it into two models and a projection adds a moving part, an eventual-consistency window, and an operational burden while solving no actual problem. A well-indexed table, perhaps with a read replica, is the correct and boring answer.

Watch for these warning signs that CQRS is the wrong call:

1. **The domain is simple CRUD.** Data is created, read, updated, and deleted with no rich behavior and no query shapes that diverge from the write shape.
2. **Read and write volumes are comparable and modest.** The independent-scaling benefit is the main payoff; with balanced, low traffic there is little to gain.
3. **The team has no operational maturity for asynchrony.** CQRS means monitoring projection lag, handling replays, and debugging eventual consistency. Without that muscle, you inherit a system you cannot reason about.
4. **Stakeholders cannot tolerate any staleness.** If every read must be immediately consistent, you are fighting the pattern's core mechanic and should not adopt it.

**Pro Tip:** Adopt CQRS at the *aggregate* or *bounded-context* level, never as a blanket rule for the whole system. Most real systems are hybrids — a few high-value contexts justify full CQRS with projections, while the majority stay comfortable CRUD. Applying the pattern selectively is the mark of judgment; applying it everywhere is the mark of dogma.

The honest heuristic: reach for CQRS when a genuine shape mismatch, a large read/write asymmetry, or a need for many divergent read models makes a single model painful — and only then. If you cannot name the specific pain, you do not yet have a reason to pay the price.

## Key Takeaways

- The **shape-mismatch problem** is CQRS's reason to exist: the normalized model that enforces write-side invariants is rarely the denormalized shape that serves reads efficiently.
- CQRS separates the **command path** (changes state, emits events, returns little) from the **query path** (reads purpose-built read models, never touches the write store), letting each scale and evolve independently.
- **Projections** are idempotent event consumers that derive read models from the event stream, making read models disposable and rebuildable by replay.
- The read side is **eventually consistent**; replication lag and read-your-own-writes are structural costs to be designed for, not bugs to be fixed. Match each read to its business tolerance for staleness.
- CQRS is **over-engineering** for simple CRUD with matching read/write shapes. Adopt it per aggregate or bounded context, only where a concrete pain justifies the added complexity.

## What's Next

Rebuildable read models hinted at a deeper idea — storing state as the events themselves; Chapter 6 makes that leap explicit with Event Sourcing.
