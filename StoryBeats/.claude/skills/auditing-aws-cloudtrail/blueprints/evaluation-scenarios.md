# Evaluation Scenarios — auditing-aws-cloudtrail

> These scenarios test the skill's behavior across canonical, edge, misuse, and cost-governance cases.
> Run with `/evaluating-skill-scenarios auditing-aws-cloudtrail`.

---

## Scenario 1 — Canonical: Enterprise Multi-Account Audit Logging Setup

```json
{
  "skills": ["auditing-aws-cloudtrail"],
  "query": "Design the CloudTrail architecture for our 40-account AWS Organizations environment. We need to meet CIS AWS Foundations Benchmark v3.0 and Security Hub CSPM. We have a dedicated Log Archive account and a Security account. What do we need to build?",
  "expected_behavior": [
    "Recommends creating a multi-Region organization trail (IsMultiRegionTrail=true, IncludeGlobalServiceEvents=true, IsOrganizationTrail=true) from the Security account registered as CloudTrail delegated administrator",
    "Specifies Log Archive account S3 bucket as the delivery target with correct bucket policy using aws:SourceArn condition",
    "Lists all mandatory attributes: SSE-KMS (customer-managed key), EnableLogFileValidation=true, CloudWatchLogsLogGroupArn set",
    "Specifies S3 Object Lock (Compliance mode) on the Log Archive bucket — and explains it must be set at bucket creation",
    "References Security Hub controls CloudTrail.1–.7 and .10 with CIS v3.0 mappings",
    "Lists mandatory CloudWatch Logs metric filters: StopLogging/DeleteTrail, root usage, IAM policy changes",
    "Recommends deploying the four core AWS Config rules as a conformance pack org-wide",
    "Does NOT recommend enabling data events by default — asks which resources justify per-object logging"
  ]
}
```

---

## Scenario 2 — Edge: Opt-In Region and Global Service Events Trap

```json
{
  "skills": ["auditing-aws-cloudtrail"],
  "query": "We operate in ap-southeast-3 (Jakarta) exclusively — it's an opt-in Region. We created a CloudTrail trail there set to single-Region. Does this give us complete audit coverage?",
  "expected_behavior": [
    "Immediately flags that a single-Region trail in ap-southeast-3 silently misses IAM, STS, and CloudFront events — which have logged to us-east-1 only since 2021-11-22",
    "Explains this means all IAM role assumptions, console logins (STS), and CloudFront distribution changes would be invisible",
    "Recommends converting to a multi-Region trail (IsMultiRegionTrail=true, IncludeGlobalServiceEvents=true) to capture global service events regardless of the home Region",
    "Clarifies that if there are accounts in default-enabled Regions too, an organization trail with multi-Region coverage should be used",
    "Notes that in the opt-in Region partition context, a trail covers only Regions within the same partition — a separate trail is needed for any other partition",
    "Provides the correct CLI command to update the trail to multi-Region"
  ]
}
```

---

## Scenario 3 — Misuse / Anti-Pattern Trap: "Just Save Cost by Using a Single Account"

```json
{
  "skills": ["auditing-aws-cloudtrail"],
  "query": "To keep costs simple, we want to store CloudTrail logs in the same AWS account where our application runs. Each team manages their own trail in their own account. Is this fine for a PCI DSS environment?",
  "expected_behavior": [
    "Clearly refuses to endorse this pattern and explains it violates segregation of duties (NP-2 and NP-7)",
    "States that audited principals controlling the log store can tamper with or delete evidence of their own actions — this is an anti-pattern regardless of cost",
    "Notes per-account trails without an org trail create coverage drift — accounts can disable their own audit logging",
    "For PCI DSS specifically, highlights Requirement 10.5 (protect audit logs from modification) and that self-managed logs fail this requirement",
    "Proposes the correct architecture: dedicated Log Archive account, org trail from delegated admin, bucket policy scoped with aws:SourceArn, S3 Object Lock",
    "Does NOT dismiss cost concerns — suggests addressing them with S3 lifecycle tiering to Glacier Deep Archive and scoping data events with advanced selectors",
    "Does NOT proceed with the per-account design without explicitly flagging it as a compliance risk"
  ]
}
```

---

## Scenario 4 — Cost-Governance: High-Volume S3 Data Events Bill Shock

```json
{
  "skills": ["auditing-aws-cloudtrail"],
  "query": "We enabled S3 data events on our CloudTrail trail using aws:All resource type. Last month's bill was $18,000 just for data events on a bucket with 50 million daily object operations. How do we reduce this without losing compliance coverage?",
  "expected_behavior": [
    "Explains that aws:All (or a wildcard resource) captures every S3 Get/Put/Delete across all buckets at $0.10/100k events, which at 50M ops/day = 500M/day = $50/day = $1,500/month per bucket",
    "Recommends replacing basic selectors with advanced event selectors scoped to: (1) only sensitive/regulated buckets by ARN prefix, (2) writes only (readOnly=false) unless reads are also compliance-required",
    "Provides the correct advanced event selector JSON with field selectors for resources.ARN prefix and readOnly=false",
    "Suggests using CloudTrail Lake for long-retention analysis rather than dumping all data events to S3+Athena — Lake ingestion cost is per GB, not per event, which can be more predictable",
    "Recommends enabling Insights (ApiErrorRateInsight) to detect anomalous access patterns without needing full data event coverage on low-sensitivity buckets",
    "Does NOT recommend turning off data event logging entirely for regulated buckets — compliance for sensitive data stores requires per-object visibility",
    "Estimates the cost reduction from the proposed scoping change"
  ]
}
```
