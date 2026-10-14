---
name: optimizing-aws-costs
description: "Applies AWS Well-Architected Framework Cost Optimization Pillar patterns for multi-account production workloads. Use when designing cost-efficient AWS architectures, selecting pricing models (Savings Plans, Reserved Instances, Spot), right-sizing resources, or implementing FinOps governance and expenditure attribution."
---

## Function

Specialist in AWS Well-Architected Framework Cost Optimization Pillar for multi-account production workloads on AWS.

## Version Context

**Framework**: AWS Well-Architected Framework — Cost Optimization Pillar
**Target edition**: June 27, 2024 (current stable)
**Research date**: 2026-08-27
**Currency threshold**: 2027-08-27
**Support status**: Active

**Significant post-publication updates**:
- **Aurora Serverless v2 scale-to-zero** — GA November 2024; minimum 0 ACU with auto-pause (300–86,400s). Supported engines: Aurora PostgreSQL 13.15+/14.12+/15.7+/16.3+, Aurora MySQL 3.08+.
- **Cost Optimization Hub (May 2025)** — added Savings Plans and reservation term/payment-preference configuration, eliminating cross-tool switching for a full optimization picture.
- **AWS FinOps Agent** — Amazon Q cost capabilities; preview as of research date; capability scope is **unverified**.

**Deprecated**: Aurora Serverless v1 (do not reference for new designs).

> ⚠️ **CRITICAL — Agent Warning**:
> Patterns below apply to the June 2024 edition + the two GA updates above.
> Do not apply Reserved Instances guidance to EC2 (use Savings Plans instead).
> Do not apply Savings Plans guidance to non-EC2 managed services (use RIs instead).

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 operational tiers
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases for skill-evaluator
- **[Integration Patterns](#integration-patterns)** — Elastic Compute Mix, Demand Buffering
- **[Verification Loop](#verification-loop)** — Cost Explorer and Compute Optimizer checks
- **[Quick Reference](#quick-reference)** — Pricing model selection table and key limits
- **[External Resources](#external-resources)** — Official dated sources

---

## Blueprints & Guardrails

### ✅ Always Do

**CO-1 — Stop Idle Resources (Consumption Model)**
Stop dev/test EC2 and RDS instances off-hours via AWS Instance Scheduler. Configure Aurora Serverless v2 with min 0 ACU and auto-pause for dev/test databases. Use Lambda for event-driven workloads that naturally scale to zero.
Omitting this violates Design Principle "Adopt a consumption model" — official guidance cites ~75% savings for dev/test shutdown.
_Services_: Instance Scheduler, EC2 Auto Scaling, Aurora Serverless v2, Lambda.

**CO-2 — Right-Size Resources Continuously**
Enable Compute Optimizer for all accounts. Enable CloudWatch agent with memory metrics on EC2 to improve recommendation accuracy. Act on "Over-provisioned" findings after evaluating the performance-risk classification. Aggregate right-sizing recommendations via Cost Optimization Hub.
Omitting this violates COST06 (select the correct resource type, size, and number).
_Services_: Compute Optimizer, CloudWatch agent, Cost Optimization Hub.

**CO-3 — Implement the Right Pricing Model per Component**
Combine Compute Savings Plans (stable EC2/Fargate/Lambda baseline) + EC2 Spot (fault-tolerant, stateless workloads) + Reserved Instances (non-EC2 managed services: RDS, ElastiCache, Redshift, DynamoDB, OpenSearch). Purchase Savings Plans at management account level. Track the potential-savings threshold: act when projected savings exceed 20%; review every 2–4 weeks. Never use a fixed coverage-% target — it drives over-commitment.
Omitting this violates COST07-BP04 — running all compute On-Demand pays a 66–72% premium on steady workloads.
_Services_: Compute Savings Plans, Instance Savings Plans, Reserved Instances, EC2 Spot, Cost Explorer.

**CO-4 — Analyze and Attribute Expenditure (Tagging)**
Define and enforce a mandatory tag schema (owner, workload, environment) across all accounts. Activate Cost Allocation Tags in the Billing console (tags must be explicitly activated to appear in CUR and Cost Explorer). Build per-owner cost dashboards in Cost Explorer. Set Budgets alerts per owner/workload.
Omitting this violates Design Principle "Analyze and attribute expenditure" — without attribution, workload owners cannot be held accountable and waste cannot be assigned to ROI.
_Services_: Cost Explorer, AWS Budgets, Cost & Usage Report (CUR), Cost Allocation Tags, AWS Organizations.

**CO-5 — Buffer and Throttle Demand Dynamically**
Place SQS between producers and consumers to smooth demand spikes. Apply API Gateway throttling at the ingress layer. Configure EC2 Auto Scaling to supply capacity matched to actual queue depth or load metrics.
Omitting this violates COST09-BP02 and COST09-BP03 — over-provisioning for peak demand is waste.
_Services_: SQS, API Gateway, EC2 Auto Scaling.

---

### ⚠️ Ask First

**Decision A — Pricing Model Selection per Workload Component**
Ask these questions before recommending a pricing model:
1. Is the workload stateless and fault-tolerant (tolerates 2-minute interruption)? → If yes, Spot is eligible.
2. Is the instance family and AWS Region stable and well-understood? → If yes, consider Instance Savings Plans (72% discount) over Compute Savings Plans (66% discount, more flexible).
3. Is the service non-EC2 (RDS, ElastiCache, Redshift, DynamoDB, OpenSearch)? → Reserved Instances required (no Savings Plans equivalent).

| Option | Max Discount | Commitment | Best When |
|---|---|---|---|
| On-Demand | 0% | None | Spiky, short-term, uninterruptible |
| Spot | up to 90% | None | Stateless, fault-tolerant batch/HPC/ECS |
| Compute Savings Plans | up to 66% | 1/3-yr hourly $ | Stable compute, changing instance mix |
| Instance Savings Plans | up to 72% | 1/3-yr hourly $, family+Region locked | Stable family and Region |
| Reserved Instances | up to 72% | 1/3-yr, service config locked | Non-EC2 managed services |

**Decision B — Database Compute Model for Variable Load**
Ask whether first-connection resume latency after auto-pause is acceptable before recommending Aurora Serverless v2 scale-to-zero for production use.

| Option | Optimizes | Sacrifices | Best When |
|---|---|---|---|
| Aurora Serverless v2 (min 0 ACU, auto-pause) | Scale-to-zero; no idle cost | Resume latency on first connection after pause | Variable/intermittent load; dev/test |
| Provisioned + Reserved Instances | Predictable cost, no resume delay | Paying for idle capacity | Steady high utilization |

**Decision C — Where to Purchase Savings Plans**
Ask whether the organization has a management account structure before recommending a purchase point.

| Option | Discount Scope | Trade-off |
|---|---|---|
| Management account purchase | All member accounts automatically | Requires centralized FinOps function |
| Workload account purchase | Single account only | Misses cross-account discount opportunities |

---

### 🚫 Never Do

| Anti-Pattern | Risk | Alternative |
|---|---|---|
| **100% On-Demand fleet with no commitment analysis** | HIGH — pays 66–72% premium vs optimized pricing mix | Cover steady baseline with Compute Savings Plans at management account level; add Spot for fault-tolerant workloads |
| **Dev/test running 24/7** | HIGH — ~4x cost vs off-hours shutdown | AWS Instance Scheduler for EC2/RDS; Aurora Serverless v2 min 0 ACU + auto-pause for databases |
| **No right-sizing (persistent over-provisioning)** | HIGH — continuous waste proportional to over-provisioning ratio | Compute Optimizer + CloudWatch memory metrics; Cost Optimization Hub |
| **Savings Plans purchased in workload account or targeting fixed coverage %** | MEDIUM — sub-optimal discount scope; over-commitment risk if usage shifts | Purchase at management account; track potential-savings threshold (>20%), review every 2–4 weeks |
| **Spot instances for stateful or uninterruptible workloads** | HIGH — data loss; availability incident (2-minute notice, no grace period) | On-Demand or Reserved Instances for primary databases, payment services, and uninterruptible coordination nodes |
| **No expenditure attribution or tagging** | MEDIUM — unchecked waste; no cost accountability; cannot measure ROI per product | Cost Allocation Tags (activated in Billing console) + Cost Explorer per-owner dashboards + Budgets alerts |

---

## Integration Patterns

**Elastic Compute + Commitment Mix (Production Baseline)**
Combine Compute Savings Plans (stable baseline: EC2/Fargate/Lambda) + EC2 Spot via Auto Scaling Group with multiple instance families (reduces interruption frequency) + On-Demand fallback. Purchase Savings Plans at management account level.

| Dimension | Benefit | Cost |
|---|---|---|
| Discount | Up to 66% (SP) + up to 90% (Spot) on respective portions | 1/3-year SP commitment risk; Spot interruption handling complexity |
| Flexibility | Compute SP covers EC2/Fargate/Lambda; Spot diversifies instance types | Spot not usable for stateful workloads |

**Demand Buffering with SQS (Variable Workloads)**
SQS queue between producers and consumers. Consumers (EC2 Auto Scaling or Lambda) scale on `ApproximateNumberOfMessagesVisible`. API Gateway throttling at ingress. Right-sizes consumers to average load, not peak.

| Dimension | Benefit | Cost |
|---|---|---|
| Cost | Eliminate idle peak-capacity over-provisioning | SQS message costs (minimal) |
| Latency | Decouples failure domains | Queue traversal; not suitable for synchronous real-time |

**FinOps Governance Integration**
Budget alerts → SNS → Lambda for automated actions (e.g., stop over-budget resources). Cost Optimization Hub aggregates Compute Optimizer + Cost Explorer recommendations into a single review surface. Review cadence: every 2–4 weeks. Purchases (Savings Plans, RIs) remain manual, human-approved decisions.

**Common Problems**:
- **Cost Allocation Tags not appearing in CUR** → Tags must be explicitly activated in the Billing console; activation is not automatic.
- **Savings Plans under-coverage** → Check that purchase was made at management account, not a workload account; verify utilization/coverage report net-savings column in Cost Explorer.
- **Compute Optimizer accuracy low for EC2** → Install CloudWatch agent with memory metrics; without it, only CPU-based recommendations are available.

---

## Verification Loop

The agent MUST verify these after each cost optimization recommendation:

### 1. Pricing Model Coverage
```
# Cost Explorer → Savings Plans → Coverage report
# Check: net-savings column; act if potential savings > 20%
# Expected: baseline compute covered by Savings Plans at management account level
# Spot instances present only for stateless/fault-tolerant workload components
```

### 2. Dev/Test Shutdown Coverage
```
# Cost Explorer → Usage hours report
# Filter: tags environment=dev OR environment=test
# Expected: EC2 and RDS show 0 usage-hours during off-hours windows
# Aurora Serverless v2: min ACU = 0, auto-pause = enabled
```

### 3. Right-Sizing Findings
```
# AWS Compute Optimizer dashboard
# Filter: Finding = "Over-provisioned"
# Expected: zero unaddressed High-confidence Over-provisioned findings older than 30 days
# Cost Optimization Hub: aggregate view shows no persistent High-savings recommendations ignored
```

### 4. Tagging and Attribution
```
# Cost & Usage Report → tag coverage analysis
# Expected: > 90% of resources tagged with owner, workload, environment
# Cost Allocation Tags: activated in Billing console
# Budgets: at least one budget per workload with SNS alert configured
```

**Troubleshooting**:
- Over-provisioned findings not improving → Verify CloudWatch agent is installed with memory metrics on EC2
- Savings Plans underutilized → Check purchase account level (must be management account); reduce commitment increment
- Tags missing from Cost Explorer → Verify tags are activated in Billing console (not just applied to resources)

---

## Quick Reference

**Pricing model selection decision tree**:
```
Is workload stateless + fault-tolerant? → Spot (up to 90% discount)
Is it steady EC2/Fargate/Lambda with changing instance mix? → Compute Savings Plans (up to 66%)
Is it steady EC2 with stable family + Region? → Instance Savings Plans (up to 72%)
Is it RDS/ElastiCache/Redshift/DynamoDB/OpenSearch? → Reserved Instances (up to 72%)
Otherwise → On-Demand
```

**Key limits and thresholds**:

| Parameter | Value | Scope |
|---|---|---|
| Dev/test savings from shutdown | ~75% | Per official Design Principle |
| Compute Savings Plans discount | up to 66% | EC2, Fargate, Lambda |
| Instance Savings Plans discount | up to 72% | EC2 (family + Region locked) |
| Reserved Instances discount | up to 72% | RDS, ElastiCache, Redshift, DynamoDB, OpenSearch |
| Spot discount | up to 90% | EC2 (2-min interruption notice) |
| Spot interruption notice | 2 minutes | No extension possible |
| Potential-savings action threshold | >20% | COST07 recommendation |
| Savings Plans review cadence | 2–4 weeks | COST07 recommendation |
| Aurora Serverless v2 auto-pause range | 300–86,400 seconds | scale-to-zero configurations |
| Cost Allocation Tag activation | Manual in Billing console | Required for CUR/Cost Explorer visibility |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/optimizing-aws-costs/
├── SKILL.md                          <- This file (guardrails + quick reference)
└── blueprints/
    └── evaluation-scenarios.md       <- 6 test cases for skill-evaluator
```

---

## External Resources

### Official Documentation
- [Cost Optimization Pillar — Main](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/) — June 27, 2024 edition (primary reference)
- [Design Principles](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html) — Consumption model, expenditure attribution
- [COST06 — Select Resource Type, Size, Number](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-correct-resource-type-size-and-number.html)
- [COST07 — Select Best Pricing Model](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html)
- [COST09 — Manage Demand and Supply](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/manage-demand-and-supply-resources.html)

### Tools and Updates
- [Cost Optimization Hub](https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html) — May 2025: Savings Plans + RI preferences added
- [Aurora Serverless v2 Scale-to-Zero](https://aws.amazon.com/blogs/database/introducing-scaling-to-0-capacity-with-amazon-aurora-serverless-v2/) — GA November 2024
- [Savings Plans Pricing](https://aws.amazon.com/savingsplans/pricing/) — Current discount rates and commitment options
- [Cost Optimization Hub launch update](https://aws.amazon.com/about-aws/whats-new/2025/05/cost-optimization-hub-savings-plans-reservations-preferences/) — May 2025
