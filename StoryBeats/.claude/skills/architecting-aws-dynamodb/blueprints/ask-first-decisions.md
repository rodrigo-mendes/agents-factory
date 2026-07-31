# Ask First Decisions — Amazon DynamoDB

> Source: AWS DynamoDB Developer Guide, retrieved 2026-07-31.
> Back to [SKILL.md](../SKILL.md)

These are architectural crossroads where the correct answer depends on workload context the agent
cannot infer. Surface the trade-off matrix and ask the architect before proceeding.

---

## D1 — Capacity Mode: On-Demand vs Provisioned (+ Auto Scaling / Reserved)

**Decision**: Which throughput mode should the table use?

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **On-demand** (default) | Zero capacity planning; instant spike absorption | Higher per-request unit price at steady high volume | Spiky or unpredictable traffic; new tables; low-ops teams |
| **Provisioned + auto scaling** | Cost predictability; lower unit cost at steady load | Auto scaling reacts in minutes (CloudWatch-driven), not instantly — spikes faster than the policy can react will throttle | Steady, forecastable traffic where cost predictability matters |
| **Provisioned + reserved capacity** | Deepest per-unit discount (1- or 3-yr commitment) | Lock-in; pays for idle; requires accurate long-term forecast | Stable baseline with multi-year workload certainty |

**Cost Profile**:
- On-demand: pay per RRU/WRU; no idle cost; higher unit price (~5–7x provisioned per unit at steady load).
- Provisioned: hourly charge for reserved RCU/WCU; lower unit price; idle capacity is wasted cost.
- Reserved: same as provisioned but with committed 1- or 3-year discounts (~30–60% off provisioned).

**Scaling Characteristics**:
- On-demand scales automatically to the table-level ceiling (default 40,000 RRU + 40,000 WRU, adjustable via Service Quotas).
- Provisioned auto scaling reacts to CloudWatch alarms — delay is typically 2–5 minutes; sudden spikes will throttle during the reaction window.

**Lock-in Assessment**: Neutral — capacity mode is switchable (subject to switch-frequency limits: once per 24 hours for on-demand→provisioned). Not a portability concern.

**Ask The Architect**:
> "Is traffic predictable and steady enough to forecast, or is it spiky/new?
> Do you have a 1–3 year baseline that justifies reserved capacity?"

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadWriteCapacityMode.html (2026-07-31)

---

## D2 — Replication Scope: Single-Region vs MREC vs MRSC Global Tables

**Decision**: Does the workload require multi-Region replication?

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Single-Region** (3-AZ default) | Cost; simplicity | No cross-Region DR or latency optimization | Most workloads; RTO/RPO met by PITR + AZ resilience |
| **MREC global tables** (Multi-Region Eventual Consistency) | Low local read/write latency globally; active-active | Eventual consistency; last-writer-wins conflict resolution; multiplied write cost | Global low-latency apps; tolerate eventual consistency |
| **MRSC global tables** (Multi-Region Strong Consistency) | Cross-Region strong consistency (read-after-write guaranteed globally) | Higher cost + latency than MREC; default quota: 400 MRSC tables | Hard cross-Region strong-consistency requirement; regulated data |

**Cost Profile**:
- Multi-Region multiplies write cost: each replica Region consumes full write throughput.
- MRSC adds further cross-Region coordination overhead (higher write latency + cost vs MREC).
- Storage is replicated per Region (multiplied storage cost).

**Conflict Resolution** (MREC): last-writer-wins based on wall-clock timestamp. Application must tolerate overwritten concurrent writes.

**MRSC Quota**: Default 400 MRSC global tables per account. Request increase via Service Quotas before designing at scale.

**Lock-in Assessment**: Global tables are DynamoDB-specific; a multi-cloud DR requirement changes the calculus materially.

**Ask The Architect**:
> "Do you need cross-Region strong consistency (MRSC), latency-optimized active-active reads and
> writes (MREC), or is single-Region multi-AZ sufficient? What are the RTO/RPO targets?
> Is multi-cloud DR a requirement?"

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html (2026-07-31)

---

## D3 — Read Consistency and Caching: Eventually Consistent vs Strongly Consistent vs DAX

**Decision**: Which read model does the application's correctness require?

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Eventually consistent read** (default) | Half the RCU cost; higher throughput | May return stale data (sub-second lag after a write) | Read-heavy; staleness tolerable (product catalog, leaderboard, session cache) |
| **Strongly consistent read** | Read-after-write guarantee | 2x RCU cost; not available on GSIs; single-AZ read path | Correctness-critical reads (financial balances, inventory counts) |
| **DAX (DynamoDB Accelerator)** | Microsecond read latency; offloads hot reads from DynamoDB | Eventual consistency only; extra cluster cost; no benefit for writes or strongly-consistent reads; DynamoDB-specific | Read-heavy hot-key workloads (top-N lists, high-traffic product pages) |

**Cost Impact**:
- Strongly consistent reads: 2x RCU vs eventually consistent — at scale this doubles read cost.
- DAX: adds EC2-backed cluster cost but can cut DynamoDB RCU spend dramatically on cache-hit paths.
  Break-even depends on hit rate and RCU price vs cluster price.

**GSI Constraint**: Strongly consistent reads are **not supported** on Global Secondary Indexes —
all GSI reads are eventually consistent regardless of `ConsistentRead` flag.

**Ask The Architect**:
> "Which specific reads require read-after-write consistency (justify 2x cost)?
> Which reads are so hot (high RCU, repeated identical queries) that a DAX cache is justified?
> Can your application tolerate sub-second staleness on non-critical reads?"

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/dax-prescriptive-guidance.html (2026-07-31)

---

## D4 — Index Choice: LSI vs GSI (and Projection Type)

**Decision**: What index type and projection should support a new access pattern?

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **LSI** (Local Secondary Index) | Strongly consistent reads on alternate sort key; shares table throughput | Must define at table creation (cannot add later); max 5 per table; 10 GB item-collection cap per partition key | Alternate sort-key access patterns known at design time that require strong consistency |
| **GSI** (Global Secondary Index) | Add anytime; alternate partition key; max 20 per table; independent throughput | Eventual consistency only; separate throughput capacity (own RCU/WCU) | New access patterns discovered after table creation; alternate partition key access |
| **Projection: KEYS_ONLY** | Minimum storage and write cost | Query returns only key attributes; application must `GetItem` for full data | Index used only for existence checks or to retrieve keys for subsequent lookups |
| **Projection: INCLUDE** | Balance: selected attributes without full duplication | Only specified attributes available; ≤ 100 projected attributes combined across all INCLUDE indexes | Query returns a predictable, bounded attribute set |
| **Projection: ALL** | Query returns all base-table attributes without secondary `GetItem` | Doubles storage and write cost (every write propagates all attributes to index) | Query requires arbitrary attribute access; item size is small |

**Cost Profile**:
- Over-projected GSIs (`ALL` on large items) multiply write cost: every base-table write triggers a
  GSI write proportional to item size.
- `KEYS_ONLY`/`INCLUDE` minimize both storage and write cost at the expense of query completeness.

**LSI Constraint**: Item collections (same partition key) are capped at **10 GB** with an LSI.
Exceeding this limit causes `ItemCollectionSizeLimitExceededException` on writes.

**Ask The Architect**:
> "Does this access pattern require strongly consistent reads (→ LSI, must define now)?
> Can it be added later if traffic proves the need (→ GSI)?
> What exact attributes must the query return — can we project only those?"

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-indexes.html (2026-07-31)

---

## D5 — Change Propagation: DynamoDB Streams vs Kinesis Data Streams for DynamoDB

**Decision**: How should downstream consumers react to item-level changes?

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **DynamoDB Streams + Lambda** | Native; ordered per shard; no extra infra; auto Lambda trigger | 24h record retention; max 2 simultaneous readers per shard (1 for global tables) | Event-driven Lambda triggers, cross-Region replication, materialized views, notifications |
| **Kinesis Data Streams for DynamoDB** | Longer retention (default 24h, up to 365h); unlimited consumers via Enhanced Fan-Out; analytics pipelines | Additional Kinesis stream cost (shard-hours); more infrastructure to manage | High fan-out (> 2 consumers); analytics pipelines needing > 24h replay; Kinesis ecosystem integration |

**Cost Profile**:
- DynamoDB Streams: billed per stream read request unit (low cost for Lambda-triggered processing).
- Kinesis Data Streams: billed per shard-hour plus PUT payload units; Enhanced Fan-Out adds per-consumer-shard-hour cost.
- Break-even: if you need > 2 concurrent stream readers, Kinesis is cheaper than workarounds (fan-out Lambda, intermediary queues).

**Reader Limit Warning**: With DynamoDB Streams and global tables, only **1 stream reader per shard**
is supported (global-tables replication uses one of the 2 slots). Factor this before attaching
additional Lambda triggers to a global table.

**Ask The Architect**:
> "Do downstream consumers need > 24h event retention or replay?
> How many independent consumers need to read the stream simultaneously (> 2 → Kinesis)?
> Is this a global table (stream reader slot already consumed by replication)?"

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html (2026-07-31)
