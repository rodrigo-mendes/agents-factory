---
name: designing-dynamodb-nosql
description: "Designs and validates DynamoDB NoSQL schemas, capacity models, and security controls for AWS cloud-native applications. Use when architecting DynamoDB tables, modeling access patterns, selecting capacity mode, configuring global tables, securing sensitive data workloads, or choosing between DynamoDB Streams and Kinesis for CDC pipelines."
---

## Function

Specialist in DynamoDB NoSQL data architecture for AWS cloud-native and serverless applications — covering single-table design, partition key modeling, capacity planning, global tables, security guardrails, and event-driven CDC patterns.

## Version Context

**Technology**: Amazon DynamoDB
**Target edition**: AWS DynamoDB 2026
**Research date**: 2026-08-28
**Currency threshold**: 2027-08-28
**Support status**: Active (fully managed, no version pinning required)

**Significant changes 2024–2026**:
- **Nov 2024**: On-demand pricing cut −50% (throughput), up to −67% (global tables replicated writes). On-demand is now the recommended default capacity mode.
- **Nov 2024**: Warm Throughput GA — pre-warm tables before traffic spikes; charge is irreversible downward.
- **Nov 2024**: ABAC GA for tables and indexes (Streams ABAC GA Aug 2026).
- **Mar 2024**: PrivateLink interface endpoint GA; resource-based policies for cross-account access GA.
- **Jun 2025**: Multi-Region Strong Consistency (MRSC) GA — zero-RPO active-active global tables (3-Region topology only).
- **Jan 2025**: Configurable PITR retention (1–35 days) GA.
- **Jan 2026**: AWS FIS MRSC fault-injection testing GA.
- **Feb 2026**: Multi-account global tables GA; Resource Control Policies (RCPs) support GA.
- **Aug 2026**: Vector search GA — DynamoDB as combined operational + vector store (up to 5 indexes per table, 4,096 dimensions, TopK 100).

**Deprecated / superseded**:
- Global Tables Legacy version 2017.11.29 — superseded by 2019.11.21 (Current). Never use for new tables.

⚠️ **CRITICAL — Agent Warning**:
This skill targets AWS DynamoDB 2026 with the November 2024 pricing and June 2025 MRSC changes.
Reject capacity-mode guidance that treats provisioned as the default — on-demand is the 2024+ default.
Do not apply MRSC topology to existing tables — MRSC requires starting from an empty table.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Three-tier patterns (✅⚠️🚫)
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases (canonical, edge, misuse)
- **[Integration Patterns](#integration-patterns)** — DynamoDB with Lambda, EventBridge, Kinesis, Bedrock
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands
- **[Quick Reference](#quick-reference)** — Hard limits and essential AWS CLI commands
- **[External Resources](#external-resources)** — Official dated documentation

---

## Blueprints & Guardrails

### ✅ Always Do

**1. Access-Pattern-First Schema Design** — Enumerate all read/write access patterns (cardinality, frequency, item size) before creating any table. Use NoSQL Workbench to model and validate against every pattern. A DynamoDB schema cannot be fixed with ad-hoc queries after the fact — there is no query planner equivalent.
> Verification: A Scan-heavy table in production almost always indicates an access pattern missed during design.

**2. High-Cardinality Partition Key** — Choose partition keys with high cardinality and uniform access distribution (`user_id`, `order_id`, `device_id+timestamp`). Enable CloudWatch Contributor Insights from day one to detect hot keys. For inherently low-cardinality keys (`status`, `region`, `type`), apply write sharding with a random or calculated suffix.
> Hard limit: 3,000 RCU / 1,000 WCU per partition per second — adaptive capacity cannot exceed this ceiling.

**3. Encryption at Rest — CMK for Regulated Data** — DynamoDB encrypts all data at rest by default (AES-256, cannot be disabled). The decision is which key type: AWS owned key (default, no cost, no ops) vs customer managed key (CMK). Use CMK for HIPAA, PCI DSS, or FedRAMP High workloads — CMK enables key rotation, granular key policies, and CloudTrail KMS audit.
> Note: Sort key boundary values are stored in plaintext in table metadata regardless of key choice.

**4. Enable CloudTrail Data-Event Logging at Provisioning** — Management events are logged automatically; item-level data-plane events (GetItem, PutItem, Query, Scan) are **off by default and opt-in per table**. This is an invisible compliance gap. Enable at table provisioning for all regulated or sensitive tables — not retroactively. Use advanced event selectors filtered by table ARN to control cost.
> Consequence of omission: No item-level audit trail. Fails PCI DSS, HIPAA, SOX compliance audits.

**5. VPC Endpoint for All DynamoDB Traffic** — Without a VPC endpoint, EC2/Lambda-to-DynamoDB traffic traverses the public internet. Deploy a gateway endpoint (free) for all in-VPC workloads. For on-premises or cross-account paths, deploy a PrivateLink interface endpoint (GA March 2024). Enforce with IAM condition `aws:sourceVpce` on the table resource-based policy to deny non-endpoint traffic.

**6. Enable PITR on All Production Tables** — Point-in-Time Recovery (PITR) provides continuous backup at per-second granularity. Configure retention window (1–35 days, GA January 2025) to match compliance requirements. Enable via IaC at table creation — restoring a PITR-enabled table creates a new table (does not overwrite). On deletion, DynamoDB automatically creates a 35-day system snapshot.

**7. Enable Contributor Insights (Throttle-Only Mode) on Production Tables** — Throttle-only mode incurs near-zero cost during normal operation (charges only on throttle events). Creates CloudWatch alarms on ThrottledRequests > 0 sustained for 5 minutes. For on-demand tables, monitor `OnDemandMaxReadRequestUnits` / `OnDemandMaxWriteRequestUnits` metrics as cost guardrails.

### ⚠️ Ask First

**1. Capacity Mode: On-Demand vs Provisioned** — On-demand is the 2024+ default and recommended choice. Ask: *"Can this workload's P99 read/write rate be forecasted reliably 6 months out?"* If yes and average utilization is above ~35%, provisioned + reserved capacity (up to 77% savings over 3 years) may reduce cost. Break-even is ~35% average utilization.

| Option | Optimizes | Sacrifices | Use When |
|--------|-----------|------------|----------|
| On-demand | Simplicity; spiky traffic | Cost at sustained high load | Unknown/unpredictable load; new tables; dev/test |
| Provisioned + Auto Scaling | Cost at steady load; reserved capacity eligibility | 2-min scale-up lag; ops overhead | Forecastable P99 over 6 months; >35% avg utilization |

**2. Global Table Consistency: MREC vs MRSC** — Ask: *"What is the acceptable RPO?"* RPO=0 mandates MRSC, which carries hard topology constraints.

| Option | RPO | Constraints | Use When |
|--------|-----|-------------|----------|
| MREC (default) | >0 (typically <1s) | Any-Region writes; supports TTL/LSI/transactions | Most global apps; active-active with eventual reconciliation |
| MRSC (Jun 2025 GA) | = 0 | Exactly 3 Regions; must start from empty table; no TTL/LSI/transactions | Zero data-loss regulated workloads; financial ledgers; inventory |

> MRSC topology is immutable. Migration to MREC requires rebuilding the table.

**3. Read Acceleration: DAX vs ElastiCache vs No Cache** — Ask: *"What is the expected cache hit rate?"* DAX is only cost-effective above 90% cache hit rate. DAX cannot serve strongly consistent reads.

| Option | Use When |
|--------|----------|
| DAX | Read-heavy; hot keys; >90% cache hit rate; sub-millisecond latency required; eventually consistent reads only |
| ElastiCache | Shared cache across services; complex eviction policies; session store |
| No cache | Write-heavy; strong consistency required; sporadic access; simplest default |

**4. Secondary Index Strategy: GSI vs LSI vs Write Sharding** — Ask: *"Is the query partition key the same as the base table?"* If yes, evaluate LSI (creation window constraint). If the partition key differs, GSI is required. If the partition key has low cardinality, apply write sharding.

| Option | Consistency | Created | Size Limit | Throughput |
|--------|-------------|---------|------------|------------|
| GSI | Eventually consistent only | Any time | None | Independent (own RCU/WCU) |
| LSI | Strongly consistent supported | Table creation only | 10 GB per PK | Shared with base table |
| Write sharding | N/A | Schema design | None | Distributed across N shards |

**5. CDC Consumer: DynamoDB Streams vs Kinesis Data Streams** — Ask: *"How many independent consumers need this stream?"* More than 2 consumers mandates Kinesis Data Streams.

| Option | Retention | Consumers/Shard | Use When |
|--------|-----------|-----------------|----------|
| DynamoDB Streams | 24 hours | 2 max | Single Lambda processor; simple fan-out ≤2 consumers |
| Kinesis Data Streams | Up to 1 year | 5+ | Multiple consumers; long retention; Flink/Firehose analytics |

### 🚫 Never Do

**1. Low-Cardinality Partition Key (Hot Partition)**
```
# 🚫 WRONG — 5 status values = max 5,000 WCU/sec total ceiling
partition_key = "STATUS"  # values: PENDING, ACTIVE, CLOSED, ...

# ✅ CORRECT — scatter by high-cardinality key; query status via GSI or filter
partition_key = "order_id"  # UUID; add status as a GSI partition key if needed
# For inherently low-cardinality keys, apply write sharding:
partition_key = f"STATUS#{random.randint(1, 200)}"  # then scatter-query all shards
```
> Impact: Partial outage — items on the hot partition return `ProvisionedThroughputExceededException` regardless of total table capacity. Adaptive capacity cannot exceed 3,000 RCU / 1,000 WCU per partition.

**2. Scan on Production Tables**
```
# 🚫 WRONG — reads every item; RCU cost proportional to total table size
response = table.scan(FilterExpression=Attr('status').eq('PENDING'))

# ✅ CORRECT — model a GSI with status as partition key at design time
response = table.query(
    IndexName='status-index',
    KeyConditionExpression=Key('status').eq('PENDING')
)
# For ad-hoc analytics: export to S3 + Athena, or use zero-ETL to Redshift
```
> Impact: Cost overrun; read throttling competing with production traffic.

**3. DAX for Strongly Consistent Read Workloads**
```
# 🚫 WRONG — ConsistentRead=True requests bypass DAX cache entirely
response = dax_client.get_item(TableName='orders', Key=key, ConsistentRead=True)
# DAX does NOT cache this — you pay for the DAX cluster AND the DynamoDB RCU with zero latency benefit.

# ✅ CORRECT — read directly from DynamoDB when strong consistency is required
response = dynamodb_client.get_item(TableName='orders', Key=key, ConsistentRead=True)
```
> Impact: Unnecessary EC2 cost for DAX cluster; zero latency improvement for consistent reads.

**4. Missing CloudTrail Data-Event Logging on Regulated Tables** — Data events are off by default. A regulated table without data-event logging has no item-level audit trail.
```
# ✅ CORRECT — enable at provisioning via IaC (Terraform example)
resource "aws_cloudtrail" "dynamodb_data_events" {
  event_selector {
    read_write_type           = "All"
    include_management_events = false
    data_resource {
      type   = "AWS::DynamoDB::Table"
      values = [aws_dynamodb_table.regulated.arn]
    }
  }
}
```
> Impact: Compliance failure — PCI DSS, HIPAA, SOX require item-level access evidence.

**5. Sensitive Data (PII/PHI) in Primary Key Values** — Primary key values appear in CloudTrail logs, DescribeTable responses, and DynamoDB internal routing metadata. They cannot be encrypted.
```
# 🚫 WRONG
pk = "USER#john.doe@company.com"  # email in PK
pk = "SSN#123-45-6789"

# ✅ CORRECT — use opaque identifiers; encrypt sensitive attributes via AWS Database Encryption SDK
pk = f"USER#{user_uuid}"  # UUID only
# Sensitive attributes encrypted client-side before PutItem
```
> Impact: PII/PHI exposed in logs and metadata; GDPR, HIPAA data-breach risk.

**6. Bypassing DAX and Writing Directly to DynamoDB** — Direct DynamoDB writes do not invalidate the DAX item cache. Subsequent reads through DAX return the stale cached value until TTL expires (default 5 min).
```
# 🚫 WRONG — mixed write path creates silent inconsistency
dynamodb_client.put_item(...)  # bypasses DAX

# ✅ CORRECT — all reads and writes through DAX when DAX is deployed
dax_client.put_item(...)
```
> Impact: Stale data served to users; silent data integrity bugs.

**7. Using Global Tables Legacy Version (2017.11.29)** — Publishes 2 stream records per write (vs 1), does not synchronize TTL, and is the superseded version. MRSC requires 2019.11.21.
```
# ✅ CORRECT — always specify Current version for new global tables
aws dynamodb create-table \
  --billing-mode PAY_PER_REQUEST \
  # ... (2019.11.21 is the default when using the current API; verify DescribeTable)

# Detect legacy: DescribeTable → GlobalTableVersion = "2017.11.29" → migrate
```
> Impact: Higher stream processing cost; TTL divergence across replicas; blocks MRSC upgrade path.

---

## Integration Patterns

- **DynamoDB + Lambda (Streams CDC)** — Enable Streams with `NEW_AND_OLD_IMAGES`. One Lambda function per shard. Use `ParallelizationFactor` (up to 10) for parallel per-shard processing while preserving per-item ordering. Hard limit: 2 concurrent consumers per shard — add EventBridge/SNS for fan-out beyond 2.
- **DynamoDB + Kinesis (Multi-Consumer CDC)** — Enable Kinesis Data Streams on the table for >2 consumers, >24h retention, or Apache Flink analytics. Kinesis may produce occasional duplicates (use idempotency tokens).
- **DynamoDB + Amazon Bedrock (Vector Search, Aug 2026 GA)** — Create up to 5 vector indexes per table (max 4,096 dimensions). Store Bedrock-generated embeddings as item attributes. Query via `SearchVectors` API with ANN search and up to 18 inline attribute filters. Limit: 600 GB base-table size without allowlisting; TopK max 100.
- **DynamoDB + Cognito (FGAC Multi-Tenant)** — Attach IAM condition `ForAllValues:StringEquals` on `dynamodb:LeadingKeys` with substitution `${cognito-identity.amazonaws.com:sub}`. Explicitly Deny `Scan` — Scan cannot be constrained by LeadingKeys.
- **DynamoDB + EventBridge (Event-Driven Decoupling)** — Lambda Streams consumer publishes to EventBridge for multi-subscriber fan-out. Decouples producers from consumers beyond the 2-shard consumer limit.

**Common problems**:
- **ThrottledRequests with low total utilization** → Hot partition key. Enable Contributor Insights to identify the key. Apply write sharding.
- **DAX returning stale data** → Mixed write path (some writes bypassing DAX). Route all writes through DAX.
- **MRSC write latency spike** → Expected — MRSC writes are synchronous cross-Region. Verify this is acceptable vs MREC RPO<1s.

---

## Verification Loop

Execute after provisioning or schema changes:

### 1. Verify Table Configuration
```bash
aws dynamodb describe-table --table-name <TABLE_NAME> \
  --query 'Table.{BillingMode:BillingModeSummary.BillingMode,SSE:SSEDescription.SSEType,StreamSpec:StreamSpecification,PITR:RestoreSummary}'
# Expected: BillingMode=PAY_PER_REQUEST (or PROVISIONED), SSEType present, PITR enabled
```

### 2. Verify PITR is Enabled
```bash
aws dynamodb describe-continuous-backups --table-name <TABLE_NAME> \
  --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus'
# Expected: "ENABLED"
```

### 3. Verify VPC Endpoint Exists
```bash
aws ec2 describe-vpc-endpoints \
  --filters "Name=service-name,Values=com.amazonaws.<REGION>.dynamodb" \
  --query 'VpcEndpoints[*].{State:State,Type:VpcEndpointType}'
# Expected: State=available, Type=Gateway (or Interface for PrivateLink)
```

### 4. Verify Contributor Insights
```bash
aws dynamodb describe-contributor-insights --table-name <TABLE_NAME> \
  --query 'ContributorInsightsStatus'
# Expected: "ENABLED"
```

### 5. Check for Hot Partitions (CloudWatch)
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB --metric-name ThrottledRequests \
  --dimensions Name=TableName,Value=<TABLE_NAME> \
  --start-time $(date -u -d '1 hour ago' +%FT%TZ) --end-time $(date -u +%FT%TZ) \
  --period 300 --statistics Sum
# Expected: Sum=0. Any throttling warrants Contributor Insights hot-key investigation.
```

**Troubleshooting**:
- `ProvisionedThroughputExceededException` on specific items → Hot partition. Redesign key or apply write sharding.
- `ResourceNotFoundException` on Streams consumer → StreamViewType may be NONE. Enable with `UPDATE_STREAM_SPECIFICATION`.
- MRSC `ValidationException` on table creation → Ensure starting from empty table; check Region set compatibility (US, EU, or AP — cannot span sets).

---

## Quick Reference

**Essential AWS CLI commands**:
```bash
# Create on-demand table with PITR and Streams
aws dynamodb create-table --table-name <NAME> \
  --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S \
  --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES

# Enable PITR
aws dynamodb update-continuous-backups --table-name <NAME> \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

# Enable Contributor Insights
aws dynamodb update-contributor-insights --table-name <NAME> \
  --contributor-insights-action ENABLE
```

**Hard limits**:

| Resource | Limit | Notes |
|----------|-------|-------|
| Per-partition read throughput | 3,000 RCU/sec | Hard ceiling; adaptive capacity cannot exceed |
| Per-partition write throughput | 1,000 WCU/sec | Hard ceiling |
| Item size | 400 KB | Includes attribute names and values |
| Transaction | 100 items / 4 MB per call | 2× capacity cost |
| GSIs per table | 20 (default) | Raiseable via Service Quotas |
| LSIs per table | 5 | Created at table creation only; 10 GB per PK value |
| DynamoDB Streams consumers/shard | 2 | Use Kinesis for >2 consumers |
| PITR retention | 1–35 days | Configurable GA January 2025 |
| Vector indexes per table | 5 | GA August 2026; max 4,096 dimensions; TopK 100 |
| On-demand default quota | 40,000 RU/WU per second | Raiseable via Service Quotas |
| Vector search base-table size | 600 GB | Without explicit allowlisting |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/designing-dynamodb-nosql/
├── SKILL.md                              ← This file (summary + guardrails)
└── blueprints/
    └── evaluation-scenarios.md           ← 6 test scenarios for skill-evaluator
```

---

## External Resources

### Official Documentation (AWS, 2026-08-28)
- [DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/) — Primary reference
- [Best Practices: NoSQL Design](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html) — Access-pattern-first methodology
- [Best Practices: Partition Key Design](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html) — Cardinality and write sharding
- [Capacity Modes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/capacity-mode.html) — On-demand vs provisioned
- [Global Tables MRSC](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html) — Zero-RPO topology (Jun 2025 GA)
- [Encryption at Rest](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/EncryptionAtRest.html) — KMS key types
- [Fine-Grained Access Control](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html) — LeadingKeys FGAC
- [CloudTrail Data Events](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/logging-using-cloudtrail.html) — Opt-in audit logging
- [VPC Endpoints / Network Isolation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/network-isolation.html) — Gateway + PrivateLink
- [PITR](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery_Howitworks.html) — Continuous backup; configurable retention
- [Contributor Insights](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/contributorinsights_HowItWorks.html) — Hot-key detection

### What's New (dated)
- [On-Demand Price Reduction (Nov 2024)](https://aws.amazon.com/blogs/database/new-amazon-dynamodb-lowers-pricing-for-on-demand-throughput-and-global-tables/)
- [MRSC GA (Jun 2025)](https://aws.amazon.com/about-aws/whats-new/2025/06/amazon-dynamo-db-global-tables-multi-region-strong-consistency-generally-available/)
- [Vector Search GA (Aug 2026)](https://aws.amazon.com/about-aws/whats-new/2026/08/amazon-dynamodb-vector-search/)
