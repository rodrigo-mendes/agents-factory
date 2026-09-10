## Expert Review — Event Sourcing — State as a Sequence of Events
Reviewer profile: Senior practitioner, 10+ years, cloud-native microservices and corporate distributed systems
Date: 2026-09-01

---

### The Truth-and-History Problem

> **Expert Note:** The prose correctly dismisses audit tables as "always slightly wrong," but the failure modes go deeper than most teams expect. Audit triggers miss intermediate states inside multi-statement transactions — if a stored procedure updates three rows and fires one trigger per row, the trigger log records individual row changes but not the single business intent that caused them. More insidiously, when the schema changes (a column is renamed or dropped), the trigger definition silently breaks or starts logging null for that field, and no error is raised. Teams discover this only during an audit, months later, when the log has a systematic gap nobody noticed. Event Sourcing avoids this entirely because the intent — the business event — is what gets written, not the row mutation.

**Integration level:** collapsed block
**Priority:** medium

---

### The Event Store and the Append-Only Log

> **Expert Note:** The `global_position` column in the schema placeholder is easy to misimplent on PostgreSQL with a `BIGSERIAL` or `SEQUENCE`, creating a silent production hazard. PostgreSQL sequences are non-transactional by design: if a transaction inserts an event and then rolls back, the sequence value is consumed and not reused. Consumers reading `global_position` in order will see gaps (e.g., positions 1, 2, 4 — position 3 was a rolled-back insert) and must decide whether a gap means "not yet committed" or "permanently missing." The standard production fix is to use a replication-slot-based change-data-capture approach (e.g., `pg_logical`) or to track the global order through a separate, lock-protected counter table flushed only on commit. EventStoreDB sidesteps this by handling position assignment inside its own transaction log. Choose your infrastructure knowing this gap problem exists on plain SQL stores.

**Integration level:** inline callout
**Priority:** high

> **Expert Note:** When comparing EventStoreDB against a homegrown PostgreSQL store, the practical corporate differentiator is subscription semantics, not storage. EventStoreDB's persistent subscriptions support a competing-consumer model per group natively, but their projection engine (historically JavaScript-based server-side projections) introduces an operational burden — a second runtime to monitor, version, and debug — that most enterprise teams underestimate. For organizations already standardising on Kafka, treating the event store as the authoritative append-only log and Kafka as the subscription/fan-out layer is a common hybrid that preserves familiarity. The two layers have different guarantees (exactly-once append vs. at-least-once delivery) and must be wired accordingly.

**Integration level:** collapsed block
**Priority:** medium

---

### State Reconstruction and Aggregates

> **Expert Note:** The prose describes command methods as methods that "produce a new event," but the standard implementation pattern adds a structural detail that changes how the aggregate interacts with its repository: the aggregate holds an internal list of "uncommitted events." When a command method decides to accept a business action, it calls its own `apply()` internally — to update in-memory state immediately — and appends the event to this uncommitted list. The repository, after calling the command, reads the uncommitted list, appends those events to the store at the expected version, then clears the list. This two-phase design (apply-now, flush-later) is why command methods can chain decisions within a single unit of work and why the aggregate never knows about the database. Omitting this pattern leads teams to either re-load the aggregate between commands in the same request or to call `apply()` twice (once in the command, once during reconstruction), causing double-mutation bugs.

**Integration level:** collapsed block
**Priority:** medium

> **Expert Note:** A common design drift that defeats the purpose of event sourcing is the event-carried state transfer anti-pattern: events that carry the full serialized state of the entity rather than only the delta that changed. Teams slide into this because it feels simpler — "just serialize the aggregate and store it." The result is events that are indistinguishable from snapshots, bloated storage, and no ability to answer "what specific thing changed between version 4 and version 5." Apply methods become no-ops that just overwrite the whole object. The discriminating question is: can you describe what happened in a single past-tense sentence without listing every field? `MoneyWithdrawn { amount: 200 }` passes. `AccountStateUpdated { id: ..., balance: ..., openedAt: ..., owner: ... }` fails.

**Integration level:** file only
**Priority:** low

---

### Snapshots and Replay Optimization

> **Expert Note:** A bug in any `apply()` method that goes undetected for weeks will silently corrupt every snapshot generated during that period. When the bug is fixed, the corrected apply logic produces different in-memory state than the stored snapshot reflects, and reconstruction that starts from a stale snapshot will produce wrong results without raising an error — the corrupted snapshot is structurally valid JSON. The production fix is to attach a `snapshot_schema_version` (an integer you increment whenever apply logic changes semantics) to every snapshot row. On load, if `snapshot_schema_version` does not match the current code version, discard the snapshot and fall back to full replay. This adds one config constant and one comparison but makes snapshot invalidation automatic and safe during deploys.

**Integration level:** inline callout
**Priority:** high

> **Expert Note:** The prose frames snapshotting as a tuning knob on read, but it matters equally on the write path. A naive implementation takes a snapshot synchronously inside the same transaction that appends the event — doubling write latency on every Nth event. Production systems almost universally make snapshotting asynchronous: a background worker (or a projection that reads the event stream) detects that a stream has advanced past a threshold and writes the snapshot out-of-band. The command path stays fast and predictable; the snapshot may lag by a few seconds, which is acceptable because reconstruction always falls back to replay if a snapshot is absent or stale.

**Integration level:** collapsed block
**Priority:** medium

---

### Long-Term Costs and Design Constraints

> **Expert Note:** Crypto-shredding as described is correct but understates a critical implementation constraint: the scope of what must be encrypted is wider than most teams anticipate. Personal data cannot appear anywhere outside the encrypted payload — not in the event type name, not in metadata fields (correlation IDs, user-agent strings, IP addresses logged as metadata), and not in stream IDs that encode a username or email. A stream ID of `user-john.doe@example.com` cannot be shredded; the identifier itself is personal data and will persist in every event header, every snapshot row, and every projection row forever. The architectural discipline is to use opaque, surrogate identifiers (UUIDs) as stream IDs from day one and to store a separate subject-keyed encryption key per data subject in a dedicated key management service (AWS KMS, HashiCorp Vault) before writing the first event. Retrofitting this onto an existing event store is effectively impossible without rewriting history, which the pattern prohibits.

**Integration level:** inline callout
**Priority:** high

---

## Summary
- Total notes: 8
- High priority (inline callout): 3
- Medium priority (collapsed): 4
- Low priority (file only): 1

**Top 3 notes to integrate:**

1. [The Event Store and the Append-Only Log] PostgreSQL `global_position` sequence-gap hazard breaks projection consumers and requires explicit mitigation
2. [Long-Term Costs and Design Constraints] Crypto-shredding scope: personal data in stream IDs, event type names, and metadata cannot be shredded — surrogate IDs and upfront key management are mandatory
3. [Snapshots and Replay Optimization] Snapshot schema versioning prevents silent corruption when apply logic changes between deploys
