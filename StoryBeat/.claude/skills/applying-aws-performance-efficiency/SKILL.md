---
name: applying-aws-performance-efficiency
description: "Applies AWS Well-Architected Framework Performance Efficiency Pillar best practices to multi-account production workloads. Use when selecting compute models, right-sizing EC2 fleets, architecting data stores with mechanical sympathy, or evaluating Graviton5 migration candidates on AWS."
---

## Function

Specialist in AWS Well-Architected Framework Performance Efficiency Pillar for multi-account production workloads on AWS — compute selection, right-sizing, dynamic scaling, Graviton5 migration, and polyglot-persistence data-store alignment.

## Version Context

**Framework**: AWS Well-Architected Framework — Performance Efficiency Pillar
**Whitepaper revision**: November 6, 2024 (current stable; verified 2026-08-28)
**Service currency**: 2026-08-28
**Scope**: Multi-account production workloads on AWS

**Critical service changes as of 2026**:
- **AWS Graviton5 GA (2026-06-10 / 2026-06-30)** — M9g/M9gd (general purpose) and C9g/C9gd (compute-optimised) supersede Graviton4 as the default ARM64 choice. Graviton4 (M8g/C8g/R8g) remains valid; R8g is the only confirmed GA memory-optimised ARM64 option until an R-series Graviton5 ships.
- M9g vs M8g: up to 25% better compute, up to 30% faster for databases, up to 35% faster for web/ML.
- C9g vs C8g: up to 25% higher perf/vCPU, 5x more L3 cache, up to 3x packet-processing, up to 15% higher network, ~20% higher EBS bandwidth.

**Whitepaper structure** (5 best-practice areas since Oct 3, 2023 restructure):
Architecture selection · Compute and hardware (PERF02) · Data management · Networking and content delivery · Process and culture

⚠️ **CRITICAL — Agent Warning**:
This skill is anchored to the November 6, 2024 whitepaper (the official current stable).
Do NOT cite a "2026 edition" of the whitepaper — no such edition exists.
Always recommend Graviton5 (M9g/C9g) for new general-purpose/compute-optimised builds; do not default to Graviton4 as the newest generation in any 2026 recommendation.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 operational rules
- **[Architecture Decisions](./blueprints/architecture-decisions.md)** — Full option/tradeoff matrices for compute model, processor architecture, and data store
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Test cases (canonical, edge, anti-pattern)
- **[Integration Patterns](#integration-patterns)** — Compute + data-store reference architecture summary
- **[Verification Loop](#verification-loop)** — CLI validation commands
- **[Quick Reference](#quick-reference)** — Critical limits at a glance
- **[External Resources](#external-resources)** — Official dated sources

---

## Blueprints & Guardrails

### ✅ Always Do

**PE-AD-1 — Select best compute option per component (not lift-and-shift)**
Match compute model (Lambda / Fargate / EC2 / Batch) to each component's traffic shape, latency requirement, and stateful/stateless nature. PERF02-BP01 rates wrong compute selection as "Level of risk: High." Mix compute models within a single workload where patterns differ.

**PE-AD-2 — Right-size compute continuously with Compute Optimizer**
Enable AWS Compute Optimizer across all accounts (93-day CloudWatch window; minimum 30 hours of metrics in past 14 days for EC2). Install the CloudWatch agent on all EC2 instances to surface memory utilisation — without it, recommendations are incomplete. Re-run after Graviton5 GA to identify M9g/C9g migration candidates. Source: PERF02-BP04.

**PE-AD-3 — Configure dynamic scaling (target-tracking)**
Deploy EC2 Auto Scaling with target-tracking policies based on CloudWatch KPI metrics (e.g., `RequestCountPerTarget` on an ALB target group). Validate scale-out and scale-in behaviour with load tests before production cutover. Design services to be stateless to enable horizontal scaling. Source: PERF02-BP05.

**PE-AD-4 — Default to current-generation Graviton (ARM64) for price-performance** ⚠️ 2026 Migration Note
Prefer Graviton5 (M9g for general purpose, C9g for compute-optimised) for new ARM64-compatible builds. Fall back to Graviton4 R8g for memory-optimised ARM64 needs until R-series Graviton5 is confirmed GA. Confirm ARM64 binary compatibility for all dependencies and verify target region carries M9g/C9g before committing. Source: PERF02-BP06.

**PE-AD-5 — Collect compute metrics before any right-sizing or scaling work**
Establish CloudWatch dashboards confirming CPU, memory, IOPS, network throughput, Lambda invocations, and Lambda duration are captured. Memory metrics on EC2 require the CloudWatch agent (not included in default hypervisor metrics). Enable CloudWatch Container Insights for ECS/EKS clusters. Source: PERF02-BP03.

**PE-AD-6 — Apply mechanical sympathy: match data store to access pattern**
Model each service's data access patterns independently. Route each pattern to its purpose-built managed store: DynamoDB (key-value / high scale), Aurora/RDS (relational/ACID), ElastiCache Redis (sub-millisecond caching), OpenSearch Service (full-text search), S3 (object/blob). Explicitly document the polyglot-persistence trade-off in design records. Source: Design principle "Consider mechanical sympathy" + PERF03.

### ⚠️ Ask First

For full option/tradeoff matrices and decision trees, see [Architecture Decisions](./blueprints/architecture-decisions.md).

**Decision A — Compute model selection (Lambda vs Fargate vs EC2 vs Batch)**
Ask: What are the p99 latency requirements, expected traffic shape (spiky vs steady-state), and stateful/stateless constraints? Spiky/event-driven favours Lambda; steady-state stateful services favour EC2 Auto Scaling; workloads requiring portability and packing density favour ECS/EKS+Fargate; large parallel batch jobs favour AWS Batch. Do not choose without this information.

**Decision B — Processor architecture (Graviton5 vs Graviton4 vs x86)**
Ask: Do all application dependencies and third-party binaries support ARM64? Does the target region carry M9g/C9g? Is a memory-optimised ARM64 instance required (if yes, default to Graviton4 R8g)? Only after confirming ARM64 compatibility and regional availability should Graviton5 be committed to design. x86 is valid when ARM64 binary compatibility cannot be guaranteed.

**Decision C — Data store selection for each service**
Ask: What is the data access pattern for this service (key-value lookup, complex relational query, full-text search, cached read, binary object)? Never default to a single RDS instance for all patterns. Each pattern warrants an explicit store selection decision using the mechanical-sympathy principle.

### 🚫 Never Do

**PE-ND-1 — Lift-and-shift on-premises compute unchanged** (Risk: HIGH)
```
# WRONG — same-spec EC2 with no re-evaluation
instance_type = "m5.4xlarge"  # mirrors on-premises server

# CORRECT — evaluate compute model first, then right-size on Graviton5
# Lambda for event-driven, or:
instance_type = "m9g.xlarge"  # Graviton5, right-sized + behind EC2 Auto Scaling
```
Impact: Cost overrun; poor performance efficiency score; zero cloud-elasticity benefit. Source: PERF02-BP01.

**PE-ND-2 — Over-provision instead of right-size** (Risk: HIGH)
```
# WRONG — single oversized instance "to be safe", no ASG
instance_type = "r8g.8xlarge"  # ~10% average utilisation, no scaling

# CORRECT — right-sized in an Auto Scaling group
instance_type = "r8g.xlarge"  # Compute Optimizer-recommended size
# + EC2 Auto Scaling with target-tracking policy
```
Impact: Cost overrun; hitting instance-level limits at peak; no elasticity. Source: PERF02-BP04, PERF02-BP05.

**PE-ND-3 — Run managed-service-equivalent workloads self-managed on EC2** (Risk: HIGH)
Do not operate self-managed Elasticsearch, Cassandra, or ML frameworks on raw EC2.
Use Amazon OpenSearch Service (search), DynamoDB/Keyspaces (NoSQL), SageMaker (ML) instead.
Source: PERF02-BP01.

**PE-ND-4 — Operate EC2 fleets without memory metrics** (Risk: MEDIUM)
Do not rely on default hypervisor metrics alone (CPU/network only). Install the CloudWatch agent on every EC2 instance. Without memory metrics, Compute Optimizer recommendations are incomplete and capacity planning lacks a critical signal. Source: PERF02-BP03.

**PE-ND-5 — Fixed static capacity for variable demand** (Risk: MEDIUM)
Do not maintain a constant N-instance fleet for workloads with a measurable daily/weekly traffic curve. Configure EC2 Auto Scaling with target-tracking policies, or migrate to Lambda for scale-to-zero. Source: PERF02-BP05.

**PE-ND-6 — Route all data access through a single RDS instance** (Risk: MEDIUM)
Do not use one Amazon RDS instance to serve relational queries, session cache, full-text search, and high-volume key-value lookups simultaneously. Apply polyglot persistence: ElastiCache for caching, OpenSearch for search, DynamoDB for key-value — alongside RDS/Aurora for relational data. Source: Design principle + PERF03.

---

## Integration Patterns

For complete reference architecture with service composition and scaling path, see [Architecture Decisions](./blueprints/architecture-decisions.md).

**Variable-traffic web application (2026 reference)**:
- ALB → EC2 Auto Scaling (Graviton5 M9g/C9g; Graviton4 M8g/C8g fallback) with target-tracking on `RequestCountPerTarget`
- ElastiCache Redis → offloads Aurora reads; sub-millisecond session/cache layer
- Aurora → ACID-compliant relational tier
- DynamoDB → high-throughput key-value patterns
- CloudWatch + CloudWatch Agent → CPU, memory, IOPS, network → Compute Optimizer input

**Common integration problems**:
- **Problem**: Compute Optimizer shows only CPU/network, no memory recommendations → **Solution**: Install CloudWatch agent on all EC2 instances before enabling Compute Optimizer.
- **Problem**: Target-tracking scaling policy over-triggers → **Solution**: Validate target metric value with a load test; tune scale-in cooldown period before production cutover.
- **Problem**: ARM64 dependency failure after Graviton migration → **Solution**: Run a full dependency audit for ARM64 binary compatibility in non-production before any Graviton5 fleet migration.

---

## Verification Loop

After any compute or data-store architectural change, confirm:

### 1. Compute Optimizer enabled and receiving data
```bash
aws compute-optimizer get-enrollment-status
# Expected: "status": "Active"

aws cloudwatch list-metrics --namespace CWAgent --dimensions Name=InstanceId,Value=<id>
# Expected: mem_used_percent metric present — confirms CloudWatch agent active
```

### 2. Auto Scaling policy active
```bash
aws autoscaling describe-policies --auto-scaling-group-name <asg-name>
# Expected: TargetTrackingScaling policy with configured target value
```

### 3. Instance generation check (Graviton5 / ARM64)
```bash
aws ec2 describe-instances --filters "Name=instance-type,Values=m9g.*,c9g.*" \
  --query 'Reservations[*].Instances[*].[InstanceId,InstanceType]' --output table
# Expected: m9g.* or c9g.* entries for new workloads
```

**Troubleshooting**:
- `Compute Optimizer no recommendations` → Ensure at least 30 hours of metrics exist in the past 14 days and CloudWatch agent is running for memory.
- `Scale-out not triggering` → Verify the CloudWatch alarm dimension matches the ASG target group; confirm load test exceeds the target metric threshold.
- `ARM64 crash on Graviton` → Run `file <binary>` on all native binaries; rebuild or source ARM64-compatible container images.

---

## Quick Reference

**Critical service limits**:

| Resource | Limit | Notes |
|---|---|---|
| Compute Optimizer window | 93 days CloudWatch data | Min 30 hours in past 14 days for EC2 recommendations |
| Lambda max duration | 15 minutes per invocation | Use Step Functions for longer workflows |
| Lambda memory | 128 MB – 10,240 MB | Compute Optimizer provides memory tuning recommendations |
| Graviton5 M9g regions (GA) | US East (N. Virginia, Ohio), US West (Oregon), EU (Frankfurt) | Verify current coverage before committing |
| Graviton5 R-series (R9g) | Not confirmed GA as of 2026-08-28 | Default to Graviton4 R8g for memory-optimised ARM64 |

**Five Performance Efficiency best-practice areas**:
```
PERF01 Architecture selection
PERF02 Compute and hardware       ← primary focus of this skill
PERF03 Data management
PERF04 Networking and content delivery
PERF05 Process and culture
```

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/applying-aws-performance-efficiency/
├── SKILL.md                              ← This file (guardrails + summary)
└── blueprints/
    ├── architecture-decisions.md         ← Full option/tradeoff matrices (Decisions A/B/C) + reference architecture
    └── evaluation-scenarios.md           ← Test cases: canonical, edge, anti-pattern
```

---

## External Resources

### Official Documentation
- [Performance Efficiency Pillar — Welcome](https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/welcome.html) — Whitepaper hub (rev. November 6, 2024)
- [PERF02 Compute and Hardware](https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/compute-and-hardware.html) — BP01–BP06
- [PERF02-BP01 Select best compute options](https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/perf_compute_hardware_select_best_compute_options.html)
- [Data Management best-practice area](https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/data-management.html) — Mechanical sympathy / PERF03
- [Design Principles](https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/design-principles.html)
- [Document Revisions](https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/document-revisions.html) — Revision history confirming Nov 6, 2024 as current stable (verified 2026-08-28)

### Graviton5 Service References (2026)
- [EC2 M9g/M9gd GA announcement](https://aws.amazon.com/about-aws/whats-new/2026/06/ec2-m9g-m9gd-instances-graviton5-processors-available/) — GA 2026-06-10
- [EC2 C9g/C9gd AWS News Blog](https://aws.amazon.com/blogs/aws/amazon-ec2-c9g-and-c9gd-instances-powered-by-aws-graviton5-processors-are-now-available/) — GA 2026-06-30
- [AWS Graviton](https://aws.amazon.com/ec2/graviton/) — All generations overview

### Right-Sizing
- [AWS Compute Optimizer User Guide](https://docs.aws.amazon.com/compute-optimizer/latest/ug/what-is-compute-optimizer.html) — 93-day window, memory-aware recommendations
