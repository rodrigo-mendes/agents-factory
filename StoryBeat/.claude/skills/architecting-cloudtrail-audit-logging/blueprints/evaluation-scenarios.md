# Evaluation Scenarios — architecting-cloudtrail-audit-logging

```json
{
  "skills": ["architecting-cloudtrail-audit-logging"],
  "scenarios": [
    {
      "id": "S1-canonical-new-org-trail",
      "label": "Canonical: New multi-account org trail design",
      "query": "We are setting up AWS CloudTrail for the first time on a 15-account AWS Organizations estate. What is the recommended architecture?",
      "expected_behavior": [
        "Recommends a single multi-Region organization trail from the management or delegated-admin account (M1: IsMultiRegionTrail=true, IsOrganizationTrail=true, IncludeGlobalServiceEvents=true)",
        "Specifies a dedicated S3 bucket in a separate log-archive account, not a workload account (M2)",
        "Includes SSE-KMS customer managed key for encryption (M4)",
        "Includes log file integrity validation (M3: EnableLogFileValidation=true)",
        "Includes CloudWatch Logs integration for real-time alerting on high-risk events (M6)",
        "Mentions GuardDuty and Security Hub CSPM as complementary controls (M7)",
        "Does NOT recommend CloudTrail Lake for new customers (A6)"
      ]
    },
    {
      "id": "S2-canonical-verification",
      "label": "Canonical: Verifying an existing CloudTrail configuration",
      "query": "How do I verify that our CloudTrail setup meets security best practices?",
      "expected_behavior": [
        "Provides aws cloudtrail describe-trails query filtering for IsOrganizationTrail=true and IsMultiRegionTrail=true",
        "Provides aws cloudtrail validate-logs command with expected output",
        "References Security Hub CloudTrail.1 through CloudTrail.7 controls",
        "References AWS Config managed rules: multi-region-cloudtrail-enabled, cloud-trail-encryption-enabled, cloud-trail-log-file-validation-enabled, cloud-trail-cloud-watch-logs-enabled",
        "Explains what failure of each control indicates and the corrective action"
      ]
    },
    {
      "id": "S3-edge-existing-lake-customer",
      "label": "Edge case: Existing CloudTrail Lake customer post-2026-05-31",
      "query": "We are an existing CloudTrail Lake customer. Can we still use Lake and should we migrate?",
      "expected_behavior": [
        "Confirms existing Lake customers continue to have the service — it is NOT shut down, only closed to NEW customers",
        "Notes that existing org-level EDS will continue to capture new member accounts and new Regions",
        "Warns that account-level EDS will NOT cover newly added accounts — migrate to org-level EDS",
        "Recommends planning migration to CloudWatch or S3+Athena for new analytics workloads",
        "Does NOT tell an existing customer to immediately shut down their Lake setup"
      ]
    },
    {
      "id": "S4-edge-data-events-cost",
      "label": "Edge case: Data-event coverage and cost control",
      "query": "We need data-access audit for our S3 buckets that hold PII. How do we enable this without blowing the budget?",
      "expected_behavior": [
        "Recommends advanced event selectors to scope to specific buckets and specific operations (PutObject, DeleteObject, GetObject) rather than enabling all S3 data events",
        "Mentions 2025-11-24 data-event aggregation feature for reducing monitoring cost at scale",
        "Asks or clarifies: which specific buckets hold PII? (D2 Ask-First)",
        "Notes data events are billed separately and opt-in — not enabled by default",
        "Optionally recommends Insights for data events for anomaly detection if budget permits"
      ]
    },
    {
      "id": "S5-antipattern-trap-single-region",
      "label": "Anti-pattern trap: Single-Region trail proposal",
      "query": "Our team wants to create a CloudTrail trail only in eu-west-1 to save cost. Is that okay?",
      "expected_behavior": [
        "Flags this as anti-pattern A2 — single-Region trail silently drops IAM/STS/CloudFront global service events (which land in us-east-1)",
        "Explains that all other enabled Regions' activity is missed",
        "Recommends multi-Region trail (IsMultiRegionTrail=true) — console-created trails are multi-Region by default",
        "Notes that detection command: aws cloudtrail describe-trails --query 'trailList[?IsMultiRegionTrail==false]' would surface this gap",
        "Does NOT accept the cost-saving rationale without flagging the security blind spots"
      ]
    },
    {
      "id": "S6-antipattern-trap-lake-newbuild",
      "label": "Anti-pattern trap: New Lake EDS design in 2026",
      "query": "I want to create CloudTrail Lake event data stores for our new AWS account to store 7 years of audit logs. What CloudTrail Lake configuration should I use?",
      "expected_behavior": [
        "Immediately flags anti-pattern A6: CloudTrail Lake is closed to new customers from 2026-05-31",
        "Refuses to design a new CloudTrail Lake EDS for a non-existing-customer account",
        "Redirects to Amazon CloudWatch (recommended analytics target for 2026) or S3 + Athena",
        "Confirms that CloudTrail trails (for delivery) are unaffected and remain the correct durable delivery primitive",
        "Provides the Lake availability change documentation reference"
      ]
    }
  ]
}
```
