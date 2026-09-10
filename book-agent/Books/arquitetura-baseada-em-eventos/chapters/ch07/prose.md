# Chapter 7: Consistency, Sagas, and Long-Running Processes

## Opening Problem Statement

Chapter 6 left the write side settled: state is an immutable log of events, and truth lives in the event store. But that chapter quietly assumed a comfortable boundary — one aggregate, one stream, one transaction. Real business processes are not so polite. Placing an order touches inventory, payment, and shipping. Onboarding a customer touches identity, billing, and compliance. Each of these lives in a different service, behind a different database, owned by a different team.

Here is the uncomfortable question this chapter answers: **how do you keep three services consistent when you cannot wrap them in a single transaction?** The classic instinct — a distributed transaction that locks all three and commits atomically — sounds correct and is almost always wrong in a cloud-native system. It couples availability, punishes latency, and fails in ways that are hard to reason about.

The alternative is the **saga**: a sequence of local transactions, each committing independently, coordinated by events, and reversed not by rollback but by *compensation*. Sagas trade the illusion of instantaneous global consistency for something honest and operable: **eventual consistency**. This chapter shows how sagas work, when to choreograph them and when to orchestrate them, how to design compensations that actually undo business effects, and how the CAP theorem quietly governs every one of these choices.

## Eventual Consistency Versus Strong Consistency

Start with the word every architect uses and few define precisely. **Strong consistency** means that once a write completes, every subsequent read — from anywhere — sees that write. The system behaves as if there were a single copy of the data and a single clock. This is the guarantee a local ACID transaction gives you inside one database.

**Eventual consistency** makes a weaker promise: if writes stop, all replicas and derived views will *eventually* converge to the same value. Between the write and that convergence, there is a window in which different parts of the system disagree. That window is not a bug. It is the price of keeping services independent and available.

The mistake is treating eventual consistency as "strong consistency, but sloppy." It is a different model with different rules. You do not ask "is the data consistent?" You ask "what is the maximum staleness the business can tolerate, and what happens inside that window?"

Consider a familiar analogy. When you transfer money between banks, the sender's balance drops immediately, but the recipient sees nothing for hours or days. The money is, for a while, *in flight* — visible nowhere. The banking system is eventually consistent by design, and it works because the business defined explicit intermediate states ("pending," "settled") and rules for each. That is the discipline eventual consistency demands.

[DIAGRAM: sequence diagram contrasting strong consistency (single locked transaction across Order, Payment, Inventory committing together) versus eventual consistency (three independent local commits over time, with a visible inconsistency window between them)]

The table below sharpens the contrast.

| Dimension | Strong consistency | Eventual consistency |
|---|---|---|
| Read after write | Always current | Current *eventually* |
| Scope | Single database / transaction | Multiple services |
| Availability under partition | Sacrificed | Preserved |
| Latency | Higher (coordination) | Lower (local commits) |
| Failure mode | All-or-nothing | Partial, then reconciled |
| Reasoning cost | Low | High — intermediate states matter |

The senior takeaway: **eventual consistency is not a compromise you accept reluctantly; it is the enabling assumption of independent services.** The moment you demand strong consistency across service boundaries, you have re-coupled the services you spent Chapters 1 through 6 decoupling.

## Why Distributed ACID Transactions Fail

Before sagas, honor the pattern they replace. The textbook answer to multi-service consistency is the **two-phase commit** (2PC): a coordinator asks every participant to *prepare*, waits for all to vote yes, then tells all to *commit*. If any participant votes no, everyone aborts. On paper, atomicity across services.

In practice, 2PC has three fatal properties for cloud-native systems.

First, **it holds locks across the network.** Between prepare and commit, every participant keeps its rows locked, waiting for the coordinator. A slow network or a distant service turns a millisecond lock into a multi-second one, collapsing throughput.

Second, **it is a blocking protocol.** If the coordinator crashes after participants vote yes but before it broadcasts the decision, participants are stuck — locked, uncertain, unable to safely proceed or abort. This is the well-known "in-doubt" state, and recovering from it is operationally miserable.

Third, **it couples availability.** A transaction succeeds only if *every* participant is up at the same instant. Five services at 99.9% availability each yield roughly 99.5% combined — you have multiplied your fragility. This directly violates the independence that makes microservices worth their cost.

[CODE: pseudocode of a two-phase commit coordinator showing the prepare/vote/commit phases and the in-doubt window where the coordinator crash leaves participants blocked with locks held]

There is a deeper truth here, and it is the CAP theorem, which we return to at the end of the chapter: when a network partition splits your services, 2PC chooses consistency by refusing to proceed. For most business processes — orders, bookings, signups — refusing to proceed is the wrong answer. The business would rather accept the order now and reconcile later. That preference *is* the choice of a saga.

## Choreographed Versus Orchestrated Sagas

A **saga** is a sequence of local transactions where each step publishes an event that triggers the next. If a step fails, the saga runs **compensating transactions** to undo the completed steps. There are two ways to wire the steps together, and the distinction — first met in Chapter 3 as a topology, now applied specifically to sagas — defines how you will operate the system.

In a **choreographed saga**, there is no central coordinator. Each service listens for events, does its local work, and emits its own event. The Order service publishes `OrderPlaced`; the Payment service reacts, charges the card, and publishes `PaymentCaptured`; the Inventory service reacts to *that* and reserves stock. The flow lives in the reactions. No single component knows the whole process.

In an **orchestrated saga**, a dedicated coordinator — the **orchestrator** — owns the process. It sends explicit commands (`CapturePayment`, `ReserveStock`), waits for replies, and decides the next step. The Order Orchestrator knows every step, every possible failure, and every compensation. The flow lives in one place.

[DIAGRAM: side-by-side comparison — left panel choreographed saga as a chain of services each reacting to the previous event with no center; right panel orchestrated saga with a central orchestrator issuing commands and receiving replies from Payment, Inventory, Shipping]

The trade-off is real and it is about *where the process logic lives*.

| Factor | Choreography | Orchestration |
|---|---|---|
| Coupling | Low — services know only events | Higher — orchestrator knows all steps |
| Visibility | Poor — flow is implicit | Excellent — flow is explicit in one place |
| Adding a step | Touch multiple services | Touch the orchestrator |
| Risk of cycles | High — events triggering events | Low — commands are directed |
| Best for | Short flows, 2–4 steps | Complex flows, many branches |
| Debugging | Hard — no single narrative | Easier — one state to inspect |

Here is the opinionated guidance. **Use choreography for short, stable flows** where the reactions are obvious and unlikely to change. The decoupling is genuine and the simplicity is real. But **the moment a saga grows past three or four steps, or acquires conditional branches, reach for orchestration.** Choreographed sagas at scale become "event spaghetti" — nobody can tell you what the process does without tracing events across six services. The implicit control flow that makes choreography elegant at small scale makes it unmaintainable at large scale. Prefer the boring, visible orchestrator.

## Compensating Transactions and Semantic Rollback

The heart of the saga is what happens when step four fails after steps one through three succeeded. There is no `ROLLBACK` — those transactions already committed, in other databases, possibly hours ago. Instead, the saga executes **compensating transactions**: new transactions that semantically undo the effect of the completed ones.

The critical word is **semantically**. A compensation is not a technical reversal to a prior state; it is a *new business action* that counteracts a previous one. You do not un-charge a credit card — you *issue a refund*. You do not un-send an email — you *send a correction*. You do not delete a shipment record — you *cancel the shipment*. The compensating action is itself a real, recorded, forward-moving fact.

[CODE: order saga example showing forward steps (ReserveStock, CapturePayment, CreateShipment) each paired with its compensation (ReleaseStock, RefundPayment, CancelShipment), and the compensation loop that runs completed steps in reverse order when a later step fails]

Three properties make compensations trustworthy, and each maps to a design rule.

1. **Compensations must be idempotent.** A refund command may be delivered more than once under at-least-once delivery (Chapter 4). Reissuing it must not refund twice. Use a compensation key and check "already compensated?" before acting.

2. **Compensations must be commutative-safe with respect to ordering.** Run them in reverse order of the forward steps, so effects unwind in a sensible sequence — release the stock you reserved, refund the payment you captured.

3. **Some actions cannot be compensated — so order the saga around them.** You cannot un-launch a missile or un-send a physical package. These are **pivot transactions**: after the pivot, the saga can only go forward. The design rule is to place all *compensatable* steps before the pivot and all *retriable* (guaranteed-to-eventually-succeed) steps after it. Structure the saga so the irreversible step happens last, once everything reversible has already succeeded.

This taxonomy — compensatable, pivot, retriable — is the single most useful mental model for designing sagas. Classify every step, then order them so failure is always either fully reversible or guaranteed to complete.

> **Pro Tip:** Compensation is not error handling bolted on afterward. It is half of the business process. If you cannot describe how to undo a step in business terms, you do not yet understand the step. Model the compensation at the same time you model the forward action — in the same Event Storming session from Chapter 2.

## Process Managers and State Machines

An orchestrator that merely forwards commands is thin. A real orchestrator must remember: which steps have completed, which are pending, what to do on each reply, when to time out, and when to start compensating. That stateful coordinator has a name — the **process manager** — and its most reliable implementation is an explicit **state machine**.

A process manager is a component that receives events, maintains the state of a single saga instance, and decides the next command based on that state. Model it as a finite set of states with defined transitions: `AwaitingPayment → AwaitingStock → AwaitingShipment → Completed`, with failure edges branching into `Compensating → Cancelled`. Every incoming event either advances the state or triggers compensation. Nothing happens implicitly.

[DIAGRAM: state machine (state diagram) for an order saga with states Started, AwaitingPayment, AwaitingStock, AwaitingShipment, Completed, Compensating, Cancelled, showing the happy-path transitions on success events and the compensation transitions on failure/timeout events]

Two implementation disciplines separate a robust process manager from a fragile one.

**Persist the saga state on every transition.** The process manager is itself an aggregate — and everything from Chapter 6 applies. Its state must survive a crash. When the orchestrator restarts, it rehydrates each in-flight saga from its persisted state and resumes exactly where it left off. A process manager that keeps saga state only in memory will, on the first pod restart, orphan every in-flight order. This is not hypothetical; it is the most common saga bug in production.

**Make timeouts first-class states, not afterthoughts.** In a synchronous world, a hung call throws an exception. In a saga, a step that never replies simply... waits, forever, silently. The process manager must set a timer on each pending step. If `PaymentCaptured` does not arrive within the deadline, the timeout is an *event* that transitions the state machine — usually into compensation. Long-running processes live and die by their handling of the reply that never comes.

> **Pro Tip:** Resist the urge to hand-code process managers with nested conditionals and boolean flags (`paymentDone`, `stockDone`). That style rots the instant a fourth step appears. An explicit state machine — a table of (current state, event) → (next state, action) — stays readable at ten states and is directly testable without any infrastructure.

Many teams reach for a workflow engine here — Temporal, AWS Step Functions, Camunda — precisely because these tools provide durable state, timers, and retries out of the box. That is a reasonable choice. But understand what they give you: a managed, persistent state machine. The pattern is the same whether you hand-roll it or buy it.

## CAP Theorem Applied to Event Flows

Everything in this chapter is a consequence of one theorem, so make it explicit. The **CAP theorem** states that a distributed system, when a network **partition** (P) splits it, can preserve either **consistency** (C) — every node sees the same data — or **availability** (A) — every request gets a response — but not both. Partitions are not optional; networks fail. So the real choice is *not* "CA versus something." When the partition happens, you choose C or A.

Distributed transactions and 2PC are the **CP** choice: under a partition, they refuse to proceed to keep data consistent. The order simply fails. Sagas are the **AP** choice: under a partition, each local transaction still commits, the system stays available, and consistency is restored later through the flow of events and compensations. **A saga is, at its core, an architectural bet that availability matters more than instantaneous consistency** — and for most business processes, that bet is correct.

This reframes eventual consistency from a limitation into a deliberate position. You are not settling for weak consistency because sagas cannot do better. You are *choosing* availability, and eventual consistency is the disciplined way to honor that choice while still converging to a correct final state.

[DIAGRAM: flowchart showing the CAP decision for a cross-service business operation — partition detected → branch: choose Consistency (block, fail the operation, 2PC/CP) versus choose Availability (commit locally, converge later via saga/AP), annotating each branch with its business consequence]

One nuance worth internalizing, and it is where senior architects earn their title. CAP is not a property of your whole system; it is a property of each *operation*. Charging a payment might demand CP-like strictness within the payment service's own boundary — a single ACID transaction, no ambiguity about money. Coordinating that payment with inventory and shipping across services is AP — a saga. Mature architectures are not uniformly consistent or uniformly available. They are strongly consistent *inside* each service boundary and eventually consistent *across* boundaries, with sagas as the bridge between the two regimes.

## Key Takeaways

- **Distributed ACID transactions do not scale.** Two-phase commit holds locks across the network, blocks on coordinator failure, and multiplies your services' fragility into a single point of failure. Reject it for cross-service business processes.
- **A saga is a sequence of local transactions coordinated by events, reversed by compensation, not rollback.** It accepts eventual consistency to preserve availability and service independence.
- **Choreograph short, stable flows; orchestrate complex or branching ones.** Choreography decouples but hides the process; orchestration centralizes logic and makes the flow visible. Past three or four steps, prefer orchestration.
- **Compensations are new business actions, not technical undos.** Classify every step as compensatable, pivot, or retriable, and order the saga so irreversibility comes last.
- **A process manager is a persistent state machine.** Persist state on every transition and treat timeouts as first-class events, or the first pod restart will orphan your in-flight sagas.
- **Sagas are the AP choice of the CAP theorem.** Strong consistency inside each service boundary, eventual consistency across boundaries, with the saga as the bridge.

## What's Next

Sagas depend on events whose meaning stays stable across services and across time — which raises the problem Chapter 8 confronts head-on: how to evolve event schemas and contracts without breaking the consumers and long-running sagas that depend on them.
