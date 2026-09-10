## Skeptical Review — Schema Evolution and Event Versioning
Reviewer profile: Rigorous technical skeptic
Date: 2026-09-01

---

### Backward and Forward Compatibility

> ⚠️ **Critical Note:** The prose states that FULL compatibility "is the target most mature registries default to." This is factually incorrect. Confluent Schema Registry — the dominant registry in Kafka-based systems and the de facto reference implementation — defaults to `BACKWARD`, not `FULL`. AWS Glue Schema Registry also defaults to `BACKWARD_ALL`. No widely deployed registry defaults to `FULL` out of the box. An architect who reads this claim and then opens their registry's admin UI will immediately encounter a contradiction, which undermines trust in the entire chapter.

**Severity:** blocking
**Suggested fix:** Replace the sentence with the accurate statement: most mature registries default to `BACKWARD` (Confluent) or `BACKWARD_ALL` (AWS Glue). Clarify that `FULL` must be explicitly configured and explain the trade-off: it prevents field removal, which causes schema bloat over time but eliminates an entire class of consumer breakage.

---

### Schema Registry and Formats (Avro, JSON Schema, Protobuf)

> ⚠️ **Critical Note:** The Protobuf section states that "renaming a field costs nothing on the wire." While true at the binary encoding level (fields are keyed by number, not name), it is misleading in practice for the target audience. Renaming a Protobuf field changes every generated client API — every service that imports the `.proto` file must recompile and update its call sites. For a shared internal contract with many consumers, a rename triggers a coordinated rollout of generated code across all consumers, which is exactly the coupling problem the chapter aims to avoid. Presenting this as "costs nothing" understates the operational impact.

**Severity:** important
**Suggested fix:** Qualify the statement: "renaming costs nothing on the *wire format*, but every consumer's generated code changes and must be recompiled and deployed." Add a note that this makes renaming a logistical concern even when it is wire-safe, particularly for widely shared contracts.

---

### Upcasting and Versioning of Persisted Events

> ⚠️ **Critical Note:** The upcaster chain pattern is presented entirely in the happy path. There is no discussion of what happens when an upcaster throws an exception or produces an output that fails downstream validation. In an event-sourced system, a defective upcaster does not just fail one message — it renders the entire aggregate history unreadable, blocking all command processing for that aggregate until the bug is fixed and redeployed. This is one of the most operationally dangerous failure modes in event-sourced systems and is completely absent from the prose.

**Severity:** important
**Suggested fix:** Add a paragraph on upcaster fault tolerance: upcasters must be tested against a corpus of real historical events before deployment; a failing upcaster should surface a clear error with the stored event payload and version, not silently corrupt state; consider wrapping the pipeline in a fallback that surfaces the raw event for triage rather than crashing the read side entirely.

---

### Upcasting and Versioning of Persisted Events

> ⚠️ **Critical Note:** The prose claims "upcasting is cheaper day to day" without acknowledging its read-time cost during replay operations. Projections, read-model rebuilds, and audit queries all replay the full event stream. A chain of N upcasters applies transformation logic to every single stored event on every replay. In systems with millions of events and chains of four or five versions, replay time can increase significantly compared to a clean-schema stream — the opposite of "cheaper." This trade-off matters for the audience making architectural decisions about whether to upcast indefinitely or periodically do stream-rewrite migrations.

**Severity:** minor
**Suggested fix:** Add a sentence acknowledging the replay cost: "Upcasting adds per-event CPU overhead during replay; for systems with very long event histories or frequent full-stream projections, a periodic stream rewrite that materializes the current schema eliminates this tax."

---

### Contracts, Consumer-Driven Contracts, and Governance

> ⚠️ **Critical Note:** The consumer-driven contracts (CDC) section presents the pattern as a reliable safety net with little acknowledgment of its primary organizational failure mode: CDC only works when every consumer actively maintains and publishes its contract. In practice, getting 100% participation is difficult — teams deprioritize contract updates, new consumers are onboarded without contracts, and legacy consumers are forgotten. A producer CI build that passes against the union of *published* contracts can still break an unpublished consumer. The prose implies CDC answers "does any real consumer actually break?" but the honest answer is "does any real consumer *that published a contract* break?" — a weaker guarantee than the table suggests.

**Severity:** important
**Suggested fix:** Add a caveat row to the comparison table noting the participation assumption, and add a sentence in the CDC prose: "The guarantee is bounded by participation — a consuming team that never publishes a contract gets no protection. CDC must be paired with a registry of known consumers and an onboarding checklist that makes contract publication mandatory."

---

### The Missing-Policy Pitfall

> ⚠️ **Critical Note:** The section recommends `BACKWARD` or `FULL` as sane defaults but does not explain *why* `FULL` is described as requiring "discipline." `FULL` compatibility requires every change to also be forward-compatible, which means fields can never be removed — only marked deprecated and left in the schema indefinitely. Over years, this produces significant schema bloat and makes it harder for new teams to understand which fields are still semantically active. Architects who choose `FULL` without understanding this trade-off will accumulate dead fields with no governance mechanism to retire them.

**Severity:** minor
**Suggested fix:** Add one sentence after the `FULL` recommendation: "Choosing `FULL` means fields are never structurally removable; pair it with a documented field-deprecation lifecycle (annotate, announce, retire by metric) or schema bloat accumulates silently."

---

## Summary
- Total notes: 6
- Blocking (inline callout): 1
- Important (collapsed): 3
- Minor (file only): 2

**Top 3 items requiring attention:**

1. [Backward and Forward Compatibility] Registry default compatibility mode stated as `FULL` — factually wrong; Confluent and AWS Glue both default to `BACKWARD`
2. [Upcasting and Versioning of Persisted Events] Upcaster failure mode completely absent — a defective upcaster blocks all command processing for affected aggregates
3. [Contracts, Consumer-Driven Contracts, and Governance] CDC participation assumption unstated — the "does any real consumer break?" guarantee is only as strong as contract coverage
