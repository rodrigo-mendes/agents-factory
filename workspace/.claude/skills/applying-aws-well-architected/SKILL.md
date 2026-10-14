---
name: applying-aws-well-architected
description: "Applies AWS Well-Architected Framework (Nov 2024 edition, six pillars) patterns to evaluate and design production AWS workloads. Use when designing, reviewing, or improving AWS cloud architectures for security, reliability, performance, cost, operational excellence, or sustainability."
---

## Function
Specialist in AWS Well-Architected Framework for multi-account production workloads on AWS — Nov 6, 2024 edition, six pillars.

## Version Context

**Framework**: AWS Well-Architected Framework
**Target edition**: November 6, 2024 (current stable — no 2025/2026 edition exists)
**Release date**: 2024-11-06
**Support status**: Active

**Key changes in Nov 2024 edition**:
- Operational Excellence expanded from 5 to **8 design principles** (added: managed services; AI-assisted ops via Amazon Q Business OPS02-BP02)
- New Sustainability best practice SUS06-BP01: cascade sustainability goals to teams
- Resource Control Policies (RCPs) launched Nov 13, 2024 — resource-centric complement to SCPs; ~40 services as of 2026-08-27

**Deprecated**:
- References to only 5 OE design principles are stale (pre-Nov 2024). Reject any source that cites 5.

⚠️ **CRITICAL — Agent Warning**:
This skill targets the **Nov 6, 2024 edition** of the AWS Well-Architected Framework.
Reject ANY patterns or principle counts from pre-Nov 2024 editions.
Do not mix pre-Nov 2024 guidance with the current stable edition.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — 10 mandatory patterns, 4 decisions, 11 anti-patterns
- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Full mandatory patterns with verification commands
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Full anti-patterns with detection and impact
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 4 architectural decision matrices
- **[Reference Architectures](./blueprints/reference-architectures.md)** — Three-tier HA, serverless, multi-account landing zone
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases
- **[Verification Loop](#verification-loop)** — Architecture review CLI checklist
- **[Quick Reference](#quick-reference)** — Six pillars and critical limits
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For full details and verification commands, see [Always Do Patterns](./blueprints/always-do-patterns.md).

- **Multi-Account Workload Separation** (SEC01-BP01) — One AWS account per workload × environment under named OUs. Management account holds no workloads. Required prerequisite for all other WAF improvements; blast radius containment; SCPs/RCPs enforce guardrails org-wide.
- **Federated Human Access via IAM Identity Center** — All human access via Identity Center SSO with permission sets; zero IAM users with long-term access keys for humans; STS temporary credentials only.
- **IAM Roles for All Workload Identities** — EC2 instance profiles, Lambda execution roles, ECS task roles, EKS Pod Identity. Never embed access keys in application code, environment variables, or AMIs.
- **Phishing-Resistant MFA for IAM and Root Users** — Register FIDO2 hardware security key on root; delete root access keys; SCP to deny sensitive API calls without MFA. TOTP and SMS MFA are not sufficient (SIM swap and phishing risks).
- **Encryption at Rest with AWS KMS** (SEC08-BP01/02) — Enable KMS for all EBS volumes, S3 buckets, RDS instances, DynamoDB tables, and SQS queues. Audit key usage via CloudTrail + CloudWatch Logs Insights.
- **Continuous Detection Stack** (SEC04-BP01–BP04) — CloudTrail org trail (Log Archive account, immutable S3) + GuardDuty org-wide (delegated admin in Audit account) + Security Hub + AWS Config in all accounts. Enable from day 1; MTTD degrades to weeks without it.
- **Multi-AZ Deployment for All Production Compute** (REL10-BP01) — Span stateless compute across ≥2 AZs behind an ELB. Enable Multi-AZ explicitly on RDS and ElastiCache (S3 and DynamoDB are Multi-AZ by default).
- **Centralized Backup for All Critical Data** (REL09-BP01) — AWS Backup plans covering all critical resources in all accounts; S3 versioning; DynamoDB and RDS PITR; test restores at minimum quarterly.
- **Infrastructure as Code for All Resources** (OE design principle 3) — All production infrastructure in CloudFormation/CDK, committed to Git, deployed via CI/CD. No console-only production changes.
- **Elastic Scaling to Match Demand** (REL-AD-4 / PE-AD-3 / CO-AD-1 / SUS-AD-B) — Define scaling policies on business KPI metrics, not just CPU. Set minimum capacity for availability; set maximum capacity to cap cost.

### ⚠️ Ask First

For option tables and tradeoff matrices, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **DR Strategy Selection** — Ask: "What is the business cost of 1 hour of downtime and 1 hour of data loss?" Then select: Backup & Restore (hours RTO, lowest cost) → Pilot Light → Warm Standby → Multi-Site Active/Active (<1 min RTO/RPO, 3–5x cost). Never assume a tier without a defined RTO/RPO SLA.
- **Compute Type Selection per Component** — Ask: "Is the workload event-driven or long-running, stateless or stateful?" Lambda for event-driven <15 min; Fargate for containers without node management; ECS/EKS EC2 for GPU/Spot; Graviton for 30% perf + 40% price-perf over x86.
- **Pricing Model Mix for Stable vs Variable Workloads** — Ask: "Has this workload run for ≥3 months with stable CPU patterns?" Only then recommend Compute Savings Plans (up to 66%). Spot for fault-tolerant burst (up to 90%). On-Demand for unpredictable spikes only.
- **Data Store Selection per Access Pattern** — Ask: "What is the primary access pattern: KV lookup, full-text search, relational join, or time-series?" Aurora/RDS for ACID; DynamoDB for single-digit ms KV; ElastiCache for sub-ms cache; S3 for unstructured; OpenSearch for full-text/aggregations.

### 🚫 Never Do

For detection commands and full impact analysis, see [Never Do Patterns](./blueprints/never-do-patterns.md).

| Anti-Pattern | Risk | Alternative |
|---|---|---|
| Long-term static access keys for humans | CRITICAL | IAM Identity Center + STS temporary credentials |
| Root user for daily operations | CRITICAL | Hardware MFA passkey on root; lock root; use only for the 4 tasks requiring it |
| Multiple unrelated workloads in one AWS account | CRITICAL | One account per workload × environment under Organizations OUs |
| Single-AZ production deployment | CRITICAL | EC2 Auto Scaling + ELB spanning ≥2 AZs; RDS/ElastiCache Multi-AZ |
| No disaster recovery plan | CRITICAL | Define RTO/RPO SLA; select DR tier; implement + test quarterly |
| Manual click-ops production changes | CRITICAL | CloudFormation/CDK + Git + CI/CD pipeline for all infra changes |
| 100% On-Demand pricing for stable compute | HIGH | Compute Savings Plans for baseline + Spot for fault-tolerant burst |
| Static over-provisioning instead of elastic scaling | HIGH | Auto Scaling + CloudWatch KPI alarms; Compute Optimizer 14-day+ cycle |
| Shared NAT gateway across Availability Zones | HIGH | One NAT gateway per AZ; route each private subnet to its own AZ's NAT |
| NAT/IGW for S3 or DynamoDB from private subnets | MEDIUM | Free S3 and DynamoDB gateway VPC endpoints on all private route tables |
| Spot instances for stateful or uninterruptible workloads | HIGH | On-Demand or Reserved Instances for stateful workloads; Spot for stateless batch only |

---

## Integration Patterns

For full reference architectures with service composition tables, see [Reference Architectures](./blueprints/reference-architectures.md).

**Reference architecture summaries**:
- **Three-Tier HA Web Application** — Route 53 → CloudFront + WAF + Shield → ALB (multi-AZ) → EC2 Auto Scaling / ECS Fargate → RDS Multi-AZ / Aurora → ElastiCache Multi-AZ → S3. ELB is the single entry point; no direct EC2 exposure.
- **Serverless Web / API** — CloudFront + S3 (SPA) → Cognito → API Gateway → Lambda → DynamoDB; EventBridge for async decoupling; SQS for load leveling. DynamoDB PITR from day 1.
- **Multi-Account Landing Zone** — Organizations → Control Tower → IAM Identity Center → CloudTrail org trail → GuardDuty + Security Hub (Audit account delegated admin) → Transit Gateway (Network account) → one account per workload × env.

**Cloud-native design patterns**:
- **Event-Driven (EventBridge)** — Decouples producers/consumers; up to 5 targets per rule; EventBridge Pipes for point-to-point. Requires event schema discipline.
- **Circuit Breaker** — Step Functions + DynamoDB CircuitStatus table (TTL auto-reset); CLOSED/OPEN/HALF-OPEN states; prevents cascade failures from downstream outages.
- **Queue-Based Load Leveling (SQS)** — Absorbs traffic spikes; CloudWatch queue-depth alarm → Auto Scaling consumers; at-least-once delivery — consumers must be idempotent.
- **CQRS** — Separate write/read stores (e.g., DynamoDB → Streams → Lambda → Aurora); results in eventual consistency — confirm business acceptability before adopting.

**Common problems**:
- **Control Tower v4.0 mandatory controls not active** → Verify active controls per version; mandatory controls are NOT applied by default from v4.0.
- **Savings Plans not sharing org-wide discounts** → Buy Savings Plans in the management account (no workloads there), not in workload accounts.
- **Unnecessary cost for S3/DynamoDB from private subnets** → Replace NAT/IGW routes with free gateway VPC endpoints; interface endpoints needed only for on-premises access via Direct Connect/VPN.

---

## Verification Loop

Run after designing or reviewing an AWS architecture:

### 1. Multi-Account Structure
```bash
aws organizations list-accounts --query 'Accounts[*].[Name,Status]'
# Expected: separate accounts per workload × environment; management account has no workloads
```

### 2. Security Baseline
```bash
# IAM users with active access keys (expected: no output for humans)
aws iam generate-credential-report
aws iam get-credential-report --output text --query Content | base64 -d \
  | awk -F',' 'NR>1 && ($9=="true" || $12=="true") {print $1,$9,$12}'

# GuardDuty org-wide coverage
aws guardduty list-detectors
# Expected: detector present with OrganizationConfiguration enabled
```

### 3. Multi-AZ Verification
```bash
# Auto Scaling groups — expect ≥2 AZs per production group
aws autoscaling describe-auto-scaling-groups \
  --query 'AutoScalingGroups[*].[AutoScalingGroupName,AvailabilityZones]'

# RDS Multi-AZ — expect true for all production instances
aws rds describe-db-instances \
  --query 'DBInstances[*].[DBInstanceIdentifier,MultiAZ]'
```

### 4. VPC Cost Check
```bash
# Verify S3/DynamoDB gateway endpoints on private route tables
aws ec2 describe-route-tables \
  --query 'RouteTables[*].Routes[?DestinationPrefixListId!=null].[DestinationPrefixListId,GatewayId]'
# Expected: pl-* routes pointing to vpce-* (gateway endpoint), not nat-* or igw-*
```

**Troubleshooting**:
- `WAF review HIGH risk on SEC01` → Multi-account structure is a mandatory prerequisite; all other WAF improvements are blocked until resolved.
- `GuardDuty findings not aggregating in Security Hub` → Check delegated administrator configuration in Audit account; Config aggregator must be enabled org-wide.
- `RDS not Multi-AZ` → `aws rds modify-db-instance --multi-az --apply-immediately`; note brief failover during the change window.

---

## Quick Reference

**WAF Six Pillars**:

| Pillar | Primary Focus | Key AWS Services |
|--------|--------------|-----------------|
| Operational Excellence | IaC, observability, 8 design principles | CloudFormation, CDK, CloudWatch, Systems Manager |
| Security | Identity, detection, data protection | IAM Identity Center, GuardDuty, KMS, Security Hub |
| Reliability | Multi-AZ, DR, backup, elastic scaling | Auto Scaling, ELB, RDS Multi-AZ, AWS Backup, Route 53 ARC |
| Performance Efficiency | Compute selection, right-sizing | EC2 Graviton, Lambda, Fargate, ECS/EKS, Compute Optimizer |
| Cost Optimization | Pricing model mix, right-sizing | Savings Plans, Spot, Cost Optimization Hub, Trusted Advisor |
| Sustainability | Energy efficiency, elastic usage | Graviton, Instance Scheduler, S3 Intelligent-Tiering, Carbon Footprint Tool |

**Critical limits**:

| Resource | Limit | Note |
|---|---|---|
| OE design principles | 8 (not 5) | Reject any source citing 5 — pre-Nov 2024 stale |
| Spot interruption notice | 2 minutes | Hard limit; stateful workloads must not use Spot |
| NAT Gateway throughput | 5–100 Gbps (auto-scales) | AZ-specific — one per AZ required |
| DynamoDB Global Tables replication lag | Typically <1 second | For Active/Active RTO/RPO planning |
| Aurora Global DB secondary promotion | <1 minute | For Warm Standby / Active-Active DR |
| Lambda max timeout | 15 minutes | Use Fargate/ECS for longer workloads |
| EventBridge rule targets | 5 per rule | Use SQS fan-out for more consumers |
| Control Tower v4.0 mandatory controls | NOT active by default | Verify active controls per version |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/applying-aws-well-architected/
├── SKILL.md                              <- This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md             <- 10 mandatory patterns with verification commands
    ├── ask-first-decisions.md            <- 4 decision matrices with option tradeoffs
    ├── never-do-patterns.md              <- 11 anti-patterns with detection and impact
    ├── reference-architectures.md        <- 3 reference architectures with full service tables
    └── evaluation-scenarios.md           <- 6 test cases
```

---

## External Resources

### Official Documentation
- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/) — Primary reference (Nov 6, 2024 edition)
- [WAF Nov 2024 Update Blog](https://aws.amazon.com/blogs/architecture/announcing-updates-to-the-aws-well-architected-framework-guidance-3/) — 2024-11-06; 8 OE principles, SUS06-BP01, 78 refreshed best practices
- [Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/) — SEC01–SEC10
- [Reliability Pillar](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/) — REL01–REL13
- [Cost Optimization Pillar](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/) — COST01–COST10 (last updated 2024-06-27)
- [Performance Efficiency Pillar](https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/) — last updated 2024-11-06
- [Sustainability Pillar](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/) — SUS01–SUS06

### Security & Best Practices
- [DR Workloads on AWS Whitepaper](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html) — 2022-04-01; current stable DR strategy reference
- [AWS Security Reference Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/architecture.html) — Multi-account landing zone blueprint
- [Resource Control Policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html) — Launched Nov 13, 2024
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html) — Credential management, roles, MFA
- [Serverless Applications Lens](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/) — WAF lens for Lambda/API Gateway workloads

> This skill targets the **Nov 6, 2024 edition**. Review after **2027-08-27** or when AWS announces a new WAF edition.
