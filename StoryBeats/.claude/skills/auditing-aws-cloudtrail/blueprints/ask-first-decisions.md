# Ask-First Decisions — AWS CloudTrail 2025

> Source: [research_aws_cloudtrail_2025.md](../../../docs/research_aws_cloudtrail_2025.md), verified 2026-07-31.
> Each decision requires architect input before proceeding. Present the tradeoff matrix and wait for the answer.

---

## AF-1 — Organization Trail vs. Per-Account Trails

**Ask the architect**: "Are all accounts in a single AWS Organization, and do you want new accounts covered automatically the moment they join?"

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Organization trail | CloudTrail org trail + Organizations | Uniform coverage, auto-enroll, tamper-resistance (member accounts cannot stop/modify) | Dependency on management/delegated-admin account and home Region | You use AWS Organizations (nearly always) |
| Per-account trails | CloudTrail trail per account | Account autonomy, per-team ownership | Coverage drift; accounts can disable own audit; scaling requires manual creation per new account | No Organizations, or strict account isolation mandate |

**Cost profile**: Comparable event volume; org trail avoids duplicated management effort. First management-event copy is free either way.

**Scaling**: Org trail scales automatically via `AWSServiceRoleForCloudTrail` as accounts join/leave; per-account requires manual creation each time.

**Decision criteria**: If the answer is "yes, AWS Organizations" — use org trail (AD-2). If "no Organizations or cannot use delegated admin" — per-account trail with a compensating control to detect disablement (AD-6 alerting on each account's trail).

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html (accessed 2026-07-31)

---

## AF-2 — CloudTrail Lake vs. S3 + Athena for Querying

**Ask the architect**: "Do you have a data-engineering team to own S3 partition management, Glue crawlers, and query tuning — or do you want managed SQL and long retention out of the box?"

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| CloudTrail Lake | CloudTrail Lake EDS (SQL) | Zero-ops, immutable, org/multi-Region + non-AWS ingest, up to ~10 yr retention | Per-GB ingestion cost ($0.75/GB CloudTrail events); Lake-specific SQL dialect | Investigations, long retention, no data-eng team |
| S3 + Athena | S3, Amazon Athena, AWS Glue Data Catalog | Cheapest at-rest storage, open Parquet/partitioning, reuse existing data lake | You build and maintain schema, partitions, and query tuning | You already run a data lake and want lowest storage cost |

**Cost profile**:
- Lake ingestion $0.75/GB + $0.023/GB/mo extended storage + $0.005/GB scanned per query (billed separately from a trail)
- Athena ~$5/TB scanned over S3 you already pay for; Lake trades higher ingest cost for zero operations

**Lock-in**: Athena/S3 keeps raw CloudTrail JSON portable; Lake keeps data inside CloudTrail (export query results to S3 to mitigate).

**Retention tiers** (CloudTrail Lake):
- **One-year extendable**: ≤25 TB/month workloads; up to 3,653 days (~10 yr); ingestion $0.75/GB
- **Seven-year**: >25 TB/month workloads; up to 2,557 days (~7 yr); tiered ingestion ($2.5/$1/$0.50/GB)

Source: https://aws.amazon.com/cloudtrail/pricing/ (accessed 2026-07-31)

---

## AF-3 — Which Event Types to Enable (Management / Data / Insights / Network Activity)

**Ask the architect**: "Which specific S3 buckets / Lambda functions / DynamoDB tables hold sensitive data and justify per-object logging? And do you need anomaly detection (Insights)?"

| Event Type | Default | Cost | Optimizes | Best When |
|---|---|---|---|---|
| Management events (control-plane) | ON | First copy free; additional copies $2.00/100k | Compliance baseline; IAM/console activity | Always — minimum requirement |
| Data events (S3/Lambda/DynamoDB/etc.) | OFF | $0.10/100k events | Object-level forensics; data-exfil detection | Sensitive data stores; regulated workloads |
| Insights events | OFF | $0.35/100k mgmt events analyzed | Anomaly detection on write/error rates | Detecting credential misuse / runaway automation |
| Network activity events | OFF | $0.10/100k events | VPC-endpoint API visibility (data perimeter) | Strict egress/exfiltration monitoring |

**Volume warning**: Data events can dwarf management-event volume by orders of magnitude on busy S3/Lambda workloads. Always scope with advanced event selectors (e.g. writes only, one specific bucket, one Lambda function).

**Advanced event selector example** (S3 data events, writes only, scoped to one bucket):
```json
[{
  "Name": "sensitive-s3-writes-only",
  "FieldSelectors": [
    {"Field": "eventCategory", "Equals": ["Data"]},
    {"Field": "resources.type", "Equals": ["AWS::S3::Object"]},
    {"Field": "resources.ARN", "StartsWith": ["arn:aws:s3:::<sensitive-bucket>/"]},
    {"Field": "readOnly", "Equals": ["false"]}
  ]
}]
```

```bash
# Apply selectors
aws cloudtrail put-event-selectors \
  --trail-name <trail-name> \
  --advanced-event-selectors file://selectors.json

# Verify
aws cloudtrail get-event-selectors --trail-name <trail-name>
```

**Note**: EDS (CloudTrail Lake) supports ONLY advanced event selectors; basic selectors are trail-only.

Source: https://aws.amazon.com/cloudtrail/pricing/ and https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html (accessed 2026-07-31)

---

## AF-4 — Multi-Region vs. Single-Region Trail

**Ask the architect**: "Is there any reason not to use a multi-Region trail? (The answer should almost always be 'no reason' — single-Region outside us-east-1 silently loses IAM/STS/CloudFront events since 2021-11-22.)"

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Multi-Region (strongly recommended) | CloudTrail multi-Region trail | Full coverage + global service events (IAM/STS/CloudFront) | Marginally more volume (management first copy still free) | Essentially always |
| Single-Region | CloudTrail single-Region trail (CLI only; console always creates multi-Region) | Narrow scope for highly isolated scenarios | MISSES global service events unless home = us-east-1; blind to other Regions | Rare, tightly scoped edge cases only |

**Critical fact since 2021-11-22**: Global service events (IAM, STS, CloudFront) are recorded only in **us-east-1**. A single-Region trail in any other Region will silently miss all IAM and STS API calls.

**Operational burden**: Multi-Region = one config; single-Region = per-Region sprawl and audit gaps as the estate grows.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html (accessed 2026-07-31)

---

## AF-5 — CloudTrail vs. AWS Config vs. Security Hub (Overlapping Concerns)

**Ask the architect**: "Do you need the API activity record (CloudTrail), the configuration-state history (Config), the posture score (Security Hub) — or all three composed together?"

| Option | AWS Service | What it answers | Optimizes | Not a substitute for |
|--------|-------------|-----------------|-----------|----------------------|
| AWS CloudTrail | CloudTrail | "Who did what, when, from where" — API call record | Audit trail, forensics, incident response | Config-state history; posture scoring |
| AWS Config | AWS Config | Resource configuration state + drift over time; compliance rules | Config compliance + change history | API-call audit log |
| Security Hub CSPM | AWS Security Hub | Aggregated posture findings vs FSBP/CIS/NIST/PCI | Central posture management + scoring | CloudTrail or Config data as inputs |

**Composition model**: Security Hub sits on top and aggregates; CloudTrail + Config are the evidence sources beneath it. All three use delegated administrators in the same security/audit account.

**Cost**: Three separate services — Config per-evaluation, Security Hub per-check + finding ingestion, CloudTrail per event model. They complement each other; turning one off degrades the others.

**Export**: All findings exportable via EventBridge / Amazon Security Lake (OCSF format) for SIEM integration.

Source: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudtrail-controls.html (accessed 2026-07-31)

---

## AF-6 — Centralized vs. Decentralized Log-Account Architecture

**Ask the architect**: "Can you stand up a dedicated Log Archive account that no workload team or audited principal can access, per AWS's separated-log-account guidance?"

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Centralized Log Archive account | Dedicated account + org trail + central S3/Lake | Segregation of duties, tamper resistance, single audit surface | Cross-account setup; central bucket policy rigor | Enterprise / regulated (AWS-recommended) |
| Decentralized (logs in each account) | Per-account S3 buckets | Local autonomy; simpler setup | Audited principals can tamper with own logs; fragmented audit; no single source of truth | Almost never for governance |

**Scaling**: Centralized + org trail auto-scales to new accounts; decentralized requires per-account effort and has coverage drift.

**Bucket policy rigor for centralized**: The central bucket policy must use `aws:SourceArn` to restrict CloudTrail write; least-privilege read for auditors only; no delete/overwrite for any audited account principal; combined with S3 Object Lock.

**If the answer is "we cannot stand up a dedicated account"**: Compensate with Object Lock + `aws:SourceAccount`-scoped bucket policy + very tight IAM permissions, and flag as a risk to the security team.

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html (accessed 2026-07-31)
