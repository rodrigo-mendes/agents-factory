# Always-Do Patterns — applying-waf-cost-optimization

Source: AWS Well-Architected Framework, Cost Optimization Pillar, edition 2024-06-27 (current stable;
research dated 2026-08-27). Discount figures are indicative "up to" values — they vary by term,
family and Region.

> **Figure note**: the research gives Compute Savings Plans "up to 66%" and EC2 Instance Savings
> Plans / RIs "up to 72%". Where SKILL.md quotes "~72%" for Savings Plans generically, prefer the
> per-plan figures below.

---

## CO-AD-1 — Consumption model: stop idle resources

**Pillar alignment**: Design Principle "Adopt a consumption model"; COST09

**Why**: The design principle cites stopping dev/test outside work hours for ~75% savings. Idle but
running resources are direct waste.

**AWS services**: AWS Instance Scheduler, EC2 Auto Scaling, Aurora Serverless v2 (min 0 ACU,
auto-pause), AWS Lambda

**Architecture decision**:
- Stop dev/test EC2 and RDS instances off-hours with Instance Scheduler.
- Configure Aurora Serverless v2 with min 0 ACU and auto-pause (300–86,400 s) for dev/test
  databases. Scale-to-zero GA November 2024; engines: Aurora PostgreSQL 13.15+/14.12+/15.7+/16.3+,
  Aurora MySQL 3.08+.
- Use Lambda for event-driven workloads that naturally scale to zero.

**Verification**: Cost Explorer usage-hours report (look for 24/7 dev/test EC2/RDS); Instance
Scheduler logs; Lambda invocation patterns.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html (accessed 2026-08-27);
https://aws.amazon.com/blogs/database/introducing-scaling-to-0-capacity-with-amazon-aurora-serverless-v2/ (accessed 2026-08-27)

---

## CO-AD-2 — Right-size resources continuously

**Pillar alignment**: COST06 — Select the correct resource type, size, and number

**Why**: Persistent over-provisioning is continuous waste.

**AWS services**: AWS Compute Optimizer, Cost Explorer rightsizing recommendations, Cost
Optimization Hub

**Architecture decision**:
- Enable Compute Optimizer for all accounts.
- Install the CloudWatch agent with memory metrics on EC2 to improve recommendation accuracy.
- Act on "Over-provisioned" findings; evaluate the performance-risk classification before applying.
- Aggregate recommendations in Cost Optimization Hub.
- Right-size before purchasing commitments (see CO-AD-3).

**Verification**: Compute Optimizer dashboard "Over-provisioned" findings; Cost Optimization Hub
aggregate view.

**Source**: https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html (accessed 2026-08-27)

---

## CO-AD-3 — Implement the right pricing model per component

**Pillar alignment**: COST07-BP04 — Implement pricing models for all components

**Why**: Running all compute On-Demand pays a 66–72% premium for steady workloads.

**AWS services**: Compute Savings Plans, EC2 Instance Savings Plans, Reserved Instances
(RDS/ElastiCache/Redshift/DynamoDB/OpenSearch), EC2 Spot (Spot Fleet/ASG/EMR/ECS/Batch), On-Demand

**Architecture decision**:
- Combine Spot + On-Demand + Savings Plans per workload characteristic.
- Purchase Savings Plans at the **management account** level for organization-wide discount.
- Never use Spot for stateful or uninterruptible workloads (2-minute interruption notice).
- Act when potential savings exceed a threshold (e.g. >20%) rather than chasing fixed coverage %.
- Analysis cycle: every 2 weeks to 1 month; use the net-savings column in Cost Explorer
  utilization/coverage reports.

| Pricing model | Max discount vs On-Demand | Commitment |
|---|---|---|
| Compute Savings Plans | up to 66% | 1/3-year hourly $ commitment |
| EC2 Instance Savings Plans | up to 72% | family + Region locked, 1/3-year |
| Reserved Instances (non-EC2 managed services) | up to 72% | 1/3-year per service configuration |
| Spot | up to 90% | none; 2-minute interruption notice |

**Verification**: Cost Explorer Savings Plans recommendations and utilization/coverage reports;
Cost Optimization Hub pricing-model recommendations.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27);
https://aws.amazon.com/savingsplans/pricing/ (accessed 2026-08-27)

---

## CO-AD-4 — Analyze and attribute expenditure (tagging)

**Pillar alignment**: Design Principle "Analyze and attribute expenditure"

**Why**: Without attribution, owners have no cost visibility; ROI measurement and waste detection
are impossible.

**AWS services**: AWS Organizations, Cost Allocation Tags, Cost Explorer, AWS Budgets, Cost &
Usage Report (CUR)

**Architecture decision**:
- Define and enforce a mandatory tag schema (owner, workload, environment) across all accounts,
  via SCPs or AWS Config rules.
- **Activate** Cost Allocation Tags in the Billing console — applied tags do not appear in CUR or
  Cost Explorer until activated.
- Build per-owner cost dashboards in Cost Explorer; set Budgets alerts per owner/workload (SNS).

**Verification**: Tag coverage in CUR; per-owner dashboards; Budget alert history.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html (accessed 2026-08-27)

---

## CO-AD-5 — Buffer/throttle demand and supply dynamically

**Pillar alignment**: COST09-BP02 (buffer/throttle demand) + COST09-BP03 (supply dynamically)

**Why**: Provisioning for peak load is over-provisioning.

**AWS services**: Amazon SQS, Amazon API Gateway (throttling), EC2 Auto Scaling

**Architecture decision**:
- Place SQS between producers and consumers; scale consumers on queue depth
  (`ApproximateNumberOfMessagesVisible`).
- Apply API Gateway throttling at the ingress layer.
- Configure EC2 Auto Scaling policies to match supply to actual load.

**Trade-off**: adds queue latency — acceptable for async workloads, not for synchronous real-time.

**Verification**: SQS queue depth and age-of-oldest-message metrics; API Gateway throttle metrics;
Auto Scaling activity log.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/manage-demand-and-supply-resources.html (accessed 2026-08-27)

---

## Operational cadence — FinOps operations

- Budget alerts → SNS → Lambda for automated actions (e.g. stop over-budget resources).
- Cost Optimization Hub aggregates Cost Explorer + Compute Optimizer recommendations; since May 2025
  it supports Savings Plans/reservation term and payment-preference configuration.
- Savings Plans and RI purchases remain manual decisions requiring human approval.
- Review cadence: 2 weeks to 1 month.

**Source**: https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html (accessed 2026-08-27);
https://aws.amazon.com/about-aws/whats-new/2025/05/cost-optimization-hub-savings-plans-reservations-preferences/ (2025-05)
