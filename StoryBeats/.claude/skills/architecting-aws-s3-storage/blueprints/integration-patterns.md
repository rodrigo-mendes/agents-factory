# Integration Patterns — Amazon S3 Storage Architecture

**Source**: S3 User Guide + CloudFront, Lambda, Athena, KMS, and VPC Endpoint documentation, accessed 2026-07-31

---

## S3 ↔ CloudFront + Origin Access Control (OAC)

**Use case**: Serve static content publicly via CDN while keeping the S3 bucket private (BPA on).

**Why OAC over OAI**: OAC (Origin Access Control) is the current recommended mechanism. OAI (Origin Access Identity) is a legacy mechanism — CloudFront has removed OAI from new distribution setup flows.

```bash
# Step 1: Create an OAC for the S3 origin
OAC_ID=$(aws cloudfront create-origin-access-control \
  --origin-access-control-config '{
    "Name": "my-s3-oac",
    "Description": "OAC for my-bucket",
    "SigningProtocol": "sigv4",
    "SigningBehavior": "always",
    "OriginAccessControlOriginType": "s3"
  }' \
  --query 'OriginAccessControl.Id' --output text)
echo "OAC ID: $OAC_ID"

# Step 2: Configure CloudFront distribution with the OAC (abbreviated config)
# Set OriginAccessControlId = $OAC_ID on the S3 origin in your distribution config
# Set S3OriginConfig.OriginAccessIdentity = "" (empty for OAC; OAI field not used)

# Step 3: Apply bucket policy granting CloudFront OAC access
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
DISTRIBUTION_ARN="arn:aws:cloudfront::${ACCOUNT_ID}:distribution/${DISTRIBUTION_ID}"

aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyNonTLS",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": ["arn:aws:s3:::'"$BUCKET_NAME"'", "arn:aws:s3:::'"$BUCKET_NAME"'/*"],
      "Condition": {"Bool": {"aws:SecureTransport": "false"}}
    },
    {
      "Sid": "AllowCloudFrontOAC",
      "Effect": "Allow",
      "Principal": {"Service": "cloudfront.amazonaws.com"},
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::'"$BUCKET_NAME"'/*",
      "Condition": {
        "StringEquals": {"AWS:SourceArn": "'"$DISTRIBUTION_ARN"'"}
      }
    }
  ]
}'
```

**Key configuration**:
- Block Public Access remains ON — CloudFront uses SigV4-signed requests, not public access
- Cache policies and origin request policies should omit `Authorization` header forwarding (not needed with OAC)
- Enable CloudFront access logging and set up WAF if the content requires geo-restriction or rate limiting

**Common issue**: CloudFront 403 from S3 → confirm OAC ID is attached to the origin in the distribution config AND the bucket policy `AWS:SourceArn` matches the exact distribution ARN.

---

## S3 ↔ Lambda (Event Notifications)

**Use case**: Trigger Lambda on object creation/deletion for processing pipelines (e.g., image resize, ETL, virus scanning).

```bash
# Step 1: Grant S3 permission to invoke the Lambda function
aws lambda add-permission \
  --function-name "$FUNCTION_NAME" \
  --statement-id "S3EventNotification" \
  --action "lambda:InvokeFunction" \
  --principal "s3.amazonaws.com" \
  --source-arn "arn:aws:s3:::${BUCKET_NAME}" \
  --source-account "$ACCOUNT_ID"

# Step 2: Configure S3 event notification
aws s3api put-bucket-notification-configuration \
  --bucket "$BUCKET_NAME" \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [{
      "LambdaFunctionArn": "arn:aws:lambda:us-east-1:'"$ACCOUNT_ID"':function:'"$FUNCTION_NAME"'",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {"Name": "prefix", "Value": "uploads/"},
            {"Name": "suffix", "Value": ".jpg"}
          ]
        }
      }
    }]
  }'
```

**Lambda handler — read the uploaded object**:

```python
import boto3
import json

s3 = boto3.client('s3')  # Credentials from Lambda execution role

def handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        # URL-decode the key (S3 encodes special characters in event notifications)
        from urllib.parse import unquote_plus
        key = unquote_plus(key)

        # Read object (execution role must have s3:GetObject on this bucket/prefix)
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read()
        print(f"Processing {key}: {len(content)} bytes")
        # Process content here...
```

**Lambda execution role — minimum required permissions**:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:HeadObject"],
    "Resource": "arn:aws:s3:::my-bucket/uploads/*"
  }]
}
```

**Performance consideration**: S3 event notifications are async (best-effort delivery, at-least-once). For guaranteed processing with backpressure, use S3 → SQS notification → Lambda SQS event source mapping with `ReportBatchItemFailures`.

**Object size**: For objects > 6 MB, do not pass content through Lambda synchronously — use presigned URLs or generate a presigned URL from the notification and have the processor download directly.

---

## S3 ↔ Athena / S3 Table Buckets

**Use case**: Query S3 data with Athena (generic objects via external tables) or use S3 Table Buckets (Apache Iceberg, query-optimized).

### Athena on Generic S3 Objects

```sql
-- Create external table pointing to S3 location (Parquet example)
CREATE EXTERNAL TABLE sales_data (
  order_id STRING,
  customer_id STRING,
  amount DECIMAL(10,2),
  order_date DATE
)
STORED AS PARQUET
LOCATION 's3://my-data-lake/sales/year=2026/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');

-- Query it (results go to Athena results bucket)
SELECT customer_id, SUM(amount) AS total
FROM sales_data
WHERE order_date >= DATE '2026-01-01'
GROUP BY customer_id
ORDER BY total DESC
LIMIT 100;
```

**IAM role for Athena**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::my-data-lake",
        "arn:aws:s3:::my-data-lake/sales/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject"],
      "Resource": "arn:aws:s3:::athena-results-bucket/*"
    }
  ]
}
```

### S3 Table Buckets (Apache Iceberg — current edition)

S3 Table Buckets use the `s3tables` namespace and expose an Iceberg REST catalog compatible with Athena, Redshift Spectrum, Apache Spark, and AWS Glue.

```bash
# Create a table bucket
aws s3tables create-table-bucket \
  --name my-table-bucket \
  --region us-east-1

# Create a namespace within the table bucket
aws s3tables create-namespace \
  --table-bucket-arn "arn:aws:s3tables:us-east-1:$ACCOUNT_ID:bucket/my-table-bucket" \
  --namespace '["analytics"]'

# Tables are created via Athena or the S3 Tables API; query via Athena:
# SELECT * FROM "s3tablescatalog/my-table-bucket"."analytics"."orders" LIMIT 10;
```

**When to use Table Buckets vs generic S3 + Athena**:
- Table Buckets: structured tabular data, frequent updates/deletes (Iceberg ACID), multiple query engines
- Generic S3 + Athena: semi-structured data (JSON/CSV/Parquet), read-heavy analytics, simpler setup

---

## S3 ↔ AWS KMS (SSE-KMS + S3 Bucket Keys)

**Use case**: Customer-managed encryption keys with audit trail, cost-controlled via Bucket Keys.

**Key policy** (minimum required for S3 SSE-KMS):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowS3ServiceToUseKey",
      "Effect": "Allow",
      "Principal": {"Service": "s3.amazonaws.com"},
      "Action": ["kms:GenerateDataKey", "kms:Decrypt"],
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "kms:EncryptionContext:aws:s3:arn": [
            "arn:aws:s3:::my-bucket",
            "arn:aws:s3:::my-bucket/*"
          ]
        }
      }
    },
    {
      "Sid": "AllowAppRoleToDecrypt",
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::$ACCOUNT_ID:role/AppRole"},
      "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
      "Resource": "*"
    }
  ]
}
```

```bash
# Enable SSE-KMS with S3 Bucket Keys (reduces KMS API calls ~99%)
aws s3api put-bucket-encryption --bucket "$BUCKET_NAME" \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "'"$KMS_KEY_ARN"'"
      },
      "BucketKeyEnabled": true
    }]
  }'

# Verify Bucket Key is enabled
aws s3api get-bucket-encryption --bucket "$BUCKET_NAME" \
  --query 'ServerSideEncryptionConfiguration.Rules[0].BucketKeyEnabled'
# Expected: true
```

**Cost impact of S3 Bucket Keys**: Without Bucket Keys, every S3 GetObject and PutObject generates a KMS API call (billed at ~$0.03 per 10,000 requests). With Bucket Keys enabled, S3 generates a short-lived data key per Bucket Key session, dramatically reducing KMS API calls for large datasets.

**Cross-account access to SSE-KMS bucket**: The accessing account's IAM role must have `kms:Decrypt` permission on the key, AND the key policy must allow the cross-account role. Both conditions must be satisfied.

---

## S3 ↔ VPC Endpoint (Gateway and Interface)

**Use case**: Route S3 traffic within the VPC without traversing the public internet — required for regulated environments and data-exfiltration prevention.

### Gateway Endpoint (Free — recommended for EC2/Lambda)

```bash
# Create Gateway endpoint (routes S3 traffic in the VPC's route tables)
aws ec2 create-vpc-endpoint \
  --vpc-id "$VPC_ID" \
  --service-name "com.amazonaws.${AWS_REGION}.s3" \
  --vpc-endpoint-type Gateway \
  --route-table-ids "$ROUTE_TABLE_ID"

# Apply endpoint policy to restrict which buckets the VPC can access
aws ec2 modify-vpc-endpoint \
  --vpc-endpoint-id "$ENDPOINT_ID" \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::my-allowed-bucket",
        "arn:aws:s3:::my-allowed-bucket/*"
      ]
    }]
  }'
```

### Exfiltration Prevention — Bucket Policy Condition

Lock a bucket to only allow access via a specific VPC or VPC endpoint:

```json
// Bucket policy — deny any request NOT coming through the VPC endpoint
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyAccessOutsideVPCEndpoint",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::my-private-bucket",
        "arn:aws:s3:::my-private-bucket/*"
      ],
      "Condition": {
        "StringNotEquals": {
          "aws:SourceVpce": "vpce-ENDPOINT_ID"
        }
      }
    }
  ]
}
```

### Interface Endpoint (PrivateLink — billed per hour + data)

```bash
# Create Interface endpoint (DNS-resolved; works for on-premises via Direct Connect/VPN)
aws ec2 create-vpc-endpoint \
  --vpc-id "$VPC_ID" \
  --service-name "com.amazonaws.${AWS_REGION}.s3" \
  --vpc-endpoint-type Interface \
  --subnet-ids "$SUBNET_ID" \
  --security-group-ids "$SG_ID" \
  --private-dns-enabled
```

**Gateway vs Interface endpoint**:
- **Gateway** (free): works for EC2 and Lambda within the VPC; uses route table entries; does not support on-premises connectivity
- **Interface/PrivateLink** (billed ~$0.01/hour per AZ + data transfer): works for on-premises via Direct Connect or VPN; uses private DNS resolution; required for cross-account private access without internet
