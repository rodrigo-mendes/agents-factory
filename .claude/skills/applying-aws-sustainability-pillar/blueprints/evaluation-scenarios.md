# Evaluation Scenarios — applying-aws-sustainability-pillar

Skill version: applying-aws-sustainability-pillar (Nov 2024 edition)
Purpose: Validate agent behavior when consuming this skill against canonical, edge, and misuse cases.

---

## Scenario 1 — Canonical: Production workload sustainability audit

```json
{
  "skills": ["applying-aws-sustainability-pillar"],
  "query": "We have a production workload on AWS: a Node.js API running on 10 always-on m5.xlarge EC2 instances with traffic peaking 2 hours per day. S3 buckets store 5 years of logs with no lifecycle policy. What should we address?",
  "expected_behavior": [
    "Identifies static over-provisioning as SUS-ND-1 — violates SUS02 / Maximize Utilization",
    "Recommends EC2 Auto Scaling with target-tracking or migration to Fargate/Lambda for spiky demand",
    "Identifies missing S3 Lifecycle rules as SUS-ND-3 — violates SUS04",
    "Recommends S3 Lifecycle rules transitioning to Intelligent-Tiering or Glacier with expiration for obsolete data",
    "Recommends running AWS Compute Optimizer to assess over-provisioned instances",
    "Recommends establishing per-unit CloudWatch KPIs per SUS06-BP01"
  ]
}
```

---

## Scenario 2 — Canonical: New architecture design for sustainability

```json
{
  "skills": ["applying-aws-sustainability-pillar"],
  "query": "We are designing a new event-driven data pipeline for AWS. How do we build it to align with the Sustainability Pillar from the start?",
  "expected_behavior": [
    "Recommends AWS Lambda or Fargate for event-driven workloads (scale-to-zero, SUS02-BP01)",
    "Recommends S3 with Lifecycle rules and Intelligent-Tiering for pipeline data (SUS04)",
    "Recommends Graviton instances if EC2 is required (SUS05)",
    "Recommends using managed services (SQS for queuing, Aurora Serverless for DB) instead of self-managed EC2 (SUS05)",
    "Recommends Region selection using Customer Carbon Footprint Tool (SUS01-BP01)",
    "Recommends establishing per-transaction CloudWatch custom KPI metrics from day one (SUS06-BP01)"
  ]
}
```

---

## Scenario 3 — Ask First: Region selection with latency constraint

```json
{
  "skills": ["applying-aws-sustainability-pillar"],
  "query": "Our company wants to reduce carbon footprint. Should we move our workload from us-east-1 to eu-north-1 which has a lower-carbon grid?",
  "expected_behavior": [
    "Does NOT give a direct yes/no recommendation without asking about constraints",
    "Asks about data-residency requirements before recommending Region migration",
    "Asks about latency SLA requirements and user geography",
    "References Decision A (Region: Carbon vs Latency vs Data Residency)",
    "Recommends using AWS Customer Carbon Footprint Tool to quantify the difference between Regions",
    "States that carbon, compliance, and latency must be resolved together — not independently"
  ]
}
```

---

## Scenario 4 — Ask First: Compute model for new service

```json
{
  "skills": ["applying-aws-sustainability-pillar"],
  "query": "We are debating between AWS Lambda and EC2 Graviton with Auto Scaling for a new microservice. Which is better from a sustainability perspective?",
  "expected_behavior": [
    "Does NOT declare one option unconditionally better",
    "Asks about the workload demand profile (spiky vs steady-state) per Decision B",
    "Explains Lambda / Fargate is optimal for spiky/event-driven (scale-to-zero eliminates idle baseline)",
    "Explains EC2 Graviton + Auto Scaling is optimal for sustained high-utilization (steady-state)",
    "Mentions cold-start latency as the trade-off for serverless",
    "Notes Graviton's performance-per-watt advantage over x86 if EC2 path is chosen"
  ]
}
```

---

## Scenario 5 — Anti-pattern trap: Fixed fleet for cost predictability

```json
{
  "skills": ["applying-aws-sustainability-pillar"],
  "query": "Our team wants to use a fixed fleet of EC2 instances for predictable pricing. Is this okay for sustainability?",
  "expected_behavior": [
    "Flags static over-provisioning as SUS-ND-1 — violates SUS02 / Maximize Utilization",
    "Clarifies that cost predictability and sustainable sizing are independent concerns",
    "Recommends AWS Savings Plans or Reserved Instances for cost predictability without static sizing",
    "Recommends running Compute Optimizer to establish the right-sized baseline first",
    "Notes that if demand is truly flat and sustained, right-size to appropriate Graviton instance type before committing",
    "States the decision should be documented in the architecture decision record"
  ]
}
```

---

## Scenario 6 — Edge case: Multi-Region globally distributed workload

```json
{
  "skills": ["applying-aws-sustainability-pillar"],
  "query": "We have a global SaaS product serving users in North America, Europe, and Asia-Pacific. Carbon footprint varies across our Regions. How do we handle Region selection for sustainability?",
  "expected_behavior": [
    "Acknowledges the multi-Region constraint where per-Region latency SLAs conflict with lowest-carbon selection",
    "Recommends Amazon CloudFront for static and cacheable content — reduces origin compute and downstream data volume globally",
    "Recommends placing dynamic workloads in nearest-user Regions to meet latency SLA",
    "Recommends accepting the carbon trade-off for latency-sensitive workloads but documenting it explicitly with Customer Carbon Footprint Tool data as evidence",
    "Recommends applying S3 Lifecycle policies aggressively in all Regions",
    "Recommends annual review cadence as AWS grid carbon intensity improves over time"
  ]
}
```
