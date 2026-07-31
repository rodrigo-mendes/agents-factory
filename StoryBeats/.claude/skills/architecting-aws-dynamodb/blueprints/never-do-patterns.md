# Never Do Patterns — Amazon DynamoDB

> Source: AWS DynamoDB Developer Guide, retrieved 2026-07-31.
> Back to [SKILL.md](../SKILL.md)

Each anti-pattern shows the wrong approach, the correct alternative, and the detection method.

---

## A1 — Scan on Hot Read Paths `[HIGH RISK]`

**Why prohibited**: `Scan` reads every item in the table and consumes capacity proportional to
table size, regardless of how many results are returned. A `Scan` on a 100 GB table with a
filter that matches 1 item still consumes capacity for the entire 100 GB.

**Blast Radius**: Table-wide throttling affecting all concurrent users; cascading latency spike;
cost overrun proportional to table size.

```python
# WRONG: Scan with FilterExpression on a hot path
response = table.scan(
    FilterExpression=Attr("customerId").eq("CUSTOMER#123")
)
# Reads EVERY item in the table, then filters — catastrophic at scale
```

```python
# CORRECT: Query on an access pattern designed for this lookup
# (customerId is the GSI partition key, or part of the base-table PK)
response = table.query(
    IndexName="GSI-CustomerIndex",
    KeyConditionExpression=Key("GSI1PK").eq("CUSTOMER#123")
)
# Reads only the customer's items — O(result set), not O(table size)
```

**Detection**: CloudWatch `ConsumedReadCapacityUnits` spikes; Contributor Insights showing
full-table read patterns; code review (`grep -r "\.scan(" src/`).

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-query-scan.html (2026-07-31)

---

## A2 — Low-Cardinality or Hot Partition Key `[CRITICAL]`

**Why prohibited**: Every DynamoDB partition is hard-capped at **3,000 RCU/s and 1,000 WCU/s**.
Concentrating traffic on one or a few partition-key values throttles those keys regardless of
total table provisioning. Adaptive capacity mitigates transient skew but cannot overcome sustained
hot-partition traffic.

**Blast Radius**: All requests to the hot partition key are throttled; service degradation or
outage for the affected entity/feature; cascading failures in dependent services.

```python
# WRONG: status field as partition key — only 2–3 distinct values for a high-write table
table.put_item(Item={
    "PK": "ACTIVE",          # hot key: all active orders share one partition
    "SK": order_id,
    "total": 99.99
})
```

```python
# CORRECT: high-cardinality key — each order gets its own partition
table.put_item(Item={
    "PK": f"ORDER#{order_id}",   # millions of distinct values
    "SK": "METADATA",
    "status": "ACTIVE",           # status is an attribute, not the partition key
    "total": 99.99
})

# For known hot writes (e.g., a global event counter), apply write sharding:
SHARD_COUNT = 10
shard = hash(order_id) % SHARD_COUNT
table.put_item(Item={
    "PK": f"COUNTER#orders#{shard}",   # spread across 10 partitions
    "SK": "COUNT",
    "value": 1
})
```

**Detection**: Contributor Insights "most accessed keys" dashboard; CloudWatch `ThrottledRequests`
with ample provisioned/on-demand headroom remaining at the table level.

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html (2026-07-31)

---

## A3 — Storing Large Blobs Directly as Item Attributes `[HIGH RISK]`

**Why prohibited**: The DynamoDB item size hard limit is **400 KB** (enforced at the service
layer — write is rejected). Large items also inflate every read/write's capacity unit consumption
by rounding up to the next 4 KB (reads) or 1 KB (writes) block.

**Blast Radius**: Write failures at the 400 KB boundary; runaway RCU/WCU cost for borderline
large items; latency increase as SDK serializes and transmits large payloads.

```python
# WRONG: storing a 2 MB PDF as a base64 attribute
with open("contract.pdf", "rb") as f:
    pdf_bytes = f.read()  # 2 MB

table.put_item(Item={
    "PK": "CONTRACT#456",
    "SK": "METADATA",
    "pdf_content": pdf_bytes  # REJECTED: ValidationException — item size exceeds 400 KB
})
```

```python
# CORRECT: upload to S3, store only the pointer and queryable metadata in DynamoDB
import boto3

s3 = boto3.client("s3")
table = boto3.resource("dynamodb").Table("Documents")

s3_key = f"contracts/456/contract.pdf"
s3.put_object(Bucket="my-docs-bucket", Key=s3_key, Body=pdf_bytes)

table.put_item(Item={
    "PK": "CONTRACT#456",
    "SK": "METADATA",
    "s3_bucket": "my-docs-bucket",   # pointer to the blob
    "s3_key": s3_key,
    "file_size_bytes": len(pdf_bytes),
    "content_type": "application/pdf",
    "uploaded_at": "2026-07-31T10:00:00Z"
    # item is now < 1 KB
})
```

**Detection**: Application-side pre-write size check; CloudWatch `UserErrors` metric spiking
(validation exceptions surface here).

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-use-s3-too.html (2026-07-31)

---

## A4 — Wildcard IAM Permissions `[CRITICAL]`

**Why prohibited**: `dynamodb:*` on `Resource: *` grants full data-plane AND control-plane access
to every table in the account and region — including `DeleteTable`, `CreateTable`, and
`CreateBackup`. This violates least-privilege and is a single-point-of-compromise for data breach.

**Blast Radius**: Full read/write/delete of every table in the account; ability to drop tables
and delete backups; compliance violation; potential for complete data destruction.

```json
// WRONG: wildcard action and resource — never attach to application roles
{
  "Effect": "Allow",
  "Action": "dynamodb:*",
  "Resource": "*"
}
```

```json
// CORRECT: scoped to specific table, specific actions, with tenant condition
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetItem",
    "dynamodb:PutItem",
    "dynamodb:UpdateItem",
    "dynamodb:DeleteItem",
    "dynamodb:Query"
  ],
  "Resource": [
    "arn:aws:dynamodb:us-east-1:123456789012:table/ApplicationDB",
    "arn:aws:dynamodb:us-east-1:123456789012:table/ApplicationDB/index/*"
  ],
  "Condition": {
    "ForAllValues:StringEquals": {
      "dynamodb:LeadingKeys": ["${aws:PrincipalTag/tenantId}"]
    }
  }
}
```

**Detection**: IAM Access Analyzer; AWS Config rule `iam-policy-no-statements-with-admin-access`;
periodic policy audit (`aws iam list-policies --scope Local`).

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security-best-practices.html (2026-07-31)

---

## A5 — No PITR and No Backup on Production Tables `[HIGH RISK]`

**Why prohibited**: Without PITR, a bad deployment that overwrites items, an accidental
`DeleteItem` loop, or silent data corruption is permanently and completely unrecoverable.
PITR takes seconds to enable and provides a 35-day continuous restore window.

**Blast Radius**: Permanent data loss; SLA/RTO breach; compliance violation; potential
irreversible business impact.

```bash
# WRONG: creating a production table with PITR disabled (the default)
aws dynamodb create-table \
  --table-name ProductionOrders \
  --attribute-definitions ... \
  --key-schema ...
# PITR is OFF by default — this table has zero recovery capability
```

```bash
# CORRECT: enable PITR immediately after (or at) table creation
aws dynamodb create-table \
  --table-name ProductionOrders \
  --attribute-definitions AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S \
  --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST

aws dynamodb update-continuous-backups \
  --table-name ProductionOrders \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

# Verify
aws dynamodb describe-continuous-backups --table-name ProductionOrders \
  --query "ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus"
# Expected: "ENABLED"
```

**Detection**: AWS Config managed rule `dynamodb-pitr-enabled`; IaC review for missing PITR
configuration; periodic audit with `aws dynamodb describe-continuous-backups`.

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-pitr-recovery.html (2026-07-31)

---

## A6 — Relational Modeling: Many Normalized Tables + Client-Side Joins `[HIGH RISK]`

**Why prohibited**: DynamoDB has no joins, no foreign keys, and no server-side query planner.
Emulating a relational schema requires multiple round-trip `Query`/`Scan` calls per request.
N round-trips per user request multiplies latency and RCU cost — and degrades under load.

**Blast Radius**: Latency and cost scale with data volume; SLA breach under load; cost overrun
proportional to join multiplicity; difficult to optimize retroactively.

```python
# WRONG: three separate tables, client-side join on every request
def get_customer_with_orders(customer_id: str) -> dict:
    customer = customers_table.get_item(Key={"id": customer_id})["Item"]
    orders = orders_table.query(
        FilterExpression=Attr("customerId").eq(customer_id)  # also a Scan!
    )["Items"]
    for order in orders:
        items = order_items_table.query(
            FilterExpression=Attr("orderId").eq(order["id"])
        )["Items"]
        order["items"] = items
    customer["orders"] = orders
    return customer
# Result: O(1 + N_orders + N_orders*N_items) round-trips per request
```

```python
# CORRECT: single-table design — one Query fetches customer + all orders
def get_customer_with_orders(customer_id: str) -> dict:
    response = app_table.query(
        KeyConditionExpression=Key("PK").eq(f"CUSTOMER#{customer_id}")
        # Returns METADATA item + all ORDER# items in one request
    )
    items = response["Items"]
    customer = next(i for i in items if i["SK"] == "METADATA")
    customer["orders"] = [i for i in items if i["SK"].startswith("ORDER#")]
    return customer
# Result: 1 round-trip, always
```

**Detection**: Architecture review; count of DynamoDB calls per user-facing request (> 1 is a
red flag); presence of multiple table references joined in application code.

**Note**: If the workload is inherently relational (ad-hoc queries, complex reporting, unknown
access patterns), DynamoDB is likely the wrong service — consider Amazon Aurora or RDS instead.

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html (2026-07-31)

---

## A7 — Public Data-Plane Access Without VPC Endpoint or TLS Enforcement `[HIGH RISK]`

**Why prohibited**: DynamoDB traffic from a VPC application routed through the public internet
is interceptable and broadens the attack surface. The absence of an explicit `aws:SecureTransport`
Deny allows SDK clients configured with plaintext transport to connect successfully.

**Blast Radius**: Data in transit exposed to interception; compliance violation (PCI DSS,
HIPAA, SOC 2); broader network attack surface.

```json
// WRONG: no VPC endpoint configured; no SecureTransport condition in policy
// Application in VPC reaches DynamoDB via Internet Gateway → public internet
{
  "Effect": "Allow",
  "Action": ["dynamodb:GetItem", "dynamodb:PutItem"],
  "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/ApplicationDB"
  // missing: Deny when aws:SecureTransport = false
  // missing: VPC endpoint in route table
}
```

```bash
# CORRECT Step 1: Create VPC Gateway Endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id <VPC_ID> \
  --service-name com.amazonaws.us-east-1.dynamodb \
  --route-table-ids <RTB_PRIVATE_1> <RTB_PRIVATE_2>
```

```json
// CORRECT Step 2: Add SecureTransport Deny to table resource policy or role policy
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyPlaintextTransport",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "dynamodb:*",
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/ApplicationDB",
      "Condition": {
        "Bool": { "aws:SecureTransport": "false" }
      }
    }
  ]
}
```

**Detection**: VPC route-table review (absence of DynamoDB prefix list route in private subnets);
IAM policy audit for missing `SecureTransport` Deny; AWS Security Hub findings.

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security-best-practices.html (2026-07-31)
