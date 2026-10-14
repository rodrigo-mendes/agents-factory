# Evaluation Scenarios — optimizing-aws-costs

> Source skill: `optimizing-aws-costs`
> Framework: AWS Well-Architected Framework — Cost Optimization Pillar (June 27, 2024 + GA updates)
> Use with `/evaluating-skill-scenarios optimizing-aws-costs`

---

## Scenario 1 — Canonical: Pricing Model Selection for Mixed Workload

```json
{
  "skills": ["optimizing-aws-costs"],
  "query": "We have a multi-account AWS setup. Production runs steady EC2 instances (t3.large, same family, us-east-1). We also have batch data processing jobs on EMR that run 3x per day for 2 hours each. How should we price the compute?",
  "expected_behavior": [
    "Recommends Instance Savings Plans for the steady EC2 production baseline (same family + Region stable)",
    "Recommends EC2 Spot for EMR worker nodes (stateless, fault-tolerant batch workload)",
    "Recommends purchasing Savings Plans at management account level, not workload account",
    "Does NOT recommend Spot for production stateful services",
    "Asks or confirms that EMR workload handles Spot interruption gracefully before recommending Spot"
  ]
}
```

---

## Scenario 2 — Canonical: Dev/Test Cost Reduction

```json
{
  "skills": ["optimizing-aws-costs"],
  "query": "Our dev and test environments run 24/7. We have EC2 instances and an RDS Aurora PostgreSQL 16.3 database in each environment. What should we do to reduce costs?",
  "expected_behavior": [
    "Recommends AWS Instance Scheduler to stop EC2 and RDS instances off-hours (~75% savings per official design principle)",
    "Recommends Aurora Serverless v2 with minimum 0 ACU and auto-pause for dev/test Aurora PostgreSQL 16.3 (eligible engine version, GA November 2024)",
    "Explains that Aurora Serverless v2 scale-to-zero requires minimum 0 ACU + auto-pause (not just min > 0 ACU)",
    "Does NOT recommend Aurora Serverless v1 (deprecated)",
    "Does not recommend scale-to-zero for production without first asking about resume latency tolerance"
  ]
}
```

---

## Scenario 3 — Canonical: FinOps Governance Setup

```json
{
  "skills": ["optimizing-aws-costs"],
  "query": "We have 15 AWS accounts under an AWS Organization. Teams complain they can't see their own costs and can't attribute spend to products. What architecture should we implement?",
  "expected_behavior": [
    "Recommends mandatory tag schema (owner, workload, environment) enforced via AWS Config rules or SCPs",
    "Explicitly states Cost Allocation Tags must be activated in Billing console (not just applied to resources)",
    "Recommends Cost Explorer per-owner cost dashboards based on activated tags",
    "Recommends AWS Budgets alerts per owner/workload with SNS notifications",
    "Mentions Cost & Usage Report (CUR) as the data source for tag coverage analysis"
  ]
}
```

---

## Scenario 4 — Edge Case: Reserved Instances vs Savings Plans for RDS

```json
{
  "skills": ["optimizing-aws-costs"],
  "query": "A developer suggests using Compute Savings Plans to cover our RDS PostgreSQL production database. Is that correct?",
  "expected_behavior": [
    "Corrects the suggestion: Compute Savings Plans do NOT cover RDS (they cover EC2, Fargate, and Lambda only)",
    "Recommends Reserved Instances for RDS (the correct commitment vehicle for non-EC2 managed services)",
    "Explains the key distinction: Savings Plans = EC2/Fargate/Lambda; Reserved Instances = RDS/ElastiCache/Redshift/DynamoDB/OpenSearch",
    "Does not recommend EC2 Reserved Instances for the RDS use case (those apply to EC2)"
  ]
}
```

---

## Scenario 5 — Anti-Pattern Trap: Spot for Primary Database

```json
{
  "skills": ["optimizing-aws-costs"],
  "query": "We want to reduce costs. Can we run our primary production PostgreSQL RDS database on Spot instances to get the 90% discount?",
  "expected_behavior": [
    "Clearly flags this as a Never-Do anti-pattern (HIGH risk)",
    "Explains that Spot instances receive a 2-minute interruption notice with no grace period — a primary database cannot tolerate abrupt termination",
    "States the impact: data loss; availability incident",
    "Recommends Reserved Instances for the steady-state production RDS database instead",
    "Does NOT suggest Spot as even a partial solution for the primary stateful database"
  ]
}
```

---

## Scenario 6 — Edge Case: Savings Plans Over-Commitment Guard

```json
{
  "skills": ["optimizing-aws-costs"],
  "query": "Our FinOps team wants to target 90% Savings Plans coverage to maximize discounts. How should we approach buying Savings Plans?",
  "expected_behavior": [
    "Warns against targeting a fixed coverage percentage (e.g., 90%) — it can drive over-commitment if usage patterns shift",
    "Recommends the potential-savings threshold approach: act when projected savings exceed 20% rather than chasing a fixed coverage %",
    "Recommends purchasing in small increments and reviewing every 2–4 weeks",
    "Recommends purchasing at management account level for maximum organization-wide discount application",
    "References Cost Explorer utilization/coverage reports (net-savings column) and Cost Optimization Hub as the verification surface"
  ]
}
```
