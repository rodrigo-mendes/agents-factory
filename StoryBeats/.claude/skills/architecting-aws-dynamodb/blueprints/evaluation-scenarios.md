# Evaluation Scenarios — architecting-aws-dynamodb

> Back to [SKILL.md](../SKILL.md)

Three scenarios that verify the skill activates correctly across canonical, edge, and misuse cases.

---

## Scenario 1 — Canonical: Single-Table OLTP API Design

```json
{
  "skills": ["architecting-aws-dynamodb"],
  "query": "We are building a serverless e-commerce API on AWS Lambda + API Gateway. The database will hold customers, orders, and order line items. Expected load is 5,000 writes/s at peak, unpredictable spikes, and access patterns include: (1) get all orders for a customer, (2) get order details with line items, (3) get a single order by order ID. Design the DynamoDB table.",
  "expected_behavior": [
    "Applies M1: enumerates the three access patterns before proposing a key schema",
    "Proposes a single-table design with overloaded PK/SK (e.g., PK=CUSTOMER#<id>, SK=ORDER#<id>) and co-location of customer + orders under one partition key",
    "Recommends on-demand capacity mode (D1) as default for spiky/unpredictable traffic",
    "Includes M6: instructs to enable PITR immediately after table creation",
    "Includes M5: recommends scoping Lambda IAM role to specific table ARN with dynamodb:LeadingKeys if multi-tenant",
    "Includes M7: recommends VPC Gateway Endpoint for Lambda-to-DynamoDB traffic",
    "Provides the CLI verification loop: describe-table, describe-continuous-backups, update-contributor-insights",
    "Does NOT suggest Scan for any of the three access patterns"
  ]
}
```

**Evaluation criteria**:
- Access-pattern-first thinking is explicit and precedes key schema design
- Single-table design with item-collection co-location is the primary recommendation, not three separate tables
- All 8 mandatory patterns (M1-M8) are addressed or referenced
- Verification Loop commands are correct AWS CLI syntax

---

## Scenario 2 — Edge Case: Cross-Region Strong Consistency (MRSC Global Table)

```json
{
  "skills": ["architecting-aws-dynamodb"],
  "query": "Our financial-services application stores account balances. We have data-sovereignty requirements that primary data must reside in EU-WEST-1, but the US-EAST-1 region must also be able to read and write balances with strong consistency guarantees — no stale reads allowed across regions. We also need the encryption to be auditable. What DynamoDB architecture do we use?",
  "expected_behavior": [
    "Surfaces D2 as a decision point: distinguishes MREC (eventual, not suitable here) from MRSC (strong, appropriate) global tables",
    "Recommends MRSC global tables explicitly and flags the default-quota constraint (400 MRSC tables per account)",
    "Warns that MRSC multiplies write cost and adds cross-region write latency",
    "Applies M4: recommends a customer-managed KMS key (not AWS-owned) because auditable encryption is required; notes CMK key policy and CloudTrail visibility",
    "Applies M5: recommends fine-grained IAM scoped per account/region",
    "Asks clarifying questions: Is the 400-table quota sufficient? Has the architect approved the replicated write cost? What is the RTO/RPO target for a full regional failure?",
    "Does NOT recommend MREC as sufficient when the requirement is cross-region strong consistency"
  ]
}
```

**Evaluation criteria**:
- Correctly distinguishes MRSC from MREC without conflating them
- CMK encryption is tied to the "auditable" requirement, not just default
- The 400-table MRSC quota is surfaced proactively
- At least one D2 clarifying question is asked before prescribing the architecture

---

## Scenario 3 — Misuse / Anti-Pattern Trap: Relational Lift-and-Shift

```json
{
  "skills": ["architecting-aws-dynamodb"],
  "query": "We want to migrate our PostgreSQL database to DynamoDB. The schema has 15 normalized tables with many-to-many relationships (Users, Roles, UserRoles, Products, Orders, OrderItems, Inventory, Suppliers, ...). Our analytics team runs complex ad-hoc JOIN queries across multiple tables daily. Can you help us model this in DynamoDB?",
  "expected_behavior": [
    "Immediately flags A6: a normalized multi-table schema with client-side joins is the canonical DynamoDB anti-pattern",
    "Asks for the complete list of application access patterns before proceeding with any modeling",
    "Raises a service-fit concern: the presence of complex ad-hoc JOIN queries for analytics is a strong signal that DynamoDB is the wrong service for the analytics use case",
    "Suggests a hybrid: DynamoDB for the OLTP/operational access patterns (if they can be enumerated and are key-value/document shaped); Amazon Athena + S3, Amazon Redshift, or Amazon Aurora for ad-hoc analytics",
    "Does NOT propose modeling 15 normalized tables in DynamoDB and joining them in application code",
    "Does NOT proceed with a full DynamoDB schema without first knowing the access patterns",
    "If the architect insists on DynamoDB only, flags A1 (Scan for ad-hoc queries) and A6 explicitly with blast radius"
  ]
}
```

**Evaluation criteria**:
- The skill refuses to lift-and-shift a relational schema without access-pattern enumeration (M1)
- A6 anti-pattern is explicitly named and explained
- The analytics use case is correctly identified as a service-fit concern, not just a DynamoDB modeling challenge
- At least one alternative service is suggested for the analytics layer
- No DynamoDB schema is produced until access patterns are provided
