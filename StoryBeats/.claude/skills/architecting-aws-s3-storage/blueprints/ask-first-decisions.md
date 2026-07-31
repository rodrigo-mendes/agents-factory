# Ask First Decisions — Amazon S3 Storage Architecture

**Tier**: Complex (5 architectural decisions requiring context) | **Source**: S3 User Guide, accessed 2026-07-31

Before committing to any of these approaches, confirm the answers to the framing questions with the architect or team. Presenting options without a recommendation is the default — only opine when a context signal makes one option clearly dominant.

---

## Decision 1 — Storage Class Strategy

**Pillar**: Cost Optimization, Reliability  
**Source**: [Understanding and managing Amazon S3 storage classes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html)

**Ask the architect**: "What is the access frequency and retrieval-latency tolerance per dataset? Can any of it survive single-AZ loss? Should class selection be automated (Intelligent-Tiering + lifecycle) or hand-tuned per dataset?"

| Class | AWS Storage Class ID | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| S3 Standard | `STANDARD` | Availability (99.99%), no retrieval fee, multi-AZ | Highest storage $/GB | Frequently accessed, hot data |
| Intelligent-Tiering | `INTELLIGENT_TIERING` | Hands-off cost optimization, no retrieval fee | Small per-object monitoring fee; objects <128 KB not tiered | Unknown or changing access patterns |
| Standard-IA | `STANDARD_IA` | Lower storage $, multi-AZ, ms retrieval | Retrieval fee; 30-day min duration; 128 KB min billable size | Infrequent (~monthly) but must be AZ-resilient |
| One Zone-IA | `ONEZONE_IA` | Cheapest IA option | Single-AZ (no AZ-loss resilience); retrieval fee; 30-day min | Re-creatable data or CRR replica copies only |
| Glacier Instant Retrieval | `GLACIER_IR` | Archive $/GB with ms retrieval | Retrieval fee; 90-day min duration | Rarely accessed (~quarterly), instant retrieval needed |
| Glacier Flexible Retrieval | `GLACIER` | Very low $/GB | Restore required (minutes to hours); 90-day min | Backups/archive accessed ~annually |
| Glacier Deep Archive | `DEEP_ARCHIVE` | Lowest $/GB | Restore required (hours); 180-day min duration | Compliance archive accessed <1× per year |

**Cost note**: Storage $/GB descends: Standard > IA > Glacier IR > Glacier Flexible > Deep Archive. Retrieval cost inverts — Deep Archive has the highest retrieval $/GB.

**Decision guidance**:
- For **unknown/changing access patterns** → Intelligent-Tiering (automated, no retrieval fees)
- For **predictable aging data** (logs, media) → lifecycle policy: Standard → Standard-IA (30d) → Glacier IR (90d) → Deep Archive (180d+)
- For **objects <128 KB** → keep in Standard or Frequent Access tier; IA/Glacier minimum billable sizes make them counterproductive
- For **latency-critical compute-colocated** data → consider S3 Express One Zone (Decision 4), but confirm single-AZ risk is acceptable

```bash
# Analyze actual access patterns before hand-coding lifecycle transitions
aws s3api get-bucket-analytics-configuration --bucket "$BUCKET_NAME" --id myAnalysis
# Enable Storage Class Analysis first (in console or CLI) — results take 24-48h
# Results show which objects are candidates for IA transitions
```

---

## Decision 2 — Encryption Key Management

**Pillar**: Security  
**Source**: [Security best practices for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

**Ask the architect**: "Do compliance requirements demand customer-managed keys or dual-layer encryption? If SSE-C is genuinely required, are you prepared to explicitly re-enable it per bucket and manage key delivery on every request?"

| Option | Optimizes | Sacrifices | Best When |
|---|---|---|---|
| SSE-S3 (default, automatic) | Zero key management, no extra cost | No customer key control or KMS audit granularity | General data, default baseline |
| SSE-KMS + S3 Bucket Keys | Customer-managed key, KMS audit trail, grants | KMS request cost/latency (Bucket Keys reduce by ~99%) | Sensitive/regulated data needing key control |
| DSSE-KMS | Dual-layer KMS encryption | Highest cost/latency | Mandated dual-layer (certain government workloads) |
| SSE-C (customer-provided key) | You own and hold the key material | Key must be sent on every request; cannot be used by AWS services (Replication, Batch); **disabled by default since April 2026** | Rare; only when organization mandates key ownership and accepts full operational burden |

**April 2026 change**: SSE-C is now disabled by default for new general purpose buckets. To re-enable it for a specific bucket:

```bash
# Re-enable SSE-C for a specific bucket (only when genuinely required)
aws s3api put-bucket-encryption --bucket "$BUCKET_NAME" \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"},
      "BucketKeyEnabled": false
    }]
  }'
# Note: SSE-C callers must provide the key on every PUT and GET request
# AWS services (Replication, Batch Operations, Athena) cannot read SSE-C objects
```

**Recommended for most regulated workloads**: SSE-KMS with S3 Bucket Keys — provides customer key control and full KMS CloudTrail audit, at ~1% of the per-request KMS cost without Bucket Keys.

---

## Decision 3 — Data-Protection / DR Posture

**Pillar**: Reliability, Security  
**Source**: [Replicating objects within and across Regions](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html)

**Ask the architect**: "What are the RTO/RPO and immutability requirements? Is single-Region durability acceptable, or is cross-Region (and RTC's 15-min SLA) required? Do any datasets need WORM — and can we enable Object Lock at bucket creation?"

| Option | RPO | Protects against | Cost | Best When |
|---|---|---|---|---|
| Versioning only | Near-zero (in-Region) | Accidental overwrite/delete; application failure | $ | Baseline for all critical buckets |
| SRR (Same-Region Replication) | 24–48h (no SLA) | Account/log isolation, data sovereignty in-Region | $$ | Log aggregation, prod↔test sync, in-country copies |
| CRR (Cross-Region Replication) | 24–48h (no SLA) | Region-level failure, compliance distance | $$$ (inter-Region transfer) | Cross-Region DR, latency-reduction copies, compliance |
| CRR + RTC (Replication Time Control) | 15 min, 99.99% SLA | Predictable cross-Region RPO | $$$$ (RTC premium) | Contractual replication-time requirements |
| Object Lock (WORM) | n/a (immutability) | Deletion, ransomware, tampering | $ (storage only) | Regulated immutable records, CloudTrail logs, financial records |

**Critical Object Lock constraints**:
- Must be enabled **at bucket creation** — cannot be enabled on an existing bucket without AWS Support involvement.
- Object Lock requires Versioning to be enabled.
- **Compliance mode**: retention period cannot be shortened even by the root account.
- **Governance mode**: users with `s3:BypassGovernanceRetention` permission can override.

```bash
# Create a bucket with Object Lock enabled (must be done at creation)
aws s3api create-bucket --bucket "$BUCKET_NAME" \
  --region us-east-1 \
  --object-lock-enabled-for-bucket

# Configure default retention (Compliance mode, 7 years)
aws s3api put-object-lock-configuration --bucket "$BUCKET_NAME" \
  --object-lock-configuration '{
    "ObjectLockEnabled": "Enabled",
    "Rule": {
      "DefaultRetention": {
        "Mode": "COMPLIANCE",
        "Years": 7
      }
    }
  }'

# Configure CRR with RTC (both source and destination must have versioning)
aws s3api put-bucket-replication --bucket "$SOURCE_BUCKET" \
  --replication-configuration '{
    "Role": "'"$REPLICATION_ROLE_ARN"'",
    "Rules": [{
      "Status": "Enabled",
      "Filter": {"Prefix": ""},
      "Destination": {
        "Bucket": "arn:aws:s3:::'"$DEST_BUCKET"'",
        "ReplicationTime": {"Status": "Enabled", "Time": {"Minutes": 15}},
        "Metrics": {"Status": "Enabled", "EventThreshold": {"Minutes": 15}}
      }
    }]
  }'
```

**Replication gap**: Replication only applies to objects written **after** the rule is configured. Use S3 Batch Replication to backfill pre-existing objects.

---

## Decision 4 — Bucket Type

**Pillar**: Performance Efficiency, Cost Optimization  
**Source**: [What is Amazon S3? (Welcome)](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)

**Ask the architect**: "Is this workload latency-critical enough to accept single-AZ durability? Is the data tabular (S3 Tables / Iceberg) or vector embeddings (S3 Vectors) rather than generic objects?"

| Bucket Type | Namespace | AZ Resilience | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|---|
| General purpose | `s3://` | Multi-AZ | Broadest features, all storage classes | Not lowest latency | Default for ~all use cases |
| Directory (Express One Zone) | `s3express://` | **Single-AZ only** | Single-digit-ms latency, high request/s, data residency | AZ-loss resilience | Latency-critical, high-request-rate workloads co-located with compute |
| Table bucket (S3 Tables) | `s3tables://` | Multi-AZ | Apache Iceberg tabular data, query-optimized | Analytics-only shape; different API | Athena/Redshift/Spark analytics on structured tables |
| Vector bucket (S3 Vectors) | Purpose-built | Multi-AZ | Embedding storage + similarity search | Purpose-built API only | ML embeddings, Bedrock/OpenSearch integration |

**Warning — single-AZ risk**: S3 Express One Zone and S3 One Zone-IA are single-AZ. Do not use them as the sole copy of any unrecreatable data. If using Express One Zone for latency, keep a durable multi-AZ copy elsewhere.

```bash
# Create a directory bucket (Express One Zone) — note the naming convention
# Directory bucket names: <bucket-base-name>--<az-id>--x-s3
# Example for us-east-1 AZ use1-az4:
aws s3api create-bucket \
  --bucket "my-app-cache--use1-az4--x-s3" \
  --region us-east-1 \
  --create-bucket-configuration '{"Location":{"Name":"use1-az4","Type":"AvailabilityZone"},"Bucket":{"DataRedundancy":"SingleAvailabilityZone","Type":"Directory"}}'
```

---

## Decision 5 — Access at Scale

**Pillar**: Security, Operational Excellence  
**Source**: [What is Amazon S3? (Welcome)](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)

**Ask the architect**: "How many distinct applications or teams share this dataset? Is private-network-only access required for compliance? Does the 20 KB bucket policy size limit create a bottleneck at your expected scale?"

| Option | Optimizes | Sacrifices | Best When |
|---|---|---|---|
| Bucket policy | Simplicity, zero extra resources | 20 KB policy size limit; hard to manage at scale | Few, well-known principals with simple access patterns |
| S3 Access Points | Per-application named endpoints; own policy per AP; per-AP BPA and VPC scoping | Extra objects to manage; one Access Point per access pattern | Shared datasets with many teams or applications |
| VPC endpoint + endpoint policy | Keeps traffic off internet; data-exfiltration prevention | Network plumbing (Gateway endpoint = free; Interface = billed) | Regulated environments; private-network-only access required |

**S3 Access Points**: Each Access Point has its own bucket-policy-like policy and can be scoped to a specific VPC. This avoids the 20 KB limit on the bucket policy and provides per-application isolation.

```bash
# Create an Access Point scoped to a specific VPC (restricts to VPC traffic only)
aws s3control create-access-point \
  --account-id "$ACCOUNT_ID" \
  --name "my-app-access-point" \
  --bucket "$BUCKET_NAME" \
  --vpc-configuration VpcId="$VPC_ID"

# Apply a policy to the Access Point (grants app role access via AP, not direct bucket)
aws s3control put-access-point-policy \
  --account-id "$ACCOUNT_ID" \
  --name "my-app-access-point" \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::'"$ACCOUNT_ID"':role/AppRole"},
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:us-east-1:'"$ACCOUNT_ID"':accesspoint/my-app-access-point/object/*"
    }]
  }'

# Create VPC Gateway Endpoint (free; routes S3 traffic within VPC)
aws ec2 create-vpc-endpoint \
  --vpc-id "$VPC_ID" \
  --service-name "com.amazonaws.us-east-1.s3" \
  --vpc-endpoint-type Gateway \
  --route-table-ids "$ROUTE_TABLE_ID"
```

**Bucket policy + Access Point interaction**: When Access Points are used, the bucket policy must also delegate to the Access Point (or use `"Principal":"*"` scoped to the Access Point ARN). The Access Point policy then governs the actual permissions.
