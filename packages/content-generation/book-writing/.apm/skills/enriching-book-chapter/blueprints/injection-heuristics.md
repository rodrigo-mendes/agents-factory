# Injection-Point Heuristics — chapter-enricher Blueprint

Reference for the `chapter-enricher` agent. Defines when and where to insert `[CODE:]` and `[DIAGRAM:]` markers into external prose that lacks them.

---

## Marker Syntax

```
[CODE: brief description of what code/algorithm/pseudocode should illustrate]
[DIAGRAM: brief description of what the diagram should show and what type (flowchart/sequence/class/ER)]
[DIAGRAM: flowchart | decision tree for choosing between {option A} and {option B} based on {criteria}]
```

Each marker must appear on its own line. Each description must be ≥5 words and specific enough for a downstream agent to resolve without re-reading the prose.

---

## `[CODE:]` Injection Triggers

Insert a `[CODE:]` marker when the prose:

| Signal | Example prose fragment | Suggested marker |
|--------|------------------------|-----------------|
| Introduces a concrete algorithm or computational step | "the idempotent consumer checks the message ID before processing" | `[CODE: idempotent consumer handler checking message ID before processing]` |
| Names a data structure, schema, or DDL definition | "the event store table has three columns: id, payload, and created_at" | `[CODE: SQL DDL for a minimal event store table with id, payload, created_at]` |
| Describes an API contract or method signature | "the function takes a userId and returns a list of orders" | `[CODE: function signature taking userId and returning list of orders]` |
| Contrasts a correct pattern with an anti-pattern | "the right approach is to emit a single canonical event; the anti-pattern is to emit two overlapping events" | `[CODE: two contrasting event schema definitions — canonical vs overlapping]` |
| Contains a "Your Turn" / exercise / hands-on section | any section heading containing "Try", "Exercise", "Practice", "Hands-on" | `[CODE: working example for the {concept} exercise]` |
| References a named library, framework, or API with specific usage | "using AWS Lambda Powertools, the handler is annotated with @Tracer" | `[CODE: Lambda function using AWS Lambda Powertools @Tracer annotation]` |
| Describes configuration as key-value pairs or environment variables | "set MAX_RETRIES to 3 and BACKOFF_MS to 500" | `[CODE: configuration snippet setting MAX_RETRIES and BACKOFF_MS]` |

**Density rule:** In any section ≥400 words that introduces a non-introductory technical concept, insert at least one `[CODE:]` marker unless the section is purely conceptual/philosophical.

---

## `[DIAGRAM:]` Injection Triggers

Insert a `[DIAGRAM:]` marker when the prose:

| Signal | Pattern | Diagram type |
|--------|---------|--------------|
| Multi-actor flow with named components | "Service A sends a message to the broker; the consumer group reads from the partition" | `[DIAGRAM: sequence diagram showing Service A → broker → consumer group flow]` |
| Side-by-side architecture comparison | "on one side… on the other side", "approach A vs approach B", "in the monolith… in the microservice" | `[DIAGRAM: comparison flowchart contrasting {A} and {B} architectures]` |
| Decision criteria / when-to-use branching | "use X when… use Y when…", "choose A if condition…", "prefer B over A unless…" | `[DIAGRAM: flowchart \| decision tree for choosing between {X} and {Y} based on {criteria}]` |
| State machine or lifecycle transitions | "moves from PENDING → PROCESSING → COMPLETE or FAILED" | `[DIAGRAM: state diagram showing {entity} lifecycle transitions]` |
| Architectural topology with named nodes | "the producer writes to topic T; partitions are replicated to N brokers; consumers belong to a group" | `[DIAGRAM: flowchart showing producer → topic → partitions → consumer group topology]` |
| Compatibility matrix or trade-off table (prose form) | "option A has high throughput but low durability; option B has medium throughput and high durability" | `[DIAGRAM: comparison flowchart showing throughput vs durability trade-offs for options A and B]` |

**Decision-diagram prefix rule:** When the diagram explains a decision ("when to use X vs Y", "how to choose"), **always** prefix the description with `flowchart |`. This signals `diagram-illustrator` to generate a `flowchart TD` with diamond decision nodes.

---

## Section-Title Heuristics

Sections with these titles almost always need at least one marker:

| Title pattern | Expected marker type |
|---------------|---------------------|
| "How It Works" | `[DIAGRAM:]` (flow or sequence) + `[CODE:]` (implementation) |
| "When to Use" / "When Not to Use" | `[DIAGRAM: flowchart \|` (decision tree) |
| "Decision Criteria" | `[DIAGRAM: flowchart \|` (decision tree) |
| "Comparison" / "X vs Y" | `[DIAGRAM:]` (comparison flowchart) |
| "The Problem" / "The Challenge" | `[DIAGRAM:]` (problem topology) |
| "The Pattern" / "The Solution" | `[DIAGRAM:]` (solution flow) + `[CODE:]` (pattern implementation) |
| "Implementation" / "Building" | `[CODE:]` (required) |
| "Example" / "Case Study" | `[CODE:]` (required) |
| "Architecture" / "Design" | `[DIAGRAM:]` (required) |
| "Key Takeaways" | No markers (summary section) |
| "What's Next" | No markers (transition section) |
| "Opening Problem Statement" | `[DIAGRAM:]` only if a topology is described |

---

## Placement Rules

These rules are identical to `chapter-writer`'s constraints and must never be violated:

1. **No back-to-back markers** — at least one full sentence of prose must appear before and after every marker
2. **One marker per injection point** — do not double-mark the same concept with both `[CODE:]` and `[DIAGRAM:]` in immediate succession; separate them by ≥1 sentence
3. **No markers inside fenced code blocks** — if the external chapter already contains ``` fences, do not insert markers inside them; treat those blocks as already-resolved
4. **No markers inside blockquotes** — do not insert inside `>` blockquote lines
5. **Marker descriptions must be specific** — "code example" alone is not acceptable; describe the specific concept, algorithm, or scenario being illustrated

---

## What chapter-enricher Must NOT Do

- 🚫 Never rewrite, rephrase, or summarize any prose — insert markers only; all original text must be preserved verbatim
- 🚫 Never generate actual code blocks or Mermaid diagrams — markers only
- 🚫 Never remove existing text, headings, or formatting
- 🚫 Never insert markers in the "Key Takeaways" or "What's Next" sections (summary/transition sections only)
