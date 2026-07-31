---
Full_Name: "AWS DynamoDB — Data Architecture (NoSQL)"
Cloud_Provider: "AWS"
Architecture_Domain: "Data Architecture — Amazon DynamoDB (managed NoSQL key-value & document database)"
Target_Edition: "AWS DynamoDB — current service documentation (Developer Guide, retrieved 2026-07-31)"
Architecture_Context: "General-purpose high-scale OLTP / key-value & document workloads (ASSUMPTION — no explicit context supplied at invocation; re-scope if this is SaaS multi-tenant, IoT, gaming, or financial-services)"
Official_Source_URL: "https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-07-31"
Currency_Threshold: "2027-07-31 — DynamoDB is an unversioned managed service; re-verify quotas, capacity modes, and global-table consistency options after this date"
---

# Executive Summary

Amazon DynamoDB is AWS's fully managed, serverless NoSQL database delivering single-digit-millisecond
performance at any scale. Because DynamoDB is a **continuously-released managed service** (not a
semantically-versioned product), version absolutism here is applied to the **service documentation state
as of 2026-07-31**: every quota, capacity mode, and consistency option below is pinned to the current
Developer Guide. Treat blog posts, Stack Overflow answers, or docs that reference the deprecated
"Global Tables 2017.11.29 (Version 2017)" model, LSI-only designs, or a 5-GSI-per-table limit as
**stale misinformation** — the current defaults are 20 GSIs per table and on-demand as the default mode.

Architecturally, DynamoDB is **not** a relational database and must not be modeled as one. Correctness
depends almost entirely on **access-pattern-first data modeling**: the partition key drives physical
data distribution, and every partition is hard-capped at **3,000 read units/s and 1,000 write units/s**
regardless of table-level throughput. The three most critical guardrails for a general-purpose
high-scale workload are: (1) design partition keys for uniform load (avoid hot partitions / use write
sharding); (2) keep items small (≤ 400 KB hard limit; offload blobs to S3); and (3) enable
point-in-time recovery, encryption controls, and least-privilege IAM (`dynamodb:LeadingKeys`) from
day one rather than retrofitting.

What is current in this edition: **on-demand capacity mode is the default and recommended option**
for most workloads; **encryption at rest is always on** (AWS-owned key by default, upgradeable to
AWS-managed or customer-managed KMS keys); **Multi-Region Strong Consistency (MRSC) global tables**
now exist alongside the older Multi-Region Eventual Consistency (MREC) model; and **warm throughput**
plus **burst/adaptive capacity** shape real-world scaling behavior.

---

# Cloud Architecture Glossary

```
Term: Partition key (hash attribute)
Definition: The primary-key attribute whose value is fed to an internal hash function that determines
  the physical partition storing the item. Must be scalar (String, Number, or Binary).
Provider Docs Section: HowItWorks.CoreComponents — Primary key
Architect Usage: Choose a key with high cardinality and uniform request distribution; it is the single
  most important data-modeling decision and cannot be changed after table creation.
Common Confusion: Confused with a relational "primary key column"; unlike SQL, it dictates physical
  placement and throughput distribution, not just uniqueness.
```
```
Term: Sort key (range attribute)
Definition: The second attribute of a composite primary key. Items sharing a partition key are stored
  together, sorted by sort-key value, enabling range queries.
Provider Docs Section: HowItWorks.CoreComponents — Primary key
Architect Usage: Encode hierarchy/time (e.g., "ORDER#2026-07-31#...") to support Query begins_with /
  between operators; enables the single-table-design overloaded-key pattern.
Common Confusion: Not an index by itself; and it is NOT the GSI partition key.
```
```
Term: Read Capacity Unit (RCU) / Write Capacity Unit (WCU)
Definition: 1 RCU = one strongly consistent read/s (or two eventually consistent reads/s) for an item
  up to 4 KB. 1 WCU = one write/s for an item up to 1 KB. On-demand tables express the same as
  Read/Write Request Units (RRU/WRU).
Provider Docs Section: bp-partition-key-design; HowItWorks.ReadWriteCapacityMode
Architect Usage: Cost and throttling math both derive from these units. Item size rounds UP to the
  next 4 KB (reads) / 1 KB (writes) block.
Common Confusion: Eventually vs strongly consistent halves read cost; transactional reads/writes cost 2x.
```
```
Term: Global Secondary Index (GSI)
Definition: An index with a partition (and optional sort) key different from the base table; spans all
  base-table partitions. Has its own provisioned/on-demand throughput and projected attributes.
Provider Docs Section: HowItWorks.CoreComponents — Secondary indexes
Architect Usage: Add access patterns after the fact; default quota is 20 GSIs per table. GSI writes
  consume separate capacity and are eventually consistent only.
Common Confusion: GSIs are eventually consistent (cannot do strongly consistent reads); LSIs can be
  strongly consistent but must be defined at table creation.
```
```
Term: Local Secondary Index (LSI)
Definition: An index sharing the base table's partition key but with a different sort key. Max 5 per
  table; MUST be created with the table. Shares the table's throughput.
Provider Docs Section: HowItWorks.CoreComponents — Secondary indexes; ServiceQuotas
Architect Usage: Use only when strongly consistent reads on an alternate sort key are required; imposes
  a 10 GB per-partition-key item-collection size limit.
Common Confusion: Cannot be added or removed after table creation, unlike GSIs.
```
```
Term: On-demand capacity mode
Definition: Serverless pay-per-request throughput mode; no capacity planning; scales automatically to
  the table-level ceiling (default 40,000 RRU + 40,000 WRU, adjustable).
Provider Docs Section: HowItWorks.ReadWriteCapacityMode — On-demand mode
Architect Usage: Default & recommended for most workloads, spiky/unpredictable traffic, and new tables.
Common Confusion: Not "unlimited" — still bound by per-partition (3,000/1,000) and table-level ceilings.
```
```
Term: Provisioned capacity mode
Definition: Mode where you specify RCU/WCU per second and pay hourly for provisioned capacity,
  optionally with auto scaling. Eligible for reserved capacity discounts.
Provider Docs Section: HowItWorks.ReadWriteCapacityMode — Provisioned mode
Architect Usage: Choose for steady, predictable traffic where cost predictability and reserved-capacity
  savings matter.
Common Confusion: Auto scaling reacts to CloudWatch alarms (minutes), not instantaneously — spikes
  faster than the policy can react will throttle.
```
```
Term: Adaptive capacity / Burst capacity
Definition: DynamoDB automatically shifts throughput toward hot partitions (adaptive) and lets a
  partition draw on unused capacity from the prior ~300 seconds (burst). Applies to on-demand and
  provisioned.
Provider Docs Section: burst-adaptive-capacity
Architect Usage: Mitigates transient imbalance but does NOT remove the hard 3,000/1,000 per-partition
  ceiling; design for uniformity anyway.
Common Confusion: Believing adaptive capacity makes hot-partition design safe — it does not for
  sustained skew.
```
```
Term: DynamoDB Streams
Definition: Optional ordered, near-real-time change-data-capture feed of item-level modifications;
  records persist 24 hours.
Provider Docs Section: HowItWorks.CoreComponents — DynamoDB Streams
Architect Usage: Trigger Lambda for event-driven architectures, cross-region replication, materialized
  views. Up to 2 simultaneous readers per shard (1 for global tables).
Common Confusion: Kinesis Data Streams for DynamoDB is a separate, longer-retention alternative.
```
```
Term: Global tables (MRSC vs MREC)
Definition: Multi-Region, multi-active replication. MREC = Multi-Region Eventual Consistency (classic);
  MRSC = Multi-Region Strong Consistency (newer). Default quota: 400 total MRSC global tables.
Provider Docs Section: V2globaltables_HowItWorks — Consistency modes; ServiceQuotas — Global tables
Architect Usage: Choose MRSC only when cross-region strong consistency is a hard requirement; MREC for
  latency-optimized active-active with last-writer-wins conflict resolution.
Common Confusion: The deprecated 2017.11.29 version-management model is NOT the current global-tables model.
```
```
Term: Point-in-Time Recovery (PITR)
Definition: Continuous backups enabling restore to any second within a rolling retention window
  (up to 35 days).
Provider Docs Section: security-best-practices; bp-pitr-recovery
Architect Usage: Enable on all production tables; protects against accidental writes/deletes and
  corruption. Independent of on-demand (snapshot) backups.
Common Confusion: PITR is not the same as AWS Backup or on-demand snapshots; it is a distinct feature.
```
```
Term: DynamoDB Accelerator (DAX)
Definition: A fully managed, in-memory, write-through cache for DynamoDB delivering microsecond read
  latency, API-compatible with DynamoDB.
Provider Docs Section: dax-prescriptive-guidance
Architect Usage: Add for read-heavy, eventually-consistent hot-read workloads; not for
  strongly-consistent-read or write-heavy patterns.
Common Confusion: DAX caches item and query/scan results but does not accelerate writes or strongly
  consistent reads.
```

---

# Framework Pillars — DynamoDB Well-Architected Lens

DynamoDB publishes a dedicated **DynamoDB Well-Architected Lens** that maps the AWS Well-Architected
Framework pillars onto DynamoDB design decisions.

```
Pillar: Operational Excellence
Definition (AWS): Run and monitor systems to deliver business value and continually improve.
Key Design Principles (DynamoDB): Use CloudWatch metrics (ThrottledRequests, ConsumedCapacity,
  SystemErrors, UserErrors), Contributor Insights for hot-key detection, and infrastructure-as-code
  for table/GSI definitions.
Applies To context: Alarm on throttling and system errors; automate capacity-mode selection review.
Assessment Questions: Are you monitoring throttling and hot keys? Is table config in IaC? Do you test
  restores?
Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-wal.html (retrieved 2026-07-31)
```
```
Pillar: Security
Definition (AWS): Protect data, systems, and assets.
Key Design Principles (DynamoDB): Encryption at rest always on (KMS options); enforce TLS via
  aws:SecureTransport; least-privilege IAM with dynamodb:LeadingKeys / dynamodb:Attributes; VPC
  endpoints; CloudTrail on control-plane and (optionally) data-plane events.
Assessment Questions: Are you using customer-managed keys where audit control is required? Is IAM
  fine-grained per identity? Is traffic private (VPC endpoint)?
Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security-best-practices.html (retrieved 2026-07-31)
```
```
Pillar: Reliability
Definition (AWS): Ensure a workload performs its intended function correctly and consistently.
Key Design Principles (DynamoDB): DynamoDB replicates across 3 AZs by default; enable PITR; use global
  tables for multi-Region; implement exponential-backoff retries; design for idempotency with
  conditional writes.
Assessment Questions: Is PITR on? Is your DR/RTO/RPO defined? Do clients retry with backoff and jitter?
Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html (retrieved 2026-07-31)
```
```
Pillar: Performance Efficiency
Definition (AWS): Use computing resources efficiently to meet requirements.
Key Design Principles (DynamoDB): Access-pattern-first (single-table) design; uniform partition keys;
  Query over Scan; sparse/overloaded GSIs; DAX for hot reads; keep items small.
Assessment Questions: Are partition keys uniform? Are you avoiding Scan on hot paths? Is item size
  within limits?
Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html (retrieved 2026-07-31)
```
```
Pillar: Cost Optimization
Definition (AWS): Avoid unnecessary costs.
Key Design Principles (DynamoDB): Match capacity mode to traffic shape; reserved capacity for steady
  provisioned workloads; sparse indexes and KEYS_ONLY/INCLUDE projections to cut storage & write cost;
  TTL to auto-expire stale items; eventually consistent reads where acceptable.
Assessment Questions: Is capacity mode right for the traffic shape? Are GSIs over-projected? Is TTL used
  for ephemeral data?
Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-wal.html (retrieved 2026-07-31)
```
```
Pillar: Sustainability
Definition (AWS): Minimize environmental impact of running workloads.
Key Design Principles (DynamoDB): Right-size projected attributes and item sizes; use TTL to remove
  dead data; prefer on-demand to eliminate over-provisioning waste.
Assessment Questions: Are you storing/replicating only needed attributes? Is dead data expired?
Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-wal.html (retrieved 2026-07-31)
```

---

# Architecture Guardrails

## ✅ Mandatory Patterns

**M1 — Access-pattern-first (single-table) data modeling**
- Pillar Alignment: Performance Efficiency, Cost Optimization
- Why: DynamoDB has no joins and no server-side query planner; every access pattern must be satisfied by
  a primary-key or index lookup. Modeling relationally (normalized tables + Scans) is the #1 cause of
  cost and latency failure.
- AWS Services: DynamoDB tables, GSIs, composite/overloaded sort keys.
- Architecture Decision: Enumerate all read/write access patterns first; design partition/sort keys and
  GSIs to serve them with `Query` (never `Scan`) on hot paths. Use overloaded keys (e.g., `PK`, `SK`)
  and sparse GSIs for the single-table pattern.
- Verification: Review each access pattern → confirm it maps to a `GetItem`/`Query`, not a `Scan`.
  `aws dynamodb describe-table --table-name <t>` to confirm key schema and GSIs.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html (retrieved 2026-07-31)

**M2 — Uniform partition-key design (respect the 3,000/1,000 per-partition ceiling)**
- Pillar Alignment: Performance Efficiency, Reliability
- Why: "Every partition in a DynamoDB table is designed to deliver a maximum capacity of 3,000 read
  units per second and 1,000 write units per second" — a skewed key throttles regardless of
  table-level throughput.
- AWS Services: DynamoDB partition keys, write sharding, adaptive/burst capacity.
- Architecture Decision: Choose high-cardinality keys; for unavoidable high-write keys, apply write
  sharding (append a calculated suffix `0..N` to the partition key and scatter-gather on read).
- Verification: Enable Contributor Insights → inspect "most accessed keys"; watch CloudWatch
  `ThrottledRequests` and `OnDemandMaxReadRequestUnits`/write equivalents.
- Trade-offs: Write sharding adds read-side fan-out complexity.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html (retrieved 2026-07-31)

**M3 — Keep items small; offload large payloads to Amazon S3**
- Pillar Alignment: Performance Efficiency, Cost Optimization
- Why: Max item size is **400 KB** (hard limit). Large items inflate RCU/WCU consumption (rounding to
  4 KB/1 KB blocks) and slow queries.
- AWS Services: DynamoDB + Amazon S3 (store blob in S3, keep S3 object key + metadata in DynamoDB).
- Architecture Decision: Store attributes > a few KB (documents, images, large JSON) in S3; persist the
  pointer + queryable metadata in the item. Use compression for borderline attributes.
- Verification: Alarm on item sizes; enforce via application-layer validation before `PutItem`.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-use-s3-too.html (retrieved 2026-07-31)

**M4 — Encryption at rest with the right KMS key tier + TLS in transit**
- Pillar Alignment: Security
- Why: Encryption at rest is always enabled. AWS-owned key is default (no audit trail);
  AWS-managed (`aws/dynamodb`) and customer-managed keys add control and CloudTrail visibility.
- AWS Services: DynamoDB + AWS KMS.
- Architecture Decision: Use a **customer-managed KMS key** for regulated/sensitive data (key policy +
  rotation + audit). Enforce TLS 1.2+ by denying `aws:SecureTransport=false` in IAM policy.
- Verification: `aws dynamodb describe-table` → `SSEDescription`; IAM policy simulator for the
  SecureTransport Deny.
- Trade-offs: Customer-managed keys add per-request KMS cost and a KMS availability dependency.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security-best-practices.html (retrieved 2026-07-31)

**M5 — Least-privilege IAM with fine-grained condition keys**
- Pillar Alignment: Security
- Why: Wildcard `dynamodb:*` on `*` is a critical anti-pattern; DynamoDB supports item-/attribute-level
  restriction via condition keys.
- AWS Services: IAM, DynamoDB.
- Architecture Decision: Scope actions to specific table ARNs; use `dynamodb:LeadingKeys` to restrict an
  identity to its own partition-key rows (multi-tenant isolation) and `dynamodb:Attributes` to limit
  columns.
- Verification: IAM Access Analyzer; policy review for `LeadingKeys`/`Attributes` on tenant-scoped roles.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security-best-practices.html (retrieved 2026-07-31)

**M6 — Point-in-Time Recovery + backup strategy on all production tables**
- Pillar Alignment: Reliability
- Why: PITR provides continuous backups with restore to any second in a rolling window (up to 35 days),
  protecting against accidental deletes/corruption.
- AWS Services: DynamoDB PITR, on-demand backups, AWS Backup.
- Architecture Decision: Enable PITR on every production table; define RTO/RPO; use on-demand snapshots
  or AWS Backup for long-term/compliance retention.
- Verification: `aws dynamodb update-continuous-backups --table-name <t>
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true`; confirm via
  `describe-continuous-backups`.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-pitr-recovery.html (retrieved 2026-07-31)

**M7 — Private connectivity via VPC endpoints**
- Pillar Alignment: Security
- Why: Keeps DynamoDB traffic off the public internet.
- AWS Services: VPC Gateway Endpoint for DynamoDB (and PrivateLink interface endpoints where required).
- Architecture Decision: Attach a Gateway Endpoint to the VPC route tables; apply an endpoint policy
  restricting access to specific table ARNs.
- Verification: Confirm route-table association; test that traffic resolves to the endpoint, not a
  public IP.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/privatelink-interface-endpoints.html (retrieved 2026-07-31)

**M8 — Exponential-backoff retries + idempotent conditional writes**
- Pillar Alignment: Reliability
- Why: Throttling (`ProvisionedThroughputExceededException`) and transient errors are expected at scale;
  clients must retry with backoff + jitter. Conditional writes prevent lost updates.
- AWS Services: AWS SDK (built-in retry), DynamoDB `ConditionExpression`, optimistic locking via a
  version attribute.
- Architecture Decision: Rely on SDK default retry/backoff; use `attribute_not_exists()` or a version
  check for idempotency; use `TransactWriteItems` for cross-item atomicity (costs 2x capacity).
- Verification: Load test and observe `ThrottledRequests`; unit-test conditional-write rejection paths.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BestPractices_ImplementingVersionControl.html (retrieved 2026-07-31)

## ⚠️ Architectural Decisions (Ask First)

**D1 — Capacity mode: On-demand vs Provisioned (+ auto scaling / reserved)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | On-demand | DynamoDB on-demand mode | Zero capacity planning, instant spike absorption | Higher per-request price at steady high volume | Spiky/unpredictable, new tables, low-ops teams (DEFAULT) |
  | Provisioned + auto scaling | DynamoDB provisioned + Application Auto Scaling | Cost predictability, lower unit cost at steady load | Slow reaction to spikes (CloudWatch-driven), tuning effort | Steady, forecastable traffic |
  | Provisioned + reserved capacity | + 1- or 3-yr reserved capacity | Deepest discount | Commitment lock-in | Baseline-heavy, long-lived steady workloads |

- Cost Profile: On-demand ≈ pay-per-request (higher unit price, zero idle waste); provisioned ≈ hourly
  reserved throughput (cheaper per unit, pays for idle); reserved ≈ lowest unit cost with commitment.
- Scaling Characteristics: On-demand scales automatically to the table ceiling (default 40,000 RRU +
  40,000 WRU, adjustable). Provisioned auto scaling reacts in minutes, not instantly.
- Lock-in Assessment: Neutral — mode is switchable (subject to switch-frequency limits); not a
  portability concern.
- Ask The Architect: "Is traffic predictable and steady enough to forecast, or spiky/new? And do you
  have a 1–3 yr baseline that justifies reserved capacity?"
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadWriteCapacityMode.html (retrieved 2026-07-31)

**D2 — Consistency & multi-Region: single-Region vs MREC vs MRSC global tables**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Single-Region | DynamoDB (3-AZ) | Cost, simplicity | No cross-Region DR/latency | Most workloads |
  | MREC global tables | Global tables (Multi-Region Eventual Consistency) | Low local latency, active-active | Eventual consistency, last-writer-wins conflicts | Global low-latency, tolerant of eventual consistency |
  | MRSC global tables | Global tables (Multi-Region Strong Consistency) | Cross-Region strong consistency | Higher cost/latency; quota 400 MRSC tables | Hard cross-Region strong-consistency requirement |

- Cost Profile: Multi-Region multiplies write cost (replicated writes) and storage per replica Region.
- Lock-in Assessment: Global tables are DynamoDB-specific; a multi-cloud DR requirement changes the
  calculus (see equivalence map).
- Ask The Architect: "Do you need cross-Region strong consistency (MRSC), latency-optimized
  active-active (MREC), or is single-Region multi-AZ sufficient? What are RTO/RPO?"
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html (retrieved 2026-07-31)

**D3 — Read consistency & caching: eventually consistent vs strongly consistent vs DAX**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Eventually consistent read | DynamoDB (default) | Half the RCU cost, higher throughput | May read stale (sub-second) data | Read-heavy, staleness-tolerant |
  | Strongly consistent read | DynamoDB (ConsistentRead=true) | Read-after-write guarantee | 2x cost; not available on GSIs; single-AZ read | Correctness-critical reads |
  | DAX | DynamoDB Accelerator | Microsecond reads, offloads hot reads | Eventual only; extra cost; no write/strong-read benefit | Read-heavy hot-key eventual reads |

- Cost Profile: Strong reads cost 2x eventual; DAX adds node cost but can cut RCU spend dramatically on
  cache hits.
- Lock-in Assessment: DAX is DynamoDB-specific (API-compatible SDK).
- Ask The Architect: "Which reads truly require read-after-write consistency, and which are hot enough
  to justify a DAX cache?"
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/dax-prescriptive-guidance.html (retrieved 2026-07-31)

**D4 — Index choice: LSI vs GSI (and projection type)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | LSI | Local Secondary Index | Strong consistency on alt sort key | Must define at create; 5 max; 10 GB item-collection cap | Strongly consistent alternate-sort-key reads |
  | GSI | Global Secondary Index | Add anytime; alt partition key; 20 max | Eventual consistency only; separate throughput | New access patterns discovered later |
  | Projection ALL vs INCLUDE vs KEYS_ONLY | GSI/LSI projection | Query completeness vs storage/write cost | ALL duplicates all attributes (cost) | Project only what the query returns |

- Cost Profile: Over-projected GSIs multiply write cost and storage; `KEYS_ONLY`/`INCLUDE` minimize both
  (≤ 100 projected attributes combined across all indexes for INCLUDE).
- Lock-in Assessment: Index concepts are DynamoDB-specific.
- Ask The Architect: "Does this access pattern need strong consistency (→ LSI at create time) or may it
  emerge later (→ GSI)? What attributes must the query return?"
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-indexes.html (retrieved 2026-07-31)

**D5 — Change propagation: DynamoDB Streams vs Kinesis Data Streams**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | DynamoDB Streams + Lambda | DynamoDB Streams | Native, ordered, exactly-per-shard triggers | 24h retention; 2 readers/shard (1 for global tables) | Event-driven triggers, replication, materialized views |
  | Kinesis Data Streams for DynamoDB | Kinesis Data Streams | Longer retention, many consumers, fan-out | More infra to manage | Analytics/fan-out beyond 24h or many consumers |

- Cost Profile: Streams billed per read request unit; Kinesis adds shard/stream cost.
- Ask The Architect: "Do downstream consumers need > 24h retention or high fan-out (→ Kinesis), or is a
  Lambda trigger enough (→ Streams)?"
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html (retrieved 2026-07-31)

## 🚫 Anti-Patterns

**A1 — Using Scan on hot read paths**
- Risk Level: HIGH
- Why (pillar): Performance Efficiency — Scan reads every item and consumes capacity proportional to
  table size, causing throttling and cost blow-ups.
- Blast Radius: Table-wide throttling; latency for all users of the table.
- ❌ Wrong: `aws dynamodb scan --table-name Orders --filter-expression "customerId = :c"` on a
  multi-GB table to fetch one customer's orders.
- ✅ Correct: Model `customerId` as (or into a GSI) partition key and use
  `Query` — `KeyConditionExpression: "customerId = :c"` returning only that customer's items.
- Detection: CloudWatch `ConsumedReadCapacityUnits` spikes; Contributor Insights; code review for `Scan`.
- Impact: Cost overrun, cascading throttling.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-query-scan.html (retrieved 2026-07-31)

**A2 — Low-cardinality / hot partition key**
- Risk Level: CRITICAL
- Why (pillar): Performance Efficiency, Reliability — every partition is capped at 3,000 RCU/s and
  1,000 WCU/s; concentrating traffic on one key throttles it no matter the table throughput.
- Blast Radius: All requests to the hot key throttle; adaptive capacity cannot save sustained skew.
- ❌ Wrong: Partition key = `status` with values `ACTIVE`/`INACTIVE` (2 keys) for a high-write table.
- ✅ Correct: Partition key = high-cardinality `orderId`, or apply write sharding
  (`status#<0..N>` suffix) and scatter-gather on read.
- Detection: Contributor Insights "most accessed keys"; CloudWatch `ThrottledRequests` with ample
  provisioned/on-demand headroom.
- Impact: Service outage on the hot key, cascading failure.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html (retrieved 2026-07-31)

**A3 — Storing large blobs directly as item attributes**
- Risk Level: HIGH
- Why (pillar): Performance Efficiency, Cost — the 400 KB item hard limit; large items inflate every
  read/write's capacity consumption.
- Blast Radius: Failed writes at the 400 KB boundary; runaway RCU/WCU cost.
- ❌ Wrong: `PutItem` with a 2 MB base64 PDF in a `document` attribute (rejected — exceeds 400 KB).
- ✅ Correct: Upload the PDF to Amazon S3; store the S3 object key + metadata in the DynamoDB item.
- Detection: Application validation of serialized item size before write; CloudWatch item-size metrics.
- Impact: Write failures, cost overrun.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-use-s3-too.html (retrieved 2026-07-31)

**A4 — Wildcard IAM permissions on DynamoDB**
- Risk Level: CRITICAL
- Why (pillar): Security — `dynamodb:*` on `Resource: *` grants full data-plane + control-plane access,
  violating least privilege.
- Blast Radius: Full read/write/delete/drop of every table in the account/Region.
- ❌ Wrong: `{ "Action": "dynamodb:*", "Resource": "*" }` attached to an application role.
- ✅ Correct: Scope to specific table ARNs and actions
  (`dynamodb:GetItem`,`Query`) with `Condition: dynamodb:LeadingKeys = ${aws:PrincipalTag/tenant}`
  for tenant isolation.
- Detection: IAM Access Analyzer; policy audit for wildcards on DynamoDB.
- Impact: Data breach, compliance violation.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security-best-practices.html (retrieved 2026-07-31)

**A5 — No PITR / no backup on production tables**
- Risk Level: HIGH
- Why (pillar): Reliability — a bad deploy or fat-finger delete is unrecoverable without continuous
  backups.
- Blast Radius: Permanent data loss.
- ❌ Wrong: Production table created with `PointInTimeRecoveryEnabled=false` and no snapshots.
- ✅ Correct: Enable PITR (up to 35-day window) + scheduled AWS Backup for long-term retention; define
  and test restore RTO/RPO.
- Detection: `aws dynamodb describe-continuous-backups`; AWS Config rule
  `dynamodb-pitr-enabled`.
- Impact: Irrecoverable data loss, compliance violation.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-pitr-recovery.html (retrieved 2026-07-31)

**A6 — Relational modeling: many normalized tables + client-side joins**
- Risk Level: HIGH
- Why (pillar): Performance Efficiency, Cost — DynamoDB has no joins; emulating them with N round-trips
  or Scans multiplies latency and cost.
- Blast Radius: Latency and cost scale with data volume; degrades under load.
- ❌ Wrong: Separate `Customers`, `Orders`, `Items` tables joined in application code with multiple
  `Scan`/`Query` round-trips per request.
- ✅ Correct: Single-table design — one table, overloaded `PK`/`SK`, item collections co-locating a
  customer and its orders, retrieved in one `Query`.
- Detection: Architecture review; count of round-trips per user request; presence of client-side joins.
- Impact: Cost overrun, latency SLA breach.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html (retrieved 2026-07-31)

**A7 — Unrestricted / public data-plane access without VPC endpoint or TLS enforcement**
- Risk Level: HIGH
- Why (pillar): Security — traffic traversing the public internet without a private endpoint, or
  policies that don't enforce TLS.
- Blast Radius: Interceptable traffic; broader attack surface.
- ❌ Wrong: Application in a VPC reaching DynamoDB over the public internet with no
  `aws:SecureTransport` condition.
- ✅ Correct: VPC Gateway Endpoint for DynamoDB + IAM `Deny` when `aws:SecureTransport = false`.
- Detection: VPC route-table review; IAM policy audit for the SecureTransport Deny.
- Impact: Data exposure, compliance violation.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security-best-practices.html (retrieved 2026-07-31)

---

# Cloud-Native Design Patterns

**Single-Table Design (overloaded keys)**
- Category: Data
- Problem: Serving multiple entity types and access patterns with minimal round-trips and no joins.
- Solution on AWS: One table with generic `PK`/`SK`; entities distinguished by key prefixes
  (`CUSTOMER#123`, `ORDER#456`); GSIs invert access (e.g., `GSI1PK`/`GSI1SK`) for secondary patterns.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Latency | One Query fetches an item collection | Steeper modeling learning curve |
  | Cost | Fewer requests, fewer tables | Harder to evolve access patterns |

- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html (retrieved 2026-07-31)

**Write Sharding for high-throughput keys**
- Category: Scalability
- Problem: A partition key hotter than 1,000 WCU/s throttles.
- Solution on AWS: Append a calculated suffix (`key#0`..`key#N`) to spread writes across partitions;
  scatter-gather across shards on read.
- Trade-offs: Even write distribution vs read-side fan-out complexity.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-sharding.html (retrieved 2026-07-31)

**Time-Series data with per-period tables + TTL**
- Category: Data / Cost
- Problem: Append-heavy time-series where recent data is hot and old data is cold.
- Solution on AWS: Roll tables per period (or partition by time bucket), keep the current table on higher
  throughput, and use TTL to auto-expire aged items.
- Trade-offs: Lower cost & hot/cold separation vs table-management overhead.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-time-series.html (retrieved 2026-07-31)

**Event-driven CDC via Streams + Lambda**
- Category: Communication / Resilience
- Problem: React to data changes (replication, materialized views, notifications) without polling.
- Solution on AWS: DynamoDB Streams → Lambda trigger; fan out to SNS/SQS/EventBridge or build read
  models. For > 24h retention/high fan-out, use Kinesis Data Streams for DynamoDB.
- Trade-offs: Near-real-time decoupling vs 24h stream retention and 2-readers-per-shard limit.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html (retrieved 2026-07-31)

**Optimistic concurrency (version control) with conditional writes**
- Category: Data / Resilience
- Problem: Concurrent updates risk lost writes.
- Solution on AWS: Maintain a `version` attribute; write with
  `ConditionExpression: version = :expected`; retry on `ConditionalCheckFailedException`. Use
  `TransactWriteItems` for multi-item atomicity.
- Trade-offs: Correctness under concurrency vs retry handling and 2x capacity for transactions.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BestPractices_ImplementingVersionControl.html (retrieved 2026-07-31)

---

# Operational Patterns

**Observability**
- Operational Domain: Observability
- AWS Services: CloudWatch (ThrottledRequests, ConsumedRead/WriteCapacityUnits, SystemErrors,
  UserErrors, SuccessfulRequestLatency), Contributor Insights (hot keys), CloudTrail (API audit).
- Cost Profile: Low–Medium (Contributor Insights and enhanced metrics add cost).
- Automation: Alarm on throttling and system errors; auto-page on sustained throttling.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-wal.html (retrieved 2026-07-31)

**Disaster Recovery**
- Operational Domain: DR
- RTO/RPO: PITR restore (RPO ≈ seconds within window; RTO = restore duration). Global tables
  (near-zero RPO, seconds RTO for regional failover).
- AWS Services: PITR, on-demand backups, AWS Backup, global tables (MREC/MRSC).
- Cost Profile: PITR (low) → global tables (high — replicated writes + per-Region storage).
- Automation: Automate PITR enablement (AWS Config remediation) and periodic restore tests.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-pitr-recovery.html (retrieved 2026-07-31)

### DR Pattern Cost-Benefit Matrix (DynamoDB-specific)

| DR Pattern | RTO | RPO | Relative Cost | Best For |
|------------|-----|-----|---------------|----------|
| PITR restore (single-Region) | Restore duration | Seconds (within 35-day window) | $ | Accidental delete/corruption recovery |
| On-demand backup / AWS Backup | Restore duration | Point of snapshot | $ | Long-term/compliance retention |
| MREC global tables | Seconds (failover) | Near-zero (eventual) | $$$ | Active-active global, staleness-tolerant |
| MRSC global tables | Seconds | Near-zero (strong) | $$$$ | Cross-Region strong-consistency requirement |

---

# Reference Architectures

**Serverless event-driven API on DynamoDB**
- AWS Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html (retrieved 2026-07-31)
- Context: High-scale OLTP API (single-table design).
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Edge/API | API Gateway | Request routing, throttling, auth |
  | Compute | AWS Lambda | Business logic, DynamoDB access via SDK |
  | Data | DynamoDB (single table, on-demand) | Primary store |
  | Read cache | DAX | Microsecond hot reads (optional) |
  | CDC | DynamoDB Streams → Lambda | Materialized views, notifications |
  | Blobs | Amazon S3 | Large-object offload (400 KB item limit) |
  | Security | KMS + IAM (LeadingKeys) + VPC endpoint | Encryption, least privilege, private access |

- Key Decisions: Capacity mode (D1), consistency/caching (D3), index strategy (D4).
- Scaling Path: On-demand → provisioned+reserved as traffic stabilizes; add global tables for
  multi-Region; add DAX for read hot spots.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html (retrieved 2026-07-31)

---

# Service Equivalence Map

> ⚠️ Service equivalence does NOT mean feature parity. DynamoDB's partition model, single-digit-ms SLA,
> and global-tables semantics differ materially from each peer. Validate against each provider's current
> docs before a portability decision.

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| **NoSQL key-value / document** | DynamoDB | Firestore (document) / Bigtable (wide-column) | Cosmos DB (Table / NoSQL API) | NoSQL Database |
| **In-memory cache** | DAX / ElastiCache | Memorystore | Azure Cache for Redis | OCI Cache |
| **Change data capture** | DynamoDB Streams / Kinesis | Firestore triggers / Pub/Sub | Cosmos DB change feed | OCI Streaming / Events |
| **Multi-Region replication** | Global tables (MREC/MRSC) | Firestore multi-region / Spanner | Cosmos DB multi-region | NoSQL Database multi-region |
| **Serverless RDBMS alt.** | Aurora Serverless v2 | AlloyDB / Spanner | Azure SQL / Cosmos DB | Autonomous Database |
| **Object store for blob offload** | S3 | Cloud Storage | Blob Storage | Object Storage |
| **KMS** | AWS KMS | Cloud KMS | Key Vault | OCI Vault / Key Management |
| **Secrets** | Secrets Manager | Secret Manager | Key Vault | OCI Vault |
| **Monitoring** | CloudWatch | Cloud Monitoring | Azure Monitor | OCI Monitoring |

Closest single-service analogue to DynamoDB by API/model: **Azure Cosmos DB (Table/NoSQL API)** and
**Google Cloud Firestore** for document/key-value; **Google Cloud Bigtable** for wide-column high-scale.

---

# Provider Differentiators (DynamoDB-relevant)

```
Differentiator: DynamoDB global tables (MRSC)
Category: Data
Unique Value: Managed multi-active, multi-Region replication with an option for Multi-Region Strong
  Consistency — a capability few competitors offer natively at this scale.
Architecture Impact: Enables active-active global writes; MRSC removes the eventual-consistency caveat
  when strong cross-Region reads are mandatory.
When to Leverage: Global low-latency apps; regulated cross-Region strong-consistency needs.
Caveat: Higher cost; MRSC default quota 400 tables; write cost multiplied per Region.
Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html (retrieved 2026-07-31)
```
```
Differentiator: DynamoDB Accelerator (DAX)
Category: Data / Performance
Unique Value: API-compatible, write-through in-memory cache delivering microsecond reads without app
  rewrites.
Architecture Impact: Offloads hot reads, cutting RCU spend and latency for eventually-consistent reads.
When to Leverage: Read-heavy hot-key workloads.
Caveat: Eventual consistency only; no benefit for writes or strongly-consistent reads.
Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/dax-prescriptive-guidance.html (retrieved 2026-07-31)
```
```
Differentiator: On-demand serverless capacity + adaptive/burst capacity
Category: Data / Cost
Unique Value: Zero-capacity-planning scaling to millions of req/s with automatic hot-partition
  mitigation.
Architecture Impact: Removes provisioning as a design concern for spiky workloads.
When to Leverage: Unpredictable/new workloads; low-ops teams.
Caveat: Still bound by 3,000 RCU/s + 1,000 WCU/s per-partition and table-level ceilings.
Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/burst-adaptive-capacity.html (retrieved 2026-07-31)
```

---

# Key Quotas & Limits (pinned, retrieved 2026-07-31)

| Limit | Value | Source |
|-------|-------|--------|
| Max item size | 400 KB (1 KB = 1024 bytes) | ServiceQuotas — Items |
| Primary-key attribute types | String, Number, Binary only | HowItWorks.CoreComponents |
| Partition key value length | 1–2048 bytes | ServiceQuotas — Items |
| Sort key value length | up to 1024 bytes | ServiceQuotas — Items |
| Nested attribute depth | up to 32 levels | HowItWorks.CoreComponents |
| Per-partition throughput ceiling | 3,000 RCU/s and 1,000 WCU/s | bp-partition-key-design |
| 1 RCU | 1 strong read/s (or 2 eventual) up to 4 KB | bp-partition-key-design |
| 1 WCU | 1 write/s up to 1 KB | bp-partition-key-design |
| GSIs per table (default quota) | 20 | ServiceQuotas — Secondary indexes |
| LSIs per table | 5 (defined at create time) | ServiceQuotas — Secondary indexes |
| Projected attributes (INCLUDE, across all indexes) | 100 combined | ServiceQuotas — Projected attributes |
| Per-table throughput (default, adjustable) | 40,000 RCU + 40,000 WCU (or RRU/WRU) | ServiceQuotas — Read/write throughput |
| Per-account provisioned throughput (default) | 80,000 RCU + 80,000 WCU | ServiceQuotas — Read/write throughput |
| Tables per Region (default → max) | 2,500 → 10,000 | ServiceQuotas — Tables |
| Provisioned throughput decreases per day | 4 baseline, up to 27 | ServiceQuotas — Read/write throughput |
| Stream record retention | 24 hours | HowItWorks.CoreComponents — Streams |
| Stream readers per shard | 2 (single-Region) / 1 (global tables) | ServiceQuotas — DynamoDB Streams |
| MRSC global tables (default quota) | 400 total | ServiceQuotas — Global tables |
| PITR retention window | up to 35 days | security-best-practices; bp-pitr-recovery |

> ⚠️ Quotas marked "default" are adjustable via Service Quotas. All values retrieved 2026-07-31; re-verify
> after 2027-07-31.

---

# Scenario Coverage

**Standard Case**: High-scale OLTP API (single-table design, on-demand mode).
- Approach: Single table + overloaded keys (M1), uniform partition key (M2), S3 blob offload (M3),
  encryption + least-privilege IAM (M4/M5), PITR (M6), VPC endpoint (M7), SDK backoff + conditional
  writes (M8). Add DAX (D3) and Streams-driven read models as needed.
- Key Decisions: Capacity mode (D1), consistency/caching (D3), index strategy (D4).

**Edge Case**: Cross-Region strong consistency at global scale.
- Approach: MRSC global tables (D2) within the 400-table quota; align table-level write throughput
  limits across all replica Regions before adding replicas; budget for multiplied write cost and higher
  latency.

**Anti-Pattern Case**: Team wants to "lift-and-shift" a normalized relational schema into DynamoDB with
Scans and client-side joins.
- Clarification: Refuse/flag — ask for the full list of access patterns first, then redesign to
  single-table/GSI (A1, A6). If the workload is inherently relational/ad-hoc-query heavy, ask whether
  Aurora/RDS is the correct service instead of DynamoDB.

---

# Source Bibliography

### Primary Sources (official AWS DynamoDB Developer Guide — all retrieved 2026-07-31)
- Best practices (index) — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html
- NoSQL design for DynamoDB — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html
- DynamoDB Well-Architected Lens — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-wal.html
- Partition key design — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html
- Write sharding — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-sharding.html
- Sort keys — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-sort-keys.html
- Secondary indexes — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-indexes.html
- Large items / use S3 too — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-use-s3-too.html
- Time-series data — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-time-series.html
- Querying and scanning — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-query-scan.html
- Concurrent updates / version control — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BestPractices_ImplementingVersionControl.html
- PITR recovery best practices — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-pitr-recovery.html
- Core components — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html
- Read/write capacity mode — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadWriteCapacityMode.html
- Burst & adaptive capacity — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/burst-adaptive-capacity.html
- Warm throughput — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/warm-throughput.html
- Service quotas — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html
- Security best practices — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security-best-practices.html
- Global tables (how it works / consistency modes) — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html
- DynamoDB Streams — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html
- DAX prescriptive guidance — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/dax-prescriptive-guidance.html
- PrivateLink / VPC endpoints — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/privatelink-interface-endpoints.html

### Confidence / Currency Notes
- All quota figures verified against the live ServiceQuotas page on 2026-07-31.
- Item-size (400 KB), partition-key length (1–2048 bytes), and sort-key length (1024 bytes) values are
  long-standing documented limits on the ServiceQuotas "Items" section; treat as HIGH confidence but
  re-confirm on next review.
- DynamoDB is unversioned; this document pins to the 2026-07-31 documentation state. Re-run research
  after 2027-07-31 or upon any AWS announcement changing capacity modes, global-table consistency, or
  index quotas.

---

# Agent Operation Notes (for downstream skill authoring)

- **High confidence (autonomous)**: All ✅ Mandatory Patterns, quota table, glossary — directly sourced.
- **Medium confidence (verify)**: Relative cost profiles in ⚠️ decisions are qualitative (order-of-
  magnitude), not billed pricing — confirm against the AWS Pricing Calculator for a specific workload.
- **Low confidence (ask user)**: Compliance-specific controls (HIPAA/PCI/SOC2/GDPR), reserved-capacity
  commitments, and exact RTO/RPO targets are organization-specific — surface before prescribing.
- **Unverified / flagged**: `ARCHITECTURE_CONTEXT` was not supplied; this document assumes general-purpose
  high-scale OLTP. If the target is multi-tenant SaaS, IoT, gaming, or financial services, re-scope the
  tenancy-isolation (LeadingKeys), time-series, and DR sections accordingly.
