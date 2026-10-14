---
name: applying-waf-sustainability-pillar
description: "Applies the AWS Well-Architected Framework Sustainability Pillar (2024-11-06 revision, 29 best practices across SUS 1-6) to production AWS workloads. Use when reviewing, designing, or improving AWS architectures for environmental sustainability — right-sizing, region selection, data lifecycle, managed services, and organizational sustainability goals."
---

## Function

Specialist in AWS Well-Architected Sustainability Pillar guidance for general AWS production workloads, pinned to the **2024-11-06 whitepaper revision**.

## Version Context

**Framework**: AWS Well-Architected Framework — Sustainability Pillar
**Pinned revision**: 2024-11-06 (current stable as of 2026-08-28)
**Pillar scope**: Environmental sustainability only — energy, resource efficiency, and waste reduction
**Support status**: Active (added to WAF 2021-12-02; latest substantive revision 2024-11-06)

**Changes in 2024-11-06 revision**:
- Added **SUS06-BP01 "Communicate and cascade your sustainability goals"** (new best practice)
- SUS 6 best practices renumbered as a result of the addition
- Updated guidance across SUS 1, SUS 3, SUS 4, SUS 5, and SUS 6

**Total best practices**: 29 across 6 areas (SUS 1: 1, SUS 2: 6, SUS 3: 5, SUS 4: 8, SUS 5: 4, SUS 6: 5)

**Currency threshold**: Re-verify after 2027-08-28 or whenever the whitepaper revision date advances past 2024-11-06.

**Deprecated / invalidated**: Any SUS06-BP numbering from before 2024-11-06 is misinformation — SUS 6 was renumbered in this revision.

> WARNING — Agent: Reject any SUS 6 best-practice IDs or titles that predate the 2024-11-06 revision. The pillar scope is environmental sustainability only — not social/governance ESG.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Three-tier patterns (✅⚠️🚫) for sustainability decisions
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases for this skill
- **[Integration Patterns](#integration-patterns)** — Service composition and cross-pillar interactions
- **[Verification Loop](#verification-loop)** — Validation checks for sustainability implementation
- **[Quick Reference](#quick-reference)** — SUS 1-6 best-practice ID map at a glance
- **[External Resources](#external-resources)** — Official AWS documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

- **Establish sustainability KPIs before any optimization (SUS 1 / design principles)** — Pull Scope 1/2/3 carbon and water-withdrawal baseline from the AWS Customer Carbon Footprint Tool (CCFT) / AWS Sustainability console by Region, service, and account. Instrument CloudWatch with per-unit-of-work proxy metrics (e.g., vCPU-hours per 1,000 requests). Set targets and review cadence before making any changes. Without a baseline, improvements cannot be prioritized or validated; unmeasured claims are a greenwashing risk.

- **Right-size and auto-scale all elastic tiers (SUS02-BP01, SUS05-BP01, SUS05-BP02)** — Attach EC2 Auto Scaling / Application Auto Scaling policies to every elastic tier. Use AWS Compute Optimizer to eliminate over-provisioned findings. Default to Graviton (ARM) instance families for ARM-compatible workloads — Graviton delivers higher performance-per-watt than comparable x86. Two hosts at 30% utilization are less efficient than one host at 60% due to baseline power per host.

- **Apply data lifecycle policies to all persistent storage (SUS04-BP01, SUS04-BP03, SUS04-BP05, SUS04-BP08)** — Attach S3 Lifecycle configurations or enable S3 Intelligent-Tiering on every production bucket. Use Amazon Data Lifecycle Manager for EBS snapshots. Expire obsolete data; back up only data that is difficult to recreate. Unmanaged data growth is a medium-risk anti-pattern with ongoing energy and cost impact.

- **Default to managed and serverless services for undifferentiated heavy lifting (SUS05-BP03, design principle "Use managed services")** — Use Fargate, Lambda, Aurora Serverless v2, DynamoDB on-demand, and S3 for standard workload components. Shared AWS-operated services achieve higher fleet utilization than dedicated customer-managed infrastructure. Document a justification in an ADR for any self-managed EC2 that replaces a managed-service equivalent.

- **Communicate, cascade, and track sustainability goals per workload (SUS06-BP01, SUS06-BP02, SUS06-BP03)** — Define per-workload sustainability targets and assign them to workload owners. Track via Well-Architected Tool review cadence (WAFR SUS 1–6 questions). Adopt methods that rapidly introduce improvements and keep workloads up to date. This is the 2024-11-06 revision's new organizational best practice — the most recently added of the 29.

### ⚠️ Ask First

- **Region selection: carbon intensity vs latency/data residency (SUS01-BP01)** — Ask whether the workload has a latency SLA or data-residency/compliance constraint before selecting a Region on sustainability grounds alone. Options: (a) lowest-carbon-intensity Region — optimizes sustainability KPI, may increase latency; (b) proximity Region — optimizes user experience, may carry higher grid carbon intensity; (c) cost-driven Region — optimizes spend, alignment with sustainability varies. The correct choice depends on workload SLA and regulatory constraints.

- **Demand shaping: buffering/async vs always-on capacity (SUS02-BP06, SUS03-BP01)** — Ask whether the workload's SLA permits asynchronous or deferred processing before mandating always-on provisioned capacity. Options: (a) SQS/Kinesis buffering + consumer auto-scaling — flattens demand curve, reduces peak provisioning, adds processing latency; (b) EventBridge Scheduler / AWS Batch — runs deferrable work off-peak on Spot/Graviton; (c) provisioned always-on capacity — meets strict real-time SLAs, but idle capacity wastes energy.

- **SLA alignment: business-required vs gold-plated redundancy (SUS02-BP02)** — Ask whether current SLAs reflect actual customer requirements or are over-specified. Multi-region active-active and over-provisioned redundancy are the correct choice for mission-critical/regulated workloads; they are a sustainability regression for internal or tiered services. Over-specified SLAs are a common sustainability anti-pattern that also inflates cost.

### 🚫 Never Do

| Anti-pattern | Why prohibited | Correct alternative |
|---|---|---|
| Publish sustainability claims without a CCFT baseline and defined KPIs | Violates design principles "Understand your impact" / "Establish sustainability goals"; constitutes greenwashing risk | Establish CCFT Scope 1/2/3 baseline and CloudWatch proxy KPIs first; measure improvements against that baseline |
| Fixed fleet of EC2 instances running 24/7 at low utilization (~15% avg CPU) with no scaling or scheduling | Violates "Maximize utilization" and SUS02-BP01; baseline power per host makes many low-utilization hosts less efficient than fewer high-utilization hosts | Attach EC2/Application Auto Scaling; use Instance Scheduler to stop non-prod out of hours; right-size to Graviton |
| All S3 objects kept in Standard storage class indefinitely with no lifecycle policy | Violates SUS04-BP03/05/08; provisioned storage and its energy grow unbounded | Attach S3 Lifecycle / Intelligent-Tiering; expire obsolete data; use Glacier classes for cold/archival access patterns |
| Idle/orphaned assets left provisioned (unattached EBS, idle load balancers, stale dev environments) | Violates SUS02-BP03 "Stop the creation and maintenance of unused assets" | Automate detection via Trusted Advisor / Cost Explorer; apply TTL tags on ephemeral environments; schedule teardown |
| Dedicated always-on build servers and physical test-device racks used intermittently | Violates SUS06-BP04/BP05; idle dedicated infrastructure wastes hardware and energy | Use AWS CodeBuild (on-demand build) and AWS Device Farm (managed device fleet) for shared, high-utilization testing |

---

## Integration Patterns

- **Sustainability Pillar + Cost Optimization Pillar** — The two pillars are the most aligned in WAF. Right-sizing, auto-scaling, Graviton adoption, S3 Lifecycle tiering, and idle-asset elimination reduce both cost and energy. Apply them jointly; use Cost Explorer and CCFT together.
- **Sustainability Pillar + Operational Excellence Pillar** — WAFR SUS 6 process-and-culture guidance (SUS06-BP01 to BP05) overlaps OpsEx; track sustainability targets in the same WAFR cadence as operational health.
- **Sustainability Pillar + Security Pillar** — Data minimization (SUS04-BP05 "Remove unneeded or redundant data") reduces both storage energy and attack surface. Align data-lifecycle policies with Security pillar data-classification guidance.
- **Sustainability ↔ Performance Efficiency Pillar** — Graviton (SUS05-BP02) and efficient code patterns (SUS03-BP03) improve both throughput-per-resource and sustainability KPIs simultaneously.

**Common problems**:
- **Problem**: CCFT shows no data for new account → **Solution**: Carbon data appears from 2022 forward; water-withdrawal data from 2023 forward; reporting lag is expected — CCFT is historical/aggregated, not real-time.
- **Problem**: SUS06-BP numbering in an older ADR differs from current whitepaper → **Solution**: The 2024-11-06 revision renumbered SUS 6; cross-reference against the [document revisions page](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/document-revisions.html) and update ADR IDs.
- **Problem**: Region with lowest latency is not the lowest-carbon region → **Solution**: Apply the SUS01-BP01 Ask-First decision; document the trade-off in an ADR.

---

## Verification Loop

Use after reviewing or designing for the Sustainability Pillar:

### 1. Measurement baseline verified
```
AWS Console: Cost Management → Customer Carbon Footprint Tool
- Account shows non-empty carbon emissions data (Scope 1/2/3)
- Data broken down by Region and service
- Proxy KPIs exist in CloudWatch (e.g., dashboard: "sustainability-kpis")
Expected: Data present; at least one per-unit-of-work metric defined
```

### 2. Utilization and scaling confirmed
```
AWS Console: Compute → EC2 → Auto Scaling Groups
- All elastic tiers have scaling policies attached
AWS Console: Compute Optimizer
- No "Over-provisioned" findings on compute resources
Expected: Auto Scaling on all elastic tiers; zero over-provisioned recommendations unaddressed
```

### 3. Storage lifecycle policies applied
```
AWS CLI: aws s3api get-bucket-lifecycle-configuration --bucket <bucket-name>
Expected: lifecycle rules present OR Intelligent-Tiering confirmed
AWS Console: S3 → Storage Lens → Unprotected (no lifecycle)
Expected: Zero production buckets with no lifecycle policy
```

### 4. WAFR SUS pillar review coverage
```
AWS Console: Well-Architected Tool → Workload → Lens: AWS Well-Architected Framework
- SUS 1 through SUS 6 questions answered
- SUS 6 uses 2024-11-06 best-practice IDs (SUS06-BP01 through SUS06-BP05)
Expected: No unanswered SUS questions; high-risk findings have improvement plans
```

**Troubleshooting**:
- CCFT blank → Account may be new; check that billing data is present; carbon data lags by months
- Compute Optimizer not available → Verify it is enabled for the account/org; it requires opt-in
- SUS06-BP numbers don't match whitepaper → Revision mismatch; use only 2024-11-06 IDs

---

## Quick Reference

**The 6 design principles** (apply to all workload decisions):
1. Understand your impact
2. Establish sustainability goals
3. Maximize utilization
4. Anticipate and adopt new, more efficient hardware and software
5. Use managed services
6. Reduce the downstream impact of your cloud workloads

**SUS question IDs by area**:

| Area | ID | Topic |
|------|-----|-------|
| SUS 1 | SUS01-BP01 | Region selection (carbon + business requirements) |
| SUS 2 | SUS02-BP01 to BP06 | Scale dynamically, align SLAs, stop unused assets, demand buffering |
| SUS 3 | SUS03-BP01 to BP05 | Async/scheduled jobs, remove low-use components, optimize hot code |
| SUS 4 | SUS04-BP01 to BP08 | Data classification, lifecycle policies, remove redundant data |
| SUS 5 | SUS05-BP01 to BP04 | Minimum hardware, Graviton/ARM, managed services, accelerators |
| SUS 6 | SUS06-BP01 to BP05 | Cascade goals (NEW), rapid adoption, keep up-to-date, build/test utilization |

**Primary measurement tools**:
- CCFT / AWS Sustainability console — Scope 1/2/3 carbon + water (historical, free)
- Amazon CloudWatch — per-transaction proxy KPIs (real-time)
- AWS Compute Optimizer — right-sizing recommendations
- AWS Trusted Advisor — idle/orphaned resource detection

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/applying-waf-sustainability-pillar/
├── SKILL.md                              <- This file (summary + guardrails)
└── blueprints/
    └── evaluation-scenarios.md           <- 6 test cases for skill-evaluator
```

---

## External Resources

### Official Documentation (all pinned to 2024-11-06 revision, accessed 2026-08-28)
- [Sustainability Pillar — overview](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html)
- [Design principles for sustainability in the cloud](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html)
- [Shared responsibility model (sustainability)](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/the-shared-responsibility-model.html)
- [SUS 2 — Alignment to demand](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/alignment-to-demand.html)
- [SUS 4 — Data management](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/data.html)
- [SUS 5 — Hardware and services](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/hardware-and-services.html)
- [SUS 6 — Process and culture](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/process-and-culture.html)
- [Document revisions (changelog)](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/document-revisions.html)

### Measurement Tools
- [AWS Customer Carbon Footprint Tool](https://aws.amazon.com/aws-cost-management/aws-customer-carbon-footprint-tool/) — Scope 1/2/3 carbon + water data (carbon from 2022, water from 2023)
