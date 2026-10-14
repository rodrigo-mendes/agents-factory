# Evaluation Scenarios — applying-aws-well-architected

> Test cases for `/evaluating-skill-scenarios applying-aws-well-architected`.
> Covers: canonical use, architectural decision, anti-pattern traps, edge cases, and misuse.

---

## Scenario 1 — Canonical: New Greenfield Production Workload

```json
{
  "skills": ["applying-aws-well-architected"],
  "query": "We are building a new SaaS web application on AWS. What is the correct account structure and baseline security setup before deploying any workload?",
  "expected_behavior": [
    "Recommends AWS Organizations with Control Tower landing zone as the starting point",
    "Requires separate AWS accounts per workload × environment (prod, staging, dev) under named OUs",
    "Management account must hold no workloads",
    "Specifies Security OU with Log Archive and Audit accounts",
    "Requires enabling GuardDuty org-wide, CloudTrail org trail, Security Hub, and AWS Config from day 1",
    "Requires IAM Identity Center for all human access — no IAM users with long-term access keys",
    "Cites SEC01-BP01 as the mandatory prerequisite for all other WAF improvements"
  ]
}
```

---

## Scenario 2 — Architectural Decision: DR Strategy with Undefined RTO/RPO

```json
{
  "skills": ["applying-aws-well-architected"],
  "query": "Our architecture review flagged REL13. We need to add a DR strategy. What should we pick?",
  "expected_behavior": [
    "Does NOT select a DR tier without first asking about the RTO/RPO SLA",
    "Asks: 'What is the business cost of 1 hour of downtime and 1 hour of data loss?'",
    "Presents the four DR tiers: Backup & Restore, Pilot Light, Warm Standby, Multi-Site Active/Active",
    "Includes cost profile comparison (1x, 1.5x, 2x, 3-5x)",
    "Notes that Active/Active requires DynamoDB global tables or Aurora Global DB and costs 3-5x more",
    "Requires quarterly DR testing regardless of tier selected"
  ]
}
```

---

## Scenario 3 — Anti-Pattern Trap: Single-Account Multi-Environment Proposal

```json
{
  "skills": ["applying-aws-well-architected"],
  "query": "Our team wants to use a single AWS account for all environments (dev, staging, prod) and use IAM permission boundaries to isolate them. Is this acceptable?",
  "expected_behavior": [
    "Flags this as a CRITICAL anti-pattern (SEC-ND-3 / multiple unrelated workloads in one account)",
    "States that IAM permission boundaries cannot replace account-level blast-radius isolation",
    "Explains that a compromised IAM role, quota breach, or misconfigured Config rule in dev can affect production",
    "Requires account separation under AWS Organizations as a mandatory prerequisite — not an optional improvement",
    "Does NOT suggest workarounds within a single account for production isolation",
    "Recommends Control Tower Account Factory for automated account vending"
  ]
}
```

---

## Scenario 4 — Edge Case: RTO < 1 Minute with RPO < 30 Seconds Cross-Region

```json
{
  "skills": ["applying-aws-well-architected"],
  "query": "Our SLA requires RTO < 1 minute and RPO < 30 seconds across AWS Regions. What architecture achieves this?",
  "expected_behavior": [
    "Identifies Multi-Site Active/Active as the only viable DR tier for these SLAs",
    "Recommends DynamoDB global tables (typically <1 s replication lag) or Aurora Global Database (<1 s lag, <1 min secondary promotion)",
    "Specifies Route 53 latency routing + health checks + Application Recovery Controller (ARC) routing-control for traffic steering",
    "Recommends AWS Fault Injection Service (FIS) to validate actual RTO/RPO under failure conditions",
    "Asks whether the business cost justifies Active/Active (3-5x cost vs Backup & Restore)",
    "Notes that Aurora Global DB secondary promotion automation must be configured and tested"
  ]
}
```

---

## Scenario 5 — Anti-Pattern Trap: Static Access Keys in Application Configuration

```json
{
  "skills": ["applying-aws-well-architected"],
  "query": "Our Lambda function needs to access DynamoDB. The developer wants to store AWS access keys in Lambda environment variables. Is this the right approach?",
  "expected_behavior": [
    "Flags this as a CRITICAL anti-pattern (long-term static credentials in code/config)",
    "States that embedded access keys are a leading cause of credential leaks",
    "Recommends assigning an IAM execution role to the Lambda function directly",
    "Explains that Lambda receives temporary STS credentials automatically from the execution role",
    "States that no access keys in environment variables, code, or AMIs is a mandatory pattern",
    "Provides detection method: secret scanning in CI/CD (e.g., Amazon CodeGuru Security)"
  ]
}
```

---

## Scenario 6 — Edge Case: Sustainability-First Architecture with Carbon Reporting Requirements

```json
{
  "skills": ["applying-aws-well-architected"],
  "query": "We are designing a workload for a regulated industry that requires carbon footprint reporting and sustainability compliance. What specific architectural choices apply?",
  "expected_behavior": [
    "Recommends SUS01 Region selection using AWS Customer Carbon Footprint Tool before deployment",
    "Recommends Graviton4 (ARM) instances for 30% perf + 40% price-perf + 60% energy efficiency over x86",
    "Recommends serverless-first compute: Lambda, Fargate, Aurora Serverless v2 (scale-to-zero since Nov 2024 GA)",
    "Recommends S3 Intelligent-Tiering for automatic storage tier optimization",
    "Recommends Instance Scheduler for dev/test off-hours shutdown (approximately 75% energy savings)",
    "References SUS06-BP01 (Nov 2024 update): cascade sustainability goals to teams via OE runbook",
    "Asks whether the organization has a commitment to Customer Carbon Footprint Tool reporting before designing custom per-unit KPI tracking"
  ]
}
```
