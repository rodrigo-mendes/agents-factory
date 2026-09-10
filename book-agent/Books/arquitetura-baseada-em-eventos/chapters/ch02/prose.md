# Chapter 2: Modeling Events as Domain Facts

## Opening Problem Statement

Chapter 1 defined an event as an immutable fact of the past and gave us a shared vocabulary: coupling axes, event styles, and Event-Carried State Transfer as the default for cross-context integration. But a definition does not tell you *which* facts deserve to become events. This is where most event-driven systems quietly rot. A team wires a broker into their stack, and within months the topics are flooded with `RowInserted`, `CacheInvalidated`, and `UserEntityUpdated`. None of these mean anything to the business. They are technical exhaust dressed up as domain knowledge, and every consumer that subscribes to them inherits the producer's database schema as a de facto contract. The problem this chapter solves is discipline in modeling: how to design events that carry genuine business meaning, that survive refactoring, and that let independent teams integrate without stepping on each other. The senior architect's job here is not to publish more events — it is to publish the *right* ones, with names that read like sentences a domain expert would speak. Get this wrong and no amount of Kafka tuning will save the architecture.

## Domain Events Versus Integration Events

The single most useful distinction in event modeling is between **domain events** and **integration events**. They look identical on the wire — both are immutable facts — but they serve different audiences and obey different rules.

A **domain event** is a fact that matters *inside* a single bounded context. It is expressed in that context's ubiquitous language and is often consumed by the same service that produced it, or by tightly related components within the same team's boundary. `OrderPlaced`, `PaymentDeclined`, `SeatReserved` — these describe something a business stakeholder cares about. Domain events are rich; they can reference internal aggregates freely because everyone who reads them shares the same model.

An **integration event** is a fact published *across* a bounded-context boundary, intended for other teams and other services. It is a deliberate, public contract. Because it crosses a boundary, it must not leak internal structure. An integration event is a translation — a stripped, stabilized projection of one or more domain events into a shape the outside world can depend on.

The table below makes the contrast concrete.

| Aspect | Domain Event | Integration Event |
|--------|--------------|-------------------|
| Audience | Inside one bounded context | Other contexts and teams |
| Language | Full ubiquitous language | Stable public vocabulary |
| Payload | Rich, references aggregates | Minimal, self-contained |
| Coupling | Tight, by design | Loose, contractual |
| Lifespan | Changes with the model | Changes only via versioning |
| Failure of leaking | Local refactor | Breaks external consumers |

The rule follows directly: **never publish a raw domain event across a context boundary.** Translate it first. The moment an external team subscribes to your internal `OrderAggregateUpdated`, your database becomes their API, and you have lost the freedom to refactor. This translation step is not bureaucracy — it is the seam that keeps teams independent.

[DIAGRAM: flowchart showing a domain event produced inside Context A, passing through a translation/anti-corruption boundary that transforms it into an integration event, which is then consumed by Context B; label the boundary as the bounded-context edge]

## Event Storming as a Discovery Technique

You cannot model events well by staring at a database schema. Events must be *discovered* from the business, and the fastest technique for that discovery is **Event Storming** — a collaborative workshop invented by Alberto Brandolini. It puts domain experts and engineers at the same wall and asks one question: what happens in this business?

The mechanics are deliberately low-tech. Participants write facts on orange sticky notes, phrased in the past tense, and place them on a timeline. `OrderPlaced` goes up, then `PaymentAuthorized`, then `OrderShipped`. When the orange notes stop flowing, other colors enter: blue for commands that trigger events, yellow for aggregates, pink for external systems, and purple for policies ("whenever *this* happens, do *that*"). The wall becomes a map of the business process before a single class is written.

Three signals from an Event Storming session directly shape your architecture:

1. **Clusters of events** around the same aggregate reveal a bounded context. Where the language shifts — where "order" starts meaning something different — you have found a boundary.
2. **Hotspots**, marked with red notes, expose disagreement or unknowns. These are the risky parts of the domain and deserve the most design attention.
3. **Pivotal events** — the ones every stakeholder points to — are your true integration events, the facts other contexts will want.

[DIAGRAM: sequence-style timeline of an Event Storming wall showing past-tense domain events left to right, with commands, aggregates, and a policy note, and a highlighted boundary where the ubiquitous language changes]

The payoff is that events emerge from the language of the business, not from the shape of a table. When a domain expert nods at `PaymentDeclined` and shakes their head at `UserRecordUpdated`, they are doing your naming review for free. Run the workshop before you design schemas, not after.

## Bounded Contexts and Event Contracts Between Teams

A **bounded context** is the scope within which a model and its ubiquitous language are consistent. "Customer" in the Sales context is not the same "Customer" in the Billing context, even if both map to the same person. Events are how these contexts talk without merging their models — and that makes every published event a **contract**.

Treating events as contracts changes how you manage them. A contract has an owner (the producing team), a specification (the schema), and consumers who build against it. Once someone depends on your integration event, you cannot silently change its shape. This is why mature organizations adopt **consumer-driven contracts**: consumers publish the expectations they hold, and the producer's pipeline verifies that changes do not break them. We return to schema evolution in depth in Chapter 8, but the modeling decision starts here — a well-modeled integration event is one whose meaning is stable enough to promise indefinitely.

The anti-corruption boundary is the practical mechanism. When Context B consumes an event from Context A, it translates A's vocabulary into its own model at the edge, rather than letting A's concepts spread inside. This keeps the two models free to evolve. The event is the wire between them; the translation layers on each side are the insulation.

**Pro Tip:** Assign every integration event a single owning team and record it in a discoverable catalog. An event with no owner is an event no one can safely change — and one that no one dares to delete.

## Granularity and Event Naming Conventions

Granularity is where good intentions produce bad systems. Too coarse, and one bloated event forces every consumer to parse fields they do not need. Too fine, and consumers must reassemble a business fact from a storm of fragments, reintroducing exactly the coupling events were meant to remove.

The guiding heuristic: **model events at the granularity of a business decision, not a data mutation.** `OrderPlaced` is a decision. `OrderTotalColumnUpdated` is a mutation. If a fact only makes sense to someone holding your table definition, it is too fine and probably not a domain event at all.

Naming carries as much weight as granularity. Follow these rules without exception:

- **Past tense, always.** An event records something that already happened: `InvoiceIssued`, not `IssueInvoice` (that is a command) and not `InvoiceIssue`.
- **Business language, not technical language.** `PaymentCaptured` beats `PaymentServiceApiCallSucceeded`.
- **Name the fact, not the handler.** `SubscriptionCancelled`, not `SendCancellationEmail` — the latter names a reaction, coupling the event to one consumer's intent.
- **Include the aggregate, keep it specific.** `CartCheckedOut` tells you the subject and the fact in two words.

[CODE: two contrasting event schema definitions side by side — a well-named coarse-grained domain event 'OrderPlaced' with meaningful business fields, versus an anti-pattern 'OrderTableRowChanged' exposing raw column diffs; annotate why the first is a durable contract and the second is technical noise]

A good name is a design review in itself. If a domain expert cannot understand your event from its name alone, the model is wrong — rename it before you ship it.

## Technical Noise as a Modeling Anti-Pattern

The most common failure in event-driven systems is **technical noise**: publishing infrastructure and persistence events as though they were domain facts. `EntitySaved`, `KafkaOffsetCommitted`, `CacheEvicted`, `FieldXChanged`. These events describe how the software works, not what the business did.

Technical noise is corrosive for three reasons. First, it couples consumers to your implementation — subscribers now depend on your ORM's save cadence or your caching strategy. Second, it destroys signal: real business events drown in a flood of mechanical chatter, and consumers cannot tell which events matter. Third, it lies. An `EntityUpdated` event claims a business fact occurred when often nothing meaningful did — a retry, a migration, or a no-op write.

The test is simple and unforgiving: **could a non-technical domain expert say this event out loud and mean it?** "The order was placed" passes. "The row was updated" fails. If the answer is no, you are looking at technical noise, and it does not belong on a domain topic.

[DIAGRAM: comparison chart contrasting a clean stream of business-meaningful events against a noisy stream polluted with persistence and infrastructure events, showing how consumers lose signal in the noisy case]

This does not mean technical events are worthless. Operational and infrastructure signals are legitimate — for monitoring, metrics, and debugging, which Chapter 9 covers. The sin is not producing them; it is publishing them onto the same domain channels that other teams treat as the source of business truth. Keep the two streams separate. Your domain topics are a business ledger, and a ledger with fake entries is worse than no ledger at all.

## Key Takeaways

- **Domain events** live inside one bounded context; **integration events** are deliberate public contracts. Never publish a raw domain event across a boundary — translate it first.
- **Event Storming** discovers events from the business language, exposing bounded contexts, hotspots, and the pivotal facts that become integration events.
- Every published event is a **contract** with an owner, a schema, and consumers; anti-corruption boundaries keep producer and consumer models independent.
- Model events at the granularity of a **business decision**, name them in the **past tense** using ubiquitous language, and name the fact rather than the handler.
- **Technical noise** — persistence and infrastructure events masquerading as domain facts — couples consumers to your implementation and drowns real signal. Apply the domain-expert test.

## What's Next

With well-modeled events in hand, Chapter 3 examines how those events actually flow — comparing broker and mediator topologies, choreography versus orchestration, and the messaging technologies that carry your domain facts across the system.
