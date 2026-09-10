---
name: applying-aws-sustainability-pillar
description: "Applies AWS Well-Architected Sustainability Pillar guidance (Nov 2024 edition) to multi-account production workloads on AWS. Use when reviewing or designing AWS workloads for environmental impact reduction, per-unit KPI instrumentation, or Well-Architected Sustainability review."
---

## Function

Specialist in AWS Well-Architected Sustainability Pillar (SUS01–SUS06) for multi-account production workloads on AWS.

## Version Context

**Framework**: AWS Well-Architected Framework — Sustainability Pillar
**Target edition**: November 6, 2024 (current stable)
**Official source**: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/
**Research date**: 2026-08-27
**Currency threshold**: 2027-08-27

**Key changes in November 2024 edition**:
- New best practice SUS06-BP01: "Communicate and cascade your sustainability goals"
- 10 best practices updated across SUS01 and SUS03–SUS06

**Pillar structure**:
- SUS01 — Region Selection
- SUS02 — Alignment to Demand
- SUS03 — Software and Architecture
- SUS04 — Data Management
- SUS05 — Hardware and Services
- SUS06 — Process and Culture (new BP in Nov 2024)

⚠️ **CRITICAL — Agent Warning**:
This skill targets the November 6, 2024 edition. Reject patterns from earlier editions.
SUS06-BP01 is a new mandatory practice as of Nov 2024 — do not treat Process and Culture as optional.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 patterns
- **[Integration Patterns](#integration-patterns)** — Governance and tooling connections
- **[Verification Loop](#verification-loop)** — AWS CLI compliance checks
- **[Quick Reference](#quick-reference)** — Critical limits at a glance
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases

---

## Blueprints & Guardrails

### ✅ Always Do

**SUS-A1 — Select Region accounting for carbon grid intensity (SUS01-BP01)**
Use AWS Customer Carbon Footprint Tool to compare Region options. Document the carbon vs latency vs data-residency trade-off rationale in the architecture decision record. Never choose a Region on latency alone without assessing carbon impact.
*Services*: AWS Customer Carbon Footprint Tool; Region placement.

**SUS-A2 — Scale infrastructure dynamically to match demand (SUS02-BP01)**
Implement elastic capacity with target-tracking Auto Scaling policies tied to CloudWatch utilization metrics. Prefer Lambda or Fargate for spiky or event-driven workloads where scale-to-zero is achievable. Never provision static fleets for variable demand.
*Services*: EC2 Auto Scaling, AWS Lambda, AWS Fargate, Karpenter on EKS.

**SUS-A3 — Identify and remove idle and orphaned resources (SUS02-BP03)**
Run Compute Optimizer and Trusted Advisor idle-resource checks on a weekly cadence. Automate cleanup of unattached EBS volumes and stopped instances beyond a retention threshold.
*Services*: AWS Compute Optimizer, AWS Trusted Advisor.

**SUS-A4 — Apply S3 Lifecycle rules to all buckets (SUS04 Data Management)**
Require S3 Lifecycle rules on every bucket. Enable Intelligent-Tiering for variable-access objects. Add expiration rules for obsolete data. Use Glacier Deep Archive for long-retention compliance data.
*Services*: S3 Lifecycle, S3 Intelligent-Tiering, S3 Glacier / Glacier Deep Archive, Amazon Data Lifecycle Manager.

**SUS-A5 — Default to managed and serverless services over self-managed always-on EC2 (SUS05)**
Require justification for any self-managed EC2 alternative to a managed service. When EC2 is required, select the latest-generation Graviton instance family and validate with Compute Optimizer.
*Services*: AWS Fargate, AWS Lambda, Amazon Aurora Serverless, Amazon SQS, Amazon RDS; Graviton instances.

**SUS-A6 — Establish per-unit sustainability KPIs and cascade goals (SUS06-BP01 — new Nov 2024)**
Define per-unit-of-work impact KPIs (e.g., compute-seconds per transaction, GB transferred per user request). Track via CloudWatch custom metrics. Schedule quarterly Customer Carbon Footprint Tool review. Document and cascade goals to team level per SUS06-BP01.
*Services*: CloudWatch custom metrics and dashboards, AWS Customer Carbon Footprint Tool.

### ⚠️ Ask First

**Decision A — Region: Carbon footprint vs latency vs data residency (SUS01-BP01)**
Ask: "What are the data-residency and latency SLA requirements?" before selecting a Region based on carbon footprint alone. Carbon, compliance, and latency constraints must be resolved together — they are not independent.

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Lowest-carbon Region | Carbon footprint | Latency; may conflict with residency | Sustainability goal outweighs latency; residency allows it |
| Region nearest users + CloudFront | Latency, downstream device energy | May be higher-carbon grid | User experience is the primary driver |

**Decision B — Compute model: Serverless vs right-sized managed instances (SUS02)**
Ask: "Is the workload demand profile spiky or steady-state?" before choosing compute architecture.

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Serverless / scale-to-zero (Lambda, Fargate) | Utilization, zero idle baseline | Cold starts; runtime limits | Spiky or event-driven workloads |
| EC2 Graviton + Auto Scaling | Steady-state efficiency; runtime control | Minimum-capacity idle baseline | Sustained high-utilization workloads |

**Decision C — Storage tiering: Cold vs hot (SUS04)**
Ask: "What is the retrieval latency tolerance and access frequency for each data class?" Never default all data to S3 Standard.

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Multi-copy hot storage (S3 Standard) | Availability, retrieval latency | Powered-storage footprint | High-availability critical data |
| Tiered / cold single-Region (Intelligent-Tiering / Glacier) | Reduced footprint, cost | Retrieval latency from cold tiers | Infrequent access; sustainability is priority |

**Decision D — SLA level vs sustainability trade-off (SUS02-BP02)**
Ask: "What is the actual business impact of a 15-minute outage?" before defaulting to 99.99% SLA. Non-critical tiers should be designed to their real SLA, not the most demanding tier's SLA. Over-provisioned high-SLA significantly increases footprint.

### 🚫 Never Do

| Anti-pattern | Why | Correct Alternative |
|---|---|---|
| **Static over-provisioning "just in case" (SUS-ND-1)** | Violates "Maximize utilization" — baseline power consumed with no productive output. Detection: sustained <30% CPU utilization. | EC2 Auto Scaling with target-tracking, Lambda, or Fargate |
| **Idle and orphaned resources left running (SUS-ND-2)** | Idle resources consume baseline energy 24/7. Detection: `aws ec2 describe-volumes --filters Name=status,Values=available` | Automated cleanup; Trusted Advisor + Compute Optimizer acted on weekly |
| **All data kept hot forever with no lifecycle policy (SUS-ND-3)** | Violates SUS04 — maximizes powered-storage footprint unnecessarily. Detection: `aws s3api get-bucket-lifecycle-configuration --bucket <name>` returns no rules. | S3 Lifecycle rules + Intelligent-Tiering + expiration on all buckets |
| **Region choice ignores carbon grid intensity (SUS-ND-4)** | Violates SUS01 and "Understand your impact." No baseline to improve from. Detection: no Region selection rationale documented; Carbon Footprint Tool never opened. | Customer Carbon Footprint Tool in Region selection; documented rationale |
| **Self-managed always-on EC2 where managed service exists (SUS-ND-5)** | Violates "Use managed services" — single-tenant EC2 achieves lower aggregate efficiency than shared managed services. Detection: self-managed services with sustained low CPU on dedicated EC2. | SQS instead of self-managed RabbitMQ; Aurora Serverless instead of MySQL on EC2 |
| **No sustainability KPIs, no measurement (SUS-ND-6)** | Violates "Understand your impact," "Establish sustainability goals," and SUS06-BP01. Regressions undetectable. Detection: no CloudWatch sustainability dashboards; no Carbon Footprint Tool history. | CloudWatch per-unit KPIs; cascaded goals; quarterly Carbon Footprint Tool review |
| **Forcing unnecessary client device upgrades or heavy clients (SUS-ND-7)** | Violates "Reduce downstream impact" — generates e-waste and user-side energy consumption. Detection: no downstream-impact testing plan. | Optimize payloads; test with device farms; backward-compatible clients |

---

## Integration Patterns

**Multi-Account Governance**
Deploy AWS Config managed rules at the Organizations level to detect: buckets without lifecycle policies, outdated EC2 instance generations, instances with no Auto Scaling. Aggregate findings in Security Hub. Use SCPs to block deprecated instance families. Carbon Footprint Tool reports at management account level for full-footprint visibility.
*Services*: AWS Organizations SCPs, AWS Config, AWS Security Hub, CloudWatch cross-account observability.

**Sustainability ↔ Cost Optimization**
Sustainability and cost often correlate but are distinct goals. Run both a sustainability review and a cost review; do not substitute one for the other. Graviton instances reduce both cost and energy. Right-sized SLA reduces both footprint and cost. Never treat a cost-only optimization as a sustainability improvement without verifying energy impact.

**Sustainability ↔ Performance Efficiency Pillar**
Dynamic scaling (Auto Scaling / Lambda) simultaneously satisfies both pillars. When performance requires additional reserved capacity for latency SLAs, document the sustainability cost explicitly and revisit annually.

**Common Problems**:
- **Problem**: Customer Carbon Footprint Tool shows flat or rising trend after optimization — **Solution**: Verify CloudWatch utilization confirms Auto Scaling is actually activating; check for bypassed static resource pools; audit all Regions including non-primary.
- **Problem**: S3 Lifecycle rules configured but Glacier retrieval costs surprise teams — **Solution**: Set Intelligent-Tiering before Glacier for unknown access patterns; document retrieval SLAs per data class before configuring cold transitions.
- **Problem**: SUS06 goals documented but not cascaded — **Solution**: Embed per-unit KPI thresholds in team OKRs and CloudWatch alarms; schedule recurring reviews with team leads.

---

## Verification Loop

Run after each sustainability review or architecture change:

### 1. Idle Resource Scan
```bash
# Detect unattached EBS volumes
aws ec2 describe-volumes \
  --filters Name=status,Values=available \
  --query 'Volumes[*].{ID:VolumeId,Size:Size,AZ:AvailabilityZone}'
# Expected: empty list for compliant accounts
```

### 2. S3 Lifecycle Compliance
```bash
# Check lifecycle configuration on a specific bucket
aws s3api get-bucket-lifecycle-configuration --bucket <bucket-name>
# Expected: JSON with at least one Rule; missing = non-compliant
```

### 3. Compute Optimizer Findings
```bash
# List over-provisioned EC2 findings
aws compute-optimizer get-ec2-instance-recommendations \
  --filters name=Finding,values=Overprovisioned \
  --query 'instanceRecommendations[*].{Instance:instanceArn,Finding:finding}'
# Expected: empty list for compliant fleet
```

### 4. Auto Scaling Validation
```bash
# Confirm target-tracking policies exist on Auto Scaling groups
aws autoscaling describe-policies \
  --query 'ScalingPolicies[?PolicyType==`TargetTrackingScaling`].{ASG:AutoScalingGroupName,Policy:PolicyName}'
# Expected: one or more policies per Auto Scaling group
```

**Troubleshooting**:
- Compute Optimizer returning no data → Enable Compute Optimizer for the account/organization and wait 12–24h for analysis
- Carbon Footprint Tool showing no data → Confirm account has sufficient usage history (30 days minimum)
- Lifecycle rules configured but data not moving to Glacier → Verify transition days threshold and object age; minimum age rules apply

---

## Quick Reference

**Six Sustainability Design Principles (official)**:
1. Understand your impact
2. Establish sustainability goals
3. Maximize utilization
4. Anticipate and adopt new, more efficient hardware and software offerings
5. Use managed services
6. Reduce the downstream impact of your cloud workloads

**Critical AWS services per pillar area**:

| Pillar Area | Primary Services |
|---|---|
| SUS01 Region Selection | Customer Carbon Footprint Tool |
| SUS02 Demand Alignment | EC2 Auto Scaling, Lambda, Fargate, Compute Optimizer |
| SUS04 Data Management | S3 Lifecycle, S3 Intelligent-Tiering, Glacier, Data Lifecycle Manager |
| SUS05 Hardware | Graviton instances, Fargate, Managed databases, SQS |
| SUS06 Process | CloudWatch custom KPIs, Customer Carbon Footprint Tool |
| Governance | AWS Config, SCPs, Security Hub |

**Key detection commands**:
```bash
# Unattached EBS
aws ec2 describe-volumes --filters Name=status,Values=available

# Bucket lifecycle check
aws s3api get-bucket-lifecycle-configuration --bucket <name>

# Over-provisioned instances
aws compute-optimizer get-ec2-instance-recommendations \
  --filters name=Finding,values=Overprovisioned
```

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/applying-aws-sustainability-pillar/
├── SKILL.md                              <- This file (summary + guardrails)
└── blueprints/
    └── evaluation-scenarios.md           <- Test scenarios for skill-evaluator
```

---

## External Resources

### Official Documentation
- [Sustainability Pillar — Overview](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html) — Nov 6, 2024 (current stable)
- [SUS01 Region Selection](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/region-selection.html)
- [SUS02 Alignment to Demand](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/align-utilization-with-user-load.html)
- [SUS04 Data Management](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/data-management.html)
- [SUS05 Hardware and Services](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/hardware-and-services.html)
- [SUS06 Process and Culture](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/process-and-culture.html)
- [Design Principles for Sustainability](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html)

### Tools and Services
- [AWS Customer Carbon Footprint Tool](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/what-is-ccft.html)
- [AWS Compute Optimizer](https://docs.aws.amazon.com/compute-optimizer/latest/ug/what-is-compute-optimizer.html)

### Release Notes
- [Nov 2024 Well-Architected Framework Update Announcement](https://aws.amazon.com/blogs/architecture/announcing-updates-to-the-aws-well-architected-framework-guidance-3/) — 2024-11-06
