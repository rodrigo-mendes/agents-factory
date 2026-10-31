# Never-Do Patterns — applying-waf-cost-optimization

Source: AWS Well-Architected Framework, Cost Optimization Pillar, edition 2024-06-27 (current stable;
research dated 2026-08-27)

Each anti-pattern lists risk, ❌ wrong / ✅ correct, detection and impact.

---

## CO-ND-1 — 100% On-Demand fleet with no commitment analysis

**Risk level**: HIGH — violates COST07

❌ **Wrong**: steady 24×7 production baseline paid entirely On-Demand.
✅ **Correct**: cover the measured baseline with Compute Savings Plans purchased at the management
account; add Spot for flexible, fault-tolerant work; On-Demand only for burst.

**Detection**: Cost Explorer Savings Plans recommendations showing large untapped savings; no
Savings Plans utilization in Cost Explorer.

**Impact**: paying up to ~3x versus an optimized pricing mix (66–72% premium on steady load).

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

---

## CO-ND-2 — Dev/test running 24/7

**Risk level**: HIGH — violates Design Principle "Adopt a consumption model"

❌ **Wrong**: dev/test EC2 and RDS running around the clock.
✅ **Correct**: AWS Instance Scheduler for off-hours EC2/RDS shutdown; Aurora Serverless v2 with
min 0 ACU and auto-pause for dev/test databases.

**Detection**: Cost Explorer usage-hours report showing 24/7 runtime on resources tagged dev/test.

**Impact**: approximately 4x cost versus off-hours shutdown (~75% savings forgone).

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html (accessed 2026-08-27)

---

## CO-ND-3 — No right-sizing (persistent over-provisioning)

**Risk level**: HIGH — violates COST06

❌ **Wrong**: oversized instances kept indefinitely; recommendations ignored.
✅ **Correct**: Compute Optimizer with the CloudWatch agent (memory metrics); aggregate in Cost
Optimization Hub; right-size before buying commitments.

**Detection**: "Over-provisioned" findings in the Compute Optimizer dashboard.

**Impact**: continuous waste proportional to the over-provisioning ratio.

**Source**: https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html (accessed 2026-08-27)

---

## CO-ND-4 — Savings Plans bought in workload accounts, or chasing fixed coverage %

**Risk level**: MEDIUM — contradicts COST07 guidance

❌ **Wrong**: per-account Savings Plans purchases; "target 80%/100% coverage" objectives.
✅ **Correct**: purchase at the management account in small increments; act when potential savings
exceed a threshold (e.g. >20%); review every 2 weeks to 1 month.

**Detection**: fragmented Savings Plans across accounts with low utilization; Cost Explorer showing
missed org-level discount.

**Impact**: sub-optimal discount application; stranded commitment if usage shifts.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

---

## CO-ND-5 — Spot for stateful or uninterruptible workloads

**Risk level**: HIGH

❌ **Wrong**: primary databases, payment processing or EMR master nodes on Spot.
✅ **Correct**: On-Demand or Reserved Instances for stateful primaries; Spot only for batch, EMR
worker nodes, ECS/Batch, HPC and testing, using multiple instance families.

**Detection**: stateful primary service configured with Spot purchasing in the launch template or
EC2 console.

**Impact**: data loss; availability incident (2-minute interruption notice).

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

---

## CO-ND-6 — No expenditure attribution or tagging

**Risk level**: MEDIUM — violates Design Principle "Analyze and attribute expenditure"

❌ **Wrong**: untagged resources, no activated Cost Allocation Tags, no Budgets.
✅ **Correct**: tag schema (owner, workload, environment) enforced via SCPs or Config rules; tags
activated in the Billing console; per-owner Cost Explorer dashboards; Budgets per workload.

**Detection**: low tag coverage in CUR; no activated Cost Allocation Tags in Billing.

**Impact**: no accountability; unchecked waste; no ROI per product or team.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html (accessed 2026-08-27)

---

## CO-ND-7 — EC2 Reserved Instances without evaluating Compute Savings Plans

**Risk level**: MEDIUM (severity unverified)

❌ **Wrong**: buying EC2 RIs by default.
✅ **Correct**: evaluate Compute Savings Plans first (similar discount, no family/Region lock, also
cover Fargate and Lambda); keep RIs for non-EC2 managed services.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

---

## CO-ND-8 — Ignoring data transfer; never decommissioning (unverified detail)

Listed in SKILL.md (COST04, COST08): routing AWS-service traffic through a NAT gateway instead of
VPC endpoints, and leaving orphaned EBS volumes, unattached Elastic IPs or idle load balancers
running. The research file gives no dated source or detection method for these (unverified).
