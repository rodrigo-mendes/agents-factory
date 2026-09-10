## Skeptical Review — Modeling Events as Domain Facts
Reviewer profile: Rigorous technical skeptic
Date: 2026-09-01

---

### Domain Events Versus Integration Events

> ⚠️ **Critical Note:** The table labels domain event coupling as "Tight, by design." This is misleading and risks confusing senior architects. Domain events within a bounded context are precisely a *decoupling* mechanism: an Order aggregate raises `OrderPlaced` so that other domain services (inventory reservation, email dispatch) can react without the aggregate calling them directly. "Tight" is inaccurate; the correct framing is "internal — boundary does not apply." Describing intra-context coupling as "tight by design" could lead readers to resist domain events inside their own context, defeating their purpose.

**Severity:** important
**Suggested fix:** Replace "Tight, by design" in the Coupling row with "Internal — no contract boundary; consumers share the same model." Add a sentence noting that domain events *enable* loose coupling within a context between aggregates and domain services.

---

### Domain Events Versus Integration Events

> ⚠️ **Critical Note:** The prose presents the translation step ("never publish a raw domain event across a context boundary — translate it first") as a design rule without addressing the reliability mechanism that makes this rule safe to follow. The translation from domain event to integration event is typically done inside the same transaction or via an outbox pattern; if it is done by a separate process or handler, the translation itself can fail silently, producing either duplicates or lost events. For senior architects, the "translate it first" rule is incomplete without acknowledging that the *how* of reliable translation is non-trivial and is the source of most real-world integration bugs. Deferring this entirely to Chapter 3 leaves a dangerous gap at the exact moment the reader is deciding to adopt the pattern.

**Severity:** important
**Suggested fix:** Add a one- or two-sentence callout acknowledging that reliable translation requires an atomicity guarantee (e.g., transactional outbox or event sourcing), and forward-reference the specific chapter where this is addressed so readers know the gap is intentional, not overlooked.

---

### Event Storming as a Discovery Technique

> ⚠️ **Critical Note:** Event Storming is presented as a straightforwardly accessible technique: "participants write facts on orange sticky notes" and the wall "becomes a map of the business process before a single class is written." This glosses over the substantial organizational and facilitation prerequisites. Without an experienced facilitator, sessions routinely collapse into technical jargon, scope explosion, or competing political agendas between departments. Domain experts must be willing and available — a constraint that is often the hardest part in enterprise settings. Presenting the technique as low-effort ("deliberately low-tech") without acknowledging facilitation complexity could cause teams to run poorly structured sessions, produce misleading event maps, and blame the technique rather than the execution.

**Severity:** important
**Suggested fix:** Add a short paragraph noting that effective Event Storming requires a skilled, neutral facilitator (ideally experienced with DDD), prepared domain experts who have authority to describe the business (not just developers describing what the system does), and a time commitment of at least a full day per major process. Recommend Brandolini's "Introducing EventStorming" as the reference for facilitation details.

---

### Bounded Contexts and Event Contracts Between Teams

> ⚠️ **Critical Note:** The prose states that "a well-modeled integration event is one whose meaning is stable enough to promise indefinitely." This is an unrealistic and potentially harmful standard for most business domains. Business meaning changes: regulations shift, products are discontinued, mergers redefine "customer." The correct framing is that integration events should be *stable enough to require explicit versioning rather than silent breakage* — not stable indefinitely. Promising indefinite stability could cause teams to over-engineer events in an attempt to anticipate all future meanings, resulting in bloated, over-generic schemas that are harder to evolve than well-scoped versioned ones.

**Severity:** important
**Suggested fix:** Replace "stable enough to promise indefinitely" with "stable enough that changes require explicit versioning and coordinated consumer migration — not silent schema mutation." Briefly note that business domain evolution makes indefinite stability a fiction; good event design minimizes the *frequency* of breaking changes, not their possibility.

---

### Granularity and Event Naming Conventions

> ⚠️ **Critical Note:** The granularity discussion is missing the critical fat-versus-thin event trade-off that every senior architect must decide at design time. Fat events (carrying full aggregate state) make consumers self-sufficient but increase payload size, may leak internal model details, and make it harder to control what constitutes a "meaningful" change. Thin events (carrying only the ID or a minimal diff) keep payloads small but force consumers to make a synchronous lookup call to fetch needed state, reintroducing temporal coupling and a potential availability dependency. For an audience of senior engineers and architects, presenting granularity only as "business decision vs. data mutation" without naming this trade-off leaves out the most consequential design decision at the schema level.

**Severity:** important
**Suggested fix:** Add a sub-section or callout covering the fat/thin spectrum: fat events favor consumer autonomy at the cost of payload size and model exposure; thin events reduce payload and exposure but can force consumers into synchronous queries. Reference Event-Carried State Transfer (from Chapter 1) as the recommended default for cross-context integration, and note that thin events are preferable when payload size or model sensitivity is a concern within a context.

---

### Granularity and Event Naming Conventions

> ⚠️ **Critical Note:** "Follow these rules without exception" overstates the universality of the naming conventions. There are legitimate, well-established cases where the rules bend: audit trails for CQRS read-model rebuilds sometimes include technical discriminators; event-sourced aggregates within a bounded context may use names like `PriceOverridden` that are meaningful only to the domain model, not to a general business stakeholder. Presenting these as exceptionless risks alienating senior practitioners who know the exceptions and will distrust the rest of the chapter.

**Severity:** minor
**Suggested fix:** Change "without exception" to "as the default." Add a parenthetical noting that internal CQRS or event-sourcing scenarios may tolerate more technical naming within a bounded context, as long as those events are never promoted to integration events without renaming.

---

### Technical Noise as a Modeling Anti-Pattern

> ⚠️ **Critical Note:** The domain-expert test ("could a non-technical domain expert say this event out loud and mean it?") is presented as "simple and unforgiving" but is actually context-dependent and subjective. First, many systems have no direct access to domain experts at development time. Second, some events have a legitimate dual nature: `UserSessionExpired` is infrastructure-adjacent but carries genuine business meaning for fraud detection or compliance. Third, the test depends heavily on which domain expert you ask and what they consider "meaningful." Stating the test is unforgiving implies it is a reliable binary gate, when in practice it is a useful heuristic that requires practitioner judgment.

**Severity:** minor
**Suggested fix:** Qualify the test: "This is a reliable heuristic, not a binary gate. Apply judgment when an event sits on the boundary — if multiple domain experts disagree about whether it is meaningful, that disagreement is itself a signal to clarify the model, not to publish the event."

---

## Summary
- Total notes: 6
- Blocking (inline callout): 0
- Important (collapsed): 4
- Minor (file only): 2

**Top 3 items requiring attention:**

1. [Granularity and Event Naming Conventions] Missing fat-vs-thin event trade-off — the most consequential schema-level decision for this audience is absent
2. [Domain Events Versus Integration Events] Translation reliability gap — "translate it first" rule is given without the atomicity mechanism that makes it safe, leaving a critical implementation hazard unaddressed
3. [Bounded Contexts and Event Contracts Between Teams] "Stable enough to promise indefinitely" — an unachievable standard that could drive over-engineering of event schemas
