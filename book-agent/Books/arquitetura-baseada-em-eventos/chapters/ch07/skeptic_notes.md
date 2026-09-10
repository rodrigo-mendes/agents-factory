## Skeptical Review — Consistency, Sagas, and Long-Running Processes
Reviewer profile: Rigorous technical skeptic
Date: 2026-09-01

---

### Choreographed Versus Orchestrated Sagas

> ⚠️ **Critical Note:** The table states that choreography carries a "High" risk of cycles as an intrinsic property, but cycles are a *design* risk, not a topological one. A well-designed choreographed saga with carefully named, domain-scoped events (e.g., `OrderPlaced` rather than a generic `ProcessNext`) and a policy that services never react to their own emitted events will never produce a cycle. Presenting cycles as an inherent characteristic of choreography may push readers toward orchestration prematurely and fails to distinguish between a pattern's properties and a pattern's common misuse. Similarly, the "3–4 steps" threshold for switching to orchestration is presented as a universal rule, but it is a heuristic that ignores team structure, domain stability, and tooling context. A two-step saga with complex branching logic may warrant an orchestrator; a six-step saga with completely stable, linear reactions may not.

**Severity:** minor
**Suggested fix:** Change the "Risk of cycles" row to "Cycle risk if events are poorly scoped" with a note that it is preventable by design. Add a footnote acknowledging the 3–4 step threshold is a heuristic, not a law, and call out that Conway's Law — which team owns the choreography logic — is a valid secondary factor.

---

### Compensating Transactions and Semantic Rollback

> ⚠️ **Critical Note:** Property 2 states "Compensations must be commutative-safe with respect to ordering." This is a terminology error that directly contradicts the advice that follows it. *Commutativity* means the order of operations does not matter — if compensations were commutative, there would be no need to run them in reverse order. The prose then immediately instructs the reader to run compensations in reverse order, which is the *opposite* of a commutativity requirement. What the property actually requires is strict *sequential* reverse ordering: each compensation must be applied in inverse sequence relative to the forward steps. Calling this "commutative-safe" will confuse any engineer who knows the term.

**Severity:** important
**Suggested fix:** Replace "Compensations must be commutative-safe with respect to ordering" with "Compensations must be applied in strict reverse sequence: undo the last committed step first." Clarify that commutativity would mean order is irrelevant, which is the opposite of the constraint here.

---

### Compensating Transactions and Semantic Rollback

> ⚠️ **Critical Note:** The entire section on compensations describes a single saga instance in isolation. It never addresses the *saga isolation problem*: because each local transaction commits independently and intermediate saga states are fully visible to other concurrent transactions, sagas suffer from phenomena that ACID isolation prevents — specifically dirty reads and lost updates. A concurrent process reading the order record between `PaymentCaptured` and `ShipmentCreated` sees a state that may later be compensated. Depending on what it does with that data, the compensation may be insufficient to restore global correctness. Garcia-Molina's original 1987 paper introducing sagas explicitly identified this limitation, and Chris Richardson's "Microservices Patterns" (the canonical practitioner reference) dedicates a full section to countermeasures: semantic locks, commutative updates, pessimistic views, and re-read values. For a senior architect audience designing high-concurrency order processing systems, omitting this is a material gap — it is the most common source of subtle data corruption in production saga implementations.

**Severity:** blocking
**Suggested fix:** Add a subsection "The Saga Isolation Problem" covering: (1) the absence of cross-step isolation means intermediate states are visible to concurrent transactions; (2) the three resulting anomalies (dirty reads, non-repeatable reads, lost updates at the saga level); (3) the four countermeasure patterns (semantic locks, commutative updates, pessimistic view, re-read value) with a note on when each applies. This is not optional nuance — it is a design constraint every implementer will encounter.

---

### Why Distributed ACID Transactions Fail

> ⚠️ **Critical Note:** The chapter frames 2PC as a pure "CP" choice — a system that sacrifices availability in exchange for consistency when a partition occurs. This is an oversimplification that the in-doubt state already disproves within the same section. When the coordinator crashes after participants have voted *yes* but before the commit decision is broadcast, participants are locked and uncertain — they can neither commit nor abort safely. The system at that point is neither available *nor* consistent: it is stuck. 2PC does not reliably guarantee C under coordinator failure; it guarantees that no incorrect commit happens, which is not the same as providing a consistent read. The CAP characterization of 2PC as CP is a useful shorthand for the partition-tolerance trade-off, but presenting it without the caveat that the "C" guarantee degrades under coordinator failure is misleading for practitioners evaluating failure modes.

**Severity:** important
**Suggested fix:** Qualify the CP characterization: "2PC is typically described as CP, but the guarantee is more precisely 'no incorrect commit' — under coordinator failure, in-doubt participants achieve neither availability nor a guaranteed consistent state. The real cost of 2PC is not only lost availability under partitions but lost recoverability under coordinator crashes."

---

### Eventual Consistency Versus Strong Consistency

> ⚠️ **Critical Note:** The prose defines "strong consistency" as "once a write completes, every subsequent read — from anywhere — sees that write," which is the definition of *linearizability*, one specific consistency model. "Strong consistency" is an informal umbrella term used differently across literature. Sequential consistency, for instance, guarantees the same program order across all nodes but does not guarantee that a read immediately after a write on a different node sees the new value. For a senior architect audience, conflating the informal term with the precise model linearizability matters: when they evaluate database guarantees in their vendor documentation (e.g., Google Spanner advertising "external consistency," DynamoDB offering "strong reads"), they will encounter precise terminology that this definition does not prepare them to interpret correctly.

**Severity:** minor
**Suggested fix:** Add a parenthetical: "Strong consistency, as used here, corresponds to *linearizability* — reads always reflect the latest completed write. This is the strongest model; sequential consistency and causal consistency are weaker but still 'strong' in the colloquial sense. Vendor documentation will use these terms precisely."

---

### CAP Theorem Applied to Event Flows

> ⚠️ **Critical Note:** The CAP theorem is presented as a complete and current framework for distributed consistency decisions, but its practical limitations are well-established. Eric Brewer himself acknowledged in his 2012 retrospective ("CAP Twelve Years Later: How the 'Rules' Have Changed," IEEE Computer) that the theorem's binary framing obscures more than it reveals. The PACELC theorem (Abadi, 2012) — which extends CAP to address the latency/consistency trade-off that exists *even when there is no partition* — is the more operationally relevant model for architects designing event-driven systems, where the everyday question is not "what happens during a partition" but "what is the latency cost of stronger consistency when the network is healthy." Presenting CAP without this context leads senior architects to use it as a blunt instrument when evaluating system behavior outside failure scenarios, which is the common case.

**Severity:** important
**Suggested fix:** Add a "Beyond CAP" sidebar noting: (1) CAP's "C" specifically means linearizability, not all consistency models; (2) the PACELC model extends the analysis to the latency/consistency dimension under normal operation; (3) Brewer's 2012 retrospective recommends treating the trade-off as continuous rather than binary. This positions the reader to read vendor documentation accurately.

---

### Process Managers and State Machines

> ⚠️ **Critical Note:** The section recommends workflow engines (Temporal, AWS Step Functions, Camunda) as managed persistent state machines and says "the pattern is the same whether you hand-roll it or buy it." This understates a meaningful operational and semantic difference. Temporal's durable execution model executes workflow code deterministically by replaying history — it is not a state machine in the traditional sense; application code *is* the state machine. This means debugging, versioning, and patching running workflows in Temporal require understanding replay semantics and determinism constraints, which are non-trivial. AWS Step Functions uses JSON-defined state machines with different retry and error-catching semantics than hand-rolled implementations. Telling a senior engineer that "the pattern is the same" before they have chosen a tool leaves them unprepared for the operational model differences they will encounter.

**Severity:** minor
**Suggested fix:** Qualify the equivalence: "The underlying pattern — durable state, timers, retries — is the same. However, each tool enforces it differently: Temporal replays workflow history to reconstruct state (requiring deterministic code); Step Functions encodes the state machine as a service-managed definition; hand-rolled implementations control persistence directly. Evaluate the operational and versioning model of each tool, not just the feature list."

---

## Summary
- Total notes: 7
- Blocking (inline callout): 1
- Important (collapsed): 3
- Minor (file only): 3

**Top 3 items requiring attention:**

1. [Compensating Transactions and Semantic Rollback] **Missing saga isolation problem** — The complete absence of dirty-read and lost-update anomalies in concurrent saga execution is a blocking gap for senior architects building high-concurrency systems. This is the most common source of subtle production data corruption in saga implementations.

2. [Compensating Transactions and Semantic Rollback] **"Commutative-safe" terminology error** — Commutativity means order is irrelevant; the prose immediately contradicts this by mandating reverse ordering. This will confuse any engineer who knows the term and may produce incorrect implementations.

3. [CAP Theorem Applied to Event Flows] **CAP presented without its known limitations** — For a senior architect audience, presenting CAP as the definitive framework without PACELC or Brewer's 2012 retrospective leaves them underequipped to reason about the latency/consistency trade-off under normal (non-partition) operating conditions, which is the everyday case.
