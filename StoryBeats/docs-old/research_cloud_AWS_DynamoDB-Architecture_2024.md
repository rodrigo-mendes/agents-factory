# AWS DynamoDB — NoSQL Data Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS DynamoDB — NoSQL Data Architecture"
Cloud_Provider: "AWS"
Architecture_Domain: "NoSQL Data Architecture"
Target_Edition: "AWS DynamoDB 2024"
Architecture_Context: "Cloud-native applications requiring single-digit millisecond NoSQL data access at any scale — covering serverless API backends, event-driven pipelines, session management, gaming, financial ledgers, time-series, and global multi-region workloads"
Official_Source_URL: "https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-25"
Currency_Threshold: "2027-05-25 — review required after this date due to DynamoDB feature velocity and pricing model changes"
```

---

## Executive Summary

Amazon DynamoDB is AWS's serverless, fully managed, distributed NoSQL database. It delivers consistent single-digit millisecond performance at any scale for both key-value and document data models, without requiring capacity planning, patching, or database software management. DynamoDB underpins Amazon's own most demanding workloads — handling trillions of calls during Prime Day events and sustaining peak traffic exceeding 500,000 requests/second for individual customer tables. It guarantees 99.99% availability for single-region tables and 99.999% availability for Global Tables. DynamoDB's schemaless nature, combined with its request-level ACID transactions, CDC streaming via DynamoDB Streams or Kinesis Data Streams, and native zero-ETL integration with Amazon Redshift and OpenSearch Service, makes it the de-facto AWS NoSQL store for operational workloads.

The 2024 edition's most architecturally significant advances are: (1) **on-demand mode promoted as the default and recommended capacity mode** — removing the previous implicit guidance toward provisioned mode for cost optimization and simplifying new-table decisions; (2) **zero-ETL integration with Amazon Redshift** — enabling near-real-time analytics on DynamoDB operational data without a custom ETL pipeline; (3) **Block Public Access (BPA) and resource-based policies with IAM Access Analyzer support** — closing a security posture gap and aligning DynamoDB access controls with the S3 and RDS security model. The DynamoDB Well-Architected Lens now covers all six WAF pillars, providing a structured assessment framework native to the service.

The three most critical architecture guardrails for DynamoDB are: (1) **design the access patterns before designing the schema** — DynamoDB's partition and sort key structure cannot be changed after table creation; querying outside defined key patterns requires full table scans that are expensive and slow; (2) **never use sequential or monotonic partition keys** — timestamps, auto-incremented IDs, and UUID v1 prefixes concentrate writes on a single partition, triggering throttling regardless of provisioned capacity or on-demand scaling; (3) **always enable Point-in-Time Recovery (PITR)** — DynamoDB is fully managed but does not protect against application-level data corruption or accidental deletes; PITR is the primary safety net for operational data integrity.

---

## Cloud Architecture Glossary

```
Term: Partition Key (Hash Key)
Definition: The primary attribute used to distribute items across DynamoDB's internal storage partitions via an internal hash function. Together with the optional Sort Key it forms the item's Primary Key. A Partition Key-only table is called a simple primary key table. Every item in the table must have the Partition Key attribute.
Provider Docs Section: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html
Architect Usage: Design Partition Keys to distribute traffic uniformly across all partitions. High-cardinality values (user ID, device ID, order ID) are preferred. Low-cardinality values (status, country, date) create hot partitions when used alone as Partition Keys.
Common Confusion: Partition Key ≠ physical partition. Multiple items with different Partition Key values share the same physical partition. DynamoDB manages the mapping internally. The Partition Key determines routing, not physical isolation.

Term: Sort Key (Range Key)
Definition: An optional secondary attribute that, combined with the Partition Key, forms a Composite Primary Key. Items with the same Partition Key are stored together sorted by Sort Key value. Enables range queries (begins_with, between, >, <, >=, <=) on items within a single partition.
Provider Docs Section: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html
Architect Usage: Use Sort Keys to group related items under a single Partition Key (entity + relationship hierarchies, time-ordered events per entity, versioned records). Use Sort Key prefix patterns (e.g., PROFILE#, ORDER#, SESSION#) to separate entity types within a single-table design.
Common Confusion: Sort Key ordering is lexicographic for String type and numeric for Number type. Storing timestamps as strings requires ISO 8601 format (YYYY-MM-DDTHH:MM:SS) to maintain natural sort order. Unix epoch integers sort correctly as Number type.

Term: Global Secondary Index (GSI)
Definition: A secondary index with a Partition Key and optional Sort Key that can differ from the table's primary key. GSIs are maintained asynchronously and support only eventually consistent reads. Up to 20 GSIs per table (default; can be increased via Service Quotas). Each GSI maintains its own provisioned throughput or participates in on-demand scaling.
Provider Docs Section: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html
Architect Usage: Use GSIs to support query patterns that cannot be served by the table's primary key. Over-provision GSIs for write-heavy tables because GSI write throughput is consumed independently from the base table. Sparse GSIs (indexing only items with a specific attribute) are efficient for filtering minority-of-table subsets.
Common Confusion: GSI ≠ eventually consistent secondary copy of the table. GSIs only index items that have the GSI Partition Key attribute; items without that attribute are not present in the GSI (this is the sparse index pattern). GSI reads do NOT consume the base table's RCU — they consume the GSI's own read capacity.

Term: Local Secondary Index (LSI)
Definition: A secondary index that shares the same Partition Key as the table but uses a different Sort Key. LSIs are co-partitioned with the base table, support both eventually consistent and strongly consistent reads, and must be defined at table creation time. Limited to 5 per table. The combined item collection (table + all LSIs for a given Partition Key value) cannot exceed 10 GB.
Provider Docs Section: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/LSI.html
Architect Usage: Use LSIs only when strongly consistent reads on an alternate sort order are required within the same partition. The 10 GB item-collection limit is a hard constraint — design Partition Key cardinality so that no single Partition Key value accumulates more than 10 GB of data inclusive of all LSIs.
Common Confusion: LSIs cannot be added or deleted after table creation. This immutability makes them a high-commitment design decision. Unlike GSIs, LSI reads consume the base table's RCU and they share the partition's throughput budget. Most architects prefer GSIs for flexibility despite losing strong consistency.

Term: Read Capacity Unit (RCU)
Definition: The unit of read throughput consumed by DynamoDB read operations. One RCU provides one strongly consistent read per second or two eventually consistent reads per second for items up to 4 KB in size. Items larger than 4 KB consume multiple RCUs (rounded up to the nearest 4 KB boundary). Transactional reads consume 2 RCUs per item (up to 4 KB).
Provider Docs Section: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/read-write-operations.html
Architect Usage: Right-size provisioned RCU by profiling item sizes and read consistency requirements. For large-item tables, strongly consistent reads are disproportionately expensive — evaluate DAX caching or shifting to eventual consistency. Use CloudWatch ConsumedReadCapacityUnits metric to validate actual consumption versus provisioned.
Common Confusion: RCU consumption is per item per read operation, not per response. A Query returning 100 items of 1 KB each consumes 50 RCUs (eventually consistent) or 100 RCUs (strongly consistent) — not 1 RCU for the entire Query response.

Term: Write Capacity Unit (WCU)
Definition: The unit of write throughput consumed by DynamoDB write operations. One WCU provides one write per second for items up to 1 KB in size. Items larger than 1 KB consume multiple WCUs (rounded up to the nearest 1 KB boundary). Transactional writes consume 2 WCUs per item (up to 1 KB). Conditional writes consume the same WCUs regardless of whether the condition is met.
Provider Docs Section: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/read-write-operations.html
Architect Usage: Model WCU cost for write-heavy workloads carefully — large items with frequent updates amplify WCU consumption linearly. Write sharding and attribute-level updates (UpdateItem targeting specific attributes) reduce WCU consumption relative to full-item PutItem operations.
Common Confusion: WCUs are consumed per write operation, not per byte changed. Updating a single attribute in a 10 KB item via UpdateItem consumes 10 WCUs (10 KB / 1 KB per WCU). This makes partial-update strategies critical for large items.

Term: On-Demand Capacity Mode
Definition: DynamoDB's default throughput mode, introduced in 2018 and promoted as the recommended mode in 2024. Automatically scales to any traffic level without capacity planning. Charges per read request unit (RRU) and write request unit (WRU) consumed. No minimum provisioned capacity required; no charges when the table has zero traffic.
Provider Docs Section: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/on-demand-capacity-mode.html
Architect Usage: Default choice for all new tables. Switch to provisioned mode only when sustained high-traffic workloads make the ~6-7x per-request price premium of on-demand economically unjustifiable versus the operational overhead of capacity planning and auto-scaling configuration.
Common Confusion: On-demand mode still has per-partition throughput limits (3,000 RCU/s and 1,000 WCU/s per partition). On-demand does not eliminate the need for good partition key design — hot partitions still cause throttling in on-demand mode.

Term: Provisioned Capacity Mode
Definition: A throughput mode where the architect specifies exact RCU and WCU values for a table. Charges are based on provisioned capacity per hour, regardless of actual consumption. DynamoDB Application Auto Scaling can automatically adjust provisioned capacity based on CloudWatch utilization metrics.
Provider Docs Section: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/provisioned-capacity-mode.html
Architect Usage: Appropriate for tables with steady, predictable traffic where on-demand's per-request premium creates meaningful cost delta at scale. Requires Application Auto Scaling to handle traffic spikes. Configure burst capacity (up to 300 seconds of unused capacity per partition) awareness into scaling policies.
Common Confusion: Provisioned capacity does not guarantee that all requests succeed — if traffic spikes beyond provisioned + burst capacity, requests are throttled (HTTP 400 ProvisionedThroughputExceededException). On-demand mode absorbs spikes more gracefully within partition limits.

Term: DynamoDB Streams
Definition: A time-ordered sequence of item-level modification events (INSERT, MODIFY, REMOVE) in a DynamoDB table. Stream records are available for up to 24 hours. Stream records can include the item's old image, new image, both, or only keys — configured per table. Enables Lambda triggers and custom stream consumers.
Provider Docs Section: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html
Architect Usage: Use DynamoDB Streams for event-driven CDC patterns, Lambda-based triggers, cross-region replication (prior to Global Tables), and search index maintenance. For retention beyond 24 hours or fan-out to multiple consumers, use Kinesis Data Streams for DynamoDB instead.
Common Confusion: DynamoDB Streams ≠ Kinesis Data Streams for DynamoDB. DynamoDB Streams: 24-hour retention, one active consumer per shard, managed by Lambda ESM. Kinesis Data Streams for DynamoDB: up to 365-day retention, multiple concurrent consumers, enhanced fan-out, CloudWatch integration, but adds Kinesis Data Streams cost.

Term: Global Tables
Definition: A fully managed, multi-active, multi-region DynamoDB replication feature. All replicas accept both reads and writes. Replication is asynchronous with last-writer-wins conflict resolution. Provides 99.999% availability SLA. Requires DynamoDB Streams to be enabled. Supports table-level configuration of replicas.
Provider Docs Section: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GlobalTables.html
Architect Usage: Use Global Tables for applications that must serve low-latency reads and writes from multiple geographic regions, or for multi-region DR with near-zero RPO. Conflict resolution uses last-writer-wins based on timestamps — design application logic to avoid concurrent conflicting writes to the same item from different regions.
Common Confusion: Global Tables ≠ active-passive multi-region failover. All replicas are active and writable simultaneously. Failover in Global Tables means redirecting application traffic to a healthy replica — there is no primary/secondary concept and no automated DNS failover in Global Tables itself. Applications must implement region-switching logic (Route 53 health checks, etc.).

Term: DynamoDB Accelerator (DAX)
Definition: A fully managed, in-memory caching service purpose-built for DynamoDB. Provides read-through and write-through caching with microsecond response times (vs millisecond for DynamoDB). API-compatible with DynamoDB SDK — replacing DynamoDB endpoint with DAX cluster endpoint requires no application logic changes for read operations.
Provider Docs Section: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.html
Architect Usage: Use DAX for read-heavy workloads with repeated reads of the same items (hot items), where reducing DynamoDB RCU consumption or achieving sub-millisecond latency is required. DAX is a VPC-resident resource — function-based workloads (Lambda) using DAX must be in the same VPC. Consider item-cache TTL and query-cache TTL carefully.
Common Confusion: DAX is a write-through cache for PutItem, UpdateItem, DeleteItem — writes go to DynamoDB AND update the DAX cache. DAX does NOT accelerate DynamoDB Streams, Scan operations by default, or write-heavy workloads where reads are not repeated. DAX clusters run on EC2 instances (not serverless) — they add operational overhead and baseline cost.

Term: Single-Table Design
Definition: An architectural pattern where all entity types for a DynamoDB application are stored in a single DynamoDB table, using composite primary keys (Partition Key + Sort Key) and GSI overloading to serve multiple distinct access patterns. Entities are differentiated by Sort Key prefixes or a dedicated entity-type attribute.
Provider Docs Section: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html
Architect Usage: The recommended DynamoDB design approach. Reduces table management overhead, permissions complexity, and backup costs. Requires upfront access-pattern enumeration. Use NoSQL Workbench to visualize the data model before implementation. Exceptions: high-volume time-series data (separate tables per time window) and teams with strictly separated access-control requirements.
Common Confusion: Single-Table Design ≠ data normalization. Single-table design intentionally duplicates data (denormalization) to serve all access patterns without JOIN-equivalent multi-table queries. This is a deliberate trade-off for query performance and throughput efficiency.

Term: Adaptive Capacity
Definition: A DynamoDB feature that automatically redistributes provisioned throughput (or on-demand capacity) from lightly accessed partitions to partitions experiencing higher traffic. Applies in real-time when uneven access patterns are detected. Applies to both on-demand and provisioned capacity modes.
Provider Docs Section: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/burst-adaptive-capacity.html
Architect Usage: Adaptive capacity is a safety net, not a design strategy. It mitigates transient hot partitions from legitimate access pattern skews but does not override per-partition hard limits (3,000 RCU/s, 1,000 WCU/s). Design partition keys for uniform distribution; rely on adaptive capacity only as a buffer for unavoidable workload spikes.
Common Confusion: Adaptive capacity ≠ unlimited single-partition throughput. A partition cannot exceed 3,000 RCU/s and 1,000 WCU/s regardless of adaptive capacity or total table throughput. Adaptive capacity redistributes unused capacity from cold partitions — it has no capacity to redistribute when all partitions are active.

Term: PartiQL for DynamoDB
Definition: A SQL-compatible query language that DynamoDB supports as an alternative to native DynamoDB API operations (GetItem, PutItem, Query, Scan, etc.). Supports SELECT, INSERT, UPDATE, DELETE statements. Available via AWS Console, CLI, SDK, and NoSQL Workbench. Does not introduce query optimization — each PartiQL statement maps to a specific DynamoDB operation.
Provider Docs Section: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ql-reference.html
Architect Usage: Use PartiQL for ad-hoc data exploration and batch operations via CLI/console. Do NOT use PartiQL as a replacement for understanding DynamoDB access patterns — a PartiQL SELECT without a WHERE clause on the primary key is a full table Scan, with all associated cost and latency implications.
Common Confusion: PartiQL support does NOT make DynamoDB a relational database. JOINs across DynamoDB tables via PartiQL require multiple queries (no server-side join). PartiQL SELECT * without key conditions triggers an expensive table Scan regardless of SQL familiarity suggesting otherwise.

Term: Point-in-Time Recovery (PITR)
Definition: A DynamoDB feature that enables continuous backups with per-second granularity, allowing table restoration to any point within the last 1–35 days (configurable). Restores create a new table — they do not overwrite the existing table. PITR does not consume provisioned capacity and does not impact table availability or performance.
Provider Docs Section: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Point-in-time-recovery.html
Architect Usage: Enable PITR on all production tables. Always-on protection against accidental item deletions, application bugs causing data corruption, and malicious writes. PITR is the minimum viable backup strategy; combine with AWS Backup for cross-region backup copies and long-term archival beyond 35 days.
Common Confusion: PITR ≠ table-level snapshot with instant restore. PITR restores to a NEW table — applications must be reconfigured or data reconciled between the restored table and the production table. The restore process itself takes time proportional to table size. PITR does not protect against table deletion (use deletion protection for that).
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Access-Pattern-First Schema Design**
- Pillar Alignment: Performance Efficiency, Cost Optimization
- Why: DynamoDB queries efficiently only via primary key (Partition Key + Sort Key) or indexes. All other access patterns require full-table Scans, which consume capacity proportional to table size and return unacceptably slow results at scale. AWS documentation states: "you shouldn't start designing your schema for DynamoDB until you know the questions it will need to answer."
- AWS Services: Amazon DynamoDB, NoSQL Workbench for DynamoDB
- Architecture Decision:
  1. Enumerate all application access patterns (reads AND writes) before designing any key schema.
  2. For each pattern, define: entity(s) involved, attributes queried, filter conditions, result ordering, read consistency requirement, estimated QPS.
  3. Design Partition Key and Sort Key to serve the most frequent, most latency-sensitive patterns directly via GetItem/Query.
  4. Design GSIs to serve secondary patterns. Accept that rare or analytical patterns may require scans or offline processing.
  5. Use NoSQL Workbench to model and validate the access-pattern coverage of the key schema before implementation.
- Verification:
  - NoSQL Workbench: Validate all access patterns are served by table keys or GSIs without full Scans.
  - CloudWatch: Monitor `SystemErrors`, `ConsumedReadCapacityUnits`, and `SuccessfulRequestLatency` after go-live.
  - AWS Config: Use `dynamodb-table-encrypted-at-rest` rule as a baseline compliance check.
- Trade-offs: Requires significant upfront design effort. Adding new access patterns post-launch may require new GSIs or data migration.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html

---

**Enable Point-in-Time Recovery (PITR) on All Production Tables**
- Pillar Alignment: Reliability
- Why: DynamoDB is a fully managed service but does not protect against application-level data errors. PITR is the primary safeguard against data loss due to application bugs, accidental deletes, and malicious writes. AWS WAF Reliability Pillar requires automated backup with defined RPO.
- AWS Services: Amazon DynamoDB (PITR), AWS Backup (cross-region copies, long-term archival)
- Architecture Decision:
  Enable PITR on table creation. Configure AWS Backup to schedule cross-account and cross-region copies for regulated workloads. Set `DeletionProtectionEnabled: true` to prevent accidental table deletion.
  ```
  aws dynamodb update-continuous-backups \
    --table-name MyTable \
    --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
  ```
- Verification:
  ```
  aws dynamodb describe-continuous-backups --table-name MyTable \
    --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus'
  # Expected: "ENABLED"
  ```
- Trade-offs: PITR adds storage cost per GB-month. Restore creates a new table — application routing must be updated manually.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Point-in-time-recovery.html

---

**Enforce Encryption at Rest with Customer-Managed Key (CMK) for Regulated Data**
- Pillar Alignment: Security
- Why: DynamoDB encrypts all data at rest by default using AWS-owned keys (no charge, no customer visibility). For regulated workloads (HIPAA, PCI-DSS, GDPR) requiring key ownership, audit trail, and key rotation control, a Customer Managed Key in AWS KMS is required.
- AWS Services: Amazon DynamoDB, AWS KMS
- Architecture Decision:
  All DynamoDB tables encrypt at rest — the question is which key type. For regulatory workloads, specify a CMK at table creation.
  Three options:
  - `AWS_OWNED_KMS_KEY` (default): No cost, no audit, no customer control.
  - `AWS_MANAGED_KEY`: AWS KMS managed key with CloudTrail audit. No additional charge.
  - `CUSTOMER_MANAGED_KEY`: Customer-created KMS key. Full audit trail, key rotation, access control. Adds KMS API call cost per DynamoDB operation.
- Verification:
  ```
  aws dynamodb describe-table --table-name MyTable \
    --query 'Table.SSEDescription.SSEType'
  # Expected: "KMS" for CMK; check KMSMasterKeyArn for customer-managed vs AWS-managed
  ```
- Trade-offs: CMK adds latency overhead (~1-2ms) per operation from KMS API calls. Key rotation must be managed. CMK deletion or disabling renders the table inaccessible until the key is restored.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/EncryptionAtRest.html

---

**Apply Least-Privilege IAM Policies with Fine-Grained Access Control**
- Pillar Alignment: Security
- Why: DynamoDB uses IAM exclusively for authentication and authorization — there are no database-level users or passwords. Over-permissive IAM policies grant broader data access than intended, violating least-privilege and expanding blast radius of compromised credentials.
- AWS Services: Amazon DynamoDB, AWS IAM, IAM Access Analyzer
- Architecture Decision:
  Scope IAM policies to specific tables, specific actions, and (where required) specific item-level or attribute-level conditions.
  ```json
  {
    "Effect": "Allow",
    "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"],
    "Resource": "arn:aws:dynamodb:us-east-1:123456789:table/UserSessions",
    "Condition": {
      "ForAllValues:StringEquals": {
        "dynamodb:LeadingKeys": ["${aws:userid}"]
      }
    }
  }
  ```
  Use `dynamodb:LeadingKeys` condition to restrict user access to their own items (row-level security). Use `dynamodb:Attributes` condition for attribute-level access control. Enable IAM Access Analyzer on the table's resource-based policy to detect unintended access.
- Verification:
  - IAM Access Analyzer: Generate access previews for DynamoDB table resource-based policies.
  - AWS Config rule: `iam-policy-no-statements-with-admin-access`
  - Block Public Access: Enable DynamoDB BPA at account level to prevent accidental public resource-based policies.
- Trade-offs: Fine-grained IAM conditions add policy complexity and require careful testing. Attribute-level conditions must be maintained as schema evolves.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security-iam.html

---

**Enable DynamoDB Streams or Kinesis Data Streams for Event-Driven Architectures**
- Pillar Alignment: Operational Excellence, Reliability
- Why: DynamoDB Streams provides the CDC foundation for event-driven patterns — Lambda triggers, cross-region sync, search index maintenance, audit logging, and cache invalidation. Without CDC, consumers must poll DynamoDB directly (expensive scans) or application code must manually fanout change events (coupling).
- AWS Services: Amazon DynamoDB (Streams), Amazon Kinesis Data Streams (for DynamoDB), AWS Lambda
- Architecture Decision:
  Choose the streaming model based on retention and fan-out requirements:
  - **DynamoDB Streams**: 24-hour retention, Lambda ESM integration, up to 2 concurrent Lambda consumers per shard. Cost: no additional charge beyond stream read operations.
  - **Kinesis Data Streams for DynamoDB**: Up to 365-day retention, multiple concurrent consumers, enhanced fan-out (2MB/s per shard per consumer), CloudWatch Contributor Insights. Cost: Kinesis Data Streams shard-hour pricing.
  Configure `StreamViewType: NEW_AND_OLD_IMAGES` for full CDC capability (required for audit logging and conflict detection in multi-source patterns).
- Verification:
  ```
  aws dynamodb describe-table --table-name MyTable \
    --query 'Table.StreamSpecification.StreamEnabled'
  # Expected: true
  ```
- Trade-offs: DynamoDB Streams have 24-hour retention — delayed consumer processing risks missing records. Kinesis Data Streams adds cost and complexity but removes retention constraints.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html

---

**Enable Deletion Protection on Production Tables**
- Pillar Alignment: Reliability
- Why: DynamoDB table deletion is an irreversible control-plane operation. Without deletion protection, a misconfigured IaC deployment, a runbook error, or an overly permissive IAM policy can permanently destroy a production table and all its data, even with PITR enabled (PITR cannot restore a deleted table without a pre-existing backup).
- AWS Services: Amazon DynamoDB
- Architecture Decision:
  Enable `DeletionProtectionEnabled: true` for all production tables at creation time. Enforce via AWS Config custom rule or Service Control Policy (SCP) denying `dynamodb:DeleteTable` on production resources without an explicit allow in a break-glass process.
  ```
  aws dynamodb update-table --table-name MyTable \
    --deletion-protection-enabled
  ```
- Verification:
  ```
  aws dynamodb describe-table --table-name MyTable \
    --query 'Table.DeletionProtectionEnabled'
  # Expected: true
  ```
- Trade-offs: Deletion protection must be explicitly disabled before legitimate table deletions (e.g., test environment cleanup). Adds a step to decommissioning runbooks.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/WorkingWithTables.Basics.html

---

### ⚠️ Architectural Decisions

**Decision: Capacity Mode Selection — On-Demand vs Provisioned**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | On-Demand | DynamoDB On-Demand Mode | Operational simplicity, cost predictability for irregular traffic | Per-request cost (~6-7x higher than provisioned at equivalent steady-state traffic) | Unpredictable traffic, new tables, dev/staging, bursty workloads, low QPS |
  | Provisioned + Auto Scaling | DynamoDB + Application Auto Scaling | Per-request cost at scale, predictable billing | Requires capacity forecasting, scaling lag on spikes, operational overhead | Steady high-throughput workloads (>10M requests/day), predictable traffic patterns |
  | Provisioned (Fixed) | DynamoDB Provisioned | Maximum cost predictability, highest compliance with cost budgets | Manual scaling, throttling risk on spikes, wasted capacity at off-peak | Regulated workloads needing fixed billing, batch-only tables with known throughput |

- Cost Profile: On-demand is approximately 6-7x more expensive per request than provisioned at equivalent constant traffic. Break-even point where provisioned becomes cheaper is roughly 50%+ utilization of provisioned capacity sustained throughout the billing period.
- Scaling Characteristics: On-demand scales instantly within partition limits; provisioned auto-scaling has a lag of 1-2 minutes and requires CloudWatch alarms to trigger.
- Operational Burden: On-demand requires zero capacity planning. Provisioned requires Application Auto Scaling configuration, target utilization tuning, and ongoing right-sizing reviews.
- Lock-in Assessment: Capacity mode can be switched between on-demand and provisioned (with a 24-hour cooldown after switching away from on-demand). No lock-in.
- Architect Instruction: "Ask what the table's expected traffic variability is and whether a 10-minute traffic spike at 10x normal load would cause acceptable user-facing latency — if not, on-demand or provisioned + pre-warmed capacity is required."
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/capacity-mode.html

---

**Decision: Single-Table Design vs Multi-Table Design**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Single-Table Design | DynamoDB (one table) | Query efficiency, atomic cross-entity operations, reduced management overhead, lower backup costs | Schema clarity, team onboarding curve, tooling support (ORMs don't understand it) | Well-defined access patterns, high-performance requirement, single-service ownership |
  | Multi-Table Design | DynamoDB (one table per entity type) | Schema clarity, independent table scaling, per-entity access control, team autonomy | Multiple round trips for cross-entity queries, higher management overhead | Microservices with independent teams per entity, entities with radically different access patterns, regulatory data isolation |

- Cost Profile: Single-table is modestly cheaper per equivalent workload (fewer tables = fewer backup streams, fewer GSI replications). At high scale, the difference is negligible compared to request cost.
- Scaling Characteristics: Single-table design can create hot partition risks if entity types have vastly different access patterns — careful key design required. Multi-table allows per-entity capacity scaling.
- Operational Burden: Single-table requires more sophisticated key design tooling and schema documentation. Multi-table requires managing permissions, backups, and monitoring for each table.
- Lock-in Assessment: Migrating between designs requires full data migration. Design decision is semi-permanent — choose based on long-term access-pattern stability.
- Architect Instruction: "Ask whether the team has enumerated all access patterns upfront, and whether they are comfortable with composite key overloading and GSI overloading patterns — if not, start with multi-table and consolidate later."
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html

---

**Decision: DynamoDB Streams vs Kinesis Data Streams for CDC**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | DynamoDB Streams | DynamoDB Streams + Lambda ESM | Simplicity, no additional cost | 24-hour retention, max 2 concurrent Lambda consumers per shard | Single Lambda consumer, real-time triggers, simple event-driven patterns |
  | Kinesis Data Streams for DynamoDB | Amazon Kinesis Data Streams | Retention (up to 365 days), unlimited consumers, enhanced fan-out | Additional Kinesis cost (shard-hour pricing), more complex setup | Multiple independent consumers (search index + audit + cache), analytics pipelines, >24h replay requirement |

- Cost Profile: DynamoDB Streams: additional charge only for stream read operations. Kinesis Data Streams: shard-hour cost + extended retention cost if enabled. For moderate tables, Kinesis adds $15-50/month per shard.
- Scaling Characteristics: Both scale with table write throughput. Kinesis enhanced fan-out provides 2 MB/s per shard per consumer — avoids consumer starvation when multiple consumers compete for the same shard.
- Operational Burden: DynamoDB Streams is simpler; Lambda ESM manages shard iteration automatically. Kinesis requires shard management, consumer group configuration, and potentially Kinesis Data Firehose for analytics.
- Lock-in Assessment: Both are AWS-proprietary CDC mechanisms. Switching between them requires updating all downstream consumers.
- Architect Instruction: "Ask how many independent downstream consumers need to process the same change events — if more than one (e.g., search index sync AND audit log AND cache invalidation), use Kinesis Data Streams."
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/kds.html

---

**Decision: DAX Caching vs Application-Level Caching vs No Cache**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | DAX (DynamoDB Accelerator) | Amazon DAX | Sub-millisecond reads, transparent API compatibility, RCU cost reduction | EC2-based cluster (not serverless), VPC-only, adds ~$50-500+/month baseline, no Lambda cold-start optimization | Hot-item read workloads, high-read low-write tables, leaderboards, session stores |
  | Application-Level Cache | ElastiCache (Redis/Valkey), local in-memory | Full cache control, TTL flexibility, multi-table caching | Cache invalidation complexity, separate infrastructure, consistency risk | Complex caching logic, multi-source caches, workloads needing Redis data structures |
  | No Cache | DynamoDB directly | Simplicity, always fresh data | Higher RCU cost, DynamoDB latency (ms vs µs) | Write-heavy tables, unique item access patterns, low traffic, strong consistency requirements |

- Cost Profile: DAX clusters start at ~$0.07/hour (dax.t3.small) for development. Production clusters (dax.r5.large, 3-node HA) run ~$0.50+/hour. Justified when RCU savings + latency improvement exceed cluster cost.
- Scaling Characteristics: DAX scales by adding nodes to the cluster. Lambda workloads in VPC using DAX still experience cold-start VPC ENI attachment latency.
- Operational Burden: DAX requires VPC placement, cluster management, node sizing, and monitoring. It is not serverless.
- Lock-in Assessment: DAX client SDK is DynamoDB-API-compatible. Removing DAX requires only endpoint swap.
- Architect Instruction: "Ask what percentage of reads target the same items repeatedly (cache hit rate estimate) — DAX only provides value when hot-item reads dominate the read pattern."
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.html

---

**Decision: Global Tables vs Single-Region with Cross-Region Backup**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Global Tables (Multi-Active) | DynamoDB Global Tables | Active-active multi-region, near-zero RPO, 99.999% SLA | Double/triple table cost per added region, eventual consistency between regions, last-writer-wins conflict model | Global user bases requiring local write latency, mission-critical applications, regulatory data residency in multiple regions |
  | Single-Region + AWS Backup Cross-Region | DynamoDB + AWS Backup | Simplicity, 1x table cost | Hours RPO for DR scenarios, no active-active reads/writes | Regional applications, non-critical DR requirements, cost-sensitive workloads |
  | Single-Region + Read Replicas via GSI | DynamoDB GSI (same region only) | Single-region query flexibility | No cross-region protection, GSIs are same-region only | Not a DR strategy — GSIs are same-region |

- Cost Profile: Global Tables billing = (base table cost) × (number of replicated regions) + replicated write cost. Adding one Global Tables replica roughly doubles DynamoDB cost for write-heavy tables.
- RTO/RPO: Global Tables: RPO ~seconds (asynchronous replication), RTO ~seconds (all replicas are active). Cross-region backup: RPO = backup frequency (hours), RTO = restore time (minutes to hours depending on table size).
- Operational Burden: Global Tables require conflict detection strategy in application logic. Application must implement region-aware routing (Route 53 latency routing or Geolocation routing).
- Lock-in Assessment: Global Tables is an AWS-proprietary multi-active replication. No equivalent in competitor NoSQL services without custom application-layer replication.
- Architect Instruction: "Ask what the business RPO/RTO requirements are and whether users in multiple geographic regions need to write to the database with local latency — if yes, Global Tables; if DR-only, cross-region backup is sufficient."
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GlobalTables.html

---

### 🚫 Anti-Patterns

**Anti-Pattern: Monotonic / Sequential Partition Keys**
- Risk Level: CRITICAL
- Why: DynamoDB hashes the Partition Key to assign items to physical partitions. Sequential values (timestamps, auto-incremented integers, ordered UUIDs) hash to clustered partition ranges, concentrating all new writes on a single "hot" partition. This triggers `ProvisionedThroughputExceededException` or on-demand throttling at the partition level (1,000 WCU/s per partition limit), regardless of total table capacity. Violates Performance Efficiency pillar.
- Instead:
  - Use high-cardinality identifiers (UUID v4, user ID, device ID) as Partition Keys.
  - For time-series access patterns, use `UserId` as Partition Key and ISO 8601 timestamp as Sort Key (distributes writes across user partitions, preserves time ordering per user).
  - For truly monotonic workloads (global event stream), use write sharding: append a random suffix `0` to `N-1` to the Partition Key and query all shards in parallel for reads.
  ```
  # Write sharding example: partition key = "events-{random 0-9}"
  # Read requires querying events-0 through events-9 in parallel
  ```
- Detection:
  ```
  # CloudWatch metric: ThrottledRequests, dimensioned by TableName + Operation
  aws cloudwatch get-metric-statistics \
    --namespace AWS/DynamoDB \
    --metric-name ThrottledRequests \
    --dimensions Name=TableName,Value=MyTable
  # Contributor Insights: Enable on table to identify hot partition keys
  ```
- Impact: Service throttling, latency degradation, cascading timeouts in dependent services, customer-facing errors.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html

---

**Anti-Pattern: Full Table Scans for Regular Application Queries**
- Risk Level: HIGH
- Why: DynamoDB Scan reads every item in the table (or every item in a GSI), consuming capacity proportional to table size regardless of the result set size. A Scan on a 100 GB table may consume millions of RCUs regardless of how many items match the filter. Violates Cost Optimization and Performance Efficiency pillars.
- Instead:
  - Design the access pattern into the table's key schema or a GSI at design time.
  - For search/filter requirements that cannot be served by key-based queries, integrate with Amazon OpenSearch Service via zero-ETL pipeline (DynamoDB Streams → Lambda → OpenSearch) and query OpenSearch for search operations.
  - For analytics on DynamoDB data, use DynamoDB export to S3 or zero-ETL to Redshift — run analytics against S3/Redshift, not production DynamoDB.
  - Use parallel Scan with `TotalSegments` and `Segment` parameters only for planned batch/migration operations, never for real-time application queries.
- Detection:
  ```
  # CloudWatch: Monitor SuccessfulRequestLatency for Scan operations
  # CloudWatch: Monitor ConsumedReadCapacityUnits — unexpectedly high consumption
  # AWS Cost Explorer: DynamoDB read cost spikes not correlated with user activity
  ```
- Impact: Cost overrun (Scan-heavy applications consume dramatically more RCUs than designed), latency spikes affecting user experience, capacity exhaustion impacting concurrent Query and GetItem operations.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-query-scan.html

---

**Anti-Pattern: Overly Large Items (Near or Exceeding 400 KB Limit)**
- Risk Level: HIGH
- Why: DynamoDB enforces a 400 KB hard limit per item. Large items consume WCUs proportional to size (1 WCU per 1 KB for writes, 1 RCU per 4 KB for strongly consistent reads). A 400 KB item consumes 400 WCUs per write — dramatically amplifying cost and degrading throughput. Violates Cost Optimization and Performance Efficiency pillars.
- Instead:
  - Store large binary or structured blobs in Amazon S3. Store the S3 object key as a DynamoDB attribute.
  - Decompose large items into parent-child relationships using the composite key pattern: `{EntityId}` as Partition Key, `PROFILE#`, `DETAILS#001`, `DETAILS#002`, etc. as Sort Keys.
  - Compress large attributes in the application layer before writing to DynamoDB (reduces both item size and WCU cost).
  - Use attribute pruning — write only required attributes, not entire object serializations.
- Detection:
  ```
  # CloudWatch: Elevated ConsumedWriteCapacityUnits not proportional to request count
  # DynamoDB Table Metrics: Average item size in ConsoleMetrics
  # AWS Cost Explorer: High WCU cost per request suggests large items
  ```
- Impact: WCU cost amplification (linear with item size), write throughput degradation, increased probability of TransactionConflicts on large transactional items.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-use-s3-too.html

---

**Anti-Pattern: Using Transactions Indiscriminately**
- Risk Level: MEDIUM
- Why: DynamoDB ACID transactions (TransactWriteItems, TransactGetItems) consume 2x the RCUs/WCUs of equivalent non-transactional operations. Each transaction is limited to 100 items or 4 MB total. Overuse of transactions for operations that don't require atomicity doubles capacity cost without benefit. Violates Cost Optimization pillar.
- Instead:
  - Use conditional writes (`PutItem`, `UpdateItem`, `DeleteItem` with `ConditionExpression`) for single-item atomicity — these do not have the 2x overhead.
  - Use optimistic locking (version attribute incremented with each update, `ConditionExpression: "version = :expected_version"`) for single-item concurrent update protection.
  - Reserve `TransactWriteItems` for multi-item operations requiring genuine atomicity (e.g., debit account A AND credit account B in the same transaction).
- Detection:
  ```
  # CloudWatch: TransactionConflict metric — high values indicate contention on hot items
  # Cost Explorer: DynamoDB write cost 2x higher than expected from request volume
  aws cloudwatch get-metric-statistics \
    --namespace AWS/DynamoDB --metric-name TransactionConflict
  ```
- Impact: 2x capacity cost for non-atomic operations using transactions, increased latency due to transaction coordination overhead, transaction conflict errors under high contention.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transactions.html

---

**Anti-Pattern: Missing Exponential Backoff on Throttled Requests**
- Risk Level: HIGH
- Why: DynamoDB returns `ProvisionedThroughputExceededException` (HTTP 400) when a request exceeds partition-level throughput. Retry without backoff creates a thundering herd: simultaneous retries compound the throttling, preventing recovery and causing cascading failures in upstream services. Violates Reliability pillar.
- Instead:
  - AWS SDKs include built-in retry logic with exponential backoff and jitter for DynamoDB operations by default. Verify SDK retry configuration is not overridden to zero retries.
  - For custom retry logic: implement exponential backoff with full jitter (not fixed delay) — `sleep = random(0, min(cap, base * 2^attempt))`.
  - Use the `RetryMode: adaptive` SDK setting for aggressive throttling environments — this adds client-side rate limiting that pre-emptively reduces request rate when throttling is detected.
  - Enable DynamoDB Contributor Insights to identify which Partition Keys are consistently throttled — indicating partition key design issues.
- Detection:
  ```
  aws cloudwatch get-metric-statistics \
    --namespace AWS/DynamoDB --metric-name ThrottledRequests \
    --dimensions Name=TableName,Value=MyTable Name=Operation,Value=PutItem
  ```
- Impact: Application availability degradation, cascading service failures, SLA breaches.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Programming.Errors.html

---

**Anti-Pattern: Hardcoded DynamoDB Table Names in Application Code**
- Risk Level: MEDIUM
- Why: Hardcoded table names prevent environment isolation (dev, staging, prod), make blue-green deployments impossible, and create environment-bleeding risk where a code deployment error causes production code to write to a staging table or vice versa. Violates Operational Excellence pillar.
- Instead:
  - Inject table names via environment variables in Lambda functions, ECS task definitions, or EC2 user data.
  - Use AWS Systems Manager Parameter Store or Secrets Manager to store table names per environment.
  - Reference table names via CloudFormation outputs or Terraform outputs injected at deployment time.
- Detection:
  - Code review: grep for hardcoded table name strings in application source.
  - AWS Config: Custom rule checking Lambda environment variable naming conventions.
- Impact: Environment cross-contamination, deployment failures, production data corruption from test workloads.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html

---

## Cloud-Native Design Patterns

**Single-Table Design with GSI Overloading**
- Category: Data
- Problem: Multiple entity types with different access patterns (e.g., Users, Orders, Products, Sessions) need to be queried efficiently without JOIN operations and without maintaining multiple tables.
- Solution on AWS:
  Store all entity types in a single DynamoDB table using generic Partition Key (`PK`) and Sort Key (`SK`) attribute names. Assign type-specific values using prefixes:
  - User: `PK=USER#userId`, `SK=PROFILE#`
  - User's Orders: `PK=USER#userId`, `SK=ORDER#orderId`
  - Order by status (GSI): `GSI1PK=STATUS#pending`, `GSI1SK=ORDER#orderId`
  GSI keys (`GSI1PK`, `GSI1SK`) are sparsely populated — only items relevant to each GSI access pattern include those attributes.
- Services Used:
  - DynamoDB Table (primary key design)
  - GSIs (up to 20; each serves distinct access patterns)
  - NoSQL Workbench (design and validation tooling)
- When to Apply: Well-defined, stable access patterns; single-service DynamoDB ownership; high-performance requirements; serverless Lambda backends.
- When NOT to Apply: Access patterns are unclear or rapidly evolving; multiple independent teams own different entity types; cross-entity access control requirements mandate table isolation.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Query Performance | All access patterns served by GetItem/Query | Requires upfront access pattern analysis |
  | Cost | Fewer tables, fewer GSIs at lower total cost | Error in key design requires data migration |
  | Operations | One table to backup, monitor, scale | Complex schema documentation required |
  | Atomicity | TransactWriteItems across entities in same table | 100-item/4MB transaction limit applies |

- Complements: DynamoDB Streams for CDC, DAX for read-heavy hot-item access
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html

---

**Write Sharding for High-Cardinality Hot Partitions**
- Category: Scalability
- Problem: A logical aggregate key (e.g., game leaderboard rank, global event counter, shared resource lock) must be written by many concurrent clients, but maps to a single DynamoDB partition key — creating a hot partition exceeding 1,000 WCU/s.
- Solution on AWS:
  Append a random suffix `0` to `N-1` to the partition key at write time. At read time, query all `N` shards in parallel and aggregate results in the application layer.
  ```
  # Write (random shard selection):
  pk = f"LEADERBOARD#{random.randint(0, N-1)}"
  
  # Read (parallel fan-out):
  results = parallel_query([f"LEADERBOARD#{i}" for i in range(N)])
  aggregated = merge_and_sort(results)
  ```
  Alternatively, use GSI write sharding: add a `shard` attribute (random 0–N-1) to items, create a GSI with `shard` as Partition Key and filter using multiple parallel queries.
- Services Used: Amazon DynamoDB (table + GSI), AWS Lambda (parallel fan-out), Amazon SQS (buffered write aggregation as alternative)
- When to Apply: Leaderboards, global counters, status flags queried/written by many concurrent users, fan-out read patterns on selective status attributes.
- When NOT to Apply: When read fan-out complexity (querying N shards and merging) is not acceptable. Consider DynamoDB Streams + Lambda aggregation to a separate summary table as a lower-read-cost alternative.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Write Throughput | N × 1,000 WCU/s aggregate partition capacity | Read fan-out requires N parallel queries |
  | Scalability | Linear throughput scaling with shard count | Application complexity for shard selection and merge |
  | Consistency | Distributed write relief | Aggregated read may be slightly stale within hot-shard TTL |

- Complements: Adaptive Capacity (provides burst relief during transition), DynamoDB Streams + Lambda aggregation (asynchronous summary pattern)
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-sharding.html

---

**DynamoDB Streams + Lambda Event-Driven Aggregation**
- Category: Data
- Problem: DynamoDB is optimized for key-based lookups, not aggregation queries (SUM, COUNT, GROUP BY). Building aggregate views (e.g., total orders per user, order count per status) directly in DynamoDB requires either expensive scans or pre-computed aggregations.
- Solution on AWS:
  Use DynamoDB Streams to capture item-level change events in near-real time. A Lambda function processes each stream record and updates a separate "aggregate" item in the same or different DynamoDB table using atomic increment operations (`ADD` expression).
  ```
  # Stream record: New ORDER#orderId item added with status=PENDING
  # Lambda: UpdateItem on SUMMARY#STATUS aggregate item
  # UpdateExpression: "ADD pending_count :1"
  # ConditionExpression: "attribute_exists(PK)"
  ```
- Services Used: Amazon DynamoDB (source + aggregate tables), DynamoDB Streams, AWS Lambda (ESM consumer), Amazon DynamoDB Transactions (for multi-item consistency in aggregation)
- When to Apply: Real-time dashboards, order status counts, user activity summaries, financial balance maintenance.
- When NOT to Apply: High-frequency writes where aggregate update cost (WCU per aggregate item) approaches Scan cost. Consider DynamoDB → Kinesis → Kinesis Data Analytics for high-throughput aggregate streaming.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Query Performance | Aggregate reads are O(1) GetItem | Aggregate item becomes a hot item (high WCU) |
  | Freshness | Near-real-time (seconds latency) | Lambda ESM batch window adds configurable latency |
  | Consistency | Atomic increments prevent double-counting | Lambda retry on failure may cause double-count without idempotency key |

- Complements: Conditional writes with version attributes for idempotency, DynamoDB Transactions for multi-aggregate atomicity
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-gsi-aggregation.html

---

**DynamoDB + OpenSearch Zero-ETL for Full-Text and Vector Search**
- Category: Data
- Problem: DynamoDB supports only key-based queries and simple attribute filters. Full-text search (product descriptions, article content), fuzzy matching, semantic/vector search, and faceted filtering are beyond DynamoDB's query capabilities.
- Solution on AWS:
  Enable Kinesis Data Streams for DynamoDB on the source table. Use an OpenSearch Ingestion pipeline (Amazon OpenSearch Ingestion) configured with DynamoDB as a source to automatically index documents in Amazon OpenSearch Service with zero custom ETL code. Query OpenSearch for search; query DynamoDB for operational key-based access.
- Services Used: Amazon DynamoDB (operational store), Amazon Kinesis Data Streams (CDC transport), Amazon OpenSearch Ingestion (managed pipeline), Amazon OpenSearch Service (search index)
- When to Apply: E-commerce product catalogs, content management systems, knowledge bases, applications requiring vector search for AI/ML recommendation features.
- When NOT to Apply: Pure key-value workloads with no search requirement. The additional cost and operational overhead of OpenSearch is only justified when DynamoDB's query capabilities are genuinely insufficient.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Search Capability | Full-text, faceted, vector search | OpenSearch Service adds $100-1000+/month |
  | Consistency | Near-real-time index sync | Search index lags DynamoDB by seconds |
  | Operational | Zero-ETL managed pipeline | OpenSearch cluster management overhead |

- Complements: DynamoDB Streams (alternative to KDS for simpler pipelines), Amazon Bedrock (vector embeddings for semantic search)
- Source: https://docs.aws.amazon.com/opensearch-service/latest/developerguide/configure-client-ddb.html

---

**Optimistic Locking with Version Numbers**
- Category: Resilience
- Problem: Concurrent writes to the same DynamoDB item from multiple clients can produce lost updates — client A reads an item, client B writes an update, client A writes its update overwriting client B's change.
- Solution on AWS:
  Add a `version` Number attribute to each item. Include a `ConditionExpression` on every write that verifies the version has not changed since the item was read. Increment the version atomically in the `UpdateExpression`.
  ```python
  table.update_item(
    Key={"PK": pk, "SK": sk},
    UpdateExpression="SET #data = :newData, version = version + :one",
    ConditionExpression="version = :expected_version",
    ExpressionAttributeValues={
      ":newData": new_data,
      ":expected_version": Decimal(current_version),
      ":one": Decimal(1)
    }
  )
  # On ConditionalCheckFailedException: re-read item and retry
  ```
- Services Used: Amazon DynamoDB (conditional expressions), AWS SDK (retry with ConditionalCheckFailedException handling)
- When to Apply: Shopping cart updates, seat/ticket reservation, inventory management, any shared mutable state with concurrent access.
- When NOT to Apply: Write-once, append-only patterns (event logs, audit trails) where concurrent write conflicts cannot occur.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Consistency | Prevents lost updates without 2x transaction cost | Requires application retry logic on conflict |
  | Throughput | Same WCU cost as non-conditional write | High-contention hot items cause high retry rates |
  | Correctness | Detects concurrent modification reliably | Retry loops must have bounds to prevent infinite loops |

- Complements: DynamoDB Transactions (for multi-item atomic updates that cannot be served by single-item conditional writes)
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BestPractices_ImplementingVersionControl.html

---

## Security Architecture

**Identity & Access Management**
- AWS Services:
  - AWS IAM: Policy-based authorization for all DynamoDB API calls
  - AWS IAM Access Analyzer: Detects unintended resource-based policy access
  - AWS STS: Temporary credentials for application roles (Lambda execution role, ECS task role)
  - DynamoDB Block Public Access (BPA): Prevents public resource-based policies at account/table level
- Architecture:
  Applications must never use long-lived AWS access keys to access DynamoDB. All compute (Lambda, ECS, EC2) uses IAM roles with DynamoDB permissions. Use `dynamodb:LeadingKeys` IAM condition to enforce row-level security — restricting users to reading/writing only their own items. Use `dynamodb:Attributes` condition for column-level access control in multi-tenant tables. Enable BPA at the account level to prevent accidental public access grants via resource-based policies.
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query"],
      "Resource": "arn:aws:dynamodb:*:*:table/UserData",
      "Condition": {
        "ForAllValues:StringEquals": {
          "dynamodb:LeadingKeys": ["${cognito-identity.amazonaws.com:sub}"]
        }
      }
    }]
  }
  ```
- Configuration Essentials:
  - Never use wildcard `*` for DynamoDB `Action` or `Resource` in production policies.
  - Use `aws:SourceVpce` condition to restrict DynamoDB access to requests originating from a specific VPC endpoint.
  - Enable IAM Access Analyzer on DynamoDB resource-based policies quarterly.
- Verification:
  ```
  # Check for overly permissive policies:
  aws iam get-policy --policy-arn <arn> | jq '.Policy.DefaultVersionId'
  # Use IAM Access Analyzer to generate policy recommendations
  aws accessanalyzer list-findings --analyzer-arn <arn>
  ```
- Compliance Alignment: SOC 2 CC6.1 (Logical Access Controls), PCI DSS Requirement 7 (Restrict Access), HIPAA § 164.312(a)(1) (Access Control)
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security-iam.html

---

**Network Security — VPC Endpoints**
- AWS Services:
  - AWS PrivateLink (Interface VPC Endpoint for DynamoDB): Private connectivity from VPC to DynamoDB without internet transit
  - VPC Gateway Endpoint for DynamoDB: Free, route-table-based private connectivity (S3 and DynamoDB only)
  - Security Groups + IAM `aws:SourceVpce` conditions: Defense-in-depth
- Architecture:
  Two VPC endpoint options for DynamoDB:
  - **Gateway Endpoint** (recommended for VPC resources): Free. Configures route table entries to route DynamoDB traffic through AWS backbone. Does not create an ENI.
  - **Interface Endpoint (PrivateLink)**: Required for on-premises connectivity via Direct Connect or VPN, cross-VPC access, and when DNS hostname is needed in private hosted zones. Costs $0.01/hour/AZ + data processing charges.
  For Lambda functions in a VPC, configure the VPC with a Gateway Endpoint for DynamoDB to avoid NAT Gateway charges on DynamoDB traffic.
- Configuration Essentials:
  - Gateway Endpoint policy: Restrict to specific DynamoDB table ARNs and specific IAM principals.
  - Add `aws:SourceVpce` condition to DynamoDB resource-based policies to enforce VPC-only access.
  - For on-premises DynamoDB access: use Interface Endpoint + Route 53 Resolver Inbound Endpoint.
- Verification:
  ```
  aws ec2 describe-vpc-endpoints \
    --filters Name=service-name,Values=com.amazonaws.us-east-1.dynamodb \
    --query 'VpcEndpoints[*].{Type:VpcEndpointType,State:State}'
  ```
- Compliance Alignment: PCI DSS Requirement 1 (Network Security Controls), HIPAA network protection controls
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/privatelink-interface-endpoints.html

---

**Data Security — Encryption Keys**
- AWS Services:
  - AWS KMS: Key management for DynamoDB encryption at rest
  - AWS Database Encryption SDK: Client-side encryption before writing to DynamoDB
  - AWS CloudTrail: KMS API call audit trail for CMK-encrypted tables
- Architecture:
  All DynamoDB data is encrypted at rest by default with AWS-owned keys. For regulated workloads, upgrade to Customer Managed Key (CMK):
  - KMS key policy restricts decrypt capability to the application IAM role.
  - CloudTrail logs every KMS API call against the CMK providing full audit trail.
  - KMS key rotation (automatic annual rotation) does not require re-encryption of DynamoDB data.
  For client-side encryption (e.g., HIPAA PHI fields that must be encrypted before leaving the application), use the AWS Database Encryption SDK — encrypts specified attributes locally before the DynamoDB SDK sends them.
- Configuration Essentials:
  - CMK key policy must include `kms:GenerateDataKey`, `kms:Decrypt` for DynamoDB service principal.
  - Enable KMS key deletion protection (7-30 day deletion waiting period).
  - Monitor `KMSDisabledException` CloudWatch events — CMK disabled = table inaccessible.
- Verification:
  ```
  aws dynamodb describe-table --table-name MyTable \
    --query 'Table.SSEDescription'
  # SSEType: "KMS", KMSMasterKeyArn: "arn:aws:kms:..." for CMK-encrypted tables
  ```
- Compliance Alignment: HIPAA § 164.312(a)(2)(iv) (Encryption), PCI DSS Requirement 3.5 (Key Management), GDPR Art. 32 (Security of Processing)
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/EncryptionAtRest.html

---

**Detection & Response — CloudWatch + Contributor Insights + CloudTrail**
- AWS Services:
  - Amazon CloudWatch: DynamoDB table and partition metrics
  - DynamoDB Contributor Insights: Identifies top partition keys by request volume and throttling frequency
  - AWS CloudTrail: API call audit log for all DynamoDB control-plane operations (CreateTable, DeleteTable, UpdateTable)
  - Amazon EventBridge: Alert routing for DynamoDB operational events
- Architecture:
  Three tiers of observability:
  1. **CloudTrail**: All DynamoDB management API calls logged automatically. Configure CloudTrail Lake or S3 destination with lifecycle policy for audit retention.
  2. **CloudWatch Alarms**: Alert on `ThrottledRequests > 0`, `SystemErrors > 0`, `ConsumedWriteCapacityUnits > 80% of provisioned`, `SuccessfulRequestLatency p99 > threshold`.
  3. **Contributor Insights**: Enable on table and all GSIs to identify hot partition keys. Outputs top-N most accessed and top-N throttled partition keys in real time.
  For security event detection: subscribe CloudTrail to GuardDuty for anomalous DynamoDB access pattern detection (unusual data exfiltration via Scan operations from unexpected principals).
- Configuration Essentials:
  - Enable Contributor Insights at table creation; not enabled by default.
  - CloudTrail: Enable data events for DynamoDB in addition to management events for full API audit.
- Verification:
  ```
  aws dynamodb describe-contributor-insights \
    --table-name MyTable
  # ContributorInsightsStatus: "ENABLED"
  ```
- Compliance Alignment: SOC 2 CC7.2 (System Monitoring), PCI DSS Requirement 10 (Logging), HIPAA § 164.312(b) (Audit Controls)
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/contributorinsights.html

---

## Operational Patterns

**Observability Stack**
- Operational Domain: Observability
- AWS Services:
  - Amazon CloudWatch (Metrics, Alarms, Dashboards): DynamoDB built-in metrics
  - DynamoDB Contributor Insights: Hot partition key identification
  - AWS CloudTrail: Control-plane audit logging
  - Amazon CloudWatch Logs Insights: Lambda stream processor log analysis
- Architecture:
  DynamoDB publishes metrics to CloudWatch at one-minute granularity for provisioned tables and on-demand tables. Critical metrics and alert thresholds:
  - `ConsumedReadCapacityUnits` / `ProvisionedReadCapacityUnits`: Alert at 80% sustained utilization for provisioned mode.
  - `ConsumedWriteCapacityUnits` / `ProvisionedWriteCapacityUnits`: Alert at 80% sustained utilization.
  - `ThrottledRequests`: Alert immediately on any throttling — zero tolerance for production tables.
  - `SystemErrors`: Alert immediately — indicates DynamoDB service-side errors.
  - `SuccessfulRequestLatency` (GetItem, Query, PutItem): Alarm on P99 > latency SLA.
  - `TransactionConflict`: Alert on sustained transaction conflicts — indicates hot-item contention.
  Build CloudWatch dashboards per table grouping latency percentiles, throttling, and capacity utilization. Enable Contributor Insights to surface hot partition keys before they cause user-facing impact.
- Cost Profile: Low — CloudWatch metrics included with DynamoDB. Contributor Insights: $0.02 per million requests analyzed. CloudTrail management events: included in first trail; data events add $0.10 per 100K events.
- Automation:
  - Automate: CloudWatch Alarms → SNS → PagerDuty/OpsGenie for ThrottledRequests and SystemErrors.
  - Automate: Lambda-based auto-remediation for provisioned capacity scaling on sustained throttling.
  - Manual: Contributor Insights analysis and partition key redesign decisions.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/monitoring.html

---

**Disaster Recovery Patterns**
- Operational Domain: DR
- RTO/RPO:

  | DR Pattern | RTO | RPO | Relative Cost | Complexity | Best For |
  |------------|-----|-----|---------------|------------|----------|
  | PITR Restore | Hours | Seconds (per-second granularity) | $ | Low | Accidental data corruption, single-table recovery |
  | On-Demand Backup via AWS Backup | Hours | Backup frequency | $ | Low | Long-term archival, regulatory compliance |
  | Cross-Region AWS Backup | Hours | Backup frequency | $$ | Low | Regional disaster recovery, secondary region restore |
  | Global Tables Active-Active | Seconds | Near-zero (seconds) | $$$$ | Medium | Mission-critical multi-region applications |

- AWS Services:
  - PITR: Built into DynamoDB, per-second granularity, 1-35 day window.
  - AWS Backup: Schedules, lifecycle policies, cross-account/cross-region copy, cold storage tiering.
  - Global Tables: Multi-active replication, integrated with AWS FIS for fault injection testing.
- Architecture:
  Baseline DR for all production tables: PITR enabled (35-day window) + AWS Backup daily snapshots with 90-day retention copied to a secondary region. For mission-critical tables: enable Global Tables to secondary region with Route 53 health-check-based failover.
  Restore procedure via PITR:
  ```
  aws dynamodb restore-table-to-point-in-time \
    --source-table-name ProductionTable \
    --target-table-name ProductionTable-restored-2026-05-25T10:00:00 \
    --restore-date-time 2026-05-25T10:00:00Z
  # Verify item counts post-restore before redirecting application traffic
  ```
- Cost Profile: PITR: ~$0.20/GB/month additional storage. AWS Backup cold storage: ~$0.01/GB/month. Global Tables: doubles DynamoDB cost per added replica region.
- Automation:
  - Automate: AWS Backup plan for schedule, retention, and cross-region copy.
  - Automate: Route 53 health checks for automated traffic failover with Global Tables.
  - Manual: Validate restore fidelity (item count comparison, spot-check queries), update application connection strings.
- Runbook Skeleton:
  1. **Detection**: CloudWatch alarm or user-reported data corruption.
  2. **Triage**: Identify affected time window using CloudTrail API logs and application logs.
  3. **Initiate Restore**: `aws dynamodb restore-table-to-point-in-time` to a new table at the last known good timestamp.
  4. **Validate**: Compare item counts, spot-check critical items, run application smoke tests against restored table.
  5. **Cutover**: Update Lambda env vars / application config to point to restored table name. Rename tables if needed.
  6. **Post-Mortem**: Root cause analysis of data corruption event. Update access patterns or add monitoring.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BackupRestore.html

---

**FinOps / Cost Optimization**
- Operational Domain: FinOps
- AWS Services:
  - DynamoDB On-Demand Mode: Pay-per-request for unpredictable workloads
  - DynamoDB Provisioned Mode + Application Auto Scaling: Cost-optimized for predictable workloads
  - AWS Cost Explorer (DynamoDB dimension): Per-table cost breakdown
  - DynamoDB S3 Export: Replace expensive Scans with S3-based analytics
- Architecture:
  Four levers for DynamoDB cost optimization:
  1. **Capacity Mode Right-Sizing**: Monitor on-demand tables monthly. If sustained traffic exceeds 50% of equivalent provisioned capacity cost, switch to provisioned with auto-scaling.
  2. **Item Size Reduction**: Profile item sizes. Every 1 KB reduction in average item size reduces WCU/RCU consumption proportionally. Compress large attributes, store binary blobs in S3.
  3. **GSI Pruning**: Each GSI independently consumes write capacity for every base table write. Audit GSIs — remove unused indexes. Project only needed attributes (`INCLUDE` or `KEYS_ONLY`) to reduce GSI item size.
  4. **Scan Elimination**: Replace full-table Scans with key-based Queries (access pattern redesign), DynamoDB S3 Export (for batch analytics), or zero-ETL to Redshift/OpenSearch.
  - Tag all DynamoDB tables with `Environment`, `Owner`, `Application`, `CostCenter` — AWS Cost Explorer filters on these dimensions.
  - Enable DynamoDB Reserved Capacity for Provisioned mode tables with 12+ months of stable throughput — provides 53% cost reduction for WCU/RCU vs on-demand pricing.
- Cost Profile: On-demand pricing (US-East-1): $1.25 per million WRUs, $0.25 per million RRUs. Provisioned: $0.00065/WCU-hour, $0.00013/RCU-hour. Storage: $0.25/GB-month. PITR backup: $0.20/GB-month.
- Automation:
  - Automate: AWS Cost Anomaly Detection with DynamoDB service monitor — alert on unexpected cost spikes.
  - Automate: Application Auto Scaling for provisioned tables based on CloudWatch target tracking.
  - Manual: Quarterly GSI utilization review, capacity mode re-evaluation, reserved capacity purchase decisions.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-understanding-billing.html

---

## Reference Architectures

**Serverless API Backend — DynamoDB + Lambda + API Gateway**
- Context: REST or GraphQL API backend for a web/mobile application requiring single-digit millisecond database response times, zero operational server management, and scale-to-zero cost model.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | API | Amazon API Gateway (REST or HTTP API) | Request routing, auth, throttling, WAF integration |
  | Compute | AWS Lambda | Stateless business logic, DynamoDB operations |
  | Data | Amazon DynamoDB (On-Demand) | Primary data store — single-table design |
  | Cache | Amazon DAX (optional) | Sub-millisecond reads for hot-item patterns |
  | Auth | Amazon Cognito User Pools + Authorizer | JWT-based user authentication |
  | Secrets | AWS Systems Manager Parameter Store | DynamoDB table name injection |
  | Observability | Amazon CloudWatch + X-Ray | Metrics, tracing, log correlation |
  | CDC | DynamoDB Streams + Lambda | Event-driven downstream processing |

- Architecture Diagram Description:
  Client → API Gateway (JWT auth via Cognito Authorizer) → Lambda function (reads table name from env var) → DynamoDB table (single-table design, on-demand mode). Lambda execution role has least-privilege IAM policy scoped to specific DynamoDB actions on specific table ARN. DynamoDB Streams triggers a separate Lambda for CDC events (search indexing, cache invalidation, audit logging). All Lambda functions in VPC with DynamoDB Gateway Endpoint — no NAT Gateway charges for DynamoDB traffic.
- Key Decisions:
  - On-demand mode: Default for new serverless APIs; switch to provisioned once traffic profile is understood.
  - Single-table design: Requires upfront access pattern analysis; enables atomic cross-entity operations.
  - DAX: Add only when profiling shows hot-item reads justify cluster cost.
  - VPC for Lambda: Required for DAX; optional for DynamoDB-only (use Gateway Endpoint if VPC-resident for other reasons).
- Scaling Path:
  - 0-100K requests/day: On-demand DynamoDB, Lambda managed concurrency, no DAX.
  - 100K-10M requests/day: Evaluate provisioned mode with auto-scaling; add DAX for hot items.
  - 10M+ requests/day: Reserved capacity for DynamoDB provisioned mode; Global Tables for multi-region.
- Cost Baseline: Low — purely pay-per-request at low traffic. DynamoDB on-demand dominates at scale; Lambda and API Gateway costs are secondary.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html

---

**Event-Driven Session Management**
- Context: Stateless application requiring fast, TTL-based session storage — user auth sessions, shopping carts, game state — with automatic expiry without application-side cleanup jobs.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Session Store | Amazon DynamoDB (On-Demand) | Session items with TTL attribute |
  | TTL | DynamoDB TTL | Automatic item deletion after expiry |
  | Cache | Amazon DAX (optional) | Sub-millisecond session reads |
  | Auth Token | Amazon Cognito / JWT | Session token generation |
  | Compute | AWS Lambda / ECS | Session read/write logic |

- Architecture Diagram Description:
  Application writes session item to DynamoDB with `ttl` attribute (Unix timestamp of expiry). DynamoDB TTL service scans for expired items and deletes them within 48 hours of expiry (TTL deletion is eventually consistent — application must validate session not expired on read). DAX caches session reads — TTL expiry items are removed from DAX cache on next cache miss. DynamoDB Streams (with `KEYS_ONLY` view) fires on TTL deletions — can trigger cleanup webhooks or audit logs.
- Key Decisions:
  - DynamoDB TTL vs application-managed expiry: DynamoDB TTL is eventually consistent (items may be readable for up to 48 hours past TTL). For strict security expiry, validate `ttl` attribute on every read in application code.
  - DAX: Recommended for session stores — session reads are highly repetitive (same session ID queried on every request).
- Scaling Path: DynamoDB TTL is fully managed and scales with table size. At very high session write rates, monitor partition distribution (session IDs should be high-cardinality to avoid hot partitions).
- Cost Baseline: Very low. DynamoDB TTL deletions are free (do not consume WCUs). Session items are typically small (<1 KB) — WCU cost per session write is minimal.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html

---

**Global Multi-Region Active-Active Application**
- Context: Application serving users in multiple geographic regions where both reads and writes must occur at local latency, with near-zero RPO/RTO requirements.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Data | DynamoDB Global Tables | Multi-active replication across regions |
  | Routing | Amazon Route 53 (Latency Routing + Health Checks) | Route users to nearest healthy region |
  | Compute | AWS Lambda (per region) | Region-local business logic |
  | API | Amazon API Gateway (per region) | Region-local API endpoint |
  | Observability | CloudWatch (per region) + CloudWatch Cross-Account Observability | Unified multi-region monitoring |
  | Conflict Handling | Application-level (last-writer-wins awareness) | Conflict resolution for concurrent cross-region writes |

- Architecture Diagram Description:
  Two or more AWS regions, each with identical application stack (API Gateway → Lambda → DynamoDB replica). Global Tables replicates item-level changes across all replicas asynchronously. Route 53 Latency Routing directs each user to the nearest healthy regional endpoint. Route 53 Health Checks monitor each region's API Gateway health endpoint; on health check failure, DNS TTL propagates region removal within 60 seconds. Application must handle eventual consistency for cross-region reads — avoid reading from a different region than the write region for latency-sensitive operations.
- Key Decisions:
  - Conflict resolution: Last-writer-wins based on item-level timestamps. Design application to minimize concurrent cross-region writes to the same item.
  - DynamoDB Streams + Global Tables: Each region's replica emits its own DynamoDB Streams — regional event consumers must deduplicate events or use global replica origin metadata.
- Scaling Path: Add Global Table replicas to new regions as needed — each replica is independently active immediately. Route 53 routing policies updated to include new regional endpoints.
- Cost Baseline: High — Global Tables roughly doubles/triples DynamoDB cost per replica region. Route 53 health checks add minimal cost. Justified only for globally distributed user bases or mission-critical RTO/RPO requirements.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GlobalTables.html

---

## Service Equivalence Map

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| **NoSQL — Key-Value / Document** | DynamoDB | Firestore / Bigtable | Cosmos DB | NoSQL Database |
| **In-Memory Cache for NoSQL** | DAX (DynamoDB-specific) | Memorystore | Azure Cache for Redis | OCI Cache |
| **CDC / Change Streams** | DynamoDB Streams / Kinesis Data Streams | Firestore Change Streams | Cosmos DB Change Feed | OCI Streaming |
| **Full-Text Search** | OpenSearch Service (via zero-ETL) | Firestore (limited) / Elastic on GCP | Cosmos DB integrated Search | OCI Search with OpenSearch |
| **NoSQL Design Tooling** | NoSQL Workbench | Firestore Emulator | Azure Cosmos DB Explorer | OCI Console / SDK |
| **Multi-Region Active-Active** | DynamoDB Global Tables | Spanner (relational, not key-value) | Cosmos DB multi-region writes | N/A — NoSQL single-region |

> **⚠️ Important**: DynamoDB's partition-key-based data model, single-digit millisecond SLA at scale, and Global Tables active-active multi-region replication have no direct architectural equivalent. Cosmos DB (Azure) is the closest functional peer with multi-model support and configurable consistency levels, but the data models, cost structures, and operational behaviors differ significantly.

---

## Provider Differentiators

**DynamoDB Global Tables (Multi-Active Replication)**
- Category: Data
- Unique Value: Fully managed, multi-active (not primary-replica) multi-region NoSQL replication. All replica regions accept reads and writes simultaneously. No manual failover, no primary election, no split-brain recovery. 99.999% availability SLA at the table level — a distinction from the 99.99% SLA of single-region tables.
- Architecture Impact: Eliminates the need for custom application-level replication logic for global data distribution. Enables low-latency writes from any region without routing through a primary. Dramatically simplifies multi-region DR architecture — all replicas are active by default.
- When to Leverage: Applications with globally distributed users requiring write-local access; financial systems requiring near-zero RPO/RTO; compliance requirements mandating multi-region data residency.
- Caveat: Last-writer-wins conflict model. Concurrent writes to the same item from different regions are resolved non-deterministically. Tables must have DynamoDB Streams enabled. Adding replicas doubles cost per region.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GlobalTables.html

---

**DynamoDB Accelerator (DAX)**
- Category: Data
- Unique Value: A purpose-built, DynamoDB-API-compatible in-memory cache that delivers microsecond read latency for DynamoDB. Unlike generic Redis/ElastiCache caching, DAX is fully integrated — it handles cache invalidation automatically for write-through operations and uses the same DynamoDB API, requiring no application code changes beyond endpoint substitution.
- Architecture Impact: Removes the cache-aside pattern complexity (separate read-from-cache / write-to-DB / invalidate-cache logic). Reduces DynamoDB RCU consumption for hot-item workloads by serving repeated reads from memory. Sub-millisecond latency enables new use cases (real-time leaderboards, gaming session state) where DynamoDB's millisecond latency was insufficient.
- When to Leverage: Read-heavy workloads with highly repetitive hot-item access (leaderboards, session stores, product catalog hot items, reference data). Not justified for write-heavy or uniquely-accessed-item workloads.
- Caveat: DAX runs on EC2 instances (not serverless) — minimum 3-node HA cluster recommended for production. VPC-resident only. Lambda functions using DAX must be in the same VPC (cold start latency impact). Eventually consistent reads from DAX cache may not reflect the absolute latest DynamoDB state.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.html

---

**DynamoDB Zero-ETL Integrations (Redshift, OpenSearch)**
- Category: Data
- Unique Value: DynamoDB supports native zero-ETL integration with Amazon Redshift and Amazon OpenSearch Ingestion pipelines — no custom Lambda ETL code, no schema mapping files, no managed Kafka connect clusters required. Changes in DynamoDB are automatically reflected in Redshift and OpenSearch with minimal latency using managed pipelines.
- Architecture Impact: Eliminates the DynamoDB → Lambda → Redshift/OpenSearch custom pipeline pattern. Reduces ETL maintenance burden from a managed service to a configuration. Enables DynamoDB operational data to be queried analytically (Redshift) or searched full-text (OpenSearch) with minimal operational overhead.
- When to Leverage: Analytics on DynamoDB operational data (sales dashboards, usage analytics), full-text or vector search on DynamoDB content (product descriptions, articles), ML feature extraction from operational data.
- Caveat: Zero-ETL integration is eventually consistent — Redshift and OpenSearch replicas lag DynamoDB by seconds to minutes. Redshift zero-ETL integration does not support all DynamoDB data types natively (complex nested structures require mapping). OpenSearch Ingestion pipeline requires additional configuration for vector embeddings.
- Source: https://docs.aws.amazon.com/redshift/latest/mgmt/zero-etl-using.html

---

**DynamoDB NoSQL Workbench**
- Category: Data
- Unique Value: AWS-provided free GUI design tool for DynamoDB data modeling, access pattern visualization, sample data generation, and live query development. Provides entity relationship diagram-style visualization mapped to DynamoDB's key schema — bridging the gap between relational design intuition and NoSQL key design requirements. Available on Windows, macOS, Linux.
- Architecture Impact: Enables architects to validate access-pattern coverage of key designs before table creation. Reduces costly schema redesigns post-production. Supports importing/exporting data models for team collaboration.
- When to Leverage: Every DynamoDB table design session. Especially valuable when onboarding teams unfamiliar with NoSQL access-pattern-first design.
- Caveat: NoSQL Workbench is a client application, not a cloud service — requires local installation. Data models in Workbench format are not directly executable IaC.
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.html

---

## Scenario Coverage

**Standard Case**: Multi-entity web/mobile application backend with mixed read/write traffic
- Approach:
  - Single-table design with composite primary keys (`PK` + `SK`) and 2-3 GSIs covering secondary access patterns.
  - On-demand capacity mode.
  - PITR enabled (35-day window) + deletion protection.
  - Lambda integration via IAM role with least-privilege DynamoDB policy.
  - DynamoDB Streams enabled for downstream event processing.
  - Encryption at rest with AWS-owned key (upgrade to CMK for regulated data).
  - VPC Gateway Endpoint if Lambda functions are VPC-resident.
- Key Decisions:
  1. Enumerate all access patterns before schema design — use NoSQL Workbench.
  2. Choose on-demand mode; re-evaluate after 30 days of traffic profiling.
  3. Determine if any patterns require strong consistency (adds 2x RCU cost) vs eventual consistency.

**Edge Case**: Ultra-high-throughput single-entity write workload (IoT telemetry, clickstream)
- Approach:
  - Time-series table design: Partition Key = `DeviceId`, Sort Key = `Timestamp` (ISO 8601). Prevents monotonic key anti-pattern at the device level.
  - For global aggregation (all devices), use write sharding: `SHARD#{random 0-99}` partition key for the aggregate table.
  - Kinesis Data Streams for DynamoDB (not DynamoDB Streams) for downstream fan-out to multiple consumers (analytics + alerting + archival).
  - Separate tables per time window (monthly) for time-series data to enable efficient archival and scan avoidance on historical data.
  - Provisioned capacity with Application Auto Scaling after traffic baseline established.

**Anti-Pattern Case**: Team requests DynamoDB as a relational database replacement, with JOINs across 15 normalized entity tables
- Clarification:
  1. Ask the team to enumerate all application access patterns explicitly before proceeding.
  2. Validate that the access patterns genuinely require cross-entity JOIN semantics, or whether denormalization into a single-table design can serve all patterns with GetItem/Query.
  3. If genuine multi-entity relational semantics are required (complex ad-hoc queries, foreign key enforcement, aggregate functions), DynamoDB is the wrong choice — evaluate Amazon Aurora Serverless v2 (relational, serverless) or Amazon RDS Multi-AZ instead.
  4. Flag that 15 separate normalized DynamoDB tables will require 15 separate IAM policies, backup strategies, and capacity configurations — this is the multi-table anti-pattern at maximum complexity.
  5. Do NOT proceed with "just use PartiQL — it looks like SQL" justification. PartiQL maps directly to DynamoDB's underlying access model; it does not enable server-side JOINs or cross-table queries.
