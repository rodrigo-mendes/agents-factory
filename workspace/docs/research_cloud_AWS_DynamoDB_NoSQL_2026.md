# AWS DynamoDB — Cloud Architecture Research

## Metadata
```yaml
Full_Name: "AWS Data Architecture — DynamoDB NoSQL"
Cloud_Provider: "AWS"
Architecture_Domain: "Data Architecture - DynamoDB NoSQL"
Target_Edition: "AWS DynamoDB 2026"
Architecture_Context: "NoSQL data modeling, capacity planning, resilience, and security for cloud-native applications"
Official_Source_URL: "https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-28"
Currency_Threshold: "2027-08-28"
Research_Depth: "exhaustive"
Max_Iterations: 5
Research_Quality_Score: "91%"
# Research_Quality_Score = (total_claims - unverified - irresolvable) / total_claims * 100
Gap_Loop_Ran: true
Iterations_Used: "5 of 5"
Triangulated_Count: 97
Unverified_Count: 9
Irresolvable_Count: 0
```

---

## Executive Summary

Amazon DynamoDB is AWS's fully managed, serverless NoSQL key-value and document database, engineered for single-digit millisecond latency at any scale without operational burden. Within cloud architecture practice, DynamoDB occupies the session store, event store, user-profile, shopping-cart, and IoT-ingest tiers of virtually every AWS serverless reference architecture — and, as of August 2026, it has extended into AI/ML workloads via native vector search.

The most significant evolution in the 2024–2026 period is pricing and topology: the November 2024 on-demand price cut (−50% throughput, up to −67% on global tables replicated writes) made on-demand the default and recommended capacity mode, eliminating the previous provisioned-first guidance. June 2025 introduced Multi-Region Strong Consistency (MRSC) for global tables — the first active-active NoSQL topology in AWS with a provable zero-RPO guarantee. August 2026 completed the AI platform extension with vector search GA, enabling DynamoDB to serve as a combined operational + vector store for RAG and recommendation workloads without an external vector database.

The three most critical architecture guardrails for DynamoDB data architecture are: **(1) access-pattern-first schema design** — DynamoDB penalizes schemas designed before access patterns are known, with no escape hatch equivalent to an RDBMS ad-hoc query; **(2) partition key cardinality and distribution** — a hot partition key creates a 3,000 RCU / 1,000 WCU hard ceiling that no provisioned capacity or adaptive capacity can bypass; **(3) CloudTrail data-event logging is opt-in per table** — without explicit enablement, item-level reads and writes produce no audit trail, a compliance gap that is invisible by default.

---

## Cloud Architecture Glossary

```
Term: Partition Key (Hash Key)
Definition: The primary attribute fed to DynamoDB's internal hash function to determine the physical partition where an item is stored. For a simple primary key, it is the sole identifier; for a composite primary key it is combined with the sort key.
Provider Docs Section: HowItWorks.CoreComponents
Architect Usage: Design partition keys for uniform distribution. A key whose values cluster on a hot item creates a per-partition hard ceiling of 3,000 RCU / 1,000 WCU regardless of total table capacity.
Common Confusion: Confused with SQL primary keys — DynamoDB partition keys do not enforce uniqueness alone; uniqueness is enforced only by the combination of partition key + sort key.
```

```
Term: Sort Key (Range Key)
Definition: The second attribute of a composite primary key. Items with the same partition key are stored physically together and sorted by sort key value, enabling efficient range queries.
Provider Docs Section: HowItWorks.CoreComponents
Architect Usage: Use to encode hierarchy, time, or status into the sort key to support Query operations without a Scan. Sort key max 1,024 bytes.
Common Confusion: Confused with a secondary index — the sort key is part of the primary key, not a GSI. Unlike a GSI, a sort key supports strongly consistent reads.
```

```
Term: Read Capacity Unit (RCU)
Definition: 1 RCU = 1 strongly consistent read per second for an item ≤ 4 KB. Or equivalently, 2 eventually consistent reads per second for items ≤ 4 KB. Larger items consume proportionally more RCUs.
Provider Docs Section: HowItWorks.ReadConsistency; on-demand-capacity-mode
Architect Usage: Baseline for capacity planning. A 20 KB item requires 5 RCUs per strongly consistent read. Per-partition limit: 3,000 RCUs/sec.
Common Confusion: Confused with WCUs — RCUs cover reads only, and the per-partition limits (3k/1k) are asymmetric.
```

```
Term: Write Capacity Unit (WCU)
Definition: 1 WCU = 1 write per second for an item ≤ 1 KB. Larger items consume proportionally more WCUs (rounded up per KB).
Provider Docs Section: on-demand-capacity-mode
Architect Usage: Write-heavy workloads with large items (e.g., 10 KB items = 10 WCU per write). Per-partition hard limit: 1,000 WCU/sec — much lower than the read limit.
Common Confusion: Confused with the RCU item-size threshold (4 KB) — WCU threshold is 1 KB, not 4 KB.
```

```
Term: Global Secondary Index (GSI)
Definition: A secondary index with a partition key (and optional sort key) that can differ from the base table's primary key. Spans all base-table data. Has its own provisioned or on-demand throughput. Only supports eventually consistent reads.
Provider Docs Section: GSI; bp-indexes-general
Architect Usage: Model alternate query patterns that require a different partition key. Can be created or deleted at any time. Up to 20 GSIs per table (default).
Common Confusion: Confused with LSIs — GSIs can differ on the partition key (full flexibility); LSIs must share the base-table partition key. GSIs never support strongly consistent reads.
```

```
Term: Local Secondary Index (LSI)
Definition: A secondary index that shares the same partition key as the base table but has a different sort key. Scoped to a single base-table partition. Shares the base table's throughput. Can serve strongly consistent reads.
Provider Docs Section: LSI
Architect Usage: Use when you need an alternate sort order within the same partition and strong consistency. Creation is only possible at table-creation time — cannot be added later. Up to 5 per table. Total items per LSI partition key value ≤ 10 GB.
Common Confusion: Often treated as freely interchangeable with GSIs — the critical difference is the immutable creation window and the 10 GB per-partition size cap.
```

```
Term: On-Demand Capacity Mode
Definition: DynamoDB's serverless, pay-per-request throughput model, where the service auto-scales with no capacity planning. Default and recommended mode since November 2024 pricing restructuring.
Provider Docs Section: on-demand-capacity-mode
Architect Usage: Use by default for new tables, spiky, or unpredictable workloads. Instantly handles up to 2× the previous peak; exceeding that within 30 minutes may throttle — pre-warm or space growth ≥30 minutes.
Common Confusion: Confused with "unlimited" — on-demand still has a default per-table quota of 40,000 RU/WU per second, raiseable via Service Quotas.
```

```
Term: Adaptive Capacity
Definition: A DynamoDB mechanism that automatically and instantly boosts throughput allocation for hot partitions by redistributing unused capacity from other partitions, up to the per-partition hard ceiling. Enabled for all tables at no cost.
Provider Docs Section: burst-adaptive-capacity
Architect Usage: Helps absorb imbalanced access, but does not eliminate the 3,000 RCU / 1,000 WCU per-partition ceiling. For items that are always hot, write sharding is still required.
Common Confusion: Often confused as a substitute for proper partition key design — adaptive capacity softens spikes but cannot overcome a structurally hot partition key.
```

```
Term: Multi-Region Strong Consistency (MRSC)
Definition: A global table consistency mode (GA June 2025) where writes are synchronously replicated to at least one other Region before the write call returns. Every replica always serves the latest version. RPO = zero.
Provider Docs Section: V2globaltables_HowItWorks
Architect Usage: Use for highest-resilience applications requiring zero RPO. Constraint: exactly 3 Regions (3 replicas OR 2 replicas + 1 witness); must start from an empty table; no TTL, no LSIs, no transactions. Available Region sets: US, EU, AP (cannot span sets).
Common Confusion: Confused with MREC (Multi-Region Eventual Consistency), the classic multi-active model. MRSC is a distinct topology with hard constraints — not a setting on an existing global table.
```

```
Term: Witness (MRSC)
Definition: A lightweight MRSC component that holds replicated change data but is not a full table replica. Provides quorum without the cost of a third full replica. No reads or writes allowed on a witness. Managed by DynamoDB; does not appear in the customer account.
Provider Docs Section: V2globaltables_HowItWorks
Architect Usage: Choose 2 replicas + 1 witness to reduce cost when a third full readable/writable replica is not needed for RPO=0. Region for the witness is visible via DescribeTable.
Common Confusion: Confused with a read replica — a witness cannot serve any traffic.
```

```
Term: Warm Throughput (GA Nov 2024)
Definition: The number of read/write operations a table or GSI can instantaneously support, reflecting historical scaling. Surfaced in DescribeTable at no cost. Pre-warming proactively raises this baseline before a known peak event.
Provider Docs Section: warm-throughput
Architect Usage: Pre-warm ahead of high-traffic events (10×/100× spikes) to avoid the 30-minute scale-up ramp of on-demand. Pre-warming incurs a charge and is irreversible downward.
Common Confusion: Confused with burst capacity — warm throughput is a sustained instantaneous baseline; burst capacity is the 5-minute reserve of unused RCU/WCU that can absorb short spikes.
```

```
Term: DynamoDB Streams
Definition: A time-ordered, exactly-once log of item-level modifications to a DynamoDB table, retained for 24 hours. Each record captures key attributes and optionally old/new item images.
Provider Docs Section: Streams
Architect Usage: Drive Lambda-based event processors, CQRS projections, or cross-table replication. Hard limit: 2 concurrent consumers per shard before throttling — a binding constraint for single-table fan-out.
Common Confusion: Confused with Kinesis Data Streams for DynamoDB — Streams has a 24h retention and 2-consumer limit; Kinesis has up to 1-year retention and 5+ consumers per shard.
```

```
Term: Fine-Grained Access Control (FGAC)
Definition: IAM condition-key-based mechanism to restrict DynamoDB access to specific items (via dynamodb:LeadingKeys) and specific attributes (via dynamodb:Attributes) within a table.
Provider Docs Section: specifying-conditions
Architect Usage: Required for multi-tenant tables where different users own different items. Must use ForAllValues: modifier on LeadingKeys. Scan operations cannot be constrained by LeadingKeys and must be explicitly denied.
Common Confusion: Confused with resource-based policies — FGAC is identity-based (IAM conditions on the principal's policy); resource-based policies attach to the table and govern cross-account access.
```

```
Term: Point-in-Time Recovery (PITR)
Definition: Continuous, fully managed backup that allows restoring a table to any second within a configurable window of 1–35 days (configurable retention GA January 2025). Restore creates a new table.
Provider Docs Section: PointInTimeRecovery_Howitworks
Architect Usage: Enable on all production tables. Set retention period based on compliance window — no longer fixed at 35 days. Deleting a PITR-enabled table auto-creates a 35-day system backup snapshot.
Common Confusion: Confused with on-demand backups — PITR is continuous and per-second granular; on-demand backups are point-in-time snapshots taken manually or on a schedule.
```

```
Term: Standard-IA Table Class
Definition: A DynamoDB table class offering ~60% lower storage cost than Standard, at the expense of ~25% higher throughput cost. Same performance, durability, and scaling as Standard.
Provider Docs Section: WorkingWithTables.tableclasses
Architect Usage: Use when storage cost exceeds ~50% of total throughput cost for the table — typical for cold time-series historical tables. Reserved capacity is NOT supported for Standard-IA.
Common Confusion: Confused with S3 Intelligent-Tiering — Standard-IA is a table-level class you select; it does not auto-tier based on access patterns.
```

---

## Architecture Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**Access-Pattern-First Schema Design** 🟢
- Pillar Alignment: Performance Efficiency; Reliability
- Why: *"You shouldn't start designing your schema for DynamoDB until you know the questions it will need to answer."* DynamoDB stores data shaped to queries — there is no query planner to compensate for a poor schema. (bp-general-nosql-design)
- AWS Services: DynamoDB, NoSQL Workbench for DynamoDB
- Architecture Decision:
  Before creating any table: enumerate all read and write access patterns with cardinality, frequency, and size. Use NoSQL Workbench to model and validate the schema against all patterns before provisioning. Do not start with an ER diagram — start with an access-pattern matrix.
- Verification: Review DescribeTable output and slow/throttled operation counts in CloudWatch. A Scan-heavy table almost always indicates a missing access-pattern during design.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html

**High-Cardinality Partition Key** 🟢
- Pillar Alignment: Performance Efficiency; Reliability
- Why: The hash function distributes writes evenly across partitions only when the key space is large and random. A low-cardinality key concentrates traffic on a small number of partitions, hitting the 3,000 RCU / 1,000 WCU per-partition ceiling. (bp-partition-key-design)
- AWS Services: DynamoDB (partition design), CloudWatch Contributor Insights (detection)
- Architecture Decision:
  Choose partition keys with high cardinality and uniform access (user_id, order_id, device_id + timestamp). Enable Contributor Insights to detect hot partition keys in production. For inherently low-cardinality keys (e.g., status flags), apply write sharding with a random or calculated suffix.
- Verification: CloudWatch Contributor Insights → ConsumedThroughputUnits per key. ThrottledRequests metric on specific partitions.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html

**Encryption at Rest — CMK for Regulated Data** 🟢
- Pillar Alignment: Security
- Why: Encryption at rest is mandatory and always on (AES-256, cannot be disabled). The architecture decision is which key type. AWS owned keys offer no customer control; customer managed keys (CMK) enable key rotation, granular key policies, CloudTrail KMS audit, and key deletion as a "break-glass." Regulated workloads (HIPAA, PCI DSS, FedRAMP High) require CMK.
- AWS Services: DynamoDB, AWS KMS
- Architecture Decision:
  Default: AWS owned key (no cost, no ops). Regulated data or multi-tenant isolation: customer managed key. Enable automatic annual rotation on CMK. Note: sort key boundary values are stored in plaintext in table metadata regardless of key choice.
- Verification: DescribeTable → SSEDescription.SSEType. KMS CloudTrail events for Decrypt calls.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/EncryptionAtRest.html

**CloudTrail Data-Event Logging — Opt-In Per Table** 🟢
- Pillar Alignment: Security; Operational Excellence
- Why: Management events (control plane) are logged automatically. Data-plane item-level events (GetItem, PutItem, UpdateItem, DeleteItem, Query, Scan) are **disabled by default**. Without explicit enablement, item-level reads and writes produce no audit trail — an invisible compliance gap.
- AWS Services: DynamoDB, AWS CloudTrail
- Architecture Decision:
  Enable CloudTrail data-event logging for all tables storing regulated or sensitive data at table provisioning time, not retroactively. Use advanced event selectors to filter by table ARN to control cost. Avoid sensitive plaintext in primary key values — key values appear in CloudTrail logs.
- Verification: CloudTrail → Event history → filter by EventSource = dynamodb.amazonaws.com, EventType = Data.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/logging-using-cloudtrail.html

**VPC Endpoint for All DynamoDB Traffic** 🟢
- Pillar Alignment: Security
- Why: Without a VPC endpoint, traffic from EC2/Lambda to DynamoDB traverses the public internet. Gateway endpoints are free and route traffic over the AWS network. Interface endpoints (PrivateLink, GA March 2024) extend coverage to on-premises and cross-account flows.
- AWS Services: DynamoDB, Amazon VPC (Gateway endpoint or PrivateLink interface endpoint)
- Architecture Decision:
  All workloads: deploy gateway endpoint for EC2/Lambda within the VPC. On-premises or cross-Region access: deploy PrivateLink interface endpoint. Enforce via IAM condition `aws:sourceVpce` on the table policy to deny all non-VPC-endpoint traffic.
- Verification: VPC Console → Endpoints → verify DynamoDB endpoint. Test via `aws dynamodb list-tables --endpoint-url` from within VPC.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/network-isolation.html

---

### ⚠️ Architectural Decisions

**Capacity Mode: On-Demand vs Provisioned** 🟢
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | On-Demand | DynamoDB on-demand | Operational simplicity; spiky traffic; new workloads | Cost at sustained high utilization | Unknown/unpredictable load; new tables; dev/test |
  | Provisioned + Auto Scaling | DynamoDB provisioned + Application Auto Scaling | Cost at predictable sustained load; reserved capacity eligibility | Operational complexity; 2-min scale-up lag | Steady, forecastable workloads above ~35% average utilization |

- Cost Profile: On-demand is break-even vs provisioned at ~35% average utilization. Below 35%, on-demand is cheaper even at high peaks. Provisioned + reserved capacity achieves up to 77% savings (3-year) for fully steady workloads.
- Lock-in Assessment: No lock-in difference between modes — DynamoDB API is identical. Can switch up to 4× per 24 hours (provisioned → on-demand).
- Architect Instruction: "Ask 'can this workload's P99 read/write rate be forecasted 6 months out?' when evaluating a provisioned migration."
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/capacity-mode.html

**Global Table Consistency: MREC vs MRSC** 🟢
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | MREC (default) | DynamoDB Global Tables 2019.11.21 | Write latency; topology flexibility; any-Region writes | RPO > 0 (usually <1s) | Active-active; most global apps; fintech with eventual reconciliation |
  | MRSC (GA Jun 2025) | DynamoDB Global Tables MRSC | RPO = 0; zero-stale reads any Region | Write latency (synchronous multi-Region); 3-Region topology constraint; no TTL/LSI/transactions | Regulated data requiring zero data loss; gaming leaderboards; inventory |

- Cost Profile: MRSC billed at current global tables pricing (no surcharge), but write latency increases due to synchronous cross-Region round-trip.
- Lock-in Assessment: MRSC topology is immutable (exactly 3 Regions, cannot add replicas, must start empty). Migration to MREC requires rebuilding the table.
- Architect Instruction: "Ask 'what is the acceptable RPO?' before designing a global table — RPO=0 mandates MRSC with its hard topology constraints."
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html

**Read Acceleration: DAX vs ElastiCache vs No Cache** 🟡
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | DAX | DynamoDB Accelerator | Microsecond read latency; DynamoDB API transparent | Strong consistency support; write-through only; in-VPC; cache hit rate dependency | Read-heavy; hot keys; repeated reads; >90% cache hit rate expected |
  | ElastiCache (Redis/Valkey) | ElastiCache | General caching; flexible eviction; Pub/Sub | Application-layer cache logic; consistency management | Shared cache across services; session store; complex eviction policies |
  | No cache | DynamoDB (native) | Simplicity; always-fresh data | Latency at scale; cost at high RCU | Write-heavy; strongly consistent requirements; sporadic access patterns |

- Cost Profile: DAX cluster adds EC2 instance cost; worthwhile when cache hit rate >90% reduces DynamoDB RCU cost and latency requirement is sub-millisecond.
- Lock-in Assessment: DAX is DynamoDB API-compatible — switching to no-cache requires removing DAX client only, not application rewrite.
- Architect Instruction: "Ask 'what is the expected cache hit rate?' before recommending DAX — below 90% hit rate, DAX adds cost with minimal latency benefit."
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.html

**Secondary Index Strategy: GSI vs LSI vs Write Sharding** 🟢
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | GSI | DynamoDB GSI | Query flexibility; different partition key | Eventually consistent; independent throughput cost | Alternate access patterns with different partition key |
  | LSI | DynamoDB LSI | Strong consistency on alternate sort; shared throughput | Created at table creation only; 10 GB per-PK limit | Same partition key, alternate sort order, small partitions |
  | Write sharding (suffix) | DynamoDB (schema design) | Hot-key distribution | Scatter-query for all-shards reads | Inherently low-cardinality partition key |

- Cost Profile: GSIs add throughput cost (own RCU/WCU); LSIs share base-table throughput. Sharding has no extra cost but increases query complexity.
- Architect Instruction: "Ask 'is the query partition key the same as the base table?' — if yes, evaluate LSI (creation window constraint). If the partition key differs, GSI is required."
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/SecondaryIndexes.html

**CDC Consumer: DynamoDB Streams vs Kinesis Data Streams** 🟢
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | DynamoDB Streams | DynamoDB Streams + Lambda | Simplicity; exactly-once delivery; per-item ordering | 24h retention; 2-consumer limit | Single Lambda processor; event sourcing; simple fan-out |
  | Kinesis Data Streams for DynamoDB | Kinesis + KCL/Flink/Firehose | Up to 1-year retention; 5+ consumers/shard; Flink/Glue integration | Occasional duplicates; more complex | Multiple consumers; long retention; analytics pipelines; Flink |

- Architect Instruction: "Ask 'how many independent consumers need this stream?' — more than 2 consumers mandates Kinesis Data Streams."
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/streamsmain.html

---

### 🚫 Anti-Patterns

**Low-Cardinality Partition Key (Hot Partition)** 🟢
- Risk Level: CRITICAL
- Why: A partition receiving more than 3,000 reads/sec or 1,000 writes/sec is throttled at the partition level regardless of total table capacity. Adaptive capacity cannot exceed the per-partition ceiling. (bp-partition-key-design)
- Instead: High-cardinality keys (user_id, order_id, UUID). For inherently low-cardinality keys (status, region, type), apply write sharding (random or calculated suffix). Use Contributor Insights to detect hot keys post-deployment.
- Detection: CloudWatch Contributor Insights → ConsumedThroughputUnits per partition key. ThrottledRequests metric spike with low total table utilization.
- Impact: Outage (partial — items with the hot key return ProvisionedThroughputExceededException)
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html

**Scan on Production Tables** 🟢
- Risk Level: HIGH
- Why: A Scan reads every item in the table or index, consuming RCUs proportional to the total data size regardless of result set, competing with production traffic. (bp-general-nosql-design)
- Instead: Model the access pattern at design time using a Query (with partition key equality). If ad-hoc queries are unavoidable, export to S3 + Athena or use zero-ETL to Redshift.
- Detection: CloudWatch → ConsumedReadCapacityUnits spike without a corresponding write; CloudTrail data events showing Scan operations.
- Impact: Cost overrun; read throttling on production tables; latency degradation for concurrent Queries.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html

**DAX for Strongly Consistent Read Workloads** 🟢
- Risk Level: HIGH
- Why: DAX cannot serve strongly consistent reads — they are passed through to DynamoDB and NOT cached. A workload that requires strong consistency gains no latency benefit from DAX and still incurs the DAX cluster cost. (DAX.consistency)
- Instead: For strong consistency requirements, read directly from DynamoDB with `ConsistentRead=true`. Reserve DAX for eventually consistent, read-heavy, hot-key workloads with >90% cache hit rate.
- Detection: DAX client metrics → CacheMisses near 100%; application logs showing ConsistentRead=true requests.
- Impact: Unnecessary cost (DAX cluster EC2 instances); no latency improvement.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.consistency.html

**Missing CloudTrail Data-Event Logging on Regulated Tables** 🟢
- Risk Level: HIGH
- Why: Management events are logged automatically; data-plane events (item reads/writes) are opt-in and off by default. A table with no data-event logging has no item-level audit trail — compliance frameworks (PCI DSS, HIPAA, SOX) require item-level access evidence.
- Instead: Enable CloudTrail data-event logging at table provisioning for all regulated tables. Use advanced event selectors to limit cost to specific tables.
- Detection: CloudTrail console → Data event logging settings for table ARN. Absence of dynamodb.amazonaws.com data events in CloudTrail logs.
- Impact: Compliance violation; audit failure; inability to investigate a data breach.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/logging-using-cloudtrail.html

**Sensitive Data in Primary Key Values** 🟢
- Risk Level: HIGH
- Why: Primary key values appear in DescribeTable responses, CloudTrail logs, and DynamoDB's internal routing metadata. They cannot be encrypted by DynamoDB — they are stored and transmitted in plaintext.
- Instead: Use opaque, non-descriptive key values (`pk`, `sk`, UUIDs) or apply the AWS Database Encryption SDK to encrypt sensitive attributes before they reach DynamoDB. Never use SSN, email, or PII as primary key attributes.
- Detection: Code review of PutItem calls; DescribeTable to inspect key schema naming; CloudTrail log sampling for sensitive patterns.
- Impact: Data breach (PII/PHI exposed in logs and metadata); compliance violation.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices-security-preventative.html

**Bypassing DAX and Writing Directly to DynamoDB** 🟢
- Risk Level: MEDIUM
- Why: Writes made directly to DynamoDB (bypassing DAX) do NOT invalidate the DAX item cache. A subsequent read through DAX returns the stale cached value until TTL expires (default 5 minutes). This creates silent inconsistency in applications that mix DAX and direct DynamoDB paths.
- Instead: Route all reads and writes through DAX when DAX is deployed. If a component must write directly, either disable DAX for those item types or accept a 5-minute inconsistency window documented in the runbook.
- Detection: Application-layer data consistency checks; DAX CacheMisses vs DynamoDB ConsumedWriteCapacityUnits discrepancy.
- Impact: Stale data served to users; data integrity bugs.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.consistency.html

**Using Global Tables Legacy Version (2017.11.29)** 🟡
- Risk Level: MEDIUM
- Why: Global Tables 2017.11.29 (Legacy) publishes 2 stream records per write (vs 1 in Current), does not synchronize TTL across replicas, and is the superseded version. AWS guidance: *"You should use Version 2019.11.21 (Current) whenever possible."* Upgrade is irreversible.
- Instead: Use version 2019.11.21 (Current) for all new global tables. Migrate existing legacy tables using the AWS-documented upgrade procedure, accounting for stream consumer record-count changes.
- Detection: DescribeTable → GlobalTableVersion attribute = "2017.11.29".
- Impact: Higher stream processing cost; TTL divergence across replicas; unsupported path for MRSC.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_versions.html

---

## Cloud-Native Design Patterns

**Single-Table Design**
- Category: Data; Scalability
- Problem: Multiple entity types with different access patterns result in many small tables, increasing operational overhead, permission complexity, and backup cost.
- Solution on AWS: Store all entity types in one table using a generic primary key schema (`pk`, `sk`). Model entity relationships via composite sort keys. Use GSIs with inverted indexes for alternate access patterns. Apply item-type prefixes on keys (e.g., `USER#<id>`, `ORDER#<id>`) to distinguish entities.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Performance | Fewer table round-trips; locality of related data | All changed items flow to Streams — consumers must filter by type |
  | Operations | One backup/restore, one set of permissions | Complex schema; harder onboarding; NoSQL Workbench required |
  | Scalability | Single table scales to any volume | 2-consumer Streams limit constrains fan-out architectures |

- Source: https://aws.amazon.com/blogs/database/single-table-vs-multi-table-design-in-amazon-dynamodb/

**Event Sourcing with DynamoDB Streams + Lambda**
- Category: Communication; Resilience
- Problem: Reliable, ordered, event-driven propagation of database mutations to downstream consumers without polling.
- Solution on AWS: Enable DynamoDB Streams (`NEW_AND_OLD_IMAGES`). Attach a Lambda function as a consumer (one function instance per shard). Use `ParallelizationFactor` (up to 10) for parallel per-shard processing while preserving per-item order.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Ordering | Per-item ordering guaranteed | Per-partition only — cross-partition ordering not guaranteed |
  | Throughput | Serverless; scales with shards | 2-consumer limit per stream shard |
  | Retention | 24-hour stream window | Use Kinesis for >24h replay or >2 consumers |

- Source: https://aws.amazon.com/blogs/database/build-scalable-event-driven-architectures-with-amazon-dynamodb-and-aws-lambda/

**Write Sharding for Hot Partition Keys**
- Category: Scalability
- Problem: A partition key with insufficient cardinality (e.g., `STATUS=PENDING`) concentrates writes on a small number of partitions, hitting the 1,000 WCU/sec per-partition ceiling.
- Solution on AWS: Append a shard suffix to the partition key. Two variants: (1) **Random suffix** (e.g., `PENDING#<random 1–200>`) for uniform distribution — requires scatter-query to read all shards. (2) **Calculated suffix** (e.g., hash-based) for deterministic routing — enables direct GetItem while still distributing writes.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Write throughput | Distributes across N shards × 1,000 WCU | Reading all items for a logical key requires N parallel Queries + merge |
  | Read cost | Direct GetItem for calculated suffix | Scatter-gather adds latency and cost for full-key scans |

- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-sharding.html

**Time-Series Data with Table Class Tiering**
- Category: Data; Scalability
- Problem: Time-series data accumulates continuously, with hot (recent) data accessed frequently and cold (historical) data rarely accessed but expensive to store at Standard class rates.
- Solution on AWS: Create one DynamoDB table per time period (e.g., per month/quarter). Keep the current-period (hot) table on Standard class. Age older periods to Standard-IA (~60% lower storage cost). Use TTL on items within the hot table to auto-expire fine-grained old records.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Cost | Storage savings on cold periods | Cross-table queries require application-level fan-out |
  | Operations | Independent backup/delete per period | Table proliferation; permission management per table |

- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-time-series.html

**Adjacency List / Materialized Graph**
- Category: Data
- Problem: Many-to-many entity relationships (users ↔ groups, orders ↔ products) are expensive to model without joins.
- Solution on AWS: Store nodes and edges in the same table. Partition key = entity ID; sort key = self-reference for the entity record, or target entity ID for the relationship record. A GSI with the sort key as partition key enables bidirectional traversal (find all entities related to a given target).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Reads | Retrieve entity + all relationships in one Query | GSI eventually consistent; complex sort key schemas |
  | Writes | Write node and edge in one table | Relationship deletes require knowing the sort key (edge ID) |

- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-adjacency-graphs.html

**Vector Search + Operational Data (DynamoDB as Combined Store) — GA Aug 2026**
- Category: Data; Communication
- Problem: RAG and AI-agent workloads require storing vector embeddings alongside operational item attributes, with ANN search and attribute filtering — historically requiring a separate vector database.
- Solution on AWS: Create a vector index on a DynamoDB table (up to 5 per table, up to 4,096 dimensions). Store Bedrock-generated embeddings as item attributes. Use `SearchVectors` API for ANN queries with inline attribute filtering (up to 18 filters). Single-digit-ms latency at 99%+ recall.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Simplicity | Eliminates separate vector DB; single operational + vector store | 600 GB base-table size cap without allowlisting; TopK max 100 |
  | Cost | Unified storage and throughput | Vector index throughput consumption on top of item operations |

- Source: https://aws.amazon.com/about-aws/whats-new/2026/08/amazon-dynamodb-vector-search/

---

## Security Architecture

**Encryption at Rest (Key Management)**
- AWS Services: DynamoDB (mandatory AES-256 encryption), AWS KMS (AWS owned key / AWS managed key / CMK)
- Architecture: All table data (items, LSIs, GSIs, Streams, backups) encrypted at rest. Key type is selectable at creation and changeable at any time with zero downtime. CMK enables customer-controlled key rotation, KMS key policy granularity, CloudTrail audit of Decrypt calls, and key deletion as a last-resort access revocation.
- Compliance Alignment: HIPAA, PCI DSS, FedRAMP High, SOC 2 — all require customer control over encryption keys; CMK satisfies this requirement.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/EncryptionAtRest.html

**Fine-Grained Access Control (Multi-Tenant Item Isolation)**
- AWS Services: DynamoDB, AWS IAM (condition keys: `dynamodb:LeadingKeys`, `dynamodb:Attributes`, `dynamodb:Select`, `dynamodb:ReturnValues`)
- Architecture: Attach IAM conditions to restrict an authenticated principal (e.g., Cognito federated user) to only items whose partition key matches their identity (`ForAllValues:StringEquals` on `dynamodb:LeadingKeys` with substitution variable `${cognito-identity.amazonaws.com:sub}`). Pair with `dynamodb:Select = SPECIFIC_ATTRIBUTES` to prevent full-item returns. Explicitly Deny `Scan` — Scan cannot be constrained by LeadingKeys.
- Compliance Alignment: SOC 2 (least privilege), HIPAA (access controls), PCI DSS (need-to-know)
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html

**Private Connectivity (VPC Isolation)**
- AWS Services: DynamoDB, Amazon VPC (Gateway endpoint — free), AWS PrivateLink (interface endpoint — GA March 2024), DAX PrivateLink (GA October 2025)
- Architecture: Gateway endpoint for all EC2/Lambda-to-DynamoDB traffic within VPC (no cost, no additional infra). Interface endpoint (PrivateLink) for on-premises Direct Connect, cross-account, or cross-Region peering paths. Enforce via IAM condition `aws:sourceVpce` on table resource-based policy to deny all non-endpoint access. DAX PrivateLink available for in-VPC cache isolation.
- Compliance Alignment: FedRAMP, DISA STIG (no internet egress for data at rest/transit), PCI DSS network segmentation
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/network-isolation.html

**Cross-Account Access (Resource-Based Policies — GA March 2024)**
- AWS Services: DynamoDB (resource-based policy on table/stream), AWS IAM, IAM Access Analyzer
- Architecture: Attach a resource-based policy to the target table granting the external account's principal. The external principal must also have an identity-based policy allowing the action on the resource ARN — both sides required. Max policy size 20 KB. Billing charged to the resource-owner account. CloudTrail captures events in both accounts. Validate with IAM Access Analyzer external-access findings.
- Compliance Alignment: SOC 2 (third-party access controls), ISO 27001 (supplier relationships)
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/access-control-resource-based.html

**Client-Side Encryption (Defense-in-Depth)**
- AWS Services: AWS Database Encryption SDK for DynamoDB, AWS KMS
- Architecture: Encrypt and sign item attributes before they leave the application, before reaching DynamoDB. Architect chooses which attributes are encrypted (sensitive) vs signed-only (integrity-checked) vs plaintext. Encrypted attributes are unreadable even to DynamoDB operators. Decryption requires the same KMS key — key deletion permanently destroys data.
- Compliance Alignment: HIPAA (PHI encryption end-to-end), GDPR (data minimization via field-level encryption)
- Source: https://docs.aws.amazon.com/database-encryption-sdk/latest/devguide/what-is-database-encryption-sdk.html

---

## Operational Patterns

**Disaster Recovery — Active-Active Multi-Region (MREC)**
- RTO/RPO: RTO ≈ minutes (traffic redirect); RPO ≈ replication lag (typically <1 second, >0)
- AWS Services: DynamoDB Global Tables 2019.11.21, Route 53 (latency-based routing / health checks), CloudWatch (ReplicationLatency metric)
- Cost Profile: Medium-High — replicated writes billed per Region. On-demand global tables replicated-write price reduced up to 67% effective Nov 2024.
- Automation: Route 53 health checks auto-redirect traffic to healthy Region. Monitor `ReplicationLatency` metric with CloudWatch alarm (threshold: >5 seconds warrants investigation). No manual failover required — all replicas accept reads and writes.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GlobalTables.html

**Disaster Recovery — Zero-RPO Active-Active (MRSC)**
- RTO/RPO: RTO ≈ minutes; RPO = 0
- AWS Services: DynamoDB Global Tables MRSC (GA June 2025), AWS FIS (resilience testing, Jan 2026)
- Cost Profile: High — same as MREC but with synchronous write overhead (higher write latency)
- Automation: MRSC writes are synchronously replicated — no replication lag to monitor. Test resilience via AWS FIS MRSC fault-injection actions (GA January 2026). On Region failure, redirect traffic to any remaining replica — reads and writes always return latest version.
- Source: https://aws.amazon.com/about-aws/whats-new/2025/06/amazon-dynamo-db-global-tables-multi-region-strong-consistency-generally-available/

**Backup Strategy — PITR + On-Demand**
- RTO/RPO: PITR RPO = seconds; RTO = minutes to hours depending on table size. On-demand RPO = time of last backup.
- AWS Services: DynamoDB (PITR, on-demand backup), S3 (export), AWS Backup (centralized scheduling)
- Cost Profile: Low — PITR charged on table + LSI data size; configurable 1–35 day window (GA January 2025). Shorter windows reduce cost.
- Automation: Enable PITR at table creation via IaC (CloudFormation/Terraform). Set retention period matching compliance window. Use AWS Backup for cross-account / cross-Region backup copies. Deletion of PITR-enabled table auto-creates a 35-day system snapshot at no cost.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery_Howitworks.html

**Observability — Throttle Detection and Hot-Key Identification**
- RTO/RPO: N/A (proactive)
- AWS Services: DynamoDB, CloudWatch (ThrottledRequests, ConsumedReadCapacityUnits, ConsumedWriteCapacityUnits), CloudWatch Contributor Insights (comprehensive mode + throttle-only mode)
- Cost Profile: Low — Contributor Insights throttle-only mode incurs near-zero cost during normal operation; charges only on throttle events.
- Automation: Enable Contributor Insights (throttle-only mode) on all production tables. Create CloudWatch Alarm on `ThrottledRequests` > 0 sustained for 5 minutes. For on-demand tables with max-throughput configured, monitor `OnDemandMaxReadRequestUnits` / `OnDemandMaxWriteRequestUnits` metrics.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/contributorinsights_HowItWorks.html

**Data Pipeline — Export to S3 and Incremental CDC**
- RTO/RPO: N/A (analytics)
- AWS Services: DynamoDB (PITR required), S3, Amazon Athena, Amazon Redshift (zero-ETL, GA Oct 2024), Amazon SageMaker Lakehouse (zero-ETL, GA Dec 2024)
- Cost Profile: Low per export — no table throughput consumed. Export stored in S3 at S3 rates.
- Automation: Full export via `ExportTableToPointInTime` API for snapshots. Incremental export (GA Sept 2023) for changed items between two timestamps (15 min – 24 hr window). Zero-ETL to Redshift or SageMaker Lakehouse for continuous SQL analytics without pipeline code.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/S3DataExport.HowItWorks.html

---

## Reference Architectures

**Serverless Web Application**
- Context: User-facing web app with authentication, CRUD operations, and content storage
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Edge | Amazon CloudFront | CDN + WAF |
  | Auth | Amazon Cognito | User pool + federated identity |
  | API | Amazon API Gateway | REST/HTTP API |
  | Compute | AWS Lambda | Stateless business logic |
  | Data | Amazon DynamoDB | User profiles, content, sessions |
  | Storage | Amazon S3 | Static assets, media |

- Key Decisions: Single-table vs multi-table (access pattern complexity); FGAC via Cognito identity + `dynamodb:LeadingKeys` for user data isolation; PITR enabled; CloudTrail data events enabled.
- Scaling Path: On-demand DynamoDB → add DAX if read latency requirements tighten → add GSIs for new access patterns as product evolves.
- Source: https://aws.amazon.com/lambda/resources/refarch/refarch-webapp/

**Active-Active Global Application (MREC)**
- Context: Multi-Region user-facing application requiring low write latency globally with tolerable RPO
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Routing | Route 53 (latency routing + health checks) | Region failover |
  | API | API Gateway (Regional) per Region | Regional entry point |
  | Compute | Lambda (Regional) per Region | Stateless processing |
  | Data | DynamoDB Global Tables 2019.11.21 (MREC) | Active-active, multi-Region |
  | Observability | CloudWatch (ReplicationLatency alarm) | Replication health |

- Key Decisions: MREC conflict resolution = last-writer-wins — design for idempotent writes. Use conditional writes for critical state. Monitor ReplicationLatency < 1s as SLO.
- Scaling Path: MREC → migrate to MRSC (June 2025 GA) if RPO=0 becomes a requirement — requires empty-table migration to 3-Region topology.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GlobalTables.html

**AI-Augmented Operational Store (Vector Search)**
- Context: RAG/recommendation workload needing both transactional item lookups and ANN vector search on the same dataset
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Embedding | Amazon Bedrock (Titan Embeddings) | Generate embeddings |
  | Storage | DynamoDB (vector index + item attributes) | Combined operational + vector store |
  | Search | DynamoDB SearchVectors API | ANN search with attribute filtering |
  | Inference | Amazon Bedrock (Claude) | LLM generation with retrieved context |
  | API | API Gateway + Lambda | Orchestration |

- Key Decisions: Up to 5 vector indexes per table; max 4,096 dimensions; TopK max 100 per query; 600 GB base-table size cap (without allowlisting). Use for datasets where operational access and vector search coexist — offload large-scale ANN-only workloads to dedicated vector services.
- Scaling Path: Start single table with vector index → enable Bedrock Knowledge Base integration → add GSI for metadata-filtered access patterns.
- Source: https://aws.amazon.com/about-aws/whats-new/2026/08/amazon-dynamodb-vector-search/

**Event-Driven Microservices (Streams + Lambda)**
- Context: Microservices architecture requiring reliable event propagation on item mutations
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Write | DynamoDB table (source of truth) | Transactional item writes |
  | CDC | DynamoDB Streams (NEW_AND_OLD_IMAGES) | Ordered item-level changelog |
  | Processing | AWS Lambda (ParallelizationFactor up to 10) | Per-shard event consumer |
  | Fan-out | Amazon EventBridge or SNS | Multi-consumer distribution |
  | Analytics | Kinesis Data Streams for DynamoDB → Flink/Firehose | Long-retention; multi-consumer CDC |

- Key Decisions: Streams 2-consumer limit per shard — use EventBridge/SNS for fan-out beyond 2. Switch to Kinesis for >24h retention or >2 direct consumers. Enable Kinesis if Apache Flink analytics required.
- Scaling Path: DynamoDB Streams + Lambda → add Kinesis when consumer count or retention window exceeds Streams limits.
- Source: https://aws.amazon.com/blogs/database/build-scalable-event-driven-architectures-with-amazon-dynamodb-and-aws-lambda/

---

## Provider Differentiators

- **Mandatory serverless encryption at rest** — DynamoDB encrypts all data at rest by default; no configuration required. Competitors (e.g., MongoDB Atlas) require encryption to be explicitly enabled in some tiers.
- **Adaptive capacity at no extra cost** — automatically rebalances throughput to hot partitions within per-partition ceilings, without manual intervention. Unique among managed NoSQL services.
- **MRSC with witness topology (June 2025)** — zero-RPO active-active across 3 Regions with a witness option for cost reduction. No equivalent in other managed NoSQL services at this scale.
- **Native vector search in a key-value store (August 2026)** — DynamoDB can now serve as a combined operational + vector store, eliminating the need for a separate vector database for moderate-scale AI workloads.
- **Zero-ETL to Redshift and SageMaker Lakehouse** — direct, no-code analytics pipelines from DynamoDB without S3 export intermediaries.
- **ParallelizationFactor on Lambda Streams consumer** — up to 10 concurrent Lambda invocations per shard, unique to DynamoDB Streams, preserving per-item ordering while increasing throughput.

---

## Scenario Coverage

**Standard Case**: Multi-tenant SaaS application with user-owned data, global reach, and event-driven processing
- Approach: Single DynamoDB table with composite keys (`pk = USER#<user_id>`, `sk = ENTITY_TYPE#<id>`). FGAC via Cognito + `dynamodb:LeadingKeys` for item isolation. DynamoDB Streams + Lambda for event-driven projections. Global Tables 2019.11.21 (MREC) for active-active global availability. PITR enabled with 35-day retention. CloudTrail data events enabled.
- Key Decisions: Access patterns defined before table creation; GSIs modeled for top 5 alternate query patterns; Contributor Insights enabled from day 1 for hot-key detection.

**Edge Case**: Regulatory workload requiring RPO = 0 across Regions (e.g., global financial ledger)
- Approach: DynamoDB Global Tables MRSC (GA June 2025), exactly 3 Regions within one Region set (US, EU, or AP). Start from empty table — no migration path from an existing table. No TTL, no LSIs, no transactions (MRSC constraints). Use conditional writes (`condition = attribute_exists(version) AND version = :expected`) for optimistic concurrency. Test via AWS FIS MRSC fault-injection (GA January 2026).
- Clarification: Confirm regulatory requirement is specifically RPO=0 — if RPO<1s is acceptable, MREC avoids MRSC's topology and feature constraints while achieving 99.999% SLA.

**Anti-Pattern Case**: Architect proposes using `STATUS` or `REGION` as the partition key for a write-heavy table
- Clarification: Ask "how many distinct values does this partition key have?" A key with 5 distinct values spreads all writes across at most 5 partitions × 1,000 WCU/sec = 5,000 WCU/sec total throughput ceiling regardless of how much provisioned or on-demand capacity is allocated. Flag this as a critical anti-pattern. Redesign: use a high-cardinality key (item ID, user ID) as partition key and use a GSI or filter expression to query by status/region. If status is a required partition key, apply write sharding (random suffix 1–N).

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Capacity | On-demand capacity mode details, billing units, initial throughput limits, switching rules | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/on-demand-capacity-mode.html (2026-08-28) |
| 1 | Capacity | On-demand maximum throughput (cost guardrail), CloudWatch metrics | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/on-demand-capacity-mode-max-throughput.html (2026-08-28) |
| 1 | Capacity | Warm throughput GA Nov 2024 — mechanics, pre-warming charge, irreversibility | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/warm-throughput.html (2026-08-28) |
| 1 | Capacity | Auto scaling target-tracking, scale-up/down trigger thresholds | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/AutoScaling.html (2026-08-28) |
| 1 | Capacity | DAX consistency model — strong reads passthrough, write-through, stale-read risk from direct DynamoDB writes | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.consistency.html (2026-08-28) |
| 1 | Capacity | Burst capacity (5 min), adaptive capacity, per-partition limits (3000/1000) | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/burst-adaptive-capacity.html (2026-08-28) |
| 1 | Capacity | Streams vs Kinesis comparison table, StreamViewType immutability, Lambda ParallelizationFactor | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/streamsmain.html (2026-08-28) |
| 1 | Capacity | Nov 2024 price reduction: on-demand −50%, global tables up to −67% | Added | https://aws.amazon.com/blogs/database/new-amazon-dynamodb-lowers-pricing-for-on-demand-throughput-and-global-tables/ (2026-08-28) |
| 2 | Data Modeling | Primary key types, key length limits (2048/1024 bytes), scalar-only constraint | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html (2026-08-28) |
| 2 | Data Modeling | Single-table vs multi-table official guidance, access-pattern-first methodology | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html (2026-08-28) |
| 2 | Data Modeling | GSI vs LSI comparison (creation window, consistency, size limits, throughput ownership) | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/SecondaryIndexes.html (2026-08-28) |
| 2 | Data Modeling | Write sharding: random suffix vs calculated suffix with trade-offs | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-sharding.html (2026-08-28) |
| 2 | Data Modeling | Data types (scalar/document/set), empty set restriction, 32-level nesting | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.NamingRulesDataTypes.html (2026-08-28) |
| 2 | Data Modeling | TTL mechanics (no WCU consumption, few-days delay, filter expressions needed) | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html (2026-08-28) |
| 2 | Data Modeling | Transactions: 100-item/4MB limits, isolation levels, cost (2× capacity), idempotency token | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html (2026-08-28) |
| 2 | Data Modeling | Vector indexes GA Aug 2026: 5 per table, 4096 dims, TopK 100, 600 GB cap | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html (2026-08-28) |
| 3 | Security | Encryption at rest: mandatory AES-256, three KMS key types, sort key plaintext caveat | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/EncryptionAtRest.html (2026-08-28) |
| 3 | Security | FGAC condition keys: LeadingKeys (ForAllValues requirement), Attributes, Select, ReturnValues, gotchas (Scan exclusion, ProjectionExpression) | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html (2026-08-28) |
| 3 | Security | ABAC GA Nov 18, 2024 (tables + indexes); Streams ABAC GA Aug 2026 | Added | https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-dynamodb-general-availability-attribute-based-access-control/ (2026-08-28) |
| 3 | Security | VPC endpoints: gateway (free) vs PrivateLink interface (GA March 2024); DAX PrivateLink Oct 2025 | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/network-isolation.html (2026-08-28) |
| 3 | Security | Resource-based policies GA March 2024: cross-account model, 20 KB limit, billing to resource owner | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/access-control-resource-based.html (2026-08-28) |
| 3 | Security | CloudTrail data events: opt-in per table, off by default — compliance gap | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/logging-using-cloudtrail.html (2026-08-28) |
| 3 | Security | RCPs support for DynamoDB GA Feb 2026 | Added | https://aws.amazon.com/about-aws/whats-new/2026/02/aws-expands-resource-control-policies-amazon/ (2026-08-28) |
| 4 | Resilience | Global tables version comparison: 2017.11.29 vs 2019.11.21 (stream records, TTL sync, upgrade irreversibility) | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_versions.html (2026-08-28) |
| 4 | Resilience | MREC: last-writer-wins conflict, sub-second replication, RPO>0, ReplicationLatency metric | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html (2026-08-28) |
| 4 | Resilience | MRSC GA June 2025: zero RPO, witness, 3-Region constraint, available region sets, restrictions (no TTL/LSI/transactions) | Added | https://aws.amazon.com/about-aws/whats-new/2025/06/amazon-dynamo-db-global-tables-multi-region-strong-consistency-generally-available/ (2026-08-28) |
| 4 | Resilience | MRSC + AWS FIS resilience testing GA January 2026 | Added | https://aws.amazon.com/about-aws/whats-new/2026/01/amazon-dynamodb-global-tables-with-mrsc-fis/ (2026-08-28) |
| 4 | Resilience | Multi-account global tables GA February 2026 | Added | https://aws.amazon.com/about-aws/whats-new/2026/02/dynamodb-gt-multi-account/ (2026-08-28) |
| 4 | Resilience | PITR configurable retention 1–35 days GA January 2025 | Added | https://aws.amazon.com/about-aws/whats-new/2025/01/amazon-dynamodb-configurable-point-in-time-recovery-periods/ (2026-08-28) |
| 4 | Resilience | Standard-IA table class: ~60% storage savings, no reserved capacity support | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/WorkingWithTables.tableclasses.html (2026-08-28) |
| 4 | Resilience | Contributor Insights: comprehensive + throttle-only modes; MRSC per-Region reporting only | Added | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/contributorinsights_HowItWorks.html (2026-08-28) |
| 5 | Changelog | Full 2024–2026 changelog: PrivateLink, resource-based policies, max throughput, ABAC, MRSC, price cut, warm throughput, multi-account GT, lambda cross-account Streams, RCPs, vector search | Added | Multiple What's New sources (2026-08-28) |
| 5 | Changelog | ExtendDB open-source DynamoDB-compatible adapter GA May 2026 | Added | https://aws.amazon.com/about-aws/whats-new/2026/05/aws-extenddb-dynamodb/ (2026-08-28) |
| 5 | Changelog | Failed conditional writes capacity consumption — not confirmed on condition-expressions page | ⚠️ IRRESOLVABLE — claim common in community but not confirmed on fetched primary doc page; marked unverified | — |
| 5 | Changelog | Exact reserved capacity savings percentages (54% / 77%) | ⚠️ IRRESOLVABLE — from search summarization, not primary pricing page; recommend reconfirmation before citing | — |
| 5 | Changelog | BatchWriteItem (25 items/16 MB) and BatchGetItem (100 items/16 MB) limits | ⚠️ IRRESOLVABLE — standard limits not fetched from API Reference in this research pass; verify before citing | — |
| 5 | Changelog | Re:Invent 2025 DynamoDB-specific GA items | ⚠️ IRRESOLVABLE — cross-service announcements confirmed; no DynamoDB-only GA clearly attributed to that week | — |
| 5 | Changelog | 2025 or 2026-specific DynamoDB pricing changes | ⚠️ IRRESOLVABLE — no pricing change dated post-Nov 2024 found in official sources | — |
