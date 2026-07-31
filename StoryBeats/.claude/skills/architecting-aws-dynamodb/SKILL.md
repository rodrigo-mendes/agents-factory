---
name: architecting-aws-dynamodb
description: "Designs and evaluates Amazon DynamoDB data architectures following AWS Well-Architected best practices for NoSQL key-value and document workloads. Use when architecting, reviewing, or troubleshooting DynamoDB table design, access-pattern modeling, capacity planning, security controls, index strategy, or global-table configuration."
---

## Function
Specialist in NoSQL data architecture for Amazon DynamoDB — AWS managed key-value and document database, documentation pinned to 2026-07-31.

## Version Context

**Technology**: Amazon DynamoDB
**Target Edition**: Current service documentation (Developer Guide, retrieved 2026-07-31)
**Service Type**: Fully managed, continuously released (no semantic version; pinned to doc state)
**Support Status**: GA — Active
**Currency Threshold**: Re-verify after 2027-07-31

**Service constants as of 2026-07-31**:
- Default capacity mode: **on-demand** (recommended for most workloads)
- Encryption at rest: always enabled (AWS-owned key by default; upgradeable)
- Global tables: MREC (eventual) and MRSC (strong, default quota 400 tables)
- Max GSIs per table: **20** (treat any source referencing 5-GSI limit as stale)
- Deprecated model: "Global Tables 2017.11.29 (Version 2017)" — do not reference

⚠️ **Version Lock**: This skill targets the 2026-07-31 DynamoDB documentation state. Reject blog
posts, Stack Overflow answers, or docs referencing the deprecated 2017 global-tables model or a
5-GSI-per-table limit as stale misinformation.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 8 mandatory patterns: access-pattern modeling, partition-key uniformity, item size, encryption, IAM, PITR, VPC endpoints, retries/idempotency
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 5 architectural crossroads: capacity mode, global-table consistency, read consistency/caching, index type, change propagation
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 7 anti-patterns with ❌/✅ code: Scan on hot paths, hot keys, large blobs, wildcard IAM, no PITR, relational modeling, public access
- **[Integration Patterns](./blueprints/integration-patterns.md)** — DynamoDB ↔ S3, Lambda/Streams, DAX, KMS, IAM fine-grained
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 test scenarios: OLTP API, cross-region MRSC, relational lift-and-shift trap
- **[Verification Loop](#verification-loop)** — AWS CLI health-check commands
- **[Quick Reference](#quick-reference)** — Critical limits at a glance
- **[External Resources](#external-resources)** — Official AWS documentation

---

## Blueprints & Guardrails

Domain complexity: **Complex** (security-critical, multi-layer, compliance-relevant).
Pattern counts: 8 Always-Do / 5 Ask-First / 7 Never-Do.
Full details with rationale and verification commands in the linked blueprints.

### ✅ Always Do

See [Always Do Patterns](./blueprints/always-do-patterns.md) for complete rationale and verification.

- **M1 — Access-pattern-first (single-table) data modeling** — Enumerate every read/write access pattern before designing keys; every hot path must map to `GetItem`/`Query`, never `Scan`. DynamoDB has no joins and no query planner — modeling relationally is the leading cause of cost and latency failure.
- **M2 — Uniform partition-key design (3,000 RCU/s + 1,000 WCU/s per-partition ceiling)** — Choose high-cardinality keys; apply write sharding (`key#0..N` suffix) for unavoidable hot writes; enable Contributor Insights to detect sustained key skew.
- **M3 — Keep items small; offload large payloads to Amazon S3** — Hard 400 KB item limit; store blobs in S3 and keep the S3 object key plus queryable metadata in the DynamoDB item.
- **M4 — Use the right KMS key tier + enforce TLS in transit** — AWS-owned key (default) has no audit trail; use a customer-managed KMS key for regulated or sensitive data. Deny `aws:SecureTransport=false` in all resource-based IAM policies.
- **M5 — Least-privilege IAM with `dynamodb:LeadingKeys` and `dynamodb:Attributes` condition keys** — Wildcard `dynamodb:*` on `Resource: *` is forbidden; scope permissions to specific table ARNs and use condition keys for per-tenant row- and column-level isolation.
- **M6 — Enable PITR on every production table; define RTO/RPO** — Continuous backups (up to 35-day window) protect against accidental deletes and corruption. Complement with on-demand snapshots or AWS Backup for long-term or compliance retention.
- **M7 — Private connectivity via VPC Gateway Endpoint for DynamoDB** — Routes DynamoDB traffic through the AWS network, off the public internet; scope endpoint policy to specific table ARNs.
- **M8 — Exponential-backoff retries (SDK default) + idempotent conditional writes** — Throttling is expected at scale; use `attribute_not_exists()` or a `version` attribute for idempotency; `TransactWriteItems` for multi-item atomicity (costs 2x capacity).

### ⚠️ Ask First

See [Ask First Decisions](./blueprints/ask-first-decisions.md) for full option tables and cost profiles.

- **D1 — Capacity mode** — On-demand (default; spiky/unpredictable) vs Provisioned+auto-scaling (steady, forecastable) vs Provisioned+reserved (baseline-heavy, 1–3 yr commitment). Ask: "Is traffic predictable enough to forecast, and is there a long-lived steady baseline?"
- **D2 — Replication scope** — Single-Region multi-AZ vs MREC global tables (active-active, eventual, last-writer-wins) vs MRSC global tables (cross-region strong consistency, 400-table default quota). Ask: "What are RTO/RPO? Is cross-region strong consistency a hard requirement?"
- **D3 — Read consistency and caching** — Eventually consistent (default, half the RCU cost) vs strongly consistent (2x cost, unavailable on GSIs) vs DAX (microsecond, eventual-only). Ask: "Which reads truly require read-after-write? Are there hot-key read spikes that justify DAX?"
- **D4 — Index type: LSI vs GSI (and projection type)** — LSI (strong consistency, must define at table creation, 5 max, 10 GB item-collection cap) vs GSI (eventual only, add anytime, 20 max). Projection: `KEYS_ONLY`/`INCLUDE` vs `ALL`. Ask: "Does this access pattern need strong consistency? Can it emerge later? What attributes must the query return?"
- **D5 — Change propagation: DynamoDB Streams vs Kinesis Data Streams** — Streams (native, ordered, 24h retention, 2 readers/shard; 1 for global tables) vs Kinesis (longer retention, high fan-out, more infra). Ask: "Do consumers need > 24h retention or more than 2 concurrent readers?"

### 🚫 Never Do

See [Never Do Patterns](./blueprints/never-do-patterns.md) for ❌ wrong / ✅ correct code side-by-side.

- **A1 — Scan on hot read paths** `[HIGH]` — `Scan` reads every item proportional to table size; causes table-wide throttling and cost blow-up. Model access patterns so every hot path uses `Query`.
- **A2 — Low-cardinality or hot partition key** `[CRITICAL]` — Keys like `status=ACTIVE` concentrate traffic; a partition is hard-capped at 3,000/1,000 RCU/WCU per second regardless of table-level throughput. Adaptive capacity does not save sustained skew.
- **A3 — Storing large blobs directly as item attributes** `[HIGH]` — Violates the 400 KB hard limit and inflates capacity consumption per read/write. Offload to S3 and store the pointer in DynamoDB.
- **A4 — Wildcard IAM: `dynamodb:*` on `Resource: *`** `[CRITICAL]` — Grants full read/write/drop of every table in the account and region. Scope to specific table ARNs and condition keys.
- **A5 — No PITR and no backup on production tables** `[HIGH]` — A bad deploy or accidental delete becomes permanent data loss. Enable PITR; define and test restore RTO/RPO.
- **A6 — Relational modeling: many normalized tables + client-side joins** `[HIGH]` — DynamoDB has no joins; N round-trips per request multiplies latency and cost. Use single-table design with overloaded `PK`/`SK`.
- **A7 — Public data-plane access without VPC endpoint or TLS enforcement** `[HIGH]` — Traffic over the public internet plus no `aws:SecureTransport` Deny exposes data in transit.

---

## Integration Patterns

See [Integration Patterns](./blueprints/integration-patterns.md) for full setup code and CLI verification.

- **DynamoDB ↔ Amazon S3** — Blob offload: write large objects to S3; store the S3 key plus queryable metadata in the DynamoDB item (respects 400 KB limit, keeps reads fast).
- **DynamoDB ↔ AWS Lambda (via Streams)** — Event-driven CDC: DynamoDB Streams trigger Lambda for materialized views, notifications, and cross-service fan-out (24h retention, 2 readers/shard).
- **DynamoDB ↔ DAX** — Read cache: API-compatible drop-in; microsecond latency for eventually-consistent hot reads. Does not accelerate strongly-consistent reads or writes.
- **DynamoDB ↔ AWS KMS** — Customer-managed key for encryption at rest; adds per-request KMS cost and an availability dependency on the KMS key policy.
- **DynamoDB ↔ IAM fine-grained access** — `dynamodb:LeadingKeys` restricts an identity to its own partition-key rows; `dynamodb:Attributes` restricts visible columns — the canonical multi-tenant isolation pattern.

---

## Verification Loop

Run after any DynamoDB table design or configuration change.

### 1. Confirm key schema, GSIs, and encryption
```bash
aws dynamodb describe-table --table-name <TABLE_NAME> \
  --query "Table.{KeySchema:KeySchema,GSIs:GlobalSecondaryIndexes,SSE:SSEDescription}"
# Expected: KeySchema defined; SSEDescription.Status = ENABLED
```

### 2. Confirm PITR enabled
```bash
aws dynamodb describe-continuous-backups --table-name <TABLE_NAME> \
  --query "ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus"
# Expected: "ENABLED"
```

### 3. Enable Contributor Insights (hot-key detection)
```bash
aws dynamodb update-contributor-insights --table-name <TABLE_NAME> \
  --contributor-insights-action ENABLE
# Expected: ContributorInsightsStatus: ENABLING → ENABLED
```

### 4. Verify CloudWatch throttling alarm exists
```bash
aws cloudwatch describe-alarms --alarm-name-prefix "<TABLE_NAME>"
# Expected: at least one alarm on ThrottledRequests
```

**Troubleshooting**:
- `ThrottledRequests` spiking → check Contributor Insights for hot keys (A2); review capacity mode (D1)
- `ProvisionedThroughputExceededException` on a single key → apply write sharding (M2)
- `ValidationException: Item size exceeds 400 KB` → validate before `PutItem`; offload blob to S3 (M3)
- `ConditionalCheckFailedException` → retry with updated version attribute (M8)

---

## Quick Reference

**Essential CLI commands**:
```bash
# Describe table
aws dynamodb describe-table --table-name <TABLE_NAME>

# Query (preferred) — use key-condition, not scan
aws dynamodb query --table-name <T> \
  --key-condition-expression "PK = :pk" \
  --expression-attribute-values '{":pk":{"S":"CUSTOMER#123"}}'

# Enable PITR
aws dynamodb update-continuous-backups --table-name <T> \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

# Enable Contributor Insights
aws dynamodb update-contributor-insights --table-name <T> \
  --contributor-insights-action ENABLE
```

**Critical limits (pinned 2026-07-31; re-verify after 2027-07-31)**:

| Limit | Value |
|-------|-------|
| Max item size | 400 KB |
| Per-partition read ceiling | 3,000 RCU/s |
| Per-partition write ceiling | 1,000 WCU/s |
| 1 RCU | 1 strong read/s ≤ 4 KB (or 2 eventual reads) |
| 1 WCU | 1 write/s ≤ 1 KB |
| Transactional operations | 2x capacity cost |
| GSIs per table (default) | 20 |
| LSIs per table (at create only) | 5 |
| LSI item-collection cap | 10 GB per partition key |
| PITR retention window | up to 35 days |
| Stream record retention | 24 hours |
| Stream readers per shard | 2 (single-Region) / 1 (global tables) |
| Per-table throughput (default) | 40,000 RCU + 40,000 WCU |
| MRSC global tables (default quota) | 400 |

---

## Blueprints Directory Structure

```
.claude/skills/architecting-aws-dynamodb/
├── SKILL.md                              <- This file (index + summaries)
└── blueprints/
    ├── always-do-patterns.md             <- M1-M8 with full rationale and verification
    ├── ask-first-decisions.md            <- D1-D5 decision matrices and option tables
    ├── never-do-patterns.md              <- A1-A7 with wrong / correct code examples
    ├── integration-patterns.md           <- DynamoDB with S3, Lambda, DAX, KMS, IAM
    └── evaluation-scenarios.md           <- 3 test scenarios: canonical, edge, misuse
```

**Extract to blueprints when**: code examples exceed 30 lines, multiple pattern variations exist, or a full integration context (imports, config, IAM policy) is needed.

---

## External Resources

### Official AWS DynamoDB Documentation (all retrieved 2026-07-31)
- [Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/) — Primary reference
- [Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [NoSQL Design for DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html)
- [DynamoDB Well-Architected Lens](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-wal.html)
- [Partition Key Design](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html)
- [Secondary Indexes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-indexes.html)
- [Read/Write Capacity Mode](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadWriteCapacityMode.html)
- [Global Tables (MREC/MRSC)](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html)
- [Security Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security-best-practices.html)
- [PITR Recovery](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-pitr-recovery.html)
- [DAX Prescriptive Guidance](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/dax-prescriptive-guidance.html)
- [Service Quotas](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html)
- [DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html)

### Research Input
- [research_cloud_AWS_DynamoDB_2026-07.md](../../../docs/research_cloud_AWS_DynamoDB_2026-07.md) — Source bibliography and guardrail derivations (retrieved 2026-07-31)
