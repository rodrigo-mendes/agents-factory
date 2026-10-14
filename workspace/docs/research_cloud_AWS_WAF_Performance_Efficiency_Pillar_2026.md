# Cloud Architecture Research — AWS Well-Architected Framework: Performance Efficiency Pillar

## Metadata
```yaml
Full_Name: "AWS Well-Architected Framework — Performance Efficiency Pillar"
Cloud_Provider: "AWS"
Architecture_Domain: "Well-Architected Framework — Performance Efficiency Pillar"
Target_Edition: "Performance Efficiency Pillar whitepaper — November 6, 2024 revision (current stable); service-currency verified as of 2026-08-28"
Architecture_Context: "Multi-account production workloads on AWS"
Official_Source_URL: "https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-28"
Research_Depth: "exhaustive"
Currency_Threshold: "2027-08-28"
```

> ## ⚠️ Version Reality Note (read first)
>
> The request pinned `TARGET_EDITION="AWS Performance efficiency Pillar 2026"`. **There is no distinct
> "2026" edition of the Performance Efficiency Pillar whitepaper.** The official document-revisions
> history confirms the most recent revision is still **November 6, 2024** (verified 2026-08-28 against
> the official revisions page). Per Version Absolutism, this research pins the *framework guidance* to
> the November 6, 2024 whitepaper and does not fabricate a 2026 whitepaper edition.
>
> What *has* changed by 2026 is the **service layer** the pillar references. The most consequential
> change for this pillar is that **AWS Graviton5 reached General Availability in 2026** — M9g/M9gd on
> **June 10, 2026** and C9g/C9gd on **June 30, 2026** — superseding Graviton4 (M8g/C8g/R8g) as the
> price-performance leader. All Graviton-related best practices below carry a `⚠️ Migration Note` and
> now recommend Graviton5 as the 2026 default, with Graviton4 retained as a still-valid prior
> generation. The whitepaper text itself (PERF02-BP06) references Graviton generically and remains
> correct; only the concrete "current generation" recommendation moved from Graviton4 → Graviton5.
>
> Source currency: the November 6, 2024 whitepaper revision is >12 months old as of 2026-08-28 but
> remains the official current stable. Re-verify service-specific claims against the official URLs
> before relying on them.

---

## Executive Summary

The AWS Well-Architected Framework Performance Efficiency Pillar defines the ability to use cloud resources efficiently to meet performance requirements, and to maintain that efficiency as demand changes and technologies evolve. It is one of the six pillars of the Well-Architected Framework and provides structured best-practice areas, design principles, and named best practices (PERF-prefixed) that architects use to evaluate and improve workload efficiency. Its five best-practice areas are: Architecture selection, Compute and hardware, Data management, Networking and content delivery, and Process and culture. The pillar was restructured from eight areas down to five in the October 3, 2023 major update; the current stable revision is November 6, 2024 (a minor update to PERF03-BP04 service recommendations).

As of 2026, the single most impactful service-level change affecting this pillar's compute guidance is the **General Availability of AWS Graviton5** (fifth generation). Graviton5-powered M9g/M9gd instances (GA June 10, 2026) deliver up to 25% better compute performance versus Graviton4 M8g/M8gd, up to 30% faster for databases, and up to 35% faster for web applications and for machine learning. Graviton5 C9g/C9gd compute-optimised instances (GA June 30, 2026) add up to 25% higher performance per vCPU versus C8g, 5x more L3 cache, up to 3x higher packet-processing performance, up to 15% higher network bandwidth, and ~20% higher EBS bandwidth. Graviton5 runs on the sixth-generation Nitro System with a formally verified Nitro Isolation Engine. This supersedes the Graviton4 guidance that was current when the November 6, 2024 whitepaper shipped — a `⚠️ Migration Note` applies to every Graviton best practice in this document.

The three most critical architecture guardrails for multi-account production workloads on AWS are: (1) select the correct compute model per component — not lift-and-shift — because wrong compute selection carries a "Level of risk: High" rating per PERF02-BP01; (2) right-size continuously using AWS Compute Optimizer rather than over-provisioning as a safety margin; and (3) apply mechanical sympathy to data store selection — using DynamoDB, Aurora, ElastiCache, OpenSearch, and S3 matched to access patterns — rather than routing all traffic through a single relational store.

---

## Cloud Architecture Glossary

Terms derived directly from the official Performance Efficiency Pillar documentation (November 6, 2024), with service-currency updates verified 2026-08-28.

```
Term: Performance Efficiency Pillar
Definition: "The ability to use cloud resources efficiently to meet performance requirements, and to maintain that efficiency as demand changes and technologies evolve."
Provider Docs Section: Welcome — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/welcome.html
Architect Usage: Use as the organising lens when evaluating whether compute, data store, and network choices are matched to actual requirements, not to convenience or habit.
Common Confusion: Confused with the Cost Optimization Pillar. Performance Efficiency is about matching resources to requirements; Cost Optimization is about eliminating waste. The two reinforce each other (right-sizing satisfies both) but are governed by separate best practices.
```

```
Term: Mechanical Sympathy
Definition: Using the technology approach that best aligns with goals — for example, matching a database or storage service to the application's data access patterns rather than using a general-purpose store for all needs.
Provider Docs Section: Design Principles — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/design-principles.html
Architect Usage: Drive polyglot persistence decisions: DynamoDB for key-value/high-scale, Aurora/RDS for relational, ElastiCache for read-heavy caching, OpenSearch for full-text search, S3 for object/blob.
Common Confusion: Confused with hardware-level CPU affinity. In the AWS WAF context, "mechanical sympathy" is a software and service architecture concept, not a CPU scheduling term.
```

```
Term: PERF02 (Compute and Hardware)
Definition: The best-practice area within the Performance Efficiency Pillar that covers selection, right-sizing, scaling, hardware acceleration, and metrics collection for compute resources.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/compute-and-hardware.html
Architect Usage: Reference PERF02-BP01 through PERF02-BP06 when making any EC2 instance type, Lambda memory, container sizing, or Graviton migration decision.
Common Confusion: Confused with the general "architecture selection" area. PERF02 is specifically about compute and hardware; architecture selection covers the broader service type decisions (serverless vs containers vs instances).
```

```
Term: AWS Compute Optimizer
Definition: An AWS service that analyzes CloudWatch metrics (up to 93 days of data; requires at least 30 hours of metrics in the past 14 days for EC2 recommendations) and provides right-sizing recommendations classified by savings opportunity versus performance risk.
Provider Docs Section: https://docs.aws.amazon.com/compute-optimizer/latest/ug/what-is-compute-optimizer.html
Architect Usage: Run as the primary input to EC2 right-sizing decisions (PERF02-BP04). Enable the CloudWatch agent on all EC2 instances to surface memory metrics; without it, Compute Optimizer works on CPU/network only, reducing recommendation accuracy.
Common Confusion: Confused with AWS Cost Explorer rightsizing recommendations. Compute Optimizer is deeper (93-day window, memory-aware, covers Lambda and Auto Scaling groups); Cost Explorer rightsizing is simpler and cost-focused.
```

```
Term: Target-Tracking Scaling Policy
Definition: An Application Auto Scaling or EC2 Auto Scaling policy that adjusts capacity to keep a chosen CloudWatch metric at a specified target value (e.g., RequestCountPerTarget on an ALB target group).
Provider Docs Section: Referenced in PERF02-BP05 (dynamic scaling)
Architect Usage: Prefer target-tracking over step scaling for most web workloads; it is simpler to configure and self-adjusting. Validate target values with load tests before production.
Common Confusion: Confused with scheduled scaling. Target-tracking reacts to real-time metric values; scheduled scaling adjusts capacity at predetermined times regardless of actual load.
```

```
Term: AWS Graviton5  ⚠️ Migration Note (2026 — supersedes Graviton4 as default)
Definition: AWS-designed ARM64 processor generation (fifth generation), powering M9g/M9gd (general purpose, GA 2026-06-10) and C9g/C9gd (compute optimized, GA 2026-06-30) EC2 instance families. Runs on the sixth-generation AWS Nitro System with a formally verified Nitro Isolation Engine. Official benchmarks vs Graviton4: M9g up to 25% better compute performance vs M8g/M8gd, up to 30% faster for databases, up to 35% faster for web applications, up to 35% faster for machine learning; C9g up to 25% higher performance per vCPU vs C8g, 5x more L3 cache, up to 3x higher packet-processing performance, up to 15% higher network bandwidth, and ~20% higher EBS bandwidth.
Provider Docs Section: PERF02-BP06 (generic Graviton reference) + https://aws.amazon.com/blogs/aws/amazon-ec2-c9g-and-c9gd-instances-powered-by-aws-graviton5-processors-are-now-available/
Architect Usage: Default choice for new general-purpose (M9g), compute-optimised (C9g), and I/O-intensive (M9gd/C9gd with local NVMe) workloads where ARM64 binary compatibility is confirmed. Use Compute Optimizer to identify existing EC2 fleets suitable for Graviton migration. Regional availability at GA: US East (N. Virginia, Ohio), US West (Oregon), EU (Frankfurt) — verify current region coverage before committing.
Common Confusion: Confused with Graviton4 figures. Graviton5 is a distinct generation; the 25%/30%/35% benchmarks are Graviton5-vs-Graviton4 claims. Memory-optimised (R9g) was not yet GA in the sources reviewed as of 2026-08-28 — verify before assuming an R-series Graviton5 exists.
```

```
Term: AWS Graviton4  (prior generation — still valid)
Definition: AWS-designed ARM64 processor generation (fourth generation), powering M8g, C8g, and R8g EC2 instance families. Official benchmarks (vs Graviton3): up to 30% better compute performance; up to 40% faster for databases; up to 45% faster for large Java applications; across the Graviton family, up to 40% better price-performance and up to 60% less energy versus comparable x86 EC2 instances.
Provider Docs Section: PERF02-BP06 + https://aws.amazon.com/ec2/graviton/
Architect Usage: Remains a valid, cost-effective ARM64 option and is the memory-optimised (R8g) choice until an R-series Graviton5 is confirmed GA. Prefer Graviton5 (M9g/C9g) for new general-purpose and compute-optimised builds where available in-region.
Common Confusion: Do not present Graviton4 as the newest generation in 2026 documentation — Graviton5 superseded it in June 2026.
```

```
Term: Serverless Architecture
Definition: An architecture approach where the cloud provider removes the need to run or maintain physical servers; managed services operate at cloud scale. In AWS, the primary serverless compute service is AWS Lambda (functions-as-a-service).
Provider Docs Section: Design Principles — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/design-principles.html
Architect Usage: Apply for spiky or event-driven workloads, short tasks, and unpredictable traffic where scale-to-zero economics are relevant. Combine with Amazon API Gateway for HTTP-triggered patterns.
Common Confusion: Confused with "no servers exist." Serverless means the architect does not manage servers — AWS manages the fleet. Underlying hardware still exists.
```

```
Term: Right-Sizing
Definition: The practice of continuously matching compute resource allocation to actual workload requirements — neither over-provisioning (wasted spend) nor under-provisioning (degraded performance). Governed by PERF02-BP04 in the Performance Efficiency Pillar.
Provider Docs Section: PERF02-BP04
Architect Usage: Use AWS Compute Optimizer recommendations on a recurring cadence (monthly minimum). Require memory metric collection (CloudWatch agent) as a prerequisite for accurate recommendations.
Common Confusion: Confused with a one-time activity performed at migration. Right-sizing is a continuous process; demand patterns, application changes, and new instance types (e.g., the Graviton5 generation) all require periodic re-evaluation.
```

```
Term: Polyglot Persistence
Definition: An architecture approach where different services within a workload use different data store technologies matched to their specific access patterns, rather than a single general-purpose store for all data.
Provider Docs Section: Derived from design principle "Consider mechanical sympathy" and the Data management best-practice area.
Architect Usage: Model each service's data access patterns (key-value, relational, search, cache, object) independently and select the purpose-built AWS managed service for each. Accept the operational complexity trade-off in exchange for performance gains.
Common Confusion: Confused with data lake architecture. Polyglot persistence is about operational data stores per service; a data lake is an analytical/aggregation pattern.
```

```
Term: CloudWatch Agent (memory metrics)
Definition: A software agent installed on EC2 instances or containers that collects operating-system-level metrics — including memory utilisation — and publishes them to Amazon CloudWatch. Required for PERF02-BP03 (data-driven approach) because EC2 does not surface memory metrics to CloudWatch by default.
Provider Docs Section: PERF02-BP03
Architect Usage: Treat CloudWatch agent installation as mandatory on all EC2-based workloads. Without memory metrics, Compute Optimizer right-sizing recommendations are incomplete, and capacity planning lacks a critical signal.
Common Confusion: Confused with CloudWatch built-in EC2 metrics. Built-in metrics cover CPU, network, and disk I/O at the hypervisor level; memory is only available via the CloudWatch agent installed inside the guest OS.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**PE-AD-1 — Select best compute option per component (not lift-and-shift)**
- Pillar Alignment: Compute and hardware (PERF02-BP01)
- Why: "Level of risk: High" per PERF02-BP01. Wrong compute model leads to lower performance efficiency. Lack of awareness of cloud compute options is a cited root cause.
- AWS Services: Amazon EC2, AWS Lambda, Amazon ECS, Amazon EKS, AWS Fargate, AWS Batch
- Architecture Decision: Match compute model to each component's processing pattern, traffic shape, latency requirement, and scaling behaviour. Mix compute models within a single workload where patterns differ — for example, Lambda for event-driven processing alongside EC2 Auto Scaling for a stateful API tier.
- Verification: Benchmark candidate compute options in non-production. Monitor with CloudWatch. Obtain recommendations from AWS Compute Optimizer. Revisit on each major traffic or feature change.
- Source: PERF02-BP01 — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/perf_compute_hardware_select_best_compute_options.html [✓✓ Triangulated | PERF02-BP01 page + compute-and-hardware.html]

**PE-AD-2 — Right-size compute continuously**
- Pillar Alignment: Compute and hardware (PERF02-BP04)
- Why: Avoids over- and under-provisioning, both of which degrade performance efficiency outcomes.
- AWS Services: AWS Compute Optimizer, Amazon CloudWatch (plus CloudWatch agent for memory), EC2 instance types
- Architecture Decision: Enable Compute Optimizer across all accounts. Compute Optimizer analyzes up to 93 days of CloudWatch data; requires at least 30 hours of metrics in the past 14 days for EC2 recommendations. Recommendations are classified by savings opportunity versus performance risk. Install CloudWatch agent on all EC2 instances to surface memory utilisation — without it, recommendations are incomplete. Re-run after the Graviton5 GA to capture M9g/C9g migration candidates.
- Verification: Compute Optimizer console dashboard; `describe-recommendations` CLI command; CloudWatch dashboards confirming memory metrics are present.
- Source: PERF02-BP04 + https://docs.aws.amazon.com/compute-optimizer/latest/ug/what-is-compute-optimizer.html [✓✓ Triangulated | PERF02-BP04 + Compute Optimizer UG]

**PE-AD-3 — Dynamic scaling**
- Pillar Alignment: Compute and hardware (PERF02-BP05)
- Why: Match compute supply to actual demand; maintain efficiency as demand changes — a core pillar definition requirement.
- AWS Services: EC2 Auto Scaling, Application Auto Scaling, ECS/EKS scaling, Lambda concurrency controls
- Architecture Decision: Configure target-tracking scaling policies based on CloudWatch KPI metrics relevant to the workload (e.g., RequestCountPerTarget, CPU utilisation, queue depth). Validate scale-out and scale-in behaviour with load tests before production cutover. Design services to be stateless to allow horizontal scaling.
- Verification: CloudWatch alarms and target-tracking policy configuration; load test results confirming scale-out triggers and latency under simulated peak.
- Source: PERF02-BP05 [✓✓ Triangulated | PERF02-BP05 + COST09-BP03 dynamic-scaling guidance]

**PE-AD-4 — Use current-generation Graviton (ARM64) for price-performance** ⚠️ Migration Note
- Pillar Alignment: Compute and hardware (PERF02-BP06 — use optimized hardware-based compute accelerators)
- Why: Custom ARM64 silicon improves both performance efficiency and energy efficiency simultaneously. **2026 currency:** Graviton5 (M9g/M9gd, C9g/C9gd) is now the default current generation, delivering up to 25% better compute performance than Graviton4, up to 30% faster for databases, and up to 35% faster for web applications and ML (M9g); C9g adds up to 25% higher performance per vCPU vs C8g, 5x more L3 cache, up to 3x packet-processing, up to 15% higher network and ~20% higher EBS bandwidth. Graviton4 (M8g/C8g/R8g) remains valid, and R8g is still the memory-optimised ARM64 choice until an R-series Graviton5 is confirmed GA.
- AWS Services: AWS Graviton5 instances (M9g, M9gd, C9g, C9gd); AWS Graviton4 instances (M8g, C8g, R8g) as prior generation; GPU/accelerator instances (p4/p5) for HPC/GPU; AWS Inferentia (Inf2) and Trainium for ML acceleration
- Architecture Decision: Prefer Graviton5 (M9g for general purpose, C9g for compute-optimised) for new ARM64-compatible builds where available in-region. Fall back to Graviton4 for memory-optimised (R8g) needs and regions lacking Graviton5. Confirm ARM64 binary compatibility for all dependencies before migrating. Use Compute Optimizer to identify existing EC2 fleets that are Graviton migration candidates.
- Verification: Benchmark on Graviton5 (or Graviton4 fallback) in non-production against current instance type. Compute Optimizer Graviton recommendations. Dependency audit for ARM64 compatibility. Confirm target region carries the M9g/C9g families.
- Source: PERF02-BP06 + https://aws.amazon.com/about-aws/whats-new/2026/06/ec2-m9g-m9gd-instances-graviton5-processors-available/ + https://aws.amazon.com/blogs/aws/amazon-ec2-c9g-and-c9gd-instances-powered-by-aws-graviton5-processors-are-now-available/ + https://aws.amazon.com/ec2/graviton/ [✓✓ Triangulated | M9g GA "what's new" + C9g AWS News Blog + PERF02-BP06]

**PE-AD-5 — Collect compute-related metrics (data-driven approach)**
- Pillar Alignment: Compute and hardware (PERF02-BP03); Design Principle: "Experiment more often" / data-driven
- Why: Without metrics, sizing and scaling decisions are guesses. PERF02-BP03 mandates a data-driven approach as a prerequisite for all other compute optimisation practices.
- AWS Services: Amazon CloudWatch (plus CloudWatch agent for memory), CloudWatch Container Insights (for ECS/EKS), Lambda built-in metrics (invocations, duration, errors, concurrency)
- Architecture Decision: Establish dashboards and alarms confirming that CPU, memory, IOPS, network throughput, Lambda invocation count, and Lambda duration are all captured before any right-sizing or scaling work begins. Memory metrics on EC2 require the CloudWatch agent.
- Verification: CloudWatch dashboards present for all compute tiers; alarms configured; CloudWatch agent confirmed running on all EC2 instances; Container Insights enabled on ECS/EKS clusters.
- Source: PERF02-BP03 — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/compute-and-hardware.html [Single official source — High confidence]

**PE-AD-6 — Mechanical sympathy: match data store to access pattern**
- Pillar Alignment: Data management best-practice area; Design Principle: "Consider mechanical sympathy"
- Why: Using a single general-purpose store for all access patterns (key-value, relational, search, caching, object) creates bottlenecks and degrades performance for mismatched patterns.
- AWS Services: Amazon DynamoDB (key-value, high scale), Amazon Aurora / Amazon RDS (relational, ACID), Amazon ElastiCache (Redis/Memcached — sub-millisecond caching), Amazon OpenSearch Service (full-text search), Amazon S3 (object/blob storage)
- Architecture Decision: Model each service's data access patterns independently. Apply polyglot persistence: route each access pattern to its purpose-built managed store. Accept the operational complexity trade-off explicitly in design documentation.
- Verification: Architecture diagram review showing distinct data stores per pattern; no single RDS instance serving cache, search, and key-value workloads simultaneously; hot-key and latency analysis per store.
- Source: Performance Efficiency design principle "Consider mechanical sympathy" + Data management best-practice area — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/data-management.html [✓✓ Triangulated | design-principles.html + data-management.html]

---

### ⚠️ Architectural Decisions

**Decision A — Compute model selection**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Functions | AWS Lambda | Ops simplicity, scale-to-zero, event-driven responsiveness | Cold start latency, 15-minute execution limit | Spiky or event-driven workloads, short tasks, unpredictable traffic |
  | Containers | Amazon ECS / EKS + AWS Fargate | Portability, packing density, orchestration control | Cluster and orchestration management overhead | Microservices, steady long-running services, migration from on-premises containers |
  | Instances | Amazon EC2 | Full control, widest instance and accelerator choice | OS patching, scaling management, operational burden | Specialised OS/kernel requirements, GPU/HPC, ISV licensing, legacy lift |
  | Batch | AWS Batch | Managed parallel throughput, job scheduling | Not suitable for interactive or low-latency workloads | Large batch or parallel data processing jobs |

- Architect Instruction: "Ask what are the p99 latency requirements, expected traffic shape (spiky vs steady), and stateful/stateless constraints when the team proposes a compute model."
- Source: PERF02-BP01 — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/perf_compute_hardware_select_best_compute_options.html

**Decision B — Processor architecture** ⚠️ Migration Note (Graviton5 now default ARM64)
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | ARM64 (current gen) | Graviton5 (M9g/M9gd, C9g/C9gd) | Best price-performance in EC2; up to 25% better compute vs Graviton4; 5x L3 cache; higher network/EBS bandwidth | ARM64 recompilation/compatibility effort; no R-series (memory-optimised) Graviton5 confirmed GA yet; limited regions at launch | New general-purpose/compute-optimised builds where all dependencies are ARM64-compatible and region carries M9g/C9g |
  | ARM64 (prior gen) | Graviton4 (M8g, C8g, R8g) | Broad regional availability; R8g memory-optimised ARM64 option; strong price-performance vs x86 | One generation behind Graviton5 on compute | Memory-optimised ARM64 needs (R8g), or regions without Graviton5 |
  | x86 | Intel/AMD EC2 instance families | Broadest binary compatibility, no recompilation required | Higher cost per unit performance, higher energy consumption | x86-only ISV software, binaries without source access |

- Architect Instruction: "Ask whether all application dependencies and third-party binaries support ARM64, and whether the target region carries M9g/C9g, before committing to Graviton5. If a memory-optimised ARM64 instance is required, default to Graviton4 R8g until an R-series Graviton5 is GA."
- Source: https://aws.amazon.com/ec2/graviton/ + https://aws.amazon.com/blogs/aws/amazon-ec2-c9g-and-c9gd-instances-powered-by-aws-graviton5-processors-are-now-available/

**Decision C — Data store selection (mechanical sympathy)**
- Options:

  | Use Case | AWS Service | Optimizes | Sacrifices |
  |----------|-------------|-----------|------------|
  | Key-value / high scale | Amazon DynamoDB | Throughput, serverless operations, horizontal scale | Complex relational queries, joins |
  | Relational / ACID | Amazon Aurora / Amazon RDS | SQL expressiveness, transactional integrity | Horizontal write scaling limits |
  | Read-heavy / caching | Amazon ElastiCache (Redis / Memcached) | Sub-millisecond read latency | Consistency guarantees, additional cost |
  | Full-text search / relevance | Amazon OpenSearch Service | Relevance ranking, analytics | Operational overhead, cost |
  | Object / blob storage | Amazon S3 | Cost, durability, scale | Latency compared to in-memory or block storage |

- Architect Instruction: "Ask what the data access pattern is (lookup by key, complex query, full-text search, cached read, binary object) before selecting a data store — never default to a single RDS instance for all patterns."
- Source: Design principle "Consider mechanical sympathy" + Data management best-practice area — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/data-management.html

---

### 🚫 Anti-Patterns

**PE-ND-1 — Lift-and-shift the same on-premises compute unchanged**
- Risk Level: HIGH
- Why: PERF02-BP01 "Level of risk: High." Rehosting a monolith on an oversized EC2 instance unchanged misses cloud-native efficiency entirely. Root cause cited in PERF02-BP01: "lack awareness of cloud compute options."
- ❌ Wrong: Migrate an on-premises app onto a same-spec x86 EC2 instance (e.g., a fixed `m5.4xlarge`) with no re-evaluation of compute model or processor architecture.
- ✅ Correct: Evaluate AWS Lambda, AWS Fargate, or a right-sized Graviton5 `m9g` EC2 instance behind EC2 Auto Scaling before migrating; match compute model to the workload's actual traffic and latency pattern.
- Detection: AWS Compute Optimizer "over-provisioned" findings on newly migrated instances; instances with identical configuration to on-premises fleet.
- Impact: Cost overrun; poor performance efficiency score; no benefit from cloud elasticity.
- Source: PERF02-BP01 — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/perf_compute_hardware_select_best_compute_options.html

**PE-ND-2 — Over-provision instead of right-size**
- Risk Level: HIGH
- Why: Scaling up to a single large EC2 instance instead of using horizontal or managed scaling is a direct violation of PERF02-BP04 and PERF02-BP05.
- ❌ Wrong: Run a single oversized `r8g.8xlarge` at ~10% average CPU/memory "to be safe," with no Auto Scaling group.
- ✅ Correct: Deploy right-sized instances in an EC2 Auto Scaling group with target-tracking, or migrate to AWS Lambda/Fargate; use AWS Compute Optimizer to select the correct instance size.
- Detection: Consistently low CPU and memory utilisation visible in CloudWatch and Compute Optimizer "over-provisioned" classification.
- Impact: Cost overrun; hitting instance-level scaling or thermal limits at peak; no elasticity benefit.
- Source: PERF02-BP04, PERF02-BP05

**PE-ND-3 — Run managed-service-equivalent workloads self-managed on EC2**
- Risk Level: HIGH
- Why: PERF02-BP01 — "lack awareness of cloud compute options." Self-managing NoSQL, ML, or search on EC2 constitutes undifferentiated heavy lifting that managed services eliminate.
- ❌ Wrong: Operate a self-managed Elasticsearch or Cassandra cluster on raw EC2 instances, patched and scaled by hand.
- ✅ Correct: Use Amazon OpenSearch Service (search), Amazon DynamoDB or Amazon Keyspaces (NoSQL), and Amazon SageMaker (ML) as managed alternatives.
- Detection: Architecture review revealing self-managed Elasticsearch, Cassandra, or ML frameworks running on EC2 inventory.
- Impact: Higher operational burden, lower availability, missed managed-service performance optimisations.
- Source: PERF02-BP01

**PE-ND-4 — Operate without compute metrics**
- Risk Level: MEDIUM
- Why: Violates PERF02-BP03 data-driven principle. Sizing decisions made without CPU, memory, IOPS, and network data are guesses.
- ❌ Wrong: Run EC2 fleets with only default hypervisor metrics (CPU/network) and no memory visibility; size instances by intuition.
- ✅ Correct: Install the CloudWatch agent on all EC2 instances for memory metrics; enable CloudWatch Container Insights for ECS/EKS; run Compute Optimizer after 30+ hours of metrics in 14 days.
- Detection: Missing dashboards or alarms; absence of memory metrics in CloudWatch for EC2 workloads.
- Impact: Mis-sized fleet; no evidential basis for optimisation; Compute Optimizer recommendations unreliable.
- Source: PERF02-BP03

**PE-ND-5 — Static capacity for variable demand**
- Risk Level: MEDIUM
- Why: Violates PERF02-BP05 dynamic scaling requirement. Static capacity cannot maintain efficiency as demand changes — a core pillar definition requirement.
- ❌ Wrong: Fix a constant fleet of N EC2 instances 24/7 for a workload with a clear daily traffic curve, with no Auto Scaling policy.
- ✅ Correct: Configure EC2 Auto Scaling with target-tracking policies (e.g., on RequestCountPerTarget), or migrate to AWS Lambda for scale-to-zero.
- Detection: CloudWatch utilisation showing high variance with no corresponding scaling events; absence of Auto Scaling policies.
- Impact: High latency at traffic peaks; compute waste at traffic troughs.
- Source: PERF02-BP05

**PE-ND-6 — Single data store for all access patterns**
- Risk Level: MEDIUM
- Why: Violates the design principle "Consider mechanical sympathy." Routing key-value lookups, full-text search, and cached reads through a single RDS instance creates hot-key bottlenecks and poor performance for mismatched access patterns.
- ❌ Wrong: One Amazon RDS instance serving relational queries, session cache, full-text search, and high-volume key-value lookups simultaneously.
- ✅ Correct: Apply polyglot persistence — Amazon ElastiCache for caching, Amazon OpenSearch Service for full-text search, Amazon DynamoDB for key-value — alongside Amazon RDS/Aurora for relational data.
- Detection: Hot-key or latency analysis identifying a single data store receiving all traffic types; architecture diagram with one RDS instance serving cache, search, and KV patterns simultaneously.
- Impact: Performance bottlenecks across all access patterns; single point of failure for the data tier.
- Source: Design principle "Consider mechanical sympathy" + Data management best-practice area

---

## Cloud-Native Design Patterns

**Serverless Compute Pattern**
- Category: Scalability
- Problem: Unpredictable or spiky traffic with varying compute demand, where maintaining a standing fleet results in waste between peaks.
- Solution on AWS: AWS Lambda (functions) behind Amazon API Gateway. Functions scale to zero between requests. No server management, OS patching, or capacity planning required. Event-driven triggers from API Gateway, SQS, SNS, S3, EventBridge, or DynamoDB Streams.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Ops simplicity | No server patching or fleet management | Less control over runtime environment and execution context |
  | Cost model | Scale-to-zero; no idle capacity cost | Cold start latency on first invocation after idle period |
  | Scalability | Auto-scales to demand without configuration | Concurrency limits apply (configurable; default limits apply per account/region) |
  | Execution | Stateless by design; natural horizontal scale | Maximum 15-minute execution duration per invocation |

- Source: Performance Efficiency design principle "Use serverless architectures" — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/design-principles.html

**Right-Sizing Pattern**
- Category: Efficiency
- Problem: Over-provisioned compute fleet driving cost and energy waste without corresponding performance benefit, typically caused by conservative initial sizing or lift-and-shift from on-premises.
- Solution on AWS: AWS Compute Optimizer analyzes up to 93 days of CloudWatch metrics and produces instance type change recommendations classified by savings opportunity versus performance risk. For Lambda: memory size tuning recommendations. For EC2 Auto Scaling groups: group-level recommendations. Pair with Cost Explorer rightsizing for cost-dimension visibility. In 2026, include Graviton5 (M9g/C9g) as target instance families where Compute Optimizer flags migration candidates.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Cost | Reduces over-provisioned spend and energy consumption | Risk of under-sizing if demand spikes are not captured in the metric window |
  | Performance | Matches resource allocation to actual workload need | Requires sufficient monitoring data (minimum 30 hours in past 14 days for EC2); incomplete without memory metrics via CloudWatch agent |
  | Operational | Continuous optimisation signal without manual profiling | Requires a recurring review process and willingness to act on recommendations |

- Source: PERF02-BP04 + https://docs.aws.amazon.com/compute-optimizer/latest/ug/what-is-compute-optimizer.html

---

## Security Architecture

> Not covered in this research scope. This research is scoped to the Performance Efficiency Pillar. For security architecture guidance, consult the AWS Well-Architected Security Pillar and the Security, Identity, and Compliance best-practice area documentation. (Note: Graviton5's Nitro Isolation Engine with formal verification is a security-relevant differentiator; see Provider Differentiators.)

---

## Operational Patterns

> Not covered in this research scope. The Performance Efficiency Pillar does not include an Operational Excellence area. Refer to the AWS Well-Architected Operational Excellence Pillar for operational runbook, incident response, and observability guidance beyond compute metrics collection (PERF02-BP03).

---

## Reference Architectures

**Variable-Traffic Web Application on AWS (Performance Efficiency, 2026)**
- Context: Multi-tier web application with variable traffic, requiring efficient compute, caching, and data store alignment.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Compute | Amazon EC2 Auto Scaling (Graviton5 M9g/C9g; Graviton4 M8g/C8g fallback) | Right-sized, ARM64 application tier with target-tracking scaling |
  | Load balancing | Application Load Balancer (ALB) | Distribute traffic; source RequestCountPerTarget metric for target-tracking |
  | Caching | Amazon ElastiCache (Redis) | Sub-millisecond read caching to offload relational DB |
  | Relational data | Amazon Aurora | ACID-compliant relational data store |
  | Key-value / scale | Amazon DynamoDB | High-throughput key-value access patterns |
  | Observability | Amazon CloudWatch + CloudWatch Agent | CPU, memory, IOPS, network; Compute Optimizer data source |
  | Optimisation | AWS Compute Optimizer | Continuous right-sizing recommendations |

- Key Decisions: Lambda vs EC2 (based on traffic pattern, latency requirements, and stateful/stateless nature); Graviton5 vs Graviton4 vs x86 (ARM64 compatibility of all dependencies + regional M9g/C9g availability) before deployment.
- Scaling Path: Begin with EC2 Auto Scaling on Graviton5 (M9g); migrate stateless event-driven components to Lambda as traffic patterns become well-understood; introduce DynamoDB Accelerator (DAX) if DynamoDB read latency becomes a bottleneck.
- Source: Derived from PERF02-BP01, PERF02-BP04, PERF02-BP05, PERF02-BP06 and the data management best-practice area.

---

## Service Equivalence Map

> Not included. This research covers a single cloud provider (AWS). Cross-provider equivalence mapping is not applicable to this scope. For reference, the AWS custom-silicon differentiator (Graviton) maps loosely to Google Cloud Axion and Azure Cobalt ARM offerings, but feature/generation parity does not hold — validate against each provider's current docs before any multi-cloud decision.

---

## Provider Differentiators

**Graviton5 (ARM64) — Current AWS Silicon Advantage (2026)**
AWS designs its own ARM64 processors (Graviton family). Graviton5 (M9g/M9gd general purpose, C9g/C9gd compute optimised) is the fifth generation, GA in 2026. Official benchmarks vs Graviton4: up to 25% better compute performance (M9g vs M8g/M8gd), up to 30% faster for databases, up to 35% faster for web applications and for ML; C9g adds up to 25% higher performance per vCPU vs C8g, 5x more L3 cache, up to 3x higher packet-processing performance, up to 15% higher network bandwidth, and ~20% higher EBS bandwidth. Runs on the sixth-generation Nitro System with a formally verified Nitro Isolation Engine, purpose-built for agentic-AI-era concurrency. This is a hardware differentiation not available from the general x86 market. Compute Optimizer can recommend Graviton migration candidates from existing EC2 fleets.
Source: https://aws.amazon.com/about-aws/whats-new/2026/06/ec2-m9g-m9gd-instances-graviton5-processors-available/ + https://aws.amazon.com/blogs/aws/amazon-ec2-c9g-and-c9gd-instances-powered-by-aws-graviton5-processors-are-now-available/ + https://aws.amazon.com/ec2/graviton/

**AWS Inferentia (Inf2) and Trainium — ML Accelerators**
Purpose-built AWS accelerators for ML inference (Inferentia/Inf2) and training (Trainium). Referenced in PERF02-BP06 as optimized hardware-based compute accelerators. Relevant for multi-account production workloads with ML inference components where GPU instance cost is a constraint.
Source: PERF02-BP06

**AWS Compute Optimizer — 93-Day Metric Window**
Compute Optimizer's analysis window of up to 93 days of CloudWatch data is notably longer than most third-party right-sizing tools' defaults, allowing it to capture seasonal or monthly traffic patterns that shorter windows would miss.
Source: https://docs.aws.amazon.com/compute-optimizer/latest/ug/what-is-compute-optimizer.html

---

## Scenario Coverage

**Standard Case**: Web application with variable traffic patterns
- Approach: EC2 Auto Scaling with Graviton5 (M9g or C9g) instances behind an ALB. Target-tracking scaling policy based on RequestCountPerTarget. ElastiCache (Redis) for session and read caching. Aurora for relational data. CloudWatch agent on all instances for memory metrics. Compute Optimizer enabled across accounts for continuous right-sizing signal.
- Key Decisions: (1) Lambda vs EC2 — evaluate traffic shape (spiky favours Lambda; steady-state with stateful connections favours EC2 Auto Scaling); (2) Graviton5 vs Graviton4 vs x86 — audit all application dependencies and third-party binaries for ARM64 compatibility and confirm the target region carries M9g/C9g before committing.

**Edge Case**: ML inference workload requiring GPU or accelerator
- Approach: EC2 GPU instances (p4 or p5 family) or AWS Inferentia (Inf2) for inference endpoints managed via Amazon SageMaker. Graviton5 (ARM64) for CPU-bound pre- and post-processing stages around the inference core. SageMaker endpoint auto-scaling handles variable inference request volume.

**Edge Case 2**: Memory-optimised ARM64 requirement in 2026
- Approach: Because an R-series Graviton5 was not confirmed GA as of 2026-08-28, default the memory-optimised ARM64 tier to Graviton4 R8g and re-evaluate once an R9g equivalent ships. Confirm current availability via the EC2 instance-types page before design sign-off.

**Anti-Pattern Case**: Team proposes maximum-specification EC2 instances "to be safe" without load testing
- Clarification: Ask for the expected p99 latency requirement and the anticipated traffic profile (requests per second, daily/weekly pattern). Ask whether AWS Compute Optimizer has been consulted on the proposed instance size. Ask whether the workload has been load-tested on a smaller instance type in non-production. Propose starting with a right-sized Graviton5 instance, running a load test, and resizing based on evidence rather than safety margin intuition.

---

## §7 Research Iteration Changelog

| Iteration | Item | Action | Resolution | Source |
|---|---|---|---|---|
| 1 | Existence of a "2026" Performance Efficiency Pillar whitepaper edition | Verified official document-revisions page | No 2026 edition exists; current stable remains November 6, 2024. Pillar pinned accordingly with a Version Reality Note. | https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/document-revisions.html (accessed 2026-08-28) |
| 2 | Whether Graviton4 remains the current-generation ARM64 recommendation for 2026 | Searched for newer Graviton generation | Graviton5 reached GA in 2026 (M9g/M9gd 2026-06-10; C9g/C9gd 2026-06-30), superseding Graviton4. Updated glossary, PE-AD-4, Decision B, differentiators, reference architecture, and scenarios. Tagged `⚠️ Migration Note`. | https://aws.amazon.com/about-aws/whats-new/2026/06/ec2-m9g-m9gd-instances-graviton5-processors-available/ (accessed 2026-08-28) |
| 3 | Exact Graviton5 vs Graviton4 benchmark figures | Fetched official AWS News Blog (C9g) and "what's new" (M9g) | Confirmed: M9g up to 25% better compute, up to 30% faster DB, up to 35% faster web/ML; C9g up to 25% higher perf/vCPU, 5x L3 cache, up to 3x packet-processing, up to 15% network, ~20% EBS bandwidth. | https://aws.amazon.com/blogs/aws/amazon-ec2-c9g-and-c9gd-instances-powered-by-aws-graviton5-processors-are-now-available/ (accessed 2026-08-28) |
| — | R-series Graviton5 (memory-optimised) GA status | Targeted search within reviewed sources | ⚠️ Not confirmed GA in reviewed sources as of 2026-08-28; documented as an explicit open item. R8g (Graviton4) remains the memory-optimised ARM64 default until confirmed. Human verification recommended before relying on an R9g assumption. | Absence of R9g in M9g/C9g GA announcements |

---

## Verification & Next Step

- All six mandatory sections present: Framework Pillars (Guardrails ✅), Always-Do Patterns, Ask-First Decisions (⚠️), Never-Do Anti-patterns (🚫, each with ❌/✅), Service Equivalence note, Source Bibliography (inline per-item + changelog).
- Every Never-Do entry carries a side-by-side ❌ Wrong / ✅ Correct example with exact AWS service names.
- Sources >12 months (the Nov 6, 2024 whitepaper) flagged in the Version Reality Note.
- Recommended follow-up: run `/skill-best-practices-validator` on this output, and re-verify R-series Graviton5 (R9g) GA status before any memory-optimised ARM64 design sign-off.
