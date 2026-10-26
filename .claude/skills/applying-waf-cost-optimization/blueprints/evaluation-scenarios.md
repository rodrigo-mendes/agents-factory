# Evaluation Scenarios — applying-waf-cost-optimization

Test cases for `/evaluating-skill-scenarios applying-waf-cost-optimization`.

---

## Scenario 1 — Canonical: FinOps governance setup for a new AWS workload

```json
{
  "skills": ["applying-waf-cost-optimization"],
  "query": "We are launching a new B2B SaaS product on AWS. The engineering team has full On-Demand EC2 instances, no cost attribution, and no alerts. What should we do to align with the Cost Optimization Pillar?",
  "expected_behavior": [
    "Identifies absence of Cloud Financial Management (COST 1) as the root gap and recommends establishing a funded FinOps function first",
    "Recommends multi-account structure via AWS Organizations / Control Tower for cost attribution (COST 2)",
    "Prescribes mandatory tag taxonomy (cost center, owner, environment, workload) and activation of cost allocation tags in Billing console",
    "Recommends configuring AWS Budgets (forecast + actual) and Cost Anomaly Detection monitors",
    "Does NOT recommend Savings Plans / Reserved Instances before right-sizing data is gathered (Compute Optimizer must come first)",
    "References COST 1, COST 2, COST 3 question alignment explicitly or implicitly"
  ]
}
```

---

## Scenario 2 — Canonical: Pricing model selection for a steady production workload

```json
{
  "skills": ["applying-waf-cost-optimization"],
  "query": "Our production ECS cluster runs 50 Fargate tasks 24/7. We are paying fully On-Demand. How should we reduce this cost?",
  "expected_behavior": [
    "Identifies 24/7 steady baseline as a Compute Savings Plans candidate (not Reserved Instances, because Fargate is not RI-eligible)",
    "Recommends measuring actual baseline utilization with Compute Optimizer before committing",
    "Explains Compute Savings Plans discount (~72% off) and the 1- or 3-year spend commitment",
    "Flags that commitment purchase is an Ask-First decision — asks about commercial terms (EDP) and whether utilization will remain stable over the term",
    "Does NOT recommend Spot for ECS Fargate production tasks without confirming they are stateless/fault-tolerant"
  ]
}
```

---

## Scenario 3 — Edge case: Batch/HPC workload requesting maximum cost reduction

```json
{
  "skills": ["applying-waf-cost-optimization"],
  "query": "We run nightly genomics batch jobs on EC2 that take 4–6 hours and can restart from a checkpoint. What is the cheapest way to run these?",
  "expected_behavior": [
    "Recommends EC2 Spot Instances as the primary compute for stateless/checkpoint-tolerant batch (up to ~90% off)",
    "Recommends EC2 Auto Scaling group with mixed instance types and capacity-optimized allocation strategy to improve Spot availability",
    "Notes the 2-minute interruption notice and confirms the checkpoint architecture handles this",
    "Recommends On-Demand fallback for capacity gaps (mixed instances policy)",
    "Does NOT recommend Savings Plans/RIs as the primary mechanism for a fault-tolerant batch workload"
  ]
}
```

---

## Scenario 4 — Edge case: Data transfer cost spike

```json
{
  "skills": ["applying-waf-cost-optimization"],
  "query": "Our AWS bill suddenly jumped by 40% and the biggest line item is 'Data Transfer'. What should we investigate and fix?",
  "expected_behavior": [
    "Instructs the user to analyze data-transfer line items in CUR / Cost Explorer broken down by type (cross-AZ, internet egress, NAT gateway)",
    "Identifies missing VPC Gateway/Interface endpoints for S3/DynamoDB as a likely NAT-gateway egress source",
    "Recommends CloudFront in front of public-facing origins to reduce internet egress from the origin",
    "Identifies cross-AZ chatty traffic as a potential source and recommends AZ-affinity for internal services",
    "References COST 8 explicitly or implicitly",
    "Does NOT recommend a single generic fix without first attributing which category of data transfer is the culprit"
  ]
}
```

---

## Scenario 5 — Misuse/anti-pattern: Requester wants to move everything to Spot

```json
{
  "skills": ["applying-waf-cost-optimization"],
  "query": "To cut our AWS bill by 80%, I want to convert all our EC2 instances — including our RDS proxy, Kafka brokers, and API servers — to Spot. How do I do this?",
  "expected_behavior": [
    "Does NOT provide migration steps without a workload classification step",
    "Challenges the request: asks which workloads are stateful, stateless, or fault-tolerant before recommending Spot",
    "Explicitly flags that RDS proxy and Kafka brokers are stateful / not Spot-tolerant (Spot is only for stateless/fault-tolerant/batch workloads)",
    "Explains the 2-minute interruption notice and its impact on stateful services",
    "Offers a correct path: use Spot only for stateless API tier / batch / async workers; cover stateful steady services with Savings Plans/RIs; optionally rightsize before committing",
    "References the Never-Do anti-pattern for applying Spot indiscriminately"
  ]
}
```

---

## Scenario 6 — Misuse: Claiming a 2026 WAF Cost Optimization edition exists

```json
{
  "skills": ["applying-waf-cost-optimization"],
  "query": "Apply the 2026 AWS Well-Architected Cost Optimization Pillar guidance to my workload.",
  "expected_behavior": [
    "Explicitly states that no 2026 edition of the Cost Optimization Pillar exists as of research date 2026-08-27",
    "Informs the user that the current stable revision is the 2024-06-27 whitepaper",
    "Does NOT invent guidance from a non-existent 2026 edition",
    "Offers to apply the current stable 2024-06-27 guidance instead",
    "References the version note from the skill's Version Context section"
  ]
}
```
