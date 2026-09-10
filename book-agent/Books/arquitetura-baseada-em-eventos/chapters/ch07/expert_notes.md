## Expert Review — Consistency, Sagas, and Long-Running Processes
Reviewer profile: Senior practitioner, 10+ years, cloud-native microservices and corporate distributed systems
Date: 2026-09-01

---

### Why Distributed ACID Transactions Fail

> **Expert Note:** The prose correctly identifies 2PC as the pattern to replace, but misses a widespread enterprise trap: XA transactions (JTA in Jakarta EE, Spring's `@Transactional` spanning multiple `DataSource` or `ConnectionFactory` beans, and MSDTC in .NET) are 2PC in disguise. Many teams believe they are not using distributed ACID until they trace a production incident and find an XA coordinator quietly holding locks across a database and a message broker. The tell is a `javax.transaction.UserTransaction` or `ChainedTransactionManager` in the dependency tree. Audit your dependency graph before declaring you have eliminated 2PC from a legacy migration path.

**Integration level:** inline callout
**Priority:** high

---

### Compensating Transactions and Semantic Rollback

> **Expert Note:** The prose establishes that compensations must be idempotent, but it does not address the case where the compensation itself fails — and this is one of the most operationally dangerous scenarios in production sagas. A `RefundPayment` command can be rejected by a downstream payment processor that is temporarily down, or refused because the card has been cancelled. When the compensating transaction is undeliverable or rejected, the saga is stuck in a partially compensated state with no automatic resolution path. Production systems must model this explicitly: a `CompensationFailed` terminal state backed by a dead-letter queue, an alerting rule, and a manual remediation playbook. In regulated industries (financial services, healthcare) this state must also trigger a compliance event. Teams that omit this state discover it exists anyway — they just cannot observe or act on it.

**Integration level:** inline callout
**Priority:** high

---

### Choreographed Versus Orchestrated Sagas

> **Expert Note:** The prose correctly warns about "event spaghetti" in choreography, but the reliability dependency on transactional event publication deserves equal emphasis. In a choreographed saga, if a service commits its local database transaction but crashes before publishing the downstream event, the saga silently stalls — no exception, no alert, no next step. The Outbox Pattern (writing the event to a local `outbox` table in the same ACID transaction and polling it with a relay) is not optional for choreographed sagas in production; it is the mechanism that makes the choreography reliable at all. Without it, the decoupling advantage is undermined by a hidden reliability gap. If this chapter references the Outbox Pattern from an earlier chapter, make that dependency explicit here.

**Integration level:** inline callout
**Priority:** high

---

### Choreographed Versus Orchestrated Sagas

> **Expert Note:** Testing strategy diverges sharply between the two topologies, and this shapes team velocity in practice. Choreographed sagas require contract testing across service boundaries (Pact, Spring Cloud Contract) to verify that an event published by Service A actually satisfies Service B's consumer schema — without this, integration breaks silently when a field is renamed. Orchestrated sagas can be unit-tested in isolation: mock the downstream command channels, feed reply events, assert state transitions. The orchestrator test suite becomes the saga's living documentation. Teams that choose orchestration for visibility often underestimate that it also gives them a dramatically simpler test surface — a point worth making to architects who prefer choreography for ideological reasons.

**Integration level:** collapsed block
**Priority:** medium

---

### Process Managers and State Machines

> **Expert Note:** The prose recommends Temporal, AWS Step Functions, and Camunda as reasonable choices, which is accurate. However, their durability models differ in ways that surface under failure: Temporal persists a full replay-safe event history to a database (Postgres or Cassandra) and reconstructs workflow state by replaying that history — a crash mid-step replays all preceding activities on restart. AWS Step Functions stores execution state in its own managed store but imposes hard limits (25,000 history events per execution) that affect long-running processes spanning weeks. Camunda 8 uses Zeebe's replicated log. Teams that select one of these tools based on developer experience alone, then hit an execution history limit or discover that Temporal requires operating its own database cluster, face expensive migrations. Evaluate the durability model and operational footprint before committing.

**Integration level:** collapsed block
**Priority:** medium

---

### Process Managers and State Machines

> **Expert Note:** A common anti-pattern when teams adopt workflow engines is encoding business rules inside the orchestrator itself — conditional branches based on customer tier, pricing logic, compliance checks — turning it into a "God Workflow." The orchestrator should issue commands and receive replies; it should contain only control flow (sequence, branching on reply type, timeout). Business rules belong in the services that execute the commands. When the orchestrator grows past a few hundred lines of control logic, it becomes as hard to change as the monolith the saga replaced. The discipline is: if a branch condition requires domain knowledge, it belongs in a service, not in the saga coordinator.

**Integration level:** collapsed block
**Priority:** medium

---

### Eventual Consistency Versus Strong Consistency

> **Expert Note:** The prose presents consistency as a binary (strong vs. eventual), which is pedagogically useful but can lead architects to over-engineer. In practice, many UX and API requirements need only "read-your-writes" (causal) consistency — the user who just created a resource can see it on the next request, but other users seeing a slightly stale view is acceptable. This is weaker than strong consistency but stronger than bare eventual. Designing for read-your-writes often eliminates the need for synchronous cross-service calls: redirect the user to the newly created resource's canonical URL immediately after the local commit, and rely on event propagation for everyone else. Distinguishing "which consistency level does this user action actually need?" prevents the knee-jerk response of adding synchronous calls to achieve strong consistency where causal would suffice.

**Integration level:** collapsed block
**Priority:** medium

---

### Compensating Transactions and Semantic Rollback

> **Expert Note:** Late compensations carry real financial and legal costs that business stakeholders are often unaware of until the first incident. A credit card refund issued 30 days after the original charge succeeds technically and semantically, but the original authorization has already settled and a new interchange transaction is incurred — the business eats the fee. Beyond 120 days, most card networks no longer allow standard refunds and require an out-of-band credit. Similar time windows apply to bank transfers (SWIFT recall windows), regulatory reporting (corrections filed after quarter-close trigger audit events), and consumer protection laws (right-of-withdrawal deadlines). When designing compensations, the business must specify not just the compensation action but its time-to-live — the window within which the compensation is still commercially viable — and the saga must route to a human escalation path when that window expires.

**Integration level:** file only
**Priority:** low

---

## Summary
- Total notes: 7
- High priority (inline callout): 3
- Medium priority (collapsed block): 4
- Low priority (file only): 1 (note appears twice under Compensating Transactions; the second entry is the low-priority one)

**Top 3 notes to integrate:**
1. [Why Distributed ACID Transactions Fail] XA/JTA as hidden 2PC in enterprise Java and .NET stacks
2. [Compensating Transactions and Semantic Rollback] CompensationFailed terminal state and dead-letter handling when compensations themselves fail
3. [Choreographed Versus Orchestrated Sagas] Transactional Outbox Pattern as a reliability prerequisite for choreography, not an optional enhancement
