---
name: applying-waf-cost-optimization
description: "Applies AWS Well-Architected Framework Cost Optimization Pillar patterns to cloud architecture design and review. Use when designing, reviewing, or optimizing AWS workloads for cost, selecting compute/pricing models, setting up FinOps governance, or addressing cost anti-patterns in an AWS environment."
---

> **Version Note**: The current stable authoritative document is the Cost Optimization Pillar whitepaper
> (publication date 2024-06-27). AWS has not published a 2026 edition as of research date 2026-08-27.
> Re-verify currency at the live docs before making binding purchase or architecture decisions.

## Function

Specialist in AWS Well-Architected Framework — Cost Optimization Pillar (COST 1–11), covering
Cloud Financial Management (FinOps), expenditure visibility, cost-effective resource selection,
demand/supply management, and continuous optimization for production AWS workloads.

## Version Context

**Framework**: AWS Well-Architected Framework — Cost Optimization Pillar
**Pinned revision**: Whitepaper publication 2024-06-27 (no later edition confirmed)
**Research date**: 2026-08-27
**Currency threshold**: Re-verify by 2027-08-27; source already > 12 months old at research date
**Support status**: Active (framework is continuously maintained at `docs.aws.amazon.com/wellarchitected/latest/`)

**Pillar structure — five focus areas / eleven questions**:
- COST 1: Cloud Financial Management
- COST 2–4: Expenditure and usage awareness (governance, monitoring, decommission)
- COST 5–8: Cost-effective resources (service selection, size/type, pricing model, data transfer)
- COST 9: Manage demand and supply resources
- COST 10–11: Optimize over time (new services, cost of effort)

**2024-06-27 refresh**: Updated eight best practices across COST 1, 2, 3, 5, and 11.
COST 11 ("How do you evaluate the cost of effort?") consolidated into the current eleven-question set.

**Deprecated framing**: Legacy "cost of effort" guidance predating the COST 11 addition — re-check against current question set.

⚠️ **CRITICAL — Agent Warning**:
This skill targets the 2024-06-27 whitepaper revision (current stable).
Reject any pattern claiming to come from a "2026 Cost Optimization Pillar edition" — no such edition exists.
Discount percentages (Savings Plans ~72%, RIs ~75%, Spot ~90%) vary by term/family/Region — treat as indicative, not contractual.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 patterns (summary)
- **[Always-Do Patterns](./blueprints/always-do-patterns.md)** — Full FinOps and architecture patterns
- **[Ask-First Decisions](./blueprints/ask-first-decisions.md)** — Pricing model and compute model matrices
- **[Never-Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with detection and fix
- **[Integration Patterns](#integration-patterns)** — Cost toolchain and reference architecture
- **[Verification Loop](#verification-loop)** — CLI checks and expected outputs
- **[Quick Reference](#quick-reference)** — COST question map and service shortcuts
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Test cases for skill validation
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For full patterns with CLI examples, see [Always-Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns** (Complex tier — COST 1–11 spans 8 first-class concerns):

- **Establish Cloud Financial Management (FinOps) as a funded capability** (COST 1) — Fund a cross-functional FinOps function (finance + engineering + leadership) before scaling spend; activate Cost Explorer and configure Budgets in the management account. Without this, all other cost controls are owner-less and unsustained.
- **Attribute every cost to an owner via account structure + tagging** (COST 2, COST 3) — Create a multi-account structure (Organizations/Control Tower); enforce a mandatory tag taxonomy (cost center, owner, environment, workload); activate cost allocation tags in the Billing console. Unattributed spend cannot be governed.
- **Monitor cost with proactive Budgets and Anomaly Detection** (COST 2, COST 3) — Configure AWS Budgets per account/service/tag with both forecast and actual thresholds; enable Cost Anomaly Detection monitors. Optionally wire Budget Actions for automated guardrails.
- **Right-size resources with data before committing** (COST 6, COST 9) — Run AWS Compute Optimizer and Trusted Advisor to right-size EC2/EBS/Lambda/ASG/RDS from real utilization metrics before purchasing Savings Plans or Reserved Instances.
- **Apply the correct pricing model per workload profile** (COST 7) — On-Demand for spiky/unknown; Savings Plans/RIs for steady baseline (up to ~72–75% off); Spot for stateless/fault-tolerant/batch (up to ~90% off). See [Ask-First Decisions](./blueprints/ask-first-decisions.md) for the decision matrix.
- **Match supply to demand with elasticity and demand shaping** (COST 9) — Use demand- or time-based Auto Scaling; throttle with API Gateway; buffer spikes with SQS; schedule shutdown of non-production environments outside working hours (~75% savings at 40 vs 168 hrs/week).
- **Plan and minimize data transfer charges before design lock-in** (COST 8) — Use CloudFront to reduce origin egress; VPC Gateway/Interface endpoints to avoid NAT/internet egress for AWS-service traffic; AZ-affinity for chatty internal paths; model cross-AZ/cross-Region/internet egress during architecture.
- **Decommission aggressively and optimize over time** (COST 4, COST 10, COST 11) — Automate detection and shutdown of orphaned/idle resources (Trusted Advisor + Config + Lambda); run recurring architecture reviews to adopt newer cheaper services; track lifecycle with tags from project inception.

### ⚠️ Ask First

For decision matrices with option comparisons, see [Ask-First Decisions](./blueprints/ask-first-decisions.md).

**Decision points requiring workload context before prescribing**:

- **Pricing model mix** (COST 7) — Ask: what fraction of compute is steady baseline vs variable, and do workloads tolerate interruption? Options: On-Demand / Compute Savings Plans / EC2 Instance Savings Plans / Standard RI / Convertible RI / Spot. Commitment purchases (SP/RI) are Ask-First decisions — confirm commercial terms (EDP/committed-use agreements) before recommending.
- **Compute model for cost efficiency** (COST 5) — Ask: what is the utilization pattern (steady vs spiky) and what is the team's operational capacity? Options: serverless (Lambda/Fargate — zero idle cost) vs managed containers (ECS/EKS Fargate — reduced ops) vs self-managed EC2 (lowest unit at scale). At low/variable utilization, serverless wins; at high steady utilization, EC2 with Graviton/Spot/RIs wins.
- **Cost of effort — automate vs managed service vs accept manual toil** (COST 11) — Ask: how frequently does the operation run, and what is the fully-loaded human cost? Options: automate (Lambda/Systems Manager/EventBridge), adopt managed service (RDS/Aurora, Fargate), or accept manual effort. Build cost of automation must be justified by recurring labor savings.
- **Chargeback vs showback** (COST 2, COST 3) — Ask: does the organization bill back cost to teams/tenants, or only report? Chargeback requires rigorous per-owner tagging and billing integration; showback is lower overhead but provides weaker accountability incentive.

### 🚫 Never Do

For full anti-patterns with detection commands, see [Never-Do Patterns](./blueprints/never-do-patterns.md).

**Prohibited patterns** (each has an inline alternative):

- **Persistent over-provisioning / idle resources** — Do not run always-on, oversized On-Demand fleets at < 20% utilization with no Auto Scaling and no non-prod shutdown. Use: right-sized ASG + scheduled shutdown of dev/test environments.
- **No cost visibility — no Budgets, no tags, no alerts** — Do not operate a single flat account with untagged resources and no AWS Budgets. Use: Organizations multi-account, enforced tag taxonomy, Budgets + Cost Anomaly Detection per owner.
- **Full On-Demand for stable predictable baseline** — Do not run 24×7 production baseline 100% On-Demand when utilization is steady and predictable. Use: Compute Savings Plans / RIs for the measured baseline; On-Demand only for burst above it.
- **Ignoring data transfer in architecture** — Do not assume egress/cross-AZ is free or negligible; do not route AWS-service traffic through a NAT gateway when VPC endpoints are available. Use: VPC endpoints + CloudFront + AZ-affinity + CUR data-transfer line item monitoring.
- **Never decommissioning / no resource lifecycle** — Do not leave orphaned EBS volumes, unattached Elastic IPs, idle load balancers, or dead dev environments running indefinitely. Use: lifecycle tags + automated idle-resource detection (Trusted Advisor/Config/Lambda) + Cost Optimization Hub.

---

## Integration Patterns

**Cost toolchain — observability and governance stack**:
- **CUR → Athena → QuickSight** — Granular hourly/resource-level cost data for custom dashboards and owner-level reporting. Use when Cost Explorer aggregation is insufficient.
- **Cost Explorer + Savings Plans/RI coverage reports** — Trend analysis and commitment health. Verify SP/RI utilization near 100%; identify under-covered steady baseline.
- **AWS Budgets + Cost Anomaly Detection → SNS → owner notification** — Proactive alerting pipeline. Wire Budget Actions for automated guardrails (e.g., deny new resource provisioning on overspend).
- **Compute Optimizer + Cost Optimization Hub** — Rightsizing and idle-resource recommendations aggregated across the Organization, deduplicated and prioritized by estimated savings.

**Reference architecture — cost-governed multi-account landing zone**:

| Layer | Service | Purpose |
|-------|---------|---------|
| Org structure | AWS Organizations / Control Tower | Account separation, cost boundary, SCP guardrails |
| Tagging | Cost allocation tags + Tag Policies | Attribute cost to owners/workloads |
| Visibility | Cost Explorer, CUR + Athena/QuickSight | Trend and granular analysis |
| Control | AWS Budgets, Cost Anomaly Detection | Proactive alerting / Budget Actions |
| Optimization | Compute Optimizer, Cost Optimization Hub, Trusted Advisor | Rightsizing + commitment + idle detection |

**Common problems**:
- **Problem**: Majority of CUR spend shows as "untagged" → **Solution**: Activate cost allocation tags in Billing console; enforce tags via Tag Policies/SCPs; implement detection for non-compliant resources.
- **Problem**: Savings Plans/RI coverage near 0% for a steady production baseline → **Solution**: Pull Compute Optimizer rightsizing data first; then purchase Compute Savings Plans to cover the measured baseline.
- **Problem**: Data transfer line items growing silently → **Solution**: Add data-transfer and NAT-gateway line items to CUR dashboards; introduce VPC Gateway endpoints for S3/DynamoDB; evaluate CloudFront for egress-heavy origins.

---

## Verification Loop

Run after each cost architecture review or IaC change:

### 1. Confirm FinOps baseline (COST 1–3)
```bash
# Verify Cost Explorer is active (management account)
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "7 days ago" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY --metrics BlendedCost \
  --query 'ResultsByTime[0].Total.BlendedCost'
# Expected: a numeric value (not an error)

# Verify at least one budget exists
aws budgets describe-budgets --account-id $(aws sts get-caller-identity --query Account --output text)
# Expected: BudgetList with at least one entry
```

### 2. Check tagging compliance (COST 2)
```bash
# Identify untagged EC2 instances (spot-check for mandatory tags)
aws ec2 describe-instances \
  --query 'Reservations[].Instances[?!Tags || length(Tags[?Key==`owner`])==`0`].InstanceId' \
  --output text
# Expected: empty output (all instances tagged with owner)
```

### 3. Verify rightsizing data is available (COST 6)
```bash
aws compute-optimizer get-recommendation-summaries
# Expected: summaries present; "OVER_PROVISIONED" count = 0 (or all addressed)
```

### 4. Check Savings Plans / RI coverage (COST 7)
```bash
# View SP utilization (last 7 days)
aws ce get-savings-plans-utilization \
  --time-period Start=$(date -d "7 days ago" +%Y-%m-%d),End=$(date +%Y-%m-%d)
# Expected: Total.UtilizationPercentage near 100 for any active commitments
```

**Troubleshooting**:
- `NoSuchEntity` on `describe-budgets` → user/role lacks `budgets:DescribeBudgets` permission; add to IAM policy.
- `Compute Optimizer: OptInRequired` → opt in at `aws compute-optimizer update-enrollment-status --status Active`.
- CUR not available in `get-cost-and-usage` → Cost Explorer must be enabled in the management account (one-time activation).

---

## Quick Reference

**COST question → focus area map**:
```
COST 1              → Cloud Financial Management (FinOps)
COST 2, 3, 4        → Expenditure and usage awareness
COST 5, 6, 7, 8     → Cost-effective resources
COST 9              → Manage demand and supply resources
COST 10, 11         → Optimize over time
```

**Pricing model decision shortcut**:
```
Spiky / unknown duration      → On-Demand
Steady baseline, evolving mix → Compute Savings Plans (~72% off, 1-3yr)
Stable, specific instance     → Reserved Instance (~75% off, 1-3yr)
Stateless / fault-tolerant    → Spot (~90% off, interruptible)
```

**Critical limits and key figures**:

| Item | Value | Notes |
|------|-------|-------|
| Dev/test shutdown savings | ~75% | 40 hrs vs 168 hrs/week on-time |
| Savings Plans max discount | ~72% off On-Demand | Varies by term/family/Region |
| Reserved Instance max discount | ~75% off On-Demand | Standard RI, 3-year, all-upfront |
| Spot max discount | ~90% off On-Demand | Interruptible with 2-min notice |
| Spot interruption notice | 2 minutes | Architecture must tolerate this |
| Cost allocation tag activation | Manual | Applied tag ≠ activated tag — activate in Billing console |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/applying-waf-cost-optimization/
├── SKILL.md                          ← This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md         ← Full ✅ patterns with CLI and architecture examples
    ├── ask-first-decisions.md        ← ⚠️ Decision matrices: pricing model, compute model, COST 11
    ├── never-do-patterns.md          ← 🚫 Anti-patterns with ❌ wrong / ✅ correct side-by-side
    └── evaluation-scenarios.md       ← Test cases for skill-evaluator
```

---

## External Resources

### Official Documentation (primary)
- [Cost Optimization Pillar — Welcome](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html) — Definition, focus areas (publication 2024-06-27 ⚠️ >12 months)
- [Design Principles (verbatim)](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html) — Five design principles (2024-06-27 ⚠️ >12 months)
- [Document Revisions](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/document-revisions.html) — Full changelog; verify exact COST xx-BPyy changes from 2024-06-27 refresh
- [Framework — Cost optimization overview](https://docs.aws.amazon.com/wellarchitected/latest/framework/cost-optimization.html) — Always-current framework page (accessed 2026-08-27)

### Focus Area Pages (always-current)
- [Expenditure and usage awareness (COST 2–4)](https://docs.aws.amazon.com/wellarchitected/latest/framework/cost-aware.html)
- [Cost-effective resources (COST 5–8)](https://docs.aws.amazon.com/wellarchitected/latest/framework/cost-cereso.html)
- [Manage demand and supply (COST 9)](https://docs.aws.amazon.com/wellarchitected/latest/framework/cost-mandem.html)
- [Optimize over time (COST 10–11)](https://docs.aws.amazon.com/wellarchitected/latest/framework/cost-opti.html)

### Cost Management Services
- [AWS Cost Optimization Hub](https://aws.amazon.com/aws-cost-management/cost-optimization-hub/) — Consolidated recommendations (accessed 2026-08-27)
- [AWS Savings Plans docs](https://docs.aws.amazon.com/savingsplans/) — Commitment pricing details (accessed 2026-08-27)
- [AWS Graviton](https://aws.amazon.com/ec2/graviton/) — ARM-based price-performance (accessed 2026-08-27)

### Update Announcement
- [WAF guidance updates 2024-06-27](https://aws.amazon.com/blogs/architecture/announcing-updates-to-the-aws-well-architected-framework-guidance-2/) — Blog post covering June 2024 refresh (2024-06-27 ⚠️ >12 months)
