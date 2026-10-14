---
name: applying-waf-reliability-pillar
description: "Applies AWS Well-Architected Framework Reliability Pillar (Nov 2024 edition) patterns for multi-account production workloads on AWS. Use when designing, reviewing, or improving workload reliability, DR strategies, fault isolation, automated recovery, or resilience testing on AWS."
---

## Function

Specialist in AWS Well-Architected Framework — Reliability Pillar for multi-account production workloads on AWS. Covers four best-practice areas (Foundations, Workload Architecture, Change Management, Failure Management) across REL1–REL13.

## Version Context

**Framework**: AWS Well-Architected Framework — Reliability Pillar
**Current stable edition**: November 6, 2024 whitepaper
**Research date**: 2026-08-28 (currency threshold: 2027-08-28)
**Cloud Provider**: AWS

**Five design principles (all editions)**:
- Automatically recover from failure
- Test recovery procedures
- Scale horizontally to increase aggregate workload availability
- Stop guessing capacity
- Manage change through automation

**Key services in current edition**: AWS Fault Injection Service (FIS), Amazon Application Recovery Controller (ARC), AWS Elastic Disaster Recovery (DRS), AWS Backup, AWS Resilience Hub, Amazon Aurora Global Database, Amazon DynamoDB global tables.

**Edition note**: AWS does not publish annual editions. "2026" is access-year only. The November 6, 2024 whitepaper is the current stable revision as of 2026-08-28. REL10-BP02 and REL12-BP03 were merged into other best practices in this edition — historical BP numbering does not map 1:1.

> **CRITICAL — Agent Warning**: This skill targets the November 6, 2024 Reliability Pillar whitepaper. Reject patterns that conflict with REL1–REL13 as defined in that edition.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 three-tier patterns (mandatory first read)
- **[DR Strategy Matrix](#dr-strategy-matrix)** — Four-tier cost/RTO/RPO decision table
- **[Reference Architectures](#reference-architectures)** — Multi-AZ baseline and Multi-Region Warm Standby
- **[Verification Loop](#verification-loop)** — AWS CLI checks for reliability guardrails
- **[Quick Reference](#quick-reference)** — Critical limits and key service summary
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases covering canonical, edge, and anti-pattern traps
- **[External Resources](#external-resources)** — Dated official source links

---

## Blueprints & Guardrails

### ✅ Always Do

**1. Multi-AZ deployment with automated recovery (REL10-BP01, REL10-BP02)**
Deploy compute across >=2 AZs (>=3 preferred) behind an ELB, use RDS Multi-AZ or Aurora (multi-AZ), and automate recovery for any component constrained to a single location. A single AZ is a single fault-isolation boundary — an AZ event takes down the whole workload.

**2. Redundant network connectivity with BGP dynamic routing (REL02-BP01, REL02-BP02)**
Provide two or more traffic paths for hybrid connectivity. Terminate VPN backup tunnels on AWS Transit Gateway with two tunnels in different AZs; run BGP dynamic routing; use the Direct Connect Resiliency Toolkit (maximum resiliency = two DX connections at separate locations, 99.99% SLA). Never rely on a single VPN tunnel or static routing only.

**3. Monitor service quotas with failover headroom (REL01-BP04, REL01-BP05, REL01-BP06)**
Automate quota monitoring and alarming with Service Quotas + CloudWatch. Maintain a sufficient gap above current peak usage so that an AZ or Region failover does not breach quotas. Track across all accounts and Regions.
```bash
aws service-quotas list-service-quotas --service-code ec2 --query 'Quotas[?Adjustable==`true`].[QuotaName,Value]'
```

**4. Automated, encrypted, tested backups aligned to RTO/RPO (REL09-BP01–BP04)**
Centralize backup policy in AWS Backup, encrypt with AWS KMS, copy cross-Region, and periodically run automated restore drills. An untested backup is not a recovery capability — restore verification is mandatory (REL09-BP04).

**5. Static stability with data-plane failover (REL11-BP04, REL11-BP05)**
Pre-provision failover capacity so recovery does not require acquiring new resources. Route failover exclusively through data-plane operations (Amazon ARC routing controls, Route 53 health-check DNS failover). Avoid any recovery step that calls the control plane to create or modify resources.

**6. Regular resiliency testing: chaos engineering + game days (REL12-BP04, REL12-BP05)**
Define a steady-state hypothesis, inject faults with AWS FIS using CloudWatch alarm stop conditions, and run scheduled game days. Use AWS Resilience Hub to generate FIS experiments and continuously validate RTO/RPO likelihood. Test findings feed into playbooks (REL12-BP01) and post-incident analysis (REL12-BP02).

**7. Automated elasticity — never guess capacity (REL07-BP01, REL07-BP03, REL07-BP04)**
Attach scaling policies (EC2 Auto Scaling, Application Auto Scaling, DynamoDB auto scaling) to all compute and data tiers. Add scheduled scaling for predictable patterns. Validate scaling with load tests. Prohibit fixed manual capacity baselines and console-only provisioning.

**8. End-to-end observability with distributed tracing (REL06-BP01–BP07)**
Instrument all components, define KPIs, configure CloudWatch alarms wired to SNS notifications and automated Lambda responses. Use AWS X-Ray + CloudWatch ServiceLens, Synthetics canaries, and RUM to trace requests across all tiers. Silent failures are the worst failure mode.

### ⚠️ Ask First

**DR strategy per workload tier (REL13-BP01, REL13-BP02, REL13-BP03)**
Ask for the business-defined RTO and RPO per workload tier before selecting a DR strategy. Confirm the strategy will be tested (REL13-BP03) — never left ad-hoc. See [DR Strategy Matrix](#dr-strategy-matrix) for options and trade-offs.

**Region strategy: single-Region multi-AZ vs multi-Region (REL10, REL13)**
Ask whether any regulatory, contractual, or availability SLA actually requires Region-level survivability before adding multi-Region cost and complexity. Options:
- **Single-Region multi-AZ** — Optimizes cost/simplicity; tolerable for most workloads where Region-level rare events are acceptable.
- **Multi-Region active/passive** — Required for Region-failure survivability; significantly higher cost and operational complexity.
- **Multi-Region active/active** — Near-zero RTO/RPO; reserve for mission-critical global workloads; requires write-conflict handling.

**Coupling model for inter-service interactions (REL04-BP02, REL04-BP04, REL05)**
Ask whether the caller truly needs a synchronous answer. If not, prefer loosely coupled dependencies and ensure mutating operations are idempotent so retries are safe.

| Option | AWS Services | Best When |
|--------|--------------|-----------|
| Sync request/response | ALB, API Gateway | Low fan-out, latency-sensitive reads |
| Async queue | Amazon SQS + Lambda | Spiky load, decoupling producers/consumers |
| Event-driven pub/sub | SNS, EventBridge | Multiple independent consumers |

### 🚫 Never Do

**Single-AZ production deployment for stateful workloads** — CRITICAL
❌ Wrong: Single-AZ Amazon RDS instance (`MultiAZ=false`), EC2 fleet in one AZ.
✅ Correct: RDS Multi-AZ with automatic failover standby; ASG spanning 3 AZs behind an ALB.

Detection:
```bash
aws rds describe-db-instances --query 'DBInstances[?MultiAZ==`false`].[DBInstanceIdentifier,DBInstanceStatus]'
aws autoscaling describe-auto-scaling-groups --query 'AutoScalingGroups[?length(AvailabilityZones)<`2`].[AutoScalingGroupName]'
```

**No DR plan / ad-hoc recovery / untested DR** — CRITICAL
❌ Wrong: "We'll spin up the other Region if the primary fails" — never provisioned, never tested.
✅ Correct: Documented RTO/RPO per workload tier (REL13-BP01), defined strategy (REL13-BP02), periodic game-day test validating actual RTO/RPO (REL13-BP03), drift managed by StackSets (REL13-BP04).

**Control-plane dependency during recovery** — HIGH
❌ Wrong: Failover runbook calls `RunInstances` or updates ASG desired capacity in the recovery Region to create capacity at failover time.
✅ Correct: Recovery Region pre-provisioned and statically stable; failover executes via Amazon ARC data-plane routing-control API only.

**Retries without exponential backoff, jitter, and a max-retry cap** — HIGH
❌ Wrong: `while true: call(); sleep(1)` at both app and API Gateway layers on a non-idempotent POST.
✅ Correct: AWS SDK default retry with exponential backoff + jitter, max 3–5 attempts, at one layer, targeting an idempotent operation (REL04-BP04, REL05-BP03).

**Manual capacity guessing / click-ops provisioning** — MEDIUM
❌ Wrong: Fixed ASG sized by manual estimate, changed in the console.
✅ Correct: Target-tracking ASG + scheduled scaling defined in CloudFormation, validated by load tests (REL07-BP04).

**Single, non-redundant network path to on-premises** — HIGH
❌ Wrong: One Site-to-Site VPN tunnel to one on-premises router, static routing.
✅ Correct: Two DX connections at separate locations + VPN backup on Transit Gateway, two tunnels in different AZs, BGP.

---

## DR Strategy Matrix

| DR Pattern | RTO | RPO | Relative Cost | Best For | Key AWS Services |
|------------|-----|-----|---------------|----------|------------------|
| Backup & Restore | ~24 h | Hours | $ | Non-critical workloads | AWS Backup, S3 CRR, CloudFormation |
| Pilot Light | Tens of minutes | Minutes | $$ | Core business systems | Elastic Disaster Recovery, Aurora replicas, ARC |
| Warm Standby | Minutes | Seconds | $$$ | Business-critical | + EC2 Auto Scaling, Route 53 |
| Multi-Site Active/Active | ~Zero | Near-zero | $$$$ | Mission-critical, global | Aurora Global DB, DynamoDB global tables, Global Accelerator |

> Source: REL13-BP02 (Nov 6, 2024) + DR whitepaper (Feb 12, 2021 — current stable; verify currency before citing verbatim).

---

## Reference Architectures

**Multi-AZ three-tier web application (single-Region reliability baseline)**

| Layer | Service | Purpose |
|-------|---------|---------|
| Edge/DNS | Route 53 + CloudFront | Health-checked DNS, edge caching |
| Ingress | ALB (multi-AZ) | Distribute + health-check targets |
| Compute | EC2 Auto Scaling across 3 AZs | Elastic, self-healing compute |
| Data | RDS/Aurora Multi-AZ | Automatic standby failover |
| Backup | AWS Backup + S3 CRR | RTO/RPO-aligned recovery |
| Observability | CloudWatch + X-Ray | Metrics/logs/traces, alarms |

**Multi-Region Warm Standby (business-critical DR)**

| Layer | Service | Purpose |
|-------|---------|---------|
| Data replication | Aurora Global DB, DynamoDB global tables, S3 CRR | Continuous cross-Region replication |
| Standby compute | Reduced-capacity ASG (always-on) in DR Region | Immediate reduced service + scale-up |
| Failover routing | Amazon ARC + Route 53 | Data-plane traffic switch |
| Scale-up | EC2 Auto Scaling | Grow DR Region to full capacity on failover |
| Deployment | CloudFormation StackSets | Consistent multi-Region deploy, drift control |

---

## Verification Loop

Run after each reliability design review or IaC change:

### 1. Multi-AZ coverage
```bash
# Check ASG spans multiple AZs
aws autoscaling describe-auto-scaling-groups \
  --query 'AutoScalingGroups[].[AutoScalingGroupName,AvailabilityZones]'

# Check RDS Multi-AZ enabled
aws rds describe-db-instances \
  --query 'DBInstances[].[DBInstanceIdentifier,MultiAZ]'
```
Expected: each ASG lists >=2 AZs; each production RDS shows `MultiAZ: true`.

### 2. Backup verification
```bash
# List AWS Backup vaults and plans
aws backup list-backup-plans --query 'BackupPlansList[].[BackupPlanName,CreationDate]'
aws backup list-backup-vaults --query 'BackupVaultList[].[BackupVaultName,EncryptionKeyArn]'
```
Expected: at least one active backup plan; all vaults have a KMS key ARN (not null).

### 3. Service quota headroom
```bash
aws service-quotas list-service-quotas --service-code ec2 \
  --query 'Quotas[?contains(QuotaName,`Running On-Demand`)].[QuotaName,Value]'
```
Expected: confirm current usage < 70% of quota for each limit relevant to failover capacity.

### 4. Resilience Hub assessment
```bash
aws resiliencehub list-apps --query 'appSummaries[].[name,resiliencyScore,lastAppComplianceEvaluationTime]'
```
Expected: each app shows a recent compliance evaluation; resiliency score meets target.

**Troubleshooting**:
- `MultiAZ=false` on RDS → Enable Multi-AZ via modify-db-instance (blue/green available for zero-downtime).
- No backup plan found → Create centralized policy in AWS Backup with cross-Region copy enabled.
- Quota at 100% → Request increase via Service Quotas console before provisioning failover capacity.

---

## Quick Reference

**Domain glossary (key terms)**:
- **RTO** — max tolerable downtime; business-derived, not a technical default.
- **RPO** — max tolerable data loss; drives replication and backup frequency.
- **Static stability** — pre-provisioned capacity; workload operates in single normal mode without acquiring new resources during failure.
- **Data plane vs control plane** — data plane (routing, serving) has higher availability than control plane (create/modify resources); use data plane for failover.
- **Cell-based (bulkhead)** — workload partitioned into independent cells by partition key; limits blast radius to one cell.

**Critical limits (current stable)**:
| Resource | Limit | Scope |
|----------|-------|-------|
| VPN tunnels per gateway | 2 (per connection) | ECMP up to 50 Gbps aggregate, 1.25 Gbps/tunnel |
| Aurora Global DB replication lag | Typically < 1 s | Cross-Region |
| Route 53 DNS TTL for health-check failover | 60 s minimum recommended | Regional failover |
| AWS FIS concurrent experiments | Check Service Quotas per account | Per Region |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/applying-waf-reliability-pillar/
├── SKILL.md                              <- This file (summary + guardrails)
└── blueprints/
    └── evaluation-scenarios.md           <- 6 test scenarios (canonical, edge, anti-pattern)
```

---

## External Resources

### Official Documentation — AWS Well-Architected Reliability Pillar (Nov 6, 2024)
- [Reliability Pillar — Welcome](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html) — Edition confirmation; accessed 2026-08-28
- [Document Revisions](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/document-revisions.html) — Edition history; confirms Nov 6, 2024 as current stable
- [Design Principles](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/design-principles.html) — Five reliability principles
- [REL9 — Back up data](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/back-up-data.html) — Backup requirements (BP01–BP04)
- [REL10 — Fault isolation](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/use-fault-isolation-to-protect-your-workload.html) — Multi-AZ and cell-based patterns
- [REL11 — Withstand component failures](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/design-your-workload-to-withstand-component-failures.html) — Static stability, control/data plane
- [REL12 — Test reliability](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/test-reliability.html) — Chaos engineering + game days
- [REL13 — Plan for DR](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/plan-for-disaster-recovery-dr.html) — Four DR strategies

### Companion Sources
- [DR whitepaper — Disaster Recovery Options in the Cloud](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html) — Pub. Feb 12, 2021; current stable but >12 months old — verify currency before citing verbatim. DR strategies independently confirmed in REL13-BP02 (Nov 2024).
- [AWS Resilience Hub](https://docs.aws.amazon.com/resilience-hub/latest/userguide/what-is.html) — Continuous RTO/RPO validation + FIS experiment generation
- [Amazon Application Recovery Controller](https://docs.aws.amazon.com/r53recovery/latest/dg/what-is-route53-recovery.html) — Data-plane failover routing controls
