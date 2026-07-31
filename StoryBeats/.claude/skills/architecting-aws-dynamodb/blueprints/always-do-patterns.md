# Always Do Patterns — Amazon DynamoDB

> Source: AWS DynamoDB Developer Guide, retrieved 2026-07-31.
> Back to [SKILL.md](../SKILL.md)

---

## M1 — Access-Pattern-First (Single-Table) Data Modeling

**Why mandatory**: DynamoDB has no server-side query planner and no joins. Physical data placement
is determined entirely by the partition key. Every access pattern must be pre-designed as a
`GetItem` or `Query` — a `Scan` on a hot path is a cost and latency disaster. Modeling relationally
(many normalized tables + client-side joins) is the #1 cause of failure on DynamoDB.

**Architecture Decision**:
1. Enumerate **all** read and write access patterns before touching the key schema.
2. Design `PK`/`SK` (overloaded generic names) and GSIs to serve every pattern with one `Query`.
3. Use key prefixes to distinguish entity types: `CUSTOMER#<id>`, `ORDER#<id>`, `PRODUCT#<id>`.
4. Co-locate related items under the same partition key so one `Query` fetches an entire item
   collection (e.g., customer + all its orders).

**Single-Table Design — Overloaded Key Example**:
```
Table: ApplicationDB

PK              | SK                  | entity | ...attributes
CUSTOMER#123    | METADATA            | CUST   | name, email
CUSTOMER#123    | ORDER#2026-07-01    | ORDER  | total, status
CUSTOMER#123    | ORDER#2026-07-15    | ORDER  | total, status

GSI1PK          | GSI1SK
ORDER#2026-07-01| CUSTOMER#123        <- invert for "orders by date" pattern
```

**Verification**:
```bash
# Confirm every access pattern maps to a Query, not a Scan
aws dynamodb describe-table --table-name <T> \
  --query "Table.{KeySchema:KeySchema,GSIs:GlobalSecondaryIndexes}"

# Review access pattern coverage checklist in design doc before table creation
```

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html (2026-07-31)

---

## M2 — Uniform Partition-Key Design

**Why mandatory**: Every DynamoDB partition is hard-capped at **3,000 RCU/s and 1,000 WCU/s**
regardless of total table throughput. A skewed key throttles even if the table has ample capacity.
Adaptive capacity mitigates *transient* skew but does not remove the hard ceiling for sustained skew.

**Architecture Decision**:
- Choose partition keys with **high cardinality** and **uniform request distribution** (e.g., `userId`,
  `orderId`, `deviceId` — not `status`, `region`, `date`).
- For unavoidable high-write keys (e.g., a global counter, a leaderboard top key): apply
  **write sharding** — append a calculated suffix `#0..N` to distribute across N partitions, then
  scatter-gather (parallel Query per shard) on reads.
- Enable **Contributor Insights** immediately on new tables to detect hot keys before they cause outages.

**Write Sharding Pattern**:
```python
import random

SHARD_COUNT = 10

def shard_key(base_key: str) -> str:
    suffix = random.randint(0, SHARD_COUNT - 1)  # or hash-based for determinism
    return f"{base_key}#{suffix}"

def scatter_gather_query(base_key: str, table) -> list:
    results = []
    for i in range(SHARD_COUNT):
        resp = table.query(
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": f"{base_key}#{i}"}
        )
        results.extend(resp["Items"])
    return results
```

**Verification**:
```bash
# Enable Contributor Insights
aws dynamodb update-contributor-insights \
  --table-name <T> --contributor-insights-action ENABLE

# Watch CloudWatch for throttling
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB --metric-name ThrottledRequests \
  --dimensions Name=TableName,Value=<T> \
  --start-time $(date -u -d '1 hour ago' +%FT%TZ) \
  --end-time $(date -u +%FT%TZ) \
  --period 300 --statistics Sum
```

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html (2026-07-31)

---

## M3 — Keep Items Small; Offload Large Payloads to Amazon S3

**Why mandatory**: The DynamoDB item size hard limit is **400 KB**. Capacity consumption rounds
UP to the next 4 KB block (reads) or 1 KB block (writes). A 400 KB item costs 100 RCUs per
strongly-consistent read — 100x more than a 4 KB item.

**Architecture Decision**:
Store blobs (PDFs, images, large JSON documents) in Amazon S3; keep the S3 object key plus
queryable metadata attributes in the DynamoDB item. Validate serialized item size before every
`PutItem`.

**S3 Offload Pattern**:
```python
import boto3, json

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb").Table("Documents")

BUCKET = "my-docs-bucket"
MAX_INLINE_BYTES = 10_000  # conservative; hard limit is 400 KB serialized

def put_document(doc_id: str, metadata: dict, payload: bytes) -> None:
    if len(payload) > MAX_INLINE_BYTES:
        s3_key = f"docs/{doc_id}/payload"
        s3.put_object(Bucket=BUCKET, Key=s3_key, Body=payload)
        metadata["s3_key"] = s3_key          # pointer in DynamoDB
        metadata["payload_size"] = len(payload)
    else:
        metadata["payload"] = payload.decode()  # inline only for small payloads

    dynamodb.put_item(Item={"PK": f"DOC#{doc_id}", "SK": "METADATA", **metadata})
```

**Verification**:
```bash
# Estimate item size before write (application-side)
python -c "import json, sys; item={'PK':'x','SK':'y','data':'...'}; print(len(json.dumps(item).encode()),'bytes')"

# Monitor via CloudWatch (no native item-size metric; alarm on UserErrors for size violations)
aws cloudwatch put-metric-alarm \
  --alarm-name <T>-UserErrors \
  --namespace AWS/DynamoDB --metric-name UserErrors \
  --dimensions Name=TableName,Value=<T> \
  --threshold 1 --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 --period 60 --statistic Sum \
  --alarm-actions <SNS_ARN>
```

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-use-s3-too.html (2026-07-31)

---

## M4 — Encryption at Rest with the Right KMS Tier + TLS in Transit

**Why mandatory**: Encryption at rest is always enabled; the **default AWS-owned key has no audit
trail**. For regulated or sensitive data (HIPAA, PCI, GDPR), a customer-managed KMS key (CMK)
provides key policy control, rotation, and CloudTrail visibility. TLS enforcement must be explicit
— the absence of a `SecureTransport` Deny allows plaintext connections.

**Architecture Decision**:

| Data Classification | KMS Key Tier | Reason |
|----|----|-----|
| Public / non-sensitive | AWS-owned key (default) | No overhead; no audit needed |
| Internal / sensitive | AWS-managed key (`aws/dynamodb`) | CloudTrail visibility; no rotation control |
| Regulated (HIPAA/PCI) | Customer-managed key (CMK) | Full key policy + rotation + audit |

**Customer-Managed Key + TLS Enforcement (IaC excerpt)**:
```json
// IAM inline policy — attach to every role accessing DynamoDB
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnencryptedTransport",
      "Effect": "Deny",
      "Action": "dynamodb:*",
      "Resource": "arn:aws:dynamodb:<REGION>:<ACCOUNT>:table/<TABLE>",
      "Condition": {
        "Bool": { "aws:SecureTransport": "false" }
      }
    }
  ]
}
```

```bash
# Verify SSE on existing table
aws dynamodb describe-table --table-name <T> \
  --query "Table.SSEDescription"
# Expected: {"Status": "ENABLED", "SSEType": "KMS", "KMSMasterKeyArn": "arn:aws:kms:..."}
```

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security-best-practices.html (2026-07-31)

---

## M5 — Least-Privilege IAM with Fine-Grained Condition Keys

**Why mandatory**: DynamoDB supports item-level and attribute-level access control via condition
keys. Wildcard `dynamodb:*` on `Resource: *` is the most common misconfiguration — it grants full
read/write/delete/drop of every table in the account and region.

**Architecture Decision**:
- Scope every policy to specific table ARNs (never `"*"`).
- For multi-tenant isolation: use `dynamodb:LeadingKeys` to restrict an identity to rows where the
  partition key matches the caller's tenant/user ID.
- Use `dynamodb:Attributes` to restrict which attributes an identity may read or write.

**Tenant-Isolated IAM Policy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query", "dynamodb:UpdateItem"],
    "Resource": "arn:aws:dynamodb:<REGION>:<ACCOUNT>:table/ApplicationDB",
    "Condition": {
      "ForAllValues:StringEquals": {
        "dynamodb:LeadingKeys": ["${aws:PrincipalTag/tenantId}"]
      }
    }
  }]
}
```

**Verification**:
```bash
# Audit for wildcard resource in DynamoDB policies
aws iam list-policies --scope Local | jq '.Policies[].PolicyName' | while read p; do
  aws iam get-policy-version --policy-arn "arn:aws:iam::<ACCOUNT>:policy/$p" \
    --version-id $(aws iam get-policy --policy-arn "arn:aws:iam::<ACCOUNT>:policy/$p" --query 'Policy.DefaultVersionId' -o text) \
    --query 'PolicyVersion.Document' | grep -l '"dynamodb:\*"' && echo "WILDCARD FOUND: $p"
done
```

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security-best-practices.html (2026-07-31)

---

## M6 — Point-in-Time Recovery + Backup Strategy on All Production Tables

**Why mandatory**: A bad deployment, a fat-finger delete, or application corruption is
permanently unrecoverable without continuous backups. PITR provides a rolling 35-day restore
window. AWS Backup or on-demand snapshots handle long-term/compliance retention.

**Architecture Decision**:
- Enable PITR on every production table at creation (or immediately after).
- Complement with on-demand backups or AWS Backup for snapshots beyond 35 days.
- Define and **test** restore RTO/RPO — confirm a restore completes within the SLA.

**Verification**:
```bash
# Enable PITR
aws dynamodb update-continuous-backups \
  --table-name <T> \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

# Confirm
aws dynamodb describe-continuous-backups --table-name <T> \
  --query "ContinuousBackupsDescription.PointInTimeRecoveryDescription"
# Expected: {"PointInTimeRecoveryStatus": "ENABLED", "EarliestRestorableDateTime": "...", "LatestRestorableDateTime": "..."}

# AWS Config rule to detect unprotected tables
aws configservice describe-config-rules \
  --config-rule-names dynamodb-pitr-enabled
```

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-pitr-recovery.html (2026-07-31)

---

## M7 — Private Connectivity via VPC Gateway Endpoint

**Why mandatory**: Without a VPC endpoint, DynamoDB traffic from an application in a VPC
traverses the public internet, broadening the attack surface and violating private-network
compliance requirements.

**Architecture Decision**:
- Create a **VPC Gateway Endpoint** for DynamoDB and associate it with all relevant route tables.
- Apply an endpoint policy restricting access to specific table ARNs.
- Use a PrivateLink interface endpoint only when Gateway Endpoint is insufficient (e.g., on-premises
  access via Direct Connect/VPN).

**VPC Gateway Endpoint (AWS CLI)**:
```bash
aws ec2 create-vpc-endpoint \
  --vpc-id <VPC_ID> \
  --service-name com.amazonaws.<REGION>.dynamodb \
  --route-table-ids <RTB_ID_1> <RTB_ID_2> \
  --policy-document '{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect":"Allow",
      "Principal":"*",
      "Action":["dynamodb:GetItem","dynamodb:PutItem","dynamodb:Query","dynamodb:UpdateItem"],
      "Resource":"arn:aws:dynamodb:<REGION>:<ACCOUNT>:table/<TABLE>"
    }]
  }'
```

**Verification**:
```bash
# Confirm endpoint in route table
aws ec2 describe-route-tables --route-table-ids <RTB_ID> \
  --query "RouteTables[0].Routes[?DestinationPrefixListId!=null]"
# Expected: entry for pl-xxxxxxxx (DynamoDB prefix list)
```

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/privatelink-interface-endpoints.html (2026-07-31)

---

## M8 — Exponential-Backoff Retries + Idempotent Conditional Writes

**Why mandatory**: `ProvisionedThroughputExceededException` and transient service errors are
expected at scale — not failure conditions. The AWS SDK retries with exponential backoff by
default. Application code must also ensure writes are idempotent to prevent lost updates under
concurrent access.

**Architecture Decision**:
- Rely on SDK default retry/backoff configuration (do not set `maxRetries=0`).
- Use `attribute_not_exists(PK)` to guard new-item creation.
- Use a `version` attribute with `ConditionExpression: version = :expected` for optimistic locking.
- Use `TransactWriteItems` for multi-item atomicity when all-or-nothing semantics are required
  (costs **2x** the capacity of individual writes).

**Optimistic Locking Pattern**:
```python
import boto3
from botocore.exceptions import ClientError

table = boto3.resource("dynamodb").Table("ApplicationDB")

def update_with_version(pk: str, sk: str, new_value: str, expected_version: int) -> bool:
    try:
        table.update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression="SET #val = :v, version = :new_v",
            ConditionExpression="version = :exp_v",
            ExpressionAttributeNames={"#val": "value"},
            ExpressionAttributeValues={
                ":v": new_value,
                ":new_v": expected_version + 1,
                ":exp_v": expected_version,
            },
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False  # concurrent write — caller should re-read and retry
        raise
```

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BestPractices_ImplementingVersionControl.html (2026-07-31)
