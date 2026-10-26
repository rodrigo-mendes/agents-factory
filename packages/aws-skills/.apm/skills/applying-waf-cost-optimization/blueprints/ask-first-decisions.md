# Ask-First Decisions — applying-waf-cost-optimization

Source: AWS Well-Architected Framework, Cost Optimization Pillar, edition 2024-06-27 (current stable;
research dated 2026-08-27)

These decisions depend on workload and organizational context. Gather the indicated information
before recommending. Commitment purchases (Savings Plans/RIs) are always Ask-First.

---

## Decision A — Pricing model selection per workload

**Pillar alignment**: COST07

**Before recommending, ask**:
> "Is the workload stateless and fault-tolerant?" (before Spot)
> "Is the compute mix (instance family, Region, EC2/Fargate/Lambda) stable?" (before Instance over
> Compute Savings Plans)

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| On-Demand | EC2/RDS On-Demand | Full flexibility | Highest unit price | Short-term, spiky, unpredictable, or uninterruptible |
| Spot | EC2 Spot, Spot in ASG/EMR/ECS/Batch | Up to 90% discount | 2-minute interruption notice | Fault-tolerant, stateless: batch, big data, HPC, containers, testing |
| Compute Savings Plans | Compute SP | Up to 66%, most flexible | 1/3-year hourly $ commitment | Steady spend with changing mix (EC2/Fargate/Lambda) |
| EC2 Instance Savings Plans | Instance SP | Up to 72% | Family + Region locked | Stable instance family and Region |
| Reserved Instances | RDS/ElastiCache/Redshift/DynamoDB/OpenSearch RI | Up to 72% | Commitment to service configuration | Non-EC2 managed services with steady usage |

**Cost profile**: On-Demand is the baseline; Spot gives the largest discount with interruption risk;
Savings Plans/RIs give 66–72% with commitment risk.

**Lock-in assessment**: Savings Plans and RIs are 1/3-year commitments with No Upfront / Partial
Upfront / All Upfront options. Spot has no commitment but requires interruption handling.

**Architect instruction**: If a team asks for EC2 Reserved Instances, ask whether Compute Savings
Plans were evaluated — they give similar discounts without family/Region lock and also cover
Fargate and Lambda. RIs are the vehicle for non-EC2 managed services.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

---

## Decision B — Database compute model for variable load

**Pillar alignment**: Consumption model (Design Principles); COST09

**Before recommending, ask**:
> "Is the first-connection resume latency after auto-pause acceptable for this workload?"

| Option | Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| Serverless DB | Aurora Serverless v2 (min 0 ACU, auto-pause) | Scale-to-zero, elastic | Resume latency after pause | Variable or intermittent load; dev/test |
| Provisioned DB + RI | Aurora/RDS provisioned + Reserved Instances | Predictable cost with RI discount | Paying for idle capacity | Steady high utilization |

**Constraints**: scale-to-zero GA November 2024; auto-pause 300–86,400 s; engines Aurora PostgreSQL
13.15+/14.12+/15.7+/16.3+, Aurora MySQL 3.08+. Only min 0 ACU + auto-pause is true scale-to-zero.

**Lock-in assessment**: Aurora Serverless v2 is AWS-proprietary; RI commitment is 1/3-year per
service configuration.

**Source**: https://aws.amazon.com/blogs/database/introducing-scaling-to-0-capacity-with-amazon-aurora-serverless-v2/ (accessed 2026-08-27)

---

## Decision C — Where to purchase Savings Plans

**Pillar alignment**: COST07

**Before recommending, ask**:
> "Are Savings Plans purchased at the management account level?"

| Option | Scope | Discount application | Sacrifices |
|---|---|---|---|
| Management account purchase | Organization-wide | Applies to member-account spend | Must be managed centrally |
| Workload account purchase | Single account | Only that account's compute spend | Missed cross-account discount |

**Architect instruction**: Purchase in small increments; act on a potential-savings threshold
(e.g. >20%) rather than a fixed coverage %; review every 2 weeks to 1 month.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

---

## Decision D — Compute model for cost efficiency (unverified detail)

**Pillar alignment**: COST05

**Before recommending, ask**:
> "What is the utilization pattern (steady vs spiky) and the team's operational capacity?"

Options as summarized in SKILL.md: serverless (Lambda/Fargate — zero idle cost) vs managed
containers vs self-managed EC2 (lowest unit cost at scale). The research file gives no option
matrix or utilization crossover point for this decision (unverified).

---

## Decision E — Cost of effort and chargeback vs showback (unverified detail)

**Pillar alignment**: COST11 (cost of effort); COST02/COST03 (attribution)

**Before recommending, ask**:
> "How often does the operation run and what is the fully-loaded human cost?"
> "Does the organization bill cost back to teams/tenants, or only report it?"

These decision points come from SKILL.md; the research file provides no option matrix or dated
source for them (unverified). Do not prescribe thresholds.
