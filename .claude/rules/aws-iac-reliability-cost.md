---
name: aws-iac-reliability-cost
description: "AWS reliability, networking, and cost guardrails for IaC artifacts (Terraform, CloudFormation, SAM, CDK). Use when reviewing or editing AWS infrastructure-as-code files for multi-AZ, networking, tagging, and cost patterns."
paths:
  - "**/*.tf"
  - "**/*.yaml"
  - "**/*.yml"
  - "**/*.json"
---

# AWS Reliability, Networking, and Cost Guardrails

Technical facts live in the aws-skills (`packages/aws-skills/.apm/skills/`). This rule references
skills; it does not duplicate their bodies. Tags `(unverified)` / `(medium confidence)` apply.

Source family rules: R07–R12 from `workspace/aws/_family_rules_v2026.md`.

## Always

- **R07 — One account per workload × environment.** IaC should not provision multiple unrelated
  workloads (different business domains) into a single AWS account. Use Organizations + Control
  Tower Account Factory for account vending.
  Skill: `architecting-aws-multi-account-organizations`.

- **R08 — All production infrastructure in IaC.** No resource should exist in production without
  a CloudFormation stack, CDK stack, or Terraform state tracking it. Drift detection must be
  enabled for all CloudFormation stacks.
  Skill: `applying-waf-operational-excellence-pillar`.

- **R09 — Multi-AZ for all production compute.** Auto Scaling Groups must list ≥2 AZs. RDS
  instances must set `MultiAZ: true`. ElastiCache replication groups must have
  `AutomaticFailoverEnabled: true` with ≥2 AZs.
  Skill: `applying-aws-reliability-pillar`, `designing-aws-vpc-networks`.

- **R10 — One NAT Gateway per AZ.** Each private subnet route table routes `0.0.0.0/0` to a
  NAT Gateway in the same AZ. Never share a single NAT Gateway ID across route tables in
  different AZs.
  Skill: `designing-aws-vpc-networks`.

- **R11 — Free S3 and DynamoDB Gateway VPC Endpoints on every VPC with private subnets.** Add
  `AWS::EC2::VPCEndpoint` (type `Gateway`) for `com.amazonaws.<region>.s3` and
  `com.amazonaws.<region>.dynamodb` and reference them in all private route tables.
  Skill: `designing-aws-vpc-networks`, `applying-aws-well-architected`.

- **R12 — Mandatory tagging on all billable resources.** All resources must carry at minimum:
  `Environment`, `Owner`, `CostCenter`, `Workload`, `ManagedBy`. Use CloudFormation Stack Tags
  or Terraform `default_tags` provider block to propagate tags automatically.
  Skill: `managing-aws-costs`, `optimizing-aws-costs`.

## Ask First

- **DR tier selection (RTO/RPO)** — ask the business cost of 1 hour of downtime and 1 hour of
  data loss before selecting Backup & Restore vs. Pilot Light vs. Warm Standby vs.
  Multi-Site Active/Active. See `applying-aws-reliability-pillar`.

- **Savings Plans vs. On-Demand vs. Spot** — ask whether the workload has run ≥3 months with
  stable CPU patterns before recommending Compute Savings Plans. See `optimizing-aws-costs`,
  `applying-waf-cost-optimization`.

- **Control Tower vs. DIY Organizations** — ask whether an existing landing zone or DIY setup
  is already in place. Retrofitting Control Tower onto a mature DIY setup is high-effort.
  See `architecting-aws-multi-account-organizations`.

## Never

- Single-AZ production deployment for stateful services → always Multi-AZ.
  See `applying-aws-reliability-pillar`.

- Shared NAT Gateway across AZs → one per AZ to eliminate cross-AZ charges and AZ-failure
  cascades. See `designing-aws-vpc-networks`.

- NAT Gateway or Internet Gateway for S3 or DynamoDB traffic from private subnets → use free
  Gateway VPC Endpoints. See `designing-aws-vpc-networks`.

- 100% On-Demand pricing for stable, predictable compute baseline → use Compute Savings Plans
  for the baseline and Spot for fault-tolerant burst. See `applying-waf-cost-optimization`.
