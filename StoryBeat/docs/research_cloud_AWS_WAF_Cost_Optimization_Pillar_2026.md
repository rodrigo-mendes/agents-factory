## Metadata
```yaml
Full_Name: "AWS Well-Architected Framework — Cost Optimization Pillar"
Cloud_Provider: "AWS"
Architecture_Domain: "Well-Architected Framework — Cost Optimization Pillar"
Target_Edition: "June 27, 2024 (current stable)"
Architecture_Context: "Multi-account production workloads on AWS"
Official_Source_URL: "https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-27"
Currency_Threshold: "2027-08-27"
```

## Executive Summary

The AWS Well-Architected Framework Cost Optimization Pillar defines the design principles and best practices for running workloads on AWS at the lowest possible price point while meeting all functional requirements. Per the official definition: "A cost-optimized workload fully utilizes all resources, achieves an outcome at the lowest possible price point, and meets your functional requirements." The pillar is organized around five best-practice areas — Practice Cloud Financial Management, Expenditure and usage awareness, Cost effective resources, Manage demand and supply resources, and Optimize over time — and five design principles that shift engineering culture toward treating financial efficiency as a first-class discipline alongside Security and Operations.

The current stable edition is dated June 27, 2024. Subsequent to publication, two significant updates have extended the pillar's tooling ecosystem: Aurora Serverless v2 scale-to-zero reached general availability in November 2024, enabling minimum 0 ACU configurations with auto-pause for supported PostgreSQL and MySQL engine versions; and Cost Optimization Hub added Savings Plans and reservation term and payment-preference configuration in May 2025, aggregating recommendations from Cost Explorer and Compute Optimizer into a single surface. The AWS FinOps Agent (Amazon Q cost capabilities) is in preview as of the research date and its specific capability scope is unverified.

For multi-account production workloads, the three most critical guardrails are: (1) purchase Savings Plans at the management account level — not workload accounts — to maximize organization-wide discount application; (2) stop dev/test environments off-hours using AWS Instance Scheduler or Aurora Serverless v2 scale-to-zero, realizing up to 75% savings per the design principles; and (3) never run Spot instances for stateful or uninterruptible workloads (primary databases, payment processing) — Spot receives a 2-minute interruption notice and is appropriate only for fault-tolerant, stateless workloads.

## Cloud Architecture Glossary

```
Term: Cloud Financial Management (CFM)
Definition: An organizational capability — knowledge, programs, and processes — built to manage cloud spend with the same rigor as Security or Operations. The pillar's first design principle frames it as an investment, not a cost-cutting exercise.
Provider Docs Section: Design Principles — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html
Architect Usage: Treat FinOps as a cross-functional program with designated owners, tagging standards, budget alerts, and regular review cadences — not an ad-hoc response to billing surprises.
Common Confusion: Often confused with simply "reducing costs." CFM includes investment in tooling and process; the goal is efficiency (output per dollar), not minimizing spend at the expense of business outcomes.
```

```
Term: Compute Savings Plans
Definition: A flexible commitment-based pricing model covering EC2, Fargate, and Lambda usage in exchange for a 1- or 3-year hourly dollar commitment. Offers up to 66% discount vs On-Demand.
Provider Docs Section: COST07 — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html
Architect Usage: Preferred over EC2 Instance Savings Plans when the instance family or AWS Region may change. Purchase at management account level to maximize organization-wide coverage.
Common Confusion: Confused with EC2 Instance Savings Plans, which lock to a specific instance family and Region for up to 72% discount. Compute Savings Plans sacrifice ~6% discount for full flexibility across instance types, Regions, and compute types (EC2/Fargate/Lambda).
```

```
Term: Instance Savings Plans
Definition: A commitment-based pricing model locked to a specific EC2 instance family and AWS Region, offering up to 72% discount vs On-Demand. 1- or 3-year hourly dollar commitment.
Provider Docs Section: COST07 — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html
Architect Usage: Use when the instance family and Region are stable and well-understood. Offers slightly higher discount than Compute Savings Plans but with reduced flexibility.
Common Confusion: Confused with Reserved Instances. Instance Savings Plans apply to EC2 and are flexible within the committed family/Region; Reserved Instances apply to non-EC2 managed services (RDS, ElastiCache, Redshift, DynamoDB, OpenSearch).
```

```
Term: Reserved Instances (RIs)
Definition: A commitment-based pricing model for non-EC2 AWS managed services (RDS, ElastiCache, Redshift, DynamoDB, OpenSearch) offering up to 72% discount for 1- or 3-year terms.
Provider Docs Section: COST07 — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html
Architect Usage: Apply RIs to steady-state managed service usage where the service type and configuration are stable. Do not use for EC2 — use Savings Plans instead.
Common Confusion: Architects sometimes purchase EC2 Reserved Instances when Compute or Instance Savings Plans would be more flexible and provide equivalent or better discounts.
```

```
Term: Spot Instances
Definition: Unused EC2 capacity offered at up to 90% discount vs On-Demand, subject to a 2-minute interruption notice when AWS reclaims capacity.
Provider Docs Section: COST07 — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html
Architect Usage: Use for fault-tolerant, stateless workloads: batch processing, EMR, ECS/Batch tasks, HPC, and testing. Combine with Spot Fleet using multiple instance families to reduce interruption probability.
Common Confusion: Incorrectly applied to stateful or latency-sensitive primary workloads where a 2-minute interruption causes data loss or availability incidents.
```

```
Term: Consumption Model
Definition: A design principle prescribing that workloads pay only for resources actually consumed, scaling with demand. The canonical example is stopping dev/test environments outside work hours for approximately 75% savings.
Provider Docs Section: Design Principles — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html
Architect Usage: Architect for elastic scale: use Lambda for event-driven workloads, Aurora Serverless v2 for variable database load, and Instance Scheduler for dev/test shutdown.
Common Confusion: Often equated with "pay-per-use" only for serverless. The consumption model applies to any resource that can be stopped or scaled to zero when idle — including EC2 and RDS.
```

```
Term: Aurora Serverless v2 (scale-to-zero / auto-pause)
Definition: A configuration for Aurora Serverless v2 allowing minimum 0 ACU (Aurora Capacity Units) with auto-pause after a configurable idle period (300–86,400 seconds). GA as of November 2024. Supported engines: Aurora PostgreSQL 13.15+/14.12+/15.7+/16.3+, Aurora MySQL 3.08+.
Provider Docs Section: https://aws.amazon.com/blogs/database/introducing-scaling-to-0-capacity-with-amazon-aurora-serverless-v2/
Architect Usage: Use for dev/test and intermittent production workloads where startup latency on resume is acceptable. Eliminates idle compute cost.
Common Confusion: Confused with Aurora Serverless v1 (deprecated) or Aurora Serverless v2 with a minimum > 0 ACU — only min-0 ACU with auto-pause achieves true scale-to-zero behavior.
```

```
Term: Cost Optimization Hub
Definition: An AWS service that aggregates cost optimization recommendations from Cost Explorer and Compute Optimizer into a single view, with filtering and savings estimates. As of May 2025, supports configuring Savings Plans and reservation term and payment preferences with corresponding savings estimates.
Provider Docs Section: https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html
Architect Usage: Use as the primary aggregation surface for right-sizing and pricing-model recommendations across an organization. Review on a 2-week to 1-month cadence.
Common Confusion: Confused with Cost Explorer (which provides raw usage/cost data and Savings Plans recommendations) or Compute Optimizer (which provides resource-specific right-sizing). Cost Optimization Hub aggregates both.
```

```
Term: Cost Allocation Tags
Definition: Key-value metadata applied to AWS resources that enables cost attribution in Cost Explorer and the Cost & Usage Report (CUR). Must be activated in the Billing console to appear in cost reports.
Provider Docs Section: Design Principles — "Analyze and attribute expenditure" — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html
Architect Usage: Define and enforce a mandatory tag schema (owner, workload, environment) organization-wide via AWS Organizations Service Control Policies or AWS Config rules. Build per-owner cost dashboards from activated tags.
Common Confusion: Confused with resource groups or AWS Config tags. Cost Allocation Tags must be explicitly activated in Billing settings to appear in CUR and Cost Explorer filtering.
```

```
Term: Potential-Savings Threshold
Definition: A COST07 guidance concept recommending that architects act on Savings Plans recommendations when potential savings exceed a defined threshold (e.g., >20%) rather than chasing a fixed coverage percentage.
Provider Docs Section: COST07 — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html
Architect Usage: Replace "target X% coverage" objectives with "act when potential savings exceed Y%" triggers to avoid over-commitment. Review on a 2-week to 1-month analysis cycle.
Common Confusion: Many teams target 80% or 100% coverage, which can drive over-commitment and stranded spend if usage patterns shift.
```

## Architecture Guardrails

### ✅ Mandatory Patterns

**CO-AD-1 — Consumption Model: Stop Idle Resources**
- Pillar Alignment: Cost Optimization — Design Principle: Adopt a consumption model; COST09
- Why: Official design principle: "stop dev/test outside work hours for ~75% savings." Resources that are idle but running are direct waste against the consumption model.
- AWS Services: AWS Instance Scheduler, EC2 Auto Scaling, Aurora Serverless v2 (min 0 ACU, auto-pause), AWS Lambda
- Architecture Decision: Stop dev/test EC2 and RDS instances off-hours using Instance Scheduler. Configure Aurora Serverless v2 with min 0 ACU and auto-pause (300–86,400s) for dev/test databases. Use Lambda for event-driven workloads that naturally scale to zero.
- Verification: Cost Explorer usage-hours report (check for 24/7 dev/test EC2/RDS); Instance Scheduler logs; Lambda invocation patterns.
- Source: COST09 + Design Principles — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html (accessed 2026-08-27)

**CO-AD-2 — Right-Size Resources Continuously**
- Pillar Alignment: Cost Optimization — COST06: Select the correct resource type, size, and number
- Why: COST06 requires selecting the correct resource type, size, and number. Persistent over-provisioning is a continuous cost waste violation.
- AWS Services: AWS Compute Optimizer, Cost Explorer rightsizing recommendations, Cost Optimization Hub
- Architecture Decision: Enable Compute Optimizer for all accounts. Enable CloudWatch agent with memory metrics for EC2 to improve recommendation accuracy. Act on "Over-provisioned" findings; evaluate performance-risk classification before applying. Use Cost Optimization Hub to aggregate recommendations.
- Verification: Compute Optimizer dashboard for "Over-provisioned" findings; Cost Optimization Hub aggregate view.
- Source: COST06 + https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html (accessed 2026-08-27)

**CO-AD-3 — Implement Right Pricing Model per Component**
- Pillar Alignment: Cost Optimization — COST07-BP04: Implement pricing models for all components
- Why: COST07-BP04 requires pricing model coverage for all components. Running all compute On-Demand pays a 66–72% premium for steady workloads.
- AWS Services: Compute Savings Plans, Instance Savings Plans, Reserved Instances (RDS/ElastiCache/Redshift/DynamoDB/OpenSearch), EC2 Spot (Spot Fleet / ASG / EMR / ECS / Batch), On-Demand
- Architecture Decision: Combine Spot + On-Demand + Savings Plans per workload characteristic. Purchase Savings Plans at management account level for maximum organization-wide discount. Never use Spot for stateful or uninterruptible workloads. Track potential-savings threshold (act when >20%); analysis cycle every 2 weeks to 1 month. Use net-savings column in Cost Explorer utilization/coverage reports.
- Verification: Cost Explorer Savings Plans recommendations and utilization/coverage reports (net-savings column); Cost Optimization Hub pricing model recommendations.
- Source: COST07-BP04 + https://aws.amazon.com/savingsplans/pricing/ (accessed 2026-08-27)

**CO-AD-4 — Analyze and Attribute Expenditure (Tagging)**
- Pillar Alignment: Cost Optimization — Design Principle: Analyze and attribute expenditure
- Why: Without expenditure attribution, workload owners have no visibility into cost, making ROI measurement and waste detection impossible.
- AWS Services: AWS Cost Explorer, AWS Budgets, Cost & Usage Report (CUR), Cost Allocation Tags, AWS Organizations
- Architecture Decision: Define and enforce a mandatory tag schema (owner, workload, environment) across all AWS accounts. Activate Cost Allocation Tags in Billing console. Build per-owner cost dashboards in Cost Explorer. Set Budgets alerts per owner/workload.
- Verification: Tag coverage report in Cost & Usage Report; per-owner cost dashboards in Cost Explorer; Budget alert history.
- Source: Design Principles — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html (accessed 2026-08-27)

**CO-AD-5 — Buffer/Throttle Demand and Supply Dynamically**
- Pillar Alignment: Cost Optimization — COST09-BP02 (buffer/throttle demand) + COST09-BP03 (supply dynamically)
- Why: COST09-BP02 and COST09-BP03 require managing both demand smoothing and dynamic supply to avoid over-provisioning for peak load.
- AWS Services: Amazon SQS (buffer), API Gateway (throttling), EC2 Auto Scaling
- Architecture Decision: Place SQS between producers and consumers to smooth demand spikes. Apply API Gateway throttling at the ingress layer. Configure EC2 Auto Scaling policies for dynamic supply matched to actual load.
- Verification: SQS queue depth and age-of-oldest-message metrics in CloudWatch; API Gateway throttle metrics; EC2 Auto Scaling activity log.
- Source: COST09 — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/manage-demand-and-supply-resources.html (accessed 2026-08-27)

### ⚠️ Architectural Decisions

**Decision A — Pricing Model Selection per Workload**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|---------------------------|-----------|------------|-----------|
  | On-Demand | EC2/RDS On-Demand | Full flexibility | Highest unit price (0% discount) | Short-term, spiky, unpredictable, or uninterruptible workloads |
  | Spot | EC2 Spot, Spot in ASG/EMR/ECS/Batch | Up to 90% discount | 2-min interruption notice | Fault-tolerant, stateless: batch, big data, HPC, containers, testing |
  | Compute Savings Plans | Compute SP | Up to 66% discount, most flexible | 1/3-year hourly dollar commitment | Steady compute spend with changing instance mix (EC2/Fargate/Lambda) |
  | Instance Savings Plans | Instance SP | Up to 72% discount | Instance family + Region locked, 1/3-year commitment | Stable instance family and Region usage |
  | Reserved Instances | RDS/ElastiCache/Redshift/DynamoDB/OpenSearch RI | Up to 72% discount | Commitment to service configuration | Non-EC2 managed services with steady, predictable usage |

- Cost Profile: On-Demand is the highest unit price baseline. Spot delivers the largest discount (up to 90%) with interruption risk. Savings Plans and RIs deliver 66–72% discount with commitment risk.
- Lock-in Assessment: Savings Plans: 1/3-year hourly dollar commitment; No Upfront / Partial Upfront / All Upfront payment options. RIs: similar commitment structure. Spot: no commitment, no lock-in, but operational dependency on interruption handling.
- Architect Instruction: "Ask whether the workload is stateless and fault-tolerant before recommending Spot; ask whether the compute mix is stable before recommending Instance over Compute Savings Plans."
- Source: COST07 — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

**Decision B — Database Compute Model for Variable Load**
- Options:

  | Option | Service | Optimizes | Sacrifices | Best When |
  |--------|---------|-----------|------------|-----------|
  | Serverless DB | Aurora Serverless v2 (min 0 ACU, auto-pause) | Scale-to-zero cost, elastic | Resume latency on first connection after pause | Variable or intermittent DB load; dev/test |
  | Provisioned DB + RI | Aurora/RDS provisioned + Reserved Instances | Predictable cost with RI discount | Paying for idle capacity | Steady high utilization |

  (Aurora Serverless v2 scale-to-zero: Aurora PostgreSQL 13.15+/14.12+/15.7+/16.3+, Aurora MySQL 3.08+. GA November 2024.)

- Cost Profile: Aurora Serverless v2 scale-to-zero eliminates idle compute cost entirely; provisioned + RI provides predictable discount for steady workloads.
- Lock-in Assessment: Aurora Serverless v2 is AWS-proprietary; RI commitment is 1/3-year per service configuration.
- Architect Instruction: "Ask whether the first-connection resume latency after auto-pause is acceptable before recommending Aurora Serverless v2 scale-to-zero for production use."
- Source: https://aws.amazon.com/blogs/database/introducing-scaling-to-0-capacity-with-amazon-aurora-serverless-v2/ (accessed 2026-08-27)

**Decision C — Where to Purchase Savings Plans**
- Options:

  | Option | Scope | Discount Application | Sacrifices |
  |--------|-------|---------------------|------------|
  | Management account purchase | Organization-wide | Applies to all member account spend automatically | Must be managed centrally |
  | Workload account purchase | Single account | Only applies to that account's compute spend | Missed cross-account discount opportunities |

- Cost Profile: Management account purchase maximizes organization-wide discount coverage. Workload account purchase limits discount to a single account's spend.
- Lock-in Assessment: 1/3-year commitment; No Upfront / Partial Upfront / All Upfront payment options.
- Architect Instruction: "Ask whether Savings Plans are purchased at the management account level — buying in a workload account limits discount application scope."
- Source: COST07 — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

### 🚫 Anti-Patterns

**CO-ND-1 — 100% On-Demand Fleet with No Commitment Analysis**
- Risk Level: HIGH
- Why: Violates COST07 — paying up to 66–72% premium for steady workloads by foregoing available Savings Plans and Reserved Instance discounts.
- Instead: Cover the stable baseline with Compute Savings Plans (purchased at management account level). Add Spot for flexible, fault-tolerant workloads.
- Detection: Cost Explorer Savings Plans recommendations showing large untapped potential savings; absence of Savings Plans utilization in Cost Explorer.
- Impact: Cost overrun — paying up to 3x vs an optimized pricing mix for equivalent steady-state workloads.
- Source: COST07 — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

**CO-ND-2 — Dev/Test Running 24/7**
- Risk Level: HIGH
- Why: Violates Design Principle "Adopt a consumption model" — official text: "stop dev/test outside work hours for ~75% savings."
- Instead: AWS Instance Scheduler for EC2/RDS off-hours shutdown; Aurora Serverless v2 with min 0 ACU and auto-pause for dev/test databases.
- Detection: Cost Explorer usage-hours report showing 24/7 EC2 or RDS runtime on environments tagged as dev or test.
- Impact: Approximately 4x cost vs a shutdown-off-hours equivalent workload.
- Source: Design Principles — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html (accessed 2026-08-27)

**CO-ND-3 — No Right-Sizing (Persistent Over-Provisioning)**
- Risk Level: HIGH
- Why: Violates COST06 — selecting incorrect (oversized) resource types and sizes without acting on available recommendations.
- Instead: Compute Optimizer with CloudWatch agent (memory metrics) for accuracy; Cost Optimization Hub for aggregated right-sizing recommendations.
- Detection: "Over-provisioned" findings in Compute Optimizer dashboard.
- Impact: Continuous cost waste proportional to the over-provisioning ratio.
- Source: COST06 — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

**CO-ND-4 — Purchase Savings Plans in Workload Account or Chase Fixed Coverage %**
- Risk Level: MEDIUM
- Why: Contradicts explicit COST07 guidance to purchase at management account for maximum org-wide coverage. Targeting a fixed coverage percentage leads to over-commitment when usage patterns change.
- Instead: Purchase Savings Plans at management account level in small increments. Track potential-savings threshold (act when potential savings >20%) instead of a fixed coverage % target. Review every 2 weeks to 1 month.
- Detection: Fragmented Savings Plans applications across individual accounts with low utilization; Cost Explorer showing missed discount opportunities at org level.
- Impact: Sub-optimal discount application; potential stranded commitment if usage shifts.
- Source: COST07 — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

**CO-ND-5 — Spot Instances for Stateful or Uninterruptible Workloads**
- Risk Level: HIGH
- Why: Spot instances receive a 2-minute interruption notice when AWS reclaims capacity. Stateful workloads (primary databases, payment processing) cannot tolerate abrupt termination.
- Instead: On-Demand or Reserved Instances for stateful primary workloads; Spot only for batch, EMR, ECS/Batch, HPC, and testing workloads that handle interruption gracefully.
- Detection: Primary stateful service (e.g., primary RDS, payment service EC2) configured with Spot purchasing in EC2 console or launch template.
- Impact: Data loss; availability incident.
- Source: COST07 — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

**CO-ND-6 — No Expenditure Attribution or Tagging**
- Risk Level: MEDIUM
- Why: Violates Design Principle "Analyze and attribute expenditure" — without attribution, workload owners cannot be held accountable and waste cannot be assigned to a revenue stream or ROI measure.
- Instead: Cost Allocation Tags (owner, workload, environment) activated in Billing console; Cost Explorer per-owner dashboards; Budgets alerts per workload.
- Detection: Low tag coverage percentage in Cost & Usage Report; absence of activated Cost Allocation Tags in Billing console.
- Impact: No cost accountability; unchecked waste across workloads; inability to measure ROI per product or team.
- Source: Design Principles — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html (accessed 2026-08-27)

## Cloud-Native Design Patterns

**Elastic Compute + Commitment Mix**
- Category: Scalability
- Problem: Production workloads have a stable baseline plus variable peak demand; On-Demand for everything is expensive and Spot-only is operationally risky.
- Solution on AWS: Combine Compute Savings Plans (baseline) + EC2 Spot via Auto Scaling Group (variable/flexible) + On-Demand as fallback. Purchase Savings Plans at management account level. Set Spot Fleet to use multiple instance families to reduce interruption frequency.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Discount | Up to 66% (SP) + up to 90% (Spot) on respective portions | 1/3-year SP commitment risk; Spot interruption handling complexity |
  | Flexibility | Compute SP covers EC2/Fargate/Lambda; Spot diversifies instance types | Spot not usable for stateful workloads |
  | Operational | Auto Scaling manages capacity automatically | Requires Spot interruption handler (graceful drain) |

- Source: COST07 — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

**Demand Buffering with SQS**
- Category: Communication
- Problem: Variable producer throughput forces consumer over-provisioning to handle spikes; over-provisioning is waste.
- Solution on AWS: SQS queue between producers and consumers. Consumers (EC2 Auto Scaling or Lambda) scale based on queue depth (ApproximateNumberOfMessagesVisible). API Gateway throttling at ingress layer smooths upstream demand.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Cost | Consumers right-sized to average not peak; eliminate idle capacity | SQS costs (minimal per million messages) |
  | Latency | Adds queue traversal latency | Acceptable for async workloads; not for synchronous real-time |
  | Resilience | Decouples producer and consumer failure domains | Queue depth monitoring required to detect backlogs |

- Source: COST09 — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/manage-demand-and-supply-resources.html (accessed 2026-08-27)

## Security Architecture

**Expenditure Governance via AWS Organizations and Budgets**
- AWS Services: AWS Organizations (Service Control Policies), AWS Budgets, AWS Cost Explorer, Cost Allocation Tags, Cost & Usage Report (CUR)
- Architecture: Define mandatory tag schema enforced via AWS Config rules or SCPs. Activate Cost Allocation Tags in Billing console. Configure Budgets per owner/workload with SNS alerts. CUR feeds cost dashboards for per-owner attribution and anomaly detection.
- Compliance Alignment: Supports internal FinOps governance and cost accountability frameworks; not a compliance certification claim.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html (accessed 2026-08-27)

## Operational Patterns

**Cloud Financial Management (FinOps) Operations**
- RTO/RPO (if applicable): N/A
- AWS Services: Cost Explorer, Cost Optimization Hub, AWS Budgets, Cost & Usage Report (CUR), Cost Allocation Tags
- Cost Profile: Near zero — these are cost-management tools with minimal or no additional service charges.
- Automation: Budget alerts → SNS → Lambda for automated actions (e.g., stop over-budget resources). Cost Optimization Hub aggregates recommendations automatically. Purchases (Savings Plans, RIs) remain manual decisions.
- Source: https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html (accessed 2026-08-27)

**Savings Plans and RI Management Operations**
- RTO/RPO (if applicable): N/A
- AWS Services: Cost Explorer (Savings Plans recommendations), Cost Optimization Hub
- Cost Profile: Management account purchase maximizes coverage; no additional service charge beyond Savings Plan commitment itself.
- Automation: Cost Explorer and Cost Optimization Hub provide recommendations automatically. Purchases are manual decisions requiring human approval. Establish a 2-week to 1-month review cadence. Track potential-savings threshold (act when >20%) rather than fixed coverage %.
- Source: COST07 — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

## Reference Architectures

**Production + Dev/Test Multi-Account Cost-Optimized Architecture**
- Context: Multi-account production workloads with steady-state production and variable dev/test environments
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Compute — Production baseline | EC2 via Compute Savings Plans | Discounted steady-state compute (up to 66%) |
  | Compute — Variable/flexible | EC2 Spot (Spot Fleet, ASG) | Up to 90% discount for fault-tolerant workloads |
  | Database — Production | Aurora/RDS Provisioned + Reserved Instances | Predictable cost with RI discount for steady DB load |
  | Database — Dev/Test | Aurora Serverless v2 (min 0 ACU, auto-pause) | Scale-to-zero when idle |
  | Scheduling | AWS Instance Scheduler | Stop EC2/RDS dev/test off-hours |
  | Demand management | Amazon SQS + API Gateway throttling | Buffer demand; avoid over-provisioning for peaks |
  | Cost attribution | Cost Allocation Tags + Cost Explorer + CUR | Per-owner cost dashboards |
  | Optimization | Cost Optimization Hub + Compute Optimizer | Aggregated right-sizing and pricing-model recommendations |
  | Alerting | AWS Budgets + SNS | Per-workload spend alerts |

- Key Decisions: (1) Compute Savings Plans vs Instance Savings Plans for EC2 (evaluate instance mix stability); (2) Reserved Instances for RDS/ElastiCache/Redshift vs provisioned without commitment; (3) Spot feasibility (is workload stateless and fault-tolerant?); (4) Aurora Serverless v2 resume latency acceptable for dev/test use case.
- Scaling Path: Add Compute Savings Plans incrementally as steady-state baseline grows. Add Spot capacity for new variable workloads. Expand Cost Optimization Hub reviews to cover new accounts.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/ (accessed 2026-08-27)

## Provider Differentiators

**Cost Optimization Hub (May 2025):** Single aggregation surface for Savings Plans, RI, and right-sizing recommendations from Cost Explorer and Compute Optimizer. Now supports configuring Savings Plans and reservation term and payment preferences with savings estimates — eliminating the need to switch between tools for a complete optimization picture.
Source: https://aws.amazon.com/about-aws/whats-new/2025/05/cost-optimization-hub-savings-plans-reservations-preferences/ (2025-05)

**Aurora Serverless v2 Scale-to-Zero (GA November 2024):** Minimum 0 ACU with auto-pause (300–86,400 seconds) eliminates idle database compute cost for qualifying engine versions. No equivalent true scale-to-zero capability was GA for Aurora Serverless v2 prior to November 2024.
Source: https://aws.amazon.com/blogs/database/introducing-scaling-to-0-capacity-with-amazon-aurora-serverless-v2/

**AWS FinOps Agent (preview):** Amazon Q cost capabilities. Specific capability scope is unverified (preview as of research date).
Source: https://docs.aws.amazon.com/finops-agent/latest/userguide/optimization-recommendations.html

## Scenario Coverage

**Standard Case**: Production + dev/test workloads with steady-state production and variable dev/test
- Approach: Compute Savings Plans for production baseline + Spot (Spot Fleet with multiple instance families) for flexible workloads + Aurora Serverless v2 scale-to-zero and Instance Scheduler for dev/test shutdown. Cost Explorer, Budgets, and Cost Allocation Tags for attribution and alerting.
- Key Decisions: (1) Savings Plans vs RIs — EC2 and Fargate use Compute Savings Plans; RDS/ElastiCache/Redshift/DynamoDB/OpenSearch use Reserved Instances. (2) Spot feasibility — confirm workload is stateless and fault-tolerant. (3) Where to purchase Savings Plans — management account for maximum coverage.

**Edge Case**: Large batch processing workloads (EMR, data pipelines)
- Approach: EC2 Spot for EMR and batch tasks using Spot Fleet with multiple instance families to minimize interruption probability. On-Demand for EMR master nodes (uninterruptible coordinator). SQS for job buffering between pipeline stages. Up to 90% cost reduction vs On-Demand for worker nodes.

**Anti-Pattern Case**: Team requests Reserved Instances for EC2 to save money
- Clarification: Ask whether Compute Savings Plans were evaluated before recommending EC2 Reserved Instances. Compute Savings Plans offer similar discounts (up to 66%) with significantly more flexibility — no instance family or Region lock — and also cover Fargate and Lambda. Reserved Instances are the preferred commitment vehicle for non-EC2 managed services (RDS, ElastiCache, Redshift, DynamoDB, OpenSearch) where no Savings Plans equivalent exists.
