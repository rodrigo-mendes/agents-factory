# Integration Patterns — Amazon DynamoDB

> Source: AWS DynamoDB Developer Guide, retrieved 2026-07-31.
> Back to [SKILL.md](../SKILL.md)

---

## DynamoDB ↔ Amazon S3 — Blob Offload

**Pattern**: Store large objects (PDFs, images, large JSON) in Amazon S3; keep the S3 object
key plus queryable metadata in the DynamoDB item.

**Why**: DynamoDB item hard limit is 400 KB. Storing blobs inline causes write rejections and
inflates RCU/WCU consumption. S3 has no object-size impact on DynamoDB throughput.

**SDK Setup (Python / boto3)**:
```python
import boto3
from typing import Optional

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("ApplicationDB")

BLOB_BUCKET = "my-app-blobs"
INLINE_THRESHOLD_BYTES = 8_000  # store inline only if < 8 KB

def put_item_with_blob(
    pk: str, sk: str, metadata: dict, payload: Optional[bytes] = None
) -> None:
    item = {"PK": pk, "SK": sk, **metadata}

    if payload and len(payload) > INLINE_THRESHOLD_BYTES:
        s3_key = f"{pk}/{sk}/payload"
        s3.put_object(Bucket=BLOB_BUCKET, Key=s3_key, Body=payload)
        item["s3_bucket"] = BLOB_BUCKET
        item["s3_key"] = s3_key
        item["payload_size_bytes"] = len(payload)
    elif payload:
        item["payload"] = payload.decode("utf-8")

    table.put_item(Item=item)

def get_blob(pk: str, sk: str) -> bytes:
    item = table.get_item(Key={"PK": pk, "SK": sk})["Item"]
    if "s3_key" in item:
        obj = s3.get_object(Bucket=item["s3_bucket"], Key=item["s3_key"])
        return obj["Body"].read()
    return item.get("payload", b"").encode("utf-8")
```

**Required IAM**:
```json
{
  "Action": ["s3:PutObject", "s3:GetObject"],
  "Resource": "arn:aws:s3:::my-app-blobs/*"
}
```

**Common Issues**:
- **Issue**: `ValidationException: Item size exceeds 400 KB`
  **Cause**: Payload stored inline without size check
  **Solution**: Validate `len(json.dumps(item).encode()) < 400_000` before `put_item`; increase `INLINE_THRESHOLD_BYTES` conservatively

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-use-s3-too.html (2026-07-31)

---

## DynamoDB ↔ AWS Lambda (via DynamoDB Streams) — Event-Driven CDC

**Pattern**: DynamoDB Streams capture item-level changes (INSERT, MODIFY, REMOVE) in an
ordered, shard-based feed. Lambda triggers process the stream for materialized views,
cross-service fan-out, notifications, and audit logs.

**Constraints**:
- Stream record retention: **24 hours** (use Kinesis Data Streams for DynamoDB for longer retention)
- Max simultaneous readers per shard: **2** (single-Region) / **1** (global tables — replication uses one slot)

**Enable Streams + Lambda Trigger (AWS CLI)**:
```bash
# Enable Streams on the table (NEW_AND_OLD_IMAGES recommended for most use cases)
aws dynamodb update-table \
  --table-name ApplicationDB \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES

# Get the stream ARN
STREAM_ARN=$(aws dynamodb describe-table --table-name ApplicationDB \
  --query "Table.LatestStreamArn" --output text)

# Create Lambda event source mapping
aws lambda create-event-source-mapping \
  --function-name ProcessDynamoDBStream \
  --event-source-arn "$STREAM_ARN" \
  --starting-position TRIM_HORIZON \
  --batch-size 100 \
  --maximum-retry-attempts 3
```

**Lambda Handler Pattern**:
```python
import json

def handler(event, context):
    for record in event["Records"]:
        event_name = record["eventName"]  # INSERT | MODIFY | REMOVE
        new_image = record.get("dynamodb", {}).get("NewImage", {})
        old_image = record.get("dynamodb", {}).get("OldImage", {})

        if event_name == "INSERT":
            handle_insert(new_image)
        elif event_name == "MODIFY":
            handle_modify(old_image, new_image)
        elif event_name == "REMOVE":
            handle_remove(old_image)

def handle_insert(new_image: dict) -> None:
    pk = new_image.get("PK", {}).get("S", "")
    # Fan out to SNS, SQS, EventBridge, or update a read model
    print(f"New item inserted: {pk}")
```

**Required IAM (Lambda execution role)**:
```json
{
  "Action": [
    "dynamodb:GetRecords",
    "dynamodb:GetShardIterator",
    "dynamodb:DescribeStream",
    "dynamodb:ListStreams"
  ],
  "Resource": "<STREAM_ARN>"
}
```

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html (2026-07-31)

---

## DynamoDB ↔ DAX — In-Memory Read Cache

**Pattern**: DynamoDB Accelerator (DAX) is an API-compatible, write-through in-memory cluster
delivering microsecond read latency for eventually-consistent hot reads. The application SDK
points to the DAX cluster endpoint instead of DynamoDB directly.

**When to add**: Read-heavy workloads with repeated identical queries (product catalog, top-N
lists, session data). Do NOT add DAX when strongly-consistent reads are required or writes are
the dominant operation.

**SDK Setup (Python / aiobotocore-compatible)**:
```python
import amazondax  # pip install amazon-dax-client

# Replace the DynamoDB resource/client with the DAX client — API is identical
dax_endpoint = "my-cluster.xxx.dax-clusters.us-east-1.amazonaws.com:8111"
dax = amazondax.AmazonDaxClient.resource(endpoint_url=f"dax://{dax_endpoint}")
table = dax.Table("ApplicationDB")

# All reads go through DAX cache (eventual consistency only)
response = table.get_item(Key={"PK": "PRODUCT#123", "SK": "METADATA"})
```

**Cluster Setup (AWS CLI)**:
```bash
aws dax create-cluster \
  --cluster-name app-dax-cluster \
  --node-type dax.r6g.large \
  --replication-factor 3 \
  --iam-role-arn arn:aws:iam::<ACCOUNT>:role/DAXRole \
  --subnet-group my-dax-subnet-group
```

**Common Issues**:
- **Issue**: Stale data after a write
  **Cause**: DAX write-through updates the cache, but eventual propagation means a subsequent read from another node may be stale
  **Solution**: Design the access pattern to tolerate sub-second staleness; use direct DynamoDB for strongly-consistent reads

- **Issue**: DAX returns `ItemNotFoundException` for a new item
  **Cause**: DAX negative-cache TTL (item-not-found result is cached)
  **Solution**: Tune `QueryTTL`/`ItemTTL` on the cluster; or write then immediately read from DynamoDB (not DAX) where consistency is required

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/dax-prescriptive-guidance.html (2026-07-31)

---

## DynamoDB ↔ AWS KMS — Customer-Managed Encryption

**Pattern**: Replace the default AWS-owned key with a Customer-Managed Key (CMK) for full audit
trail, key-policy control, and automated rotation.

**When to use**: Regulated data (HIPAA, PCI DSS, SOC 2, GDPR), data residency requirements,
or any workload where key ownership and CloudTrail visibility of every decryption event is required.

**Create Table with CMK (AWS CLI)**:
```bash
# Create the CMK (or use an existing one)
KEY_ARN=$(aws kms create-key \
  --description "DynamoDB CMK for ApplicationDB" \
  --key-usage ENCRYPT_DECRYPT \
  --query "KeyMetadata.Arn" --output text)

aws kms create-alias --alias-name alias/dynamodb-app-key --target-key-id "$KEY_ARN"

# Enable automatic annual rotation
aws kms enable-key-rotation --key-id "$KEY_ARN"

# Create DynamoDB table with CMK
aws dynamodb create-table \
  --table-name ApplicationDB \
  --attribute-definitions AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S \
  --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --sse-specification Enabled=true,SSEType=KMS,KMSMasterKeyId="$KEY_ARN"
```

**Verify SSE**:
```bash
aws dynamodb describe-table --table-name ApplicationDB \
  --query "Table.SSEDescription"
# Expected: {"Status":"ENABLED","SSEType":"KMS","KMSMasterKeyArn":"arn:aws:kms:..."}
```

**Cost Impact**: Each DynamoDB read/write generates a KMS API call (cached within the SDK for a
short TTL). At very high request rates, KMS costs can be non-trivial — monitor with
`aws cloudwatch get-metric-statistics --namespace AWS/KMS`.

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security-best-practices.html (2026-07-31)

---

## DynamoDB ↔ IAM Fine-Grained Access (Multi-Tenant Isolation)

**Pattern**: Use `dynamodb:LeadingKeys` and `dynamodb:Attributes` IAM condition keys to enforce
row-level and column-level isolation between tenants without application-layer enforcement.

**When to use**: Any multi-tenant application where one tenant must never access another tenant's
data rows or sensitive attribute columns.

**Row-Level Isolation (LeadingKeys)**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "TenantRowIsolation",
    "Effect": "Allow",
    "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem",
               "dynamodb:DeleteItem", "dynamodb:Query"],
    "Resource": "arn:aws:dynamodb:<REGION>:<ACCOUNT>:table/ApplicationDB",
    "Condition": {
      "ForAllValues:StringEquals": {
        "dynamodb:LeadingKeys": ["${aws:PrincipalTag/tenantId}"]
      }
    }
  }]
}
```

**Column-Level Isolation (Attributes)**:
```json
{
  "Sid": "HideInternalAdminAttributes",
  "Effect": "Deny",
  "Action": ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan"],
  "Resource": "arn:aws:dynamodb:<REGION>:<ACCOUNT>:table/ApplicationDB",
  "Condition": {
    "ForAnyValue:StringEquals": {
      "dynamodb:Attributes": ["internalCost", "adminNotes", "fraudScore"]
    }
  }
}
```

**Verification**:
```bash
# Test policy with IAM Policy Simulator
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::<ACCOUNT>:role/TenantRole \
  --action-names dynamodb:GetItem \
  --resource-arns arn:aws:dynamodb:<REGION>:<ACCOUNT>:table/ApplicationDB \
  --context-entries '{"ContextKeyName":"aws:PrincipalTag/tenantId","ContextKeyValues":["tenant-A"],"ContextKeyType":"string"}' \
  --query "EvaluationResults[0].EvalDecision"
# Expected: "allowed"
```

**Common Issues**:
- **Issue**: `AccessDeniedException` for valid tenant operations
  **Cause**: Tag `tenantId` not propagated to the principal's session via STS
  **Solution**: Ensure `sts:TagSession` is allowed and the tag is set at assume-role time (`--tags Key=tenantId,Value=<id>`)

**Source**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security-best-practices.html (2026-07-31)
