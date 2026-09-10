# Chapter 8: Schema Evolution and Event Versioning

## Opening Problem Statement

Chapter 7 left the reader with a system whose truth is spread across services that converge over time through sagas and compensations. Chapter 6 made a heavier promise still: with Event Sourcing, every event is kept forever. That promise now presents its bill. A request-response API can deprecate a field in a quarter and force every caller to upgrade. An event store cannot. An event written in 2021 will be read in 2027, by a consumer written in 2025, running code nobody on the original team remembers. The event is not a transient message; it is a **persisted contract with the future**. So the real question of this chapter is uncomfortable: how does an architect change the shape of a fact that has already happened, is stored millions of times over, and is consumed by teams they have never met? Get this wrong and every deployment becomes a coordinated, cross-team, high-risk event. Get it right and teams evolve their contracts independently, on their own schedule, without a single broken consumer. This chapter is about buying that independence — and about the one policy decision that, if skipped, quietly guarantees the opposite.

## Backward and Forward Compatibility

Every conversation about schema evolution eventually reduces to two words: **compatibility** direction. Confusing them is the most common — and most expensive — mistake in this domain, so define them precisely and never mix them again.

**Backward compatibility** means a *new consumer* can read *old events*. You changed the schema; a consumer running the new schema still understands data written under the old one. This is the direction Event Sourcing demands, because your event store is full of old events that will be replayed forever.

**Forward compatibility** means an *old consumer* can read *new events*. You changed the schema; a consumer still running the old version tolerates data written under the new one, typically by ignoring what it does not recognize. This is the direction that pub/sub integration demands, because you cannot upgrade every consumer at the same instant you upgrade the producer.

**Full compatibility** is both at once. It is the strictest and the safest, and it is the target most mature registries default to.

The practical payoff is a simple rule set for what a change is allowed to do. The safe changes are almost always additive.

[DIAGRAM: A comparison table rendered as a decision matrix (class/table style) mapping schema changes to compatibility direction. Rows: "Add optional field with default", "Remove optional field", "Add required field (no default)", "Rename field", "Widen type (int->long)", "Narrow type (long->int)", "Change field meaning". Columns: "Backward-safe?", "Forward-safe?", "Full-safe?" with check/cross marks. Include a legend note that renaming = remove + add and is never safe.]

Notice the trap hiding in that matrix. Adding a **required** field breaks backward compatibility, because old events simply do not carry it. Removing a field breaks forward compatibility, because old consumers still expect it. And a rename is not one operation — it is a delete plus an add, so it fails on both fronts. The discipline, then, is boring on purpose: prefer optional fields, always supply defaults, and treat "required" as a word you have to justify in a review.

[CODE: Two contrasting event schema definitions in Avro (or JSON Schema) — "before" and "after". The safe evolution adds an optional field `couponCode` with a default of null. Annotate with comments showing why a consumer on the old schema still reads the new event (forward) and a consumer on the new schema still reads the old event (backward).]

One more distinction that senior engineers routinely blur: compatibility is a property of the *schema pair*, not of the event. A single change can be backward-compatible and forward-incompatible at the same time. Always ask "compatible in which direction, for whom?" before approving anything.

## Schema Registry and Formats (Avro, JSON Schema, Protobuf)

Rules are worthless if nobody enforces them. A **schema registry** is the component that stores the canonical schema for each event type, assigns it a version, and — this is the part that matters — *refuses* to register a new version that violates the configured compatibility rule. It turns compatibility from a code-review hope into a build-time gate.

The mechanics are straightforward. The producer registers a schema and gets back a numeric ID. It publishes events tagged with that ID rather than the full schema. The consumer reads the ID, fetches the matching schema from the registry (and caches it), and deserializes. Two benefits fall out immediately: events on the wire are small, and no consumer can ever guess the schema — it always resolves the exact one the producer used.

[DIAGRAM: Sequence diagram of a schema registry interaction. Actors: Producer, Schema Registry, Broker, Consumer. Flow: (1) Producer submits new schema -> Registry runs compatibility check -> returns schema ID or rejects. (2) Producer serializes event with schema ID, publishes to Broker. (3) Consumer reads message, extracts schema ID, requests schema from Registry (cache miss), Registry returns schema. (4) Consumer deserializes. Show the rejection path as an alternative branch.]

The registry is format-neutral in concept, but the choice of serialization format is itself a design decision with real consequences. The three that dominate cloud-native systems trade off differently.

| Format | Schema location | Evolution model | Human-readable | Best fit |
|---|---|---|---|---|
| **Avro** | External, resolved by ID | Reader/writer schema resolution — strongest evolution story | No (binary) | Kafka event streams, event stores |
| **Protobuf** | Compiled into code (field numbers) | Field-number based; add/reserve, never reuse numbers | No (binary) | gRPC, high-throughput internal contracts |
| **JSON Schema** | External or inline | Additive with defaults; validation-centric | Yes (text) | Public/partner events, debuggability first |

**Avro** deserves the architect's attention in event-sourced systems because of one feature: it deserializes using *both* the writer's schema (what produced the event) and the reader's schema (what the consumer expects), reconciling the difference automatically. That reader/writer split is exactly the backward-compatibility machinery Event Sourcing needs, built into the format.

**Protobuf** encodes fields by number, not name, so renaming a field costs nothing on the wire — but reusing a retired field number is catastrophic, silently mapping old bytes to a new meaning. The rule is absolute: **reserve** deleted field numbers, never recycle them.

**JSON Schema** buys you readability and painless debugging at the cost of size and weaker guarantees. For events that cross a company boundary to a partner who will inspect them by eye, that trade is often correct.

There is no universal winner. Streams internal to your platform lean Avro or Protobuf; contracts you hand to outsiders lean JSON. What is non-negotiable is that *some* registry enforces *some* policy.

## Upcasting and Versioning of Persisted Events

Compatibility rules keep you safe as long as every change is additive. Reality is not that kind. Eventually a business concept genuinely changes shape — a single `name` field must become `firstName` and `lastName`, or an amount stored as a float must become an integer of minor units. No additive rule covers this, and you cannot rewrite history: the old events are immutable facts, already persisted, possibly by the millions.

The answer is **upcasting**: transforming an old event into the current schema *at read time*, in memory, on its way from the store to the application. The stored bytes never change. A component in the deserialization pipeline detects the old version and applies a function that maps it forward to the new shape. Your domain logic only ever sees the latest version and stays blissfully unaware that five historical formats exist beneath it.

[CODE: An upcaster implementation. Show a versioned event `CustomerRegistered` at v1 (single `fullName` field) and v2 (split `firstName`/`lastName`). Implement an upcaster function/class that, given a v1 payload, splits `fullName` and produces a v2 payload. Show it registered in a chain/pipeline keyed by (eventType, version), and note that the domain handler only ever receives v2.]

The upcaster chain is the pattern that scales this. Each upcaster promotes exactly one version forward — v1→v2, v2→v3 — and the pipeline runs them in sequence. A v1 event on disk passes through both upcasters and arrives as v3. This keeps every transformation small, independently testable, and honest about exactly which change it represents.

[DIAGRAM: Flowchart of an upcaster pipeline. Input: raw stored event with version tag. Branch on version: v1 enters upcaster v1->v2, output feeds upcaster v2->v3; v2 enters at v2->v3; v3 passes straight through. All paths converge to "current schema event" delivered to the domain handler. Emphasize that stored bytes are never mutated.]

Two disciplines make upcasting sustainable rather than a growing tax. First, **every event carries an explicit version number** in its metadata from day one — retrofitting versioning onto an unversioned store is painful, so pay this cost up front even when v1 is all you have. Second, upcasting is not the *only* option for large migrations. When an upcaster chain grows unwieldy, you can **rewrite the stream** into a new one under the new schema (a "copy-and-transform" migration), leaving the old stream as an immutable archive. Upcasting is cheaper day to day; stream rewriting is cleaner long-term. Most systems use both, and choosing between them is a genuine architectural judgment, not a default.

Resist the temptation to "just fix the data" with an in-place update to the store. That destroys the one property — an immutable, auditable history — that justified Event Sourcing in the first place.

## Contracts, Consumer-Driven Contracts, and Governance

Everything so far is mechanism. The hardest part of schema evolution is not technical; it is organizational. An event that crosses a bounded context (Chapter 2 framed events as owned contracts) is a promise from a producing team to consuming teams that may sit in other departments, other time zones, other reporting lines. The registry enforces syntactic compatibility. It cannot tell you *who is actually consuming what*, and therefore cannot tell you whether a technically-compatible change is *semantically* safe to ship.

This is where **consumer-driven contracts** (CDC) earn their place. The idea inverts the usual direction of authority. Instead of the producer declaring "here is my schema, adapt to it," each consumer publishes a contract stating exactly the fields and shapes *it* depends on. The producer's build then verifies its schema against the union of all consumer contracts. If a proposed change breaks any consumer's stated expectations, the producer's pipeline fails — before deployment, on the producer's side, where the change originated.

[DIAGRAM: Sequence/flow diagram of a consumer-driven contract workflow. Consumer A and Consumer B each publish a contract (expected fields) to a shared contract broker. Producer's CI pipeline pulls all consumer contracts, runs its candidate schema against them, and either passes or fails the build. Contrast a small callout showing the producer-driven direction (schema pushed down) versus consumer-driven (contracts pulled up).]

The distinction between a schema registry and consumer-driven contracts is worth stating plainly, because teams often assume one replaces the other.

| Concern | Schema registry | Consumer-driven contracts |
|---|---|---|
| Question answered | "Is this change structurally compatible?" | "Does any real consumer actually break?" |
| Knows about consumers | No | Yes, explicitly |
| Enforcement point | Schema registration | Producer CI build |
| Catches semantic misuse | No | Partially (only stated expectations) |

They are complementary layers, not competitors. The registry is the fast, coarse gate; CDC is the slower, consumer-aware one.

Around both sits **governance**: the policies that make evolution predictable across an organization. Effective governance is lighter than teams fear and consists of a few durable rules. Assign every event type a single owning team. Mandate an explicit compatibility mode per event stream, registered and visible. Require deprecation to be announced with a timeline and a metric proving the old version is no longer read before it is retired. Version in metadata, never by mutating payloads. Governance is not a committee that slows teams down; it is the small set of agreements that let teams move *without* coordinating every release.

## The Missing-Policy Pitfall

The single most damaging mistake in this entire chapter is not a bad schema change. It is the *absence of a declared compatibility policy at all*. This deserves its own section because it fails silently and is nearly always discovered too late.

A system without a policy does not announce the problem. Everything works — right up until the first genuinely breaking change ships, a consumer three teams away deserializes garbage, and a production incident traces back to a field someone "cleaned up" months earlier. Because there was no gate, nothing stopped it. Because events are persisted, the poison is now in the store permanently, and every replay re-triggers it.

The fix is embarrassingly cheap relative to the damage it prevents: **choose a default compatibility mode before your first event ships**, and make the registry enforce it. `BACKWARD` is the sane default for most event-sourced systems; `FULL` if you can afford the discipline. That one decision, made early, converts an entire class of cross-team production incidents into build-time failures on the desk of the person who caused them.

## Key Takeaways

- **Compatibility has a direction.** Backward = new consumer reads old events (Event Sourcing needs this); forward = old consumer reads new events (pub/sub needs this); full = both. Always ask "compatible in which direction, for whom?"
- **Additive-only is the safe path.** Add optional fields with defaults; never rename in place, add required fields without defaults, or reuse a retired Protobuf field number.
- **A schema registry turns policy into a build-time gate.** It rejects incompatible schemas before they ship; Avro's reader/writer resolution makes it especially strong for event stores.
- **Upcast, don't mutate.** Transform old persisted events to the current schema at read time through a versioned upcaster chain; version every event in metadata from day one.
- **The registry answers "is it structurally compatible?"; consumer-driven contracts answer "does any real consumer break?"** You need both, plus lightweight governance: one owner per event type, an explicit compatibility mode, and metric-backed deprecation.
- **No compatibility policy is the pitfall.** Choose a default mode (BACKWARD or FULL) and enforce it before your first event ships.

## What's Next

With contracts that can evolve safely in place, Chapter 9 turns to the operational reality of running these systems — observing, tracing, and debugging event flows whose control flow is implicit and spread across decoupled services.
