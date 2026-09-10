# Evaluation Scenarios — designing-dynamodb-nosql

6 test cases for `/evaluating-skill-scenarios designing-dynamodb-nosql`.

---

## Scenario 1 — Canonical: Single-Table Schema for a Multi-Tenant SaaS App

```json
{
  "skills": ["designing-dynamodb-nosql"],
  "query": "Design the DynamoDB schema for a multi-tenant SaaS application. Users own documents, comments, and tags. Access patterns: (1) get all documents for a user, (2) get a specific document by ID, (3) get all comments for a document sorted by timestamp, (4) list all documents with a given tag across all users.",
  "expected_behavior": [
    "Asks for or enumerates all access patterns before proposing any schema",
    "Proposes composite primary key (pk = USER#<user_id>, sk = DOC#<doc_id>) for user-scoped patterns",
    "Models comments with sk = COMMENT#<ISO8601_timestamp>#<uuid> for range query on pattern 3",
    "Proposes a GSI (e.g., gsi1pk = TAG#<tag>, gsi1sk = DOC#<doc_id>) for pattern 4",
    "Uses opaque key prefixes (USER#, DOC#, COMMENT#, TAG#) — no PII in key values",
    "Recommends on-demand capacity mode as the default for a new workload",
    "Recommends enabling PITR and CloudTrail data events at provisioning"
  ]
}
```

---

## Scenario 2 — Canonical: Choosing Global Table Topology for a Financial Ledger

```json
{
  "skills": ["designing-dynamodb-nosql"],
  "query": "We need a global DynamoDB table for a financial transaction ledger that must serve reads and writes from US-East, EU-West, and AP-Southeast. Our compliance team says RPO must be exactly zero. What global table configuration should we use?",
  "expected_behavior": [
    "Identifies RPO=0 as the deterministic trigger for MRSC (not MREC)",
    "States MRSC GA June 2025 and its topology constraints explicitly: exactly 3 Regions, must start from empty table, no TTL / no LSIs / no transactions",
    "Confirms US + EU + AP spans two Region sets — flags this as a hard MRSC constraint (MRSC available Region sets: US, EU, AP cannot be mixed)",
    "Asks the architect to verify all 3 Regions are within a single supported MRSC Region set before proceeding",
    "Contrasts with MREC: RPO typically <1s, no topology constraints — if RPO<1s is acceptable, MREC avoids the constraints",
    "Does NOT recommend MRSC without flagging the empty-table start requirement and Region-set constraint"
  ]
}
```

---

## Scenario 3 — Canonical: Capacity Mode Selection for a Predictable E-Commerce Workload

```json
{
  "skills": ["designing-dynamodb-nosql"],
  "query": "Our e-commerce orders table currently processes 8,000 WCU and 24,000 RCU at sustained peak (>70% of operating hours), with a very predictable daily curve. We're on on-demand today. Should we switch to provisioned?",
  "expected_behavior": [
    "Identifies that average utilization >35% is the break-even threshold for provisioned vs on-demand",
    "Confirms >70% utilization at sustained peak is well above break-even — provisioned is likely cost-optimal",
    "Asks 'Can this workload's P99 read/write rate be forecasted reliably 6 months out?' before recommending the switch",
    "Mentions provisioned + reserved capacity savings (up to 77% over 3 years) for fully steady workloads",
    "Notes the 2-minute auto-scaling lag for provisioned — recommends maintaining burst buffer or pre-warming",
    "Does NOT recommend provisioned without confirming the forecasting question"
  ]
}
```

---

## Scenario 4 — Edge Case: MRSC with Existing Table and Conflicting Requirements

```json
{
  "skills": ["designing-dynamodb-nosql"],
  "query": "We have an existing DynamoDB global table (2019.11.21, MREC, US-East + EU-West) with TTL enabled and active Lambda triggers. The architect wants to upgrade it to MRSC for RPO=0. How do we do the migration?",
  "expected_behavior": [
    "States clearly that MRSC cannot be applied to an existing table — migration requires building a new empty table from scratch",
    "Lists MRSC hard constraints that conflict with current setup: no TTL support, incompatible with existing replication topology",
    "Proposes a migration path: (1) provision new empty MRSC table in a compatible 3-Region set, (2) migrate data, (3) switch Lambda triggers, (4) decommission old table",
    "Flags that Lambda cross-account Streams may be needed if Lambda functions are in different accounts",
    "Asks architect to confirm all 3 target Regions are within a single MRSC Region set before proceeding",
    "Does NOT suggest an in-place MREC → MRSC upgrade path — that does not exist"
  ]
}
```

---

## Scenario 5 — Edge Case: DynamoDB Streams Fan-Out Beyond 2 Consumers

```json
{
  "skills": ["designing-dynamodb-nosql"],
  "query": "We have a DynamoDB Streams-triggered Lambda function processing order events. Now we need to add a second Lambda for analytics and a third Lambda for fraud detection. Can we just add more Lambda triggers?",
  "expected_behavior": [
    "Flags the hard limit: DynamoDB Streams supports only 2 concurrent consumers per shard",
    "Explains that adding a third direct Lambda trigger will cause throttling / missed events",
    "Recommends fan-out pattern: first Lambda publishes to EventBridge or SNS, downstream Lambdas subscribe",
    "Alternatively recommends migrating to Kinesis Data Streams for DynamoDB when >2 direct consumers are needed (supports 5+ consumers per shard)",
    "Notes Kinesis Data Streams tradeoff: occasional duplicates (use idempotency tokens), more complex setup vs DynamoDB Streams exactly-once"
  ]
}
```

---

## Scenario 6 — Misuse: Architect Proposes SSN as Partition Key for a Patient Record Table

```json
{
  "skills": ["designing-dynamodb-nosql"],
  "query": "Our team wants to use the patient's Social Security Number as the DynamoDB partition key for the patient records table since it's unique and high-cardinality. Is that a good design?",
  "expected_behavior": [
    "Flags this as a critical anti-pattern: PII/PHI in primary key values",
    "Explains why: primary key values appear in CloudTrail logs, DescribeTable responses, and DynamoDB internal metadata — they cannot be encrypted",
    "States the compliance impact: HIPAA PHI exposure in logs is a data-breach risk; GDPR data minimization violation",
    "Recommends using an opaque UUID as the partition key (pk = PATIENT#<uuid>)",
    "Recommends storing SSN as an item attribute encrypted via the AWS Database Encryption SDK before PutItem",
    "Does NOT endorse SSN as partition key even with the high-cardinality justification",
    "Notes that enabling CloudTrail data-event logging (mandatory for HIPAA) would expose SSNs in all item-level log entries if used as a key"
  ]
}
```
