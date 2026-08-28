# Cloud Architecture Research — AWS Well-Architected Framework: Sustainability Pillar

## Metadata
```yaml
Full_Name: "AWS Well-Architected Framework — Sustainability Pillar"
Cloud_Provider: "AWS"
Architecture_Domain: "Well-Architected Framework — Sustainability Pillar"
Target_Edition: "November 6, 2024 (current stable)"
Architecture_Context: "Multi-account production workloads on AWS"
Official_Source_URL: "https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-27"
Currency_Threshold: "2027-08-27"
```

## Executive Summary

The Sustainability Pillar of the AWS Well-Architected Framework focuses on environmental sustainability for cloud workloads. As stated in the official documentation: "This document focuses on the sustainability pillar, and within the scope of sustainability, it focuses on environmental sustainability." It provides design principles, operational guidance, best-practices, potential trade-offs and improvement plans architects can use to meet sustainability targets for AWS workloads. The pillar is structured around six best-practice areas: Region selection (SUS01), Alignment to demand (SUS02), Software and architecture (SUS03), Data management (SUS04), Hardware and services (SUS05), and Process and culture (SUS06).

The November 6, 2024 edition introduced notable updates: a new best practice SUS06-BP01 ("Communicate and cascade your sustainability goals") and 10 best practices updated across six questions (SUS01, SUS03–SUS06). These updates reflect AWS's increasing operational emphasis on measurable goals and organizational accountability, not merely technical optimization. The edition is flagged as >12 months old but remains the current stable release as of the research date, and is treated as authoritative per Version Absolutism.

For multi-account production workloads on AWS, the three most critical guardrails are: (1) always scale dynamically to match demand — never statically over-provision; (2) apply storage lifecycle policies to all data; and (3) establish per-unit sustainability KPIs and cascade goals to teams via SUS06-BP01 so that regressions are detectable and accountable across accounts.

Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html (pub. Nov 6, 2024 — ⚠️ >12mo, current stable)

---

## Cloud Architecture Glossary

```
Term: Sustainability Pillar
Definition: One of the six pillars of the AWS Well-Architected Framework. Focused exclusively on
  environmental sustainability of cloud workloads — measuring, minimizing and improving the
  environmental impact (energy, carbon, resources) of workloads running on AWS.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html
Architect Usage: Apply when reviewing workload design for environmental impact; run alongside cost,
  reliability, performance, security, and operational excellence pillars.
Common Confusion: Confused with cost optimization — sustainability and cost often correlate but are
  distinct goals; reducing cost does not automatically reduce environmental impact.
```

```
Term: SUS01 — Region Selection
Definition: Best-practice area requiring that Region placement decisions account for sustainability
  goals (carbon grid intensity, proximity to users) in addition to latency and compliance needs.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/region-selection.html
Architect Usage: Document Region selection rationale using Customer Carbon Footprint Tool data;
  trade-off analysis between carbon footprint and latency/data residency must be explicit.
Common Confusion: Treated as purely a latency/compliance decision; sustainability impact of grid
  carbon intensity is ignored.
```

```
Term: SUS02 — Alignment to Demand
Definition: Best-practice area requiring that infrastructure provisioned at any moment matches
  actual workload demand — no static over-provisioning. Includes SUS02-BP01 (scale to demand),
  SUS02-BP02 (align SLAs with sustainability goals), SUS02-BP03 (eliminate idle resources).
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/align-utilization-with-user-load.html
Architect Usage: Enforce elastic capacity with Auto Scaling / Lambda / Fargate; run Compute
  Optimizer to identify over-provisioned resources; delete unattached EBS volumes and idle assets.
Common Confusion: Conflated with cost savings only — the goal is resource efficiency (energy),
  which has a sustainability rationale independent of cost.
```

```
Term: SUS04 — Data Management
Definition: Best-practice area focused on minimizing the storage footprint: use data classification,
  lifecycle policies, deduplication, and cold storage to reduce powered-storage volume.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/data-management.html
Architect Usage: Require S3 Lifecycle or Intelligent-Tiering on all S3 buckets; expire obsolete
  data; deduplicate; use cold tiers (Glacier / Deep Archive) for infrequent access.
Common Confusion: Treated as a backup/archive concern rather than a continuous data-lifecycle
  discipline applied to all storage.
```

```
Term: SUS05 — Hardware and Services
Definition: Best-practice area requiring use of latest-generation hardware and managed/serverless
  services to maximize hardware energy efficiency and multi-tenant utilization.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/hardware-and-services.html
Architect Usage: Prefer Graviton-based instances; adopt managed services (RDS, SQS, Fargate)
  instead of self-managed EC2; audit instance generation via Compute Optimizer.
Common Confusion: Assumed to apply only to on-premises hardware; applies equally to EC2 instance
  generation selection on AWS.
```

```
Term: SUS06 — Process and Culture
Definition: Best-practice area requiring organizational processes and cultural practices that
  operationalize sustainability: goal-setting, measurement, communication, and cascading targets.
  SUS06-BP01 (new Nov 2024): "Communicate and cascade your sustainability goals."
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/process-and-culture.html
Architect Usage: Establish per-unit-of-work KPIs tracked in CloudWatch; schedule quarterly
  Customer Carbon Footprint Tool reviews; document and publish sustainability goals per workload.
Common Confusion: Treated as a "soft" or optional pillar — in Nov 2024 update it gained a new
  mandatory best practice and 10 updated practices, signaling increased structural weight.
```

```
Term: AWS Customer Carbon Footprint Tool
Definition: AWS-provided tool that reports estimated carbon emissions associated with AWS service
  usage, enabling architects to track and reduce carbon footprint per account or organization.
Provider Docs Section: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/what-is-ccft.html
Architect Usage: Use for Region selection rationale (SUS01-BP01) and for ongoing KPI tracking
  (SUS06); schedule monthly review; generate trend data to detect regressions.
Common Confusion: Confused with AWS Cost Explorer — Carbon Footprint Tool reports carbon, not
  cost; the two tools complement each other but measure different things.
```

```
Term: AWS Compute Optimizer
Definition: ML-based AWS service that analyzes workload utilization patterns and recommends
  right-sized EC2 instances, Lambda functions, EBS volumes, ECS tasks, and Auto Scaling groups.
Provider Docs Section: https://docs.aws.amazon.com/compute-optimizer/latest/ug/what-is-compute-optimizer.html
Architect Usage: Run as the first step in a sustainability audit to identify over-provisioned
  resources (SUS02-BP03); act on "over-provisioned" and "under-utilized" findings.
Common Confusion: Confused with AWS Trusted Advisor — both surface idle/under-used resources but
  Compute Optimizer uses ML on utilization history while Trusted Advisor applies threshold rules.
```

```
Term: Maximize Utilization (Design Principle)
Definition: One of the six sustainability design principles. Requires right-sizing workloads and
  implementing efficient design for high utilization. Official rationale: "Two hosts running at 30%
  utilization are less efficient than one host running at 60% due to baseline power consumption per
  host."
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html
Architect Usage: Validate all always-on resources against utilization metrics; consolidate where
  possible; eliminate baseline waste from idle fleets.
Common Confusion: Interpreted as 100% utilization target — the goal is to eliminate idle waste,
  not to saturate resources to the point of reliability risk.
```

```
Term: Use Managed Services (Design Principle)
Definition: One of the six sustainability design principles. States that "sharing services across a
  broad customer base maximizes resource utilization." Names AWS Fargate (serverless containers),
  Amazon S3 Lifecycle configurations, and Amazon EC2 Auto Scaling explicitly.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html
Architect Usage: Default to managed/serverless services; justify any self-managed EC2 alternative;
  adopt Graviton instances for further efficiency.
Common Confusion: Understood as a cost or operational convenience principle only — its primary
  sustainability rationale is multi-tenant hardware utilization, not reduced operational burden.
```

```
Term: Reduce Downstream Impact (Design Principle)
Definition: One of the six sustainability design principles. Requires reducing energy/resources
  required by customers to use cloud-backed services; includes reducing or eliminating the need for
  customers to upgrade devices; recommends testing with device farms.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html
Architect Usage: Include downstream device impact in sustainability assessments; test client
  applications with device farms; minimize payload sizes and client-side compute requirements.
Common Confusion: Treated as a UX concern — it is a sustainability concern: unnecessary client
  upgrades cause e-waste and downstream energy consumption.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**SUS-AD-A — Region Selection Based on Sustainability and Business Goals (SUS01-BP01)**
- Pillar Alignment: SUS01 Region Selection; Design Principle "Understand your impact"
- Why: Region choice significantly affects carbon footprint. The design principle "Understand your impact" requires measuring impact including all sources. Region grid carbon intensity is a primary variable.
- AWS Services: AWS Customer Carbon Footprint Tool; Region placement near renewable/low-carbon energy and near users.
- Architecture Decision:
  Place workloads in Regions aligned to sustainability goals while simultaneously meeting latency and data-residency requirements. Document the trade-off rationale explicitly. Use Customer Carbon Footprint Tool to compare Region options.
- Verification:
  Customer Carbon Footprint Tool monthly trend reports; documented Region selection rationale in architecture decision records.
- Source: SUS01-BP01 https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/region-selection.html [triangulated with design principle "Understand your impact"]

**SUS-AD-B — Scale Infrastructure Dynamically to Match Demand (SUS02-BP01)**
- Pillar Alignment: SUS02 Alignment to Demand; Design Principle "Maximize utilization"
- Why: "Maximize utilization — use only minimum resources required." Static fleets running at low utilization violate this principle by consuming baseline power without productive output.
- AWS Services: Amazon EC2 Auto Scaling, AWS Auto Scaling, AWS Lambda (scale-to-zero), AWS Fargate, Kubernetes/Karpenter on EKS.
- Architecture Decision:
  Implement elastic capacity using target-tracking Auto Scaling policies tied to CloudWatch utilization metrics. Prefer Lambda or Fargate for workloads with spiky or event-driven demand patterns where scale-to-zero is achievable.
- Verification:
  Auto Scaling groups with target-tracking policies in place; CloudWatch utilization metrics confirm no sustained low-utilization periods; Compute Optimizer shows no "over-provisioned" flags.
- Source: SUS02-BP01 + design principle #3 "Maximize utilization" (naming EC2 Auto Scaling) [triangulated]

**SUS-AD-C — Stop Idle and Orphaned Resources (SUS02-BP03)**
- Pillar Alignment: SUS02 Alignment to Demand; Design Principle "Maximize utilization"
- Why: Idle resources consume baseline energy continuously. "Eliminate/minimize idle resources" is an explicit directive under the "Maximize utilization" principle.
- AWS Services: AWS Trusted Advisor (idle/underutilized checks), AWS Compute Optimizer, AWS Cost Explorer; delete unattached EBS volumes, idle EC2 instances, and idle load balancers.
- Architecture Decision:
  Continuously identify and remove or right-size idle assets. Implement automated cleanup for unattached EBS volumes and stopped instances beyond a threshold. Review Trusted Advisor and Compute Optimizer findings on a weekly cadence.
- Verification:
  Compute Optimizer "over-provisioned" findings resolved or accepted with justification; Trusted Advisor idle-resource checks showing zero open items; no unattached EBS volumes in account inventory.
- Source: SUS02-BP03 + design principle "Maximize utilization" [triangulated]

**SUS-AD-D — Storage Lifecycle Optimization (SUS04 Data Management)**
- Pillar Alignment: SUS04 Data Management; Design Principle "Use managed services"
- Why: Minimize provisioned and powered storage. Design principle #5 explicitly names S3 Lifecycle configurations as a mechanism to move infrequently accessed data to cold storage.
- AWS Services: Amazon S3 Lifecycle configurations, S3 Intelligent-Tiering, S3 Glacier / Glacier Deep Archive, Amazon EBS snapshot lifecycle, Amazon Data Lifecycle Manager.
- Architecture Decision:
  Require S3 Lifecycle rules on all buckets. Enable Intelligent-Tiering for objects with unknown or variable access patterns. Configure expiration rules for obsolete data. Use Glacier Deep Archive for long-retention compliance data. Deduplicate where feasible.
- Verification:
  `aws s3api get-bucket-lifecycle-configuration --bucket <name>` confirms rules exist on all buckets; S3 Intelligent-Tiering enabled where appropriate; no buckets with undefined lifecycle policies.
- Source: Design principle #5 (naming S3 Lifecycle) + SUS04 Data Management area [triangulated]

**SUS-AD-E — Prefer Managed and Serverless Over Self-Managed Always-On EC2 (SUS05)**
- Pillar Alignment: SUS05 Hardware and Services; Design Principle "Use managed services"
- Why: Design principle "Use managed services" states that "sharing services across a broad customer base maximizes resource utilization." Multi-tenant managed infrastructure achieves aggregate efficiency that self-managed single-tenant cannot.
- AWS Services: AWS Fargate (named in design principle), AWS Lambda, Amazon Aurora Serverless, Amazon SQS, Amazon RDS managed databases instead of self-managed EC2; Graviton instances (latest generation) where EC2 is required.
- Architecture Decision:
  Prefer managed and serverless services as the default. Require justification for any self-managed EC2 alternative. When EC2 is required, select the latest-generation Graviton instance family and validate with Compute Optimizer.
- Verification:
  Inventory of managed vs self-managed services; Compute Optimizer instance-generation audit shows no outdated generations without justification.
- Source: Design principle #5 (naming Fargate) + SUS05 Hardware and Services area [triangulated]

**SUS-AD-F — Measure Impact and Set Sustainability KPIs (SUS06-BP01)**
- Pillar Alignment: SUS06 Process and Culture; Design Principles "Understand your impact" and "Establish sustainability goals"
- Why: "Understand your impact" requires measuring impact and establishing KPIs. "Establish sustainability goals" requires per-workload long-term goals. SUS06-BP01 (new in Nov 2024) specifically mandates communicating and cascading sustainability goals — central IT drives org-wide reduction.
- AWS Services: AWS Customer Carbon Footprint Tool, CloudWatch custom metrics for proxy KPIs (e.g., resources per transaction), Cost and Usage Report as utilization proxy.
- Architecture Decision:
  Establish per-unit-of-work impact KPIs (e.g., compute seconds per transaction, GB transferred per user request). Track via CloudWatch custom metrics. Schedule quarterly Customer Carbon Footprint Tool review. Document and cascade sustainability goals to team level.
- Verification:
  KPI dashboards exist in CloudWatch; sustainability goals documented in architecture decision records; Carbon Footprint Tool trend data reviewed on a recurring schedule.
- Source: SUS06-BP01 + AWS architecture blog update announcement (2024-11-06) https://aws.amazon.com/blogs/architecture/announcing-updates-to-the-aws-well-architected-framework-guidance-3/ [triangulated]

---

### ⚠️ Architectural Decisions

**Decision A — Region Placement: Carbon vs Latency vs Data Residency**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Lowest-carbon Region | Region + Customer Carbon Footprint Tool | Carbon footprint | Latency, may conflict with data-residency requirements | Sustainability goal outweighs latency and residency allows it |
  | Region nearest users | Local Region + CloudFront | Latency, downstream device energy | May be higher-carbon grid | User experience is the primary driver |

- Cost Profile: Region pricing varies; lowest-carbon may not be lowest-cost — evaluate together.
- Lock-in Assessment: Low — workloads can be moved across Regions with effort; no managed-service lock-in specific to sustainability.
- Architect Instruction: "Ask what the data-residency and latency SLA requirements are before selecting a Region based on carbon footprint alone — sustainability and compliance constraints must be resolved together."
- Source: SUS01-BP01 https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/region-selection.html

**Decision B — Compute Model for Sustainability**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Serverless / scale-to-zero | AWS Lambda, AWS Fargate | Utilization, zero idle baseline | Cold starts, runtime and duration limits | Spiky or event-driven workloads |
  | Right-sized managed instances with Auto Scaling | EC2 Graviton + Auto Scaling | Steady-state efficiency, runtime control | Some idle baseline at minimum capacity | Sustained high-utilization workloads |

- Cost Profile: Serverless is consumption-based (lower idle cost); EC2 Graviton with Savings Plans offers predictable cost for steady-state.
- Lock-in Assessment: Medium — Lambda runtimes and Fargate are AWS-specific; Graviton ARM64 is portable to other providers' ARM offerings with code compatibility validation.
- Architect Instruction: "Ask whether the workload demand profile is spiky or steady-state before choosing between serverless and managed instances — both can be sustainable but for different demand shapes."
- Source: SUS02 + design principle #5

**Decision C — Data Storage Footprint**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Multi-copy hot storage | S3 Standard, cross-Region replication | Availability, retrieval latency | More powered storage, higher footprint | High-availability critical data where retrieval speed is non-negotiable |
  | Tiered / cold single-Region | S3 Intelligent-Tiering / Glacier | Reduced storage footprint, cost | Retrieval latency from cold tiers | Infrequent access, sustainability and cost are priority |

- Cost Profile: Cold tiers are significantly cheaper; retrieval costs apply when accessing Glacier.
- Lock-in Assessment: Low — S3 APIs are widely emulated; Intelligent-Tiering is AWS-specific automation but data is portable.
- Architect Instruction: "Ask what the retrieval latency tolerance and access frequency are for each data class before assigning a storage tier — never default all data to S3 Standard."
- Source: SUS04 https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/data-management.html

**Decision D — SLA Level vs Sustainability (SUS02-BP02)**
- Options:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Very high SLA (redundant, over-provisioned) | Availability, fault tolerance | Extra resources and energy from redundant capacity | Critical-tier workloads where outage cost exceeds sustainability cost |
  | SLA aligned to actual business need | Reduced footprint, resource efficiency | Lower headroom and redundancy | Non-critical tiers where slightly reduced availability is acceptable |

- Cost Profile: Over-provisioned high-SLA significantly increases cost and footprint; right-sized SLA reduces both.
- Lock-in Assessment: N/A — SLA level is an architecture decision, not a provider coupling.
- Architect Instruction: "Ask what the actual business impact of a 15-minute outage would be before defaulting to 99.99% SLA — non-critical tiers should be designed to their real SLA, not to the most demanding tier's SLA."
- Source: SUS02-BP02 https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/align-utilization-with-user-load.html

---

### 🚫 Anti-Patterns

**SUS-ND-1 — Static Over-Provisioning "Just in Case"**
- Risk Level: HIGH
- Why: Violates design principle "Maximize utilization." A fixed fleet of large EC2 instances running at 15% utilization 24/7 consumes baseline power without productive output — "Two hosts running at 30% utilization are less efficient than one host running at 60% due to baseline power consumption per host."
- Instead: EC2 Auto Scaling with target-tracking policies, AWS Lambda, or AWS Fargate tracking actual demand.
- Detection: CloudWatch showing sustained low CPU/memory utilization; AWS Compute Optimizer flagging "over-provisioned" instances.
- Impact: Wasted energy and resources; higher cost and unnecessary carbon footprint.
- Source: Design principle "Maximize utilization" https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html

**SUS-ND-2 — Leaving Idle and Orphaned Resources Running**
- Risk Level: HIGH
- Why: Violates design principles "Maximize utilization" and "Alignment to demand" (SUS02). Idle resources consume baseline energy continuously with zero productive output.
- Instead: Automated cleanup scripts; AWS Trusted Advisor idle-resource checks; Compute Optimizer recommendations acted upon; unattached EBS volumes deleted.
- Detection: AWS Trusted Advisor / Compute Optimizer idle findings; `aws ec2 describe-volumes --filters Name=status,Values=available` for unattached EBS volumes.
- Impact: Continuous baseline energy waste across accounts; compounding cost and carbon over time.
- Source: SUS02-BP03 https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/align-utilization-with-user-load.html

**SUS-ND-3 — All Data Kept Hot Forever**
- Risk Level: MEDIUM
- Why: Violates SUS04 Data Management. Keeping all data in S3 Standard with no lifecycle policy maximizes powered-storage footprint unnecessarily.
- Instead: S3 Lifecycle rules transitioning to Intelligent-Tiering or Glacier; expiration rules for obsolete data; deduplication where applicable.
- Detection: `aws s3api get-bucket-lifecycle-configuration --bucket <name>` returns no rules; S3 console shows no lifecycle policies on buckets.
- Impact: Excess storage footprint; ongoing unnecessary cost.
- Source: SUS04 https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/data-management.html

**SUS-ND-4 — Ignoring Region Carbon in Placement Decisions**
- Risk Level: MEDIUM
- Why: Violates SUS01 and design principle "Understand your impact." Region grid carbon intensity is a measurable and manageable input to environmental footprint — ignoring it is equivalent to ignoring a known impact source.
- Instead: Use AWS Customer Carbon Footprint Tool in Region selection; document carbon rationale alongside latency and residency rationale.
- Detection: No documented Region selection rationale; Customer Carbon Footprint Tool never opened; Region chosen purely on latency defaults.
- Impact: Higher-than-necessary emissions; no baseline to improve from.
- Source: SUS01-BP01 https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/region-selection.html

**SUS-ND-5 — Self-Managed Always-On Infrastructure Instead of Managed or Serverless**
- Risk Level: MEDIUM
- Why: Violates design principle "Use managed services." A self-hosted queue or database on 24/7 EC2 at low utilization achieves lower aggregate efficiency than the equivalent managed service shared across AWS customers.
- Instead: Amazon SQS instead of self-managed RabbitMQ; Amazon Aurora Serverless instead of self-managed MySQL on EC2; AWS Fargate instead of self-managed container hosts.
- Detection: Workload inventory shows self-managed services with sustained low CPU utilization on dedicated EC2.
- Impact: Lower aggregate hardware efficiency; more infrastructure required for equivalent throughput.
- Source: Design principle "Use managed services" + SUS05 https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/hardware-and-services.html

**SUS-ND-6 — No Sustainability KPIs and No Measurement**
- Risk Level: MEDIUM
- Why: Violates design principles "Understand your impact" and "Establish sustainability goals," and SUS06-BP01 (new Nov 2024). Without measurement there is no accountability and regressions go undetected.
- Instead: Per-unit CloudWatch KPIs (e.g., compute seconds per transaction); cascaded sustainability goals per team; quarterly Customer Carbon Footprint Tool review scheduled.
- Detection: No CloudWatch dashboards tracking sustainability proxy metrics; no documented sustainability goals; Carbon Footprint Tool reports never generated.
- Impact: No visibility into environmental impact; regressions in workload efficiency go undetected indefinitely.
- Source: SUS06-BP01 + design principles "Understand your impact" / "Establish sustainability goals" https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/process-and-culture.html

**SUS-ND-7 — Forcing Customer Device Upgrades or Requiring Heavy Clients Unnecessarily**
- Risk Level: LOW-MEDIUM
- Why: Violates design principle "Reduce the downstream impact of your cloud workloads." Unnecessary client-side compute requirements and forced device upgrades generate downstream e-waste and user-side energy consumption.
- Instead: Optimize client application payloads and compute requirements; test with device farms; design for backward-compatible clients that run on older hardware.
- Detection: No downstream-impact testing plan in place; application requires the latest device generation without documented necessity.
- Impact: Downstream e-waste and energy consumption for end users; reputational risk.
- Source: Design principle "Reduce the downstream impact of your cloud workloads" https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html

---

## Cloud-Native Design Patterns

**Dynamic Demand Alignment with Auto Scaling and Serverless**
- Category: Scalability
- Problem: Always-on fixed-capacity infrastructure wastes energy at low utilization periods and fails to eliminate idle baseline.
- Solution on AWS: EC2 Auto Scaling with target-tracking policies for steady-state workloads; AWS Lambda or AWS Fargate for event-driven or spiky workloads (scale-to-zero during idle). CloudWatch alarms drive scaling decisions. Karpenter on EKS for container workloads requiring node-level auto-provisioning.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Energy efficiency | Eliminates idle baseline; resources match demand curve | Cold-start latency on Lambda/Fargate scale-up events |
  | Carbon footprint | Reduced emissions proportional to demand reduction | Requires investment in monitoring and policy tuning |
  | Operational complexity | Managed by AWS scaling services | Scaling configuration requires testing under realistic load |

- Source: SUS02-BP01 https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/align-utilization-with-user-load.html

**Tiered Storage Lifecycle Automation**
- Category: Data
- Problem: All data stored in hot storage regardless of access frequency causes an inflated powered-storage footprint over time.
- Solution on AWS: S3 Lifecycle rules configured per bucket to transition objects to S3 Intelligent-Tiering after initial period, then to S3 Glacier Flexible Retrieval or Glacier Deep Archive based on access patterns. Amazon Data Lifecycle Manager for EBS snapshot retention. RDS automated snapshots with defined retention windows.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Storage footprint | Significant reduction in powered-storage volume | Retrieval latency from cold tiers when data is needed |
  | Cost | Lower ongoing storage cost | Glacier retrieval charges apply; Intelligent-Tiering monitoring charge per object |
  | Automation | Fully automated once lifecycle rules are configured | Initial classification of data access patterns requires analysis |

- Source: SUS04 + design principle #5 https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/data-management.html

**Per-Unit KPI Instrumentation for Sustainability Accountability**
- Category: Resilience
- Problem: Without per-unit metrics, sustainability regressions introduced by new features or traffic changes are invisible.
- Solution on AWS: CloudWatch custom metrics publishing proxy KPIs (e.g., vCPU-seconds per API request, GB transferred per active user). CloudWatch dashboards surfacing trends. Customer Carbon Footprint Tool for account-level carbon trend. AWS Cost and Usage Report as utilization proxy.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Accountability | Regressions detected; goals measurable; teams responsible | Instrumentation effort to publish custom CloudWatch metrics |
  | Attribution accuracy | Per-unit metrics isolate efficiency changes from volume changes | Proxy metrics (compute time, bandwidth) are imperfect carbon proxies |
  | Governance | Goals cascaded per SUS06-BP01 drive org-wide improvement | Requires process to review and act on metrics (not just collect) |

- Source: SUS06-BP01 + design principles "Understand your impact" / "Establish sustainability goals"

---

## Security Architecture

**Multi-Account Sustainability Governance**
- AWS Services: AWS Organizations Service Control Policies (SCPs), AWS Config rules for lifecycle policies and instance type compliance, AWS Security Hub for aggregated findings, CloudWatch cross-account observability.
- Architecture: In a multi-account production environment, deploy AWS Config managed rules at the Organizations level to detect non-compliant resources (e.g., buckets without lifecycle policies, outdated instance generations). Aggregate findings in Security Hub. Use SCPs to prevent use of deprecated instance families. Carbon Footprint Tool reports at the management account level for full-footprint visibility.
- Compliance Alignment: AWS Well-Architected Sustainability Pillar SUS02, SUS04, SUS05 best practices; not legal compliance advice.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html

---

## Operational Patterns

**Sustainability Measurement and Reporting**
- RTO/RPO (if applicable): N/A
- AWS Services: AWS Customer Carbon Footprint Tool, AWS Cost and Usage Report (as utilization proxy), Amazon CloudWatch (custom per-unit metrics and dashboards)
- Cost Profile: Near zero — reporting tools are included in AWS account access; investment is in metric instrumentation engineering time.
- Automation: CloudWatch custom metrics published per transaction or per user request; scheduled monthly review of Customer Carbon Footprint Tool reports; CloudWatch alarms on KPI threshold breaches; quarterly goal review process.
- Source: SUS06-BP01 https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/process-and-culture.html

**Data Lifecycle Automation**
- RTO/RPO (if applicable): N/A
- AWS Services: Amazon S3 Lifecycle policies, S3 Intelligent-Tiering, Amazon Data Lifecycle Manager (EBS snapshots), RDS automated snapshot retention configuration.
- Cost Profile: Low — lifecycle transitions reduce storage cost while reducing environmental footprint. S3 Intelligent-Tiering monitoring charge applies per object; no retrieval charge for monitoring-triggered transitions.
- Automation: S3 Lifecycle rules are fully automated once configured; Intelligent-Tiering auto-moves objects based on access patterns with no manual intervention; EBS snapshot cleanup via Data Lifecycle Manager policies.
- Source: SUS04 https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/data-management.html

---

## Reference Architectures

**Production Multi-Account Workload — Sustainability-Optimized**
- Context: Multi-account production workload targeting measurable reduction in per-unit environmental impact.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Compute | AWS Lambda / AWS Fargate / EC2 Graviton with Auto Scaling | Scale-to-zero or elastic capacity; latest-generation hardware |
  | Storage | S3 + Lifecycle rules + Intelligent-Tiering + Glacier | Tiered data footprint reduction |
  | Delivery | Amazon CloudFront | Edge caching reduces origin compute and downstream data volume |
  | Database | Amazon Aurora Serverless / Amazon RDS managed | Managed multi-tenant infra; avoid self-managed EC2 databases |
  | Monitoring | CloudWatch custom KPIs + Customer Carbon Footprint Tool | Per-unit impact tracking and carbon trend reporting |
  | Governance | AWS Config rules + SCPs + Compute Optimizer | Detect non-compliance; prevent outdated instance families |

- Key Decisions: Region selection (carbon vs latency/residency); Graviton ARM64 compatibility for existing workloads; which data tiers qualify for cold storage; serverless vs Auto Scaling for each service boundary.
- Scaling Path: Start with right-sizing existing fleet via Compute Optimizer; enable Auto Scaling; migrate self-managed services to managed equivalents; add S3 Lifecycle rules; instrument CloudWatch KPIs; schedule quarterly Carbon Footprint Tool review.
- Source: SUS01–SUS06 https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/

---

## Provider Differentiators

**AWS Customer Carbon Footprint Tool**: AWS provides an account- and organization-level carbon footprint report integrated into the billing console. This enables architects to measure and trend environmental impact directly against AWS usage without third-party tooling. Comparable native tools are less mature or less integrated on other major providers as of the research date.

**Graviton (ARM-based) instances**: AWS Graviton3 and Graviton4 instances offer materially better performance-per-watt than comparable x86 instances. Compute Optimizer can recommend Graviton migration automatically, providing a clear, measurable path to hardware efficiency improvement without application-level changes in most cases (for ARM64-compatible runtimes).

**Managed service breadth**: AWS's managed service portfolio (Aurora Serverless, Fargate, SQS, DynamoDB, etc.) is broad enough that most common self-managed EC2 workload patterns have a fully managed equivalent, enabling the "Use managed services" design principle to be applied comprehensively.

---

## Scenario Coverage

**Standard Case**: Production workload seeking to reduce environmental footprint
- Approach: Audit compute fleet with AWS Compute Optimizer to identify over-provisioned and outdated-generation instances; right-size to Graviton instances; enable EC2 Auto Scaling with target-tracking policies; apply S3 Intelligent-Tiering on all data buckets and add Lifecycle rules for transition to Glacier; establish per-transaction CloudWatch custom KPI metric; schedule quarterly Customer Carbon Footprint Tool review and document sustainability goals per SUS06-BP01.
- Key Decisions: Which Region achieves the best carbon vs latency vs residency balance (SUS01-BP01); whether existing code is ARM64/Graviton compatible; which storage tiers qualify for cold storage based on access-frequency analysis; whether spiky services should migrate from EC2 Auto Scaling to Lambda/Fargate.

**Edge Case**: Multi-Region globally distributed workload where Region selection conflicts between latency and carbon
- Approach: Deploy Amazon CloudFront for static and cacheable content — edge delivery reduces downstream data volume and origin compute load globally. Place dynamic workloads in nearest-user Regions to meet latency SLA. Apply S3 Lifecycle policies aggressively on all Regions. Accept the carbon trade-off for latency-sensitive workloads and document the decision explicitly in the architecture decision record with Customer Carbon Footprint Tool data as evidence. Revisit annually as AWS grid carbon intensity improves.

**Anti-Pattern Case**: Architecture team proposes a fixed large instance fleet for predictable pricing
- Clarification: Ask whether the workload is truly steady-state with flat demand 24/7 before accepting the proposal. If cost predictability is the goal, AWS Savings Plans or Reserved Instances address cost predictability without requiring static sizing — the two concerns are independent. Propose a Compute Optimizer assessment first to establish the right-sized baseline. If after assessment the load is genuinely flat and sustained, right-size to the appropriate Graviton instance type before committing. Document why Auto Scaling was evaluated and rejected so the decision is auditable.
