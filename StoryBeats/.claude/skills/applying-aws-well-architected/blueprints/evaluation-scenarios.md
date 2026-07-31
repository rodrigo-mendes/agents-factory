# Evaluation Scenarios — applying-aws-well-architected

> 4 test cases for validating the `applying-aws-well-architected` skill behavior.
> Use with `/evaluating-skill-scenarios applying-aws-well-architected`.

---

## Scenario 1 — Canonical: New SaaS API architecture review

```json
{
  "skills": ["applying-aws-well-architected"],
  "query": "We are launching a new multi-tenant SaaS API on AWS. We plan to use Lambda for compute, DynamoDB for data, and deploy everything in a single AWS account. What does the Well-Architected Framework require us to address before go-live?",
  "expected_behavior": [
    "References all 6 pillars: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability",
    "Flags AD-7 (multi-account governance): single-account deployment is insufficient for production; recommends separating prod/non-prod accounts via AWS Organizations",
    "Flags AD-1: confirms Lambda uses execution roles (not IAM user access keys)",
    "Flags AD-2: confirms DynamoDB encryption at rest and TLS in transit",
    "Flags AD-5: asks whether CloudWatch alarms are tied to business KPIs and CloudTrail is enabled",
    "Raises AF-3 (multi-tenant isolation): asks whether Pool/Silo/Bridge model has been decided and confirmed against compliance requirements",
    "Flags AD-8: asks about cost-allocation tagging and AWS Budgets before launch",
    "Does NOT assume a compute or datastore change without first resolving AF-1/AF-2 for the user's traffic pattern"
  ]
}
```

---

## Scenario 2 — Edge case: Enterprise tenant with strict data residency

```json
{
  "skills": ["applying-aws-well-architected"],
  "query": "A new enterprise customer requires that their data never share infrastructure with other tenants and must remain in eu-west-1. They also need SOC 2 Type II evidence. What isolation model and architecture should we use?",
  "expected_behavior": [
    "Recommends Silo isolation model (AF-3) — dedicated account per enterprise tenant, strongest isolation boundary",
    "Specifies AWS Organizations + Control Tower for lifecycle management of the dedicated tenant account",
    "Specifies CloudTrail organization trail with centralized immutable S3 archive for SOC 2 evidence (AD-7 / ND-7)",
    "Specifies deploying all resources in eu-west-1 only; mentions AWS Config rule to restrict resource creation to that Region via SCP",
    "Flags AD-2 encryption requirements for SOC 2: KMS CMK, RDS encryption, EBS default encryption",
    "Does NOT recommend Pool model for this scenario",
    "Raises AF-2 (datastore choice) to confirm whether relational or NoSQL fits the tenant's access patterns"
  ]
}
```

---

## Scenario 3 — Misuse / anti-pattern trap: IAM user access keys

```json
{
  "skills": ["applying-aws-well-architected"],
  "query": "Our team uses IAM user access keys stored in environment variables on EC2 instances because it is simpler than setting up roles. Is this acceptable for a production AWS workload?",
  "expected_behavior": [
    "Identifies ND-1 (long-lived IAM user access keys in application code/environment) as a Critical risk anti-pattern",
    "States that this violates the Security pillar principle 'Implement a strong identity foundation'",
    "Provides the ✅ Correct alternative: EC2 instance profile (IAM role attached to the instance), credentials obtained via AWS STS automatically",
    "Explains blast-radius consequence: leaked key = account-wide API access within the key's policy",
    "References detection: IAM Access Analyzer, AWS Config access-keys-rotated, Amazon GuardDuty UnauthorizedAccess findings",
    "Does NOT accept 'it is simpler' as justification — clearly marks the pattern as Never-Do",
    "Offers a remediation path: create IAM role, attach as instance profile, remove access keys from environment"
  ]
}
```

---

## Scenario 4 — Multi-pillar: Cost and sustainability optimization review

```json
{
  "skills": ["applying-aws-well-architected"],
  "query": "Our AWS bill has grown 40% in three months. We have EC2 instances running 24/7 in dev/test, no budget alerts, and no cost-allocation tags. We also want to reduce our carbon footprint. What should we do?",
  "expected_behavior": [
    "Identifies ND-6 (no cost guardrails): no AWS Budgets, no cost-allocation tags, oversized always-on dev instances",
    "Recommends AD-8 remediation: mandatory cost-allocation tags via Organizations tag policies; AWS Budgets per account; AWS Compute Optimizer quarterly review",
    "Recommends AWS Instance Scheduler to stop dev/test EC2 instances outside working hours (Cost Optimization + Sustainability pillar)",
    "Addresses Sustainability pillar: maximizing utilization (AD-8), using managed/serverless services to reduce idle resources",
    "Recommends AWS Cost Explorer anomaly detection + SNS alerts to catch future spikes early",
    "Raises AF-5 (purchasing model): if baseline EC2 workloads are predictable, Compute Savings Plans can reduce cost 40-72%",
    "Does NOT recommend switching cloud provider or rebuilding architecture as first step — starts with tagging, budgets, and right-sizing",
    "Does NOT claim specific discount percentages without flagging they are approximate maxima that vary by instance/Region"
  ]
}
```
