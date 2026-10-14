---
name: applying-aws-reliability-pillar
description: "Architects multi-account AWS workloads using the Well-Architected Framework Reliability Pillar (November 2024 edition). Use when designing for AZ resilience, selecting a DR strategy (RTO/RPO), reviewing production workloads against REL best practices, or validating fault-isolation, backup, and recovery automation patterns."
---

## Function

Specialist in AWS Well-Architected Reliability Pillar for multi-account production workloads on AWS, covering fault isolation, DR strategy selection, elastic scaling, fault injection testing, and data backup/recovery patterns.

## Version Context

**Framework**: AWS Well-Architected Framework — Reliability Pillar
**Target edition**: November 6, 2024 (current stable)
**Research date**: 2026-08-27
**Valid until**: 2027-08-27
**Official source**: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/

**Key services confirmed current**:
- AWS Fault Injection Service (FIS) — chaos/failure testing
- Amazon Application Recovery Controller (ARC) — data-plane failover
- AWS Elastic Disaster Recovery — managed server DR (Pilot Light)
- AWS Resilience Hub — automated RTO/RPO posture assessment

**Companion whitepaper note**: DR strategy guidance (Backup & Restore / Pilot Light / Warm Standby / Multi-Site Active/Active) references the AWS DR whitepaper (last updated 2022-04-01 — current stable but >12 months; review for updates before use).

**Critical design principles preserved in this edition**:
1. Automatically recover from failure
2. Test recovery procedures via simulation
3. Scale horizontally to increase aggregate availability
4. Stop guessing capacity
5. Manage change in automation

> **Agent Warning**: This skill targets the November 2024 edition. Reject patterns from pre-2023 editions that predate ARC or FIS GA.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Three-tier operational rules
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test scenarios
- **[Integration Patterns](#integration-patterns)** — Cross-service composition summaries
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands
- **[Quick Reference](#quick-reference)** — DR strategy matrix and critical limits
- **[External Resources](#external-resources)** — Dated official links

---

## Blueprints & Guardrails

### ✅ Always Do

**REL-AD-1 — Deploy across multiple Availability Zones**
Configure EC2 Auto Scaling groups spanning ≥2 AZs (≥3 recommended). Enable cross-zone load balancing on ELB. Use RDS Multi-AZ with synchronous standby. Distribute VPC subnets across AZs. Single-AZ deployment is a CRITICAL anti-pattern (REL10-BP01).

**REL-AD-2 — Back up all critical data with cross-Region copy**
Enable AWS Backup plans with cross-Region copy to the DR Region. Enable S3 versioning + Cross-Region Replication (CRR) on critical buckets. Enable RDS automated backups with PITR. Enable DynamoDB PITR. Combine replication with independent backup — replication alone does not protect against corruption or deletion (REL09-BP01).

**REL-AD-3 — Monitor and manage service quotas proactively**
Monitor quota utilization via CloudWatch quota-usage metrics and Trusted Advisor. Request increases before reaching limits. Include quota planning in DR readiness reviews — the DR Region must have equivalent quotas pre-provisioned. Some quotas are hard limits; plan around them (Reliability Foundations).

**REL-AD-4 — Elastic scaling driven by KPI-based CloudWatch alarms**
Define Auto Scaling policies based on business-value KPIs, not raw infrastructure metrics alone. Use Application Auto Scaling for non-EC2 resources. Validate scale-out behavior under load test before production. Fixed/guessed capacity violates Design Principle 4 (Change Management).

**REL-AD-5 — Define, implement, and test a DR strategy with measured RTO/RPO**
Derive RTO/RPO from business impact analysis (REL13-BP01). Select the DR strategy whose achievable objectives match those targets (REL13-BP02). Define all DR infrastructure in IaC (CloudFormation/StackSets) to prevent configuration drift (REL13-BP04). Automate failover via ARC routing controls using data-plane operations only (REL11-BP04). Measure achieved RTO/RPO vs targets on every drill (REL13-BP03).

**REL-AD-6 — Test reliability via fault injection with stop conditions**
Create AWS FIS experiment templates for representative failure scenarios (AZ impairment, instance termination, network latency injection). Attach CloudWatch-based stop conditions to each experiment to auto-halt on real customer impact. Schedule game days via EventBridge. Record outcomes and validate automated recovery within RTO (Design Principle 2).

---

### ⚠️ Ask First

**Decision A — DR Strategy Selection**
Ask the business-defined RTO and RPO before recommending a strategy. Do not select based on cost alone.

| Strategy | RTO | RPO | Cost | When |
|----------|-----|-----|------|------|
| Backup & Restore | Hours | Hours | Lowest | Non-critical / cost-sensitive |
| Pilot Light | Tens of minutes | Minutes | Low | Moderate criticality, cost-conscious |
| Warm Standby | Minutes | Seconds | Higher | Business-critical, faster recovery |
| Multi-Site Active/Active | Near-zero | Near-zero | Highest | Mission-critical / global |

**Decision B — Failover Routing Mechanism**
Ask whether the DR runbook requires creating or modifying resources during failover. If yes, flag REL11-BP04 (control-plane dependency risk) and evaluate ARC routing controls. Route 53 DNS failover (TTL delay) vs ARC data-plane failover (immediate, control-plane-independent) vs Elastic Disaster Recovery (managed server-based DR).

**Decision C — Cross-Region Data Synchronization Tier**
Ask whether the data tier requires multi-Region active-active writes or active-passive reads: DynamoDB global tables (active-active, near-zero RPO, eventual consistency with conflict resolution) vs Aurora Global Database (active-passive, <1s replication lag, managed promotion <1 min) vs S3 CRR + versioning (object storage DR).

**Decision D — Single-Region (Multi-AZ) vs Multi-Region**
Ask whether the business requires protection against a full AWS Region outage AND whether data residency regulations permit cross-Region data transfer. Both must be confirmed before proposing multi-Region. Multi-AZ protects against AZ failure; multi-Region protects against regional loss.

---

### 🚫 Never Do

**REL-ND-1 — Single-AZ deployment in production** (CRITICAL)
Single-AZ means AZ failure = complete production outage with no automatic recovery.
Use instead: EC2 ASG spanning ≥2 AZs + ALB with cross-zone load balancing + RDS Multi-AZ.
Detection: `aws autoscaling describe-auto-scaling-groups` (confirm ≥2 AZs); `aws rds describe-db-instances` (confirm `MultiAZ: true`).

**REL-ND-2 — No DR plan or ad-hoc recovery** (CRITICAL)
Named anti-pattern in REL13-BP02. Without a pre-defined and tested plan, recovery objectives will not be met under pressure.
Use instead: RTO/RPO from business impact analysis, IaC-defined DR infrastructure, AWS Backup + Elastic Disaster Recovery, scheduled DR drills with recorded results.

**REL-ND-3 — Control-plane dependency during recovery** (CRITICAL)
Named anti-pattern in REL13-BP02 and REL11-BP04. The control plane may be degraded during the exact event requiring recovery.
Use instead: Data-plane operations only (ARC routing controls). Pre-provision all resources via IaC before a disaster — never create resources during the DR event.

**REL-ND-4 — Replication only without PITR or versioning** (HIGH)
Verbatim from REL13-BP02: replication does not protect against data corruption/deletion — both copies become unusable.
Use instead: Combine replication with AWS Backup PITR, S3 versioning, and DynamoDB PITR.

**REL-ND-5 — Fixed or guessed capacity without auto-scaling** (HIGH)
Violates Design Principle 4. Causes saturation-driven outages at demand peaks; wasted cost during low demand.
Use instead: AWS Auto Scaling + CloudWatch KPI-based alarms + proactive quota increase requests.

**REL-ND-6 — Never testing recovery procedures** (CRITICAL)
Named anti-pattern in REL13-BP03. Backups and failover mechanisms may be silently broken or misconfigured — discovered only during a real disaster.
Use instead: AWS FIS experiment templates with stop conditions, game days via EventBridge, restore-test records, measured RTO/RPO vs targets after every drill.

---

## Integration Patterns

**Multi-AZ Highly Available Web Application** — Route 53 (health-check DNS) → ALB (cross-zone, multi-AZ) → EC2 ASG (≥2 AZs) → RDS Multi-AZ + ElastiCache (multi-AZ) + S3. AWS Backup with cross-Region copy for RDS/EBS.

**Tested DR with Automated Failover** — CloudFormation StackSets (IaC for all DR infra) + AWS Backup (cross-Region) + ARC routing controls (data-plane failover) + Elastic Disaster Recovery (server-based) + FIS game days (scheduled via EventBridge). Measure achieved RTO/RPO per drill.

**Backup Integrity with Cross-Account Isolation** — AWS Backup vaults in dedicated DR account. KMS customer-managed keys separate from primary account. Organizations SCPs blocking vault deletion across member accounts. Backup Vault Lock (WORM) for critical vaults. IAM least-privilege on vault access.

**Common problems**:
- **DNS failover too slow for strict RTO** → Replace Route 53-only failover with ARC routing controls (data-plane, immediate traffic shift)
- **DR Region lacks capacity at failover** → Pre-provision service quota increases in DR Region; include in quarterly readiness reviews
- **Configuration drift in DR environment** → Enforce CloudFormation drift detection on all DR stacks; run regularly via CloudFormation StackSets

---

## Verification Loop

Run after architectural review or IaC deployment:

### 1. Multi-AZ posture
```bash
# Confirm ASG spans ≥2 AZs
aws autoscaling describe-auto-scaling-groups \
  --query 'AutoScalingGroups[*].{Name:AutoScalingGroupName,AZs:AvailabilityZones}'
# Expected: each group lists ≥2 AZs

# Confirm RDS Multi-AZ enabled
aws rds describe-db-instances \
  --query 'DBInstances[*].{ID:DBInstanceIdentifier,MultiAZ:MultiAZ}'
# Expected: MultiAZ: true for all production instances

# Confirm ELB cross-zone load balancing
aws elbv2 describe-load-balancer-attributes --load-balancer-arn <arn> \
  --query 'Attributes[?Key==`load_balancing.cross_zone.enabled`]'
# Expected: Value: true
```

### 2. Backup posture
```bash
# Confirm backup jobs completing
aws backup list-backup-jobs --by-state COMPLETED \
  --query 'BackupJobs[*].{Resource:ResourceArn,CompletionDate:CompletionDate}'

# Confirm S3 versioning on critical buckets
aws s3api get-bucket-versioning --bucket <bucket-name>
# Expected: {"Status": "Enabled"}

# Confirm RDS backup retention
aws rds describe-db-instances \
  --query 'DBInstances[*].{ID:DBInstanceIdentifier,RetentionDays:BackupRetentionPeriod}'
# Expected: RetentionDays > 0
```

### 3. Quota utilization
```bash
# List current quota utilization for a service
aws service-quotas list-service-quotas --service-code ec2 \
  --query 'Quotas[*].{Name:QuotaName,Value:Value}'
# Review against current usage; request increases proactively
```

### 4. DR readiness
```bash
# Confirm FIS experiment templates exist
aws fis list-experiment-templates \
  --query 'experimentTemplates[*].{ID:id,Description:description}'
# Expected: ≥1 template per failure scenario covered

# CloudFormation drift detection
aws cloudformation detect-stack-drift --stack-name <dr-stack-name>
# Expected: StackDriftStatus: IN_SYNC after completion
```

**Troubleshooting**:
- `MultiAZ: false` on RDS → Enable Multi-AZ (takes minutes; requires maintenance window for restart)
- No FIS experiment templates found → Create templates for AZ impairment, instance termination, latency injection
- Backup jobs FAILED → Check IAM role permissions on backup vault and KMS key

---

## Quick Reference

**DR Strategy Matrix**:

| Strategy | RTO | RPO | Key AWS Services | Cost |
|----------|-----|-----|-----------------|------|
| Backup & Restore | Hours | Hours | AWS Backup + CloudFormation | Lowest |
| Pilot Light | ~30 min | Minutes | Elastic Disaster Recovery | Low |
| Warm Standby | Minutes | Seconds | Scaled-down always-on stack + ARC | Higher |
| Multi-Site Active/Active | Near-zero | Near-zero | Route 53 + ARC + DynamoDB global / Aurora Global DB | Highest |

**Aurora Global Database key metrics**:
- Cross-Region replication lag: <1 second
- Secondary Region promotion: <1 minute (even in complete regional outage)

**ARC vs Route 53 failover**:
- Route 53: DNS TTL propagation delay (minutes); simple to configure
- ARC routing controls: Immediate data-plane traffic shift; control-plane-independent

**Critical limits to monitor**:

| Resource | Why it matters |
|----------|----------------|
| EC2 vCPU quotas per Region | Scale-out blocked silently if quota exhausted |
| VPC limits (subnets, EIPs, security groups) | DR Region must have equivalent quota headroom |
| RDS instance quotas | DR Region standby instances count against quota |
| S3 bucket policies | CRR requires source bucket versioning + destination bucket policy |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/applying-aws-reliability-pillar/
├── SKILL.md                              <- This file (guardrails + summaries)
└── blueprints/
    └── evaluation-scenarios.md           <- 6 test scenarios for skill-evaluator
```

---

## External Resources

### Official Documentation (current stable — November 2024 edition)
- [Reliability Pillar whitepaper](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/) — Primary reference (November 6, 2024)
- [REL10-BP01 — Fault isolation](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/use-fault-isolation-to-protect-your-workload.html)
- [REL13-BP02 — DR strategy planning](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html)
- [Reliability Foundations — Service Quotas](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/foundations.html)
- [Failure Management — Backup & FIS](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/failure-management.html)

### Key Services
- [AWS Fault Injection Service](https://docs.aws.amazon.com/fis/latest/userguide/) — Chaos engineering with stop conditions
- [Amazon Application Recovery Controller](https://docs.aws.amazon.com/r53recovery/latest/dg/what-is-route53-recovery.html) — Data-plane failover
- [AWS Elastic Disaster Recovery](https://docs.aws.amazon.com/drs/latest/userguide/) — Managed server DR
- [AWS Resilience Hub](https://docs.aws.amazon.com/resilience-hub/latest/userguide/) — Automated RTO/RPO posture assessment

### Companion Reference (review for currency)
- [DR Whitepaper](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/) — Last updated 2022-04-01; current stable for DR strategy taxonomy
