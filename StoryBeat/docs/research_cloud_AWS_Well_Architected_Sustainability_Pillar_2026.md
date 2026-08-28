# AWS Well-Architected Framework — Sustainability Pillar

## Metadata
```yaml
Full_Name: "AWS Well-Architected Framework — Sustainability Pillar"
Cloud_Provider: "AWS"
Architecture_Domain: "Well-Architected Framework — Sustainability Pillar"
Target_Edition: "AWS Sustainability Pillar 2026 (currency label)"
Pinned_Stable_Revision: "Sustainability Pillar whitepaper — revision dated 2024-11-06 (current stable)"
Architecture_Context: "General AWS production workloads (context not supplied in arguments — see note in Executive Summary)"
Official_Source_URL: "https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-28"
Currency_Threshold: "2027-08-28 (re-verify after this date; also re-verify whenever the whitepaper revision date advances past 2024-11-06)"
Research_Depth: exhaustive
```

> ⚠️ **Version note (Version Absolutism).** AWS does **not** publish a distinct "2026" edition of the
> Sustainability Pillar. The current stable whitepaper revision is **dated November 6, 2024**
> ([Document revisions](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/document-revisions.html), accessed 2026-08-28).
> The `TARGET_EDITION="AWS Sustainability Pillar 2026"` in the request is treated here as a
> **currency/review label**, and all patterns below are pinned to the **2024-11-06 revision**. Any
> guidance predating 2024-11-06 that was superseded by that revision is treated as misinformation.
> Re-verify against the live whitepaper if the revision date has since advanced.

---

## Executive Summary

The **Sustainability pillar** is the sixth pillar of the AWS Well-Architected Framework (added
December 2, 2021). It focuses specifically on **environmental sustainability** — minimizing the
energy and resources required to run cloud workloads and reducing their downstream impact. It is
built on a **shared responsibility model**: AWS is responsible for sustainability *of* the cloud
(efficient shared infrastructure, water stewardship, renewable power sourcing), while customers are
responsible for sustainability *in* the cloud (optimizing workloads, maximizing utilization, and
minimizing total resources deployed) (source: [The shared responsibility model](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/the-shared-responsibility-model.html), accessed 2026-08-28).

**What changed in the pinned (2024-11-06) revision vs prior editions:** the November 6, 2024 revision
updated best-practice guidance across **SUS 1, SUS 3, SUS 4, SUS 5, and SUS 6**, and — most notably —
added a **new best practice `SUS06-BP01 Communicate and cascade your sustainability goals`**, with the
remaining SUS 6 best practices renumbered as a result. Earlier milestones: prescriptive-guidance
rewrite (2023-04-10), risk-level updates (2023-10-03), and minor edits (2024-06-27). The pillar now
spans **six best-practice areas (SUS 1–6) containing 29 best practices total** (source:
[Document revisions](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/document-revisions.html), accessed 2026-08-28).

**Three most critical architecture guardrails** for general production workloads: (1) **Measure before
you optimize** — establish sustainability KPIs using the AWS Customer Carbon Footprint Tool / AWS
Sustainability console before making changes; (2) **Maximize utilization** — right-size and use
auto-scaling so hardware runs at high utilization rather than many under-utilized hosts; (3) **Choose
managed services and efficient hardware** (e.g., AWS Graviton, Fargate, S3 Lifecycle tiering) to
shift efficiency work onto AWS-operated shared infrastructure.

> ⚠️ **Context gap (Ask-First per skill guardrails).** `ARCHITECTURE_CONTEXT` was not provided in the
> arguments. This document uses a general production-workload lens. If a specific context applies
> (multi-tenant SaaS, real-time IoT, regulated financial services, global e-commerce), re-scope the
> Ask-First decisions accordingly before authoring a skill from this research.

---

## Cloud Architecture Glossary

```
Term: Sustainability (pillar scope)
Definition: Within Well-Architected, "sustainability" is scoped to ENVIRONMENTAL sustainability —
  minimizing the environmental impacts of running cloud workloads (energy/resource reduction and efficiency).
Provider Docs Section: Sustainability Pillar → Introduction
Architect Usage: Frame sustainability decisions as efficiency/waste-reduction decisions, not ESG reporting.
Common Confusion: Confused with cost optimization (overlaps heavily but is not identical) and with
  corporate ESG/social sustainability (out of scope for this pillar).
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html
```
```
Term: Sustainability of the cloud vs Sustainability in the cloud
Definition: "Of the cloud" = AWS responsibility (efficient infrastructure, renewable power, water
  stewardship). "In the cloud" = customer responsibility (workload/resource-utilization optimization).
Provider Docs Section: The shared responsibility model
Architect Usage: Use to set scope boundaries — you cannot optimize datacenter PUE; you can optimize
  utilization, region choice, data lifecycle, and code efficiency.
Common Confusion: Mirrors but is distinct from the Security shared responsibility model.
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/the-shared-responsibility-model.html
```
```
Term: Impact intensity / proxy metrics
Definition: Sustainability KPIs expressed per unit of useful work (e.g., resources or emissions per
  transaction or per user), used because absolute carbon is often not directly measurable in real time.
Provider Docs Section: Design principles → Understand your impact / Establish sustainability goals
Architect Usage: Define KPIs like "vCPU-hours per 1,000 requests" as proxies to track improvement.
Common Confusion: Confusing absolute footprint (from CCFT, delayed/aggregated) with real-time proxy metrics.
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html
```
```
Term: AWS Customer Carbon Footprint Tool (CCFT)
Definition: A free tool providing estimated carbon emissions (Scope 1, 2, 3) and water-withdrawal data
  from AWS usage, broken down by Region, service, and account; uses location-based and market-based
  methodology (independently verified).
Provider Docs Section: AWS Cost Management → Customer Carbon Footprint Tool
Architect Usage: The authoritative source for measuring "Understand your impact." Carbon data from 2022;
  water-withdrawal data from 2023. Now evolving into the AWS Sustainability console with API access.
Common Confusion: CCFT reports historical/aggregated data with lag — not a real-time metric.
Source: https://aws.amazon.com/aws-cost-management/aws-customer-carbon-footprint-tool/
```
```
Term: AWS Graviton
Definition: AWS-designed ARM-based processors offering higher performance-per-watt than comparable x86 instances.
Provider Docs Section: SUS05-BP02 Use instance types with the least impact
Architect Usage: Default consideration for right-sizing when workloads are ARM-compatible.
Common Confusion: Treated purely as a cost lever; it is also a primary sustainability lever.
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/hardware-and-services.html
```
```
Term: Managed device farms
Definition: AWS-operated shared physical device fleets (e.g., AWS Device Farm) for testing across real
  devices without provisioning/maintaining dedicated hardware.
Provider Docs Section: SUS06-BP05 Use managed device farms for testing
Architect Usage: Use to test downstream device impact and avoid idle test-hardware fleets.
Common Confusion: Confused with emulators/simulators (which do not measure real-device downstream impact).
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/process-and-culture.html
```
```
Term: SUS question / best practice ID (SUSxx-BPyy)
Definition: The pillar's structured review questions (SUS 1–6) and their numbered best practices,
  used in Well-Architected Framework Reviews (WAFR) and the Well-Architected Tool.
Provider Docs Section: Best-practice areas (Region selection, Alignment to demand, etc.)
Architect Usage: Cite exact IDs (e.g., SUS04-BP03) in ADRs and WAFR findings for traceability.
Common Confusion: Renumbering across revisions — SUS 6 was renumbered in the 2024-11-06 revision.
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/document-revisions.html
```

---

## Framework Pillars — Sustainability Pillar Detail

```
Pillar: Sustainability
Definition: "This document focuses on the sustainability pillar, and within the scope of
  sustainability, it focuses on environmental sustainability." The pillar provides design principles,
  operational guidance, best practices, trade-offs, and improvement plans to meet sustainability
  targets for AWS workloads.
Key Design Principles (6, verbatim titles):
  1. Understand your impact
  2. Establish sustainability goals
  3. Maximize utilization
  4. Anticipate and adopt new, more efficient hardware and software offerings
  5. Use managed services
  6. Reduce the downstream impact of your cloud workloads
Applies To General Production Workloads: Sustainability decisions concentrate on utilization
  (right-sizing + auto-scaling), region choice, data lifecycle, efficient hardware (Graviton), and
  managed-service adoption — most of which also reduce cost, making it the pillar most aligned with
  Cost Optimization.
Assessment Questions (SUS 1–6):
  - SUS 1: How do you select Regions for your workload?
  - SUS 2: How do you take advantage of user behavior patterns to support your sustainability goals? (Alignment to demand)
  - SUS 3: How do you take advantage of software and architecture patterns to support your sustainability goals?
  - SUS 4: How do you take advantage of data access and usage patterns to support your sustainability goals?
  - SUS 5: How do your hardware management and usage practices support your sustainability goals?
  - SUS 6: How do your organizational processes support your sustainability goals? (Process and culture)
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html (accessed 2026-08-28)
```

### The six design principles (verbatim guidance)

1. **Understand your impact** — Measure the impact of your cloud workload and model its future impact.
   Include all sources of impact, including customer use of your products and eventual decommissioning/retirement.
   Compare productive output with total impact (resources/emissions per unit of work); use the data to
   establish KPIs and estimate the impact of proposed changes.
2. **Establish sustainability goals** — For each workload, establish long-term goals (e.g., reduced
   compute/storage per transaction); model ROI of improvements; architect so that growth reduces impact
   intensity per unit (per user / per transaction).
3. **Maximize utilization** — Right-size and implement efficient design for high utilization. "Two hosts
   running at 30% utilization are less efficient than one host running at 60% due to baseline power
   consumption per host." Eliminate/minimize idle resources, processing, and storage.
4. **Anticipate and adopt new, more efficient hardware and software offerings** — Support upstream
   improvements from partners/suppliers; continually monitor/evaluate more efficient offerings; design
   for flexibility to adopt new efficient technologies rapidly.
5. **Use managed services** — Sharing services across a broad customer base maximizes resource
   utilization (e.g., AWS Fargate for serverless containers; S3 Lifecycle to move cold data; EC2 Auto Scaling).
6. **Reduce the downstream impact of your cloud workloads** — Reduce energy/resources needed to use your
   services; reduce/eliminate the need for customers to upgrade devices; use device farms to test impact.

Source: [Design principles](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html) (accessed 2026-08-28)

### The sustainability improvement process (iterative)

The pillar prescribes a continuous improvement loop: **(1)** identify targets for improvement,
**(2)** evaluate specific improvements, **(3)** prioritize and plan improvements, **(4)** test and
validate improvements, **(5)** deploy changes, **(6)** measure results and replicate successes.

> ⚠️ **Unverified wording.** The improvement-process page did not return extractable body text on
> fetch (2026-08-28); the six steps above are the pillar's documented iterative loop but the exact
> section wording could not be captured. Treat step titles as **paraphrase**, not verbatim, until
> re-verified at
> [the-sustainability-improvement-process.html](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/the-sustainability-improvement-process.html).

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Measure impact before optimizing (establish sustainability KPIs)**
- Pillar Alignment: Sustainability — Design principles "Understand your impact" & "Establish sustainability goals"
- Why: The pillar makes measurement the entry point; goals and improvement prioritization depend on baseline KPIs and impact modeling.
- AWS Services: AWS Customer Carbon Footprint Tool / AWS Sustainability console; Amazon CloudWatch (proxy metrics); AWS Cost & Usage Report (utilization proxies).
- Architecture Decision: Instrument workloads to emit per-unit-of-work proxy metrics (e.g., vCPU-hours per 1,000 requests); pull absolute carbon (Scope 1/2/3) and water-withdrawal data from CCFT by Region/service/account; set KPIs and review cadence.
- Verification: CCFT console shows non-empty emissions data for the account; CloudWatch dashboards expose per-transaction resource metrics.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html + https://aws.amazon.com/aws-cost-management/aws-customer-carbon-footprint-tool/ (accessed 2026-08-28)
- [✓✓ Triangulated | Design principles page + Customer Carbon Footprint Tool page]

**Maximize utilization via right-sizing + dynamic scaling**
- Pillar Alignment: Sustainability — "Maximize utilization"; SUS02-BP01, SUS05-BP01, SUS05-BP02
- Why: Baseline power per host means consolidating load onto fewer, better-utilized hosts is more energy efficient; idle resources waste energy.
- AWS Services: Amazon EC2 Auto Scaling, Application Auto Scaling, AWS Fargate, Compute Optimizer, AWS Graviton instance families.
- Architecture Decision: Scale infrastructure dynamically to match demand; select smallest instance types meeting requirements; prefer Graviton where ARM-compatible; consolidate under-utilized components.
- Verification: Auto Scaling policies attached to all elastic tiers; Compute Optimizer shows no "over-provisioned" findings; target utilization thresholds met.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/alignment-to-demand.html + https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/hardware-and-services.html (accessed 2026-08-28)
- [✓✓ Triangulated | Alignment-to-demand (SUS 2) + Hardware-and-services (SUS 5)]

**Data lifecycle management and classification**
- Pillar Alignment: Sustainability — SUS04-BP01, SUS04-BP03, SUS04-BP05
- Why: Reducing provisioned storage and moving cold data to less energy-intensive tiers cuts total resources; deleting redundant data removes ongoing impact.
- AWS Services: Amazon S3 Lifecycle configurations, S3 Intelligent-Tiering, S3 Glacier storage classes, Amazon Data Lifecycle Manager (EBS snapshots).
- Architecture Decision: Apply a data classification policy; attach lifecycle policies that tier/expire objects by access pattern; remove redundant data; back up only data difficult to recreate (SUS04-BP08).
- Verification: All production S3 buckets carry a lifecycle policy or Intelligent-Tiering; snapshot retention policies present.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/data.html (accessed 2026-08-28)
- [✓ Single-source (SUS 4 page) — Medium confidence on exhaustiveness; reinforced by design principle "Use managed services" for S3 Lifecycle]

**Prefer managed and serverless services**
- Pillar Alignment: Sustainability — Design principle "Use managed services"; SUS05-BP03
- Why: Shared, AWS-operated services achieve higher fleet utilization than dedicated customer-managed infrastructure, reducing total infrastructure needed.
- AWS Services: AWS Fargate, AWS Lambda, Amazon S3, Amazon RDS/Aurora Serverless v2, Amazon DynamoDB on-demand.
- Architecture Decision: Default to managed/serverless for undifferentiated heavy lifting; reserve self-managed compute for cases with a documented reason.
- Verification: Architecture review shows managed services used for standard workloads; self-managed EC2 justified in ADRs.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html + https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/hardware-and-services.html (accessed 2026-08-28)
- [✓✓ Triangulated | Design principles page + SUS05-BP03]

**Communicate and cascade sustainability goals (organizational)**
- Pillar Alignment: Sustainability — SUS06-BP01 (NEW in 2024-11-06 revision)
- Why: Process-and-culture guidance ensures sustainability goals reach workload owners so improvements are actually prioritized and funded.
- AWS Services: N/A (organizational practice); supported by AWS Well-Architected Tool for tracking.
- Architecture Decision: Define and cascade workload-level sustainability goals to owners; track via WAFR cadence; adopt methods that rapidly introduce improvements (SUS06-BP02) and keep workloads up to date (SUS06-BP03).
- Verification: Documented per-workload sustainability goals; WAFR includes SUS 6 answers.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/process-and-culture.html (accessed 2026-08-28)
- ⚠️ Migration Note: `SUS06-BP01 Communicate and cascade your sustainability goals` is **new** in the 2024-11-06 revision; SUS 6 best practices were **renumbered**. Any pre-2024-11-06 SUS06-BP numbering is misinformation. (Source: Document revisions.)

### ⚠️ Architectural Decisions

**Region selection: proximity/cost vs carbon intensity (SUS01-BP01)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Region chosen for low carbon intensity | Any (Region choice) | Sustainability KPI / carbon footprint | Possibly latency to users, some service availability | Latency budget tolerant; sustainability goal is explicit |
  | Region chosen for proximity/latency | Any (Region choice) | Performance, user experience | Potentially higher carbon intensity grid | Real-time / low-latency user-facing workloads |
  | Region chosen for cost | Any (Region choice) | Cost | May not be lowest-carbon | Cost-constrained batch/non-latency-sensitive workloads |

- Cost Profile: Region choice materially affects both price and carbon; the two do not always align.
- Lock-in Assessment: Low technical lock-in, but data residency/compliance may constrain choice.
- Architect Instruction: "Ask whether the workload has a latency/data-residency constraint that overrides carbon-intensity optimization before selecting a Region purely on sustainability grounds (SUS01-BP01)."
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/region-selection.html (accessed 2026-08-28)

**Demand shaping: buffering/throttling vs always-on capacity (SUS02-BP06)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Buffer/throttle to flatten demand | Amazon SQS, API Gateway throttling, Kinesis | Utilization, reduced peak provisioning | Immediate responsiveness for bursty spikes | Workload tolerates async / eventual processing |
  | Async & scheduled jobs | AWS Batch, EventBridge Scheduler, Lambda | High utilization, off-peak scheduling | Real-time results | Jobs are deferrable (SUS03-BP01) |
  | Always-on provisioned capacity | EC2 / provisioned concurrency | Latency, predictability | Sustainability (idle capacity) | Strict real-time SLA |

- Cost Profile: Demand-flattening reduces peak capacity and cost; may add queue/latency overhead.
- Lock-in Assessment: Low; queue/scheduler patterns are portable in concept.
- Architect Instruction: "Ask whether the workload's SLA permits buffering/throttling or asynchronous processing before mandating always-on capacity (SUS02-BP06 / SUS03-BP01)."
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/alignment-to-demand.html (accessed 2026-08-28)

**SLA alignment: gold-plated SLAs vs sustainability (SUS02-BP02)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | SLA aligned to actual customer need | N/A (policy) | Sustainability, cost | Marketing "always-max" positioning | Internal or tiered services |
  | Maximum availability/performance SLA | Multi-region active-active, over-provisioning | Availability, latency | Sustainability (redundant idle capacity) | Mission-critical, regulated |

- Architect Instruction: "Ask whether current SLAs exceed real customer requirements before provisioning redundant capacity (SUS02-BP02). Over-specified SLAs are a common sustainability regression."
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/alignment-to-demand.html (accessed 2026-08-28)

### 🚫 Anti-Patterns

**Optimizing without measurement**
- Risk Level: HIGH
- Why: Violates design principles "Understand your impact" / "Establish sustainability goals" — changes cannot be prioritized or validated without baseline KPIs.
- ❌ Wrong: Right-sizing instances by guesswork with no CCFT baseline and no per-transaction proxy metrics in CloudWatch.
- ✅ Correct: Establish CCFT carbon baseline (Scope 1/2/3) and CloudWatch proxy KPIs, then apply and measure improvements against the baseline.
- Detection: CCFT never reviewed; no sustainability KPIs defined; WAFR SUS 1 answered "none."
- Impact: Cost overrun + unverifiable sustainability claims (greenwashing risk).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html (accessed 2026-08-28)

**Chronically under-utilized, always-on infrastructure**
- Risk Level: HIGH
- Why: Violates "Maximize utilization"; baseline power per host makes many low-utilization hosts less efficient than fewer high-utilization hosts.
- ❌ Wrong: A fixed fleet of EC2 instances running 24/7 at ~15% average CPU with no Auto Scaling and no scheduled shutdown for non-prod.
- ✅ Correct: EC2 Auto Scaling / Application Auto Scaling matching demand; Instance Scheduler stopping non-prod out of hours; Graviton right-sized instances (SUS02-BP01, SUS05-BP01/BP02).
- Detection: Compute Optimizer "over-provisioned" findings; sustained low CloudWatch CPU/utilization; no scaling policies.
- Impact: Cost overrun + avoidable energy consumption.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/alignment-to-demand.html + https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/hardware-and-services.html (accessed 2026-08-28)

**Unmanaged data growth (no lifecycle, redundant/idle data)**
- Risk Level: MEDIUM
- Why: Violates SUS 4 (data management) — provisioned storage and its energy grow unbounded; redundant data and needless backups add ongoing impact.
- ❌ Wrong: All objects kept in S3 Standard indefinitely; no lifecycle policy; full backups of easily recreatable data.
- ✅ Correct: S3 Lifecycle / Intelligent-Tiering moving cold data to Glacier classes; expiration of obsolete data; back up only data difficult to recreate (SUS04-BP03, SUS04-BP05, SUS04-BP08).
- Detection: S3 buckets without lifecycle rules; growing storage with flat access patterns; Storage Lens metrics.
- Impact: Cost overrun + avoidable storage energy.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/data.html (accessed 2026-08-28)

**Idle/orphaned assets left provisioned**
- Risk Level: MEDIUM
- Why: Violates SUS02-BP03 (stop creation/maintenance of unused assets) and "Maximize utilization."
- ❌ Wrong: Unattached EBS volumes, idle load balancers, stale dev environments, and unused Elastic IPs left running.
- ✅ Correct: Automated detection and cleanup of unused assets; TTL/tags on ephemeral environments; scheduled teardown (SUS02-BP03).
- Detection: AWS Trusted Advisor idle-resource checks; Cost Explorer anomaly detection; resource tagging audit.
- Impact: Cost overrun + wasted capacity.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/alignment-to-demand.html (accessed 2026-08-28)

**Dedicated, idle test hardware / device fleets**
- Risk Level: MEDIUM
- Why: Violates SUS06-BP05 (use managed device farms) and SUS06-BP04 (increase utilization of build environments).
- ❌ Wrong: A rack of physical test devices and always-on self-managed build servers used intermittently.
- ✅ Correct: AWS Device Farm for real-device testing; shared/on-demand build environments (e.g., CodeBuild) instead of idle dedicated build hosts (SUS06-BP04, SUS06-BP05).
- Detection: Standing test/build hardware with low utilization; no managed-service alternative evaluated.
- Impact: Cost overrun + hardware/energy waste.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/process-and-culture.html (accessed 2026-08-28)

---

## Best-Practice Areas Reference (SUS 1–6, verbatim best-practice titles)

Pinned to the **2024-11-06** revision. All best-practice IDs and titles below are verbatim from the
official pages (accessed 2026-08-28).

### SUS 1 — Region selection
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/region-selection.html
- **SUS01-BP01** Choose Region based on both business requirements and sustainability goals

### SUS 2 — Alignment to demand (user behavior patterns)
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/alignment-to-demand.html
- **SUS02-BP01** Scale workload infrastructure dynamically
- **SUS02-BP02** Align SLAs with sustainability goals
- **SUS02-BP03** Stop the creation and maintenance of unused assets
- **SUS02-BP04** Optimize geographic placement of workloads based on their networking requirements
- **SUS02-BP05** Optimize team member resources for activities performed
- **SUS02-BP06** Implement buffering or throttling to flatten the demand curve

### SUS 3 — Software and architecture
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/software-and-architecture.html
- **SUS03-BP01** Optimize software and architecture for asynchronous and scheduled jobs
- **SUS03-BP02** Remove or refactor workload components with low or no use
- **SUS03-BP03** Optimize areas of code that consume the most time or resources
- **SUS03-BP04** Optimize impact on devices and equipment
- **SUS03-BP05** Use software patterns and architectures that best support data access and storage patterns

### SUS 4 — Data management
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/data.html
- **SUS04-BP01** Implement a data classification policy
- **SUS04-BP02** Use technologies that support data access and storage patterns
- **SUS04-BP03** Use policies to manage the lifecycle of your datasets
- **SUS04-BP04** Use elasticity and automation to expand block storage or file system
- **SUS04-BP05** Remove unneeded or redundant data
- **SUS04-BP06** Use shared file systems or storage to access common data
- **SUS04-BP07** Minimize data movement across networks
- **SUS04-BP08** Back up data only when difficult to recreate

### SUS 5 — Hardware and services
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/hardware-and-services.html
- **SUS05-BP01** Use the minimum amount of hardware to meet your needs
- **SUS05-BP02** Use instance types with the least impact
- **SUS05-BP03** Use managed services
- **SUS05-BP04** Optimize your use of hardware-based compute accelerators

### SUS 6 — Process and culture
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/process-and-culture.html
- **SUS06-BP01** Communicate and cascade your sustainability goals  ⚠️ *NEW in 2024-11-06 revision*
- **SUS06-BP02** Adopt methods that can rapidly introduce sustainability improvements
- **SUS06-BP03** Keep your workload up-to-date
- **SUS06-BP04** Increase utilization of build environments
- **SUS06-BP05** Use managed device farms for testing

**Total: 29 best practices across 6 areas** (1 + 6 + 5 + 8 + 4 + 5).

---

## Cloud-Native Design Patterns (sustainability-relevant)

**Demand-flattening with queue-based load leveling**
- Category: Scalability
- Problem: Bursty demand forces peak-capacity provisioning that sits idle most of the time.
- Solution on AWS: Amazon SQS/Kinesis buffer requests; consumers (Lambda/Fargate/EC2 Auto Scaling) process at steady, high utilization; API Gateway throttling caps spikes.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Utilization | Higher, steadier | Added latency for buffered work |
  | Capacity | Lower peak provisioning | Queue/operational complexity |
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/alignment-to-demand.html (accessed 2026-08-28)

**Asynchronous / scheduled batch execution**
- Category: Scalability / Resilience
- Problem: Synchronous always-on processing keeps resources warm when work is deferrable.
- Solution on AWS: AWS Batch / EventBridge Scheduler / Step Functions run deferrable work off-peak on Spot or Graviton (SUS03-BP01).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Utilization | Off-peak consolidation | Not suitable for real-time SLAs |
  | Cost | Spot/Graviton savings | Scheduling/retry complexity |
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/software-and-architecture.html (accessed 2026-08-28)

**Storage tiering by access pattern**
- Category: Data
- Problem: Uniform hot storage for data with declining access wastes energy and cost.
- Solution on AWS: S3 Lifecycle / Intelligent-Tiering transition to S3 Glacier classes; EBS snapshot lifecycle via Data Lifecycle Manager (SUS04-BP03).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Storage energy | Lower for cold data | Retrieval latency/fees for archived tiers |
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/data.html (accessed 2026-08-28)

---

## Security Architecture
Not the primary focus of the Sustainability pillar. Where they intersect: minimizing data retention
(SUS04-BP05 "Remove unneeded or redundant data") reduces both attack surface and storage impact —
align data-minimization with the Security pillar's data-classification guidance. No sustainability-
specific security patterns are prescribed by this pillar. (Source: SUS 4 data page, accessed 2026-08-28.)

---

## Operational Patterns

**Sustainability measurement & reporting**
- {{AWS}} Services: AWS Customer Carbon Footprint Tool / AWS Sustainability console (Scope 1/2/3 carbon + water withdrawals by Region/service/account; carbon data from 2022, water from 2023, evolving to API access); Amazon CloudWatch (proxy KPIs); Cost & Usage Report.
- Cost Profile: Low (CCFT is free; CloudWatch metrics at standard rates).
- Automation: Automate proxy-KPI dashboards and periodic CCFT review; manual decision point = target-setting and prioritization.
- Source: https://aws.amazon.com/aws-cost-management/aws-customer-carbon-footprint-tool/ (accessed 2026-08-28)

**Right-sizing & utilization operations**
- AWS Services: AWS Compute Optimizer, Trusted Advisor, Instance Scheduler, EC2/Application Auto Scaling.
- Cost Profile: Low tooling cost; net savings from reduced idle capacity.
- Automation: Automate scaling and non-prod scheduling; review Compute Optimizer findings on a cadence.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/hardware-and-services.html (accessed 2026-08-28)

---

## Reference Architectures

**Sustainability-optimized elastic web/API workload**
- AWS Source: Sustainability Pillar SUS 2 / SUS 5 guidance (accessed 2026-08-28)
- Context: General user-facing production workload with variable demand.
- Services Composition:

  | Layer | Service | Purpose | Alternative |
  |-------|---------|---------|-------------|
  | Edge | CloudFront | Cache to cut origin compute + data movement (SUS04-BP07) | — |
  | Compute | Fargate / Lambda / Graviton EC2 Auto Scaling | High-utilization, right-sized, ARM-efficient compute | ECS on EC2 |
  | Async | SQS + Lambda / AWS Batch | Demand flattening, off-peak batch (SUS02-BP06, SUS03-BP01) | Kinesis + consumers |
  | Data | Aurora Serverless v2 / DynamoDB on-demand | Scale-to-demand managed data (SUS05-BP03) | RDS right-sized |
  | Storage | S3 + Lifecycle/Intelligent-Tiering | Tiered storage by access pattern (SUS04-BP03) | — |
  | Measure | CCFT / Sustainability console + CloudWatch | Baseline + proxy KPIs | — |
- Key Decisions: Region (SUS01-BP01), ARM adoption (SUS05-BP02), SLA alignment (SUS02-BP02).
- Scaling Path: Demand-driven scaling keeps utilization high as traffic grows (impact intensity per user should fall).
- Cost Baseline: Low-to-moderate; sustainability optimizations are largely cost-reducing.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/hardware-and-services.html (accessed 2026-08-28)

---

## Service Equivalence Map

`CLOUD_PROVIDER = AWS` (single provider). Cross-provider sustainability-tooling comparison is included
because architects frequently benchmark carbon tooling across clouds.

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|--------------|-------|--------------------|
| Well-Architected sustainability guidance | WAF Sustainability Pillar | Architecture Framework — (sustainability woven into pillars; no standalone pillar) | Azure WAF Sustainability guidance / Well-Architected sustainability workload | OCI Best Practices Framework (no standalone sustainability pillar) |
| Carbon measurement tool | Customer Carbon Footprint Tool / Sustainability console | Carbon Footprint | Emissions Impact Dashboard / Microsoft Sustainability Manager | OCI (no equivalent first-party carbon tool at parity) |
| Efficient ARM compute | AWS Graviton | Tau T2A (Arm) / Axion | Cobalt (Arm) | OCI Ampere A1 |
| Serverless (utilization sharing) | Lambda / Fargate | Cloud Run / Cloud Functions | Azure Functions / Container Apps | OCI Functions |
| Storage lifecycle tiering | S3 Lifecycle / Intelligent-Tiering / Glacier | Cloud Storage lifecycle / Autoclass / Archive | Blob lifecycle / Cool-Archive tiers | Object Storage lifecycle / Archive |

> ⚠️ Equivalence ≠ feature or methodology parity. Carbon tools differ in scope coverage (Scope 3),
> update lag, and verification methodology. Validate against each provider's current docs.
> Cross-provider rows are directional (Medium confidence); only the AWS column is pinned to the
> 2024-11-06 Sustainability Pillar revision.

---

## Provider Differentiators (AWS, sustainability-relevant)

```
Differentiator: AWS Graviton (custom ARM processors)
Category: Compute
Unique Value: Higher performance-per-watt vs comparable x86; a first-class sustainability + cost lever.
Architecture Impact: Default-consider Graviton for ARM-compatible tiers (SUS05-BP02).
When to Leverage: Stateless compute, containers, managed-DB engines supporting Graviton.
Caveat: Requires ARM-compatible builds/dependencies; validate per workload.
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/hardware-and-services.html (accessed 2026-08-28)
```
```
Differentiator: Customer Carbon Footprint Tool → AWS Sustainability console
Category: Measurement
Unique Value: Free Scope 1/2/3 carbon + water-withdrawal data by Region/service/account; independently
  verified location-based & market-based methodology; evolving to programmatic API access.
Architecture Impact: Enables the mandatory "Understand your impact" baseline without third-party tooling.
When to Leverage: Any workload needing a sustainability baseline / KPI.
Caveat: Historical/aggregated with reporting lag (carbon from 2022, water from 2023); not real-time.
Source: https://aws.amazon.com/aws-cost-management/aws-customer-carbon-footprint-tool/ (accessed 2026-08-28)
```
```
Differentiator: Sustainability as a formal sixth WAF pillar
Category: Governance
Unique Value: AWS uniquely codifies environmental sustainability as a standalone Well-Architected
  pillar with review questions (SUS 1–6) reviewable in the Well-Architected Tool; GCP/Azure/OCI weave
  sustainability into other pillars rather than a dedicated pillar.
Architecture Impact: Sustainability findings become part of standard WAFR governance.
When to Leverage: Organizations running formal Well-Architected reviews.
Caveat: Pillar scope is environmental only (not social/governance ESG).
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html (accessed 2026-08-28)
```

---

## Scenario Coverage

**Standard Case**: Variable-demand user-facing workload seeking to reduce impact intensity per user.
- Approach: Measure baseline (CCFT + CloudWatch proxy KPIs) → right-size + Auto Scaling + Graviton →
  flatten demand (SQS/async) → tier storage (S3 Lifecycle) → adopt managed services → review via WAFR SUS 1–6.
- Key Decisions: Region (SUS01-BP01), SLA alignment (SUS02-BP02), ARM adoption (SUS05-BP02).

**Edge Case**: Strict real-time, low-latency, regulated workload where demand-flattening and lowest-carbon
Region are constrained by SLA and data-residency.
- Approach: Prioritize proximity/residency Regions; still apply right-sizing, Graviton, storage tiering,
  and idle-asset elimination — the utilization levers remain available even when Region/async are constrained.

**Anti-Pattern Case**: Team asks to publish a "carbon-neutral architecture" claim without any measurement.
- Clarification: Refuse to certify. Ask for the CCFT baseline and defined sustainability KPIs first
  (design principles "Understand your impact" / "Establish sustainability goals"); unmeasured claims are
  a greenwashing risk. Also confirm `ARCHITECTURE_CONTEXT` before tailoring Ask-First decisions.

---

## §7 — Research Iteration Changelog

| Iteration | Item | Action | Source added | Status |
|-----------|------|--------|--------------|--------|
| 0 (initial) | Pillar definition, 6 design principles, shared responsibility model | Fetched | sustainability-pillar.html, design-principles..., the-shared-responsibility-model.html | ✓ Verified |
| 0 (initial) | SUS 1–6 best-practice areas + all 29 BP IDs/titles | Fetched | region-selection, alignment-to-demand, software-and-architecture, data, hardware-and-services, process-and-culture | ✓ Verified |
| 0 (initial) | Changelog / edition delta (SUS06-BP01 new, SUS 6 renumbered) | Fetched | document-revisions.html | ✓ Verified |
| 0 (initial) | CCFT methodology, scope, dates | Fetched | aws-customer-carbon-footprint-tool page | ✓ Verified |
| 1 | Improvement-process exact wording | Fetch returned no body text | the-sustainability-improvement-process.html (unretrieved) | ⚠️ IRRESOLVABLE — page body not extractable on fetch; six-step loop provided as paraphrase, human verification required for verbatim wording |

**Triangulation status (P5.triangulate):** 4 of 5 Always-Do patterns are `✓✓ Triangulated` against two
independent official pages. "Data lifecycle management" rests primarily on the SUS 4 page (Medium
confidence on exhaustiveness, reinforced by the "Use managed services" design principle).

---

## Source Bibliography

All sources are official AWS documentation, accessed **2026-08-28**. The pillar whitepaper is pinned to
its **2024-11-06** revision.

1. Sustainability Pillar — overview & publication date — https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html
2. Design principles for sustainability in the cloud — https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html
3. The shared responsibility model — https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/the-shared-responsibility-model.html
4. SUS 1 Region selection — https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/region-selection.html
5. SUS 2 Alignment to demand — https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/alignment-to-demand.html
6. SUS 3 Software and architecture — https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/software-and-architecture.html
7. SUS 4 Data management — https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/data.html
8. SUS 5 Hardware and services — https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/hardware-and-services.html
9. SUS 6 Process and culture — https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/process-and-culture.html
10. Document revisions (changelog) — https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/document-revisions.html
11. AWS Customer Carbon Footprint Tool — https://aws.amazon.com/aws-cost-management/aws-customer-carbon-footprint-tool/
12. The sustainability improvement process (⚠️ body not extractable on fetch — verify manually) — https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/the-sustainability-improvement-process.html

> **Next step:** run `/skill-best-practices-validator` on this research file before authoring a
> SKILL.md from it, and re-verify the improvement-process verbatim wording (the one irresolvable gap).
